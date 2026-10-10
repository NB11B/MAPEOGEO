"""7x7 Functional Organization Matrix (M_F in F x F) Domain Implementation.

This module provides the permanent MAPEOGEO domain representation of organizational
functions and cross-functional graph projections over standard graph relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class OrganizationalFunction(str, Enum):
    """The 7 canonical organizational functions over the platform graph."""
    INTELLIGENCE = "INTELLIGENCE"
    ENFORCEMENT = "ENFORCEMENT"
    FORCE = "FORCE"
    GOVERNANCE = "GOVERNANCE"
    FINANCE = "FINANCE"
    PRODUCTION_POPULACE = "PRODUCTION_POPULACE"
    PERCEPTION = "PERCEPTION"


ALL_FUNCTIONS: List[OrganizationalFunction] = list(OrganizationalFunction)


@dataclass(frozen=True)
class FunctionalEdge:
    """A standard graph relationship annotated with functional coordinates."""
    edge_id: str
    source_function: OrganizationalFunction
    target_function: OrganizationalFunction
    actor: str
    target_actor: str
    operation: str
    evidence_ref: Optional[str] = None
    epistemic_state: str = "supported"  # "supported", "hypothesis", "unresolved"
    attributes: Dict[str, Any] = field(default_factory=dict)


class FunctionalMatrix:
    """7x7 Functional Matrix M_F in F x F realized as queries over the platform graph."""

    def __init__(self, edges: Optional[List[FunctionalEdge]] = None) -> None:
        self.edges: List[FunctionalEdge] = list(edges) if edges else []

    def add_edge(self, edge: FunctionalEdge) -> None:
        self.edges.append(edge)

    def query_cell(
        self,
        source: OrganizationalFunction,
        target: OrganizationalFunction,
    ) -> List[FunctionalEdge]:
        """Queries M_{ij} = { e in E : e.sourceFunction == F_i and e.targetFunction == F_j }."""
        return [
            e for e in self.edges
            if e.source_function == source and e.target_function == target
        ]

    def functions_supporting(self, target: OrganizationalFunction) -> Set[OrganizationalFunction]:
        """Returns all functions that provide supporting edges to the target function."""
        return {e.source_function for e in self.edges if e.target_function == target}

    def functions_governing(self, target: OrganizationalFunction) -> Set[OrganizationalFunction]:
        """Identifies governance-originating relationships directed toward the target function."""
        return {
            e.source_function for e in self.edges
            if e.source_function == OrganizationalFunction.GOVERNANCE and e.target_function == target
        }

    def dependencies_crossing_boundaries(self) -> List[FunctionalEdge]:
        """Identifies relationships that cross distinct organizational functions (i != j)."""
        return [e for e in self.edges if e.source_function != e.target_function]

    def unevidenced_cells(self) -> List[Tuple[OrganizationalFunction, OrganizationalFunction]]:
        """Identifies any cell in the 49-cell matrix with zero supporting evidence."""
        empty_cells = []
        for src in ALL_FUNCTIONS:
            for tgt in ALL_FUNCTIONS:
                cell_edges = self.query_cell(src, tgt)
                if not cell_edges or all(e.evidence_ref is None for e in cell_edges):
                    empty_cells.append((src, tgt))
        return empty_cells

    def multi_functional_actors(self) -> Dict[str, Set[OrganizationalFunction]]:
        """Maps actors to the set of organizational functions they participate in."""
        actor_map: Dict[str, Set[OrganizationalFunction]] = {}
        for e in self.edges:
            actor_map.setdefault(e.actor, set()).add(e.source_function)
            actor_map.setdefault(e.target_actor, set()).add(e.target_function)
        return actor_map
