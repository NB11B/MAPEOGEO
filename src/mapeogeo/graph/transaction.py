"""Graph transaction lifecycle and invariant validation.

Enforces:
    proposal -> validation -> certificate -> commit
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Protocol

from mapeogeo.graph.edge import Edge
from mapeogeo.graph.node import Node


class GraphInvariant(Protocol):
    """Protocol for checking structural or relational invariants over a graph."""

    def name(self) -> str:
        """Name of the invariant rule."""
        ...

    def validate(self, nodes: list[Node], edges: list[Edge]) -> tuple[bool, list[str]]:
        """Validate invariant, returning (is_valid, list_of_violations)."""
        ...


class DanglingEdgeInvariant:
    """Ensures every edge connects valid registered nodes."""

    def name(self) -> str:
        return "DANGLING_EDGE_INVARIANT"

    def validate(self, nodes: list[Node], edges: list[Edge]) -> tuple[bool, list[str]]:
        node_ids = {n.node_id for n in nodes}
        violations: list[str] = []
        for e in edges:
            if e.source_id not in node_ids:
                violations.append(f"Edge references nonexistent source_id '{e.source_id}'")
            if e.target_id not in node_ids:
                violations.append(f"Edge references nonexistent target_id '{e.target_id}'")
        return len(violations) == 0, violations


class AcyclicInvariant:
    """Ensures graph forms a directed acyclic graph (DAG)."""

    def name(self) -> str:
        return "ACYCLIC_INVARIANT"

    def validate(self, nodes: list[Node], edges: list[Edge]) -> tuple[bool, list[str]]:
        adj: dict[str, list[str]] = {n.node_id: [] for n in nodes}
        for e in edges:
            if e.source_id in adj:
                adj[e.source_id].append(e.target_id)

        # 0 = unvisited, 1 = visiting (in recursion stack), 2 = visited
        visited: dict[str, int] = {n.node_id: 0 for n in nodes}
        cycles: list[str] = []

        def dfs(node_id: str, path: list[str]) -> bool:
            visited[node_id] = 1
            path.append(node_id)
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    continue
                if visited[neighbor] == 1:
                    cycle_repr = " -> ".join(path + [neighbor])
                    cycles.append(f"Cycle detected: {cycle_repr}")
                    return False
                elif visited[neighbor] == 0:
                    if not dfs(neighbor, path):
                        return False
            path.pop()
            visited[node_id] = 2
            return True

        for n in nodes:
            if visited[n.node_id] == 0:
                if not dfs(n.node_id, []):
                    break

        return len(cycles) == 0, cycles


@dataclass(frozen=True)
class TransactionCertificate:
    """Cryptographic certificate issued when a proposal satisfies all invariants."""

    transaction_id: str
    invariants_passed: tuple[str, ...]
    timestamp: float
    certificate_hash: str


@dataclass(frozen=True)
class GraphSnapshot:
    """Immutable snapshot of committed graph state."""

    snapshot_id: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    state_hash: str
    created_at: float = field(default_factory=time.time)

    @classmethod
    def create(cls, snapshot_id: str, nodes: list[Node], edges: list[Edge]) -> GraphSnapshot:
        sorted_nodes = tuple(sorted(nodes, key=lambda n: n.node_id))
        sorted_edges = tuple(sorted(edges, key=lambda e: e.edge_key))

        # Compute deterministic state hash
        hasher = hashlib.sha256()
        node_repr = json.dumps(
            [{"id": n.node_id, "k": n.kind.value, "r": n.role.value} for n in sorted_nodes]
        )
        edge_repr = json.dumps(
            [{"s": e.source_id, "t": e.target_id, "r": e.relation.value} for e in sorted_edges]
        )
        hasher.update(node_repr.encode())
        hasher.update(b"\n")
        hasher.update(edge_repr.encode())
        state_hash = hasher.hexdigest()

        return cls(
            snapshot_id=snapshot_id,
            nodes=sorted_nodes,
            edges=sorted_edges,
            state_hash=state_hash,
        )


class GraphTransaction:
    """Manages transactional state changes on a decision graph.

    Guarantees proposal -> validation -> certificate -> commit.
    """

    def __init__(self, initial_snapshot: GraphSnapshot, transaction_id: str) -> None:
        self.transaction_id = transaction_id
        self._nodes: dict[str, Node] = {n.node_id: n for n in initial_snapshot.nodes}
        self._edges: dict[tuple[str, str, str], Edge] = {
            e.edge_key: e for e in initial_snapshot.edges
        }
        self._certificate: TransactionCertificate | None = None
        self._is_committed: bool = False

    def add_node(self, node: Node) -> None:
        if self._is_committed:
            raise RuntimeError("Transaction already committed")
        self._nodes[node.node_id] = node
        self._certificate = None  # invalidate previous validation

    def remove_node(self, node_id: str) -> None:
        if self._is_committed:
            raise RuntimeError("Transaction already committed")
        self._nodes.pop(node_id, None)
        # remove incident edges
        self._edges = {
            k: e
            for k, e in self._edges.items()
            if e.source_id != node_id and e.target_id != node_id
        }
        self._certificate = None

    def add_edge(self, edge: Edge) -> None:
        if self._is_committed:
            raise RuntimeError("Transaction already committed")
        self._edges[edge.edge_key] = edge
        self._certificate = None

    def remove_edge(self, source_id: str, target_id: str, relation_val: str) -> None:
        if self._is_committed:
            raise RuntimeError("Transaction already committed")
        self._edges.pop((source_id, target_id, relation_val), None)
        self._certificate = None

    def validate(self, invariants: list[GraphInvariant] | None = None) -> TransactionCertificate:
        """Validate proposed modifications against invariants and produce certificate."""
        if self._is_committed:
            raise RuntimeError("Transaction already committed")

        rules: list[GraphInvariant] = invariants or [
            DanglingEdgeInvariant(),
            AcyclicInvariant(),
        ]
        node_list = list(self._nodes.values())
        edge_list = list(self._edges.values())

        passed_rules: list[str] = []
        all_violations: list[str] = []

        for rule in rules:
            is_valid, violations = rule.validate(node_list, edge_list)
            if not is_valid:
                all_violations.extend(violations)
            else:
                passed_rules.append(rule.name())

        if all_violations:
            raise ValueError("Transaction validation failed:\n" + "\n".join(all_violations))

        # Issue certificate
        hasher = hashlib.sha256()
        hasher.update(self.transaction_id.encode())
        for r_name in passed_rules:
            hasher.update(r_name.encode())
        now = time.time()
        hasher.update(str(now).encode())

        cert = TransactionCertificate(
            transaction_id=self.transaction_id,
            invariants_passed=tuple(passed_rules),
            timestamp=now,
            certificate_hash=hasher.hexdigest(),
        )
        self._certificate = cert
        return cert

    def commit(self, certificate: TransactionCertificate) -> GraphSnapshot:
        """Commit transaction with a valid matching certificate."""
        if self._is_committed:
            raise RuntimeError("Transaction already committed")
        if self._certificate is None or self._certificate != certificate:
            raise PermissionError(
                "Transaction commit rejected: must present valid matching TransactionCertificate"
            )

        self._is_committed = True
        return GraphSnapshot.create(
            snapshot_id=f"snap-{self.transaction_id}",
            nodes=list(self._nodes.values()),
            edges=list(self._edges.values()),
        )
