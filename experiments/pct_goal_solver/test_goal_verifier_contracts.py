"""Review regressions: complete contracts, bounded domains and identified fits."""
from dataclasses import FrozenInstanceError, is_dataclass, replace
from fractions import Fraction
import math

import pytest
import sympy as sp

from experiments.pct_goal_solver.test_goal_verifiers import _goal, _module, _verify, SQUARE
from experiments.pct_goal_solver.goals import build_goal_corpus
from experiments.pct_goal_solver.historical_oracles import build_historical_reference


def test_full_contract_registry_is_immutable_and_declares_its_numeric_domain():
    contracts = _module().HISTORICAL_GOAL_CONTRACTS
    contract = contracts["G8"]
    assert is_dataclass(contract), "a type tuple does not bind the historical goal contract"
    with pytest.raises(FrozenInstanceError):
        contract.family = "G1"
    assert contract.target.objective == "DISCOVER_AND_VERIFY"
    assert contract.tolerance_policy.metric == "absolute-least-squares-coefficient-error"
    assert contract.tolerance_policy.fit_tolerance > 0
    assert contract.resource_limits.max_matrix_dimension > 0


@pytest.mark.parametrize("change", [
    {"target_id": "forged"}, {"objective": "FORGED"}, {"metadata": (("trusted", True),)},
])
def test_full_target_identity_cannot_be_relabelled(change):
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)})
    assert _verify(goal, (1, 2, 3, 4)).passed
    assert not _verify(replace(goal, target=replace(goal.target, **change)), (1, 2, 3, 4)).passed


@pytest.mark.parametrize("change", [
    {"semantic_type": "BLINDED_INPUT_TYPE"}, {"representation_class": "WRONG"},
    {"exactness_class": "NUMERICAL"}, {"metadata": (("rank", 2), ("extra", 1))},
    {"metadata": (("rank", 2), ("rank", 2))}, {"metadata": (("rank", True),)},
])
def test_root_artifact_contract_and_metadata_are_closed(change):
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)})
    root = replace(goal.inputs["cumulative"], **change)
    assert not _verify(replace(goal, inputs={"cumulative": root}), (1, 2, 3, 4)).passed


def test_extra_roots_are_rejected():
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)})
    assert not _verify(replace(goal, inputs={**goal.inputs, "hidden": goal.inputs["cumulative"]}), (1, 2, 3, 4)).passed


def test_extra_candidate_metadata_is_rejected():
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)})
    assert not _verify(goal, (1, 2, 3, 4), (("ignored_claim", True),)).passed


@pytest.mark.parametrize("constraints", [(), (("lattice_rank", 2), ("extra", True)), (("lattice_rank", True),)])
def test_constraint_schema_is_not_optional_or_extensible(constraints):
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)}, constraints=constraints)
    assert not _verify(goal, (1, 2, 3, 4)).passed


@pytest.mark.parametrize("budget", [True, 1.5, -1, 10**9])
def test_search_budget_must_be_an_exact_bounded_nonnegative_integer(budget):
    goal = replace(_goal("G1", {"cumulative": (1, 3, 4, 10)}), search_budget=budget)
    assert not _verify(goal, (1, 2, 3, 4)).passed


def test_exact_families_do_not_accept_an_unbound_numeric_tolerance():
    assert not _verify(_goal("G1", {"cumulative": (1, 3, 4, 10)}, tolerance=1), (1, 2, 3, 4)).passed


@pytest.mark.parametrize("coefficient", [0, 10**6, 10**12])
def test_tiny_trajectory_excitation_is_rejected_even_when_a_coefficient_is_unique(coefficient):
    goal = _goal(
        "G8",
        {"trajectory": tuple((time, Fraction(time, 10**20), 0, 1) for time in range(4))},
    )
    assert not _verify(goal, coefficient).passed


def test_identified_coefficient_error_is_not_raw_trajectory_residual():
    goal = _goal(
        "G8",
        {"trajectory": tuple((time, Fraction(time, 10**4), 0, 1) for time in range(4))},
    )
    assert _verify(goal, 0).passed
    assert not _verify(goal, Fraction(1, 10**5)).passed


def test_least_squares_fit_must_meet_its_separate_normalized_tolerance():
    goal = _goal("G8", {"trajectory": ((0, 0, 0, 1), (1, 1, 2, 1), (2, 2, 3, 1))})
    assert not _verify(goal, Fraction(-22, 5)).passed


@pytest.mark.parametrize("symbol", ["pi", sp.Symbol("pi"), sp.Symbol("E"), sp.Symbol("_hidden"), "for", sp.Symbol("for")])
def test_state_symbols_cannot_collide_with_constants_or_reserved_names(symbol):
    goal = _goal("G7", {"state": (symbol,), "generator": ((1,),), "candidate_invariant": "pi"})
    assert not _verify(goal, True).passed


@pytest.mark.parametrize("expression", [sp.sqrt(2), sp.sin(1), sp.E, sp.gamma(sp.Rational(1, 3)), sp.Float("0.5")])
def test_prebuilt_sympy_expressions_obey_the_same_exact_grammar_as_strings(expression):
    goal = _goal("G12", {"lhs": expression, "rhs": expression}, constraints=(("symbols", ()),))
    assert not _verify(goal, True).passed


def test_exact_string_and_prebuilt_symbolic_forms_agree():
    x = sp.Symbol("x", real=True)
    for expression in ("x**2 + 2*x + 1", x**2 + 2*x + 1):
        goal = _goal("G12", {"lhs": expression, "rhs": "(x+1)**2"}, constraints=(("symbols", (x,)),))
        assert _verify(goal, True).passed


@pytest.mark.parametrize("rhs,identity", [("1/10", True), ("0", False)])
def test_whitespace_cannot_change_the_value_of_a_decimal_token(rhs, identity):
    goal = _goal("G12", {"lhs": " 0.1 ", "rhs": rhs}, constraints=(("symbols", ()),))
    assert _verify(goal, identity).passed
    assert not _verify(goal, not identity).passed


@pytest.mark.parametrize("expression", ["1/0", "0/0", "1/(x-x)", sp.Pow(0, -1, evaluate=False)])
def test_unevaluated_zero_denominators_are_not_constant_invariants(expression):
    goal = _goal("G7", {"state": ("x",), "generator": ((0,),), "candidate_invariant": expression})
    assert not _verify(goal, True).passed


def test_unrecomputed_graph_diagnostics_are_rejected():
    graph = _goal("G5", {"graph_a": ((0, 1),), "graph_b": ((2, 3),)})
    assert not _verify(graph, {"distinct": False, "level": "DEGREE"}).passed


def test_unrecomputed_spectrum_diagnostics_are_rejected():
    square = _goal("G10", {"body": SQUARE})
    assert not _verify(square, {"order": 4, "active_harmonics": (7,), "energy": (999,)}).passed


def test_graph_domain_cannot_smuggle_isolated_vertices_through_metadata():
    goal = _goal("G5", {"graph_a": ((0, 1),), "graph_b": ((0, 1),)})
    root = replace(goal.inputs["graph_a"], metadata=(("vertices", (0, 1, 2)),))
    assert not _verify(replace(goal, inputs={**goal.inputs, "graph_a": root}), {"distinct": False}).passed


def test_graph_domain_rejects_duplicate_edges_instead_of_silently_collapsing_them():
    goal = _goal("G5", {"graph_a": ((0, 1), (1, 0)), "graph_b": ((0, 1),)})
    assert not _verify(goal, {"distinct": False}).passed


@pytest.mark.parametrize("expression", ["x**100", "x+" * 40 + "0", " " * 5000 + "x"])
def test_symbolic_work_limits_are_checked_before_algebra(expression):
    goal = _goal("G12", {"lhs": expression, "rhs": expression}, constraints=(("symbols", ("x",)),))
    assert not _verify(goal, True).passed


def test_boolean_work_limits_fail_closed():
    assert not _verify(_goal("G1", {"cumulative": (0,) * 512}), (0,) * 512).passed


def test_integer_bit_work_limits_fail_closed():
    assert not _verify(_goal("G1", {"cumulative": (1 << 5000,)}), (1 << 5000,)).passed


def test_symbolic_float_size_is_checked_before_allocating_its_exact_integer(monkeypatch):
    huge = sp.Float("1e100000", 20)
    goal = _goal("G9", {"body": SQUARE, "offset": huge})
    def prohibited_conversion(*args, **kwargs):
        raise AssertionError("unbounded exact conversion ran before the size check")
    # An unsafe backend allocation is replaced, not the validation under test.
    monkeypatch.setattr(_module().sp, "Rational", prohibited_conversion)
    result = _verify(goal, 0)
    assert not result.passed and "resource limit" in result.reason


def test_matrix_domain_has_deterministic_bounds():
    matrix = tuple(tuple(int(i == j) for j in range(17)) for i in range(17))
    assert not _verify(_goal("G6", {"exact_matrix": matrix}), 17).passed


def test_graph_domain_has_deterministic_bounds():
    graph = tuple((i, (i + 1) % 13) for i in range(13))
    assert not _verify(_goal("G5", {"graph_a": graph, "graph_b": graph}), {"distinct": False}).passed


def test_barcode_domain_has_deterministic_bounds():
    barcode = ((0, 0, 1),) * 65
    assert not _verify(_goal("G4", {"barcode_a": barcode, "barcode_b": barcode}), {"distinct": False, "level": "NONE"}).passed


def test_polygon_domain_has_deterministic_bounds():
    polygon = tuple((math.cos(2 * math.pi * i / 33), math.sin(2 * math.pi * i / 33)) for i in range(33))
    assert not _verify(_goal("G10", {"body": polygon}), {"order": 33}).passed


def test_numeric_subclasses_cannot_override_exact_evidence_conversions():
    class ForgedInt(int):
        def __int__(self):
            return 0
    assert not _verify(_goal("G1", {"cumulative": (ForgedInt(9),)}), (0,)).passed


def test_numeric_matrix_must_be_the_declared_dtype_view_of_exact_matrix():
    goal = _goal(
        "G6",
        {
            "exact_matrix": ((1, 0), (0, 1)),
            "numeric_matrix": ((0.0, 0.0), (0.0, 0.0)),
        },
    )
    assert not _verify(goal, 2).passed


def test_nilpotent_generator_contract_is_mandatory_and_recomputed():
    base = _goal(
        "G7",
        {"generator": ((0, 1), (0, 0)), "state": ("x", "y"), "candidate_invariant": "y"},
    )
    good = replace(
        base,
        inputs={**base.inputs, "generator": replace(base.inputs["generator"], metadata=(("nilpotency_bound", 2),))},
    )
    assert _verify(good, True).passed

    no_bound = replace(
        good,
        inputs={**good.inputs, "generator": replace(good.inputs["generator"], metadata=())},
    )
    assert not _verify(no_bound, True).passed

    nonnilpotent = replace(
        good,
        inputs={
            **good.inputs,
            "generator": replace(good.inputs["generator"], value=((1, 0), (0, 1))),
            "candidate_invariant": replace(good.inputs["candidate_invariant"], value="1"),
        },
    )
    assert not _verify(nonnilpotent, True).passed

    state_dependent = replace(
        good,
        inputs={
            **good.inputs,
            "generator": replace(good.inputs["generator"], value=((0, "x"), (0, 0))),
        },
    )
    assert not _verify(state_dependent, True).passed


def test_chain_duplicate_evidence_is_rejected_even_when_python_equality_is_lossy():
    goal = _goal(
        "G3",
        {
            "source_boundary": ((-1,), (1,)),
            "target_boundary": ((-1,), (1,)),
            "vertex_map": ((1, 0), (0, 1)),
            "edge_map": ((2,),),
        },
        constraints=(("localize_if_invalid", True),),
    )
    value = {
        "is_chain_map": False,
        "residual": ((-1,), (1,)),
        "residual_rows": (0, 1),
        "map_columns": (0,),
    }
    assert not _verify(
        goal,
        value,
        (("residual_rows", (False, True)), ("map_columns", (False,))),
    ).passed


def test_relation_fit_contract_does_not_accept_a_false_physical_model_label():
    goal = _goal(
        "G8",
        {"trajectory": ((0, 1, 1, 1), (1, 4, 2, 1), (2, 9, 3, 1), (3, 16, 4, 1))},
    )
    trajectory = replace(
        goal.inputs["trajectory"],
        metadata=(("model", "parallel_body_2d"),),
    )
    # A stale physical-model label must not be silently reinterpreted as the
    # narrower algebraic relation contract, even when the rows fit it.
    assert not _verify(replace(goal, inputs={"trajectory": trajectory}), -1).passed


def test_rotation_order_is_invariant_under_exact_orthogonal_coordinates():
    polygon = (
        (Fraction(-1), Fraction(-1)),
        (Fraction(1), Fraction(-1)),
        (Fraction(50067, 50000), Fraction(1)),
        (Fraction(-1), Fraction(1)),
    )
    rotated = tuple(
        (
            Fraction(3, 5) * x - Fraction(4, 5) * y,
            Fraction(4, 5) * x + Fraction(3, 5) * y,
        )
        for x, y in polygon
    )
    first = _goal("G10", {"body": polygon}, tolerance=0.001)
    second = _goal("G10", {"body": rotated}, tolerance=0.001)
    first_results = [order for order in range(1, 5) if _verify(first, {"order": order}).passed]
    second_results = [order for order in range(1, 5) if _verify(second, {"order": order}).passed]
    assert first_results == second_results


def test_string_and_sympy_symbolic_forms_share_post_normalization_limits():
    x = sp.Symbol("x")
    for expression in ("x**16*x**16", x**32):
        goal = _goal(
            "G12",
            {"lhs": expression, "rhs": expression},
            constraints=(("symbols", ("x",)),),
        )
        assert not _verify(goal, True).passed


def test_matrix_bit_complexity_is_bounded_before_exact_rank():
    huge = 1 << 255
    matrix = tuple(
        tuple(huge + (1 if row == column else 0) for column in range(16))
        for row in range(16)
    )
    assert not _verify(_goal("G6", {"exact_matrix": matrix}), 16).passed


@pytest.mark.parametrize("tolerance", [0.001, Fraction(1, 1000)])
def test_declared_rotation_tolerance_boundary_accepts_exact_symmetry(tolerance):
    assert _verify(_goal("G10", {"body": SQUARE}, tolerance=tolerance), {"order": 4}).passed


@pytest.mark.parametrize("goal", [goal for goals in build_goal_corpus().values() for goal in goals], ids=lambda g: g.goal_id)
def test_frozen_corpus_contracts_have_independent_historical_witnesses(goal):
    """A separate bounded algorithm derives every campaign expectation."""
    visible = goal.solver_visible()
    reference = build_historical_reference(visible)
    assert reference.implementation_independent and reference.authoritative
    if reference.expected_verdict == "NOT_APPLICABLE":
        assert goal.sealed_expected_result == "NOT_APPLICABLE"
        assert not _verify(visible, 0.0).passed
        return
    assert reference.expected_verdict == "PASS"
    sealed = _verify(visible, goal.sealed_expected_result)
    assert sealed.passed, (goal.goal_id, "stored campaign result", sealed.reason)
    result = _verify(visible, reference.candidate_value)
    assert result.passed, (goal.goal_id, result.reason, reference.candidate_value)
