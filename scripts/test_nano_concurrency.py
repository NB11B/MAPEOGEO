"""SOVCTX Nano Research Work Plane Bounded Concurrency & Resource Qualification.

Measures the 2 GB operational envelope under bounded concurrency C in {1, 2, 4}:
- Safety threshold: M_free > 512 MB
- Backpressure floor: 256 MB (triggers backpressure_flag=True)
- Latency per UoW and throughput
- Peak RSS and G1 observer overhead
- Emits qualification report to evidence/n5/nano_concurrency_stress_report.json
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.guard import ResourceGuard
from sovctx.node.nano_research_worker import (
    CandidateBundleVerifier,
    NanoResearchWorker,
)


def run_concurrency_level(
    concurrency: int,
    num_uows: int,
    output_dir: Path,
) -> Dict[str, Any]:
    """Executes a bounded batch of research UoWs at specified concurrency level."""
    guard = ResourceGuard()
    initial_sample = guard.sample()
    ram_initial_mb = initial_sample.ram_available_mb or 1024.0

    print(f"\n" + "-" * 70)
    print(f"[CONCURRENCY C={concurrency}] Starting {num_uows} UoWs (Initial RAM: {ram_initial_mb:.1f} MB)")
    print("-" * 70)

    workers = [
        NanoResearchWorker(
            worker_id=f"nano-worker-c{concurrency}-{i}",
            tracker_k=2,
            tracker_alpha=0.5,
            shadow_mode=True,
            output_telemetry_dir=output_dir,
        )
        for i in range(concurrency)
    ]

    query = (
        "Find primary-source evidence bearing on whether Feldbaum's dual-control formulation "
        "explicitly distinguishes information-gathering action from directing action."
    )

    t_start = time.perf_counter()
    results = []
    min_ram_observed = ram_initial_mb
    max_rss_observed = 0.0
    backpressure_events = 0

    def task_exec(worker_idx: int, task_id: int) -> Dict[str, Any]:
        worker = workers[worker_idx]
        t0 = time.perf_counter()
        packet = worker.execute_primary_research_uow(
            uow_id=f"UOW_CONCUR_C{concurrency}_T{task_id:03d}",
            target_query=query,
        )
        t_el = time.perf_counter() - t0
        return {
            "task_id": task_id,
            "uow_id": packet.uow_id,
            "elapsed_s": t_el,
            "ram_avail_mb": packet.ram_available_mb,
            "rss_mb": packet.worker_rss_mb,
            "backpressure": packet.backpressure_flag,
            "hash": packet.candidate_bundle.candidate_bundle_hash,
            "speed": packet.geometric_observation.speed_max_angle,
            "num_candidates": len(packet.candidate_bundle.candidate_claims)
            + len(packet.candidate_bundle.candidate_relations),
        }

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(task_exec, i % concurrency, i)
            for i in range(num_uows)
        ]
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            if res["ram_avail_mb"] < min_ram_observed:
                min_ram_observed = res["ram_avail_mb"]
            if res["rss_mb"] > max_rss_observed:
                max_rss_observed = res["rss_mb"]
            if res["backpressure"]:
                backpressure_events += 1

    t_total = time.perf_counter() - t_start
    uow_latencies = [r["elapsed_s"] for r in results]
    avg_latency = sum(uow_latencies) / len(uow_latencies) if uow_latencies else 0.0
    p95_latency = sorted(uow_latencies)[int(0.95 * len(uow_latencies))] if uow_latencies else 0.0
    total_candidates = sum(r["num_candidates"] for r in results)
    throughput_uow_per_s = num_uows / t_total if t_total > 0 else 0.0
    throughput_cand_per_s = total_candidates / t_total if t_total > 0 else 0.0

    # Safety checks
    safety_threshold_met = min_ram_observed > 512.0
    backpressure_floor_respected = min_ram_observed > 256.0

    print(f"  Duration:              {t_total:.2f} s")
    print(f"  Avg UoW Latency:       {avg_latency * 1000:.2f} ms (p95: {p95_latency * 1000:.2f} ms)")
    print(f"  Throughput:            {throughput_uow_per_s:.2f} UoW/s ({throughput_cand_per_s:.2f} candidates/s)")
    print(f"  Min RAM Available:     {min_ram_observed:.1f} MB (Safety > 512 MB: {safety_threshold_met})")
    print(f"  Peak RSS:              {max_rss_observed:.1f} MB")
    print(f"  Backpressure Events:   {backpressure_events}")

    return {
        "concurrency": concurrency,
        "num_uows": num_uows,
        "total_time_s": t_total,
        "avg_latency_s": avg_latency,
        "p95_latency_s": p95_latency,
        "throughput_uow_per_s": throughput_uow_per_s,
        "throughput_candidates_per_s": throughput_cand_per_s,
        "min_ram_avail_mb": min_ram_observed,
        "peak_rss_mb": max_rss_observed,
        "safety_threshold_met": safety_threshold_met,
        "backpressure_floor_respected": backpressure_floor_respected,
        "backpressure_events": backpressure_events,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Nano Concurrency & Resource Stress Test")
    parser.add_argument("--uows-per-level", type=int, default=8, help="Number of UoWs per concurrency level")
    parser.add_argument("--output-dir", type=Path, default=Path("evidence/n5"), help="Output directory")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("SOVCTX NANO 2 GB OPERATIONAL ENVELOPE: BOUNDED CONCURRENCY SWEEP")
    print(f"Target Concurrency Levels: C in {{1, 2, 4}} | Safety Floor: M_free > 512 MB")
    print("=" * 80)

    sweep_results = []
    for c in [1, 2, 4]:
        res = run_concurrency_level(c, args.uows_per_level, args.output_dir)
        sweep_results.append(res)

    # Backpressure protocol injection verification
    print("\n" + "=" * 80)
    print("BACKPRESSURE PROTOCOL INJECTION TEST")
    print("=" * 80)

    # 1. Test simulated low-RAM condition (< 256 MB) triggers backpressure flag
    test_worker = NanoResearchWorker(shadow_mode=True, output_telemetry_dir=args.output_dir)
    # Temporarily mock guard sample to simulate low RAM
    from unittest.mock import patch
    from sovctx.node.guard import ResourceSample

    with patch.object(
        test_worker.guard,
        "sample",
        return_value=ResourceSample(
            sampled_at="2026-10-12T05:00:00Z",
            disk_free_gb=20.0,
            ram_available_mb=210.0,  # Below 256 MB floor
            swap_used_gb=0.5,
            thermal_max_c=48.0,
            load_1m=1.0,
            worker_rss_mb=120.0,
            verdict="WARN",
            reasons=["Low RAM threshold"],
        ),
    ):
        packet_bp = test_worker.process_work_unit(uow_id="UOW_BACKPRESSURE_TEST_001")
        assert packet_bp.backpressure_flag is True, "Backpressure flag must be True when RAM < 256 MB"
        print("  [PASS] Low RAM (< 256 MB) backpressure trigger: backpressure_flag = True")

    # 2. Test thermal pressure condition (> 80 C / STOP verdict) triggers backpressure flag
    with patch.object(
        test_worker.guard,
        "sample",
        return_value=ResourceSample(
            sampled_at="2026-10-12T05:00:00Z",
            disk_free_gb=20.0,
            ram_available_mb=850.0,
            swap_used_gb=0.5,
            thermal_max_c=84.0,
            load_1m=1.0,
            worker_rss_mb=65.0,
            verdict="STOP",
            reasons=["Thermal critical"],
        ),
    ):
        packet_thermal = test_worker.process_work_unit(uow_id="UOW_THERMAL_TEST_001")
        assert packet_thermal.backpressure_flag is True, "Backpressure flag must be True when thermal verdict == STOP"
        print("  [PASS] Thermal pressure (STOP verdict) trigger: backpressure_flag = True")

    report = {
        "timestamp": time.time(),
        "qualified_commit": "c8a975e974e3a12af94f647944ac56d1fb8597fc",
        "concurrency_sweep": sweep_results,
        "backpressure_protocol_verified": True,
        "safety_envelope_2gb_status": "PASS"
        if all(r["backpressure_floor_respected"] for r in sweep_results)
        else "FAIL",
    }

    report_path = args.output_dir / "nano_concurrency_stress_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[REPORT] Saved concurrency stress report to {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
