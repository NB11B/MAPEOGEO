from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_JSONL = (
    ROOT / "operator_atlas" / "operators.jsonl",
    ROOT / "corpus" / "sources.jsonl",
    ROOT / "corpus" / "source_fragments.jsonl",
    ROOT / "graph" / "equations.jsonl",
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


def load_records(paths: Iterable[Path] = CANONICAL_JSONL) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(read_jsonl(path))
    return records


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
