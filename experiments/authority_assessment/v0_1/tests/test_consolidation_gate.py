r"""Verification Test Suite for the Authority Reuse and Consolidation Gate.

Verifies:
1. 7x7 Functional Organization Matrix (M_F in F x F) over graph relationships:
   - Querying individual cells M_ij.
   - Identifying cross-boundary functional dependencies.
   - Detecting functions supporting or governing target functions.
   - Finding unevidenced cells and multi-functional actors.
2. Authority Certification Bridge (C_A in C(W)):
   - Supported cases yield valid authority certificate witnesses (admitted).
   - Prohibited / unmet cases yield authority obstructions (obstructed).
3. Standard Platform Deficiency Integration (D = R \setminus G):
   - Computes missing requirements directly from graph state.
   - Routes deficiencies to operators in the UoW 7-operator grammar basis \Sigma_W.
4. Pilot Qualification Claim Classification:
   - Asserts legal_pilot_charter.json explicitly declares synthetic_authority_profile_pilot
     and records 30/30 synthetic authority-profile pilot agreement.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from experiments.authority_assessment.v0_1.intel_authority.certificate_bridge import (
    AuthorityCertificateWitness,
    evaluate_authority_certificate,
    map_authority_deficiencies,
)
from experiments.authority_assessment.v0_1.intel_authority.functional_matrix import (
    ALL_FUNCTIONS,
    FunctionalEdge,
    FunctionalMatrix,
    OrganizationalFunction,
)

BASE_DIR = Path(__file__).resolve().parents[1]
QUAL_DIR = BASE_DIR / "qualification"
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"


class TestConsolidationGate(unittest.TestCase):
    def setUp(self) -> None:
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            self.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_public_oversight.json", "r", encoding="utf-8") as f:
            self.pack_oversight = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            self.sources_and_reviews = json.load(f)

        self.context_privacy = {
            "ref": {"id": "ctx:priv", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }

    # --------------------------------------------------------------------------
    # 1. 7x7 FUNCTIONAL MATRIX QUERIES
    # --------------------------------------------------------------------------
    def test_7x7_functional_matrix_queries(self) -> None:
        """7x7 functional matrix operates as typed queries over graph edges without new engine."""
        matrix = FunctionalMatrix()
        self.assertEqual(len(ALL_FUNCTIONS), 7)

        # Populate sample cross-functional edges
        e1 = FunctionalEdge(
            edge_id="e1",
            source_function=OrganizationalFunction.INTELLIGENCE,
            target_function=OrganizationalFunction.FORCE,
            actor="actor:intel_unit",
            target_actor="actor:operations_unit",
            operation="op:feed_threat_telemetry",
            evidence_ref="src:report_101",
        )
        e2 = FunctionalEdge(
            edge_id="e2",
            source_function=OrganizationalFunction.GOVERNANCE,
            target_function=OrganizationalFunction.ENFORCEMENT,
            actor="actor:regulator",
            target_actor="actor:inspector",
            operation="op:issue_audit_order",
            evidence_ref="src:mandate_202",
        )
        e3 = FunctionalEdge(
            edge_id="e3",
            source_function=OrganizationalFunction.FINANCE,
            target_function=OrganizationalFunction.FINANCE,
            actor="actor:auditor",
            target_actor="actor:treasury",
            operation="op:verify_ledger",
            evidence_ref="src:ledger_303",
        )
        matrix.add_edge(e1)
        matrix.add_edge(e2)
        matrix.add_edge(e3)

        # Cell query M_{ij}
        intel_force_cell = matrix.query_cell(
            OrganizationalFunction.INTELLIGENCE, OrganizationalFunction.FORCE
        )
        self.assertEqual(len(intel_force_cell), 1)
        self.assertEqual(intel_force_cell[0].edge_id, "e1")

        # Functions supporting FORCE
        supporting_force = matrix.functions_supporting(OrganizationalFunction.FORCE)
        self.assertIn(OrganizationalFunction.INTELLIGENCE, supporting_force)

        # Governance control over ENFORCEMENT
        governing_enforcement = matrix.functions_governing(OrganizationalFunction.ENFORCEMENT)
        self.assertIn(OrganizationalFunction.GOVERNANCE, governing_enforcement)

        # Cross-boundary dependencies
        cross_boundary = matrix.dependencies_crossing_boundaries()
        self.assertEqual(len(cross_boundary), 2)  # e1 and e2 cross functions; e3 is within finance

        # Unevidenced cells in the 49-cell matrix
        unevidenced = matrix.unevidenced_cells()
        self.assertGreater(len(unevidenced), 40)

    # --------------------------------------------------------------------------
    # 2. AUTHORITY CERTIFICATION BRIDGE
    # --------------------------------------------------------------------------
    def test_authority_certification_bridge(self) -> None:
        """Authority evaluator supplies domain certificate witness C_A into course certification."""
        with open(QUAL_DIR / "direct_oracle_v0_1.json", "r", encoding="utf-8") as f:
            oracle = json.load(f)

        # Case 1: Supported case
        supp_cell = next(c for c in oracle["cells"] if c["disposition"] == "supported_within_scope")
        cert_supp = evaluate_authority_certificate(supp_cell["case"], self.context_privacy)
        self.assertEqual(cert_supp.status, "admitted")
        self.assertTrue(cert_supp.is_supported)
        self.assertIsNotNone(cert_supp.witness_ref)

        # Case 2: Prohibited case
        proh_cell = next(c for c in oracle["cells"] if c["disposition"] == "prohibited_under_reviewed_rule")
        cert_proh = evaluate_authority_certificate(proh_cell["case"], self.context_privacy)
        self.assertEqual(cert_proh.status, "obstructed")
        self.assertFalse(cert_proh.is_supported)
        self.assertIsNone(cert_supp.witness_ref if False else cert_proh.witness_ref)
        self.assertIn("Authority certification failed", cert_proh.obstruction_reason)

    # --------------------------------------------------------------------------
    # 3. DEFICIENCY MAPPING (D = R \ G)
    # --------------------------------------------------------------------------
    def test_deficiency_mapping_and_uow_operator_routing(self) -> None:
        r"""Deficiencies compute D = R \setminus G and route to UoW operator grammar \Sigma_W."""
        required = {"identity", "authority_evidence", "factual_telemetry", "grant"}
        grounded = {"identity", "factual_telemetry"}

        gap_types = {
            "authority_evidence": "authority_evidence_missing",
            "grant": "grant_required",
        }

        deficiencies = map_authority_deficiencies(required, grounded, gap_types)
        self.assertEqual(len(deficiencies), 2)

        subjects = {d.target_subject for d in deficiencies}
        self.assertEqual(subjects, {"authority_evidence", "grant"})

        # Verify operator assignments
        def_map = {d.target_subject: d for d in deficiencies}
        self.assertEqual(def_map["authority_evidence"].required_operator, "K")  # Classify: retrieve warrant
        self.assertEqual(def_map["grant"].required_operator, "S")               # Select: propose grant

    # --------------------------------------------------------------------------
    # 4. PILOT QUALIFICATION CLAIM CLASSIFICATION
    # --------------------------------------------------------------------------
    def test_pilot_qualification_claim_classification(self) -> None:
        """Pilot charter explicitly bounds claim to 30/30 synthetic authority-profile agreement."""
        charter_file = QUAL_DIR / "legal_pilot_charter.json"
        with open(charter_file, "r", encoding="utf-8") as f:
            charter = json.load(f)

        self.assertEqual(charter["qualification_classification"], "synthetic_authority_profile_pilot")
        self.assertIn("30/30 synthetic authority-profile pilot agreement", charter["claim_limit"])
        self.assertIn("does not assert real-world statutory legal correctness", charter["claim_limit"])


if __name__ == "__main__":
    unittest.main()
