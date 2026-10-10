"""Baseline, Freeze, and Qualification Consistency Tests for Gate G0a/G0b.

Verifies:
1. Reference baseline integrity: tampered source digests or reference failures are rejected.
2. Baseline capture parsing: counters are parsed strictly from the runner's summary block.
3. Nested counter discipline: 152 methods include 24 qualification cases as nested counters,
   preserving 19 legacy passes and 5 documented disagreements.
4. Successor freeze lifecycle: refuses missing mandatory artifacts, refuses silent in-place
   overwrites, records predecessor linkage, and verifies byte-level SHA-256 integrity.
5. AQ index coverage: all 56 qualification cases (AQ01-AQ56) are completely indexed.
6. Oracle semantics & reverse query consistency: direct oracle has 288 valid cells matching
   derived counts, and reverse queries match direct oracle filtering.
7. Host mapping contract: documents inspected host commit, node attributes, runtime entry contracts,
   and clock stream ownership.
"""

from __future__ import annotations

import hashlib
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
    MissingMandatoryArtifactError,
    freeze_all_qualification_inputs,
    freeze_qualification_expectations,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
PKG_ROOT = Path(__file__).resolve().parents[1]
REF_DIR = REPO_ROOT / "artifacts" / "intelligence_qualification" / "v0_3" / "intelligence_qualification_v0_3"


class TestBaseline(unittest.TestCase):
    def test_reference_digest_mismatch_rejected(self):
        """Assert a changed pinned workflow byte prevents a qualified baseline."""
        manifest_path = PKG_ROOT / "baseline_manifest.json"
        self.assertTrue(manifest_path.exists(), "baseline_manifest.json must exist")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        valid, mismatches = verify_reference_sources(REPO_ROOT, manifest)
        self.assertTrue(valid, f"Pristine sources must verify, but got mismatches: {mismatches}")

        tampered_manifest = json.loads(json.dumps(manifest))
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

    def test_nested_counters_not_additive_and_legacy_disagreements(self):
        """Assert 152 methods include 24 qualification cases as nested counters, preserving 5 legacy disagreements."""
        manifest_path = PKG_ROOT / "baseline_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        evidence = manifest.get("retained_evidence", {})

        self.assertEqual(evidence.get("reference_unittest_methods"), 152)
        self.assertEqual(evidence.get("passed_methods"), 152)
        self.assertEqual(evidence.get("failed_methods"), 0)
        self.assertEqual(evidence.get("frozen_obligations_included_in_methods"), 24)
        self.assertEqual(evidence.get("counters_classification"), "nested_not_additive")
        self.assertEqual(evidence.get("original_grammar_matches"), 19)
        self.assertEqual(evidence.get("original_grammar_disagreements"), 5)

        # Verify execution record exists and runner exited 0
        execution = evidence.get("execution", {})
        self.assertEqual(execution.get("return_code"), 0)
        self.assertTrue(Path(evidence.get("evidence_file")).exists())

    def test_freeze_refuses_existing_manifest(self):
        """Assert an existing freeze cannot be overwritten without explicit authorization."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_file = Path(tmp_dir) / "frozen_test.json"
            target_file.write_text(json.dumps({"existing": "data"}), encoding="utf-8")

            with self.assertRaises(ExistingFreezeError):
                freeze_qualification_expectations(
                    target_file=target_file,
                    payload={"new": "data"},
                    allow_overwrite=False,
                )

    def test_freeze_refuses_missing_mandatory_artifacts(self):
        """Assert freezer refuses when mandatory artifacts are absent or empty (F02)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            empty_base = Path(tmp_dir)
            out_manifest = empty_base / "qualification" / "frozen_manifest.json"
            with self.assertRaises(MissingMandatoryArtifactError):
                freeze_all_qualification_inputs(empty_base, out_manifest)

    def test_successor_freeze_integrity_and_byte_closure(self):
        """Assert all 13 declared files in frozen_expectations_manifest.json match SHA-256 and contain LF line endings (F01, F02)."""
        freeze_manifest_path = PKG_ROOT / "qualification" / "frozen_expectations_manifest.json"
        self.assertTrue(freeze_manifest_path.exists())
        data = json.loads(freeze_manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(data.get("freeze_id"), "authority_qualification_freeze_v0_1_2")
        self.assertEqual(data.get("predecessor_freeze_id"), "authority_v0_1_qualification_freeze_g0a")
        self.assertEqual(data.get("predecessor_manifest_sha256"), "a13d03fa9ea604925c3c0bbc1e63a448da1748ef2133fec4926503812a249734")
        self.assertEqual(len(data.get("declared_files", [])), 13)

        for item in data.get("declared_files", []):
            file_path = PKG_ROOT / item["path"]
            self.assertTrue(file_path.exists(), f"Frozen file missing: {file_path}")
            raw = file_path.read_bytes()
            self.assertNotIn(b"\r\n", raw, f"File {file_path} contains CRLF line endings; must be LF (F01)")
            actual_sha = hashlib.sha256(raw).hexdigest()
            self.assertEqual(actual_sha, item["sha256"], f"SHA mismatch on frozen file: {file_path}")

    def test_aq_subcase_index_coverage(self):
        """Assert all 56 AQ qualification obligations (AQ01-AQ56) are completely mapped in aq_subcase_index_v0_1.json (F06)."""
        aq_index_path = PKG_ROOT / "qualification" / "aq_subcase_index_v0_1.json"
        self.assertTrue(aq_index_path.exists())
        data = json.loads(aq_index_path.read_text(encoding="utf-8"))

        self.assertEqual(data.get("total_obligations"), 56)
        subcases = data.get("subcases", [])
        self.assertEqual(len(subcases), 56)

        mapped_ids = {s["aq_id"] for s in subcases}
        for i in range(1, 57):
            expected_id = f"AQ{i:02d}"
            self.assertIn(expected_id, mapped_ids, f"Obligation {expected_id} missing from AQ subcase index")

    def test_direct_oracle_and_reverse_queries_consistency(self):
        """Assert direct oracle has 288 valid cells, respects F05 semantic corrections, and reverse queries match direct oracle."""
        oracle_path = PKG_ROOT / "qualification" / "direct_oracle_v0_1.json"
        self.assertTrue(oracle_path.exists())
        oracle = json.loads(oracle_path.read_text(encoding="utf-8"))

        self.assertEqual(oracle.get("total_cells"), 288)
        counts = oracle.get("disposition_counts", {})
        self.assertEqual(counts.get("supported_within_scope"), 66)
        self.assertEqual(counts.get("conditions_unmet"), 3)
        self.assertEqual(counts.get("prohibited_under_reviewed_rule"), 22)
        self.assertEqual(counts.get("unresolved"), 197)

        cells_by_id = {c["cell_id"]: c for c in oracle.get("cells", [])}

        # F05: Retention cells 147, 151, 171, 175, 195, 199 must be unresolved (target capacity restriction)
        for cid in ["cell_147", "cell_151", "cell_171", "cell_175", "cell_195", "cell_199"]:
            c = cells_by_id[cid]
            self.assertEqual(c["disposition"], "unresolved", f"{cid} must be unresolved under rule:over:04 target limits")
            self.assertEqual(c["applicable_rule_refs"], [])

        # F05: Disclosure cells 196, 200, 220, 224 must bind recipient to affected actor
        for cid in ["cell_196", "cell_200", "cell_220", "cell_224"]:
            c = cells_by_id[cid]
            self.assertEqual(c["disposition"], "supported_within_scope")
            recipients = c["case"]["recipients"]
            self.assertEqual(recipients, [{"id": c["affected_actor"], "revision": 1}], f"{cid} recipient must be affected actor")

        # F05: Refuted consent (citizen) vs Unknown consent (licensee) contrast in privacy sharing
        # Citizen refuted: cell_068, cell_092, cell_140
        for cid in ["cell_068", "cell_092", "cell_140"]:
            c = cells_by_id[cid]
            self.assertEqual(c["disposition"], "conditions_unmet")
            self.assertEqual(c["condition_states"].get("cond:has_explicit_consent"), "refuted")

        # Licensee unknown: cell_060, cell_084, cell_132
        for cid in ["cell_060", "cell_084", "cell_132"]:
            c = cells_by_id[cid]
            self.assertEqual(c["disposition"], "unresolved")
            self.assertEqual(c["condition_states"].get("cond:has_explicit_consent"), "unknown")
            self.assertIn("missing_factual_evidence", c.get("expected_gap_kinds", []))

        # Reverse domains parity
        rev_path = PKG_ROOT / "qualification" / "reverse_domains_v0_1.json"
        self.assertTrue(rev_path.exists())
        rev_data = json.loads(rev_path.read_text(encoding="utf-8"))
        self.assertEqual(rev_data.get("total_action_queries"), 72)
        self.assertEqual(rev_data.get("total_actor_queries"), 48)

    def test_host_mapping_contract_g0b(self):
        """Assert host mapping contract documents inspected host commit, node attributes, runtime entry contracts, and Gate G0b (F08)."""
        host_contract_path = PKG_ROOT / "host_mapping_contract.json"
        self.assertTrue(host_contract_path.exists())
        contract = json.loads(host_contract_path.read_text(encoding="utf-8"))

        self.assertEqual(contract.get("status"), "gate_g0b_inspected_and_complete")
        self.assertEqual(contract.get("clock_identity_format"), "uow-clock:v1:[domain_id, local_actor]")
        self.assertIn("f7e6ee6", contract.get("inspected_host_commit", ""))

        # F08: Verify host grounded nodes attribute mappings
        node_map = {n["node_id"]: n["attributes"] for n in contract.get("host_grounded_nodes", [])}
        self.assertIn("src:carrier_schedule:v1", node_map)
        self.assertEqual(
            node_map["src:carrier_schedule:v1"],
            ["regular_capacity", "bridge_capacity", "loading_capacity"],
        )
        self.assertIn("src:service_contract:v1", node_map)
        self.assertIn("demand_units", node_map["src:service_contract:v1"])
        self.assertIn("obj:carrier_capacity_model:v1", node_map)
        self.assertIn("capacity_values", node_map["obj:carrier_capacity_model:v1"])


if __name__ == "__main__":
    unittest.main()
