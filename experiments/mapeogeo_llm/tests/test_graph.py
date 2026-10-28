from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.mapeogeo_llm.graph_adapter import GraphAdapter


FIXTURE = Path(__file__).parent / "fixtures" / "graph_snapshot.json"
SOURCE_COMMIT = "64a36dce10000e47bc4c651e7b92f14e28c68652"


def test_query_preserves_candidate_and_certified_metadata_without_proof_promotion() -> None:
    result = GraphAdapter(FIXTURE, source_commit=SOURCE_COMMIT).query("candidate")
    assert result["node"]["node_id"] == "candidate"
    assert result["snapshot"]["source_commit"] == SOURCE_COMMIT
    assert len(result["snapshot"]["digest_sha256"]) == 64
    edge = result["edges"][0]
    assert edge["relation"] == "CANDIDATE_REPRESENTS"
    assert edge["evidence_class"] == "candidate"
    assert edge["proof_replayed"] is False
    assert edge["proof_verified"] is False

    certified_metadata = GraphAdapter(FIXTURE, source_commit=SOURCE_COMMIT).query("result")["edges"][0]
    assert certified_metadata["relation"] == "EQUIVALENT_TO"
    assert certified_metadata["evidence_class"] == "certified_metadata"
    assert certified_metadata["contract"]["is_certified"] is True
    assert certified_metadata["proof_replayed"] is False
    assert certified_metadata["proof_verified"] is False


def test_relation_filter_and_result_bound_are_enforced() -> None:
    adapter = GraphAdapter(FIXTURE, source_commit=SOURCE_COMMIT)
    assert adapter.query("candidate", relation="REPRESENTS")["edges"] == []
    assert len(adapter.query("candidate", max_results=1)["edges"]) == 1
    with pytest.raises(ValueError):
        adapter.query("candidate", max_results=0)
    with pytest.raises(ValueError):
        adapter.query("candidate", relation="MADE_UP")


def test_snapshot_is_read_only_after_adapter_construction(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_bytes(FIXTURE.read_bytes())
    adapter = GraphAdapter(snapshot, source_commit=SOURCE_COMMIT)
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    data["nodes"][0]["node_id"] = "mutated"
    snapshot.write_text(json.dumps(data), encoding="utf-8")
    assert adapter.query("candidate")["node"]["node_id"] == "candidate"


def test_invalid_snapshot_schema_hash_and_dangling_edges_fail_closed(tmp_path: Path) -> None:
    base = json.loads(FIXTURE.read_text(encoding="utf-8"))
    variants = []
    wrong_schema = dict(base, schema="not.a.snapshot")
    variants.append(wrong_schema)
    wrong_hash = dict(base, state_hash="0" * 64)
    variants.append(wrong_hash)
    dangling = json.loads(FIXTURE.read_text(encoding="utf-8"))
    dangling["edges"][0]["target_id"] = "missing"
    variants.append(dangling)
    for index, payload in enumerate(variants):
        path = tmp_path / f"bad-{index}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError):
            GraphAdapter(path, source_commit=SOURCE_COMMIT)


def test_unknown_node_is_a_lookup_error() -> None:
    with pytest.raises(KeyError):
        GraphAdapter(FIXTURE, source_commit=SOURCE_COMMIT).query("absent")


def test_live_mapeogeov2_serializer_snapshot_is_accepted(tmp_path: Path) -> None:
    source_root = Path(r"C:\Users\nateb\Documents\MAPEOGEOv2")
    assert source_root.is_dir(), "pinned MAPEOGEOv2 checkout is required"
    snapshot = tmp_path / "live-snapshot.json"
    script = """
from pathlib import Path
from mapeogeo.graph.edge import Edge
from mapeogeo.graph.node import Node, NodeKind, NodeRole
from mapeogeo.graph.relation import RelationType
from mapeogeo.graph.serialization import serialize_snapshot
from mapeogeo.graph.transaction import GraphSnapshot

nodes = [
    Node(node_id='live-query', kind=NodeKind.QUERY, role=NodeRole.ATOMIC_JUDGMENT),
    Node(node_id='live-result', kind=NodeKind.DECIDE, role=NodeRole.POLICY_DECISION),
]
edges = [Edge(source_id='live-query', target_id='live-result', relation=RelationType.CANDIDATE_REPRESENTS)]
Path(__import__('sys').argv[1]).write_text(serialize_snapshot(GraphSnapshot.create('live-v2', nodes, edges)), encoding='utf-8')
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(source_root / "src")
    subprocess.run(
        [sys.executable, "-c", script, str(snapshot)],
        cwd=source_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        shell=False,
    )
    result = GraphAdapter(snapshot, source_commit=SOURCE_COMMIT).query("live-query")
    assert result["snapshot"]["snapshot_id"] == "live-v2"
    assert result["edges"][0]["evidence_class"] == "candidate"
