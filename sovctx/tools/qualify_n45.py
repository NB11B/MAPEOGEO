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
from sovctx.node.synthesis import HistoricalSynthesisEngine
from sovctx.node.work_db import WorkDatabase


def run_n45_qualification() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "qualify_n45.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()

        engine = HistoricalSynthesisEngine(config=config, db=db)
        res = engine.run_synthesis()

        m = res["metrics"]
        inv = res["invariants"]

        thresholds = {
            "all_8_schools_synthesized": m["dossiers_synthesized"] == 8,
            "independence_ratio_met": m["independence_ratio"] >= 0.10,
            "temporal_consistency_met": m["temporal_consistency_rate"] == 1.0,
            "direct_evidence_separated": m["direct_evidence_ratio"] >= 0.50,
            "contradictions_cataloged": m["contradictions_cataloged"] >= 4,
            "contradiction_coverage_full": m["contradiction_coverage"] == 1.0,
            "provenance_completeness_full": m["provenance_completeness"] == 1.0,
            "canonical_promotion_zero": inv["canonical_promotion_violations"] == 0,
            "temporal_impossibilities_zero": inv["temporal_impossibilities"] == 0,
            "mapeogeo_access_zero": inv["mapeogeo_cross_graph_access"] == 0,
            "mirror_inflation_zero": inv["mirror_inflation_violations"] == 0,
            "all_10_questions_answered": all(
                len(d.get("dossier_answers", {})) == 10 for d in res["dossiers"]
            ),
            "lineages_extracted": m["lineages_extracted"] >= 10,
        }

        verdict = "PASS" if all(thresholds.values()) else "FAIL"

        return {
            "verdict": verdict,
            "campaign_id": res["campaign_id"],
            "timestamp": res["timestamp"],
            "metrics": m,
            "thresholds": thresholds,
            "dossiers_count": len(res["dossiers"]),
            "lineages_count": len(res["lineages"]),
            "contradictions_count": len(res["contradictions"]),
            "invariants": inv,
        }


def main() -> int:
    print("===========================================================")
    print("SOVCTX Gate N4.5 Epistemic Synthesis Qualification")
    print("===========================================================")
    res = run_n45_qualification()

    print("\n--- Synthesis Metrics ---")
    m = res["metrics"]
    for k, v in m.items():
        if isinstance(v, float):
            print(f"  {k:30}: {v * 100:.1f}%" if v <= 1.0 else f"  {k:30}: {v:.2f}")
        else:
            print(f"  {k:30}: {v}")

    print("\n--- Invariants Ledger ---")
    for inv, count in res["invariants"].items():
        if inv == "provenance_completeness_met":
            st = "PASS" if count == 1 else "FAIL"
        else:
            st = "PASS" if count == 0 else "FAIL"
        print(f"  {inv:35}: {count} [{st}]")

    print("\n--- Thresholds Checklist ---")
    for t_name, passed in res["thresholds"].items():
        print(f"  {t_name:35}: {'PASS' if passed else 'FAIL'}")

    print("===========================================================")
    print(f"Gate N4.5 Synthesis Verdict : {res['verdict']}")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
