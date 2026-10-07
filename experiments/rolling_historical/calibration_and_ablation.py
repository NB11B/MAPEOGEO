r"""Rank Calibration, Information Retrieval Metrics, and Historical Ablation Module.

Eliminates ceiling effects and verifies ranking quality:
1. Calibration Bins: S in [0, 0.1), [0.1, 0.2), ..., [0.9, 1.0]
2. Ranking Metrics: Precision@k, Recall@k, NDCG, MRR
3. Historical Ablations:
   - S_full
   - S_{-paths}
   - S_{-support}
   - S_{-witness}
   - S_{-\proximity}
   - S_{-convergence}
"""

import math
from typing import Dict, List, Any

def compute_ndcg_at_k(ranked_items: List[Dict[str, Any]], k: int) -> float:
    """Computes Normalized Discounted Cumulative Gain at k."""
    dcg = 0.0
    for i, item in enumerate(ranked_items[:k]):
        rel = 1.0 if item.get("is_occupied", False) else 0.0
        dcg += rel / math.log2(i + 2)

    # Ideal DCG
    total_relevant = sum(1 for item in ranked_items if item.get("is_occupied", False))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(k, total_relevant)))
    if idcg == 0.0:
        return 0.0
    return round(dcg / idcg, 4)

def compute_calibration_bins(
    all_scored_candidates: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Partitions candidates into score deciles [0.0, 0.1), ..., [0.9, 1.0] to test probability calibration."""
    bin_edges = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    bins = {}

    for i in range(len(bin_edges) - 1):
        low = bin_edges[i]
        high = bin_edges[i+1]
        label = f"[{low:.1f}, {min(high, 1.0):.1f})"
        cohort = [c for c in all_scored_candidates if low <= c.get("prediction_score_S", 0.0) < high]
        n = len(cohort)
        y = sum(1 for c in cohort if c.get("is_occupied", False))
        rate = round(y / n, 4) if n > 0 else 0.0
        bins[label] = {
            "n_candidates": n,
            "y_occupied": y,
            "observed_occupation_rate": rate,
            "expected_midpoint": round((low + min(high, 1.0)) / 2.0, 2)
        }

    return bins

def check_calibration_monotonicity(calibration_bins: Dict[str, Dict[str, Any]]) -> bool:
    """Checks whether occupation rates increase monotonically with higher score brackets."""
    active_bins = [b for b in calibration_bins.values() if b["n_candidates"] > 0]
    if len(active_bins) < 2:
        return True
    
    # Verify higher score bins have >= occupation rate than lower score bins
    rates = [b["observed_occupation_rate"] for b in active_bins]
    # Allow small noise margin 0.05
    violations = sum(1 for i in range(len(rates) - 1) if rates[i+1] < rates[i] - 0.05)
    return violations == 0

def run_score_ablations(
    candidates: List[Dict[str, Any]],
    discoveries: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Ablates each scoring component to determine which carries discovery predictive signal:

    - full: S_full
    - minus_paths: S_{-paths}
    - minus_support: S_{-support}
    - minus_witness: S_{-witness}
    - minus_proximity: S_{-proximity}
    - minus_convergence: S_{-convergence}
    """
    ablation_modes = [
        "full",
        "minus_paths",
        "minus_support",
        "minus_witness",
        "minus_proximity",
        "minus_convergence"
    ]

    ablation_results = {}

    for mode in ablation_modes:
        rescored = []
        for c in candidates:
            # Component values
            p_val = c.get("component_paths", 0.8)
            s_val = c.get("component_support", 0.8)
            w_val = c.get("component_witness", 0.8)
            x_val = c.get("component_proximity", 0.8)
            c_val = min(1.0, c.get("convergence_count", 1) / 3.0)

            if mode == "full":
                score = 0.25*p_val + 0.25*s_val + 0.15*w_val + 0.15*x_val + 0.20*c_val
            elif mode == "minus_paths":
                score = (0.25*s_val + 0.15*w_val + 0.15*x_val + 0.20*c_val) / 0.75
            elif mode == "minus_support":
                score = (0.25*p_val + 0.15*w_val + 0.15*x_val + 0.20*c_val) / 0.75
            elif mode == "minus_witness":
                score = (0.25*p_val + 0.25*s_val + 0.15*x_val + 0.20*c_val) / 0.85
            elif mode == "minus_proximity":
                score = (0.25*p_val + 0.25*s_val + 0.15*w_val + 0.20*c_val) / 0.85
            elif mode == "minus_convergence":
                score = (0.25*p_val + 0.25*s_val + 0.15*w_val + 0.15*x_val) / 0.80

            copy_c = dict(c)
            copy_c["ablation_score"] = round(score, 4)
            rescored.append(copy_c)

        rescored.sort(key=lambda x: x["ablation_score"], reverse=True)

        # Compute precision@top1, NDCG@5, and MRR under this ablation
        top1 = rescored[0] if rescored else {}
        p_at_1 = 1.0 if top1.get("is_occupied", False) else 0.0
        ndcg_5 = compute_ndcg_at_k(rescored, 5)

        first_hit_rank = next((idx + 1 for idx, x in enumerate(rescored) if x.get("is_occupied", False)), len(rescored))
        mrr = round(1.0 / first_hit_rank, 4) if first_hit_rank > 0 else 0.0

        ablation_results[mode] = {
            "precision_at_1": p_at_1,
            "ndcg_at_5": ndcg_5,
            "mrr": mrr
        }

    return ablation_results
