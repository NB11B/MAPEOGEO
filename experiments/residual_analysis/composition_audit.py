"""Composition Audit: Determines whether unexplained transitions factor into composites
of existing frozen primitives P_i o P_j under (Delta, I, W, sigma).

If an edge labeled as a single operator actually satisfies the algebraic composition
of existing operations, it is classified as COMPOSITION rather than requiring a new coordinate.
"""

from typing import Dict, List, Any

def audit_compositional_factorization(
    transitions: List[Dict[str, Any]],
    frozen_composition_table: Dict[str, Dict[str, str]]
) -> Dict[str, Any]:
    """
    Audits candidate transitions to check if they factor into chains of 2 or 3 existing primitives.
    """
    factored_composites: List[Dict[str, Any]] = []
    unfactorable_residuals: List[Dict[str, Any]] = []

    for t in transitions:
        factorization = t.get("factors")
        if factorization and len(factorization) >= 2:
            # Verify validity in composition table
            is_valid_chain = True
            for i in range(len(factorization) - 1):
                p_curr = factorization[i]
                p_next = factorization[i+1]
                comp_status = frozen_composition_table.get(p_curr, {}).get(p_next, "FORBIDDEN")
                if comp_status not in ("DEFINED", "CONDITIONALLY DEFINED"):
                    is_valid_chain = False
                    break
            
            if is_valid_chain:
                factored_composites.append({
                    "id": t.get("id"),
                    "factors": factorization,
                    "length": len(factorization),
                    "domain": t.get("domain", "general")
                })
            else:
                unfactorable_residuals.append(t)
        else:
            unfactorable_residuals.append(t)

    total = len(transitions)
    n_factored = len(factored_composites)
    return {
        "total_audited": total,
        "factored_composites_count": n_factored,
        "unfactorable_count": len(unfactorable_residuals),
        "composition_resolution_rate": n_factored / total if total > 0 else 0.0,
        "factored_samples": factored_composites[:10],
        "unfactorable_residuals": unfactorable_residuals
    }
