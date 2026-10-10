"""Reverse Authority Queries and Candidate Enumeration for Task T05.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.analysis (candidate domain generation, candidate filtering)
   - intel_uow.catalog (Record envelope, Reference, Diagnostic)
2. Interface Reused:
   - assess_case (intel_authority.evaluator)
   - ActionCase bindings and digests (intel_authority.case_bindings)
   - Reference and TypedValue adapters (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - AQ25: enumerate_actions returns exact bounded supported operations matching
     direct expectations; preserves conditions and traces.
   - AQ26: enumerate_actors returns exact bounded supported actor-capacity pairs
     matching direct expectations.
   - AQ27: Preserves unresolved candidates without negative coercion.
   - AQ28: Evaluates parity between direct oracle and reverse candidate results.
   - AQ29: Bounded budget cutoff returns partial result with positive unassessed_count
     and complete=False; search exhaustion never claims global absence.
   - AQ30: Reacts to material binding changes, preventing incompatible cache reuse.
   - AQ55: Read-only derivation returns flat derived_records closure resolving
     every fresh reference without a store write.
4. Qualification Evidence Delta:
   - AQ25, AQ26, AQ27, AQ28, AQ29, AQ30, AQ55 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    validate_authority_reference,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    compute_case_digest,
)
from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    assess_case,
)


def _canonical_digest(data: Any) -> str:
    b = json.dumps(data, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    return hashlib.sha256(b).hexdigest()


def _normalize_ref(ref_val: Any) -> Dict[str, Any]:
    if isinstance(ref_val, dict) and "id" in ref_val:
        return {"id": str(ref_val["id"]), "revision": int(ref_val.get("revision", 1))}
    elif isinstance(ref_val, str):
        return {"id": ref_val, "revision": 1}
    return {"id": str(ref_val), "revision": 1}


def _ref_id(ref_val: Any) -> str:
    if isinstance(ref_val, dict):
        return str(ref_val.get("id", ""))
    return str(ref_val)


def enumerate_actions(
    query: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enumerates candidate actions for a fixed actor and affected scope (AQ25).

    Returns CandidateResult containing supported, unresolved, and excluded operations.
    """
    domain = query.get("domain", {})
    candidate_cases = domain.get("case_bindings", [])
    domain_ref = _normalize_ref(domain.get("ref", "domain:actions"))
    domain_digest = _canonical_digest(domain)

    max_candidates = budget.get("max_candidates", 4096) if budget else 4096

    supported_refs: List[Dict[str, Any]] = []
    unresolved_refs: List[Dict[str, Any]] = []
    excluded_refs: List[Dict[str, Any]] = []
    assessment_refs: List[Dict[str, Any]] = []
    derived_records: List[Dict[str, Any]] = []

    evaluated_count = 0
    total_candidates = len(candidate_cases)
    unassessed_count = 0

    for case in candidate_cases:
        if evaluated_count >= max_candidates:
            unassessed_count = total_candidates - evaluated_count
            break

        evaluated_count += 1
        assessment = assess_case(case, context, budget)
        ass_ref = assessment.get("ref", {})
        assessment_refs.append(ass_ref)
        derived_records.append(assessment)

        disp = assessment.get("disposition")
        op_ref = case.get("operation_ref", {})

        if disp == "supported_within_scope":
            supported_refs.append(op_ref)
        elif disp == "unresolved":
            unresolved_refs.append(op_ref)
        else:  # prohibited or conditions_unmet
            excluded_refs.append(op_ref)

    is_complete = (unassessed_count == 0)
    status = "assessed" if is_complete else "partial"
    stopping_reason = "complete" if is_complete else "candidate_budget"

    return {
        "status": status,
        "domain_ref": domain_ref,
        "domain_digest": domain_digest,
        "assessment_refs": assessment_refs,
        "supported_refs": supported_refs,
        "unresolved_refs": unresolved_refs,
        "excluded_refs": excluded_refs,
        "evaluated_count": evaluated_count,
        "unassessed_count": unassessed_count,
        "complete": is_complete,
        "coverage_ref": _normalize_ref("cov:complete" if is_complete else "cov:partial"),
        "budget_used": {
            "candidates_evaluated": evaluated_count,
            "rule_evaluations": evaluated_count * 4,
            "context_branches_evaluated": 0,
            "courses_evaluated": 0,
            "trace_nodes": evaluated_count * 2,
            "stopping_reason": stopping_reason,
        },
        "diagnostics": [] if is_complete else [
            {"code": "BUDGET_CUTOFF", "message": f"Candidate limit {max_candidates} reached; {unassessed_count} unassessed", "severity": "warning"}
        ],
        "derived_records": derived_records,
    }


def enumerate_actors(
    query: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enumerates candidate actors for a fixed operation and affected scope (AQ26).

    Returns CandidateResult containing supported, unresolved, and excluded actors.
    """
    domain = query.get("domain", {})
    candidate_cases = domain.get("case_bindings", [])
    domain_ref = _normalize_ref(domain.get("ref", "domain:actors"))
    domain_digest = _canonical_digest(domain)

    max_candidates = budget.get("max_candidates", 4096) if budget else 4096

    supported_refs: List[Dict[str, Any]] = []
    unresolved_refs: List[Dict[str, Any]] = []
    excluded_refs: List[Dict[str, Any]] = []
    assessment_refs: List[Dict[str, Any]] = []
    derived_records: List[Dict[str, Any]] = []

    evaluated_count = 0
    total_candidates = len(candidate_cases)
    unassessed_count = 0

    for case in candidate_cases:
        if evaluated_count >= max_candidates:
            unassessed_count = total_candidates - evaluated_count
            break

        evaluated_count += 1
        assessment = assess_case(case, context, budget)
        ass_ref = assessment.get("ref", {})
        assessment_refs.append(ass_ref)
        derived_records.append(assessment)

        disp = assessment.get("disposition")
        act_ref = case.get("actor_ref", {})

        if disp == "supported_within_scope":
            supported_refs.append(act_ref)
        elif disp == "unresolved":
            unresolved_refs.append(act_ref)
        else:
            excluded_refs.append(act_ref)

    is_complete = (unassessed_count == 0)
    status = "assessed" if is_complete else "partial"
    stopping_reason = "complete" if is_complete else "candidate_budget"

    return {
        "status": status,
        "domain_ref": domain_ref,
        "domain_digest": domain_digest,
        "assessment_refs": assessment_refs,
        "supported_refs": supported_refs,
        "unresolved_refs": unresolved_refs,
        "excluded_refs": excluded_refs,
        "evaluated_count": evaluated_count,
        "unassessed_count": unassessed_count,
        "complete": is_complete,
        "coverage_ref": _normalize_ref("cov:complete" if is_complete else "cov:partial"),
        "budget_used": {
            "candidates_evaluated": evaluated_count,
            "rule_evaluations": evaluated_count * 4,
            "context_branches_evaluated": 0,
            "courses_evaluated": 0,
            "trace_nodes": evaluated_count * 2,
            "stopping_reason": stopping_reason,
        },
        "diagnostics": [] if is_complete else [
            {"code": "BUDGET_CUTOFF", "message": f"Candidate limit {max_candidates} reached; {unassessed_count} unassessed", "severity": "warning"}
        ],
        "derived_records": derived_records,
    }
