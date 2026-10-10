"""Qualification Suite for Permanent Authority Domain Profile."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from mapeogeo.domains.authority.certification import (
    AuthorityCertificateWitness,
    CertificateOutcome,
    create_authority_certificate,
    map_authority_deficiencies,
)
from mapeogeo.domains.authority.evaluator import AuthorityEvaluator
from mapeogeo.domains.authority.ontology import (
    AuthorityDisposition,
    HohfeldianModality,
)

BASE_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = BASE_DIR / "experiments" / "authority_assessment" / "v0_1"
QUAL_DIR = EXPERIMENT_DIR / "qualification"
FIXTURES_DIR = EXPERIMENT_DIR / "fixtures" / "synthetic"


class TestAuthorityDomain(unittest.TestCase):
    def setUp(self) -> None:
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            self.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            self.sources_and_reviews = json.load(f)

        self.context_privacy = {
            "ref": {"id": "ctx:perm_auth", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        self.evaluator = AuthorityEvaluator(self.context_privacy)

    def test_hohfeldian_modalities_count(self) -> None:
        self.assertEqual(len(HohfeldianModality), 8)

    def test_direct_oracle_cell_evaluation(self) -> None:
        oracle_file = QUAL_DIR / "direct_oracle_v0_1.json"
        with open(oracle_file, "r", encoding="utf-8") as f:
            oracle = json.load(f)

        cell_000 = oracle["cells"][0]
        case = cell_000["case"]
        expected_disp = cell_000["disposition"]

        res = self.evaluator.assess_case(case)
        self.assertEqual(res.get("disposition"), expected_disp)

    def test_matrix_cell_query(self) -> None:
        res = self.evaluator.evaluate_matrix_cell(
            actor_id="actor:carrier:beta",
            affected_actor_id="actor:carrier:beta",
            operation_id="op:inspect_telemetry",
        )
        self.assertIn("disposition", res)

    def test_four_outcome_certification(self) -> None:
        cert_supp = create_authority_certificate("w1", AuthorityDisposition.SUPPORTED.value, ["r1"])
        self.assertEqual(cert_supp.outcome, CertificateOutcome.CERTIFIED)
        self.assertEqual(cert_supp.status, "admitted")
        self.assertTrue(cert_supp.is_certified)

        cert_proh = create_authority_certificate("w2", AuthorityDisposition.PROHIBITED.value, ["r2"])
        self.assertEqual(cert_proh.outcome, CertificateOutcome.OBSTRUCTED)
        self.assertEqual(cert_proh.status, "obstructed")
        self.assertTrue(cert_proh.is_obstructed)

        cert_unres = create_authority_certificate("w3", AuthorityDisposition.UNRESOLVED.value, [])
        self.assertEqual(cert_unres.outcome, CertificateOutcome.UNRESOLVED)
        self.assertEqual(cert_unres.status, "unresolved")
        self.assertTrue(cert_unres.is_unresolved)
        self.assertFalse(cert_unres.is_obstructed)
        self.assertFalse(cert_unres.is_certified)


if __name__ == "__main__":
    unittest.main()
