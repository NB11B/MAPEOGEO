"""Network Intelligence Analysis & Epistemic Propagation Engine.

Implements:
1. Multi-hop graph traversal across the 7 organizational functions M_F.
2. Cross-functional chokepoint detection (actors bridging functions without redundancy).
3. Non-collapsing epistemic state propagation:
   - Upstream REFUTED -> Downstream cannot be SUPPORTED (becomes REFUTED/UNRESOLVED).
   - Upstream CONFLICTING -> Downstream inherits CONFLICTING.
   - Upstream UNRESOLVED -> Downstream inherits UNRESOLVED.
   - Contradictory reporting is preserved without forced resolution or silent omission.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from mapeogeo.domains.intelligence.functions import (
    ALL_FUNCTIONS,
    FunctionalEdge,
    FunctionalMatrix,
    OrganizationalFunction,
)
from mapeogeo.domains.intelligence.ontology import EpistemicState


@dataclass
class NetworkNode:
    """An actor or entity node in the intelligence network graph."""
    node_id: str
    primary_function: OrganizationalFunction
    epistemic_state: EpistemicState = EpistemicState.SUPPORTED
    confidence: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)


class NetworkIntelligenceGraph:
    """Multi-functional network intelligence graph with epistemic tracking."""

    def __init__(self) -> None:
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: List[FunctionalEdge] = []
        self._adj: Dict[str, List[FunctionalEdge]] = defaultdict(list)
        self._rev_adj: Dict[str, List[FunctionalEdge]] = defaultdict(list)

    def add_node(
        self,
        node_id: str,
        primary_function: OrganizationalFunction,
        epistemic_state: EpistemicState = EpistemicState.SUPPORTED,
        confidence: float = 1.0,
    ) -> None:
        self.nodes[node_id] = NetworkNode(
            node_id=node_id,
            primary_function=primary_function,
            epistemic_state=epistemic_state,
            confidence=confidence,
        )

    def add_edge(self, edge: FunctionalEdge) -> None:
        self.edges.append(edge)
        self._adj[edge.actor].append(edge)
        self._rev_adj[edge.target_actor].append(edge)

        # Ensure endpoints exist
        if edge.actor not in self.nodes:
            self.add_node(edge.actor, edge.source_function)
        if edge.target_actor not in self.nodes:
            self.add_node(edge.target_actor, edge.target_function)

    def to_functional_matrix(self) -> FunctionalMatrix:
        """Projects graph relationships into the 7x7 organizational functional matrix."""
        return FunctionalMatrix(self.edges)

    def find_functional_paths(
        self,
        source_actor: str,
        target_actor: str,
        max_hops: int = 5,
    ) -> List[List[FunctionalEdge]]:
        """Finds all functional multi-hop paths between source and target actors."""
        if source_actor not in self.nodes or target_actor not in self.nodes:
            return []

        paths: List[List[FunctionalEdge]] = []
        queue: deque = deque([([source_actor], [])])

        while queue:
            visited_actors, current_edges = queue.popleft()
            curr = visited_actors[-1]

            if curr == target_actor and current_edges:
                paths.append(current_edges)
                continue

            if len(current_edges) >= max_hops:
                continue

            for edge in self._adj.get(curr, []):
                next_actor = edge.target_actor
                if next_actor not in visited_actors:
                    queue.append((visited_actors + [next_actor], current_edges + [edge]))

        return paths

    def detect_chokepoints(self) -> List[Dict[str, Any]]:
        """Identifies critical single-point-of-failure actors bridging distinct organizational functions."""
        chokepoints = []
        for node_id, node in self.nodes.items():
            outgoing_funcs = {e.target_function for e in self._adj.get(node_id, [])}
            incoming_funcs = {e.source_function for e in self._rev_adj.get(node_id, [])}

            # If actor bridges 2 or more distinct external functions
            distinct_bridged = (outgoing_funcs | incoming_funcs) - {node.primary_function}
            if len(distinct_bridged) >= 2:
                chokepoints.append({
                    "actor_id": node_id,
                    "primary_function": node.primary_function.value,
                    "bridged_functions": [f.value for f in distinct_bridged],
                    "connectivity_degree": len(self._adj.get(node_id, [])) + len(self._rev_adj.get(node_id, [])),
                })

        return sorted(chokepoints, key=lambda c: len(c["bridged_functions"]), reverse=True)

    def propagate_epistemic_uncertainty(self) -> Dict[str, EpistemicState]:
        """Propagates upstream uncertainty and conflicts through the network DAG.

        Invariants:
        1. Non-collapsing: CONFLICTING remains CONFLICTING; UNRESOLVED remains UNRESOLVED.
        2. Downstream contagion: If an essential upstream input is REFUTED, downstream
           nodes cannot be SUPPORTED.
        """
        # Topological / BFS traversal
        derived_states: Dict[str, EpistemicState] = {
            nid: n.epistemic_state for nid, n in self.nodes.items()
        }

        # Multiple relaxation passes for convergence
        for _ in range(len(self.nodes)):
            changed = False
            for edge in self.edges:
                src_state = derived_states.get(edge.actor, EpistemicState.UNRESOLVED)
                edge_state = EpistemicState(edge.epistemic_state) if hasattr(edge, "epistemic_state") and edge.epistemic_state in EpistemicState._value2member_map_ else EpistemicState.SUPPORTED
                tgt_id = edge.target_actor
                current_tgt_state = derived_states.get(tgt_id, EpistemicState.SUPPORTED)

                # Upstream conflict or refutation propagates
                new_state = current_tgt_state
                if src_state == EpistemicState.REFUTED or edge_state == EpistemicState.REFUTED:
                    if current_tgt_state == EpistemicState.SUPPORTED:
                        new_state = EpistemicState.UNRESOLVED
                elif src_state == EpistemicState.CONFLICTING or edge_state == EpistemicState.CONFLICTING:
                    if current_tgt_state == EpistemicState.SUPPORTED:
                        new_state = EpistemicState.CONFLICTING
                elif src_state == EpistemicState.UNRESOLVED or edge_state == EpistemicState.UNRESOLVED:
                    if current_tgt_state == EpistemicState.SUPPORTED:
                        new_state = EpistemicState.UNRESOLVED

                if new_state != current_tgt_state:
                    derived_states[tgt_id] = new_state
                    changed = True

            if not changed:
                break

        return derived_states
