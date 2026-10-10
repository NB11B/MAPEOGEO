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

    def test_to_platform_deficiency_translation(self) -> None:
        """to_platform_deficiency faithfully projects authority gap without inference."""
        from experiments.authority_assessment.v0_1.intel_authority.gaps import (
            AuthorityGapKind,
            to_platform_deficiency,
        )

        mock_gap = {
            "ref": {"id": "gap:test:1", "revision": 1},
            "kind": AuthorityGapKind.FACT_GAP.value,
            "proposition_ref": {"id": "prop:carrier_license_valid", "revision": 1},
            "scope_ref": {"id": "scope:transport", "revision": 1},
            "assessment_ref": {"id": "ass:123", "revision": 1},
            "question_ref": {"id": "q:verify", "revision": 1},
            "dependency_refs": [{"id": "rule:456", "revision": 1}],
            "resolution_route_kinds": ["investigate_fact"],
            "materiality": "outcome_change_witnessed",
            "witness_refs": [{"id": "ass:123", "revision": 1}],
            "actual_resolution_state": "open",
        }

        pdef = to_platform_deficiency(mock_gap)
        self.assertEqual(pdef.target_subject, "prop:carrier_license_valid")
        self.assertEqual(pdef.required_operator, "O")  # Fact gap -> Observe
        self.assertEqual(pdef.authority_gap_kind, AuthorityGapKind.FACT_GAP.value)
        self.assertTrue(pdef.is_unresolved)
        self.assertEqual(pdef.dependency_refs, [{"id": "rule:456", "revision": 1}])
        self.assertEqual(pdef.scope_ref, {"id": "scope:transport", "revision": 1})
        self.assertEqual(pdef.resolution_routes, ["investigate_fact"])


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

    # --------------------------------------------------------------------------
    # 5. OWNERSHIP MANIFEST & ARCHITECTURAL REUSE INTEGRITY
    # --------------------------------------------------------------------------
    def test_ownership_manifest_completeness(self) -> None:
        """Every authority module must have an explicit ownership classification."""
        manifest_path = BASE_DIR / "consolidation" / "ownership_manifest_v0_1.json"
        self.assertTrue(manifest_path.exists(), f"Missing manifest at {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest_modules = {m["module"]: m for m in manifest["modules"]}
        authority_dir = BASE_DIR / "intel_authority"
        py_files = {p.name for p in authority_dir.glob("*.py")}

        # Every file in intel_authority must be declared in ownership manifest
        undeclared = py_files - set(manifest_modules.keys())
        self.assertEqual(
            len(undeclared), 0,
            f"Found undeclared authority modules without ownership entry: {undeclared}"
        )

        # Every REUSE module must declare a platform owner and generic semantics to remove
        for mod_name, entry in manifest_modules.items():
            if entry["classification"] == "REUSE":
                self.assertIsNotNone(entry["platform_owner"], f"{mod_name} REUSE must have platform owner")
                self.assertTrue(len(entry["generic_semantics_to_remove"]) > 0, f"{mod_name} must declare generic semantics to remove")

    def test_domain_neutrality_imports(self) -> None:
        """Shared platform machinery must never import intel_authority (Core -/-> Domain)."""
        import ast
        core_root = BASE_DIR.parents[2] / "mapeogeo"
        if not core_root.exists():
            return  # In modular setups where mapeogeo root is elsewhere

        for py_path in core_root.glob("**/*.py"):
            with open(py_path, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=str(py_path))
                except Exception:
                    continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(
                            "intel_authority", alias.name,
                            f"Domain neutrality violation: {py_path} imports {alias.name}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    self.assertNotIn(
                        "intel_authority", mod,
                        f"Domain neutrality violation: {py_path} imports from {mod}"
                    )

    def test_authority_certificate_preserves_unresolved(self) -> None:
        """Authority certificate witness strictly distinguishes UNRESOLVED from OBSTRUCTED."""
        with open(QUAL_DIR / "direct_oracle_v0_1.json", "r", encoding="utf-8") as f:
            oracle = json.load(f)

        unres_cell = next(c for c in oracle["cells"] if c["disposition"] == "unresolved")
        cert_unres = evaluate_authority_certificate(unres_cell["case"], self.context_privacy)
        self.assertEqual(cert_unres.status, "unresolved")
        self.assertTrue(cert_unres.is_unresolved)
        self.assertFalse(cert_unres.is_supported)
        self.assertFalse(cert_unres.is_obstructed)
        self.assertIsNone(cert_unres.witness_ref)
        self.assertIsNotNone(cert_unres.uncertainty_description)

    def test_authority_does_not_define_generic_event_graph(self) -> None:
        """Authority causal module delegates event graph and DAG traversal to PlatformCausalDAG."""
        import inspect
        from experiments.authority_assessment.v0_1.intel_authority import causal
        self.assertTrue(hasattr(causal, "PlatformCausalDAG"))
        relate_src = inspect.getsource(causal.relate_events)
        self.assertIn("PlatformCausalDAG", relate_src)

    def test_authority_does_not_own_generic_resource_ledger(self) -> None:
        """Authority allocations module delegates ledger and leases to PlatformResourceEngine."""
        import inspect
        from experiments.authority_assessment.v0_1.intel_authority import allocations
        self.assertTrue(hasattr(allocations, "PlatformResourceEngine"))
        self.assertTrue(hasattr(allocations, "AuthorityAllocationConstraint"))
        # AllocationManager is deprecated wrapper
        self.assertIn("DEPRECATED in C2", allocations.AllocationManager.__doc__ or "")

    def test_authority_does_not_define_second_persistent_store(self) -> None:
        """Authority store delegates persistence to PlatformRecordStore and retains schema."""
        from experiments.authority_assessment.v0_1.intel_authority import store
        self.assertTrue(hasattr(store, "PlatformRecordStore"))
        self.assertTrue(hasattr(store, "AuthorityRecordSchema"))
        self.assertTrue(issubclass(store.AuthorityStore, store.PlatformRecordStore))

    def test_authority_does_not_define_generic_candidate_router(self) -> None:
        """Authority query module delegates candidate iteration and budget cutoff to router."""
        import inspect
        from experiments.authority_assessment.v0_1.intel_authority import queries
        self.assertTrue(hasattr(queries, "evaluate_candidate_domain"))
        self.assertTrue(hasattr(queries, "AuthorityActionQuery"))
        self.assertTrue(hasattr(queries, "AuthorityActorQuery"))
        enum_actions_src = inspect.getsource(queries.enumerate_actions)
        enum_actors_src = inspect.getsource(queries.enumerate_actors)
        self.assertIn("evaluate_candidate_domain", enum_actions_src)
        self.assertIn("evaluate_candidate_domain", enum_actors_src)


if __name__ == "__main__":
    unittest.main()


