"""Negative Frontier Generator: Near-admissible but invalid states F_1950."""

import json
from pathlib import Path
from typing import Dict, List, Any

def generate_negative_frontier(ranked_frontier: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    negative_states = []

    violation_types = [
        ("WITNESS_INCOMPATIBILITY", "W", "cohen_poset_density_certificate"), # forcing witness applied to smooth de Rham forms
        ("INVALID_COMPOSITION", "composition", "non_composable_arrow_type_mismatch"),
        ("WRONG_POLARITY", "Delta", "contradictory_preservation_and_removal"),
        ("GRADING_CONFLICT", "Gamma", "odd_parity_on_commutative_even_algebra"),
        ("SEMANTIC_SCOPE_VIOLATION", "sigma", "SAME_SEMANTICS_on_non_isomorphic_fibers")
    ]

    for idx, item in enumerate(ranked_frontier):
        v_name, v_target, v_detail = violation_types[idx % len(violation_types)]
        nid = f"NEG_FRONTIER_{item['frontier_state_id']}"

        coords = dict(item["coordinates"])
        if v_target == "W":
            coords["W"] = v_detail
        elif v_target == "Gamma":
            coords["Gamma"] = "odd" # conflict with even ring
        elif v_target == "sigma":
            coords["sigma"] = "SAME_SEMANTICS"

        negative_states.append({
            "negative_state_id": nid,
            "derived_from_state_id": item["frontier_state_id"],
            "domain_context": item["domain_context"],
            "violation_type": v_name,
            "violation_target": v_target,
            "violation_detail": v_detail,
            "kernel_v3_admissibility": "STRICT_VIOLATION_FAIL",
            "coordinates": coords
        })

    with open(output_dir / "negative_frontier_1950.jsonl", "w", encoding="utf-8") as f:
        for neg in negative_states:
            f.write(json.dumps(neg) + "\n")

    return negative_states
