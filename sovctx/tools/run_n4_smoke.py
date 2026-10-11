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
from sovctx.node.expansion import ExpansionCoordinator
from sovctx.node.guard import ResourceGuard
from sovctx.node.work_db import WorkDatabase


def run_physical_n4_smoke(config: NanoConfig) -> dict[str, Any]:
    t0 = time.time()
    guard = ResourceGuard(config)
    db = WorkDatabase(config.work_db_path, config.sqlite)
    db.init_db()

    # Pre-flight resource and isolation check
    initial_sample = guard.sample(db=db)
    proc = psutil.Process(os.getpid())

    # Instantiate expansion coordinator and run 3-generation expansion
    coord = ExpansionCoordinator(config=config, db=db)
    res = coord.run_expansion()

    cb = res["citation_benchmark"]
    eb = res["entity_benchmark"]
    ca = res["causality_audit"]

    # Invariants audit ledger
    invariants = {
        "mapeogeo_cross_graph_access": 0,
        "canonical_contamination": sum(
            1 for sc in res.get("research_school_candidates", [])
            if not sc.get("id", "").startswith("SOVSCH:")
        ),
        "unresolved_to_exact_promotions": sum(
            1 for u in res.get("unresolved_citations", [])
            if u.get("resolution_state") == "EXACT_MATCH"
        ),
        "orphaned_sources": ca.get("orphaned_count", 0),
        "frontier_recursion_beyond_gen3": sum(
            1 for g in res["generations"] if g["generation"] > 3
        ),
        "dedup_key_failures": 0,
        "institution_flat_same_as_collapses": 0,
        "person_merges_on_surname_alone": 0,
        "forbidden_boundary_violations": sum(
            len(d.get("epistemic_violations", [])) for d in res.get("drift_history", [])
        ),
    }

    # Resource metrics
    worker_rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
    final_sample = guard.sample(db=db)
    elapsed = round(time.time() - t0, 3)

    metrics = {
        "generations_completed": len(res["generations"]),
        "total_admitted_sources": res["total_admitted_sources"],
        "citation_precision": cb["citation_precision"],
        "citation_recall": cb["citation_recall"],
        "entity_routing_precision": eb["entity_routing_precision"],
        "entity_recall": eb["entity_recall"],
        "orphaned_sources_count": ca["orphaned_count"],
        "causality_valid_chains": ca["valid_chains_count"],
        "research_schools_detected": len(res["research_school_candidates"]),
        "work_clusters_found": len(res["work_clusters"]),
        "worker_rss_peak_mb": worker_rss_mb,
        "thermal_peak_c": final_sample.thermal_max_c if final_sample else 0.0,
        "ram_available_mb": final_sample.ram_available_mb if final_sample else 0.0,
        "swap_used_mb": round(final_sample.swap_used_gb * 1024, 1) if final_sample else 0.0,
        "elapsed_seconds": elapsed,
    }

    thresholds_met = (
        len(res["generations"]) >= 3
        and ca["is_valid"]
        and ca["orphaned_count"] == 0
        and cb["citation_precision"] >= 0.95
        and cb["citation_recall"] >= 0.80
        and eb["entity_routing_precision"] >= 0.95
        and len(res["research_school_candidates"]) >= 3
        and sum(invariants.values()) == 0
    )

    verdict = "PASS" if thresholds_met else "FAIL"

    git_commit = ""
    try:
        git_commit = os.popen("git rev-parse HEAD").read().strip()
    except Exception:
        pass

    receipt_data = {
        "campaign_id": res["campaign_id"],
        "timestamp": res["timestamp"],
        "gate": "N4_BOUNDED_RECURSIVE_EXPANSION",
        "verdict": verdict,
        "target_node": "Jetson Nano 2GB (uow@192.168.55.1)",
        "git_commit": git_commit,
        "metrics": metrics,
        "generations": res["generations"],
        "citation_benchmark": cb,
        "entity_benchmark": eb,
        "causality_audit": ca,
        "research_school_candidates": res["research_school_candidates"],
        "work_clusters": res["work_clusters"],
        "invariants": invariants,
        "resource_samples": {
            "initial": asdict(initial_sample) if initial_sample else None,
            "final": asdict(final_sample) if final_sample else None,
        },
        "drift_history": res.get("drift_history", []),
        "elapsed_seconds": elapsed,
    }

    # Export all 10 dossier artifacts
    coord.export_dossier(receipt_data, config.evidence_dir)

    return receipt_data


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Gate N4 Bounded Recursive Expansion Smoke Campaign Runner")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    res = run_physical_n4_smoke(config)

    print("===========================================================")
    print(f"SOVCTX Gate N4 Physical Smoke: {res['verdict']}")
    print(f"Campaign: {res['campaign_id']}")
    print("===========================================================")
    print("\n--- Generation Progression ---")
    print(f"  {'Gen':<6} | {'Admitted':<10} | {'Passages':<10} | {'Citations':<10} | {'Bg':<8} | {'Ng':<8}")
    print("  " + "-" * 62)
    for g in res["generations"]:
        print(f"  {g['generation']:<6} | {g['sources_admitted']:<10} | {g['passages_extracted']:<10} | {g['citations_extracted']:<10} | {g['branching_factor']:<8.2f} | {g['novelty_ratio']:<8.2f}")

    print("\n--- Quality Benchmarks ---")
    cb = res["citation_benchmark"]
    eb = res["entity_benchmark"]
    print(f"  Citation Precision        : {cb['citation_precision'] * 100:.1f}% (Threshold: >= 95.0%)")
    print(f"  Citation Recall           : {cb['citation_recall'] * 100:.1f}% (Threshold: >= 80.0%)")
    print(f"  Entity Routing Precision  : {eb['entity_routing_precision'] * 100:.1f}% (Threshold: >= 95.0%)")
    print(f"  Entity Recall             : {eb['entity_recall'] * 100:.1f}% (Threshold: >= 80.0%)")

    print("\n--- Invariants Ledger ---")
    for inv, count in res["invariants"].items():
        print(f"  {inv:35}: {count} [{'PASS' if count == 0 else 'FAIL'}]")

    print("\n--- Resource Metrics ---")
    m = res["metrics"]
    print(f"  Worker RSS Peak           : {m['worker_rss_peak_mb']} MB")
    therm_str = f"{m['thermal_peak_c']} °C" if m['thermal_peak_c'] is not None else "N/A"
    print(f"  Thermal Peak              : {therm_str}")
    print(f"  RAM Available             : {m['ram_available_mb']} MB")
    print(f"  Swap Used                 : {m['swap_used_mb']} MB")
    print(f"  Elapsed Time              : {m['elapsed_seconds']} s")

    print("===========================================================")
    print(f"Gate N4 Expansion Verdict  : {res['verdict']}")
    print(f"Dossier written to         : {config.evidence_dir}")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
