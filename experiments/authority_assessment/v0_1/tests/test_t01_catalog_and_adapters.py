"""Qualification and Unit Test Suite for Task T01: Catalog and Adapters.

Verifies:
1. Base contracts immutability: pristine reference schema remains unchanged.
2. Reference adapter: strict bijective round-trip mapping between authority and base formats.
3. TypedValue adapter: strict type validation across all declared types without zero-fabrication.
4. AQ41: Clock identity encoding preserves distinct streams under boundary overlaps.
5. Catalog extension: registers authority records without modifying base contracts.
6. AQ05: Any actor pair preserves directionality and interests.
7. AQ09: Grant binds exact action and parties; mutating any dimension creates distinct case digest.
8. AQ13: Jurisdiction types (territorial, subject-matter, organizational) are not interchangeable.
9. AQ56: Input and boundary errors emit technical Diagnostics and NO legal disposition.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[4]
REF_PKG_DIR = REPO_ROOT / "artifacts" / "intelligence_qualification" / "v0_3" / "intelligence_qualification_v0_3"
if str(REF_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(REF_PKG_DIR))

from intel_uow.catalog import Catalog, Graph

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    ClockStreamAdapter,
    ReferenceAdapterError,
    TypedValueError,
    authority_to_base_ref,
    base_to_authority_ref,
    create_typed_value,
    extract_typed_value,
    validate_authority_reference,
    validate_base_reference,
)
from experiments.authority_assessment.v0_1.intel_authority.catalog_extension import (
    AUTHORITY_RECORDS,
    AuthorityCatalog,
    AuthorityGraph,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    ActionCaseBuilder,
    JurisdictionKind,
    compute_case_digest,
    mutate_case_dimension,
)


class TestT01CatalogAndAdapters(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = AuthorityCatalog()
        self.graph = AuthorityGraph(self.catalog)

    # --------------------------------------------------------------------------
    # 1. BASE CONTRACTS IMMUTABILITY
    # --------------------------------------------------------------------------
    def test_base_contracts_remain_unmodified(self) -> None:
        """Base intelligence architecture contract file is unchanged and unmutated."""
        base_schema_file = REF_PKG_DIR / "fixtures" / "intelligence_architecture_v0_3" / "intelligence_architecture_contracts_v0_3.json"
        self.assertTrue(base_schema_file.exists())
        data = json.loads(base_schema_file.read_text(encoding="utf-8"))

        # Base contract records count remains exactly 42
        self.assertEqual(len(data["records"]), 42)
        base_record_names = {r["name"] for r in data["records"]}
        # Authority-specific records are NOT in the base contracts file
        self.assertNotIn("ActionCase", base_record_names)
        self.assertNotIn("LegalAssessment", base_record_names)
        self.assertNotIn("RulePack", base_record_names)

    # --------------------------------------------------------------------------
    # 2. REFERENCE ADAPTER BIJECTIVE ROUND-TRIP
    # --------------------------------------------------------------------------
    def test_reference_adapter_bijective_round_trip(self) -> None:
        """Authority Reference and base Reference map bijectively and preserve identity."""
        auth_ref = {"id": "actor:regulator:alpha", "revision": 1}
        base_ref = authority_to_base_ref(auth_ref)
        self.assertEqual(base_ref, {"record_id": "actor:regulator:alpha", "revision": 1})

        round_trip = base_to_authority_ref(base_ref)
        self.assertEqual(round_trip, auth_ref)

    def test_reference_adapter_rejections(self) -> None:
        """Reference adapter rejects invalid formats (empty strings, non-positive revisions)."""
        with self.assertRaises(ReferenceAdapterError):
            authority_to_base_ref({"id": "", "revision": 1})

        with self.assertRaises(ReferenceAdapterError):
            authority_to_base_ref({"id": "valid", "revision": 0})

        with self.assertRaises(ReferenceAdapterError):
            authority_to_base_ref({"id": "valid", "revision": -1})

        with self.assertRaises(ReferenceAdapterError):
            base_to_authority_ref({"record_id": "", "revision": 1})

    # --------------------------------------------------------------------------
    # 3. TYPED VALUE ADAPTER & ZERO-FABRICATION
    # --------------------------------------------------------------------------
    def test_typed_value_adapter_strict_types(self) -> None:
        """TypedValue preserves exact types without truthiness or zero-coercion."""
        # Valid string
        tv_str = create_typed_value("string", "test_value")
        self.assertEqual(extract_typed_value(tv_str), "test_value")

        # Valid integer
        tv_int = create_typed_value("integer", 42)
        self.assertEqual(extract_typed_value(tv_int), 42)

        # Zero-fabrication: integer rejects boolean (True is not integer 1)
        with self.assertRaises(TypedValueError):
            create_typed_value("integer", True)

        # Boolean rejects integer 0 or 1
        with self.assertRaises(TypedValueError):
            create_typed_value("boolean", 0)

        # Reference type validates authority reference
        tv_ref = create_typed_value("reference", {"id": "obj:doc:01", "revision": 2})
        self.assertEqual(extract_typed_value(tv_ref)["id"], "obj:doc:01")

        with self.assertRaises(TypedValueError):
            create_typed_value("reference", "plain_string_ref")

    # --------------------------------------------------------------------------
    # 4. CLOCK IDENTITY ADAPTER (AQ41)
    # --------------------------------------------------------------------------
    def test_aq41_clock_identity_preserves_distinct_streams(self) -> None:
        """Boundary-overlapping pairs (ops:, analyst) vs (ops, :analyst) map to distinct representations."""
        adapter_1 = ClockStreamAdapter("ops:", "uow:boundary:b1")
        adapter_2 = ClockStreamAdapter("ops", "uow:boundary:b2")

        encoded_1 = adapter_1.encode_actor("analyst")
        encoded_2 = adapter_2.encode_actor(":analyst")

        self.assertNotEqual(encoded_1, encoded_2, "AQ41: Boundary-overlapping clock streams must not collide")

        # Exact bijective decoding
        dec_domain_1, dec_actor_1 = ClockStreamAdapter.decode_actor(encoded_1)
        self.assertEqual(dec_domain_1, "ops:")
        self.assertEqual(dec_actor_1, "analyst")

        dec_domain_2, dec_actor_2 = ClockStreamAdapter.decode_actor(encoded_2)
        self.assertEqual(dec_domain_2, "ops")
        self.assertEqual(dec_actor_2, ":analyst")

    # --------------------------------------------------------------------------
    # 5. CATALOG EXTENSION & GRAPH ENVELOPE
    # --------------------------------------------------------------------------
    def test_catalog_extension_registers_authority_records(self) -> None:
        """Extended catalog recognizes all declared authority records alongside base records."""
        self.assertIn("ActionCase", self.catalog.required)
        self.assertIn("LegalAssessment", self.catalog.required)
        self.assertIn("RulePack", self.catalog.required)
        self.assertIn("ActorRecord", self.catalog.required)

        # Base records remain present
        self.assertIn("AdmissionDecision", self.catalog.required)
        self.assertIn("AnalyticUoW", self.catalog.required)

    def test_authority_graph_adds_valid_authority_record(self) -> None:
        """AuthorityGraph successfully envelopes and stores valid authority records."""
        # Add ActorRecord in registry layer
        rec = self.graph.add_authority_record(
            record_type="ActorRecord",
            record_id="actor:regulator:alpha",
            revision=1,
            layer="registry",
            payload={
                "ref": {"id": "actor:regulator:alpha", "revision": 1},
                "kind": "organization",
                "identity_evidence_refs": [],
                "capacity_refs": [],
            },
        )
        self.assertEqual(rec["record_id"], "actor:regulator:alpha")
        self.assertEqual(rec["revision"], 1)

        # Retrieve and verify
        retrieved = self.graph.get({"record_id": "actor:regulator:alpha", "revision": 1})
        self.assertEqual(retrieved["record_type"], "ActorRecord")
        self.assertEqual(retrieved["layer"], "registry")

    # --------------------------------------------------------------------------
    # 6. AQ05: ACTOR PAIR DIRECTIONALITY AND INTERESTS
    # --------------------------------------------------------------------------
    def test_aq05_actor_pair_directionality_and_interests(self) -> None:
        """Swapping actors A and B produces distinct ActionCase structures and distinct digests."""
        builder_ab = (
            ActionCaseBuilder(
                case_id="case:aq05:ab",
                revision=1,
                actor_ref={"id": "actor:regulator:alpha", "revision": 1},
                capacity_ref={"id": "cap:regulator:alpha:oversight", "revision": 1},
                operation_ref={"id": "op:compel_record", "revision": 1},
                operation_revision=1,
                jurisdiction_context_ref={"id": "jur:fictional:state", "revision": 1},
            )
            .add_recipient("actor:licensee:gamma")
            .add_affected_binding(
                entity_ref={"id": "actor:licensee:gamma", "revision": 1},
                relationship_role="target_licensee",
                interest_refs=[{"id": "interest:due_process", "revision": 1}],
                effect_refs=[{"id": "effect:record_compelled", "revision": 1}],
            )
        )
        case_ab = builder_ab.build()
        digest_ab = compute_case_digest(case_ab)

        # Swapped direction: gamma compelling alpha
        builder_ba = (
            ActionCaseBuilder(
                case_id="case:aq05:ba",
                revision=1,
                actor_ref={"id": "actor:licensee:gamma", "revision": 1},
                capacity_ref={"id": "cap:licensee:gamma:operator", "revision": 1},
                operation_ref={"id": "op:compel_record", "revision": 1},
                operation_revision=1,
                jurisdiction_context_ref={"id": "jur:fictional:state", "revision": 1},
            )
            .add_recipient("actor:regulator:alpha")
            .add_affected_binding(
                entity_ref={"id": "actor:regulator:alpha", "revision": 1},
                relationship_role="target_regulator",
                interest_refs=[{"id": "interest:due_process", "revision": 1}],
                effect_refs=[{"id": "effect:record_compelled", "revision": 1}],
            )
        )
        case_ba = builder_ba.build()
        digest_ba = compute_case_digest(case_ba)

        self.assertNotEqual(digest_ab, digest_ba, "AQ05: Reversing actor direction must change case digest")
        self.assertEqual(case_ab["actor_ref"]["id"], "actor:regulator:alpha")
        self.assertEqual(case_ba["actor_ref"]["id"], "actor:licensee:gamma")

    # --------------------------------------------------------------------------
    # 7. AQ09: EXACT CASE AND CONTEXT BINDINGS
    # --------------------------------------------------------------------------
    def test_aq09_mutating_any_dimension_changes_case_digest(self) -> None:
        """Mutating performer, capacity, operation, affected actor, purpose, object, recipient, or jurisdiction changes digest."""
        base_case = (
            ActionCaseBuilder(
                case_id="case:aq09:base",
                revision=1,
                actor_ref={"id": "actor:regulator:alpha", "revision": 1},
                capacity_ref={"id": "cap:regulator:alpha:oversight", "revision": 1},
                operation_ref={"id": "op:request_record", "revision": 1},
                operation_revision=1,
                jurisdiction_context_ref={"id": "jur:fictional:state", "revision": 1},
            )
            .set_purpose("purpose:routine_audit")
            .add_object("obj:record:001")
            .add_recipient("actor:licensee:gamma")
            .add_affected_binding(
                entity_ref={"id": "actor:licensee:gamma", "revision": 1},
                relationship_role="target_licensee",
                interest_refs=[{"id": "interest:compliance", "revision": 1}],
                effect_refs=[{"id": "effect:record_requested", "revision": 1}],
            )
            .build()
        )
        base_digest = compute_case_digest(base_case)

        dimensions_and_mutations = [
            ("actor", "actor:investigator:beta"),
            ("capacity", "cap:investigator:beta:enforcement"),
            ("operation", "op:compel_record"),
            ("affected_actor", "actor:citizen:epsilon"),
            ("purpose", "purpose:criminal_investigation"),
            ("object", "obj:record:999"),
            ("recipient", "actor:third_party:zeta"),
            ("jurisdiction", "jur:foreign:state"),
        ]

        for dim, new_val in dimensions_and_mutations:
            mutated = mutate_case_dimension(base_case, dim, new_val)
            mut_digest = compute_case_digest(mutated)
            self.assertNotEqual(
                base_digest,
                mut_digest,
                f"AQ09: Mutating dimension '{dim}' must change case digest to prevent grant leakage",
            )

    # --------------------------------------------------------------------------
    # 8. AQ13: JURISDICTION TYPES ARE NOT INTERCHANGEABLE
    # --------------------------------------------------------------------------
    def test_aq13_jurisdiction_types_not_interchangeable(self) -> None:
        """Territorial jurisdiction cannot substitute for subject-matter or capacity jurisdiction."""
        case_territorial = (
            ActionCaseBuilder(
                case_id="case:aq13:ter",
                revision=1,
                actor_ref={"id": "actor:regulator:alpha", "revision": 1},
                capacity_ref={"id": "cap:regulator:alpha:oversight", "revision": 1},
                operation_ref={"id": "op:compel_record", "revision": 1},
                operation_revision=1,
                jurisdiction_context_ref={"id": "jur:territorial:state_a", "revision": 1},
                jurisdiction_kind=JurisdictionKind.TERRITORIAL,
            ).build()
        )

        case_subject_matter = (
            ActionCaseBuilder(
                case_id="case:aq13:sm",
                revision=1,
                actor_ref={"id": "actor:regulator:alpha", "revision": 1},
                capacity_ref={"id": "cap:regulator:alpha:oversight", "revision": 1},
                operation_ref={"id": "op:compel_record", "revision": 1},
                operation_revision=1,
                jurisdiction_context_ref={"id": "jur:subject_matter:environmental", "revision": 1},
                jurisdiction_kind=JurisdictionKind.SUBJECT_MATTER,
            ).build()
        )

        self.assertNotEqual(case_territorial["_jurisdiction_kind"], case_subject_matter["_jurisdiction_kind"])
        self.assertNotEqual(compute_case_digest(case_territorial), compute_case_digest(case_subject_matter))

    # --------------------------------------------------------------------------
    # 9. AQ56: INPUT BOUNDARY ERRORS DO NOT MASQUERADE AS LAW
    # --------------------------------------------------------------------------
    def test_aq56_input_errors_emit_technical_diagnostics_no_legal_disposition(self) -> None:
        """Malformed inputs produce technical Diagnostics and NEVER fabricate a legal disposition."""
        # 1. Malformed record missing required fields
        malformed_record = {
            "record_type": "ActionCase",
            "record_id": "case:malformed:01",
            "revision": 1,
            "layer": "subject_hypothesis",
            # Missing actor_ref, capacity_ref, etc.
        }
        diagnostics = self.catalog.validate_authority_record(malformed_record)
        self.assertTrue(len(diagnostics) > 0)
        codes = [d["code"] for d in diagnostics]
        self.assertIn("MISSING_REQUIRED_FIELD", codes)

        # 2. Ensure NO legal disposition (supported/prohibited/conditions_unmet) is present in diagnostics
        for d in diagnostics:
            self.assertNotIn("supported", d.get("message", "").lower())
            self.assertNotIn("prohibited", d.get("message", "").lower())
            self.assertNotIn("conditions_unmet", d.get("message", "").lower())

        # 3. Illegal layer generates technical error
        illegal_layer_record = {
            "record_type": "ActorRecord",
            "record_id": "actor:illegal",
            "revision": 1,
            "layer": "subject_hypothesis",  # ActorRecord allowed only in registry
            "ref": {"id": "actor:illegal", "revision": 1},
            "kind": "organization",
            "identity_evidence_refs": [],
            "capacity_refs": [],
        }
        layer_diagnostics = self.catalog.validate_authority_record(illegal_layer_record)
        self.assertTrue(any(d["code"] == "ILLEGAL_LAYER" for d in layer_diagnostics))


if __name__ == "__main__":
    unittest.main()
