from pathlib import Path
import json

from experiments.pct_e25gh.morphisms import run_c5a_audit
from experiments.pct_e25gh.provenance import run_c5b_audit
from experiments.pct_e25gh.policies import run_e25h_policy_comparison


def test_c5a_all_four_real_contracts_agree_exactly():
    result = run_c5a_audit()
    assert result["status"] == "PASS"
    assert result["component_count"] == 4
    assert all(c["all_routes_agree"] for c in result["components"])
    assert sum(c["inputs_tested"] for c in result["components"]) > 3000


def test_lp_c5a_preserves_all_active_minimizers():
    result = run_c5a_audit()
    lp = next(c for c in result["components"] if c["contract"] == "lp")
    assert lp["tie_case_count"] > 0
    assert lp["all_active_minimizers_preserved"] is True


def test_c5b_binds_every_real_component_to_source_and_adapter():
    result = run_c5b_audit()
    assert result["status"] == "PASS"
    assert result["component_count"] == 4
    for c in result["components"]:
        assert c["provenance_state"] == "PASS"
        assert len(c["provenance_sha256"]) == 64
        assert c["source_statement_sha256"]
        assert c["formal_scope"]
        assert c["certificate_ids"]
        assert c["adapter_sha256"]


def test_strict_policy_has_zero_false_accepts():
    result = run_e25h_policy_comparison()
    strict = result["policies"]["STRICT_AND"]
    assert strict["false_accepts"] == 0
    assert strict["valid_rejects"] == 0


def test_single_axis_policies_are_exposed_by_axis_specific_faults():
    result = run_e25h_policy_comparison()
    assert result["policies"]["MAP_ONLY"]["false_accepts"] > 0
    assert result["policies"]["PROVENANCE_ONLY"]["false_accepts"] > 0
    assert result["policies"]["ANY_AXIS"]["false_accepts"] >= max(
        result["policies"]["MAP_ONLY"]["false_accepts"],
        result["policies"]["PROVENANCE_ONLY"]["false_accepts"],
    )


def test_every_contract_has_both_single_axis_fault_classes():
    result = run_e25h_policy_comparison()
    for contract in result["contracts"]:
        cases = {x["fault_class"] for x in contract["adversarial_cases"]}
        assert "CORRECT_MAP_WRONG_PROVENANCE" in cases
        assert "WRONG_MAP_CORRECT_PROVENANCE" in cases


def test_frozen_e25gh_evidence_matches_fresh_execution():
    root = Path(__file__).resolve().parents[2]
    assert json.loads((root / "evidence/pct_e25g_exact_morphism_audit.json").read_text()) == run_c5a_audit()
    assert json.loads((root / "evidence/pct_e25g_provenance_bindings.json").read_text()) == run_c5b_audit()
    assert json.loads((root / "evidence/pct_e25h_policy_comparison.json").read_text()) == run_e25h_policy_comparison()


def test_strict_c5_eligibility_requires_both_component_and_policy_success():
    result = run_e25h_policy_comparison()
    assert result["strict_policy_acceptable"] is True
    assert all(c["strict_c5_eligible"] for c in result["contracts"])
