from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.checkpoint import CheckpointSubsystem
from sovctx.node.config import load_config
from sovctx.node.endurance import CampaignCeilings, EnduranceSupervisor
from sovctx.node.endurance_metrics import (
    EnduranceMetricsTracker,
    EpistemicPause,
    ResourcePause,
)
from sovctx.node.recovery import RecoveryManager
from sovctx.node.work_db import WorkDatabase


def run_n5_qualification() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        db_path = temp_dir / "qualify_n5.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()

        # Redirect evidence dir to temp for qualification test
        chk_dir = temp_dir / "n5" / "checkpoints"
        chk_sub = CheckpointSubsystem(db, chk_dir)
        recovery_mgr = RecoveryManager(config, db, chk_sub)

        # 1. Recovery Audit
        rec_report = recovery_mgr.perform_startup_recovery()
        recovery_passed = rec_report.status == "PASS"

        # 2. Checkpoint & State Hash
        chk1 = chk_sub.create_checkpoint(1, {"TIKHONOV": "HISTORICALLY_ATTESTED"})
        chk_latest = chk_sub.load_latest_checkpoint()
        checkpoint_passed = chk_latest is not None and chk_latest.checkpoint_id == chk1.checkpoint_id

        # 3. Circuit Breaker Test - Resource Pause
        tracker = EnduranceMetricsTracker(temp_dir / "n5")
        resource_pause_passed = False
        class MockResourceSample:
            thermal_max_c = 78.0  # > 75C trigger
            ram_available_mb = 1200.0
            swap_used_gb = 0.1
            worker_rss_mb = 50.0

        try:
            tracker.check_circuit_breakers(MockResourceSample(), {}, {})
        except ResourcePause:
            resource_pause_passed = True

        # 4. Circuit Breaker Test - Epistemic Pause
        epistemic_pause_passed = False
        try:
            tracker.check_circuit_breakers(None, {"canonical_promotion_violations": 1}, {})
        except EpistemicPause:
            epistemic_pause_passed = True

        # 5. Short Functional Supervisor Run
        ceilings = CampaignCeilings(max_sources=15, max_blobs=30)
        supervisor = EnduranceSupervisor(
            config=config,
            db=db,
            duration_seconds=3,
            epoch_duration_seconds=1,
            ceilings=ceilings,
        )
        receipt = supervisor.run_campaign()
        supervisor_passed = receipt["verdict"] == "PASS" and receipt["epochs_completed"] >= 1

        thresholds = {
            "substrate_parent_baseline_valid": recovery_passed,
            "checkpoint_system_verified": checkpoint_passed,
            "resource_pause_circuit_breaker_verified": resource_pause_passed,
            "epistemic_pause_circuit_breaker_verified": epistemic_pause_passed,
            "autonomous_supervisor_loop_verified": supervisor_passed,
            "epistemic_error_rate_zero": receipt["epistemic_error_rate_re_t"] == 0.0,
            "zero_canonical_promotions": receipt["invariants_ledger"]["canonical_promotion_violations"] == 0,
            "zero_mapeogeo_access": receipt["invariants_ledger"]["mapeogeo_cross_graph_access"] == 0,
        }

        verdict = "PASS" if all(thresholds.values()) else "FAIL"

        return {
            "verdict": verdict,
            "thresholds": thresholds,
            "receipt": receipt,
        }


def main() -> int:
    print("===========================================================")
    print("SOVCTX Gate N5 Autonomous Endurance Qualification")
    print("===========================================================")
    res = run_n5_qualification()

    print("\n--- Qualification Thresholds ---")
    for t_name, passed in res["thresholds"].items():
        print(f"  {t_name:42}: {'PASS' if passed else 'FAIL'}")

    print("===========================================================")
    print(f"Gate N5 Qualification Verdict : {res['verdict']}")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
