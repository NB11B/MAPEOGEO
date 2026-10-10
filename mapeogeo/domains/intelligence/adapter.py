"""Intelligence Domain Adapter for MAPEOGEO Graph Architecture.

Connects platform graph structures into the 7x7 functional matrix and
operational grammar interpretation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from mapeogeo.domains.intelligence.functions import (
    FunctionalEdge,
    FunctionalMatrix,
    OrganizationalFunction,
)
from mapeogeo.domains.intelligence.ontology import IntelligenceRequirement


class IntelligenceAdapter:
    """Adapter projecting platform graph relationships into intelligence domain views."""

    def __init__(self) -> None:
        self.matrix = FunctionalMatrix()

    def load_graph_edges(self, edges_data: List[Dict[str, Any]]) -> None:
        """Loads and binds raw graph edges into typed FunctionalEdge representations."""
        for ed in edges_data:
            edge = FunctionalEdge(
                edge_id=ed.get("id", f"edge:{len(self.matrix.edges)}"),
                source_function=OrganizationalFunction(ed.get("source_function", "INTELLIGENCE")),
                target_function=OrganizationalFunction(ed.get("target_function", "INTELLIGENCE")),
                actor=ed.get("actor", "unknown"),
                target_actor=ed.get("target_actor", "unknown"),
                operation=ed.get("operation", "unspecified"),
                evidence_ref=ed.get("evidence_ref"),
                epistemic_state=ed.get("epistemic_state", "supported"),
                attributes=ed.get("attributes", {}),
            )
            self.matrix.add_edge(edge)

    def get_functional_matrix(self) -> FunctionalMatrix:
        return self.matrix
