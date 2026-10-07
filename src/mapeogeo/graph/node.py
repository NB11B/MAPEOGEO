"""Graph node primitives and registry.

Domain-neutral representation of execution and judgment units.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class NodeKind(StrEnum):
    """Categorical kind of node in a decision graph."""

    QUERY = "QUERY"
    COMPOSE = "COMPOSE"
    GUARD = "GUARD"
    DECIDE = "DECIDE"
    GENERIC = "GENERIC"


class NodeRole(StrEnum):
    """Execution or judgment role assigned to a node."""

    ATOMIC_JUDGMENT = "ATOMIC_JUDGMENT"
    DETERMINISTIC_COMPOSE = "DETERMINISTIC_COMPOSE"
    CONTROL_GUARD = "CONTROL_GUARD"
    POLICY_DECISION = "POLICY_DECISION"
    PASS_THROUGH = "PASS_THROUGH"


@dataclass(frozen=True)
class Node:
    """Canonical domain-neutral graph node.

    Must not contain domain semantics (no math theorem strings, no physical equations).
    """

    node_id: str
    kind: NodeKind = NodeKind.GENERIC
    role: NodeRole = NodeRole.PASS_THROUGH
    scope_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id or not self.node_id.strip():
            raise ValueError("node_id must be a non-empty string")


class NodeRegistry:
    """Namespace-isolated registry of nodes."""

    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self._nodes: dict[str, Node] = {}

    def register(self, node: Node) -> None:
        """Register a node, raising ValueError on collision."""
        if node.node_id in self._nodes:
            raise ValueError(
                f"Node '{node.node_id}' already registered in namespace '{self.namespace}'"
            )
        self._nodes[node.node_id] = node

    def get(self, node_id: str) -> Node | None:
        """Retrieve node by ID."""
        return self._nodes.get(node_id)

    def require(self, node_id: str) -> Node:
        """Retrieve node or raise KeyError."""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not found in namespace '{self.namespace}'")
        return self._nodes[node_id]

    def all_nodes(self) -> list[Node]:
        """Return all registered nodes in sorted order."""
        return sorted(self._nodes.values(), key=lambda n: n.node_id)

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes
