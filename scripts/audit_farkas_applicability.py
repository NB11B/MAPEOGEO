#!/usr/bin/env python3
"""Audit real MAPEOGEO Farkas routing for exact proof-data availability.

This is deliberately stricter than semantic routing.  It answers:
    Among edges routed to the Farkas family by the current broad
    label heuristic, how many actually persist exact linear-certificate data?

It never invents A, b, c, d, or lambda.
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


FARKAS_TERMS = ("farkas", "inequality", "polytope", "convex")
ELIGIBLE_EDGE_TYPES = {
    "UPWARD_FOUNDATION_DEPENDENCY",
    "PROOF_DEPENDENCY",
}

READY_ENDPOINT = "ENDPOINT_CONTRACT_READY"
READY_EDGE = "EXPLICIT_EDGE_PAYLOAD_READY"
SOURCE_RECOVERY = "SOURCE_RECOVERY_REQUIRED"
LABEL_ONLY = "LABEL_HINT_ONLY"
STRUCTURAL_ONLY = "STRUCTURAL_ONLY"

EXACT_PAYLOAD_KEYS = {
    "certificate_type",
    "matrix",
    "bounds",
    "multipliers",
}


def _load(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("graph root must be object")
    return value


def _source_hash(node: dict[str, Any]) -> str | None:
    attrs = node.get("attributes", {})
    if not isinstance(attrs, dict):
        return None
    value = attrs.get("statement_sha256") or attrs.get("source_segment_sha256")
    profile = attrs.get("independent_profile", {})
    if not value and isinstance(profile, dict):
        value = profile.get("statement_sha256")
    if (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    ):
        return value
    return None


def _records(node: dict[str, Any]) -> list[dict[str, Any]]:
    attrs = node.get("attributes", {})
    if not isinstance(attrs, dict):
        return []
    value = attrs.get("semantic_contracts", [])
    if not isinstance(value, list):
        return []
    return [r for r in value if isinstance(r, dict)]


def _endpoint_farkas_contract(
    source: dict[str, Any],
    target: dict[str, Any],
) -> tuple[bool, str]:
    for left in _records(source):
        for right in _records(target):
            if (
                left.get("binding_mode") == "ENDPOINT_CONTRACT_BOUND"
                and right.get("binding_mode") == "ENDPOINT_CONTRACT_BOUND"
                and left.get("semantic_id") == "GFY.FARKAS_IMPLICATION.v1"
                and left.get("semantic_id") == right.get("semantic_id")
                and left.get("contract_id") == right.get("contract_id")
                and left.get("contract_digest") == right.get("contract_digest")
                and left.get("semantic_payload_sha256")
                == right.get("semantic_payload_sha256")
            ):
                if left.get("role") == "premise" and right.get("role") == "conclusion":
                    return True, str(left.get("contract_id", ""))
    return False, ""


def _edge_payload(edge: dict[str, Any]) -> dict[str, Any] | None:
    attrs = edge.get("attributes", {})
    if not isinstance(attrs, dict):
        return None
    for key in ("farkas_payload", "proof_payload", "semantic_payload"):
        payload = attrs.get(key)
        if (
            isinstance(payload, dict)
            and EXACT_PAYLOAD_KEYS <= set(payload)
            and payload.get("certificate_type") in {"implication", "infeasible"}
        ):
            return payload
    return None


def _farkas_hint(source: dict[str, Any], target: dict[str, Any]) -> bool:
    text = " ".join(
        (
            str(source.get("id", "")),
            str(source.get("label", "")),
            str(target.get("id", "")),
            str(target.get("label", "")),
        )
    ).lower()
    return any(term in text for term in FARKAS_TERMS)


def _canonical_reachability(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[dict[str, set[str]], set[str]]:
    canonical = {
        node_id
        for node_id, node in nodes.items()
        if node.get("type") == "CANONICAL_OBJECT"
    }
    advanced = {
        node_id
        for node_id in canonical
        if not nodes[node_id].get("attributes", {}).get("is_foundation", False)
    }
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge.get("type") in {
            "UPWARD_FOUNDATION_DEPENDENCY",
            "DEPENDS_ON",
            "STRUCTURAL_REFERENCE",
            "STRUCTURAL_DEPENDENCY",
        }:
            source = edge.get("source")
            target = edge.get("target")
            if source in canonical and target in canonical:
                adjacency[str(source)].add(str(target))

    reach: dict[str, set[str]] = {}
    for start in canonical:
        seen: set[str] = set()
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for nxt in adjacency.get(current, set()):
                if nxt not in seen and nxt in advanced:
                    seen.add(nxt)
                    queue.append(nxt)
        reach[start] = seen
    return reach, advanced


def audit(graph_path: Path) -> dict[str, Any]:
    graph = _load(graph_path)
    nodes = {
        str(node["id"]): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }
    edges = [
        edge
        for edge in graph.get("edges", [])
        if isinstance(edge, dict)
    ]

    reach, advanced = _canonical_reachability(nodes, edges)

    rows = []
    all_unlock: set[str] = set()
    ready_unlock: set[str] = set()

    for edge in edges:
        if edge.get("type") not in ELIGIBLE_EDGE_TYPES:
            continue
        source_id = str(edge.get("source", ""))
        target_id = str(edge.get("target", ""))
        source = nodes.get(source_id, {})
        target = nodes.get(target_id, {})
        if not _farkas_hint(source, target):
            continue

        for node_id in (source_id, target_id):
            all_unlock.update(reach.get(node_id, set()))
            if node_id in advanced:
                all_unlock.add(node_id)

        endpoint_ready, contract_id = _endpoint_farkas_contract(source, target)
        payload = _edge_payload(edge)

        if endpoint_ready:
            klass = READY_ENDPOINT
        elif payload is not None:
            klass = READY_EDGE
        elif _source_hash(source) or _source_hash(target):
            klass = SOURCE_RECOVERY
        elif source.get("type") == "CANONICAL_OBJECT" and target.get("type") == "CANONICAL_OBJECT":
            # Current foundation upward dependencies are curated structural
            # candidates; labels alone do not imply a linear inequality theorem.
            klass = LABEL_ONLY
        else:
            klass = STRUCTURAL_ONLY

        if klass in {READY_ENDPOINT, READY_EDGE}:
            for node_id in (source_id, target_id):
                ready_unlock.update(reach.get(node_id, set()))
                if node_id in advanced:
                    ready_unlock.add(node_id)

        rows.append(
            {
                "edge_id": str(edge.get("id", "")),
                "edge_type": str(edge.get("type", "")),
                "source_id": source_id,
                "source_label": source.get("label", source_id),
                "source_type": source.get("type"),
                "target_id": target_id,
                "target_label": target.get("label", target_id),
                "target_type": target.get("type"),
                "audit_class": klass,
                "contract_id": contract_id,
                "has_source_hash": bool(_source_hash(source) or _source_hash(target)),
                "has_explicit_payload": payload is not None,
                "per_edge_delta_g_upper_bound": len(
                    set(reach.get(source_id, set()))
                    | set(reach.get(target_id, set()))
                    | ({source_id} if source_id in advanced else set())
                    | ({target_id} if target_id in advanced else set())
                ),
            }
        )

    counts = Counter(row["audit_class"] for row in rows)
    sample_by_class: dict[str, list[dict[str, Any]]] = {}
    for klass in sorted(counts):
        sample_by_class[klass] = [
            row
            for row in sorted(
                (r for r in rows if r["audit_class"] == klass),
                key=lambda r: (-r["per_edge_delta_g_upper_bound"], r["edge_id"]),
            )[:10]
        ]

    return {
        "schema": "mapeogeo.farkas-applicability-audit.v1",
        "graph": graph_path.as_posix(),
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "farkas_routed_candidates": len(rows),
        "audit_counts": dict(sorted(counts.items())),
        "exact_payload_or_contract_ready": (
            counts.get(READY_ENDPOINT, 0) + counts.get(READY_EDGE, 0)
        ),
        "source_recovery_required": counts.get(SOURCE_RECOVERY, 0),
        "label_hint_only": counts.get(LABEL_ONLY, 0),
        "structural_only": counts.get(STRUCTURAL_ONLY, 0),
        "routed_delta_g_upper_bound": len(all_unlock),
        "exact_ready_delta_g_upper_bound": len(ready_unlock),
        "samples": sample_by_class,
        "claim_boundary": {
            "supported": (
                "Counts persisted exact Farkas contracts/payloads separately "
                "from source-bound recovery opportunities and label-only routing."
            ),
            "not_supported": (
                "Does not infer linear systems or multipliers from labels, "
                "descriptions, topology, or reachability."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--graph",
        type=Path,
        default=Path(
            "artifacts/foundation_backfill/mapeogeo_foundation_graph.json.gz"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "artifacts/farkas_applicability_audit/farkas_applicability_audit.json"
        ),
    )
    args = parser.parse_args()

    result = audit(args.graph)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
