# SPDX-License-Identifier: MIT
"""Selection Metrics Tracker for PDI-135M-v0.3.

Computes:
- Oracle Coverage@8
- Conditional Top-1 Correctness
- End-to-End Useful Selection (Top-1 or Correct Abstention)
- Correct vs Incorrect Abstention Rate
- Invalid-Index Rate
- Latency percentiles (mean, p50, p95, p99)
- Menu-Order Sensitivity (permutation consistency)
- Breakdowns by Operation Family and Context Arm
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional


def percentile(values: List[float], p: float) -> float:
    """Compute percentile p (0..100) using nearest-rank interpolation."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return float(d0 + d1)


@dataclass
class TrialResult:
    scenario_id: str
    seed: int
    context_arm: str
    selector_name: str
    op_family: str
    selected_index: int
    selected_cand_id: Optional[str]
    is_valid_index: bool
    is_eligible: bool
    coverage_at_8: bool
    is_conditional_top1: bool
    is_acceptable_alternative: bool
    is_abstain: bool
    is_correct_abstention: bool
    is_useful_selection: bool
    candidate_gen_latency_ms: float
    projection_latency_ms: float
    selection_latency_ms: float
    end_to_end_latency_ms: float
    prompt_tokens: int
    generated_tokens: int


class SelectionMetricsAggregator:
    """Aggregates trial results and computes summary metrics across arms and selectors."""

    def __init__(self) -> None:
        self.trials: List[TrialResult] = []

    def record(self, trial: TrialResult) -> None:
        self.trials.append(trial)

    def summarize(self, filter_selector: Optional[str] = None, filter_arm: Optional[str] = None) -> Dict[str, Any]:
        subset = [
            t for t in self.trials
            if (filter_selector is None or t.selector_name == filter_selector)
            and (filter_arm is None or t.context_arm == filter_arm)
        ]
        total = len(subset)
        if total == 0:
            return {"total_trials": 0}

        valid_idx_cnt = sum(1 for t in subset if t.is_valid_index)
        coverage_cnt = sum(1 for t in subset if t.coverage_at_8)
        cond_top1_cnt = sum(1 for t in subset if t.is_conditional_top1)
        accept_cnt = sum(1 for t in subset if t.is_acceptable_alternative)
        correct_abs_cnt = sum(1 for t in subset if t.is_correct_abstention)
        useful_cnt = sum(1 for t in subset if t.is_useful_selection)

        gen_lats = [t.candidate_gen_latency_ms for t in subset]
        proj_lats = [t.projection_latency_ms for t in subset]
        sel_lats = [t.selection_latency_ms for t in subset]
        e2e_lats = [t.end_to_end_latency_ms for t in subset]

        prompt_toks = [t.prompt_tokens for t in subset]
        gen_toks = [t.generated_tokens for t in subset]

        # Calculate menu-order sensitivity (permutation consistency across seeds)
        # Group by (scenario_id, context_arm, selector_name)
        grouped: Dict[tuple, List[Optional[str]]] = {}
        for t in subset:
            key = (t.scenario_id, t.context_arm, t.selector_name)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(t.selected_cand_id)

        consistent_groups = 0
        total_groups = len(grouped)
        for _, cands in grouped.items():
            if len(cands) > 1 and len(set(cands)) == 1:
                consistent_groups += 1

        order_consistency_pct = (consistent_groups / max(1, total_groups)) * 100.0
        # Sensitivity is 100 - consistency
        order_sensitivity_pct = 100.0 - order_consistency_pct

        # Breakdown by op family
        families = sorted(list(set(t.op_family for t in subset)))
        by_family: Dict[str, Dict[str, float]] = {}
        for fam in families:
            fam_subset = [t for t in subset if t.op_family == fam]
            f_tot = len(fam_subset)
            f_cov = sum(1 for t in fam_subset if t.coverage_at_8)
            f_top1 = sum(1 for t in fam_subset if t.is_conditional_top1)
            f_use = sum(1 for t in fam_subset if t.is_useful_selection)
            by_family[fam] = {
                "count": f_tot,
                "coverage_pct": round((f_cov / max(1, f_tot)) * 100.0, 2),
                "conditional_top1_pct": round((f_top1 / max(1, f_cov)) * 100.0, 2),
                "useful_selection_pct": round((f_use / max(1, f_tot)) * 100.0, 2),
            }

        return {
            "total_trials": total,
            "valid_index_pct": round((valid_idx_cnt / total) * 100.0, 2),
            "coverage_at_8_pct": round((coverage_cnt / total) * 100.0, 2),
            "conditional_top1_pct": round((cond_top1_cnt / max(1, coverage_cnt)) * 100.0, 2),
            "acceptable_alternative_pct": round((accept_cnt / total) * 100.0, 2),
            "correct_abstention_pct": round((correct_abs_cnt / total) * 100.0, 2),
            "end_to_end_useful_pct": round((useful_cnt / total) * 100.0, 2),
            "order_consistency_pct": round(order_consistency_pct, 2),
            "order_sensitivity_pct": round(order_sensitivity_pct, 2),
            "tokens": {
                "mean_prompt": round(sum(prompt_toks) / max(1, total), 2),
                "mean_generated": round(sum(gen_toks) / max(1, total), 2),
            },
            "latencies_ms": {
                "candidate_gen": {
                    "mean": round(sum(gen_lats) / max(1, total), 2),
                    "p50": round(percentile(gen_lats, 50), 2),
                    "p95": round(percentile(gen_lats, 95), 2),
                    "p99": round(percentile(gen_lats, 99), 2),
                },
                "projection": {
                    "mean": round(sum(proj_lats) / max(1, total), 2),
                    "p50": round(percentile(proj_lats, 50), 2),
                    "p95": round(percentile(proj_lats, 95), 2),
                    "p99": round(percentile(proj_lats, 99), 2),
                },
                "selection": {
                    "mean": round(sum(sel_lats) / max(1, total), 2),
                    "p50": round(percentile(sel_lats, 50), 2),
                    "p95": round(percentile(sel_lats, 95), 2),
                    "p99": round(percentile(sel_lats, 99), 2),
                },
                "end_to_end": {
                    "mean": round(sum(e2e_lats) / max(1, total), 2),
                    "p50": round(percentile(e2e_lats, 50), 2),
                    "p95": round(percentile(e2e_lats, 95), 2),
                    "p99": round(percentile(e2e_lats, 99), 2),
                },
            },
            "by_op_family": by_family,
        }
