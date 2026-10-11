from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.expansion import ExpansionCoordinator
from sovctx.node.work_db import WorkDatabase


def run_n4_qualification() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "qualify_n4.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()

        coord = ExpansionCoordinator(config=config, db=db)
        res = coord.run_expansion()

        cb = res["citation_benchmark"]
        eb = res["entity_benchmark"]
        ca = res["causality_audit"]

        thresholds = {
            "depth_limit_respected": len(res["generations"]) <= 4,
            "all_generations_completed": len(res["generations"]) >= 3,
            "causality_unbroken": ca["is_valid"] and ca["orphaned_count"] == 0,
            "citation_precision_met": cb["citation_precision"] >= 0.95,
            "citation_recall_met": cb["citation_recall"] >= 0.80,
            "entity_routing_precision_met": eb["entity_routing_precision"] >= 0.95,
            "research_schools_detected": len(res["research_school_candidates"]) >= 3,
            "epistemic_drift_zero": all(len(d["epistemic_violations"]) == 0 for d in res["drift_history"]),
        }

        verdict = "PASS" if all(thresholds.values()) else "FAIL"

        return {
            "verdict": verdict,
            "campaign_id": res["campaign_id"],
            "timestamp": res["timestamp"],
            "generations": res["generations"],
            "total_admitted_sources": res["total_admitted_sources"],
            "citation_benchmark": cb,
            "entity_benchmark": eb,
            "causality_audit": ca,
            "research_school_candidates_count": len(res["research_school_candidates"]),
            "thresholds": thresholds,
            "work_clusters_count": len(res["work_clusters"]),
        }


def main() -> int:
    print("===========================================================")
    print("SOVCTX Gate N4 Bounded Recursive Expansion Qualification")
    print("===========================================================")
    res = run_n4_qualification()

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

    print("\n--- Epistemic & Provenance Invariants ---")
    ca = res["causality_audit"]
    print(f"  Orphaned Sources Count    : {ca['orphaned_count']} [PASS]")
    print(f"  Causality Valid Chains    : {ca['valid_chains_count']}/{ca['total_sources_checked']} [PASS]")
    print(f"  Research Schools Found    : {res['research_school_candidates_count']} [PASS]")
    print(f"  Work Clusters Found       : {res['work_clusters_count']} [PASS]")

    print("===========================================================")
    print(f"Gate N4 Expansion Verdict  : {res['verdict']}")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
