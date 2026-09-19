#!/usr/bin/env python3
"""Foundation connectivity and fail-closed proof-grounding metrics."""

from __future__ import annotations

import collections
from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

RAW_BIDIRECTIONAL_TYPES = {"SAME_SEMANTICS", "SCOPED_OVERLAP", "RELATED_TO"}
RAW_DIRECTIONAL_TYPES = {
    "REPRESENTS",
    "UPWARD_FOUNDATION_DEPENDENCY",
    "PROOF_DEPENDENCY",
    "STRUCTURAL_REFERENCE",
}
PROOF_BIDIRECTIONAL_TYPES = {"SAME_SEMANTICS"}
PROOF_DIRECTIONAL_TYPES = {
    "REPRESENTS",
    "UPWARD_FOUNDATION_DEPENDENCY",
    "PROOF_DEPENDENCY",
    "CANDIDATE_EO",
    "CANDIDATE_GEO",
}
INACTIVE_STATUSES = {"REJECTED", "SUPERSEDED", "UNRESOLVED", "WOUND"}
STATUS_FIELDS = (
    "status",
    "alignment_status",
    "cross_source_status",
    "relation_status",
    "evidence_status",
)


@dataclass(frozen=True)
class RegisteredEdgeEvidence:
    """Closed-registry certificate binding one exact edge to exact endpoints."""

    edge_id: str
    edge_type: str
    source: str
    target: str
    endpoint_identity_sha256: tuple[tuple[str, str], ...]
    evidence_contract_digest: str
    source_statement_sha256: str | None
    evidence_digest: str


EDGE_EVIDENCE_CONTRACT_DIGEST = hashlib.sha256(
    b"MAPEOGEO:registered-edge-evidence:v1"
).hexdigest()


def node_identity_sha256(node: dict[str, Any]) -> str:
    payload = json.dumps(
        node,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def bound_edge_evidence_sha256(
    edge_type: str,
    source: str,
    target: str,
    endpoint_identity_sha256: dict[str, str],
    evidence_contract_digest: str,
) -> str:
    payload = {
        "edge_type": edge_type,
        "source": source,
        "target": target,
        "endpoint_identity_sha256": endpoint_identity_sha256,
        "evidence_contract_digest": evidence_contract_digest,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _node_statement_hash(node: dict[str, Any]) -> str | None:
    attrs = node.get("attributes", {})
    direct = attrs.get("statement_sha256") or attrs.get("source_segment_sha256")
    if direct:
        return direct
    return attrs.get("independent_profile", {}).get("statement_sha256")


def _source_identity_for_metrics(node: dict[str, Any]) -> str | None:
    attrs = node.get("attributes", {})
    return attrs.get("source_id") or attrs.get("source")


def _edge_status(edge: dict[str, Any]) -> str:
    attrs = edge.get("attributes", {})
    return str(
        attrs.get("status")
        or attrs.get("alignment_status")
        or attrs.get("cross_source_status")
        or "ACTIVE"
    ).upper()


def _has_inactive_status(edge: dict[str, Any]) -> bool:
    attrs = edge.get("attributes", {})
    return any(
        str(attrs.get(field, "")).upper() in INACTIVE_STATUSES
        for field in STATUS_FIELDS
    )


def build_registered_edge_evidence(
    *,
    edge_id: str,
    edge_type: str,
    source: str,
    target: str,
    nodes: dict[str, dict[str, Any]],
    source_statement_sha256: str | None = None,
) -> tuple[dict[str, Any], RegisteredEdgeEvidence]:
    """Create a registry record and matching edge; missing or invalid inputs fail closed."""
    if edge_type not in PROOF_DIRECTIONAL_TYPES | PROOF_BIDIRECTIONAL_TYPES:
        raise ValueError(f"unsupported proof edge type: {edge_type}")
    if source not in nodes or target not in nodes:
        raise ValueError("registered edge endpoint is missing")
    endpoint_hashes = {
        source: node_identity_sha256(nodes[source]),
        target: node_identity_sha256(nodes[target]),
    }
    if edge_type == "REPRESENTS":
        actual_hash = _node_statement_hash(nodes[source])
        if not actual_hash or source_statement_sha256 != actual_hash:
            raise ValueError("REPRESENTS evidence requires the exact source statement hash")
    digest = bound_edge_evidence_sha256(
        edge_type,
        source,
        target,
        endpoint_hashes,
        EDGE_EVIDENCE_CONTRACT_DIGEST,
    )
    record = RegisteredEdgeEvidence(
        edge_id=edge_id,
        edge_type=edge_type,
        source=source,
        target=target,
        endpoint_identity_sha256=tuple(sorted(endpoint_hashes.items())),
        evidence_contract_digest=EDGE_EVIDENCE_CONTRACT_DIGEST,
        source_statement_sha256=source_statement_sha256,
        evidence_digest=digest,
    )
    attrs: dict[str, Any] = {
        "relation_status": "VERIFIED",
        "evidence_status": "VERIFIED",
        "evidence_digest": digest,
        "evidence_contract_digest": EDGE_EVIDENCE_CONTRACT_DIGEST,
        "evidence_subject_ids": [source, target],
        "endpoint_identity_sha256": endpoint_hashes,
    }
    if source_statement_sha256 is not None:
        attrs["source_statement_sha256"] = source_statement_sha256
    edge = {
        "id": edge_id,
        "type": edge_type,
        "source": source,
        "target": target,
        "attributes": attrs,
    }
    return edge, record


def _raw_edge_eligible(edge: dict[str, Any], _nodes: dict[str, dict[str, Any]]) -> bool:
    if edge.get("type") == "HAS_WOUND" or _has_inactive_status(edge):
        return False
    return edge.get("type") in RAW_DIRECTIONAL_TYPES | RAW_BIDIRECTIONAL_TYPES


def _proof_edge_eligible(
    edge: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
    registry: dict[str, RegisteredEdgeEvidence],
) -> bool:
    edge_type = edge.get("type")
    if edge_type not in PROOF_DIRECTIONAL_TYPES | PROOF_BIDIRECTIONAL_TYPES:
        return False
    if _has_inactive_status(edge):
        return False
    attrs = edge.get("attributes", {})
    if attrs.get("evidence_status") != "VERIFIED":
        return False
    digest = attrs.get("evidence_digest", "")
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        return False
    source = edge.get("source")
    target = edge.get("target")
    subjects = attrs.get("evidence_subject_ids")
    if not isinstance(subjects, list) or set(subjects) != {source, target}:
        return False
    endpoint_hashes = attrs.get("endpoint_identity_sha256")
    contract_digest = attrs.get("evidence_contract_digest", "")
    if not isinstance(endpoint_hashes, dict) or set(endpoint_hashes) != {source, target}:
        return False
    if any(
        not isinstance(value, str) or not SHA256_RE.fullmatch(value)
        for value in endpoint_hashes.values()
    ):
        return False
    if not isinstance(contract_digest, str) or not SHA256_RE.fullmatch(contract_digest):
        return False
    if endpoint_hashes[source] != node_identity_sha256(nodes[source]):
        return False
    if endpoint_hashes[target] != node_identity_sha256(nodes[target]):
        return False
    expected_digest = bound_edge_evidence_sha256(
        edge_type,
        source,
        target,
        endpoint_hashes,
        contract_digest,
    )
    if digest != expected_digest:
        return False
    record = registry.get(digest)
    if record is None:
        return False
    expected_record = RegisteredEdgeEvidence(
        edge_id=str(edge.get("id", "")),
        edge_type=str(edge_type),
        source=str(source),
        target=str(target),
        endpoint_identity_sha256=tuple(sorted(endpoint_hashes.items())),
        evidence_contract_digest=contract_digest,
        source_statement_sha256=attrs.get("source_statement_sha256"),
        evidence_digest=digest,
    )
    if record != expected_record:
        return False
    if edge_type == "REPRESENTS":
        if nodes[source].get("type") not in {"SOURCE_DECLARATION", "STATEMENT"}:
            return False
        if nodes[target].get("type") != "CANONICAL_OBJECT":
            return False
        actual_hash = _node_statement_hash(nodes[source])
        bound_hash = attrs.get("source_statement_sha256")
        if not actual_hash or bound_hash != actual_hash or not SHA256_RE.fullmatch(bound_hash):
            return False
    if edge_type == "SAME_SEMANTICS":
        if any(
            nodes[node_id].get("type") not in {"SOURCE_DECLARATION", "STATEMENT"}
            for node_id in (source, target)
        ):
            return False
    if edge_type == "UPWARD_FOUNDATION_DEPENDENCY":
        if nodes[source].get("type") != "CANONICAL_OBJECT":
            return False
        if not nodes[source].get("attributes", {}).get("is_foundation", False):
            return False
        if nodes[target].get("type") != "CANONICAL_OBJECT":
            return False
    return True


def _build_adjacency(
    graph: dict[str, Any],
    eligibility: Callable[[dict[str, Any], dict[str, dict[str, Any]]], bool],
    *,
    bidirectional_types: set[str],
) -> tuple[dict[str, list[str]], dict[str, int]]:
    nodes = {node["id"]: node for node in graph.get("nodes", []) if node.get("id")}
    adjacency: dict[str, list[str]] = collections.defaultdict(list)
    diagnostics = {"dangling_edges": 0, "ineligible_edges": 0, "eligible_edges": 0}
    for edge in graph.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        if source not in nodes or target not in nodes:
            diagnostics["dangling_edges"] += 1
            continue
        if not eligibility(edge, nodes):
            diagnostics["ineligible_edges"] += 1
            continue
        diagnostics["eligible_edges"] += 1
        adjacency[source].append(target)
        if edge.get("type") in bidirectional_types:
            adjacency[target].append(source)
    for source in adjacency:
        adjacency[source] = sorted(set(adjacency[source]))
    return adjacency, diagnostics


def _channel_metrics(
    graph: dict[str, Any],
    adjacency: dict[str, list[str]],
    *,
    seed_ids: set[str],
) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    foundation_source_ids = {
        node["id"]
        for node in nodes
        if node.get("type") in {"SOURCE_DECLARATION", "STATEMENT"}
        and node.get("attributes", {}).get("source_id") == "FOUNDATION_MATHEMATICS_BASE"
    }
    foundation_canonical_ids = {
        node["id"]
        for node in nodes
        if node.get("type") == "CANONICAL_OBJECT"
        and node.get("attributes", {}).get("is_foundation", False)
    }
    foundation_primitives = set(seed_ids)
    advanced = [
        node
        for node in nodes
        if node.get("type") == "CANONICAL_OBJECT"
        and not node.get("attributes", {}).get("is_foundation", False)
    ]
    advanced_ids = {node["id"] for node in advanced}

    distances: dict[str, int] = {}
    queue: collections.deque[str] = collections.deque()
    for source in sorted(foundation_primitives):
        distances[source] = 0
        queue.append(source)
    while queue:
        current = queue.popleft()
        for neighbor in adjacency.get(current, []):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)

    reachable = sorted(advanced_ids & distances.keys())
    unreachable = sorted(advanced_ids - distances.keys())
    depths = [distances[node_id] for node_id in reachable]
    by_domain: dict[str, list[int]] = collections.defaultdict(list)
    for node in advanced:
        if node["id"] in distances:
            by_domain[node.get("attributes", {}).get("domain", "Unknown")].append(distances[node["id"]])

    return {
        "foundation_primitives_count": len(foundation_primitives),
        "foundation_source_declarations": len(foundation_source_ids),
        "foundation_canonical_objects": len(foundation_canonical_ids),
        "advanced_canonical_objects_total": len(advanced_ids),
        "advanced_canonical_objects_reachable": len(reachable),
        "advanced_canonical_objects_unreachable": len(unreachable),
        "foundation_reachability_pct": round(100.0 * len(reachable) / max(1, len(advanced_ids)), 2),
        "reachable_ids": reachable,
        "unreachable_ids": unreachable,
        "vertical_depth_stats": {
            "min_depth": min(depths) if depths else None,
            "max_depth": max(depths) if depths else None,
            "avg_depth": round(sum(depths) / len(depths), 3) if depths else None,
        },
        "depth_by_domain": {
            domain: {
                "count": len(values),
                "avg_depth": round(sum(values) / len(values), 2),
                "min_depth": min(values),
                "max_depth": max(values),
            }
            for domain, values in sorted(by_domain.items())
        },
    }


def compute_foundation_metrics(
    graph: dict[str, Any],
    *,
    edge_evidence_registry: dict[str, RegisteredEdgeEvidence] | None = None,
    validated_root_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Return separate descriptive topology and evidence-qualified channels."""
    raw_adjacency, raw_diagnostics = _build_adjacency(
        graph, _raw_edge_eligible, bidirectional_types=RAW_BIDIRECTIONAL_TYPES
    )
    registry = edge_evidence_registry or {}
    nodes_by_id = {node["id"]: node for node in graph.get("nodes", []) if node.get("id")}
    requested_roots = validated_root_ids or set()
    valid_roots = {
        root_id
        for root_id in requested_roots
        if root_id in nodes_by_id
        and nodes_by_id[root_id].get("type") in {"SOURCE_DECLARATION", "STATEMENT"}
        and _source_identity_for_metrics(nodes_by_id[root_id]) == "FOUNDATION_MATHEMATICS_BASE"
    }
    proof_adjacency, proof_diagnostics = _build_adjacency(
        graph,
        lambda edge, nodes: _proof_edge_eligible(edge, nodes, registry),
        bidirectional_types=PROOF_BIDIRECTIONAL_TYPES,
    )
    raw_seed_ids = {
        node_id
        for node_id, node in nodes_by_id.items()
        if (
            node.get("type") in {"SOURCE_DECLARATION", "STATEMENT"}
            and _source_identity_for_metrics(node) == "FOUNDATION_MATHEMATICS_BASE"
        )
        or (
            node.get("type") == "CANONICAL_OBJECT"
            and node.get("attributes", {}).get("is_foundation", False)
        )
    }
    return {
        "raw_topology_reachability": _channel_metrics(
            graph, raw_adjacency, seed_ids=raw_seed_ids
        ),
        "proof_eligible_grounding": _channel_metrics(
            graph, proof_adjacency, seed_ids=valid_roots
        ),
        "diagnostics": {
            "dangling_edges": max(raw_diagnostics["dangling_edges"], proof_diagnostics["dangling_edges"]),
            "raw": raw_diagnostics,
            "proof_eligible": proof_diagnostics,
        },
        "policy": {
            "raw_directional_edge_types": sorted(RAW_DIRECTIONAL_TYPES),
            "raw_bidirectional_edge_types": sorted(RAW_BIDIRECTIONAL_TYPES),
            "proof_directional_edge_types": sorted(PROOF_DIRECTIONAL_TYPES),
            "proof_bidirectional_edge_types": sorted(PROOF_BIDIRECTIONAL_TYPES),
            "diagnostic_edges_are_evidence": False,
            "proof_roots_require_explicit_validation": True,
            "registered_edge_evidence_required": True,
        },
    }


def main() -> int:
    graph_path = ROOT / "artifacts" / "foundation_backfill" / "mapeogeo_foundation_graph.json.gz"
    if not graph_path.exists():
        print(f"Graph not found at {graph_path}, run foundation_intake.py first.")
        return 1
    with gzip.open(graph_path, "rt", encoding="utf-8") as handle:
        graph = json.load(handle)
    print(json.dumps(compute_foundation_metrics(graph), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
