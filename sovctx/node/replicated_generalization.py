#!/usr/bin/env python3
"""
Replicated Cross-Problem Synthetic-Lens Generalization Engine.
Milestone SOVCTX-M4.2R: Statistical Replication & Cutoff Multiplier Sweep.

Executes a large-sample Monte Carlo evaluation across 16 operator/noise regimes:
- 4 Operators: Fredholm Scattering, Gaussian Blur Deconvolution, Abel Volterra Inversion, Inverse Heat Conduction.
- 4 Noise Decades: sigma in {1e-4, 1e-3, 1e-2, 5e-2}.
- N_mc = 100 independent noise realizations per regime (1,600 total trial solves).

Statistical Metrics Reported:
- Expected relative error: E[Error]
- Median relative error: median(Error)
- 95% Confidence Intervals: [q_0.025, q_0.975]
- Empirical superiority probabilities:
  * P(E_C < E_B): Probability Synthetic Lens (tau = 2*sigma) beats Standard TSVD (tau = sigma)
  * P(E_D < E_A): Probability Combined Subspace Treatment beats Full Tikhonov
  * P(E_C < E_A): Probability Synthetic Lens alone beats Full Tikhonov

Cutoff Multiplier Sweep:
- Evaluates tau(c) = c * sigma for c in [0.5, 4.0] (grid of 8 multipliers).
- Maps empirical optimal multiplier c_opt = argmin_c E[Error(c)].
- Tests whether c_opt consistently clusters around c ~= 2.0 or varies with operator decay geometry.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.linalg import qr

from sovctx.node.cross_problem_generalization import (
    AbelVolterraOperator,
    FredholmScatteringOperator,
    GaussianDeconvolutionOperator,
    HeatConductionOperator,
    solve_tikhonov_morozov,
    solve_tikhonov_oracle,
)


@dataclass
class ReplicatedRegimeResult:
    operator_id: str
    operator_name: str
    ill_posedness_type: str
    noise_sigma: float
    m_observations: int
    n_unknowns: int
    n_mc_samples: int

    # Arm A: Full Tikhonov (Morozov)
    mean_err_a: float
    median_err_a: float
    ci95_low_a: float
    ci95_high_a: float

    # Arm B: Standard TSVD (tau = 1.0 * sigma)
    k_b: int
    mean_err_b: float
    median_err_b: float
    ci95_low_b: float
    ci95_high_b: float

    # Arm C: Synthetic Lens Alone (tau = 2.0 * sigma)
    k_c: int
    mean_err_c: float
    median_err_c: float
    ci95_low_c: float
    ci95_high_c: float
    dim_reduction_ratio: float
    simulated_sensor_omission_ratio: float

    # Arm D: Synthetic + Conventional Combined
    mean_err_d: float
    median_err_d: float
    ci95_low_d: float
    ci95_high_d: float

    # Pre-Acquisition Sparse Physical Selection (DEIM in simulation)
    k_sensors_sparse: int
    mean_err_sparse: float
    median_err_sparse: float
    ci95_low_sparse: float
    ci95_high_sparse: float

    # Empirical Probabilities
    p_c_beats_b: float  # P(E_C < E_B)
    p_d_beats_a: float  # P(E_D < E_A)
    p_c_beats_a: float  # P(E_C < E_A)

    # Cutoff Sweep Analytics: c in [0.5, 4.0]
    c_grid: List[float]
    c_sweep_means: Dict[float, float]
    optimal_c: float
    optimal_c_err: float
    is_c_opt_near_two: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReplicatedGeneralizationBenchmark:
    """Executes N_mc replicated Monte Carlo runs across all 16 regimes and sweeps cutoff multipliers."""

    def __init__(self, n_mc: int = 100, seed: int = 42) -> None:
        self.n_mc = n_mc
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.c_grid = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

    def evaluate_regime(
        self,
        operator: Any,
        sigma: float
    ) -> ReplicatedRegimeResult:
        A = operator.A
        m, n = A.shape
        f_true = operator.get_ground_truth()
        norm_true = float(np.linalg.norm(f_true))
        U, S, Vt = operator.U, operator.S, operator.Vt
        p = len(S)

        # Baseline cutoffs
        k_b = max(1, min(int(np.sum(S >= 1.0 * sigma)), p))
        k_c = max(1, min(int(np.sum(S >= 2.0 * sigma)), p))

        # Pre-acquisition sparse sensors via DEIM (greedy pivoted QR on top k_c modes)
        Uk_c = U[:, :k_c]
        _, _, p_piv = qr(Uk_c.T, pivoting=True)
        selected_sensors = p_piv[:k_c]
        A_sp = A[selected_sensors, :]
        U_sp, S_sp, Vt_sp = np.linalg.svd(A_sp, full_matrices=False)

        errs_a = []
        errs_b = []
        errs_c = []
        errs_d = []
        errs_sp = []
        sweep_errs = {c: [] for c in self.c_grid}

        for _ in range(self.n_mc):
            noise = self.rng.normal(0.0, sigma, size=m)
            y = (A @ f_true) + noise

            # Arm A: Full Tikhonov (Morozov)
            _, f_a = solve_tikhonov_morozov(U, S, Vt, y, m, sigma)
            err_a = float(np.linalg.norm(f_a - f_true) / norm_true)
            errs_a.append(err_a)

            # Arm B: Standard TSVD (tau = 1.0 * sigma)
            Uy_b = U[:, :k_b].T @ y
            f_b = Vt[:k_b, :].T @ (Uy_b / S[:k_b])
            err_b = float(np.linalg.norm(f_b - f_true) / norm_true)
            errs_b.append(err_b)

            # Arm C: Synthetic Lens Alone (tau = 2.0 * sigma)
            Uy_c = U[:, :k_c].T @ y
            f_c = Vt[:k_c, :].T @ (Uy_c / S[:k_c])
            err_c = float(np.linalg.norm(f_c - f_true) / norm_true)
            errs_c.append(err_c)

            # Arm D: Synthetic + Conventional Combined
            _, f_d = solve_tikhonov_morozov(U[:, :k_c], S[:k_c], Vt[:k_c, :], y, k_c, sigma)
            err_d = float(np.linalg.norm(f_d - f_true) / norm_true)
            errs_d.append(err_d)

            # Simulated Pre-Acquisition Sparse Point Sampling
            y_sp = y[selected_sensors]
            _, f_sp = solve_tikhonov_morozov(U_sp, S_sp, Vt_sp, y_sp, k_c, sigma)
            err_sp = float(np.linalg.norm(f_sp - f_true) / norm_true)
            errs_sp.append(err_sp)

            # Cutoff Multiplier Sweep: tau = c * sigma
            for c in self.c_grid:
                kc_val = max(1, min(int(np.sum(S >= c * sigma)), p))
                Uy_val = U[:, :kc_val].T @ y
                f_val = Vt[:kc_val, :].T @ (Uy_val / S[:kc_val])
                err_val = float(np.linalg.norm(f_val - f_true) / norm_true)
                sweep_errs[c].append(err_val)

        # Statistics
        def calc_stats(vals: List[float]) -> Tuple[float, float, float, float]:
            arr = np.array(vals)
            mean_v = float(np.mean(arr))
            med_v = float(np.median(arr))
            q_low = float(np.percentile(arr, 2.5))
            q_high = float(np.percentile(arr, 97.5))
            return mean_v, med_v, q_low, q_high

        mean_a, med_a, q_low_a, q_high_a = calc_stats(errs_a)
        mean_b, med_b, q_low_b, q_high_b = calc_stats(errs_b)
        mean_c, med_c, q_low_c, q_high_c = calc_stats(errs_c)
        mean_d, med_d, q_low_d, q_high_d = calc_stats(errs_d)
        mean_sp, med_sp, q_low_sp, q_high_sp = calc_stats(errs_sp)

        # Probabilities
        p_c_lt_b = float(np.mean([c < b for c, b in zip(errs_c, errs_b)]))
        p_d_lt_a = float(np.mean([d < a for d, a in zip(errs_d, errs_a)]))
        p_c_lt_a = float(np.mean([c < a for c, a in zip(errs_c, errs_a)]))

        # Sweep averages
        c_means = {c: float(np.mean(sweep_errs[c])) for c in self.c_grid}
        opt_c = min(c_means, key=lambda k: c_means[k])
        opt_c_err = c_means[opt_c]
        is_near_two = (1.5 <= opt_c <= 3.0)

        dim_red = float(m / k_c)
        sim_omit = float((m - k_c) / m)

        return ReplicatedRegimeResult(
            operator_id=operator.operator_id,
            operator_name=operator.operator_name,
            ill_posedness_type=operator.ill_posedness_type,
            noise_sigma=sigma,
            m_observations=m,
            n_unknowns=n,
            n_mc_samples=self.n_mc,
            mean_err_a=mean_a,
            median_err_a=med_a,
            ci95_low_a=q_low_a,
            ci95_high_a=q_high_a,
            k_b=k_b,
            mean_err_b=mean_b,
            median_err_b=med_b,
            ci95_low_b=q_low_b,
            ci95_high_b=q_high_b,
            k_c=k_c,
            mean_err_c=mean_c,
            median_err_c=med_c,
            ci95_low_c=q_low_c,
            ci95_high_c=q_high_c,
            dim_reduction_ratio=dim_red,
            simulated_sensor_omission_ratio=sim_omit,
            mean_err_d=mean_d,
            median_err_d=med_d,
            ci95_low_d=q_low_d,
            ci95_high_d=q_high_d,
            k_sensors_sparse=k_c,
            mean_err_sparse=mean_sp,
            median_err_sparse=med_sp,
            ci95_low_sparse=q_low_sp,
            ci95_high_sparse=q_high_sp,
            p_c_beats_b=p_c_lt_b,
            p_d_beats_a=p_d_lt_a,
            p_c_beats_a=p_c_lt_a,
            c_grid=self.c_grid,
            c_sweep_means=c_means,
            optimal_c=opt_c,
            optimal_c_err=opt_c_err,
            is_c_opt_near_two=is_near_two,
        )

    def run_replicated_campaign(self) -> List[ReplicatedRegimeResult]:
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
                res = self.evaluate_regime(op, sigma)
                results.append(res)

        return results


def main() -> None:
    bench = ReplicatedGeneralizationBenchmark(n_mc=100, seed=42)
    results = bench.run_replicated_campaign()
    print(f"Executed {len(results)} replicated regimes ({bench.n_mc} Monte Carlo runs each, {len(results)*bench.n_mc} total solves).")
    for r in results:
        print(f"[{r.operator_name:28}] sig={r.noise_sigma:.0e} | TSVD={r.mean_err_b:.4f} | Synth={r.mean_err_c:.4f} | P(C<B)={r.p_c_beats_b:.1%} | Opt c={r.optimal_c:.1f} (err={r.optimal_c_err:.4f})")


if __name__ == "__main__":
    main()
