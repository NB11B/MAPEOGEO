"""Structured Explanation and Reporting Module for Task T09.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.catalog (Diagnostic, Reference, record formatting)
2. Interface Reused:
   - LegalAssessment, assess_case (intel_authority.evaluator)
   - derive_authority_gaps (intel_authority.gaps)
   - compare_courses (intel_authority.courses)
   - enumerate_actions, enumerate_actors (intel_authority.queries)
3. Additional Semantic Responsibility:
   - R20 & AQ20: Explanation access follows reader's AccessContext (audience, clearance).
   - The legal actor being evaluated confers NO reader permission (actor != reader).
   - Public summary can reference restricted support without disclosing protected source details.
   - Formats decisive traces, Hohfeldian categories, condition breakdown, and typed gaps.
4. Qualification Evidence Delta:
   - AQ05, AQ09, AQ20, AQ24, AQ30, AQ55, AQ56 qualification reporting assertions.
================================================================================
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import json
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class AccessContext:
    """Represents reader identity, clearance, and authorized audiences."""
    reader_actor: str
    clearance_level: str = "public"  # "public", "confidential", "restricted"
    allowed_audiences: List[str] = field(default_factory=lambda: ["public"])
    jurisdictions: List[str] = field(default_factory=list)

    def can_access_restricted(self) -> bool:
        return self.clearance_level in ("restricted", "top_secret")

    def can_access_confidential(self) -> bool:
        return self.clearance_level in ("confidential", "restricted", "top_secret")


def filter_assessment_for_reader(
    assessment: Dict[str, Any],
    access_ctx: Optional[AccessContext] = None,
) -> Dict[str, Any]:
    """Applies reader access control and redacts protected source details.

    Invariant:
    - Host permissions govern access; the legal actor being assessed confers no reader permission.
    - Public summary can reference restricted support without disclosing protected source details.
    """
    if access_ctx is None:
        access_ctx = AccessContext(reader_actor="reader:public", clearance_level="public")

    # The legal actor being assessed confers NO reader permission
    assessed_actor = assessment.get("case", {}).get("actor_ref", {}).get("id")
    # Even if reader_actor == assessed_actor, access is governed purely by clearance_level / allowed_audiences

    filtered = deepcopy(assessment)
    trace = filtered.get("trace", [])

    if isinstance(trace, list):
        sanitized_trace = []
        for item in trace:
            item_copy = deepcopy(item)
            conf = item_copy.get("confidentiality", "public")
            audiences = item_copy.get("target_audiences", ["public"])
            has_audience = bool(set(audiences).intersection(set(access_ctx.allowed_audiences)))
            is_restricted = conf == "restricted" and not access_ctx.can_access_restricted()
            is_confidential = conf == "confidential" and not access_ctx.can_access_confidential()
            if (is_restricted or is_confidential) or not has_audience:
                item_copy["finding"] = "[REDACTED_PROTECTED_CONTENT]"
                item_copy["protected_redacted"] = True
            sanitized_trace.append(item_copy)
        filtered["trace"] = sanitized_trace
    elif isinstance(trace, dict):
        rules_applied = trace.get("rules_applied", [])
        sanitized_rules = []
        for r in rules_applied:
            r_copy = deepcopy(r)
            rule_confidentiality = r_copy.get("confidentiality", "public")
            rule_audiences = r_copy.get("target_audiences", ["public"])

            has_audience = bool(set(rule_audiences).intersection(set(access_ctx.allowed_audiences)))
            is_restricted = rule_confidentiality == "restricted" and not access_ctx.can_access_restricted()
            is_confidential = rule_confidentiality == "confidential" and not access_ctx.can_access_confidential()

            if (is_restricted or is_confidential) or not has_audience:
                rule_id = r_copy.get("rule_ref", {}).get("id", "rule:unknown")
                r_copy["title"] = f"[RESTRICTED RULE: {rule_id} - source details redacted]"
                r_copy["text"] = "[REDACTED_PROTECTED_CONTENT]"
                if "source_ref" in r_copy:
                    r_copy["source_ref"] = {
                        "id": r_copy["source_ref"].get("id"),
                        "redacted": True,
                    }
                r_copy["protected_redacted"] = True

            sanitized_rules.append(r_copy)

        trace_copy = deepcopy(trace)
        trace_copy["rules_applied"] = sanitized_rules
        filtered["trace"] = trace_copy

    filtered["reader_audience_applied"] = access_ctx.allowed_audiences
    filtered["reader_clearance_applied"] = access_ctx.clearance_level
    return filtered


def render_explanation(
    assessment: Dict[str, Any],
    access_ctx: Optional[AccessContext] = None,
    format_mode: str = "text",
) -> str:
    """Renders a structured, human-readable explanation of an authority assessment."""
    filtered = filter_assessment_for_reader(assessment, access_ctx)

    if format_mode == "json":
        return json.dumps(filtered, indent=2)

    case = filtered.get("case", {})
    actor = case.get("actor_ref", {}).get("id", "unknown")
    capacity = case.get("capacity_ref", {}).get("id", "unknown")
    operation = case.get("operation_ref", {}).get("id", "unknown")
    jurisdiction = case.get("jurisdiction_context_ref", {}).get("id", "unknown")
    disposition = filtered.get("disposition", "unresolved")

    lines = [
        "================================================================================",
        f"AUTHORITY ASSESSMENT REPORT: {case.get('case_id', 'case:unknown')} (rev {case.get('revision', 1)})",
        "================================================================================",
        f"Assessed Legal Actor: {actor} (acting in capacity: {capacity})",
        f"Operation:            {operation}",
        f"Jurisdiction:         {jurisdiction}",
        f"Legal Disposition:    {disposition.upper()}",
        f"Status:               {filtered.get('status', 'complete')}",
        "--------------------------------------------------------------------------------",
        "DECISIVE FINDING SUMMARY:",
    ]

    decisive_rules = filtered.get("decisive_rule_refs", [])
    if decisive_rules:
        lines.append(f"  Decisive Rules: {', '.join(decisive_rules)}")
    else:
        lines.append("  Decisive Rules: None (disposition determined by condition absence or unresolved law)")

    trace = filtered.get("trace", {})
    if isinstance(trace, dict):
        lines.append("\nCONDITION AND FACT EVALUATIONS:")
        cond_evals = trace.get("conditions_evaluated", [])
        if cond_evals:
            for ce in cond_evals:
                pred = ce.get("predicate", "unknown_predicate")
                st = ce.get("state", "unknown")
                lines.append(f"  - [{st.upper()}] {pred}")
        else:
            lines.append("  - No conditions evaluated")

        lines.append("\nHOHFELDIAN CATEGORY:")
        hohfeldian = trace.get("hohfeldian_classification", "unclassified")
        lines.append(f"  Classification: {hohfeldian}")

        duties = trace.get("post_action_duties", [])
        if duties:
            lines.append("\nOUTSTANDING POST-ACTION DUTIES:")
            for d in duties:
                lines.append(f"  - Duty: {d.get('description', d.get('id', str(d)))}")
    elif isinstance(trace, list):
        lines.append("\nDECISIVE TRACE LOG:")
        for t in trace:
            k = t.get("kind", "step")
            f = t.get("finding", "")
            lines.append(f"  - [{k.upper()}] {f}")

        # Check conditions in root
        conds = filtered.get("conditions", [])
        if conds:
            lines.append("\nCONDITION AND FACT EVALUATIONS:")
            for ce in conds:
                pred = ce.get("predicate", ce.get("condition_ref", {}).get("id", "condition"))
                st = ce.get("state", "unknown")
                lines.append(f"  - [{st.upper()}] {pred}")

        # Check Hohfeldian in root
        norm = filtered.get("normative_positions", [])
        if norm:
            lines.append("\nHOHFELDIAN CATEGORY:")
            for np in norm:
                lines.append(f"  Classification: {np.get('modality', 'unclassified')}")

        duties = filtered.get("duties", [])
        if duties:
            lines.append("\nOUTSTANDING POST-ACTION DUTIES:")
            for d in duties:
                lines.append(f"  - Duty: {d.get('description', d.get('id', str(d)))}")

    gaps = filtered.get("derived_gaps", [])
    if gaps:
        lines.append("\nOPEN AUTHORITY GAPS AND RESOLUTION ROUTES:")
        for g in gaps:
            lines.append(f"  - Gap Type: {g.get('gap_type')} | Missing: {g.get('missing_target')}")
            lines.append(f"    Route:    {g.get('resolution_route')}")

    lines.append("================================================================================")
    return "\n".join(lines)


def format_json_report(
    assessment: Dict[str, Any],
    access_ctx: Optional[AccessContext] = None,
) -> Dict[str, Any]:
    """Returns access-filtered assessment report as a dictionary."""
    return filter_assessment_for_reader(assessment, access_ctx)


def render_reverse_query_report(
    query_result: Dict[str, Any],
    access_ctx: Optional[AccessContext] = None,
    format_mode: str = "text",
) -> str:
    """Renders human-readable report for reverse action or actor queries."""
    if format_mode == "json":
        return json.dumps(query_result, indent=2)

    query_mode = query_result.get("mode", "unknown")
    status = query_result.get("status", "complete")
    eval_count = query_result.get("evaluated_count", 0)
    unassessed = query_result.get("unassessed_count", 0)

    lines = [
        "================================================================================",
        f"REVERSE AUTHORITY QUERY REPORT: MODE={query_mode.upper()}",
        "================================================================================",
        f"Query Status:     {status.upper()} (complete: {query_result.get('complete', True)})",
        f"Evaluated Count:  {eval_count}",
        f"Unassessed Count: {unassessed}",
        "--------------------------------------------------------------------------------",
        "MATCHING CANDIDATES AND OPERATIONS:",
    ]

    supported_refs = query_result.get("supported_refs", [])
    if supported_refs:
        lines.append("  Supported:")
        for r in supported_refs:
            r_id = r.get("id") if isinstance(r, dict) else str(r)
            lines.append(f"    - {r_id}")

    candidates = query_result.get("candidates", [])
    if candidates:
        lines.append("  Candidate Breakdown:")
        for c in candidates:
            c_id = c.get("candidate_id") or c.get("operation_ref", {}).get("id") or c.get("actor_ref", {}).get("id")
            disp = c.get("disposition", "unknown")
            rules = ", ".join(c.get("decisive_rule_refs", []))
            lines.append(f"    - [{disp}] {c_id} (Rules: {rules})")

    if not supported_refs and not candidates:
        lines.append("  (No supported candidates found within bounded domain)")

    lines.append("================================================================================")
    return "\n".join(lines)


def render_course_comparison_report(
    comparison_result: Dict[str, Any],
    access_ctx: Optional[AccessContext] = None,
    format_mode: str = "text",
) -> str:
    """Renders human-readable comparison of courses of action."""
    if format_mode == "json":
        return json.dumps(comparison_result, indent=2)

    lines = [
        "================================================================================",
        "COURSE OF ACTION COMPARISON REPORT (display_only mode)",
        "================================================================================",
        f"Comparability: {comparison_result.get('comparability', 'not_ranked')}",
        f"Policy:        {comparison_result.get('policy', 'display_only')}",
        "--------------------------------------------------------------------------------",
        "EVALUATED COURSES:",
    ]

    courses = comparison_result.get("courses", [])
    for c in courses:
        c_id = c.get("course_id", "course:unknown")
        status = c.get("status", "unknown")
        blocked = c.get("blocked", False)
        witness = c.get("blocking_witness")
        lines.append(f"  - Course: {c_id} | Status: {status} | Blocked: {blocked}")
        if blocked and witness:
            lines.append(f"    Blocking Witness: {witness}")

    lines.append("================================================================================")
    return "\n".join(lines)
