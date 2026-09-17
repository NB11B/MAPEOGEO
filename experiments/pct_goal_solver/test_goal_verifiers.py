"""Adversarial root-recomputation tests; expectations are hand-derived fixtures."""
from dataclasses import replace
from fractions import Fraction
import importlib
import importlib.util
import math

import pytest
import sympy as sp

from experiments.pct_goal_solver.model import Artifact
from experiments.pct_goal_solver.goals import goals_for


CONTRACTS = {
    "G1": ("BOOLEAN_ATOMIC_SIGNAL", "FINITE_LATTICE", "EXACT", "EXACT_EQUALITY"),
    "G2": ("IDENTIFIABILITY_RESULT", "MATRIX", "EXACT", "EXACT_LINEAR_ALGEBRA"),
    "G3": ("CHAIN_DIAGNOSIS", "CHAIN", "EXACT", "CHAIN_RESIDUAL"),
    "G4": ("REPRESENTATION_SEPARATION", "PERSISTENCE", "EXACT", "EXACT_EQUALITY"),
    "G5": ("GRAPH_DISTINGUISHABILITY", "GRAPH", "EXACT", "GRAPH_ISOMORPHISM_CONTROL"),
    "G6": ("MATRIX_RANK", "MATRIX", "EXACT", "EXACT_LINEAR_ALGEBRA"),
    "G7": ("INVARIANT_VERDICT", "SYMBOLIC", "SYMBOLIC", "SYMBOLIC_IDENTITY"),
    "G8": ("NUMERIC_RELATION", "NUMERICAL", "NUMERICAL", "NUMERIC_THEN_SYMBOLIC"),
    "G9": ("AREA", "GEOMETRY", "NUMERICAL", "GEOMETRIC_NUMERICAL"),
    "G10": ("ROTATIONAL_HARMONIC_ORDER", "NUMERICAL", "NUMERICAL", "SPECTRAL_NUMERICAL"),
    "G11": ("HOMOTHETY_VERDICT", "GEOMETRY", "NUMERICAL", "GEOMETRIC_NUMERICAL"),
    "G12": ("IDENTITY_VERDICT", "SYMBOLIC", "SYMBOLIC", "SYMBOLIC_IDENTITY"),
}


def _module():
    name = "experiments.pct_goal_solver.goal_verifiers"
    assert importlib.util.find_spec(name) is not None, "independent historical verifier module is required"
    return importlib.import_module(name)


def _goal(family, inputs, *, constraints=None, tolerance=None):
    """Preserve the public historical problem contract, changing only roots."""
    base = goals_for("CALIBRATION", family)[0].solver_visible()
    roots = {key: replace(base.inputs[key], artifact_id=key, value=value) for key, value in inputs.items()}
    if family == "G1" and "cumulative" in inputs:
        rank = len(inputs["cumulative"]).bit_length() - 1
        roots["cumulative"] = replace(roots["cumulative"], metadata=(("rank", rank),))
        if constraints is None:
            constraints = (("lattice_rank", rank),)
    if family == "G6" and "exact_matrix" in inputs and "numeric_matrix" not in inputs:
        roots["numeric_matrix"] = replace(base.inputs["numeric_matrix"],
            value=tuple(tuple(float(x) for x in row) for row in inputs["exact_matrix"]))
    if family == "G7" and "generator" in roots:
        roots["generator"] = replace(
            roots["generator"],
            metadata=(("nilpotency_bound", len(inputs["generator"])),),
        )
    if family == "G10" and "body" in roots:
        roots["body"] = replace(roots["body"], metadata=())  # No answer-bearing hints.
    return replace(base, goal_id="opaque", inputs=roots, constraints=base.constraints if constraints is None else tuple(constraints),
                   allowed_numeric_tolerance=base.allowed_numeric_tolerance if tolerance is None else tolerance,
                   search_budget=100)


def _candidate(goal, value, metadata=()):
    return Artifact("candidate", goal.target.semantic_type, goal.target.representation_class,
                    value, goal.target.exactness_class, tuple(metadata))


def _verify(goal, value, metadata=()):
    return _module().verify_historical_goal(goal, _candidate(goal, value, metadata))


def test_dispatch_rejects_wrong_verifier_class_even_for_correct_answer():
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)})
    assert _verify(goal, (1, 2, 3, 4)).passed
    assert not _verify(replace(goal, required_verifier_class="SYMBOLIC_IDENTITY"), (1, 2, 3, 4)).passed
    assert not _verify(replace(goal, family="G99"), (1, 2, 3, 4)).passed


@pytest.mark.parametrize("field,value", [("semantic_type", "OTHER"), ("representation_class", "OTHER"), ("exactness_class", "NUMERICAL")])
def test_candidate_contract_cannot_be_forged(field, value):
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)})
    candidate = replace(_candidate(goal, (1, 2, 3, 4)), **{field: value})
    assert not _module().verify_historical_goal(goal, candidate).passed


def test_family_target_contract_is_not_replaceable_by_an_arbitrary_target():
    goal = _goal("G1", {"cumulative": (1, 3, 4, 10)})
    altered = replace(goal, target=replace(goal.target, semantic_type="OTHER"))
    assert not _verify(altered, (1, 2, 3, 4)).passed


@pytest.mark.parametrize("root,candidate", [((1, 3, 4, 10), (1, 2, 3, 5)), ((), ()), ((1, 2, 3), (1, 1, 1)), ((True, 2), (1, 1)), ((1, math.inf), (1, 1))])
def test_boolean_lattice_rejects_wrong_or_malformed_signals(root, candidate):
    assert not _verify(_goal("G1", {"cumulative": root}), candidate).passed


def test_exact_verifier_does_not_float_convert_large_integers():
    large = 10 ** 1000
    assert _verify(_goal("G1", {"cumulative": (large, large + 1)}), (large, 1)).passed


@pytest.mark.parametrize("basis", [((-2, 1),), ((-6, 3),)])
def test_nullspace_accepts_any_valid_full_basis(basis):
    goal = _goal("G2", {"observation_matrix": ((1, 2), (2, 4))})
    assert _verify(goal, {"unique": False, "nullity": 1, "basis": basis}).passed


@pytest.mark.parametrize("value", [
    {"unique": False, "nullity": 1},
    {"unique": False, "nullity": 1, "basis": ((0, 0),)},
    {"unique": False, "nullity": 1, "basis": ((1, 0),)},
    {"unique": False, "nullity": 1, "basis": ((-2, 1), (-4, 2))},
    {"unique": 0, "nullity": 1, "basis": ((-2, 1),)},
    {"unique": False, "nullity": True, "basis": ((-2, 1),)},
])
def test_nullspace_rejects_forged_or_incomplete_certificates(value):
    assert not _verify(_goal("G2", {"observation_matrix": ((1, 2), (2, 4))}), value).passed


def test_nullspace_dimension_and_zero_basis_are_checked():
    goal = _goal("G2", {"observation_matrix": ((1, 0, 0),)})
    assert not _verify(goal, {"unique": False, "nullity": 2, "basis": ((0, 1, 0), (0, 2, 0))}).passed
    full = _goal("G2", {"observation_matrix": ((1, 0), (0, 1))})
    assert _verify(full, {"unique": True, "nullity": 0, "basis": ()}).passed


def _chain(corrupt=False):
    return _goal("G3", {"source_boundary": ((-1,), (1,)), "target_boundary": ((-1,), (1,)),
                        "vertex_map": ((1, 0), (0, 1)), "edge_map": ((2 if corrupt else 1,),)},
                 constraints=(("localize_if_invalid", True),))


def test_chain_requires_exact_localization_when_requested():
    assert _verify(_chain(), True).passed
    goal = _chain(True)
    assert not _verify(goal, False).passed
    assert not _verify(goal, False, (("residual", ((-1,), (1,))),)).passed
    certificate = {"is_chain_map": False, "residual": ((-1,), (1,)), "residual_rows": (0, 1), "map_columns": (0,)}
    assert _verify(goal, certificate).passed
    assert not _verify(goal, {**certificate, "residual_rows": (0,)}).passed
    assert not _verify(goal, {**certificate, "residual": ((0,), (0,))}).passed


def test_historical_chain_localization_obligation_cannot_be_removed():
    assert not _verify(replace(_chain(True), constraints=()), False).passed


@pytest.mark.parametrize("a,b,level", [
    (((0, 0, 2),), ((0, 0, 3),), "EULER"),
    (((0, 0, 2), (1, 0, 2)), (), "BETTI"),
    (((0, 0, 3), (0, 1, 2)), ((0, 0, 2), (0, 1, 3)), "BARCODE"),
    (((0, 0, 2), (1, 1, 3)), ((1, 1, 3), (0, 0, 2)), "NONE"),
])
def test_information_order_is_recomputed_on_common_endpoint_grid(a, b, level):
    goal = _goal("G4", {"barcode_a": a, "barcode_b": b})
    assert _verify(goal, {"level": level, "distinct": level != "NONE"}).passed
    wrong = "NONE" if level != "NONE" else "EULER"
    assert not _verify(goal, {"level": wrong, "distinct": wrong != "NONE"}).passed


def test_information_order_rejects_invalid_intervals():
    goal = _goal("G4", {"barcode_a": ((0, 2, 1),), "barcode_b": ()})
    assert not _verify(goal, {"level": "EULER", "distinct": True}).passed


def test_graph_isomorphism_uses_structure_not_vertex_names_or_signature_labels():
    goal = _goal("G5", {"graph_a": ((0, 1), (1, 2), (2, 0)), "graph_b": ((4, 5), (5, 6), (6, 4))})
    assert _verify(goal, {"distinct": False}).passed
    assert not _verify(goal, {"distinct": True, "level": "WL"}).passed


def test_graph_schema_rejects_loops_and_nonfinite_nodes():
    for graph in [((0, 0),), ((0, math.nan),)]:
        goal = _goal("G5", {"graph_a": graph, "graph_b": ((0, 1),)})
        assert not _verify(goal, {"distinct": True, "level": "WL"}).passed


def test_exact_rank_validates_rational_matrix_and_integer_output():
    goal = _goal("G6", {"exact_matrix": ((1, Fraction(1, 2)), (2, 1))})
    assert _verify(goal, 1).passed
    for value in (True, 1.0, 2):
        assert not _verify(goal, value).passed
    assert not _verify(_goal("G6", {"exact_matrix": ((1, math.nan),)}), 1).passed


def test_conservation_uses_supplied_generator_not_hardcoded_flow():
    goal = _goal("G7", {"generator": ((0, 1), (0, 0)), "state": ("x", "y"), "candidate_invariant": "x"})
    assert _verify(goal, False).passed
    assert not _verify(goal, True).passed
    invariant = replace(goal, inputs={**goal.inputs, "candidate_invariant": replace(goal.inputs["candidate_invariant"], value="y")})
    assert _verify(invariant, True).passed


def test_symbolic_parser_rejects_executable_text_and_undefined_expressions():
    for expression in ("__import__('os').getcwd()", "1/0", "z", "sin(x)"):
        goal = _goal("G7", {"generator": ((0,),), "state": ("x",), "candidate_invariant": expression})
        assert not _verify(goal, True).passed


def test_invariant_checks_symbol_identity_not_just_symbol_names():
    x = sp.Symbol("x", real=True)
    y = sp.Symbol("y", real=True)
    goal = _goal(
        "G7",
        {"generator": ((0, 1), (0, 0)), "state": (x, y), "candidate_invariant": x ** 2},
    )
    assert _verify(goal, False).passed
    assert not _verify(goal, True).passed


def test_trajectory_relation_requires_non_degenerate_finite_roots():
    goal = _goal(
        "G8",
        {"trajectory": ((0, 0, 0, 1), (1, 1, 2, 1), (2, 4, 4, 1), (3, 9, 6, 1))},
    )
    assert _verify(goal, -4.0).passed
    assert not _verify(goal, -3.0).passed
    for value in (True, math.nan, math.inf):
        assert not _verify(goal, value).passed
    for trajectory in ((), ((0, 1, 1, 1),), ((0, 1, 1, 1), (1, 1, 1, 1)), ((0, 0, 0, 1), (1, math.inf, 2, 1))):
        assert not _verify(_goal("G8", {"trajectory": trajectory}), -4.0).passed


SQUARE = ((0, 0), (2, 0), (2, 2), (0, 2))


@pytest.mark.parametrize("offset", [1.0, 600.0, 10000.0])
def test_steiner_area_is_bounded_analytically_without_buffer_bias(offset):
    goal = _goal("G9", {"body": SQUARE, "offset": offset}, tolerance=5e-5)
    expected = 4.0 + 8.0 * offset + math.pi * offset * offset
    result = _verify(goal, expected)
    assert result.passed
    assert result.residual is not None and result.residual <= goal.allowed_numeric_tolerance
    assert not _verify(goal, expected + 0.01).passed


@pytest.mark.parametrize("polygon,offset", [
    (((0, 0), (2, 0), (1, Fraction(1, 2)), (2, 2), (0, 2)), 1),
    (((0, 0), (2, 2), (0, 2), (2, 0)), 1),
    (((0, 0), (1, 0), (2, 0)), 1),
    ((), 1), (SQUARE, -1), (SQUARE, math.inf),
])
def test_steiner_rejects_unsupported_geometry_and_offsets(polygon, offset):
    assert not _verify(_goal("G9", {"body": polygon, "offset": offset}), 1.0).passed


@pytest.mark.parametrize("polygon,order", [
    (SQUARE, 4), (((0, 0), (4, 0), (4, 2), (0, 2)), 2),
    (((0, 0), (3, 0), (2, 2), (0, 1)), 1),
    (((0, 0), (1, 0), (2, 0), (2, 2), (0, 2)), 4),
])
def test_rotational_order_comes_from_geometry_not_vertex_count(polygon, order):
    goal = _goal("G10", {"body": polygon})
    assert _verify(goal, {"order": order}).passed
    assert not _verify(goal, {"order": order + 1}).passed


def test_rotational_order_ten_is_not_sample_alias_two():
    polygon = tuple((math.cos(2 * math.pi * k / 10), math.sin(2 * math.pi * k / 10)) for k in range(10))
    goal = _goal("G10", {"body": polygon})
    assert _verify(goal, {"order": 10}).passed
    assert not _verify(goal, {"order": 2}).passed


def test_rotation_uses_the_requested_finite_order_angle_not_a_fitted_near_isometry():
    polygon = (
        (Fraction(-1), Fraction(-1)),
        (Fraction(1), Fraction(-1)),
        (Fraction(101, 100), Fraction(1)),
        (Fraction(-1), Fraction(1)),
    )
    # A generic best-fit linear transform is not the declared 90-degree
    # Euclidean rotation.  The latter exceeds the normalized tolerance.
    goal = _goal("G10", {"body": polygon}, tolerance=0.001)
    assert not _verify(goal, {"order": 4}).passed


def test_homothety_distinguishes_same_vertex_count_and_accepts_translation_scaling():
    goal = _goal("G11", {"body_a": SQUARE, "body_b": ((3, 5), (9, 5), (9, 11), (3, 11))})
    assert _verify(goal, {"homothetic": True, "defect": 0.0}).passed
    rectangle = _goal("G11", {"body_a": SQUARE, "body_b": ((0, 0), (4, 0), (4, 2), (0, 2))})
    # V(square, rectangle)=6, A*B=32; 36/32 - 1 = 1/8.
    assert _verify(rectangle, {"homothetic": False, "defect": 0.125}).passed
    assert not _verify(rectangle, {"homothetic": True, "defect": 0.0}).passed
    assert not _verify(rectangle, {"homothetic": False, "defect": 9.0}).passed


def test_homothety_does_not_treat_rotation_as_translation_and_scaling():
    goal = _goal("G11", {"body_a": ((0, 0), (2, 0), (2, 1), (0, 1)), "body_b": ((0, 0), (1, 0), (1, 2), (0, 2))})
    assert not _verify(goal, {"homothetic": True, "defect": 0.0}).passed
    assert _verify(goal, {"homothetic": False, "defect": 0.5625}).passed


def test_symbolic_identity_is_independent_of_sealed_answers_and_candidate_truthiness():
    goal = _goal("G12", {"lhs": "(x+1)**2", "rhs": "x**2+2*x+1"}, constraints=(("symbols", ("x",)),))
    assert _verify(goal, True).passed
    for value in (1, "true", False):
        assert not _verify(goal, value).passed
    bad = replace(goal, inputs={**goal.inputs, "rhs": replace(goal.inputs["rhs"], value="x**2+2*x+2")})
    assert _verify(bad, False).passed
    assert not _verify(bad, True).passed


@pytest.mark.parametrize("lhs,rhs", [("0.1+0.2", "0.3"), ("1000000000000000000.1-1000000000000000000", "1/10"), ("1e999/1e998", "10")])
def test_symbolic_decimal_literals_keep_their_authored_exact_value(lhs, rhs):
    goal = _goal("G12", {"lhs": lhs, "rhs": rhs}, constraints=(("symbols", ()),))
    assert _verify(goal, True).passed


@pytest.mark.parametrize("tolerance", [-1, math.inf, math.nan, True])
def test_invalid_numeric_tolerance_fails_closed(tolerance):
    goal = _goal("G9", {"body": SQUARE, "offset": 1}, tolerance=tolerance)
    assert not _verify(goal, 12 + math.pi).passed


def test_missing_roots_and_malformed_candidate_fail_without_raising():
    for family in CONTRACTS:
        result = _verify(_goal(family, {}), {"forged": True})
        assert not result.passed
        assert result.reason
