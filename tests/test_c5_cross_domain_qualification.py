"""C5 Cross-Domain Qualification Unit Test Suite.

Verifies the 6 cross-domain audits:
1. Domain Neutrality (Core Platform -/-> Domain Profiles)
2. Representation Collision (CANDIDATE_REPRESENTS != REPRESENTS != SAME_SEMANTICS)
3. Graph Label Collision (Namespacing of power, field, ring, authority, operator)
4. Grammar Factoring (Sigma_W = {O, E, K, C, F, D, S})
5. Certification Isolation (MathWitness != AuthorityCertificateWitness != ExecutionReceipt)
6. Cross-Domain Useful Composition (Software -> Intel -> Authority -> Admission)
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.c5_cross_domain_qualification import (
    audit_certification_isolation,
    audit_cross_domain_composition,
    audit_domain_neutrality,
    audit_grammar_factoring,
    audit_graph_label_collisions,
    audit_representation_collision,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "cross_domain"


class TestC5CrossDomainQualification(unittest.TestCase):
    def test_c5_1_domain_neutrality(self) -> None:
        """Core Platform files must not import domain profiles."""
        res = audit_domain_neutrality(REPO_ROOT)
        self.assertEqual(res["status"], "PASSED")
        self.assertEqual(res["violations_count"], 0)
        self.assertGreater(res["core_files_audited"], 0)

    def test_c5_2_representation_collision(self) -> None:
        """CANDIDATE_REPRESENTS != REPRESENTS != SAME_SEMANTICS."""
        res = audit_representation_collision()
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["strict_discrimination_verified"])
        self.assertEqual(len(res["pairwise_collisions"]), 0)

    def test_c5_3_graph_label_collision(self) -> None:
        """Domain homonyms (power, field, ring, authority, operator) are strictly namespaced."""
        res = audit_graph_label_collisions()
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["all_definitions_namespaced"])
        self.assertIn("power", res["homonymous_terms_audited"])
        self.assertIn("authority", res["homonymous_terms_audited"])

    def test_c5_4_grammar_factoring(self) -> None:
        """All domains factor into Sigma_W = {O, E, K, C, F, D, S} without 8th operator."""
        res = audit_grammar_factoring()
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["basis_completeness"])
        self.assertEqual(set(res["platform_operator_basis"]), {"O", "E", "K", "C", "F", "D", "S"})

    def test_c5_5_certification_isolation(self) -> None:
        """MathWitness != AuthorityCertificateWitness != ExecutionReceipt; 4-outcome model preserves UNRESOLVED."""
        res = audit_certification_isolation()
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["four_outcome_model_verified"])

    def test_c5_6_cross_domain_useful_composition(self) -> None:
        """Software event -> Intel observation -> Authority assessment -> UoW admission."""
        res = audit_cross_domain_composition(REPO_ROOT)
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["composition_trace_complete"])
        self.assertEqual(res["admission_decision"]["uow_status"], "SCHEDULED")

    def test_c5_7_generated_artifacts_exist_and_valid(self) -> None:
        """Ensures all 5 formal C5 artifacts exist and parse as valid JSON / Markdown."""
        expected_files = [
            "CROSS_DOMAIN_ISOLATION.json",
            "DOMAIN_MAPPING_MATRIX.json",
            "GRAMMAR_FACTORING_AUDIT.json",
            "CERTIFICATION_ISOLATION.json",
            "C5_QUALIFICATION_REPORT.md",
        ]
        for fname in expected_files:
            p = ARTIFACTS_DIR / fname
            self.assertTrue(p.exists(), f"Missing expected artifact {p}")
            if p.suffix == ".json":
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.assertIsInstance(data, dict)
            elif p.suffix == ".md":
                text = p.read_text(encoding="utf-8")
                self.assertIn("Cross-Domain Qualification", text)


if __name__ == "__main__":
    unittest.main()
