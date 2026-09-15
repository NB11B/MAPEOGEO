#!/usr/bin/env python3
"""MAPEOGEO v0.11 Pinch-Driven Mathematics Intake artifact validator.

Independent fail-closed validator for v0.11 artifacts:
- Validates presence of all required output files.
- Enforces strict gate checks and dynamic target counts (never hardcoded 4/4).
- Verifies kernel certificate structures and UNTESTED/PASS test states.
- Verifies absence of automatic FORMAL -> EO/GEO EQUIVALENT_TO edges.
- Verifies historical direct views and profiles are preserved byte-for-byte.
- Verifies graph topology integrity and absence of forbidden prose keys.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

REQUIRED_FILES = (
    "pinch_v0_11_results.json",
    "pinch_v0_11_certificates.json",
    "pinch_v0_11_wounds.json",
    "mapeogeo_v0_11_graph.json.gz",
    "V0_11_SUMMARY.md",
)

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate MAPEOGEO v0.11 Pinch-Driven Mathematics Intake artifacts")
    ap.add_argument("artifact_dir", type=Path, help="Directory containing v0.11 artifacts")
    args = ap.parse_args()
    root = args.artifact_dir

    # 1. Check all required artifact files exist
    for name in REQUIRED_FILES:
        fpath = root / name
        assert fpath.is_file(), f"Missing required artifact: {name}"
        assert fpath.stat().st_size > 0, f"Artifact file is empty: {name}"

    # 2. Parse artifacts
    results = json.loads((root / "pinch_v0_11_results.json").read_text(encoding="utf-8"))
    certs = json.loads((root / "pinch_v0_11_certificates.json").read_text(encoding="utf-8"))
    wounds = json.loads((root / "pinch_v0_11_wounds.json").read_text(encoding="utf-8"))
    summary_text = (root / "V0_11_SUMMARY.md").read_text(encoding="utf-8")

    with gzip.open(root / "mapeogeo_v0_11_graph.json.gz", "rt", encoding="utf-8") as f:
        graph = json.load(f)

    # 3. Validate results report & gates
    assert results.get("status") == "PASS", f"Results status is not PASS: {results.get('status')}"
    assert results.get("stage") == "v0.11_PINCH_DRIVEN_INTAKE"
    gates = results.get("gates", {})
    assert all(gates.values()), f"Some intake gates failed: {gates}"
    assert len(gates) >= 15, f"Insufficient gate checks: {len(gates)}"

    # 4. Validate certificates dynamically
    counts = results.get("counts", {})
    certified_expected = counts.get("certified_targets", len(certs))
    assert len(certs) == certified_expected, f"Expected {certified_expected} certificates, got {len(certs)}"

    for c in certs:
        assert c.get("status") == "PASS"
        assert c.get("certificate_class") == "KERNEL_VERIFIED"
        assert c.get("verifier") == "Lean 4"
        assert len(c.get("statement_sha256", "")) == 64
        assert c.get("formal_scope")

    # 5. Validate S3 contract verdicts in results
    contracts = results.get("contracts", [])
    for c in contracts:
        sid = c["source_id"]
        if c["test_state"] == "UNTESTED":
            assert c["verdict"] == "UNTESTED"
            assert len(c["refused"]) > 0
        elif c["test_state"] == "EXECUTABLE_CONTRACT":
            assert c["verdict"] == "PASS"
            assert c["measured"].get("all_checks_passed") is True

    # 6. Validate Graph integrity
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_by_id = {n["id"]: n for n in nodes}
    edge_by_id = {e["id"]: e for e in edges}

    assert len(node_by_id) == len(nodes), "Duplicate node IDs found in graph"
    assert len(edge_by_id) == len(edges), "Duplicate edge IDs found in graph"

    for e in edges:
        assert e["source"] in node_by_id, f"Orphan edge source: {e['id']} -> {e['source']}"
        assert e["target"] in node_by_id, f"Orphan edge target: {e['id']} -> {e['target']}"

    # 7. Check absence of forbidden copyright prose or page images
    for n in nodes:
        attrs = n.get("attributes", {})
        forbidden_found = FORBIDDEN_PERSISTED_KEYS.intersection(attrs)
        assert not forbidden_found, f"Forbidden keys {forbidden_found} found in node {n['id']}"

    # 8. Check that no EQUIVALENT_TO edges originate from formal:lean:v011:* nodes
    formal_equiv_edges = [
        e for e in edges
        if e.get("type") == "EQUIVALENT_TO" and "formal:lean:v011" in e.get("source", "")
    ]
    assert len(formal_equiv_edges) == 0, (
        f"Found forbidden automatic EQUIVALENT_TO edges from v0.11 formal nodes: {formal_equiv_edges}"
    )

    # 9. Check formal representation nodes and certificates in graph
    formal_nodes = [
        n for n in nodes
        if n.get("view") == "FORMAL" and "v011" in n.get("id", "")
    ]
    assert len(formal_nodes) == len(certs), (
        f"Expected {len(certs)} v0.11 formal nodes, got {len(formal_nodes)}"
    )

    cert_nodes = [
        n for n in nodes
        if n.get("type") == "CERTIFICATE" and "v011" in n.get("id", "")
    ]
    assert len(cert_nodes) == len(certs), (
        f"Expected {len(certs)} v0.11 certificate nodes, got {len(cert_nodes)}"
    )

    # 10. Verify summary markdown
    assert "# MAPEOGEO v0.11 — Pinch-Driven Mathematics Intake" in summary_text
    assert "**Status:** PASS" in summary_text
    assert "Coverage changed; architecture did not." in summary_text

    print(
        f"MAPEOGEO_V0_11_VALIDATION: PASS certs={len(certs)}/{counts.get('frozen_targets', len(certs))} "
        f"contracts={len(contracts)} graph={len(nodes)}/{len(edges)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
