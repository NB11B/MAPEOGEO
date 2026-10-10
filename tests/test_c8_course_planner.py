"""C8 Analytical Course-of-Action (COA) Planner Test Suite.

Verifies:
1. Multi-step candidate course discovery across network intelligence graph.
2. Step-by-step legal authority qualification against reviewed rule packs.
3. Invariant: Analytical Finding != Operational Admission.
4. Discovery of unconventional admissible courses when direct pathways are legally blocked.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from mapeogeo.domains.authority.certification import CertificateOutcome
from mapeogeo.domains.intelligence import (
    CandidateCourse,
    CoursePlanner,
    CourseStatus,
    CourseStep,
    FunctionalEdge,
    NetworkIntelligenceGraph,
    OrganizationalFunction,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "experiments" / "authority_assessment" / "v0_1" / "fixtures" / "synthetic"


class TestC8CoursePlanner(unittest.TestCase):
    def setUp(self) -> None:
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            self.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            self.sources_and_reviews = json.load(f)

        self.authority_context = {
            "ref": {"id": "ctx:coa_planning", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }

        # Build graph with:
        # 1. Direct coercive edge: Licensee -> Citizen (compel_record, PROHIBITED by rule:priv:02)
        # 2. Indirect pathway:
        #    Step 1: Licensee -> Regulator (request_record, PERMITTED by rule:priv:01)
        #    Step 2: Regulator -> Citizen (request_record, PERMITTED by rule:priv:01)
        self.graph = NetworkIntelligenceGraph()
        self.graph.add_node("actor:licensee:gamma", OrganizationalFunction.PRODUCTION_POPULACE)
        self.graph.add_node("actor:regulator:alpha", OrganizationalFunction.GOVERNANCE)
        self.graph.add_node("actor:citizen:epsilon", OrganizationalFunction.PRODUCTION_POPULACE)

        # Direct edge (blocked)
        self.graph.add_edge(
            FunctionalEdge(
                edge_id="edge:direct_coercion",
                source_function=OrganizationalFunction.PRODUCTION_POPULACE,
                target_function=OrganizationalFunction.PRODUCTION_POPULACE,
                actor="actor:licensee:gamma",
                target_actor="actor:citizen:epsilon",
                operation="op:compel_record",
            )
        )

        # Indirect unconventional path
        self.graph.add_edge(
            FunctionalEdge(
                edge_id="edge:step1_consult_regulator",
                source_function=OrganizationalFunction.PRODUCTION_POPULACE,
                target_function=OrganizationalFunction.GOVERNANCE,
                actor="actor:licensee:gamma",
                target_actor="actor:regulator:alpha",
                operation="op:request_record",
            )
        )
        self.graph.add_edge(
            FunctionalEdge(
                edge_id="edge:step2_regulator_inquiry",
                source_function=OrganizationalFunction.GOVERNANCE,
                target_function=OrganizationalFunction.PRODUCTION_POPULACE,
                actor="actor:regulator:alpha",
                target_actor="actor:citizen:epsilon",
                operation="op:request_record",
            )
        )

        self.planner = CoursePlanner(self.graph, self.authority_context)

    def test_c8_1_discover_and_evaluate_candidate_courses(self) -> None:
        """Discovers both direct and indirect courses and evaluates legal admissibility."""
        courses = self.planner.plan_candidate_courses(
            start_actor="actor:licensee:gamma",
            target_actor="actor:citizen:epsilon",
            objective="Acquire compliance telemetry records",
        )
        self.assertEqual(len(courses), 2)

        # Identify direct and indirect courses
        direct_course = next(c for c in courses if len(c.steps) == 1)
        indirect_course = next(c for c in courses if len(c.steps) == 2)

        # Direct course must be BLOCKED by rule:priv:02
        self.assertEqual(direct_course.status, CourseStatus.BLOCKED)
        self.assertFalse(direct_course.is_fully_admissible)
        self.assertEqual(direct_course.blocked_step_index, 0)
        self.assertEqual(direct_course.steps[0].disposition, "prohibited_under_reviewed_rule")
        self.assertIn("rule:priv:02", direct_course.steps[0].decisive_rules)

        # Indirect course must be UNCONVENTIONAL_ADMISSIBLE
        self.assertEqual(indirect_course.status, CourseStatus.UNCONVENTIONAL_ADMISSIBLE)
        self.assertTrue(indirect_course.is_fully_admissible)
        self.assertTrue(indirect_course.is_unconventional)
        self.assertEqual(len(indirect_course.steps), 2)
        for step in indirect_course.steps:
            self.assertEqual(step.outcome, CertificateOutcome.CERTIFIED)
            self.assertEqual(step.disposition, "supported_within_scope")
            self.assertIn("rule:priv:01", step.decisive_rules)

    def test_c8_2_analytical_finding_distinct_from_operational_admission(self) -> None:
        """Asserts that candidate course planning outputs analytical findings, not UoW execution receipts."""
        courses = self.planner.plan_candidate_courses(
            start_actor="actor:licensee:gamma",
            target_actor="actor:citizen:epsilon",
            objective="Audit",
        )
        indirect = next(c for c in courses if c.is_unconventional)

        # The course has status UNCONVENTIONAL_ADMISSIBLE, but possesses NO execution receipt or schedule ID
        self.assertIsInstance(indirect, CandidateCourse)
        self.assertFalse(hasattr(indirect, "execution_receipt"))
        self.assertFalse(hasattr(indirect, "schedule_id"))
        # Steps carry authority witnesses, but work is not committed
        for s in indirect.steps:
            self.assertIsInstance(s, CourseStep)
            self.assertEqual(s.outcome, CertificateOutcome.CERTIFIED)


if __name__ == "__main__":
    unittest.main()
