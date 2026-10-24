"""Tests for Track A left-side triangular reconstruction and Checkpoint 01 completeness."""

from __future__ import annotations

from experiments.rule30_proof_closure.left import (
    evaluate_autonomous_no11_left_evolution,
    evaluate_left_cone_elimination,
    verify_checkpoint_01_reconstruction_completeness,
)


def test_checkpoint_01_left_triangular_reconstruction_completeness():
    res = verify_checkpoint_01_reconstruction_completeness(steps=24)
    assert res.checkpoint_01_passed is True
    assert res.reconstruction_mismatches == 0
    assert res.inverse_orcol_mismatches == 0
    assert res.unit_triangular_sensitivity_mismatches == 0
    assert res.cells_reconstructed == 24 * 25 // 2


def test_left_phase_macros_and_cone_elimination():
    macro_res = evaluate_autonomous_no11_left_evolution(max_transient_t=5, max_steps=32)
    assert macro_res.black_step_mismatches == 0
    assert macro_res.effective_boundary_mismatches == 0
    for t_val in range(1, 6):
        assert macro_res.autonomous_no11_max_survival_by_transient[t_val] < 16

    elim = evaluate_left_cone_elimination(transient_t=3, word=(0, 0, 1), max_horizon=24)
    assert elim.surviving_left_states == 0
    assert elim.left_unsat_horizon_h == 6
