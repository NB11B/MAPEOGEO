from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sovctx.node.calibration import is_negative_control_phrase, is_valid_equation_line
from sovctx.node.citations import (
    extract_authors,
    extract_identifier,
    extract_references_from_passage,
    parse_single_reference,
)
from sovctx.node.entities import (
    extract_entity_mentions,
    is_institution_entity,
)
from sovctx.node.equation_witness import extract_equation_witnesses_from_passage
from sovctx.node.frontier import (
    FrontierEvidenceRecord,
    FrontierItemRecord,
    SourceNominationRecord,
    compute_terminology_frontier_score,
    make_dedup_key,
    make_frontier_id,
)
from sovctx.node.frontier_coordinator import FrontierCoordinator
from sovctx.node.resolution import resolve_reference
from sovctx.node.terminology import NativeTerm, compute_technicality
from sovctx.node.work_db import WorkDatabase
from dataclasses import dataclass


@dataclass
class DummyPassage:
    id: str
    text: str


def test_soviet_bibliographic_parsing() -> None:
    ref_dan = "[1] Тихонов А. Н. Об устойчивости обратных задач // ДАН СССР. 1943. Т. 39, № 5. С. 195–198."
    rec1 = parse_single_reference(ref_dan, "SOVSRC:test1", "SOVPASS:p1", 1)

    assert rec1.reference_index == 1
    authors = rec1.authors_list()
    assert "Тихонов А.Н." in authors or "Тихонов А. Н." in authors
    assert rec1.year_raw == 1943
    assert rec1.volume_raw == "39"
    assert rec1.issue_raw == "5"
    assert "195" in str(rec1.pages_raw)
    assert rec1.publication_raw is not None
    assert "ДАН СССР" in rec1.publication_raw
    assert rec1.title_raw is not None
    assert "устойчивости" in rec1.title_raw

    # Multi-author book
    ref_book = "2. Понтрягин Л. С., Болтянский В. Г., Гамкрелидзе Р. В., Мищенко Е. Ф. Математическая теория оптимальных процессов. М.: Наука, 1961. 392 с."
    rec2 = parse_single_reference(ref_book, "SOVSRC:test1", "SOVPASS:p1", 2)
    assert rec2.reference_index == 2
    authors2 = rec2.authors_list()
    assert len(authors2) >= 3
    assert rec2.year_raw == 1961
    assert rec2.title_raw is not None
    assert "Математическая теория" in rec2.title_raw


def test_citation_identifier_extraction() -> None:
    ref_doi = "[3] Тихонов А. Н. О решении некорректно поставленных задач // ДАН СССР. 1963. Т. 151, № 3. С. 501–504. DOI: 10.1007/BF01234567"
    rec3 = parse_single_reference(ref_doi, "SOVSRC:test1", "SOVPASS:p1", 3)
    assert rec3.identifier_raw == "doi:10.1007/BF01234567"

    ref_mathnet = "4. Самарский А. А. О разностных схемах // ЖВМиМФ. 1962. Т. 2, № 5. http://www.mathnet.ru/php/archive.phtml?wshow=paper&jrnid=dan&paperid=3316"
    rec4 = parse_single_reference(ref_mathnet, "SOVSRC:test1", "SOVPASS:p1", 4)
    assert rec4.identifier_raw is not None
    assert "3316" in rec4.identifier_raw


def test_resolution_exact_identifier_dominance() -> None:
    ref = parse_single_reference(
        "[1] A. N. Tikhonov. On inverse problems // DAN. 1963. doi:10.1007/xyz",
        "SOVSRC:test",
        "SOVPASS:p1",
        1,
    )
    # Candidate pool where one candidate has matching DOI but slightly different title
    candidates = [
        {
            "id": "SOVSRC:cand1",
            "url": "https://mathnet.ru/paper/123",
            "title": "On ill-posed problems and regularization",
            "authors": ["Тихонов А. Н."],
            "year": 1963,
            "identifier": "doi:10.1007/xyz",
        },
        {
            "id": "SOVSRC:cand2",
            "url": "https://other.org/paper/456",
            "title": "On inverse problems",
            "authors": ["Tikhonov A. N."],
            "year": 1963,
            "identifier": "doi:10.1007/different",
        },
    ]

    attempt = resolve_reference(ref, candidates)
    # Exact identifier strictly dominates
    assert attempt.candidate_source_id == "SOVSRC:cand1"
    assert attempt.resolution_state == "EXACT_MATCH"
    assert attempt.confidence >= 0.95
    assert attempt.identifier_score == 1.0


def test_resolution_probable_and_unresolved() -> None:
    ref = parse_single_reference(
        "[1] Гельфанд И. М., Левитан Б. М. Об определении дифференциального уравнения по спектральной функции // Изв. АН СССР. 1951. Т. 15. С. 309–360.",
        "SOVSRC:test",
        "SOVPASS:p1",
        1,
    )
    good_cand = [
        {
            "id": "SOVSRC:gelfand_cand",
            "url": "https://mathnet.ru/im123",
            "title": "Об определении дифференциального уравнения по его спектральной функции",
            "authors": ["Гельфанд И. М.", "Левитан Б. М."],
            "year": 1951,
            "publication": "Изв. АН СССР. Сер. матем.",
        }
    ]
    attempt_good = resolve_reference(ref, good_cand)
    assert attempt_good.resolution_state in ("EXACT_MATCH", "PROBABLE_MATCH")
    assert attempt_good.confidence >= 0.70

    bad_cand = [
        {
            "id": "SOVSRC:wrong",
            "url": "https://example.com/unrelated",
            "title": "Квантовая электродинамика вакуума",
            "authors": ["Боголюбов Н. Н."],
            "year": 1980,
        }
    ]
    attempt_bad = resolve_reference(ref, bad_cand)
    assert attempt_bad.resolution_state == "UNRESOLVED"
    assert attempt_bad.confidence < 0.45


def test_negative_control_phrases() -> None:
    negative_phrases = [
        "разного типа",
        "в данном случае",
        "таким образом",
        "в связи с этим",
        "с другой стороны",
        "в частности",
    ]
    for phrase in negative_phrases:
        assert is_negative_control_phrase(phrase) is True

        # Check technicality score
        tech = compute_technicality(phrase, "compound_phrase")
        assert tech.score < 0.20

        # Check frontier scoring
        f_score = compute_terminology_frontier_score(
            term=phrase,
            independent_source_count=10,
            occurs_in_definition=True,
            near_equation=True,
            technicality_score=tech.score,
        )
        assert f_score.score < 0.30
        assert f_score.qualifies_for_frontier is False
        assert f_score.is_negative_control is True


def test_institution_entity_routing() -> None:
    institutions = ["АН СССР", "МГУ", "МИАН", "ЦАГИ", "ИПМ им. Келдыша", "МФТИ"]
    for inst in institutions:
        assert is_institution_entity(inst) is True

    passage_text = "Исследования проводились в МИАН и АН СССР при участии сотрудников МГУ."
    mentions = extract_entity_mentions(passage_text, "SOVSRC:inst1", "SOVPASS:p1")
    assert len(mentions) >= 3
    for m in mentions:
        assert m.entity_type == "INSTITUTION"
        assert m.normalized_name != ""


def test_equation_witness_html_attribute_rejection() -> None:
    # Contaminated lines from HTML or URL attributes
    html_lines = [
        '<div class="header">',
        'href="/php/archive.phtml?wshow=paper&jrnid=dan&paperid=3316&option_lang=rus"',
        'paperid=3316',
        'class="title-math"',
        '<span style="color:red">',
        '<a href="http://mathnet.ru">Link</a>',
    ]
    for line in html_lines:
        assert is_valid_equation_line(line) is False

    # Genuine mathematical equation lines
    math_lines = [
        r"u_t = a^2 u_{xx} + f(x, t)",
        r"\int_0^\infty K(x, s) \phi(s) ds = f(x)",
        r"H(x, p, u) = \sum_{i=1}^n p_i f_i(x, u)",
        r"x_{k+1} = A x_k + B u_k",
    ]
    for line in math_lines:
        assert is_valid_equation_line(line) is True

    # Test with extractor
    extracted_html = extract_equation_witnesses_from_passage(
        "\n".join(html_lines), "SOVSRC:h1", "SOVPASS:p1", 1
    )
    assert len(extracted_html) == 0

    extracted_math = extract_equation_witnesses_from_passage(
        "\n".join(math_lines), "SOVSRC:m1", "SOVPASS:p1", 1
    )
    assert len(extracted_math) == len(math_lines)


def test_frontier_dedup_and_loop_prevention() -> None:
    k1 = make_dedup_key("F0_CITATION_DIRECT", "тихонов 1963 дан ссср")
    k2 = make_dedup_key("F0_CITATION_DIRECT", "ТИХОНОВ 1963 ДАН СССР")
    assert k1 == k2

    id1 = make_frontier_id(k1)
    id2 = make_frontier_id(k2)
    assert id1 == id2
    assert id1.startswith("SOVFRONT:")


def test_coordinator_workflow() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_n2.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        # Create sample passages and terms
        p1 = DummyPassage(
            id="SOVPASS:p1",
            text=(
                "В работе рассматривается метод регуляризации для некорректных задач.\n"
                "Под регуляризующим алгоритмом понимается оператор R_alpha.\n"
                "Исследования проводились в АН СССР.\n"
                "u_t = a^2 u_{xx}\n"
                "[1] Тихонов А. Н. О решении некорректно поставленных задач // ДАН СССР. 1963. Т. 151, № 3. С. 501–504."
            ),
        )
        t1 = NativeTerm(
            id="SOVTERM:t1",
            surface_form="регуляризующий алгоритм",
            normalized_unicode="регуляризующий алгоритм",
            term_type="compound_phrase",
            technicality_score=0.85,
        )
        t_negative = NativeTerm(
            id="SOVTERM:tneg",
            surface_form="разного типа",
            normalized_unicode="разного типа",
            term_type="compound_phrase",
            technicality_score=0.15,
        )

        cohort_data = [
            {
                "source_id": "SOVSRC:s1",
                "passages": [p1],
                "terms": [t1, t_negative],
                "definitions": [],
                "equations": [],
            }
        ]

        coordinator = FrontierCoordinator(db)
        summary = coordinator.process_cohort_data(
            cohort=cohort_data,
            candidate_source_pool=[],
            max_nominations=10,
        )

        assert summary.sources_processed == 1
        assert summary.references_extracted >= 1
        assert summary.resolutions_attempted >= 1
        assert summary.entity_mentions_extracted >= 1
        assert summary.negative_controls_rejected >= 1

        # Check DB states
        f_items = db.get_frontier_items()
        assert len(f_items) >= 2

        # Check institution routed to F2_INSTITUTION_VENUE
        inst_items = [f for f in f_items if f.frontier_type == "F2_INSTITUTION_VENUE"]
        assert len(inst_items) >= 1

        # Check negative control is NOT in frontier items
        neg_in_frontier = any("разного типа" in f.target_label for f in f_items)
        assert neg_in_frontier is False

        # Check stats methods
        f_stats = db.get_frontier_stats()
        assert f_stats["total_frontier_items"] >= 2
        ref_stats = db.get_reference_stats()
        assert ref_stats["total_references"] >= 1
        ent_stats = db.get_entity_stats()
        assert ent_stats.get("INSTITUTION", 0) >= 1
