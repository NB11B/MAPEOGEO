"""Frontier Deduplication: Canonicalizes isomorphic slots into unique states U_1950."""

import json
from pathlib import Path
from typing import Dict, List, Any

def deduplicate_frontier_slots(raw_slots: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    dedup_map = {}
    
    for s in raw_slots:
        coords = s["coordinates"]
        sig_key = (
            s["prototype"],
            s["domain_context"],
            coords["Delta"],
            coords["I"],
            coords["W"],
            coords["sigma"],
            coords["Pi"],
            coords["Gamma"]
        )

        if sig_key not in dedup_map:
            dedup_map[sig_key] = {
                "frontier_state_id": f"U1950_STATE_{len(dedup_map)+1:04d}",
                "prototype": s["prototype"],
                "domain_context": s["domain_context"],
                "primary_parents": [s["parent_source_id"], s["parent_target_id"]],
                "all_generating_parents": set(),
                "total_generating_paths": 0,
                "min_composition_depth": s["composition_depth"],
                "coordinates": coords,
                "structural_justification": s["structural_justification"]
            }

        entry = dedup_map[sig_key]
        entry["all_generating_parents"].add(s["parent_source_id"])
        entry["all_generating_parents"].add(s["parent_target_id"])
        entry["total_generating_paths"] += s["generating_paths_count"]
        entry["min_composition_depth"] = min(entry["min_composition_depth"], s["composition_depth"])

    unique_states = []
    for entry in dedup_map.values():
        unique_states.append({
            "frontier_state_id": entry["frontier_state_id"],
            "prototype": entry["prototype"],
            "domain_context": entry["domain_context"],
            "primary_parents": entry["primary_parents"],
            "generating_parent_count": len(entry["all_generating_parents"]),
            "total_generating_paths": entry["total_generating_paths"],
            "min_composition_depth": entry["min_composition_depth"],
            "coordinates": entry["coordinates"],
            "structural_justification": entry["structural_justification"]
        })

    with open(output_dir / "U1950.jsonl", "w", encoding="utf-8") as f:
        for u in unique_states:
            f.write(json.dumps(u) + "\n")

    return unique_states
