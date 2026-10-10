"""Baseline and Freeze Verification Tests.

Verifies:
1. Pinned reference integrity: a tampered workflow byte or mismatched digest is rejected.
2. Freeze immutability: an existing manifest or expectation file cannot be silently overwritten.
3. Reference suite counters: reports 152 methods with 24 qualification cases as nested counters, not additive.
4. Preserved legacy baseline: preserves 19 passes and 5 documented disagreements.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from experiments.authority_assessment.v0_1.tools.capture_baseline import (
    DigestMismatchError,
    capture_baseline_manifest,
    verify_reference_sources,
)
from experiments.authority_assessment.v0_1.tools.freeze_expectations import (
    ExistingFreezeError,
    freeze_qualification_expectations,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
PKG_ROOT = Path(__file__).resolve().parents[1]
REF_DIR = REPO_ROOT / "artifacts" / "intelligence_qualification" / "v0_3" / "intelligence_qualification_v0_3"


class TestBaseline(unittest.TestCase):
    def test_reference_digest_mismatch_rejected(self):
        """Assert a changed pinned workflow byte prevents a qualified baseline."""
        # 1. Verification against pristine sources should pass
        manifest_path = PKG_ROOT / "baseline_manifest.json"
        self.assertTrue(manifest_path.exists(), "baseline_manifest.json must exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        valid, mismatches = verify_reference_sources(REPO_ROOT, manifest)
        self.assertTrue(valid, f"Pristine sources must verify, but got mismatches: {mismatches}")

        # 2. Tampered content must fail closed
        tampered_manifest = json.loads(json.dumps(manifest))
        # Tamper with the expected workflow.py hash
        for src in tampered_manifest.get("local_sources", []):
            if "workflow.py" in src["path"]:
                src["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"

        valid_tampered, mismatches_tampered = verify_reference_sources(REPO_ROOT, tampered_manifest)
        self.assertFalse(valid_tampered, "Tampered manifest must be rejected")
        self.assertTrue(any("workflow.py" in m for m in mismatches_tampered))

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_manifest = Path(tmp_dir) / "baseline_manifest.json"
            evidence_dir = Path(tmp_dir) / "evidence"
            with self.assertRaises(DigestMismatchError):
                capture_baseline_manifest(
                    repo_root=REPO_ROOT,
                    reference_dir=REF_DIR,
                    output_manifest_path=out_manifest,
                    evidence_dir=evidence_dir,
                    manifest_template=tampered_manifest,
                )

    def test_freeze_refuses_existing_manifest(self):
        """Assert an existing freeze cannot be overwritten without explicit authorization."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_file = Path(tmp_dir) / "frozen_test.json"
            target_file.write_text(json.dumps({"existing": "data"}), encoding="utf-8")

            # Attempting to freeze to an existing file must raise ExistingFreezeError
            with self.assertRaises(ExistingFreezeError):
                freeze_qualification_expectations(
                    target_file=target_file,
                    payload={"new": "data"},
                    allow_overwrite=False,
                )

    def test_nested_counters_not_additive_and_legacy_disagreements(self):
        """Assert 152 methods include 24 qualification cases as nested counters, preserving 5 legacy disagreements."""
        manifest_path = PKG_ROOT / "baseline_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        evidence = manifest.get("retained_evidence", {})

        self.assertEqual(evidence.get("reference_unittest_methods"), 152)
        self.assertEqual(evidence.get("frozen_obligations_included_in_methods"), 24)
        self.assertEqual(evidence.get("counters_classification"), "nested_not_additive")
        self.assertEqual(evidence.get("original_grammar_matches"), 19)
        self.assertEqual(evidence.get("original_grammar_disagreements"), 5)

    def test_frozen_expectations_integrity_g0a(self):
        """Assert all 9 files in frozen_expectations_manifest.json match their SHA-256 digests."""
        freeze_manifest_path = PKG_ROOT / "qualification" / "frozen_expectations_manifest.json"
        self.assertTrue(freeze_manifest_path.exists())
        data = json.loads(freeze_manifest_path.read_text(encoding="utf-8"))

        import hashlib
        for item in data.get("declared_files", []):
            file_path = PKG_ROOT / item["path"]
            self.assertTrue(file_path.exists(), f"Frozen file missing: {file_path}")
            actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
            self.assertEqual(actual_sha, item["sha256"], f"SHA mismatch on frozen file: {file_path}")

    def test_host_mapping_contract_g0b(self):
        """Assert host mapping contract documents inspected host commit, clock mapping, and Gate G0b."""
        host_contract_path = PKG_ROOT / "host_mapping_contract.json"
        self.assertTrue(host_contract_path.exists())
        contract = json.loads(host_contract_path.read_text(encoding="utf-8"))

        self.assertEqual(contract.get("status"), "gate_g0b_inspected_and_complete")
        self.assertEqual(contract.get("clock_identity_format"), "uow-clock:v1:[domain_id, local_actor]")
        self.assertIn("f7e6ee6", contract.get("inspected_host_commit", ""))


if __name__ == "__main__":
    unittest.main()
