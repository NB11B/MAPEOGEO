"""C13 Release Manifest & Packaging Test Suite.

Verifies:
1. Release v1.0 Candidate manifest exists and declares status QUALIFIED.
2. Complete 9 sealed release artifacts exist in artifacts/releases/v1_0_authority_intelligence/.
3. Reproducibility metadata and exact SHA-256 bindings are present.
4. Package inventory accurately catalogs delivered domain and test files with pure LF line endings.
5. Known limitations document discloses epistemic boundaries and legal constraints.
6. Qualification scorecard matches exact targets across mechanical, host, pilot, and domain tiers.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = REPO_ROOT / "artifacts" / "releases" / "v1_0_authority_intelligence"


class TestC13ReleaseManifest(unittest.TestCase):
    def test_c13_1_release_manifest_qualified(self) -> None:
        """Release manifest exists and certifies QUALIFIED status with 0 CRLF violations."""
        manifest_path = RELEASE_DIR / "RELEASE_MANIFEST.json"
        self.assertTrue(manifest_path.exists(), "Missing RELEASE_MANIFEST.json")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["status"], "QUALIFIED")
        self.assertTrue(manifest["release"].startswith("v1.0-authority-intelligence"))
        self.assertEqual(len(manifest["crlf_violations"]), 0)
        self.assertTrue(manifest["invariants"]["no_parallel_engines"])
        self.assertTrue(manifest["invariants"]["core_domain_neutrality"])
        self.assertTrue(manifest["invariants"]["non_collapsing_4_outcomes"])
        self.assertTrue(manifest["invariants"]["pure_lf_line_endings"])
        self.assertTrue(manifest["invariants"]["deterministic_integrity_binding"])
        self.assertTrue(manifest["invariants"]["analytical_exploration_distinct_from_admission"])
        self.assertGreaterEqual(manifest["delivered_files_count"], 35)
        self.assertGreaterEqual(manifest["test_suites_passed"], 10)

    def test_c13_2_all_nine_release_artifacts_exist(self) -> None:
        """All 9 sealed release artifacts are present in the release directory."""
        required_artifacts = [
            "RELEASE_MANIFEST.json",
            "PACKAGE_INVENTORY.json",
            "RELEASE_NOTES.md",
            "QUALIFICATION_REPORT.md",
            "QUALIFICATION_RESULTS.json",
            "SOURCE_PROVENANCE.json",
            "KNOWN_LIMITATIONS.md",
            "CROSS_DOMAIN_REPORT.json",
            "SCALE_REPORT.json",
        ]
        for name in required_artifacts:
            path = RELEASE_DIR / name
            self.assertTrue(path.exists(), f"Missing required release artifact: {name}")
            self.assertGreater(path.stat().st_size, 0, f"Artifact {name} is empty")

    def test_c13_3_reproducibility_bindings_present(self) -> None:
        """Manifest contains exact git commit, branch, and artifact hash bindings."""
        manifest_path = RELEASE_DIR / "RELEASE_MANIFEST.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        required_keys = [
            "source_commit",
            "source_branch",
            "base_commit",
            "authority_reference_commit",
            "intelligence_reference_digest",
            "package_inventory_sha256",
            "cross_domain_report_sha256",
            "benchmark_report_sha256",
            "qualification_results_sha256",
            "source_provenance_sha256",
            "known_limitations_sha256",
            "qualification_run_ids",
        ]
        for key in required_keys:
            self.assertIn(key, manifest, f"Missing reproducibility key: {key}")
            val = manifest[key]
            if isinstance(val, str):
                self.assertGreater(len(val), 0, f"Empty value for {key}")

    def test_c13_4_package_inventory_integrity(self) -> None:
        """Package inventory records all files with valid SHA-256 and LF line endings."""
        inv_path = RELEASE_DIR / "PACKAGE_INVENTORY.json"
        self.assertTrue(inv_path.exists(), "Missing PACKAGE_INVENTORY.json")

        with open(inv_path, "r", encoding="utf-8") as f:
            inv = json.load(f)

        files = inv.get("files", [])
        self.assertGreater(len(files), 0)
        for entry in files:
            self.assertIn("path", entry)
            self.assertIn("sha256", entry)
            self.assertEqual(len(entry["sha256"]), 64)
            self.assertEqual(entry["line_ending"], "LF")

    def test_c13_5_known_limitations_disclosures(self) -> None:
        """KNOWN_LIMITATIONS.md documents all 6 mandatory epistemic and legal boundaries."""
        lim_path = RELEASE_DIR / "KNOWN_LIMITATIONS.md"
        self.assertTrue(lim_path.exists(), "Missing KNOWN_LIMITATIONS.md")
        content = lim_path.read_text(encoding="utf-8")

        self.assertIn("Synthetic Profile Agreement", content)
        self.assertIn("Deterministic Integrity Binding", content)
        self.assertIn("No Law by Silence", content)
        self.assertIn("Analytical Course Discovery Does Not Grant Operational Admission", content)
        self.assertIn("Scoped Jurisdictional Coverage", content)
        self.assertIn("Epistemic Uncertainty", content)

    def test_c13_6_qualification_scorecard_integrity(self) -> None:
        """Qualification scorecard records 100% agreement across all verification dimensions."""
        qual_path = RELEASE_DIR / "QUALIFICATION_RESULTS.json"
        self.assertTrue(qual_path.exists(), "Missing QUALIFICATION_RESULTS.json")

        with open(qual_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sc = data["scorecard"]
        self.assertEqual(sc["reference_methods_passed"], 152)
        self.assertEqual(sc["direct_oracle_cells_matched"], 288)
        self.assertEqual(sc["action_queries_matched"], 72)
        self.assertEqual(sc["actor_queries_matched"], 48)
        self.assertEqual(sc["aq_obligations_passed"], 56)
        self.assertEqual(sc["host_checks_passed"], 18)
        self.assertEqual(sc["pilot_agreements"], 30)
        self.assertEqual(sc["c_series_suites_passed"], 10)


if __name__ == "__main__":
    unittest.main()
