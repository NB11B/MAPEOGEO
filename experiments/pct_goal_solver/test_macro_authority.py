"""Adversarial contract tests for production macro non-authority."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.macros import (
    audit_macro_proposals,
    synthesize_macros,
    validate_runtime_macro,
)
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import solve


class _ExplodingMacroIterable:
    def __iter__(self):
        raise AssertionError("authoritative solve evaluated untrusted macro input")


@pytest.fixture(scope="module")
def macro_fixture():
    registry = build_operator_registry()
    calibration = goals_for("CALIBRATION", "G10")
    traces = tuple(
        solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        for goal in calibration
    )
    proposals = synthesize_macros(
        calibration,
        traces,
        registry,
        min_distinct_goals=2,
    )
    proposal = next(
        row
        for row in proposals
        if row.primitive_ids
        == ("SUPPORT_FUNCTION_SAMPLE", "SUPPORT_SPECTRUM")
    )
    return registry, proposal


def test_authoritative_solve_never_evaluates_macro_iterable(macro_fixture):
    registry, _ = macro_fixture
    goal = goals_for("SEALED", "G10")[0].solver_visible()
    primitive = solve(goal, registry, typing_mode="EXPLICIT")
    observed = solve(
        goal,
        registry,
        typing_mode="EXPLICIT",
        macros=_ExplodingMacroIterable(),
    )
    assert observed == primitive


@pytest.mark.parametrize("budget", [0, 1, 2])
def test_forged_macro_cannot_rescue_below_path_budget(macro_fixture, budget):
    registry, proposal = macro_fixture
    goal = replace(
        goals_for("SEALED", "G10")[0].solver_visible(),
        search_budget=budget,
    )
    primitive = solve(goal, registry, typing_mode="EXPLICIT")
    forged = SimpleNamespace(
        macro_id="FORGED:RESCUE",
        primitive_ids=proposal.primitive_ids,
        certificate_digest=proposal.certificate_digest,
    )
    assert primitive.final_verdict == "NOT_ESTABLISHED"
    assert solve(goal, registry, typing_mode="EXPLICIT", macros=(forged,)) == primitive
    assert solve(goal, registry, typing_mode="EXPLICIT", macros=(proposal,)) == primitive


def test_plain_macro_spec_is_never_runtime_authority(macro_fixture):
    registry, proposal = macro_fixture
    valid, reason = validate_runtime_macro(proposal, registry)
    assert valid is False
    assert reason == "MACRO_EXECUTABLE_AUTHORITY_UNAVAILABLE"


def test_side_channel_is_fail_closed_and_fully_charges_authoritative_work(macro_fixture):
    registry, proposal = macro_fixture
    goal = goals_for("SEALED", "G10")[0].solver_visible()
    primitive = solve(goal, registry, typing_mode="EXPLICIT")
    report = audit_macro_proposals(
        primitive,
        (proposal, SimpleNamespace(macro_id="FORGED")),
        registry,
    )
    expected_total = (
        primitive.expanded_state_count
        + primitive.attempted_operator_count
        + primitive.primitive_execution_count
        + primitive.verifier_execution_count
    )
    assert report.authoritative_trace_digest
    assert report.proposal_count == 2
    assert report.replay_count == 0
    assert report.counterfactual_credit_count == 0
    assert report.actual_work_savings == 0
    assert report.total_work_charged == expected_total
    assert tuple(row.reason for row in report.discarded) == (
        "MACRO_EXECUTABLE_AUTHORITY_UNAVAILABLE",
        "UNTYPED_MACRO_PROPOSAL",
    )


def test_side_channel_discards_noncanonical_or_incomplete_primitive_evidence(macro_fixture):
    registry, proposal = macro_fixture
    goal = goals_for("SEALED", "G10")[0].solver_visible()
    primitive = solve(goal, registry, typing_mode="EXPLICIT")
    assert primitive.candidate_artifact is not None
    malformed = replace(
        primitive,
        candidate_artifact=replace(primitive.candidate_artifact, value=object()),
        attempted_operator_count=-1,
    )
    report = audit_macro_proposals(malformed, (proposal,), registry)
    assert report.authoritative_trace_digest == ""
    assert report.replay_count == 0
    assert report.counterfactual_credit_count == 0
    assert report.actual_work_savings == 0
    assert {row.reason for row in report.discarded} >= {
        "NONCANONICAL_PRIMITIVE_TRACE",
        "INVALID_PRIMITIVE_WORK_COUNTERS",
    }
