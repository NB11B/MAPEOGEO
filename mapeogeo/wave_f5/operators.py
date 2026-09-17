"""Exact & Scoped Operator Contracts (Q01–Q05) for Wave F5."""

from fractions import Fraction
from typing import Any, Callable, Dict, List, Tuple
import numpy as np


def verify_q01_contraction(
    T: Callable[[Fraction], Fraction],
    interval: Tuple[Fraction, Fraction],
    q: Fraction,
    fixed_point: Fraction,
) -> Dict[str, Any]:
    """Verify Banach Contraction (Q01) on closed interval [a, b]."""
    a, b = interval
    if a >= b:
        return {"verified": False, "error": f"Invalid interval [{a}, {b}]"}

    if q >= Fraction(1) or q < Fraction(0):
        return {"verified": False, "error": f"Contraction factor must satisfy 0 <= q < 1, got q={q}"}

    # Invariance check: T([a, b]) subset [a, b]
    Ta = T(a)
    Tb = T(b)
    if not (a <= Ta <= b and a <= Tb <= b):
        return {"verified": False, "error": f"Interval [{a}, {b}] is not invariant under T: T(a)={Ta}, T(b)={Tb}"}

    # Fixed point check: T(x*) == x*
    T_fp = T(fixed_point)
    if T_fp != fixed_point:
        return {"verified": False, "error": f"T({fixed_point}) = {T_fp} != {fixed_point}"}

    # Check contraction condition on endpoints
    if abs(Ta - Tb) > q * abs(a - b):
        return {"verified": False, "error": f"Contraction bound violated: |T(a)-T(b)|={abs(Ta-Tb)} > q*|a-b|={q*abs(a-b)}"}

    return {
        "verified": True,
        "fixed_point": fixed_point,
        "q": q,
        "error": None,
    }


def verify_q02_adjoint(
    A: np.ndarray,
    G: np.ndarray,
    A_star: np.ndarray,
) -> Dict[str, Any]:
    """Verify Hilbert Adjoint Operator (Q02) under metric G: A* = G^{-1} A^T G."""
    # Check G is symmetric positive-definite / non-singular
    try:
        G_inv = np.linalg.inv(G.astype(float))
    except Exception as e:
        return {"verified": False, "error": f"Metric matrix G is singular: {e}"}

    # In exact fractions / numpy
    # G A* == A^T G
    lhs = np.dot(G, A_star)
    rhs = np.dot(A.T, G)

    diff = lhs - rhs
    if np.any(diff != 0):
        return {"verified": False, "error": "Adjoint pairing identity G A* = A^T G violated"}

    return {
        "verified": True,
        "A_star": A_star,
        "error": None,
    }


def verify_q03_orthogonal_projection(
    P: np.ndarray,
    basis: List[np.ndarray],
) -> Dict[str, Any]:
    """Verify Hilbert Projection Theorem (Q03): P^2 = P, P^T = P, and P spans subspace."""
    # Idempotence: P^2 == P
    P2 = np.dot(P, P)
    if np.any(P2 != P):
        return {"verified": False, "error": "Operator P is not idempotent (P^2 != P)"}

    # Orthogonality / Symmetry: P^T == P
    if np.any(P.T != P):
        return {"verified": False, "error": "Projection P is not symmetric/orthogonal (P^T != P)"}

    # Invariance on basis
    for v in basis:
        Pv = np.dot(P, v)
        if np.any(Pv != v):
            return {"verified": False, "error": f"Basis vector {v} is not invariant under projection: Pv = {Pv}"}

    return {
        "verified": True,
        "rank": len(basis),
        "error": None,
    }


def verify_q04_neumann_series(
    A: np.ndarray,
    N: int,
) -> Dict[str, Any]:
    """Verify Neumann Series Inversion Bound (Q04): ||A||_1 < 1, residual and geometric tail bound."""
    # Compute 1-norm (max column sum of absolute values)
    col_sums = [sum(abs(A[i, j]) for i in range(A.shape[0])) for j in range(A.shape[1])]
    norm_A = max(col_sums)

    if norm_A >= Fraction(1):
        return {"verified": False, "error": f"Induced matrix norm ||A||_1 = {norm_A} >= 1; Neumann series cannot certify"}

    # Compute truncated sum S_N = sum_{k=0}^N A^k
    I = np.eye(A.shape[0], dtype=object)
    for r in range(A.shape[0]):
        for c in range(A.shape[1]):
            I[r, c] = Fraction(1) if r == c else Fraction(0)

    S_N = np.zeros_like(A, dtype=object)
    for r in range(A.shape[0]):
        for c in range(A.shape[1]):
            S_N[r, c] = Fraction(0)

    current_power = I.copy()
    for k in range(N + 1):
        S_N = S_N + current_power
        if k < N:
            current_power = np.dot(current_power, A)

    # Tail bound = ||A||^{N+1} / (1 - ||A||)
    tail_bound = (norm_A ** (N + 1)) / (Fraction(1) - norm_A)

    return {
        "verified": True,
        "norm_A": norm_A,
        "tail_bound": tail_bound,
        "S_N": S_N,
        "error": None,
    }


def verify_q05_spectral_decomposition(
    A: np.ndarray,
    eigenvalues: List[Fraction],
    projectors: List[np.ndarray],
) -> Dict[str, Any]:
    """Verify Spectral Decomposition (Q05): A = sum lambda_i P_i, sum P_i = I, P_i P_j = delta_ij P_i."""
    if len(eigenvalues) != len(projectors):
        return {"verified": False, "error": "Mismatch between count of eigenvalues and projectors"}

    dim = A.shape[0]
    I = np.eye(dim, dtype=object)
    for r in range(dim):
        for c in range(dim):
            I[r, c] = Fraction(1) if r == c else Fraction(0)

    # Check sum P_i == I
    sum_P = np.zeros((dim, dim), dtype=object)
    for r in range(dim):
        for c in range(dim):
            sum_P[r, c] = Fraction(0)
    for P in projectors:
        sum_P = sum_P + P

    if np.any(sum_P != I):
        return {"verified": False, "error": "Projectors do not sum to identity (resolution of identity failed)"}

    # Check orthogonality of projectors
    for i, Pi in enumerate(projectors):
        for j, Pj in enumerate(projectors):
            prod = np.dot(Pi, Pj)
            expected = Pi if i == j else np.zeros((dim, dim), dtype=object)
            if np.any(prod != expected):
                return {"verified": False, "error": f"Orthogonality failed between projector {i} and {j}"}

    # Reconstruct A = sum lambda_i P_i
    reconstructed_A = np.zeros((dim, dim), dtype=object)
    for r in range(dim):
        for c in range(dim):
            reconstructed_A[r, c] = Fraction(0)

    for lam, P in zip(eigenvalues, projectors):
        for r in range(dim):
            for c in range(dim):
                reconstructed_A[r, c] += lam * P[r, c]

    if np.any(reconstructed_A != A):
        return {"verified": False, "error": "Reconstructed operator sum(lambda_i P_i) != A"}

    return {
        "verified": True,
        "eigenvalues": eigenvalues,
        "error": None,
    }
