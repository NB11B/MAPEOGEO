from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

from experiments.pct_goal_solver import v0_20_campaign as campaign
from experiments.pct_goal_solver.model import Refusal
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v0_20_goals import (
    build_v0_20_corpus,
    prove_no_same_class_shortcut,
)
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry


def test_invalid_challenge_cannot_become_math_authority_or_earn_coverage() -> None:
    invalid_goals = tuple(
        replace(goal, search_budget=goal.search_budget + 1)
        for goal in build_v0_20_corpus()["SEALED_V0_20"]
        if goal.family == "F1"
    )
    assert len(invalid_goals) == 2
    registry = build_v0_20_operator_registry()
    cases = []

    for goal in invalid_goals:
        oracle = campaign._build_campaign_oracle(goal)
        trace = solve(goal.solver_visible(), registry)
        case = campaign.evaluate_case(goal, trace, oracle)

        assert oracle["authoritative"] is False
        assert oracle["authority_kind"] == "INVALID_CHALLENGE_CONTRACT"
        assert oracle["expected_verdict"] == "INVALID"
        assert case["assessment"]["challenge_contract_valid"] is False
        assert case["assessment"]["oracle_available"] is False
        assert case["assessment"]["correct"] is None
        cases.append(case)

    assert campaign._family_coverage({"cases": cases}) == 0


def test_invalid_core_challenge_forces_engine_invalid_before_evidence_status() -> None:
    corpus = dict(build_v0_20_corpus())
    sealed = list(corpus["SEALED_V0_20"])
    sealed[0] = replace(
        sealed[0],
        required_verifier_class=f"{sealed[0].required_verifier_class}:INVALID",
    )
    corpus["SEALED_V0_20"] = sealed

    receipt_builder = getattr(campaign, "_challenge_domain_receipt", None)
    assert receipt_builder is not None
    receipt = receipt_builder(corpus)

    # Any frozen-manifest drift invalidates the whole closed-domain authority.
    assert receipt["numerator"] == 0
    assert receipt["passed"] is False
    gates = dict(campaign.FROZEN_EXPECTED_GATE_VECTOR)
    gates["closed_challenge_domain_valid"] = receipt["passed"]
    assert campaign.classify_scientific_status(gates) == "ENGINE_INVALID"


def test_only_exact_frozen_gate_vector_matches_campaign_expectation() -> None:
    expected = getattr(campaign, "FROZEN_EXPECTED_GATE_VECTOR", None)
    matcher = getattr(campaign, "matches_frozen_expected_gate_vector", None)
    assert expected is not None
    assert matcher is not None
    assert set(expected) == set(campaign.EXPECTED_GATE_KEYS)
    assert matcher(dict(expected)) is True

    regressed = dict(expected)
    regressed["shortcut_proofs_complete"] = False
    assert matcher(regressed) is False

    wrong_type = dict(expected)
    wrong_type["shortcut_proofs_complete"] = 1
    assert matcher(wrong_type) is False


def test_proved_label_cannot_launder_an_incomplete_shortcut_proof() -> None:
    predicate = getattr(campaign, "_shortcut_proof_complete", None)
    assert predicate is not None
    goal = next(
        item
        for item in build_v0_20_corpus()["SEALED_V0_20"]
        if item.family == "X1"
    )
    registry = build_v0_20_operator_registry()
    proof = prove_no_same_class_shortcut(goal, registry)
    assert predicate(proof, goal, registry) is True

    assert predicate({**proof, "proof_validated": False}, goal, registry) is False
    assert predicate({**proof, "registry_digest": "0" * 64}, goal, registry) is False
    assert predicate({key: value for key, value in proof.items() if key != "proof_digest"}, goal, registry) is False


def test_evidence_preflight_bounds_fraction_bits_and_cumulative_text() -> None:
    oversized_fraction = Fraction(1 << 70_000, 1)
    with pytest.raises(ValueError, match="Fraction"):
        campaign._bounded_evidence_shape(oversized_fraction)

    repeated_text = "x" * 40_000
    with pytest.raises(ValueError, match="cumulative"):
        campaign._bounded_evidence_shape((repeated_text,) * 32)


def test_authoritative_nonpass_requires_bound_structured_refusal() -> None:
    goals = tuple(
        goal
        for goal in build_v0_20_corpus()["SEALED_V0_20"]
        if goal.family == "G9"
    )
    assert len(goals) == 2
    registry = build_v0_20_operator_registry()
    cases = {}
    traces = {}
    for goal in goals:
        trace = solve(goal.solver_visible(), registry)
        traces[trace.final_verdict] = trace
        cases[trace.final_verdict] = campaign.evaluate_case(
            goal,
            trace,
            campaign._build_campaign_oracle(goal),
        )

    assert set(cases) == {"PASS", "NOT_APPLICABLE"}
    assert cases["NOT_APPLICABLE"]["assessment"]["correct"] is True
    assert cases["NOT_APPLICABLE"]["observation"]["semantic_certificate"]["complete"] is True
    # A two-case family fragment cannot stand in for the frozen 38-case mode.
    assert campaign._family_coverage({
        "total": len(cases),
        "cases": list(cases.values()),
    }) == 0

    refusal_goal = next(
        goal for goal in goals if goal.sealed_expected_result == "NOT_APPLICABLE"
    )
    refusal_trace = traces["NOT_APPLICABLE"]
    assert refusal_trace.refusal is not None
    forged_refusals = {
        "absent": None,
        "malformed": Refusal(
            code="GOAL_NOT_APPLICABLE",
            reason="",
            operator_id=refusal_trace.refusal.operator_id,
        ),
        "wrong-code": replace(
            refusal_trace.refusal,
            code="NO_ADMISSIBLE_PATH",
        ),
        "wrong-operator": replace(
            refusal_trace.refusal,
            operator_id="FOREIGN_OPERATOR",
        ),
    }
    expected_certificate_completeness = {
        "absent": False,
        "malformed": False,
        "wrong-code": True,
        "wrong-operator": True,
    }
    for label, forged_refusal in forged_refusals.items():
        forged_case = campaign.evaluate_case(
            refusal_goal,
            replace(refusal_trace, refusal=forged_refusal),
            campaign._build_campaign_oracle(refusal_goal),
        )
        assert forged_case["assessment"]["correct"] is False, label
        assert (
            forged_case["observation"]["semantic_certificate"]["complete"]
            is expected_certificate_completeness[label]
        ), label
        assert campaign._family_coverage(
            {"cases": [cases["PASS"], forged_case]}
        ) == 0, label
