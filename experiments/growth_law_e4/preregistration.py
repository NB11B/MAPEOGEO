"""Preregistration module for Campaign E4."""

import json
from pathlib import Path
from typing import Dict, Any

def create_e4_preregistrations(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    e4_prereg = {
        "campaign_id": "E4_COMBINATORIAL_INTERACTION_AND_SCALE",
        "objective": (
            "Deliberate stress-testing of M6^{++} against scale and combinatorial multi-coordinate "
            "interaction (kappa >= 4.2 active coordinates per record) to audit Cartesian product "
            "factorization and rule/depth compactness."
        ),
        "parent_frozen_grammar": "M6^{++}",
        "parent_parameters": {
            "dimension_d": 6,
            "alphabet_complexity_a": 36,
            "max_composition_depth_c": 6,
            "b8_population": 2756,
            "historical_clean_transformations": 49370
        },
        "epistemic_indices": {
            "J_milestone": 6,
            "J_prospective": 4,
            "prospective_gate_for_model_selection": 5
        },
        "adjudication_hierarchy": [
            "COMPOSITION",
            "ALPHABET",
            "REFINEMENT",
            "NEW_COORDINATE"
        ],
        "preregistered_failure_modes": [
            {
                "id": "FAILURE_1_NEW_COORDINATE",
                "condition": "Delta_d >= 1 (discovery of C7 following failure of hierarchical reduction)"
            },
            {
                "id": "FAILURE_2_COORDINATE_COUPLING",
                "condition": "Pairwise conditional mutual information I(Ci; Cj | C_{/i,j}) >= 0.05 bits or triple interaction I(Ci; Cj; Ck) >= 0.05 bits"
            },
            {
                "id": "FAILURE_3_COMPOSITION_EXPLOSION",
                "condition": "Max composition depth Delta_c_max >= 2 (c_max >= 8) or composition rule count growth > 50%"
            }
        ],
        "result_vocabulary": [
            "E4_PASS_FACTORIZATION_AND_COMPACTNESS_MAINTAINED",
            "E4_FAIL_NEW_COORDINATE",
            "E4_FAIL_COORDINATE_COUPLING",
            "E4_FAIL_COMPOSITION_EXPLOSION",
            "E4_PARTIAL",
            "E4_BLOCKED"
        ],
        "growth_law_status": "TRAJECTORY_INSUFFICIENT_FOR_MODEL_SELECTION",
        "model_selection_scheduled_milestone": "J_prospective >= 5"
    }

    with open(output_dir / "e4_preregistration.json", "w", encoding="utf-8") as f:
        json.dump(e4_prereg, f, indent=2)

    model_prereg = {
        "framework": "THREE_WAY_ASYMPTOTIC_MODEL_COMPARISON",
        "evaluation_rule": "Model preference over observed prospective range (J_prospective >= 5)",
        "models": {
            "H1_extensible_ontology_linear": {
                "equation": "d(D) = alpha * D + beta",
                "meaning": "Unbounded linear coordinate accretion proportional to domain diversity"
            },
            "H2_finite_relational_basis": {
                "equation": "d(D) = d^* - A * exp(-lambda * D)",
                "meaning": "Strict saturation toward a finite basis d^* in {6, 7}"
            },
            "H3_sublinear_logarithmic_basis": {
                "equation": "d(D) = beta + alpha * log(1 + D)",
                "meaning": "Discrete, slow, sublinear unbounded growth without strict finite bound"
            }
        },
        "adjudication_criterion": "AIC, BIC, and cross-validated out-of-domain trajectory error at J_prospective >= 5"
    }

    with open(output_dir / "model_selection_preregistration.json", "w", encoding="utf-8") as f:
        json.dump(model_prereg, f, indent=2)

    return {
        "e4_prereg": e4_prereg,
        "model_prereg": model_prereg
    }
