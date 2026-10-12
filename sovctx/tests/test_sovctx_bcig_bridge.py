#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-BCIG-1: Cybernetic-Bionic Methodological Architecture Bridge.

Verifies:
1. Cross-graph architecture mapping (7 historical + 3 predicted = 10 architectures).
2. Bridge relations ontology (REALIZES_METHOD_PRIMITIVE, ARCHITECTURAL_MANIFESTATION_OF).
3. Question-sufficient reduction and negative information definitions on all architectures.
4. Cross-graph methodological grammar concordance (100% compliance with M6.2 matrix).
5. Unbuilt synthetic predicted architectures (structural synthesis, historical barriers, modern embodiments).
"""

import pytest
from sovctx.node.cybernetic_bionic_bridge_engine import (
    BcigBridgeSummaryReport,
    CyberneticBionicBridgeEngine,
)


@pytest.fixture(scope="module")
def bcig_summary() -> BcigBridgeSummaryReport:
    engine = CyberneticBionicBridgeEngine()
    return engine.evaluate_bridge_grammar_concordance()


def test_bcig_engine_initialization(bcig_summary: BcigBridgeSummaryReport):
    """Verifies that 10 total architectures are mapped (7 historical, 3 predicted)."""
    assert bcig_summary.total_architectures_mapped == 10
    assert bcig_summary.historical_architectures_count == 7
    assert bcig_summary.predicted_architectures_count == 3
    assert bcig_summary.total_bridge_relations >= 50


def test_bcig_cross_graph_relations(bcig_summary: BcigBridgeSummaryReport):
    """Verifies that cross-graph relations connect architectures to methodological primitives."""
    rel_dist = bcig_summary.relation_type_distribution
    assert "REALIZES_METHOD_PRIMITIVE" in rel_dist
    assert "ARCHITECTURAL_MANIFESTATION_OF" in rel_dist

    # Verify coverage across essential primitives
    coverage = bcig_summary.primitive_realization_coverage
    for sym in ["Ax", "Sr", "N", "I", "C", "Ad", "Iv", "Sa", "Sc", "Ii"]:
        assert sym in coverage, f"Primitive {sym} not realized in any cybernetic/bionic architecture"


def test_bcig_question_sufficient_state(bcig_summary: BcigBridgeSummaryReport):
    """
    Verifies that all historical architectures define question-sufficient state
    and negative information (what need not be modeled).
    """
    for arch in bcig_summary.architectures:
        assert len(arch.question_sufficient_reduction) > 20
        assert len(arch.what_is_ignored_as_irrelevant) > 20
        assert len(arch.operational_sequence) >= 3


def test_bcig_grammar_concordance(bcig_summary: BcigBridgeSummaryReport):
    """
    Verifies that operational sequences of cybernetic architectures
    satisfy the M6.2 Noncommutative Grammar Matrix.
    """
    assert bcig_summary.grammar_concordance_rate == 1.0
    assert bcig_summary.high_gamma_epistemic_matches >= 3


def test_bcig_predicted_unbuilt_architectures(bcig_summary: BcigBridgeSummaryReport):
    """
    Verifies that predicted unbuilt architectures specify valid compositions,
    historical barriers, and modern edge-intelligence embodiments.
    """
    preds = bcig_summary.predicted_architectures
    assert len(preds) == 3

    pred_ids = {p.prediction_id for p in preds}
    expected_ids = {
        "PRED_ARCH_ALPHA_DUAL_REGULARIZED_SYNERGISTIC_OBSERVER",
        "PRED_ARCH_BETA_SELF_CONSISTENT_VIABILITY_AUTOMATON",
        "PRED_ARCH_GAMMA_INDUCTIVE_TOPOLOGICAL_HOMEOSTAT",
    }
    assert pred_ids == expected_ids

    for p in preds:
        assert len(p.predicted_primitive_composition) >= 4
        assert len(p.structural_synthesis_rationale) > 30
        assert len(p.unbuilt_historical_barrier) > 30
        assert len(p.potential_modern_embodiment) > 30
