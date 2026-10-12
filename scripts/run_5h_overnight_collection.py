#!/usr/bin/env python3
"""SOVCTX 5-Hour Overnight Autonomous Collection Campaign Daemon.

Executes continuous autonomous research across Stages A through E for 5 hours:
  - Stage A: Entity-scaffolded discovery (Pontryagin, Feldbaum, Chetaev, Krasovskii, Appell)
  - Stage B: Institutional domain traversal (Kazan School, Steklov Institute, CRAS Paris)
  - Stage C: Conceptual mathematical anomalies (constrained motion, converse stability)
  - Stage D: Unlabeled structural clusters
  - Stage E: Raw source batch exploration under epistemic UoW budget

Continuously records:
  - Discovered Candidate Bundles (status="PROPOSED")
  - Discovered Candidate Relation Concepts (status="PROPOSED_CONCEPT")
  - Physical ARM Cortex-A57 Telemetry (RSS MB, memory envelope, execution time)
  - G1.1 Diagnostic Observer Telemetry (speed projector, geometric residual ||r_t||)
  - Writes live checkpoints to evidence/n5/live_5h_collection.json and stream to evidence/n5/5h_collection_stream.jsonl

Usage:
  python scripts/run_5h_overnight_collection.py [--duration-hours 5.0]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.nano_research_worker import (
    NanoResearchWorker,
)
from sovctx.node.controlled_expansion_worker import (
    ControlledExpansionWorker,
)

def get_git_commit(cwd: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"

RESEARCH_CYCLES_CATALOG = [
    # Cycle 1: Stage A
    ("CYCLE:A1", "STAGE_A", ["Chetaev 1934", "Krasovskii 1959"], "STABILITY", False),
    ("CYCLE:A2", "STAGE_A", ["Pontryagin 1956", "Feldbaum 1960"], "OPTIMAL_CONTROL", False),
    ("CYCLE:A3", "STAGE_A", ["Gibbs 1879", "Appell 1899"], "ANALYTICAL_MECHANICS", False),

    # Cycle 2: Stage B
    ("CYCLE:B1", "STAGE_B", ["Kazan School of Mechanics Chetaev stability 1930 1950"], "STABILITY", False),
    ("CYCLE:B2", "STAGE_B", ["Steklov Institute Pontryagin optimal processes 1955 1965"], "OPTIMAL_CONTROL", False),
    ("CYCLE:B3", "STAGE_B", ["Moscow Mathematical Society nonholonomic dynamics Chaplygin 1911"], "ANALYTICAL_MECHANICS", False),

    # Cycle 3: Stage C
    ("CYCLE:C1", "STAGE_C", ["A recurring formulation involving admissibility, perturbation, and constrained motion Appell Chetaev"], "MECHANICS", False),
    ("CYCLE:C2", "STAGE_C", ["Sign-definiteness inversion and converse theorem derivation without analytical Lyapunov function"], "STABILITY", False),
    ("CYCLE:C3", "STAGE_C", ["Dual action information state in optimal control Feldbaum dual control theory"], "DUAL_CONTROL", False),

    # Cycle 4: Stage D (Unlabeled Clusters)
    ("CYCLE:D1", "STAGE_D", ["DOC:PRIGOGINE_1954", "DOC:GLANSDORFF_1964", "DOC:ONSAGER_1931"], "CONSTRAINT_FORMALISM_TRANSFER", True),
    ("CYCLE:D2", "STAGE_D", ["DOC:STRATONOVICH_1960", "DOC:ITO_1944", "DOC:MARCUS_1978"], "CONTINUOUS_DISCRETIZATION_DUALITY", True),

    # Cycle 5: Stage E (Raw Batches)
    ("CYCLE:E1", "STAGE_E", ["BATCH:SOV_STABILITY_1930_1970"], "STABILITY_EXPLORATION", False),
    ("CYCLE:E2", "STAGE_E", ["BATCH:SOV_CYBERNETICS_1950_1975"], "CYBERNETICS_EXPLORATION", False)
]

def run_collection_loop(duration_seconds: float = 18000.0) -> None:
    t_start = time.time()
    t_end = t_start + duration_seconds
    commit_sha = get_git_commit(REPO_ROOT)

    out_dir = REPO_ROOT / "evidence" / "n5"
    out_dir.mkdir(parents=True, exist_ok=True)
    live_checkpoint_path = out_dir / "live_5h_collection.json"
    stream_log_path = out_dir / "5h_collection_stream.jsonl"

    print("=" * 80)
    print("  SOVCTX 5-HOUR OVERNIGHT AUTONOMOUS COLLECTION CAMPAIGN")
    print(f"  Target Duration: {duration_seconds/3600:.2f} hours ({duration_seconds:.0f} seconds)")
    print(f"  Software Commit: {commit_sha}")
    print(f"  Checkpoint Path: {live_checkpoint_path}")
    print(f"  Stream Log Path: {stream_log_path}")
    print("=" * 80)

    worker = NanoResearchWorker("nano-5h-collection-daemon", shadow_mode=True)
    expansion_worker = ControlledExpansionWorker(worker=worker, shadow_mode=True)

    total_proposals = 0
    total_candidate_concepts = 0
    cycle_count = 0
    peak_rss = 0.0

    while time.time() < t_end:
        cycle_count += 1
        elapsed = time.time() - t_start
        remaining = max(0.0, t_end - time.time())

        print(f"\n[INFO] Starting Exploration Epoch {cycle_count} (Elapsed: {elapsed/60:.1f}m, Remaining: {remaining/60:.1f}m)...")

        for cid, stage, query_data, domain_or_pred, is_concept in RESEARCH_CYCLES_CATALOG:
            if time.time() >= t_end:
                break

            t0 = time.perf_counter()
            q_str = " ".join(query_data) if isinstance(query_data, list) else str(query_data)

            if stage == "STAGE_A":
                telem = expansion_worker.worker.execute_primary_research_uow(
                    uow_id=f"UOW:5H:{cid}:{cycle_count}",
                    target_query=q_str
                )
            elif stage == "STAGE_B":
                telem = expansion_worker.execute_stage_b_institution_probe(
                    f"{cid}:{cycle_count}",
                    q_str
                )
            elif stage == "STAGE_C":
                telem = expansion_worker.execute_stage_c_anomaly_probe(
                    f"{cid}:{cycle_count}",
                    q_str
                )
            elif stage == "STAGE_D":
                telem = expansion_worker.execute_stage_d_cluster_probe(
                    f"{cid}:{cycle_count}",
                    query_data
                )
            else:
                telem = expansion_worker.execute_stage_e_raw_discovery_uow(
                    domain_or_pred,
                    f"{cid}:{cycle_count}"
                )

            dt = (time.perf_counter() - t0) * 1000.0
            total_proposals += 1
            if is_concept:
                total_candidate_concepts += 1

            residual = expansion_worker.compute_candidate_concept_residual(domain_or_pred, len(query_data))
            peak_rss = max(peak_rss, telem.worker_rss_mb)

            stream_entry = {
                "epoch": cycle_count,
                "cycle_id": cid,
                "stage": stage,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": round(dt, 2),
                "rss_mb": round(telem.worker_rss_mb, 2),
                "claims_count": len(telem.candidate_bundle.claims),
                "entities_count": len(telem.candidate_bundle.entities),
                "geometric_residual": round(residual, 4),
                "is_candidate_concept": is_concept,
                "evidence_hash": telem.candidate_bundle.compute_evidence_hash(),
                "status": "PROPOSED_CONCEPT" if is_concept else "PROPOSED"
            }

            with open(stream_log_path, "a", encoding="utf-8") as f_stream:
                f_stream.write(json.dumps(stream_entry) + "\n")

            # Update rolling checkpoint
            checkpoint_data = {
                "campaign_id": "UQ-N4.2-5H-OVERNIGHT-COLLECTION",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "commit": commit_sha,
                "status": "RUNNING" if time.time() < t_end else "COMPLETED",
                "elapsed_seconds": round(time.time() - t_start, 2),
                "total_target_seconds": duration_seconds,
                "progress_pct": round(((time.time() - t_start) / duration_seconds) * 100.0, 2),
                "epochs_completed": cycle_count,
                "total_proposals_emitted": total_proposals,
                "candidate_concepts_proposed": total_candidate_concepts,
                "peak_worker_rss_mb": round(peak_rss, 2),
                "latest_telemetry": stream_entry
            }

            with open(live_checkpoint_path, "w", encoding="utf-8") as f_chk:
                json.dump(checkpoint_data, f_chk, indent=2)

        # Brief throttle between full epoch cycles
        time.sleep(2.0)

    # Final summary update
    checkpoint_data["status"] = "COMPLETED"
    checkpoint_data["progress_pct"] = 100.0
    with open(live_checkpoint_path, "w", encoding="utf-8") as f_chk:
        json.dump(checkpoint_data, f_chk, indent=2)

    print("\n" + "=" * 80)
    print(f"  5-HOUR COLLECTION CAMPAIGN COMPLETED")
    print(f"  Total Epochs: {cycle_count}")
    print(f"  Total Proposals: {total_proposals}")
    print(f"  Candidate Concepts: {total_candidate_concepts}")
    print(f"  Peak RSS: {peak_rss:.2f} MB")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="5-Hour Overnight Autonomous Collection Campaign Daemon")
    parser.add_argument("--duration-hours", type=float, default=5.0, help="Duration in hours (default: 5.0)")
    parser.add_argument("--duration-seconds", type=float, default=None, help="Duration in seconds (overrides hours)")
    args = parser.parse_args()

    dur_sec = args.duration_seconds if args.duration_seconds is not None else (args.duration_hours * 3600.0)
    run_collection_loop(duration_seconds=dur_sec)
