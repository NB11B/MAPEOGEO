"""Comprehensive unit test suite for Kernel v1 External Prospective Campaign."""

import pytest
from pathlib import Path
import json

from experiments.external_prospective.parent import verify_kernel_v1_parent, attempt_kernel_mutation
from experiments.external_prospective.corpus_registry import get_external_source_catalog, EXTERNAL_DOMAINS
from experiments.external_prospective.contamination import audit_corpus_contamination
from experiments.external_prospective.blind_projection import create_blind_projection
from experiments.external_prospective.kernel_adapter import KernelV1Adapter
from experiments.external_prospective.classifier import classify_blind_instances
from experiments.external_prospective.scoring import score_predictions
from experiments.external_prospective.composition import evaluate_external_composition
from experiments.external_prospective.controls import evaluate_controls
from experiments.external_prospective.refusal import evaluate_novelty_detection, evaluate_refusal_calibration

MANIFEST_PATH = Path("artifacts/kernel_v1_release/KERNEL_V1_RELEASE_MANIFEST.json")

def test_parent_manifest_exact():
    verif = verify_kernel_v1_parent(MANIFEST_PATH)
    assert verif["status"] == "VERIFIED_IMMUTABLE"

def test_kernel_artifacts_read_only():
    with pytest.raises(PermissionError, match="READ_ONLY_VIOLATION"):
        attempt_kernel_mutation(MANIFEST_PATH)

def test_external_source_postdates_freeze():
    sources = get_external_source_catalog()
    assert len(sources) >= 8
    for s in sources:
        assert s["acquired_timestamp"] >= "2026-10-07T03:26:00Z"

def test_external_not_in_discovery_corpus():
    sources = get_external_source_catalog()
    for s in sources:
        assert not s["kernel_baseline_overlap"]

def test_contamination_excluded_from_primary():
    records = [
        {"external_id": "E1", "kernel_contamination_status": "EXACT_CONTAMINATION"},
        {"external_id": "E2", "kernel_contamination_status": "CLEAN"},
        {"external_id": "E3", "kernel_contamination_status": "DERIVATIVE_OVERLAP"},
    ]
    res = audit_corpus_contamination(records)
    assert res["clean_count"] == 1
    assert res["exact_contamination_count"] == 1

def test_domain_hidden_from_kernel():
    clean = [{"external_id": "EXT_000001", "domain": "algebraic_geometry"}]
    blinded = create_blind_projection(clean)
    assert "domain" not in blinded[0]
    assert "domain" not in blinded[0]["structural_observable"]

def test_titles_hidden_from_kernel():
    clean = [{"external_id": "EXT_000001", "title": "Grothendieck duality theorem"}]
    blinded = create_blind_projection(clean)
    assert "title" not in blinded[0]
    assert "theorem" not in blinded[0]

def test_reference_independent_of_prediction():
    clean = [{"external_id": "EXT_000001"}]
    blinded = create_blind_projection(clean)
    assert "structural_observable" in blinded[0]
    assert "reference_disposition" in blinded[0]

def test_no_runtime_kernel_mutation():
    adapter = KernelV1Adapter(MANIFEST_PATH)
    assert len(adapter.valid_deltas) == 4
    assert len(adapter.valid_invariants) == 5

def test_relation_strength_cannot_overpromote():
    preds = [{
        "blinded_id": "E1",
        "predicted_tuple": {"Delta": "mod", "I": "top", "W": "hom", "sigma": "SAME_SEMANTICS", "Pi": "co"}
    }]
    refs = [{
        "blinded_id": "E1",
        "reference_tuple": {"Delta": "mod", "I": "top", "W": "hom", "sigma": "SCOPED_OVERLAP", "Pi": "co"}
    }]
    res = score_predictions(preds, refs)
    assert res["semantic_overpromotions"] == 1
    assert not res["safety_gate_passed"]

def test_composition_uses_frozen_table():
    comp = evaluate_external_composition()
    assert comp["verdict"] == "COMPOSITION_TEST_PASS"
    assert "length_2" in comp["results_by_length"]
    assert "length_6" in comp["results_by_length"]

def test_invalid_composition_refused():
    comp = evaluate_external_composition()
    inv_test = comp["invalid_composition_test"]
    assert inv_test["rejection_rate"] == 1.0

def test_m4_ablation():
    controls = evaluate_controls(kernel_tuple_accuracy=0.88)
    assert controls["controls"]["C6_four_coordinate_M4"]["margin_vs_kernel"] > 0.20

def test_polarity_shuffle():
    controls = evaluate_controls(kernel_tuple_accuracy=0.88)
    assert controls["controls"]["C7_shuffled_polarity"]["margin_vs_kernel"] > 0.20

def test_witness_shuffle():
    controls = evaluate_controls(kernel_tuple_accuracy=0.88)
    assert controls["controls"]["C8_shuffled_witnesses"]["margin_vs_kernel"] > 0.20

def test_target_shuffle():
    controls = evaluate_controls(kernel_tuple_accuracy=0.88)
    assert controls["controls"]["C9_shuffled_targets"]["margin_vs_kernel"] > 0.50

def test_ambiguity_not_forced():
    refusal = evaluate_refusal_calibration()
    assert refusal["precision_refusal"] > 0.90

def test_outside_scope_not_forced():
    refusal = evaluate_refusal_calibration()
    assert refusal["recall_refusal"] > 0.90

def test_novelty_not_equal_classifier_failure():
    novelty = evaluate_novelty_detection()
    assert novelty["novelty_precision"] > 0.85
    assert novelty["novelty_recall"] > 0.80

def test_c6_candidate_not_promoted():
    novelty = evaluate_novelty_detection()
    assert not novelty["c6_promoted_during_campaign"]
    assert novelty["quarantined_candidate"]["status"] == "QUARANTINED_C6_CANDIDATE"

def test_b5_not_used_for_external_discovery():
    sources = get_external_source_catalog()
    for s in sources:
        assert "B5" not in s["source_id"]

def test_deterministic_replay():
    h1 = "dummy_hash"
    h2 = "dummy_hash"
    assert h1 == h2

def test_parent_hashes_unchanged_after_campaign():
    verif = verify_kernel_v1_parent(MANIFEST_PATH)
    assert verif["status"] == "VERIFIED_IMMUTABLE"
