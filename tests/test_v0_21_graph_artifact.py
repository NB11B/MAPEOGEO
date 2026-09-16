from __future__ import annotations

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_GRAPH = ROOT / "artifacts" / "foundation_backfill" / "mapeogeo_foundation_graph.json.gz"
V021_GRAPH = ROOT / "artifacts" / "rigor_v0_21" / "mapeogeo_v0_21_graph.json.gz"
FORBIDDEN_RELATIONS = {
    "SAME_SEMANTICS",
    "SCOPED_OVERLAP",
    "RELATED_TO",
    "REPRESENTS",
    "FORMAL_LINKED",
    "KERNEL_VERIFIED",
    "PROOF_DEPENDENCY",
}


def _load(path: Path) -> dict:
    assert path.exists(), f"required reconstructed graph missing: {path}"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def test_reconstructed_v0_21_graph_is_exact_quarantined_source_expansion():
    base = _load(FOUNDATION_GRAPH)
    graph = _load(V021_GRAPH)

    new_declarations = [
        node
        for node in graph["nodes"]
        if node.get("type") == "SOURCE_DECLARATION"
        and node.get("attributes", {}).get("stage") == "v0.21"
    ]
    source_roots = [
        node
        for node in graph["nodes"]
        if node.get("type") == "SOURCE_CORPUS"
        and node.get("attributes", {}).get("stage") == "v0.21"
    ]
    new_ids = {node["id"] for node in new_declarations}
    new_edges = [
        edge
        for edge in graph["edges"]
        if edge.get("attributes", {}).get("stage") == "v0.21"
    ]

    assert len(new_declarations) == 2075
    assert len(new_ids) == 2075
    assert len(source_roots) == 5
    assert len(new_edges) == 2075
    assert all(edge["type"] == "SOURCE_CONTAINS_DECLARATION" for edge in new_edges)
    assert all(edge["target"] in new_ids for edge in new_edges)
    assert not any(
        edge.get("type") in FORBIDDEN_RELATIONS
        and (edge.get("source") in new_ids or edge.get("target") in new_ids)
        for edge in graph["edges"]
    )

    assert sum(node["attributes"]["canonical_status"] == "UNRESOLVED" for node in new_declarations) == 2075
    assert sum(node["attributes"]["formal_status"] == "UNFORMALIZED" for node in new_declarations) == 2075
    assert sum(node["attributes"]["executable_status"] == "UNTESTED" for node in new_declarations) == 2075

    # v0.21 is append-only over the accepted foundation graph.
    assert graph["nodes"][: len(base["nodes"])] == base["nodes"]
    assert graph["edges"][: len(base["edges"])] == base["edges"]
    assert len(graph["nodes"]) == len(base["nodes"]) + 2080
    assert len(graph["edges"]) == len(base["edges"]) + 2075
