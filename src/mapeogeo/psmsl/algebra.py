"""Pure numeric linear algebra and operator information semantics for PSMSL.

Contains NO domain-specific or physical concepts.
Operates strictly on discrete matrices and vectors over R.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeAlias

Matrix: TypeAlias = tuple[tuple[float, ...], ...]
Vector: TypeAlias = tuple[float, ...]


def eye(n: int) -> Matrix:
    """Return an n x n identity matrix."""
    return tuple(tuple(1.0 if i == j else 0.0 for j in range(n)) for i in range(n))


def matmul(A: Matrix, B: Matrix) -> Matrix:
    """Matrix multiplication A x B."""
    if not A or not B:
        raise ValueError("Matrices must be non-empty")
    if len(A[0]) != len(B):
        raise ValueError(
            f"Shape mismatch in matmul: ({len(A)}, {len(A[0])}) vs ({len(B)}, {len(B[0])})"
        )
    return tuple(
        tuple(sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0])))
        for i in range(len(A))
    )


def matsub(A: Matrix, B: Matrix) -> Matrix:
    """Matrix subtraction A - B."""
    if len(A) != len(B) or len(A[0]) != len(B[0]):
        raise ValueError("Shape mismatch in matsub")
    return tuple(tuple(A[i][j] - B[i][j] for j in range(len(A[0]))) for i in range(len(A)))


def frobenius_norm(A: Matrix) -> float:
    """Frobenius norm of matrix A."""
    return math.sqrt(sum(x * x for row in A for x in row))


def rank(A: Matrix, tol: float = 1e-10) -> int:
    """Compute numerical matrix rank using Gaussian elimination."""
    if not A or not A[0]:
        return 0
    m_rows = [list(map(float, r)) for r in A]
    m = len(m_rows)
    n = len(m_rows[0])
    r = 0
    for c in range(n):
        p = next((i for i in range(r, m) if abs(m_rows[i][c]) > tol), None)
        if p is None:
            continue
        m_rows[r], m_rows[p] = m_rows[p], m_rows[r]
        q = m_rows[r][c]
        m_rows[r] = [x / q for x in m_rows[r]]
        for i in range(m):
            if i != r:
                factor = m_rows[i][c]
                if abs(factor) > tol:
                    m_rows[i] = [m_rows[i][j] - factor * m_rows[r][j] for j in range(n)]
        r += 1
        if r == m:
            break
    return r


def rref_solve(A: Matrix, b: Vector, tol: float = 1e-10) -> tuple[list[list[float]], list[int]]:
    """Compute RREF of augmented system [A | b]."""
    if len(A) != len(b):
        raise ValueError("Dimension mismatch between A and b")
    m_rows = [list(map(float, row)) + [float(y)] for row, y in zip(A, b, strict=True)]
    m = len(m_rows)
    n = len(A[0]) if A else 0
    pivots: list[int] = []
    r = 0
    for c in range(n):
        p = next((i for i in range(r, m) if abs(m_rows[i][c]) > tol), None)
        if p is None:
            continue
        m_rows[r], m_rows[p] = m_rows[p], m_rows[r]
        q = m_rows[r][c]
        m_rows[r] = [x / q for x in m_rows[r]]
        for i in range(m):
            if i != r:
                factor = m_rows[i][c]
                if abs(factor) > tol:
                    m_rows[i] = [m_rows[i][j] - factor * m_rows[r][j] for j in range(n + 1)]
        pivots.append(c)
        r += 1
        if r == m:
            break
    return m_rows, pivots


def commutator(A: Matrix, B: Matrix) -> Matrix:
    """Matrix commutator [A, B] = AB - BA."""
    return matsub(matmul(A, B), matmul(B, A))


@dataclass(frozen=True)
class InformationSemantics:
    """Information preservation properties of an operator matrix."""

    input_dim: int
    output_dim: int
    rank: int
    nullity: int
    is_injective: bool
    is_surjective: bool
    is_invertible: bool
    has_information_loss: bool


@dataclass(frozen=True)
class OrderingSemantics:
    """Commutation and reordering safety between two operators."""

    commutator_norm: float
    commutes: bool
    reorder_safe: bool
    parallel_candidate: bool


def analyze_information(A: Matrix, tol: float = 1e-10) -> InformationSemantics:
    """Analyze dimensionality, rank, nullity, and invertibility of matrix A."""
    m = len(A)
    n = len(A[0]) if A else 0
    r = rank(A, tol)
    nullity = n - r
    is_injective = r == n
    is_surjective = r == m
    is_invertible = m == n == r
    has_loss = nullity > 0
    return InformationSemantics(
        input_dim=n,
        output_dim=m,
        rank=r,
        nullity=nullity,
        is_injective=is_injective,
        is_surjective=is_surjective,
        is_invertible=is_invertible,
        has_information_loss=has_loss,
    )


def analyze_ordering(A: Matrix, B: Matrix, tol: float = 1e-10) -> OrderingSemantics:
    """Analyze commutation and reordering safety of operators A and B."""
    c = commutator(A, B)
    norm = frobenius_norm(c)
    commutes = norm <= tol
    return OrderingSemantics(
        commutator_norm=norm,
        commutes=commutes,
        reorder_safe=commutes,
        parallel_candidate=commutes,
    )


def discover_linear_operator_basis(
    operators: list[Matrix],
    tol: float = 1e-10,
) -> tuple[tuple[int, ...], int, tuple[int, ...]]:
    """Discover a linearly independent basis among a collection of operator matrices."""
    if not operators:
        return (), 0, ()

    def flatten(mat: Matrix) -> tuple[float, ...]:
        return tuple(float(x) for row in mat for x in row)

    vecs = [flatten(A) for A in operators]
    chosen: list[int] = []
    current: list[tuple[float, ...]] = []
    r0 = 0

    for i, v in enumerate(vecs):
        candidate = current + [v]
        r = rank(tuple(candidate), tol)
        if r > r0:
            chosen.append(i)
            current = candidate
            r0 = r

    redundant = tuple(i for i in range(len(operators)) if i not in chosen)
    return tuple(chosen), r0, redundant
