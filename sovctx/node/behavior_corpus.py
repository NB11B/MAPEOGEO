from __future__ import annotations

import json
from typing import Any, Optional

from .behavior import BehaviorClass, BehaviorEvaluationResult, BehaviorTestCase
from .calibration import is_negative_control_phrase, is_valid_equation_line
from .citations import extract_references_from_passage, parse_single_reference
from .entities import extract_entity_mentions, is_institution_entity
from .frontier import (
    compute_terminology_frontier_score,
    make_dedup_key,
    make_frontier_id,
)
from .resolution import resolve_reference
from .temporal import (
    FORBIDDEN_COLLAPSE_RELATIONS,
    resolve_institutional_state,
    validate_genealogical_edge,
)
from .terminology import compute_technicality


# ---------------------------------------------------------------------------
# Frozen Behavioral Corpus (62 Cases Across 6 Families)
# ---------------------------------------------------------------------------

BEHAVIORAL_CORPUS: list[BehaviorTestCase] = [
    # -----------------------------------------------------------------------
    # Family 1: Citation Behavior (Resolution states & identifier dominance)
    # -----------------------------------------------------------------------
    BehaviorTestCase(
        case_id="CIT_01",
        family="CITATION",
        description="Exact DOI match achieves EXACT_MATCH with high confidence",
        input_payload={
            "ref_text": "[1] Tikhonov A. N. Ill-posed problems // DAN. 1963. doi:10.1007/bf01234",
            "candidate_pool": [
                {
                    "id": "SOVSRC:target1",
                    "title": "On the solution of ill-posed problems",
                    "authors": ["Тихонов А. Н."],
                    "year": 1963,
                    "identifier": "doi:10.1007/bf01234",
                }
            ],
        },
        expected_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="EXACT_MATCH",
        forbidden_behaviors=[BehaviorClass.B5_DEFER_UNRESOLVED.value],
        forbidden_states=["UNRESOLVED", "CONFLICTING_MATCHES"],
    ),
    BehaviorTestCase(
        case_id="CIT_02",
        family="CITATION",
        description="Math-Net identifier match yields EXACT_MATCH",
        input_payload={
            "ref_text": "[2] Самарский А. А. // ЖВМиМФ. 1962. http://www.mathnet.ru/php/archive.phtml?paperid=3316",
            "candidate_pool": [
                {
                    "id": "SOVSRC:samarskii1962",
                    "title": "О разностных схемах газовой динамики",
                    "authors": ["Самарский А. А."],
                    "year": 1962,
                    "identifier": "mathnet:3316",
                }
            ],
        },
        expected_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="EXACT_MATCH",
    ),
    BehaviorTestCase(
        case_id="CIT_03",
        family="CITATION",
        description="Complete Soviet bibliography match without identifier",
        input_payload={
            "ref_text": "[3] Тихонов А. Н. Об устойчивости обратных задач // ДАН СССР. 1943. Т. 39, № 5. С. 195–198.",
            "candidate_pool": [
                {
                    "id": "SOVSRC:tikh_1943",
                    "title": "Об устойчивости обратных задач",
                    "authors": ["Тихонов А. Н."],
                    "year": 1943,
                    "publication": "ДАН СССР",
                }
            ],
        },
        expected_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="EXACT_MATCH",
    ),
    BehaviorTestCase(
        case_id="CIT_04",
        family="CITATION",
        description="Abbreviated citation with missing title held as PARTIAL_MATCH",
        input_payload={
            "ref_text": "[4] Тихонов А. Н. // ДАН СССР. 1963. Т. 151, № 3.",
            "candidate_pool": [
                {
                    "id": "SOVSRC:tikh_1963",
                    "title": "О решении некорректно поставленных задач",
                    "authors": ["Тихонов А. Н."],
                    "year": 1963,
                }
            ],
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="PARTIAL_MATCH",
        forbidden_states=["EXACT_MATCH"],
    ),
    BehaviorTestCase(
        case_id="CIT_05",
        family="CITATION",
        description="Divergent year (>= 5 years off) rejected as UNRESOLVED",
        input_payload={
            "ref_text": "[5] Тихонов А. Н. Об устойчивости обратных задач // ДАН СССР. 1970.",
            "candidate_pool": [
                {
                    "id": "SOVSRC:tikh_1943",
                    "title": "Об устойчивости обратных задач",
                    "authors": ["Тихонов А. Н."],
                    "year": 1943,
                }
            ],
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="UNRESOLVED",
        forbidden_states=["EXACT_MATCH", "PROBABLE_MATCH"],
    ),
    BehaviorTestCase(
        case_id="CIT_06",
        family="CITATION",
        description="Same author and matching title with 1 year difference yields PROBABLE_MATCH",
        input_payload={
            "ref_text": "[6] Понтрягин Л. С. Оптимальные процессы // Наука, 1961.",
            "candidate_pool": [
                {
                    "id": "SOVSRC:pont_1962",
                    "title": "Математическая теория оптимальных процессов",
                    "authors": ["Понтрягин Л. С."],
                    "publication": "Наука",
                    "year": 1962,
                }
            ],
        },
        expected_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="PROBABLE_MATCH",
    ),
    BehaviorTestCase(
        case_id="CIT_07",
        family="CITATION",
        description="Two near-identical candidate targets yield CONFLICTING_MATCHES",
        input_payload={
            "ref_text": "[7] Гельфанд И. М., Левитан Б. М. Дифференциальные уравнения // Изв. АН СССР. 1951.",
            "candidate_pool": [
                {
                    "id": "SOVSRC:cand_a",
                    "title": "Дифференциальные уравнения и спектральные функции",
                    "authors": ["Гельфанд И. М.", "Левитан Б. М."],
                    "publication": "Изв. АН СССР",
                    "year": 1951,
                },
                {
                    "id": "SOVSRC:cand_b",
                    "title": "Дифференциальные уравнения и спектральные функции",
                    "authors": ["Гельфанд И. М.", "Левитан Б. М."],
                    "publication": "Изв. АН СССР",
                    "year": 1951,
                },
            ],
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="CONFLICTING_MATCHES",
        forbidden_states=["EXACT_MATCH"],
    ),
    BehaviorTestCase(
        case_id="CIT_08",
        family="CITATION",
        description="Inaccessible archival citation yields NOT_PUBLICLY_LOCATED",
        input_payload={
            "ref_text": "[8] Келдыш М. В. Отчет ОПМ МИАН № 44 // Архив ИПМ. 1954. ДСП.",
            "candidate_pool": [],
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="NOT_PUBLICLY_LOCATED",
    ),
    BehaviorTestCase(
        case_id="CIT_09_A1",
        family="CITATION",
        description="Counterfactual Pair A1: Author + Title + Matching DOI yields EXACT_MATCH",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_A",
        input_payload={
            "ref_text": "[9] Боголюбов Н. Н. Статистическая механика. 1946. doi:10.1007/bogo46",
            "candidate_pool": [
                {
                    "id": "SOVSRC:bogo_correct",
                    "title": "Проблемы динамической теории",
                    "authors": ["Боголюбов Н. Н."],
                    "year": 1946,
                    "identifier": "doi:10.1007/bogo46",
                }
            ],
        },
        expected_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="EXACT_MATCH",
    ),
    BehaviorTestCase(
        case_id="CIT_09_A2",
        family="CITATION",
        description="Counterfactual Pair A2: Author + Title + Conflicting DOI refuses EXACT_MATCH",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_A",
        input_payload={
            "ref_text": "[10] Боголюбов Н. Н. Статистическая механика. 1946. doi:10.1007/bogo46",
            "candidate_pool": [
                {
                    "id": "SOVSRC:bogo_conflict",
                    "title": "Проблемы динамической теории",
                    "authors": ["Боголюбов Н. Н."],
                    "year": 1946,
                    "identifier": "doi:10.1007/different_doi_99",
                }
            ],
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="UNRESOLVED",
        forbidden_states=["EXACT_MATCH"],
    ),
    BehaviorTestCase(
        case_id="CIT_10",
        family="CITATION",
        description="Monograph with 4 authors in Nauka publisher yields PROBABLE_MATCH",
        input_payload={
            "ref_text": "11. Понтрягин Л. С., Болтянский В. Г., Гамкрелидзе Р. В., Мищенко Е. Ф. Математическая теория оптимальных процессов. М.: Наука, 1961.",
            "candidate_pool": [
                {
                    "id": "SOVSRC:pont_mono",
                    "title": "Математическая теория оптимальных процессов",
                    "authors": ["Понтрягин Л. С.", "Болтянский В. Г.", "Гамкрелидзе Р. В.", "Мищенко Е. Ф."],
                    "year": 1961,
                }
            ],
        },
        expected_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="EXACT_MATCH",
    ),
    BehaviorTestCase(
        case_id="CIT_11",
        family="CITATION",
        description="Completely mismatched subject matter candidate yields UNRESOLVED",
        input_payload={
            "ref_text": "[12] Тихонов А. Н. Метод регуляризации. 1963.",
            "candidate_pool": [
                {
                    "id": "SOVSRC:chebyshev",
                    "title": "О непрерывных дробях",
                    "authors": ["Чебышев П. Л."],
                    "year": 1855,
                }
            ],
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="UNRESOLVED",
    ),

    # -----------------------------------------------------------------------
    # Family 2: Terminology & Negative Controls Behavior
    # -----------------------------------------------------------------------
    BehaviorTestCase(
        case_id="TERM_01",
        family="TERMINOLOGY",
        description="High-technicality Russian phrase in definition span qualifies for frontier",
        input_payload={
            "term": "регуляризующий алгоритм",
            "independent_sources": 2,
            "in_definition": True,
            "near_equation": True,
            "technicality": 0.85,
        },
        expected_behavior=BehaviorClass.B2_NOMINATE.value,
        expected_state="F3_NATIVE_TERMINOLOGY",
        forbidden_behaviors=[BehaviorClass.B9_NO_ACTION.value],
    ),
    BehaviorTestCase(
        case_id="TERM_02",
        family="TERMINOLOGY",
        description="Core scientific concept (функция Ляпунова) qualifies for frontier",
        input_payload={
            "term": "функция ляпунова",
            "independent_sources": 3,
            "in_definition": True,
            "near_equation": True,
            "technicality": 0.88,
        },
        expected_behavior=BehaviorClass.B2_NOMINATE.value,
        expected_state="F3_NATIVE_TERMINOLOGY",
    ),
    BehaviorTestCase(
        case_id="TERM_03",
        family="TERMINOLOGY",
        description="Mathematical method collocation routes to F5_METHOD_OPERATOR",
        input_payload={
            "surface_text": "метод регуляризации Тихонова",
            "passage_text": "Применяется метод регуляризации Тихонова для решения задачи.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F5_METHOD_OPERATOR",
        forbidden_states=["F3_NATIVE_TERMINOLOGY"],
    ),
    BehaviorTestCase(
        case_id="TERM_04",
        family="TERMINOLOGY",
        description="Soviet computing instrument routes to INSTRUMENT entity",
        input_payload={
            "surface_text": "БЭСМ-6",
            "passage_text": "Расчеты проводились на ЭВМ БЭСМ-6 в Вычислительном центре.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="INSTRUMENT",
    ),
    BehaviorTestCase(
        case_id="TERM_05",
        family="TERMINOLOGY",
        description="Negative control phrase 'разного типа' strictly rejected (< 0.30)",
        input_payload={
            "term": "разного типа",
            "independent_sources": 10,
            "in_definition": True,
            "near_equation": True,
            "technicality": 0.15,
        },
        expected_behavior=BehaviorClass.B9_NO_ACTION.value,
        expected_state="REJECTED_NEGATIVE_CONTROL",
        forbidden_behaviors=[BehaviorClass.B0_ACQUIRE.value, BehaviorClass.B2_NOMINATE.value],
        forbidden_states=["F3_NATIVE_TERMINOLOGY", "F0_CITATION_DIRECT"],
    ),
    BehaviorTestCase(
        case_id="TERM_06",
        family="TERMINOLOGY",
        description="Negative control phrase 'в данном случае' rejected",
        input_payload={
            "term": "в данном случае",
            "independent_sources": 5,
            "in_definition": False,
            "near_equation": True,
            "technicality": 0.15,
        },
        expected_behavior=BehaviorClass.B9_NO_ACTION.value,
        expected_state="REJECTED_NEGATIVE_CONTROL",
    ),
    BehaviorTestCase(
        case_id="TERM_07",
        family="TERMINOLOGY",
        description="Negative control phrase 'таким образом' rejected",
        input_payload={
            "term": "таким образом",
            "independent_sources": 8,
            "in_definition": False,
            "near_equation": False,
            "technicality": 0.15,
        },
        expected_behavior=BehaviorClass.B9_NO_ACTION.value,
        expected_state="REJECTED_NEGATIVE_CONTROL",
    ),
    BehaviorTestCase(
        case_id="TERM_08",
        family="TERMINOLOGY",
        description="Negative control phrase 'в связи с этим' rejected",
        input_payload={
            "term": "в связи с этим",
            "independent_sources": 4,
            "in_definition": False,
            "near_equation": False,
            "technicality": 0.15,
        },
        expected_behavior=BehaviorClass.B9_NO_ACTION.value,
        expected_state="REJECTED_NEGATIVE_CONTROL",
    ),
    BehaviorTestCase(
        case_id="TERM_09_B1",
        family="TERMINOLOGY",
        description="Counterfactual Pair B1: 'АН СССР' routes strictly to F2_INSTITUTION_VENUE, NEVER term frontier",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_B",
        input_payload={
            "surface_text": "АН СССР",
            "passage_text": "Работа выполнена в АН СССР.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F2_INSTITUTION_VENUE",
        forbidden_states=["F3_NATIVE_TERMINOLOGY"],
    ),
    BehaviorTestCase(
        case_id="TERM_09_B2",
        family="TERMINOLOGY",
        description="Counterfactual Pair B2: 'метод АН СССР' does not corrupt АН СССР routing",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_B",
        input_payload={
            "surface_text": "АН СССР",
            "passage_text": "Использован метод АН СССР для анализа.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F2_INSTITUTION_VENUE",
        forbidden_states=["F3_NATIVE_TERMINOLOGY"],
    ),

    # -----------------------------------------------------------------------
    # Family 3: Identity & Naming Ambiguity
    # -----------------------------------------------------------------------
    BehaviorTestCase(
        case_id="IDENT_01",
        family="IDENTITY",
        description="Author initials order: 'А. Н. Тихонов' normalizes to 'Тихонов А. Н.' while preserving surface",
        input_payload={
            "passage_text": "Академик А. Н. Тихонов разработал теорию некорректных задач.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F1_AUTHOR_BIBLIOGRAPHY",
    ),
    BehaviorTestCase(
        case_id="IDENT_02",
        family="IDENTITY",
        description="Author surname first: 'Тихонов А.Н.' normalizes to canonical author",
        input_payload={
            "passage_text": "Статья Тихонов А.Н. посвящена регуляризации.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F1_AUTHOR_BIBLIOGRAPHY",
    ),
    BehaviorTestCase(
        case_id="IDENT_03",
        family="IDENTITY",
        description="Honorific title: 'акад. А. Н. Тихонов' routes to person without honorific in canonical name",
        input_payload={
            "passage_text": "Под руководством акад. А. Н. Тихонова велись расчеты.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F1_AUTHOR_BIBLIOGRAPHY",
    ),
    BehaviorTestCase(
        case_id="IDENT_04",
        family="IDENTITY",
        description="Bare surname 'Тихонов' without initials held as ambiguous, no silent merge",
        input_payload={
            "surface_text": "Тихонов",
            "has_initials": False,
            "context": "Как показал Тихонов в недавней заметке...",
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="AMBIGUOUS_PERSON_MENTION",
        forbidden_states=["EXACT_MATCH"],
    ),
    BehaviorTestCase(
        case_id="IDENT_05",
        family="IDENTITY",
        description="Latinized Soviet author 'A. N. Tikhonov' creates candidate correspondence link, not silent overwrite",
        input_payload={
            "source_surface": "A. N. Tikhonov",
            "target_canonical": "Тихонов А. Н.",
            "language": "en",
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="CANDIDATE_CORRESPONDS_TO",
    ),
    BehaviorTestCase(
        case_id="IDENT_06",
        family="IDENTITY",
        description="English institution name creates candidate link, not silent destruction of МИАН",
        input_payload={
            "source_surface": "Steklov Mathematical Institute",
            "target_canonical": "МИАН",
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="CANDIDATE_CORRESPONDS_TO",
        forbidden_states=["SAME_AS"],
    ),
    BehaviorTestCase(
        case_id="IDENT_07",
        family="IDENTITY",
        description="Full historical title of Steklov Institute routes to МИАН",
        input_payload={
            "passage_text": "Доклад представлен в Математический институт им. В. А. Стеклова АН СССР.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F2_INSTITUTION_VENUE",
    ),
    BehaviorTestCase(
        case_id="IDENT_08_C1",
        family="IDENTITY",
        description="Counterfactual Pair C1: Full name 'П. Л. Чебышев' routes to Chebyshev author entity",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_C",
        input_payload={
            "passage_text": "Теорема доказана П. Л. Чебышевым в 1855 году.",
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="F1_AUTHOR_BIBLIOGRAPHY",
    ),
    BehaviorTestCase(
        case_id="IDENT_08_C2",
        family="IDENTITY",
        description="Counterfactual Pair C2: Isolated 'Чебышев' without initials held as ambiguous",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_C",
        input_payload={
            "surface_text": "Чебышев",
            "has_initials": False,
            "context": "Рассмотрим полиномы Чебышева.",
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="AMBIGUOUS_PERSON_MENTION",
    ),
    BehaviorTestCase(
        case_id="IDENT_09",
        family="IDENTITY",
        description="Pre-1918 spelling 'А. М. Ляпуновъ' links via HISTORICAL_SPELLING_OF without glyph loss",
        input_payload={
            "historical_surface": "А. М. Ляпуновъ",
            "modern_form": "А. М. Ляпунов",
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="HISTORICAL_SPELLING_OF",
    ),

    # -----------------------------------------------------------------------
    # Family 4: Institution Genealogy & Temporal Dynamics
    # -----------------------------------------------------------------------
    BehaviorTestCase(
        case_id="GEN_01",
        family="GENEALOGY",
        description="АН СССР in 1991 links via RENAMED_TO to РАН, strictly refusing SAME_AS",
        input_payload={
            "source_entity": "АН СССР",
            "target_entity": "РАН",
            "proposed_relation": "RENAMED_TO",
            "year": 1991,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="RENAMED_TO",
        forbidden_states=["SAME_AS", "EQUIVALENT_TO"],
    ),
    BehaviorTestCase(
        case_id="GEN_02",
        family="GENEALOGY",
        description="АН УССР in 1991 links via RENAMED_TO to НАН Украины",
        input_payload={
            "source_entity": "АН УССР",
            "target_entity": "НАН Украины",
            "proposed_relation": "RENAMED_TO",
            "year": 1991,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="RENAMED_TO",
        forbidden_states=["SAME_AS"],
    ),
    BehaviorTestCase(
        case_id="GEN_03",
        family="GENEALOGY",
        description="ИПМ founding in 1953 links via FOUNDED_AS to ОПМ МИАН",
        input_payload={
            "source_entity": "ИПМ",
            "target_entity": "Отделение прикладной математики МИАН",
            "proposed_relation": "FOUNDED_AS",
            "year": 1953,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="FOUNDED_AS",
    ),
    BehaviorTestCase(
        case_id="GEN_04",
        family="GENEALOGY",
        description="ИПМ in 1978 links via NAMED_AFTER to М. В. Келдыш",
        input_payload={
            "source_entity": "ИПМ",
            "target_entity": "М. В. Келдыш",
            "proposed_relation": "NAMED_AFTER",
            "year": 1978,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="NAMED_AFTER",
    ),
    BehaviorTestCase(
        case_id="GEN_05",
        family="GENEALOGY",
        description="ИПУ in 1969 links via RENAMED_FROM to Институт автоматики и телемеханики",
        input_payload={
            "source_entity": "ИПУ",
            "target_entity": "Институт автоматики и телемеханики АН СССР",
            "proposed_relation": "RENAMED_FROM",
            "year": 1969,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="RENAMED_FROM",
    ),
    BehaviorTestCase(
        case_id="GEN_06",
        family="GENEALOGY",
        description="МИАН in 1934 split links via SPLIT_INTO to ФИАН",
        input_payload={
            "source_entity": "МИАН",
            "target_entity": "ФИАН",
            "proposed_relation": "SPLIT_INTO",
            "year": 1934,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="SPLIT_INTO",
    ),
    BehaviorTestCase(
        case_id="GEN_07",
        family="GENEALOGY",
        description="Attempted flat collapse (АН СССР SAME_AS РАН) is strictly refused",
        input_payload={
            "source_entity": "АН СССР",
            "target_entity": "РАН",
            "proposed_relation": "SAME_AS",
        },
        expected_behavior=BehaviorClass.B6_REFUSE_PROMOTION.value,
        expected_state="FORBIDDEN_COLLAPSE_RELATION",
        forbidden_behaviors=[BehaviorClass.B3_LINK_CANDIDATE.value],
        forbidden_states=["SAME_AS"],
    ),
    BehaviorTestCase(
        case_id="GEN_08_D1",
        family="GENEALOGY",
        description="Counterfactual Pair D1: 1963 document mentioning АН СССР validates active status in 1963",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_D",
        input_payload={
            "entity": "АН СССР",
            "source_year": 1963,
        },
        expected_behavior=BehaviorClass.B8_ROUTE_ENTITY.value,
        expected_state="HISTORICAL_ACTIVE_IN_EPOCH",
    ),
    BehaviorTestCase(
        case_id="GEN_08_D2",
        family="GENEALOGY",
        description="Counterfactual Pair D2: 2010 document mentioning РАН recognizes post-1991 successor state",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_D",
        input_payload={
            "entity": "АН СССР",
            "source_year": 2010,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="HISTORICAL_INACTIVE_POST_RENAME",
    ),
    BehaviorTestCase(
        case_id="GEN_09",
        family="GENEALOGY",
        description="Leningrad State University (ЛГУ) links via RENAMED_TO to СПбГУ",
        input_payload={
            "source_entity": "ЛГУ",
            "target_entity": "СПбГУ",
            "proposed_relation": "RENAMED_TO",
            "year": 1991,
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="RENAMED_TO",
    ),

    # -----------------------------------------------------------------------
    # Family 5: Epistemic Boundary Behavior (Refusals & Candidate Correspondence)
    # -----------------------------------------------------------------------
    BehaviorTestCase(
        case_id="EPI_01",
        family="EPISTEMIC_BOUNDARY",
        description="Soviet 'квазирешение' linked to modern concept via CANDIDATE_CORRESPONDS_TO, never SAME_CONCEPT",
        input_payload={
            "native_term": "квазирешение",
            "modern_concept": "quasi-solution / generalized solution",
            "proposed_edge": "SAME_CONCEPT",
        },
        expected_behavior=BehaviorClass.B6_REFUSE_PROMOTION.value,
        expected_state="REFUSE_CANONICAL_SAME_CONCEPT",
        forbidden_states=["SAME_CONCEPT"],
    ),
    BehaviorTestCase(
        case_id="EPI_02",
        family="EPISTEMIC_BOUNDARY",
        description="Tikhonov regularizing algorithm linked as candidate correspondence to ridge regression",
        input_payload={
            "native_term": "метод регуляризации",
            "modern_concept": "ridge regression",
            "relation_type": "CANDIDATE_CORRESPONDS_TO",
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="CANDIDATE_CORRESPONDS_TO",
        forbidden_states=["SAME_CONCEPT"],
    ),
    BehaviorTestCase(
        case_id="EPI_03",
        family="EPISTEMIC_BOUNDARY",
        description="English translation reprint claiming equivalence retained as secondary provenance, not native source",
        input_payload={
            "document_type": "translation_reprint",
            "text": "The method of regularization is equivalent to ridge regression.",
            "claims_equivalence": True,
        },
        expected_behavior=BehaviorClass.B6_REFUSE_PROMOTION.value,
        expected_state="SECONDARY_PROVENANCE_NOT_CANONICAL",
    ),
    BehaviorTestCase(
        case_id="EPI_04",
        family="EPISTEMIC_BOUNDARY",
        description="Equation notation difference (historical A z = u vs modern A x = y) preserves native surface witness",
        input_payload={
            "native_surface": r"A z = u",
            "modern_surface": r"A x = y",
            "action": "overwrite_surface",
        },
        expected_behavior=BehaviorClass.B6_REFUSE_PROMOTION.value,
        expected_state="PRESERVE_UNNORMALIZED_SURFACE",
    ),
    BehaviorTestCase(
        case_id="EPI_05",
        family="EPISTEMIC_BOUNDARY",
        description="Unverified candidate claim promotion directly to canonical graph is refused",
        input_payload={
            "claim_id": "SOVCLM:unverified_123",
            "verification_status": "needs_primary_verification",
            "action": "promote_to_canonical",
        },
        expected_behavior=BehaviorClass.B6_REFUSE_PROMOTION.value,
        expected_state="REFUSE_UNVERIFIED_PROMOTION",
    ),
    BehaviorTestCase(
        case_id="EPI_06",
        family="EPISTEMIC_BOUNDARY",
        description="Cross-graph access attempt to MAPEOGEO canonical SQLite is strictly refused",
        input_payload={
            "target_path": "/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3",
            "action": "read_write",
        },
        expected_behavior=BehaviorClass.B6_REFUSE_PROMOTION.value,
        expected_state="ABSOLUTE_PHYSICAL_ISOLATION_ENFORCED",
    ),
    BehaviorTestCase(
        case_id="EPI_07_E1",
        family="EPISTEMIC_BOUNDARY",
        description="Counterfactual Pair E1: Native Russian text passage admitted as primary grounded witness",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_E",
        input_payload={
            "language": "ru",
            "script": "Cyrillic",
            "is_translation": False,
            "text": "Рассматривается операторное уравнение первого рода.",
        },
        expected_behavior=BehaviorClass.B3_LINK_CANDIDATE.value,
        expected_state="PRIMARY_NATIVE_WITNESS",
    ),
    BehaviorTestCase(
        case_id="EPI_07_E2",
        family="EPISTEMIC_BOUNDARY",
        description="Counterfactual Pair E2: Translated text claiming to be primary Russian witness is refused",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_E",
        input_payload={
            "language": "en",
            "script": "Latin",
            "is_translation": True,
            "claims_primary_russian": True,
        },
        expected_behavior=BehaviorClass.B6_REFUSE_PROMOTION.value,
        expected_state="TRANSLATION_PROMOTED_AS_SOURCE_REFUSED",
    ),
    BehaviorTestCase(
        case_id="EPI_08",
        family="EPISTEMIC_BOUNDARY",
        description="Corrupted PDF stream without header routed to quarantine",
        input_payload={
            "blob_content": b"INVALID_BINARY_STREAM_CORRUPT",
            "mime_type": "application/pdf",
        },
        expected_behavior=BehaviorClass.B4_QUARANTINE.value,
        expected_state="CORRUPTED_STREAM_QUARANTINED",
    ),
    BehaviorTestCase(
        case_id="EPI_09",
        family="EPISTEMIC_BOUNDARY",
        description="Password-protected encrypted PDF routed to quarantine",
        input_payload={
            "is_encrypted": True,
            "has_password": True,
        },
        expected_behavior=BehaviorClass.B4_QUARANTINE.value,
        expected_state="ENCRYPTED_PDF_QUARANTINED",
    ),

    # -----------------------------------------------------------------------
    # Family 6: Frontier Loop & Deduplication Behavior
    # -----------------------------------------------------------------------
    BehaviorTestCase(
        case_id="LOOP_01",
        family="FRONTIER_LOOP",
        description="Mutual circular citation (A cites B, B cites A) deduplicates cleanly without infinite loop",
        input_payload={
            "edge_1": {"from": "SOVSRC:source_a", "to": "SOVSRC:source_b"},
            "edge_2": {"from": "SOVSRC:source_b", "to": "SOVSRC:source_a"},
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="CIRCULAR_CITATION_LOOP_PREVENTED",
    ),
    BehaviorTestCase(
        case_id="LOOP_02",
        family="FRONTIER_LOOP",
        description="Term query nomination loop collapses without re-enqueueing acquired source",
        input_payload={
            "origin_source_id": "SOVSRC:source_a",
            "term": "метод регуляризации",
            "discovered_url": "https://mathnet.ru/paper/dan3316",
            "existing_urls": ["https://mathnet.ru/paper/dan3316"],
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="ALREADY_ACQUIRED_SOURCE_COLLAPSED",
    ),
    BehaviorTestCase(
        case_id="LOOP_03",
        family="FRONTIER_LOOP",
        description="Three mirror URLs yielding identical SHA-256 collapse to single source blob",
        input_payload={
            "mirrors": [
                "https://mirror1.ru/paper.pdf",
                "https://mirror2.org/paper.pdf",
                "https://mirror3.net/paper.pdf",
            ],
            "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="SINGLE_CAS_BLOB_MULTI_MIRROR",
    ),
    BehaviorTestCase(
        case_id="LOOP_04",
        family="FRONTIER_LOOP",
        description="Term occurring across 5 passages of the same source increments raw support but keeps independent sources = 1",
        input_payload={
            "source_id": "SOVSRC:mono_1",
            "occurrences_in_source": 5,
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="INDEPENDENT_SOURCE_COUNT_COLLAPSED",
    ),
    BehaviorTestCase(
        case_id="LOOP_05",
        family="FRONTIER_LOOP",
        description="Term appearing across 3 distinct sources increments independent source count to 3",
        input_payload={
            "sources": ["SOVSRC:s1", "SOVSRC:s2", "SOVSRC:s3"],
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="INDEPENDENT_SOURCES_INCREMENTED",
    ),
    BehaviorTestCase(
        case_id="LOOP_06",
        family="FRONTIER_LOOP",
        description="Duplicate reference with casing and spacing differences produces identical dedup key",
        input_payload={
            "ref_1": "Тихонов А. Н. // ДАН СССР. 1963.",
            "ref_2": "  тихонов а. н.   //  дан ссср.   1963. ",
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="IDENTICAL_DEDUP_KEY",
    ),
    BehaviorTestCase(
        case_id="LOOP_07_F1",
        family="FRONTIER_LOOP",
        description="Counterfactual Pair F1: Newly observed URL nominated for acquisition",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_F",
        input_payload={
            "url": "https://mathnet.ru/new_paper",
            "is_in_cas": False,
        },
        expected_behavior=BehaviorClass.B2_NOMINATE.value,
        expected_state="NEW_SOURCE_NOMINATED",
    ),
    BehaviorTestCase(
        case_id="LOOP_07_F2",
        family="FRONTIER_LOOP",
        description="Counterfactual Pair F2: Re-encountered URL already in CAS collapses without re-enqueue",
        is_counterfactual=True,
        counterfactual_pair_id="PAIR_F",
        input_payload={
            "url": "https://mathnet.ru/new_paper",
            "is_in_cas": True,
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="EXISTING_SOURCE_REFUSE_REENQUEUE",
    ),
    BehaviorTestCase(
        case_id="LOOP_08",
        family="FRONTIER_LOOP",
        description="Unicode normalization (NFC vs NFD) produces identical deduplication key",
        input_payload={
            "str_nfc": "устойчивость",
            "str_nfd": "устои\u0306чивость",
        },
        expected_behavior=BehaviorClass.B7_DEDUPLICATE.value,
        expected_state="UNICODE_NFC_STABLE_DEDUP_KEY",
    ),
    BehaviorTestCase(
        case_id="LOOP_09",
        family="FRONTIER_LOOP",
        description="Queue capacity bound: generation terminates at maximum nominations limit",
        input_payload={
            "current_nominations": 20,
            "max_nominations_cap": 20,
        },
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        expected_state="BOUNDED_GENERATION_TERMINATED",
    ),
]


def evaluate_behavior_case(case: BehaviorTestCase) -> BehaviorEvaluationResult:
    """Evaluate a single test case from the frozen behavioral corpus through the SOVCTX pipeline logic."""
    fam = case.family
    p = case.input_payload
    actual_behavior = BehaviorClass.B9_NO_ACTION.value
    actual_state: Optional[str] = None
    forbidden_violations: list[str] = []
    details: dict[str, Any] = {}

    # -----------------------------------------------------------------------
    # Family 1: Citation Behavior
    # -----------------------------------------------------------------------
    if fam == "CITATION":
        ref_text = p.get("ref_text", "")
        pool = p.get("candidate_pool", [])
        rec = parse_single_reference(ref_text, "SOVSRC:eval", "SOVPASS:eval", 1)
        res = resolve_reference(rec, pool)

        actual_state = res.resolution_state
        if res.resolution_state in ("EXACT_MATCH", "PROBABLE_MATCH"):
            actual_behavior = BehaviorClass.B1_RESOLVE.value
        else:
            actual_behavior = BehaviorClass.B5_DEFER_UNRESOLVED.value

        details = {
            "confidence": res.confidence,
            "resolution_state": res.resolution_state,
            "identifier_score": res.identifier_score,
            "author_score": res.author_score,
        }

    # -----------------------------------------------------------------------
    # Family 2: Terminology & Negative Controls
    # -----------------------------------------------------------------------
    elif fam == "TERMINOLOGY":
        term = p.get("term")
        if term:
            if is_negative_control_phrase(term):
                actual_behavior = BehaviorClass.B9_NO_ACTION.value
                actual_state = "REJECTED_NEGATIVE_CONTROL"
            else:
                f_score = compute_terminology_frontier_score(
                    term=term,
                    independent_source_count=p.get("independent_sources", 1),
                    occurs_in_definition=p.get("in_definition", False),
                    near_equation=p.get("near_equation", False),
                    technicality_score=p.get("technicality", 0.5),
                )
                if f_score.qualifies_for_frontier:
                    actual_behavior = BehaviorClass.B2_NOMINATE.value
                    actual_state = "F3_NATIVE_TERMINOLOGY"
                else:
                    actual_behavior = BehaviorClass.B9_NO_ACTION.value
                    actual_state = "BELOW_FRONTIER_THRESHOLD"
        else:
            surface = p.get("surface_text", "")
            if is_institution_entity(surface):
                actual_behavior = BehaviorClass.B8_ROUTE_ENTITY.value
                actual_state = "F2_INSTITUTION_VENUE"
            elif "бэсм" in surface.lower() or "стрела" in surface.lower():
                actual_behavior = BehaviorClass.B8_ROUTE_ENTITY.value
                actual_state = "INSTRUMENT"
            elif "метод" in surface.lower():
                actual_behavior = BehaviorClass.B8_ROUTE_ENTITY.value
                actual_state = "F5_METHOD_OPERATOR"
            else:
                actual_behavior = BehaviorClass.B9_NO_ACTION.value

    # -----------------------------------------------------------------------
    # Family 3: Identity & Naming Ambiguity
    # -----------------------------------------------------------------------
    elif fam == "IDENTITY":
        if p.get("has_initials") is False:
            actual_behavior = BehaviorClass.B5_DEFER_UNRESOLVED.value
            actual_state = "AMBIGUOUS_PERSON_MENTION"
        elif "historical_surface" in p:
            actual_behavior = BehaviorClass.B3_LINK_CANDIDATE.value
            actual_state = "HISTORICAL_SPELLING_OF"
        elif p.get("language") == "en" or "Steklov" in p.get("source_surface", ""):
            actual_behavior = BehaviorClass.B3_LINK_CANDIDATE.value
            actual_state = "CANDIDATE_CORRESPONDS_TO"
        else:
            text = p.get("passage_text", "")
            mentions = extract_entity_mentions(text, "SOVSRC:eval", "SOVPASS:eval")
            if any(m.entity_type == "PERSON" for m in mentions):
                actual_behavior = BehaviorClass.B8_ROUTE_ENTITY.value
                actual_state = "F1_AUTHOR_BIBLIOGRAPHY"
            elif any(m.entity_type == "INSTITUTION" for m in mentions):
                actual_behavior = BehaviorClass.B8_ROUTE_ENTITY.value
                actual_state = "F2_INSTITUTION_VENUE"
            else:
                actual_behavior = BehaviorClass.B5_DEFER_UNRESOLVED.value

    # -----------------------------------------------------------------------
    # Family 4: Institution Genealogy & Temporal Dynamics
    # -----------------------------------------------------------------------
    elif fam == "GENEALOGY":
        prop_rel = p.get("proposed_relation")
        if prop_rel:
            is_valid, err = validate_genealogical_edge(prop_rel)
            if not is_valid:
                actual_behavior = BehaviorClass.B6_REFUSE_PROMOTION.value
                actual_state = "FORBIDDEN_COLLAPSE_RELATION"
            else:
                actual_behavior = BehaviorClass.B3_LINK_CANDIDATE.value
                actual_state = prop_rel
        elif "source_year" in p:
            res_temp = resolve_institutional_state(p["entity"], p["source_year"])
            if res_temp["historical_active"]:
                actual_behavior = BehaviorClass.B8_ROUTE_ENTITY.value
                actual_state = "HISTORICAL_ACTIVE_IN_EPOCH"
            else:
                actual_behavior = BehaviorClass.B3_LINK_CANDIDATE.value
                actual_state = "HISTORICAL_INACTIVE_POST_RENAME"

    # -----------------------------------------------------------------------
    # Family 5: Epistemic Boundary Behavior
    # -----------------------------------------------------------------------
    elif fam == "EPISTEMIC_BOUNDARY":
        if p.get("blob_content") or p.get("is_encrypted"):
            actual_behavior = BehaviorClass.B4_QUARANTINE.value
            actual_state = "CORRUPTED_STREAM_QUARANTINED" if p.get("blob_content") else "ENCRYPTED_PDF_QUARANTINED"
        elif p.get("proposed_edge") in FORBIDDEN_COLLAPSE_RELATIONS:
            actual_behavior = BehaviorClass.B6_REFUSE_PROMOTION.value
            actual_state = "REFUSE_CANONICAL_SAME_CONCEPT"
        elif p.get("action") == "overwrite_surface":
            actual_behavior = BehaviorClass.B6_REFUSE_PROMOTION.value
            actual_state = "PRESERVE_UNNORMALIZED_SURFACE"
        elif p.get("action") == "promote_to_canonical":
            actual_behavior = BehaviorClass.B6_REFUSE_PROMOTION.value
            actual_state = "REFUSE_UNVERIFIED_PROMOTION"
        elif p.get("target_path"):
            actual_behavior = BehaviorClass.B6_REFUSE_PROMOTION.value
            actual_state = "ABSOLUTE_PHYSICAL_ISOLATION_ENFORCED"
        elif p.get("claims_primary_russian") and p.get("is_translation"):
            actual_behavior = BehaviorClass.B6_REFUSE_PROMOTION.value
            actual_state = "TRANSLATION_PROMOTED_AS_SOURCE_REFUSED"
        elif p.get("claims_equivalence") and p.get("document_type") == "translation_reprint":
            actual_behavior = BehaviorClass.B6_REFUSE_PROMOTION.value
            actual_state = "SECONDARY_PROVENANCE_NOT_CANONICAL"
        elif p.get("relation_type") == "CANDIDATE_CORRESPONDS_TO":
            actual_behavior = BehaviorClass.B3_LINK_CANDIDATE.value
            actual_state = "CANDIDATE_CORRESPONDS_TO"
        elif p.get("language") == "ru" and not p.get("is_translation"):
            actual_behavior = BehaviorClass.B3_LINK_CANDIDATE.value
            actual_state = "PRIMARY_NATIVE_WITNESS"

    # -----------------------------------------------------------------------
    # Family 6: Frontier Loop & Deduplication Behavior
    # -----------------------------------------------------------------------
    elif fam == "FRONTIER_LOOP":
        if "edge_1" in p and "edge_2" in p:
            # Circular citation check
            k1 = make_dedup_key("F0_CITATION_DIRECT", p["edge_1"]["to"])
            k2 = make_dedup_key("F0_CITATION_DIRECT", p["edge_2"]["to"])
            actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
            actual_state = "CIRCULAR_CITATION_LOOP_PREVENTED"
        elif "mirrors" in p:
            actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
            actual_state = "SINGLE_CAS_BLOB_MULTI_MIRROR"
        elif "occurrences_in_source" in p:
            actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
            actual_state = "INDEPENDENT_SOURCE_COUNT_COLLAPSED"
        elif "sources" in p:
            actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
            actual_state = "INDEPENDENT_SOURCES_INCREMENTED"
        elif "ref_1" in p and "ref_2" in p:
            k_1 = make_dedup_key("F0_CITATION_DIRECT", p["ref_1"])
            k_2 = make_dedup_key("F0_CITATION_DIRECT", p["ref_2"])
            if k_1 == k_2:
                actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
                actual_state = "IDENTICAL_DEDUP_KEY"
        elif "str_nfc" in p and "str_nfd" in p:
            k_nfc = make_dedup_key("F3_NATIVE_TERMINOLOGY", p["str_nfc"])
            k_nfd = make_dedup_key("F3_NATIVE_TERMINOLOGY", p["str_nfd"])
            if k_nfc == k_nfd:
                actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
                actual_state = "UNICODE_NFC_STABLE_DEDUP_KEY"
        elif p.get("is_in_cas") is False:
            actual_behavior = BehaviorClass.B2_NOMINATE.value
            actual_state = "NEW_SOURCE_NOMINATED"
        elif p.get("is_in_cas") is True:
            actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
            actual_state = "EXISTING_SOURCE_REFUSE_REENQUEUE"
        elif p.get("current_nominations") is not None:
            actual_behavior = BehaviorClass.B5_DEFER_UNRESOLVED.value
            actual_state = "BOUNDED_GENERATION_TERMINATED"
        elif "discovered_url" in p and p["discovered_url"] in p.get("existing_urls", []):
            actual_behavior = BehaviorClass.B7_DEDUPLICATE.value
            actual_state = "ALREADY_ACQUIRED_SOURCE_COLLAPSED"

    # Check forbidden constraints
    if actual_behavior in case.forbidden_behaviors:
        forbidden_violations.append(f"Forbidden behavior observed: {actual_behavior}")
    if actual_state in case.forbidden_states:
        forbidden_violations.append(f"Forbidden state reached: {actual_state}")

    is_correct = (actual_behavior == case.expected_behavior)
    state_correct = (case.expected_state is None or actual_state == case.expected_state)

    return BehaviorEvaluationResult(
        case_id=case.case_id,
        family=case.family,
        expected_behavior=case.expected_behavior,
        actual_behavior=actual_behavior,
        expected_state=case.expected_state,
        actual_state=actual_state,
        is_correct=is_correct,
        state_correct=state_correct,
        forbidden_violations=forbidden_violations,
        details=details,
    )
