from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sovctx.node.config import NanoConfig
from sovctx.node.equation_witness import extract_equation_witnesses_from_passage
from sovctx.node.morphology import (
    analyze_russian_word,
    detect_historical_orthography,
    make_lemma_id,
    modern_spelling_from_historical,
)
from sovctx.node.notation import extract_symbol_occurrences
from sovctx.node.passages import PassageRecord
from sovctx.node.term_occurrence import extract_occurrences_from_passage, split_sentences
from sovctx.node.terminology import (
    NativeTerm,
    compute_technicality,
    make_definition_id,
    make_occurrence_id,
    make_term_id,
)
from sovctx.node.terminology_ingest import TerminologyExtractor
from sovctx.node.work_db import WorkDatabase
from sovctx.tools.qualify_n15 import run_n15_qualification


def test_term_identity_and_surface_separation() -> None:
    # 1. Same stem, different inflections must have distinct term IDs
    id_sg = make_term_id("пространство", "ru")
    id_pl = make_term_id("пространства", "ru")
    assert id_sg != id_pl

    # 2. Case insensitive normalized unicode
    id_lower = make_term_id("ляпунов", "ru")
    id_upper = make_term_id("Ляпунов", "ru")
    assert id_lower == id_upper

    # 3. Short I vs Simple I must never collapse
    id_short_i = make_term_id("устойчивый", "ru")
    id_simple_i = make_term_id("устоичивый", "ru")
    assert id_short_i != id_simple_i


def test_historical_russian_orthography() -> None:
    archaic = "О движеніи твердаго тѣла около неподвижной точки. Ѳеодоръ."
    assert detect_historical_orthography(archaic) is True

    # Pre-reform characters preserved in surface
    terms, occs, _ = extract_occurrences_from_passage("SOVPASS:t1", "SOVSRC:s1", archaic)
    surfs = {t.surface_form for t in terms}
    assert "тѣла" in surfs
    assert "движеніи" in surfs
    assert "Ѳеодоръ" in surfs

    # Candidate modern spelling derivation
    assert modern_spelling_from_historical("тѣла") == "тела"
    assert modern_spelling_from_historical("движеніи") == "движении"
    assert modern_spelling_from_historical("твердаго") == "твердого"
    assert modern_spelling_from_historical("законъ") == "закон"


def test_sentence_splitting_abbreviation_protection() -> None:
    text = "Институт им. Стеклова АН СССР выпустил труды. Рассматривается ур. движения, т.е. dx/dt = v."
    sentences = split_sentences(text)
    # Must NOT split on "им.", "АН СССР", "ур.", "т.е."
    assert len(sentences) == 2
    assert "им. Стеклова" in sentences[0][2]
    assert "т.е." in sentences[1][2]


def test_multiword_technical_phrase_extraction() -> None:
    text = "Основное уравнение движения описывает электромагнитное поле."
    terms, occs, contains = extract_occurrences_from_passage("SOVPASS:t2", "SOVSRC:s2", text)

    compound_terms = [t for t in terms if t.term_type == "compound_phrase"]
    assert len(compound_terms) >= 1
    assert any("электромагнитное поле" in t.surface_form.lower() for t in compound_terms)

    # Subterms linked
    assert len(contains) >= 1


def test_symbol_extraction_no_meaning_assumption() -> None:
    text = "Пусть V(x) - функция Ляпунова, а Ф - поток."
    symbols = extract_symbol_occurrences(text, "SOVSRC:s3", "SOVPASS:t3")

    sym_names = {s.symbol for s in symbols}
    assert "V(x)" in sym_names or "x" in sym_names
    assert "Ф" in sym_names

    # Invariant: meaning_candidate is None
    for s in symbols:
        assert s.meaning_candidate is None


def test_equation_witnesses_preservation() -> None:
    text = "Рассматривается одномерное волновое уравнение:\nu_tt - c^2 u_xx = 0, c = const. (1)"
    witnesses = extract_equation_witnesses_from_passage(text, "SOVSRC:s4", "SOVPASS:t4", 1)
    assert len(witnesses) >= 1
    assert witnesses[0].locator == "(1)"
    assert "u_tt - c^2 u_xx = 0" in witnesses[0].surface_representation


def test_n15_full_qualification_matrix() -> None:
    res = run_n15_qualification()
    assert res["verdict"] == "PASS"
    assert res["total_cases"] == 16
    assert all(v == 0 for v in res["invariants"].values())
