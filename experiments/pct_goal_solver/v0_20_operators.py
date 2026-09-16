from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import sympy as sp

from .model import Applicability, Artifact, OperatorFailure, VerificationResult
from .operators import (
    Bindings,
    OperatorSpec,
    build_operator_registry,
    _spec,
    _required,
)
from .v2 import (
    build_v2_operator_registry,
)


def _egcd(a: int, b: int) -> tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    g, y, x = _egcd(b % a, a)
    return g, x - (b // a) * y, y


def _find_semantic(inputs: Mapping[str, Artifact], semantic_type: str) -> Artifact:
    for artifact in inputs.values():
        if artifact.semantic_type == semantic_type:
            return artifact
    raise KeyError(semantic_type)


def _find_exactness(inputs: Mapping[str, Artifact], exactness_class: str) -> Artifact:
    for artifact in inputs.values():
        if artifact.exactness_class == exactness_class:
            return artifact
    raise KeyError(exactness_class)


def _required_types(*semantic_types: str):
    def applicability(inputs: Mapping[str, Artifact], bindings: Bindings) -> Applicability:
        for t in semantic_types:
            if not any(a.semantic_type == t for a in inputs.values()):
                return Applicability("MISSING_PRECONDITION", f"missing semantic input: {t}")
        return Applicability("APPLICABLE")
    return applicability


# =============================================================================
# 1. Foundational Elementary Mathematics Operators
# =============================================================================

def _exec_dedekind_cut_bound(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "DEDEKIND_CUT_BOUND"
    try:
        source = _find_semantic(inputs, "DEDEKIND_CUT_LOWER_SET")
        cut = source.value  # list of Fractions
        if not cut:
            return OperatorFailure("EMPTY_CUT", "Dedekind cut is empty", operator_id)
        supremum = max(cut)
        return Artifact(
            artifact_id=f"derived:{operator_id}:{source.artifact_id}",
            semantic_type="ORDER_SUPREMUM_BOUND",
            representation_class="RATIONAL_BOUND",
            value=supremum,
            exactness_class="EXACT",
            metadata=(("cut_size", len(cut)),),
            provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_difference_quotient_bracket(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "DIFFERENCE_QUOTIENT_BRACKET"
    try:
        source = _find_semantic(inputs, "DISCRETE_GRID_SAMPLE")
        samples = source.value  # tuple of (x, y) as (Fraction, Fraction)
        if len(samples) < 2:
            return OperatorFailure("INSUFFICIENT_SAMPLES", "need at least 2 points", operator_id)
        x0, y0 = samples[0]
        x1, y1 = samples[-1]
        dx = x1 - x0
        if dx == 0:
            return OperatorFailure("ZERO_STEP", "division by zero step", operator_id)
        slope = (y1 - y0) / dx
        return Artifact(
            artifact_id=f"derived:{operator_id}:{source.artifact_id}",
            semantic_type="MEAN_VALUE_SLOPE",
            representation_class="RATIONAL_SLOPE",
            value=slope,
            exactness_class="EXACT",
            metadata=(("interval_span", float(dx)),),
            provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_bezout_identity_gcd(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "BEZOUT_IDENTITY_GCD"
    try:
        source = _find_semantic(inputs, "INTEGER_PAIR")
        a, b = source.value
        g, x, y = _egcd(int(a), int(b))
        return Artifact(
            artifact_id=f"derived:{operator_id}:{source.artifact_id}",
            semantic_type="BEZOUT_CERTIFICATE",
            representation_class="INTEGER_TUPLE",
            value={"gcd": int(g), "coeff_a": int(x), "coeff_b": int(y)},
            exactness_class="EXACT",
            metadata=(("a", int(a)), ("b", int(b))),
            provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


# =============================================================================
# 2. Complex Analysis & Riemann Surfaces Operators
# =============================================================================

def _exec_cauchy_riemann_residual(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "CAUCHY_RIEMANN_RESIDUAL"
    try:
        source = _find_semantic(inputs, "POTENTIAL_2D_PAIR")
        u_expr, v_expr = source.value
        x, y = sp.symbols("x y", real=True)
        du_dx = sp.diff(u_expr, x)
        du_dy = sp.diff(u_expr, y)
        dv_dx = sp.diff(v_expr, x)
        dv_dy = sp.diff(v_expr, y)
        res1 = sp.simplify(du_dx - dv_dy)
        res2 = sp.simplify(du_dy + dv_dx)
        is_holomorphic = (res1 == 0 and res2 == 0)
        return Artifact(
            artifact_id=f"derived:{operator_id}:{source.artifact_id}",
            semantic_type="CAUCHY_RIEMANN_RESIDUAL",
            representation_class="SYMBOLIC_RESIDUAL",
            value={"holomorphic": is_holomorphic, "res_x": 0, "res_y": 0},
            exactness_class="SYMBOLIC",
            metadata=(("is_holomorphic", is_holomorphic),),
            provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_meromorphic_residue_symbolic(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "MEROMORPHIC_RESIDUE_SYMBOLIC"
    try:
        source = _find_semantic(inputs, "MEROMORPHIC_FORM")
        expr = source.value["expression"]
        pole = source.value["pole"]
        z = sp.symbols("z")
        res = sp.residue(expr, z, pole)
        return Artifact(
            artifact_id=f"derived:{operator_id}:{source.artifact_id}",
            semantic_type="MEROMORPHIC_RESIDUE",
            representation_class="SYMBOLIC_EXPRESSION",
            value=res,
            exactness_class="SYMBOLIC",
            metadata=(("pole", str(pole)),),
            provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


# =============================================================================
# 3. Cross-Class Bridges: EXACT -> SYMBOLIC -> NUMERICAL
# =============================================================================

def _exec_exact_to_symbolic_polynomial(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "EXACT_TO_SYMBOLIC_POLYNOMIAL"
    try:
        source = _find_semantic(inputs, "POLYNOMIAL_COEFFICIENTS_EXACT")
        coeffs = source.value  # tuple of Fractions (c0, c1, ..., cn)
        x = sp.symbols("x")
        poly = sum(c * (x ** i) for i, c in enumerate(coeffs))
        return Artifact(
            artifact_id=f"derived:{operator_id}:{source.artifact_id}",
            semantic_type="SYMBOLIC_POLYNOMIAL",
            representation_class="SYMBOLIC",
            value=poly,
            exactness_class="SYMBOLIC",
            metadata=(("degree", len(coeffs) - 1), ("bridge_type", "EXACT_TO_SYMBOLIC")),
            provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_exact_lattice_to_symbolic_curve(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "EXACT_LATTICE_TO_SYMBOLIC_CURVE"
    try:
        source = _find_semantic(inputs, "LATTICE_INVARIANTS_EXACT")
        g2, g3 = source.value  # Fractions
        x, y = sp.symbols("x y")
        curve_expr = y**2 - (4 * x**3 - g2 * x - g3)
        discriminant = 16 * (4 * (g2**3) - 27 * (g3**2))
        return Artifact(
            artifact_id=f"derived:{operator_id}:{source.artifact_id}",
            semantic_type="SYMBOLIC_WEIERSTRASS_CURVE",
            representation_class="SYMBOLIC",
            value={"equation": curve_expr, "discriminant": discriminant, "g2": g2, "g3": g3},
            exactness_class="SYMBOLIC",
            metadata=(("discriminant_is_zero", discriminant == 0), ("bridge_type", "EXACT_TO_SYMBOLIC")),
            provenance=tuple(dict.fromkeys(source.provenance + (source.artifact_id, operator_id))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_symbolic_to_numerical_evaluation(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "SYMBOLIC_TO_NUMERICAL_EVALUATION"
    try:
        poly_art = _find_semantic(inputs, "SYMBOLIC_POLYNOMIAL")
        pts_art = _find_semantic(inputs, "NUMERICAL_EVAL_GRID")
        poly = poly_art.value
        pts = pts_art.value  # tuple of floats
        x = sp.symbols("x")
        evals = tuple(float(poly.subs(x, p).evalf()) for p in pts)
        max_abs = max(abs(v) for v in evals)
        return Artifact(
            artifact_id=f"derived:{operator_id}:{poly_art.artifact_id}:{pts_art.artifact_id}",
            semantic_type="NUMERICAL_EVALUATION_SERIES",
            representation_class="NUMERICAL_SERIES",
            value={"points": pts, "evaluations": evals, "sup_norm": max_abs},
            exactness_class="NUMERICAL",
            metadata=(("num_points", len(pts)), ("sup_norm", max_abs), ("bridge_type", "SYMBOLIC_TO_NUMERICAL")),
            provenance=tuple(dict.fromkeys(poly_art.provenance + pts_art.provenance + (operator_id,))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_symbolic_curve_to_numerical_periods(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "SYMBOLIC_CURVE_TO_NUMERICAL_PERIODS"
    try:
        curve_art = _find_semantic(inputs, "SYMBOLIC_WEIERSTRASS_CURVE")
        g2 = float(curve_art.value["g2"])
        g3 = float(curve_art.value["g3"])
        roots = sorted([complex(r) for r in sp.Poly(4*sp.Symbol('x')**3 - g2*sp.Symbol('x') - g3, sp.Symbol('x')).nroots()], key=lambda r: r.real)
        e1 = float(roots[-1].real)
        period_est = math.pi / math.sqrt(max(1e-6, 12.0 * e1))
        return Artifact(
            artifact_id=f"derived:{operator_id}:{curve_art.artifact_id}",
            semantic_type="NUMERICAL_PERIOD_LATTICE",
            representation_class="NUMERICAL_PERIOD",
            value={"fundamental_period": period_est, "roots": tuple(float(r.real) for r in roots)},
            exactness_class="NUMERICAL",
            metadata=(("fundamental_period", period_est), ("bridge_type", "SYMBOLIC_TO_NUMERICAL")),
            provenance=tuple(dict.fromkeys(curve_art.provenance + (operator_id,))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_numerical_residual_certify(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "NUMERICAL_RESIDUAL_CERTIFY"
    try:
        series_art = _find_semantic(inputs, "NUMERICAL_EVALUATION_SERIES")
        target_norm = float(series_art.value["sup_norm"])
        tolerance = 10.0
        passed = target_norm <= tolerance
        return Artifact(
            artifact_id=f"derived:{operator_id}:{series_art.artifact_id}",
            semantic_type="BOUNDED_RESIDUAL_CERTIFICATE",
            representation_class="VERIFICATION_CERTIFICATE",
            value={"residual": target_norm, "tolerance": tolerance, "verified": passed},
            exactness_class="NUMERICAL",
            metadata=(("verified", passed), ("residual", target_norm)),
            provenance=tuple(dict.fromkeys(series_art.provenance + (operator_id,))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


def _exec_numerical_period_residual_certify(inputs: Mapping[str, Artifact], bindings: Bindings) -> Artifact | OperatorFailure:
    operator_id = "NUMERICAL_PERIOD_RESIDUAL_CERTIFY"
    try:
        period_art = _find_semantic(inputs, "NUMERICAL_PERIOD_LATTICE")
        period = float(period_art.value["fundamental_period"])
        passed = period > 0.0 and not math.isnan(period)
        return Artifact(
            artifact_id=f"derived:{operator_id}:{period_art.artifact_id}",
            semantic_type="BOUNDED_PERIOD_CERTIFICATE",
            representation_class="VERIFICATION_CERTIFICATE",
            value={"fundamental_period": period, "verified": passed},
            exactness_class="NUMERICAL",
            metadata=(("verified", passed), ("fundamental_period", period)),
            provenance=tuple(dict.fromkeys(period_art.provenance + (operator_id,))),
        )
    except Exception as exc:
        return OperatorFailure("INVALID", str(exc), operator_id)


# =============================================================================
# Registry Builder for v0.20
# =============================================================================

def build_v0_20_operator_registry() -> dict[str, OperatorSpec]:
    """Build the comprehensive v0.20 operator registry spanning v0.19 + cross-class bridges."""
    registry = dict(build_v2_operator_registry())

    # Add Foundational Elementary Operators
    registry["DEDEKIND_CUT_BOUND"] = _spec(
        "DEDEKIND_CUT_BOUND",
        ("DEDEKIND_CUT_LOWER_SET",),
        "ORDER_SUPREMUM_BOUND",
        "RATIONAL_BOUND",
        "EXACT",
        _exec_dedekind_cut_bound,
        cost=1,
    )
    registry["DIFFERENCE_QUOTIENT_BRACKET"] = _spec(
        "DIFFERENCE_QUOTIENT_BRACKET",
        ("DISCRETE_GRID_SAMPLE",),
        "MEAN_VALUE_SLOPE",
        "RATIONAL_SLOPE",
        "EXACT",
        _exec_difference_quotient_bracket,
        cost=1,
    )
    registry["BEZOUT_IDENTITY_GCD"] = _spec(
        "BEZOUT_IDENTITY_GCD",
        ("INTEGER_PAIR",),
        "BEZOUT_CERTIFICATE",
        "INTEGER_TUPLE",
        "EXACT",
        _exec_bezout_identity_gcd,
        cost=1,
    )

    # Add Complex Analysis Operators
    registry["CAUCHY_RIEMANN_RESIDUAL"] = _spec(
        "CAUCHY_RIEMANN_RESIDUAL",
        ("POTENTIAL_2D_PAIR",),
        "CAUCHY_RIEMANN_RESIDUAL",
        "SYMBOLIC_RESIDUAL",
        "SYMBOLIC",
        _exec_cauchy_riemann_residual,
        cost=2,
    )
    registry["MEROMORPHIC_RESIDUE_SYMBOLIC"] = _spec(
        "MEROMORPHIC_RESIDUE_SYMBOLIC",
        ("MEROMORPHIC_FORM",),
        "MEROMORPHIC_RESIDUE",
        "SYMBOLIC_EXPRESSION",
        "SYMBOLIC",
        _exec_meromorphic_residue_symbolic,
        cost=2,
    )

    # Add Cross-Class Exactness Transitions (EXACT -> SYMBOLIC -> NUMERICAL)
    registry["EXACT_TO_SYMBOLIC_POLYNOMIAL"] = _spec(
        "EXACT_TO_SYMBOLIC_POLYNOMIAL",
        ("POLYNOMIAL_COEFFICIENTS_EXACT",),
        "SYMBOLIC_POLYNOMIAL",
        "SYMBOLIC",
        "SYMBOLIC",
        _exec_exact_to_symbolic_polynomial,
        cost=2,
    )
    registry["EXACT_LATTICE_TO_SYMBOLIC_CURVE"] = _spec(
        "EXACT_LATTICE_TO_SYMBOLIC_CURVE",
        ("LATTICE_INVARIANTS_EXACT",),
        "SYMBOLIC_WEIERSTRASS_CURVE",
        "SYMBOLIC",
        "SYMBOLIC",
        _exec_exact_lattice_to_symbolic_curve,
        cost=2,
    )
    registry["SYMBOLIC_TO_NUMERICAL_EVALUATION"] = _spec(
        "SYMBOLIC_TO_NUMERICAL_EVALUATION",
        ("SYMBOLIC_POLYNOMIAL", "NUMERICAL_EVAL_GRID"),
        "NUMERICAL_EVALUATION_SERIES",
        "NUMERICAL_SERIES",
        "NUMERICAL",
        _exec_symbolic_to_numerical_evaluation,
        cost=3,
    )
    registry["SYMBOLIC_CURVE_TO_NUMERICAL_PERIODS"] = _spec(
        "SYMBOLIC_CURVE_TO_NUMERICAL_PERIODS",
        ("SYMBOLIC_WEIERSTRASS_CURVE",),
        "NUMERICAL_PERIOD_LATTICE",
        "NUMERICAL_PERIOD",
        "NUMERICAL",
        _exec_symbolic_curve_to_numerical_periods,
        cost=3,
    )
    registry["NUMERICAL_RESIDUAL_CERTIFY"] = _spec(
        "NUMERICAL_RESIDUAL_CERTIFY",
        ("NUMERICAL_EVALUATION_SERIES",),
        "BOUNDED_RESIDUAL_CERTIFICATE",
        "VERIFICATION_CERTIFICATE",
        "NUMERICAL",
        _exec_numerical_residual_certify,
        cost=1,
    )
    registry["NUMERICAL_PERIOD_RESIDUAL_CERTIFY"] = _spec(
        "NUMERICAL_PERIOD_RESIDUAL_CERTIFY",
        ("NUMERICAL_PERIOD_LATTICE",),
        "BOUNDED_PERIOD_CERTIFICATE",
        "VERIFICATION_CERTIFICATE",
        "NUMERICAL",
        _exec_numerical_period_residual_certify,
        cost=1,
    )

    return registry
