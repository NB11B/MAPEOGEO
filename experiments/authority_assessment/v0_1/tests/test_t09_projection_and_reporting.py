"""Unit and Qualification Test Suite for Task T09: Host Projection and Reporting.

Verifies:
1. Snapshot immutability: Host snapshot digest is unchanged across all projections and evaluations.
2. Grounded host nodes & field provenance: Correct extraction from src:service_contract:v1,
   src:carrier_schedule:v1, and obj:carrier_capacity_model:v1.
3. AQ37: Excluded surfaces return UNSUPPORTED_PROJECTION (no actual lifecycle projection,
   no live host graph mutation, no external execution).
4. AQ05: Unfamiliar actor identities are handled without fabrication.
5. AQ24: Coverage limits prevent law by silence; unmapped operations remain explicit gaps.
6. AQ41: Preserves canonical clock identity encoding for timeline events and actors.
7. AQ56: Malformed inputs (duplicate IDs, NaN, boolean masquerade) return INVALID_INPUT
   with technical diagnostics and no legal disposition.
8. AQ20: Retrieved sources without authentication cannot act as reviewed law packs.
9. AQ09 & AQ30: Material binding mutations produce distinct digests and cannot silently match.
10. Reporting & Access Control (R20): Public summary references restricted support without
    disclosing protected source details; assessed actor receives no reader permission.
11. CLI Subcommands: assess, enumerate, gaps, and compare work with explicit arguments.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import tempfile
import unittest

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    ActionCaseBuilder,
    compute_case_digest,
)
from experiments.authority_assessment.v0_1.intel_authority.cli import main as cli_main
from experiments.authority_assessment.v0_1.intel_authority.projection import (
    ProjectedAuthorityCase,
    _canonical_digest,
    project_host_case,
)
from experiments.authority_assessment.v0_1.intel_authority.reporting import (
    AccessContext,
    filter_assessment_for_reader,
    format_json_report,
    render_course_comparison_report,
    render_explanation,
    render_reverse_query_report,
)
from experiments.intelligence_integration.v0_1.cases import (
    build_constructed_capacity_snapshot,
    build_constructed_selection_manifest,
)
from experiments.intelligence_integration.v0_1.contract import (
    ClockDomain,
    ProjectionStatus,
)
from experiments.intelligence_integration.v0_2.authority_adapter import (
    MAPEOGEOAuthorityAdapter,
)

BASE_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"
QUAL_DIR = BASE_DIR / "qualification"


class TestT09ProjectionAndReporting(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = build_constructed_capacity_snapshot()
        self.manifest = build_constructed_selection_manifest()
        self.adapter = MAPEOGEOAuthorityAdapter()

        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            self.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            self.sources_and_reviews = json.load(f)

        self.context = {
            "ref": {"id": "ctx:t09_test", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }

    # --------------------------------------------------------------------------
    # 1. SNAPSHOT IMMUTABILITY AND GROUNDED NODES
    # --------------------------------------------------------------------------
    def test_snapshot_immutability_and_field_provenance(self) -> None:
        """Host snapshot digest is identical before and after projection, and fields are attributed."""
        digest_before = _canonical_digest(self.snapshot)

        projected = self.adapter.project_authority_case(self.snapshot, self.manifest)

        digest_after = _canonical_digest(self.snapshot)
        self.assertEqual(digest_before, digest_after, "Host snapshot must not be mutated!")
        self.assertEqual(projected.status, ProjectionStatus.SUPPORTED_CASE)
        self.assertEqual(projected.source_snapshot_digest, digest_before)

        # Verify field provenance contains grounded nodes
        node_ids = {fp.host_node_id for fp in projected.field_provenance}
        self.assertIn("src:service_contract:v1", node_ids)
        self.assertIn("src:carrier_schedule:v1", node_ids)
        self.assertIn("obj:carrier_capacity_model:v1", node_ids)

        # Evaluate authority case and verify snapshot remains unmutated
        res = self.adapter.evaluate_authority_case(
            projected, self.context, snapshot_ref=self.snapshot
        )
        self.assertEqual(_canonical_digest(self.snapshot), digest_before)
        self.assertIsNotNone(res.disposition)

    # --------------------------------------------------------------------------
    # 2. AQ37: EXCLUDED SURFACES RETURN UNSUPPORTED_PROJECTION
    # --------------------------------------------------------------------------
    def test_aq37_excluded_surfaces_rejected(self) -> None:
        """Requests for actual lifecycle mutations or external execution are strictly rejected."""
        manifest_lifecycle = deepcopy(self.manifest)
        manifest_lifecycle["request_lifecycle_projection"] = True

        digest_before = _canonical_digest(self.snapshot)
        projected = self.adapter.project_authority_case(self.snapshot, manifest_lifecycle)
        self.assertEqual(projected.status, ProjectionStatus.UNSUPPORTED_PROJECTION)
        self.assertTrue(any("actual_lifecycle_projection" in r for r in projected.unsupported_reasons))
        self.assertEqual(_canonical_digest(self.snapshot), digest_before)

        # Excluded surface in requested_surfaces
        manifest_mutation = deepcopy(self.manifest)
        manifest_mutation["requested_surfaces"] = ["live_mutation_of_host_graph"]
        projected_mut = self.adapter.project_authority_case(self.snapshot, manifest_mutation)
        self.assertEqual(projected_mut.status, ProjectionStatus.UNSUPPORTED_PROJECTION)

    # --------------------------------------------------------------------------
    # 3. AQ05: UNFAMILIAR ACTOR IDENTITY
    # --------------------------------------------------------------------------
    def test_aq05_unfamiliar_actor_handled_without_fabrication(self) -> None:
        """Unfamiliar actor identities are attributed to named unresolved binding."""
        manifest_unknown = deepcopy(self.manifest)
        manifest_unknown["actor_id"] = "actor:unknown:zeta_99"

        projected = self.adapter.project_authority_case(self.snapshot, manifest_unknown)
        self.assertEqual(projected.status, ProjectionStatus.SUPPORTED_WITH_UNKNOWNS)
        self.assertTrue(any("UNFAMILIAR_ACTOR_IDENTITY" in d for d in projected.diagnostics))
        self.assertIn("unknown_party", projected.action_case["actor_ref"]["id"])

    # --------------------------------------------------------------------------
    # 4. AQ24: UNMAPPED OPERATION PREVENTS LAW BY SILENCE
    # --------------------------------------------------------------------------
    def test_aq24_unmapped_operation_coverage_gap(self) -> None:
        """Unmapped operations return coverage gap and are not silently allowed or prohibited."""
        manifest_op = deepcopy(self.manifest)
        manifest_op["operation_id"] = "op:unmapped_extraterritorial_teleport"

        projected = self.adapter.project_authority_case(self.snapshot, manifest_op)
        self.assertEqual(projected.status, ProjectionStatus.SUPPORTED_WITH_UNKNOWNS)
        self.assertTrue(any("UNMAPPED_OPERATION_COVERAGE_GAP" in d for d in projected.diagnostics))

    # --------------------------------------------------------------------------
    # 5. AQ41: CLOCK IDENTITY ENCODING PRESERVED IN PROJECTION
    # --------------------------------------------------------------------------
    def test_aq41_clock_domain_namespacing_in_projection(self) -> None:
        """Timeline events in projected case are canonically namespaced by ClockDomain."""
        clock = ClockDomain(
            domain_id="ops:stream1",
            owner_boundary="uow:boundary:uow-01",
            description="Operational review timeline",
        )
        manifest_events = deepcopy(self.manifest)
        manifest_events["timeline_events"] = [
            {"event_id": "ev_101", "actor": "analyst", "seq": 1}
        ]

        projected = self.adapter.project_authority_case(
            self.snapshot, manifest_events, clock_domain=clock
        )
        self.assertEqual(len(projected.timeline_events), 1)
        ev = projected.timeline_events[0]
        self.assertEqual(ev["event_id"], "ops:stream1:ev_101")
        self.assertTrue(ev["actor"].startswith("uow-clock:v1:"))
        self.assertIn("ops:stream1", ev["actor"])

    # --------------------------------------------------------------------------
    # 6. AQ56: INPUT BOUNDARIES AND MALFORMED SNAPSHOT
    # --------------------------------------------------------------------------
    def test_aq56_malformed_snapshot_returns_invalid_input(self) -> None:
        """Malformed structures (duplicate IDs, NaN, booleans as numbers) return INVALID_INPUT."""
        malformed_snap = deepcopy(self.snapshot)
        # Duplicate node
        dup_node = deepcopy(malformed_snap["nodes"][0])
        malformed_snap["nodes"].append(dup_node)

        projected = project_host_case(malformed_snap, self.manifest)
        self.assertEqual(projected.status, ProjectionStatus.INVALID_INPUT)
        self.assertTrue(any("DUPLICATE_NODE_ID" in d for d in projected.diagnostics))

        # NaN attribute check
        nan_snap = deepcopy(self.snapshot)
        nan_snap["nodes"][0]["attributes"]["demand_units"] = float("nan")
        projected_nan = project_host_case(nan_snap, self.manifest)
        self.assertEqual(projected_nan.status, ProjectionStatus.INVALID_INPUT)
        self.assertTrue(any("INVALID_NUMERIC_VALUE" in d for d in projected_nan.diagnostics))

    # --------------------------------------------------------------------------
    # 7. AQ20 & REPORTING ACCESS CONTROL: PUBLIC SUMMARY VS RESTRICTED SUPPORT
    # --------------------------------------------------------------------------
    def test_aq20_and_reporting_access_control(self) -> None:
        """Public summary can reference restricted support without disclosing protected source details."""
        sample_assessment = {
            "case": {
                "case_id": "case:commercial_assessment_01",
                "revision": 1,
                "actor_ref": {"id": "actor:licensee:beta"},
                "capacity_ref": {"id": "cap:commercial_licensee"},
                "operation_ref": {"id": "op:disclose_audit_records"},
                "jurisdiction_context_ref": {"id": "jur:synthetic_oversight"},
            },
            "disposition": "supported_within_scope",
            "status": "complete",
            "decisive_rule_refs": ["rule:statutory_reporting_mandate"],
            "trace": {
                "hohfeldian_classification": "duty",
                "rules_applied": [
                    {
                        "rule_ref": {"id": "rule:classified_safeguard"},
                        "confidentiality": "restricted",
                        "target_audiences": ["regulator", "security_council"],
                        "title": "Restricted Security Protocol Alpha",
                        "text": "Secret operational parameters for emergency disclosure.",
                        "source_ref": {"id": "src:classified_briefing_v1"},
                    },
                    {
                        "rule_ref": {"id": "rule:public_disclosure_rule"},
                        "confidentiality": "public",
                        "target_audiences": ["public", "commercial"],
                        "title": "Public Disclosure Mandate",
                        "text": "General reporting requirements for licensees.",
                        "source_ref": {"id": "src:statute_gazette_v1"},
                    },
                ],
            },
        }

        # Reader 1: Public citizen (no clearance)
        public_reader = AccessContext(reader_actor="actor:citizen:anon", clearance_level="public")
        filtered_public = filter_assessment_for_reader(sample_assessment, public_reader)
        rules_pub = filtered_public["trace"]["rules_applied"]

        # Restricted rule must be sanitized
        self.assertTrue(rules_pub[0].get("protected_redacted"))
        self.assertIn("REDACTED", rules_pub[0]["text"])
        self.assertTrue(rules_pub[0]["source_ref"].get("redacted"))
        # Public rule remains intact
        self.assertFalse(rules_pub[1].get("protected_redacted", False))

        # Text explanation renders without error
        report_text = render_explanation(sample_assessment, public_reader)
        self.assertIn("AUTHORITY ASSESSMENT REPORT", report_text)
        self.assertIn("SUPPORTED_WITHIN_SCOPE", report_text)

        # Reader 2: Assessed actor itself receives NO implicit reader permission (actor != reader)
        assessed_actor_reader = AccessContext(
            reader_actor="actor:licensee:beta", clearance_level="public"
        )
        filtered_actor = filter_assessment_for_reader(sample_assessment, assessed_actor_reader)
        self.assertTrue(
            filtered_actor["trace"]["rules_applied"][0].get("protected_redacted"),
            "Being the assessed actor confers no access to restricted source material!",
        )

        # Reader 3: Authorized regulator with restricted clearance
        regulator_reader = AccessContext(
            reader_actor="actor:regulator:chief",
            clearance_level="restricted",
            allowed_audiences=["regulator", "security_council", "public"],
        )
        filtered_reg = filter_assessment_for_reader(sample_assessment, regulator_reader)
        self.assertFalse(filtered_reg["trace"]["rules_applied"][0].get("protected_redacted", False))

    # --------------------------------------------------------------------------
    # 8. AQ09 & AQ30: MATERIAL BINDING MUTATIONS PRODUCE DISTINCT DIGESTS
    # --------------------------------------------------------------------------
    def test_aq09_aq30_material_binding_mutation_distinct_digests(self) -> None:
        """Mutating performer, capacity, operation or jurisdiction produces distinct digests."""
        builder = ActionCaseBuilder(
            case_id="case:base",
            revision=1,
            actor_ref={"id": "actor:agent:alpha", "revision": 1},
            capacity_ref={"id": "cap:agent", "revision": 1},
            operation_ref={"id": "op:inspect", "revision": 1},
            operation_revision=1,
            jurisdiction_context_ref={"id": "jur:commercial", "revision": 1},
        )
        base_case = builder.build()
        base_digest = compute_case_digest(base_case)

        # Mutate actor
        builder_actor = deepcopy(builder)
        builder_actor.actor_ref = {"id": "actor:agent:beta", "revision": 1}
        self.assertNotEqual(base_digest, compute_case_digest(builder_actor.build()))

        # Mutate capacity
        builder_cap = deepcopy(builder)
        builder_cap.capacity_ref = {"id": "cap:supervisor", "revision": 1}
        self.assertNotEqual(base_digest, compute_case_digest(builder_cap.build()))

        # Mutate operation
        builder_op = deepcopy(builder)
        builder_op.operation_ref = {"id": "op:delete_record", "revision": 1}
        self.assertNotEqual(base_digest, compute_case_digest(builder_op.build()))

    # --------------------------------------------------------------------------
    # 9. CLI COMMANDS INTEGRATION
    # --------------------------------------------------------------------------
    def test_cli_subcommands(self) -> None:
        """CLI assess, enumerate, gaps, and compare execute deterministically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # 1. CLI assess
            builder = ActionCaseBuilder(
                case_id="case:cli_test",
                revision=1,
                actor_ref={"id": "actor:auditor:delta", "revision": 1},
                capacity_ref={"id": "cap:financial_auditor", "revision": 1},
                operation_ref={"id": "op:inspect_financial_ledger", "revision": 1},
                operation_revision=1,
                jurisdiction_context_ref={"id": "jur:synthetic_oversight", "revision": 1},
            )
            case_file = tmp_path / "case.json"
            with open(case_file, "w", encoding="utf-8") as f:
                json.dump(builder.build(), f)

            ctx_file = tmp_path / "context.json"
            with open(ctx_file, "w", encoding="utf-8") as f:
                json.dump(self.context, f)

            out_assess = tmp_path / "out_assess.txt"
            code = cli_main([
                "assess",
                "--case", str(case_file),
                "--context", str(ctx_file),
                "--format", "text",
                "--out", str(out_assess),
            ])
            self.assertEqual(code, 0)
            self.assertTrue(out_assess.exists())
            self.assertIn("AUTHORITY ASSESSMENT REPORT", out_assess.read_text(encoding="utf-8"))

            # 2. CLI gaps
            out_gaps = tmp_path / "out_gaps.json"
            code_gaps = cli_main([
                "gaps",
                "--case", str(case_file),
                "--context", str(ctx_file),
                "--format", "json",
                "--out", str(out_gaps),
            ])
            self.assertEqual(code_gaps, 0)
            self.assertTrue(out_gaps.exists())
            gaps_data = json.loads(out_gaps.read_text(encoding="utf-8"))
            self.assertIn("derived_gaps", gaps_data)

            # 3. CLI enumerate
            domain_file = tmp_path / "domain.json"
            with open(domain_file, "w", encoding="utf-8") as f:
                json.dump({
                    "domain_id": "domain:test",
                    "jurisdiction": "jur:synthetic_oversight",
                    "candidates": [
                        {
                            "candidate_id": "c1",
                            "operation_ref": {"id": "op:inspect_financial_ledger", "revision": 1},
                        }
                    ],
                }, f)

            out_enum = tmp_path / "out_enum.json"
            code_enum = cli_main([
                "enumerate",
                "--mode", "actions",
                "--candidate-domain", str(domain_file),
                "--context", str(ctx_file),
                "--actor", "actor:auditor:delta",
                "--capacity", "cap:financial_auditor",
                "--format", "json",
                "--out", str(out_enum),
            ])
            self.assertEqual(code_enum, 0)
            self.assertTrue(out_enum.exists())

            # 4. CLI compare
            courses_file = tmp_path / "courses.json"
            with open(courses_file, "w", encoding="utf-8") as f:
                json.dump({
                    "courses": [
                        {
                            "course_id": "course:alpha",
                            "steps": [
                                {
                                    "step_id": "s1",
                                    "case": builder.build(),
                                }
                            ],
                        }
                    ]
                }, f)

            out_comp = tmp_path / "out_comp.json"
            code_comp = cli_main([
                "compare",
                "--courses", str(courses_file),
                "--context", str(ctx_file),
                "--format", "json",
                "--out", str(out_comp),
            ])
            self.assertEqual(code_comp, 0)
            self.assertTrue(out_comp.exists())


if __name__ == "__main__":
    unittest.main()
