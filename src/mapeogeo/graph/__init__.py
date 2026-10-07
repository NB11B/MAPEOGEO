"""Graph and Topology Substrate Layer.

Provides canonical domain-neutral DAG structures, evidentiary relation
contracts, transactional mutations, and deterministic serialization.
"""

from __future__ import annotations

from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node, NodeKind, NodeRegistry, NodeRole
from mapeogeo.graph.relation import RelationType, check_relation_strength_invariance
from mapeogeo.graph.serialization import (
    deserialize_edge,
    deserialize_node,
    deserialize_snapshot,
    serialize_edge,
    serialize_node,
    serialize_snapshot,
)
from mapeogeo.graph.transaction import (
    AcyclicInvariant,
    DanglingEdgeInvariant,
    GraphInvariant,
    GraphSnapshot,
    GraphTransaction,
    TransactionCertificate,
)

__all__ = [
    "AcyclicInvariant",
    "DanglingEdgeInvariant",
    "DecisionGraph",
    "Edge",
    "EdgeContract",
    "GraphInvariant",
    "GraphSnapshot",
    "GraphTransaction",
    "Node",
    "NodeKind",
    "NodeRegistry",
    "NodeRole",
    "RelationType",
    "TransactionCertificate",
    "check_relation_strength_invariance",
    "deserialize_edge",
    "deserialize_node",
    "deserialize_snapshot",
    "serialize_edge",
    "serialize_node",
    "serialize_snapshot",
]
