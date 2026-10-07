r"""Expanded Unit of Work (UoW) Discovery State Machine and Frontier Partition Module.

Formulates the 6-stage prospective discovery state machine:
Q -> TYPE -> RELATIONAL_ADMISSIBILITY -> OBSTRUCTION -> REALIZABILITY -> CONSTRUCTION

Dispositions:
- ILL_TYPED
- INADMISSIBLE
- ADMISSIBLE_UNTESTED
- OBSTRUCTED
- CONDITIONALLY_REALIZABLE
- REALIZABLE
- CONSTRUCTED

Partitions the frontier:
U = U_{realizable} \sqcup U_{obstructed} \sqcup U_{unresolved}

Formalizes the discovery loop:
prediction -> obstruction Omega(X) -> minimal repair rho(Omega) -> construction.
"""

from typing import Dict, List, Any

DISPOSITIONS = [
    "ILL_TYPED",
    "INADMISSIBLE",
    "ADMISSIBLE_UNTESTED",
    "OBSTRUCTED",
    "CONDITIONALLY_REALIZABLE",
    "REALIZABLE",
    "CONSTRUCTED"
]

def partition_live_frontier(
    candidates_evaluations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Partitions the live mathematical frontier into realizable, obstructed, and unresolved sets."""
    u_realizable = []
    u_obstructed = []
    u_unresolved = []

    for c in candidates_evaluations:
        status = c.get("verdict", "ADMISSIBLE_UNTESTED")
        cid = c.get("candidate_id")

        if status in ["CONSTRUCTED", "CONSTRUCTED_UP_TO_EQUIVALENCE", "REALIZABLE"]:
            u_realizable.append({
                "candidate_id": cid,
                "nominal_title": c.get("nominal_title"),
                "disposition": "REALIZABLE",
                "details": c.get("details", "")
            })
        elif status in ["OBSTRUCTED", "CONDITIONALLY_REALIZABLE"]:
            u_obstructed.append({
                "candidate_id": cid,
                "nominal_title": c.get("nominal_title"),
                "disposition": "OBSTRUCTED",
                "obstruction_class": c.get("obstruction_class", "Omega != 0"),
                "minimal_repair_rho": c.get("minimal_repair", "None specified")
            })
        else:
            u_unresolved.append({
                "candidate_id": cid,
                "nominal_title": c.get("nominal_title"),
                "disposition": status
            })

    total = len(candidates_evaluations)
    return {
        "total_frontier_evaluated": total,
        "u_realizable_count": len(u_realizable),
        "u_realizable": u_realizable,
        "u_obstructed_count": len(u_obstructed),
        "u_obstructed": u_obstructed,
        "u_unresolved_count": len(u_unresolved),
        "u_unresolved": u_unresolved,
        "true_construction_frontier": [u["candidate_id"] for u in u_realizable]
    }
