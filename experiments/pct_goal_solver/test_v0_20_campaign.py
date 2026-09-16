from __future__ import annotations

from experiments.pct_goal_solver.v0_20_campaign import execute_v0_20_campaign


def test_v0_20_campaign_executes_all_gates_and_segregates_channels():
    result = execute_v0_20_campaign()
    
    # 1. Overall Status and Gate Perfection
    assert result["campaign_id"] == "PCT_GOAL_SOLVER_CROSS_CLASS_V0_20"
    assert result["scientific_status"] == "SUPPORTED"
    assert result["gates_passed"] == 10
    assert result["gates_total"] == 10
    assert result["total_wrong_positives"] == 0
    
    gates = result["gates"]
    assert gates["zero_wrong_positives"] is True
    assert gates["zero_macro_rescues"] is True
    assert gates["historical_g1_g12_coverage"] is True
    assert gates["foundational_f1_f3_coverage"] is True
    assert gates["complex_c1_c2_coverage"] is True
    assert gates["cross_class_x1_x2_coverage"] is True
    assert gates["no_same_class_shortcuts_proven"] is True
    assert gates["type_blind_routing_inferred"] is True
    assert gates["type_blind_routing_hybrid"] is True
    assert gates["certified_macro_witness_bound"] is True

    # 2. Segregated Channels Verification
    channels = result["channels"]
    
    # Historical Regression Channel
    hist = channels["historical_regression"]
    assert hist["baseline_families_count"] == 12
    assert hist["solved_families_count"] == 12
    assert hist["cases_correct"] >= 22  # 12 families * 2 sealed goals
    
    # Cross-Class Composition Channel
    cross = channels["cross_class_composition"]
    assert cross["foundational_f1_f3"]["correct"] == 6  # 3 families * 2 sealed
    assert cross["complex_c1_c2"]["correct"] == 4       # 2 families * 2 sealed
    assert cross["cross_class_x1_x2"]["correct"] == 4   # 2 families * 2 sealed
    assert len(cross["shortcut_proofs"]) == 4
    assert all(p["proven_no_shortcut"] for p in cross["shortcut_proofs"])
    
    # Macro Conservation Channel
    macro = channels["macro_conservation"]
    assert macro["zero_macro_rescues"] is True
    assert macro["total_macro_rescues"] == 0
    assert macro["total_credited_cases"] > 0
    assert macro["total_state_savings"] > 0
