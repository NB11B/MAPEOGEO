from dataclasses import replace

from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import solve


def _sealed(family: str, index: int = 0):
    return goals_for("SEALED", family)[index]


def test_explicit_planner_solves_multistep_exact_goal():
    goal = _sealed("G1")
    trace = solve(goal.solver_visible(), build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "PASS"
    assert len(trace.operator_path) >= 2
    assert trace.operator_path[-1] == "VERIFY_CANDIDATE"
    assert trace.verifier_chain[-1].passed
    assert trace.candidate_artifact is not None


def test_legacy_statewide_derived_type_list_is_not_a_historical_contract_field():
    visible = _sealed("G1").solver_visible()
    visible = replace(
        visible,
        constraints=visible.constraints + (("required_derived_types", ("BOOLEAN_ZETA_SIGNAL",)),),
    )
    trace = solve(visible, build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "INVALID"
    assert trace.operator_path == ()
    assert trace.derived_obligations == ()
    assert trace.refusal is not None
    assert trace.refusal.code == "INVALID_GOAL_CONTRACT"


def test_explicit_planner_refuses_nonconvex_steiner_goal():
    goal = next(g for g in goals_for("SEALED", "G9") if g.sealed_expected_result == "NOT_APPLICABLE")
    trace = solve(goal.solver_visible(), build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "NOT_APPLICABLE"
    assert "STEINER_OFFSET_PREDICT" in trace.operator_path


def test_budget_exhaustion_is_not_established():
    goal = _sealed("G1").solver_visible()
    trace = solve(replace(goal, search_budget=0), build_operator_registry(), typing_mode="EXPLICIT")
    assert trace.final_verdict == "NOT_ESTABLISHED"
    assert trace.candidate_artifact is None


def test_explicit_search_is_deterministic():
    goal = _sealed("G10").solver_visible()
    registry = build_operator_registry()
    a = solve(goal, registry, typing_mode="EXPLICIT")
    b = solve(goal, registry, typing_mode="EXPLICIT")
    assert a.final_verdict == b.final_verdict
    assert a.operator_path == b.operator_path
    assert a.expanded_state_count == b.expanded_state_count
    assert a.primitive_execution_count == b.primitive_execution_count


def test_no_positive_result_without_terminal_verifier():
    goal = _sealed("G12").solver_visible()
    trace = solve(goal, build_operator_registry(), typing_mode="EXPLICIT")
    if trace.final_verdict == "PASS":
        assert trace.verifier_chain
        assert trace.verifier_chain[-1].passed
        assert trace.operator_path[-1] == "VERIFY_CANDIDATE"
