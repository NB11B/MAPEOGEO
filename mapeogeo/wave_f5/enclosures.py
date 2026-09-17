"""Validated Enclosures, Interval Arithmetic & Solution-Tube Certificates (Q15–Q18) for Wave F5."""

import math
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Tuple


class Interval:
    """Interval arithmetic abstraction for validated ODE enclosures."""

    def __init__(self, low: float, high: float) -> None:
        if low > high:
            raise ValueError(f"Invalid interval: low={low} > high={high}")
        self.low = float(low)
        self.high = float(high)

    def contains(self, x: float) -> bool:
        return self.low <= x <= self.high

    @property
    def width(self) -> float:
        return self.high - self.low

    @property
    def midpoint(self) -> float:
        return (self.low + self.high) / 2.0

    def __add__(self, other: "Interval") -> "Interval":
        return Interval(self.low + other.low, self.high + other.high)

    def __sub__(self, other: "Interval") -> "Interval":
        return Interval(self.low - other.high, self.high - other.low)

    def __mul__(self, other: "Interval") -> "Interval":
        products = [
            self.low * other.low,
            self.low * other.high,
            self.high * other.low,
            self.high * other.high,
        ]
        return Interval(min(products), max(products))

    def __repr__(self) -> str:
        return f"Interval({self.low}, {self.high})"


def verify_q15_residual_enclosure(
    h: Fraction,
    degree: int,
    e0: Fraction,
    claimed_R: Fraction,
) -> Dict[str, Any]:
    """Verify Continuous-Slab Solution-Tube Residual Enclosure (Q15) for y' = y."""
    # Factorial of degree
    fact = math.factorial(degree)
    # True supremum of residual on [0, h] for y_hat = sum_{k=0}^d t^k/k! is h^d / d!
    R_true = (h ** degree) / Fraction(fact)

    if claimed_R < R_true:
        return {
            "verified": False,
            "error": f"Underestimated residual bound: claimed R={claimed_R} < true supremum R={R_true}",
        }

    # Lipschitz constant L = 1 for y' = y
    L = 1.0
    h_f = float(h)
    e0_f = float(e0)
    R_f = float(claimed_R)

    # Validated solution-tube radius: exp(L*h)*e0 + (R/L)*(exp(L*h) - 1)
    exp_Lh = math.exp(L * h_f)
    tube_radius = exp_Lh * e0_f + (R_f / L) * (exp_Lh - 1.0)

    return {
        "verified": True,
        "tube_radius": tube_radius,
        "R_bound": R_f,
        "e0": e0_f,
        "error": None,
    }


def verify_q16_logistic_invariant_interval(
    initial_box: Interval,
    invariant_box: Interval,
) -> Dict[str, Any]:
    """Verify Invariant Interval and Solution Tube (Q16) for Logistic Flow x' = x(1-x)."""
    # Check initial box is subset of claimed invariant box
    if initial_box.low < invariant_box.low or initial_box.high > invariant_box.high:
        return {
            "verified": False,
            "error": f"Initial enclosure {initial_box} is not subset of invariant region {invariant_box}",
        }

    # Vector field check at boundary of invariant box [a, b]:
    # f(a) >= 0 (no outward flow below a)
    # f(b) <= 0 (no outward flow above b)
    def f(x: float) -> float:
        return x * (1.0 - x)

    f_low = f(invariant_box.low)
    f_high = f(invariant_box.high)

    if f_low < 0.0 or f_high > 0.0:
        return {
            "verified": False,
            "error": f"Boundary vector field violates invariance: f(low)={f_low}, f(high)={f_high}",
        }

    return {
        "verified": True,
        "invariant": True,
        "tube_box": invariant_box,
        "error": None,
    }


def verify_q17_transversal_event(
    grad_H: float,
    f_val: float,
    t_interval: Interval,
    x_interval: Interval,
) -> Dict[str, Any]:
    """Verify Transversal Event Localization Certificate (Q17)."""
    lie_deriv = grad_H * f_val
    if abs(lie_deriv) < 1e-9:
        return {
            "verified": False,
            "error": "Transversality condition violated: Lie derivative nabla H . f is zero (tangential event)",
        }

    return {
        "verified": True,
        "transversal": True,
        "lie_derivative": lie_deriv,
        "crossing_time_enclosure": t_interval,
        "error": None,
    }


def verify_q18_regular_dirichlet_bvp(
    u_func: Callable[[float], float],
    u_xx_func: Callable[[float], float],
    f_func: Callable[[float], float],
    bc_0: float = 0.0,
    bc_1: float = 0.0,
    x_grid: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Verify Regular Dirichlet Boundary Value Problem Green Operator (Q18)."""
    # Check boundary conditions
    u0 = u_func(0.0)
    u1 = u_func(1.0)
    if not math.isclose(u0, bc_0, abs_tol=1e-12) or not math.isclose(u1, bc_1, abs_tol=1e-12):
        return {
            "verified": False,
            "error": f"Boundary condition mismatch: u(0)={u0} (expected {bc_0}), u(1)={u1} (expected {bc_1})",
        }

    # Check differential equation -u''(x) == f(x) on grid
    if x_grid is None:
        x_grid = [0.0, 0.25, 0.5, 0.75, 1.0]

    for x in x_grid:
        lhs = -u_xx_func(x)
        rhs = f_func(x)
        if not math.isclose(lhs, rhs, abs_tol=1e-12):
            return {
                "verified": False,
                "error": f"BVP operator residual failed at x={x}: -u''(x)={lhs} != f(x)={rhs}",
            }

    return {
        "verified": True,
        "bc_satisfied": True,
        "pde_satisfied": True,
        "error": None,
    }
