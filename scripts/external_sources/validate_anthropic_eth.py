"""Validate the Anthropic ETH source-graph staging artifact without promoting evidence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "formal" / "external_sources" / "anthropic_eth_2026_graph.json"
SHA = "16a5ce41304fcdaea4e0be7c132e1c361dc26da5"

def validate(path: Path = GRAPH) -> dict[str, int]:
    g = json.loads(path.read_text(encoding="utf-8"))
    assert g["schema"] == "mapeogeo.external_proof_source_graph.v1"
    assert g["provenance"]["commit"] == SHA
    assert g["integration_status"] == "SOURCE_GRAPH_STAGED_NOT_MERGED_INTO_SEALED_REGISTRY"
    nodes = g["nodes"]
    edges = g["edges"]
    ids = [node["id"] for node in nodes]
    assert len(ids) == len(set(ids)), "Duplicate node identifiers"
    known = set(ids)
    for node in nodes:
        assert node["source_locator"].startswith(
            f"https://github.com/anthropics/formal-math/blob/{SHA}/eth/"
        ), node["id"]
        assert node["expression"], node["id"]
        assert node["verification_status"] == "UPSTREAM_REPORTED_NOT_LOCALLY_KERNEL_VERIFIED"
        assert node["type"] != "KERNEL_VERIFIED"
    assert len(set((e["source"], e["target"], e["relation"]) for e in edges)) == len(edges)
    for edge in edges:
        assert edge["source"] in known and edge["target"] in known, edge
        assert edge["source"] != edge["target"], edge
        assert edge["status"] == "SOURCE_INDEX_OR_MATHEMATICAL_RELATION_UNCERTIFIED"
    assert {"eth:theorem:main", "eth:theorem:eth_false", "eth:bound:recursive_exponent", "eth:identity:eight_square"} <= known
    return {"nodes": len(nodes), "edges": len(edges)}

if __name__ == "__main__":
    print(json.dumps({"status": "PASS", **validate()}, sort_keys=True))
