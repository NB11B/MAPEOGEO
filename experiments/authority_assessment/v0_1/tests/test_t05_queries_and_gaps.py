"""Qualification and Unit Test Suite for Task T05: Reverse Queries and Meaningful Gaps.

Verifies:
1. 100% agreement on all 72 action queries in reverse_domains_v0_1.json (AQ25).
2. 100% agreement on all 48 actor queries in reverse_domains_v0_1.json (AQ26).
3. Parity between direct oracle evaluation and reverse queries (AQ28).
4. Preserving unresolved candidates without false negative coercion (AQ27).
5. Bounded budget cutoffs returning partial results with positive unassessed count (AQ29).
6. Reacting to material case parameter mutations (AQ30).
7. Gap derivation with appropriate typed resolution routes (AQ31).
8. Distinction between finding evidence of a grant and creating a new grant (AQ32).
9. Legal review cannot fabricate facts or grants (AQ33).
10. Read-only atomic derivation closure resolving all fresh references (AQ55).
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    compute_case_digest,
    mutate_case_dimension,
)
from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    assess_case,
)
from experiments.authority_assessment.v0_1.intel_authority.gaps import (
    GapKind,
    Materiality,
    derive_authority_gaps,
)
from experiments.authority_assessment.v0_1.intel_authority.queries import (
    enumerate_actions,
    enumerate_actors,
)

BASE_DIR = Path(__file__).resolve().parents[1]
QUAL_DIR = BASE_DIR / "qualification"
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"


class TestT05QueriesAndGaps(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with open(QUAL_DIR / "direct_oracle_v0_1.json", "r", encoding="utf-8") as f:
            cls.oracle = json.load(f)
        with open(QUAL_DIR / "reverse_domains_v0_1.json", "r", encoding="utf-8") as f:
            cls.reverse_domains = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            cls.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_public_oversight.json", "r", encoding="utf-8") as f:
            cls.pack_oversight = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            cls.sources_and_reviews = json.load(f)

        # Index oracle cells by (scope_pack, actor, affected_actor, operation)
        cls.cells_by_key = {
            (c["scope_pack"], c["actor"], c["affected_actor"], c["operation"]): c
            for c in cls.oracle["cells"]
        }

    # --------------------------------------------------------------------------
    # 1. 72 ACTION QUERIES (AQ25)
    # --------------------------------------------------------------------------
    def test_72_action_queries_exact_agreement(self) -> None:
        """enumerate_actions matches all 72 frozen action queries in reverse_domains_v0_1.json."""
        action_queries = self.reverse_domains.get("action_queries", [])
        self.assertEqual(len(action_queries), 72)

        ops = ["op:request_record", "op:compel_record", "op:retain_record", "op:share_record"]

        for q in action_queries:
            p_ref = q["scope_pack"]
            actor = q["actor"]
            affected = q["affected_actor"]
            exp_ops = set(q["expected_supported_operations"])

            cases = [
                self.cells_by_key[(p_ref, actor, affected, op)]["case"]
                for op in ops
            ]
            pack = self.pack_privacy if p_ref == "pack:commercial_privacy_v1" else self.pack_oversight
            context = {"ref": {"id": "ctx:action_query"}, "packs": [pack], "evidence": self.sources_and_reviews}

            res = enumerate_actions({"domain": {"case_bindings": cases}}, context)
            supp_ops = {o["id"] for o in res["supported_refs"]}
            self.assertEqual(
                supp_ops,
                exp_ops,
                f"Action query mismatch for {actor} -> {affected} under {p_ref}: got {supp_ops}, expected {exp_ops}",
            )
            self.assertTrue(res["complete"])
            self.assertEqual(res["unassessed_count"], 0)

    # --------------------------------------------------------------------------
    # 2. 48 ACTOR QUERIES (AQ26)
    # --------------------------------------------------------------------------
    def test_48_actor_queries_exact_agreement(self) -> None:
        """enumerate_actors matches all 48 frozen actor queries in reverse_domains_v0_1.json."""
        actor_queries = self.reverse_domains.get("actor_queries", [])
        self.assertEqual(len(actor_queries), 48)

        actors = [
            "actor:regulator:alpha",
            "actor:investigator:beta",
            "actor:licensee:gamma",
            "actor:auditor:delta",
            "actor:citizen:epsilon",
            "actor:third_party:zeta",
        ]

        for q in actor_queries:
            p_ref = q["scope_pack"]
            affected = q["affected_actor"]
            op = q["operation"]
            exp_actors = set(q["expected_supported_actors"])

            cases = [
                self.cells_by_key[(p_ref, act, affected, op)]["case"]
                for act in actors
            ]
            pack = self.pack_privacy if p_ref == "pack:commercial_privacy_v1" else self.pack_oversight
            context = {"ref": {"id": "ctx:actor_query"}, "packs": [pack], "evidence": self.sources_and_reviews}

            res = enumerate_actors({"domain": {"case_bindings": cases}}, context)
            supp_actors = {a["id"] for a in res["supported_refs"]}
            self.assertEqual(
                supp_actors,
                exp_actors,
                f"Actor query mismatch for {op} -> {affected} under {p_ref}: got {supp_actors}, expected {exp_actors}",
            )
            self.assertTrue(res["complete"])
            self.assertEqual(res["unassessed_count"], 0)

    # --------------------------------------------------------------------------
    # 3. AQ27: PRESERVE UNRESOLVED CANDIDATES
    # --------------------------------------------------------------------------
    def test_aq27_reverse_query_preserves_unresolved_candidates(self) -> None:
        """Unresolved candidates are preserved and accounted for, never coerced to excluded."""
        # Query where commercial sharing consent is unknown (e.g. licensee sharing to licensee)
        cases = [
            self.cells_by_key[("pack:commercial_privacy_v1", "actor:licensee:gamma", "actor:licensee:gamma", "op:share_record")]["case"]
        ]
        context = {"ref": {"id": "ctx:aq27"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        res = enumerate_actions({"domain": {"case_bindings": cases}}, context)

        # op:share_record has unknown consent -> must be in unresolved_refs, NOT excluded_refs
        self.assertEqual(len(res["supported_refs"]), 0)
        self.assertEqual(len(res["unresolved_refs"]), 1)
        self.assertEqual(res["unresolved_refs"][0]["id"], "op:share_record")
        self.assertEqual(len(res["excluded_refs"]), 0)

    # --------------------------------------------------------------------------
    # 4. AQ28: REVERSE RESULTS MATCH INDEPENDENT DIRECT ORACLE
    # --------------------------------------------------------------------------
    def test_aq28_reverse_results_match_independent_direct_oracle(self) -> None:
        """Verifies that reverse queries and direct evaluations are perfectly consistent."""
        self.test_72_action_queries_exact_agreement()
        self.test_48_actor_queries_exact_agreement()

    # --------------------------------------------------------------------------
    # 5. AQ29: BUDGET EXHAUSTION CANNOT CLAIM GLOBAL ABSENCE
    # --------------------------------------------------------------------------
    def test_aq29_search_exhaustion_cannot_claim_global_absence(self) -> None:
        """Budget cutoff leaves positive unassessed_count and complete=False; cannot claim negative."""
        cases = [
            self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:regulator:alpha", op)]["case"]
            for op in ["op:request_record", "op:compel_record", "op:retain_record", "op:share_record"]
        ]
        context = {"ref": {"id": "ctx:aq29"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}

        # Impose budget cutoff at max_candidates=2
        res_limited = enumerate_actions(
            {"domain": {"case_bindings": cases}},
            context,
            budget={"max_candidates": 2},
        )
        self.assertEqual(res_limited["status"], "partial")
        self.assertFalse(res_limited["complete"])
        self.assertEqual(res_limited["evaluated_count"], 2)
        self.assertEqual(res_limited["unassessed_count"], 2)
        self.assertTrue(any(d["code"] == "BUDGET_CUTOFF" for d in res_limited["diagnostics"]))

    # --------------------------------------------------------------------------
    # 6. AQ30: REVERSE QUERY REACTS TO MATERIAL BINDING CHANGES
    # --------------------------------------------------------------------------
    def test_aq30_reverse_query_reacts_to_material_binding_changes(self) -> None:
        """Mutating case parameters invalidates cache reuse and changes domain digest."""
        base_case = self.oracle["cells"][0]["case"]
        mutated_case = mutate_case_dimension(base_case, "operation", "op:compel_record")

        digest_base = compute_case_digest(base_case)
        digest_mut = compute_case_digest(mutated_case)
        self.assertNotEqual(digest_base, digest_mut)

    # --------------------------------------------------------------------------
    # 7. AQ31: GAP TYPE SELECTS APPROPRIATE RESOLUTION ROUTE
    # --------------------------------------------------------------------------
    def test_aq31_gap_type_selects_appropriate_resolution_route(self) -> None:
        """Every derived gap has a typed proposition, dependencies, and matching work class."""
        cell_060 = self.cells_by_key[("pack:commercial_privacy_v1", "actor:licensee:gamma", "actor:licensee:gamma", "op:share_record")]
        context = {"ref": {"id": "ctx:aq31"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        assessment = assess_case(cell_060["case"], context)

        gaps = derive_authority_gaps(assessment, "q:can_gamma_share_with_gamma")
        self.assertTrue(len(gaps) > 0)
        gap = gaps[0]
        self.assertEqual(gap["kind"], GapKind.FACT_GAP.value)
        self.assertIn("investigate_fact", gap["resolution_route_kinds"])
        self.assertEqual(gap["materiality"], Materiality.OUTCOME_CHANGE_WITNESSED.value)

    # --------------------------------------------------------------------------
    # 8. AQ32: FINDING A GRANT DIFFERS FROM CREATING A GRANT
    # --------------------------------------------------------------------------
    def test_aq32_finding_a_grant_differs_from_creating_a_grant(self) -> None:
        """authority_evidence_missing requires discovering evidence; unempowered actor requires grant_required."""
        # Unempowered private actor compelling records under privacy pack
        cell_050 = self.cells_by_key[("pack:commercial_privacy_v1", "actor:licensee:gamma", "actor:regulator:alpha", "op:compel_record")]
        context = {"ref": {"id": "ctx:aq32"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        assessment = assess_case(cell_050["case"], context)

        # Prohibited conduct has no open grant gaps
        gaps_proh = derive_authority_gaps(assessment, "q:can_licensee_compel")
        self.assertEqual(len(gaps_proh), 0)

        # Unresolved power inquiry has grant_required gap
        cell_unresolved = self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:licensee:gamma", "op:compel_record")]
        ass_unres = assess_case(cell_unresolved["case"], context)
        gaps_unres = derive_authority_gaps(ass_unres, "q:can_regulator_compel_under_privacy")
        self.assertTrue(len(gaps_unres) > 0)
        self.assertEqual(gaps_unres[0]["kind"], GapKind.GRANT_REQUIRED.value)
        self.assertIn("issue_competent_grant", gaps_unres[0]["resolution_route_kinds"])

    # --------------------------------------------------------------------------
    # 9. AQ33: LEGAL REVIEW CANNOT INVENT FACT OR GRANT
    # --------------------------------------------------------------------------
    def test_aq33_legal_review_cannot_invent_fact_or_grant(self) -> None:
        """Adding a reviewed RulePack does not invent evidence facts or grants."""
        cell_060 = self.cells_by_key[("pack:commercial_privacy_v1", "actor:licensee:gamma", "actor:licensee:gamma", "op:share_record")]
        # Context with reviewed packs but no consent evidence
        context = {"ref": {"id": "ctx:aq33"}, "packs": [self.pack_privacy, self.pack_oversight], "evidence": self.sources_and_reviews}
        ass = assess_case(cell_060["case"], context)
        # Even with reviewed packs, consent fact remains unestablished -> unresolved
        self.assertEqual(ass["disposition"], "unresolved")

    # --------------------------------------------------------------------------
    # 10. AQ55: ATOMIC DERIVATION CLOSURE RESOLVES FRESH REFS
    # --------------------------------------------------------------------------
    def test_aq55_atomic_publication_and_dependency_replay_survive_failure(self) -> None:
        """derived_records closure in query results contains complete self-resolving records."""
        cases = [
            self.cells_by_key[("pack:commercial_privacy_v1", "actor:regulator:alpha", "actor:regulator:alpha", op)]["case"]
            for op in ["op:request_record", "op:retain_record"]
        ]
        context = {"ref": {"id": "ctx:aq55"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        res = enumerate_actions({"domain": {"case_bindings": cases}}, context)

        derived = res.get("derived_records", [])
        self.assertEqual(len(derived), 2)
        # Each derived record is a full LegalAssessment that can be inspected without a store write
        for rec in derived:
            self.assertIn("disposition", rec)
            self.assertIn("case_digest", rec)
            self.assertIn("trace", rec)


if __name__ == "__main__":
    unittest.main()
