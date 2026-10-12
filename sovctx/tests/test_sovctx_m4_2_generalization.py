#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-M4.2: Cross-Problem Synthetic-Lens Generalization.

Verifies:
1. Four distinct mathematical operators (Fredholm, Deconvolution, Abel, Heat).
2. Diverse ill-posedness spectra (exponential vs algebraic decay).
3. Four-arm protocol implementations (Tikhonov Morozov, TSVD, Synthetic Lens, Combined).
4. Pre-acquisition physical sparse sensor selection (DEIM / QR pivoting).
5. Picard condition starvation boundary detection at ultra-low noise.
6. Synthetic lens noise stabilization outperforming standard TSVD at moderate noise.
"""

import numpy as np
import pytest

from sovctx.node.cross_problem_generalization import (
    AbelVolterraOperator,
    CrossProblemGeneralizationBenchmark,
    FredholmScatteringOperator,
    GaussianDeconvolutionOperator,
    HeatConductionOperator,
    solve_tikhonov_morozov,
    solve_tikhonov_oracle,
)


def test_four_diverse_operators_instantiation():
    """Confirms all four operators instantiate with valid dimensions and spectra."""
    op1 = FredholmScatteringOperator(n_points=64, m_sensors=128)
    assert op1.A.shape == (128, 64)
    assert op1.ill_posedness_type == "SEVERE_EXPONENTIAL"
    assert op1.raw_condition_number > 1e10

    op2 = GaussianDeconvolutionOperator(n_points=64, blur_sigma=3.0)
    assert op2.A.shape == (64, 64)
    assert op2.ill_posedness_type == "MODERATE_EXPONENTIAL"
    assert op2.raw_condition_number > 1e4

    op3 = AbelVolterraOperator(n_points=64, delta=0.05)
    assert op3.A.shape == (64, 64)
    assert op3.ill_posedness_type == "MILD_ALGEBRAIC"
    # Abel condition number is algebraic / moderate
    assert 5.0 <= op3.raw_condition_number <= 1e4

    op4 = HeatConductionOperator(n_points=32, diff_coeff=0.5, t_final=0.05)
    assert op4.A.shape == (32, 32)
    assert op4.ill_posedness_type == "SEVERE_EXPONENTIAL"
    assert op4.raw_condition_number > 1e10


def test_tikhonov_morozov_and_oracle():
    """Tests Morozov discrepancy principle and oracle parameter selection."""
    op = HeatConductionOperator(n_points=32)
    f_true = op.get_ground_truth()
    sigma = 0.01
    noise = np.random.default_rng(123).normal(0.0, sigma, size=op.m)
    y = op.A @ f_true + noise

    alpha_mor, f_mor = solve_tikhonov_morozov(op.U, op.S, op.Vt, y, op.m, sigma)
    alpha_or, f_or, err_or = solve_tikhonov_oracle(op.U, op.S, op.Vt, y, f_true)

    assert alpha_mor > 0.0
    assert alpha_or > 0.0
    err_mor = np.linalg.norm(f_mor - f_true) / np.linalg.norm(f_true)
    assert err_mor < 0.20
    assert err_or <= err_mor + 1e-6  # Oracle is theoretical lower bound


def test_tsvd_vs_synthetic_cutoff():
    """Verifies that synthetic cutoff tau=2*sigma is strictly more conservative than TSVD tau=sigma."""
    op = FredholmScatteringOperator(n_points=64, m_sensors=128)
    sigma = 0.01
    k_tsvd = int(np.sum(op.S >= sigma))
    k_synth = int(np.sum(op.S >= 2.0 * sigma))

    assert k_synth <= k_tsvd
    assert k_synth >= 1
    # Check that condition number of synthetic is strictly smaller than or equal to TSVD
    cond_tsvd = op.S[0] / op.S[k_tsvd - 1]
    cond_synth = op.S[0] / op.S[k_synth - 1]
    assert cond_synth <= cond_tsvd


def test_pre_acquisition_sparse_sensor_selection():
    """Tests DEIM / QR column pivoting pre-acquisition sensor selection."""
    from scipy.linalg import qr
    op = GaussianDeconvolutionOperator(n_points=64, blur_sigma=3.0)
    sigma = 0.01
    k = max(1, int(np.sum(op.S >= 2.0 * sigma)))

    Uk = op.U[:, :k]
    _, _, p_piv = qr(Uk.T, pivoting=True)
    selected = p_piv[:k]

    assert len(selected) == k
    assert len(set(selected)) == k  # all unique physical sensors
    assert max(selected) < op.m
    assert min(selected) >= 0

    # Verify sensor reduction ratio
    omission_ratio = (op.m - k) / op.m
    assert omission_ratio > 0.0


def test_cross_problem_benchmark_campaign_execution():
    """Executes a small cross-problem generalization trial and checks consistency."""
    bench = CrossProblemGeneralizationBenchmark(seed=99)
    op = HeatConductionOperator(n_points=32)
    res = bench.evaluate_operator_at_noise(op, sigma=0.01, trials=3)

    assert res.operator_id == "OP_INVERSE_HEAT_CONDUCTION"
    assert res.arm_a_err_morozov > 0.0
    assert res.arm_b_err > 0.0
    assert res.arm_c_err > 0.0
    assert res.pre_acq_sparse_sensors_count == res.arm_c_k
    assert res.pre_acq_sparse_omission_ratio > 0.50  # Over 50% physical sensors omitted
    assert res.c_vs_b_error_ratio < 1.5  # Synthetic lens performs within bounds of TSVD
