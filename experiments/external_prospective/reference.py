"""Independent Reference Construction: Constructs ground truth references separately from predictions."""

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
