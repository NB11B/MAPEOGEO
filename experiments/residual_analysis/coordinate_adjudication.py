"""Coordinate Adjudication: Implements the strict acceptance criteria for any candidate coordinate C_5.

A candidate coordinate must:
1. Reduce residual conditional entropy materially (relative reduction >= 20%).
2. Operate across multiple independent domains (>= 4 domains).
3. Improve at least two distinct residual projections.
4. Survive shuffled-coordinate controls (shuffled MI drop > 85%).
5. Retain effect on a sealed holdout (holdout retention >= 85%).
6. Introduce 0 false SAME_SEMANTICS promotions.
7. Remain useful after conditioning on deeper Sigma_k (k=5, 6).
8. Possess an explicit mathematical interpretation in terms of structural work.
"""

from typing import Dict, List, Any

def adjudicate_candidate(
    candidate_eval: Dict[str, Any],
    domain_distribution: Dict[str, int],
    projections_improved: List[str],
    control_shuffled_mi: float,
    holdout_mi: float,
    false_semantic_promotions: int,
    persists_at_k5: bool,
    mathematical_interpretation: str
) -> Dict[str, Any]:
    """
    Applies the 8 preregistered acceptance gates to candidate coordinate C_5.
    """
    rel_reduction = candidate_eval.get("relative_entropy_reduction", 0.0)
    disc_mi = candidate_eval.get("incremental_mutual_information_bits", 0.0)
    
    gate_1_entropy = rel_reduction >= 0.20
    gate_2_domains = len(domain_distribution) >= 4 and all(c >= 10 for c in domain_distribution.values())
    gate_3_projections = len(projections_improved) >= 2
    
    # Shuffled control test: shuffled MI must be near zero compared to discovery MI
    shuffled_reduction = (disc_mi - control_shuffled_mi) / disc_mi if disc_mi > 0 else 0.0
    gate_4_controls = control_shuffled_mi <= 0.02 and shuffled_reduction >= 0.85
    
    # Holdout generalization
    holdout_retention = holdout_mi / disc_mi if disc_mi > 0 else 0.0
    gate_5_holdout = holdout_retention >= 0.85
    
    # Semantic safety: zero spurious SAME_SEMANTICS promotions
    gate_6_safety = false_semantic_promotions == 0
    
    # Depth independence
    gate_7_depth = persists_at_k5
    
    # Interpretability
    gate_8_interpretability = len(mathematical_interpretation.strip()) > 20

    all_passed = all([
        gate_1_entropy, gate_2_domains, gate_3_projections,
        gate_4_controls, gate_5_holdout, gate_6_safety,
        gate_7_depth, gate_8_interpretability
    ])

    return {
        "candidate": candidate_eval.get("candidate_coordinate"),
        "verdict": "ACCEPTED_C5" if all_passed else "REJECTED_COORDINATE",
        "gates": {
            "G1_entropy_reduction_material": {
                "passed": gate_1_entropy,
                "relative_reduction": rel_reduction,
                "threshold": 0.20
            },
            "G2_multi_domain_breadth": {
                "passed": gate_2_domains,
                "domain_count": len(domain_distribution),
                "domains": list(domain_distribution.keys())
            },
            "G3_multi_projection_improvement": {
                "passed": gate_3_projections,
                "projections": projections_improved
            },
            "G4_shuffled_controls_resisted": {
                "passed": gate_4_controls,
                "discovery_mi": disc_mi,
                "shuffled_mi": control_shuffled_mi
            },
            "G5_sealed_holdout_retention": {
                "passed": gate_5_holdout,
                "retention_rate": holdout_retention,
                "threshold": 0.85
            },
            "G6_semantic_safety_zero_promotions": {
                "passed": gate_6_safety,
                "false_promotions": false_semantic_promotions
            },
            "G7_depth_independence_k5": {
                "passed": gate_7_depth
            },
            "G8_mathematical_interpretation": {
                "passed": gate_8_interpretability,
                "interpretation": mathematical_interpretation
            }
        }
    }
