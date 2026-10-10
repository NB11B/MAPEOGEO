"""Authority Gap Derivation and Materiality for Task T05.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.analysis (DeficiencyExtractor, blocker resolution)
   - intel_uow.catalog (Record envelope, Reference)
2. Interface Reused:
   - LegalAssessment (intel_authority.evaluator)
   - ConditionVerifier and BilateralState (intel_authority.condition_verifier)
   - Reference and TypedValue adapters (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - AQ31: derive_authority_gaps identifies typed gaps with scoped propositions,
     dependencies, and matching resolution work classes without invented probabilities.
   - AQ32: Distinguishes finding evidence of an existing grant (authority_evidence_missing)
     from creating a new grant (grant_required).
   - AQ33: Legal review cannot invent a fact or grant; review addresses interpretation
     and applicability gaps, but factual and grant gaps remain unestablished until evidenced.
   - Determines materiality: outcome_change_witnessed, basis_change_witnessed,
     coverage_required, or undetermined.
4. Qualification Evidence Delta:
   - AQ31, AQ32, AQ33 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    validate_authority_reference,
)


class GapKind(str, Enum):
    FACT_GAP = "fact_gap"
    AUTHORITY_EVIDENCE_MISSING = "authority_evidence_missing"
    GRANT_REQUIRED = "grant_required"
    SOURCE_APPLICABILITY_GAP = "source_applicability_gap"
    INTERPRETATION_GAP = "interpretation_gap"
    COVERAGE_GAP = "coverage_gap"
    OPERATION_DEFINITION_GAP = "operation_definition_gap"
    RESOURCE_COMMITMENT_REQUIRED = "resource_commitment_required"
    COMPLETION_RECONCILIATION_REQUIRED = "completion_reconciliation_required"
    ADMISSION_REQUIRED = "admission_required"


# Canonical alias for domain-specific gap taxonomy
AuthorityGapKind = GapKind


# Mapping: AuthorityGapKind -> required work operator in \Sigma_W = {O, E, K, C, F, D, S}
AUTHORITY_GAP_TO_OPERATOR: Dict[str, str] = {
    GapKind.FACT_GAP.value: "O",                          # Observe: Inquire/acquire factual source evidence
    GapKind.AUTHORITY_EVIDENCE_MISSING.value: "K",        # Classify: Retrieve warrant / existing grant
    GapKind.GRANT_REQUIRED.value: "S",                    # Select: Propose grant to competent principal
    GapKind.SOURCE_APPLICABILITY_GAP.value: "C",          # Compare: Perform legal scope interpretation
    GapKind.INTERPRETATION_GAP.value: "K",                # Classify: Review interpretation profile
    GapKind.COVERAGE_GAP.value: "C",                      # Compare: Expand coverage contract
    GapKind.OPERATION_DEFINITION_GAP.value: "F",          # Form: Formalize operation contract
    GapKind.RESOURCE_COMMITMENT_REQUIRED.value: "S",      # Select: Request resource allocation
    GapKind.COMPLETION_RECONCILIATION_REQUIRED.value: "O",# Observe: Reconcile UoW completion frontier
    GapKind.ADMISSION_REQUIRED.value: "S",                # Select: Submit UoW admission proposal
}


@dataclass
class PlatformDeficiency:
    r"""Thin domain projection of authority gap into platform deficiency D = R \setminus G.
    
    The authority domain owns only the gap classification and proposition derivation;
    generic deficiency lifecycle, storage, and scheduling belong to the platform.
    """
    target_subject: str
    required_operator: str
    authority_gap_kind: str
    supporting_assessment_ref: Dict[str, Any]
    dependency_refs: List[Dict[str, Any]]
    scope_ref: Dict[str, Any]
    witness_refs: List[Dict[str, Any]]
    is_unresolved: bool
    resolution_routes: List[str]
    materiality: str
    raw_gap_ref: Dict[str, Any]


def to_platform_deficiency(authority_gap: Dict[str, Any]) -> PlatformDeficiency:
    """Projects an authority domain gap into a standard platform deficiency without inference."""
    kind = authority_gap.get("kind", GapKind.FACT_GAP.value)
    op = AUTHORITY_GAP_TO_OPERATOR.get(kind, "O")
    prop = authority_gap.get("proposition_ref", {})
    subject = prop.get("id", str(prop)) if isinstance(prop, dict) else str(prop)

    return PlatformDeficiency(
        target_subject=subject,
        required_operator=op,
        authority_gap_kind=kind,
        supporting_assessment_ref=authority_gap.get("assessment_ref", {}),
        dependency_refs=authority_gap.get("dependency_refs", []),
        scope_ref=authority_gap.get("scope_ref", {}),
        witness_refs=authority_gap.get("witness_refs", []),
        is_unresolved=(authority_gap.get("actual_resolution_state") == "open"),
        resolution_routes=authority_gap.get("resolution_route_kinds", []),
        materiality=authority_gap.get("materiality", Materiality.OUTCOME_CHANGE_WITNESSED.value),
        raw_gap_ref=authority_gap.get("ref", {}),
    )


class Materiality(str, Enum):
    OUTCOME_CHANGE_WITNESSED = "outcome_change_witnessed"
    BASIS_CHANGE_WITNESSED = "basis_change_witnessed"
    COVERAGE_REQUIRED = "coverage_required"
    UNDETERMINED = "undetermined"


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


# Mapping from gap kind to appropriate resolution route kinds (AQ31)
RESOLUTION_ROUTES: Dict[str, List[str]] = {
    GapKind.FACT_GAP.value: ["investigate_fact", "request_corroborating_evidence"],
    GapKind.AUTHORITY_EVIDENCE_MISSING.value: ["discover_grant_evidence", "authenticate_instrument"],
    GapKind.GRANT_REQUIRED.value: ["issue_competent_grant"],
    GapKind.SOURCE_APPLICABILITY_GAP.value: ["review_source_applicability", "review_jurisdiction_scope"],
    GapKind.INTERPRETATION_GAP.value: ["review_interpretation_profile"],
    GapKind.COVERAGE_GAP.value: ["expand_coverage_contract"],
    GapKind.OPERATION_DEFINITION_GAP.value: ["formalize_operation_contract"],
    GapKind.RESOURCE_COMMITMENT_REQUIRED.value: ["request_resource_allocation"],
    GapKind.COMPLETION_RECONCILIATION_REQUIRED.value: ["reconcile_uow_completion"],
    GapKind.ADMISSION_REQUIRED.value: ["submit_uow_admission_proposal"],
}


def derive_authority_gaps(
    assessment: Dict[str, Any],
    question_ref: Dict[str, Any] | str,
) -> List[Dict[str, Any]]:
    """Derives typed AuthorityGap records from an unresolved or partial assessment (AQ31)."""
    q_ref = _normalize_ref(question_ref)
    ass_ref = _normalize_ref(assessment.get("ref", "assessment:unnamed"))
    case_ref = _normalize_ref(assessment.get("case_ref", "case:unnamed"))
    disposition = assessment.get("disposition")

    gaps: List[Dict[str, Any]] = []
    gap_idx = 0

    # If already supported or explicitly prohibited, no blocker gaps needed
    if disposition in ("supported_within_scope", "prohibited_under_reviewed_rule"):
        return []

    # 1. Inspect unresolved basis paths
    basis_paths = assessment.get("basis_paths", [])
    for bp in basis_paths:
        bp_state = bp.get("state")
        rule_refs = bp.get("rule_refs", [])
        cond_refs = bp.get("condition_refs", [])
        r_id = _ref_id(rule_refs[0]) if rule_refs else "rule:unknown"

        if bp_state == "unresolved":
            # Missing facts / conditions
            for c_ref in cond_refs:
                c_id = _ref_id(c_ref)
                gap_idx += 1
                gaps.append({
                    "ref": _normalize_ref(f"gap:{_ref_id(ass_ref)}:{gap_idx}"),
                    "kind": GapKind.FACT_GAP.value,
                    "proposition_ref": _normalize_ref(c_id),
                    "scope_ref": bp.get("regime_ref", _normalize_ref("regime:default")),
                    "assessment_ref": ass_ref,
                    "question_ref": q_ref,
                    "dependency_refs": [_normalize_ref(r_id)],
                    "resolution_route_kinds": RESOLUTION_ROUTES[GapKind.FACT_GAP.value],
                    "materiality": Materiality.OUTCOME_CHANGE_WITNESSED.value,
                    "witness_refs": [ass_ref],
                    "actual_resolution_state": "open",
                })

    # 2. Inspect diagnostics for missing capacity or statutory basis
    diagnostics = assessment.get("diagnostics", [])
    for d in diagnostics:
        code = d.get("code")
        if code == "CAPACITY_EVIDENCE_REFUTED" or "MISSING_GRANT" in code:
            gap_idx += 1
            gaps.append({
                "ref": _normalize_ref(f"gap:{_ref_id(ass_ref)}:{gap_idx}"),
                "kind": GapKind.AUTHORITY_EVIDENCE_MISSING.value,
                "proposition_ref": _normalize_ref(d.get("message", "missing_authority")),
                "scope_ref": _normalize_ref("scope:capacity"),
                "assessment_ref": ass_ref,
                "question_ref": q_ref,
                "dependency_refs": [case_ref],
                "resolution_route_kinds": RESOLUTION_ROUTES[GapKind.AUTHORITY_EVIDENCE_MISSING.value],
                "materiality": Materiality.OUTCOME_CHANGE_WITNESSED.value,
                "witness_refs": [ass_ref],
                "actual_resolution_state": "open",
            })

    # 3. If disposition is unresolved and no basis paths exist, it's a statutory basis gap (grant_required or source_applicability_gap)
    if disposition == "unresolved" and not gaps:
        gap_idx += 1
        gaps.append({
            "ref": _normalize_ref(f"gap:{_ref_id(ass_ref)}:{gap_idx}"),
            "kind": GapKind.GRANT_REQUIRED.value,
            "proposition_ref": _normalize_ref("prop:delegated_authority"),
            "scope_ref": _normalize_ref("scope:powers"),
            "assessment_ref": ass_ref,
            "question_ref": q_ref,
            "dependency_refs": [case_ref],
            "resolution_route_kinds": RESOLUTION_ROUTES[GapKind.GRANT_REQUIRED.value],
            "materiality": Materiality.OUTCOME_CHANGE_WITNESSED.value,
            "witness_refs": [ass_ref],
            "actual_resolution_state": "open",
        })

    return gaps
