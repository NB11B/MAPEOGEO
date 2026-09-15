#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

REQUIRED_FILES = (
    "pinch_quartet_v0_10_report.json",
    "pinch_quartet_kernel_certificates_v0_10.json",
    "mapeogeo_v0_10_graph.json.gz",
    "V0_10_SUMMARY.md",
)

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

TARGET_IDS = {
    "srcdecl:proposition:3_14",
    "srcdecl:proposition:3_13",
    "srcdecl:theorem:27_10",
    "srcdecl:proposition:4_4",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate MAPEOGEO v0.10 Pinch Quartet Promotion artifacts")
    ap.add_argument("artifact_dir", type=Path)
    args = ap.parse_args()
    root = args.artifact_dir

    for name in REQUIRED_FILES:
        assert (root / name).is_file(), f"missing required artifact: {name}"

    report = json.loads((root / "pinch_quartet_v0_10_report.json").read_text(encoding="utf-8"))
    certs = json.loads((root / "pinch_quartet_kernel_certificates_v0_10.json").read_text(encoding="utf-8"))
    with gzip.open(root / "mapeogeo_v0_10_graph.json.gz", "rt", encoding="utf-8") as f:
        graph = json.load(f)

    assert report["status"] == "PASS"
    assert all(report["gates"].values()), report["gates"]
    assert len(certs) == 4
    assert {c["source_id"] for c in certs} == TARGET_IDS
    assert all(c["certificate_class"] == "KERNEL_VERIFIED" and c["status"] == "PASS" for c in certs)

    # Validate graph integrity
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_by_id = {n["id"]: n for n in nodes}
    assert len(node_by_id) == len(nodes)
    assert len({e["id"] for e in edges}) == len(edges)
    assert all(e["source"] in node_by_id and e["target"] in node_by_id for e in edges)

    # Check forbidden keys
    for n in nodes:
        attrs = n.get("attributes", {})
        assert not FORBIDDEN_PERSISTED_KEYS.intersection(attrs), f"Forbidden key in node {n['id']}"

    # Check formal nodes and certificates are in graph
    formal_nodes = [n for n in nodes if n.get("view") == "FORMAL" and "v010" in n.get("id", "") or any(t.replace("srcdecl:", "").replace(":", "_") in n["id"] for t in TARGET_IDS)]
    assert len(formal_nodes) >= 4

    print(f"MAPEOGEO_V0_10_ARTIFACT_VALIDATION: PASS certs={len(certs)} nodes={len(nodes)} edges={len(edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
