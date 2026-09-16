from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import mpmath as mp
import pytest

from . import elliptic_periods
from .elliptic_periods import certify_rectangular_periods, verify_period_certificate


def test_discriminant_convention_and_square_lattice_periods() -> None:
    cert = certify_rectangular_periods(Fraction(4), Fraction(0), decimal_places=18)
    assert cert.elliptic_discriminant == 64
    assert cert.polynomial_discriminant == 1024
    reference = Fraction("2.622057554292119810464839589891")
    assert cert.omega1.lower < reference < cert.omega1.upper
    assert cert.omega2_imag.lower < reference < cert.omega2_imag.upper
    assert verify_period_certificate(cert)


def test_nonsquare_positive_discriminant_full_periods() -> None:
    cert = certify_rectangular_periods(Fraction(4), Fraction(1), decimal_places=18)
    assert cert.omega1.lower < Fraction("2.451389381986790060854224831866") < cert.omega1.upper
    assert cert.omega2_imag.lower < Fraction("2.993458646231959629832009979452") < cert.omega2_imag.upper
    assert cert.invariant_diagnostic.within_threshold
    assert verify_period_certificate(cert)


@pytest.mark.parametrize("gap_exponent", (60, 256, 320))
def test_near_degenerate_positive_discriminant_adapts_interval_precision(
    gap_exponent: int,
) -> None:
    """A narrow real-root gap remains inside the certified rectangular domain."""

    g2 = Fraction(3)
    g3 = -Fraction(1) + Fraction(1, 2**gap_exponent)

    cert = certify_rectangular_periods(g2, g3, decimal_places=15)

    assert cert.elliptic_discriminant > 0
    assert cert.modulus.upper < 1
    assert verify_period_certificate(cert)


def test_singular_and_unsupported_curves_fail_closed() -> None:
    with pytest.raises(ValueError, match="singular"):
        certify_rectangular_periods(Fraction(3), Fraction(1))
    with pytest.raises(ValueError, match="positive discriminant"):
        certify_rectangular_periods(Fraction(0), Fraction(1))


def test_mutated_period_enclosure_does_not_verify() -> None:
    cert = certify_rectangular_periods(Fraction(5), Fraction(1), decimal_places=14)
    object.__setattr__(cert.omega1, "lower", cert.omega1.upper + 1)
    assert not verify_period_certificate(cert)


def test_invariant_diagnostic_is_non_authoritative() -> None:
    cert = certify_rectangular_periods(10**20, 0, decimal_places=12)
    assert not cert.invariant_diagnostic.authoritative
    assert not cert.invariant_diagnostic.within_threshold
    assert verify_period_certificate(cert)
    changed_diagnostic = replace(
        cert.invariant_diagnostic,
        within_threshold=not cert.invariant_diagnostic.within_threshold,
    )
    assert verify_period_certificate(replace(cert, invariant_diagnostic=changed_diagnostic))


def test_diagnostic_must_explicitly_remain_non_authoritative() -> None:
    cert = certify_rectangular_periods(4, 0, decimal_places=12)
    forged = replace(cert.invariant_diagnostic, authoritative=True)
    assert not verify_period_certificate(replace(cert, invariant_diagnostic=forged))
    malformed = replace(cert.invariant_diagnostic, relative_residual_g2="nan")
    assert not verify_period_certificate(replace(cert, invariant_diagnostic=malformed))


def test_non_authoritative_diagnostic_failure_cannot_break_exact_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    cert = certify_rectangular_periods(4, 1, decimal_places=12)

    def _fail(*args: object, **kwargs: object) -> object:
        raise ArithmeticError("diagnostic unavailable")

    monkeypatch.setattr(elliptic_periods, "_invariant_diagnostic", _fail)
    assert verify_period_certificate(cert)


def test_period_verifier_rejects_value_equal_but_inexact_authoritative_fields() -> None:
    cert = certify_rectangular_periods(4, 0, decimal_places=12)
    assert not verify_period_certificate(replace(cert, g2=4))  # type: ignore[arg-type]
    root = cert.root_intervals_descending[0]
    assert root.lower.denominator == 1
    forged_root = replace(root)
    object.__setattr__(forged_root, "lower", root.lower.numerator)
    forged_roots = (forged_root, *cert.root_intervals_descending[1:])
    assert not verify_period_certificate(replace(cert, root_intervals_descending=forged_roots))
    assert not verify_period_certificate(object())  # type: ignore[arg-type]


def test_period_precision_has_a_hard_resource_limit() -> None:
    with pytest.raises(ValueError, match="at most 64"):
        certify_rectangular_periods(4, 0, decimal_places=65)


def test_period_inputs_require_bounded_exact_rationals() -> None:
    with pytest.raises(TypeError, match="exact rational"):
        certify_rectangular_periods(True, 0)
    with pytest.raises(ValueError, match="resource limit"):
        certify_rectangular_periods(1 << 1100, 0)


def test_invariant_diagnostic_does_not_leak_mpmath_precision() -> None:
    original_precision = mp.mp.dps
    try:
        mp.mp.dps = 37
        certify_rectangular_periods(4, 1, decimal_places=14)
        assert mp.mp.dps == 37
    finally:
        mp.mp.dps = original_precision
