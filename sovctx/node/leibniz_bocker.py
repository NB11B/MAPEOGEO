"""The Leibniz-Bocker Framework: Spectral Subspace Geometry on Grassmann Manifolds.

Formalizes the geometric decomposition of infinitesimal motion:
    phi(t) = x(t+1) - x(t)
    C(t) = E[phi phi^T]
    E_k(t) in Gr(k, N)

Decomposes motion into:
    phi(t) = E_k(t) a(t) + r(t)
    where a(t) = E_k(t)^T phi(t) are harmonic coordinates
    and r(t) is orthogonal residual novelty.

Tracks the Diagnostic Trinity:
    1. Coherence rho_k(t): variance concentration in leading k modes
    2. Curvature Omega_k(t): rate of dominant subspace rotation (principal angles)
    3. Projector Curvature Omega_tilde_k(t): Frobenius rate of projector evolution
    4. Residual norm ||r_k(t)||: novelty outside dominant subspace
    5. Spectral gap gamma_k(t): stability and degeneracy indicator

Includes streaming online Oja-style subspace tracker and autonomous regime classifier:
    - STABLE_REGIME
    - SLOW_DRIFT_ADAPTATION
    - REGIME_REORIENTATION
    - DIMENSIONALITY_EXPANSION
    - MODEL_COLLAPSE

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


@dataclass
class LeibnizBockerDiagnostics:
    """Diagnostic state computed at step t for increment phi(t)."""
    t: int
    step_label: str
    coherence: float
    curvature_max_angle: float
    curvature_projector: float
    residual_norm: float
    spectral_gap: float
    instability_ratio: float
    regime: DiagnosticRegime
    eigenvalues: List[float]
    principal_angles: List[float]
    residual_fraction: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["regime"] = self.regime.value
        return d


class LeibnizBockerTracker:
    """Grassmannian subspace tracker and geometric diagnostics engine."""

    def __init__(
        self,
        k: int = 2,
        alpha: float = 0.5,
        dt: float = 1.0,
        regime_thresholds: Optional[Dict[str, float]] = None,
    ) -> None:
        self.k = k
        self.alpha = alpha
        self.dt = dt
        self.thresholds = regime_thresholds or {
            "coherence_high": 0.70,
            "curvature_low": 0.25,
            "curvature_high": 0.70,
            "residual_high": 0.35,
        }
        self.C_prev: Optional[np.ndarray] = None
        self.E_prev: Optional[np.ndarray] = None
        self.P_prev: Optional[np.ndarray] = None
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

    def classify_regime(
        self, coherence: float, curvature: float, residual_fraction: float
    ) -> DiagnosticRegime:
        """Classifies the system regime according to the Leibniz-Bocker diagnostic table."""
        th = self.thresholds
        c_high = coherence >= th["coherence_high"]
        curv_low = curvature <= th["curvature_low"]
        curv_high = curvature >= th["curvature_high"]
        res_high = residual_fraction >= th["residual_high"]

        if c_high and curv_low and not res_high:
            return DiagnosticRegime.STABLE_REGIME
        elif c_high and not curv_high and not res_high:
            return DiagnosticRegime.SLOW_DRIFT_ADAPTATION
        elif c_high and curv_high and not res_high:
            return DiagnosticRegime.REGIME_REORIENTATION
        elif c_high and res_high:
            return DiagnosticRegime.DIMENSIONALITY_EXPANSION
        else:
            if res_high and (curv_high or not c_high):
                return DiagnosticRegime.MODEL_COLLAPSE
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
        else:
            C_t = (1.0 - self.alpha) * self.C_prev + self.alpha * C_inc

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
        if len(vals) > self.k:
            gap = float(vals[self.k - 1] - vals[self.k])
        else:
            gap = float(vals[self.k - 1])
        instability = 1.0 / (gap + 1e-9)

        # Curvature metrics
        if self.E_prev is None or self.P_prev is None:
            omega_max = 0.0
            omega_proj = 0.0
            angles = [0.0] * self.k
        else:
            p_angles, max_a = self.compute_principal_angles(self.E_prev, E_k)
            angles = [float(a) for a in p_angles]
            omega_max = max_a / self.dt

            # Projector curvature ||P_{t+dt} - P_t||_F / dt
            omega_proj = float(la.norm(P_t - self.P_prev, "fro")) / self.dt

        regime = self.classify_regime(coherence, omega_max, res_fraction)

        # Online Oja tracker update (Section 4, Bocker Extended 2025):
        # Ut = phi phi^T W_t, W_{t+1}^* = W_t + eta Ut, W_{t+1} = qr(W_{t+1}^*)
        if self.W_online is None:
            self.W_online = E_k.copy()
        else:
            Ut = np.dot(C_inc, self.W_online)
            eta = 0.1 / (1.0 + 0.05 * t)
            W_star = self.W_online + eta * Ut
            q, _ = la.qr(W_star, mode="economic")
            self.W_online = q[:, : self.k]

        diag = LeibnizBockerDiagnostics(
            t=t,
            step_label=step_label,
            coherence=float(coherence),
            curvature_max_angle=float(omega_max),
            curvature_projector=float(omega_proj),
            residual_norm=float(res_norm),
            spectral_gap=float(gap),
            instability_ratio=float(instability),
            regime=regime,
            eigenvalues=[float(v) for v in vals[: min(N, 6)]],
            principal_angles=angles,
            residual_fraction=float(res_fraction),
        )

        self.C_prev = C_t
        self.E_prev = E_k
        self.P_prev = P_t

        return diag
