from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
import sympy as sp

from .rigorous_math import (
    certify_bezout,
    certify_cauchy_riemann,
    certify_grid_evaluation,
    certify_quadratic_mean_value,
    certify_residue,
    certify_sqrt2_cut,
    verify_bezout,
    verify_bezout_certificate,
    verify_cauchy_riemann,
    verify_grid_evaluation,
    verify_quadratic_mean_value,
    verify_residue,
    verify_sqrt2_cut,
)


class _IntSubclass(int):
    pass


class _FloatSubclass(float):
    pass


def test_sqrt2_cut_uses_exact_boundary_arithmetic() -> None:
    lower = Fraction(318281039, 225058681)
    upper = Fraction(19601, 13860)
    cert = certify_sqrt2_cut(lower, upper)
    assert cert.lower_square_gap == -1
    assert cert.upper_square_gap > 0
    assert cert.verified
    assert verify_sqrt2_cut(lower, upper, cert)
    assert not verify_sqrt2_cut(lower, upper + 1, cert)
    assert not verify_sqrt2_cut(lower, upper, replace(cert, lower_square_gap=0))


@pytest.mark.parametrize(
    "lower,upper",
    [
        (Fraction(3, 2), Fraction(7, 5)),
        (Fraction(-1), Fraction(3, 2)),
        (Fraction(1), Fraction(1)),
    ],
)
def test_sqrt2_cut_rejects_invalid_brackets(lower: Fraction, upper: Fraction) -> None:
    with pytest.raises(ValueError):
        certify_sqrt2_cut(lower, upper)


def test_sqrt2_cut_rejects_inexact_types_and_bounded_exact_arithmetic() -> None:
    with pytest.raises(TypeError):
        certify_sqrt2_cut(True, Fraction(3, 2))
    with pytest.raises(ValueError, match="resource limit"):
        certify_sqrt2_cut(Fraction(1, 1 << 5000), Fraction(3, 2))
    assert not verify_sqrt2_cut(Fraction(7, 5), Fraction(3, 2), object())  # type: ignore[arg-type]


def test_degree_at_most_two_mean_value_certificate_is_exact_and_source_bound() -> None:
    coefficients = (Fraction(0), Fraction(-2), Fraction(5))
    left = Fraction(-4)
    right = Fraction(7)
    cert = certify_quadratic_mean_value(
        coefficients,
        left,
        right,
    )
    assert cert.witness == Fraction(3, 2)
    assert cert.secant_slope == cert.derivative_at_witness
    assert cert.verified
    assert verify_quadratic_mean_value(coefficients, left, right, cert)
    assert not verify_quadratic_mean_value((1, -2, 5), left, right, cert)
    assert not verify_quadratic_mean_value(coefficients, left, right, replace(cert, witness=Fraction(8)))


@pytest.mark.parametrize("witness", [Fraction(-3), Fraction(0), Fraction(13, 2)])
def test_affine_mean_value_verifier_accepts_every_exact_interior_witness(witness: Fraction) -> None:
    coefficients = (Fraction(0), Fraction(-2), Fraction(5))
    left, right = Fraction(-4), Fraction(7)
    canonical = certify_quadratic_mean_value(coefficients, left, right)
    alternate = replace(
        canonical,
        witness=witness,
        derivative_at_witness=Fraction(-2),
    )
    assert verify_quadratic_mean_value(coefficients, left, right, alternate)


def test_mean_value_verifier_rejects_endpoints_wrong_derivatives_and_inexact_fields() -> None:
    coefficients = (Fraction(1), Fraction(-2), Fraction(5))
    left, right = Fraction(-4), Fraction(7)
    certificate = certify_quadratic_mean_value(coefficients, left, right)
    assert not verify_quadratic_mean_value(
        coefficients,
        left,
        right,
        replace(certificate, witness=left, derivative_at_witness=2 * left - 2),
    )
    assert not verify_quadratic_mean_value(
        coefficients,
        left,
        right,
        replace(certificate, derivative_at_witness=certificate.derivative_at_witness + 1),
    )
    assert not verify_quadratic_mean_value(
        (0, 1, 0),
        -1,
        1,
        replace(certify_quadratic_mean_value((0, 1, 0), -1, 1), witness=0),
    )
    assert not verify_quadratic_mean_value(coefficients, left, right, object())  # type: ignore[arg-type]


def test_mean_value_verifier_rejects_oversized_affine_certificate_fields_before_arithmetic() -> None:
    coefficients = (Fraction(0), Fraction(3), Fraction(-2))
    left, right = Fraction(0), Fraction(1)
    certificate = certify_quadratic_mean_value(coefficients, left, right)
    oversized_witness = Fraction(1, (1 << 4097) + 1)
    forged = replace(
        certificate,
        witness=oversized_witness,
        derivative_at_witness=Fraction(3),
    )

    assert not verify_quadratic_mean_value(coefficients, left, right, forged)


def test_bezout_accepts_alternate_valid_coefficients_and_normalizes_gcd() -> None:
    cert = certify_bezout(-12, 8)
    assert cert.gcd == 4
    assert verify_bezout(-12, 8, cert.gcd, cert.x - 2, cert.y - 3)
    assert verify_bezout_certificate(-12, 8, cert)
    assert verify_bezout_certificate(-12, 8, replace(cert, x=cert.x - 2, y=cert.y - 3))
    assert not verify_bezout_certificate(-12, 8, replace(cert, verified=1))  # type: ignore[arg-type]


def test_bezout_freezes_totalized_zero_zero_convention() -> None:
    cert = certify_bezout(0, 0)
    assert cert.gcd == 0
    assert verify_bezout(0, 0, cert.gcd, cert.x, cert.y)
    assert verify_bezout(0, 0, 0, -123, 456)
    assert verify_bezout_certificate(0, 0, replace(cert, x=-123, y=456))
    assert not verify_bezout(0, 0, 1, 0, 0)
    assert not verify_bezout(0, 0, -1, 0, 0)


@pytest.mark.parametrize("a,b", [(1.5, 2), (True, 3), (3, "4")])
def test_bezout_rejects_nonintegers(a: object, b: object) -> None:
    with pytest.raises(TypeError):
        certify_bezout(a, b)  # type: ignore[arg-type]


def test_bezout_rejects_integer_subclasses_and_bounds_integer_work() -> None:
    with pytest.raises(TypeError):
        certify_bezout(_IntSubclass(12), 8)
    with pytest.raises(ValueError, match="resource limit"):
        certify_bezout(1 << 5000, 1)
    assert not verify_bezout(_IntSubclass(12), 8, 4, 1, -1)


def test_cauchy_riemann_uses_the_supplied_symbol_objects() -> None:
    x, y = sp.symbols("x y", real=True)
    positive_u = x**2 - y**2
    positive_v = 2 * x * y
    positive = certify_cauchy_riemann(positive_u, positive_v, x=x, y=y)
    negative = certify_cauchy_riemann(x, 0, x=x, y=y)
    assert positive.holomorphic
    assert positive.residuals == (0, 0)
    assert not negative.holomorphic
    assert negative.residuals != (0, 0)
    assert verify_cauchy_riemann(positive_u, positive_v, positive, x=x, y=y)
    assert verify_cauchy_riemann(x, 0, negative, x=x, y=y)
    assert not verify_cauchy_riemann(x, 0, positive, x=x, y=y)
    assert not verify_cauchy_riemann(
        positive_u,
        positive_v,
        replace(positive, holomorphic=False),
        x=x,
        y=y,
    )


def test_cauchy_riemann_rejects_hidden_symbols() -> None:
    x, y, t = sp.symbols("x y t", real=True)
    with pytest.raises(ValueError):
        certify_cauchy_riemann(t * x, 0, x=x, y=y)


@pytest.mark.parametrize("invalid", [sp.oo, sp.nan, sp.zoo])
def test_cauchy_riemann_rejects_nonfinite_polynomial_values(invalid: sp.Expr) -> None:
    x, y = sp.symbols("x y", real=True)
    with pytest.raises(ValueError, match="finite real"):
        certify_cauchy_riemann(invalid, 0, x=x, y=y)


def test_cauchy_riemann_requires_real_coordinates_and_coefficients() -> None:
    x, y = sp.symbols("x y")
    with pytest.raises(ValueError, match="real coordinate"):
        certify_cauchy_riemann(x**2 - y**2, 2 * x * y, x=x, y=y)
    xr, yr = sp.symbols("x y", real=True)
    with pytest.raises(ValueError, match="finite real"):
        certify_cauchy_riemann(sp.I * (xr**2 - yr**2), 2 * sp.I * xr * yr, x=xr, y=yr)


def test_cauchy_riemann_requires_exact_bounded_polynomials_and_exact_certificate_schema() -> None:
    x, y = sp.symbols("x y", real=True)
    with pytest.raises(ValueError, match="exact"):
        certify_cauchy_riemann(sp.Float("1.0") * x, y, x=x, y=y)
    with pytest.raises(ValueError, match="resource limit"):
        certify_cauchy_riemann(x**1000, y, x=x, y=y)
    certificate = certify_cauchy_riemann(x**2 - y**2, 2 * x * y, x=x, y=y)
    assert not verify_cauchy_riemann(
        x**2 - y**2,
        2 * x * y,
        replace(certificate, holomorphic=1),  # type: ignore[arg-type]
        x=x,
        y=y,
    )
    assert not verify_cauchy_riemann(x, y, object(), x=x, y=y)  # type: ignore[arg-type]


def test_residue_is_exact_for_rational_functions_at_actual_poles() -> None:
    z = sp.Symbol("z")
    simple = certify_residue(7 / (z - 3), variable=z, pole=3)
    second_order = certify_residue(1 / (z - 2) ** 2, variable=z, pole=2)
    third_order_expr = (1 + z + sp.Rational(1, 2) * z**2) / z**3
    third_order = certify_residue(third_order_expr, variable=z, pole=0)
    assert (simple.pole_order, simple.residue) == (1, 7)
    assert (second_order.pole_order, second_order.residue) == (2, 0)
    assert (third_order.pole_order, third_order.residue) == (3, sp.Rational(1, 2))
    assert verify_residue(7 / (z - 3), simple, variable=z, pole=3)
    assert verify_residue(third_order_expr, third_order, variable=z, pole=0)
    assert not verify_residue(8 / (z - 3), simple, variable=z, pole=3)
    assert not verify_residue(
        7 / (z - 3),
        replace(simple, residue=sp.Integer(8)),
        variable=z,
        pole=3,
    )


@pytest.mark.parametrize(
    "expression,pole",
    [
        (lambda z: sp.Abs(z) / z, 0),
        (lambda z: sp.conjugate(z) / z, 0),
        (lambda z: sp.exp(z) / z**3, 0),
        (lambda z: z + 1, 0),
        (lambda z: sp.Float("1.5") / (z - 1), 1),
        (lambda z: sp.oo / (z - 1), 1),
    ],
)
def test_residue_rejects_nonrational_nonexact_or_regular_inputs(expression: object, pole: object) -> None:
    z = sp.Symbol("z")
    with pytest.raises(ValueError):
        certify_residue(expression(z), variable=z, pole=pole)  # type: ignore[operator]


def test_residue_rejects_nonconstant_or_undeclared_poles() -> None:
    z, t = sp.symbols("z t")
    with pytest.raises(ValueError, match="exact rational"):
        certify_residue(1 / (z - 1), variable=z, pole=t)
    with pytest.raises(ValueError, match="exact rational"):
        certify_residue(1 / (z - 1), variable=z, pole=z)


def test_residue_rejects_parser_inputs_resource_exhaustion_and_inexact_certificate_schema() -> None:
    z = sp.Symbol("z")
    with pytest.raises(TypeError, match="SymPy expression"):
        certify_residue("1 / (z - 1)", variable=z, pole=1)
    with pytest.raises(ValueError, match="resource limit"):
        certify_residue(1 / (z - 1) ** 1000, variable=z, pole=1)
    certificate = certify_residue(1 / (z - 1), variable=z, pole=1)
    assert not verify_residue(
        1 / (z - 1),
        replace(certificate, verified=1),  # type: ignore[arg-type]
        variable=z,
        pole=1,
    )
    assert not verify_residue(1 / (z - 1), object(), variable=z, pole=1)  # type: ignore[arg-type]


def test_grid_evaluation_certificate_uses_exact_reference_values() -> None:
    cert = certify_grid_evaluation(
        coefficients=(Fraction(1, 3), Fraction(-2), Fraction(5, 7)),
        grid=(Fraction(-2), Fraction(0), Fraction(3, 2)),
        numerical_values=(7.190476190476191, 0.3333333333333333, -1.0595238095238095),
        tolerance=Fraction(1, 10**12),
    )
    assert cert.verified
    assert cert.maximum_error >= 0
    assert verify_grid_evaluation(cert)


def test_forged_zero_grid_residual_is_rejected() -> None:
    cert = certify_grid_evaluation(
        coefficients=(Fraction(1), Fraction(1)),
        grid=(Fraction(0), Fraction(1)),
        numerical_values=(0.0, 0.0),
        tolerance=Fraction(1, 100),
    )
    assert not cert.verified
    assert cert.maximum_error == 2


def test_grid_evaluation_rejects_nonfinite_or_length_mismatch() -> None:
    with pytest.raises(ValueError):
        certify_grid_evaluation((Fraction(1),), (Fraction(0),), (float("nan"),), Fraction(1, 10))
    with pytest.raises(ValueError):
        certify_grid_evaluation((Fraction(1),), (Fraction(0),), (), Fraction(1, 10))


def test_grid_evaluation_requires_builtin_floats_and_exact_certificate_schema() -> None:
    with pytest.raises(ValueError, match="Python floats"):
        certify_grid_evaluation((1,), (0,), (_FloatSubclass(1.0),), 1)
    certificate = certify_grid_evaluation((1,), (0,), (1.0,), 0)
    assert not verify_grid_evaluation(replace(certificate, exact_values=(1,)))  # type: ignore[arg-type]
    assert not verify_grid_evaluation(replace(certificate, verified=1))  # type: ignore[arg-type]
    assert not verify_grid_evaluation(object())  # type: ignore[arg-type]


def test_grid_evaluation_rejects_unbounded_collections_and_work() -> None:
    with pytest.raises(ValueError, match="collection resource limit"):
        certify_grid_evaluation(range(5000), (0,), (0.0,), 0)
    with pytest.raises(ValueError, match="work resource limit"):
        certify_grid_evaluation(range(400), range(400), (0.0 for _ in range(400)), 0)


def test_all_exact_certificate_verifiers_reject_bool_equivalent_schema_forgery() -> None:
    cut = certify_sqrt2_cut(Fraction(7, 5), Fraction(3, 2))
    assert not verify_sqrt2_cut(
        cut.lower,
        cut.upper,
        replace(cut, verified=1),  # type: ignore[arg-type]
    )
