from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add repo root to sys.path so sovctx is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.guard import ResourceGuard
from sovctx.node.work_db import WorkDatabase


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Jetson Nano Resource Governor & Isolation Guard")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--check", action="store_true", help="Perform a single sample and print verdict")
    parser.add_argument("--watch", action="store_true", help="Run continuously and sample periodically")
    parser.add_argument("--interval", type=float, default=10.0, help="Watch interval in seconds")
    parser.add_argument("--audit-isolation", action="store_true", help="Verify isolation from MAPEOGEO paths")
    parser.add_argument("--json", action="store_true", help="Format output as JSON")
    args = parser.parse_args()

    config = load_config(args.config)
    guard = ResourceGuard(config)
    db = WorkDatabase(config.work_db_path, config.sqlite)
    db.init_db()

    if args.audit_isolation:
        for p in config.isolation.forbidden_write_paths:
            assert guard.isolation.is_forbidden(p, is_write=True)
            assert guard.isolation.is_forbidden(p, is_write=False)
        print("SOVCTX Physical Isolation Audit: PASS (MAPEOGEO paths sealed)")
        return 0

    if args.watch:
        print(f"Starting ResourceGuard watch daemon on {config.data_root} (interval={args.interval}s)...")
        try:
            while True:
                sample = guard.sample(db=db)
                print(
                    f"[{sample.sampled_at}] verdict={sample.verdict} "
                    f"disk={sample.disk_free_gb}GB ram={sample.ram_available_mb}MB "
                    f"swap={sample.swap_used_gb}GB "
                    f"thermal={sample.thermal_max_c}°C load={sample.load_1m} "
                    f"rss={sample.worker_rss_mb}MB"
                )
                if sample.reasons:
                    print(f"  reasons: {'; '.join(sample.reasons)}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nResourceGuard stopped.")
            return 0

    # Default: single sample
    sample = guard.sample(db=db)
    if args.json:
        print(json.dumps(sample.__dict__, indent=2))
    else:
        print(f"SOVCTX Resource Sample ({sample.sampled_at}):")
        print(f"  Verdict:        {sample.verdict}")
        print(f"  Disk Free:      {sample.disk_free_gb} GB (stop <= {config.resources.disk_stop_free_gb} GB)")
        print(f"  RAM Available:  {sample.ram_available_mb} MB (stop <= {config.resources.ram_stop_available_mb} MB)")
        print(f"  Swap Used:      {sample.swap_used_gb} GB (stop >= {config.resources.swap_stop_used_gb} GB)")
        print(f"  Thermal Peak:   {sample.thermal_max_c} °C (stop >= {config.resources.thermal_stop_c} °C)")
        print(f"  1-min Load:     {sample.load_1m} (stop >= {config.resources.load1_stop})")
        print(f"  Worker RSS:     {sample.worker_rss_mb} MB (stop >= {config.resources.max_worker_rss_mb} MB)")
        if sample.reasons:
            print(f"  Reasons:        {'; '.join(sample.reasons)}")

    return 0 if sample.verdict != "STOP" else 1


if __name__ == "__main__":
    raise SystemExit(main())
