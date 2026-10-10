"""Unit and Governance Test Suite for Task T10: Qualification Campaign & Release Gate.

Verifies:
1. test_runner_separates_counts: Asserts separate counters for reference methods (152),
   QF cases (24, 19 passes / 5 legacy disagreements), direct oracle cells (288),
   action queries (72), actor queries (48), AQ obligations (56), host checks (18),
   and pilot cases (30).
2. test_runner_refuses_false_pass: Injected cell failure or missing case prevents gate closure.
3. test_gq01_release_governance (R24): Release publication closes fixed campaign only
   when all required gates pass; zero critical defects allowed.
4. test_gq02_release_selection_and_no_wall_clock_authority (R21, R23, R24):
   Requires explicit release_selection.json; strictly forbids implicit wall-clock authority.
5. test_all_seven_gates_closed: Gates G0a, G0b, G1, G2, G3, G4, and G5 achieved.
6. test_canonical_line_endings: Release manifest files contain strictly LF line endings.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from experiments.authority_assessment.v0_1.tools.publish_release import (
    _check_lf_endings,
    _sha256_file,
    publish_release,
)
from experiments.authority_assessment.v0_1.tools.run_qualification import (
    QualificationRunner,
    run_campaign,
)

BASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BASE_DIR.parents[2]
EVIDENCE_ROOT = REPO_ROOT / "evidence" / "authority_assessment" / "v0_1"
ARTIFACTS_ROOT = REPO_ROOT / "artifacts" / "authority_assessment" / "v0_1"


class TestT10QualificationCampaign(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = QualificationRunner(evidence_root=EVIDENCE_ROOT)

    # --------------------------------------------------------------------------
    # 1. TEST RUNNER SEPARATES COUNTS
    # --------------------------------------------------------------------------
    def test_runner_separates_counts(self) -> None:
        """Qualification runner records distinct fields for every dimension."""
        mech_rep = self.runner.run_stage_mechanical()
        host_rep = self.runner.run_stage_host()
        pilot_rep = self.runner.run_stage_pilot()

        c_mech = mech_rep["counters"]
        self.assertEqual(c_mech["reference_methods_passed"], 152)
        self.assertEqual(c_mech["reference_methods_total"], 152)
        self.assertEqual(c_mech["reference_qf_cases_passed"], 19)
        self.assertEqual(c_mech["reference_qf_legacy_disagreements"], 5)
        self.assertEqual(c_mech["reference_qf_cases_total"], 24)
        self.assertEqual(c_mech["direct_oracle_cells_matched"], 288)
        self.assertEqual(c_mech["direct_oracle_cells_total"], 288)
        self.assertEqual(c_mech["action_queries_matched"], 72)
        self.assertEqual(c_mech["action_queries_total"], 72)
        self.assertEqual(c_mech["actor_queries_matched"], 48)
        self.assertEqual(c_mech["actor_queries_total"], 48)
        self.assertEqual(c_mech["aq_obligations_passed"], 56)
        self.assertEqual(c_mech["aq_obligations_total"], 56)

        c_host = host_rep["counters"]
        self.assertEqual(c_host["host_checks_passed"], 18)
        self.assertEqual(c_host["host_checks_total"], 18)
        self.assertTrue(c_host["snapshot_immutability_verified"])

        c_pilot = pilot_rep["counters"]
        self.assertEqual(c_pilot["pilot_cases_evaluated"], 30)
        self.assertEqual(c_pilot["pilot_cases_total"], 30)
        self.assertEqual(c_pilot["pilot_agreements"], 30)

    # --------------------------------------------------------------------------
    # 2. TEST RUNNER REFUSES FALSE PASS
    # --------------------------------------------------------------------------
    def test_runner_refuses_false_pass(self) -> None:
        """Injected failure or missing case prevents passing status and gate closure."""
        # Mutate runner's oracle cell to wrong disposition
        corrupted_runner = QualificationRunner(evidence_root=EVIDENCE_ROOT)
        corrupted_runner.oracle["cells"][0]["disposition"] = "invented_false_disposition"

        rep = corrupted_runner.run_stage_mechanical()
        self.assertEqual(rep["status"], "failed")
        self.assertEqual(rep["gates"]["gate_g1_direct_oracle"], "failed")
        self.assertEqual(rep["gates"]["gate_g4_finite_mechanical"], "failed")
        self.assertEqual(rep["critical_defects"], 1)

    # --------------------------------------------------------------------------
    # 3. GQ01: RELEASE GOVERNANCE ENFORCEMENT
    # --------------------------------------------------------------------------
    def test_gq01_release_governance(self) -> None:
        """Publication refuses release if any stage report is failed or has critical defects."""
        with tempfile.TemporaryDirectory() as tmp_ev, tempfile.TemporaryDirectory() as tmp_out:
            ev_path = Path(tmp_ev)
            out_path = Path(tmp_out)

            # Create failed mechanical report
            runs_dir = ev_path / "runs" / "failed_run"
            runs_dir.mkdir(parents=True, exist_ok=True)
            failed_rep = {"stage": "mechanical", "status": "failed", "critical_defects": 1}
            with open(runs_dir / "qualification_report_mechanical.json", "w", encoding="utf-8") as f:
                json.dump(failed_rep, f)

            with open(ev_path / "release_selection.json", "w", encoding="utf-8") as f:
                json.dump({
                    "release_version": "0.1",
                    "selected_runs": {
                        "mechanical": "runs/failed_run/qualification_report_mechanical.json",
                        "host": "runs/campaign_final_v0_1/qualification_report_host.json",
                        "pilot": "runs/campaign_final_v0_1/qualification_report_pilot.json",
                    }
                }, f)

            code = publish_release(
                release_version="0.1",
                evidence_root_str=str(ev_path),
                output_root_str=str(out_path),
            )
            self.assertEqual(code, 1, "Failed report must prevent release publication!")

    # --------------------------------------------------------------------------
    # 4. GQ02: NO WALL-CLOCK IMPLICIT SELECTION
    # --------------------------------------------------------------------------
    def test_gq02_no_wall_clock_implicit_selection(self) -> None:
        """Absence of explicit release_selection.json strictly bars release publication."""
        with tempfile.TemporaryDirectory() as tmp_ev, tempfile.TemporaryDirectory() as tmp_out:
            ev_path = Path(tmp_ev)
            out_path = Path(tmp_out)
            # Do NOT create release_selection.json
            code = publish_release(
                release_version="0.1",
                evidence_root_str=str(ev_path),
                output_root_str=str(out_path),
            )
            self.assertEqual(code, 1, "Missing release_selection.json must fail (GQ02)!")

    # --------------------------------------------------------------------------
    # 5. ALL SEVEN GATES ACHIEVED IN PUBLISHED RELEASE
    # --------------------------------------------------------------------------
    def test_all_seven_gates_closed(self) -> None:
        """Release manifest records all seven gates: G0a, G0b, G1, G2, G3, G4, G5."""
        manifest_file = ARTIFACTS_ROOT / "release_manifest.json"
        self.assertTrue(manifest_file.exists(), f"Release manifest must exist at {manifest_file}")

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        expected_gates = ["G0a", "G0b", "G1", "G2", "G3", "G4", "G5"]
        self.assertEqual(manifest["gates_achieved"], expected_gates)
        self.assertEqual(manifest["critical_defects"], 0)
        self.assertEqual(manifest["counters"]["direct_oracle_cells_matched"], 288)
        self.assertEqual(manifest["counters"]["action_queries_matched"], 72)
        self.assertEqual(manifest["counters"]["actor_queries_matched"], 48)
        self.assertEqual(manifest["counters"]["aq_obligations_passed"], 56)
        self.assertEqual(manifest["counters"]["host_checks_passed"], 18)
        self.assertEqual(manifest["counters"]["pilot_agreements"], 30)

    # --------------------------------------------------------------------------
    # 6. CANONICAL LF LINE ENDINGS AND SOURCE HASHES
    # --------------------------------------------------------------------------
    def test_canonical_line_endings_and_source_hashes(self) -> None:
        """All files in release manifest exist, have verified SHA-256, and have strict LF endings."""
        manifest_file = ARTIFACTS_ROOT / "release_manifest.json"
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        source_manifest = manifest.get("source_manifest", {})
        self.assertGreaterEqual(len(source_manifest), 10)

        for rel_path, exp_hash in source_manifest.items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Source file must exist: {full_path}")
            self.assertTrue(_check_lf_endings(full_path), f"File must have strict LF line endings: {full_path}")
            act_hash = _sha256_file(full_path)
            self.assertEqual(act_hash, exp_hash, f"Hash mismatch for {rel_path}: got {act_hash}, exp {exp_hash}")


if __name__ == "__main__":
    unittest.main()
