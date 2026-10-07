"""Test Suite for Campaign H2 (Rolling Historical Discovery Replications)."""

import pytest
from pathlib import Path

from experiments.rolling_historical.historical_epochs import ROLLING_ORIGINS, EPOCH_DEFINITIONS
from experiments.rolling_historical.attention_confounders import (
    compute_attention_profile,
    compute_attention_propensity_score,
    select_attention_matched_controls,
    evaluate_conditional_independence
)
from experiments.rolling_historical.lodo_convergence import compute_lodo_convergence
from experiments.rolling_historical.epoch_replay import execute_epoch_replay
from experiments.rolling_historical.calibration_and_ablation import (
    compute_ndcg_at_k,
    compute_calibration_bins,
    check_calibration_monotonicity,
    run_score_ablations
)
from experiments.rolling_historical.meta_analysis import (
    run_random_effects_meta_analysis,
    evaluate_gate_criteria
)
from experiments.rolling_historical.frontier_2026 import generate_live_2026_frontier
from experiments.rolling_historical.campaign import run_campaign_h2

@pytest.fixture
def temp_output_dir(tmp_path):
    out = tmp_path / "artifacts_h2_test"
    out.mkdir(parents=True, exist_ok=True)
    return out

def test_epoch_definitions_and_sources():
    assert len(ROLLING_ORIGINS) == 12
    for year in ROLLING_ORIGINS:
        assert year in EPOCH_DEFINITIONS
        defn = EPOCH_DEFINITIONS[year]
        assert len(defn["core_nodes"]) >= 3
        assert len(defn["key_sources"]) >= 3
        for s in defn["key_sources"]:
            assert s["year"] <= year  # Strict semantic backdating

def test_attention_confounders_and_matching():
    sample_state = {"state_id": "TEST_01", "domain": "Algebra", "degree": 6, "depth": 2}
    profile = compute_attention_profile(sample_state, 1950)
    assert profile["active_authors"] > 0
    assert profile["recent_theorem_rate"] > 0
    assert profile["unresolved_conjectures"] >= 1
    
    propensity = compute_attention_propensity_score(profile)
    assert 0.0 <= propensity <= 1.0

    matched = select_attention_matched_controls([sample_state], 1950)
    assert len(matched) == 1
    assert matched[0]["target_type"] == "MATCHED_CONTROL_ATTENTION_BALANCED"

def test_lodo_convergence():
    candidate = {
        "state_id": "U1950_TEST",
        "domain": "Topology",
        "parent_states": ["N1950_01"],
        "coordinates": {"Delta": 4, "I": 3, "W": 3, "sigma": 2, "Pi": 2, "Gamma": 2}
    }
    nodes = [{"id": "N1950_01", "domain": "Topology"}]
    lodo = compute_lodo_convergence(candidate, nodes, 1950)
    assert lodo["convergence_count"] >= 1
    assert "lodo_evaluations" in lodo

def test_epoch_replay_and_right_censoring(temp_output_dir):
    # Test 1950 replay
    res_1950 = execute_epoch_replay(1950, temp_output_dir)
    assert res_1950["hazard_ratio_HR_t"] > 1.0
    assert res_1950["negative_frontier_rate"] == 0.0
    assert len(res_1950["valid_horizons"]) == 4

    # Test 2010 replay (must right-censor horizons > 2026)
    res_2010 = execute_epoch_replay(2010, temp_output_dir)
    assert 5 in res_2010["valid_horizons"]
    assert 10 in res_2010["valid_horizons"]
    assert 25 in res_2010["censored_horizons"]
    assert 50 in res_2010["censored_horizons"]
    assert res_2010["enrichment_by_horizon"]["horizon_25yr"]["censored"] is True

def test_calibration_and_ablations():
    candidates = [
        {"state_id": "C1", "prediction_score_S": 0.95, "is_occupied": True, "component_paths": 0.9, "component_support": 0.9, "component_witness": 0.9, "component_proximity": 0.9, "convergence_count": 3},
        {"state_id": "C2", "prediction_score_S": 0.85, "is_occupied": True, "component_paths": 0.8, "component_support": 0.8, "component_witness": 0.8, "component_proximity": 0.8, "convergence_count": 2},
        {"state_id": "C3", "prediction_score_S": 0.60, "is_occupied": False, "component_paths": 0.5, "component_support": 0.5, "component_witness": 0.5, "component_proximity": 0.5, "convergence_count": 1},
    ]
    ndcg = compute_ndcg_at_k(candidates, 3)
    assert ndcg > 0.8
    
    bins = compute_calibration_bins(candidates)
    assert check_calibration_monotonicity(bins) is True

    ablations = run_score_ablations(candidates, [])
    assert "full" in ablations
    assert "minus_convergence" in ablations

def test_meta_analysis_and_gates(temp_output_dir):
    epoch_results = [execute_epoch_replay(y, temp_output_dir) for y in [1900, 1950, 1980]]
    meta = run_random_effects_meta_analysis(epoch_results)
    assert meta["pooled_relative_risk"] > 1.0
    assert meta["ci_excludes_unity"] is True

    gates = evaluate_gate_criteria(epoch_results, meta)
    assert gates["gate_1_majority_enrichment"]["passed"] is True
    assert gates["gate_3_negative_frontier_avoidance"]["passed"] is True

def test_frontier_2026_and_candidate_1(temp_output_dir):
    f2026 = generate_live_2026_frontier(temp_output_dir)
    assert len(f2026["constructible_candidates"]) >= 3
    assert len(f2026["frontier_candidates"]) >= 3
    assert len(f2026["certificates"]) >= 3

    # Check Candidate #1 Prediction Work Certificate
    c1_cert = f2026["certificates"][0]
    assert c1_cert["candidate_id"] == "U2026_CONST_0001"
    assert "parents" in c1_cert
    assert "operator_word" in c1_cert
    assert "constraints" in c1_cert
    assert "independent_convergence_paths" in c1_cert
    assert "concrete_falsifier" in c1_cert
    assert len(c1_cert["independent_convergence_paths"]) >= 3

def test_full_campaign_h2(temp_output_dir):
    results = run_campaign_h2(temp_output_dir)
    assert results["status"] == "GATE_PASSED_PROSPECTIVE_2026_UNLOCKED"
    assert (temp_output_dir / "ROLLING_HISTORICAL_H2_REPORT.md").exists()
    assert (temp_output_dir / "meta_analysis_results.json").exists()
    assert (temp_output_dir / "gate_evaluation_results.json").exists()
    assert (temp_output_dir / "frontier_2026" / "prediction_freeze_manifest_2026.json").exists()
