from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import NanoConfig, load_config
from sovctx.node.guard import ResourceGuard
from sovctx.node.synthesis import HistoricalSynthesisEngine
from sovctx.node.work_db import WorkDatabase


def run_physical_n45_smoke(config: NanoConfig) -> dict[str, Any]:
    t0 = time.time()
    guard = ResourceGuard(config)
    db = WorkDatabase(config.work_db_path, config.sqlite)
    db.init_db()

    # Pre-flight resource and isolation check
    initial_sample = guard.sample(db=db)
    proc = psutil.Process(os.getpid())

    # Instantiate synthesis engine and run historical synthesis across accumulated evidence
    engine = HistoricalSynthesisEngine(config=config, db=db)
    res = engine.run_synthesis()

    # Hardware resource metrics
    worker_rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
    final_sample = guard.sample(db=db)
    elapsed = round(time.time() - t0, 3)

    res["metrics"]["worker_rss_peak_mb"] = worker_rss_mb
    res["metrics"]["thermal_peak_c"] = final_sample.thermal_max_c if final_sample else None
    res["metrics"]["ram_available_mb"] = final_sample.ram_available_mb if final_sample else 0.0
    res["metrics"]["swap_used_mb"] = round(final_sample.swap_used_gb * 1024, 1) if final_sample else 0.0
    res["elapsed_seconds"] = elapsed
    res["resource_samples"] = {
        "initial": asdict(initial_sample) if initial_sample else None,
        "final": asdict(final_sample) if final_sample else None,
    }

    # Export all 8 Gate N4.5 artifacts
    exported = engine.export_dossier_suite(res, config.evidence_dir)
    res["exported_artifacts"] = {k: str(v) for k, v in exported.items()}

    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Gate N4.5 Epistemic Synthesis Smoke Campaign Runner")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    res = run_physical_n45_smoke(config)

    print("===========================================================")
    print(f"SOVCTX Gate N4.5 Physical Smoke: {res['verdict']}")
    print(f"Campaign: {res['campaign_id']}")
    print("===========================================================")
    print("\n--- Synthesis Metrics ---")
    m = res["metrics"]
    skip_keys = {"worker_rss_peak_mb", "thermal_peak_c", "ram_available_mb", "swap_used_mb"}
    for k, v in m.items():
        if k in skip_keys:
            continue
        if isinstance(v, float) and v <= 1.0:
            print(f"  {k:30}: {v * 100:.1f}%")
        else:
            print(f"  {k:30}: {v}")

    print("\n--- Invariants Ledger ---")
    for inv, count in res["invariants"].items():
        st = "PASS" if (count == 0 or inv == "provenance_completeness_met" and count == 1) else "FAIL"
        print(f"  {inv:35}: {count} [{st}]")

    print("\n--- Resource Metrics ---")
    print(f"  Worker RSS Peak           : {m['worker_rss_peak_mb']} MB")
    therm_str = f"{m['thermal_peak_c']} °C" if m['thermal_peak_c'] is not None else "N/A"
    print(f"  Thermal Peak              : {therm_str}")
    print(f"  RAM Available             : {m['ram_available_mb']} MB")
    print(f"  Swap Used                 : {m['swap_used_mb']} MB")
    print(f"  Elapsed Time              : {res['elapsed_seconds']} s")

    print("===========================================================")
    print(f"Gate N4.5 Synthesis Verdict : {res['verdict']}")
    print(f"Dossier written to          : {config.evidence_dir}")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
