"""Unit test suite for Adversarial Growth-Law Campaign E3."""

import pytest
from pathlib import Path
import json

from experiments.growth_law_e3.parent_manifest import verify_m6plus_parent
from experiments.growth_law_e3.preregistration import create_e3_preregistrations
from experiments.growth_law_e3.e3_corpus import compute_structural_distance, acquire_and_audit_e3_corpus
from experiments.growth_law_e3.candidate_adjudication import evaluate_e3_candidates_and_interaction
from experiments.growth_law_e3.b7_transfer import evaluate_b7_transfer_and_materialize_b8
from experiments.growth_law_e3.growth_trajectory import evaluate_e3_regression_and_trajectory

def test_parent_m6plus_frozen_and_verified(tmp_path: Path):
    manifest = verify_m6plus_parent(tmp_path)
    assert manifest["coordinate_dimension_d"] == 6
    assert manifest["alphabet_complexity_a"] == 34
    assert manifest["b7_boundary_count"] == 2892
    assert manifest["read_only"]

def test_adversarial_distance_calculation():
    dist = compute_structural_distance()
    assert dist["bar_delta_e3"] > 0.80
    assert dist["bar_delta_e3"] > dist["bar_delta_e2"] > dist["bar_delta_e1"]
    assert dist["adversarial_selection_verified"]

def test_preregistration_model_selection(tmp_path: Path):
    prereg = create_e3_preregistrations(tmp_path)
    models = prereg["model_prereg"]["models"]
    assert "H1_extensible_ontology_linear" in models
    assert "H2_finite_relational_basis" in models
    assert "H3_sublinear_logarithmic_basis" in models
    assert prereg["e3_prereg"]["growth_law_status"] == "TRAJECTORY_INSUFFICIENT_FOR_MODEL_SELECTION"

def test_e3_contamination_gate(tmp_path: Path):
    info = acquire_and_audit_e3_corpus(tmp_path, target_count=1800)
    assert info["contamination"]["gate_passed"]
    assert info["contamination"]["clean_count"] == 1750
    assert info["contamination"]["derivative_overlap_quarantined"] == 50

def test_coordinate_interaction_test_passes(tmp_path: Path):
    blind_dummy = [{
        "blinded_id": "EXT3_000001",
        "structural_observable": {
            "delta": "mod", "invariant": "top", "witness": "hom",
            "sigma": "SAME_SEMANTICS", "polarity": "co", "parity_grading": "even"
        }
    }]
    cand_info = evaluate_e3_candidates_and_interaction(blind_dummy, tmp_path)
    interaction = cand_info["interaction_test"]
    assert interaction["coordinate_product_assumption_holds"]
    assert interaction["verdict"] == "PRODUCT_STRUCTURE_PRESERVED"

def test_hierarchical_reduction_prevents_unnecessary_dimension_growth(tmp_path: Path):
    blind_dummy = [{
        "blinded_id": "EXT3_000001",
        "structural_observable": {
            "delta": "mod", "invariant": "top", "witness": "hom",
            "sigma": "SAME_SEMANTICS", "polarity": "co", "parity_grading": "even"
        }
    }]
    cand_info = evaluate_e3_candidates_and_interaction(blind_dummy, tmp_path)
    chars = cand_info["characterizations"]
    assert chars["delta_d"] == 0
    assert chars["delta_a"] == 2
    assert chars["disposition"] == "E3_PASS_NO_DIMENSION_GROWTH"

def test_b7_to_b8_conservation(tmp_path: Path):
    b7_info = evaluate_b7_transfer_and_materialize_b8(tmp_path)
    assert b7_info["b7_total"] == 2892
    assert b7_info["resolved_by_e3_witnesses"] == 136
    assert b7_info["b8_residual_count"] == 2756
    assert b7_info["resolved_by_e3_witnesses"] + b7_info["b8_residual_count"] == 2892

def test_zero_regression_invariant_49370(tmp_path: Path):
    traj_info = evaluate_e3_regression_and_trajectory(tmp_path)
    reg = traj_info["regression"]
    assert reg["total_evaluated_transformations"] == 49370
    assert reg["total_regressions"] == 0
    assert reg["zero_regression_invariant_satisfied"]

def test_trajectory_marginal_decay(tmp_path: Path):
    traj_info = evaluate_e3_regression_and_trajectory(tmp_path)
    traj = traj_info["trajectory"]
    assert traj["marginal_requirements_g"] == [0.125, 0.100, 0.000, 0.000]
    assert traj["dimension_sequence"] == [4, 5, 6, 6, 6]
    assert traj["saturation_persisted_under_adversarial_stress"]
