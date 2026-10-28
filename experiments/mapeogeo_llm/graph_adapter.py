"""Read-only adapter for MAPEOGEOv2 graph snapshot schema version 1."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


RELATIONS = {
    "CANDIDATE_REPRESENTS",
    "SCOPED_OVERLAP",
    "REPRESENTS",
    "EQUIVALENT_TO",
    "SAME_SEMANTICS",
}
KINDS = {"QUERY", "COMPOSE", "GUARD", "DECIDE", "GENERIC"}
ROLES = {
    "ATOMIC_JUDGMENT",
    "DETERMINISTIC_COMPOSE",
    "CONTROL_GUARD",
    "POLICY_DECISION",
    "PASS_THROUGH",
}
STRONG_RELATIONS = {"EQUIVALENT_TO", "SAME_SEMANTICS"}


def _topology_hash(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    canonical_nodes = sorted(
        ({"id": node["node_id"], "k": node["kind"], "r": node["role"]} for node in nodes),
        key=lambda item: item["id"],
    )
    canonical_edges = sorted(
        ({"s": edge["source_id"], "t": edge["target_id"], "r": edge["relation"]} for edge in edges),
        key=lambda item: (item["s"], item["t"], item["r"]),
    )
    digest = hashlib.sha256()
    digest.update(json.dumps(canonical_nodes).encode())
    digest.update(b"\n")
    digest.update(json.dumps(canonical_edges).encode())
    return digest.hexdigest()


class GraphAdapter:
    """Load one immutable snapshot and return evidence-labelled adjacency records."""

    def __init__(
        self,
        snapshot_path: str | Path,
        *,
        source_commit: str,
        source_repository: str = "NB11B/MAPEOGEOv2",
    ):
        path = Path(snapshot_path)
        raw = path.read_bytes()
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("graph snapshot must be UTF-8 JSON") from exc
        self._validate(payload)
        if not isinstance(source_commit, str) or len(source_commit) != 40 or any(
            char not in "0123456789abcdef" for char in source_commit.lower()
        ):
            raise ValueError("source_commit must be a full 40-character Git SHA")
        self._snapshot = deepcopy(payload)
        self._nodes = {node["node_id"]: node for node in payload["nodes"]}
        self._digest = hashlib.sha256(raw).hexdigest()
        self._source_commit = source_commit.lower()
        self._source_repository = source_repository

    @staticmethod
    def _validate(payload: Any) -> None:
        if not isinstance(payload, dict):
            raise ValueError("graph snapshot must be an object")
        if payload.get("schema") != "mapeogeo.graph.snapshot" or payload.get("schema_version") != 1:
            raise ValueError("unsupported graph snapshot schema")
        if not isinstance(payload.get("snapshot_id"), str) or not payload["snapshot_id"]:
            raise ValueError("snapshot_id must be a non-empty string")
        nodes, edges = payload.get("nodes"), payload.get("edges")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("nodes and edges must be arrays")
        node_ids: set[str] = set()
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("nodes must be objects")
            node_id = node.get("node_id")
            if not isinstance(node_id, str) or not node_id or node_id in node_ids:
                raise ValueError("node IDs must be unique non-empty strings")
            if node.get("kind", "GENERIC") not in KINDS or node.get("role", "PASS_THROUGH") not in ROLES:
                raise ValueError("unknown node kind or role")
            if not isinstance(node.get("metadata", {}), dict):
                raise ValueError("node metadata must be an object")
            node_ids.add(node_id)
            node.setdefault("kind", "GENERIC")
            node.setdefault("role", "PASS_THROUGH")
        edge_keys: set[tuple[str, str, str]] = set()
        for edge in edges:
            if not isinstance(edge, dict) or edge.get("source_id") not in node_ids or edge.get("target_id") not in node_ids:
                raise ValueError("graph contains a malformed or dangling edge")
            relation = edge.get("relation")
            if relation not in RELATIONS:
                raise ValueError("unknown graph relation")
            key = (edge["source_id"], edge["target_id"], relation)
            if edge["source_id"] == edge["target_id"] or key in edge_keys:
                raise ValueError("self-loops and duplicate edges are forbidden")
            contract = edge.get("contract")
            if contract is not None and not isinstance(contract, dict):
                raise ValueError("edge contract must be an object or null")
            if relation in STRONG_RELATIONS and not (
                isinstance(contract, dict)
                and contract.get("is_certified") is True
                and isinstance(contract.get("certificate_id"), str)
                and contract["certificate_id"]
            ):
                raise ValueError("strong semantic relations require certified metadata")
            edge_keys.add(key)
        if payload.get("state_hash") != _topology_hash(nodes, edges):
            raise ValueError("graph snapshot state_hash does not match topology")

    def query(self, node_id: str, relation: str | None = None, max_results: int = 32) -> dict[str, Any]:
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("node_id must be a non-empty string")
        if relation is not None and relation not in RELATIONS:
            raise ValueError("unknown relation filter")
        if type(max_results) is not int or not 1 <= max_results <= 1024:
            raise ValueError("max_results must be an integer in [1, 1024]")
        if node_id not in self._nodes:
            raise KeyError(node_id)
        selected = []
        for edge in self._snapshot["edges"]:
            if edge["source_id"] != node_id or (relation is not None and edge["relation"] != relation):
                continue
            contract = edge.get("contract")
            if edge["relation"] == "CANDIDATE_REPRESENTS":
                evidence_class = "candidate"
            elif isinstance(contract, dict) and contract.get("is_certified") is True:
                evidence_class = "certified_metadata"
            else:
                evidence_class = "declared"
            item = deepcopy(edge)
            item.update(
                {
                    "evidence_class": evidence_class,
                    "proof_replayed": False,
                    "proof_verified": False,
                }
            )
            selected.append(item)
            if len(selected) == max_results:
                break
        return {
            "node": deepcopy(self._nodes[node_id]),
            "edges": selected,
            "snapshot": {
                "schema": "mapeogeo.graph.snapshot",
                "schema_version": 1,
                "snapshot_id": self._snapshot["snapshot_id"],
                "state_hash": self._snapshot["state_hash"],
                "digest_sha256": self._digest,
                "source_repository": self._source_repository,
                "source_commit": self._source_commit,
                "read_only": True,
            },
        }
