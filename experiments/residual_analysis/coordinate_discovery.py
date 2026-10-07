"""Coordinate Discovery: Information-theoretic search for missing structural coordinates.

Tests whether candidate structural dimensions C_j satisfy:
I(C_j; R | Delta, I, W, sigma, Sigma_k) > 0
and provide genuine conditional entropy reduction across residual errors.
"""

import math
from typing import Dict, List, Any, Tuple

def compute_entropy(labels: List[Any]) -> float:
    """Calculates Shannon entropy H(Y) in bits."""
    if not labels:
        return 0.0
    total = len(labels)
    counts: Dict[Any, int] = {}
    for y in labels:
        counts[y] = counts.get(y, 0) + 1
    
    ent = 0.0
    for cnt in counts.values():
        p = cnt / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent

def compute_conditional_entropy(target_labels: List[Any], condition_keys: List[Tuple]) -> float:
    """Calculates H(Y | X) in bits."""
    if not target_labels or len(target_labels) != len(condition_keys):
        return 0.0
    
    total = len(target_labels)
    groups: Dict[Tuple, List[Any]] = {}
    for y, x in zip(target_labels, condition_keys):
        groups.setdefault(x, []).append(y)
        
    cond_ent = 0.0
    for x, y_list in groups.items():
        p_x = len(y_list) / total
        cond_ent += p_x * compute_entropy(y_list)
        
    return cond_ent

def evaluate_candidate_coordinate(
    residuals: List[Dict[str, Any]],
    candidate_name: str,
    target_error_key: str = "error_class"
) -> Dict[str, Any]:
    """
    Evaluates whether candidate_name provides incremental information
    I(C_j; R | Delta, I, W, sigma) = H(R | Delta, I, W, sigma) - H(R | Delta, I, W, sigma, C_j).
    """
    target_labels = [r[target_error_key] for r in residuals]
    base_conditions = [
        (r.get("delta", ""), r.get("invariant", ""), r.get("witness", ""), r.get("sigma", ""))
        for r in residuals
    ]
    augmented_conditions = [
        (r.get("delta", ""), r.get("invariant", ""), r.get("witness", ""), r.get("sigma", ""), r.get(candidate_name, ""))
        for r in residuals
    ]

    h_r_given_base = compute_conditional_entropy(target_labels, base_conditions)
    h_r_given_augmented = compute_conditional_entropy(target_labels, augmented_conditions)
    mutual_info = max(0.0, h_r_given_base - h_r_given_augmented)
    relative_reduction = (mutual_info / h_r_given_base) if h_r_given_base > 0 else 0.0

    return {
        "candidate_coordinate": candidate_name,
        "h_residual_given_frozen": h_r_given_base,
        "h_residual_given_frozen_plus_candidate": h_r_given_augmented,
        "incremental_mutual_information_bits": mutual_info,
        "relative_entropy_reduction": relative_reduction,
        "is_informative": mutual_info > 0.05
    }
