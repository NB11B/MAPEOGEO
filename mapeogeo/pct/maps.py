"""Chain maps, exact residuals, and correspondence integrity checks."""

from __future__ import annotations

from typing import Any
import sympy as sp

from mapeogeo.pct.chain import boundary_matrix, simplices_by_degree
from mapeogeo.pct.fixtures import triangle_loop_complex, triangle_loop_subdivided_complex
from mapeogeo.pct.models import ChainMap, FiniteComplex


def triangle_subdivision_map(corrupt: bool = False) -> ChainMap:
    """Construct chain map from coarse triangle_loop to fine triangle_loop_subdivided.
    
    If corrupt=True, intentionally perturbs the 1-chain map to fail commutativity.
    """
    coarse = triangle_loop_complex()
    fine = triangle_loop_subdivided_complex()

    deg_coarse = simplices_by_degree(coarse)
    deg_fine = simplices_by_degree(fine)

    # Degree 0: coarse vertices (0,1,2) -> fine vertices (0,2,4)
    # fine C0: [(0,), (1,), (2,), (3,), (4,), (5,)]
    # coarse C0: [(0,), (1,), (2,)]
    f0 = sp.zeros(len(deg_fine[0]), len(deg_coarse[0]))
    f0[0, 0] = 1  # 0 -> 0
    f0[2, 1] = 1  # 1 -> 2
    f0[4, 2] = 1  # 2 -> 4

    # Degree 1:
    # coarse C1: [(0, 1), (0, 2), (1, 2)]
    # fine C1: [(0, 1), (0, 5), (1, 2), (2, 3), (3, 4), (4, 5)]
    fine_c1_idx = {s.vertices: i for i, s in enumerate(deg_fine[1])}
    coarse_c1_idx = {s.vertices: i for i, s in enumerate(deg_coarse[1])}

    f1 = sp.zeros(len(deg_fine[1]), len(deg_coarse[1]))

    # (0, 1) -> (0, 1) + (1, 2)
    c_01 = coarse_c1_idx[(0, 1)]
    f1[fine_c1_idx[(0, 1)], c_01] = 1
    if not corrupt:
        f1[fine_c1_idx[(1, 2)], c_01] = 1
    else:
        # Corruption: omit (1, 2) or perturb
        f1[fine_c1_idx[(1, 2)], c_01] = 0

    # (0, 2) -> (0, 5) - (4, 5)
    c_02 = coarse_c1_idx[(0, 2)]
    f1[fine_c1_idx[(0, 5)], c_02] = 1
    f1[fine_c1_idx[(4, 5)], c_02] = -1

    # (1, 2) -> (2, 3) + (3, 4)
    c_12 = coarse_c1_idx[(1, 2)]
    f1[fine_c1_idx[(2, 3)], c_12] = 1
    f1[fine_c1_idx[(3, 4)], c_12] = 1

    return ChainMap(
        map_id="triangle_subdivision_corrupted" if corrupt else "triangle_subdivision",
        source_id=coarse.complex_id,
        target_id=fine.complex_id,
        matrices_by_degree={0: f0, 1: f1},
        construction_method="BARYCENTRIC_SUBDIVISION_1D",
    )


def chain_map_residual(
    source: FiniteComplex,
    target: FiniteComplex,
    chain_map: ChainMap,
    k: int,
) -> sp.Matrix:
    """Compute exact residual matrix at degree k: d_k^target * F_k - F_{k-1} * d_k^source."""
    deg_source = simplices_by_degree(source)
    deg_target = simplices_by_degree(target)

    f_k = chain_map.matrices_by_degree.get(k)
    f_k_minus_1 = chain_map.matrices_by_degree.get(k - 1)

    dim_s_k = len(deg_source.get(k, []))
    dim_s_km1 = len(deg_source.get(k - 1, []))
    dim_t_k = len(deg_target.get(k, []))
    dim_t_km1 = len(deg_target.get(k - 1, []))

    if f_k is None:
        f_k = sp.zeros(dim_t_k, dim_s_k)
    if f_k_minus_1 is None:
        f_k_minus_1 = sp.zeros(dim_t_km1, dim_s_km1)

    d_k_target = boundary_matrix(target, k)
    d_k_source = boundary_matrix(source, k)

    # target: d_k: C_k -> C_{k-1} (size dim_t_km1 x dim_t_k)
    # F_k: size dim_t_k x dim_s_k
    # d_k_target * F_k : size dim_t_km1 x dim_s_k
    term1 = d_k_target * f_k if (d_k_target.rows > 0 and f_k.cols > 0) else sp.zeros(dim_t_km1, dim_s_k)

    # F_{k-1}: size dim_t_km1 x dim_s_km1
    # d_k_source: size dim_s_km1 x dim_s_k
    # F_{k-1} * d_k_source : size dim_t_km1 x dim_s_k
    term2 = f_k_minus_1 * d_k_source if (f_k_minus_1.rows > 0 and d_k_source.cols > 0) else sp.zeros(dim_t_km1, dim_s_k)

    return term1 - term2


def check_chain_map(
    source: FiniteComplex,
    target: FiniteComplex,
    chain_map: ChainMap,
) -> dict[str, Any]:
    """Verify that chain map commutes with boundaries across all relevant degrees."""
    deg_source = simplices_by_degree(source)
    deg_target = simplices_by_degree(target)
    max_dim = max(
        max(deg_source.keys()) if deg_source else 0,
        max(deg_target.keys()) if deg_target else 0,
    )

    residuals: dict[int, sp.Matrix] = {}
    residual_nonzeros: dict[int, int] = {}
    nonzeros_detail: dict[int, list[dict[str, Any]]] = {}

    overall_pass = True

    for k in range(max_dim + 2):
        res = chain_map_residual(source, target, chain_map, k)
        residuals[k] = res
        nnz = 0
        details = []
        for r in range(res.rows):
            for c in range(res.cols):
                val = res[r, c]
                if val != 0:
                    nnz += 1
                    details.append({"row": r, "col": c, "value": int(val)})
        residual_nonzeros[k] = nnz
        nonzeros_detail[k] = details
        if nnz > 0:
            overall_pass = False

    return {
        "pass": overall_pass,
        "residuals_by_degree": residuals,
        "residual_nonzero_entries": residual_nonzeros,
        "nonzeros_detail": nonzeros_detail,
    }
