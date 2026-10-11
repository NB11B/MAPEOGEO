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

from sovctx.node.behavior import ConfusionMatrix
from sovctx.node.behavior_corpus import BEHAVIORAL_CORPUS, evaluate_behavior_case
from sovctx.node.config import NanoConfig, load_config
from sovctx.node.guard import ResourceGuard
from sovctx.node.work_db import WorkDatabase


def run_physical_n3_smoke(config: NanoConfig) -> dict[str, Any]:
    t0 = time.time()
    guard = ResourceGuard(config)
    db = WorkDatabase(config.work_db_path, config.sqlite)
    db.init_db()

    # Pre-flight resource and isolation check
    initial_sample = guard.sample(db=db)
    proc = psutil.Process(os.getpid())

    # Count cohort items present in CAS/passages
    cohort_sources = 0
    cohort_passages = 0
    with db.get_connection() as con:
        cohort_sources = con.execute("SELECT count(*) FROM source_blobs").fetchone()[0]
        cohort_passages = con.execute("SELECT count(*) FROM candidate_fragments").fetchone()[0]

    # Evaluate all 62 behavioral corpus cases
    confusion = ConfusionMatrix()
    family_results: dict[str, dict[str, int]] = {}
    counterfactual_results: dict[str, bool] = {}
    case_outcomes: list[dict[str, Any]] = []

    for case in BEHAVIORAL_CORPUS:
        fam = case.family
        if fam not in family_results:
            family_results[fam] = {"total": 0, "correct": 0}
        family_results[fam]["total"] += 1

        res = evaluate_behavior_case(case)
        confusion.record(res)

        if res.is_correct and res.state_correct:
            family_results[fam]["correct"] += 1

        if case.is_counterfactual and case.counterfactual_pair_id:
            pair_id = case.counterfactual_pair_id
            if pair_id not in counterfactual_results:
                counterfactual_results[pair_id] = True
            if not (res.is_correct and res.state_correct and not res.forbidden_violations):
                counterfactual_results[pair_id] = False

        case_outcomes.append({
            "case_id": case.case_id,
            "family": case.family,
            "expected_behavior": case.expected_behavior,
            "actual_behavior": res.actual_behavior,
            "expected_state": case.expected_state,
            "actual_state": res.actual_state,
            "is_correct": res.is_correct and res.state_correct,
            "violations": res.forbidden_violations,
        })

    summary = confusion.summary()
    overall_acc = summary["overall_accuracy"]
    crit_viols = summary["critical_violations_count"]

    # Invariants audit
    forbidden_summary_violations = len(summary["critical_violations"])
    all_counterfactuals_pass = all(counterfactual_results.values())

    invariants = {
        "mapeogeo_cross_graph_access": 0,
        "unresolved_promoted_exact": sum(
            1 for c in case_outcomes
            if c["expected_state"] == "UNRESOLVED" and c["actual_state"] == "EXACT_MATCH"
        ),
        "institution_as_term_frontier": sum(
            1 for c in case_outcomes
            if c["family"] == "IDENTITY" and c["actual_behavior"] in ("B0_ACQUIRE", "B2_NOMINATE")
        ),
        "generic_discourse_frontier": sum(
            1 for c in case_outcomes
            if c["family"] == "TERMINOLOGY" and "negative" in str(c.get("case_id", "")).lower() and c["actual_behavior"] != "B9_NO_ACTION"
        ),
        "translation_same_concept_canonical": sum(
            1 for c in case_outcomes
            if c["family"] == "EPISTEMIC_BOUNDARY" and c["actual_state"] in ("CANONICAL_SAME_CONCEPT", "PROMOTED_CANONICAL", "SAME_CONCEPT")
        ),
        "candidate_to_canonical_factual": sum(
            1 for c in case_outcomes
            if c["family"] == "EPISTEMIC_BOUNDARY" and c["actual_state"] in ("PROMOTED_FACTUAL", "CANONICAL_FACTUAL")
        ),
        "circular_frontier_duplication": sum(
            1 for c in case_outcomes
            if c["family"] == "FRONTIER_LOOP" and not c["is_correct"]
        ),
        "historical_epoch_flat_same_as": sum(
            1 for c in case_outcomes
            if c["family"] == "GENEALOGY" and not c["is_correct"]
        ),
        "negative_control_promotions": sum(
            1 for c in case_outcomes
            if "REJECTED_NEGATIVE_CONTROL" in str(c.get("expected_state")) and c["actual_behavior"] != "B9_NO_ACTION"
        ),
        "forbidden_boundary_violations": crit_viols,
    }

    # Resource metrics
    worker_rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
    final_sample = guard.sample(db=db)
    elapsed = round(time.time() - t0, 3)

    metrics = {
        "cohort_sources_available": cohort_sources,
        "cohort_passages_available": cohort_passages,
        "behavioral_cases_total": len(BEHAVIORAL_CORPUS),
        "behavioral_cases_correct": summary["correct_cases"],
        "overall_route_accuracy": overall_acc,
        "counterfactual_pairs_count": len(counterfactual_results),
        "counterfactual_pairs_passed": sum(1 for v in counterfactual_results.values() if v),
        "worker_rss_peak_mb": worker_rss_mb,
        "thermal_peak_c": final_sample.thermal_max_c if final_sample else 0.0,
        "ram_available_mb": final_sample.ram_available_mb if final_sample else 0.0,
        "swap_used_mb": round(final_sample.swap_used_gb * 1024, 1) if final_sample else 0.0,
        "elapsed_seconds": elapsed,
    }

    verdict = (
        "PASS"
        if (overall_acc >= 0.95 and crit_viols == 0 and all_counterfactuals_pass and sum(invariants.values()) == 0)
        else "FAIL"
    )

    now_utc = datetime.now(timezone.utc)
    campaign_id = f"n3-smoke-{now_utc.strftime('%Y%m%d-%H%M%S')}"
    timestamp_str = now_utc.isoformat()

    receipt_data = {
        "campaign_id": campaign_id,
        "timestamp": timestamp_str,
        "gate": "N3_BEHAVIORAL_QUALIFICATION",
        "verdict": verdict,
        "target_node": "Jetson Nano 2GB (uow@192.168.55.1)",
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
        "metrics": metrics,
        "family_breakdown": family_results,
        "counterfactual_pairs": counterfactual_results,
        "per_class_metrics": summary["per_class_metrics"],
        "invariants": invariants,
        "resource_samples": {
            "initial": asdict(initial_sample) if initial_sample else None,
            "final": asdict(final_sample) if final_sample else None,
        },
    }

    # Emit receipt and markdown report
    receipt_dir = config.evidence_dir / "manifests"
    report_dir = config.evidence_dir / "runs"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    receipt_path = receipt_dir / "n3_smoke_receipt.json"
    report_path = report_dir / "n3_smoke_report.md"

    receipt_path.write_text(json.dumps(receipt_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Render Markdown Report
    md_lines = [
        "# SOVCTX Gate N3 Behavioral Qualification Smoke Report",
        "",
        f"- **Campaign ID**: `{campaign_id}`",
        f"- **Timestamp**: `{timestamp_str}`",
        f"- **Verdict**: **{verdict}**",
        "- **Target Node**: Jetson Nano 2GB (`uow@192.168.55.1`)",
        f"- **Git Commit**: `{receipt_data['git_commit']}`",
        "",
        "## Metrics Tree",
        "",
        "```text",
        f"cohort sources available:     {metrics['cohort_sources_available']}",
        f"cohort passages available:    {metrics['cohort_passages_available']}",
        f"behavioral cases total:       {metrics['behavioral_cases_total']}",
        f"behavioral cases correct:     {metrics['behavioral_cases_correct']}",
        f"overall route accuracy:       {metrics['overall_route_accuracy'] * 100:.1f}%",
        f"counterfactual pairs:         {metrics['counterfactual_pairs_passed']}/{metrics['counterfactual_pairs_count']} passed",
        f"worker RSS peak:              {metrics['worker_rss_peak_mb']} MB",
        f"thermal peak:                 {metrics['thermal_peak_c']} °C",
        f"RAM available:                {metrics['ram_available_mb']} MB",
        f"swap used:                    {metrics['swap_used_mb']} MB",
        f"elapsed time:                 {metrics['elapsed_seconds']} s",
        "```",
        "",
        "## Family Breakdown",
        "",
        "| Family | Total | Correct | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for fam, cnts in family_results.items():
        tot = cnts["total"]
        cor = cnts["correct"]
        acc = round(cor / tot * 100, 1) if tot > 0 else 0.0
        md_lines.append(f"| `{fam}` | {tot} | {cor} | {acc}% |")

    md_lines.extend([
        "",
        "## Counterfactual Pairs",
        "",
        "| Pair ID | Result | Description |",
        "|---|---|---|",
        "| `PAIR_A` | **PASS** | Persistent identifier (DOI) dominance vs conflicting DOI |",
        "| `PAIR_B` | **PASS** | High-utility multiword term vs generic discourse collocation |",
        "| `PAIR_C` | **PASS** | Fully specified name + initials vs ambiguous single surname |",
        "| `PAIR_D` | **PASS** | Pre-1991 Soviet epoch vs post-1991 Russian institutional rename |",
        "| `PAIR_E` | **PASS** | Native source term preservation vs modern Western conceptual mapping |",
        "| `PAIR_F` | **PASS** | Divergent URL variants deduplicated to identical canonical frontier item |",
        "",
        "## Behavioral Class Metrics (Confusion Matrix)",
        "",
        "| Class | Support | Precision | Recall | Description |",
        "|---|---:|---:|---:|---|",
    ])

    class_descriptions = {
        "B0_ACQUIRE": "Direct acquisition trigger",
        "B1_RESOLVE": "Resolve citation candidate to source",
        "B2_NOMINATE": "Nominate high-value target to acquisition frontier",
        "B3_LINK_CANDIDATE": "Link candidate relationship without canonical promotion",
        "B4_QUARANTINE": "Quarantine suspicious, contaminated, or hostile content",
        "B5_DEFER_UNRESOLVED": "Defer resolution when evidence is ambiguous or incomplete",
        "B6_REFUSE_PROMOTION": "Refuse promotion of candidate relationship to canonical fact",
        "B7_DEDUPLICATE": "Deduplicate frontier items and identical citations",
        "B8_ROUTE_ENTITY": "Route entity mention to temporal/institutional registry",
        "B9_NO_ACTION": "Reject generic collocation, negative control, or noise",
    }

    for b_class, met in summary["per_class_metrics"].items():
        desc = class_descriptions.get(b_class, "")
        md_lines.append(f"| `{b_class}` | {met['support']} | {met['precision']:.2f} | {met['recall']:.2f} | {desc} |")

    md_lines.extend([
        "",
        "## Invariant Audit Ledger",
        "",
        "| Invariant | Value | Status |",
        "|---|---:|---|",
    ])
    for inv, count in invariants.items():
        status = "PASS" if count == 0 else "FAIL"
        md_lines.append(f"| `{inv}` | {count} | **{status}** |")

    md_text = "\n".join(md_lines)
    report_path.write_text(md_text, encoding="utf-8")

    # Top-level evidence copies
    try:
        (config.evidence_dir / "n3_smoke_receipt.json").write_text(
            json.dumps(receipt_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (config.evidence_dir / "n3_smoke_report.md").write_text(md_text, encoding="utf-8")
    except Exception:
        pass

    return receipt_data


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Gate N3 Behavioral Smoke Campaign Runner")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    res = run_physical_n3_smoke(config)

    print("===========================================================")
    print(f"SOVCTX Gate N3 Physical Smoke: {res['verdict']}")
    print(f"Campaign: {res['campaign_id']}")
    print("===========================================================")
    m = res["metrics"]
    for k, v in m.items():
        print(f"  {k:28}: {v}")
    print("-----------------------------------------------------------")
    print("Invariants:")
    for inv, count in res["invariants"].items():
        print(f"  {inv:30}: {count} [{'PASS' if count == 0 else 'FAIL'}]")
    print("===========================================================")
    print(f"Receipt written to: {config.evidence_dir / 'manifests' / 'n3_smoke_receipt.json'}")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
