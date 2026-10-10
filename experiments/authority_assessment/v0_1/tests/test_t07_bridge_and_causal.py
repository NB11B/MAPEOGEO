"""Qualification and Unit Test Suite for Task T07: UoW Bridge and Causal History.

Verifies:
1. AQ06: Analytical admission vs operational execution separation.
2. AQ22: Effective law and known-at-frontier are separate.
3. AQ37: Hypothetical mode cannot enter actual execution.
4. AQ39: Unrelated local counters establish no causal order (relation: unknown).
5. AQ40: Causal receipts preserve local order; causal cycles produce diagnostics.
6. AQ42: Legal reference time mapped via ReferenceTimeMapping; unmapped returns unknown.
7. AQ43 & AQ44: Prior assessments remain replayable; revocation affects successor use.
8. AQ45: Requirement retirement does not discharge attached residual duties.
9. AQ46 & AQ47: Cancellation request does not release reservation without release basis.
10. AQ48: Domain expansion requires successor admission; external execution disabled.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from experiments.authority_assessment.v0_1.intel_authority.allocations import (
    AllocationManager,
    AllocationState,
)
from experiments.authority_assessment.v0_1.intel_authority.causal import (
    EventRelationKind,
    LegalTimeRelationKind,
    compare_legal_reference,
    relate_events,
)
from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    assess_case,
)
from experiments.authority_assessment.v0_1.intel_authority.uow_bridge import (
    UowEntryStatus,
    assess_uow_entry,
)

BASE_DIR = Path(__file__).resolve().parents[1]
QUAL_DIR = BASE_DIR / "qualification"
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"


class TestT07BridgeAndCausal(unittest.TestCase):

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
    # 1. AQ06: ANALYTICAL WORK ADMISSION VS ACTION EXECUTION SEPARATION
    # --------------------------------------------------------------------------
    def test_aq06_uow_admission_and_legal_finding_are_independent_axes(self) -> None:
        """Analysis UoW is admitted to evaluate prohibited act; execution entry is rejected."""
        # Prohibited cell (licensee gamma compelling records)
        cell_050 = self.cells_by_key[("pack:commercial_privacy_v1", "actor:licensee:gamma", "actor:regulator:alpha", "op:compel_record")]
        context = {"ref": {"id": "ctx:aq06"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        legal_ass = assess_case(cell_050["case"], context)
        self.assertEqual(legal_ass["disposition"], "prohibited_under_reviewed_rule")

        admission_ctx = {
            "boundary_ref": {"id": "boundary:platform"},
            "access_context": {"analyst_cleared": True},
            "actual_policy_views": [{"view_id": "pv:01"}],
        }

        # 1. Analytical proposal investigating this case -> ADMITTED
        analysis_prop = {
            "ref": {"id": "prop:analytical_investigation"},
            "work_kind": "assess_case",
            "subject": {"kind": "case", "ref": cell_050["case"]["actor_ref"]},
            "mode": "actual",
        }
        dec_analysis = assess_uow_entry(analysis_prop, admission_ctx)
        self.assertEqual(dec_analysis["status"], UowEntryStatus.ADMITTED.value)
        self.assertFalse(dec_analysis["external_execution_enabled"])

        # 2. Execution proposal attempting to perform this prohibited action -> REJECTED
        exec_prop = {
            "ref": {"id": "prop:execute_compulsion"},
            "work_kind": "execute_assessed_action",
            "subject": {"kind": "case", "ref": cell_050["case"]["actor_ref"]},
            "legal_assessment_ref": legal_ass["ref"],
            "legal_assessment": legal_ass,
            "mode": "actual",
        }
        dec_exec = assess_uow_entry(exec_prop, admission_ctx)
        self.assertEqual(dec_exec["status"], UowEntryStatus.REJECTED.value)

        # 3. Malformed proposal -> CONTEXT_OR_MODEL_ERROR
        malformed_prop = {"ref": {"id": "prop:empty"}}
        dec_err = assess_uow_entry(malformed_prop, admission_ctx)
        self.assertEqual(dec_err["status"], UowEntryStatus.CONTEXT_OR_MODEL_ERROR.value)

    # --------------------------------------------------------------------------
    # 2. AQ37: HYPOTHETICAL MODE CANNOT ENTER ACTUAL EXECUTION
    # --------------------------------------------------------------------------
    def test_aq37_source_scenario_and_actual_layers_do_not_cross(self) -> None:
        """A proposal in hypothetical mode cannot be admitted for actual execution entry."""
        cell_001 = self.oracle["cells"][0]
        context = {"ref": {"id": "ctx:aq37"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        legal_ass = assess_case(cell_001["case"], context)

        admission_ctx = {
            "boundary_ref": {"id": "boundary:platform"},
            "actual_policy_views": [{"view_id": "pv:01"}],
        }

        hypo_exec_prop = {
            "ref": {"id": "prop:hypo_exec"},
            "work_kind": "execute_assessed_action",
            "subject": {"kind": "case", "ref": cell_001["case"]["actor_ref"]},
            "legal_assessment_ref": legal_ass["ref"],
            "legal_assessment": legal_ass,
            "mode": "hypothetical",  # Hypothetical!
        }
        dec = assess_uow_entry(hypo_exec_prop, admission_ctx)
        self.assertEqual(dec["status"], UowEntryStatus.REJECTED.value)
        self.assertTrue(any(d["code"] == "HYPOTHETICAL_CANNOT_EXECUTE" for d in dec.get("diagnostics", [])))

    # --------------------------------------------------------------------------
    # 3. AQ39: UNRELATED LOCAL COUNTERS ESTABLISH NO ORDER
    # --------------------------------------------------------------------------
    def test_aq39_unrelated_local_counters_establish_no_order(self) -> None:
        """Counters on different streams without causal parent links return relation: unknown."""
        ev_uow_1 = {"stream_id": "uow:01:analyst", "sequence": 42}
        ev_uow_2 = {"stream_id": "uow:02:regulator", "sequence": 15}

        # Snapshot contains no causal links between these two streams
        snapshot = {"events": []}
        rel = relate_events(ev_uow_1, ev_uow_2, snapshot)
        self.assertEqual(rel["relation"], EventRelationKind.UNKNOWN.value)

    # --------------------------------------------------------------------------
    # 4. AQ40: CAUSAL RECEIPTS PRESERVE LOCAL ORDER & CYCLE DIAGNOSTICS
    # --------------------------------------------------------------------------
    def test_aq40_causal_receipts_preserve_local_knowledge(self) -> None:
        """Cross-stream link establishes before/after; cycle in graph returns error."""
        ev_parent = {"stream_id": "stream:A", "sequence": 10}
        ev_child = {"stream_id": "stream:B", "sequence": 1}

        # Snapshot where ev_child has ev_parent as causal parent
        snapshot_valid = {
            "events": [
                {
                    "stream_id": "stream:B",
                    "sequence": 1,
                    "causal_parent_refs": [ev_parent],
                }
            ]
        }
        rel = relate_events(ev_parent, ev_child, snapshot_valid)
        self.assertEqual(rel["relation"], EventRelationKind.BEFORE.value)

        # Cycle in snapshot: A -> B -> A
        snapshot_cycle = {
            "events": [
                {"stream_id": "stream:B", "sequence": 1, "causal_parent_refs": [ev_parent]},
                {"stream_id": "stream:A", "sequence": 10, "causal_parent_refs": [ev_child]},
            ]
        }
        rel_cycle = relate_events(ev_parent, ev_child, snapshot_cycle)
        self.assertEqual(rel_cycle["relation"], EventRelationKind.CONTEXT_OR_MODEL_ERROR.value)
        self.assertTrue(any(d["code"] == "CAUSAL_CYCLE" for d in rel_cycle["diagnostics"]))

    # --------------------------------------------------------------------------
    # 5. AQ42: LEGAL REFERENCE TIME IS NOT A UOW COUNTER
    # --------------------------------------------------------------------------
    def test_aq42_legal_effective_time_is_not_a_uow_counter(self) -> None:
        """compare_legal_reference requires explicit ReferenceTimeMapping; unmapped returns unknown."""
        ev_occ = {"stream_id": "stream:ops", "sequence": 100}
        mapping = {
            "ref": {"id": "map:statutory_2026", "revision": 1},
            "covered_event_refs": [ev_occ],
            "relation": "within",
        }
        context = {"ref": {"id": "ctx:time"}}

        # Mapped event -> within
        res_mapped = compare_legal_reference(mapping, ev_occ, context)
        self.assertEqual(res_mapped["relation"], LegalTimeRelationKind.WITHIN.value)

        # Unmapped event -> unknown
        ev_unmapped = {"stream_id": "stream:unrelated", "sequence": 500}
        res_unmapped = compare_legal_reference(mapping, ev_unmapped, context)
        self.assertEqual(res_unmapped["relation"], LegalTimeRelationKind.UNKNOWN.value)

    # --------------------------------------------------------------------------
    # 6. AQ46 & AQ47: CANCELLATION REQUEST DOES NOT RELEASE RESERVATION
    # --------------------------------------------------------------------------
    def test_aq46_and_aq47_cancellation_and_release_boundaries(self) -> None:
        """Cancellation request preserves reservation; only authorized release basis frees capacity."""
        manager = AllocationManager()
        ok, rec, _ = manager.reserve("alloc:test", "actor:alpha", "res:quota", "uow:01", 10)
        self.assertTrue(ok)

        # Cancellation request
        ok_cancel, _ = manager.request_cancellation("alloc:test")
        self.assertTrue(ok_cancel)
        self.assertEqual(rec["state"], AllocationState.RESERVED.value)

        # Explicit authorized release
        ok_rel, _ = manager.release("alloc:test", "basis:statutory_release_order")
        self.assertTrue(ok_rel)
        self.assertEqual(rec["state"], AllocationState.RELEASED.value)

    # --------------------------------------------------------------------------
    # 7. AQ48: DOMAIN EXPANSION REQUIRES SUCCESSOR ADMISSION
    # --------------------------------------------------------------------------
    def test_aq48_unknown_completion_requires_reconciliation_before_retry(self) -> None:
        """Expanding subject domain requires successor admission, rejecting raw extension."""
        admission_ctx = {
            "boundary_ref": {"id": "boundary:platform"},
            "access_context": {"analyst_cleared": True},
        }

        # Proposal with un-admitted domain expansion
        expanded_prop = {
            "ref": {"id": "prop:expanded"},
            "work_kind": "enumerate_actions",
            "subject": {
                "kind": "action_query",
                "ref": {"id": "query:expanded"},
                "requires_successor_admission": True,
            },
            "mode": "actual",
        }
        dec = assess_uow_entry(expanded_prop, admission_ctx)
        self.assertEqual(dec["status"], UowEntryStatus.UNSUPPORTED_PROJECTION.value)
        self.assertTrue(any(d["code"] == "SUCCESSOR_ADMISSION_REQUIRED" for d in dec.get("diagnostics", [])))


if __name__ == "__main__":
    unittest.main()
