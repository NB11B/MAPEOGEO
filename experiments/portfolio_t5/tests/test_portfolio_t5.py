"""Pytest Test Suite for Target T5: Untruncated Operadic Coherence Divergence."""

import pytest
from experiments.portfolio_t5.operadic_tower_t5_1 import verify_operadic_coherence_tower
from experiments.portfolio_t5.boundary_undecidability_t5_2 import verify_boundary_undecidability
from experiments.portfolio_t5.canonicity_divergence_t5_3 import simulate_canonicity_divergence
from experiments.portfolio_t5.impossibility_theorem_t5_4 import prove_impossibility_theorem

def test_gate_t5_1_operadic_tower():
    res = verify_operadic_coherence_tower()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["tower_is_infinite"] is True
    assert res["obstruction_type"] == "INFINITE_TAQ_OBSTRUCTIONS"

def test_gate_t5_2_boundary_undecidability():
    res = verify_boundary_undecidability()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["constructively_undecidable"] is True
    assert res["requires_choice"] is True

def test_gate_t5_3_canonicity_divergence():
    res = simulate_canonicity_divergence(depth=8)
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["divergence_confirmed"] is True
    assert res["normal_form_reached"] is False
    assert len(res["trace"]) == 8

def test_gate_t5_4_impossibility_theorem():
    res = prove_impossibility_theorem()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["final_status"] == "OBSTRUCTED"
    assert res["obstruction"]["non_vanishing"] is True
    assert "INFINITE_COHERENCE_DIVERGENCE" in res["obstruction"]["id"]

def test_kernel_v3_regression_zero():
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"
