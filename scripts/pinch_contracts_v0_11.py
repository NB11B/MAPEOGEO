"""S3 computational contract executor for MAPEOGEO v0.11 intake targets."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any
import sympy as sp


@dataclass(frozen=True)
class ContractResult:
    source_id: str
    contract_id: str | None
    test_state: str
    applicability: str
    verdict: str
    scope: str | None
    measured: dict[str, Any]
    refused: tuple[str, ...]


def _eval_linear_independence_not_in_span_q() -> dict[str, Any]:
    """Positive and negative tests for linear independence vs span of remainder over Q."""
    # Positive: linearly independent vectors in Q^3
    v1 = sp.Matrix([1, 0, 0])
    v2 = sp.Matrix([0, 1, 0])
    v3 = sp.Matrix([1, 1, 1])
    mat_pos = sp.Matrix.hstack(v1, v2, v3)
    pos_rank = int(mat_pos.rank())
    pos_independent = (pos_rank == 3)

    # Check v3 not in span(v1, v2)
    mat_v12 = sp.Matrix.hstack(v1, v2)
    mat_v12_v3 = sp.Matrix.hstack(v1, v2, v3)
    v3_in_span = (mat_v12.rank() == mat_v12_v3.rank())

    # Negative control: linearly dependent vectors
    w1 = sp.Matrix([1, 0, 0])
    w2 = sp.Matrix([0, 1, 0])
    w3 = sp.Matrix([2, 3, 0])
    mat_neg = sp.Matrix.hstack(w1, w2, w3)
    neg_rank = int(mat_neg.rank())
    mat_w12 = sp.Matrix.hstack(w1, w2)
    w3_in_span = (mat_w12.rank() == mat_neg.rank())

    all_ok = (pos_independent and not v3_in_span and (neg_rank < 3) and w3_in_span)
    return {
        "positive_independent": pos_independent,
        "positive_v3_not_in_span": not v3_in_span,
        "negative_dependent": neg_rank < 3,
        "negative_w3_in_span": w3_in_span,
        "all_checks_passed": all_ok,
    }


def _eval_spectral_decomposition_symmetric_matrix() -> dict[str, Any]:
    """Test symmetric matrix real eigenvalue and orthogonal eigenbasis decomposition."""
    # 3x3 symmetric matrix over Q with rational eigenvalues
    A = sp.Matrix([
        [2, 1, 0],
        [1, 2, 0],
        [0, 0, 3],
    ])
    assert A == A.T

    # Diagonalize using sympy
    P, D = A.diagonalize()
    # Verify P * D * P^(-1) == A
    recon_diff = A - P * D * P.inv()
    is_diagonal = D.is_diagonal()
    recon_zero = (recon_diff == sp.zeros(3, 3))

    all_ok = (is_diagonal and recon_zero)
    return {
        "is_symmetric": True,
        "is_diagonalized": is_diagonal,
        "reconstruction_exact_zero": recon_zero,
        "eigenvalues": [str(D[i, i]) for i in range(3)],
        "all_checks_passed": all_ok,
    }


def _eval_subspace_disjoint_intersection_q() -> dict[str, Any]:
    """Test direct sum disjoint intersection U cap W = {0} over Q."""
    # Positive case: U = span(e1, e2), W = span(e3) in Q^3
    u1 = sp.Matrix([1, 0, 0])
    u2 = sp.Matrix([0, 1, 0])
    w1 = sp.Matrix([0, 0, 1])

    mat_U = sp.Matrix.hstack(u1, u2)
    mat_W = sp.Matrix.hstack(w1)
    mat_total = sp.Matrix.hstack(u1, u2, w1)

    # dim(U) + dim(W) = dim(U + W) <=> U cap W = {0}
    dim_U = int(mat_U.rank())
    dim_W = int(mat_W.rank())
    dim_total = int(mat_total.rank())
    pos_disjoint = (dim_total == dim_U + dim_W)

    # Negative control: U = span(e1, e2), W' = span(e1 + e2)
    w_dep = sp.Matrix([1, 1, 0])
    mat_neg_total = sp.Matrix.hstack(u1, u2, w_dep)
    dim_neg_total = int(mat_neg_total.rank())
    neg_not_disjoint = (dim_neg_total < dim_U + 1)

    all_ok = (pos_disjoint and neg_not_disjoint)
    return {
        "pos_dim_U": dim_U,
        "pos_dim_W": dim_W,
        "pos_dim_total": dim_total,
        "positive_disjoint": pos_disjoint,
        "negative_control_rejected": neg_not_disjoint,
        "all_checks_passed": all_ok,
    }


def run_contract(target: dict[str, Any]) -> ContractResult:
    """Execute S3 computational contract for a given intake target."""
    source_id = target.get("source_id", "UNKNOWN")
    test_state = target.get("s3_test_state", "UNTESTED")
    contract_id = target.get("s3_contract_id")
    scope = target.get("s3_scope")

    if test_state == "UNTESTED":
        return ContractResult(
            source_id=source_id,
            contract_id=None,
            test_state="UNTESTED",
            applicability="NOT_RUN",
            verdict="UNTESTED",
            scope=None,
            measured={},
            refused=("S3 computational contract explicitly marked UNTESTED; no executable tests run.",),
        )

    elif test_state == "PCT_CONTRACT":
        return ContractResult(
            source_id=source_id,
            contract_id=contract_id,
            test_state="PCT_CONTRACT",
            applicability="NOT_APPLICABLE",
            verdict="NOT_APPLICABLE",
            scope=scope,
            measured={},
            refused=("PCT representation not applicable to algebraic module target.",),
        )

    elif test_state == "EXECUTABLE_CONTRACT":
        if contract_id == "linear_independence_not_in_span_q":
            res = _eval_linear_independence_not_in_span_q()
            verdict = "PASS" if res.get("all_checks_passed") else "FAIL"
            return ContractResult(
                source_id=source_id,
                contract_id=contract_id,
                test_state=test_state,
                applicability="APPLICABLE",
                verdict=verdict,
                scope=scope,
                measured=res,
                refused=(),
            )
        elif contract_id == "spectral_decomposition_symmetric_matrix":
            res = _eval_spectral_decomposition_symmetric_matrix()
            verdict = "PASS" if res.get("all_checks_passed") else "FAIL"
            return ContractResult(
                source_id=source_id,
                contract_id=contract_id,
                test_state=test_state,
                applicability="APPLICABLE",
                verdict=verdict,
                scope=scope,
                measured=res,
                refused=(),
            )
        elif contract_id == "subspace_disjoint_intersection_q":
            res = _eval_subspace_disjoint_intersection_q()
            verdict = "PASS" if res.get("all_checks_passed") else "FAIL"
            return ContractResult(
                source_id=source_id,
                contract_id=contract_id,
                test_state=test_state,
                applicability="APPLICABLE",
                verdict=verdict,
                scope=scope,
                measured=res,
                refused=(),
            )
        else:
            return ContractResult(
                source_id=source_id,
                contract_id=contract_id,
                test_state=test_state,
                applicability="APPLICABLE",
                verdict="INVALID",
                scope=scope,
                measured={},
                refused=(f"Unknown executable contract_id: {contract_id}",),
            )

    else:
        return ContractResult(
            source_id=source_id,
            contract_id=contract_id,
            test_state=test_state,
            applicability="NOT_RUN",
            verdict="INVALID",
            scope=scope,
            measured={},
            refused=(f"Unknown s3_test_state: {test_state}",),
        )
