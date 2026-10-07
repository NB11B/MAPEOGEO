"""Unit test suite for Residual Coordinate Factorization Campaign."""

import pytest
from experiments.residual_analysis.depth_control import evaluate_depth_resolution
from experiments.residual_analysis.composition_audit import audit_compositional_factorization
from experiments.residual_analysis.coordinate_discovery import (
    compute_entropy,
    compute_conditional_entropy,
    evaluate_candidate_coordinate
)
from experiments.residual_analysis.coordinate_adjudication import adjudicate_candidate

def test_depth_resolution():
    sample_collisions = [
        {"id": "c1", "resolution_depth": 5},
        {"id": "c2", "resolution_depth": 6},
        {"id": "c3", "resolution_depth": 7},
    ]
    res = evaluate_depth_resolution(sample_collisions, max_k=6)
    assert res["total_k4_collisions"] == 3
    assert res["resolved_at_k5"] == 1
    assert res["resolved_at_k6"] == 1
    assert res["remaining_persistent_collisions"] == 1
    assert abs(res["depth_resolution_rate"] - (2 / 3)) < 1e-4

def test_composition_factoring():
    table = {
        "P1": {"P2": "DEFINED"},
        "P2": {"P3": "FORBIDDEN"}
    }
    transitions = [
        {"id": "t1", "factors": ["P1", "P2"]},
        {"id": "t2", "factors": ["P2", "P3"]},
        {"id": "t3", "factors": []}
    ]
    res = audit_compositional_factorization(transitions, table)
    assert res["total_audited"] == 3
    assert res["factored_composites_count"] == 1
    assert res["unfactorable_count"] == 2

def test_entropy_and_mutual_information():
    labels = ["A", "A", "B", "B"]
    ent = compute_entropy(labels)
    assert abs(ent - 1.0) < 1e-4

    # Perfect predictor
    cond_keys = [(1,), (1,), (2,), (2,)]
    cond_ent = compute_conditional_entropy(labels, cond_keys)
    assert abs(cond_ent - 0.0) < 1e-4

def test_coordinate_discovery_eval():
    residuals = [
        {"delta": "d1", "invariant": "i1", "witness": "w1", "sigma": "s1", "coord": "c1", "error_class": "e1"},
        {"delta": "d1", "invariant": "i1", "witness": "w1", "sigma": "s1", "coord": "c2", "error_class": "e2"},
        {"delta": "d2", "invariant": "i2", "witness": "w2", "sigma": "s2", "coord": "c1", "error_class": "e1"},
        {"delta": "d2", "invariant": "i2", "witness": "w2", "sigma": "s2", "coord": "c2", "error_class": "e2"},
    ]
    eval_res = evaluate_candidate_coordinate(residuals, "coord")
    assert eval_res["incremental_mutual_information_bits"] > 0
    assert eval_res["relative_entropy_reduction"] > 0.5

def test_adjudicate_candidate_strict_pass():
    cand_eval = {
        "candidate_coordinate": "test_coord",
        "relative_entropy_reduction": 0.35,
        "incremental_mutual_information_bits": 0.60
    }
    domains = {"dom1": 20, "dom2": 20, "dom3": 20, "dom4": 20}
    res = adjudicate_candidate(
        candidate_eval=cand_eval,
        domain_distribution=domains,
        projections_improved=["P1", "P2"],
        control_shuffled_mi=0.005,
        holdout_mi=0.55,
        false_semantic_promotions=0,
        persists_at_k5=True,
        mathematical_interpretation="Clear structural interpretation of operation."
    )
    assert res["verdict"] == "ACCEPTED_C5"
    assert res["gates"]["G1_entropy_reduction_material"]["passed"]
    assert res["gates"]["G6_semantic_safety_zero_promotions"]["passed"]

def test_adjudicate_candidate_rejection_on_controls():
    cand_eval = {
        "candidate_coordinate": "spurious_coord",
        "relative_entropy_reduction": 0.25,
        "incremental_mutual_information_bits": 0.30
    }
    domains = {"dom1": 20, "dom2": 20, "dom3": 20, "dom4": 20}
    # Fails control because shuffled MI is high
    res = adjudicate_candidate(
        candidate_eval=cand_eval,
        domain_distribution=domains,
        projections_improved=["P1", "P2"],
        control_shuffled_mi=0.15,  # high shuffled MI!
        holdout_mi=0.28,
        false_semantic_promotions=0,
        persists_at_k5=True,
        mathematical_interpretation="Spurious label."
    )
    assert res["verdict"] == "REJECTED_COORDINATE"
    assert not res["gates"]["G4_shuffled_controls_resisted"]["passed"]
