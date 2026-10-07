"""Pytest Test Suite for Target T3: Truncated Cubical Moduli Localization."""

import pytest
from experiments.portfolio_t3.typing_t3_1 import TruncatedUniverseSpecification
from experiments.portfolio_t3.finite_kan_t3_2 import verify_finite_kan_operator, CubicalTerm, hcomp_k, evaluate_glue_term
from experiments.portfolio_t3.normalization_t3_3 import verify_normalization_and_canonicity
from experiments.portfolio_t3.annihilation_t3_4 import verify_repair_annihilation_and_certify

def test_gate_t3_1_typing():
    spec = TruncatedUniverseSpecification(truncation_level=2)
    res = spec.verify_typing()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["truncation_level"] == 2
    assert "tau_{<= 2}" in res["universe_definition"]["name"]

def test_gate_t3_2_finite_kan():
    res = verify_finite_kan_operator()
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["operator_defined"] is True

def test_gate_t3_2_term_execution():
    u0 = CubicalTerm("CONSTRUCTOR", "BaseSpectrum", degree=1)
    side = CubicalTerm("CONSTRUCTOR", "Path", degree=1)
    res = hcomp_k(u0, [side], max_k=2)
    assert res.kind == "CONSTRUCTOR"
    glued = evaluate_glue_term(res, "EquivWitness", max_k=2)
    assert glued.kind == "CONSTRUCTOR"
    assert "Glued" in glued.value

def test_gate_t3_3_normalization():
    res = verify_normalization_and_canonicity(k_bound=2)
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["canonicity_satisfied"] is True
    assert "CONSTRUCTOR" in res["final_normalized_term"]

def test_gate_t3_4_annihilation():
    res = verify_repair_annihilation_and_certify(k_bound=2)
    assert res["status"] == "PASSED"
    assert res["verified"] is True
    assert res["annihilation_record"]["divergence_annihilated"] is True
    assert res["annihilation_record"]["conditional_status"] == "CONDITIONALLY_REALIZABLE"

def test_kernel_v3_regression_zero():
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"
