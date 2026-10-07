"""Depth Control: Distinguishes observation radius deficiency from ontology deficiency.

If Sigma_4(X) == Sigma_4(Y) but Sigma_{4+m}(X) != Sigma_{4+m}(Y) for m in {1, 2},
the collision is labeled DEPTH, not a missing coordinate.
"""

from typing import Dict, List, Any, Tuple

def evaluate_depth_resolution(
    collisions_k4: List[Dict[str, Any]],
    max_k: int = 6
) -> Dict[str, Any]:
    """
    Evaluates collision resolution when neighborhood radius is expanded to k=5, 6.
    
    Each item in collisions_k4 represents a colliding pair/cluster (X, Y) where
    Sigma_4(X) == Sigma_4(Y) despite X !~ Y.
    """
    resolved_by_k: Dict[int, List[Dict[str, Any]]] = {5: [], 6: []}
    unresolved_at_max_k: List[Dict[str, Any]] = []

    for item in collisions_k4:
        # Check if distinguished at k=5 or k=6
        resolution_depth = item.get("resolution_depth")
        if resolution_depth == 5:
            resolved_by_k[5].append(item)
        elif resolution_depth == 6:
            resolved_by_k[6].append(item)
        else:
            unresolved_at_max_k.append(item)

    total_collisions = len(collisions_k4)
    total_depth_resolved = len(resolved_by_k[5]) + len(resolved_by_k[6])

    return {
        "total_k4_collisions": total_collisions,
        "resolved_at_k5": len(resolved_by_k[5]),
        "resolved_at_k6": len(resolved_by_k[6]),
        "total_resolved_by_depth": total_depth_resolved,
        "depth_resolution_rate": total_depth_resolved / total_collisions if total_collisions > 0 else 0.0,
        "remaining_persistent_collisions": len(unresolved_at_max_k),
        "persistent_collision_rate": len(unresolved_at_max_k) / total_collisions if total_collisions > 0 else 0.0,
        "persistent_clusters": unresolved_at_max_k
    }
