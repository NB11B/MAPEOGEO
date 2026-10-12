#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-M5: Physical Pre-Acquisition Gating.

Verifies:
1. Physical aperture hardware cost calculation (ADC conversions, bus traffic, time, energy).
2. DEIM channel selection selects unique, valid physical sensor indices.
3. Gated pre-acquisition achieves > 75% omission with < 1.25x error ratio on nominal targets.
4. Crucial falsification suite maps degradation boundaries under kernel drift and anomalies.
"""

import numpy as np
import pytest

from sovctx.node.physical_gating_engine import (
    CrucialFalsificationSuite,
    HardwareProfile,
    PhysicalGatingAperture,
)


def test_hardware_cost_calculation():
    """Confirms linear scaling of ADC conversions, bus bytes, and energy."""
    ap = PhysicalGatingAperture(m_channels=64)
    t_full, e_full, b_full = ap.measure_hardware_costs(64)
    t_gated, e_gated, b_gated = ap.measure_hardware_costs(16)

    assert b_full == 128
    assert b_gated == 32
    assert t_gated < t_full
    assert e_gated < e_full
    # Check exact ratio
    assert abs((e_full / e_gated) - 4.0) < 0.1


def test_deim_channel_selection():
    """Verifies that DEIM selects k unique sensor indices within aperture bounds."""
    ap = PhysicalGatingAperture(m_channels=64)
    P_sparse, sel_idx, k = ap.select_gated_channels(sigma_noise=0.01)

    assert len(sel_idx) == k
    assert len(set(sel_idx)) == k
    assert min(sel_idx) >= 0
    assert max(sel_idx) < 64
    assert P_sparse.shape == (k, 64)
    assert np.allclose(P_sparse.sum(axis=1), np.ones(k))


def test_gated_acquisition_parity():
    """Verifies that gated acquisition delivers > 75% channel reduction with parity."""
    ap = PhysicalGatingAperture(m_channels=64)
    f_nom = ap.get_nominal_target()
    full_m, gated_m, _ = ap.run_acquisition_comparison(f_nom, sigma_noise=0.01)

    assert gated_m.omission_ratio >= 0.75
    assert gated_m.adc_conversions_omitted >= 48
    ratio = gated_m.reconstruction_relative_error / full_m.reconstruction_relative_error
    assert ratio <= 1.25  # Within 25% error parity


def test_crucial_falsification_suite():
    """Verifies that operator drift triggers the falsification boundary (degradation > 2.0x)."""
    ap = PhysicalGatingAperture(m_channels=64)
    suite = CrucialFalsificationSuite(ap, sigma=0.01)
    results = suite.run_all_perturbations()

    assert len(results) == 4
    # Nominal is adequate
    assert results[0].is_adequate
    # Operator drift exhibits significant degradation
    drift_res = results[3]
    assert drift_res.degradation_ratio > 2.0
    assert not drift_res.is_adequate
