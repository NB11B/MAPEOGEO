"""Pytest Test Suite for Target T2: Independent Nuclear Inverse Limits."""

import pytest
import numpy as np
from experiments.portfolio_t2.typing_t2_1 import ExactNuclearTypingSpecification
from experiments.portfolio_t2.summability_t2_2 import verify_gate_t2_2, NuclearOperatorModel
from experiments.portfolio_t2.derived_limit_t2_3 import derive_r1_projective_limit_vanishing, NuclearInverseSystem
from experiments.portfolio_t2.consequences_t2_4 import IndependentNuclearConsequences

def test_gate_t2_1_nuclear_typing():
    spec = ExactNuclearTypingSpecification()
    res = spec.verify_typing()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["category_definition"]["foundational_structural_properties"]["dualizable"] is True
    assert res["category_definition"]["foundational_structural_properties"]["compactly_generated"] is False

def test_gate_t2_2_summability():
    res = verify_gate_t2_2()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["trace_norm"] < np.inf
    assert res["approximation_errors"]["rank_20"] < 1e-6
    assert res["comparison"]["identity_is_summable"] is False
    assert res["comparison"]["nuclear_is_summable"] is True

def test_gate_t2_3_derived_limit_vanishing():
    res = derive_r1_projective_limit_vanishing()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["nuclear_mittag_leffler_verified"] is True
    assert res["failing_system_detection"] is True
    assert res["milnor_solution"]["coker_phi_vanishes"] is True

def test_gate_t2_3_system_dynamics():
    sys = NuclearInverseSystem(num_stages=8, rho=0.4, has_dense_images=True)
    is_nml, _ = sys.verify_nuclear_mittag_leffler()
    assert is_nml is True
    sol = sys.solve_milnor_shift([1.0] * 8)
    assert sol["coker_phi_vanishes"] is True
    assert sol["truncation_residual"] < 1e-3

    # System with rho >= 1 fails
    bad_sys = NuclearInverseSystem(num_stages=8, rho=1.2, has_dense_images=True)
    is_nml_bad, _ = bad_sys.verify_nuclear_mittag_leffler()
    assert is_nml_bad is False

def test_gate_t2_4_consequences():
    inc = IndependentNuclearConsequences()
    res = inc.verify_consequences()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert len(res["consequences"]) == 4
    for c in res["consequences"]:
        assert c["verified"] is True
    for b in res["epistemic_boundaries"]:
        assert b["audited"] is True

def test_kernel_v3_regression_zero():
    # Kernel v3 integration check: Ensure regression baseline remains 0
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"

