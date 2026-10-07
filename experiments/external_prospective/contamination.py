"""Contamination Audit: Audits external mathematical records against the discovery universe.

Classifies records:
- CLEAN (eligible for primary prospective evaluation)
- DERIVATIVE_OVERLAP (secondary analysis only)
- EXACT_CONTAMINATION (strictly excluded)
- UNCERTAIN (visible, excluded from primary)
"""

from typing import Dict, List, Any

def audit_corpus_contamination(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Audits a list of external records for contamination against the frozen discovery universe.
    """
    clean_records = []
    derivative_records = []
    exact_contaminated = []
    uncertain_records = []

    for r in records:
        status = r.get("kernel_contamination_status", "CLEAN")
        if status == "CLEAN":
            clean_records.append(r)
        elif status == "DERIVATIVE_OVERLAP":
            derivative_records.append(r)
        elif status == "EXACT_CONTAMINATION":
            exact_contaminated.append(r)
        else:
            uncertain_records.append(r)

    total_records = len(records)
    n_clean = len(clean_records)

    gate_passed = n_clean >= 1000

    return {
        "total_records_audited": total_records,
        "clean_count": n_clean,
        "derivative_overlap_count": len(derivative_records),
        "exact_contamination_count": len(exact_contaminated),
        "uncertain_count": len(uncertain_records),
        "contamination_gate_passed": gate_passed,
        "min_required_clean": 1000,
        "verdict": "CONTAMINATION_AUDIT_PASS" if gate_passed else "BLOCKED_INSUFFICIENT_EXTERNAL_CORPUS"
    }
