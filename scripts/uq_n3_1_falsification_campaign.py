#!/usr/bin/env python3
"""SOVCTX Path Falsification & De-Anomalization Campaign (Milestone UQ-N3.1).

Executes the formal falsification campaign across the Soviet Constrained Mechanics Lineage:
  1. Appell (1899) vs Chaplygin (1911) chronology de-anomalization via Chetaev (1938) Retrospective Synthesis.
  2. Adversarial refutation of Vakonomic mechanics false equivalence.
  3. Adversarial refutation of 1980s Stanford robotics priority claim.
  4. Quarantining ambiguous heuristic edges.

Saves qualification report to evidence/n5/UQ_N3_1_QUALIFICATION_REPORT.json.
"""

from __future__ import annotations

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
from sovctx.node.path_falsification_worker import (
    PathFalsificationWorker,
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

def run_campaign() -> Dict[str, Any]:
    print("=" * 80)
    print("  SOVCTX CAMPAIGN UQ-N3.1: PATH FALSIFICATION & DE-ANOMALIZATION")
    print("  Axiom: DISCOVERED PATH != ACCEPTED LINEAGE")
    print("=" * 80)

    t_start = time.perf_counter()
    commit_sha = get_git_commit(REPO_ROOT)
    print(f"[INFO] Software Commit: {commit_sha}")

    worker = NanoResearchWorker("nano-falsification-worker-01", shadow_mode=True)
    falsify_worker = PathFalsificationWorker(worker=worker, shadow_mode=True)

    # 1. Execute Retrospective Synthesis Probe
    print("\n[STEP 1/3] Executing Retrospective Synthesis Discrimination Probe (Chetaev 1938) ...")
    t0 = time.perf_counter()
    telem_retro = falsify_worker.probe_retrospective_synthesis()
    dt_retro = (time.perf_counter() - t0) * 1000.0
    print(f"  -> UoW: {telem_retro.uow_id}")
    print(f"  -> Claims: {[c.claim_id for c in telem_retro.candidate_bundle.claims]}")
    print(f"  -> Sources: {[s.source_id for s in telem_retro.candidate_bundle.sources]}")
    print(f"  -> Latency: {dt_retro:.2f} ms | RSS: {telem_retro.worker_rss_mb:.2f} MB")

    # 2. Execute Vakonomic Physical Inequivalence Probe
    print("\n[STEP 2/3] Executing Vakonomic Equivalence Adversarial Probe ...")
    t0 = time.perf_counter()
    telem_vak = falsify_worker.probe_vakonomic_physical_equivalence()
    dt_vak = (time.perf_counter() - t0) * 1000.0
    vak_refused = len(telem_vak.candidate_bundle.claims) == 0
    print(f"  -> UoW: {telem_vak.uow_id}")
    print(f"  -> Claims count: {len(telem_vak.candidate_bundle.claims)} (Refused: {vak_refused})")
    print(f"  -> Latency: {dt_vak:.2f} ms")

    # 3. Execute Robotics Priority Anachronism Probe
    print("\n[STEP 3/3] Executing Robotics 1980s Anachronism Adversarial Probe ...")
    t0 = time.perf_counter()
    telem_rob = falsify_worker.probe_historical_priority()
    dt_rob = (time.perf_counter() - t0) * 1000.0
    rob_refused = len(telem_rob.candidate_bundle.claims) == 0
    print(f"  -> UoW: {telem_rob.uow_id}")
    print(f"  -> Claims count: {len(telem_rob.candidate_bundle.claims)} (Refused: {rob_refused})")
    print(f"  -> Latency: {dt_rob:.2f} ms")

    all_passed = (len(telem_retro.candidate_bundle.claims) > 0) and vak_refused and rob_refused
    total_dt = (time.perf_counter() - t_start) * 1000.0

    report = {
        "campaign_id": "UQ-N3.1-FALSIFICATION-v1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": commit_sha,
        "axiom": "DISCOVERED PATH != ACCEPTED LINEAGE",
        "verdict": "QUALIFIED_PASS" if all_passed else "FAILED",
        "metrics": {
            "retrospective_synthesis_confirmed": len(telem_retro.candidate_bundle.claims) > 0,
            "adversarial_false_positive_rate": 0.0 if (vak_refused and rob_refused) else 1.0,
            "negative_control_discipline": 1.0 if (vak_refused and rob_refused) else 0.0,
            "g1_shadow_mode_maintained": telem_retro.geometric_observation.shadow_mode,
            "total_duration_ms": round(total_dt, 2),
            "peak_rss_mb": round(max(telem_retro.worker_rss_mb, telem_vak.worker_rss_mb, telem_rob.worker_rss_mb), 2)
        },
        "probes": [
            {
                "probe": "CHETAEV_RETROSPECTIVE_SYNTHESIS",
                "uow_id": telem_retro.uow_id,
                "claims": [c.claim_id for c in telem_retro.candidate_bundle.claims],
                "sources": [s.source_id for s in telem_retro.candidate_bundle.sources],
                "duration_ms": round(dt_retro, 2),
                "rss_mb": round(telem_retro.worker_rss_mb, 2)
            },
            {
                "probe": "VAKONOMIC_PHYSICAL_INEQUIVALENCE",
                "uow_id": telem_vak.uow_id,
                "refused": vak_refused,
                "claims_count": len(telem_vak.candidate_bundle.claims),
                "duration_ms": round(dt_vak, 2)
            },
            {
                "probe": "ROBOTICS_ANACHRONISM_PRIORITY",
                "uow_id": telem_rob.uow_id,
                "refused": rob_refused,
                "claims_count": len(telem_rob.candidate_bundle.claims),
                "duration_ms": round(dt_rob, 2)
            }
        ]
    }

    out_dir = REPO_ROOT / "evidence" / "n5"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "UQ_N3_1_QUALIFICATION_REPORT.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print(f"[RESULT] Campaign UQ-N3.1 Verdict: {report['verdict']}")
    print(f"[REPORT] Saved to: {out_path}")
    print("=" * 80)
    return report

if __name__ == "__main__":
    run_campaign()
