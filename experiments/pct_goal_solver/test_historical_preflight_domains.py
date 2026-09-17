"""Fail-closed regressions for historical root domains and G6 binary32 views."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import struct

import pytest

from experiments.pct_goal_solver.goal_verifiers import (
    _fraction_to_binary32,
    validate_historical_goal_contract,
    verify_historical_goal,
)
from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.model import Artifact
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import solve


def _replace_root(family: str, key: str, value: object):
    goal = goals_for("CALIBRATION", family)[0].solver_visible()
    root = replace(goal.inputs[key], value=value)
    return replace(goal, inputs={**goal.inputs, key: root})


def _candidate(goal, value: object) -> Artifact:
    return Artifact(
        "candidate",
        goal.target.semantic_type,
        goal.target.representation_class,
        value,
        goal.target.exactness_class,
    )


@pytest.mark.parametrize(
    ("family", "key", "value"),
    (
        ("G1", "cumulative", (1, 2, 3)),
        ("G1", "cumulative", tuple(range(8))),
        ("G2", "observation_matrix", ()),
        ("G3", "edge_map", ((1,),)),
        ("G4", "barcode_a", ((0, 1, 1),)),
        ("G5", "graph_a", ((0, 0),)),
        ("G6", "numeric_matrix", ((0.0, 0.0, 0.0),) * 3),
        ("G7", "state", ()),
        ("G8", "trajectory", ((0, 0, 0, 1),)),
        ("G9", "offset", -1),
        ("G9", "body", ((0, 0), (2, 2), (0, 2), (2, 0))),
        ("G10", "body", ((0, 0), (1, 0), (2, 0))),
        ("G11", "body_b", ((0, 0), (1, 0), (2, 0))),
        ("G12", "lhs", "undeclared_symbol"),
    ),
)
def test_malformed_historical_math_domains_are_rejected_before_search(
    family: str,
    key: str,
    value: object,
) -> None:
    goal = _replace_root(family, key, value)

    contract = validate_historical_goal_contract(goal)
    assert contract.passed is False

    trace = solve(goal, build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "INVALID"
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_CONTRACT"
    assert trace.operator_path == ()
    assert trace.expanded_state_count == 0
    assert trace.attempted_operator_count == 0
    assert trace.primitive_execution_count == 0
    assert trace.verifier_execution_count == 0


@pytest.mark.parametrize(
    ("value", "expected_hex"),
    (
        (Fraction(0), "00000000"),
        (Fraction(1, 2**150), "00000000"),
        (Fraction(3, 2**150), "00000002"),
        (Fraction(1, 2**126) - Fraction(1, 2**150), "00800000"),
        (Fraction(1) + Fraction(1, 2**24), "3f800000"),
        (Fraction(1) + Fraction(1, 2**24) + Fraction(1, 2**80), "3f800001"),
        (Fraction(1) + Fraction(3, 2**24), "3f800002"),
        (-Fraction(1) - Fraction(1, 2**24) - Fraction(1, 2**80), "bf800001"),
        (Fraction(2**128) - Fraction(2**104), "7f7fffff"),
        (Fraction(2**128) - Fraction(2**103), "7f800000"),
    ),
)
def test_exact_fraction_to_binary32_boundaries(value: Fraction, expected_hex: str) -> None:
    rounded = _fraction_to_binary32(value)
    assert struct.pack("!f", rounded).hex() == expected_hex


def test_g6_binary32_view_is_rounded_once_from_the_exact_fraction() -> None:
    # q is strictly above the midpoint between 1 and the next binary32 value.
    # Converting q to binary64 first erases 2**-80 and creates an artificial tie
    # that rounds to 1.  Direct binary32 rounding must round upward instead.
    q = Fraction(1) + Fraction(1, 2**24) + Fraction(1, 2**80)
    next_binary32 = struct.unpack("!f", bytes.fromhex("3f800001"))[0]
    base = goals_for("CALIBRATION", "G6")[0].solver_visible()
    exact = ((q, 1), (1, 1))
    correct_numeric = ((next_binary32, 1.0), (1.0, 1.0))
    inputs = {
        **base.inputs,
        "exact_matrix": replace(base.inputs["exact_matrix"], value=exact),
        "numeric_matrix": replace(base.inputs["numeric_matrix"], value=correct_numeric),
    }
    goal = replace(base, inputs=inputs)

    assert validate_historical_goal_contract(goal).passed
    assert verify_historical_goal(goal, _candidate(goal, 2)).passed
    assert not verify_historical_goal(goal, _candidate(goal, 1)).passed

    double_rounded = replace(
        goal,
        inputs={
            **goal.inputs,
            "numeric_matrix": replace(goal.inputs["numeric_matrix"], value=((1.0, 1.0), (1.0, 1.0))),
        },
    )
    assert not validate_historical_goal_contract(double_rounded).passed
    assert not verify_historical_goal(double_rounded, _candidate(double_rounded, 1)).passed
