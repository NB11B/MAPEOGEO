"""Qualification and Unit Test Suite for Task T06: Course Analysis and Shared Allocations.

Verifies:
1. AQ34: Whole-course evaluation requires each step and its dependencies.
2. AQ35: Individually supported steps can exceed cumulative limits when composed.
3. AQ36: Course comparison in display_only mode without ranking, with budget cutoff.
4. AQ53: Shared allowances cannot be double-spent; cancellation request does not release reservation.
5. AQ54: Contingent observation guards require information available at decision frontier.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
)
from experiments.authority_assessment.v0_1.intel_authority.allocations import (
    AllocationManager,
    AllocationState,
)
from experiments.authority_assessment.v0_1.intel_authority.courses import (
    assess_course,
    compare_courses,
)

BASE_DIR = Path(__file__).resolve().parents[1]
QUAL_DIR = BASE_DIR / "qualification"
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"


class TestT06CoursesAndAllocations(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with open(QUAL_DIR / "direct_oracle_v0_1.json", "r", encoding="utf-8") as f:
            cls.oracle = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            cls.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_public_oversight.json", "r", encoding="utf-8") as f:
            cls.pack_oversight = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            cls.sources_and_reviews = json.load(f)

        cls.cells_by_key = {
            (c["scope_pack"], c["actor"], c["affected_actor"], c["operation"]): c
            for c in cls.oracle["cells"]
        }

    # --------------------------------------------------------------------------
    # 1. AQ34: COURSE REQUIRES EACH STEP AND DEPENDENCY
    # --------------------------------------------------------------------------
    def test_aq34_course_requires_each_step_and_dependency(self) -> None:
        """A course is supported only if all steps are supported; dependency failure blocks the course."""
        # Step 1: Voluntary request (supported)
        step_1_case = self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:regulator:alpha", "op:request_record")]["case"]
        # Step 2: Prohibited compulsion by private actor (prohibited)
        step_2_case = self.cells_by_key[("pack:commercial_privacy_v1", "actor:licensee:gamma", "actor:regulator:alpha", "op:compel_record")]["case"]

        course = {
            "ref": {"id": "course:alpha_investigation", "revision": 1},
            "steps": [
                {"ref": {"id": "step:01"}, "case": step_1_case, "depends_on": []},
                {"ref": {"id": "step:02"}, "case": step_2_case, "depends_on": [{"id": "step:01"}]},
            ],
        }

        context = {
            "ref": {"id": "ctx:aq34"},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_course(course, context)
        self.assertEqual(res["disposition"], "prohibited_under_reviewed_rule")
        self.assertIsNotNone(res["blocking_step_ref"])
        self.assertEqual(res["blocking_step_ref"]["id"], "step:02")

    # --------------------------------------------------------------------------
    # 2. AQ35: INDIVIDUALLY SUPPORTED STEPS COMPOSITIONAL CONFLICT
    # --------------------------------------------------------------------------
    def test_aq35_individually_supported_steps_may_conflict_when_composed(self) -> None:
        """Individually supported steps exceeding cumulative quota yield conditions_unmet with witness."""
        # Both steps are request_record (individually supported)
        step_case_1 = dict(self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:regulator:alpha", "op:request_record")]["case"])
        step_case_1["parameters"] = dict(step_case_1.get("parameters", {}), record_count=create_typed_value("integer", 35))

        step_case_2 = dict(self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:regulator:alpha", "op:request_record")]["case"])
        step_case_2["parameters"] = dict(step_case_2.get("parameters", {}), record_count=create_typed_value("integer", 25))

        # Course sets cumulative limit of 50 records (35 + 25 = 60 > 50)
        course = {
            "ref": {"id": "course:cumulative_quota", "revision": 1},
            "cumulative_limits": {"record_count": 50},
            "steps": [
                {"ref": {"id": "step:batch_1"}, "case": step_case_1, "depends_on": []},
                {"ref": {"id": "step:batch_2"}, "case": step_case_2, "depends_on": [{"id": "step:batch_1"}]},
            ],
        }

        context = {
            "ref": {"id": "ctx:aq35"},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_course(course, context)
        self.assertEqual(res["disposition"], "conditions_unmet")
        self.assertTrue(len(res["combined_constraint_refs"]) > 0)
        self.assertTrue(any("exceeded:record_count" in c["id"] for c in res["combined_constraint_refs"]))

    # --------------------------------------------------------------------------
    # 3. AQ36: ALTERNATIVE SEARCH RETAINS LIMITS AND COMPARABILITY
    # --------------------------------------------------------------------------
    def test_aq36_alternative_search_retains_limits_and_comparability(self) -> None:
        """compare_courses operates in display_only mode without ranking; budget cutoff preserves unassessed count."""
        step_case = self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:regulator:alpha", "op:request_record")]["case"]
        course_1 = {"ref": {"id": "course:01"}, "steps": [{"ref": {"id": "s1"}, "case": step_case, "depends_on": []}]}
        course_2 = {"ref": {"id": "course:02"}, "steps": [{"ref": {"id": "s2"}, "case": step_case, "depends_on": []}]}
        course_3 = {"ref": {"id": "course:03"}, "steps": [{"ref": {"id": "s3"}, "case": step_case, "depends_on": []}]}

        course_set = {
            "ref": {"id": "courseset:test"},
            "courses": [course_1, course_2, course_3],
        }

        context = {"ref": {"id": "ctx:aq36"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}

        # 1. Full comparison: comparability is not_ranked (display_only)
        res_full = compare_courses(course_set, context, comparison_policy={"ref": "policy:display_only"})
        self.assertEqual(res_full["comparability"], "not_ranked")
        self.assertEqual(res_full["evaluated_count"], 3)
        self.assertEqual(res_full["unassessed_count"], 0)
        self.assertTrue(res_full["complete"])

        # 2. Budget cutoff at max_courses=2: leaves unassessed_count=1 and complete=False
        res_cutoff = compare_courses(
            course_set,
            context,
            comparison_policy={"ref": "policy:display_only"},
            budget={"max_courses": 2},
        )
        self.assertEqual(res_cutoff["status"], "partial")
        self.assertFalse(res_cutoff["complete"])
        self.assertEqual(res_cutoff["evaluated_count"], 2)
        self.assertEqual(res_cutoff["unassessed_count"], 1)

    # --------------------------------------------------------------------------
    # 4. AQ53: SHARED ALLOWANCE CANNOT BE SPENT TWICE ACROSS UOWS
    # --------------------------------------------------------------------------
    def test_aq53_shared_allowance_cannot_be_spent_twice_across_uows(self) -> None:
        """Indivisible resource cannot be reserved by two UoWs; cancellation request does not release reservation."""
        manager = AllocationManager()

        # UoW 1 reserves the shared slot
        ok1, rec1, err1 = manager.reserve(
            allocation_ref="alloc:01",
            owner_ref="actor:regulator:alpha",
            resource_ref="res:bandwidth_slot_A",
            uow_ref="uow:first_consumer",
            quantity=1,
        )
        self.assertTrue(ok1)
        self.assertIsNone(err1)

        # UoW 2 attempts to reserve the same slot -> REJECTED
        ok2, rec2, err2 = manager.reserve(
            allocation_ref="alloc:02",
            owner_ref="actor:licensee:gamma",
            resource_ref="res:bandwidth_slot_A",
            uow_ref="uow:second_consumer",
            quantity=1,
        )
        self.assertFalse(ok2)
        self.assertIn("double-spending prohibited", err2)

        # Cancellation request alone DOES NOT release the reservation
        ok_cancel, msg_cancel = manager.request_cancellation("alloc:01")
        self.assertTrue(ok_cancel)
        self.assertEqual(rec1["state"], AllocationState.RESERVED.value)

        # Still cannot be reserved by UoW 2
        ok3, _, _ = manager.reserve(
            allocation_ref="alloc:03",
            owner_ref="actor:licensee:gamma",
            resource_ref="res:bandwidth_slot_A",
            uow_ref="uow:second_consumer",
            quantity=1,
        )
        self.assertFalse(ok3)

        # Only explicit authorized release frees the resource
        ok_rel, _ = manager.release("alloc:01", release_basis_ref="basis:authorized_release_order")
        self.assertTrue(ok_rel)
        self.assertEqual(rec1["state"], AllocationState.RELEASED.value)

        # Now UoW 2 can reserve
        ok4, _, _ = manager.reserve(
            allocation_ref="alloc:04",
            owner_ref="actor:licensee:gamma",
            resource_ref="res:bandwidth_slot_A",
            uow_ref="uow:second_consumer",
            quantity=1,
        )
        self.assertTrue(ok4)

    # --------------------------------------------------------------------------
    # 5. AQ54: ROBUST AND CONTINGENT QUANTIFIERS ARE DISTINCT
    # --------------------------------------------------------------------------
    def test_aq54_robust_and_contingent_quantifiers_are_distinct(self) -> None:
        """Contingent branch cannot be selected using information unavailable at the decision frontier."""
        step_case = self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:regulator:alpha", "op:request_record")]["case"]

        # Step has an observation guard that is NOT available at the decision frontier
        course_with_future_guard = {
            "ref": {"id": "course:contingent_cheat"},
            "steps": [
                {
                    "ref": {"id": "step:01"},
                    "case": step_case,
                    "guard_ref": {"id": "guard:unobserved_future_event"},
                    "guard_available_at_frontier": False,  # Hidden future info!
                    "depends_on": [],
                }
            ],
        }

        context = {"ref": {"id": "ctx:aq54"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        res = assess_course(course_with_future_guard, context)
        self.assertEqual(res["disposition"], "unresolved")
        self.assertTrue(any(d["code"] == "GUARD_UNAVAILABLE_AT_FRONTIER" for d in res["diagnostics"]))


if __name__ == "__main__":
    unittest.main()
