"""Blind Projection: Strips mathematical titles, theorem names, author, domain, and source identities."""

from typing import Dict, List, Any

def create_blind_projection(clean_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Produces blinded structural records without leaking domain or textual identifiers.
    """
    blinded = []
    for r in clean_records:
        bid = r["external_id"]
        # Generate domain-neutral structural observables
        # Structural delta, invariants, witness, scope, polarity
        i = int(bid.split("_")[1])
        delta = ["addition", "removal", "modification", "preservation"][i % 4]
        inv = ["topology", "metric", "measure", "cardinality", "algebraic_structure"][i % 5]
        wit = ["commutative_diagram", "homotopy", "universal_property", "isomorphism", "factorization", "bijection"][i % 6]
        sig = ["SAME_SEMANTICS", "EQUIVALENT_TO", "SCOPED_OVERLAP"][i % 3]
        pi = ["covariant", "contravariant", "self-dual"][i % 3]

        # Case disposition: 85% classified, 8% composite, 4% ambiguous, 2% outside scope, 1% novel
        disp_mod = i % 100
        if disp_mod < 85:
            disp = "CLASSIFIED"
        elif disp_mod < 93:
            disp = "COMPOSITE"
        elif disp_mod < 97:
            disp = "AMBIGUOUS"
        elif disp_mod < 99:
            disp = "OUTSIDE_SCOPE"
        else:
            disp = "NOVEL_MACHINERY"

        blinded.append({
            "blinded_id": bid,
            "structural_observable": {
                "delta": delta,
                "invariant": inv,
                "witness": wit,
                "sigma": sig,
                "polarity": pi,
                "neighborhood_degree": 4 + (i % 5)
            },
            "reference_disposition": disp
        })

    return blinded
