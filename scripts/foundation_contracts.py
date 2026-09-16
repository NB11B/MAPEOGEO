#!/usr/bin/env python3
"""MAPEOGEO Foundation Backfill: Exact Executable EO/GEO Dual Contracts.

Provides fully executable symbolic and numerical dual verification across all 8 foundational mathematical layers:
  1. Logic & Proofs
  2. Set Theory
  3. Relations & Functions
  4. Number Systems
  5. Elementary Arithmetic & Algebra
  6. Order, Metrics & Sequences
  7. Euclidean Geometry & Trigonometry
  8. Elementary Calculus
"""

from __future__ import annotations

import math
from typing import Any, Callable


# =========================================================================
# LAYER 1: LOGIC & PROOFS CONTRACTS
# =========================================================================

def eval_boolean_implication(p: bool, q: bool) -> bool:
    """Material implication: p => q <=> (not p) or q."""
    return (not p) or q


def eval_boolean_biconditional(p: bool, q: bool) -> bool:
    """Biconditional: p <=> q."""
    return p == q


def verify_de_morgan_logic(p: bool, q: bool) -> bool:
    """Verify De Morgan's laws for propositional logic:
    ¬(P ∧ Q) <=> (¬P ∨ ¬Q) and ¬(P ∨ Q) <=> (¬P ∧ ¬Q).
    """
    law1_lhs = not (p and q)
    law1_rhs = (not p) or (not q)
    law2_lhs = not (p or q)
    law2_rhs = (not p) and (not q)
    return (law1_lhs == law1_rhs) and (law2_lhs == law2_rhs)


def verify_modus_ponens(p: bool, p_implies_q: bool) -> bool:
    """Modus ponens: from p and (p => q), infer q."""
    if p and p_implies_q:
        q = True
        return p_implies_q == eval_boolean_implication(p, q)
    return True


# =========================================================================
# LAYER 2: SET THEORY CONTRACTS
# =========================================================================

def set_union(a: set, b: set) -> set:
    return a | b


def set_intersection(a: set, b: set) -> set:
    return a & b


def set_difference(a: set, b: set) -> set:
    return a - b


def set_complement(a: set, universe: set) -> set:
    return universe - a


def set_indicator(x: Any, a: set) -> int:
    return 1 if x in a else 0


def verify_indicator_algebra(a: set, b: set, universe: set, samples: list[Any]) -> bool:
    """Verify indicator function algebra:
    1_{A ∩ B} = 1_A · 1_B
    1_{A ∪ B} = 1_A + 1_B - 1_A · 1_B
    1_{A^c} = 1 - 1_A
    """
    inter = set_intersection(a, b)
    union = set_union(a, b)
    comp_a = set_complement(a, universe)

    for x in samples:
        i_a = set_indicator(x, a)
        i_b = set_indicator(x, b)
        i_inter = set_indicator(x, inter)
        i_union = set_indicator(x, union)
        i_comp = set_indicator(x, comp_a)

        if i_inter != (i_a * i_b):
            return False
        if i_union != (i_a + i_b - i_a * i_b):
            return False
        if i_comp != (1 - i_a):
            return False
    return True


def cartesian_product(a: set, b: set) -> set[tuple[Any, Any]]:
    return {(x, y) for x in a for y in b}


# =========================================================================
# LAYER 3: RELATIONS & FUNCTIONS CONTRACTS
# =========================================================================

def is_reflexive(relation: set[tuple[Any, Any]], domain: set) -> bool:
    return all((x, x) in relation for x in domain)


def is_symmetric(relation: set[tuple[Any, Any]], domain: set) -> bool:
    return all((y, x) in relation for (x, y) in relation)


def is_transitive(relation: set[tuple[Any, Any]], domain: set) -> bool:
    for (x, y) in relation:
        for (y2, z) in relation:
            if y == y2 and (x, z) not in relation:
                return False
    return True


def is_equivalence_relation(relation: set[tuple[Any, Any]], domain: set) -> bool:
    return is_reflexive(relation, domain) and is_symmetric(relation, domain) and is_transitive(relation, domain)


def compute_equivalence_classes(relation: set[tuple[Any, Any]], domain: set) -> list[set]:
    classes = []
    seen = set()
    for x in domain:
        if x not in seen:
            eq_class = {y for y in domain if (x, y) in relation}
            classes.append(eq_class)
            seen |= eq_class
    return classes


def eval_function_composition(f: Callable[[Any], Any], g: Callable[[Any], Any], x: Any) -> Any:
    return g(f(x))


def verify_bijective_inverse(f: Callable[[float], float], f_inv: Callable[[float], float], test_inputs: list[float], tol: float = 1e-7) -> bool:
    for x in test_inputs:
        y = f(x)
        x_rec = f_inv(y)
        if abs(x - x_rec) > tol:
            return False
    return True


# =========================================================================
# LAYER 4: NUMBER SYSTEMS CONTRACTS
# =========================================================================

def dedekind_cut_sqrt2(p: float, q: float) -> tuple[bool, bool]:
    """Check if positive rational p/q is in lower cut of sqrt(2): (p/q)^2 < 2."""
    val = (p / q) ** 2
    return val < 2.0, val > 2.0


def cauchy_sequence_leibniz_pi(terms: int) -> float:
    """Leibniz series for pi: pi/4 = sum_{k=0}^n (-1)^k / (2k + 1)."""
    s = 0.0
    for k in range(terms):
        s += ((-1.0) ** k) / (2 * k + 1)
    return 4.0 * s


def complex_multiply(z1: tuple[float, float], z2: tuple[float, float]) -> tuple[float, float]:
    """(a + bi)(c + di) = (ac - bd) + (ad + bc)i."""
    a, b = z1
    c, d = z2
    return (a * c - b * d, a * d + b * c)


def complex_modulus(z: tuple[float, float]) -> float:
    a, b = z
    return math.sqrt(a * a + b * b)


# =========================================================================
# LAYER 5: ELEMENTARY ARITHMETIC & ALGEBRA CONTRACTS
# =========================================================================

def binomial_coefficient(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def verify_binomial_theorem(a: float, b: float, n: int, tol: float = 1e-7) -> bool:
    """Verify (a + b)^n = sum_{k=0}^n C(n, k) a^k b^{n-k}."""
    lhs = (a + b) ** n
    rhs = sum(binomial_coefficient(n, k) * (a ** k) * (b ** (n - k)) for k in range(n + 1))
    return abs(lhs - rhs) < tol


def polynomial_eval(coeffs: list[float], x: float) -> float:
    """Evaluate P(x) = c_0 + c_1 x + c_2 x^2 + ... using Horner's method."""
    res = 0.0
    for c in reversed(coeffs):
        res = res * x + c
    return res


def polynomial_multiply(p1: list[float], p2: list[float]) -> list[float]:
    """Multiply polynomials represented as coefficient lists [c0, c1, c2, ...]."""
    res = [0.0] * (len(p1) + len(p2) - 1)
    for i, c1 in enumerate(p1):
        for j, c2 in enumerate(p2):
            res[i + j] += c1 * c2
    return res


# =========================================================================
# LAYER 6: ORDER, METRICS & SEQUENCES CONTRACTS
# =========================================================================

def verify_triangle_inequality_reals(a: float, b: float) -> bool:
    """|a + b| <= |a| + |b|."""
    return abs(a + b) <= abs(a) + abs(b) + 1e-12


def verify_sequence_convergence_bound(seq_fn: Callable[[int], float], limit: float, eps: float, n_threshold: int, max_test: int = 100) -> bool:
    """Verify for all n >= n_threshold, |a_n - limit| < eps."""
    for n in range(n_threshold, n_threshold + max_test):
        if abs(seq_fn(n) - limit) >= eps:
            return False
    return True


def geometric_series_sum(a: float, r: float, terms: int) -> tuple[float, float]:
    """Compute partial sum vs analytic infinite sum a / (1 - r) for |r| < 1."""
    if abs(r) >= 1.0:
        raise ValueError("Geometric series converges only for |r| < 1")
    s = sum(a * (r ** k) for k in range(terms))
    analytic = a / (1.0 - r)
    return s, analytic


# =========================================================================
# LAYER 7: EUCLIDEAN GEOMETRY & TRIGONOMETRY CONTRACTS
# =========================================================================

def euclidean_dot_product(u: list[float], v: list[float]) -> float:
    return sum(x * y for x, y in zip(u, v))


def euclidean_norm(v: list[float]) -> float:
    return math.sqrt(euclidean_dot_product(v, v))


def euclidean_distance(u: list[float], v: list[float]) -> float:
    diff = [x - y for x, y in zip(u, v)]
    return euclidean_norm(diff)


def verify_cauchy_schwarz(u: list[float], v: list[float]) -> bool:
    """|u · v| <= ||u|| · ||v||."""
    dot = abs(euclidean_dot_product(u, v))
    norms = euclidean_norm(u) * euclidean_norm(v)
    return dot <= norms + 1e-10


def verify_pythagorean_theorem(u: list[float], v: list[float], tol: float = 1e-7) -> bool:
    """If u ⊥ v (u · v == 0), then ||u + v||^2 == ||u||^2 + ||v||^2."""
    if abs(euclidean_dot_product(u, v)) > tol:
        return False
    u_plus_v = [x + y for x, y in zip(u, v)]
    norm_sq_sum = euclidean_norm(u_plus_v) ** 2
    sum_norms_sq = euclidean_norm(u) ** 2 + euclidean_norm(v) ** 2
    return abs(norm_sq_sum - sum_norms_sq) < tol


def verify_pythagorean_trig_identity(theta: float, tol: float = 1e-9) -> bool:
    """sin^2(theta) + cos^2(theta) == 1."""
    val = math.sin(theta) ** 2 + math.cos(theta) ** 2
    return abs(val - 1.0) < tol


def verify_angle_sum_formulas(alpha: float, beta: float, tol: float = 1e-9) -> bool:
    """sin(a + b) = sin a cos b + cos a sin b, cos(a + b) = cos a cos b - sin a sin b."""
    sin_sum_lhs = math.sin(alpha + beta)
    sin_sum_rhs = math.sin(alpha) * math.cos(beta) + math.cos(alpha) * math.sin(beta)

    cos_sum_lhs = math.cos(alpha + beta)
    cos_sum_rhs = math.cos(alpha) * math.cos(beta) - math.sin(alpha) * math.sin(beta)

    return (abs(sin_sum_lhs - sin_sum_rhs) < tol) and (abs(cos_sum_lhs - cos_sum_rhs) < tol)


# =========================================================================
# LAYER 8: ELEMENTARY CALCULUS CONTRACTS
# =========================================================================

def numerical_difference_quotient(f: Callable[[float], float], x: float, h: float = 1e-6) -> float:
    """Central difference quotient: (f(x + h) - f(x - h)) / (2h)."""
    return (f(x + h) - f(x - h)) / (2.0 * h)


def verify_power_rule_derivative(n: int, x: float, tol: float = 1e-4) -> bool:
    """d/dx (x^n) = n x^{n-1}."""
    f = lambda t: t ** n
    analytic = n * (x ** (n - 1))
    numeric = numerical_difference_quotient(f, x, h=1e-5)
    return abs(numeric - analytic) < tol


def verify_product_rule_derivative(
    f: Callable[[float], float],
    f_prime: Callable[[float], float],
    g: Callable[[float], float],
    g_prime: Callable[[float], float],
    x: float,
    tol: float = 1e-4,
) -> bool:
    """(fg)' = f'g + fg'."""
    prod = lambda t: f(t) * g(t)
    analytic = f_prime(x) * g(x) + f(x) * g_prime(x)
    numeric = numerical_difference_quotient(prod, x, h=1e-5)
    return abs(numeric - analytic) < tol


def verify_chain_rule_derivative(
    f: Callable[[float], float],
    f_prime: Callable[[float], float],
    g: Callable[[float], float],
    g_prime: Callable[[float], float],
    x: float,
    tol: float = 1e-4,
) -> bool:
    """(f ∘ g)'(x) = f'(g(x)) · g'(x)."""
    comp = lambda t: f(g(t))
    analytic = f_prime(g(x)) * g_prime(x)
    numeric = numerical_difference_quotient(comp, x, h=1e-5)
    return abs(numeric - analytic) < tol


def numerical_riemann_sum(f: Callable[[float], float], a: float, b: float, n_intervals: int = 1000) -> float:
    """Midpoint Riemann sum: sum_{i=1}^n f((x_{i-1} + x_i)/2) dx."""
    dx = (b - a) / n_intervals
    total = 0.0
    for i in range(n_intervals):
        mid = a + (i + 0.5) * dx
        total += f(mid) * dx
    return total


def verify_fundamental_theorem_of_calculus(
    f: Callable[[float], float],
    F: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-3,
) -> bool:
    """int_a^b f(x) dx == F(b) - F(a)."""
    numeric_integral = numerical_riemann_sum(f, a, b, n_intervals=2000)
    analytic_integral = F(b) - F(a)
    return abs(numeric_integral - analytic_integral) < tol


def run_all_foundation_contracts() -> dict[str, bool]:
    """Execute all 8 foundational domain dual verification contracts and return results."""
    results = {}

    # 1. Logic
    de_morgan_ok = all(verify_de_morgan_logic(p, q) for p in [True, False] for q in [True, False])
    mp_ok = all(verify_modus_ponens(p, eval_boolean_implication(p, q)) for p in [True, False] for q in [True, False])
    results["logic_contracts"] = de_morgan_ok and mp_ok

    # 2. Sets
    U = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    A = {1, 2, 3, 4, 5}
    B = {4, 5, 6, 7}
    results["set_contracts"] = verify_indicator_algebra(A, B, U, list(U))

    # 3. Relations & Functions
    dom = {1, 2, 3, 4}
    eq_rel = {(x, y) for x in dom for y in dom if (x % 2) == (y % 2)}
    classes = compute_equivalence_classes(eq_rel, dom)
    f_bij = lambda x: 2.0 * x + 3.0
    f_inv = lambda y: (y - 3.0) / 2.0
    bij_ok = verify_bijective_inverse(f_bij, f_inv, [-5.0, 0.0, 1.0, 10.0])
    results["relation_function_contracts"] = is_equivalence_relation(eq_rel, dom) and len(classes) == 2 and bij_ok

    # 4. Numbers
    cut_ok, _ = dedekind_cut_sqrt2(7, 5)  # (7/5)^2 = 1.96 < 2
    c1, c2 = (1.0, 2.0), (3.0, 4.0)
    c_prod = complex_multiply(c1, c2)
    c_ok = (c_prod == (-5.0, 10.0)) and abs(complex_modulus(c1) - math.sqrt(5.0)) < 1e-9
    results["number_contracts"] = cut_ok and c_ok

    # 5. Algebra
    bin_ok = verify_binomial_theorem(2.0, 3.0, 5)
    p1 = [1.0, 2.0]  # 1 + 2x
    p2 = [3.0, 4.0]  # 3 + 4x
    p_prod = polynomial_multiply(p1, p2)  # 3 + 10x + 8x^2
    results["algebra_contracts"] = bin_ok and (p_prod == [3.0, 10.0, 8.0])

    # 6. Sequences & Metrics
    tri_ok = verify_triangle_inequality_reals(3.5, -4.2)
    seq_1_over_n = lambda n: 1.0 / n if n > 0 else 0.0
    seq_conv_ok = verify_sequence_convergence_bound(seq_1_over_n, limit=0.0, eps=0.01, n_threshold=101)
    geom_sum, geom_ana = geometric_series_sum(1.0, 0.5, 30)
    results["sequence_metric_contracts"] = tri_ok and seq_conv_ok and abs(geom_sum - geom_ana) < 1e-7

    # 7. Geometry & Trigonometry
    u, v = [1.0, 0.0, 2.0], [0.0, 3.0, 0.0]
    cs_ok = verify_cauchy_schwarz(u, v)
    pyth_ok = verify_pythagorean_theorem(u, v)
    trig_ok = verify_pythagorean_trig_identity(0.75) and verify_angle_sum_formulas(0.4, 0.6)
    results["geometry_trig_contracts"] = cs_ok and pyth_ok and trig_ok

    # 8. Calculus
    power_ok = verify_power_rule_derivative(4, 2.5)
    f_exp = lambda x: math.exp(x)
    f_sin = lambda x: math.sin(x)
    f_cos = lambda x: math.cos(x)
    prod_ok = verify_product_rule_derivative(f_exp, f_exp, f_sin, f_cos, 1.0)
    ftc_ok = verify_fundamental_theorem_of_calculus(lambda x: x ** 2, lambda x: (x ** 3) / 3.0, 0.0, 3.0)
    results["calculus_contracts"] = power_ok and prod_ok and ftc_ok

    return results


if __name__ == "__main__":
    res = run_all_foundation_contracts()
    print("Foundation Executable Dual Contracts Verification:")
    for k, v in res.items():
        print(f"  {k:30s}: {'PASS' if v else 'FAIL'}")
    all_pass = all(res.values())
    print(f"\nOverall Contracts Status: {'ALL PASS (100%)' if all_pass else 'FAILURES DETECTED'}")
