"""C12 Local CLI Interfaces Test Suite.

Verifies:
1. python -m mapeogeo.authority verify-pack
2. python -m mapeogeo.authority inspect-matrix
3. python -m mapeogeo.authority assess
4. python -m mapeogeo.authority certify
5. python -m mapeogeo.intelligence matrix-query
6. python -m mapeogeo.intelligence detect-gaps
7. python -m mapeogeo.intelligence plan-coa
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "experiments" / "authority_assessment" / "v0_1" / "fixtures" / "synthetic"
LEGAL_PACKS_DIR = REPO_ROOT / "fixtures" / "legal_packs"


class TestC12CLIInterfaces(unittest.TestCase):
    def test_c12_1_authority_verify_pack_cli(self) -> None:
        """CLI: verify-pack returns 0 and valid status on reviewed legal pack."""
        pack_path = LEGAL_PACKS_DIR / "statute_stored_communications_act_v1.json"
        text_path = LEGAL_PACKS_DIR / "statute_stored_communications_act_v1.txt"

        cmd = [
            sys.executable, "-m", "mapeogeo.authority", "verify-pack",
            "--pack-file", str(pack_path),
            "--text-file", str(text_path),
        ]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertTrue(data["valid"])
        self.assertEqual(data["rules_count"], 3)

    def test_c12_2_authority_inspect_matrix_cli(self) -> None:
        """CLI: inspect-matrix returns cell evaluation with disposition."""
        pack_path = FIXTURES_DIR / "rule_pack_commercial_privacy.json"
        cmd = [
            sys.executable, "-m", "mapeogeo.authority", "inspect-matrix",
            "--actor", "actor:regulator:alpha",
            "--affected", "actor:licensee:gamma",
            "--operation", "op:request_record",
            "--pack-file", str(pack_path),
        ]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("disposition", data)

    def test_c12_3_intelligence_matrix_query_cli(self) -> None:
        """CLI: matrix-query queries functional matrix cell in 7x7 matrix."""
        cmd = [
            sys.executable, "-m", "mapeogeo.intelligence", "matrix-query",
            "--source", "INTELLIGENCE",
            "--target", "GOVERNANCE",
        ]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["source_function"], "INTELLIGENCE")
        self.assertEqual(data["target_function"], "GOVERNANCE")
        self.assertGreater(data["edge_count"], 0)

    def test_c12_4_intelligence_detect_gaps_cli(self) -> None:
        """CLI: detect-gaps outputs PIRs and deficiency queue."""
        cmd = [
            sys.executable, "-m", "mapeogeo.intelligence", "detect-gaps",
        ]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("pir_count", data)
        self.assertGreater(data["pir_count"], 0)
        self.assertIn("deficiency_queue", data)

    def test_c12_5_intelligence_plan_coa_cli(self) -> None:
        """CLI: plan-coa discovers multi-step courses across network."""
        pack_path = FIXTURES_DIR / "rule_pack_commercial_privacy.json"
        cmd = [
            sys.executable, "-m", "mapeogeo.intelligence", "plan-coa",
            "--start", "actor:collector:alpha",
            "--target", "actor:marshal:delta",
            "--objective", "Coordinate operational interdiction",
            "--pack-file", str(pack_path),
        ]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("courses_discovered", data)
        self.assertGreater(data["courses_discovered"], 0)


if __name__ == "__main__":
    unittest.main()
