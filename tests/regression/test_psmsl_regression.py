"""Semantic regression tests reproducing historical PSMSL operator algebra
and latent observability.
"""

from __future__ import annotations

import math

from mapeogeo.psmsl.algebra import analyze_information, analyze_ordering
from mapeogeo.psmsl.latent import ObservableSignature
from mapeogeo.psmsl.operator import TransformationOperator
from mapeogeo.psmsl.projection import InverseProjection, StateProjection


def test_projection_declares_information_loss_regression() -> None:
    P = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    s = analyze_information(P)
    assert s.rank == 2 and s.nullity == 1 and s.has_information_loss
    assert s.is_surjective and not s.is_injective and not s.is_invertible


def test_rotation_is_information_preserving_regression() -> None:
    R = ((0.0, -1.0), (1.0, 0.0))
    s = analyze_information(R)
    assert s.rank == 2 and s.nullity == 0 and s.is_invertible and not s.has_information_loss


def test_uniform_scale_commutes_with_rotation_regression() -> None:
    S = ((2.0, 0.0), (0.0, 2.0))
    R = ((0.0, -1.0), (1.0, 0.0))
    o = analyze_ordering(S, R)
    assert o.commutes and o.reorder_safe and o.parallel_candidate


def test_anisotropic_scale_does_not_commute_with_rotation_regression() -> None:
    S = ((2.0, 0.0), (0.0, 1.0))
    R = ((0.0, -1.0), (1.0, 0.0))
    o = analyze_ordering(S, R)
    assert not o.commutes and not o.reorder_safe
    assert o.commutator_norm > 0


def test_operator_composition_preserves_fusion_order_regression() -> None:
    A = TransformationOperator(operator_id="A", matrix=((2.0, 0.0), (0.0, 1.0)))
    B = TransformationOperator(operator_id="B", matrix=((0.0, -1.0), (1.0, 0.0)))
    # fuse(A, B) = matmul(B, A) = ((0, -1), (2, 0))
    fused = B.compose(A)
    assert fused.matrix == ((0.0, -1.0), (2.0, 0.0))


def test_trajectory_observability_matrix_recovers_state_regression() -> None:
    # A = 90 deg rotation, C = first coordinate projection
    A = ((0.0, -1.0), (1.0, 0.0))
    C = ((1.0, 0.0),)
    # O = [C; CA] = [ [1, 0]; [0, -1] ]
    O_mat = ObservableSignature.build_trajectory_matrix(A, C, 2)
    assert O_mat == ((1.0, 0.0), (0.0, -1.0))

    # True state q0 = (2.0, 3.0). Obs: y0 = 2.0, y1 = -3.0
    P = StateProjection(projection_id="trajectory_P", matrix=O_mat)
    obs = (2.0, -3.0)
    res = InverseProjection.reconstruct(P, obs)
    assert res.is_uniquely_identified
    assert res.null_basis == ()
    assert all(
        math.isclose(a, b, abs_tol=1e-12)
        for a, b in zip(res.reconstructed_state, (2.0, 3.0), strict=True)
    )
