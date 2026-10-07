"""Derivable Filter: Identifies constructively determined unknowns D_1950."""

import json
from pathlib import Path
from typing import Dict, List, Any

def extract_derivable_population(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    derivable_states = []
    
    # Derivable states are constructible unknowns: combinations formed by deterministic algebraic operators
    # (e.g. dual space of an existing Banach space, direct sum of two simplicial complexes, tensor product of two modules)
    for i in range(len(nodes)):
        n1 = nodes[i]
        n2 = nodes[(i + 2) % len(nodes)]
        
        # 1. Dual functor constructible unknown
        derivable_states.append({
            "derivable_id": f"DERIV_{i+1:04d}_DUAL",
            "construction_type": "FUNCTORIAL_DUAL",
            "parent_nodes": [n1["historical_id"]],
            "generating_operator": "Pontryagin_or_Banach_Duality",
            "coordinates": {
                "Delta": "preservation",
                "I": "algebraic_structure",
                "W": "isomorphism",
                "sigma": "EQUIVALENT_TO",
                "Pi": "contravariant",
                "Gamma": "even"
            },
            "constructive_determinism": "EXACT_CANONICAL_FORM_DETERMINED"
        })

        # 2. Product / Direct Sum constructible unknown
        derivable_states.append({
            "derivable_id": f"DERIV_{i+1:04d}_DIRECT_SUM",
            "construction_type": "UNIVERSAL_PRODUCT",
            "parent_nodes": [n1["historical_id"], n2["historical_id"]],
            "generating_operator": "Direct_Sum_Coproduct",
            "coordinates": {
                "Delta": "addition",
                "I": "topology",
                "W": "universal_property",
                "sigma": "SAME_SEMANTICS",
                "Pi": "covariant",
                "Gamma": "even"
            },
            "constructive_determinism": "EXACT_CANONICAL_FORM_DETERMINED"
        })

    with open(output_dir / "derivable_1950.jsonl", "w", encoding="utf-8") as f:
        for d in derivable_states:
            f.write(json.dumps(d) + "\n")

    return derivable_states
