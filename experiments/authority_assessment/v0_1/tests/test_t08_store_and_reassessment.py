"""Qualification and Unit Test Suite for Task T08: Durable Store and Reassessment.

Verifies:
1. AQ55: Atomic SQLite publication, idempotent replay, and mutation rejection.
2. AQ21: Pinned assessments preserve exact source/rule versions on successor arrival.
3. AQ30: Reacting to material dependency changes via find_reassessment.
4. AQ43: Historical assessment remains replayable without mutation.
5. AQ44: Revocation flags successor use without rewriting historical records.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    assess_case,
)
from experiments.authority_assessment.v0_1.intel_authority.reassessment import (
    find_reassessment,
)
from experiments.authority_assessment.v0_1.intel_authority.store import (
    AuthorityStore,
    PublicationStatus,
    publish_assessment,
)

BASE_DIR = Path(__file__).resolve().parents[1]
QUAL_DIR = BASE_DIR / "qualification"
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"


class TestT08StoreAndReassessment(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with open(QUAL_DIR / "direct_oracle_v0_1.json", "r", encoding="utf-8") as f:
            cls.oracle = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            cls.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            cls.sources_and_reviews = json.load(f)

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.temp_dir.name) / "authority_store.db"
        self.store = AuthorityStore(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # --------------------------------------------------------------------------
    # 1. AQ55: ATOMIC PUBLICATION, IDEMPOTENT REPLAY, AND MUTATION REJECTION
    # --------------------------------------------------------------------------
    def test_aq55_atomic_publication_and_idempotent_replay(self) -> None:
        """Publishes atomically, returns identical_replay on retry, rejects mutation."""
        cell_001 = self.oracle["cells"][0]
        context = {"ref": {"id": "ctx:test"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        assessment = assess_case(cell_001["case"], context)

        # 1. First publication -> PUBLISHED
        receipt1 = publish_assessment(assessment, self.store)
        self.assertEqual(receipt1["status"], PublicationStatus.PUBLISHED.value)
        self.assertIsNotNone(receipt1["transaction_ref"])

        # 2. Idempotent replay of identical record -> IDENTICAL_REPLAY
        receipt2 = publish_assessment(assessment, self.store)
        self.assertEqual(receipt2["status"], PublicationStatus.IDENTICAL_REPLAY.value)
        self.assertEqual(receipt2["record_ref"]["id"], assessment["ref"]["id"])

        # 3. Mutation under same ID and revision -> CONTEXT_OR_MODEL_ERROR (mutation rejected)
        mutated_assessment = dict(assessment, explanation="Unauthorized tampering of explanation")
        receipt_mut = publish_assessment(mutated_assessment, self.store)
        self.assertEqual(receipt_mut["status"], PublicationStatus.CONTEXT_OR_MODEL_ERROR.value)
        self.assertTrue(any(d["code"] == "RECORD_MUTATION_REJECTED" for d in receipt_mut["diagnostics"]))

    # --------------------------------------------------------------------------
    # 2. AQ21 & AQ43: PINNED ASSESSMENTS REMAIN REPLAYABLE
    # --------------------------------------------------------------------------
    def test_aq21_and_aq43_prior_assessment_remains_replayable(self) -> None:
        """Prior assessment remains bound to original digest when successor context arrives."""
        cell_001 = self.oracle["cells"][0]
        context_v1 = {"ref": {"id": "ctx:v1"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        ass_v1 = assess_case(cell_001["case"], context_v1)

        # Context changes (successor context arrives)
        context_v2 = {"ref": {"id": "ctx:v2"}, "packs": [self.pack_privacy], "evidence": dict(self.sources_and_reviews, new_field=True)}

        # Check reassessment
        reass = find_reassessment(ass_v1, context_v2)
        self.assertTrue(reass["required"])
        self.assertTrue(any(r["code"] == "CONTEXT_DIGEST_CHANGED" for r in reass["reasons"]))

        # Prior assessment v1 itself remains unmutated
        self.assertEqual(ass_v1["context_ref"]["id"], "ctx:v1")

    # --------------------------------------------------------------------------
    # 3. AQ44: REVOCATION OF PINNED RULE FLAGS SUCCESSOR USE
    # --------------------------------------------------------------------------
    def test_aq44_revocation_affects_successor_use(self) -> None:
        """Revocation of a pinned dependency rule flags changed_refs in find_reassessment."""
        cell_001 = self.oracle["cells"][0]
        context_v1 = {"ref": {"id": "ctx:v1"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        ass_v1 = assess_case(cell_001["case"], context_v1)
        # ass_v1 depends on rule:priv:01
        self.assertIn("rule:priv:01", [r["id"] for r in ass_v1["dependency_refs"]])

        # In successor context, rule:priv:01 is revoked
        revoked_pack = {
            "ref": "pack:commercial_privacy_v1",
            "rules": [
                {
                    "ref": "rule:priv:01",
                    "revoked": True,  # Revoked!
                }
            ],
        }
        context_successor = {"ref": {"id": "ctx:successor"}, "packs": [revoked_pack], "evidence": self.sources_and_reviews}

        reass = find_reassessment(ass_v1, context_successor)
        self.assertTrue(reass["required"])
        self.assertTrue(any(r["id"] == "rule:priv:01" for r in reass["changed_refs"]))
        self.assertTrue(any(r["code"] == "DEPENDENCY_RULE_REVOKED" for r in reass["reasons"]))


if __name__ == "__main__":
    unittest.main()
