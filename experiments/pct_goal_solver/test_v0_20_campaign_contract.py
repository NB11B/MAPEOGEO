from __future__ import annotations

from experiments.pct_goal_solver.model import Artifact, SolveTrace, VerificationResult
from experiments.pct_goal_solver.v0_20_campaign import (
    _macro_analysis,
    evaluate_case,
    evaluate_terminal_control,
)
from experiments.pct_goal_solver.v0_20_goals import (
    build_case_oracle,
    build_v0_20_corpus,
    build_v0_20_terminal_controls,
)


def test_case_evaluation_keeps_observation_and_oracle_separate() -> None:
    goal = build_v0_20_corpus()["SEALED_V0_20"][0]
    oracle = build_case_oracle(goal)
    candidate = Artifact(
        artifact_id="candidate:test",
        semantic_type=goal.target.semantic_type,
        representation_class=goal.target.representation_class,
        value=goal.sealed_expected_result,
        exactness_class=goal.target.exactness_class or "EXACT",
    )
    trace = SolveTrace(
        goal_id=goal.goal_id,
        mode="EXPLICIT/PRIMITIVE",
        operator_path=("TEST_ONLY", "VERIFY_CANDIDATE"),
        expanded_state_count=1,
        primitive_execution_count=1,
        macro_ids=(),
        candidate_artifact=candidate,
        verifier_chain=(VerificationResult(True, goal.required_verifier_class),),
        falsification_events=(),
        final_verdict="PASS",
    )
    case = evaluate_case(goal, trace, oracle)
    assert case["observation"]["verdict"] == "PASS"
    assert case["oracle"]["goal_id"] == goal.goal_id
    assert "expected" not in case["observation"]
    assert "observed" not in case["oracle"]
    assert case["assessment"]["oracle_available"] is oracle["authoritative"]


def test_corrupt_target_like_control_is_not_laundered_into_oracle_truth() -> None:
    control = next(
        control
        for control in build_v0_20_terminal_controls()
        if control.family == "F3" and control.kind.value == "INVALID_TERMINAL_CERTIFICATE"
    )
    result = evaluate_terminal_control(control)
    assert result["candidate_was_planner_root"] is False
    assert result["observed_verification_pass"] is False
    assert result["correct"] is True


def test_macro_rescue_is_verdict_based_and_incomplete_parity_gets_no_credit() -> None:
    def case(verdict: str) -> dict:
        return {
            "goal_id": "sealed:test",
            "family": "X1",
            "observation": {
                "verdict": verdict,
                "macro_ids": ["candidate"] if verdict == "PASS" else [],
                "expanded_state_count": 1,
                "primitive_execution_count": 1,
                "semantic_certificate": {"complete": False, "verdict": verdict},
            },
        }

    modes = {
        "EXPLICIT/PRIMITIVE": {"cases": [case("NOT_ESTABLISHED")]},
        "EXPLICIT/SYNTHESIZED": {"cases": [case("PASS")]},
    }
    analysis = _macro_analysis(modes)
    assert analysis["total_comparisons"] == 1
    assert analysis["macro_rescue_count"] == 1
    assert analysis["exact_conservation_count"] == 0
    assert analysis["efficiency_credit_count"] == 0
