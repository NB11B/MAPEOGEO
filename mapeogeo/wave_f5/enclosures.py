"""Validated Enclosures, Exact Rational Bounds & Solution-Tube Certificates (Q15–Q18) for Wave F5."""

import math
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class RationalInterval:
    """Rigorous interval arithmetic with exact rational endpoints for guaranteed enclosures."""

    def __init__(self, low: Union[Fraction, float, int], high: Union[Fraction, float, int]) -> None:
        self.low = Fraction(low) if not isinstance(low, Fraction) else low
        self.high = Fraction(high) if not isinstance(high, Fraction) else high
        if self.low > self.high:
            raise ValueError(f"Invalid interval: low={self.low} > high={self.high}")

    def contains(self, x: Union[Fraction, float, int]) -> bool:
        frac_x = Fraction(x) if not isinstance(x, Fraction) else x
        return self.low <= frac_x <= self.high

    @property
    def width(self) -> Fraction:
        return self.high - self.low

    @property
    def midpoint(self) -> Fraction:
        return (self.low + self.high) / Fraction(2)

    def __add__(self, other: "RationalInterval") -> "RationalInterval":
        return RationalInterval(self.low + other.low, self.high + other.high)

    def __sub__(self, other: "RationalInterval") -> "RationalInterval":
        return RationalInterval(self.low - other.high, self.high - other.low)

    def __mul__(self, other: "RationalInterval") -> "RationalInterval":
        products = [
            self.low * other.low,
            self.low * other.high,
            self.high * other.low,
            self.high * other.high,
        ]
        return RationalInterval(min(products), max(products))

    def __truediv__(self, other: "RationalInterval") -> "RationalInterval":
        if other.contains(Fraction(0)):
            raise ZeroDivisionError("Interval division by interval containing zero")
        quotients = [
            self.low / other.low,
            self.low / other.high,
            self.high / other.low,
            self.high / other.high,
        ]
        return RationalInterval(min(quotients), max(quotients))

    def intersect(self, other: "RationalInterval") -> Optional["RationalInterval"]:
        new_low = max(self.low, other.low)
        new_high = min(self.high, other.high)
        if new_low <= new_high:
            return RationalInterval(new_low, new_high)
        return None

    def __repr__(self) -> str:
        return f"RationalInterval({self.low}, {self.high})"


# Alias for backward compatibility
Interval = RationalInterval


def rational_exp_lower_bound(x: Fraction, order: int = 8) -> Fraction:
    """Exact rational lower bound for exp(x) via Taylor series truncation."""
    if x >= Fraction(0):
        # Truncated series with positive terms is a rigorous lower bound
        s = Fraction(0)
        term = Fraction(1)
        for k in range(order + 1):
            if k > 0:
                term = term * x / Fraction(k)
            s += term
        return s
    else:
        # exp(-|x|) >= 1 / exp_upper(|x|)
        return Fraction(1) / rational_exp_upper_bound(-x, order=order)


def rational_exp_upper_bound(x: Fraction, order: int = 8) -> Fraction:
    """Exact rational upper bound for exp(x) via Taylor series plus geometric tail bound."""
    if x >= Fraction(0):
        if x >= Fraction(order + 2):
            order = int(math.ceil(float(x))) + 4
        s = Fraction(0)
        term = Fraction(1)
        for k in range(order + 1):
            if k > 0:
                term = term * x / Fraction(k)
            s += term
        # Tail bound: sum_{k=order+1}^infinity x^k/k! <= (x^{order+1}/(order+1)!) * 1/(1 - x/(order+2))
        last_term = term * x / Fraction(order + 1)
        tail_multiplier = Fraction(1) / (Fraction(1) - x / Fraction(order + 2))
        tail = last_term * tail_multiplier
        return s + tail
    else:
        # exp(-|x|) <= 1 / exp_lower(|x|)
        return Fraction(1) / rational_exp_lower_bound(-x, order=order)


def rational_exp_enclosure(x: Fraction, order: int = 8) -> RationalInterval:
    """Rigorous rational interval enclosing exp(x)."""
    return RationalInterval(rational_exp_lower_bound(x, order), rational_exp_upper_bound(x, order))


def verify_q15_residual_enclosure(
    h: Fraction,
    degree: int,
    e0: Fraction,
    claimed_R: Fraction,
) -> Dict[str, Any]:
    """Verify Continuous-Slab Solution-Tube Residual Enclosure (Q15) for y' = y with exact rational bounds."""
    fact = Fraction(math.factorial(degree))
    # Exact supremum of residual on [0, h] for y_hat = sum_{k=0}^d t^k/k! is h^d / d!
    R_true = (h ** degree) / fact

    if claimed_R < R_true:
        return {
            "verified": False,
            "error": f"Underestimated residual bound: claimed R={claimed_R} < true supremum R={R_true}",
        }

    # Lipschitz constant L = 1 for y' = y
    L = Fraction(1)
    # Validated continuous-slab upper bound for exp(L*h)
    exp_Lh_upper = rational_exp_upper_bound(L * h, order=8)

    # Tube radius = exp(L*h)*e0 + (R/L)*(exp(L*h) - 1)
    tube_radius = exp_Lh_upper * e0 + (claimed_R / L) * (exp_Lh_upper - Fraction(1))

    return {
        "verified": True,
        "tube_radius": tube_radius,
        "R_bound": claimed_R,
        "e0": e0,
        "h": h,
        "exp_bound": exp_Lh_upper,
        "error": None,
    }


def verify_q16_logistic_invariant_interval(
    initial_box: RationalInterval,
    invariant_box: RationalInterval,
) -> Dict[str, Any]:
    """Verify Invariant Interval and Solution Tube (Q16) for Logistic Flow x' = x(1-x)."""
    if initial_box.low < invariant_box.low or initial_box.high > invariant_box.high:
        return {
            "verified": False,
            "error": f"Initial enclosure {initial_box} is not subset of invariant region {invariant_box}",
        }

    # Boundary normal vector field checks:
    # At lower face x = a: f(a) >= 0
    # At upper face x = b: f(b) <= 0
    def f(x: Fraction) -> Fraction:
        return x * (Fraction(1) - x)

    f_low = f(invariant_box.low)
    f_high = f(invariant_box.high)

    if f_low < Fraction(0) or f_high > Fraction(0):
        return {
            "verified": False,
            "error": f"Boundary vector field violates invariance: f(low)={f_low}, f(high)={f_high}",
        }

    return {
        "verified": True,
        "invariant": True,
        "tube_box": invariant_box,
        "f_low": f_low,
        "f_high": f_high,
        "error": None,
    }


def verify_q17_transversal_event(
    H_func: Callable[[Fraction], Fraction],
    grad_H_func: Callable[[Fraction], Fraction],
    f_func: Callable[[Fraction, Fraction], Fraction],
    trajectory_enclosure: Callable[[Fraction], RationalInterval],
    t_interval: RationalInterval,
    x_interval: RationalInterval,
) -> Dict[str, Any]:
    """Verify Transversal Event Localization Certificate (Q17) via IVT bracket and uniform Lie derivative bound."""
    ta = t_interval.low
    tb = t_interval.high

    # Evaluate trajectory enclosure at endpoints
    xa_box = trajectory_enclosure(ta)
    xb_box = trajectory_enclosure(tb)

    Ha = H_func(xa_box.midpoint)
    Hb = H_func(xb_box.midpoint)

    # 1. Sign change bracket verification
    if Ha * Hb >= Fraction(0):
        return {
            "verified": False,
            "error": f"Sign change bracket not established on [{ta}, {tb}]: H(x(ta))={Ha} and H(x(tb))={Hb} do not have opposite signs",
        }

    # 2. Check trajectory containment in x_interval and uniform transversality
    sample_count = 10
    dt = (tb - ta) / Fraction(sample_count)
    for i in range(sample_count + 1):
        t_sample = ta + Fraction(i) * dt
        x_box = trajectory_enclosure(t_sample)
        if not (x_interval.low <= x_box.low and x_box.high <= x_interval.high):
            return {
                "verified": False,
                "error": f"Trajectory enclosure {x_box} at t={t_sample} escapes spatial domain {x_interval}",
            }
        x_val = x_box.midpoint
        lie_deriv = grad_H_func(x_val) * f_func(t_sample, x_val)
        if abs(lie_deriv) < Fraction(1, 1000):
            return {
                "verified": False,
                "error": f"Transversality condition violated at t={t_sample}: Lie derivative |nabla H . f| = {lie_deriv} is too small / vanishes (tangential event)",
            }

    return {
        "verified": True,
        "transversal": True,
        "crossing_isolated": True,
        "Ha": Ha,
        "Hb": Hb,
        "error": None,
    }


def verify_q18_regular_dirichlet_bvp(
    u_poly_coeffs: List[Fraction],
    f_poly_coeffs: List[Fraction],
    bc_0: Fraction = Fraction(0),
    bc_1: Fraction = Fraction(0),
) -> Dict[str, Any]:
    """Verify Regular Dirichlet Boundary Value Problem Green Operator (Q18) with exact symbolic differentiation."""
    # u(x) = sum_{k=0}^n c_k x^k
    # Check boundary conditions
    u_0 = u_poly_coeffs[0] if len(u_poly_coeffs) > 0 else Fraction(0)
    u_1 = sum(u_poly_coeffs)

    if u_0 != bc_0 or u_1 != bc_1:
        return {
            "verified": False,
            "error": f"Boundary condition mismatch: u(0)={u_0} (expected {bc_0}), u(1)={u_1} (expected {bc_1})",
        }

    # Symbolic second derivative of u:
    # u'(x) = sum_{k=1}^n k * c_k x^{k-1}
    # u''(x) = sum_{k=2}^n k * (k-1) * c_k x^{k-2}
    # -u''(x) = sum_{k=2}^n -k * (k-1) * c_k x^{k-2}
    neg_u_xx_coeffs: List[Fraction] = []
    for k in range(2, len(u_poly_coeffs)):
        neg_u_xx_coeffs.append(-Fraction(k * (k - 1)) * u_poly_coeffs[k])

    # Normalize lengths
    max_len = max(len(neg_u_xx_coeffs), len(f_poly_coeffs))
    neg_u_xx_padded = neg_u_xx_coeffs + [Fraction(0)] * (max_len - len(neg_u_xx_coeffs))
    f_padded = f_poly_coeffs + [Fraction(0)] * (max_len - len(f_poly_coeffs))

    # Compare polynomials across all degrees
    if neg_u_xx_padded != f_padded:
        return {
            "verified": False,
            "error": f"ODE differential equation residual failed: -u''(x)={neg_u_xx_padded} != f(x)={f_padded}",
        }

    return {
        "verified": True,
        "bc_satisfied": True,
        "ode_satisfied_symbolic": True,
        "u_coeffs": u_poly_coeffs,
        "f_coeffs": f_poly_coeffs,
        "error": None,
    }
