"""Unit tests for canonical PSMSL operator algebra, projection, and latent generators."""

from __future__ import annotations

import pytest

from mapeogeo.psmsl.algebra import (
    analyze_information,
    analyze_ordering,
    discover_linear_operator_basis,
    matmul,
    rank,
)
from mapeogeo.psmsl.latent import LatentGenerator
from mapeogeo.psmsl.operator import OperatorWord, TransformationOperator
from mapeogeo.psmsl.projection import InverseProjection, StateProjection


def test_matrix_operations_and_rank() -> None:
    A = ((1.0, 2.0), (3.0, 4.0))
    B = ((2.0, 0.0), (1.0, 2.0))
    # AB = ((4, 4), (10, 8))
    AB = matmul(A, B)
    assert AB == ((4.0, 4.0), (10.0, 8.0))

    assert rank(A) == 2
    singular = ((1.0, 2.0), (2.0, 4.0))
    assert rank(singular) == 1


def test_information_and_ordering_semantics() -> None:
    A = ((1.0, 0.0), (0.0, 1.0))
    info_A = analyze_information(A)
    assert info_A.is_invertible
    assert not info_A.has_information_loss

    lossy = ((1.0, 0.0), (0.0, 0.0))
    info_lossy = analyze_information(lossy)
    assert info_lossy.has_information_loss
    assert info_lossy.nullity == 1

    # Commuting operators
    B = ((2.0, 0.0), (0.0, 3.0))
    ordering = analyze_ordering(A, B)
    assert ordering.commutes
    assert ordering.reorder_safe


def test_transformation_operator_and_word_composition() -> None:
    T1 = TransformationOperator(operator_id="T1", matrix=((1.0, 1.0), (0.0, 1.0)))
    T2 = TransformationOperator(operator_id="T2", matrix=((2.0, 0.0), (0.0, 2.0)))

    # T2 o T1
    composed = T2.compose(T1)
    assert composed.operator_id == "(T2oT1)"
    assert composed.matrix == ((2.0, 2.0), (0.0, 2.0))

    word = OperatorWord(word_id="w1", operators=(T2, T1))
    eval_op = word.evaluate()
    assert eval_op.matrix == composed.matrix


def test_linear_operator_basis_discovery() -> None:
    op1 = ((1.0, 0.0), (0.0, 0.0))
    op2 = ((0.0, 1.0), (0.0, 0.0))
    op3 = ((2.0, 2.0), (0.0, 0.0))  # 2*op1 + 2*op2 (redundant)

    basis_idx, b_rank, redundant_idx = discover_linear_operator_basis([op1, op2, op3])
    assert basis_idx == (0, 1)
    assert b_rank == 2
    assert redundant_idx == (2,)


def test_state_projection_and_exact_inverse_reconstruction() -> None:
    # Full rank projection: 2 latent dims, 2 observations
    P = StateProjection(projection_id="P_full", matrix=((1.0, 0.0), (0.0, 1.0)))
    true_state = (3.5, -1.2)
    obs = P.project(true_state)
    assert obs == (3.5, -1.2)

    res = InverseProjection.reconstruct(P, obs)
    assert res.is_uniquely_identified
    assert res.reconstructed_state == (3.5, -1.2)
    assert len(res.null_basis) == 0
    assert res.residual <= 1e-9


def test_rank_deficient_projection_identifies_null_space() -> None:
    # Projection has null space: 3 latent dims, 2 observation rows
    P = StateProjection(projection_id="P_lossy", matrix=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    obs = (4.0, 5.0)

    res = InverseProjection.reconstruct(P, obs)
    assert not res.is_uniquely_identified
    assert len(res.null_basis) == 1  # 3 - 2 = 1 null dimension
    assert res.reconstructed_state[:2] == (4.0, 5.0)
    assert res.reconstructed_state[2] == 0.0


def test_inconsistent_observation_fails_closed() -> None:
    # Inconsistent projection system: row 1: x1 = 1, row 2: x1 = 2
    P = StateProjection(projection_id="P_incon", matrix=((1.0,), (1.0,)))
    obs = (1.0, 2.0)
    with pytest.raises(ValueError, match="Inconsistent observation"):
        InverseProjection.reconstruct(P, obs)


def test_latent_generator_fail_closed_status() -> None:
    # 1. Status 'unknown' is allowed and preserves non-identified state
    gen_unknown = LatentGenerator(generator_id="gen_unk", status="unknown", nullity=2)
    assert gen_unknown.status == "unknown"

    # 2. Positive nullity strictly forbids status 'identified'
    with pytest.raises(ValueError, match="Fail-closed invariant violation"):
        LatentGenerator(
            generator_id="gen_bad",
            status="identified",
            nullity=1,
            estimated_state=(1.0, 2.0),
        )

    # 3. Full rank (nullity=0) allows identified state
    gen_identified = LatentGenerator(
        generator_id="gen_good",
        status="identified",
        nullity=0,
        estimated_state=(1.0, 2.0),
    )
    assert gen_identified.status == "identified"
