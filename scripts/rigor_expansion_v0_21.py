#!/usr/bin/env python3
"""Provenance-only graph intake for MAPEOGEO v0.21.

v0.21 deliberately expands source coverage without automatic semantic promotion.
New source declarations enter canonical quarantine and receive only corpus
containment edges.
"""

import argparse
import copy
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.io_utils import atomic_write_deterministic_json_gzip
from scripts.source_admission_v0_21 import validate_admitted_metadata
from scripts.source_registry_v0_21 import load_source_registry

STAGE = "v0.21"
FORBIDDEN_NEW_RELATIONS = {
    "SAME_SEMANTICS",
    "SCOPED_OVERLAP",
    "RELATED_TO",
    "REPRESENTS",
    "FORMAL_LINKED",
    "KERNEL_VERIFIED",
    "PROOF_DEPENDENCY",
}


def _load_json_or_gz(path: Path) -> dict:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(path.read_text(encoding="utf-8"))


def _source_root_id(source_id: str) -> str:
    return f"source:v0_21:{source_id}"


def integrate_quarantined_sources(graph: dict, specs, metadata_rows: list[dict]) -> dict:
    """Append v0.21 source records and provenance containment edges only."""
    validate_admitted_metadata(metadata_rows)
    source_specs = {spec.source_id: spec for spec in specs}
    if len(source_specs) != len(specs):
        raise ValueError("duplicate source_id in v0.21 intake specs")

    nodes = graph.setdefault("nodes", [])
    edges = graph.setdefault("edges", [])
    by_id = {node.get("id"): node for node in nodes}
    edge_ids = {edge.get("id") for edge in edges}

    # Source roots are provenance objects, never mathematical declarations.
    for spec in sorted(specs, key=lambda item: item.source_id):
        root_id = _source_root_id(spec.source_id)
        if root_id in by_id:
            raise ValueError(f"node ID collision during v0.21 intake: {root_id}")
        root = {
            "id": root_id,
            "type": "SOURCE_CORPUS",
            "label": spec.source_id,
            "attributes": {
                "source_id": spec.source_id,
                "repository": spec.repository,
                "revision": spec.revision,
                "parser": spec.parser,
                "license": spec.license,
                "scope": spec.scope,
                "stage": STAGE,
                "provenance_status": "PINNED_SOURCE",
            },
        }
        nodes.append(root)
        by_id[root_id] = root

    new_node_ids: set[str] = set()
    for row in sorted(
        metadata_rows,
        key=lambda item: (
            item["source_id"],
            item["source_path"],
            item["line_start"],
            item["structured_id"],
            item["node_id"],
        ),
    ):
        spec = source_specs.get(row["source_id"])
        if spec is None:
            raise ValueError(f"unregistered v0.21 source: {row['source_id']}")
        if row["repository"] != spec.repository or row["revision"] != spec.revision:
            raise ValueError(f"source provenance mismatch for {row['node_id']}")

        node_id = row["node_id"]
        if node_id in by_id:
            raise ValueError(f"node ID collision during v0.21 intake: {node_id}")
        attrs = {
            key: value
            for key, value in row.items()
            if key not in {"node_id", "node_type"}
        }
        attrs["stage"] = STAGE
        node = {
            "id": node_id,
            "type": "SOURCE_DECLARATION",
            "label": row["structured_id"],
            "attributes": attrs,
        }
        nodes.append(node)
        by_id[node_id] = node
        new_node_ids.add(node_id)

        root_id = _source_root_id(row["source_id"])
        edge_id = f"e:v0_21:contains:{row['source_id']}:{node_id}"
        if edge_id in edge_ids:
            raise ValueError(f"edge ID collision during v0.21 intake: {edge_id}")
        edge = {
            "id": edge_id,
            "type": "SOURCE_CONTAINS_DECLARATION",
            "source": root_id,
            "target": node_id,
            "attributes": {
                "stage": STAGE,
                "relation_status": "PROVENANCE_ONLY",
            },
        }
        edges.append(edge)
        edge_ids.add(edge_id)

    # Fail closed if any future edit accidentally creates authority-bearing
    # relations from the newly admitted source records.
    for edge in edges:
        if edge.get("source") in new_node_ids or edge.get("target") in new_node_ids:
            if edge.get("type") in FORBIDDEN_NEW_RELATIONS:
                raise ValueError(
                    f"v0.21 quarantined declaration received forbidden relation {edge.get('type')}: {edge.get('id')}"
                )
            if edge.get("attributes", {}).get("stage") == STAGE and edge.get("type") != "SOURCE_CONTAINS_DECLARATION":
                raise ValueError(f"v0.21 emitted non-provenance edge: {edge.get('id')}")

    return graph


def build_v0_21_graph(base_graph: dict, registry_path: Path, declarations_path: Path) -> dict:
    specs = load_source_registry(registry_path)
    payload = json.loads(declarations_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "v0.21":
        raise ValueError("v0.21 declaration manifest schema mismatch")
    rows = payload.get("declarations")
    if not isinstance(rows, list):
        raise ValueError("v0.21 declaration manifest must contain declarations list")
    return integrate_quarantined_sources(copy.deepcopy(base_graph), specs, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Integrate quarantined v0.21 source declarations")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "foundation_backfill" / "mapeogeo_foundation_graph.json.gz",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "formal" / "source_registry_v0_21.json",
    )
    parser.add_argument(
        "--declarations",
        type=Path,
        default=ROOT / "formal" / "source_declarations_v0_21.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "rigor_v0_21" / "mapeogeo_v0_21_graph.json.gz",
    )
    args = parser.parse_args()

    base = _load_json_or_gz(args.base_graph)
    graph = build_v0_21_graph(base, args.registry, args.declarations)
    atomic_write_deterministic_json_gzip(args.out, graph)
    print(
        json.dumps(
            {
                "stage": STAGE,
                "nodes": len(graph.get("nodes", [])),
                "edges": len(graph.get("edges", [])),
                "output": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
