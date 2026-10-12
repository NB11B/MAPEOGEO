"""The Leibniz-Bocker Framework: Spectral Subspace Geometry on Grassmann Manifolds.

Formalizes the geometric decomposition of infinitesimal motion:
    phi(t) = x(t+1) - x(t)
    C(t) = E[phi phi^T]
    E_k(t) in Gr(k, N)

Decomposes motion into:
    phi(t) = E_k(t) a(t) + r(t)
    where a(t) = E_k(t)^T phi(t) are harmonic coordinates
    and r(t) is orthogonal residual novelty.

Tracks the Diagnostic Trinity & Qualification Metrics:
    1. Coherence rho_k(t): variance concentration in leading k modes
    2. Grassmannian max-angle reorientation rate Omega_k(t) (OMEGA_MAXANGLE)
    3. Projector displacement rate Omega_tilde_k(t) (OMEGA_PROJECTOR)
    4. Genuine Riemannian covariant acceleration / curvature kappa_G(t) = ||nabla_{dot E} dot E||
    5. Residual norm ||r_k(t)||: novelty outside dominant subspace
    6. Spectral gap gamma_k(t), relative gap gamma_tilde_k(t), and Davis-Kahan ratio D_k(t)
    7. Subspace identifiability gating: IDENTIFIABLE, MARGINAL, NON_IDENTIFIABLE

Includes streaming online Oja-style subspace tracker, exact batch baseline, and autonomous regime classifier:
    - STABLE_REGIME
    - SLOW_DRIFT_ADAPTATION
    - REGIME_REORIENTATION
    - DIMENSIONALITY_EXPANSION
    - MODEL_COLLAPSE
    - IDENTIFIABILITY_DEGRADED

Reference:
    Bocker, N. J. (2025). "Geometric Decomposition of Infinitesimal Motion:
    Evolving Spectral Subspaces on the Grassmann Manifold — The Leibniz-Bocker Framework"
    Bocker, N. J. (2025). "The Leibniz/Bocker Framework: Extended Diagnostics,
    Curvature Metrics, and Streaming Implementation"
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import scipy.linalg as la


class DiagnosticRegime(str, Enum):
    """Regime classifications from Section 6 of Leibniz-Bocker Extended (2025)."""
    STABLE_REGIME = "STABLE_REGIME"
    SLOW_DRIFT_ADAPTATION = "SLOW_DRIFT_ADAPTATION"
    REGIME_REORIENTATION = "REGIME_REORIENTATION"
    DIMENSIONALITY_EXPANSION = "DIMENSIONALITY_EXPANSION"
    MODEL_COLLAPSE = "MODEL_COLLAPSE"
    IDENTIFIABILITY_DEGRADED = "IDENTIFIABILITY_DEGRADED"


class SubspaceIdentifiability(str, Enum):
    """Davis-Kahan eigenspace identifiability classification."""
    IDENTIFIABLE = "IDENTIFIABLE"
    MARGINAL = "MARGINAL"
    NON_IDENTIFIABLE = "NON_IDENTIFIABLE"


@dataclass
class LeibnizBockerDiagnostics:
    """Diagnostic state computed at step t for increment phi(t)."""
    t: int
    step_label: str
    coherence: float
    speed_max_angle: float        # OMEGA_MAXANGLE: Grassmannian max-angle reorientation rate
    speed_projector: float        # OMEGA_PROJECTOR: Projector displacement rate
    residual_norm: float
    spectral_gap: float           # Absolute gap gamma_k = lambda_k - lambda_{k+1}
    instability_ratio: float      # 1 / gamma_k
    regime: DiagnosticRegime
    eigenvalues: List[float]
    principal_angles: List[float]
    residual_fraction: float
    relative_gap: float = 0.0     # gamma_tilde_k = gamma_k / (lambda_1 + eps)
    davis_kahan_ratio: float = 0.0 # D_k = ||Delta C_t||_2 / max(gamma_k, eps)
    identifiability: SubspaceIdentifiability = SubspaceIdentifiability.IDENTIFIABLE
    is_subspace_identifiable: bool = True
    kappa_g: float = 0.0          # Genuine second-order Grassmannian curvature (covariant acceleration)

    # Backwards-compatible properties
    @property
    def curvature_max_angle(self) -> float:
        return self.speed_max_angle

    @property
    def curvature_projector(self) -> float:
        return self.speed_projector

    @property
    def stability_ratio(self) -> float:
        return self.davis_kahan_ratio

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["regime"] = self.regime.value
        d["identifiability"] = self.identifiability.value
        d["curvature_max_angle"] = self.speed_max_angle
        d["curvature_projector"] = self.speed_projector
        d["stability_ratio"] = self.davis_kahan_ratio
        return d


class LeibnizBockerTracker:
    """Grassmannian subspace tracker and geometric diagnostics engine."""

    def __init__(
        self,
        k: int = 2,
        alpha: float = 0.5,
        dt: float = 1.0,
        regime_thresholds: Optional[Dict[str, float]] = None,
        oja_eta: float = 0.1,
        oja_constant_eta: bool = False,
    ) -> None:
        self.k = k
        self.alpha = alpha
        self.dt = dt
        self.oja_eta = oja_eta
        self.oja_constant_eta = oja_constant_eta
        self.thresholds = regime_thresholds or {
            "coherence_high": 0.70,
            "speed_low": 0.25,
            "speed_high": 0.70,
            "residual_high": 0.35,
            "tau_gamma": 0.01,
            "tau_relative_gap": 0.02,
            "tau_dk_identifiable": 0.75,
            "tau_dk_marginal": 1.50,
            # Backwards compatibility
            "curvature_low": 0.25,
            "curvature_high": 0.70,
        }
        self.C_prev: Optional[np.ndarray] = None
        self.E_prev: Optional[np.ndarray] = None
        self.P_prev: Optional[np.ndarray] = None
        self.V_prev: Optional[np.ndarray] = None  # Horizontal tangent velocity
        self.W_online: Optional[np.ndarray] = None  # Online Oja tracker frame

    def compute_eigenspace(
        self, C: np.ndarray, E_prev: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Eigendecomposition with descending sort and sign-alignment."""
        vals, vecs = la.eigh(C)
        idx = np.argsort(vals)[::-1]
        vals = np.maximum(vals[idx], 0.0)
        vecs = vecs[:, idx]

        E_k = vecs[:, : self.k].copy()

        # Sign-alignment to prevent 180-deg phase flips (Bocker 2025, Section 5)
        if E_prev is not None and E_prev.shape == E_k.shape:
            for j in range(self.k):
                dot = np.dot(E_prev[:, j], E_k[:, j])
                if dot < 0.0:
                    E_k[:, j] = -E_k[:, j]

        return vals, vecs, E_k

    def compute_principal_angles(
        self, E1: np.ndarray, E2: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """Principal angles between two k-dimensional subspaces via SVD of E1^T E2."""
        M = np.dot(E1.T, E2)
        _, s, _ = la.svd(M)
        s = np.clip(s, 0.0, 1.0)
        angles = np.arccos(s)
        max_angle = float(np.max(angles))
        return angles, max_angle

    def evaluate_identifiability(
        self, gap: float, lambda_1: float, norm_Delta_C: float, t: int
    ) -> Tuple[float, float, SubspaceIdentifiability, bool]:
        """Computes Davis-Kahan stability ratio D_k and classifies identifiability."""
        eps = 1e-12
        rel_gap = gap / (lambda_1 + eps)
        dk_ratio = norm_Delta_C / max(gap, eps)

        th = self.thresholds
        tau_gamma = th.get("tau_gamma", 0.01)
        tau_rel = th.get("tau_relative_gap", 0.02)
        tau_dk_id = th.get("tau_dk_identifiable", 0.75)
        tau_dk_marg = th.get("tau_dk_marginal", 1.50)

        if t == 0:
            return rel_gap, 0.0, SubspaceIdentifiability.IDENTIFIABLE, True

        if gap < tau_gamma or rel_gap < tau_rel or dk_ratio > tau_dk_marg:
            status = SubspaceIdentifiability.NON_IDENTIFIABLE
            is_id = False
        elif dk_ratio > tau_dk_id:
            status = SubspaceIdentifiability.MARGINAL
            is_id = True
        else:
            status = SubspaceIdentifiability.IDENTIFIABLE
            is_id = True

        return rel_gap, dk_ratio, status, is_id

    def classify_regime(
        self,
        coherence: float,
        speed: float,
        residual_fraction: float,
        is_subspace_identifiable: bool = True,
        t: int = 0,
    ) -> DiagnosticRegime:
        """Classifies the system regime according to the Leibniz-Bocker diagnostic table.
        
        Enforces Davis-Kahan identifiability gating: if eigenspace identifiability
        is degraded and speed is low, returns IDENTIFIABILITY_DEGRADED.
        """
        th = self.thresholds
        c_high = coherence >= th.get("coherence_high", 0.70)
        s_low = speed <= th.get("speed_low", th.get("curvature_low", 0.25))
        s_high = speed >= th.get("speed_high", th.get("curvature_high", 0.70))
        res_high = residual_fraction >= th.get("residual_high", 0.35)

        # 1. Structural reorientations and expansions take precedence
        if c_high and s_high and not res_high:
            return DiagnosticRegime.REGIME_REORIENTATION
        elif c_high and res_high:
            return DiagnosticRegime.DIMENSIONALITY_EXPANSION
        elif res_high and (s_high or not c_high):
            return DiagnosticRegime.MODEL_COLLAPSE

        # 2. Identifiability check: low speed + unidentifiable eigenspace cannot be STABLE_REGIME
        if not is_subspace_identifiable and t > 0:
            return DiagnosticRegime.IDENTIFIABILITY_DEGRADED

        # 3. Stable regime or slow drift
        if c_high and s_low and not res_high:
            return DiagnosticRegime.STABLE_REGIME
        else:
            return DiagnosticRegime.SLOW_DRIFT_ADAPTATION

    def step(
        self,
        phi_t: np.ndarray,
        step_label: str = "",
        t: int = 0,
    ) -> LeibnizBockerDiagnostics:
        """Processes one increment vector phi(t) = x(t+1) - x(t)."""
        phi_t = np.asarray(phi_t, dtype=float)
        N = len(phi_t)
        phi_norm_sq = float(np.dot(phi_t, phi_t))
        phi_norm = np.sqrt(phi_norm_sq)

        # Outer product increment covariance: C_inc = phi phi^T
        C_inc = np.outer(phi_t, phi_t)

        # Update covariance operator: Sigma_{t+1} = (1 - alpha) Sigma_t + alpha phi phi^T
        if self.C_prev is None:
            C_t = C_inc
            Delta_C = np.zeros_like(C_inc)
            norm_Delta_C = 0.0
        else:
            C_t = (1.0 - self.alpha) * self.C_prev + self.alpha * C_inc
            Delta_C = C_t - self.C_prev
            norm_Delta_C = float(la.norm(Delta_C, 2))

        vals, _, E_k = self.compute_eigenspace(C_t, self.E_prev)
        total_var = float(np.sum(vals)) + 1e-12
        k_var = float(np.sum(vals[: self.k]))
        coherence = k_var / total_var

        # Projector P_t = E_k E_k^T
        P_t = np.dot(E_k, E_k.T)

        # Decomposition of motion: phi(t) = E_k a(t) + r(t)
        a_t = np.dot(E_k.T, phi_t)
        proj_norm_sq = float(np.dot(a_t, a_t))
        res_sq = max(0.0, phi_norm_sq - proj_norm_sq)
        res_norm = np.sqrt(res_sq)
        res_fraction = res_norm / (phi_norm + 1e-12)

        # Spectral gap gamma_k = lambda_k - lambda_{k+1}
        lambda_1 = float(vals[0]) if len(vals) > 0 else 0.0
        if len(vals) > self.k:
            gap = float(vals[self.k - 1] - vals[self.k])
        else:
            gap = float(vals[self.k - 1])
        instability = 1.0 / (gap + 1e-9)

        # Davis-Kahan Subspace Identifiability
        rel_gap, dk_ratio, ident_status, is_identifiable = self.evaluate_identifiability(
            gap=gap, lambda_1=lambda_1, norm_Delta_C=norm_Delta_C, t=t
        )

        # Reorientation speeds & genuine Riemannian covariant acceleration (second-order curvature)
        if self.E_prev is None or self.P_prev is None:
            speed_max = 0.0
            speed_proj = 0.0
            kappa_g = 0.0
            angles = [0.0] * self.k
            self.V_prev = None
        else:
            p_angles, max_a = self.compute_principal_angles(self.E_prev, E_k)
            angles = [float(a) for a in p_angles]
            speed_max = max_a / self.dt
            speed_proj = float(la.norm(P_t - self.P_prev, "fro")) / self.dt

            # Grassmannian horizontal tangent velocity: V_t = (I - P_t) (E_k - E_prev) / dt
            I_minus_P = np.eye(N) - P_t
            V_t = np.dot(I_minus_P, (E_k - self.E_prev) / self.dt)

            if self.V_prev is None:
                kappa_g = 0.0
            else:
                # Covariant derivative along curve: nabla_{dot E} dot E ~ (I - P_t) (V_t - V_prev) / dt
                cov_accel = np.dot(I_minus_P, (V_t - self.V_prev) / self.dt)
                kappa_g = float(la.norm(cov_accel, "fro"))
            self.V_prev = V_t

        regime = self.classify_regime(
            coherence=coherence,
            speed=speed_max,
            residual_fraction=res_fraction,
            is_subspace_identifiable=is_identifiable,
            t=t,
        )

        # Online Oja tracker update (Section 4, Bocker Extended 2025):
        # Associative evaluation: phi (phi^T W_t) in O(N k) without forming N x N outer product
        if self.W_online is None:
            self.W_online = E_k.copy()
        else:
            # 1. v = phi^T W_t in R^k: O(N k)
            v = np.dot(phi_t, self.W_online)
            # 2. Ut = phi v in R^{N x k}: O(N k)
            Ut = np.outer(phi_t, v)
            if self.oja_constant_eta:
                eta = self.oja_eta
            else:
                eta = self.oja_eta / (1.0 + 0.05 * t)
            W_star = self.W_online + eta * Ut
            # 3. Economic QR orthonormalization: O(N k^2)
            q, _ = la.qr(W_star, mode="economic")
            self.W_online = q[:, : self.k]

        diag = LeibnizBockerDiagnostics(
            t=t,
            step_label=step_label,
            coherence=float(coherence),
            speed_max_angle=float(speed_max),
            speed_projector=float(speed_proj),
            residual_norm=float(res_norm),
            spectral_gap=float(gap),
            instability_ratio=float(instability),
            regime=regime,
            eigenvalues=[float(v) for v in vals[: min(N, 8)]],
            principal_angles=angles,
            residual_fraction=float(res_fraction),
            relative_gap=float(rel_gap),
            davis_kahan_ratio=float(dk_ratio),
            identifiability=ident_status,
            is_subspace_identifiable=bool(is_identifiable),
            kappa_g=float(kappa_g),
        )

        self.C_prev = C_t
        self.E_prev = E_k
        self.P_prev = P_t

        return diag


def compute_exact_batch_eigenspace(
    Phi: np.ndarray,
    k: int = 2,
    window: Optional[int] = None,
) -> List[np.ndarray]:
    """Computes exact batch eigendecomposition at each step t on sliding or cumulative window.
    
    Returns list of orthonormal bases E_k^batch(t) in St(k, N).
    """
    T, N = Phi.shape
    batch_bases: List[np.ndarray] = []
    for t in range(T):
        if window is None:
            # Cumulative window: all samples up to t
            window_phi = Phi[: t + 1]
        else:
            start = max(0, t - window + 1)
            window_phi = Phi[start : t + 1]
        
        # Exact empirical covariance C_batch = (1/M) sum phi phi^T
        C_batch = np.dot(window_phi.T, window_phi) / len(window_phi)
        vals, vecs = la.eigh(C_batch)
        idx = np.argsort(vals)[::-1]
        vecs = vecs[:, idx]
        E_batch = vecs[:, :k].copy()

        # Sign alignment relative to previous batch frame
        if len(batch_bases) > 0:
            E_prev = batch_bases[-1]
            for j in range(k):
                if np.dot(E_prev[:, j], E_batch[:, j]) < 0.0:
                    E_batch[:, j] = -E_batch[:, j]

        batch_bases.append(E_batch)
    return batch_bases


def compute_grassmann_distance(E1: np.ndarray, E2: np.ndarray) -> float:
    """Grassmannian geodesic distance between subspaces span(E1) and span(E2).
    
    d_Gr(E1, E2) = sqrt(sum_i theta_i^2)
    """
    M = np.dot(E1.T, E2)
    _, s, _ = la.svd(M)
    s = np.clip(s, 0.0, 1.0)
    thetas = np.arccos(s)
    return float(np.sqrt(np.sum(thetas ** 2)))


def compute_novelty_assimilation_time(
    states: np.ndarray,
    novelty_dim_indices: List[int],
    tau_r: float = 0.50,
    tau_speed: float = 0.25,
    min_coherence: float = 0.90,
    k: int = 2,
    alpha: float = 0.5,
    dt: float = 1.0,
    seconds_per_epoch: float = 600.0,
) -> Dict[str, Any]:
    """Mechanically computes novelty assimilation time tau_A from state observation timestamps.
    
    Definition:
        t_novelty: first transition whose state vectors observe the new dimensions.
        t_assimilated: first subsequent transition where residual, speed, and coherence satisfy normal mode criteria.
        tau_A = t_assimilated - t_novelty
    """
    states = np.asarray(states, dtype=float)
    if len(states) < 2:
        raise ValueError("At least 2 states required to evaluate transitions.")

    # 1. Identify first state where novelty dimensions become non-zero
    t_novelty_state = None
    for s_idx, state in enumerate(states):
        if any(abs(state[d]) > 1e-6 for d in novelty_dim_indices):
            t_novelty_state = s_idx
            break

    if t_novelty_state is None:
        return {
            "error": "NOVELTY_NOT_OBSERVED",
            "tau_A": None,
        }

    # First transition observing the novelty change
    t_novelty_transition = max(0, t_novelty_state - 1)

    # 2. Run tracker across state transitions
    Phi = np.diff(states, axis=0)
    tracker = LeibnizBockerTracker(k=k, alpha=alpha, dt=dt)
    diagnostics: List[LeibnizBockerDiagnostics] = []

    t_assimilated_transition = None
    for t_idx, phi in enumerate(Phi):
        diag = tracker.step(phi, step_label=f"trans_{t_idx}", t=t_idx)
        diagnostics.append(diag)
        if t_idx > t_novelty_transition and t_assimilated_transition is None:
            if (
                diag.residual_norm < tau_r
                and diag.speed_max_angle < tau_speed
                and diag.coherence >= min_coherence
            ):
                t_assimilated_transition = t_idx

    tau_A = (
        (t_assimilated_transition - t_novelty_transition)
        if t_assimilated_transition is not None
        else None
    )

    elapsed_seconds = (tau_A * seconds_per_epoch) if tau_A is not None else None

    return {
        "novelty_transition_index": t_novelty_transition,
        "novelty_observation_time": f"Epoch {t_novelty_state:02d}",
        "assimilation_transition_index": t_assimilated_transition,
        "assimilation_observation_time": (
            f"Epoch {t_assimilated_transition + 1:02d}"
            if t_assimilated_transition is not None
            else None
        ),
        "tau_A_transitions": tau_A,
        "elapsed_seconds": elapsed_seconds,
        "diagnostics": diagnostics,
    }
