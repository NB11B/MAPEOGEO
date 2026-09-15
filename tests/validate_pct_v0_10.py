#!/usr/bin/env python3
"""Strict deterministic acceptance artifact validator for MAPEOGEO PCT v0.10."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mapeogeo.pct.artifacts import FORBIDDEN_GRAPH_KEYS


REQUIRED_FILES = [
    "manifest.json",
    "hashes.json",
    "objects/fixtures.json",
    "probes/responses.json",
    "complexes/chain_data.json",
    "maps/chain_maps.json",
    "homology/betti.json",
    "persistence/pairs.json",
    "geometry/metrics.json",
    "event_ledger/events.json",
    "reconstruction/results.json",
    "negative_controls/results.json",
    "residuals/results.json",
    "validity.json",
    "scientific_result.json",
    "pct_graph_fragment.json",
    "summary.md",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_pct_artifacts(artifacts_dir: Path | str) -> tuple[bool, str]:
    art_path = Path(artifacts_dir)
    if not art_path.is_dir():
        return False, f"Artifacts directory does not exist: {art_path}"

    # 1. Check all required files exist
    for f_rel in REQUIRED_FILES:
        target = art_path / f_rel
        if not target.is_file():
            return False, f"Missing required artifact: {f_rel}"

    # 2. Check manifest.json
    manifest_data = json.loads((art_path / "manifest.json").read_text(encoding="utf-8"))
    if manifest_data.get("run_id") != "MAPEOGEO-PCT-V0.10":
        return False, f"Unexpected manifest run_id: {manifest_data.get('run_id')}"

    # 3. Check hashes.json integrity
    hashes_data: dict[str, str] = json.loads((art_path / "hashes.json").read_text(encoding="utf-8"))
    for rel_path_str, expected_hash in hashes_data.items():
        actual_file = art_path / rel_path_str
        if not actual_file.is_file():
            return False, f"File listed in hashes.json does not exist: {rel_path_str}"
        actual_hash = sha256_file(actual_file)
        if actual_hash != expected_hash:
            return False, f"SHA-256 mismatch for {rel_path_str}: expected {expected_hash}, got {actual_hash}"

    # Check that no unhashed files exist in artifacts directory
    for p in art_path.rglob("*"):
        if p.is_file() and p.name != "hashes.json":
            rel_str = p.relative_to(art_path).as_posix()
            if rel_str not in hashes_data:
                return False, f"Unhashed artifact file found: {rel_str}"

    # 4. Check validity.json
    validity_data = json.loads((art_path / "validity.json").read_text(encoding="utf-8"))
    if validity_data.get("ENGINE_VALIDITY") != "PASS":
        return False, f"ENGINE_VALIDITY is not PASS: {validity_data.get('ENGINE_VALIDITY')}"

    gates = validity_data.get("validity_gates", {})
    required_gates = ["V0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]
    for g in required_gates:
        if g not in gates:
            return False, f"Missing validity gate: {g}"
        g_verdict = gates[g].get("verdict") if isinstance(gates[g], dict) else getattr(gates[g], "verdict", None)
        if g_verdict != "PASS":
            return False, f"Gate {g} verdict is not PASS: {g_verdict}"

    # 5. Check negative controls
    neg_data = json.loads((art_path / "negative_controls" / "results.json").read_text(encoding="utf-8"))
    if not neg_data.get("corrupted_chain_map", {}).get("rejected", False):
        return False, "Corrupted chain map was not properly rejected in negative controls"
    if not neg_data.get("reentrant_applicability_refusal", {}).get("refused_properly", False):
        return False, "Reentrant geometry was not properly refused in negative controls"
    if not neg_data.get("corrupted_probe_response", {}).get("detected_properly", False):
        return False, "Corrupted probe response was not properly detected in negative controls"

    # 6. Check scientific_result.json
    sci_data = json.loads((art_path / "scientific_result.json").read_text(encoding="utf-8"))
    sci_result = sci_data.get("SCIENTIFIC_RESULT")
    if sci_result not in {"H1_SUPPORTED", "H1_NOT_SUPPORTED", "INCONCLUSIVE"}:
        return False, f"Invalid SCIENTIFIC_RESULT value: {sci_result}"

    sci_tests = sci_data.get("scientific_tests", {})
    required_s = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
    for s in required_s:
        if s not in sci_tests:
            return False, f"Missing scientific test record: {s}"

    base_matrix = sci_data.get("baseline_matrix", {})
    for b in ["B0", "B1", "B2", "B3", "B4", "B5"]:
        if b not in base_matrix.get("S1", {}) or b not in base_matrix.get("S3", {}):
            return False, f"Baseline {b} missing from baseline matrix"

    # 7. Check pct_graph_fragment.json
    graph_data = json.loads((art_path / "pct_graph_fragment.json").read_text(encoding="utf-8"))
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    node_ids = {n["id"] for n in nodes}
    if len(node_ids) != len(nodes):
        return False, "Duplicate node IDs in graph fragment"

    edge_ids = {e["id"] for e in edges}
    if len(edge_ids) != len(edges):
        return False, "Duplicate edge IDs in graph fragment"

    for e in edges:
        if e["source"] not in node_ids:
            return False, f"Graph edge source not in nodes: {e['source']}"
        if e["target"] not in node_ids:
            return False, f"Graph edge target not in nodes: {e['target']}"

    for n in nodes:
        for k in FORBIDDEN_GRAPH_KEYS:
            if k in n or k in n.get("attributes", {}):
                return False, f"Forbidden key {k} found in graph node {n.get('id')}"
        if n.get("type") == "CERTIFICATE":
            if n.get("certificate_class") == "KERNEL_VERIFIED":
                return False, "Executable PCT certificate incorrectly labeled KERNEL_VERIFIED"

    msg = f"MAPEOGEO_PCT_V0_10_ARTIFACT_VALIDATION: PASS (files={len(hashes_data)}, validity={validity_data.get('ENGINE_VALIDITY')}, result={sci_result})"
    return True, msg


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MAPEOGEO PCT v0.10 sealed artifacts.")
    parser.add_argument(
        "artifacts_dir",
        nargs="?",
        default="artifacts/pct_v0_10",
        help="Path to sealed artifacts directory",
    )
    args = parser.parse_args()

    ok, msg = validate_pct_artifacts(args.artifacts_dir)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
