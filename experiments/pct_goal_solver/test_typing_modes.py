from dataclasses import replace

from experiments.pct_goal_solver.compatibility import CompatibilityModel, structural_descriptors
from experiments.pct_goal_solver.goals import build_goal_corpus, goals_for
from experiments.pct_goal_solver.operators import build_operator_registry
from experiments.pct_goal_solver.planner import solve


def _calibrated_model():
    corpus = build_goal_corpus()
    registry = build_operator_registry()
    traces = [
        solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        for goal in corpus["CALIBRATION"]
    ]
    return corpus, registry, traces, CompatibilityModel.fit(corpus["CALIBRATION"], traces, registry)


def test_inferred_model_never_reads_sealed_goals():
    corpus, _, _, model = _calibrated_model()
    assert not model.goal_ids & {g.goal_id for g in corpus["SEALED"]}
    assert model.goal_ids == {g.goal_id for g in corpus["CALIBRATION"]}


def test_structural_descriptors_do_not_contain_semantic_type_names():
    corpus = build_goal_corpus()
    known_types = {
        artifact.semantic_type
        for split in corpus.values()
        for goal in split
        for artifact in goal.inputs.values()
    }
    tokens = set()
    for goal in corpus["CALIBRATION"]:
        tokens.update(structural_descriptors(goal.solver_visible().inputs))
    assert not tokens & known_types


def test_inferred_mode_transfers_across_exact_symbolic_numeric():
    _, registry, _, model = _calibrated_model()
    for family in ("G1", "G7", "G9"):
        goal = goals_for("SEALED", family)[0]
        trace = solve(
            goal.solver_visible(),
            registry,
            typing_mode="INFERRED",
            compatibility_model=model,
        )
        assert trace.final_verdict in {"PASS", "NOT_ESTABLISHED", "NOT_APPLICABLE"}
        assert trace.final_verdict not in {"INVALID", "ERROR"}


def test_inferred_mode_can_solve_with_input_semantic_types_blinded():
    _, registry, _, model = _calibrated_model()
    visible = goals_for("SEALED", "G8")[0].solver_visible()
    blinded = replace(
        visible,
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in visible.inputs.items()
        },
    )
    explicit = solve(blinded, registry, typing_mode="EXPLICIT")
    inferred = solve(blinded, registry, typing_mode="INFERRED", compatibility_model=model)
    assert explicit.final_verdict == "NOT_ESTABLISHED"
    assert inferred.final_verdict == "PASS"
    assert "NUMERIC_RELATION_FIT" in inferred.operator_path


def test_hybrid_mode_preserves_hard_compatibility_barrier():
    _, registry, _, model = _calibrated_model()
    goal = goals_for("SEALED", "G9")[0]
    trace = solve(
        goal.solver_visible(),
        registry,
        typing_mode="HYBRID",
        compatibility_model=model,
    )
    # A matrix operator may rank highly under an inferred model, but hybrid execution
    # must never admit it into a geometry solution path.
    assert "EXACT_MATRIX_RANK_Q" not in trace.operator_path
    assert trace.final_verdict in {"PASS", "NOT_APPLICABLE", "NOT_ESTABLISHED"}


def test_inferred_operator_ranking_is_deterministic():
    _, registry, _, model = _calibrated_model()
    goal = goals_for("SEALED", "G10")[0].solver_visible()
    a = solve(goal, registry, typing_mode="INFERRED", compatibility_model=model)
    b = solve(goal, registry, typing_mode="INFERRED", compatibility_model=model)
    assert a.operator_path == b.operator_path
    assert a.final_verdict == b.final_verdict
