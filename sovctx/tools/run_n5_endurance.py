from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.endurance import CampaignCeilings, EnduranceSupervisor
from sovctx.node.work_db import WorkDatabase


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Gate N5 Autonomous Endurance Campaign Runner")
    parser.add_argument("--duration", type=int, default=3600, help="Campaign duration in seconds (default: 3600s / 1 hour)")
    parser.add_argument("--epoch-duration", type=int, default=600, help="Epoch duration in seconds (default: 600s / 10 minutes)")
    parser.add_argument("--max-sources", type=int, default=1500, help="Ceiling on admitted sources (default: 1500)")
    parser.add_argument("--max-blobs", type=int, default=3000, help="Ceiling on CAS blobs (default: 3000)")
    parser.add_argument("--pace-seconds", type=float, default=3.6, help="Pacing delay in seconds between acquisition cycles (default: 3.6s)")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    db = WorkDatabase(config.work_db_path, config.sqlite)

    ceilings = CampaignCeilings(
        max_sources=args.max_sources,
        max_blobs=args.max_blobs,
        max_depth=6,
        max_open_frontier=10000,
        max_unresolved=5000,
        max_disk_gb=20.0,
    )

    supervisor = EnduranceSupervisor(
        config=config,
        db=db,
        duration_seconds=args.duration,
        epoch_duration_seconds=args.epoch_duration,
        ceilings=ceilings,
        pace_seconds=args.pace_seconds,
    )

    print("===========================================================")
    print("SOVCTX Gate N5 Autonomous Endurance Expansion Campaign")
    print(f"Target Duration: {args.duration} s ({args.duration/3600:.2f} h) | Epoch Duration: {args.epoch_duration} s | Pace: {args.pace_seconds} s/source")
    print(f"Node: Jetson Nano 2GB (uow@192.168.55.1) | Work DB: {config.work_db_path}")
    print("===========================================================")

    receipt = supervisor.run_campaign()

    print("\n===========================================================")
    print(f"Gate N5 Campaign Verdict  : {receipt['verdict']}")
    print(f"Campaign ID               : {receipt['campaign_id']}")
    print(f"Termination Reason        : {receipt['termination_reason']}")
    print(f"Actual Duration           : {receipt['duration_actual_seconds']} s ({receipt['duration_actual_seconds']/3600:.2f} h)")
    print(f"Epochs Completed          : {receipt['epochs_completed']}")
    print(f"Sources Admitted          : {receipt['total_sources_admitted']}")
    print(f"Growth Efficiency (Eg)    : {receipt['useful_growth_efficiency'] * 100:.1f}%")
    print(f"Epistemic Error Rate re(t): {receipt['epistemic_error_rate_re_t']:.4f}")
    print("===========================================================")
    print(f"Receipt written to        : {config.evidence_dir / 'n5' / 'final' / 'n5_endurance_receipt.json'}")
    print(f"Report written to         : {config.evidence_dir / 'n5' / 'final' / 'n5_endurance_report.md'}")
    print("===========================================================")

    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
