#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-M4.1: External Perspective Falsification.
Tests the synthetic perspective DUAL_INVERSE_OMISSION on an external Fredholm integral equation.
"""

from __future__ import annotations

import math
from pathlib import Path
import pytest
import numpy as np

from sovctx.node.external_falsification import (
    FredholmScatteringOperator,
    TargetSignalGenerator,
    ExternalFalsificationEngine,
    InversionTrialResult,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def engine() -> ExternalFalsificationEngine:
    return ExternalFalsificationEngine(seed=42)


def test_external_forward_operator_properties(engine: ExternalFalsificationEngine) -> None:
    """Verifies that the external Fredholm operator is well-defined and severely ill-posed."""
    op = engine.op
    assert op.m == 256
    assert op.n == 128
    assert op.A.shape == (256, 128)
    assert op.S.shape == (128,)
    assert op.S[0] > 1.0
    assert op.S[-1] < 1e-15
    assert op.raw_condition_number > 1e14, f"Condition number {op.raw_condition_number} should be > 1e14"


def test_target_signals(engine: ExternalFalsificationEngine) -> None:
    """Verifies smooth and inclusion signal generation."""
    gen = engine.sig_gen
    f_smooth = gen.get_smooth_signal()
    f_incl = gen.get_inclusion_signal()

    assert f_smooth.shape == (128,)
    assert f_incl.shape == (128,)
    assert np.all(f_smooth >= 0.0)
    assert np.all(f_incl >= 0.0)
    # Inclusion has higher peak than smooth signal
    assert np.max(f_incl) > np.max(f_smooth)


def test_arm_b_massive_state_omission(engine: ExternalFalsificationEngine) -> None:
    """Verifies that Arm B omits >= 90% of observations across all noise levels."""
    for sigma in [1e-4, 1e-3, 1e-2, 5e-2]:
        res = engine.evaluate_condition("SMOOTH", sigma, trials=3)
        assert res.arm_b_omission_ratio >= 0.90, f"Omission ratio {res.arm_b_omission_ratio} < 0.90 at sigma={sigma}"
        assert res.arm_b_retained_modes <= 25
        assert res.arm_b_omitted_modes >= 230
        assert res.arm_b_flop_reduction_ratio >= 10.0


def test_falsification_information_starvation_boundary(engine: ExternalFalsificationEngine) -> None:
    """Verifies the deliberate mathematical falsification: Arm B fails at low noise (sigma=1e-4)."""
    res = engine.evaluate_condition("SMOOTH", 1e-4, trials=5)
    assert res.is_falsified_information_starvation
    assert res.b_vs_a_error_ratio > 1.25
    assert res.boundary_regime == "FALSIFIED_INFORMATION_STARVATION"
    assert "FALSIFICATION CONFIRMED" in res.boundary_notes


def test_arm_c_combined_subspace_regularization(engine: ExternalFalsificationEngine) -> None:
    """Verifies that Arm C (combined) rescues the boundary in rank k <= 19."""
    for sigma in [1e-4, 1e-3, 1e-2]:
        res = engine.evaluate_condition("SMOOTH", sigma, trials=3)
        # Arm C relative error should be comparable to or lower than Arm A
        assert res.arm_c_relative_error <= res.arm_a_relative_error * 1.15
        assert res.c_vs_a_error_ratio <= 1.15


def test_full_falsification_campaign(engine: ExternalFalsificationEngine) -> None:
    """Verifies the complete 8-case campaign and boundary delimitation."""
    camp = engine.run_full_campaign()
    assert camp["total_trials"] == 8
    assert camp["has_established_exact_falsification_boundary"]
    assert camp["has_demonstrated_massive_state_omission"]
    assert camp["falsified_count"] >= 1
    assert camp["stabilized_count"] >= 4
    assert len(camp["falsification_conclusion"]) > 50
