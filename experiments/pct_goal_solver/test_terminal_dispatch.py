from dataclasses import replace

from experiments.pct_goal_solver.canonical import canonical_sha256
from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.model import Artifact, RoutingReceipt
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import (
    _terminal_goal_view,
    solve,
    verify_terminal_candidate,
)


def _candidate(goal, value, *, metadata=()):
    return Artifact(
        "external-candidate",
        goal.target.semantic_type,
        goal.target.representation_class,
        value,
        goal.target.exactness_class,
        metadata,
    )


def test_public_terminal_dispatch_is_the_strict_historical_authority():
    goal = goals_for("CALIBRATION", "G10")[0].solver_visible()
    accepted = verify_terminal_candidate(goal, _candidate(goal, {"order": 1}))
    forged = verify_terminal_candidate(
        goal,
        _candidate(goal, {"order": 1, "active_harmonics": (1,)}),
    )
    assert accepted.passed
    assert not forged.passed
    assert accepted.verifier_class == goal.required_verifier_class
    assert ("verifier_version", "historical-root-v2") in accepted.evidence


def test_solver_accepts_complete_negative_chain_diagnosis_not_mapping_truthiness():
    goal = next(
        row
        for row in goals_for("CALIBRATION", "G3")
        if row.sealed_expected_result["is_chain_map"] is False
    )
    trace = solve(goal.solver_visible(), build_operator_registry())
    assert trace.final_verdict == "PASS"
    assert trace.candidate_artifact is not None
    assert trace.candidate_artifact.value == goal.sealed_expected_result


def test_solver_recomputes_rotation_and_homothety_instead_of_vertex_count():
    registry = build_operator_registry()
    rotation = goals_for("CALIBRATION", "G10")[0]
    homothety = next(
        row
        for row in goals_for("CALIBRATION", "G11")
        if row.sealed_expected_result["homothetic"] is False
    )
    for goal in (rotation, homothety):
        trace = solve(goal.solver_visible(), registry)
        assert trace.final_verdict == "PASS", (goal.goal_id, trace.failure_reason)
        assert trace.verifier_chain[-1].passed


def test_terminal_dispatch_rejects_family_target_and_candidate_relabelling():
    goal = goals_for("CALIBRATION", "G1")[0].solver_visible()
    candidate = _candidate(goal, goals_for("CALIBRATION", "G1")[0].sealed_expected_result)
    assert verify_terminal_candidate(goal, candidate).passed
    assert not verify_terminal_candidate(replace(goal, family="G2"), candidate).passed
    assert not verify_terminal_candidate(
        replace(goal, target=replace(goal.target, target_id="forged")),
        candidate,
    ).passed
    assert not verify_terminal_candidate(
        goal,
        replace(candidate, semantic_type="BLINDED_INPUT_TYPE"),
    ).passed


def test_terminal_retyping_rejects_a_forged_routing_receipt():
    goal = goals_for("CALIBRATION", "G1")[0].solver_visible()
    blinded = replace(
        goal,
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in goal.inputs.items()
        },
    )
    inferred_rows = tuple(
        (key, artifact.artifact_type) for key, artifact in sorted(goal.inputs.items())
    )
    payload = {
        "inferred_root_types": inferred_rows,
        "ordered_operator_ids": (),
        "ambiguous_input_keys": (),
        "compatibility_model_digest": "a" * 64,
    }
    receipt = RoutingReceipt(
        "INFERRED",
        inferred_rows,
        (),
        (),
        "a" * 64,
        canonical_sha256(payload, domain="pct-routing-decision-v1"),
    )
    effective = dict(inferred_rows)
    typed, reason = _terminal_goal_view(blinded, effective, receipt)
    assert typed is not None and reason is None
    forged, forged_reason = _terminal_goal_view(
        blinded,
        effective,
        replace(receipt, decision_digest="0" * 64),
    )
    assert forged is None
    assert forged_reason == "routing decision digest mismatch"
