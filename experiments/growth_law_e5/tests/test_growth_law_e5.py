"""Unit and integration tests for Growth-Law Campaign E5."""

import pytest
import json
from pathlib import Path

from experiments.growth_law_e5.parent_manifest import verify_m6plusplusplus_parent
from experiments.growth_law_e5.model_selection_freeze import freeze_model_selection_protocol
from experiments.growth_law_e5.preregistration import create_e5_preregistrations
from experiments.growth_law_e5.extractors import EXTRACTOR_REGISTRY
from experiments.growth_law_e5.e5_corpus import acquire_and_audit_e5_corpus
from experiments.growth_law_e5.representation_audit import audit_representation_invariance
from experiments.growth_law_e5.interaction_and_composition_audit import audit_e5_interaction_and_composition
from experiments.growth_law_e5.candidate_adjudication import adjudicate_e5_candidates
from experiments.growth_law_e5.b9_transfer import evaluate_b9_transfer_and_materialize_b10
from experiments.growth_law_e5.regression_audit import audit_e5_regression
from experiments.growth_law_e5.model_selection_runner import execute_model_selection
from experiments.growth_law_e5.campaign import run_campaign_e5

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / "artifacts_e5_test"

def test_parent_manifest(temp_output_dir):
    data = verify_m6plusplusplus_parent(temp_output_dir)
    assert data["parent_grammar"] == "M6^{+++}"
    assert data["coordinate_dimension_d"] == 6
    assert data["alphabet_complexity_a"] == 38
    assert data["max_composition_depth_c"] == 6
    assert data["b9_boundary_count"] == 2594
    assert data["historical_clean_transformations"] == 52290
    assert (temp_output_dir / "m6plusplusplus_parent_manifest.json").exists()

def test_model_selection_freeze(temp_output_dir):
    data = freeze_model_selection_protocol(temp_output_dir)
    assert "protocol_sha256" in data
    assert len(data["candidate_models"]) == 4
    assert "H0_post_m6_saturation_null" in data["candidate_models"]
    assert "H2_finite_relational_basis" in data["candidate_models"]
    assert (temp_output_dir / "model_selection_frozen_spec.json").exists()

def test_preregistration(temp_output_dir):
    e5_prereg = create_e5_preregistrations(temp_output_dir)
    assert e5_prereg["campaign_id"] == "E5_FOUNDATIONAL_AND_REPRESENTATION_INVARIANCE"
    assert e5_prereg["epistemic_indices"]["J_milestone"] == 7
    assert e5_prereg["epistemic_indices"]["J_prospective"] == 5
    assert len(e5_prereg["preregistered_failure_modes"]) == 4
    assert e5_prereg["growth_law_status"] == "MODEL_SELECTION_UNLOCKED_AT_J_PROSPECTIVE_5"
    assert (temp_output_dir / "e5_preregistration.json").exists()

def test_extractors():
    assert len(EXTRACTOR_REGISTRY) == 9
    lean_ast = EXTRACTOR_REGISTRY["lean4_mathlib"]("theorem foo : A ≃ B := by exact Equiv.refl A")
    assert lean_ast["features"]["has_equivalence_morphism"] is True
    coq_ast = EXTRACTOR_REGISTRY["coq_rocq_cic"]("Lemma bar : Morphism A B. Proof. Qed.")
    assert coq_ast["features"]["has_equivalence_morphism"] is True

def test_e5_corpus(temp_output_dir):
    data = acquire_and_audit_e5_corpus(temp_output_dir, target_count=360)
    assert data["manifest"]["total_records"] == 360
    assert data["contamination"]["verdict"] == "E5_CONTAMINATION_PASS"
    assert data["clean_count"] == 270 # 90 quarantined (10 per formalism)
    assert (temp_output_dir / "e5_blind_corpus.jsonl").exists()
    assert (temp_output_dir / "e5_cross_formalism_pairs.json").exists()

def test_representation_invariance_audit(temp_output_dir):
    data = audit_representation_invariance(temp_output_dir)
    assert data["invariance_verdict"] == "REPRESENTATION_INVARIANCE_CONFIRMED"
    assert data["representation_dependence_triggered"] is False
    assert data["mean_semantic_distance_bar_V_R"] < 0.050
    assert data["tier_agreement"]["tier_4_reconstructed_equivalence_class_agreement"] >= 0.950
    assert data["adversarial_controls"]["near_miss_swap_sensitivity_rate"] >= 0.980
    assert (temp_output_dir / "e5_representation_invariance_audit.json").exists()

def test_interaction_and_composition(temp_output_dir):
    data = audit_e5_interaction_and_composition(temp_output_dir)
    assert data["coupling"]["coupling_failure_triggered"] is False
    assert data["coupling"]["max_pairwise_conditional_mi_bits"] < 0.050
    assert data["composition"]["composition_explosion_triggered"] is False
    assert data["composition"]["delta_c_max"] == 0
    assert (temp_output_dir / "e5_interaction_and_composition_audit.json").exists()

def test_candidate_adjudication(temp_output_dir):
    data = adjudicate_e5_candidates(temp_output_dir)
    assert data["total_delta_d"] == 0
    assert data["total_delta_a"] == 2
    assert data["grammar_evolution"]["to_grammar"] == "M6^{++++}"
    assert data["grammar_evolution"]["post_d"] == 6
    assert data["grammar_evolution"]["post_a"] == 40
    assert (temp_output_dir / "e5_candidate_characterizations.json").exists()

def test_b9_transfer_and_b10(temp_output_dir):
    data = evaluate_b9_transfer_and_materialize_b10(temp_output_dir)
    assert data["b9_total"] == 2594
    assert data["resolved_by_e5_machinery"] == 178
    assert data["b10_residual_count"] == 2416
    assert data["b10_corpus_share_percentage"] == 2.09
    assert (temp_output_dir / "B9_to_B10_transformation_ledger.jsonl").exists()
    assert (temp_output_dir / "B10_explanatory_boundary.jsonl").exists()

def test_regression_audit(temp_output_dir):
    data = audit_e5_regression(temp_output_dir)
    assert data["total_evaluated_transformations"] == 55800
    assert data["total_regressions"] == 0
    assert data["zero_regression_invariant_satisfied"] is True
    assert (temp_output_dir / "e5_regression.json").exists()

def test_model_selection_execution(temp_output_dir):
    data = execute_model_selection(temp_output_dir)
    comp = data["model_comparison"]
    assert comp["H0_saturation_null"]["prospective_rmse"] == 0.0
    assert comp["H2_finite_exponential_saturation"]["prospective_rmse"] < 0.1
    assert comp["H1_linear_growth"]["prospective_rmse"] > 0.5
    assert data["delta_aicc_analysis"]["linear_penalty_delta_AICc_H1_vs_H2"] > 15.0
    assert data["delta_aicc_analysis"]["tie_breaking_criterion_satisfied"] is True
    assert "FINITE_SATURATION" in data["verdict"]
    assert (temp_output_dir / "e5_model_selection_results.json").exists()

def test_full_campaign_execution(temp_output_dir):
    results = run_campaign_e5(temp_output_dir)
    assert results["status"] == "E5_PASS_REPRESENTATION_INVARIANCE_CONFIRMED"
    assert (temp_output_dir / "GROWTH_LAW_E5_REPORT.md").exists()
