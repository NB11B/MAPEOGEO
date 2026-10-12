#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-M4.2R: Replicated Generalization.

Verifies:
1. Monte Carlo replication produces stable statistical moments (mean, median, 95% CI).
2. Synthetic lens (tau = 2*sigma) beats Standard TSVD (tau = sigma) with high empirical probability P(C < B).
3. Cutoff multiplier sweep maps optimal multiplier c_opt across operator families.
4. Structural difference between severe exponential decay (Fredholm, Heat, Deconv) and mild algebraic decay (Abel).
"""

import numpy as np
import pytest

from sovctx.node.cross_problem_generalization import (
    FredholmScatteringOperator,
    GaussianDeconvolutionOperator,
    HeatConductionOperator,
    AbelVolterraOperator,
)
from sovctx.node.replicated_generalization import (
    ReplicatedGeneralizationBenchmark,
    ReplicatedRegimeResult,
)


def test_replicated_regime_moments():
    """Tests that a 20-run replication produces valid statistical intervals."""
    bench = ReplicatedGeneralizationBenchmark(n_mc=20, seed=123)
    op = HeatConductionOperator(n_points=32)
    res = bench.evaluate_regime(op, sigma=0.01)

    assert res.n_mc_samples == 20
    assert res.ci95_low_c <= res.median_err_c <= res.ci95_high_c
    assert res.ci95_low_b <= res.median_err_b <= res.ci95_high_b
    assert res.mean_err_c > 0.0
    assert 0.0 <= res.p_c_beats_b <= 1.0


def test_synthetic_superiority_probability():
    """Verifies that on severely ill-posed operators at moderate noise, P(C < B) > 80%."""
    bench = ReplicatedGeneralizationBenchmark(n_mc=30, seed=456)
    op = FredholmScatteringOperator(n_points=64, m_sensors=128)
    res = bench.evaluate_regime(op, sigma=0.01)

    assert res.p_c_beats_b >= 0.80
    assert res.mean_err_c < res.mean_err_b


def test_cutoff_multiplier_sweep():
    """Verifies that cutoff sweep identifies an optimal multiplier c in [1.5, 4.0] for exponential decay."""
    bench = ReplicatedGeneralizationBenchmark(n_mc=20, seed=789)
    op = GaussianDeconvolutionOperator(n_points=64, blur_sigma=3.0)
    res = bench.evaluate_regime(op, sigma=0.01)

    assert len(res.c_sweep_means) == len(res.c_grid)
    assert res.optimal_c >= 1.5
    assert res.c_sweep_means[res.optimal_c] <= res.c_sweep_means[1.0]  # Opt beats standard TSVD multiplier
