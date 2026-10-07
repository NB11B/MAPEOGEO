"""Held-Out Repair Prediction Module.

Predicts minimal repair transformations rho(Omega) for novel or held-out obstructed states,
verifying both minimality and exact annihilation Omega(rho(X)) = 0.
"""

from typing import Dict, Any, List
from experiments.obstruction_repair.signatures import ObstructionSignature, RepairTransformation
from experiments.obstruction_repair.discover_obstructions import infer_obstruction_signature
from experiments.obstruction_repair.discover_repairs import infer_repair_transformation
from experiments.obstruction_repair.minimality import verify_repair_minimality
from experiments.obstruction_repair.annihilation import evaluate_annihilation_on_state

def predict_and_verify_repair(state: Dict[str, Any]) -> Dict[str, Any]:
    """Given a candidate state, infers obstruction, predicts minimal repair,

    verifies minimality, and evaluates annihilation.
    """
    omega = infer_obstruction_signature(state)
    repair = infer_repair_transformation(omega)
    minimality_info = verify_repair_minimality(omega, repair)
    annihilation_info = evaluate_annihilation_on_state(state)
    
    return {
        "case_id": state.get("case_id"),
        "is_obstructed": not omega.is_vanishing(),
        "obstruction_signature": omega.to_dict(),
        "predicted_repair": repair.to_dict(),
        "minimality_verified": minimality_info["is_minimal"],
        "retention_efficiency": minimality_info["retention_efficiency"],
        "annihilated": annihilation_info["annihilated"],
        "is_exact_zero": annihilation_info["is_exact_zero"]
    }

def run_held_out_repair_prediction(held_out_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Runs repair prediction on a set of held-out test states."""
    evaluations = [predict_and_verify_repair(s) for s in held_out_states]
    n_total = len(evaluations)
    n_annihilated = sum(1 for e in evaluations if e["annihilated"])
    n_minimal = sum(1 for e in evaluations if e["minimality_verified"])
    
    return {
        "total_held_out": n_total,
        "annihilation_count": n_annihilated,
        "annihilation_rate": round(n_annihilated / n_total, 4) if n_total > 0 else 1.0,
        "minimality_rate": round(n_minimal / n_total, 4) if n_total > 0 else 1.0,
        "all_valid": (n_annihilated == n_total and n_minimal == n_total),
        "predictions": evaluations
    }
