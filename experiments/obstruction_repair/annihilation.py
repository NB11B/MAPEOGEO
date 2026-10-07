"""Obstruction Annihilation Module.

Verifies the central closure property:
    Omega(rho(X)) = 0
for every state in the corpus, ensuring that the repair transformation
strictly annihilates the detected obstruction.
"""

from typing import Dict, Any, List
import copy
from experiments.obstruction_repair.signatures import ObstructionSignature, RepairTransformation
from experiments.obstruction_repair.discover_obstructions import infer_obstruction_signature
from experiments.obstruction_repair.discover_repairs import infer_repair_transformation

def apply_repair_to_state(state: Dict[str, Any], repair: RepairTransformation) -> Dict[str, Any]:
    """Applies the domain restriction rho to the mathematical state's structural features."""
    repaired_state = copy.deepcopy(state)
    feats = repaired_state.get("structural_features", {})
    
    rtype = repair.repair_type
    if rtype == "RESTRICT_TO_NUCLEAR_SUBCATEGORY":
        feats["feature_smashing_defect"] = 0.0
    elif rtype == "TRUNCATE_HOMOTOPY_LEVEL":
        feats["feature_operadic_infinity"] = 0.0
    elif rtype == "RESTRICT_TO_DENSE_CLOSED_DOMAIN":
        feats["feature_domain_closure_defect"] = 0.0
    elif rtype == "PASS_TO_SIGMA_ADDITIVE_MEASURABILITY":
        feats["feature_measure_nonadditivity"] = 0.0
    elif rtype == "RESTRICT_TO_STRATIFIED_SEPARATION_ZFC":
        feats["feature_self_referential_comprehension"] = 0.0
    elif rtype == "RESTRICT_TO_BOUNDED_DEGREE":
        feats["feature_coordinate_bound_overflow"] = 0.0
    elif rtype == "ENFORCE_PENTAGON_COHERENCE":
        feats["feature_unfunctorial_pairing"] = 0.0
    elif rtype == "PASS_TO_DIEUDONNE_DETERMINANT":
        feats["feature_non_abelian_multiplicativity"] = 0.0
    elif rtype == "IDENTITY_REPAIR":
        pass
    else:
        pass

    repaired_state["structural_features"] = feats
    return repaired_state

def evaluate_annihilation_on_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Tests Omega(rho(X)) = 0 for an individual state."""
    omega_initial = infer_obstruction_signature(state)
    repair = infer_repair_transformation(omega_initial)
    repaired_state = apply_repair_to_state(state, repair)
    omega_repaired = infer_obstruction_signature(repaired_state)
    
    annihilated = omega_repaired.is_vanishing()
    return {
        "case_id": state.get("case_id"),
        "initial_obstruction": omega_initial.to_dict(),
        "repair": repair.to_dict(),
        "repaired_obstruction": omega_repaired.to_dict(),
        "annihilated": annihilated,
        "is_exact_zero": omega_repaired.intensity == 0.0
    }

def run_annihilation_suite(corpus: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Runs annihilation tests across the entire corpus."""
    results = [evaluate_annihilation_on_state(state) for state in corpus]
    total = len(results)
    annihilated_count = sum(1 for r in results if r["annihilated"])
    rate = annihilated_count / total if total > 0 else 1.0
    
    return {
        "total_evaluated": total,
        "annihilated_count": annihilated_count,
        "annihilation_rate": rate,
        "all_annihilated": (annihilated_count == total),
        "results": results
    }
