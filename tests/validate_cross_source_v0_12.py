#!/usr/bin/env python3
"""MAPEOGEO v0.12 Cross-Source Expansion Fail-Closed Artifact Validator.

Validates that all v0.12 expansion artifacts adhere to the preregistration specification:
- Artifact presence and integrity (graph gzip, alignments, metrics, scientific results).
- Strict zero-prose persistence compliance (no statement_text, proof_text, source_prose, page_image).
- Tolerances compliance (N_source, N_canonical, N_cross_source, unresolved_rate).
- 3-layer ontology graph integrity (Source Declarations -> Canonical Objects -> Views).
- Cross-source alignment consistency.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}


def load_json_or_gz(path: Path) -> dict:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def validate_artifacts(
    artifacts_dir: Path,
    prereg_path: Path = ROOT / "evidence" / "v0_12_preregistration.json",
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # 1. Check artifact files existence
    graph_path = artifacts_dir / "mapeogeo_v0_12_graph.json.gz"
    align_path = artifacts_dir / "cross_source_alignments.json"
    metrics_path = artifacts_dir / "expansion_metrics.json"
    results_path = artifacts_dir / "scientific_results.json"

    for p in [graph_path, align_path, metrics_path, results_path]:
        if not p.exists():
            errors.append(f"Missing required artifact: {p.name}")

    if errors:
        return False, errors

    # 2. Check Preregistration
    if not prereg_path.exists():
        errors.append(f"Missing preregistration file: {prereg_path}")
        return False, errors

    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    tolerances = prereg.get("tolerances", {})

    # 3. Validate Graph & Zero-Prose Policy
    graph = load_json_or_gz(graph_path)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        errors.append("Graph contains 0 nodes")
    if not edges:
        errors.append("Graph contains 0 edges")

    for node in nodes:
        nid = node.get("id", "UNKNOWN")
        attrs = node.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            if forbidden in node:
                errors.append(f"Zero-prose violation: node '{nid}' contains top-level key '{forbidden}'")
            if forbidden in attrs:
                errors.append(f"Zero-prose violation: node '{nid}' attributes contain key '{forbidden}'")

    for edge in edges:
        eid = edge.get("id", "UNKNOWN")
        attrs = edge.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            if forbidden in edge:
                errors.append(f"Zero-prose violation: edge '{eid}' contains top-level key '{forbidden}'")
            if forbidden in attrs:
                errors.append(f"Zero-prose violation: edge '{eid}' attributes contain key '{forbidden}'")

    # 4. Validate Node & Edge Ontology
    node_types = set(n.get("type") for n in nodes)
    edge_types = set(e.get("type") for e in edges)

    if "CANONICAL_OBJECT" not in node_types:
        errors.append("Graph missing CANONICAL_OBJECT node type")
    if not ({"SOURCE_DECLARATION", "DECLARATION"} & node_types):
        errors.append("Graph missing SOURCE_DECLARATION node type")
    if "REPRESENTS" not in edge_types:
        errors.append("Graph missing REPRESENTS edge type")

    # 5. Validate Alignments
    alignments = json.loads(align_path.read_text(encoding="utf-8"))
    total_canonical = alignments.get("total_canonical_objects", 0)
    aligned_canonical = alignments.get("aligned_canonical_objects", 0)
    if total_canonical == 0:
        errors.append("Alignments report 0 total canonical objects")
    if aligned_canonical == 0:
        errors.append("Alignments report 0 aligned canonical objects")

    # 6. Validate Metrics against Preregistration
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    dashboard = metrics.get("primary_dashboard", {})
    coverage = metrics.get("coverage_metrics", {})

    n_source = dashboard.get("N_source", 0)
    n_canonical = dashboard.get("N_canonical", 0)
    n_cross_source = dashboard.get("N_cross_source", 0)
    unresolved_rate = coverage.get("unresolved_rate", 1.0)

    min_axler = tolerances.get("min_axler_declarations", 30)
    min_canonical = tolerances.get("min_canonical_objects", 25)
    min_matches = tolerances.get("min_cross_source_matches", 15)
    max_unresolved = tolerances.get("max_unresolved_rate", 0.50)

    if n_source < min_axler:
        errors.append(f"N_source ({n_source}) below preregistered minimum ({min_axler})")
    if n_canonical < min_canonical:
        errors.append(f"N_canonical ({n_canonical}) below preregistered minimum ({min_canonical})")
    if n_cross_source < min_matches:
        errors.append(f"N_cross_source ({n_cross_source}) below preregistered minimum ({min_matches})")
    if unresolved_rate > max_unresolved:
        errors.append(f"unresolved_rate ({unresolved_rate}) exceeds preregistered maximum ({max_unresolved})")

    # 7. Validate Scientific Results
    results = json.loads(results_path.read_text(encoding="utf-8"))
    eval_block = results.get("evaluation", {})
    if eval_block.get("engine_validity") != "VALID":
        errors.append(f"Scientific results engine_validity is {eval_block.get('engine_validity')}, expected VALID")
    if eval_block.get("scientific_result") != "PASS":
        errors.append(f"Scientific results scientific_result is {eval_block.get('scientific_result')}, expected PASS")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MAPEOGEO v0.12 Cross-Source Expansion Artifacts")
    parser.add_argument("artifacts_dir", type=Path, nargs="?", default=ROOT / "artifacts" / "cross_source_v0_12")
    parser.add_argument("--preregistration", type=Path, default=ROOT / "evidence" / "v0_12_preregistration.json")
    args = parser.parse_args()

    print(f"Validating v0.12 artifacts in {args.artifacts_dir}...")
    success, errors = validate_artifacts(args.artifacts_dir, args.preregistration)

    if success:
        print("PASS: All v0.12 cross-source expansion validation gates passed successfully.")
        return 0
    else:
        print("FAIL: Validation failures detected:")
        for err in errors:
            print(f"  - {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
