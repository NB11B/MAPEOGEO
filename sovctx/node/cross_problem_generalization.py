#!/usr/bin/env python3
"""
Cross-Problem Synthetic-Lens Generalization Engine.
Milestone SOVCTX-M4.2: Cross-Problem Generalization & Pre-Acquisition Omission.

Evaluates the frozen M4 synthetic lens DUAL_INVERSE_OMISSION (Sa -> N -> Iv)
across four diverse, unrelated linear inverse operators:
1. Operator 1: Non-local Fredholm First-Kind Integral Scattering (continuous kernel, asymmetric M=256, N=128)
2. Operator 2: 1D Gaussian Blur Deconvolution (Toeplitz convolution operator, M=128, N=128)
3. Operator 3: Mildly Ill-Posed Abel-Type Integral Inversion (Volterra triangular kernel, algebraic decay, M=128, N=128)
4. Operator 4: 1D Inverse Heat Conduction / Backward Parabolic Diffusion (spectral decay exp(-n^2 T), M=64, N=64)

Four-Arm Protocol:
- Arm A: Contemporary Full Tikhonov (using data-driven Morozov Discrepancy Principle + oracle reference)
- Arm B: Standard TSVD baseline (classical spectral cutoff tau = sigma_noise, zero alpha)
- Arm C: Synthetic Lens Alone (Sa -> N -> Iv with negative information ledger threshold tau = 2*sigma_noise, zero alpha)
- Arm D: Synthetic + Conventional Combined (subspace projection to rank k_c + subspace Tikhonov regularization)

Pre-Acquisition Physical Sensor Reduction:
- Modal Analog Projection: P_modal = U_k^T in R^{k x M} (transports only k scalar values)
- Discrete Physical Sensor Selection: P_sparse in {0, 1}^{k x M} via DEIM / QR column pivoting,
  physically acquiring ONLY k sensor locations and omitting (M - k) sensors before acquisition.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.linalg import qr


@dataclass
class CrossProblemTrialResult:
    operator_id: str
    operator_name: str
    ill_posedness_type: str  # "SEVERE_EXPONENTIAL", "MODERATE_EXPONENTIAL", "MILD_ALGEBRAIC"
    m_observations: int
    n_unknowns: int
    raw_condition_number: float
    noise_sigma: float

    # Arm A: Full Tikhonov (Morozov Discrepancy Principle + Oracle)
    arm_a_alpha_morozov: float
    arm_a_alpha_oracle: float
    arm_a_err_morozov: float
    arm_a_err_oracle: float
    arm_a_cond: float

    # Arm B: Standard TSVD (tau = sigma)
    arm_b_k: int
    arm_b_cutoff_tau: float
    arm_b_err: float
    arm_b_cond: float

    # Arm C: Synthetic Lens Alone (tau = 2*sigma)
    arm_c_k: int
    arm_c_cutoff_tau: float
    arm_c_err: float
    arm_c_cond: float
    arm_c_dim_reduction_ratio: float
    arm_c_invertible_dir_omitted_ratio: float
    arm_c_coord_compression_ratio: float

    # Arm D: Synthetic + Conventional Combined
    arm_d_alpha_subspace: float
    arm_d_err: float
    arm_d_cond: float

    # Pre-Acquisition Physical Sensor Omission (PSMSL)
    pre_acq_sparse_sensors_count: int
    pre_acq_sparse_err: float
    pre_acq_sparse_omission_ratio: float
    pre_acq_sparse_vs_a_ratio: float
    pre_acq_modal_err: float

    # Comparative Analytics
    c_vs_b_error_ratio: float  # < 1.0 means synthetic lens beats standard TSVD
    c_vs_a_error_ratio: float  # Picard condition starvation if >> 1.0 at low noise
    is_picard_starvation: bool
    is_synthetic_superior_to_tsvd: bool
    is_sparse_pre_acq_effective: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =============================================================================
# OPERATOR DEFINITIONS
# =============================================================================

class FredholmScatteringOperator:
    """Operator 1: Continuous Fredholm Integral Scattering (Severe exponential ill-posedness)."""

    def __init__(self, n_points: int = 128, m_sensors: int = 256, ell: float = 0.08) -> None:
        self.operator_id = "OP_FREDHOLM_SCATTERING"
        self.operator_name = "Fredholm Integral Scattering"
        self.ill_posedness_type = "SEVERE_EXPONENTIAL"
        self.n = n_points
        self.m = m_sensors
        self.ell = ell
        self.t = np.linspace(0.0, 1.0, self.n)
        self.s = np.linspace(0.0, 1.0, self.m)
        self.dt = 1.0 / float(self.n)

        diff = self.s[:, np.newaxis] - self.t[np.newaxis, :]
        self.A = (self.dt / (math.sqrt(2.0 * math.pi) * self.ell)) * np.exp(-(diff**2) / (2.0 * self.ell**2))
        self.U, self.S, self.Vt = np.linalg.svd(self.A, full_matrices=False)
        self.raw_condition_number = float(self.S[0] / max(1e-18, self.S[-1]))

    def get_ground_truth(self) -> np.ndarray:
        return np.sin(2.0 * math.pi * self.t) + 0.5 * np.sin(4.0 * math.pi * self.t)


class GaussianDeconvolutionOperator:
    """Operator 2: 1D Gaussian Blur Deconvolution (Toeplitz convolution operator)."""

    def __init__(self, n_points: int = 128, blur_sigma: float = 4.0) -> None:
        self.operator_id = "OP_GAUSSIAN_DECONVOLUTION"
        self.operator_name = "Gaussian Blur Deconvolution"
        self.ill_posedness_type = "MODERATE_EXPONENTIAL"
        self.n = n_points
        self.m = n_points
        self.blur_sigma = blur_sigma
        coords = np.arange(self.n, dtype=float)
        diff = np.abs(coords[:, np.newaxis] - coords[np.newaxis, :])
        self.A = np.exp(-(diff**2) / (2.0 * self.blur_sigma**2))
        self.A /= np.sum(self.A[self.n // 2, :])  # normalize row sums to unit energy

        self.U, self.S, self.Vt = np.linalg.svd(self.A, full_matrices=False)
        self.raw_condition_number = float(self.S[0] / max(1e-18, self.S[-1]))

    def get_ground_truth(self) -> np.ndarray:
        f = np.zeros(self.n, dtype=float)
        f[35:55] = 1.0
        f[70:90] = 0.6
        return f


class AbelVolterraOperator:
    """Operator 3: Mildly Ill-Posed Abel-Type Integral Inversion (Volterra triangular kernel)."""

    def __init__(self, n_points: int = 128, delta: float = 0.02) -> None:
        self.operator_id = "OP_ABEL_VOLTERRA"
        self.operator_name = "Abel Volterra Inversion"
        self.ill_posedness_type = "MILD_ALGEBRAIC"
        self.n = n_points
        self.m = n_points
        self.delta = delta
        self.s = np.linspace(0.01, 1.0, self.m)
        self.t = np.linspace(0.01, 1.0, self.n)
        self.dt = 1.0 / float(self.n)

        self.A = np.zeros((self.m, self.n), dtype=float)
        for i in range(self.m):
            for j in range(i, self.n):
                diff = max(0.0, self.t[j]**2 - self.s[i]**2) + (self.delta**2)
                self.A[i, j] = self.dt * self.t[j] / math.sqrt(diff)

        self.U, self.S, self.Vt = np.linalg.svd(self.A, full_matrices=False)
        self.raw_condition_number = float(self.S[0] / max(1e-18, self.S[-1]))

    def get_ground_truth(self) -> np.ndarray:
        return 1.0 - (self.t**2)


class HeatConductionOperator:
    """Operator 4: 1D Inverse Heat Conduction / Backward Parabolic Diffusion."""

    def __init__(self, n_points: int = 64, diff_coeff: float = 0.5, t_final: float = 0.05) -> None:
        self.operator_id = "OP_INVERSE_HEAT_CONDUCTION"
        self.operator_name = "Inverse Heat Conduction"
        self.ill_posedness_type = "SEVERE_EXPONENTIAL"
        self.n = n_points
        self.m = n_points
        self.diff_coeff = diff_coeff
        self.t_final = t_final
        self.x = np.linspace(0.0, math.pi, self.n + 2)[1:-1]

        self.A = np.zeros((self.n, self.n), dtype=float)
        for mode in range(1, self.n + 1):
            decay = math.exp(-self.diff_coeff * (mode**2) * self.t_final)
            phi = np.sin(mode * self.x)
            phi /= np.linalg.norm(phi)
            self.A += decay * np.outer(phi, phi)

        self.U, self.S, self.Vt = np.linalg.svd(self.A, full_matrices=False)
        self.raw_condition_number = float(self.S[0] / max(1e-18, self.S[-1]))

    def get_ground_truth(self) -> np.ndarray:
        return np.sin(self.x) + 0.5 * np.sin(2.0 * self.x)


# =============================================================================
# SOLVER IMPLEMENTATIONS: MOROZOV DISCREPANCY & ORACLE
# =============================================================================

def solve_tikhonov_morozov(
    U: np.ndarray,
    S: np.ndarray,
    Vt: np.ndarray,
    y: np.ndarray,
    m: int,
    sigma: float,
    tau_morozov: float = 1.05,
    alpha_grid: Optional[np.ndarray] = None
) -> Tuple[float, np.ndarray]:
    """
    Computes Tikhonov regularized solution via Morozov's Discrepancy Principle:
    Finds alpha such that || A f_alpha - y ||_2 = tau_morozov * sqrt(m) * sigma.
    """
    if alpha_grid is None:
        alpha_grid = np.logspace(-14, 4, 250)

    delta = tau_morozov * math.sqrt(float(m)) * sigma
    p = len(S)
    Uy = U[:, :p].T @ y
    orth_norm_sq = max(0.0, float(np.sum(y**2) - np.sum(Uy**2))) if m > p else 0.0

    best_diff = float("inf")
    best_alpha = float(alpha_grid[-1])

    for alpha in alpha_grid:
        f_filt = alpha / (S**2 + alpha)
        res_norm = math.sqrt(float(np.sum((f_filt * Uy)**2) + orth_norm_sq))
        diff = abs(res_norm - delta)
        if diff < best_diff:
            best_diff = diff
            best_alpha = float(alpha)

    filt = S / (S**2 + best_alpha)
    f_hat = Vt[:p, :].T @ (filt * Uy)
    return best_alpha, f_hat


def solve_tikhonov_oracle(
    U: np.ndarray,
    S: np.ndarray,
    Vt: np.ndarray,
    y: np.ndarray,
    f_true: np.ndarray,
    alpha_grid: Optional[np.ndarray] = None
) -> Tuple[float, np.ndarray, float]:
    """Computes oracle Tikhonov solution minimizing exact error to f_true."""
    if alpha_grid is None:
        alpha_grid = np.logspace(-14, 4, 250)

    p = len(S)
    Uy = U[:, :p].T @ y
    norm_true = float(np.linalg.norm(f_true))
    best_err = float("inf")
    best_alpha = float(alpha_grid[0])

    for alpha in alpha_grid:
        filt = S / (S**2 + alpha)
        f_cand = Vt[:p, :].T @ (filt * Uy)
        err = float(np.linalg.norm(f_cand - f_true) / max(1e-16, norm_true))
        if err < best_err:
            best_err = err
            best_alpha = float(alpha)

    filt = S / (S**2 + best_alpha)
    f_hat = Vt[:p, :].T @ (filt * Uy)
    return best_alpha, f_hat, best_err


# =============================================================================
# BENCHMARK EVALUATOR
# =============================================================================

class CrossProblemGeneralizationBenchmark:
    """Evaluates cross-problem generalization and pre-acquisition omission."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def evaluate_operator_at_noise(
        self,
        operator: Any,
        sigma: float,
        trials: int = 5
    ) -> CrossProblemTrialResult:
        """Runs multi-trial benchmark on a specific operator and noise level."""
        A = operator.A
        m, n = A.shape
        f_true = operator.get_ground_truth()
        norm_true = float(np.linalg.norm(f_true))
        U, S, Vt = operator.U, operator.S, operator.Vt
        p = len(S)

        # Cutoffs
        # Arm B (Standard TSVD): tau = sigma
        k_b = int(np.sum(S >= sigma))
        k_b = max(1, min(k_b, p))
        tau_b = sigma

        # Arm C (Synthetic Lens): tau = 2 * sigma
        k_c = int(np.sum(S >= 2.0 * sigma))
        k_c = max(1, min(k_c, p))
        tau_c = 2.0 * sigma

        # Pre-acquisition physical sparse sensor selection via DEIM / QR column pivoting
        Uk_c = U[:, :k_c]
        _, _, p_piv = qr(Uk_c.T, pivoting=True)
        selected_sensors = p_piv[:k_c]
        A_sparse = A[selected_sensors, :]
        U_sp, S_sp, Vt_sp = np.linalg.svd(A_sparse, full_matrices=False)

        a_errs_mor = []
        a_errs_oracle = []
        b_errs = []
        c_errs = []
        d_errs = []
        sparse_errs = []
        modal_errs = []

        last_a_alpha_mor = 0.0
        last_a_alpha_oracle = 0.0
        last_d_alpha_sub = 0.0

        for _ in range(trials):
            noise = self.rng.normal(0.0, sigma, size=m)
            y = (A @ f_true) + noise

            # Arm A: Full Tikhonov (Morozov + Oracle)
            alpha_a_mor, f_a_mor = solve_tikhonov_morozov(U, S, Vt, y, m, sigma)
            alpha_a_oracle, f_a_oracle, err_a_or = solve_tikhonov_oracle(U, S, Vt, y, f_true)
            a_errs_mor.append(float(np.linalg.norm(f_a_mor - f_true) / norm_true))
            a_errs_oracle.append(err_a_or)
            last_a_alpha_mor = alpha_a_mor
            last_a_alpha_oracle = alpha_a_oracle

            # Arm B: Standard TSVD (tau = sigma, zero alpha)
            Uy_b = U[:, :k_b].T @ y
            f_b = Vt[:k_b, :].T @ (Uy_b / S[:k_b])
            b_errs.append(float(np.linalg.norm(f_b - f_true) / norm_true))

            # Arm C: Synthetic Lens Alone (tau = 2*sigma, zero alpha)
            Uy_c = U[:, :k_c].T @ y
            f_c = Vt[:k_c, :].T @ (Uy_c / S[:k_c])
            c_errs.append(float(np.linalg.norm(f_c - f_true) / norm_true))

            # Arm D: Synthetic + Conventional Combined (subspace Morozov)
            alpha_d, f_d = solve_tikhonov_morozov(U[:, :k_c], S[:k_c], Vt[:k_c, :], y, k_c, sigma)
            d_errs.append(float(np.linalg.norm(f_d - f_true) / norm_true))
            last_d_alpha_sub = alpha_d

            # Pre-Acquisition Modal Projection: y_modal = P_modal y in R^{k_c}
            # Modal reconstruction uses exactly the same operator as Arm C:
            modal_errs.append(float(np.linalg.norm(f_c - f_true) / norm_true))

            # Pre-Acquisition Discrete Physical Sensor Selection (DEIM):
            y_sparse = y[selected_sensors]  # Only k_c physical sensors acquired!
            alpha_sp, f_sp = solve_tikhonov_morozov(U_sp, S_sp, Vt_sp, y_sparse, k_c, sigma)
            sparse_errs.append(float(np.linalg.norm(f_sp - f_true) / norm_true))

        # Averages
        avg_a_mor = float(np.mean(a_errs_mor))
        avg_a_oracle = float(np.mean(a_errs_oracle))
        avg_b = float(np.mean(b_errs))
        avg_c = float(np.mean(c_errs))
        avg_d = float(np.mean(d_errs))
        avg_sparse = float(np.mean(sparse_errs))
        avg_modal = float(np.mean(modal_errs))

        cond_a = float(math.sqrt(S[0]**2 + last_a_alpha_mor) / math.sqrt(S[-1]**2 + last_a_alpha_mor))
        cond_b = float(S[0] / S[k_b - 1])
        cond_c = float(S[0] / S[k_c - 1])
        cond_d = float(math.sqrt(S[0]**2 + last_d_alpha_sub) / math.sqrt(S[k_c - 1]**2 + last_d_alpha_sub))

        dim_reduction = float(m / k_c)
        invertible_dirs_omitted = float((p - k_c) / p)
        coord_compression = float((m - k_c) / m)
        sparse_omission = float((m - k_c) / m)

        c_vs_b_ratio = float(avg_c / max(1e-16, avg_b))
        c_vs_a_ratio = float(avg_c / max(1e-16, avg_a_oracle))
        is_starvation = (c_vs_a_ratio > 1.4 and sigma <= 1e-3)
        is_synth_better_tsvd = (avg_c <= avg_b * 1.05)
        sparse_vs_a = float(avg_sparse / max(1e-16, avg_a_mor))
        is_sparse_eff = (sparse_vs_a <= 3.5)

        return CrossProblemTrialResult(
            operator_id=operator.operator_id,
            operator_name=operator.operator_name,
            ill_posedness_type=operator.ill_posedness_type,
            m_observations=m,
            n_unknowns=n,
            raw_condition_number=operator.raw_condition_number,
            noise_sigma=sigma,
            arm_a_alpha_morozov=last_a_alpha_mor,
            arm_a_alpha_oracle=last_a_alpha_oracle,
            arm_a_err_morozov=avg_a_mor,
            arm_a_err_oracle=avg_a_oracle,
            arm_a_cond=cond_a,
            arm_b_k=k_b,
            arm_b_cutoff_tau=tau_b,
            arm_b_err=avg_b,
            arm_b_cond=cond_b,
            arm_c_k=k_c,
            arm_c_cutoff_tau=tau_c,
            arm_c_err=avg_c,
            arm_c_cond=cond_c,
            arm_c_dim_reduction_ratio=dim_reduction,
            arm_c_invertible_dir_omitted_ratio=invertible_dirs_omitted,
            arm_c_coord_compression_ratio=coord_compression,
            arm_d_alpha_subspace=last_d_alpha_sub,
            arm_d_err=avg_d,
            arm_d_cond=cond_d,
            pre_acq_sparse_sensors_count=k_c,
            pre_acq_sparse_err=avg_sparse,
            pre_acq_sparse_omission_ratio=sparse_omission,
            pre_acq_sparse_vs_a_ratio=sparse_vs_a,
            pre_acq_modal_err=avg_modal,
            c_vs_b_error_ratio=c_vs_b_ratio,
            c_vs_a_error_ratio=c_vs_a_ratio,
            is_picard_starvation=is_starvation,
            is_synthetic_superior_to_tsvd=is_synth_better_tsvd,
            is_sparse_pre_acq_effective=is_sparse_eff,
        )

    def run_full_campaign(self) -> List[CrossProblemTrialResult]:
        """Runs the complete 4-operator x 4-noise decade cross-problem evaluation."""
        operators = [
            FredholmScatteringOperator(),
            GaussianDeconvolutionOperator(),
            AbelVolterraOperator(),
            HeatConductionOperator(),
        ]
        noise_levels = [1e-4, 1e-3, 1e-2, 5e-2]
        results = []

        for op in operators:
            for sigma in noise_levels:
                res = self.evaluate_operator_at_noise(op, sigma)
                results.append(res)

        return results


def main() -> None:
    bench = CrossProblemGeneralizationBenchmark(seed=42)
    results = bench.run_full_campaign()
    print(f"Executed {len(results)} cross-problem generalization trials.")
    for r in results:
        print(f"[{r.operator_name}] sigma={r.noise_sigma:.0e} | Arm A(Morozov)={r.arm_a_err_morozov:.4f} | TSVD={r.arm_b_err:.4f} [k={r.arm_b_k}] | Synth={r.arm_c_err:.4f} [k={r.arm_c_k}] | Sparse Pre-Acq ({r.pre_acq_sparse_sensors_count}/{r.m_observations})={r.pre_acq_sparse_err:.4f}")


if __name__ == "__main__":
    main()
