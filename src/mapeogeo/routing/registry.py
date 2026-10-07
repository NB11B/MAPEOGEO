"""Contract and Route Registry bound to the Wave-3 DecisionGraph Substrate.

INVARIANTS:
    Route != Graph
    RouteRegistry uses and references the Wave-3 graph substrate rather than
    introducing an independent, duplicated graph representation.
"""

from __future__ import annotations

from collections.abc import Iterable

from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node, NodeKind, NodeRole
from mapeogeo.graph.relation import RelationType
from mapeogeo.routing.contracts import WorkContract


class RouteRegistry:
    """Central registry of executable work contracts linked to the DecisionGraph substrate."""

    def __init__(self, contracts: Iterable[WorkContract] | None = None) -> None:
        self._contracts: dict[str, WorkContract] = {}
        self._by_source: dict[str, list[WorkContract]] = {}
        self._by_target: dict[str, list[WorkContract]] = {}

        if contracts:
            for c in contracts:
                self.register_contract(c)

    def register_contract(self, contract: WorkContract) -> None:
        """Register a work contract and index by source and target."""
        self._contracts[contract.contract_id] = contract
        self._by_source.setdefault(contract.source, []).append(contract)
        self._by_target.setdefault(contract.target, []).append(contract)

    def get_contract(self, contract_id: str) -> WorkContract | None:
        """Retrieve contract by ID."""
        return self._contracts.get(contract_id)

    def all_contracts(self) -> tuple[WorkContract, ...]:
        """Return all registered contracts in deterministic ID order."""
        return tuple(self._contracts[cid] for cid in sorted(self._contracts.keys()))

    def find_by_source(self, source: str) -> tuple[WorkContract, ...]:
        """Return all contracts originating from source."""
        return tuple(sorted(self._by_source.get(source, []), key=lambda c: c.contract_id))

    def find_by_target(self, target: str) -> tuple[WorkContract, ...]:
        """Return all contracts leading to target."""
        return tuple(sorted(self._by_target.get(target, []), key=lambda c: c.contract_id))

    def as_decision_graph(self) -> DecisionGraph:
        """Project registered work contracts into a Wave-3 DecisionGraph substrate.

        Maps:
            contract.source, contract.target -> Node(kind=DECIDE)
            contract -> Edge(relation=DERIVES_TRANSFORMATION / REPRESENTS)
        """
        nodes: dict[str, Node] = {}
        edges: list[Edge] = []

        for c in self.all_contracts():
            if c.source not in nodes:
                nodes[c.source] = Node(
                    node_id=c.source,
                    kind=NodeKind.DECIDE,
                    role=NodeRole.ATOMIC_JUDGMENT,
                    metadata={"label": f"State: {c.source}"},
                )
            if c.target not in nodes:
                nodes[c.target] = Node(
                    node_id=c.target,
                    kind=NodeKind.DECIDE,
                    role=NodeRole.ATOMIC_JUDGMENT,
                    metadata={"label": f"State: {c.target}"},
                )

            rel = RelationType.REPRESENTS if c.is_certified else RelationType.CANDIDATE_REPRESENTS
            edge = Edge(
                source_id=c.source,
                target_id=c.target,
                relation=rel,
                contract=EdgeContract(
                    contract_id=f"ec-{c.contract_id}",
                    required_relation=rel,
                    is_certified=c.is_certified,
                ),
            )
            edges.append(edge)

        # Build DecisionGraph with initial nodes and edges
        return DecisionGraph(
            graph_id="route-registry-graph",
            initial_nodes=list(nodes.values()),
            initial_edges=edges,
        )
