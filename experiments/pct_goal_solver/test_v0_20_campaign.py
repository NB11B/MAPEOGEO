from __future__ import annotations

from experiments.pct_goal_solver.v0_20_campaign import (
    CAPABILITY_GATE_KEYS,
    ENGINE_GATE_KEYS,
    EVIDENCE_GATE_KEYS,
    EXPECTED_GATE_KEYS,
    FROZEN_EXPECTED_GATE_VECTOR,
    FROZEN_EXPECTED_SCIENTIFIC_STATUS,
    GATE_DENOMINATORS,
    classify_scientific_status,
    execute_v0_20_campaign,
    matches_frozen_expected_gate_vector,
)


def test_status_requires_every_nonvacuous_gate() -> None:
    all_true = {gate: True for gate in GATE_DENOMINATORS}
    assert classify_scientific_status(all_true) == "SUPPORTED"
    assert set(all_true) == set(EXPECTED_GATE_KEYS)

    engine_failed = dict(all_true)
    engine_failed[next(iter(ENGINE_GATE_KEYS))] = False
    assert classify_scientific_status(engine_failed) == "ENGINE_INVALID"

    evidence_missing = dict(all_true)
    evidence_missing[next(iter(EVIDENCE_GATE_KEYS))] = False
    assert classify_scientific_status(evidence_missing) == "EVIDENCE_PARTIAL"

    unsupported = dict(all_true)
    unsupported[next(iter(CAPABILITY_GATE_KEYS))] = False
    assert classify_scientific_status(unsupported) == "NOT_SUPPORTED"
    assert classify_scientific_status({}) == "ENGINE_INVALID"


def test_v0_20_campaign_is_truthful_and_channels_are_segregated() -> None:
    result = execute_v0_20_campaign()
    assert result["campaign_id"] == "PCT_GOAL_SOLVER_CROSS_CLASS_V0_20"
    assert result["scientific_status"] == classify_scientific_status(result["gates"])
    assert result["scientific_status"] == FROZEN_EXPECTED_SCIENTIFIC_STATUS
    assert matches_frozen_expected_gate_vector(result["gates"])
    assert result["gates"] == dict(FROZEN_EXPECTED_GATE_VECTOR)
    assert result["scientific_status"] != "SUPPORTED" or all(result["gates"].values())
    assert result["gates_total"] == len(GATE_DENOMINATORS)
    assert result["gates_passed"] == sum(result["gates"].values())

    receipts = result["gate_receipts"]
    assert set(receipts) == set(GATE_DENOMINATORS)
    for gate, denominator in GATE_DENOMINATORS.items():
        receipt = receipts[gate]
        assert denominator > 0
        assert receipt["denominator"] == denominator
        assert 0 <= receipt["numerator"] <= denominator
        assert receipt["passed"] is result["gates"][gate]

    sample = result["splits"]["SEALED_V0_20"]["EXPLICIT/PRIMITIVE"]["cases"][0]
    assert set(sample) >= {"observation", "oracle", "assessment"}
    assert "observed" not in sample["oracle"]
    assert "expected" not in sample["observation"]

    channels = result["channels"]
    observed_case = channels["observed_solver_outcomes"]["sealed"]["EXPLICIT/PRIMITIVE"]["cases"][0]
    oracle_case = channels["mathematical_oracle_certificates"]["cases"][0]
    assessed_case = channels["independent_assessments"]["sealed"]["EXPLICIT/PRIMITIVE"]["cases"][0]
    assert "oracle" not in observed_case and "assessment" not in observed_case
    assert "observation" not in oracle_case and "assessment" not in oracle_case
    assert "observation" not in assessed_case and "oracle" not in assessed_case

    assert result["provenance"]["frozen_feature_base_sha"] == "32967600a00a5659e49fa3ef056be02567c74efa"
    for digest_name in ("corpus_sha256", "terminal_controls_sha256", "registry_contract_sha256"):
        assert len(result["provenance"][digest_name]) == 64
    implementation = result["provenance"]["implementation_manifest"]
    assert len(implementation["manifest_sha256"]) == 64
    assert implementation["complete"] is True

    terminal_controls = channels["terminal_candidate_controls"]
    assert terminal_controls["total"] > 0
    assert all(case["candidate_was_planner_root"] is False for case in terminal_controls["cases"])

    x2_oracles = [case for case in channels["mathematical_oracle_certificates"]["cases"] if case["family"] == "X2"]
    assert x2_oracles
    assert all(case["authoritative"] is False for case in x2_oracles)
    assert result["scientific_status"] != "SUPPORTED"


def test_empty_or_missing_channels_cannot_pass_fixed_gates() -> None:
    result = execute_v0_20_campaign()
    for gate, receipt in result["gate_receipts"].items():
        if receipt["numerator"] == 0:
            assert not result["gates"][gate]
            assert receipt["denominator"] == GATE_DENOMINATORS[gate]
