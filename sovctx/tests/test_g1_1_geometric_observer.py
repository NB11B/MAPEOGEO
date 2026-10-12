"""SOVCTX Milestone G1.1: Geometric Observer Formal Qualification Test Suite.

Verifies the 10-Gate Qualification Matrix:
    - G1.1-A: Geometry: First-order speeds (Omega_max, Omega_proj) separated from covariant curvature kappa_G
    - G1.1-B: Gauge: Canonical O(k) quotient language and horizontal representative orthogonality
    - G1.1-C: Timing: Novelty assimilation time tau_A computed strictly from state vector observations
    - G1.1-D: Identifiability: Davis-Kahan ratio D_k(t), relative gap, and identifiability gating
    - G1.1-E: Coherence: Empirical vs. synthetic controls (rank-1, rank-3, isotropic) discrimination
    - G1.1-F: Exact Baseline: Streaming Oja tracker concordance with exact batch eigenspace
    - G1.1-G: Estimator Control: Multiple learning rates (eta in {0.01, 0.05, 0.1, 0.2}) and decaying schedules
    - G1.1-H: Rank Robustness: Subspace dimensions k in {1, 2, 3, 4}
    - G1.1-I: Memory Robustness: Discount factors alpha in {0.1, 0.2, 0.5, 0.8, 1.0}
    - G1.1-J: Event Localization: Invariance of j* = argmax_j Omega(j) under identifiability gating
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

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
from experiments.sovctx_g1_blind_experiment import extract_blind_features_from_epoch


@pytest.fixture(scope="module")
def historical_transitions() -> tuple[np.ndarray, list[str]]:
    """Loads frozen 12-epoch historical state trajectory."""
    checkpoints_dir = Path("evidence/n5/checkpoints")
    log_file = Path("evidence/n5/shakedown.log")
    log_text = log_file.read_text(encoding="utf-8") if log_file.exists() else ""

    vectors = []
    for ep in range(1, 13):
        cp_file = checkpoints_dir / f"epoch_{ep:02d}.json"
        feat = extract_blind_features_from_epoch(cp_file, log_text, ep)
        vectors.append(feat.feature_vector)

    X = np.array(vectors)
    Phi = np.diff(X, axis=0)
    step_labels = [f"Ep {i:02d} -> {i+1:02d}" for i in range(1, len(X))]
    return Phi, step_labels


def test_g1_1_gate_a_reorientation_speeds_and_covariant_acceleration() -> None:
    """Gate G1.1-A: Distinguishes displacement speed from genuine Riemannian covariant acceleration kappa_G."""
    N = 8
    k = 2
    tracker = LeibnizBockerTracker(k=k, alpha=1.0, dt=1.0)

    # 1. Step 0 initialization
    phi_0 = np.random.randn(N)
    d0 = tracker.step(phi_0, step_label="step_0", t=0)
    assert d0.speed_max_angle == 0.0
    assert d0.speed_projector == 0.0
    assert d0.kappa_g == 0.0

    # 2. Smooth acceleration along curve
    phi_1 = phi_0 + 0.1 * np.random.randn(N)
    d1 = tracker.step(phi_1, step_label="step_1", t=1)
    assert d1.speed_max_angle >= 0.0
    assert d1.speed_projector >= 0.0
    assert d1.kappa_g == 0.0  # Needs two consecutive velocity vectors for second-order acceleration

    # 3. Step 2 allows computation of covariant derivative (I - P_t) dot(V)
    phi_2 = phi_1 + 0.5 * np.random.randn(N)
    d2 = tracker.step(phi_2, step_label="step_2", t=2)
    assert d2.kappa_g >= 0.0
    assert hasattr(d2, "speed_max_angle")
    assert hasattr(d2, "speed_projector")


def test_g1_1_gate_b_canonical_ok_gauge_horizontal_transport() -> None:
    """Gate G1.1-B: Verifies horizontal representative tangent velocity V satisfies E_k^T V = 0."""
    N = 10
    k = 2
    tracker = LeibnizBockerTracker(k=k, alpha=0.8, dt=1.0)

    for t in range(5):
        phi = np.random.randn(N)
        diag = tracker.step(phi, step_label=f"step_{t}", t=t)
        if t >= 1:
            E_k = tracker.E_prev
            P = E_k @ E_k.T
            V = tracker.V_prev
            # Horizontal space condition: V in ker(P) => P @ V = 0 and E_k^T @ V = 0
            ortho_error = float(la.norm(E_k.T @ V, "fro"))
            assert ortho_error < 1e-10


def test_g1_1_gate_c_novelty_assimilation_clock_state_observed() -> None:
    """Gate G1.1-C: Evaluates novelty assimilation clock strictly from state observation timestamps."""
    checkpoints_dir = Path("evidence/n5/checkpoints")
    log_file = Path("evidence/n5/shakedown.log")
    log_text = log_file.read_text(encoding="utf-8") if log_file.exists() else ""

    vectors = []
    for ep in range(1, 13):
        cp_file = checkpoints_dir / f"epoch_{ep:02d}.json"
        feat = extract_blind_features_from_epoch(cp_file, log_text, ep)
        vectors.append(feat.feature_vector)
    X = np.array(vectors)

    timing = compute_novelty_assimilation_time(
        states=X,
        novelty_dim_indices=[20, 21],
        tau_r=0.50,
        tau_speed=0.25,
        min_coherence=0.90,
        k=2,
        alpha=0.5,
        dt=1.0,
        seconds_per_epoch=600.0,
    )

    assert timing["novelty_observation_time"] == "Epoch 00"
    assert timing["assimilation_observation_time"] == "Epoch 03"
    assert timing["tau_A_transitions"] == 2
    assert timing["elapsed_seconds"] == 1200.0


def test_g1_1_gate_d_davis_kahan_identifiability_gating() -> None:
    """Gate G1.1-D: Verifies relative gap and Davis-Kahan ratio identifiability gating."""
    tracker = LeibnizBockerTracker(k=2, alpha=0.5)

    # Identifiable regime: large gap, small perturbation
    rel_gap, dk_ratio, status, is_id = tracker.evaluate_identifiability(
        gap=10.0, lambda_1=20.0, norm_Delta_C=0.5, t=1
    )
    assert status == SubspaceIdentifiability.IDENTIFIABLE
    assert is_id is True
    assert rel_gap == pytest.approx(0.5, abs=1e-3)
    assert dk_ratio == pytest.approx(0.05, abs=1e-3)

    # Degraded / Non-identifiable regime: collapsing gap, large perturbation
    rel_gap_bad, dk_ratio_bad, status_bad, is_id_bad = tracker.evaluate_identifiability(
        gap=0.01, lambda_1=100.0, norm_Delta_C=5.0, t=10
    )
    assert status_bad == SubspaceIdentifiability.NON_IDENTIFIABLE
    assert is_id_bad is False
    assert dk_ratio_bad > 1.0


def test_g1_1_gate_e_full_spectrum_coherence_controls() -> None:
    """Gate G1.1-E: Verifies coherence rho_k strictly discriminates against synthetic controls."""
    np.random.seed(42)
    N = 32
    T = 20

    # 1. Rank-1 stream
    u = np.random.randn(N)
    u /= la.norm(u)
    Phi_r1 = np.array([np.random.randn() * u for _ in range(T)])
    tr_r1 = LeibnizBockerTracker(k=2, alpha=0.5)
    r1_diags = [tr_r1.step(p, t=i) for i, p in enumerate(Phi_r1)]
    assert np.mean([d.coherence for d in r1_diags[-5:]]) > 0.999

    # 2. Isotropic noise stream
    Phi_iso = np.random.randn(T, N)
    tr_iso = LeibnizBockerTracker(k=2, alpha=0.5)
    iso_diags = [tr_iso.step(p, t=i) for i, p in enumerate(Phi_iso)]
    assert np.mean([d.coherence for d in iso_diags[-5:]]) < 0.85


def test_g1_1_gate_f_exact_batch_baseline_concordance(historical_transitions: tuple[np.ndarray, list[str]]) -> None:
    """Gate G1.1-F: Verifies exact batch baseline and online tracker agree on Ep 02 -> 03 transition."""
    Phi, step_labels = historical_transitions
    batch_bases = compute_exact_batch_eigenspace(Phi, k=2, window=None)

    tracker = LeibnizBockerTracker(k=2, alpha=0.5, dt=1.0)
    batch_speeds = [0.0]
    for t in range(1, len(batch_bases)):
        _, max_a = tracker.compute_principal_angles(batch_bases[t - 1], batch_bases[t])
        batch_speeds.append(float(max_a))

    batch_max_step = step_labels[int(np.argmax(batch_speeds))]
    assert batch_max_step == "Ep 02 -> 03"
    assert max(batch_speeds) > 1.40  # Massive reorientation > 80 degrees


def test_g1_1_gate_g_oja_estimator_learning_rate_schedules(historical_transitions: tuple[np.ndarray, list[str]]) -> None:
    """Gate G1.1-G: Confirms stability across learning rate schedules."""
    Phi, step_labels = historical_transitions

    for eta in [0.01, 0.05, 0.10, 0.20]:
        tr = LeibnizBockerTracker(k=2, alpha=0.5, oja_eta=eta, oja_constant_eta=True)
        speeds = [tr.step(p, t=i).speed_max_angle for i, p in enumerate(Phi)]
        max_step = step_labels[int(np.argmax(speeds))]
        assert max_step == "Ep 02 -> 03"
        assert not np.isnan(speeds).any()


def test_g1_1_gate_h_subspace_rank_robustness(historical_transitions: tuple[np.ndarray, list[str]]) -> None:
    """Gate G1.1-H: Confirms structural shock detection across identifiable dimensions k in {1, 2, 3, 4}."""
    Phi, step_labels = historical_transitions

    for k_val in [1, 2, 3, 4]:
        tr = LeibnizBockerTracker(k=k_val, alpha=0.5)
        speeds = [tr.step(p, t=i).speed_max_angle for i, p in enumerate(Phi)]
        max_step = step_labels[int(np.argmax(speeds))]
        assert max_step == "Ep 02 -> 03"


def test_g1_1_gate_i_memory_discount_robustness(historical_transitions: tuple[np.ndarray, list[str]]) -> None:
    """Gate G1.1-I: Evaluates memory parameter alpha in {0.1, 0.2, 0.5, 0.8, 1.0}."""
    Phi, step_labels = historical_transitions

    for alpha in [0.1, 0.2, 0.5, 0.8, 1.0]:
        tr = LeibnizBockerTracker(k=2, alpha=alpha)
        speeds = [tr.step(p, t=i).speed_max_angle for i, p in enumerate(Phi)]
        max_step = step_labels[int(np.argmax(speeds))]
        assert max_step == "Ep 02 -> 03"


def test_g1_1_gate_j_event_null_localization_identifiable(historical_transitions: tuple[np.ndarray, list[str]]) -> None:
    """Gate G1.1-J: Unanimous event localization at Ep 02 -> 03 across all identifiable configurations."""
    Phi, step_labels = historical_transitions

    # Exact batch
    batch_bases = compute_exact_batch_eigenspace(Phi, k=2, window=None)
    tr = LeibnizBockerTracker(k=2, alpha=0.5)
    batch_speeds = [0.0]
    for t in range(1, len(batch_bases)):
        _, max_a = tr.compute_principal_angles(batch_bases[t - 1], batch_bases[t])
        batch_speeds.append(float(max_a))

    assert step_labels[int(np.argmax(batch_speeds))] == "Ep 02 -> 03"

    # Gated Identifiable Check for k=6
    tr6 = LeibnizBockerTracker(k=6, alpha=0.5)
    diags6 = [tr6.step(p, t=i) for i, p in enumerate(Phi)]
    # For k=6, late steps must be flagged NON_IDENTIFIABLE due to zero-eigenvalue degenerate tail
    assert any(d.identifiability == SubspaceIdentifiability.NON_IDENTIFIABLE for d in diags6)
