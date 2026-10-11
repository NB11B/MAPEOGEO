from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.behavior import ConfusionMatrix
from sovctx.node.behavior_corpus import BEHAVIORAL_CORPUS, evaluate_behavior_case


def run_n3_qualification() -> dict[str, Any]:
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

    # Threshold checks
    thresholds_met = (
        overall_acc >= 0.95
        and crit_viols == 0
        and all(counterfactual_results.values())
    )
    verdict = "PASS" if thresholds_met else "FAIL"

    return {
        "verdict": verdict,
        "total_cases": summary["total_cases"],
        "correct_cases": summary["correct_cases"],
        "overall_accuracy": overall_acc,
        "critical_violations_count": crit_viols,
        "critical_violations": summary["critical_violations"],
        "family_breakdown": family_results,
        "counterfactual_pairs": counterfactual_results,
        "per_class_metrics": summary["per_class_metrics"],
        "case_outcomes": case_outcomes,
    }


def main() -> int:
    print("===========================================================")
    print("SOVCTX Gate N3 Behavioral Qualification Harness")
    print("===========================================================")
    res = run_n3_qualification()

    print("\n--- Family Breakdown ---")
    for fam, counts in res["family_breakdown"].items():
        tot = counts["total"]
        cor = counts["correct"]
        acc = round(cor / tot * 100, 1) if tot > 0 else 0.0
        print(f"  {fam:22}: {cor}/{tot} ({acc}%)")

    print("\n--- Counterfactual Pairs ---")
    for pair, passed in res["counterfactual_pairs"].items():
        print(f"  {pair:15}: {'PASS' if passed else 'FAIL'}")

    print("\n--- Behavioral Class Confusion / Metrics ---")
    print(f"  {'Class':<22} | {'Support':<8} | {'Precision':<10} | {'Recall':<10}")
    print("  " + "-" * 56)
    for b_class, met in res["per_class_metrics"].items():
        p_str = f"{met['precision']:.2f}" if met['precision'] is not None else "N/A"
        r_str = f"{met['recall']:.2f}" if met['recall'] is not None else "N/A"
        print(f"  {b_class:<22} | {met['support']:<8} | {p_str:<10} | {r_str:<10}")

    print("-----------------------------------------------------------")
    print(f"Overall Route Accuracy     : {res['overall_accuracy'] * 100:.1f}% (Threshold: >= 95.0%)")
    print(f"Critical Violations Count  : {res['critical_violations_count']} (Threshold: 0)")
    print("===========================================================")
    print(f"Gate N3 Behavioral Verdict : {res['verdict']} ({res['correct_cases']}/{res['total_cases']} cases passing)")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
