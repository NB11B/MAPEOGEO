"""Unit tests for the Leibniz-Bocker Grassmannian Subspace Tracker and Diagnostics."""

import numpy as np
import pytest
import scipy.linalg as la

from sovctx.node.leibniz_bocker import (
    DiagnosticRegime,
    LeibnizBockerDiagnostics,
    LeibnizBockerTracker,
    SubspaceIdentifiability,
    compute_exact_batch_eigenspace,
    compute_grassmann_distance,
    compute_novelty_assimilation_time,
)


def test_tracker_initialization_and_single_step() -> None:
    tracker = LeibnizBockerTracker(k=2, alpha=0.5)
    phi = np.array([1.0, 2.0, 0.5, 0.0, 0.1])
    diag = tracker.step(phi, step_label="step_0", t=0)

    assert diag.t == 0
    assert diag.coherence == pytest.approx(1.0, abs=1e-5)
    assert diag.speed_max_angle == 0.0
    assert diag.speed_projector == 0.0
    assert diag.curvature_max_angle == 0.0
    assert diag.curvature_projector == 0.0
    assert diag.residual_norm == pytest.approx(0.0, abs=1e-5)
    assert diag.regime == DiagnosticRegime.STABLE_REGIME


def test_rotating_subspace_curvature_and_orthogonality() -> None:
    """Experiment 1: Subspace rotating in R^10 with an orthogonal shock."""
    N = 10
    k = 2
    tracker = LeibnizBockerTracker(k=k, alpha=0.9, dt=1.0)

    theta = 0.05  # 0.05 rad per step
    # Rotation matrix in plane (0, 1)
    c, s = np.cos(theta), np.sin(theta)
    R = np.eye(N)
    R[0, 0], R[0, 1] = c, -s
    R[1, 0], R[1, 1] = s, c

    v = np.zeros(N)
    v[0] = 1.0

    # 1. Smooth rotation
    for t in range(10):
        v = R @ v
        diag = tracker.step(v, step_label=f"rot_{t}", t=t)
        if t > 2:
            assert diag.coherence > 0.95
            assert diag.residual_fraction < 0.1

    # 2. Inject orthogonal shock in coordinate 5
    v_shock = np.zeros(N)
    v_shock[5] = 5.0  # Completely orthogonal to plane (0, 1)
    diag_shock = tracker.step(v_shock, step_label="shock", t=10)

    # Shock must produce a high displacement speed
    assert diag_shock.speed_max_angle > 0.5 or diag_shock.speed_projector > 0.5
    assert diag_shock.regime in (
        DiagnosticRegime.REGIME_REORIENTATION,
        DiagnosticRegime.DIMENSIONALITY_EXPANSION,
        DiagnosticRegime.MODEL_COLLAPSE,
    )


def test_projector_curvature_approximation_identity() -> None:
    """Tests Section 3 identity: ||P_{t+dt} - P_t||_F^2 \approx 2 sum_i theta_i^2 for small angles.

    Also tests the exact Grassmannian relation ||P_{t+dt} - P_t||_F^2 = 2 sum_i sin^2(theta_i).
    """
    N = 8
    k = 2
    tracker = LeibnizBockerTracker(k=k, alpha=1.0)

    # Orthonormal rank-k frame
    E1, _ = np.linalg.qr(np.random.randn(N, k))
    # Small skew-symmetric rotation in ambient space
    G = np.random.randn(N, N)
    A = (G - G.T) * 0.03
    R = la.expm(A)
    E2 = R @ E1

    angles, _ = tracker.compute_principal_angles(E1, E2)
    P1 = E1 @ E1.T
    P2 = E2 @ E2.T
    frob_sq = float(np.linalg.norm(P2 - P1, "fro") ** 2)

    theta_sum = float(np.sum(np.square(angles)))
    sin_sq_sum = float(np.sum(np.square(np.sin(angles))))

    # 1. Exact Grassmannian projector identity
    assert frob_sq == pytest.approx(2.0 * sin_sq_sum, rel=1e-5)

    # 2. Small-angle Taylor approximation from paper: frob_sq \approx 2 * theta_sum
    assert frob_sq == pytest.approx(2.0 * theta_sum, rel=0.01)


def test_online_oja_tracker_alignment() -> None:
    """Verifies that online Oja streaming frame aligns with leading eigenspace."""
    N = 6
    k = 2
    tracker = LeibnizBockerTracker(k=k, alpha=0.2)

    # Generate samples from a fixed 2D subspace
    U_true, _ = np.linalg.qr(np.random.randn(N, k))
    for t in range(60):
        coeff = np.random.randn(k)
        phi = U_true @ coeff
        diag = tracker.step(phi, t=t)

    assert tracker.W_online is not None
    assert tracker.E_prev is not None

    # Check subspace overlap: ||W^T E||_F should be close to sqrt(k) ~ 1.414
    overlap = np.linalg.norm(tracker.W_online.T @ tracker.E_prev, "fro")
    assert overlap > 1.0  # high subspace projection overlap


def test_novelty_assimilation_time_uses_state_observation_times() -> None:
    """G1.1-C: Verifies that tau_A is derived mechanically from state vector observations."""
    N = 5
    states = np.zeros((6, N))
    states[1, 3] = 5.0
    states[2, 3] = 5.0
    states[2, 1] = 2.0
    states[3, 3] = 5.0
    states[3, 1] = 4.0
    states[4, 3] = 5.0
    states[4, 1] = 6.0
    states[5, 3] = 5.0
    states[5, 1] = 8.0

    res = compute_novelty_assimilation_time(
        states=states,
        novelty_dim_indices=[3],
        tau_r=0.50,
        tau_speed=0.25,
        min_coherence=0.85,
        k=2,
        alpha=0.5,
        dt=1.0,
        seconds_per_epoch=600.0,
    )

    assert res["novelty_observation_time"] == "Epoch 01"
    assert res["novelty_transition_index"] == 0
    assert res["assimilation_transition_index"] is not None
    assert res["tau_A_transitions"] is not None
    assert res["tau_A_transitions"] >= 1
    assert res["elapsed_seconds"] == res["tau_A_transitions"] * 600.0


def test_davis_kahan_identifiability_gating() -> None:
    """G1.1-D: Verifies that shrinking eigengap blocks false STABLE_REGIME attribution."""
    tracker = LeibnizBockerTracker(
        k=2,
        alpha=0.5,
        regime_thresholds={
            "coherence_high": 0.70,
            "speed_low": 0.25,
            "speed_high": 0.70,
            "residual_high": 0.35,
            "tau_gamma": 0.05,
            "tau_relative_gap": 0.05,
            "tau_dk_identifiable": 0.50,
            "tau_dk_marginal": 1.00,
        },
    )

    v1 = np.array([1.0, 0.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0, 0.0])
    v3 = np.array([0.0, 0.0, 1.0, 0.0])

    for t in range(15):
        phi = v1 if t % 3 == 0 else (v2 if t % 3 == 1 else v3)
        diag = tracker.step(phi, t=t)

    assert diag.identifiability in (
        SubspaceIdentifiability.MARGINAL,
        SubspaceIdentifiability.NON_IDENTIFIABLE,
    )
    assert diag.regime != DiagnosticRegime.STABLE_REGIME


def test_exact_batch_baseline_and_grassmann_distance() -> None:
    """G1.1-F: Verifies exact batch baseline and Grassmannian distance computation."""
    N = 6
    k = 2
    T = 10
    np.random.seed(42)

    U1, _ = np.linalg.qr(np.random.randn(N, k))
    U2, _ = np.linalg.qr(np.random.randn(N, k))

    Phi = np.zeros((T, N))
    for t in range(5):
        Phi[t] = U1 @ np.random.randn(k)
    for t in range(5, T):
        Phi[t] = U2 @ np.random.randn(k)

    batch_bases = compute_exact_batch_eigenspace(Phi, k=k)
    assert len(batch_bases) == T

    d_shock = compute_grassmann_distance(batch_bases[4], batch_bases[5])
    assert d_shock > 0.2
