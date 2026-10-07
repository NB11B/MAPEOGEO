"""Pytest Test Suite for Phase 1: Direct T4R Ext Computation Resolution."""

import pytest
from t4r_direct_ext_computation.ravenel_wilson_acyclicity import RavenelWilsonAcyclicity
from t4r_direct_ext_computation.mapping_spectrum_vanishing import MappingSpectrumVanishing
from t4r_direct_ext_computation.ext_computation_resolution import ExtComputationResolution

def test_ravenel_wilson_acyclicity():
    rw = RavenelWilsonAcyclicity(prime=2, height=2)
    res = rw.verify_acyclicity()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["is_kn_acyclic"] is True
    assert res["is_tn_acyclic"] is True
    assert "0" in res["lk_localization"]
    assert "0" in res["lt_localization"]

def test_mapping_spectrum_vanishing():
    msv = MappingSpectrumVanishing(prime=2, height=2)
    res = msv.verify_vanishing()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["mapping_spectrum_is_contractible"] is True
    assert "0" in res["solid_mapping_spectrum"]

def test_ext_computation_resolution():
    resolver = ExtComputationResolution(prime=2, height=2)
    res = resolver.resolve_conjecture()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["ext1_dimension"] == 0
    assert res["ext1_class_value"] == 0
    assert res["verdict"]["mathematical_outcome"] == "[\\xi_n] = 0"
    assert res["verdict"]["conjecture_status"] == "RESOLVED_FALSIFIED"

def test_kernel_v3_regression_zero():
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"
