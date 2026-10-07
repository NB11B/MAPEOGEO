"""Test Suite for Campaign C1 (Prospective Construction of U2026_CONST_0001)."""

import pytest
from pathlib import Path

from experiments.frontier_construction_c1.certificate_loader import load_and_verify_candidate_certificate
from experiments.frontier_construction_c1.type_audit import audit_mathematical_typing
from experiments.frontier_construction_c1.obligation_o1 import verify_obligation_o1
from experiments.frontier_construction_c1.obligation_o2 import verify_obligation_o2
from experiments.frontier_construction_c1.obligation_o3 import verify_obligation_o3
from experiments.frontier_construction_c1.obstruction_search import (
    evaluate_filtered_colimits,
    evaluate_ext1_obstruction_class,
    run_falsifier_stress_test
)
from experiments.frontier_construction_c1.compatibility import solve_route_intersection
from experiments.frontier_construction_c1.realizability import adjudicate_realizability
from experiments.frontier_construction_c1.campaign import run_campaign_c1

@pytest.fixture
def temp_output_dir(tmp_path):
    out = tmp_path / "artifacts_c1_test"
    out.mkdir(parents=True, exist_ok=True)
    return out

def test_certificate_loader_and_custody():
    res = load_and_verify_candidate_certificate("U2026_CONST_0001")
    assert res["integrity_verified"] is True
    assert res["custody_status"] == "SEALED_INTACT"
    cert = res["certificate"]
    assert cert["candidate_id"] == "U2026_CONST_0001"
    assert cert["kernel_v3_coordinates"] == {"Delta": 4, "I": 4, "W": 4, "sigma": 3, "Pi": 4, "Gamma": 4}

def test_gate_c1_1_type_audit():
    res = load_and_verify_candidate_certificate("U2026_CONST_0001")
    type_res = audit_mathematical_typing(res["certificate"])
    assert type_res["is_well_typed"] is True
    assert type_res["gate_status"] == "GATE_C1_1_PASSED_WELL_TYPED"
    assert "SolidMod_R" in type_res["type_signatures"]
    assert "Adjunction" in type_res["type_signatures"]

def test_obligations_verification():
    o1 = verify_obligation_o1()
    assert o1["status"] == "ESTABLISHED"
    assert o1["counterexample_found"] is False

    o2 = verify_obligation_o2()
    assert o2["obstruction_identified"] is True
    assert o2["is_arbitrary_limit_commutation_false"] is True
    assert o2["survives_under_nuclear_restriction"] is True

    o3 = verify_obligation_o3()
    assert o3["status"] == "ESTABLISHED"
    assert o3["degenerates_at_e2"] is True

def test_obstruction_search_and_falsifier():
    falsifier = run_falsifier_stress_test()
    assert falsifier["falsifier_triggered"] is True
    assert falsifier["verdict"] == "FALSIFIER_OBSTRUCTION_DETECTED"
    assert falsifier["ext1_obstruction_test"]["obstruction_is_zero"] is False

def test_route_intersection():
    routes = solve_route_intersection()
    assert routes["is_intersection_empty_unrestricted"] is True
    assert routes["is_intersection_nonempty_nuclear"] is True
    assert len(routes["minimal_inconsistent_subset"]) >= 1

def test_realizability_adjudication():
    res = load_and_verify_candidate_certificate("U2026_CONST_0001")
    adjudication = adjudicate_realizability(res["certificate"])
    assert adjudication["verdict"] == "OBSTRUCTED"
    assert "scientific_discovery" in adjudication["construction_details"]

def test_full_campaign_c1(temp_output_dir):
    results = run_campaign_c1(temp_output_dir)
    assert results["verdict"] == "OBSTRUCTED"
    assert (temp_output_dir / "PROSPECTIVE_CONSTRUCTION_C1_REPORT.md").exists()
    assert (temp_output_dir / "certificate_audit.json").exists()
    assert (temp_output_dir / "realizability_adjudication.json").exists()
