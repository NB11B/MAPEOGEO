from __future__ import annotations

from dataclasses import replace

import pytest

from .model import Artifact, OperatorFailure
from .v0_20_contracts import NEW_V0_20_FAMILIES
from .v0_20_goals import build_v0_20_corpus
from .v0_20_operators import build_v0_20_operator_registry
from .v0_20_terminal_verification import verify_terminal_candidate
from .v0_20_verifiers import verify_v0_20_goal


def _goal(family: str):
    return next(
        goal
        for goal in build_v0_20_corpus()["CALIBRATION_V0_20"]
        if goal.family == family
    )


def _reference_candidate(goal):
    registry = build_v0_20_operator_registry()
    artifacts = dict(goal.inputs)
    candidate = None
    for operator_id in goal.sealed_reference_path:
        if operator_id == "VERIFY_CANDIDATE":
            continue
        specification = registry[operator_id]
        output = specification.execute(artifacts, tuple(goal.constraints))
        assert not isinstance(output, OperatorFailure)
        assert specification.verify(tuple(artifacts.values()), output).passed
        artifacts[f"derived:{operator_id}"] = output
        candidate = output
    assert candidate is not None
    return candidate


@pytest.mark.parametrize("family", NEW_V0_20_FAMILIES)
def test_compatibility_entrypoint_is_exactly_the_strict_authority_for_valid_candidates(
    family: str,
) -> None:
    goal = _goal(family)
    candidate = _reference_candidate(goal)
    strict = verify_v0_20_goal(goal.solver_visible(), candidate)

    assert strict.passed, (goal.goal_id, strict)
    assert verify_terminal_candidate(goal.solver_visible(), candidate) == strict


def test_compatibility_entrypoint_rejects_a_legacy_shaped_forgery() -> None:
    current = _goal("F3").solver_visible()
    malformed = replace(
        current,
        inputs={
            "pair": Artifact(
                artifact_id=f"{current.goal_id}:pair",
                semantic_type="INTEGER_PAIR",
                representation_class="PAIR",
                value=(30, 18),
                exactness_class="EXACT",
            )
        },
    )
    forged = Artifact(
        artifact_id="forged:legacy-bezout",
        semantic_type=current.target.semantic_type,
        representation_class=current.target.representation_class,
        exactness_class=current.target.exactness_class or "EXACT",
        value={"gcd": 6, "coeff_a": -1, "coeff_b": 2},
        metadata=(("trusted", True),),
        provenance=("unregistered-step",),
    )
    strict = verify_v0_20_goal(malformed, forged)

    assert not strict.passed
    assert strict.reason == "GOAL_CONTRACT_MISMATCH"
    assert verify_terminal_candidate(malformed, forged) == strict
