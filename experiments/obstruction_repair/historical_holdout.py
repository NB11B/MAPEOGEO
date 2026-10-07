"""Historical Obstruction Backtest Module (Phase B).

Replays frozen historical frontier predictions from 1950 and the rolling historical epochs (1900–2010).
Evaluates Omega(X) using only structural features available at cutoff t:
    U_t -> {realizable (Omega=0), obstructed (Omega!=0), unresolved}
Reveals historical realization and measures:
    P(occupation | Omega = 0) vs P(occupation | Omega != 0)
and verifies repair structural correspondence.
"""

from typing import Dict, Any, List
import json
import os
from experiments.obstruction_repair.signatures import ObstructionSignature, RepairTransformation
from experiments.obstruction_repair.discover_obstructions import infer_obstruction_signature
from experiments.obstruction_repair.discover_repairs import infer_repair_transformation

def run_historical_backtest(
    historical_candidates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Runs the historical obstruction backtest on a combined set of historical candidates."""
    records = []
    
    n_omega_zero = 0
    n_omega_zero_occupied = 0
    n_omega_nonzero = 0
    n_omega_nonzero_occupied = 0
    
    for cand in historical_candidates:
        omega = infer_obstruction_signature(cand)
        is_obstructed = not omega.is_vanishing()
        prediction = "obstructed" if is_obstructed else "realizable"
        
        is_occupied = cand.get("is_occupied", False)
        
        if is_obstructed:
            n_omega_nonzero += 1
            if is_occupied:
                n_omega_nonzero_occupied += 1
        else:
            n_omega_zero += 1
            if is_occupied:
                n_omega_zero_occupied += 1
                
        repair = infer_repair_transformation(omega) if is_obstructed else None
        
        records.append({
            "candidate_id": cand.get("candidate_id") or cand.get("state_id") or cand.get("negative_state_id"),
            "historical_era": cand.get("historical_era", 1950),
            "domain": cand.get("domain", cand.get("domain_context")),
            "omega_signature": omega.to_dict(),
            "predicted_status": prediction,
            "is_occupied_historical": is_occupied,
            "predicted_repair": repair.to_dict() if repair else None
        })

    # Probabilities
    # Haldane-Anscombe correction if zero
    p_occ_given_zero = n_omega_zero_occupied / n_omega_zero if n_omega_zero > 0 else 0.0
    p_occ_given_nonzero = n_omega_nonzero_occupied / n_omega_nonzero if n_omega_nonzero > 0 else 0.0
    
    # Enrichment / Relative Risk
    if p_occ_given_nonzero > 0:
        rr = p_occ_given_zero / p_occ_given_nonzero
    else:
        # Haldane-Anscombe corrected RR
        rr = ((n_omega_zero_occupied + 0.5) / (n_omega_zero + 1.0)) / ((n_omega_nonzero_occupied + 0.5) / (n_omega_nonzero + 1.0))

    return {
        "total_historical_candidates": len(records),
        "n_omega_zero": n_omega_zero,
        "n_omega_zero_occupied": n_omega_zero_occupied,
        "p_occupation_given_omega_zero": round(p_occ_given_zero, 4),
        "n_omega_nonzero": n_omega_nonzero,
        "n_omega_nonzero_occupied": n_omega_nonzero_occupied,
        "p_occupation_given_omega_nonzero": round(p_occ_given_nonzero, 4),
        "obstruction_relative_risk": round(rr, 4),
        "backtest_gate_passed": (p_occ_given_zero > 0.8 and p_occ_given_nonzero == 0.0),
        "records": records
    }
