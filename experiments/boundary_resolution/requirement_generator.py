"""Requirement Generator: Emits domain-neutral mathematical acquisition specifications
from deficiency clusters.
"""

from typing import Dict, List, Any

def generate_acquisition_spec(cluster: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a domain-neutral specification of the mathematical capability required.
    """
    cid = cluster["cluster_id"]
    work = cluster["missing_work"]
    res_type = cluster["candidate_resolution_type"]

    return {
        "deficiency_id": cid,
        "missing_work_capability": work,
        "candidate_resolution_type": res_type,
        "required_operator_behavior": [
            f"must_witness_{work}_inversion",
            "must_preserve_typed_composition_associativity"
        ],
        "required_invariant_behavior": [
            "must_not_collapse_distinct_fibers"
        ],
        "required_witness_behavior": [
            f"constructive_certificate_for_{work}"
        ],
        "required_composition_behavior": [
            "composable_under_circ_with_M5_primitives"
        ],
        "prohibited_leakage": [
            "specific_theorem_names",
            "b5_object_identifiers",
            "author_lexical_signatures"
        ],
        "target_b5_screen_cohort_size": cluster["screen_set_A_count"],
        "target_b5_confirm_cohort_size": cluster["confirm_set_B_count"]
    }
