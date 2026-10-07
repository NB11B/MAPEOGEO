"""DecisionGraph high-level container and query engine.

Domain-neutral container for DAG-based decision and execution representations.
"""

from __future__ import annotations

import uuid

from mapeogeo.graph.edge import Edge
from mapeogeo.graph.node import Node
from mapeogeo.graph.transaction import GraphSnapshot, GraphTransaction


class DecisionGraph:
    """High-level container managing an immutable GraphSnapshot through transactions."""

    def __init__(
        self,
        graph_id: str,
        initial_nodes: list[Node] | None = None,
        initial_edges: list[Edge] | None = None,
    ) -> None:
        self.graph_id = graph_id
        nodes = initial_nodes or []
        edges = initial_edges or []
        self._current_snapshot = GraphSnapshot.create(
            snapshot_id=f"init-{graph_id}",
            nodes=nodes,
            edges=edges,
        )

    @property
    def snapshot(self) -> GraphSnapshot:
        """Current committed graph snapshot."""
        return self._current_snapshot

    @property
    def nodes(self) -> tuple[Node, ...]:
        return self._current_snapshot.nodes

    @property
    def edges(self) -> tuple[Edge, ...]:
        return self._current_snapshot.edges

    def get_node(self, node_id: str) -> Node | None:
        for n in self._current_snapshot.nodes:
            if n.node_id == node_id:
                return n
        return None

    def parents(self, node_id: str) -> list[str]:
        """Return source IDs of all edges directed into node_id."""
        return sorted([e.source_id for e in self._current_snapshot.edges if e.target_id == node_id])

    def children(self, node_id: str) -> list[str]:
        """Return target IDs of all edges directed out of node_id."""
        return sorted([e.target_id for e in self._current_snapshot.edges if e.source_id == node_id])

    def topological_sort(self) -> list[str]:
        """Compute deterministic topological ordering of node IDs."""
        adj: dict[str, list[str]] = {n.node_id: [] for n in self._current_snapshot.nodes}
        in_degree: dict[str, int] = {n.node_id: 0 for n in self._current_snapshot.nodes}

        for e in self._current_snapshot.edges:
            adj[e.source_id].append(e.target_id)
            in_degree[e.target_id] += 1

        # Deterministic queue sorted lexicographically
        ready = sorted([nid for nid, deg in in_degree.items() if deg == 0])
        order: list[str] = []

        while ready:
            curr = ready.pop(0)
            order.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    ready.append(neighbor)
            ready.sort()

        if len(order) != len(self._current_snapshot.nodes):
            raise ValueError("Graph contains cycles; cannot topologically sort")

        return order

    def begin_transaction(self, transaction_id: str | None = None) -> GraphTransaction:
        """Start a new transaction against the current snapshot."""
        tx_id = transaction_id or f"tx-{uuid.uuid4().hex[:8]}"
        return GraphTransaction(initial_snapshot=self._current_snapshot, transaction_id=tx_id)

    def apply_snapshot(self, snapshot: GraphSnapshot) -> None:
        """Commit an external or newly produced snapshot to this graph."""
        self._current_snapshot = snapshot
