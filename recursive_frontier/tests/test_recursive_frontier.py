"""Pytest Test Suite for Generation 2 Recursive Frontier Discovery Pipeline."""

import pytest
import json
from pathlib import Path
from recursive_frontier.admit_t1 import AdmittedT1Node
from recursive_frontier.admit_t3 import AdmittedT3Node
from recursive_frontier.delta_frontier import DeltaFrontierEngine
from recursive_frontier.ancestry import AncestryCertificateBuilder
from recursive_frontier.obstruction import Generation2ObstructionEvaluator
from recursive_frontier.convergence import CompoundingDiscoveryEngine
from recursive_frontier.rank_g2 import Generation2RankingEngine

def test_admit_t1_node():
    node = AdmittedT1Node()
    data = node.get_node_data()
    assert data["node_id"] == "X_T1"
    assert data["coordinates"]["Delta"] == 4
    assert len(data["outgoing_operators"]) == 4

def test_admit_t3_node():
    node = AdmittedT3Node()
    data = node.get_node_data()
    assert data["node_id"] == "X_T3"
    assert data["coordinates"]["Gamma"] == 4
    assert len(data["outgoing_operators"]) == 4

def test_delta_frontier_computation():
    engine = DeltaFrontierEngine()
    res = engine.compute_delta_frontiers()
    assert res["num_delta_t1"] == 3
    assert res["num_delta_t3"] == 3
    assert res["num_convergent"] == 1
    assert res["total_g2_population"] == 5
    assert res["convergent"][0]["candidate_id"] == "U2026_GEN2_CONV_0001"

def test_ancestry_certificates():
    builder = AncestryCertificateBuilder()
    certs = builder.build_certificates()
    assert len(certs) == 5
    for c in certs:
        assert c["generation"] == 2
        assert c["original_frontier_status"] == "UNREACHABLE_IN_G0"
        assert c["ancestry_factor_C_ancestry"] in [1.2, 2.0]
        assert len(c["independent_paths"]) >= 2

def test_obstruction_evaluation():
    evaluator = Generation2ObstructionEvaluator()
    obs_conv = evaluator.evaluate_candidate("U2026_GEN2_CONV_0001")
    assert obs_conv["is_unobstructed"] is True
    assert obs_conv["p_unobstructed"] == 1.0
    assert obs_conv["obstruction_class"] == "NONE"

def test_compounding_discovery_ratio():
    conv_engine = CompoundingDiscoveryEngine()
    metrics = conv_engine.compute_compounding_metrics()
    assert metrics["n_0_admitted_results"] == 2
    assert metrics["n_1_unlocked_candidates"] == 5
    assert metrics["r_discovery"] == 2.50
    assert metrics["r_discovery"] > 1.0

def test_ranking_and_champion():
    ranker = Generation2RankingEngine()
    ranked = ranker.rank_candidates()
    assert len(ranked) == 5
    champ = ranker.get_champion_target()
    assert champ["candidate_id"] == "U2026_GEN2_CONV_0001"
    assert champ["rank"] == 1
    assert champ["s2_composite_score"] > 2.0
    assert champ["is_champion_u2_star"] is True

def test_g2_freeze_manifest():
    out_dir = Path("artifacts/recursive_frontier")
    manifest_path = out_dir / "G2_FRONTIER_FREEZE_MANIFEST.json"
    assert manifest_path.exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["generation"] == 2
    assert manifest["champion_target_id"] == "U2026_GEN2_CONV_0001"
    assert manifest["compounding_ratio_r_discovery"] == 2.50

def test_kernel_v3_regression_zero():
    from experiments.kernel_v3_release import assemble_kernel_v3_release
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest = assemble_kernel_v3_release(Path(tmp_dir))
        assert manifest["total_regressions"] == 0
        assert manifest["release_version"] == "v3.0.0"
