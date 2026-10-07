"""Preregistration module for Campaign E3."""

import json
from pathlib import Path
from typing import Dict, Any

def create_e3_preregistrations(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    e3_prereg = {
        "campaign_id": "E3_ADVERSARIAL_STRESS_TEST",
        "objective": (
            "Deliberately targeted stress-test population selected to maximize structural "
            "distance and the probability of falsifying six-dimensional saturation."
        ),
        "parent_frozen_grammar": "M6^+",
        "parent_parameters": {
            "dimension_d": 6,
            "alphabet_complexity_a": 34,
            "max_composition_depth_c": 6,
            "b7_population": 2892
        },
        "adjudication_hierarchy": [
            "COMPOSITION",
            "ALPHABET",
            "REFINEMENT",
            "NEW_COORDINATE"
        ],
        "permitted_dimension_increments": [0, 1, 2, 3],
        "coordinate_interaction_permitted": True,
        "result_vocabulary": [
            "E3_PASS_NO_DIMENSION_GROWTH",
            "E3_PASS_DIMENSION_GROWTH",
            "E3_PASS_COORDINATE_INTERACTION",
            "E3_PARTIAL",
            "E3_FAIL",
            "E3_BLOCKED"
        ],
        "growth_law_status": "TRAJECTORY_INSUFFICIENT_FOR_MODEL_SELECTION",
        "model_selection_scheduled_milestone": "J >= 5"
    }

    with open(output_dir / "e3_preregistration.json", "w", encoding="utf-8") as f:
        json.dump(e3_prereg, f, indent=2)

    model_prereg = {
        "framework": "THREE_WAY_ASYMPTOTIC_MODEL_COMPARISON",
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
        "adjudication_criterion": "BIC and cross-validated out-of-domain trajectory error at J >= 5"
    }

    with open(output_dir / "model_selection_preregistration.json", "w", encoding="utf-8") as f:
        json.dump(model_prereg, f, indent=2)

    return {
        "e3_prereg": e3_prereg,
        "model_prereg": model_prereg
    }
