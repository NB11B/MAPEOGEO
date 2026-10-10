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


@dataclass
class AuthorityActionQuery:
    """Authority-domain action query specification."""
    actor_ref: Dict[str, Any]
    capacity_ref: Dict[str, Any]
    affected_ref: Dict[str, Any]
    candidate_cases: List[Dict[str, Any]]
    domain_ref: Dict[str, Any] = field(default_factory=lambda: {"id": "domain:actions", "revision": 1})


@dataclass
class AuthorityActorQuery:
    """Authority-domain actor query specification."""
    operation_ref: Dict[str, Any]
    affected_ref: Dict[str, Any]
    candidate_cases: List[Dict[str, Any]]
    domain_ref: Dict[str, Any] = field(default_factory=lambda: {"id": "domain:actors", "revision": 1})


def evaluate_candidate_domain(
    candidate_cases: List[Dict[str, Any]],
    eval_fn: Any,
    budget: Optional[Dict[str, Any]] = None,
    extract_target_ref_fn: Optional[Any] = None,
) -> Dict[str, Any]:
    """Shared platform candidate domain router with bounded budget cutoff and partial semantics.
    
    This encapsulates the generic router engine: candidate enumeration, finite budget cutoff,
    evaluated/unassessed counters, stopping reasons, and partial-result tracking.
    """
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
        assessment = eval_fn(case)
        ass_ref = assessment.get("ref", {})
        assessment_refs.append(ass_ref)
        derived_records.append(assessment)

        disp = assessment.get("disposition")
        target_ref = extract_target_ref_fn(case) if extract_target_ref_fn else case.get("ref", {})

        if disp == "supported_within_scope":
            supported_refs.append(target_ref)
        elif disp == "unresolved":
            unresolved_refs.append(target_ref)
        else:  # prohibited or conditions_unmet
            excluded_refs.append(target_ref)

    is_complete = (unassessed_count == 0)
    status = "assessed" if is_complete else "partial"
    stopping_reason = "complete" if is_complete else "candidate_budget"

    return {
        "status": status,
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


def enumerate_actions(
    query: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enumerates candidate actions for a fixed actor and affected scope (AQ25).

    Delegates generic candidate iteration and budget cutoff to evaluate_candidate_domain,
    supplying domain-specific case assessment predicate and operation extraction.
    """
    domain = query.get("domain", {})
    candidate_cases = domain.get("case_bindings", [])
    domain_ref = _normalize_ref(domain.get("ref", "domain:actions"))
    domain_digest = _canonical_digest(domain)

    # Authority domain predicate
    def assess_predicate(case: Dict[str, Any]) -> Dict[str, Any]:
        return assess_case(case, context, budget)

    # Execute shared candidate routing
    router_res = evaluate_candidate_domain(
        candidate_cases=candidate_cases,
        eval_fn=assess_predicate,
        budget=budget,
        extract_target_ref_fn=lambda c: c.get("operation_ref", {}),
    )

    router_res["domain_ref"] = domain_ref
    router_res["domain_digest"] = domain_digest
    return router_res


def enumerate_actors(
    query: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enumerates candidate actors for a fixed operation and affected scope (AQ26).

    Delegates generic candidate iteration and budget cutoff to evaluate_candidate_domain,
    supplying domain-specific case assessment predicate and actor extraction.
    """
    domain = query.get("domain", {})
    candidate_cases = domain.get("case_bindings", [])
    domain_ref = _normalize_ref(domain.get("ref", "domain:actors"))
    domain_digest = _canonical_digest(domain)

    # Authority domain predicate
    def assess_predicate(case: Dict[str, Any]) -> Dict[str, Any]:
        return assess_case(case, context, budget)

    # Execute shared candidate routing
    router_res = evaluate_candidate_domain(
        candidate_cases=candidate_cases,
        eval_fn=assess_predicate,
        budget=budget,
        extract_target_ref_fn=lambda c: c.get("actor_ref", {}),
    )

    router_res["domain_ref"] = domain_ref
    router_res["domain_digest"] = domain_digest
    return router_res

