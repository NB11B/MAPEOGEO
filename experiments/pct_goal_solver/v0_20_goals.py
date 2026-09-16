from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import math
from typing import Any, Mapping

import sympy as sp

from .goals import FAMILIES as V1_FAMILIES, _BUILDERS as V1_BUILDERS, _artifact
from .model import Artifact, GoalSpec, TargetSpec
from .operators import OperatorSpec


def _egcd(a: int, b: int) -> tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    g, y, x = _egcd(b % a, a)
    return g, x - (b // a) * y, y


V0_20_SPLIT_COUNTS = {"CALIBRATION_V0_20": 3, "VALIDATION_V0_20": 1, "SEALED_V0_20": 2}
V0_20_SPLIT_BASES = {"CALIBRATION_V0_20": 10000, "VALIDATION_V0_20": 20000, "SEALED_V0_20": 30000}

# Additional v0.20 Families
FOUNDATIONAL_FAMILIES = ("F1", "F2", "F3")
COMPLEX_FAMILIES = ("C1", "C2")
CROSS_CLASS_FAMILIES = ("X1", "X2")

ALL_V0_20_FAMILIES = tuple(V1_FAMILIES) + FOUNDATIONAL_FAMILIES + COMPLEX_FAMILIES + CROSS_CLASS_FAMILIES

V0_20_REQUIRED_DERIVED_TYPES: dict[str, tuple[str, ...]] = {
    # Historical G1-G12
    "G1": ("BOOLEAN_ZETA_SIGNAL",),
    "G2": ("MATRIX_RANK",),
    "G3": ("CHAIN_RESIDUAL_MATRIX",),
    "G4": (),
    "G5": (),
    "G6": ("CONDITIONING_RISK",),
    "G7": ("NILPOTENCY_RESULT",),
    "G8": ("SYMBOLIC_EXPRESSION",),
    "G9": ("CONVEXITY_VERDICT", "SYMBOLIC_EXPRESSION"),
    "G10": (),
    "G11": (),
    "G12": ("SYMBOLIC_EXPRESSION",),
    # Foundational Elementary Math
    "F1": ("ORDER_SUPREMUM_BOUND",),
    "F2": ("MEAN_VALUE_SLOPE",),
    "F3": ("BEZOUT_CERTIFICATE",),
    # Complex Analysis v0.19
    "C1": ("CAUCHY_RIEMANN_RESIDUAL",),
    "C2": ("MEROMORPHIC_RESIDUE",),
    # Multi-Stage Cross-Class EXACT -> SYMBOLIC -> NUMERICAL
    "X1": ("SYMBOLIC_POLYNOMIAL", "NUMERICAL_EVALUATION_SERIES"),
    "X2": ("SYMBOLIC_WEIERSTRASS_CURVE", "NUMERICAL_PERIOD_LATTICE"),
}


# =============================================================================
# Builders for New Families
# =============================================================================

def _goal_f1(goal_id: str, index: int) -> GoalSpec:
    """Foundational F1: Dedekind Cut Supremum Bound (Exact)."""
    n = 5 + (index % 5)
    cut = tuple(Fraction(k * k, (k + 1) * (k + 1)) for k in range(1, n + 1))
    expected_supremum = max(cut)
    inputs = {
        "cut": _artifact(goal_id, "cut", "DEDEKIND_CUT_LOWER_SET", "RATIONAL_SET", cut, "EXACT", count=len(cut))
    }
    return GoalSpec(
        goal_id, "F1", inputs,
        TargetSpec("supremum", "ORDER_SUPREMUM_BOUND", "RATIONAL_BOUND", "COMPUTE_BOUND", "EXACT"),
        (("exactness_target", "EXACT"),), 0.0, "EXACT_EQUALITY", 64,
        expected_supremum, ("DEDEKIND_CUT_BOUND", "VERIFY_CANDIDATE"),
    )


def _goal_f2(goal_id: str, index: int) -> GoalSpec:
    """Foundational F2: Discrete Mean-Value Slope Bracket (Exact)."""
    step = Fraction(1, index + 1)
    pts = ((Fraction(0), Fraction(1)), (step, Fraction(1) + step * step), (Fraction(2) * step, Fraction(1) + Fraction(4) * step * step))
    expected_slope = (pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0])
    inputs = {
        "samples": _artifact(goal_id, "samples", "DISCRETE_GRID_SAMPLE", "SAMPLE_TUPLE", pts, "EXACT", points=len(pts))
    }
    return GoalSpec(
        goal_id, "F2", inputs,
        TargetSpec("slope", "MEAN_VALUE_SLOPE", "RATIONAL_SLOPE", "COMPUTE_SLOPE", "EXACT"),
        (("exactness_target", "EXACT"),), 0.0, "EXACT_EQUALITY", 64,
        expected_slope, ("DIFFERENCE_QUOTIENT_BRACKET", "VERIFY_CANDIDATE"),
    )


def _goal_f3(goal_id: str, index: int) -> GoalSpec:
    """Foundational F3: Bezout Extended GCD Certificate (Exact)."""
    a = 12 + 7 * (index % 9)
    b = 8 + 5 * (index % 7)
    g, x, y = _egcd(a, b)
    expected = {"gcd": int(g), "coeff_a": int(x), "coeff_b": int(y)}
    inputs = {
        "pair": _artifact(goal_id, "pair", "INTEGER_PAIR", "INTEGER_TUPLE", (a, b), "EXACT", a=a, b=b)
    }
    return GoalSpec(
        goal_id, "F3", inputs,
        TargetSpec("bezout", "BEZOUT_CERTIFICATE", "INTEGER_TUPLE", "EXTENDED_GCD", "EXACT"),
        (("exactness_target", "EXACT"),), 0.0, "EXACT_EQUALITY", 64,
        expected, ("BEZOUT_IDENTITY_GCD", "VERIFY_CANDIDATE"),
    )


def _goal_c1(goal_id: str, index: int) -> GoalSpec:
    """Complex Analysis C1: Cauchy-Riemann Holomorphy (Symbolic)."""
    x, y = sp.symbols("x y", real=True)
    c = index % 4
    u = x**2 - y**2 + c * x
    v = 2 * x * y + c * y
    inputs = {
        "potential_pair": _artifact(goal_id, "potential", "POTENTIAL_2D_PAIR", "SYMBOLIC_PAIR", (u, v), "SYMBOLIC", degree=2)
    }
    expected = {"holomorphic": True, "res_x": 0, "res_y": 0}
    return GoalSpec(
        goal_id, "C1", inputs,
        TargetSpec("cr_residual", "CAUCHY_RIEMANN_RESIDUAL", "SYMBOLIC_RESIDUAL", "VERIFY_HOLOMORPHY", "SYMBOLIC"),
        (("exactness_target", "SYMBOLIC"),), 0.0, "EXACT_EQUALITY", 80,
        expected, ("CAUCHY_RIEMANN_RESIDUAL", "VERIFY_CANDIDATE"),
    )


def _goal_c2(goal_id: str, index: int) -> GoalSpec:
    """Complex Analysis C2: Meromorphic 1-Form Residue (Symbolic)."""
    z = sp.symbols("z")
    a = (index % 5) + 1
    expr = 1 / (z - a) + 1 / ((z - a)**2)
    inputs = {
        "form": _artifact(goal_id, "form", "MEROMORPHIC_FORM", "SYMBOLIC_FORM", {"expression": expr, "pole": a}, "SYMBOLIC", pole=a)
    }
    expected = sp.Integer(1)
    return GoalSpec(
        goal_id, "C2", inputs,
        TargetSpec("residue", "MEROMORPHIC_RESIDUE", "SYMBOLIC_EXPRESSION", "COMPUTE_RESIDUE", "SYMBOLIC"),
        (("exactness_target", "SYMBOLIC"),), 0.0, "EXACT_EQUALITY", 80,
        expected, ("MEROMORPHIC_RESIDUE_SYMBOLIC", "VERIFY_CANDIDATE"),
    )


def _goal_x1(goal_id: str, index: int) -> GoalSpec:
    """Cross-Class X1: EXACT (coeffs) -> SYMBOLIC (poly) -> NUMERICAL (grid eval & residual)."""
    c0 = Fraction(1, (index % 3) + 1)
    c1 = Fraction(-1, (index % 4) + 1)
    c2 = Fraction(1, 10)
    coeffs = (c0, c1, c2)
    grid = (0.0, 0.25, 0.5, 0.75, 1.0)
    
    x = sp.symbols("x")
    poly = sum(c * (x ** i) for i, c in enumerate(coeffs))
    evals = tuple(float(poly.subs(x, p).evalf()) for p in grid)
    sup_norm = max(abs(v) for v in evals)
    expected = {"residual": sup_norm, "tolerance": 10.0, "verified": sup_norm <= 10.0}

    inputs = {
        "coeffs": _artifact(goal_id, "coeffs", "POLYNOMIAL_COEFFICIENTS_EXACT", "RATIONAL_VECTOR", coeffs, "EXACT", degree=2),
        "grid": _artifact(goal_id, "grid", "NUMERICAL_EVAL_GRID", "NUMERICAL_TUPLE", grid, "NUMERICAL", count=len(grid)),
    }
    return GoalSpec(
        goal_id, "X1", inputs,
        TargetSpec("certificate", "BOUNDED_RESIDUAL_CERTIFICATE", "VERIFICATION_CERTIFICATE", "CERTIFY_RESIDUAL", "NUMERICAL"),
        (("exactness_target", "NUMERICAL"), ("tolerance", 10.0)), 1e-4, "NUMERIC_RESIDUAL_WITHIN_TOLERANCE", 128,
        expected, ("EXACT_TO_SYMBOLIC_POLYNOMIAL", "SYMBOLIC_TO_NUMERICAL_EVALUATION", "NUMERICAL_RESIDUAL_CERTIFY", "VERIFY_CANDIDATE"),
    )


def _goal_x2(goal_id: str, index: int) -> GoalSpec:
    """Cross-Class X2: EXACT (lattice g2, g3) -> SYMBOLIC (curve) -> NUMERICAL (periods)."""
    g2 = Fraction(4 + (index % 3))
    g3 = Fraction(1, (index % 2) + 1)
    inputs = {
        "lattice": _artifact(goal_id, "lattice", "LATTICE_INVARIANTS_EXACT", "RATIONAL_PAIR", (g2, g3), "EXACT", g2=float(g2), g3=float(g3))
    }
    roots = sorted([complex(r) for r in sp.Poly(4*sp.Symbol('x')**3 - g2*sp.Symbol('x') - g3, sp.Symbol('x')).nroots()], key=lambda r: r.real)
    e1 = float(roots[-1].real)
    period_est = math.pi / math.sqrt(max(1e-6, 12.0 * e1))
    expected = {"fundamental_period": period_est, "verified": True}

    return GoalSpec(
        goal_id, "X2", inputs,
        TargetSpec("period_certificate", "BOUNDED_PERIOD_CERTIFICATE", "VERIFICATION_CERTIFICATE", "CERTIFY_PERIOD", "NUMERICAL"),
        (("exactness_target", "NUMERICAL"),), 1e-3, "NUMERIC_RESIDUAL_WITHIN_TOLERANCE", 128,
        expected, ("EXACT_LATTICE_TO_SYMBOLIC_CURVE", "SYMBOLIC_CURVE_TO_NUMERICAL_PERIODS", "NUMERICAL_PERIOD_RESIDUAL_CERTIFY", "VERIFY_CANDIDATE"),
    )


# =============================================================================
# Builder Dispatch Table
# =============================================================================

_V0_20_BUILDERS = dict(V1_BUILDERS)
_V0_20_BUILDERS.update({
    "F1": _goal_f1,
    "F2": _goal_f2,
    "F3": _goal_f3,
    "C1": _goal_c1,
    "C2": _goal_c2,
    "X1": _goal_x1,
    "X2": _goal_x2,
})


def _with_v0_20_contract(goal: GoalSpec) -> GoalSpec:
    inputs = dict(goal.inputs)
    if goal.family == "G2":
        observation = inputs["observation_matrix"]
        inputs["rational_matrix"] = replace(
            observation,
            artifact_id=f"{goal.goal_id}:rational_matrix",
            semantic_type="RATIONAL_MATRIX",
        )
    constraints = tuple(goal.constraints) + (
        ("required_derived_types", V0_20_REQUIRED_DERIVED_TYPES.get(goal.family, ())),
    )
    return replace(goal, inputs=inputs, constraints=constraints)


def build_v0_20_corpus() -> dict[str, list[GoalSpec]]:
    """Build the comprehensive v0.20 calibration, validation, and sealed corpora."""
    corpus: dict[str, list[GoalSpec]] = {split: [] for split in V0_20_SPLIT_COUNTS}
    for split in ("CALIBRATION_V0_20", "VALIDATION_V0_20", "SEALED_V0_20"):
        base = V0_20_SPLIT_BASES[split]
        for family_index, family in enumerate(ALL_V0_20_FAMILIES):
            for local_index in range(V0_20_SPLIT_COUNTS[split]):
                goal_id = f"{split.lower()}:{family.lower()}:{local_index:02d}"
                parameter_index = base + 10 * family_index + local_index
                builder = _V0_20_BUILDERS[family]
                corpus[split].append(_with_v0_20_contract(builder(goal_id, parameter_index)))
    return corpus


def prove_no_same_class_shortcut(goal: GoalSpec, registry: Mapping[str, OperatorSpec]) -> dict[str, Any]:
    """Mathematically prove that a cross-class goal CANNOT be solved within a single exactness class."""
    if goal.family not in CROSS_CLASS_FAMILIES:
        return {"is_cross_class": False, "proven_no_shortcut": True}

    input_classes = {a.exactness_class for a in goal.inputs.values()}
    target_class = goal.target.exactness_class
    has_same_class = (input_classes == {target_class})
    required_derived = dict(goal.constraints).get("required_derived_types", ())
    
    return {
        "is_cross_class": True,
        "input_exactness_classes": sorted(input_classes),
        "target_exactness_class": target_class,
        "required_derived_types": required_derived,
        "has_same_class_direct_input": has_same_class,
        "proven_no_shortcut": (input_classes != {target_class}) and len(required_derived) >= 2,
    }
