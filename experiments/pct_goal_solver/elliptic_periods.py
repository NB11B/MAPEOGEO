"""Certified real period enclosures for a scoped Weierstrass family.

The supported curve is ``y^2 = 4*x^3 - g2*x - g3`` with exact rational
invariants and positive elliptic discriminant.  In this regime the cubic has
three distinct real roots ``e1 > e2 > e3`` and a rectangular fundamental
lattice.  Root isolation, square roots, pi, and AGM evaluation are all carried
as rational intervals.  Floating-point values are used only by the independent,
non-authoritative q-series diagnostic; they do not establish or invalidate the
enclosure.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import math

import mpmath as mp
import sympy as sp


_MAX_DECIMAL_PLACES = 64
_MAX_INVARIANT_BITS = 1024
_MAX_CERTIFICATE_BITS = 8192
_MAX_DIAGNOSTIC_TEXT = 256
_MAX_WORKING_DECIMAL_PLACES = 2048


class PeriodCertificationUnavailable(ArithmeticError):
    """The bounded interval algorithm could not certify an in-domain curve."""


class _InsufficientIntervalPrecision(ArithmeticError):
    """A retry with finer rational intervals may establish the enclosure."""


@dataclass(frozen=True)
class RationalInterval:
    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        if type(self.lower) is not Fraction or type(self.upper) is not Fraction:
            raise TypeError("rational interval endpoints must be exact Fraction values")
        if self.lower > self.upper:
            raise ValueError("interval lower endpoint exceeds upper endpoint")

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    @property
    def midpoint(self) -> Fraction:
        return (self.lower + self.upper) / 2


@dataclass(frozen=True)
class InvariantDiagnostic:
    """Non-authoritative floating-point comparison against q-series invariants."""

    terms: int
    reconstructed_g2: str
    reconstructed_g3: str
    relative_residual_g2: str
    relative_residual_g3: str
    e4_tail_bound: str
    e6_tail_bound: str
    within_threshold: bool
    authoritative: bool = False


@dataclass(frozen=True)
class PeriodCertificate:
    g2: Fraction
    g3: Fraction
    elliptic_discriminant: Fraction
    polynomial_discriminant: Fraction
    root_intervals_descending: tuple[RationalInterval, RationalInterval, RationalInterval]
    modulus: RationalInterval
    omega1: RationalInterval
    omega2_imag: RationalInterval
    decimal_places: int
    invariant_diagnostic: InvariantDiagnostic


def _as_fraction(value: Fraction | int, name: str) -> Fraction:
    if type(value) not in (Fraction, int):
        raise TypeError(f"{name} must be an exact rational")
    result = Fraction(value)
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > _MAX_INVARIANT_BITS:
        raise ValueError(f"{name} exceeds the exact-rational resource limit")
    return result


def _validate_decimal_places(decimal_places: object) -> int:
    if type(decimal_places) is not int or not 10 <= decimal_places <= _MAX_DECIMAL_PLACES:
        raise ValueError(
            f"decimal_places must be an integer from 10 to at most {_MAX_DECIMAL_PLACES}"
        )
    return decimal_places


def _add(a: RationalInterval, b: RationalInterval) -> RationalInterval:
    return RationalInterval(a.lower + b.lower, a.upper + b.upper)


def _sub(a: RationalInterval, b: RationalInterval) -> RationalInterval:
    return RationalInterval(a.lower - b.upper, a.upper - b.lower)


def _scale(value: RationalInterval, scalar: Fraction) -> RationalInterval:
    if scalar >= 0:
        return RationalInterval(value.lower * scalar, value.upper * scalar)
    return RationalInterval(value.upper * scalar, value.lower * scalar)


def _mul_positive(a: RationalInterval, b: RationalInterval) -> RationalInterval:
    if a.lower < 0 or b.lower < 0:
        raise ValueError("positive interval multiplication received a negative endpoint")
    return RationalInterval(a.lower * b.lower, a.upper * b.upper)


def _div_positive(a: RationalInterval, b: RationalInterval) -> RationalInterval:
    if a.lower < 0 or b.lower <= 0:
        raise ValueError("positive interval division requires a positive denominator")
    return RationalInterval(a.lower / b.upper, a.upper / b.lower)


def _sqrt_fraction_interval(value: Fraction, places: int) -> RationalInterval:
    if value < 0:
        raise ValueError("cannot enclose a negative square root")
    if value == 0:
        return RationalInterval(Fraction(0), Fraction(0))
    scale = 10**places
    scaled_floor = value.numerator * scale * scale // value.denominator
    root_floor = math.isqrt(scaled_floor)
    lower = Fraction(root_floor, scale)
    upper = lower if lower * lower == value else Fraction(root_floor + 1, scale)
    return RationalInterval(lower, upper)


def _sqrt_interval(value: RationalInterval, places: int) -> RationalInterval:
    if value.lower < 0:
        raise ValueError("cannot enclose a square root crossing negative values")
    lower = _sqrt_fraction_interval(value.lower, places).lower
    upper = _sqrt_fraction_interval(value.upper, places).upper
    return RationalInterval(lower, upper)


def _arctan_reciprocal_interval(q: int, target: Fraction) -> RationalInterval:
    if q <= 1:
        raise ValueError("alternating arctan enclosure requires q > 1")
    partial = Fraction(0)
    n = 0
    while True:
        term = Fraction(1, (2 * n + 1) * q ** (2 * n + 1))
        partial = partial + term if n % 2 == 0 else partial - term
        next_n = n + 1
        next_term = Fraction(1, (2 * next_n + 1) * q ** (2 * next_n + 1))
        if next_term <= target:
            adjacent = partial + next_term if next_n % 2 == 0 else partial - next_term
            return RationalInterval(min(partial, adjacent), max(partial, adjacent))
        n = next_n


def _pi_interval(places: int) -> RationalInterval:
    target = Fraction(1, 10 ** (places + 8))
    a = _arctan_reciprocal_interval(5, target / 32)
    b = _arctan_reciprocal_interval(239, target / 8)
    # Machin: pi = 16 atan(1/5) - 4 atan(1/239).
    return RationalInterval(16 * a.lower - 4 * b.upper, 16 * a.upper - 4 * b.lower)


def _agm_interval(
    a: RationalInterval,
    b: RationalInterval,
    places: int,
    *,
    target_places: int | None = None,
) -> RationalInterval:
    if a.lower <= 0 or b.lower <= 0:
        raise _InsufficientIntervalPrecision("AGM input enclosure reached zero")
    # ``places`` controls interval arithmetic precision.  ``target_places``
    # remains tied to the requested certificate precision while adaptive
    # retries refine the roots and square roots.  Conflating these two roles
    # would make every retry demand an even narrower (and unnecessary) AGM.
    target_precision = places if target_places is None else target_places
    target = Fraction(1, 10 ** (target_precision - 2))
    current_a, current_b = a, b
    for _ in range(80):
        enclosure = RationalInterval(
            min(current_a.lower, current_b.lower),
            max(current_a.upper, current_b.upper),
        )
        if enclosure.width <= target:
            return enclosure
        next_a = _scale(_add(current_a, current_b), Fraction(1, 2))
        next_b = _sqrt_interval(_mul_positive(current_a, current_b), places + 10)
        current_a, current_b = next_a, next_b
    raise _InsufficientIntervalPrecision("AGM interval failed to contract")


def _sympy_fraction(value: sp.Rational) -> Fraction:
    return Fraction(int(value.p), int(value.q))


def _isolate_roots(g2: Fraction, g3: Fraction, places: int) -> tuple[RationalInterval, RationalInterval, RationalInterval]:
    x = sp.Symbol("x")
    polynomial = sp.Poly(
        4 * x**3 - sp.Rational(g2.numerator, g2.denominator) * x - sp.Rational(g3.numerator, g3.denominator),
        x,
        domain=sp.QQ,
    )
    epsilon = sp.Rational(1, 10 ** (places + 12))
    raw = polynomial.intervals(eps=epsilon)
    if len(raw) != 3 or any(multiplicity != 1 for _, multiplicity in raw):
        raise _InsufficientIntervalPrecision(
            "root isolation did not yet separate three simple real roots"
        )
    intervals = [RationalInterval(_sympy_fraction(pair[0]), _sympy_fraction(pair[1])) for pair, _ in raw]
    intervals.sort(key=lambda item: item.midpoint, reverse=True)
    if not (
        intervals[0].lower > intervals[1].upper
        and intervals[1].lower > intervals[2].upper
    ):
        raise _InsufficientIntervalPrecision(
            "root intervals are not yet disjoint and ordered"
        )
    return intervals[0], intervals[1], intervals[2]


def _divisor_power_sum(n: int, power: int) -> int:
    total = 0
    root = math.isqrt(n)
    for divisor in range(1, root + 1):
        if n % divisor:
            continue
        other = n // divisor
        total += divisor**power
        if other != divisor:
            total += other**power
    return total


def _eisenstein_sums(q: mp.mpf, places: int) -> tuple[mp.mpf, mp.mpf, int, mp.mpf, mp.mpf]:
    e4_sum = mp.mpf("0")
    e6_sum = mp.mpf("0")
    target = mp.power(10, -(places + 8))
    n = 1
    while True:
        qn = q**n
        e4_sum += _divisor_power_sum(n, 3) * qn
        e6_sum += _divisor_power_sum(n, 5) * qn
        n0 = n + 1
        rho4 = q * mp.power(mp.mpf(n0 + 1) / n0, 3)
        rho6 = q * mp.power(mp.mpf(n0 + 1) / n0, 5)
        if rho4 < 1 and rho6 < 1:
            tail4 = mp.zeta(3) * n0**3 * q**n0 / (1 - rho4)
            tail6 = mp.zeta(5) * n0**5 * q**n0 / (1 - rho6)
            if max(240 * tail4, 504 * tail6) < target:
                return 1 + 240 * e4_sum, 1 - 504 * e6_sum, n, 240 * tail4, 504 * tail6
        n += 1
        if n > 100000:
            raise ArithmeticError("q-series failed to reach the requested tail bound")


def _invariant_diagnostic(
    g2: Fraction,
    g3: Fraction,
    omega1: RationalInterval,
    omega2_imag: RationalInterval,
    places: int,
) -> InvariantDiagnostic:
    with mp.workdps(max(60, places + 35)):
        w1 = mp.mpf(omega1.midpoint.numerator) / omega1.midpoint.denominator
        w2 = mp.mpf(omega2_imag.midpoint.numerator) / omega2_imag.midpoint.denominator
        tau_imag = w2 / w1
        q = mp.e ** (-2 * mp.pi * tau_imag)
        e4, e6, terms, tail4, tail6 = _eisenstein_sums(q, places)
        reconstructed_g2 = 4 * mp.pi**4 * e4 / (3 * w1**4)
        reconstructed_g3 = 8 * mp.pi**6 * e6 / (27 * w1**6)
        target_g2 = mp.mpf(g2.numerator) / g2.denominator
        target_g3 = mp.mpf(g3.numerator) / g3.denominator
        residual_g2 = abs(reconstructed_g2 - target_g2) / max(mp.mpf(1), abs(target_g2))
        residual_g3 = abs(reconstructed_g3 - target_g3) / max(mp.mpf(1), abs(target_g3))
        threshold = mp.power(10, -max(8, min(places - 3, 14)))
        return InvariantDiagnostic(
            terms=terms,
            reconstructed_g2=mp.nstr(reconstructed_g2, places + 8),
            reconstructed_g3=mp.nstr(reconstructed_g3, places + 8),
            relative_residual_g2=mp.nstr(residual_g2, places + 8),
            relative_residual_g3=mp.nstr(residual_g3, places + 8),
            e4_tail_bound=mp.nstr(tail4, places + 8),
            e6_tail_bound=mp.nstr(tail6, places + 8),
            within_threshold=bool(residual_g2 <= threshold and residual_g3 <= threshold),
        )


def _authoritative_period_data_at_precision(
    invariant_g2: Fraction,
    invariant_g3: Fraction,
    decimal_places: int,
    working_places: int,
) -> tuple[
    Fraction,
    Fraction,
    tuple[RationalInterval, RationalInterval, RationalInterval],
    RationalInterval,
    RationalInterval,
    RationalInterval,
]:
    """Compute authoritative fields at one bounded working precision."""

    discriminant = invariant_g2**3 - 27 * invariant_g3**2
    roots = _isolate_roots(invariant_g2, invariant_g3, working_places)
    e1, e2, e3 = roots
    d = _sub(e1, e3)
    numerator = _sub(e2, e3)
    modulus = _div_positive(numerator, d)
    if not (0 < modulus.lower <= modulus.upper < 1):
        raise _InsufficientIntervalPrecision(
            "root enclosures did not establish a modulus inside (0, 1)"
        )

    one = RationalInterval(Fraction(1), Fraction(1))
    complementary = _sub(one, modulus)
    b_primary = _sqrt_interval(complementary, working_places + 12)
    b_complementary = _sqrt_interval(modulus, working_places + 12)
    agm_primary = _agm_interval(
        one,
        b_primary,
        working_places + 8,
        target_places=decimal_places + 8,
    )
    agm_complementary = _agm_interval(
        one,
        b_complementary,
        working_places + 8,
        target_places=decimal_places + 8,
    )
    pi = _pi_interval(decimal_places + 10)
    k_primary = _div_positive(pi, _scale(agm_primary, Fraction(2)))
    k_complementary = _div_positive(pi, _scale(agm_complementary, Fraction(2)))
    sqrt_d = _sqrt_interval(d, working_places + 12)
    omega1 = _div_positive(_scale(k_primary, Fraction(2)), sqrt_d)
    omega2_imag = _div_positive(_scale(k_complementary, Fraction(2)), sqrt_d)
    requested_width = Fraction(1, 10**decimal_places)
    if omega1.width > requested_width or omega2_imag.width > requested_width:
        raise _InsufficientIntervalPrecision(
            "period enclosures remain wider than the requested decimal precision"
        )
    return discriminant, 16 * discriminant, roots, modulus, omega1, omega2_imag


def _authoritative_period_data(
    invariant_g2: Fraction,
    invariant_g3: Fraction,
    decimal_places: int,
) -> tuple[
    Fraction,
    Fraction,
    tuple[RationalInterval, RationalInterval, RationalInterval],
    RationalInterval,
    RationalInterval,
    RationalInterval,
]:
    """Compute exact/interval fields with bounded adaptive precision.

    Positive discriminant proves that the cubic has three simple real roots,
    but it does not provide a uniform separation bound at the caller's output
    precision.  Near a double-root limit, fixed-width root enclosures are too
    coarse for the square-root and AGM maps.  We therefore increase only the
    internal rational working precision while keeping the requested output
    width fixed.  The schedule and ceiling make the retry policy deterministic
    and bounded; exhaustion is an explicit inability to certify, never an
    invalid-mathematics verdict.
    """

    discriminant = invariant_g2**3 - 27 * invariant_g3**2
    if discriminant == 0:
        raise ValueError("singular Weierstrass curve")
    if discriminant < 0:
        raise ValueError("campaign certificate requires positive discriminant")

    working_places = decimal_places
    last_error: _InsufficientIntervalPrecision | None = None
    while working_places <= _MAX_WORKING_DECIMAL_PLACES:
        try:
            return _authoritative_period_data_at_precision(
                invariant_g2,
                invariant_g3,
                decimal_places,
                working_places,
            )
        except _InsufficientIntervalPrecision as exc:
            last_error = exc
        if working_places == _MAX_WORKING_DECIMAL_PLACES:
            break
        guard_digits = max(2, working_places - decimal_places)
        next_places = min(
            _MAX_WORKING_DECIMAL_PLACES,
            decimal_places + 2 * guard_digits,
        )
        if next_places <= working_places:
            break
        working_places = next_places

    raise PeriodCertificationUnavailable(
        "bounded adaptive interval precision was exhausted"
    ) from last_error


def certify_rectangular_periods(
    g2: Fraction | int,
    g3: Fraction | int,
    *,
    decimal_places: int = 15,
) -> PeriodCertificate:
    """Return rational enclosures for full fundamental periods.

    Negative-discriminant curves have a different basis formula and are
    intentionally outside this campaign's frozen scope.  ``invariant_diagnostic``
    is explicitly non-authoritative: it is useful as an independent numerical
    smoke check, but none of its values participate in exact verification.
    """

    invariant_g2 = _as_fraction(g2, "g2")
    invariant_g3 = _as_fraction(g3, "g3")
    places = _validate_decimal_places(decimal_places)
    (
        discriminant,
        polynomial_discriminant,
        roots,
        modulus,
        omega1,
        omega2_imag,
    ) = _authoritative_period_data(invariant_g2, invariant_g3, places)
    diagnostic = _invariant_diagnostic(invariant_g2, invariant_g3, omega1, omega2_imag, decimal_places)
    return PeriodCertificate(
        g2=invariant_g2,
        g3=invariant_g3,
        elliptic_discriminant=discriminant,
        polynomial_discriminant=polynomial_discriminant,
        root_intervals_descending=roots,
        modulus=modulus,
        omega1=omega1,
        omega2_imag=omega2_imag,
        decimal_places=decimal_places,
        invariant_diagnostic=diagnostic,
    )


def _valid_interval_schema(value: object) -> bool:
    return (
        type(value) is RationalInterval
        and type(value.lower) is Fraction
        and type(value.upper) is Fraction
        and max(abs(value.lower.numerator).bit_length(), value.lower.denominator.bit_length())
        <= _MAX_CERTIFICATE_BITS
        and max(abs(value.upper.numerator).bit_length(), value.upper.denominator.bit_length())
        <= _MAX_CERTIFICATE_BITS
        and value.lower <= value.upper
    )


def _valid_certificate_fraction(value: object) -> bool:
    return (
        type(value) is Fraction
        and max(abs(value.numerator).bit_length(), value.denominator.bit_length())
        <= _MAX_CERTIFICATE_BITS
    )


def _diagnostic_decimal(value: object, *, nonnegative: bool = False) -> bool:
    if type(value) is not str or not value or len(value) > _MAX_DIAGNOSTIC_TEXT:
        return False
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return False
    return parsed.is_finite() and (not nonnegative or parsed >= 0)


def _valid_non_authoritative_diagnostic(value: object) -> bool:
    """Validate the diagnostic's schema, never its numerical conclusion."""

    return (
        type(value) is InvariantDiagnostic
        and type(value.terms) is int
        and 0 <= value.terms <= 100_000
        and _diagnostic_decimal(value.reconstructed_g2)
        and _diagnostic_decimal(value.reconstructed_g3)
        and _diagnostic_decimal(value.relative_residual_g2, nonnegative=True)
        and _diagnostic_decimal(value.relative_residual_g3, nonnegative=True)
        and _diagnostic_decimal(value.e4_tail_bound, nonnegative=True)
        and _diagnostic_decimal(value.e6_tail_bound, nonnegative=True)
        and type(value.within_threshold) is bool
        and value.authoritative is False
    )


def verify_period_certificate(certificate: PeriodCertificate) -> bool:
    """Replay every authoritative field without executing the diagnostic.

    The diagnostic is accepted only when it explicitly declares itself
    non-authoritative and has a bounded, finite schema.  Its numerical values
    are deliberately excluded from the acceptance decision.
    """

    if (
        type(certificate) is not PeriodCertificate
        or not _valid_certificate_fraction(certificate.g2)
        or not _valid_certificate_fraction(certificate.g3)
        or not _valid_certificate_fraction(certificate.elliptic_discriminant)
        or not _valid_certificate_fraction(certificate.polynomial_discriminant)
        or type(certificate.root_intervals_descending) is not tuple
        or len(certificate.root_intervals_descending) != 3
        or any(not _valid_interval_schema(value) for value in certificate.root_intervals_descending)
        or not _valid_interval_schema(certificate.modulus)
        or not _valid_interval_schema(certificate.omega1)
        or not _valid_interval_schema(certificate.omega2_imag)
        or type(certificate.decimal_places) is not int
        or not _valid_non_authoritative_diagnostic(certificate.invariant_diagnostic)
    ):
        return False
    try:
        invariant_g2 = _as_fraction(certificate.g2, "g2")
        invariant_g3 = _as_fraction(certificate.g3, "g3")
        places = _validate_decimal_places(certificate.decimal_places)
        authoritative = _authoritative_period_data(
            invariant_g2,
            invariant_g3,
            places,
        )
    except (ArithmeticError, TypeError, ValueError):
        return False
    expected = (
        invariant_g2,
        invariant_g3,
        *authoritative,
        places,
    )
    observed = (
        certificate.g2,
        certificate.g3,
        certificate.elliptic_discriminant,
        certificate.polynomial_discriminant,
        certificate.root_intervals_descending,
        certificate.modulus,
        certificate.omega1,
        certificate.omega2_imag,
        certificate.decimal_places,
    )
    return observed == expected
