"""Test Suite for Frontier Construction Suite (C1–C3 and Historical Controls)."""

import pytest
from pathlib import Path

from experiments.frontier_construction_suite.audit_c1_claims import audit_c1_seven_claims
from experiments.frontier_construction_suite.candidate_c2 import evaluate_candidate_c2
from experiments.frontier_construction_suite.candidate_c3 import evaluate_candidate_c3
from experiments.frontier_construction_suite.historical_controls import evaluate_historical_controls
from experiments.frontier_construction_suite.uow_state_machine import partition_live_frontier
from experiments.frontier_construction_suite.campaign import run_construction_suite

@pytest.fixture
def temp_output_dir(tmp_path):
    out = tmp_path / "artifacts_suite_test"
    out.mkdir(parents=True, exist_ok=True)
    return out

def test_audit_c1_claims():
    res = audit_c1_seven_claims()
    assert res["all_seven_claims_verified"] is True
    assert res["calibrated_scientific_status"] == "OBSTRUCTION_CANDIDATE_DETECTED"
    assert res["graph_level_verdict"] == "OBSTRUCTED"
    assert len(res["audited_claims"]) == 7

def test_candidate_c2_construction():
    c2 = evaluate_candidate_c2()
    assert c2["verdict"] == "CONSTRUCTED_UP_TO_EQUIVALENCE"
    assert c2["obligations"]["O_1_quasi_syntomic_descent"]["status"] == "ESTABLISHED"
    assert c2["obligations"]["O_2_nygaard_self_duality"]["status"] == "ESTABLISHED"
    assert c2["falsifier_test"]["preserves_validity_on_quasi_syntomic_stacks"] is True

def test_candidate_c3_obstruction():
    c3 = evaluate_candidate_c3()
    assert c3["verdict"] == "OBSTRUCTED"
    assert c3["obligations"]["O_1_constructive_kan_filling"]["status"] == "OBSTRUCTED"
    assert c3["falsifier_test"]["falsifier_triggered"] is True
    assert "Coherence" in c3["obstruction_mechanism"]

def test_historical_controls():
    hist = evaluate_historical_controls()
    assert hist["positive_control_acceptance_rate"] == "3/3 (100.0%)"
    assert hist["negative_control_rejection_rate"] == "3/3 (100.0%)"
    for pos in hist["positive_controls"]:
        assert pos["obstruction_verdict"] == "REALIZABLE"
    for neg in hist["negative_controls"]:
        assert neg["obstruction_verdict"] == "OBSTRUCTED_INADMISSIBLE"

def test_uow_frontier_partition():
    candidates = [
        {"candidate_id": "C1", "verdict": "OBSTRUCTED", "obstruction_class": "Ext1 != 0", "minimal_repair": "SolidMod_nuc"},
        {"candidate_id": "C2", "verdict": "CONSTRUCTED_UP_TO_EQUIVALENCE", "details": "Realizable on Stk(QSyn)"},
        {"candidate_id": "C3", "verdict": "OBSTRUCTED", "obstruction_class": "Canonicity loss", "minimal_repair": "tau_{<= k}"}
    ]
    partition = partition_live_frontier(candidates)
    assert partition["u_realizable_count"] == 1
    assert partition["u_obstructed_count"] == 2
    assert "C2" in partition["true_construction_frontier"]

def test_full_construction_suite(temp_output_dir):
    results = run_construction_suite(temp_output_dir)
    assert results["status"] == "SUITE_COMPLETED"
    assert results["c2_verdict"] == "CONSTRUCTED_UP_TO_EQUIVALENCE"
    assert results["c3_verdict"] == "OBSTRUCTED"
    assert (temp_output_dir / "PROSPECTIVE_CONSTRUCTION_SUITE_REPORT.md").exists()
    assert (temp_output_dir / "c1_mathematical_audit.json").exists()
    assert (temp_output_dir / "candidate_c2_realizability.json").exists()
    assert (temp_output_dir / "candidate_c3_realizability.json").exists()
    assert (temp_output_dir / "historical_controls_results.json").exists()
    assert (temp_output_dir / "frontier_partition_2026.json").exists()
