"""Pre-Revelation Prediction Scoring and Ranking for U_1950."""

import json
from pathlib import Path
from typing import Dict, List, Any

def score_and_rank_frontier(frontier_states: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    ranked_states = []

    for state in frontier_states:
        paths = state["total_generating_paths"]
        parents = state["generating_parent_count"]
        depth = state["min_composition_depth"]
        
        # 1. Path convergence factor (more paths = higher pressure)
        path_score = min(1.0, paths / 150.0)

        # 2. Parent support factor (centrality in historical graph)
        support_score = min(1.0, parents / 16.0)

        # 3. Composition certainty (shorter paths have lower variance)
        cert_score = 1.0 / (1.0 + 0.2 * depth)

        # 4. Domain centrality (e.g. foundational gaps like sheaves and homological algebra)
        domain_weights = {
            "sheaf_and_cohomology": 0.95,
            "homological_algebra": 0.92,
            "algebraic_geometry": 0.88,
            "algebraic_topology": 0.85,
            "differential_analysis": 0.82
        }
        domain_score = domain_weights.get(state["domain_context"], 0.75)

        # Composite Pre-Revelation Score S(u) in [0.0, 1.0]
        s_u = 0.35 * path_score + 0.25 * support_score + 0.20 * cert_score + 0.20 * domain_score

        ranked_states.append({
            **state,
            "prediction_score_S": round(s_u, 4),
            "score_components": {
                "path_score": round(path_score, 4),
                "support_score": round(support_score, 4),
                "certainty_score": round(cert_score, 4),
                "domain_score": round(domain_score, 4)
            }
        })

    # Sort strictly descending by S(u)
    ranked_states.sort(key=lambda x: x["prediction_score_S"], reverse=True)

    # Assign percentile and rank
    total = len(ranked_states)
    for idx, r in enumerate(ranked_states):
        r["rank"] = idx + 1
        r["percentile"] = round((idx + 1) / total, 4)

    with open(output_dir / "U1950_ranked.jsonl", "w", encoding="utf-8") as f:
        for r in ranked_states:
            f.write(json.dumps(r) + "\n")

    return ranked_states
