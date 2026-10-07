"""Preregistration module for Campaign E5."""

import json
from pathlib import Path
from typing import Dict, Any

def create_e5_preregistrations(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    e5_prereg = {
        "campaign_id": "E5_FOUNDATIONAL_AND_REPRESENTATION_INVARIANCE",
        "objective": (
            "Test whether M6^{+++} is invariant to the foundational and formal language used to express "
            "mathematics across 9 disjoint formalisms, and unlock asymptotic model selection at J_prospective = 5."
        ),
        "parent_frozen_grammar": "M6^{+++}",
        "parent_parameters": {
            "dimension_d": 6,
            "alphabet_complexity_a": 38,
            "max_composition_depth_c": 6,
            "b9_population": 2594,
            "historical_clean_transformations": 52290
        },
        "epistemic_indices": {
            "J_milestone": 7,
            "J_prospective": 5,
            "prospective_gate_for_model_selection": 5,
            "gate_status": "GATED_CRITERION_REACHED"
        },
        "formalisms_evaluated": [
            "lean4_mathlib",
            "coq_rocq_cic",
            "agda_dependent_types",
            "isabelle_hol_isar",
            "hott_univalent_foundations",
            "bishop_constructive_analysis",
            "smt_lib_first_order",
            "categorical_internal_logic",
            "cas_symbolic_rewrite"
        ],
        "preregistered_failure_modes": [
            {
                "id": "FAILURE_1_REPRESENTATION_DEPENDENCE",
                "condition": "Cross-formalism mean semantic distance bar_V_R(X) >= 0.05 or Tier-4 Equivalence Agreement < 95.0%"
            },
            {
                "id": "FAILURE_2_NEW_COORDINATE",
                "condition": "Delta_d >= 1 (discovery of C7 following failure of hierarchical reduction)"
            },
            {
                "id": "FAILURE_3_COORDINATE_COUPLING",
                "condition": "Pairwise conditional mutual information I(Ci; Cj | C_{/i,j}) >= 0.05 bits or triple interaction I(Ci; Cj; Ck) >= 0.05 bits"
            },
            {
                "id": "FAILURE_4_COMPOSITION_EXPLOSION",
                "condition": "Max composition depth Delta_c_max >= 2 (c_max >= 8) or composition rule count growth > 50%"
            }
        ],
        "result_vocabulary": [
            "E5_PASS_REPRESENTATION_INVARIANCE_CONFIRMED",
            "E5_FAIL_REPRESENTATION_DEPENDENCE",
            "E5_FAIL_NEW_COORDINATE",
            "E5_FAIL_COORDINATE_COUPLING",
            "E5_FAIL_COMPOSITION_EXPLOSION",
            "E5_PARTIAL",
            "E5_BLOCKED"
        ],
        "growth_law_status": "MODEL_SELECTION_UNLOCKED_AT_J_PROSPECTIVE_5"
    }

    with open(output_dir / "e5_preregistration.json", "w", encoding="utf-8") as f:
        json.dump(e5_prereg, f, indent=2)

    return e5_prereg
