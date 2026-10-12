from __future__ import annotations

from pathlib import Path
import pytest

from sovctx.node.graph_controls import GraphControlsEngine
from sovctx.node.leibniz_lineage import LeibnizLineageEngine
from sovctx.node.priority_matrix import PriorityMatrixEngine
from sovctx.node.relational_duality import (
    NORMALIZED_RELATION_VERBS,
    RelationalDualityEngine,
)
from sovctx.node.temporal_relations import TemporalRelationsEngine


def test_relational_duality_projection() -> None:
    engine = RelationalDualityEngine()
    assert len(engine.relation_nodes) in {453, 537}
    assert len(engine.g_star_adj) > 0
    # Over 10,000 transitions in G*
    total_dual_edges = sum(len(v) for v in engine.g_star_adj.values())
    assert total_dual_edges > 10000


def test_canonical_17_verbs_and_centrality() -> None:
    engine = RelationalDualityEngine()
    metrics = engine.calculate_relation_centrality()
    assert len(metrics) == len(NORMALIZED_RELATION_VERBS)

    # REPRESENT and STABILIZE must be top central verbs
    top_verbs = [m.verb for m in metrics[:3]]
    assert "REPRESENT" in top_verbs
    assert "STABILIZE" in top_verbs


def test_target_grammar_sequences() -> None:
    engine = RelationalDualityEngine()
    targets = engine.audit_target_grammar_sequences()
    assert len(targets) == 3

    t_map = {t.target_sequence: t for t in targets}
    s1 = t_map["OBSERVE -> INVERT -> CONSTRAIN -> STABILIZE"]
    s2 = t_map["REPRESENT -> PERTURB -> STABILIZE -> CONTROL"]
    s3 = t_map["REPRESENT -> REDUCE -> EVOLVE -> RECONSTRUCT"]

    assert s1.raw_count > 1000
    assert "TIKHONOV" in s1.found_in_schools or "GELFAND" in s1.found_in_schools

    assert s2.raw_count > 100
    assert "LYAPUNOV" in s2.found_in_schools or "PONTRYAGIN" in s2.found_in_schools

    assert s3.raw_count > 50
    assert "VLASOV" in s3.found_in_schools


def test_graph_compression_and_blinded_recovery() -> None:
    engine = RelationalDualityEngine()
    comp = engine.compare_graph_compression()
    assert comp.compression_gain_percent > 80.0
    assert comp.relation_graph_entropy_bits < comp.entity_graph_entropy_bits

    recovery = engine.blinded_school_recovery()
    assert len(recovery) >= 4
    for r in recovery:
        assert r.clustering_purity_score > 0.65


def test_randomized_graph_controls_fast() -> None:
    controls = GraphControlsEngine(seed=42)
    # Quick 5-iteration verification of Control A, B, C, D
    res_a = controls.run_control_a(iterations=5, swaps_per_iter=50)
    assert res_a.control_id == "CONTROL-A"
    assert len(res_a.statistics) == 3

    res_b = controls.run_control_b(iterations=5)
    assert res_b.control_id == "CONTROL-B"

    res_c = controls.run_control_c(iterations=5)
    assert res_c.control_id == "CONTROL-C"

    res_d = controls.run_control_d(iterations=5)
    assert res_d.control_id == "CONTROL-D"
    assert res_d.statistics[0].z_score > 10.0


def test_temporal_relations_6_slices() -> None:
    engine = TemporalRelationsEngine()
    profiles = engine.analyze_all_slices()
    assert len(profiles) == 6
    for p in profiles:
        assert p.active_entity_count > 0
        assert p.active_edge_count > 0
        assert len(p.dominant_verbs) > 0


def test_leibniz_lineage_and_provenance_isolation() -> None:
    engine = LeibnizLineageEngine()
    chain = engine.extract_genealogical_chain()
    assert len(chain) == 8
    assert chain[0].person_name == "G. W. Leibniz"
    assert chain[1].person_name == "Leonhard Euler"

    h1, h2 = engine.test_hypotheses(chain)
    assert h1.verdict == "PARTIALLY_REFUTED"
    assert h2.verdict == "STRONGLY_SUPPORTED"

    iso = engine.isolate_oral_provenance()
    assert iso.sensitivity_delta_percent == 0.0
    assert "STRICTLY_ISOLATED" in iso.epistemic_verdict


def test_priority_matrix() -> None:
    engine = PriorityMatrixEngine()
    rows = engine.build_matrix()
    assert len(rows) > 10

    # Top item should be STABILIZE or CONSTRAIN
    assert rows[0].item_id in ("VERB:STABILIZE", "VERB:CONSTRAIN")
    assert rows[0].composite_priority_index > 3.0
