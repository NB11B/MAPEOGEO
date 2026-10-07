"""Unit tests for literal 6-coordinate work grammar M_6."""

from __future__ import annotations

from mapeogeo.grammar.coordinates import (
    KERNEL_GRAMMAR_DIMENSION,
    CanonicalCoordinate,
    WitnessCertificate,
)
from mapeogeo.grammar.work_grammar import WorkGrammar


def test_grammar_dimension_invariant() -> None:
    grammar = WorkGrammar(base_alphabet_size=58)
    assert grammar.dimension == 6
    assert grammar.dimension == KERNEL_GRAMMAR_DIMENSION
    assert len(grammar.coordinates) == 6
    assert CanonicalCoordinate.DELTA in grammar.coordinates
    assert CanonicalCoordinate.GENERATOR in grammar.coordinates


def test_witness_extension_increments_alphabet() -> None:
    grammar = WorkGrammar(base_alphabet_size=58)
    assert grammar.alphabet_size == 58
    assert grammar.delta_a_w == 0

    w1 = grammar.register_witness("wit_trace", "Tr", "Trace certificate")
    assert isinstance(w1, WitnessCertificate)
    assert grammar.alphabet_size == 59
    assert grammar.delta_a_w == 1

    # Idempotent registration
    w1_dup = grammar.register_witness("wit_trace", "Tr", "Trace certificate")
    assert w1_dup == w1
    assert grammar.alphabet_size == 59


def test_semantic_drift_auditor_rejects_relabeling() -> None:
    grammar = WorkGrammar()

    # Rejection of relabeling Gamma as 'connection'
    drift_attempt_gamma = {"Gamma": "affine_connection_operator"}
    is_valid, violations = grammar.audit_coordinate_semantics(drift_attempt_gamma)
    assert not is_valid
    assert any("Semantic drift rejected on Gamma" in v for v in violations)

    # Rejection of relabeling sigma as 'symmetry_group'
    drift_attempt_sigma = {"sigma": "symmetry_group_gauge"}
    is_valid, violations = grammar.audit_coordinate_semantics(drift_attempt_sigma)
    assert not is_valid
    assert any("Semantic drift rejected on sigma" in v for v in violations)

    # Valid literal semantics pass
    literal_meanings = {"Gamma": "generator / transition", "sigma": "structure / topology"}
    is_valid, violations = grammar.audit_coordinate_semantics(literal_meanings)
    assert is_valid
    assert len(violations) == 0
