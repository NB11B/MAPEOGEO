#!/usr/bin/env python3
r"""
Unit tests for TRIAD-APP-0: Frozen Architecture Application Protocol & Verification Harness.
Verifies:
1. Three independent sequential gates (Gate L1, Gate L2, Gate L3).
2. Falsifiability property: L1 pass does not imply L2 pass; L2 pass does not imply L3 pass.
3. Diagnostic failure localization (L1_FAILURE, L2_FAILURE, L3_FAILURE).
4. Full Triad Congruence on real systems (Data Center, Microgrid, Drone Swarm).
5. Standardized report formatting compliance.
"""

import pytest
from sovctx.node.triad_application_harness import (
    DiagnosticVerdict,
    GateStatus,
    TriadApplicationHarness,
)


@pytest.fixture
def harness() -> TriadApplicationHarness:
    return TriadApplicationHarness()


def test_congruent_applications_pass_all_gates(harness: TriadApplicationHarness) -> None:
    """Verify that valid real applications pass Gate L1, L2, and L3."""
    congruent_ids = ["APP_01_DATACENTER", "APP_02_MICROGRID", "APP_03_DRONE_SWARM"]
    for app_id in congruent_ids:
        spec = harness.specimens[app_id]
        res = harness.evaluate_specimen(spec)

        assert res.gate_l1_status == GateStatus.PASSED, f"{app_id} failed L1"
        assert res.gate_l2_status == GateStatus.PASSED, f"{app_id} failed L2"
        assert res.gate_l3_status == GateStatus.PASSED, f"{app_id} failed L3"
        assert res.diagnostic_verdict == DiagnosticVerdict.TRIAD_CONGRUENT


def test_diagnostic_failure_localization_l1(harness: TriadApplicationHarness) -> None:
    """Verify that Gate L1 failure halts progression and is accurately localized."""
    spec = harness.specimens["PROBE_01_L1_FAIL"]
    res = harness.evaluate_specimen(spec)

    assert res.gate_l1_status == GateStatus.FAILED
    assert res.gate_l2_status == GateStatus.NOT_REACHED
    assert res.gate_l3_status == GateStatus.NOT_REACHED
    assert res.diagnostic_verdict == DiagnosticVerdict.L1_FAILURE


def test_diagnostic_failure_localization_l2(harness: TriadApplicationHarness) -> None:
    """Verify that Gate L1 pass with Gate L2 failure is accurately localized."""
    spec = harness.specimens["PROBE_02_L2_FAIL"]
    res = harness.evaluate_specimen(spec)

    assert res.gate_l1_status == GateStatus.PASSED
    assert res.gate_l2_status == GateStatus.FAILED
    assert res.gate_l3_status == GateStatus.NOT_REACHED
    assert res.diagnostic_verdict == DiagnosticVerdict.L2_FAILURE


def test_diagnostic_failure_localization_l3(harness: TriadApplicationHarness) -> None:
    """Verify that Gate L1 and L2 pass with Gate L3 failure is accurately localized."""
    spec = harness.specimens["PROBE_03_L3_FAIL"]
    res = harness.evaluate_specimen(spec)

    assert res.gate_l1_status == GateStatus.PASSED
    assert res.gate_l2_status == GateStatus.PASSED
    assert res.gate_l3_status == GateStatus.FAILED
    assert res.diagnostic_verdict == DiagnosticVerdict.L3_FAILURE


def test_standard_report_formatting(harness: TriadApplicationHarness) -> None:
    """Verify that the generated report strictly conforms to the specified block format."""
    report = harness.generate_standard_report("APP_01_DATACENTER")

    required_headers = [
        "APPLICATION:",
        "FUNCTIONAL_REQUIREMENT:",
        "LAYER_1",
        "full_state:",
        "question:",
        "reduced_state:",
        "invariants:",
        "omitted_information:",
        "sufficiency_result:",
        "LAYER_2",
        "controlled_variables:",
        "observed_variables:",
        "policy:",
        "feedback:",
        "control_equivalence_result:",
        "LAYER_3",
        "subsystems:",
        "local_functions:",
        "coordination:",
        "viability_envelope:",
        "organizational_result:",
        "FAILURE_BOUNDARIES",
        "L1_failure_conditions:",
        "L2_failure_conditions:",
        "L3_failure_conditions:",
        "OVERALL_VERDICT:",
    ]

    for header in required_headers:
        assert header in report, f"Missing header '{header}' in standard report"
