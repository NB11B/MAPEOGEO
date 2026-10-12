from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
from enum import Enum

class GraphView(str, Enum):
    HISTORICAL = "HISTORICAL"       # Strict historical core: ANC, SOV, RUS
    ANALYTICAL = "ANALYTICAL"       # Historical core plus sealed modern analytical overlay: ANC, SOV, RUS, MOD
    FULL = "FULL"                   # All records including SYN, CASE, OPEN, OP

HISTORICAL_NAMESPACES = frozenset({"ANC", "SOV", "RUS"})
ANALYTICAL_NAMESPACES = frozenset({"ANC", "SOV", "RUS", "MOD"})


def filter_by_view(
    records: Iterable[dict[str, Any]],
    view: GraphView = GraphView.HISTORICAL,
) -> list[dict[str, Any]]:
    """Filters graph records strictly according to the specified graph view."""
    if view == GraphView.FULL:
        return list(records)

    allowed = HISTORICAL_NAMESPACES if view == GraphView.HISTORICAL else ANALYTICAL_NAMESPACES
    nodes, edges = split_records(records)
    
    # 1. Filter nodes
    valid_nodes = [n for n in nodes if n.get("namespace") in allowed]
    valid_node_ids = {n["id"] for n in valid_nodes}

    # 2. Filter edges: must have allowed namespace AND both endpoints must exist in valid_node_ids
    valid_edges = [
        e for e in edges
        if e.get("namespace") in allowed
        and e.get("source") in valid_node_ids
        and e.get("target") in valid_node_ids
    ]
    return valid_nodes + valid_edges


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_JSONL = (
    ROOT / "operator_atlas" / "operators.jsonl",
    ROOT / "corpus" / "sources.jsonl",
    ROOT / "corpus" / "source_fragments.jsonl",
    ROOT / "graph" / "equations.jsonl",
    ROOT / "graph" / "equation_families.jsonl",
    ROOT / "graph" / "invariants.jsonl",
    ROOT / "graph" / "behavioral_tests.jsonl",
    ROOT / "graph" / "assumptions.jsonl",
    ROOT / "graph" / "symbols.jsonl",
    ROOT / "unresolved" / "open_questions.jsonl",
    ROOT / "graph" / "entities.jsonl",
    ROOT / "graph" / "claims.jsonl",
    ROOT / "graph" / "edges.jsonl",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{lineno}: JSONL record must be an object")
        out.append(obj)
    return out


def load_records(paths: Iterable[Path] = CANONICAL_JSONL, view: GraphView = GraphView.HISTORICAL) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(read_jsonl(path))
    return filter_by_view(records, view=view)


def split_records(
    records: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for record in records:
        (edges if record.get("type") == "EDGE" else nodes).append(record)
    return nodes, edges


def canonical_digest(paths: Iterable[Path] = CANONICAL_JSONL) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
        digest.update(b"\0")
        if path.exists():
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def node_index(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        record["id"]: record
        for record in records
        if record.get("type") != "EDGE"
    }
