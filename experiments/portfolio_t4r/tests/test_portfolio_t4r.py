"""Pytest Test Suite for Target T4R: Reconstructed Chromatic Obstruction and Nuclear Repair."""

import pytest
from experiments.portfolio_t4r.bhls_foundation_t4r_1 import GenuineChromaticFoundation
from experiments.portfolio_t4r.obstruction_reconstruction_t4r_2 import ReconstructedChromaticObstruction
from experiments.portfolio_t4r.repair_annihilation_t4r_3 import NuclearRepairAnnihilation

def test_gate_t4r_1_genuine_foundations():
    foundations = GenuineChromaticFoundation(prime=2, height=2)
    res = foundations.verify_foundations()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["theorems"]["hopkins_smith_1998"]["is_smashing"] is True
    assert res["theorems"]["morava_k_theory"]["is_smashing"] is False
    assert res["theorems"]["bhls_2023"]["equivalence"] is False
    assert res["theorems"]["bhls_2023"]["fiber_noncontractible"] is True

def test_gate_t4r_2_obstruction_reconstruction():
    reconstruction = ReconstructedChromaticObstruction(prime=2, height=2)
    res = reconstruction.compute_obstruction_class()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["obstruction"]["non_vanishing"] is True
    assert res["obstruction"]["dimension"] > 0
    assert "alpha_{BHLS}" in res["obstruction"]["fiber_homotopy_class"]

def test_gate_t4r_3_repair_annihilation():
    annihilation = NuclearRepairAnnihilation()
    res = annihilation.verify_annihilation()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["annihilation_record"]["annihilated"] is True
    assert res["annihilation_record"]["post_repair_ext1_dim"] == 0

def test_kernel_v3_regression_zero():
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"
