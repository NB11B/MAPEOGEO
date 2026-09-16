#!/usr/bin/env python3
"""Source identity, dependency, and detector state auditor for MAPEOGEO v0.11."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import sys
from typing import Any


def load_graph(graph_path: Path | str) -> dict[str, Any]:
    p = Path(graph_path)
    if p.suffix == ".gz":
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(p.read_text(encoding="utf-8"))


def audit_targets(graph: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    """Audit v0.11 pinch targets against the base graph nodes and explicit dependencies."""
    by_id = {n["id"]: n for n in graph.get("nodes", [])}

    dep_map: dict[str, set[str]] = {}
    for edge in graph.get("edges", []):
        if edge.get("type") == "DEPENDS_ON":
            dep_map.setdefault(edge["source"], set()).add(edge["target"])

    rows: list[dict[str, Any]] = []

    for target in bindings.get("targets", []):
        source_id = target["source_id"]
        node = by_id.get(source_id)

        profile = (
            None
            if node is None
            else node.get("attributes", {}).get("independent_profile", {})
        )

        expected_hash = target.get("statement_sha256")
        expected_status = target.get("expected_direct_status")
        expected_deps = set(target.get("explicit_dependencies", []))

        actual_hash = profile.get("statement_sha256") if profile else None
        actual_status = profile.get("direct_status") if profile else None
        actual_deps = dep_map.get(source_id, set())

        hash_match = (actual_hash == expected_hash) if profile else False
        direct_state_match = (actual_status == expected_status) if profile else False
        dependencies_present = expected_deps.issubset(actual_deps)

        rows.append({
            "source_id": source_id,
            "node_present": node is not None,
            "hash_match": hash_match,
            "actual_hash": actual_hash,
            "expected_hash": expected_hash,
            "direct_state_match": direct_state_match,
            "actual_status": actual_status,
            "expected_status": expected_status,
            "dependencies_present": dependencies_present,
            "missing_dependencies": sorted(list(expected_deps - actual_deps)),
            "formal_decl": target.get("formal_decl"),
            "scope_status": target.get("scope_status"),
            "s3_test_state": target.get("s3_test_state"),
        })

    all_hashes = all(r["hash_match"] for r in rows)
    all_states = all(r["direct_state_match"] for r in rows)
    all_deps = all(r["dependencies_present"] for r in rows)
    audit_passed = all_hashes and all_states and all_deps

    return {
        "targets": rows,
        "all_hashes_match": all_hashes,
        "all_direct_states_match": all_states,
        "all_explicit_dependencies_present": all_deps,
        "audit_passed": audit_passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v0.11 source targets against graph.")
    parser.add_argument("source_pdf", nargs="?", default=None, help="Optional path to source PDF for transient audit")
    parser.add_argument(
        "--graph",
        default=Path(__file__).resolve().parents[1] / "artifacts" / "proof_paths_v0_9" / "mapeogeo_s5_v0_9_graph.json.gz",
        help="Path to base graph JSON or JSON.GZ",
    )
    parser.add_argument(
        "--bindings",
        default=Path(__file__).resolve().parents[1] / "formal" / "pinch_bindings_v0_11.json",
        help="Path to formal/pinch_bindings_v0_11.json",
    )
    parser.add_argument("--out", required=False, help="Path to output audit JSON")
    args = parser.parse_args()

    graph_path = Path(args.graph)
    if not graph_path.exists():
        fallback = Path(__file__).resolve().parents[1] / "data" / "gallier_quaintance_graph_v0_3.json.gz"
        if fallback.exists():
            graph_path = fallback
    graph = load_graph(graph_path)
    bindings = json.loads(Path(args.bindings).read_text(encoding="utf-8"))

    results = audit_targets(graph, bindings)

    if args.out:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"v0.11 Source Audit: {'PASS' if results['audit_passed'] else 'FAIL'}")
    for r in results["targets"]:
        print(f"  - {r['source_id']}: hash={r['hash_match']} state={r['direct_state_match']} deps={r['dependencies_present']}")

    return 0 if results["audit_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
