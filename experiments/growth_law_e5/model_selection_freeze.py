"""Pre-Execution Model Selection Freeze for J_prospective >= 5."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any

def freeze_model_selection_protocol(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "freeze_timestamp": "2026-10-07T03:48:00Z",
        "purpose": (
            "Freeze the exact asymptotic model-selection mathematical specifications, parameter bounds, "
            "loss metrics, and adjudication thresholds BEFORE evaluating Campaign E5 data, ensuring "
            "strictly prospective and immutable model comparison at J_prospective = 5."
        ),
        "target_regime": {
            "eval_units": "independent_prospective_cycles",
            "cycle_count_J_prospective": 5,
            "external_diversity_points_D": [28, 38, 48, 58, 68],
            "campaign_labels": ["E1", "E2", "E3", "E4", "E5"]
        },
        "candidate_models": {
            "H0_post_m6_saturation_null": {
                "equation": "d(D) = 6",
                "free_parameters": 0,
                "meaning": "Strict dimensional invariance once the 6-coordinate basis was discovered"
            },
            "H1_extensible_ontology_linear": {
                "equation": "d(D) = alpha * D + beta",
                "free_parameters": 2,
                "bounds": {"alpha": [0.0, 1.0], "beta": [0.0, 10.0]},
                "meaning": "Unbounded linear coordinate accretion proportional to domain diversity"
            },
            "H2_finite_relational_basis": {
                "equation": "d(D) = d^* - A * exp(-lambda * D)",
                "free_parameters": 3,
                "bounds": {"d_star": [6.0, 7.0], "A": [0.0, 10.0], "lambda": [0.001, 1.0]},
                "meaning": "Asymptotic exponential approach to a finite relational basis d^*"
            },
            "H3_sublinear_logarithmic_basis": {
                "equation": "d(D) = beta + alpha * log(1 + D)",
                "free_parameters": 2,
                "bounds": {"alpha": [0.0, 5.0], "beta": [0.0, 10.0]},
                "meaning": "Slow, unbounded logarithmic coordinate growth"
            }
        },
        "scoring_hierarchy": {
            "primary_metric": "prospective_rmse",
            "secondary_metrics": ["AICc", "BIC"],
            "discrete_handling": "integer_rounding_round_d",
            "tie_breaking_threshold_delta_aicc": 2.0
        },
        "interpretation_constraint": (
            "The selected model shall be reported strictly as 'model preference over the observed diversity range', "
            "never as a formal proof of an infinite limit."
        )
    }

    serialized = json.dumps(protocol, indent=2, sort_keys=True)
    protocol_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    protocol["protocol_sha256"] = protocol_hash

    with open(output_dir / "model_selection_frozen_spec.json", "w", encoding="utf-8") as f:
        json.dump(protocol, f, indent=2)

    return protocol
