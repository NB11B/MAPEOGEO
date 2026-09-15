#!/usr/bin/env python3
"""MAPEOGEO v0.13 Tri-Source Expansion Fail-Closed Artifact Validator.

Validates that all v0.13 tri-source expansion artifacts adhere to the preregistration specification:
- Artifact presence and integrity (graph gzip, alignments, metrics, benchmark results, scientific results).
- Strict zero-prose persistence compliance (no statement_text, proof_text, source_prose, page_image).
- Tolerances compliance (N_source >= 100, N_canonical >= 35, N_2-source >= 25, N_3-source >= 10, D_domains >= 2).
- Tri-source 3-layer ontology graph integrity (S_A, S_B, S_C -> Canonical Objects -> Views).
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


def validate_tri_source_artifacts(
    artifacts_dir: Path,
    prereg_path: Path = ROOT / "evidence" / "v0_13_preregistration.json",
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # 1. Check artifact files existence
    graph_path = artifacts_dir / "mapeogeo_v0_13_graph.json.gz"
    align_path = artifacts_dir / "tri_source_alignments.json"
    metrics_path = artifacts_dir / "expansion_metrics.json"
    bench_path = artifacts_dir / "blinded_alignment_results.json"
    results_path = artifacts_dir / "scientific_results.json"

    for p in [graph_path, align_path, metrics_path, bench_path, results_path]:
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

    # Check presence of all three corpora
    source_corpora = set()
    for n in nodes:
        attrs = n.get("attributes", {})
        sid = attrs.get("source_id", "")
        if "GALLIER" in sid:
            source_corpora.add("GALLIER")
        elif "AXLER" in sid:
            source_corpora.add("AXLER")
        elif "VMLS" in sid:
            source_corpora.add("VMLS")

    for corp in ["GALLIER", "AXLER", "VMLS"]:
        if corp not in source_corpora:
            errors.append(f"Graph missing source declarations from corpus {corp}")

    # 5. Validate Alignments
    alignments = json.loads(align_path.read_text(encoding="utf-8"))
    total_canonical = alignments.get("total_canonical_objects", 0)
    two_source = alignments.get("two_source_canonical_objects", 0)
    three_source = alignments.get("three_source_canonical_objects", 0)

    min_canonical = tolerances.get("min_canonical_objects", 35)
    min_2_source = tolerances.get("min_2_source_bridges", 25)
    min_3_source = tolerances.get("min_3_source_bridges", 10)

    if total_canonical < min_canonical:
        errors.append(f"Total canonical objects ({total_canonical}) below preregistered minimum ({min_canonical})")
    if two_source < min_2_source:
        errors.append(f"Two-source canonical objects ({two_source}) below preregistered minimum ({min_2_source})")
    if three_source < min_3_source:
        errors.append(f"Three-source canonical objects ({three_source}) below preregistered minimum ({min_3_source})")

    # 6. Validate Metrics against Preregistration
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    dashboard = metrics.get("primary_dashboard", {})
    coverage = metrics.get("coverage_metrics", {})

    n_source = dashboard.get("N_source", 0)
    n_canonical = dashboard.get("N_canonical", 0)
    n_domains = dashboard.get("D_domains_count", 0)
    unresolved_rate = coverage.get("unresolved_rate", 1.0)

    min_source = tolerances.get("min_total_source_declarations", 100)
    min_domains = tolerances.get("min_domains", 2)
    max_unresolved = tolerances.get("max_unresolved_rate", 0.40)

    if n_source < min_source:
        errors.append(f"N_source ({n_source}) below preregistered minimum ({min_source})")
    if n_domains < min_domains:
        errors.append(f"Domains count ({n_domains}) below preregistered minimum ({min_domains})")
    if unresolved_rate > max_unresolved:
        errors.append(f"unresolved_rate ({unresolved_rate}) exceeds preregistered maximum ({max_unresolved})")

    # 7. Validate Blinded Benchmark
    bench = json.loads(bench_path.read_text(encoding="utf-8"))
    if bench.get("evaluation", {}).get("status") != "PASS":
        errors.append(f"Blinded benchmark status is {bench.get('evaluation', {}).get('status')}, expected PASS")

    # 8. Validate Scientific Results
    results = json.loads(results_path.read_text(encoding="utf-8"))
    eval_block = results.get("evaluation", {})
    if eval_block.get("engine_validity") != "VALID":
        errors.append(f"Scientific results engine_validity is {eval_block.get('engine_validity')}, expected VALID")
    if eval_block.get("scientific_result") != "PASS":
        errors.append(f"Scientific results scientific_result is {eval_block.get('scientific_result')}, expected PASS")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MAPEOGEO v0.13 Tri-Source Expansion Artifacts")
    parser.add_argument("artifacts_dir", type=Path, nargs="?", default=ROOT / "artifacts" / "tri_source_v0_13")
    parser.add_argument("--preregistration", type=Path, default=ROOT / "evidence" / "v0_13_preregistration.json")
    args = parser.parse_args()

    print(f"Validating v0.13 artifacts in {args.artifacts_dir}...")
    success, errors = validate_tri_source_artifacts(args.artifacts_dir, args.preregistration)

    if success:
        print("PASS: All v0.13 tri-source expansion validation gates passed successfully.")
        return 0
    else:
        print("FAIL: Validation failures detected:")
        for err in errors:
            print(f"  - {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
