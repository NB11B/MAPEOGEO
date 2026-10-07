"""Deficiency Clustering: Groups B5 deficiencies by missing mathematical work,
and partitions each cluster into screen (A) and confirm (B) holdouts.
"""

from typing import Dict, List, Any

def cluster_deficiencies(deficiencies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Partitions deficiencies into clusters D_1..D_r based on missing_work,
    with deterministic split into D_i^A (screen) and D_i^B (confirm).
    """
    clusters: Dict[str, List[Dict[str, Any]]] = {}
    for d in deficiencies:
        mw = d["missing_work"]
        clusters.setdefault(mw, []).append(d)

    structured_clusters = {}
    singletons = []

    for idx, (work_name, items) in enumerate(clusters.items()):
        if len(items) < 10:
            singletons.extend(items)
            continue
        
        cid = f"D_{idx+1:02d}_{work_name}"
        # Deterministic 50/50 split into screen (A) and confirm (B)
        items_a = [item for i, item in enumerate(items) if i % 2 == 0]
        items_b = [item for i, item in enumerate(items) if i % 2 != 0]

        structured_clusters[cid] = {
            "cluster_id": cid,
            "missing_work": work_name,
            "candidate_resolution_type": items[0]["candidate_resolution_type"],
            "total_count": len(items),
            "screen_set_A_count": len(items_a),
            "confirm_set_B_count": len(items_b),
            "screen_ids": [x["boundary_id"] for x in items_a],
            "confirm_ids": [x["boundary_id"] for x in items_b],
            "domains": sorted(list({x["domain"] for x in items}))
        }

    return {
        "clusters": structured_clusters,
        "singletons_count": len(singletons),
        "singletons": singletons
    }
