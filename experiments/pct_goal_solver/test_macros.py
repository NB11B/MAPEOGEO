from experiments.pct_goal_solver.goals import goals_for
from experiments.pct_goal_solver.macros import synthesize_macros
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import solve


def test_single_trace_cannot_create_macro():
    registry = build_operator_registry()
    goal = goals_for("CALIBRATION", "G10")[0]
    trace = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
    assert synthesize_macros((goal,), (trace,), registry, min_distinct_goals=2) == ()


def test_repeated_verified_path_synthesizes_replayable_macro():
    registry = build_operator_registry()
    goals = goals_for("CALIBRATION", "G10")
    traces = tuple(solve(goal.solver_visible(), registry, typing_mode="EXPLICIT") for goal in goals)
    macros = synthesize_macros(goals, traces, registry, min_distinct_goals=2)
    macro = next(
        macro
        for macro in macros
        if macro.primitive_ids == ("SUPPORT_FUNCTION_SAMPLE", "SUPPORT_SPECTRUM")
    )
    assert macro.support_goal_ids >= {goal.goal_id for goal in goals[:2]}
    assert macro.terminal_output_type == "ROTATIONAL_HARMONIC_ORDER"


def test_synthesized_mode_replays_macro_without_changing_result():
    registry = build_operator_registry()
    calibration = goals_for("CALIBRATION", "G10")
    traces = tuple(solve(goal.solver_visible(), registry, typing_mode="EXPLICIT") for goal in calibration)
    macros = synthesize_macros(calibration, traces, registry, min_distinct_goals=2)
    goal = goals_for("SEALED", "G10")[0]
    primitive = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
    synthesized = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT", macros=macros)
    assert primitive.final_verdict == synthesized.final_verdict == "PASS"
    assert primitive.candidate_artifact is not None
    assert synthesized.candidate_artifact is not None
    assert primitive.candidate_artifact.value == synthesized.candidate_artifact.value
    assert synthesized.macro_ids
    assert synthesized.expanded_state_count <= primitive.expanded_state_count
