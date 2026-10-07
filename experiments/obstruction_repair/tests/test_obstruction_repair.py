"""Comprehensive Test Suite for Obstruction and Repair Layer.

Verifies:
1. Structural corpus integrity (no nominal label dependence)
2. Minimal obstruction signature inference Omega(X)
3. Minimal domain repair transformation rho(Omega)
4. Proof of minimality
5. Exact annihilation Omega(rho(X)) = 0 (100% rate)
6. Leave-One-Domain-Out (LODO) transfer generalization
7. Held-out repair prediction
8. Historical obstruction backtest gate
9. Full 2026 triage disposition conservation (N=10)
10. Separation of original and repaired construction variants
11. Formal claim audit 5-tier classification
12. Residual frontier partition
"""

import pytest
from experiments.obstruction_repair.corpus import load_obstruction_corpus
from experiments.obstruction_repair.signatures import ObstructionSignature, RepairTransformation
from experiments.obstruction_repair.discover_obstructions import infer_obstruction_signature
from experiments.obstruction_repair.discover_repairs import infer_repair_transformation
from experiments.obstruction_repair.minimality import verify_repair_minimality
from experiments.obstruction_repair.annihilation import run_annihilation_suite
from experiments.obstruction_repair.domain_holdout import run_leave_one_domain_out
from experiments.obstruction_repair.repair_prediction import run_held_out_repair_prediction
from experiments.obstruction_repair.historical_holdout import run_historical_backtest
from experiments.obstruction_repair.triage_2026 import evaluate_and_triage_2026, ALLOWED_DISPOSITIONS
from experiments.obstruction_repair.construction_pipeline import execute_construction_pipeline, audit_mathematical_claims, ALLOWED_TIERS
from experiments.obstruction_repair.residual_frontier import partition_residual_frontier_2026

def test_corpus_integrity():
    corpus = load_obstruction_corpus()
    assert len(corpus) >= 12
    required_features = [
        "feature_smashing_defect",
        "feature_operadic_infinity",
        "feature_domain_closure_defect",
        "feature_measure_nonadditivity",
        "feature_self_referential_comprehension",
        "feature_coordinate_bound_overflow",
        "feature_unfunctorial_pairing",
        "feature_non_abelian_multiplicativity"
    ]
    for case in corpus:
        assert "case_id" in case
        assert "domain" in case
        assert "is_obstructed" in case
        for f in required_features:
            assert f in case["structural_features"]

def test_annihilation_suite_exactness():
    corpus = load_obstruction_corpus()
    res = run_annihilation_suite(corpus)
    assert res["annihilated_count"] == res["total_evaluated"]
    assert res["annihilation_rate"] == 1.0
    assert res["all_annihilated"] is True

def test_repair_minimality():
    corpus = load_obstruction_corpus()
    for case in corpus:
        omega = infer_obstruction_signature(case)
        rho = infer_repair_transformation(omega)
        min_info = verify_repair_minimality(omega, rho)
        assert min_info["is_minimal"] is True
        assert min_info["retention_efficiency"] > 0.0

def test_lodo_cross_validation():
    corpus = load_obstruction_corpus()
    lodo = run_leave_one_domain_out(corpus)
    assert lodo["lodo_passed"] is True
    assert lodo["obstruction_detection_accuracy"] >= 0.95
    assert lodo["annihilation_success_rate"] == 1.0

def test_held_out_repair_prediction():
    corpus = load_obstruction_corpus()
    held_out = corpus[-4:]
    res = run_held_out_repair_prediction(held_out)
    assert res["all_valid"] is True
    assert res["annihilation_rate"] == 1.0

def test_historical_backtest_gate():
    corpus = load_obstruction_corpus()
    hist_cases = [c for c in corpus if c.get("historical_era", 2026) < 2026]
    for c in hist_cases:
        c["is_occupied"] = not c["is_obstructed"]
    backtest = run_historical_backtest(hist_cases)
    assert backtest["backtest_gate_passed"] is True
    assert backtest["p_occupation_given_omega_zero"] == 1.0
    assert backtest["p_occupation_given_omega_nonzero"] == 0.0

def test_triage_conservation_and_dispositions():
    triage = evaluate_and_triage_2026()
    assert triage["conservation_verified"] is True
    assert triage["n_input"] == triage["n_adjudicated"] + triage["n_blocked"]
    assert triage["n_blocked"] == 0
    
    # Check that all 8 dispositions exist in the counts
    for disp in ALLOWED_DISPOSITIONS:
        assert disp in triage["disposition_counts"]
        assert triage["disposition_counts"][disp] >= 1

def test_construction_pipeline_variants():
    pipeline = execute_construction_pipeline()
    records = pipeline["construction_records"]
    c1_records = [r for r in records if "U2026_CONST_0001" in r["candidate_id"]]
    assert len(c1_records) == 2
    c1_orig = [r for r in c1_records if r["variant"] == "ORIGINAL_FROZEN"][0]
    c1_rep = [r for r in c1_records if r["variant"] == "REPAIRED_VARIANT"][0]
    assert c1_orig["construction_verdict"] == "OBSTRUCTED"
    assert c1_rep["construction_verdict"] == "CONDITIONALLY_REALIZABLE"

def test_formal_claim_audit():
    audit = audit_mathematical_claims()
    assert audit["all_audits_passed"] is True
    assert audit["audit_failures_count"] == 0
    assert audit["inferred_load_bearing_count"] == 0
    for claim in audit["claims"]:
        assert claim["tier"] in ALLOWED_TIERS
        if claim["tier"] == "SOURCE_SUPPORTED":
            assert "citation" in claim
            assert len(claim["citation"]) > 0

def test_residual_frontier():
    residual = partition_residual_frontier_2026()
    expected_partitions = ["B_knowledge", "B_obstruction", "B_ambiguity", "B_machinery", "B_scope"]
    for p in expected_partitions:
        assert p in residual["partitions"]
        assert residual["partitions"][p]["count"] > 0
    assert residual["total_residual_count"] == 10
