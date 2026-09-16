from dataclasses import replace

import sympy as sp

from experiments.pct_goal_solver.campaign import score_trace
from experiments.pct_goal_solver.compatibility import CompatibilityModel
from experiments.pct_goal_solver.macros import synthesize_macros
from experiments.pct_goal_solver.model import OperatorFailure
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v2 import (
    V2_REQUIRED_DERIVED_TYPES,
    build_v2_corpus,
    build_v2_operator_registry,
)


def _blind(visible):
    return replace(
        visible,
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in visible.inputs.items()
        },
    )


def _primitive_path(trace, registry):
    return tuple(
        operator_id
        for operator_id in trace.operator_path
        if operator_id in registry and operator_id != "VERIFY_CANDIDATE"
    )


def _cross_class(trace, registry):
    path = _primitive_path(trace, registry)
    exactness = {registry[operator_id].exactness_class for operator_id in path}
    representations = {registry[operator_id].representation_class for operator_id in path}
    return len(exactness) > 1 or len(representations) > 1


def _calibration_state():
    corpus = build_v2_corpus()
    registry = build_v2_operator_registry()
    calibration_traces = tuple(
        solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        for goal in corpus["CALIBRATION_V2"]
    )
    model = CompatibilityModel.fit(corpus["CALIBRATION_V2"], calibration_traces, registry)
    macros = synthesize_macros(corpus["CALIBRATION_V2"], calibration_traces, registry)
    return corpus, registry, calibration_traces, model, macros


def test_v2_corpus_is_fresh_and_carries_frozen_evidence_obligations():
    corpus = build_v2_corpus()
    assert {name: len(rows) for name, rows in corpus.items()} == {
        "CALIBRATION_V2": 36,
        "VALIDATION_V2": 12,
        "SEALED_V2": 24,
    }
    assert all("_v2:" in goal.goal_id for rows in corpus.values() for goal in rows)
    for rows in corpus.values():
        for goal in rows:
            required = tuple(dict(goal.constraints).get("required_derived_types", ()))
            assert required == V2_REQUIRED_DERIVED_TYPES[goal.family]


def test_v2_g2_supplies_both_observation_and_exact_matrix_views():
    goal = next(goal for goal in build_v2_corpus()["CALIBRATION_V2"] if goal.family == "G2")
    semantic_types = {artifact.semantic_type for artifact in goal.inputs.values()}
    assert {"OBSERVATION_MATRIX", "RATIONAL_MATRIX"} <= semantic_types


def test_v2_registry_adds_only_two_generic_symbolization_bridges():
    registry = build_v2_operator_registry()
    assert len(registry) == 35
    assert {"NUMERIC_RELATION_SYMBOLIZE", "AREA_SYMBOLIZE"} <= set(registry)

    g8 = next(goal for goal in build_v2_corpus()["CALIBRATION_V2"] if goal.family == "G8")
    fit = registry["NUMERIC_RELATION_FIT"].execute(g8.inputs, ())
    assert not isinstance(fit, OperatorFailure)
    symbolic = registry["NUMERIC_RELATION_SYMBOLIZE"].execute({"relation": fit}, ())
    assert not isinstance(symbolic, OperatorFailure)
    assert symbolic.semantic_type == "SYMBOLIC_EXPRESSION"
    assert symbolic.representation_class == "SYMBOLIC"
    assert symbolic.exactness_class == "SYMBOLIC"
    assert abs(float(sp.N(symbolic.value)) - float(fit.value)) < 1e-10
    assert registry["NUMERIC_RELATION_SYMBOLIZE"].verify((fit,), symbolic).passed


def test_v2_validation_reaches_frozen_composition_targets_before_sealed_execution():
    corpus = build_v2_corpus()
    registry = build_v2_operator_registry()
    traces = {
        goal.family: solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        for goal in corpus["VALIDATION_V2"]
    }
    scores = {
        goal.family: score_trace(goal, traces[goal.family])
        for goal in corpus["VALIDATION_V2"]
    }
    assert {family for family, score in scores.items() if score["correct"]} == {f"G{i}" for i in range(1, 13)}
    multi_step = {
        family for family, trace in traces.items()
        if scores[family]["correct_pass"] and len(_primitive_path(trace, registry)) >= 2
    }
    cross_class = {
        family for family, trace in traces.items()
        if scores[family]["correct_pass"] and _cross_class(trace, registry)
    }
    assert len(multi_step) >= 10
    assert len(cross_class) >= 3
    assert {"G6", "G8", "G9"} <= cross_class


def test_v2_validation_type_blinding_routes_all_families_without_sealed_data():
    corpus, registry, _, model, _ = _calibration_state()
    failures = {}
    for goal in corpus["VALIDATION_V2"]:
        trace = solve(
            _blind(goal.solver_visible()),
            registry,
            typing_mode="INFERRED",
            compatibility_model=model,
        )
        score = score_trace(goal, trace)
        if not score["correct"]:
            failures[goal.family] = (trace.final_verdict, trace.failure_reason, trace.operator_path)
    assert failures == {}


def test_v2_hybrid_blinded_validation_preserves_family_coverage_and_safety():
    corpus, registry, _, model, _ = _calibration_state()
    failures = {}
    for goal in corpus["VALIDATION_V2"]:
        trace = solve(
            _blind(goal.solver_visible()),
            registry,
            typing_mode="HYBRID",
            compatibility_model=model,
        )
        score = score_trace(goal, trace)
        if not score["correct"]:
            failures[goal.family] = (trace.final_verdict, trace.failure_reason, trace.operator_path)
    assert failures == {}


def test_v2_macros_preserve_validation_answers_and_reduce_search_before_sealing():
    corpus, registry, _, _, macros = _calibration_state()
    assert macros
    reductions = 0
    changes = {}
    for goal in corpus["VALIDATION_V2"]:
        primitive = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        synthesized = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT", macros=macros)
        primitive_score = score_trace(goal, primitive)
        synthesized_score = score_trace(goal, synthesized)
        if primitive_score["correct"] != synthesized_score["correct"]:
            changes[goal.family] = (primitive.final_verdict, synthesized.final_verdict)
        if primitive.candidate_artifact is not None and synthesized.candidate_artifact is not None:
            if primitive.candidate_artifact.value != synthesized.candidate_artifact.value:
                changes[goal.family] = (primitive.candidate_artifact.value, synthesized.candidate_artifact.value)
        if synthesized.expanded_state_count < primitive.expanded_state_count:
            reductions += 1
    assert changes == {}
    assert reductions >= 1
