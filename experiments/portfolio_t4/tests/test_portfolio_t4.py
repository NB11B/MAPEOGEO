"""Pytest Suite for Portfolio Target T4.

Verifies all five engineering gates of Target T4:
- T4.1: Exact typing
- T4.2: Concrete failure witness
- T4.3: Obstruction extraction
- T4.4: Nonvanishing proof
- T4.5: Repair annihilation
"""

import pytest
from experiments.portfolio_t4.typing_t4_1 import ExactTypingSpecification
from experiments.portfolio_t4.failure_witness_t4_2 import ConcreteFailureWitness
from experiments.portfolio_t4.obstruction_extraction_t4_3 import ObstructionExtraction
from experiments.portfolio_t4.nonvanishing_t4_4 import NonvanishingProof
from experiments.portfolio_t4.repair_annihilation_t4_5 import RepairAnnihilationVerification
from experiments.portfolio_t4.campaign import run_t4_campaign

def test_gate_t4_1_typing():
    spec = ExactTypingSpecification()
    res = spec.verify_typing()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert "SolidMod_R" in res["specification"]["categories"]
    assert "Sp_{E(n)}" in res["specification"]["categories"]

def test_gate_t4_2_witness():
    witness = ConcreteFailureWitness(prime=2, height=2)
    res = witness.verify_failure()
    assert res["status"] == "PASSED"
    assert res["failure_confirmed"] is True
    assert res["is_equivalence"] is False

def test_gate_t4_3_extraction():
    extractor = ObstructionExtraction()
    res = extractor.verify_extraction()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert "L_n(\\prod_{i=1}^\\infty C(M_i))" in res["fiber_sequence"]["fiber_object"]
    assert "Ext^1_{SolidMod_R}" in res["derived_obstruction_group"]["primary_group"]

def test_gate_t4_4_nonvanishing():
    verifier = NonvanishingProof()
    res = verifier.verify_gate()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["proof"]["is_non_zero"] is True

def test_gate_t4_5_repair_annihilation():
    verifier = RepairAnnihilationVerification()
    res = verifier.verify_annihilation()
    assert res["status"] == "PASSED"
    assert res["annihilation_satisfied"] is True
    assert "NONE" in res["omega_repaired"]

def test_full_t4_campaign_execution():
    summary = run_t4_campaign()
    assert summary["all_five_gates_passed"] is True
    for g_name, g_status in summary["gates"].items():
        assert g_status == "PASSED"
