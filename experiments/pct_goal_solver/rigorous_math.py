"""Small, independently replayable mathematical certificates for v0.20.

The functions in this module do not know about the planner.  Their inputs are
the mathematical roots of a problem and their outputs contain enough exact
data for a terminal verifier to recompute the result.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Iterable, Sequence

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, PolynomialError


_MAX_EXACT_BITS = 4096
_MAX_POLYNOMIAL_DEGREE = 64
_MAX_POLYNOMIAL_TERMS = 4096
_MAX_SYMBOLIC_NODES = 4096
_MAX_GRID_ITEMS = 4096
_MAX_GRID_WORK = 100_000


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if abs(value).bit_length() > _MAX_EXACT_BITS:
        raise ValueError(f"{name} exceeds the exact-integer resource limit")
    return value


def _fraction(value: Fraction | int, name: str) -> Fraction:
    if type(value) not in (int, Fraction):
        raise TypeError(f"{name} must be an exact rational")
    result = Fraction(value)
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > _MAX_EXACT_BITS:
        raise ValueError(f"{name} exceeds the exact-rational resource limit")
    return result


def _bounded_tuple(values: Iterable[object], *, limit: int, name: str) -> tuple[object, ...]:
    """Materialize an iterable without allowing an unbounded stream."""

    try:
        iterator = iter(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be iterable") from exc
    result: list[object] = []
    for index, value in enumerate(iterator):
        if index >= limit:
            raise ValueError(f"{name} exceeds the collection resource limit of {limit}")
        result.append(value)
    return tuple(result)


def _bounded_symbolic_nodes(expression: sp.Expr, name: str) -> None:
    for index, _ in enumerate(sp.preorder_traversal(expression)):
        if index >= _MAX_SYMBOLIC_NODES:
            raise ValueError(f"{name} exceeds the symbolic resource limit")


def _exact_expression(value: object, name: str) -> sp.Expr:
    if type(value) not in (int, Fraction) and not isinstance(value, sp.Expr):
        raise TypeError(f"{name} must be an exact SymPy expression or exact rational")
    expression = sp.sympify(value)
    _bounded_symbolic_nodes(expression, name)
    if expression.atoms(sp.Float):
        raise ValueError(f"{name} must use exact coefficients, not floating-point atoms")
    if expression.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
        raise ValueError(f"{name} must contain finite real exact values away from certified poles")
    for rational in expression.atoms(sp.Rational):
        if max(abs(int(rational.p)).bit_length(), int(rational.q).bit_length()) > _MAX_EXACT_BITS:
            raise ValueError(f"{name} exceeds the exact-number resource limit")
    return expression


def _polynomial_degree_bound(expression: sp.Expr, variables: frozenset[sp.Symbol]) -> int:
    """Bound total degree from the unexpanded expression tree."""

    if not expression.free_symbols:
        if expression.is_real is not True or expression.is_finite is not True:
            raise ValueError("polynomial coefficients must be finite real exact constants")
        return 0
    if expression in variables:
        return 1
    if isinstance(expression, sp.Add):
        degree = max((_polynomial_degree_bound(arg, variables) for arg in expression.args), default=0)
    elif isinstance(expression, sp.Mul):
        degree = sum(_polynomial_degree_bound(arg, variables) for arg in expression.args)
    elif isinstance(expression, sp.Pow):
        exponent = expression.exp
        if not isinstance(exponent, sp.Integer) or exponent < 0:
            raise ValueError("coordinate-dependent powers must have nonnegative integer exponents")
        degree = _polynomial_degree_bound(expression.base, variables) * int(exponent)
    else:
        raise ValueError("expression is outside the exact polynomial grammar")
    if degree > _MAX_POLYNOMIAL_DEGREE:
        raise ValueError(
            f"polynomial degree exceeds the resource limit of {_MAX_POLYNOMIAL_DEGREE}"
        )
    return degree


def _rational_degree_bound(expression: sp.Expr, variable: sp.Symbol) -> tuple[int, int]:
    """Bound numerator/denominator degrees before rational simplification."""

    if not expression.free_symbols:
        if not isinstance(expression, sp.Rational):
            raise ValueError("rational-function constants must be exact rationals")
        return 0, 0
    if expression == variable:
        return 1, 0
    if isinstance(expression, sp.Add):
        numerator_degree = denominator_degree = 0
        for argument in expression.args:
            next_numerator, next_denominator = _rational_degree_bound(argument, variable)
            numerator_degree = max(
                numerator_degree + next_denominator,
                next_numerator + denominator_degree,
            )
            denominator_degree += next_denominator
            if max(numerator_degree, denominator_degree) > _MAX_POLYNOMIAL_DEGREE:
                raise ValueError("rational-function degree exceeds the resource limit")
        return numerator_degree, denominator_degree
    if isinstance(expression, sp.Mul):
        numerator_degree = denominator_degree = 0
        for argument in expression.args:
            next_numerator, next_denominator = _rational_degree_bound(argument, variable)
            numerator_degree += next_numerator
            denominator_degree += next_denominator
            if max(numerator_degree, denominator_degree) > _MAX_POLYNOMIAL_DEGREE:
                raise ValueError("rational-function degree exceeds the resource limit")
        return numerator_degree, denominator_degree
    if isinstance(expression, sp.Pow):
        exponent = expression.exp
        if not isinstance(exponent, sp.Integer):
            raise ValueError("rational-function powers must have integer exponents")
        numerator_degree, denominator_degree = _rational_degree_bound(expression.base, variable)
        multiplier = abs(int(exponent))
        if exponent < 0:
            numerator_degree, denominator_degree = denominator_degree, numerator_degree
        result = numerator_degree * multiplier, denominator_degree * multiplier
        if max(result) > _MAX_POLYNOMIAL_DEGREE:
            raise ValueError("rational-function degree exceeds the resource limit")
        return result
    raise ValueError("expression is outside the exact rational-function grammar")


@dataclass(frozen=True)
class Sqrt2CutCertificate:
    lower: Fraction
    upper: Fraction
    lower_square_gap: int
    upper_square_gap: int
    verified: bool


def _sqrt2_square_gap(value: Fraction) -> int:
    return value.numerator * value.numerator - 2 * value.denominator * value.denominator


def certify_sqrt2_cut(lower: Fraction | int, upper: Fraction | int) -> Sqrt2CutCertificate:
    """Certify ``lower < sqrt(2) < upper`` using integer arithmetic only."""

    lo = _fraction(lower, "lower")
    hi = _fraction(upper, "upper")
    if lo <= 0 or hi <= lo:
        raise ValueError("bounds must satisfy 0 < lower < upper")
    lo_gap = _sqrt2_square_gap(lo)
    hi_gap = _sqrt2_square_gap(hi)
    if lo_gap >= 0 or hi_gap <= 0:
        raise ValueError("bounds do not strictly bracket sqrt(2)")
    return Sqrt2CutCertificate(lo, hi, lo_gap, hi_gap, True)


def verify_sqrt2_cut(
    lower: Fraction | int,
    upper: Fraction | int,
    certificate: Sqrt2CutCertificate,
) -> bool:
    """Replay a square-root cut certificate against explicit source bounds."""

    if (
        type(certificate) is not Sqrt2CutCertificate
        or type(certificate.lower) is not Fraction
        or type(certificate.upper) is not Fraction
        or type(certificate.lower_square_gap) is not int
        or type(certificate.upper_square_gap) is not int
        or certificate.verified is not True
    ):
        return False
    try:
        replay = certify_sqrt2_cut(lower, upper)
    except (TypeError, ValueError):
        return False
    return replay == certificate


@dataclass(frozen=True)
class QuadraticMeanValueCertificate:
    coefficients: tuple[Fraction, Fraction, Fraction]
    interval: tuple[Fraction, Fraction]
    witness: Fraction
    secant_slope: Fraction
    derivative_at_witness: Fraction
    verified: bool


def _quadratic_value(coefficients: tuple[Fraction, Fraction, Fraction], x: Fraction) -> Fraction:
    a2, a1, a0 = coefficients
    return a2 * x * x + a1 * x + a0


def certify_quadratic_mean_value(
    coefficients: Sequence[Fraction | int],
    left: Fraction | int,
    right: Fraction | int,
) -> QuadraticMeanValueCertificate:
    """Give the exact MVT witness for a degree-at-most-two polynomial.

    Coefficients are ordered ``(a2, a1, a0)``.  The leading coefficient may
    vanish, so exact affine and constant polynomials remain in scope.
    """

    raw_coefficients = _bounded_tuple(coefficients, limit=4, name="coefficients")
    if len(raw_coefficients) != 3:
        raise ValueError("a degree-at-most-two certificate requires exactly three coefficients")
    coeffs = tuple(
        _fraction(value, f"coefficient[{index}]")
        for index, value in enumerate(raw_coefficients)
    )
    a = _fraction(left, "left")
    b = _fraction(right, "right")
    if not a < b:
        raise ValueError("mean-value interval must satisfy left < right")
    witness = _fraction((a + b) / 2, "derived witness")
    secant = _fraction(
        (_quadratic_value(coeffs, b) - _quadratic_value(coeffs, a)) / (b - a),
        "derived secant slope",
    )
    derivative = _fraction(
        2 * coeffs[0] * witness + coeffs[1],
        "derived witness derivative",
    )
    verified = a < witness < b and secant == derivative
    if not verified:
        raise AssertionError("internal exact quadratic MVT identity failed")
    return QuadraticMeanValueCertificate(coeffs, (a, b), witness, secant, derivative, True)


def verify_quadratic_mean_value(
    coefficients: Sequence[Fraction | int],
    left: Fraction | int,
    right: Fraction | int,
    certificate: QuadraticMeanValueCertificate,
) -> bool:
    """Verify any exact interior MVT witness against its source problem.

    The constructor returns the midpoint as a deterministic representative.
    For affine or constant polynomials every interior rational is a valid
    witness, and verification deliberately accepts all of them.
    """

    if (
        type(certificate) is not QuadraticMeanValueCertificate
        or type(certificate.coefficients) is not tuple
        or len(certificate.coefficients) != 3
        or any(type(value) is not Fraction for value in certificate.coefficients)
        or type(certificate.interval) is not tuple
        or len(certificate.interval) != 2
        or any(type(value) is not Fraction for value in certificate.interval)
        or type(certificate.witness) is not Fraction
        or type(certificate.secant_slope) is not Fraction
        or type(certificate.derivative_at_witness) is not Fraction
        or certificate.verified is not True
    ):
        return False
    try:
        certificate_coefficients = tuple(
            _fraction(value, f"certificate.coefficient[{index}]")
            for index, value in enumerate(certificate.coefficients)
        )
        certificate_interval = tuple(
            _fraction(value, f"certificate.interval[{index}]")
            for index, value in enumerate(certificate.interval)
        )
        witness = _fraction(certificate.witness, "certificate.witness")
        certificate_secant = _fraction(
            certificate.secant_slope,
            "certificate.secant_slope",
        )
        certificate_derivative = _fraction(
            certificate.derivative_at_witness,
            "certificate.derivative_at_witness",
        )
        raw_coefficients = _bounded_tuple(coefficients, limit=4, name="coefficients")
        if len(raw_coefficients) != 3:
            return False
        coeffs = tuple(
            _fraction(value, f"coefficient[{index}]")
            for index, value in enumerate(raw_coefficients)
        )
        a = _fraction(left, "left")
        b = _fraction(right, "right")
    except (TypeError, ValueError):
        return False
    if not a < b:
        return False
    secant = (_quadratic_value(coeffs, b) - _quadratic_value(coeffs, a)) / (b - a)
    derivative = 2 * coeffs[0] * witness + coeffs[1]
    return (
        certificate_coefficients == coeffs
        and certificate_interval == (a, b)
        and a < witness < b
        and certificate_secant == secant
        and certificate_derivative == derivative
        and secant == derivative
    )


@dataclass(frozen=True)
class BezoutCertificate:
    a: int
    b: int
    gcd: int
    x: int
    y: int
    verified: bool


def _extended_gcd_nonnegative(a: int, b: int) -> tuple[int, int, int]:
    old_r, r = abs(a), abs(b)
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    x = old_s if a >= 0 else -old_s
    y = old_t if b >= 0 else -old_t
    return old_r, x, y


def verify_bezout(a: int, b: int, gcd_value: int, x: int, y: int) -> bool:
    """Verify Bézout data using the totalized convention ``gcd(0, 0) = 0``."""

    try:
        aa = _integer(a, "a")
        bb = _integer(b, "b")
        gg = _integer(gcd_value, "gcd")
        xx = _integer(x, "x")
        yy = _integer(y, "y")
    except (TypeError, ValueError):
        return False
    return gg >= 0 and gg == math.gcd(aa, bb) and aa * xx + bb * yy == gg


def certify_bezout(a: int, b: int) -> BezoutCertificate:
    """Construct Bézout data, with ``gcd(0, 0)`` explicitly defined as zero."""

    aa = _integer(a, "a")
    bb = _integer(b, "b")
    gcd_value, x, y = _extended_gcd_nonnegative(aa, bb)
    if not verify_bezout(aa, bb, gcd_value, x, y):
        raise AssertionError("internal extended-gcd certificate failed")
    return BezoutCertificate(aa, bb, gcd_value, x, y, True)


def verify_bezout_certificate(a: int, b: int, certificate: BezoutCertificate) -> bool:
    """Verify a source-bound certificate without requiring canonical coefficients.

    Bézout coefficients are non-unique.  In particular, under the totalized
    convention ``gcd(0, 0) = 0``, every integer coefficient pair witnesses the
    identity.  Acceptance therefore checks the mathematical relation rather
    than equality with the constructor's deterministic representative.
    """

    if (
        type(certificate) is not BezoutCertificate
        or type(certificate.a) is not int
        or type(certificate.b) is not int
        or type(certificate.gcd) is not int
        or type(certificate.x) is not int
        or type(certificate.y) is not int
        or certificate.verified is not True
    ):
        return False
    try:
        aa = _integer(a, "a")
        bb = _integer(b, "b")
    except (TypeError, ValueError):
        return False
    return (
        certificate.a == aa
        and certificate.b == bb
        and verify_bezout(aa, bb, certificate.gcd, certificate.x, certificate.y)
    )


@dataclass(frozen=True)
class CauchyRiemannCertificate:
    u: sp.Expr
    v: sp.Expr
    x: sp.Symbol
    y: sp.Symbol
    residuals: tuple[sp.Expr, sp.Expr]
    holomorphic: bool


def certify_cauchy_riemann(
    u: object,
    v: object,
    *,
    x: sp.Symbol,
    y: sp.Symbol,
) -> CauchyRiemannCertificate:
    if type(x) is not sp.Symbol or type(y) is not sp.Symbol or x == y:
        raise TypeError("x and y must be distinct explicit SymPy symbols")
    if x.is_real is not True or y.is_real is not True:
        raise ValueError("x and y must be explicitly real coordinate symbols")
    u_expr = _exact_expression(u, "u")
    v_expr = _exact_expression(v, "v")
    hidden = (u_expr.free_symbols | v_expr.free_symbols) - {x, y}
    if hidden:
        raise ValueError(f"expressions contain undeclared symbols: {sorted(map(str, hidden))}")
    variables = frozenset((x, y))
    _polynomial_degree_bound(u_expr, variables)
    _polynomial_degree_bound(v_expr, variables)
    # The campaign deliberately scopes this certificate to polynomial potentials,
    # which are real differentiable everywhere.  Rational-domain bookkeeping is
    # not silently inferred.
    try:
        polynomials = (sp.Poly(u_expr, x, y), sp.Poly(v_expr, x, y))
    except PolynomialError as exc:
        raise ValueError("Cauchy-Riemann certificate is scoped to polynomial potentials") from exc
    if any(len(polynomial.terms()) > _MAX_POLYNOMIAL_TERMS for polynomial in polynomials):
        raise ValueError("expanded polynomial exceeds the term-count resource limit")
    coefficients = tuple(coefficient for polynomial in polynomials for coefficient in polynomial.coeffs())
    if any(
        coefficient.atoms(sp.Float)
        or coefficient.is_real is not True
        or coefficient.is_finite is not True
        for coefficient in coefficients
    ):
        raise ValueError("polynomial potentials must have finite real exact coefficients")
    residual_1 = sp.simplify(sp.diff(u_expr, x) - sp.diff(v_expr, y))
    residual_2 = sp.simplify(sp.diff(u_expr, y) + sp.diff(v_expr, x))
    holomorphic = residual_1 == 0 and residual_2 == 0
    return CauchyRiemannCertificate(u_expr, v_expr, x, y, (residual_1, residual_2), holomorphic)


def verify_cauchy_riemann(
    u: object,
    v: object,
    certificate: CauchyRiemannCertificate,
    *,
    x: sp.Symbol,
    y: sp.Symbol,
) -> bool:
    """Replay Cauchy-Riemann residuals against the supplied potentials."""

    if (
        type(certificate) is not CauchyRiemannCertificate
        or not isinstance(certificate.u, sp.Expr)
        or not isinstance(certificate.v, sp.Expr)
        or type(certificate.x) is not sp.Symbol
        or type(certificate.y) is not sp.Symbol
        or type(certificate.residuals) is not tuple
        or len(certificate.residuals) != 2
        or any(not isinstance(value, sp.Expr) for value in certificate.residuals)
        or type(certificate.holomorphic) is not bool
    ):
        return False
    try:
        replay = certify_cauchy_riemann(u, v, x=x, y=y)
    except (TypeError, ValueError):
        return False
    return replay == certificate


@dataclass(frozen=True)
class ResidueCertificate:
    expression: sp.Expr
    variable: sp.Symbol
    pole: sp.Expr
    pole_order: int
    residue: sp.Expr
    verified: bool


def certify_residue(expression: object, *, variable: sp.Symbol, pole: object) -> ResidueCertificate:
    """Certify a residue for a rational function over ``QQ``.

    The deliberately narrow domain supplies a decidable meromorphicity proof:
    both numerator and denominator must be exact polynomials over the rationals,
    and ``pole`` must be an exact rational zero of the reduced denominator.
    """

    if type(variable) is not sp.Symbol or variable.is_commutative is not True:
        raise TypeError("variable must be an explicit commutative SymPy symbol")
    expr = _exact_expression(expression, "expression")
    if type(pole) not in (int, Fraction) and not isinstance(pole, sp.Rational):
        raise ValueError("pole must be an exact rational constant")
    pole_expr = sp.sympify(pole)
    if not isinstance(pole_expr, sp.Rational):
        raise ValueError("pole must be an exact rational constant")
    _fraction(Fraction(int(pole_expr.p), int(pole_expr.q)), "pole")
    hidden = expr.free_symbols - {variable}
    if hidden:
        raise ValueError(f"expression contains undeclared symbols: {sorted(map(str, hidden))}")
    _rational_degree_bound(expr, variable)
    try:
        normalized = sp.cancel(expr)
        numerator_expr, denominator_expr = sp.fraction(normalized)
        numerator = sp.Poly(numerator_expr, variable, domain=sp.QQ)
        denominator = sp.Poly(denominator_expr, variable, domain=sp.QQ)
    except (CoercionFailed, PolynomialError, TypeError, ValueError) as exc:
        raise ValueError("expression must be an exact rational function over QQ") from exc
    if denominator.is_zero or denominator.eval(pole_expr) != 0:
        raise ValueError("the supplied point is not a pole of the reduced rational function")
    if numerator.eval(pole_expr) == 0:
        raise ValueError("rational function was not reduced at the supplied pole")
    if (
        numerator.degree() > _MAX_POLYNOMIAL_DEGREE
        or denominator.degree() > _MAX_POLYNOMIAL_DEGREE
        or len(numerator.terms()) > _MAX_POLYNOMIAL_TERMS
        or len(denominator.terms()) > _MAX_POLYNOMIAL_TERMS
    ):
        raise ValueError("reduced rational function exceeds the polynomial resource limit")

    factor = sp.Poly(variable - pole_expr, variable, domain=sp.QQ)
    remaining_denominator = denominator
    pole_order = 0
    while remaining_denominator.eval(pole_expr) == 0:
        quotient, remainder = remaining_denominator.div(factor)
        if not remainder.is_zero:
            raise AssertionError("exact pole factorization failed")
        remaining_denominator = quotient
        pole_order += 1
    if pole_order <= 0 or remaining_denominator.eval(pole_expr) == 0:
        raise AssertionError("failed to establish a finite positive pole order")

    analytic_factor = sp.cancel(numerator.as_expr() / remaining_denominator.as_expr())
    residue = sp.cancel(
        sp.diff(analytic_factor, variable, pole_order - 1).subs(variable, pole_expr)
        / sp.factorial(pole_order - 1)
    )
    if not isinstance(residue, sp.Rational) or residue.is_finite is not True:
        raise AssertionError("exact rational residue computation left the certified domain")
    return ResidueCertificate(normalized, variable, pole_expr, pole_order, residue, True)


def verify_residue(
    expression: object,
    certificate: ResidueCertificate,
    *,
    variable: sp.Symbol,
    pole: object,
) -> bool:
    """Replay a residue certificate against its exact source expression."""

    if (
        type(certificate) is not ResidueCertificate
        or not isinstance(certificate.expression, sp.Expr)
        or type(certificate.variable) is not sp.Symbol
        or not isinstance(certificate.pole, sp.Rational)
        or type(certificate.pole_order) is not int
        or certificate.pole_order <= 0
        or not isinstance(certificate.residue, sp.Rational)
        or certificate.verified is not True
    ):
        return False
    try:
        replay = certify_residue(expression, variable=variable, pole=pole)
    except (AssertionError, TypeError, ValueError):
        return False
    return replay == certificate and replay.verified


def _polynomial_values(
    coefficients: tuple[Fraction, ...],
    grid: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    values: list[Fraction] = []
    for point in grid:
        result = Fraction(0)
        for index, coefficient in enumerate(reversed(coefficients)):
            result = _fraction(
                result * point + coefficient,
                f"derived polynomial value step[{index}]",
            )
        values.append(result)
    return tuple(values)


@dataclass(frozen=True)
class GridEvaluationCertificate:
    coefficients: tuple[Fraction, ...]
    grid: tuple[Fraction, ...]
    exact_values: tuple[Fraction, ...]
    numerical_values: tuple[float, ...]
    point_errors: tuple[Fraction, ...]
    maximum_error: Fraction
    tolerance: Fraction
    verified: bool


def certify_grid_evaluation(
    coefficients: Iterable[Fraction | int],
    grid: Iterable[Fraction | int],
    numerical_values: Iterable[float],
    tolerance: Fraction | int,
) -> GridEvaluationCertificate:
    raw_coefficients = _bounded_tuple(coefficients, limit=_MAX_GRID_ITEMS, name="coefficients")
    raw_points = _bounded_tuple(grid, limit=_MAX_GRID_ITEMS, name="grid")
    observed = _bounded_tuple(numerical_values, limit=_MAX_GRID_ITEMS, name="numerical values")
    coeffs = tuple(_fraction(value, "coefficient") for value in raw_coefficients)
    points = tuple(_fraction(value, "grid point") for value in raw_points)
    tol = _fraction(tolerance, "tolerance")
    if not coeffs or not points:
        raise ValueError("coefficients and grid must be nonempty")
    if len(coeffs) * len(points) > _MAX_GRID_WORK:
        raise ValueError("polynomial grid evaluation exceeds the work resource limit")
    if tol < 0:
        raise ValueError("tolerance must be nonnegative")
    if len(observed) != len(points):
        raise ValueError("one numerical value is required for every grid point")
    if any(type(value) is not float or not math.isfinite(value) for value in observed):
        raise ValueError("numerical values must be finite Python floats")
    exact = _polynomial_values(coeffs, points)
    observed_exact = tuple(Fraction.from_float(value) for value in observed)
    errors = tuple(abs(actual - expected) for actual, expected in zip(observed_exact, exact))
    maximum = max(errors, default=Fraction(0))
    return GridEvaluationCertificate(coeffs, points, exact, observed, errors, maximum, tol, maximum <= tol)


def verify_grid_evaluation(certificate: GridEvaluationCertificate) -> bool:
    if (
        type(certificate) is not GridEvaluationCertificate
        or type(certificate.coefficients) is not tuple
        or not certificate.coefficients
        or len(certificate.coefficients) > _MAX_GRID_ITEMS
        or any(type(value) is not Fraction for value in certificate.coefficients)
        or type(certificate.grid) is not tuple
        or not certificate.grid
        or len(certificate.grid) > _MAX_GRID_ITEMS
        or any(type(value) is not Fraction for value in certificate.grid)
        or type(certificate.exact_values) is not tuple
        or len(certificate.exact_values) != len(certificate.grid)
        or any(type(value) is not Fraction for value in certificate.exact_values)
        or type(certificate.numerical_values) is not tuple
        or len(certificate.numerical_values) != len(certificate.grid)
        or any(type(value) is not float or not math.isfinite(value) for value in certificate.numerical_values)
        or type(certificate.point_errors) is not tuple
        or len(certificate.point_errors) != len(certificate.grid)
        or any(type(value) is not Fraction for value in certificate.point_errors)
        or len(certificate.coefficients) * len(certificate.grid) > _MAX_GRID_WORK
        or type(certificate.maximum_error) is not Fraction
        or type(certificate.tolerance) is not Fraction
        or certificate.verified is not True
    ):
        return False
    try:
        replay = certify_grid_evaluation(
            certificate.coefficients,
            certificate.grid,
            certificate.numerical_values,
            certificate.tolerance,
        )
    except (TypeError, ValueError):
        return False
    return replay == certificate and replay.verified
