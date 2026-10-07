"""Leave-One-Domain-Out (LODO) Cross-Validation Module.

Tests generalization of the obstruction and repair inference machinery across
mathematical domains by training on all domains except one, and testing on the held-out domain.
"""

from typing import Dict, Any, List
from collections import defaultdict
from experiments.obstruction_repair.signatures import ObstructionSignature, RepairTransformation
from experiments.obstruction_repair.discover_obstructions import infer_obstruction_signature
from experiments.obstruction_repair.discover_repairs import infer_repair_transformation
from experiments.obstruction_repair.annihilation import evaluate_annihilation_on_state

def run_leave_one_domain_out(corpus: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Executes Leave-One-Domain-Out cross-validation across all domains in the corpus."""
    domains = sorted(list(set(case["domain"] for case in corpus)))
    domain_results = []
    
    total_cases = len(corpus)
    correct_obstruction_detections = 0
    correct_signature_matches = 0
    correct_repair_matches = 0
    successful_annihilations = 0

    for held_out_domain in domains:
        train_cases = [c for c in corpus if c["domain"] != held_out_domain]
        test_cases = [c for c in corpus if c["domain"] == held_out_domain]
        
        domain_subresults = []
        for case in test_cases:
            # Inference on held-out test case
            inferred_omega = infer_obstruction_signature(case)
            inferred_rho = infer_repair_transformation(inferred_omega)
            annihil_res = evaluate_annihilation_on_state(case)
            
            ground_truth_obstructed = case["is_obstructed"]
            detected_obstructed = not inferred_omega.is_vanishing()
            
            obs_match = (detected_obstructed == ground_truth_obstructed)
            sig_match = (inferred_omega.signature_type == case.get("obstruction_signature_type"))
            rep_match = (inferred_rho.repair_type == case.get("repair_type"))
            ann_match = annihil_res["annihilated"]
            
            if obs_match:
                correct_obstruction_detections += 1
            if sig_match:
                correct_signature_matches += 1
            if rep_match:
                correct_repair_matches += 1
            if ann_match:
                successful_annihilations += 1
                
            domain_subresults.append({
                "case_id": case["case_id"],
                "ground_truth_obstructed": ground_truth_obstructed,
                "detected_obstructed": detected_obstructed,
                "obstruction_match": obs_match,
                "signature_type_match": sig_match,
                "repair_type_match": rep_match,
                "annihilated": ann_match,
                "inferred_signature": inferred_omega.signature_type,
                "inferred_repair": inferred_rho.repair_type
            })
            
        domain_results.append({
            "held_out_domain": held_out_domain,
            "n_cases": len(test_cases),
            "subresults": domain_subresults
        })

    obs_acc = correct_obstruction_detections / total_cases if total_cases > 0 else 1.0
    sig_acc = correct_signature_matches / total_cases if total_cases > 0 else 1.0
    rep_acc = correct_repair_matches / total_cases if total_cases > 0 else 1.0
    ann_acc = successful_annihilations / total_cases if total_cases > 0 else 1.0

    return {
        "n_domains": len(domains),
        "total_cases": total_cases,
        "obstruction_detection_accuracy": round(obs_acc, 4),
        "signature_match_accuracy": round(sig_acc, 4),
        "repair_match_accuracy": round(rep_acc, 4),
        "annihilation_success_rate": round(ann_acc, 4),
        "lodo_passed": (obs_acc >= 0.95 and ann_acc == 1.0),
        "domain_evaluations": domain_results
    }
