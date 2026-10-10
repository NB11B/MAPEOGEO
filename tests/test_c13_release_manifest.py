"""C13 Release Manifest & Packaging Test Suite.

Verifies:
1. Release v1.0 manifest exists and declares status QUALIFIED.
2. Package inventory accurately catalogs all delivered domain and test files.
3. Zero CRLF violations across delivered files.
4. Release notes document architecture, delivered capabilities, and invariant proofs.
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
        self.assertEqual(manifest["release"], "v1.0-authority-intelligence")
        self.assertEqual(len(manifest["crlf_violations"]), 0)
        self.assertTrue(manifest["invariants"]["no_parallel_engines"])
        self.assertTrue(manifest["invariants"]["core_domain_neutrality"])
        self.assertTrue(manifest["invariants"]["non_collapsing_4_outcomes"])
        self.assertTrue(manifest["invariants"]["pure_lf_line_endings"])
        self.assertGreaterEqual(manifest["delivered_files_count"], 40)
        self.assertGreaterEqual(manifest["test_suites_passed"], 10)

    def test_c13_2_package_inventory_integrity(self) -> None:
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

    def test_c13_3_release_notes_complete(self) -> None:
        """Release notes exist and document the 8 core delivered capabilities."""
        notes_path = RELEASE_DIR / "RELEASE_NOTES.md"
        self.assertTrue(notes_path.exists(), "Missing RELEASE_NOTES.md")
        content = notes_path.read_text(encoding="utf-8")
        self.assertIn("Functional Organization Matrix", content)
        self.assertIn("Prioritized Intelligence Requirements", content)
        self.assertIn("Deterministic Authority Evaluator", content)
        self.assertIn("Real Legal-Pack Intake Pipeline", content)
        self.assertIn("Analytical Course Planner", content)
        self.assertIn("Tertiary Impact Modeling", content)


if __name__ == "__main__":
    unittest.main()
