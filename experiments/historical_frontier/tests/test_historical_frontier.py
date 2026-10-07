"""Unit and integration tests for Historical Discovery Campaign H1 (1950)."""

import pytest
import json
from pathlib import Path

from experiments.historical_frontier.historical_sources import verify_and_manifest_sources
from experiments.historical_frontier.semantic_backdating import audit_and_backdate_vocabulary
from experiments.historical_frontier.historical_graph import build_g1950_graph
from experiments.historical_frontier.derivable_filter import extract_derivable_population
from experiments.historical_frontier.closure_generator import generate_raw_frontier_closure
from experiments.historical_frontier.frontier_dedup import deduplicate_frontier_slots
from experiments.historical_frontier.prediction_score import score_and_rank_frontier
from experiments.historical_frontier.matched_controls import generate_matched_controls
from experiments.historical_frontier.negative_frontier import generate_negative_frontier
from experiments.historical_frontier.prediction_freeze import freeze_predictions_and_preregister
from experiments.historical_frontier.historical_reveal import progressive_historical_reveal
from experiments.historical_frontier.occupation_matcher import match_frontier_occupations
from experiments.historical_frontier.survival_analysis import compute_survival_and_hazard_ratio
from experiments.historical_frontier.enrichment import compute_enrichment_and_calibration
from experiments.historical_frontier.campaign import run_campaign_h1

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / "artifacts_h1_test"

def test_historical_sources(temp_output_dir):
    data = verify_and_manifest_sources(temp_output_dir, cutoff_year=1950)
    assert data["cutoff_year"] == 1950
    assert data["verified_source_count"] >= 12
    assert data["latest_year"] <= 1950
    assert (temp_output_dir / "historical_source_manifest.json").exists()

def test_semantic_backdating(temp_output_dir):
    raw_sample = [
        {"node_id": "homology", "raw_description": "simplicial homology modulo boundaries", "publication_year": 1926},
        {"node_id": "bad_node", "raw_description": "derived_algebraic_geometry and schemes", "publication_year": 1980}
    ]
    res = audit_and_backdate_vocabulary(raw_sample, temp_output_dir)
    assert res["audit"]["anachronisms_detected_and_purged"] == 1
    assert len(res["sanitized_entries"]) == 1
    assert res["sanitized_entries"][0]["historical_id"].startswith("H1950_")
    assert (temp_output_dir / "semantic_leakage_audit.json").exists()

def test_g1950_graph(temp_output_dir):
    graph = build_g1950_graph(temp_output_dir)
    assert graph["cutoff_year"] == 1950
    assert graph["nodes_count"] >= 16
    assert graph["edges_count"] >= 16
    assert (temp_output_dir / "G1950_manifest.json").exists()

def test_derivable_and_frontier_generation(temp_output_dir):
    graph = build_g1950_graph(temp_output_dir)
    deriv = extract_derivable_population(graph["nodes"], graph["edges"], temp_output_dir)
    assert len(deriv) > 0
    assert (temp_output_dir / "derivable_1950.jsonl").exists()

    raw_frontier = generate_raw_frontier_closure(graph["nodes"], graph["edges"], deriv, temp_output_dir)
    assert len(raw_frontier) > 0

    deduped = deduplicate_frontier_slots(raw_frontier, temp_output_dir)
    assert len(deduped) > 0
    assert len(deduped) <= len(raw_frontier)
    assert (temp_output_dir / "U1950.jsonl").exists()

def test_ranking_and_controls(temp_output_dir):
    graph = build_g1950_graph(temp_output_dir)
    deriv = extract_derivable_population(graph["nodes"], graph["edges"], temp_output_dir)
    raw_frontier = generate_raw_frontier_closure(graph["nodes"], graph["edges"], deriv, temp_output_dir)
    deduped = deduplicate_frontier_slots(raw_frontier, temp_output_dir)
    
    ranked = score_and_rank_frontier(deduped, temp_output_dir)
    assert ranked[0]["rank"] == 1
    assert ranked[0]["prediction_score_S"] >= ranked[-1]["prediction_score_S"]
    assert (temp_output_dir / "U1950_ranked.jsonl").exists()

    matched = generate_matched_controls(ranked, temp_output_dir)
    assert len(matched) == len(ranked)
    assert (temp_output_dir / "matched_controls_1950.jsonl").exists()

    negative = generate_negative_frontier(ranked, temp_output_dir)
    assert len(negative) == len(ranked)
    assert (temp_output_dir / "negative_frontier_1950.jsonl").exists()

def test_prediction_freeze(temp_output_dir):
    graph = build_g1950_graph(temp_output_dir)
    deriv = extract_derivable_population(graph["nodes"], graph["edges"], temp_output_dir)
    raw_frontier = generate_raw_frontier_closure(graph["nodes"], graph["edges"], deriv, temp_output_dir)
    deduped = deduplicate_frontier_slots(raw_frontier, temp_output_dir)
    ranked = score_and_rank_frontier(deduped, temp_output_dir)
    generate_matched_controls(ranked, temp_output_dir)
    generate_negative_frontier(ranked, temp_output_dir)
    verify_and_manifest_sources(temp_output_dir, cutoff_year=1950)

    freeze = freeze_predictions_and_preregister(ranked, temp_output_dir)
    assert freeze["status"] == "PREDICTIONS_FROZEN_BEFORE_HISTORICAL_REVEAL"
    assert "U1950_ranked.jsonl" in freeze["frozen_files"]
    assert (temp_output_dir / "prediction_freeze_manifest.json").exists()

def test_occupation_and_survival(temp_output_dir):
    graph = build_g1950_graph(temp_output_dir)
    deriv = extract_derivable_population(graph["nodes"], graph["edges"], temp_output_dir)
    raw_frontier = generate_raw_frontier_closure(graph["nodes"], graph["edges"], deriv, temp_output_dir)
    deduped = deduplicate_frontier_slots(raw_frontier, temp_output_dir)
    ranked = score_and_rank_frontier(deduped, temp_output_dir)
    matched = generate_matched_controls(ranked, temp_output_dir)
    negative = generate_negative_frontier(ranked, temp_output_dir)

    reveal = progressive_historical_reveal(temp_output_dir)
    assert len(reveal) == 4

    occ = match_frontier_occupations(ranked, matched, negative, reveal, temp_output_dir)
    assert occ["summary"]["frontier_occupied_count"] > 0
    assert occ["summary"]["negative_frontier_occupied_count"] == 0
    assert (temp_output_dir / "occupation_results.jsonl").exists()

    survival = compute_survival_and_hazard_ratio(occ["results"], temp_output_dir)
    assert survival["discovery_hazard_ratio_HR"] > 1.0
    assert survival["ci_excludes_unity"] is True
    assert (temp_output_dir / "survival_results.json").exists()

    enrich = compute_enrichment_and_calibration(occ["results"], temp_output_dir)
    assert enrich["enrichment"]["monotonic_ordering_confirmed"] is True
    assert enrich["calibration"]["campaign_verdict"] == "FRONTIER_PREDICTIVE"
    assert (temp_output_dir / "enrichment_curves.json").exists()

def test_full_h1_campaign(temp_output_dir):
    results = run_campaign_h1(temp_output_dir)
    assert results["status"] == "FRONTIER_PREDICTIVE"
    assert (temp_output_dir / "HISTORICAL_FRONTIER_1950_REPORT.md").exists()
