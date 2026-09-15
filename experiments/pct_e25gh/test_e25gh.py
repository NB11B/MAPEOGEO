from experiments.pct_e25gh.morphisms import run_c5a_audit


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
