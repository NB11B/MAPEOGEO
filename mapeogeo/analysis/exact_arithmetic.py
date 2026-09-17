"""Exact rational and interval arithmetic for proof-eligible real analysis.

Enforces zero-float tolerance in proof-bearing pipelines.
All values are exact rational fractions (fractions.Fraction) or exact intervals.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Sequence


def ensure_exact_fraction(val: Any) -> Fraction:
    """Ensure value is an exact integer, Fraction, or rational string. Rejects float."""
    if isinstance(val, float):
        raise TypeError(
            f"Floating-point value {val} is strictly forbidden in proof-eligible arithmetic! "
            "Use fractions.Fraction, int, or rational string."
        )
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        if "." in val and "/" not in val:
            # Reject decimal float strings in proof-eligible arithmetic
            raise TypeError(
                f"Decimal string '{val}' treated as floating point; use Fraction(p, q) or 'p/q' format."
            )
        return Fraction(val)
    raise TypeError(f"Cannot convert {type(val)} to exact Fraction: {val}")


@dataclass(frozen=True)
class ExactInterval:
    """Exact rational closed interval [a, b] with a, b in Q, a <= b."""
    a: Fraction
    b: Fraction

    def __post_init__(self):
        # Validate exactness and ordering
        a_frac = ensure_exact_fraction(self.a)
        b_frac = ensure_exact_fraction(self.b)
        if a_frac > b_frac:
            raise ValueError(f"Invalid interval: lower bound {a_frac} > upper bound {b_frac}")
        object.__setattr__(self, "a", a_frac)
        object.__setattr__(self, "b", b_frac)

    @classmethod
    def from_bounds(cls, a: Any, b: Any) -> ExactInterval:
        return cls(ensure_exact_fraction(a), ensure_exact_fraction(b))

    @property
    def diameter(self) -> Fraction:
        return self.b - self.a

    @property
    def midpoint(self) -> Fraction:
        return (self.a + self.b) / 2

    def contains_point(self, x: Any) -> bool:
        x_frac = ensure_exact_fraction(x)
        return self.a <= x_frac <= self.b

    def contains_interval(self, other: ExactInterval) -> bool:
        return self.a <= other.a and other.b <= self.b

    def intersect(self, other: ExactInterval) -> ExactInterval | None:
        max_a = max(self.a, other.a)
        min_b = min(self.b, other.b)
        if max_a <= min_b:
            return ExactInterval(max_a, min_b)
        return None

    def __add__(self, other: Any) -> ExactInterval:
        if isinstance(other, ExactInterval):
            return ExactInterval(self.a + other.a, self.b + other.b)
        c = ensure_exact_fraction(other)
        return ExactInterval(self.a + c, self.b + c)

    def __sub__(self, other: Any) -> ExactInterval:
        if isinstance(other, ExactInterval):
            return ExactInterval(self.a - other.b, self.b - other.a)
        c = ensure_exact_fraction(other)
        return ExactInterval(self.a - c, self.b - c)

    def __mul__(self, other: Any) -> ExactInterval:
        if isinstance(other, ExactInterval):
            p1 = self.a * other.a
            p2 = self.a * other.b
            p3 = self.b * other.a
            p4 = self.b * other.b
            return ExactInterval(min(p1, p2, p3, p4), max(p1, p2, p3, p4))
        c = ensure_exact_fraction(other)
        p1 = self.a * c
        p2 = self.b * c
        return ExactInterval(min(p1, p2), max(p1, p2))

    def __truediv__(self, other: Any) -> ExactInterval:
        if isinstance(other, ExactInterval):
            if other.contains_point(0):
                raise ZeroDivisionError("Interval division by interval containing zero is undefined.")
            inv = ExactInterval(Fraction(1, 1) / other.b, Fraction(1, 1) / other.a)
            return self * inv
        c = ensure_exact_fraction(other)
        if c == 0:
            raise ZeroDivisionError("Division by zero fraction.")
        return self * (Fraction(1, 1) / c)

    def to_dict(self) -> dict[str, str]:
        return {"a": str(self.a), "b": str(self.b), "diam": str(self.diameter)}


@dataclass(frozen=True)
class ExactRationalPolynomial:
    """Exact polynomial P(x) = sum_{i=0}^d c_i x^i with c_i in Q."""
    coeffs: tuple[Fraction, ...]

    def __init__(self, coeffs: Sequence[Any]):
        validated = tuple(ensure_exact_fraction(c) for c in coeffs)
        # Trim leading zeros if non-constant
        while len(validated) > 1 and validated[-1] == 0:
            validated = validated[:-1]
        object.__setattr__(self, "coeffs", validated)

    @property
    def degree(self) -> int:
        return len(self.coeffs) - 1

    def eval(self, x: Any) -> Fraction:
        """Horner's rule exact polynomial evaluation."""
        x_frac = ensure_exact_fraction(x)
        result = Fraction(0, 1)
        for c in reversed(self.coeffs):
            result = result * x_frac + c
        return result

    def eval_interval(self, I: ExactInterval) -> ExactInterval:
        """Evaluate polynomial over interval via exact interval arithmetic."""
        result = ExactInterval(self.coeffs[-1], self.coeffs[-1])
        for c in reversed(self.coeffs[:-1]):
            result = (result * I) + c
        return result

    def derivative(self) -> ExactRationalPolynomial:
        if self.degree == 0:
            return ExactRationalPolynomial([0])
        d_coeffs = [self.coeffs[i] * i for i in range(1, len(self.coeffs))]
        return ExactRationalPolynomial(d_coeffs)

    def derivative_k(self, k: int) -> ExactRationalPolynomial:
        p = self
        for _ in range(k):
            p = p.derivative()
        return p

    def integrate(self, a: Any, b: Any) -> Fraction:
        """Exact definite integral int_a^b P(x) dx."""
        a_frac = ensure_exact_fraction(a)
        b_frac = ensure_exact_fraction(b)
        # Antiderivative coefficients
        anti_coeffs = [Fraction(0, 1)] + [self.coeffs[i] / (i + 1) for i in range(len(self.coeffs))]
        anti = ExactRationalPolynomial(anti_coeffs)
        return anti.eval(b_frac) - anti.eval(a_frac)

    def taylor_polynomial(self, x0: Any, k: int) -> ExactRationalPolynomial:
        """Compute degree-k Taylor polynomial at x0 in standard basis."""
        x0_frac = ensure_exact_fraction(x0)
        # Expansion: P(x) = sum_{j=0}^k (P^(j)(x0)/j!) (x - x0)^j
        # We accumulate polynomials in standard basis
        current_poly = ExactRationalPolynomial([0])
        x_minus_x0 = ExactRationalPolynomial([-x0_frac, Fraction(1, 1)])

        factorial = 1
        x_minus_x0_pow = ExactRationalPolynomial([1])

        for j in range(k + 1):
            deriv_j = self.derivative_k(j)
            coeff_j = deriv_j.eval(x0_frac) / factorial
            term = x_minus_x0_pow * coeff_j
            current_poly = current_poly + term
            # Update for next iteration
            factorial *= (j + 1)
            x_minus_x0_pow = x_minus_x0_pow * x_minus_x0

        return current_poly

    def __add__(self, other: Any) -> ExactRationalPolynomial:
        if isinstance(other, ExactRationalPolynomial):
            max_len = max(len(self.coeffs), len(other.coeffs))
            c1 = list(self.coeffs) + [Fraction(0, 1)] * (max_len - len(self.coeffs))
            c2 = list(other.coeffs) + [Fraction(0, 1)] * (max_len - len(other.coeffs))
            return ExactRationalPolynomial([c1[i] + c2[i] for i in range(max_len)])
        c = ensure_exact_fraction(other)
        new_c = list(self.coeffs)
        new_c[0] += c
        return ExactRationalPolynomial(new_c)

    def __sub__(self, other: Any) -> ExactRationalPolynomial:
        return self + (other * Fraction(-1, 1))

    def __mul__(self, other: Any) -> ExactRationalPolynomial:
        if isinstance(other, ExactRationalPolynomial):
            res_coeffs = [Fraction(0, 1)] * (len(self.coeffs) + len(other.coeffs) - 1)
            for i, c1 in enumerate(self.coeffs):
                for j, c2 in enumerate(other.coeffs):
                    res_coeffs[i + j] += c1 * c2
            return ExactRationalPolynomial(res_coeffs)
        c = ensure_exact_fraction(other)
        return ExactRationalPolynomial([coeff * c for coeff in self.coeffs])

    def to_dict(self) -> dict[str, Any]:
        return {
            "degree": self.degree,
            "coeffs": [str(c) for c in self.coeffs],
        }


@dataclass(frozen=True)
class RationalMeshPartition:
    """Exact partition of [a, b] by strictly increasing rational points a = x_0 < x_1 < ... < x_n = b."""
    points: tuple[Fraction, ...]

    def __init__(self, points: Sequence[Any]):
        if len(points) < 2:
            raise ValueError("Partition must contain at least 2 points.")
        frac_points = tuple(ensure_exact_fraction(p) for p in points)
        for i in range(len(frac_points) - 1):
            if frac_points[i] >= frac_points[i + 1]:
                raise ValueError(
                    f"Partition points must be strictly increasing: points[{i}]={frac_points[i]} >= points[{i+1}]={frac_points[i+1]}"
                )
        object.__setattr__(self, "points", frac_points)

    @classmethod
    def uniform(cls, a: Any, b: Any, n: int) -> RationalMeshPartition:
        a_frac = ensure_exact_fraction(a)
        b_frac = ensure_exact_fraction(b)
        if n < 1:
            raise ValueError("Subinterval count n must be >= 1.")
        step = (b_frac - a_frac) / n
        pts = [a_frac + step * i for i in range(n + 1)]
        return cls(pts)

    @property
    def mesh_width(self) -> Fraction:
        return max(self.points[i + 1] - self.points[i] for i in range(len(self.points) - 1))

    @property
    def interval(self) -> ExactInterval:
        return ExactInterval(self.points[0], self.points[-1])

    def upper_darboux_sum(self, poly: ExactRationalPolynomial) -> Fraction:
        """Exact upper Darboux sum U(P, f) using interval supremum over each subinterval."""
        total = Fraction(0, 1)
        for i in range(len(self.points) - 1):
            sub_int = ExactInterval(self.points[i], self.points[i + 1])
            val_int = poly.eval_interval(sub_int)
            sup_i = val_int.b
            delta_x = self.points[i + 1] - self.points[i]
            total += sup_i * delta_x
        return total

    def lower_darboux_sum(self, poly: ExactRationalPolynomial) -> Fraction:
        """Exact lower Darboux sum L(P, f) using interval infimum over each subinterval."""
        total = Fraction(0, 1)
        for i in range(len(self.points) - 1):
            sub_int = ExactInterval(self.points[i], self.points[i + 1])
            val_int = poly.eval_interval(sub_int)
            inf_i = val_int.a
            delta_x = self.points[i + 1] - self.points[i]
            total += inf_i * delta_x
        return total

    def darboux_gap(self, poly: ExactRationalPolynomial) -> Fraction:
        return self.upper_darboux_sum(poly) - self.lower_darboux_sum(poly)

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_subintervals": len(self.points) - 1,
            "mesh_width": str(self.mesh_width),
            "interval": self.interval.to_dict(),
        }
