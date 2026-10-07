"""Deterministic serialization for graph primitives and snapshots.

Enforces:
    serialize(X) == serialize(X) byte-for-byte across runs.
Explicit schemas and schema versions.
"""

from __future__ import annotations

import json
from typing import Any

from tools.deterministic_json import serialize_deterministic

from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node, NodeKind, NodeRole
from mapeogeo.graph.relation import RelationType
from mapeogeo.graph.transaction import GraphSnapshot


def serialize_node(node: Node) -> str:
    """Serialize a Node to deterministic JSON string."""
    data = {
        "schema": "mapeogeo.graph.node",
        "schema_version": 1,
        "node_id": node.node_id,
        "kind": node.kind.value,
        "role": node.role.value,
        "scope_hash": node.scope_hash,
        "metadata": node.metadata,
    }
    return serialize_deterministic(data)


def deserialize_node(raw_json: str | dict[str, Any]) -> Node:
    """Deserialize JSON data to Node."""
    data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
    if data.get("schema") != "mapeogeo.graph.node":
        raise ValueError(f"Invalid schema: {data.get('schema')}")
    return Node(
        node_id=data["node_id"],
        kind=NodeKind(data.get("kind", "GENERIC")),
        role=NodeRole(data.get("role", "PASS_THROUGH")),
        scope_hash=data.get("scope_hash", ""),
        metadata=data.get("metadata", {}),
    )


def serialize_edge(edge: Edge) -> str:
    """Serialize an Edge to deterministic JSON string."""
    contract_data = None
    if edge.contract is not None:
        contract_data = {
            "contract_id": edge.contract.contract_id,
            "required_relation": edge.contract.required_relation.value,
            "is_certified": edge.contract.is_certified,
            "certificate_id": edge.contract.certificate_id,
        }

    data = {
        "schema": "mapeogeo.graph.edge",
        "schema_version": 1,
        "source_id": edge.source_id,
        "target_id": edge.target_id,
        "relation": edge.relation.value,
        "port_binding": edge.port_binding,
        "contract": contract_data,
        "metadata": edge.metadata,
    }
    return serialize_deterministic(data)


def deserialize_edge(raw_json: str | dict[str, Any]) -> Edge:
    """Deserialize JSON data to Edge."""
    data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
    if data.get("schema") != "mapeogeo.graph.edge":
        raise ValueError(f"Invalid schema: {data.get('schema')}")

    contract = None
    if data.get("contract") is not None:
        c_data = data["contract"]
        contract = EdgeContract(
            contract_id=c_data["contract_id"],
            required_relation=RelationType(c_data["required_relation"]),
            is_certified=c_data.get("is_certified", False),
            certificate_id=c_data.get("certificate_id"),
        )

    return Edge(
        source_id=data["source_id"],
        target_id=data["target_id"],
        relation=RelationType(data["relation"]),
        contract=contract,
        port_binding=data.get("port_binding", "default"),
        metadata=data.get("metadata", {}),
    )


def serialize_snapshot(snapshot: GraphSnapshot) -> str:
    """Serialize a GraphSnapshot to deterministic JSON string."""
    node_payloads = [
        {
            "node_id": n.node_id,
            "kind": n.kind.value,
            "role": n.role.value,
            "scope_hash": n.scope_hash,
            "metadata": n.metadata,
        }
        for n in snapshot.nodes
    ]
    edge_payloads = [
        {
            "source_id": e.source_id,
            "target_id": e.target_id,
            "relation": e.relation.value,
            "port_binding": e.port_binding,
            "contract": (
                {
                    "contract_id": e.contract.contract_id,
                    "required_relation": e.contract.required_relation.value,
                    "is_certified": e.contract.is_certified,
                    "certificate_id": e.contract.certificate_id,
                }
                if e.contract
                else None
            ),
            "metadata": e.metadata,
        }
        for e in snapshot.edges
    ]

    data = {
        "schema": "mapeogeo.graph.snapshot",
        "schema_version": 1,
        "snapshot_id": snapshot.snapshot_id,
        "state_hash": snapshot.state_hash,
        "nodes": sorted(node_payloads, key=lambda d: str(d["node_id"])),
        "edges": sorted(
            edge_payloads,
            key=lambda d: (str(d["source_id"]), str(d["target_id"]), str(d["relation"])),
        ),
    }
    return serialize_deterministic(data)


def deserialize_snapshot(raw_json: str | dict[str, Any]) -> GraphSnapshot:
    """Deserialize JSON data to GraphSnapshot."""
    data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
    if data.get("schema") != "mapeogeo.graph.snapshot":
        raise ValueError(f"Invalid schema: {data.get('schema')}")

    nodes = [
        Node(
            node_id=nd["node_id"],
            kind=NodeKind(nd.get("kind", "GENERIC")),
            role=NodeRole(nd.get("role", "PASS_THROUGH")),
            scope_hash=nd.get("scope_hash", ""),
            metadata=nd.get("metadata", {}),
        )
        for nd in data.get("nodes", [])
    ]

    edges = []
    for ed in data.get("edges", []):
        contract = None
        if ed.get("contract") is not None:
            c = ed["contract"]
            contract = EdgeContract(
                contract_id=c["contract_id"],
                required_relation=RelationType(c["required_relation"]),
                is_certified=c.get("is_certified", False),
                certificate_id=c.get("certificate_id"),
            )
        edges.append(
            Edge(
                source_id=ed["source_id"],
                target_id=ed["target_id"],
                relation=RelationType(ed["relation"]),
                contract=contract,
                port_binding=ed.get("port_binding", "default"),
                metadata=ed.get("metadata", {}),
            )
        )

    return GraphSnapshot.create(
        snapshot_id=data["snapshot_id"],
        nodes=nodes,
        edges=edges,
    )
