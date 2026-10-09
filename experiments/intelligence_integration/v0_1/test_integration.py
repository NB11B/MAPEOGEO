"""Integration Test Suite: MAPEOGEO to Intelligence Analysis Reference Model (v0.1).

Validates all 10 architectural boundaries and guarantees required for milestone v0.1:
1. Reference parity (adapted vs direct reference evaluation)
2. Projection fidelity (field and layer preservation)
3. Missing information (unknowns remain explicit; zero-fabrication)
4. Interpretation preservation (candidate mappings remain unpromoted; grammar readings visible)
5. Lineage preservation (report identity separate from evidential origin count)
6. Scenario isolation (hypothetical analysis leaves snapshot and workflow state unchanged)
7. Authority separation (source assertions and scenario events barred from grants/admission)
8. Revision behavior (contract rebinding invalidates adequacy while preserving history)
9. Local ordering (clock domain isolation prevents cross-UoW spurious ordering)
10. Repository compatibility (clean module imports without namespace collisions)
"""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

# Ensure pristine reference package and experiments module are on sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
REF_PKG_DIR = REPO_ROOT / "artifacts" / "intelligence_qualification" / "v0_3" / "intelligence_qualification_v0_3"
EXP_DIR = REPO_ROOT / "experiments" / "intelligence_integration" / "v0_1"

if str(REF_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(REF_PKG_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from intel_uow import analysis, grammar
from intel_uow.workflow import Workflow, event_relation

from experiments.intelligence_integration.v0_1.adapter import (
    MAPEOGEOAnalysisAdapter,
    _canonical_digest,
)
from experiments.intelligence_integration.v0_1.contract import (
    AdapterContract,
    ClockDomain,
    ProjectionStatus,
)
from experiments.intelligence_integration.v0_1.cases import (
    build_constructed_capacity_snapshot,
    build_constructed_selection_manifest,
    build_direct_reference_evaluation,
)


class TestIntelligenceIntegration(unittest.TestCase):
    def setUp(self):
        self.adapter = MAPEOGEOAnalysisAdapter()
        self.snapshot = build_constructed_capacity_snapshot()
        self.manifest = build_constructed_selection_manifest()
        self.direct_ref = build_direct_reference_evaluation()

    # --------------------------------------------------------------------------
    # 1. REFERENCE PARITY
    # --------------------------------------------------------------------------
    def test_reference_parity(self):
        """Adapted evaluation matches direct reference evaluation across all core dimensions."""
        projected = self.adapter.project_graph_to_case(self.snapshot, self.manifest)
        self.assertEqual(projected.status, ProjectionStatus.SUPPORTED_CASE)

        result = self.adapter.evaluate_case(projected, self.snapshot)

        # Baseline evaluation parity
        self.assertEqual(result.baseline_evaluation["status"], self.direct_ref["baseline"]["status"])
        self.assertEqual(result.baseline_evaluation["capability"], self.direct_ref["baseline"]["capability"])
        self.assertEqual(result.baseline_evaluation["preferred_options"], self.direct_ref["baseline"]["preferred_options"])
        self.assertEqual(result.baseline_evaluation["risk"], self.direct_ref["baseline"]["risk"])
        self.assertEqual(result.baseline_evaluation["option_upper_bounds"], self.direct_ref["baseline"]["option_upper_bounds"])

        # Evidence summary parity
        self.assertEqual(result.evidence_summary["disposition"], self.direct_ref["evidence"]["disposition"])
        self.assertEqual(result.evidence_summary["supporting_origins"], self.direct_ref["evidence"]["supporting_origins"])
        self.assertEqual(result.evidence_summary["opposing_origins"], self.direct_ref["evidence"]["opposing_origins"])

        # Meaningful gaps parity
        self.assertEqual(result.meaningful_gaps, self.direct_ref["gaps"])

        # Hypothetical consequences parity
        self.assertEqual(result.hypothetical_consequences["status"], self.direct_ref["hypothetical"]["status"])
        self.assertEqual(result.hypothetical_consequences["states"], self.direct_ref["hypothetical"]["states"])

        # Grammar interpretation parity
        self.assertEqual(
            result.grammar_interpretation["interpretation_resolution"],
            self.direct_ref["interpretation"]["interpretation_resolution"],
        )

        # Dependency reassessment parity
        self.assertEqual(result.reassessment_result, self.direct_ref["reassessment"])

    # --------------------------------------------------------------------------
    # 2. PROJECTION FIDELITY
    # --------------------------------------------------------------------------
    def test_projection_fidelity(self):
        """All declared fields retain their scope, provenance, and layer classifications."""
        projected = self.adapter.project_graph_to_case(self.snapshot, self.manifest)

        self.assertEqual(projected.scope["subject"], "reserve-carrier")
        self.assertEqual(projected.scope["window"], "service-window")
        self.assertEqual(projected.model_parameters["demand"], 10)
        self.assertEqual(projected.model_parameters["regular_capacity"], 4)
        self.assertEqual(projected.model_parameters["bridge_capacity"], 6)
        self.assertEqual(projected.model_parameters["loading_capacity"], 10)

        # Ensure node layer mapping fidelity
        for node in self.snapshot["nodes"]:
            valid, err = self.adapter.contract.validate_node_layer(node["type"], node.get("layer"))
            self.assertTrue(valid, f"Layer fidelity failed for {node['id']}: {err}")

    # --------------------------------------------------------------------------
    # 3. MISSING INFORMATION (ZERO-FABRICATION & PROVENANCE)
    # --------------------------------------------------------------------------
    def test_missing_information_preserves_unknowns(self):
        """Unknown facts in host records remain unknown; no default Boolean False or zero is injected."""
        snapshot_with_unknowns = deepcopy(self.snapshot)
        # Set demand_units to None in host source node
        for n in snapshot_with_unknowns["nodes"]:
            if n["id"] == "src:service_contract:v1":
                n["attributes"]["demand_units"] = None

        projected = self.adapter.project_graph_to_case(snapshot_with_unknowns, self.manifest)
        self.assertEqual(projected.status, ProjectionStatus.SUPPORTED_WITH_UNKNOWNS)
        self.assertIsNone(projected.model_parameters["demand"])

        result = self.adapter.evaluate_case(projected, snapshot_with_unknowns)
        # Ensure evaluate did not silently convert None to 0
        self.assertEqual(result.baseline_evaluation["status"], "context_or_model_error")

    def test_host_field_provenance_is_explicitly_tracked(self):
        """Field provenance connects projected parameters to host node IDs and attributes."""
        projected = self.adapter.project_graph_to_case(self.snapshot, self.manifest)
        prov_map = {p.field_name: p for p in projected.field_provenance}

        self.assertIn("demand", prov_map)
        self.assertEqual(prov_map["demand"].host_node_id, "src:service_contract:v1")
        self.assertEqual(prov_map["demand"].source_attribute, "demand_units")
        self.assertEqual(prov_map["demand"].extracted_value, 10)

        self.assertIn("regular_capacity", prov_map)
        self.assertEqual(prov_map["regular_capacity"].host_node_id, "src:carrier_schedule:v1")
        self.assertEqual(prov_map["regular_capacity"].extracted_value, 4)

    # --------------------------------------------------------------------------
    # 4. INTERPRETATION PRESERVATION (CANDIDATE != SAME_SEMANTICS)
    # --------------------------------------------------------------------------
    def test_candidate_mappings_never_promoted_to_same_semantics(self):
        """CANDIDATE_EO / CANDIDATE_GEO cannot be silently promoted to SAME_SEMANTICS."""
        tampered_snapshot = deepcopy(self.snapshot)
        # Attempt illegal promotion of candidate edge
        tampered_snapshot["edges"][1]["type"] = "CANDIDATE_EO"
        tampered_snapshot["edges"][1]["attributes"]["interpretation"] = "SAME_SEMANTICS"

        projected = self.adapter.project_graph_to_case(tampered_snapshot, self.manifest)
        self.assertTrue(any("Illegal promotion" in d for d in projected.diagnostics))

    # --------------------------------------------------------------------------
    # 5. LINEAGE PRESERVATION (REPORT COUNT != ORIGIN COUNT)
    # --------------------------------------------------------------------------
    def test_lineage_preservation_avoids_false_corroboration(self):
        """Multiple reports sharing one reviewed origin retain shared origin without inflating lineage."""
        manifest = deepcopy(self.manifest)
        target = manifest["scope"]
        # Two reports with distinct report IDs but the SAME reviewed origin
        manifest["selected_reports"] = [
            dict(target, id="rep-01", polarity="positive", origin="reviewed-origin-alpha", status="supported", predicate="availability", modality="actual"),
            dict(target, id="rep-02", polarity="positive", origin="reviewed-origin-alpha", status="supported", predicate="availability", modality="actual"),
        ]

        projected = self.adapter.project_graph_to_case(self.snapshot, manifest)
        result = self.adapter.evaluate_case(projected, self.snapshot)

        # 2 reports, but only 1 evidential origin
        self.assertEqual(len(result.evidence_summary["supporting_report_ids"]), 2)
        self.assertEqual(len(result.evidence_summary["supporting_origins"]), 1)
        self.assertEqual(result.evidence_summary["supporting_origins"], ["reviewed-origin-alpha"])

    # --------------------------------------------------------------------------
    # 6. SCENARIO ISOLATION
    # --------------------------------------------------------------------------
    def test_scenario_isolation_preserves_snapshot_and_actual_workflow(self):
        """Hypothetical evaluations leave the input snapshot and actual workflow state unchanged."""
        original_digest = _canonical_digest(self.snapshot)

        projected = self.adapter.project_graph_to_case(self.snapshot, self.manifest)
        result = self.adapter.evaluate_case(projected, self.snapshot)

        # Verify input snapshot remained untouched
        self.assertTrue(result.immutability_verified)
        self.assertEqual(_canonical_digest(self.snapshot), original_digest)

        # Verify hypothetical outcome explicitly marks actual world unchanged
        self.assertFalse(result.hypothetical_consequences.get("actual_world_changed", True))
        self.assertEqual(result.hypothetical_consequences.get("interpretation"), "hypothetical")

    # --------------------------------------------------------------------------
    # 7. AUTHORITY SEPARATION
    # --------------------------------------------------------------------------
    def test_source_assertion_cannot_supply_authority_admission(self):
        """A source assertion claiming authority cannot become an actual grant or establish admission."""
        manifest = deepcopy(self.manifest)
        # Attempt to pass a source assertion as an authority grant
        source_grant = {
            "status": "established",
            "actor": "analyst",
            "actions": ["review_records"],
            "purpose": "assess service uncertainty",
            "scope": manifest["scope"],
            "resource_limits": {"analyst_hours": 2},
            "recipients": ["case-review-team"],
            "grant_id": "unauthorized-source-grant",
            "grant_revision": 1,
            "grant_effective": True,
            "source_assertion": True,
            "layer": "source",
        }
        manifest["authority_views"] = [source_grant]

        projected = self.adapter.project_graph_to_case(self.snapshot, manifest)
        self.assertTrue(any("Source assertion claiming authority" in d for d in projected.diagnostics))

        result = self.adapter.evaluate_case(projected, self.snapshot)
        self.assertEqual(result.admission_result["status"], "unresolved")

    # --------------------------------------------------------------------------
    # 8. REVISION BEHAVIOR
    # --------------------------------------------------------------------------
    def test_requirement_revision_preserves_history_and_invalidates_adequacy(self):
        """A changed question or model contract invalidates prior criteria adequacy while preserving history."""
        wf = Workflow()
        scope = self.manifest["scope"]
        proposal = self.manifest["proposal"]
        grant = self.manifest["authority_views"][0]

        wf.apply({
            "type": "add_requirement",
            "id": "req-01",
            "question_revision": 1,
            "gap_ids": ["C", "A"],
            "adequacy_purpose": "requested_product",
            "scope": scope,
        })
        wf.apply({"type": "add_work", "id": "work-01", "proposal": proposal, "reservations": {"analyst_hours": 1}, "duties": ["retain attribution"]})
        wf.apply({"type": "bind", "requirement_id": "req-01", "work_id": "work-01"})
        wf.apply({"type": "admit_work", "work_id": "work-01", "views": [grant]})
        outcome = wf.apply({
            "type": "record_result",
            "work_id": "work-01",
            "observer": "analyst",
            "result": {
                "kind": "uncertainty_report",
                "criteria_met": True,
                "basis_status": "supported",
                "subject_resolved": False,
                "evidence_mode": "actual",
            },
            "receipt_event": {"id": "rcpt-01", "actor": "analyst", "seq": 1, "parents": []},
        })
        self.assertTrue(outcome["governed"])

        assessment1 = wf.apply({"type": "assess_requirement", "requirement_id": "req-01", "work_id": "work-01"})
        self.assertEqual(assessment1["answer_adequacy"], "adequate")

        # Now revise the requirement question revision to 2
        revised_req = wf.apply({
            "type": "revise_requirement",
            "requirement_id": "req-01",
            "question_revision": 2,
            "adequacy_purpose": "target_gap_resolution",
            "scope": scope,
        })
        self.assertEqual(revised_req["status"], "revised")

        # Snapshot check: prior revision preserved in history as adequate, current is unassessed
        s = wf.snapshot()
        req_state = s["requirements"]["req-01"]
        self.assertEqual(req_state["answer_adequacy"], "unassessed")
        self.assertEqual(req_state["gap_resolution"], "unresolved")
        self.assertEqual(req_state["revision_history"][0]["question_revision"], 1)
        self.assertEqual(req_state["revision_history"][0]["answer_adequacy"], "adequate")

        # Prior result does NOT complete successor question revision
        assessment2 = wf.apply({"type": "assess_requirement", "requirement_id": "req-01", "work_id": "work-01"})
        self.assertEqual(assessment2["answer_adequacy"], "unresolved")
        self.assertIn("actual aligned adequate contribution for current binding is not established", assessment2["reasons"])

    # --------------------------------------------------------------------------
    # 9. LOCAL ORDERING (CLOCK DOMAIN ISOLATION & CAUSAL PARENTS)
    # --------------------------------------------------------------------------
    def test_unrelated_timelines_remain_unordered_across_clock_domains(self):
        """Two independently timed UoWs sharing the same person remain unordered (unknown relation)."""
        cd1 = ClockDomain(domain_id="uow:01", owner_boundary="boundary:01", description="UoW 1")
        cd2 = ClockDomain(domain_id="uow:02", owner_boundary="boundary:02", description="UoW 2")

        # Same human actor "alice", but in separate clock domains
        actor1 = cd1.format_event_actor("alice")
        actor2 = cd2.format_event_actor("alice")

        events = [
            {"id": "evt-01", "actor": actor1, "seq": 1, "parents": []},
            {"id": "evt-02", "actor": actor2, "seq": 1, "parents": []},
        ]

        # In reference model, these two events have no causal edge and distinct actor timelines
        rel = event_relation("evt-01", "evt-02", events)
        self.assertEqual(rel, "unknown", "Unrelated local events must remain unordered")

    def test_local_ordering_within_same_clock_domain(self):
        """Events within the same clock domain are ordered by their local sequence."""
        cd = ClockDomain(domain_id="uow:01", owner_boundary="boundary:01", description="UoW 1")
        actor = cd.format_event_actor("alice")
        events = [
            {"id": "evt-01", "actor": actor, "seq": 1, "parents": []},
            {"id": "evt-02", "actor": actor, "seq": 2, "parents": []},
        ]
        self.assertEqual(event_relation("evt-01", "evt-02", events), "before")
        self.assertEqual(event_relation("evt-02", "evt-01", events), "after")

    def test_explicit_causal_parent_orders_events_across_clock_domains(self):
        """When an explicit causal edge connects events across clock domains, order is established."""
        cd1 = ClockDomain(domain_id="uow:01", owner_boundary="boundary:01", description="UoW 1")
        cd2 = ClockDomain(domain_id="uow:02", owner_boundary="boundary:02", description="UoW 2")
        actor1 = cd1.format_event_actor("alice")
        actor2 = cd2.format_event_actor("bob")
        events = [
            {"id": "evt-01", "actor": actor1, "seq": 1, "parents": []},
            {"id": "evt-02", "actor": actor2, "seq": 1, "parents": ["evt-01"]},
        ]
        self.assertEqual(event_relation("evt-01", "evt-02", events), "before")

    # --------------------------------------------------------------------------
    # 10. UNSUPPORTED PROJECTIONS AND INVALID INPUT
    # --------------------------------------------------------------------------
    def test_unsupported_continuous_projection(self):
        """Continuous domains produce UNSUPPORTED_PROJECTION with clean diagnostics."""
        manifest = deepcopy(self.manifest)
        manifest["domain_type"] = "continuous"
        projected = self.adapter.project_graph_to_case(self.snapshot, manifest)
        self.assertEqual(projected.status, ProjectionStatus.UNSUPPORTED_PROJECTION)
        self.assertIn("Continuous domains are unsupported in finite reference model", projected.unsupported_reasons)

        result = self.adapter.evaluate_case(projected, self.snapshot)
        self.assertEqual(result.baseline_evaluation["status"], "unsupported_projection")

    def test_invalid_input_diagnosed(self):
        """Empty state domain in host snapshot produces INVALID_INPUT."""
        snapshot_empty = deepcopy(self.snapshot)
        for n in snapshot_empty["nodes"]:
            if n["id"] == "obj:carrier_capacity_model:v1":
                n["attributes"]["capacity_values"] = []
        projected = self.adapter.project_graph_to_case(snapshot_empty, self.manifest)
        self.assertEqual(projected.status, ProjectionStatus.INVALID_INPUT)

    def test_ambiguous_clock_domain_delimiters_rejected(self):
        """ClockDomain and local_actor reject '::' to prevent ambiguous delimiter collisions."""
        with self.assertRaises(ValueError):
            ClockDomain(domain_id="uow::bad", owner_boundary="b", description="desc")
        
        cd = ClockDomain(domain_id="uow01", owner_boundary="b", description="desc")
        with self.assertRaises(ValueError):
            cd.format_event_actor("bad::actor")

    def test_unsupported_actual_lifecycle_projection_in_v0_1(self):
        """Actual lifecycle projection (grant expiry invalidation, cancellation release) is declared unsupported in v0.1."""
        manifest = deepcopy(self.manifest)
        manifest["request_lifecycle_projection"] = True
        projected = self.adapter.project_graph_to_case(self.snapshot, manifest)
        self.assertEqual(projected.status, ProjectionStatus.UNSUPPORTED_PROJECTION)
        self.assertIn(
            "Actual lifecycle projection (grant expiry invalidation, cancellation release) is unsupported in v0.1",
            projected.unsupported_reasons,
        )

    # --------------------------------------------------------------------------
    # 11. REPOSITORY COMPATIBILITY
    # --------------------------------------------------------------------------
    def test_repository_compatibility_and_clean_imports(self):
        """Modules import cleanly without namespace collisions and verify contract specification."""
        self.assertIn("uow.intelligence.meaningful_gaps.carrier_continuity.v0_3", self.adapter.contract.supported_models)
        self.assertIn("continuous_probability_distributions", self.adapter.contract.unsupported_features)
        self.assertIn("actual_lifecycle_projection", self.adapter.contract.unsupported_features)


if __name__ == "__main__":
    unittest.main()
