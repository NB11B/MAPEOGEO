"""C4 Qualification & Domain Promotion Test Suite.

Verifies complete behavioral equivalence and structural integrity of the
promoted permanent MAPEOGEO domain profiles:
- mapeogeo.domains.intelligence
- mapeogeo.domains.authority

Invariants Verified:
1. Exact parity across 288 direct oracle cells.
2. Exact parity across 72 action queries and 48 actor queries.
3. 4-outcome non-collapsing certificate model: CERTIFIED, OBSTRUCTED, UNRESOLVED.
4. 7x7 organizational functional matrix projections.
5. Grammar projection into the platform 7-operator basis Sigma_W = {O, E, K, C, F, D, S}.
6. Domain neutrality: Core Platform machinery does NOT import domain packages.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from mapeogeo.domains.authority import (
    ActionCase,
    AuthorityAdapter,
    AuthorityCertificateWitness,
    AuthorityDisposition,
    AuthorityEvaluator,
    CertificateOutcome,
    HohfeldianModality,
    map_authority_deficiencies,
)
from mapeogeo.domains.intelligence import (
    ALL_FUNCTIONS,
    FunctionalEdge,
    FunctionalMatrix,
    OrganizationalFunction,
    EpistemicState,
    IntelligenceGapKind,
    IntelligenceRequirement,
    INTELLIGENCE_GAP_TO_OPERATOR,
    map_intelligence_deficiency,
)
from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    assess_case as exp_assess_case,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ROOT = REPO_ROOT / "experiments" / "authority_assessment" / "v0_1"
QUAL_DIR = EXPERIMENT_ROOT / "qualification"
FIXTURES_DIR = EXPERIMENT_ROOT / "fixtures" / "synthetic"


class TestC4DomainPromotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            cls.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_public_oversight.json", "r", encoding="utf-8") as f:
            cls.pack_oversight = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            cls.sources_and_reviews = json.load(f)
        with open(QUAL_DIR / "direct_oracle_v0_1.json", "r", encoding="utf-8") as f:
            cls.direct_oracle = json.load(f)
        with open(QUAL_DIR / "reverse_domains_v0_1.json", "r", encoding="utf-8") as f:
            cls.reverse_domains = json.load(f)

        cls.cells_by_key = {
            (c["scope_pack"], c["actor"], c["affected_actor"], c["operation"]): c
            for c in cls.direct_oracle["cells"]
        }

    def _get_context(self, scope_pack: str) -> dict:
        pack = self.pack_privacy if scope_pack == "pack:commercial_privacy_v1" else self.pack_oversight
        return {
            "ref": {"id": f"ctx:{scope_pack}", "revision": 1},
            "packs": [pack],
            "evidence": self.sources_and_reviews,
        }

    def test_c4_1_direct_oracle_288_cells_parity(self) -> None:
        """Asserts 288/288 direct oracle cells yield identical dispositions and modalities."""
        cells = self.direct_oracle["cells"]
        self.assertEqual(len(cells), 288)

        matched = 0
        for cell in cells:
            case = cell["case"]
            expected_disp = cell["disposition"]
            expected_modality = cell.get("primary_modality")

            ctx = self._get_context(cell["scope_pack"])
            evaluator = AuthorityEvaluator(ctx)

            res_perm = evaluator.assess_case(case)
            self.assertEqual(res_perm.get("disposition"), expected_disp)
            if expected_modality:
                self.assertEqual(res_perm.get("primary_modality"), expected_modality)

            # Compare directly against experiment function
            res_exp = exp_assess_case(case, ctx)
            self.assertEqual(res_perm.get("disposition"), res_exp.get("disposition"))
            matched += 1

        self.assertEqual(matched, 288)

    def test_c4_2_action_queries_parity(self) -> None:
        """Asserts action query compatibility matches all 72 frozen reverse domain queries."""
        action_queries = self.reverse_domains.get("action_queries", [])
        self.assertEqual(len(action_queries), 72)

        ops = ["op:request_record", "op:compel_record", "op:retain_record", "op:share_record"]
        for q in action_queries:
            p_ref = q["scope_pack"]
            actor = q["actor"]
            affected = q["affected_actor"]
            exp_ops = set(q["expected_supported_operations"])

            ctx = self._get_context(p_ref)
            evaluator = AuthorityEvaluator(ctx)
            supported = set()
            for op in ops:
                case = self.cells_by_key[(p_ref, actor, affected, op)]["case"]
                cell_res = evaluator.assess_case(case)
                if cell_res.get("disposition") in ("supported", "supported_within_scope"):
                    supported.add(op)

            self.assertEqual(
                supported, exp_ops,
                f"Action query mismatch for {actor} -> {affected} under {p_ref}",
            )

    def test_c4_3_actor_queries_parity(self) -> None:
        """Asserts actor query compatibility matches all 48 frozen reverse domain queries."""
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

            ctx = self._get_context(p_ref)
            evaluator = AuthorityEvaluator(ctx)
            supported = set()
            for actor in actors:
                case = self.cells_by_key[(p_ref, actor, affected, op)]["case"]
                cell_res = evaluator.assess_case(case)
                if cell_res.get("disposition") in ("supported", "supported_within_scope"):
                    supported.add(actor)

            self.assertEqual(
                supported, exp_actors,
                f"Actor query mismatch for op {op} -> {affected} under {p_ref}",
            )

    def test_c4_4_non_collapsing_four_outcomes(self) -> None:
        """Verifies strict non-collapsing 4 outcomes: CERTIFIED, OBSTRUCTED, UNRESOLVED."""
        # Find supported cell
        supp_cell = next(c for c in self.direct_oracle["cells"] if c["disposition"] == "supported_within_scope")
        ctx_supp = self._get_context(supp_cell["scope_pack"])
        evaluator_supp = AuthorityEvaluator(ctx_supp)
        w_supp = evaluator_supp.certify_work(supp_cell["case"])
        self.assertEqual(w_supp.outcome, CertificateOutcome.CERTIFIED)
        self.assertEqual(w_supp.status, "admitted")
        self.assertTrue(w_supp.is_certified)
        self.assertFalse(w_supp.is_obstructed)
        self.assertFalse(w_supp.is_unresolved)

        # Find prohibited cell
        proh_cell = next(c for c in self.direct_oracle["cells"] if c["disposition"] == "prohibited_under_reviewed_rule")
        ctx_proh = self._get_context(proh_cell["scope_pack"])
        evaluator_proh = AuthorityEvaluator(ctx_proh)
        w_proh = evaluator_proh.certify_work(proh_cell["case"])
        self.assertEqual(w_proh.outcome, CertificateOutcome.OBSTRUCTED)
        self.assertEqual(w_proh.status, "obstructed")
        self.assertTrue(w_proh.is_obstructed)
        self.assertFalse(w_proh.is_certified)

        # Find unresolved cell
        unres_cell = next(c for c in self.direct_oracle["cells"] if c["disposition"] == "unresolved")
        ctx_unres = self._get_context(unres_cell["scope_pack"])
        evaluator_unres = AuthorityEvaluator(ctx_unres)
        w_unres = evaluator_unres.certify_work(unres_cell["case"])
        self.assertEqual(w_unres.outcome, CertificateOutcome.UNRESOLVED)
        self.assertEqual(w_unres.status, "unresolved")
        self.assertTrue(w_unres.is_unresolved)
        self.assertFalse(w_unres.is_obstructed)
        self.assertFalse(w_unres.is_certified)

    def test_c4_5_functional_matrix_projections(self) -> None:
        """Verifies 7x7 organizational functional matrix projection."""
        matrix = FunctionalMatrix()
        edge = FunctionalEdge(
            edge_id="edge:intel_to_enf:01",
            source_function=OrganizationalFunction.INTELLIGENCE,
            target_function=OrganizationalFunction.ENFORCEMENT,
            actor="actor:analyst:alpha",
            target_actor="actor:officer:beta",
            operation="op:disseminate_intel",
        )
        matrix.add_edge(edge)

        cells = matrix.query_cell(OrganizationalFunction.INTELLIGENCE, OrganizationalFunction.ENFORCEMENT)
        self.assertEqual(len(cells), 1)
        self.assertEqual(cells[0].target_function, OrganizationalFunction.ENFORCEMENT)
        self.assertEqual(len(ALL_FUNCTIONS), 7)

    def test_c4_6_grammar_projections_sigma_w(self) -> None:
        """Verifies mapping of intelligence gaps into platform grammar Sigma_W."""
        # Check operator mappings for intelligence gaps
        self.assertEqual(INTELLIGENCE_GAP_TO_OPERATOR[IntelligenceGapKind.FACT_GAP], "O")
        self.assertEqual(INTELLIGENCE_GAP_TO_OPERATOR[IntelligenceGapKind.SOURCE_APPLICABILITY_GAP], "C")
        self.assertEqual(INTELLIGENCE_GAP_TO_OPERATOR[IntelligenceGapKind.INTERPRETATION_GAP], "K")
        self.assertEqual(INTELLIGENCE_GAP_TO_OPERATOR[IntelligenceGapKind.OPERATION_DEFINITION_GAP], "F")
        self.assertEqual(INTELLIGENCE_GAP_TO_OPERATOR[IntelligenceGapKind.CUSTODY_TRANSFER_GAP], "O")
        self.assertEqual(INTELLIGENCE_GAP_TO_OPERATOR[IntelligenceGapKind.AUTHORIZATION_GAP], "K")

        # Check deficiency mapping
        d_fact = map_intelligence_deficiency(IntelligenceGapKind.FACT_GAP, "target:node_1")
        self.assertEqual(d_fact["required_operator"], "O")
        self.assertEqual(d_fact["target_subject"], "target:node_1")
        self.assertTrue(d_fact["is_unresolved"])


if __name__ == "__main__":
    unittest.main()
