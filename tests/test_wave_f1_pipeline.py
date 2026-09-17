"""Tests for Wave F1 Intake Pipeline and Graph Reconstruction."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts.wave_f1_intake import (
    FORBIDDEN_PERSISTED_KEYS,
    compute_wave_f1_metrics,
    run_wave_f1_intake,
)

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "artifacts" / "wave_f1_v0_21" / "mapeogeo_v0_21_f1_graph.json.gz"
EVIDENCE_PATH = ROOT / "evidence" / "v0_21_wave_f1_scientific_results.json"
REPORT_PATH = ROOT / "docs" / "V0_21_WAVE_F1_REPORT.md"


def test_wave_f1_graph_artifacts_exist() -> None:
    assert GRAPH_PATH.exists(), f"Missing graph artifact: {GRAPH_PATH}"
    assert EVIDENCE_PATH.exists(), f"Missing evidence artifact: {EVIDENCE_PATH}"
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"


def test_wave_f1_graph_schema_and_zero_prose() -> None:
    with gzip.open(GRAPH_PATH, "rt", encoding="utf-8") as f:
        graph = json.load(f)

    assert graph["schema_version"] == "v0.21-mapeogeo-graph"
    assert graph["stage"] == "v0.21_wave_f1"

    nodes = graph["nodes"]
    edges = graph["edges"]
    assert len(nodes) > 3000
    assert len(edges) > 27000

    node_ids = set()
    f1_counts = {"OPEN_LOGIC": 0, "OPEN_SET_THEORY": 0, "LEVIN_DISCRETE": 0}
    for n in nodes:
        assert "id" in n
        assert "type" in n
        assert n["id"] not in node_ids, f"Duplicate node ID {n['id']}"
        node_ids.add(n["id"])

        attrs = n.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            assert forbidden not in attrs, f"Forbidden key '{forbidden}' found in node {n['id']}"

        corpus = attrs.get("corpus")
        if corpus in f1_counts:
            f1_counts[corpus] += 1

    assert f1_counts["OPEN_LOGIC"] == 35
    assert f1_counts["OPEN_SET_THEORY"] == 30
    assert f1_counts["LEVIN_DISCRETE"] == 35

    # Check edges
    edge_ids = set()
    for e in edges:
        assert "id" in e
        assert "source" in e
        assert "target" in e
        assert e["id"] not in edge_ids, f"Duplicate edge ID {e['id']}"
        edge_ids.add(e["id"])
        assert e["source"] in node_ids, f"Dangling edge source: {e['source']}"
        assert e["target"] in node_ids, f"Dangling edge target: {e['target']}"


def test_wave_f1_scientific_evidence_and_metrics() -> None:
    ev_data = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    assert ev_data["schema_version"] == "v0.21-wave-f1-scientific-results"
    assert ev_data["stage"] == "v0.21_wave_f1"

    metrics = ev_data["metrics"]
    assert metrics["wave_f1_declarations_ingested"] == 100
    assert 0.0 < metrics["raw_topology_reachability_pct"] <= 100.0
    assert 0.0 < metrics["proof_eligible_grounding_pct"] <= 100.0

    provenance = ev_data["provenance"]
    assert provenance["open_logic_declarations"] == 35
    assert provenance["open_set_declarations"] == 30
    assert provenance["levin_discrete_declarations"] == 35
    assert provenance["canonical_objects"] == 32
    assert provenance["cross_source_alignments"] == 100
    assert provenance["executable_contracts_passed"] == 4


def test_wave_f1_deterministic_reconstruction(tmp_path: Path) -> None:
    out1 = tmp_path / "run1"
    ev1 = tmp_path / "ev1.json"
    rep1 = tmp_path / "rep1.md"

    out2 = tmp_path / "run2"
    ev2 = tmp_path / "ev2.json"
    rep2 = tmp_path / "rep2.md"

    run_wave_f1_intake(out_dir=out1, evidence_out=ev1, report_out=rep1)
    run_wave_f1_intake(out_dir=out2, evidence_out=ev2, report_out=rep2)

    g1_bytes = (out1 / "mapeogeo_v0_21_f1_graph.json.gz").read_bytes()
    g2_bytes = (out2 / "mapeogeo_v0_21_f1_graph.json.gz").read_bytes()
    assert g1_bytes == g2_bytes, "Gzipped graph serialization is not byte-identical"

    ev1_bytes = ev1.read_bytes()
    ev2_bytes = ev2.read_bytes()
    assert ev1_bytes == ev2_bytes, "Scientific evidence serialization is not byte-identical"
