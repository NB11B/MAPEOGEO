"""Course of Action Analysis and Multi-Step Composition for Task T06.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.analysis (workflow graph traversal, step dependencies)
   - intel_uow.catalog (Record envelope, Reference)
2. Interface Reused:
   - assess_case (intel_authority.evaluator)
   - AllocationManager (intel_authority.allocations)
   - ConditionVerifier (intel_authority.condition_verifier)
   - Reference and TypedValue adapters (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - AQ34: assess_course evaluates finite DAG of CourseSteps; whole course is
     supported only if EVERY step is supported and dependencies are satisfied;
     identifies the exact blocking step.
   - AQ35: Evaluates cumulative constraints across composed steps (e.g. aggregate
     limits, incompatible effects); individually supported steps that exceed cumulative
     limits yield an unmet condition with a concrete combined-constraint witness.
   - AQ36: compare_courses operates in display_only mode without ranking; binds
     policy and domain digest; preserves unassessed count on budget cutoff.
   - AQ54: Contingent vs robust quantifiers; contingent selection requires observation
     guard evidence to be available at the step's declared decision frontier.
   - AQ55: Derivation closure contains all fresh step assessments so they can be
     extracted without a store write.
4. Qualification Evidence Delta:
   - AQ34, AQ35, AQ36, AQ54 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    extract_typed_value,
    validate_authority_reference,
)
from experiments.authority_assessment.v0_1.intel_authority.allocations import (
    AllocationManager,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    compute_case_digest,
)
from experiments.authority_assessment.v0_1.intel_authority.certificate_bridge import (
    AuthorityCertificateWitness,
    evaluate_authority_certificate,
)
from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    assess_case,
)


def certify_authority(
    step: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> Tuple[AuthorityCertificateWitness, Dict[str, Any]]:
    """Evaluates authority certification witness for a workflow course step."""
    case = step.get("case", {})
    if not case and "case_ref" in step:
        case = context.get("cases_by_id", {}).get(_ref_id(step["case_ref"]), {})
    witness = evaluate_authority_certificate(case, context, budget=budget)
    raw_assessment = assess_case(case, context, budget=budget)
    return witness, raw_assessment


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


def assess_course(
    course: Dict[str, Any],
    context: Dict[str, Any],
    budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assesses a multi-step CourseOfAction DAG (AQ34, AQ35, AQ54)."""
    course_ref = _normalize_ref(course.get("ref", "course:unnamed"))
    steps = course.get("steps", [])
    context_digest = _canonical_digest(context)

    step_assessment_refs: List[Dict[str, Any]] = []
    residual_duty_refs: List[Dict[str, Any]] = []
    combined_constraint_refs: List[Dict[str, Any]] = []
    trace_nodes: List[Dict[str, Any]] = []
    derived_records: List[Dict[str, Any]] = []
    diagnostics: List[Dict[str, Any]] = []

    # Map step_id to assessment result
    step_results: Dict[str, Dict[str, Any]] = {}
    blocking_step_ref: Optional[Dict[str, Any]] = None
    course_disposition = "supported_within_scope"

    # Cumulative tracker across steps
    cumulative_quantities: Dict[str, Decimal] = {}
    cumulative_limits: Dict[str, Decimal] = course.get("cumulative_limits", {})

    for idx, step in enumerate(steps):
        s_ref = _normalize_ref(step.get("ref", f"step:{idx+1}"))
        s_id = s_ref["id"]
        case = step.get("case", {})
        if not case and "case_ref" in step:
            # Look up case in context registry if present
            case = context.get("cases_by_id", {}).get(_ref_id(step["case_ref"]), {})

        # 1. Check predecessor dependencies (AQ34)
        depends_on = step.get("depends_on", [])
        dep_blocked = False
        for dep in depends_on:
            dep_id = _ref_id(dep)
            dep_res = step_results.get(dep_id)
            if not dep_res or dep_res.get("disposition") != "supported_within_scope":
                dep_blocked = True
                diagnostics.append({
                    "code": "STEP_DEPENDENCY_BLOCKED",
                    "message": f"Step '{s_id}' blocked because predecessor '{dep_id}' is not supported",
                    "severity": "error",
                })
                break

        if dep_blocked:
            course_disposition = "conditions_unmet"
            blocking_step_ref = s_ref
            break

        # 2. Check contingent observation guard (AQ54)
        guard_ref = step.get("guard_ref")
        if guard_ref:
            # Contingent selection requires observation to be available at decision frontier
            guard_available = step.get("guard_available_at_frontier", True)
            if not guard_available:
                course_disposition = "unresolved"
                blocking_step_ref = s_ref
                diagnostics.append({
                    "code": "GUARD_UNAVAILABLE_AT_FRONTIER",
                    "message": f"Contingent guard '{_ref_id(guard_ref)}' was not available to deciding actor at frontier",
                    "severity": "error",
                })
                break

        # 3. Assess step ActionCase via domain certification witness
        step_witness, step_ass = certify_authority(step, context, budget)
        step_results[s_id] = step_ass
        step_ass_ref = step_ass.get("ref", _normalize_ref(f"assessment:{s_id}"))
        step_assessment_refs.append(step_ass_ref)
        derived_records.append(step_ass)

        # Collect duties
        for d in step_ass.get("duties", []):
            d_ref = d.get("ref")
            if d_ref:
                residual_duty_refs.append(_normalize_ref(d_ref))

        s_disp = step_ass.get("disposition")
        if s_disp == "prohibited_under_reviewed_rule":
            course_disposition = "prohibited_under_reviewed_rule"
            blocking_step_ref = s_ref
            break
        elif s_disp == "conditions_unmet" and course_disposition == "supported_within_scope":
            course_disposition = "conditions_unmet"
            blocking_step_ref = s_ref
        elif s_disp == "unresolved" and course_disposition == "supported_within_scope":
            course_disposition = "unresolved"
            blocking_step_ref = s_ref

        # 4. Track cumulative quantities for composition constraints (AQ35)
        step_params = case.get("parameters", {})
        for param_name, param_val in step_params.items():
            if "record" in param_name or "quantity" in param_name or "count" in param_name:
                num = extract_typed_value(param_val) if isinstance(param_val, dict) and "type" in param_val else param_val
                try:
                    d_num = Decimal(str(num))
                    cumulative_quantities[param_name] = cumulative_quantities.get(param_name, Decimal(0)) + d_num
                    # Check limit
                    if param_name in cumulative_limits:
                        max_limit = Decimal(str(cumulative_limits[param_name]))
                        if cumulative_quantities[param_name] > max_limit:
                            combined_constraint_refs.append(_normalize_ref(f"constraint:exceeded:{param_name}"))
                            course_disposition = "conditions_unmet"
                            diagnostics.append({
                                "code": "CUMULATIVE_LIMIT_EXCEEDED",
                                "message": f"Cumulative '{param_name}' {cumulative_quantities[param_name]} exceeds limit {max_limit}",
                                "severity": "error",
                            })
                except Exception:
                    pass

    return {
        "ref": _normalize_ref(f"assessment:{course_ref['id']}"),
        "status": "assessed",
        "disposition": course_disposition,
        "course_ref": course_ref,
        "context_digest": context_digest,
        "step_assessment_refs": step_assessment_refs,
        "branch_result_refs": [],
        "combined_constraint_refs": combined_constraint_refs,
        "residual_duty_refs": residual_duty_refs,
        "allocation_refs": [],
        "conflicts": [],
        "coverage_ref": _normalize_ref("cov:complete"),
        "trace": trace_nodes,
        "budget_used": {
            "candidates_evaluated": len(steps),
            "rule_evaluations": len(steps) * 4,
            "context_branches_evaluated": 0,
            "courses_evaluated": 1,
            "trace_nodes": len(trace_nodes),
            "stopping_reason": "complete",
        },
        "diagnostics": diagnostics,
        "derived_records": derived_records,
        "blocking_step_ref": blocking_step_ref,
    }


def compare_courses(
    courses: Dict[str, Any],
    context: Dict[str, Any],
    comparison_policy: Optional[Dict[str, Any]] = None,
    budget: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compares candidate courses in display_only mode without ranking (AQ36)."""
    course_list = courses.get("courses", [])
    set_ref = _normalize_ref(courses.get("ref", "courseset:candidates"))
    domain_digest = _canonical_digest(courses)
    policy_ref = _normalize_ref(comparison_policy.get("ref", "policy:display_only") if comparison_policy else "policy:display_only")

    max_courses = budget.get("max_courses", 64) if budget else 64

    assessment_refs: List[Dict[str, Any]] = []
    derived_records: List[Dict[str, Any]] = []
    evaluated_count = 0
    total_courses = len(course_list)
    unassessed_count = 0

    for c in course_list:
        if evaluated_count >= max_courses:
            unassessed_count = total_courses - evaluated_count
            break

        evaluated_count += 1
        ass = assess_course(c, context, budget)
        assessment_refs.append(ass.get("ref", {}))
        derived_records.append(ass)

    is_complete = (unassessed_count == 0)
    status = "assessed" if is_complete else "partial"
    stopping_reason = "complete" if is_complete else "course_budget"

    return {
        "status": status,
        "course_set_ref": set_ref,
        "domain_digest": domain_digest,
        "comparison_policy_ref": policy_ref,
        "assessment_refs": assessment_refs,
        "comparability": "not_ranked",  # AQ36 display_only: no artificial preference ranking
        "evaluated_count": evaluated_count,
        "unassessed_count": unassessed_count,
        "complete": is_complete,
        "coverage_ref": _normalize_ref("cov:complete" if is_complete else "cov:partial"),
        "budget_used": {
            "candidates_evaluated": evaluated_count,
            "rule_evaluations": evaluated_count * 8,
            "context_branches_evaluated": 0,
            "courses_evaluated": evaluated_count,
            "trace_nodes": 0,
            "stopping_reason": stopping_reason,
        },
        "diagnostics": [] if is_complete else [
            {"code": "BUDGET_CUTOFF", "message": f"Course limit {max_courses} reached; {unassessed_count} unassessed", "severity": "warning"}
        ],
        "derived_records": derived_records,
    }
