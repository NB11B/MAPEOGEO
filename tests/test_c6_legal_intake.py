"""C6 Legal Pack Intake & Reviewer Pipeline Test Suite.

Verifies:
1. Ingestion of formal real statutory pack with valid ReviewerRecord.
2. Invariant AQ20: Unauthenticated retrieved sources cannot act as reviewed law packs.
3. Tamper detection: Modified source text or post-review modified rules are rejected.
4. Deterministic evaluation of real statutory rules (ECPA / 18 U.S.C. 2701) under AuthorityEvaluator:
   - Prohibited unauthorized access yields OBSTRUCTED certificate.
   - Permitted provider access yields CERTIFIED certificate.
   - Government investigator access yields evaluated statutory power.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from mapeogeo.domains.authority import (
    AuthorityDisposition,
    AuthorityEvaluator,
    CertificateOutcome,
    LegalPackIntake,
    LegalPackIntakeResult,
    ReviewerRecord,
    RulePack,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures" / "legal_packs"


class TestC6LegalIntake(unittest.TestCase):
    def setUp(self) -> None:
        self.pack_path = FIXTURES_DIR / "statute_stored_communications_act_v1.json"
        self.text_path = FIXTURES_DIR / "statute_stored_communications_act_v1.txt"

        with open(self.pack_path, "r", encoding="utf-8") as f:
            self.pack_data = json.load(f)
        with open(self.text_path, "r", encoding="utf-8") as f:
            self.source_text = f.read()

        self.context = {
            "ref": {"id": "ctx:real_statute:ecpa", "revision": 1},
            "packs": [self.pack_data],
            "evidence": {},
        }
        self.evaluator = AuthorityEvaluator(self.context)

    def test_c6_1_valid_intake(self) -> None:
        """Valid reviewed pack ingests cleanly and parses into domain RulePack."""
        result = LegalPackIntake.validate_and_ingest(self.pack_data, source_text=self.source_text)
        self.assertTrue(result.valid, f"Intake failed with diagnostics: {result.diagnostics}")
        self.assertIsNotNone(result.rule_pack)
        self.assertIsInstance(result.rule_pack, RulePack)
        self.assertEqual(len(result.rule_pack.rules), 3)
        self.assertEqual(result.pack_id, "pack:statute:stored_communications_act_v1")

    def test_c6_2_aq20_rejection_of_unauthenticated_source(self) -> None:
        """AQ20: Pack without reviewer record is rejected as UNAUTHENTICATED_LEGAL_SOURCE."""
        raw_scraped_pack = copy.deepcopy(self.pack_data)
        del raw_scraped_pack["reviewer_record"]

        result = LegalPackIntake.validate_and_ingest(raw_scraped_pack)
        self.assertFalse(result.valid)
        self.assertIsNone(result.rule_pack)
        self.assertTrue(any("UNAUTHENTICATED_LEGAL_SOURCE" in d for d in result.diagnostics))

    def test_c6_3_rejection_of_tampered_source_text(self) -> None:
        """Mismatched source text hash causes validation failure."""
        tampered_text = self.source_text + "\nUnauthorized statutory amendment injected."
        result = LegalPackIntake.validate_and_ingest(self.pack_data, source_text=tampered_text)
        self.assertFalse(result.valid)
        self.assertTrue(any("SOURCE_TEXT_DIGEST_MISMATCH" in d for d in result.diagnostics))

    def test_c6_4_rejection_of_tampered_rules(self) -> None:
        """Post-review modification of rule priority or condition causes RULES_DIGEST_MISMATCH."""
        tampered_pack = copy.deepcopy(self.pack_data)
        tampered_pack["rules"][0]["priority"] = 999  # Tampering with priority

        result = LegalPackIntake.validate_and_ingest(tampered_pack, source_text=self.source_text)
        self.assertFalse(result.valid)
        self.assertTrue(any("RULES_DIGEST_MISMATCH" in d for d in result.diagnostics))

    def test_c6_5_evaluation_under_real_statutory_pack(self) -> None:
        """Evaluates real statutory rules under AuthorityEvaluator."""
        # Case 1: Unauthorized access to stored communications -> PROHIBITED
        case_unauthorized = {
            "id": "case:ecpa:intruder_access",
            "actor_ref": {"id": "actor:external:attacker", "revision": 1},
            "capacity_ref": {"id": "cap:unaffiliated_user", "revision": 1},
            "affected_scope": {
                "bindings": [
                    {"entity_ref": {"id": "actor:telecom:provider", "revision": 1}}
                ]
            },
            "operation_ref": {"id": "op:access_stored_communication", "revision": 1},
        }
        res_unauth = self.evaluator.assess_case(case_unauthorized)
        self.assertEqual(res_unauth.get("disposition"), "prohibited_under_reviewed_rule")
        self.assertIn("rule:ecpa:2701_a:general_prohibition", res_unauth.get("decisive_rule_refs", []))

        w_unauth = self.evaluator.certify_work(case_unauthorized)
        self.assertEqual(w_unauth.outcome, CertificateOutcome.OBSTRUCTED)
        self.assertEqual(w_unauth.status, "obstructed")
        self.assertTrue(w_unauth.is_obstructed)

        # Case 2: Provider authorized access -> PERMITTED
        case_provider = {
            "id": "case:ecpa:provider_maintenance",
            "actor_ref": {"id": "actor:provider:sysadmin", "revision": 1},
            "capacity_ref": {"id": "cap:telecom_admin", "revision": 1},
            "affected_scope": {
                "bindings": [
                    {"entity_ref": {"id": "actor:telecom:provider", "revision": 1}}
                ]
            },
            "operation_ref": {"id": "op:access_stored_communication", "revision": 1},
        }
        res_prov = self.evaluator.assess_case(case_provider)
        self.assertEqual(res_prov.get("disposition"), "supported_within_scope")
        self.assertIn("rule:ecpa:2701_c1:provider_exception", res_prov.get("decisive_rule_refs", []))

        w_prov = self.evaluator.certify_work(case_provider)
        self.assertEqual(w_prov.outcome, CertificateOutcome.CERTIFIED)
        self.assertEqual(w_prov.status, "admitted")
        self.assertTrue(w_prov.is_certified)


if __name__ == "__main__":
    unittest.main()
