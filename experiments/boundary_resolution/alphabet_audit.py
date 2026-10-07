"""Alphabet Audit: Distinguishes missing coordinate dimensions (C_6) from missing values
within existing coordinates (ALPHABET refinement).

For example, enriching W with 'unit_counit_adjunction' or 'nuclear_trace_witness'
resolves work deficiencies without adding a new dimension to M5.
"""

from typing import Dict, List, Any

def audit_alphabet_expansion(
    deficiency_clusters: Dict[str, Any],
    frozen_m5_spec: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Identifies candidates for coordinate value expansion.
    """
    refinements = []

    for cid, cluster in deficiency_clusters.items():
        res_type = cluster["candidate_resolution_type"]
        work = cluster["missing_work"]

        if res_type == "ALPHABET_WITNESS":
            new_value = f"{work}_certificate"
            refinements.append({
                "cluster_id": cid,
                "target_coordinate": "W",
                "proposed_new_value": new_value,
                "affected_instances_count": cluster["total_count"],
                "status": "RESOLVED_COORDINATE_VALUE",
                "rationale": f"Extends witness alphabet W with {new_value} rather than manufacturing C_6."
            })

    return {
        "total_alphabet_refinements": len(refinements),
        "refinements": refinements
    }
