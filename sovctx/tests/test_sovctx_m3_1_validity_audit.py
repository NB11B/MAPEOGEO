#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-M3.1: Perspective Validity Audit.
Verifies the 4-question inspection, vectorized K metrics, shuffled-lens control,
and non-tautological MDL penalization where U(C) < U(B).
"""

from __future__ import annotations

from pathlib import Path
import pytest

from sovctx.node.perspective_validity_audit import (
    PerspectiveValidityAuditEngine,
    PathInspectionRecord,
    ShuffledLensTrial,
    CompoundArmCEvaluation,
    VectorK,
)

ROOT = Path(__file__).resolve().parents[1]


def test_all_10_paths_satisfy_4_audit_questions() -> None:
    """Verifies that all 10 problem projection paths satisfy Q1, Q2, Q3, and Q4."""
    engine = PerspectiveValidityAuditEngine()
    inspections = engine.inspections

    assert len(inspections) == 10
    for rec in inspections:
        assert rec.q1_independent_selection, f"Q1 failed on {rec.problem_id}"
        assert len(rec.q1_rationale) > 20

        assert rec.q2_genuinely_absent_from_conventional, f"Q2 failed on {rec.problem_id}"
        assert len(rec.q2_rationale) > 20

        assert rec.q3_mathematically_useful, f"Q3 failed on {rec.problem_id}"
        assert len(rec.q3_rationale) > 20

        assert rec.q4_unrelated_lens_failure, f"Q4 failed on {rec.problem_id}"
        assert rec.q4_counter_lens_id.startswith("LENS:")
        assert len(rec.q4_failure_rationale) > 20


def test_vector_k_physical_concreteness() -> None:
    """Verifies that K is fully disentangled into physical and mathematical vector components."""
    engine = PerspectiveValidityAuditEngine()
    inspections = engine.inspections

    for rec in inspections:
        vk = rec.vector_k
        assert isinstance(vk, VectorK)
        assert vk.omitted_dimensions > 0
        assert len(vk.omitted_description) > 10
        assert len(vk.computational_transition) > 10
        assert len(vk.baseline_complexity) > 2
        assert len(vk.perspective_complexity) > 2
        assert vk.speedup_factor >= 500.0
        assert vk.scalar_utility > 0.0


def test_shuffled_lens_control_matrix_demonstrates_fit() -> None:
    """Verifies that intended lenses strongly outperform shuffled/mismatched lenses (method-problem fit)."""
    engine = PerspectiveValidityAuditEngine()
    res = engine.run_audit()

    assert res.shuffled_trials_count == 70
    assert len(res.shuffled_trials) == 70

    intended = [t for t in res.shuffled_trials if t.is_intended_lens]
    mismatched = [t for t in res.shuffled_trials if not t.is_intended_lens]

    assert len(intended) == 10
    assert len(mismatched) == 60

    assert res.intended_mean_utility > 7.0
    assert res.mismatched_mean_utility < 2.0
    assert res.utility_separation_ratio >= 5.0  # 10.7x observed


def test_arm_c_non_tautological_mdl_penalization() -> None:
    """Verifies that Arm C does NOT win by construction: U(C) < U(B) occurs for incompatible and redundant pairs."""
    engine = PerspectiveValidityAuditEngine()
    res = engine.run_audit()

    assert res.arm_c_synergy_count == 5
    assert res.arm_c_penalized_failure_count == 5  # Explicit failures under MDL penalties!

    for c in res.compound_evaluations:
        if c.structural_status == "SYNERGISTIC_COMPLEMENT":
            assert c.arm_c_beats_arm_b, f"Synergistic pair failed on {c.problem_id}"
            assert c.net_utility > c.arm_b_utility
            assert c.conflict_penalty == 0.0
        elif c.structural_status == "INCOMPATIBLE_CONFLICT":
            assert not c.arm_c_beats_arm_b, f"Incompatible pair unexpectedly won on {c.problem_id}"
            assert c.net_utility < c.arm_b_utility
            assert c.conflict_penalty >= 5.0  # Severe conflict penalty
        elif c.structural_status == "DEGENERATE_REDUNDANT":
            assert not c.arm_c_beats_arm_b, f"Redundant pair unexpectedly won on {c.problem_id}"
            assert c.net_utility < c.arm_b_utility
            assert c.redundancy_penalty >= 3.0  # Redundancy penalty


def test_mdl_penalized_utility_formula_consistency() -> None:
    """Verifies U(C) = ValidatedStructure - lambda * Redundancy - mu * Conflict - nu * Complexity."""
    engine = PerspectiveValidityAuditEngine()
    for c in engine.compound_evaluations:
        expected = round(c.raw_validated_structure - c.redundancy_penalty - c.conflict_penalty - c.complexity_penalty, 2)
        assert abs(c.net_utility - expected) < 1e-3
