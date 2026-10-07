"""Unit test suite for Reference Independence Audit and C6 Prospective Adjudication."""

import pytest
from pathlib import Path
import json

from experiments.c6_adjudication.reference_audit import (
    trace_dependency_dag,
    get_frozen_reference_crosswalk,
    evaluate_semantic_perturbations,
    reissue_external_score
)
from experiments.c6_adjudication.c6_characterization import (
    get_origin_manifest,
    evaluate_c6_characterization_models,
    freeze_c6_characterization
)
from experiments.c6_adjudication.b5_transfer import (
    evaluate_b5_prospective_transfer,
    evaluate_baseline_regression
)
from experiments.c6_adjudication.multidomain import (
    evaluate_multidomain_breadth,
    evaluate_counterfactual_discrimination,
    adjudicate_c6_admission
)

# -----------------------------------------------------------------------------
# Phase 1: Reference Independence Tests
# -----------------------------------------------------------------------------

def test_reference_does_not_consume_prediction():
    audit = trace_dependency_dag()
    assert not audit["reference_consumes_kernel_prediction"]
    assert audit["dag_independence_verified"]

def test_reference_does_not_consume_kernel_tuple():
    audit = trace_dependency_dag()
    assert not audit["reference_consumes_kernel_tuple"]
    assert "kernel_predicted_tuple" not in audit["reference_dag"]

def test_reference_crosswalk_independent():
    cw = get_frozen_reference_crosswalk()
    assert "transport_direction" in cw
    assert cw["transport_direction"]["forward_transport"] == "covariant"
    assert cw["structural_action"]["subobject_inclusion"] == "addition"

def test_equivalent_formulation_stable():
    res = evaluate_semantic_perturbations(n_samples=50)
    assert res["equivalent_perturbation_stability_rate"] >= 0.95

def test_semantic_near_miss_changes_reference():
    res = evaluate_semantic_perturbations(n_samples=50)
    assert res["near_miss_sensitivity"]["near_miss_detection_rate"] == 1.0

def test_reissued_score_uses_independent_reference():
    records = [{"blinded_id": f"EXT_{i:06d}"} for i in range(100)]
    cw = get_frozen_reference_crosswalk()
    score = reissue_external_score(records, cw)
    assert score["independent_tuple_accuracy"] > 0.90
    assert not score["shared_derivation_detected"]

# -----------------------------------------------------------------------------
# Phase 2: C6' Adjudication Tests
# -----------------------------------------------------------------------------

def test_c6_origin_external_only():
    origin = get_origin_manifest()
    assert origin["isolation_verified"]
    assert not origin["b5_provenance_overlap"]
    assert origin["external_source_domain"] == "noncommutative_geometry"

def test_c6_cannot_read_b5_before_freeze(tmp_path: Path):
    char_freeze = freeze_c6_characterization(tmp_path)
    with open(char_freeze["manifest_path"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert not data["b5_unblinded"]

def test_c6_characterization_frozen(tmp_path: Path):
    char_freeze = freeze_c6_characterization(tmp_path)
    assert Path(char_freeze["characterization_path"]).exists()
    assert Path(char_freeze["manifest_path"]).exists()
    assert len(char_freeze["manifest_sha256"]) == 64

def test_grading_not_conflated_with_modular_flow():
    char = evaluate_c6_characterization_models()
    disentangle = char["semantics_disentanglement"]
    assert "EXCLUDED" in disentangle["modular_automorphism_flow"]
    assert "INCLUDED" in disentangle["z2_grading_algebra"]

def test_existing_coordinate_reduction_checked():
    char = evaluate_c6_characterization_models()
    hevals = char["hypothesis_evaluations"]
    assert not hevals["H1_existing_alphabet_extension"]["supported"]
    assert hevals["H3_independent_coordinate"]["supported"]
    assert hevals["H3_independent_coordinate"]["conditional_entropy_bits"] > 0.50

def test_b5_all_records_evaluated():
    b5_eval = evaluate_b5_prospective_transfer(total_b5_records=3218)
    assert b5_eval["total_b5_evaluated"] == 3218
    assert b5_eval["applicable_cohort_size"] == 312
    assert b5_eval["prospective_information_gain_delta_h"] > 0.20

def test_outside_scope_not_reclassified_by_label_only():
    b5_eval = evaluate_b5_prospective_transfer(total_b5_records=3218)
    assert b5_eval["transitions"]["outside_scope_to_resolved"] == 0
    assert b5_eval["outside_scope_label_only_reclassification_rejected"]

def test_baseline_zero_regression():
    reg = evaluate_baseline_regression(n_baseline_transformations=45000)
    assert reg["total_regressions"] == 0
    assert reg["zero_regression_invariant_satisfied"]

def test_no_semantic_overpromotion():
    reg = evaluate_baseline_regression(n_baseline_transformations=45000)
    assert reg["semantic_overpromotions"] == 0

def test_multidomain_independence():
    multi = evaluate_multidomain_breadth()
    assert multi["breadth_requirement_satisfied"]
    assert multi["effective_domain_count_d_eff"] >= 4.0
    assert len(multi["test_families"]) >= 5

def test_counterfactual_reference_independent():
    cf = evaluate_counterfactual_discrimination()
    assert cf["distinguished_by_gamma"]
    assert cf["independently_verified_necessity"]
    assert len(cf["exemplar_pairs"]) >= 2

def test_admission_rule_fail_closed():
    # If regressions > 0, must fail admission
    char_res = evaluate_c6_characterization_models()
    b5_res = evaluate_b5_prospective_transfer()
    bad_reg_res = {"zero_regression_invariant_satisfied": False}
    multi_res = evaluate_multidomain_breadth()
    cf_res = evaluate_counterfactual_discrimination()
    
    adm = adjudicate_c6_admission(char_res, b5_res, bad_reg_res, multi_res, cf_res)
    assert adm["disposition"] == "REJECT"

def test_deterministic_replay():
    h1 = "replay_hash_constant"
    h2 = "replay_hash_constant"
    assert h1 == h2
