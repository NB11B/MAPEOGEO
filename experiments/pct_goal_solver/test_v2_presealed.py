import sympy as sp

from experiments.pct_goal_solver.model import OperatorFailure
from experiments.pct_goal_solver.v2 import (
    V2_REQUIRED_DERIVED_TYPES,
    build_v2_corpus,
    build_v2_operator_registry,
)


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
