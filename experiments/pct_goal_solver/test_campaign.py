from __future__ import annotations

from experiments.pct_goal_solver.campaign import MODE_NAMES, run_campaign, score_trace
from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.model import Artifact, SolveTrace, VerificationResult


def _trace(goal, value, verdict="PASS"):
    candidate = None
    verifiers = ()
    path = ()
    if verdict == "PASS":
        candidate = Artifact(
            artifact_id="candidate:test",
            semantic_type=goal.target.semantic_type,
            representation_class=goal.target.representation_class,
            value=value,
            exactness_class=goal.target.exactness_class or "EXACT",
        )
        verifiers = (VerificationResult(True, "TEST_VERIFIER"),)
        path = ("TEST_OPERATOR", "VERIFY_CANDIDATE")
    return SolveTrace(
        goal_id=goal.goal_id,
        mode="TEST",
        operator_path=path,
        expanded_state_count=1,
        primitive_execution_count=1 if verdict == "PASS" else 0,
        macro_ids=(),
        candidate_artifact=candidate,
        verifier_chain=verifiers,
        falsification_events=(),
        final_verdict=verdict,
    )


def test_family_specific_scoring_normalizes_candidate_shapes():
    g2 = goals_for("SEALED", "G2")[0]
    t2 = _trace(g2, {"unique": g2.sealed_expected_result["unique"], "nullity": g2.sealed_expected_result["nullity"], "basis": ()})
    assert score_trace(g2, t2)["correct"] is True

    g3 = goals_for("SEALED", "G3")[0]
    assert score_trace(g3, _trace(g3, g3.sealed_expected_result["is_chain_map"]))["correct"] is True

    g10 = goals_for("SEALED", "G10")[0]
    assert score_trace(g10, _trace(g10, {"order": g10.sealed_expected_result, "energy": ()}))["correct"] is True

    g11 = goals_for("SEALED", "G11")[0]
    assert score_trace(g11, _trace(g11, {"homothetic": g11.sealed_expected_result, "defect": 0.0}))["correct"] is True


def test_nonpass_verdicts_are_never_counted_as_wrong_positive():
    goal = goals_for("SEALED", "G1")[0]
    score = score_trace(goal, _trace(goal, None, verdict="NOT_ESTABLISHED"))
    assert score["answered"] is False
    assert score["wrong_positive"] is False


def test_campaign_executes_all_six_modes_without_using_ci_status_as_science():
    report = run_campaign()
    assert tuple(report["modes"]) == MODE_NAMES
    assert report["corpus_counts"] == {"CALIBRATION": 36, "VALIDATION": 12, "SEALED": 24}
    assert report["scientific_status"] in {"SUPPORTED", "PARTIAL", "NOT_SUPPORTED"}
    assert set(report["conclusions"]) == {
        "GOAL_DIRECTED_SOLVING",
        "INFERRED_COMPATIBILITY",
        "MIXED_DOMAIN_COMPOSITION",
        "MACRO_SYNTHESIS",
    }
    for mode_name, mode in report["modes"].items():
        assert mode["total"] == 24, mode_name
        assert mode["wrong_positive_count"] >= 0
        assert len(mode["cases"]) == 24
        for case in mode["cases"]:
            if case["verdict"] == "PASS":
                assert case["terminal_verifier_passed"] is True


def test_scientific_gates_are_reported_not_asserted_as_software_success():
    report = run_campaign()
    assert set(report["gates"]) == {
        "explicit_all_12_families",
        "explicit_zero_wrong_positives",
        "explicit_six_multistep_families",
        "three_cross_class_families",
        "inferred_nonzero_exact_symbolic_numeric",
        "inferred_no_control_wrong_positive_increase",
        "hybrid_preserves_controls_and_family_coverage",
        "macro_reduces_search_without_semantic_change",
        "all_positive_results_independently_verified",
    }
    assert all(isinstance(value, bool) for value in report["gates"].values())
