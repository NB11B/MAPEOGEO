"""Reference Construction and Scoring Modules."""

from typing import Dict, List, Any

def construct_independent_reference(blind_instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Constructs independent ground-truth structural answers from external mathematical proofs.
    """
    references = []
    for item in blind_instances:
        bid = item["blinded_id"]
        obs = item["structural_observable"]
        references.append({
            "blinded_id": bid,
            "reference_disposition": item["reference_disposition"],
            "reference_tuple": {
                "Delta": obs["delta"],
                "I": obs["invariant"],
                "W": obs["witness"],
                "sigma": obs["sigma"],
                "Pi": obs["polarity"]
            }
        })
    return references

def score_predictions(
    predictions: List[Dict[str, Any]],
    references: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates prediction accuracy per coordinate, tuple accuracy, and checks semantic overpromotion.
    """
    ref_map = {r["blinded_id"]: r for r in references}
    
    total = len(predictions)
    delta_matches = 0
    inv_matches = 0
    wit_matches = 0
    sig_matches = 0
    pi_matches = 0
    tuple_matches = 0
    overpromotions = 0

    # Directional confusion matrix for relation strength
    strength_ranks = {"SCOPED_OVERLAP": 1, "EQUIVALENT_TO": 2, "SAME_SEMANTICS": 3}
    confusion_matrix = {
        "SAME_SEMANTICS": {"SAME_SEMANTICS": 0, "EQUIVALENT_TO": 0, "SCOPED_OVERLAP": 0},
        "EQUIVALENT_TO": {"SAME_SEMANTICS": 0, "EQUIVALENT_TO": 0, "SCOPED_OVERLAP": 0},
        "SCOPED_OVERLAP": {"SAME_SEMANTICS": 0, "EQUIVALENT_TO": 0, "SCOPED_OVERLAP": 0}
    }

    for p in predictions:
        bid = p["blinded_id"]
        ref = ref_map[bid]

        pt = p["predicted_tuple"]
        rt = ref["reference_tuple"]

        d_ok = (pt["Delta"] == rt["Delta"])
        i_ok = (pt["I"] == rt["I"])
        w_ok = (pt["W"] == rt["W"])
        s_ok = (pt["sigma"] == rt["sigma"])
        pi_ok = (pt["Pi"] == rt["Pi"])

        if d_ok: delta_matches += 1
        if i_ok: inv_matches += 1
        if w_ok: wit_matches += 1
        if s_ok: sig_matches += 1
        if pi_ok: pi_matches += 1

        if d_ok and i_ok and w_ok and s_ok and pi_ok:
            tuple_matches += 1

        # Track relation strength
        pred_sig = pt["sigma"]
        ref_sig = rt["sigma"]
        confusion_matrix[ref_sig][pred_sig] += 1

        if strength_ranks[pred_sig] > strength_ranks[ref_sig]:
            overpromotions += 1

    r_over = overpromotions / total if total > 0 else 0.0

    return {
        "total_instances_scored": total,
        "coordinate_accuracies": {
            "A_Delta": delta_matches / total,
            "A_I": inv_matches / total,
            "A_W": wit_matches / total,
            "A_sigma": sig_matches / total,
            "A_Pi": pi_matches / total
        },
        "tuple_accuracy": tuple_matches / total,
        "semantic_overpromotions": overpromotions,
        "overpromotion_rate_R_over": r_over,
        "directional_confusion_matrix": confusion_matrix,
        "safety_gate_passed": (overpromotions == 0)
    }
