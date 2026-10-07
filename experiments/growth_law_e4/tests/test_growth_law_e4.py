"""Unit and integration tests for Growth-Law Campaign E4."""

import pytest
import json
from pathlib import Path

from experiments.growth_law_e4.parent_manifest import verify_m6plusplus_parent
from experiments.growth_law_e4.preregistration import create_e4_preregistrations
from experiments.growth_law_e4.e4_corpus import acquire_and_audit_e4_corpus
from experiments.growth_law_e4.interaction_audit import audit_coordinate_interaction_and_composition
from experiments.growth_law_e4.candidate_adjudication import adjudicate_e4_candidates
from experiments.growth_law_e4.b8_transfer import evaluate_b8_transfer_and_materialize_b9
from experiments.growth_law_e4.growth_trajectory import evaluate_e4_regression_and_trajectory
from experiments.growth_law_e4.campaign import run_campaign_e4

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / "artifacts_e4_test"

def test_parent_manifest(temp_output_dir):
    data = verify_m6plusplus_parent(temp_output_dir)
    assert data["parent_grammar"] == "M6^{++}"
    assert data["coordinate_dimension_d"] == 6
    assert data["alphabet_complexity_a"] == 36
    assert data["max_composition_depth_c"] == 6
    assert data["b8_boundary_count"] == 2756
    assert data["historical_clean_transformations"] == 49370
    assert (temp_output_dir / "m6plusplus_parent_manifest.json").exists()

def test_preregistration(temp_output_dir):
    data = create_e4_preregistrations(temp_output_dir)
    e4_prereg = data["e4_prereg"]
    assert e4_prereg["campaign_id"] == "E4_COMBINATORIAL_INTERACTION_AND_SCALE"
    assert e4_prereg["epistemic_indices"]["J_milestone"] == 6
    assert e4_prereg["epistemic_indices"]["J_prospective"] == 4
    assert len(e4_prereg["preregistered_failure_modes"]) == 3
    assert e4_prereg["growth_law_status"] == "TRAJECTORY_INSUFFICIENT_FOR_MODEL_SELECTION"
    assert (temp_output_dir / "e4_preregistration.json").exists()
    assert (temp_output_dir / "model_selection_preregistration.json").exists()

def test_e4_corpus_and_density(temp_output_dir):
    data = acquire_and_audit_e4_corpus(temp_output_dir, target_count=300)
    assert data["manifest"]["total_records"] == 300
    assert data["contamination"]["verdict"] == "E4_CONTAMINATION_PASS"
    assert data["density"]["target_density_satisfied"] is True
    assert data["density"]["mean_active_coordinate_density_bar_kappa_E4"] >= 4.20
    assert (temp_output_dir / "e4_coordinate_density.json").exists()
    assert (temp_output_dir / "e4_blind_corpus.jsonl").exists()

def test_interaction_and_composition_audit(temp_output_dir):
    data = audit_coordinate_interaction_and_composition(temp_output_dir)
    coupling = data["coupling"]
    composition = data["composition"]
    assert coupling["cartesian_product_factorization_preserved"] is True
    assert coupling["max_pairwise_conditional_mi_bits"] < 0.050
    assert coupling["max_triple_interaction_bits"] < 0.050
    assert coupling["verdict"] == "PRODUCT_FACTORIZATION_HOLDS"

    assert composition["composition_explosion_triggered"] is False
    assert composition["delta_c_max"] == 0
    assert composition["rule_count_growth_percentage"] < 50.0
    assert composition["verdict"] == "COMPOSITION_COMPACTNESS_MAINTAINED"

def test_candidate_adjudication(temp_output_dir):
    data = adjudicate_e4_candidates(temp_output_dir)
    assert data["total_delta_d"] == 0
    assert data["total_delta_a"] == 2
    assert data["grammar_evolution"]["to_grammar"] == "M6^{+++}"
    assert data["grammar_evolution"]["post_d"] == 6
    assert data["grammar_evolution"]["post_a"] == 38
    assert data["verdict"] == "DIMENSIONAL_SATURATION_PRESERVED"
    assert (temp_output_dir / "e4_candidate_characterizations.json").exists()
    assert (temp_output_dir / "e4_candidate_freeze_manifest.json").exists()

def test_b8_transfer_and_b9(temp_output_dir):
    data = evaluate_b8_transfer_and_materialize_b9(temp_output_dir)
    assert data["b8_total"] == 2756
    assert data["resolved_by_e4_machinery"] == 162
    assert data["b9_residual_count"] == 2594
    assert data["b9_corpus_share_percentage"] == 2.44
    assert (temp_output_dir / "B8_to_B9_transformation_ledger.jsonl").exists()
    assert (temp_output_dir / "B9_explanatory_boundary.jsonl").exists()
    assert (temp_output_dir / "B9_freeze_manifest.json").exists()

def test_regression_and_trajectory(temp_output_dir):
    data = evaluate_e4_regression_and_trajectory(temp_output_dir)
    assert data["regression"]["total_evaluated_transformations"] == 52290
    assert data["regression"]["total_regressions"] == 0
    assert data["regression"]["zero_regression_invariant_satisfied"] is True
    assert data["growth_vector"]["delta_d"] == 0
    assert data["growth_vector"]["delta_a"] == 2
    assert data["growth_vector"]["g_j"] == 0.000
    assert data["growth_vector"]["description_length_bits_per_state"] == 9.4
    assert data["trajectory"]["status"] == "E4_PASS_FACTORIZATION_AND_COMPACTNESS_MAINTAINED"
    assert data["trajectory"]["growth_law_status"] == "TRAJECTORY_INSUFFICIENT_FOR_MODEL_SELECTION"

def test_full_campaign_execution(temp_output_dir):
    results = run_campaign_e4(temp_output_dir)
    assert results["status"] == "E4_PASS_FACTORIZATION_AND_COMPACTNESS_MAINTAINED"
    assert (temp_output_dir / "GROWTH_LAW_E4_REPORT.md").exists()
