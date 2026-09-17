import sympy as sp
import pytest

from experiments.pct_goal_solver.bridge_operators import (
    build_cross_representation_operator_registry,
)
from experiments.pct_goal_solver.model import OperatorFailure
from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v2 import (
    V2_REQUIRED_DERIVED_TYPES,
    build_legacy_v2_shaped_fixture,
    build_v2_corpus,
)
from experiments.pct_goal_solver.v2_campaign import FrozenV2ReplayError


def test_legacy_v2_reconstruction_is_not_labeled_as_the_frozen_corpus():
    fixture = build_legacy_v2_shaped_fixture()
    assert fixture.status == "CURRENT_BUILDERS_NOT_FROZEN_CORPUS"
    corpus = fixture.splits
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


def test_historical_v2_corpus_api_refuses_current_builder_substitution():
    with pytest.raises(FrozenV2ReplayError):
        build_v2_corpus()


def test_legacy_v2_g2_reconstruction_supplies_both_matrix_views():
    corpus = build_legacy_v2_shaped_fixture().splits
    goal = next(goal for goal in corpus["CALIBRATION_V2"] if goal.family == "G2")
    semantic_types = {artifact.semantic_type for artifact in goal.inputs.values()}
    assert {"OBSERVATION_MATRIX", "RATIONAL_MATRIX"} <= semantic_types


def test_legacy_v2_registry_reconstruction_keeps_bridge_smoke_coverage():
    registry = build_cross_representation_operator_registry()
    assert len(registry) == 35
    assert {"NUMERIC_RELATION_SYMBOLIZE", "AREA_SYMBOLIZE"} <= set(registry)

    corpus = build_legacy_v2_shaped_fixture().splits
    g8 = next(goal for goal in corpus["CALIBRATION_V2"] if goal.family == "G8")
    fit = registry["NUMERIC_RELATION_FIT"].execute(g8.inputs, ())
    assert not isinstance(fit, OperatorFailure)
    symbolic = registry["NUMERIC_RELATION_SYMBOLIZE"].execute({"relation": fit}, ())
    assert not isinstance(symbolic, OperatorFailure)
    assert symbolic.semantic_type == "SYMBOLIC_EXPRESSION"
    assert symbolic.representation_class == "SYMBOLIC"
    assert symbolic.exactness_class == "SYMBOLIC"
    assert abs(float(sp.N(symbolic.value)) - float(fit.value)) < 1e-10
    assert registry["NUMERIC_RELATION_SYMBOLIZE"].verify((fit,), symbolic).passed


def _assert_no_execution(trace):
    assert trace.final_verdict == "INVALID"
    assert trace.operator_path == ()
    assert trace.expanded_state_count == 0
    assert trace.primitive_execution_count == 0
    assert trace.candidate_artifact is None
    assert trace.derived_obligations == ()
    assert trace.refusal is not None


def test_legacy_v2_contract_extensions_are_quarantined_by_current_runtime():
    corpus = build_legacy_v2_shaped_fixture().splits
    registry = build_cross_representation_operator_registry()
    for goal in corpus["VALIDATION_V2"]:
        trace = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        _assert_no_execution(trace)
        assert trace.refusal.code == "INVALID_GOAL_CONTRACT"
