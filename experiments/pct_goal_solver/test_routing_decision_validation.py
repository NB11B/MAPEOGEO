from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.pct_goal_solver.canonical import canonical_sha256
from experiments.pct_goal_solver.compatibility import CompatibilityModel, RoutingDecision
from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.model import ArtifactType
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v0_20_goals import build_v0_20_corpus
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry


def _blind(goal):
    return replace(
        goal,
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in goal.inputs.items()
        },
    )


def _decision_with_digest(decision: RoutingDecision, **changes) -> RoutingDecision:
    changed = replace(decision, **changes)
    return replace(
        changed,
        decision_digest=canonical_sha256(
            {
                "inferred_root_types": changed.inferred_root_types,
                "ordered_operator_ids": changed.ordered_operator_ids,
                "ambiguous_input_keys": changed.ambiguous_input_keys,
                "compatibility_model_digest": changed.compatibility_model_digest,
            },
            domain="pct-routing-decision-v1",
        ),
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "unknown_operator",
        "duplicate_operator",
        "unknown_ambiguity_key",
        "missing_root",
        "changed_structural_class",
        "non_string_semantic_type",
        "exploding_decision_digest",
        "wrong_digest",
    ),
)
def test_malformed_routing_decisions_fail_closed(monkeypatch, mutation: str) -> None:
    registry = build_operator_registry()
    calibration = goals_for("CALIBRATION", "G8")[0]
    calibration_trace = solve(calibration.solver_visible(), registry)
    model = CompatibilityModel.fit((calibration,), (calibration_trace,), registry)
    visible = _blind(calibration.solver_visible())
    valid = model.routing_decision(visible.inputs, registry)

    if mutation == "unknown_operator":
        bad = _decision_with_digest(
            valid,
            ordered_operator_ids=("NOT_IN_REGISTRY",) + valid.ordered_operator_ids[1:],
        )
    elif mutation == "duplicate_operator":
        bad = _decision_with_digest(
            valid,
            ordered_operator_ids=(valid.ordered_operator_ids[0],) + valid.ordered_operator_ids[:-1],
        )
    elif mutation == "unknown_ambiguity_key":
        bad = _decision_with_digest(valid, ambiguous_input_keys=("not_a_goal_input",))
    elif mutation == "missing_root":
        bad = _decision_with_digest(valid, inferred_root_types=valid.inferred_root_types[:-1])
    elif mutation == "changed_structural_class":
        key, artifact_type = valid.inferred_root_types[0]
        forged = ArtifactType(
            artifact_type.semantic_type,
            "FORGED_REPRESENTATION",
            artifact_type.exactness_class,
        )
        bad = _decision_with_digest(
            valid,
            inferred_root_types=((key, forged),) + valid.inferred_root_types[1:],
        )
    elif mutation == "non_string_semantic_type":
        key, artifact_type = valid.inferred_root_types[0]
        forged = ArtifactType(
            object(),  # type: ignore[arg-type]
            artifact_type.representation_class,
            artifact_type.exactness_class,
        )
        bad = replace(
            valid,
            inferred_root_types=((key, forged),) + valid.inferred_root_types[1:],
        )
    elif mutation == "exploding_decision_digest":
        class ExplodingDigest:
            def __eq__(self, other):
                raise AssertionError("untrusted digest equality was invoked")

        bad = replace(valid, decision_digest=ExplodingDigest())
    else:
        bad = replace(valid, decision_digest="0" * 64)

    monkeypatch.setattr(
        CompatibilityModel,
        "routing_decision",
        lambda self, artifacts, live_registry: bad,
    )
    trace = solve(
        visible,
        registry,
        typing_mode="INFERRED",
        compatibility_model=model,
    )

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_ROUTING_DECISION"


def test_non_compatibility_model_fails_closed_without_calling_it() -> None:
    class ExplodingModel:
        def routing_decision(self, artifacts, registry):
            raise AssertionError("untrusted model was called")

    goal = _blind(goals_for("CALIBRATION", "G8")[0].solver_visible())
    trace = solve(
        goal,
        build_operator_registry(),
        typing_mode="INFERRED",
        compatibility_model=ExplodingModel(),
    )

    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_COMPATIBILITY_MODEL"


def test_rehashed_decision_cannot_suppress_known_x2_ambiguity(monkeypatch) -> None:
    registry = build_v0_20_operator_registry()
    calibration = next(
        goal
        for goal in build_v0_20_corpus()["CALIBRATION_V0_20"]
        if goal.family == "X2"
    )
    calibration_trace = solve(calibration.solver_visible(), registry)
    model = CompatibilityModel.fit((calibration,), (calibration_trace,), registry)
    visible = _blind(calibration.solver_visible())
    valid = model.routing_decision(visible.inputs, registry)
    assert set(valid.ambiguous_input_keys) == {"g2", "g3"}

    forged = _decision_with_digest(
        valid,
        inferred_root_types=tuple(
            (key, calibration.inputs[key].artifact_type)
            for key in sorted(calibration.inputs)
        ),
        ambiguous_input_keys=(),
    )
    monkeypatch.setattr(
        CompatibilityModel,
        "routing_decision",
        lambda self, artifacts, live_registry: forged,
    )

    trace = solve(
        visible,
        registry,
        typing_mode="INFERRED",
        compatibility_model=model,
    )

    assert trace.final_verdict == "INVALID"
    assert trace.candidate_artifact is None
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_ROUTING_DECISION"
