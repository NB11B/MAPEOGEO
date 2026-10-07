"""Deficiency Extractor: Transforms raw failure records into structured work deficiency tuples.

For every b in B5:
D(b) = (known_state, failed_discrimination, missing_work, required_evidence)
"""

from typing import Dict, Any

def extract_deficiency(b5_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts a work-deficiency specification from a raw B5 failure record.
    """
    bid = b5_record["boundary_id"]
    proj = b5_record["failure_projection"]
    mech = b5_record["failure_mechanism"]
    domain = b5_record["domain"]
    m5_sig = b5_record["m5_signature"]

    # Map failure mechanisms to missing mathematical work
    work_mapping = {
        "non_abelian_higher_gauge_coherence": {
            "missing_work": "higher_gerbe_gauge_coherence",
            "required_evidence": "2_morphism_commutator_witness",
            "candidate_type": "ALPHABET_WITNESS"
        },
        "infinite_dimensional_trace_class_boundary": {
            "missing_work": "operator_ideal_nuclear_admissibility",
            "required_evidence": "trace_norm_convergence_witness",
            "candidate_type": "ALPHABET_WITNESS"
        },
        "transcendental_essential_singularity": {
            "missing_work": "picard_exceptional_value_tracking",
            "required_evidence": "monodromy_defect_witness",
            "candidate_type": "OUTSIDE_DECLARED_SCOPE"
        },
        "undecidable_fiber_separation_condition": {
            "missing_work": "unresolvable_fiber_symmetry",
            "required_evidence": "independent_oracle_witness",
            "candidate_type": "INFORMATION_THEORETICALLY_AMBIGUOUS"
        },
        "stratified_micro_local_defect": {
            "missing_work": "conormal_sheaf_microlocalization",
            "required_evidence": "characteristic_cycle_witness",
            "candidate_type": "COMPOSITION_LONG"
        }
    }

    spec = work_mapping.get(mech, {
        "missing_work": "unclassified_work_deficiency",
        "required_evidence": "generic_witness_certificate",
        "candidate_type": "INDEPENDENT_EVIDENCE_REQUIRED"
    })

    return {
        "boundary_id": bid,
        "domain": domain,
        "known_state": m5_sig,
        "failed_discrimination": proj,
        "missing_work": spec["missing_work"],
        "required_evidence": spec["required_evidence"],
        "candidate_resolution_type": spec["candidate_type"]
    }
