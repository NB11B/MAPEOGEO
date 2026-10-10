"""Qualification Test Suite for Permanent Intelligence Domain Profile."""

from __future__ import annotations

import unittest
from mapeogeo.domains.intelligence.functions import (
    ALL_FUNCTIONS,
    FunctionalEdge,
    FunctionalMatrix,
    OrganizationalFunction,
)
from mapeogeo.domains.intelligence.grammar_mapping import (
    INTELLIGENCE_GAP_TO_OPERATOR,
    map_intelligence_deficiency,
)
from mapeogeo.domains.intelligence.ontology import (
    IntelligenceGapKind,
    OperationalRole,
)


class TestIntelligenceDomain(unittest.TestCase):
    def test_all_seven_functions_defined(self) -> None:
        self.assertEqual(len(ALL_FUNCTIONS), 7)
        expected = {
            "INTELLIGENCE", "ENFORCEMENT", "FORCE", "GOVERNANCE",
            "FINANCE", "PRODUCTION_POPULACE", "PERCEPTION",
        }
        self.assertEqual({f.value for f in ALL_FUNCTIONS}, expected)

    def test_functional_matrix_queries(self) -> None:
        matrix = FunctionalMatrix()
        edge = FunctionalEdge(
            edge_id="e1",
            source_function=OrganizationalFunction.INTELLIGENCE,
            target_function=OrganizationalFunction.ENFORCEMENT,
            actor="actor:analyst:1",
            target_actor="actor:officer:1",
            operation="tip_off",
            evidence_ref="ev:1",
        )
        matrix.add_edge(edge)
        cell = matrix.query_cell(OrganizationalFunction.INTELLIGENCE, OrganizationalFunction.ENFORCEMENT)
        self.assertEqual(len(cell), 1)
        self.assertEqual(cell[0].edge_id, "e1")

        # Cross boundary check
        cross = matrix.dependencies_crossing_boundaries()
        self.assertEqual(len(cross), 1)

    def test_grammar_mapping(self) -> None:
        pdef = map_intelligence_deficiency(IntelligenceGapKind.FACT_GAP, "source:telemetry")
        self.assertEqual(pdef["required_operator"], "O")


if __name__ == "__main__":
    unittest.main()
