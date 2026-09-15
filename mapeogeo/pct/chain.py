"""Exact finite simplicial chain complex algebra and Euler-Poincare invariants."""

from __future__ import annotations

from collections import defaultdict
import sympy as sp

from mapeogeo.pct.models import CoefficientField, FiniteComplex, Simplex


def permutation_sign(seq: tuple[int, ...]) -> int:
    """Compute permutation sign (+1 or -1) of a sequence relative to its sorted order."""
    inversions = 0
    n = len(seq)
    for i in range(n):
        for j in range(i + 1, n):
            if seq[i] > seq[j]:
                inversions += 1
    return -1 if inversions % 2 == 1 else 1


def canonical_simplex(s: Simplex) -> tuple[Simplex, int]:
    """Return (canonical_simplex_with_sorted_vertices, sign)."""
    sorted_v = tuple(sorted(s.vertices))
    sign = permutation_sign(s.vertices)
    return Simplex(vertices=sorted_v), sign


def simplices_by_degree(complex_: FiniteComplex) -> dict[int, list[Simplex]]:
    """Return dict mapping degree k -> canonically sorted list of unique canonical k-simplices."""
    by_deg: dict[int, set[Simplex]] = defaultdict(set)
    for s in complex_.simplices:
        canon_s, _ = canonical_simplex(s)
        by_deg[canon_s.dimension].add(canon_s)

    # Ensure all intermediate degrees down to 0 are present
    max_dim = max(by_deg.keys()) if by_deg else 0
    for d in range(max_dim + 1):
        if d not in by_deg:
            by_deg[d] = set()

    return {
        d: sorted(list(simps), key=lambda x: x.vertices)
        for d, simps in sorted(by_deg.items())
    }


def boundary_matrix(complex_: FiniteComplex, k: int) -> sp.Matrix:
    """Compute exact boundary matrix d_k: C_k -> C_{k-1} as a sympy.Matrix.
    
    Rows correspond to canonical (k-1)-simplices, columns to canonical k-simplices.
    """
    deg_map = simplices_by_degree(complex_)
    c_k = deg_map.get(k, [])
    c_k_minus_1 = deg_map.get(k - 1, [])

    n_rows = len(c_k_minus_1)
    n_cols = len(c_k)

    if n_rows == 0 or n_cols == 0:
        return sp.zeros(n_rows, n_cols)

    row_index = {s: idx for idx, s in enumerate(c_k_minus_1)}
    mat = sp.zeros(n_rows, n_cols)

    for col_idx, s in enumerate(c_k):
        v = s.vertices
        for i in range(len(v)):
            face_v = v[:i] + v[i + 1:]
            canon_face, p_sign = canonical_simplex(Simplex(vertices=face_v))
            if canon_face in row_index:
                coeff = ((-1) ** i) * p_sign
                r_idx = row_index[canon_face]
                mat[r_idx, col_idx] += coeff

    return mat


def rank_gf2(matrix: sp.Matrix) -> int:
    """Compute rank of matrix over GF(2) using exact XOR Gaussian elimination."""
    if matrix.rows == 0 or matrix.cols == 0:
        return 0
    rows = [
        [int(matrix[r, c]) & 1 for c in range(matrix.cols)]
        for r in range(matrix.rows)
    ]
    rank = 0
    for col in range(matrix.cols):
        pivot = next((r for r in range(rank, len(rows)) if rows[r][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for r in range(len(rows)):
            if r != rank and rows[r][col]:
                rows[r] = [a ^ b for a, b in zip(rows[r], rows[rank])]
        rank += 1
    return rank


def rank_over_field(matrix: sp.Matrix, field: CoefficientField) -> int:
    """Compute exact rank over GF(2) or Q."""
    if matrix.rows == 0 or matrix.cols == 0:
        return 0
    if field == CoefficientField.GF2:
        return rank_gf2(matrix)
    elif field == CoefficientField.Q:
        return int(matrix.rank())
    else:
        raise ValueError(f"Unsupported coefficient field: {field}")


def betti_numbers(complex_: FiniteComplex, field: CoefficientField) -> dict[int, int]:
    """Compute Betti numbers beta_k = dim(C_k) - rank(d_k) - rank(d_{k+1})."""
    deg_map = simplices_by_degree(complex_)
    max_dim = max(deg_map.keys()) if deg_map else 0

    ranks: dict[int, int] = {}
    for k in range(max_dim + 2):
        d_k = boundary_matrix(complex_, k)
        ranks[k] = rank_over_field(d_k, field)

    betti: dict[int, int] = {}
    for k in range(max_dim + 1):
        dim_c_k = len(deg_map.get(k, []))
        rk_dk = ranks.get(k, 0)
        rk_dk_plus_1 = ranks.get(k + 1, 0)
        bk = dim_c_k - rk_dk - rk_dk_plus_1
        if bk < 0:
            raise ValueError(f"Negative Betti number at degree {k}: {bk}")
        betti[k] = bk

    return betti


def euler_from_chains(complex_: FiniteComplex) -> int:
    """Compute Euler characteristic from alternating sum of chain group dimensions."""
    deg_map = simplices_by_degree(complex_)
    return sum(((-1) ** k) * len(simps) for k, simps in deg_map.items())


def euler_from_homology(complex_: FiniteComplex, field: CoefficientField) -> int:
    """Compute Euler characteristic from alternating sum of Betti numbers."""
    betti = betti_numbers(complex_, field)
    return sum(((-1) ** k) * bk for k, bk in betti.items())


def check_chain_condition(complex_: FiniteComplex) -> bool:
    """Verify exact d_{k-1} * d_k = 0 for all degrees."""
    deg_map = simplices_by_degree(complex_)
    max_dim = max(deg_map.keys()) if deg_map else 0
    for k in range(1, max_dim + 2):
        d_k = boundary_matrix(complex_, k)
        d_k_minus_1 = boundary_matrix(complex_, k - 1)
        if d_k_minus_1.rows > 0 and d_k.cols > 0:
            prod = d_k_minus_1 * d_k
            if prod != sp.zeros(prod.rows, prod.cols):
                return False
    return True
