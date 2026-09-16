#!/usr/bin/env python3
"""Scoped executable checks used by the MAPEOGEO foundation backfill.

Most helpers below check finite examples or numerical residuals; they do not
verify universal mathematical declarations.  Only records emitted by the
closed evidence registry at the end of this module may be promoted as scoped
declaration evidence.

The helpers cover examples from all 8 foundational mathematical layers:
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

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Callable


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DE_MORGAN_SUBJECT_ID = "srcdecl:foundation:logic:de_morgan_logic"


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ContractEvidence:
    """Executable evidence for named, hash-bound declaration subjects.

    This is deliberately not a kernel certificate.  Its scope describes exactly
    what the executable checker established and cannot promote unrelated source
    declarations.
    """

    contract_id: str
    contract_version: str
    subject_ids: tuple[str, ...]
    subject_hashes: tuple[tuple[str, str], ...]
    verifier_id: str
    certificate_class: str
    scope: str
    witnesses: tuple[dict[str, Any], ...]
    status: str
    evidence_digest: str

    @classmethod
    def create(
        cls,
        *,
        contract_id: str,
        contract_version: str,
        subject_ids: tuple[str, ...],
        subject_hashes: tuple[tuple[str, str], ...],
        verifier_id: str,
        certificate_class: str,
        scope: str,
        witnesses: tuple[dict[str, Any], ...],
        status: str,
    ) -> "ContractEvidence":
        core = {
            "contract_id": contract_id,
            "contract_version": contract_version,
            "subject_ids": list(subject_ids),
            "subject_hashes": [list(item) for item in subject_hashes],
            "verifier_id": verifier_id,
            "certificate_class": certificate_class,
            "scope": scope,
            "witnesses": list(witnesses),
            "status": status,
        }
        return cls(evidence_digest=_canonical_digest(core), **{
            "contract_id": contract_id,
            "contract_version": contract_version,
            "subject_ids": subject_ids,
            "subject_hashes": subject_hashes,
            "verifier_id": verifier_id,
            "certificate_class": certificate_class,
            "scope": scope,
            "witnesses": witnesses,
            "status": status,
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "subject_ids": list(self.subject_ids),
            "subject_hashes": dict(self.subject_hashes),
            "verifier_id": self.verifier_id,
            "certificate_class": self.certificate_class,
            "scope": self.scope,
            "witnesses": list(self.witnesses),
            "status": self.status,
            "evidence_digest": self.evidence_digest,
        }


# =========================================================================
# LAYER 1: LOGIC & PROOFS CONTRACTS
# =========================================================================

def eval_boolean_implication(p: bool, q: bool) -> bool:
    """Material implication: p => q <=> (not p) or q."""
    if not isinstance(p, bool) or not isinstance(q, bool):
        raise TypeError("material implication operands must be bool")
    return (not p) or q


def eval_boolean_biconditional(p: bool, q: bool) -> bool:
    """Biconditional: p <=> q."""
    if not isinstance(p, bool) or not isinstance(q, bool):
        raise TypeError("biconditional operands must be bool")
    return p == q


def verify_implication_truth_table(
    evaluator: Callable[[bool, bool], bool] = eval_boolean_implication,
) -> bool:
    """Check an implication evaluator against all four boolean assignments."""
    expected = {
        (False, False): True,
        (False, True): True,
        (True, False): False,
        (True, True): True,
    }
    try:
        return all(evaluator(p, q) is result for (p, q), result in expected.items())
    except Exception:
        return False


def verify_de_morgan_logic(p: bool, q: bool) -> bool:
    """Verify De Morgan's laws for propositional logic:
    ¬(P ∧ Q) <=> (¬P ∨ ¬Q) and ¬(P ∨ Q) <=> (¬P ∧ ¬Q).
    """
    if not isinstance(p, bool) or not isinstance(q, bool):
        return False
    law1_lhs = not (p and q)
    law1_rhs = (not p) or (not q)
    law2_lhs = not (p or q)
    law2_rhs = (not p) and (not q)
    return (law1_lhs == law1_rhs) and (law2_lhs == law2_rhs)


def verify_modus_ponens(p: bool, q: bool, p_implies_q: bool) -> bool:
    """Check the finite truth-table validity of a claimed modus-ponens row."""
    if not all(isinstance(value, bool) for value in (p, q, p_implies_q)):
        return False
    if p_implies_q is not eval_boolean_implication(p, q):
        return False
    return not (p and p_implies_q) or q


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
    if not samples or not a <= universe or not b <= universe or set(samples) != universe:
        return False
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
    return _relation_within_domain(relation, domain) and all((x, x) in relation for x in domain)


def is_symmetric(relation: set[tuple[Any, Any]], domain: set) -> bool:
    return _relation_within_domain(relation, domain) and all((y, x) in relation for (x, y) in relation)


def is_transitive(relation: set[tuple[Any, Any]], domain: set) -> bool:
    if not _relation_within_domain(relation, domain):
        return False
    for (x, y) in relation:
        for (y2, z) in relation:
            if y == y2 and (x, z) not in relation:
                return False
    return True


def _relation_within_domain(relation: set[tuple[Any, Any]], domain: set) -> bool:
    return all(x in domain and y in domain for x, y in relation)


def is_equivalence_relation(relation: set[tuple[Any, Any]], domain: set) -> bool:
    return is_reflexive(relation, domain) and is_symmetric(relation, domain) and is_transitive(relation, domain)


def compute_equivalence_classes(relation: set[tuple[Any, Any]], domain: set) -> list[set]:
    if not is_equivalence_relation(relation, domain):
        raise ValueError("relation must be an equivalence relation on the declared domain")
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


def verify_bijective_inverse(
    f: Callable[[float], float],
    f_inv: Callable[[float], float],
    domain_samples: list[float],
    codomain_samples: list[float] | None = None,
    tol: float = 1e-7,
) -> bool:
    """Finite two-sided inverse check; never a proof on an infinite domain."""
    try:
        if (
            not domain_samples
            or not codomain_samples
            or isinstance(tol, bool)
            or not isinstance(tol, (int, float))
            or not math.isfinite(tol)
            or tol < 0
        ):
            return False
        for x in domain_samples:
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
                return False
            y = f(x)
            x_rec = f_inv(y)
            if not all(math.isfinite(v) for v in (y, x_rec)) or abs(x - x_rec) > tol:
                return False
        for y in codomain_samples:
            if isinstance(y, bool) or not isinstance(y, (int, float)) or not math.isfinite(y):
                return False
            x = f_inv(y)
            y_rec = f(x)
            if not all(math.isfinite(v) for v in (x, y_rec)) or abs(y - y_rec) > tol:
                return False
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False
    return True


# =========================================================================
# LAYER 4: NUMBER SYSTEMS CONTRACTS
# =========================================================================

def dedekind_cut_sqrt2(p: int, q: int) -> tuple[bool, bool]:
    """Check if positive rational p/q is in lower cut of sqrt(2): (p/q)^2 < 2."""
    if isinstance(p, bool) or isinstance(q, bool) or not isinstance(p, int) or not isinstance(q, int):
        raise TypeError("p and q must be integers")
    if p < 0 or q <= 0:
        raise ValueError("p must be nonnegative and q must be positive")
    comparison = p * p - 2 * q * q
    return comparison < 0, comparison > 0


def cauchy_sequence_leibniz_pi(terms: int) -> float:
    """Return the partial sum with ``terms`` summands of the Leibniz series."""
    if isinstance(terms, bool) or not isinstance(terms, int) or terms < 0:
        raise ValueError("terms must be a nonnegative integer")
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
    if (
        isinstance(n, bool)
        or isinstance(k, bool)
        or not isinstance(n, int)
        or not isinstance(k, int)
        or n < 0
    ):
        raise ValueError("n and k must be integers with n nonnegative")
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def verify_binomial_theorem(a: float, b: float, n: int, tol: float = 1e-7) -> bool:
    """Check one finite floating-point instance of the binomial identity."""
    try:
        if (
            any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (a, b, tol))
            or not isinstance(n, int)
            or isinstance(n, bool)
            or n < 0
            or tol <= 0
        ):
            return False
        lhs = (a + b) ** n
        rhs = sum(binomial_coefficient(n, k) * (a ** k) * (b ** (n - k)) for k in range(n + 1))
        return math.isfinite(lhs) and math.isfinite(rhs) and math.isclose(
            lhs,
            rhs,
            rel_tol=tol,
            abs_tol=tol,
        )
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


def _validate_polynomial_coefficients(coeffs: list[float]) -> None:
    if not isinstance(coeffs, list) or not coeffs:
        raise ValueError("polynomial coefficient lists must be nonempty")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in coeffs
    ):
        raise ValueError("polynomial coefficients must be finite real numbers")


def polynomial_eval(coeffs: list[float], x: float) -> float:
    """Evaluate P(x) = c_0 + c_1 x + c_2 x^2 + ... using Horner's method."""
    _validate_polynomial_coefficients(coeffs)
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError("polynomial evaluation point must be a finite real number")
    res = 0.0
    for c in reversed(coeffs):
        res = res * x + c
    return res


def polynomial_multiply(p1: list[float], p2: list[float]) -> list[float]:
    """Multiply polynomials represented as coefficient lists [c0, c1, c2, ...]."""
    _validate_polynomial_coefficients(p1)
    _validate_polynomial_coefficients(p2)
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
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in (a, b)
    ):
        return False
    lhs = abs(a + b)
    rhs = abs(a) + abs(b)
    return math.isfinite(lhs) and math.isfinite(rhs) and lhs <= rhs + 1e-12


def verify_sequence_window(
    seq_fn: Callable[[int], float],
    limit: float,
    eps: float,
    n_threshold: int,
    window_size: int = 100,
) -> bool:
    """Check a finite window only; this does not prove eventual convergence."""
    try:
        if (
            isinstance(n_threshold, bool)
            or isinstance(window_size, bool)
            or not isinstance(n_threshold, int)
            or not isinstance(window_size, int)
            or n_threshold < 0
            or window_size <= 0
            or isinstance(limit, bool)
            or isinstance(eps, bool)
            or not isinstance(limit, (int, float))
            or not isinstance(eps, (int, float))
            or not math.isfinite(limit)
            or not math.isfinite(eps)
            or eps <= 0
        ):
            return False
        for n in range(n_threshold, n_threshold + window_size):
            value = seq_fn(n)
            if not math.isfinite(value) or abs(value - limit) >= eps:
                return False
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False
    return True


def verify_sequence_convergence_bound(
    seq_fn: Callable[[int], float],
    limit: float,
    eps: float,
    n_threshold: int,
    max_test: int = 100,
) -> bool:
    """Reject the obsolete API: a finite window cannot verify convergence."""
    raise ValueError(
        "a finite window cannot verify a convergence bound; use verify_sequence_window"
    )


def geometric_series_sum(a: float, r: float, terms: int) -> tuple[float, float]:
    """Compute partial sum vs analytic infinite sum a / (1 - r) for |r| < 1."""
    if (
        isinstance(a, bool)
        or isinstance(r, bool)
        or not isinstance(a, (int, float))
        or not isinstance(r, (int, float))
        or not math.isfinite(a)
        or not math.isfinite(r)
        or isinstance(terms, bool)
        or not isinstance(terms, int)
        or terms < 0
    ):
        raise ValueError("a and r must be finite reals and terms a nonnegative integer")
    if abs(r) >= 1.0:
        raise ValueError("Geometric series converges only for |r| < 1")
    s = sum(a * (r ** k) for k in range(terms))
    analytic = a / (1.0 - r)
    return s, analytic


# =========================================================================
# LAYER 7: EUCLIDEAN GEOMETRY & TRIGONOMETRY CONTRACTS
# =========================================================================

def _validate_vectors(u: list[float], v: list[float] | None = None) -> None:
    if not u or (v is not None and (not v or len(u) != len(v))):
        raise ValueError("vectors must have equal nonzero dimension")
    values = u if v is None else [*u, *v]
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) for x in values):
        raise ValueError("vector coordinates must be finite real numbers")


def euclidean_dot_product(u: list[float], v: list[float]) -> float:
    _validate_vectors(u, v)
    return sum(x * y for x, y in zip(u, v))


def euclidean_norm(v: list[float]) -> float:
    _validate_vectors(v)
    return math.sqrt(euclidean_dot_product(v, v))


def euclidean_distance(u: list[float], v: list[float]) -> float:
    _validate_vectors(u, v)
    diff = [x - y for x, y in zip(u, v)]
    return euclidean_norm(diff)


def verify_cauchy_schwarz(u: list[float], v: list[float]) -> bool:
    """|u · v| <= ||u|| · ||v||."""
    dot = abs(euclidean_dot_product(u, v))
    norms = euclidean_norm(u) * euclidean_norm(v)
    return math.isfinite(dot) and math.isfinite(norms) and dot <= norms + 1e-10


def verify_pythagorean_theorem(u: list[float], v: list[float], tol: float = 1e-7) -> bool:
    """Check the norm identity only after exact floating-point orthogonality."""
    try:
        if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not math.isfinite(tol) or tol <= 0:
            return False
        if euclidean_dot_product(u, v) != 0.0:
            return False
        u_plus_v = [x + y for x, y in zip(u, v)]
        norm_sq_sum = euclidean_norm(u_plus_v) ** 2
        sum_norms_sq = euclidean_norm(u) ** 2 + euclidean_norm(v) ** 2
        return all(math.isfinite(value) for value in (norm_sq_sum, sum_norms_sq)) and abs(norm_sq_sum - sum_norms_sq) < tol
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


def verify_pythagorean_trig_identity(theta: float, tol: float = 1e-9) -> bool:
    """sin^2(theta) + cos^2(theta) == 1."""
    try:
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (theta, tol)) or tol <= 0:
            return False
        val = math.sin(theta) ** 2 + math.cos(theta) ** 2
        return math.isfinite(val) and abs(val - 1.0) < tol
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


def verify_angle_sum_formulas(alpha: float, beta: float, tol: float = 1e-9) -> bool:
    """sin(a + b) = sin a cos b + cos a sin b, cos(a + b) = cos a cos b - sin a sin b."""
    try:
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (alpha, beta, tol)) or tol <= 0:
            return False
        sin_sum_lhs = math.sin(alpha + beta)
        sin_sum_rhs = math.sin(alpha) * math.cos(beta) + math.cos(alpha) * math.sin(beta)
        cos_sum_lhs = math.cos(alpha + beta)
        cos_sum_rhs = math.cos(alpha) * math.cos(beta) - math.sin(alpha) * math.sin(beta)
        values = (sin_sum_lhs, sin_sum_rhs, cos_sum_lhs, cos_sum_rhs)
        return all(math.isfinite(value) for value in values) and (abs(sin_sum_lhs - sin_sum_rhs) < tol) and (abs(cos_sum_lhs - cos_sum_rhs) < tol)
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


# =========================================================================
# LAYER 8: ELEMENTARY CALCULUS CONTRACTS
# =========================================================================

def numerical_difference_quotient(f: Callable[[float], float], x: float, h: float = 1e-6) -> float:
    """Central difference quotient: (f(x + h) - f(x - h)) / (2h)."""
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in (x, h)
    ) or h == 0:
        raise ValueError("x and h must be finite real numbers and h must be nonzero")
    left = f(x - h)
    right = f(x + h)
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in (left, right)
    ):
        raise ValueError("difference quotient samples must be finite real numbers")
    result = (right - left) / (2.0 * h)
    if not math.isfinite(result):
        raise ValueError("difference quotient result must be finite")
    return result


def _within_numeric_tolerance(actual: float, expected: float, tol: float) -> bool:
    return abs(actual - expected) <= tol * max(1.0, abs(actual), abs(expected))


def verify_power_rule_derivative(n: int, x: float, tol: float = 1e-4) -> bool:
    """d/dx (x^n) = n x^{n-1}."""
    try:
        if (
            isinstance(n, bool)
            or not isinstance(n, int)
            or n < 0
            or isinstance(x, bool)
            or not isinstance(x, (int, float))
            or not math.isfinite(x)
            or isinstance(tol, bool)
            or not isinstance(tol, (int, float))
            or not math.isfinite(tol)
            or tol <= 0
        ):
            return False
        if n == 0:
            return True
        f = lambda t: t ** n
        analytic = n * (x ** (n - 1))
        numeric = numerical_difference_quotient(f, x, h=1e-5)
        return all(math.isfinite(value) for value in (analytic, numeric)) and abs(numeric - analytic) < tol
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


def verify_product_rule_derivative(
    f: Callable[[float], float],
    f_prime: Callable[[float], float],
    g: Callable[[float], float],
    g_prime: Callable[[float], float],
    x: float,
    tol: float = 1e-4,
) -> bool:
    """Finite local consistency check including independent derivative samples."""
    try:
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (x, tol)) or tol <= 0:
            return False
        f_claim = f_prime(x)
        g_claim = g_prime(x)
        f_numeric = numerical_difference_quotient(f, x, h=1e-5)
        g_numeric = numerical_difference_quotient(g, x, h=1e-5)
        if not _within_numeric_tolerance(f_numeric, f_claim, tol):
            return False
        if not _within_numeric_tolerance(g_numeric, g_claim, tol):
            return False
        prod = lambda t: f(t) * g(t)
        analytic = f_claim * g(x) + f(x) * g_claim
        numeric = numerical_difference_quotient(prod, x, h=1e-5)
        return all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in (analytic, numeric)) and _within_numeric_tolerance(numeric, analytic, tol)
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


def verify_chain_rule_derivative(
    f: Callable[[float], float],
    f_prime: Callable[[float], float],
    g: Callable[[float], float],
    g_prime: Callable[[float], float],
    x: float,
    tol: float = 1e-4,
) -> bool:
    """Finite local consistency check including independent derivative samples."""
    try:
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (x, tol)) or tol <= 0:
            return False
        gx = g(x)
        f_claim = f_prime(gx)
        g_claim = g_prime(x)
        f_numeric = numerical_difference_quotient(f, gx, h=1e-5)
        g_numeric = numerical_difference_quotient(g, x, h=1e-5)
        if not _within_numeric_tolerance(f_numeric, f_claim, tol):
            return False
        if not _within_numeric_tolerance(g_numeric, g_claim, tol):
            return False
        comp = lambda t: f(g(t))
        analytic = f_claim * g_claim
        numeric = numerical_difference_quotient(comp, x, h=1e-5)
        return all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in (analytic, numeric)) and _within_numeric_tolerance(numeric, analytic, tol)
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


def numerical_riemann_sum(f: Callable[[float], float], a: float, b: float, n_intervals: int = 1000) -> float:
    """Midpoint Riemann sum: sum_{i=1}^n f((x_{i-1} + x_i)/2) dx."""
    if (
        isinstance(n_intervals, bool)
        or not isinstance(n_intervals, int)
        or n_intervals <= 0
    ):
        raise ValueError("n_intervals must be a positive integer")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in (a, b)
    ):
        raise ValueError("integration endpoints must be finite real numbers")
    dx = (b - a) / n_intervals
    total = 0.0
    for i in range(n_intervals):
        mid = a + (i + 0.5) * dx
        value = f(mid)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Riemann samples must be finite real numbers")
        total += value * dx
    if not math.isfinite(total):
        raise ValueError("Riemann sum must be finite")
    return total


def verify_fundamental_theorem_of_calculus(
    f: Callable[[float], float],
    F: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-3,
) -> bool:
    """Finite quadrature check with independent interior antiderivative samples."""
    try:
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (a, b, tol)) or tol <= 0:
            return False
        if a == b:
            return False
        for fraction in (0.25, 0.5, 0.75):
            point = a + fraction * (b - a)
            step = min(1e-5, abs(b - a) / 1000.0)
            derivative = numerical_difference_quotient(F, point, h=step)
            expected = f(point)
            if (
                isinstance(expected, bool)
                or not isinstance(expected, (int, float))
                or not math.isfinite(expected)
                or not _within_numeric_tolerance(derivative, expected, tol)
            ):
                return False
        numeric_integral = numerical_riemann_sum(f, a, b, n_intervals=2000)
        analytic_integral = F(b) - F(a)
        return all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in (numeric_integral, analytic_integral)) and _within_numeric_tolerance(numeric_integral, analytic_integral, tol)
    except (ArithmeticError, OverflowError, TypeError, ValueError):
        return False


def build_foundation_contract_evidence(declarations: list[Any]) -> tuple[ContractEvidence, ...]:
    """Build the sole current declaration-level exhaustive certificate.

    Other helper checks remain useful implementation tests, but they are not
    promoted to declaration-level mathematical evidence.
    """
    declaration_by_id = {item.node_id: item for item in declarations}
    subject = declaration_by_id.get(DE_MORGAN_SUBJECT_ID)
    if subject is None or not SHA256_RE.fullmatch(subject.statement_sha256):
        raise ValueError("De Morgan subject declaration/hash is unavailable")

    witnesses = tuple(
        {
            "p": p,
            "q": q,
            "not_and": not (p and q),
            "or_not": (not p) or (not q),
            "not_or": not (p or q),
            "and_not": (not p) and (not q),
            "passed": verify_de_morgan_logic(p, q),
        }
        for p in (False, True)
        for q in (False, True)
    )
    status = "PASS" if all(item["passed"] for item in witnesses) else "FAIL"
    return (
        ContractEvidence.create(
            contract_id="foundation.logic.de_morgan.truth_table",
            contract_version="1.0.0",
            subject_ids=(subject.node_id,),
            subject_hashes=((subject.node_id, subject.statement_sha256),),
            verifier_id="python:boolean-exhaustive-2-variable",
            certificate_class="EXECUTABLE_EXHAUSTIVE_FINITE",
            scope="ALL_FOUR_BOOLEAN_ASSIGNMENTS",
            witnesses=witnesses,
            status=status,
        ),
    )


def validate_contract_evidence(
    evidence: tuple[ContractEvidence, ...] | list[ContractEvidence],
    declarations: list[Any],
) -> dict[str, Any]:
    if not evidence:
        raise ValueError("contract evidence registry is empty")
    declaration_ids = [item.node_id for item in declarations]
    if len(declaration_ids) != len(set(declaration_ids)):
        raise ValueError("duplicate declaration identity in contract registry")
    declarations_by_id = {item.node_id: item for item in declarations}
    expected_by_id = {
        item.contract_id: item
        for item in build_foundation_contract_evidence(declarations)
    }
    verified_subjects: set[str] = set()
    seen_contracts: set[str] = set()

    for item in evidence:
        if item.contract_id in seen_contracts:
            raise ValueError(f"duplicate contract ID: {item.contract_id}")
        seen_contracts.add(item.contract_id)
        expected = expected_by_id.get(item.contract_id)
        if expected is None:
            raise ValueError(f"unknown contract definition: {item.contract_id}")
        definition_fields = (
            "contract_version",
            "subject_ids",
            "subject_hashes",
            "verifier_id",
            "certificate_class",
            "scope",
            "witnesses",
            "status",
        )
        for field_name in definition_fields:
            if getattr(item, field_name) != getattr(expected, field_name):
                raise ValueError(
                    f"contract definition mismatch ({field_name}): {item.contract_id}"
                )
        if item.certificate_class == "KERNEL_VERIFIED":
            raise ValueError("executable evidence cannot claim KERNEL_VERIFIED")
        if item.certificate_class != "EXECUTABLE_EXHAUSTIVE_FINITE":
            raise ValueError(f"unsupported certificate class: {item.certificate_class}")
        if item.status != "PASS" or not item.witnesses or not item.subject_ids:
            raise ValueError(f"contract {item.contract_id} lacks passing nonempty evidence")
        hashes = dict(item.subject_hashes)
        if set(hashes) != set(item.subject_ids):
            raise ValueError(f"contract {item.contract_id} subject/hash binding mismatch")
        for subject_id in item.subject_ids:
            declaration = declarations_by_id.get(subject_id)
            bound_hash = hashes.get(subject_id, "")
            if declaration is None:
                raise ValueError(f"unbound declaration subject: {subject_id}")
            if not SHA256_RE.fullmatch(bound_hash) or bound_hash != declaration.statement_sha256:
                raise ValueError(f"subject hash mismatch: {subject_id}")
            verified_subjects.add(subject_id)
        rebuilt = ContractEvidence.create(
            contract_id=item.contract_id,
            contract_version=item.contract_version,
            subject_ids=item.subject_ids,
            subject_hashes=item.subject_hashes,
            verifier_id=item.verifier_id,
            certificate_class=item.certificate_class,
            scope=item.scope,
            witnesses=item.witnesses,
            status=item.status,
        )
        if rebuilt.evidence_digest != item.evidence_digest:
            raise ValueError(f"evidence digest mismatch: {item.contract_id}")

    return {
        "registered_contracts": len(evidence),
        "passed_contracts": len(evidence),
        "verified_declarations": len(verified_subjects),
        "unverified_declarations": len(declarations) - len(verified_subjects),
        "kernel_verified_declarations": 0,
        "verified_subject_ids": sorted(verified_subjects),
        "evidence": [item.to_dict() for item in evidence],
    }


def run_all_foundation_contracts(declarations: list[Any]) -> tuple[ContractEvidence, ...]:
    """Compatibility entry point returning declaration-bound evidence records."""
    return build_foundation_contract_evidence(declarations)


if __name__ == "__main__":
    from scripts.import_foundation_backfill import generate_foundation_declarations

    declarations = generate_foundation_declarations()
    records = build_foundation_contract_evidence(declarations)
    summary = validate_contract_evidence(records, declarations)
    print(json.dumps(summary, indent=2, sort_keys=True))
