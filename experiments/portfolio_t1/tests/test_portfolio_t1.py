"""Pytest Test Suite for Target T1: Analytic Stack Prismatic Coherence Duality."""

import pytest
import numpy as np
from experiments.portfolio_t1.typing_t1_1 import QuasisyntomicTypingSpecification
from experiments.portfolio_t1.descent_t1_2 import prove_quasisyntomic_descent
from experiments.portfolio_t1.nygaard_duality_t1_3 import PrismaticDualityModel
from experiments.portfolio_t1.contractibility_t1_4 import prove_contractibility_and_certify

def test_gate_t1_1_typing():
    spec = QuasisyntomicTypingSpecification()
    res = spec.verify_typing()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert "QSyn" in res["site_definition"]["name"]
    assert "Stk(QSyn)" in res["stack_category"]["name"]

def test_gate_t1_2_descent():
    res = prove_quasisyntomic_descent()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["comonadicity_theorem"] == "Barr-Beck-Lurie"

def test_gate_t1_3_nygaard_duality():
    model = PrismaticDualityModel(dimension=4)
    res = model.verify_duality()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert abs(res["determinant"]) > 1e-6
    assert "omega_X" in res["duality_formula"]

def test_gate_t1_4_contractibility():
    res = prove_contractibility_and_certify()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["is_contractible"] is True
    assert res["construction_verdict"] == "CONSTRUCTED_UP_TO_EQUIVALENCE"

def test_kernel_v3_regression_zero():
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"
