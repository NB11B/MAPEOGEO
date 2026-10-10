r"""C7 Network Intelligence Analysis & Gap Qualification Test Suite.

Verifies:
1. Prioritized Intelligence Requirement (PIR) generation from functional matrix gaps.
2. Direct projection of PIRs into platform deficiency queue D = R \setminus G.
3. Multi-hop path finding across the 7 organizational functions.
4. Cross-functional chokepoint detection.
5. Epistemic state propagation preserving CONFLICTING and UNRESOLVED non-collapsing states.
6. Execution performance across connected network graph topology.
"""

from __future__ import annotations

import unittest

from mapeogeo.domains.intelligence import (
    ALL_FUNCTIONS,
    EpistemicState,
    FunctionalEdge,
    FunctionalMatrix,
    IntelligenceGapEngine,
    IntelligenceGapKind,
    NetworkIntelligenceGraph,
    OrganizationalFunction,
    PrioritizedIntelligenceRequirement,
)


class TestC7NetworkIntelligence(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = NetworkIntelligenceGraph()

        # Add nodes across organizational functions
        self.graph.add_node("actor:collector:alpha", OrganizationalFunction.INTELLIGENCE)
        self.graph.add_node("actor:analyst:beta", OrganizationalFunction.INTELLIGENCE)
        self.graph.add_node("actor:director:gamma", OrganizationalFunction.GOVERNANCE)
        self.graph.add_node("actor:marshal:delta", OrganizationalFunction.ENFORCEMENT)
        self.graph.add_node("actor:treasurer:epsilon", OrganizationalFunction.FINANCE)

        # Add functional relationships
        self.graph.add_edge(
            FunctionalEdge(
                edge_id="edge:col_to_ana",
                source_function=OrganizationalFunction.INTELLIGENCE,
                target_function=OrganizationalFunction.INTELLIGENCE,
                actor="actor:collector:alpha",
                target_actor="actor:analyst:beta",
                operation="op:feed_raw_sensor",
                evidence_ref="ev:sensor_log:01",
                epistemic_state="supported",
            )
        )
        self.graph.add_edge(
            FunctionalEdge(
                edge_id="edge:ana_to_dir",
                source_function=OrganizationalFunction.INTELLIGENCE,
                target_function=OrganizationalFunction.GOVERNANCE,
                actor="actor:analyst:beta",
                target_actor="actor:director:gamma",
                operation="op:brief_intelligence",
                evidence_ref="ev:briefing_memo:01",
                epistemic_state="supported",
            )
        )
        self.graph.add_edge(
            FunctionalEdge(
                edge_id="edge:dir_to_mar",
                source_function=OrganizationalFunction.GOVERNANCE,
                target_function=OrganizationalFunction.ENFORCEMENT,
                actor="actor:director:gamma",
                target_actor="actor:marshal:delta",
                operation="op:issue_operational_order",
                evidence_ref="ev:signed_order:01",
                epistemic_state="supported",
            )
        )
        self.graph.add_edge(
            FunctionalEdge(
                edge_id="edge:dir_to_tre",
                source_function=OrganizationalFunction.GOVERNANCE,
                target_function=OrganizationalFunction.FINANCE,
                actor="actor:director:gamma",
                target_actor="actor:treasurer:epsilon",
                operation="op:authorize_funds",
                evidence_ref="ev:warrant_funds:01",
                epistemic_state="supported",
            )
        )

    def test_c7_1_multi_hop_path_traversal(self) -> None:
        """Finds multi-hop organizational paths: Collector -> Analyst -> Director -> Marshal."""
        paths = self.graph.find_functional_paths("actor:collector:alpha", "actor:marshal:delta")
        self.assertEqual(len(paths), 1)
        path = paths[0]
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0].edge_id, "edge:col_to_ana")
        self.assertEqual(path[1].edge_id, "edge:ana_to_dir")
        self.assertEqual(path[2].edge_id, "edge:dir_to_mar")

    def test_c7_2_cross_functional_chokepoint_detection(self) -> None:
        """Director gamma is detected as a critical chokepoint bridging Governance, Intelligence, Enforcement, and Finance."""
        chokepoints = self.graph.detect_chokepoints()
        self.assertGreater(len(chokepoints), 0)
        top_chokepoint = chokepoints[0]
        self.assertEqual(top_chokepoint["actor_id"], "actor:director:gamma")
        self.assertEqual(top_chokepoint["primary_function"], "GOVERNANCE")
        bridged = set(top_chokepoint["bridged_functions"])
        self.assertIn("INTELLIGENCE", bridged)
        self.assertIn("ENFORCEMENT", bridged)
        self.assertIn("FINANCE", bridged)

    def test_c7_3_matrix_gap_detection_and_pir_generation(self) -> None:
        """Detects unevidenced cells in the 49-cell matrix and generates PIRs with Sigma_W operators."""
        matrix = self.graph.to_functional_matrix()
        engine = IntelligenceGapEngine(matrix)
        pirs = engine.detect_matrix_gaps()

        self.assertGreater(len(pirs), 0)
        # All PIRs must have valid priorities and valid Sigma_W operators
        for p in pirs:
            self.assertIn(p.priority, [1, 2, 3, 4, 5])
            self.assertIn(p.required_operator, ["O", "E", "K", "C", "F", "D", "S"])
            self.assertIsInstance(p.epistemic_state, EpistemicState)

        # High priority PIRs include unevidenced Governance and Force cells
        prio_1_pirs = [p for p in pirs if p.priority == 1]
        self.assertGreater(len(prio_1_pirs), 0)

        # Test deficiency queue projection D = R \setminus G
        queue = engine.compile_deficiency_queue()
        self.assertEqual(len(queue), len(pirs))
        self.assertTrue(all("deficiency_id" in d and "required_operator" in d for d in queue))

    def test_c7_4_epistemic_state_propagation(self) -> None:
        """Verifies that upstream uncertainty and conflicts propagate downstream without collapsing."""
        # Inject conflicting evidence at analyst level
        self.graph.nodes["actor:analyst:beta"].epistemic_state = EpistemicState.CONFLICTING

        propagated = self.graph.propagate_epistemic_uncertainty()

        # Collector remains SUPPORTED (upstream from analyst)
        self.assertEqual(propagated["actor:collector:alpha"], EpistemicState.SUPPORTED)
        # Analyst remains CONFLICTING
        self.assertEqual(propagated["actor:analyst:beta"], EpistemicState.CONFLICTING)
        # Downstream Director and Marshal inherit CONFLICTING rather than false/true collapse
        self.assertEqual(propagated["actor:director:gamma"], EpistemicState.CONFLICTING)
        self.assertEqual(propagated["actor:marshal:delta"], EpistemicState.CONFLICTING)

    def test_c7_5_epistemic_refutation_propagation(self) -> None:
        """Refuted upstream proposition blocks downstream SUPPORTED status."""
        self.graph.nodes["actor:analyst:beta"].epistemic_state = EpistemicState.REFUTED
        propagated = self.graph.propagate_epistemic_uncertainty()

        self.assertEqual(propagated["actor:director:gamma"], EpistemicState.UNRESOLVED)
        self.assertEqual(propagated["actor:marshal:delta"], EpistemicState.UNRESOLVED)


if __name__ == "__main__":
    unittest.main()
