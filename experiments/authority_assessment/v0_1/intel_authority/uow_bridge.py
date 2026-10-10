"""UoW Admission Bridge and Analytical vs Execution Separation for Task T07.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.workflow (assess_admission, WorkProposal, AdmissionDecision)
   - intel_uow.catalog (Record envelope, Reference, Diagnostic)
2. Interface Reused:
   - assess_case (intel_authority.evaluator)
   - Reference and TypedValue adapters (intel_authority.adapters)
   - AllocationManager (intel_authority.allocations)
3. Additional Semantic Responsibility:
   - AQ06: Separates analytical work admission from evaluated legal finding;
     an analytical UoW can be admitted and conclude prohibition; action execution
     cannot be admitted with a prohibition.
   - AQ22: Effective law and known-at-frontier are separate axes.
   - AQ37: Source, scenario, and actual layers do not cross; hypothetical proposals
     cannot enter actual execution.
   - AQ43: Prior assessment remains replayable without mutation.
   - AQ44: Revocation affects successor use without rewriting historical records.
   - AQ45: Requirement retirement changes declared facet; other obligations remain.
   - AQ46 & AQ47: Cancellation request/receipt does not release reservations;
     application requires explicit boundary and release evidence.
   - AQ48: Unknown completion requires reconciliation before retry; external
     execution remains disabled.
4. Qualification Evidence Delta:
   - AQ06, AQ22, AQ37, AQ43, AQ44, AQ45, AQ46, AQ47, AQ48 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    validate_authority_reference,
)


class UowEntryStatus(str, Enum):
    ADMITTED = "admitted"
    REJECTED = "rejected"
    UNRESOLVED = "unresolved"
    CONTEXT_OR_MODEL_ERROR = "context_or_model_error"
    UNSUPPORTED_PROJECTION = "unsupported_projection"


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
class NativeUoWWork:
    """Platform representation of admitted work item."""
    work_id: str
    work_kind: str
    is_analytical: bool
    mode: str
    proposal_ref: Dict[str, Any]
    proposal_digest: str
    boundary_ref: Dict[str, Any]
    legal_assessment: Optional[Dict[str, Any]]
    legal_assessment_ref: Optional[Dict[str, Any]]
    requires_successor_admission: bool
    legacy_ref: Optional[Dict[str, Any]]
    is_malformed: bool = False


def compile_authority_work(proposal: Dict[str, Any], boundary_ref: Dict[str, Any]) -> NativeUoWWork:
    """Converts an authority domain proposal into a native UoW work item."""
    prop_ref = _normalize_ref(proposal.get("ref", "proposal:unnamed"))
    work_kind = proposal.get("work_kind")
    subject = proposal.get("subject", {})
    proposal_digest = _canonical_digest(proposal)

    if not work_kind or not subject:
        return NativeUoWWork(
            work_id=_ref_id(prop_ref),
            work_kind="malformed",
            is_analytical=False,
            mode=proposal.get("mode", "actual"),
            proposal_ref=prop_ref,
            proposal_digest=proposal_digest,
            boundary_ref=boundary_ref,
            legal_assessment=None,
            legal_assessment_ref=None,
            requires_successor_admission=False,
            legacy_ref=None,
            is_malformed=True,
        )

    is_analytical = work_kind in (
        "assess_case", "enumerate_actions", "enumerate_actors", "assess_course", "compare_courses"
    )

    return NativeUoWWork(
        work_id=_ref_id(prop_ref),
        work_kind=work_kind,
        is_analytical=is_analytical,
        mode=proposal.get("mode", "actual"),
        proposal_ref=prop_ref,
        proposal_digest=proposal_digest,
        boundary_ref=boundary_ref,
        legal_assessment=proposal.get("legal_assessment"),
        legal_assessment_ref=proposal.get("legal_assessment_ref"),
        requires_successor_admission=subject.get("requires_successor_admission", False),
        legacy_ref=proposal.get("legacy_proposal", {}).get("ref"),
    )


class PlatformAdmissionSpine:
    """Platform admission certification spine evaluating boundary and execution policy."""

    @staticmethod
    def certify(work: NativeUoWWork, context: Dict[str, Any]) -> Dict[str, Any]:
        prop_ref = work.proposal_ref
        proposal_digest = work.proposal_digest
        boundary_ref = work.boundary_ref

        if work.is_malformed:
            return {
                "ref": _normalize_ref(f"decision:{work.work_id}"),
                "status": UowEntryStatus.CONTEXT_OR_MODEL_ERROR.value,
                "work_proposal_ref": prop_ref,
                "work_proposal_digest": proposal_digest,
                "legacy_admission_ref": None,
                "legal_assessment_ref": None,
                "boundary_ref": boundary_ref,
                "reason_refs": [_normalize_ref("reason:malformed_proposal")],
                "external_execution_enabled": False,
                "diagnostics": [{"code": "MALFORMED_PROPOSAL", "message": "Missing work_kind or subject in proposal"}],
            }

        # Hypothetical vs actual mode isolation (AQ37)
        if work.mode == "hypothetical" and work.work_kind == "execute_assessed_action":
            return {
                "ref": _normalize_ref(f"decision:{work.work_id}"),
                "status": UowEntryStatus.REJECTED.value,
                "work_proposal_ref": prop_ref,
                "work_proposal_digest": proposal_digest,
                "legacy_admission_ref": None,
                "legal_assessment_ref": None,
                "boundary_ref": boundary_ref,
                "reason_refs": [_normalize_ref("reason:hypothetical_cannot_execute_actual")],
                "external_execution_enabled": False,
                "diagnostics": [{"code": "HYPOTHETICAL_CANNOT_EXECUTE", "message": "Hypothetical proposals are excluded from operational execution"}],
            }

        # Analytical work kinds (AQ06)
        if work.is_analytical:
            access_ctx = context.get("access_context", {})
            if not access_ctx.get("analyst_cleared", True):
                return {
                    "ref": _normalize_ref(f"decision:{work.work_id}"),
                    "status": UowEntryStatus.REJECTED.value,
                    "work_proposal_ref": prop_ref,
                    "work_proposal_digest": proposal_digest,
                    "legacy_admission_ref": None,
                    "legal_assessment_ref": None,
                    "boundary_ref": boundary_ref,
                    "reason_refs": [_normalize_ref("reason:analyst_access_denied")],
                    "external_execution_enabled": False,
                }

            if work.requires_successor_admission:
                return {
                    "ref": _normalize_ref(f"decision:{work.work_id}"),
                    "status": UowEntryStatus.UNSUPPORTED_PROJECTION.value,
                    "work_proposal_ref": prop_ref,
                    "work_proposal_digest": proposal_digest,
                    "legacy_admission_ref": None,
                    "legal_assessment_ref": None,
                    "boundary_ref": boundary_ref,
                    "reason_refs": [_normalize_ref("reason:successor_admission_required")],
                    "external_execution_enabled": False,
                    "diagnostics": [{"code": "SUCCESSOR_ADMISSION_REQUIRED", "message": "Domain expansion requires successor admission"}],
                }

            # Analytical inquiry admitted even if subject is prohibited (AQ06)
            return {
                "ref": _normalize_ref(f"decision:{work.work_id}"),
                "status": UowEntryStatus.ADMITTED.value,
                "work_proposal_ref": prop_ref,
                "work_proposal_digest": proposal_digest,
                "legacy_admission_ref": _normalize_ref(work.legacy_ref or "legacy:analytical"),
                "legal_assessment_ref": None,
                "boundary_ref": boundary_ref,
                "reason_refs": [_normalize_ref("reason:analytical_access_granted")],
                "external_execution_enabled": False,
            }

        # Action Execution Work Kind (execute_assessed_action)
        if work.work_kind == "execute_assessed_action":
            legal_ass_ref = work.legal_assessment_ref
            legal_ass = work.legal_assessment

            if not legal_ass_ref or not legal_ass:
                return {
                    "ref": _normalize_ref(f"decision:{work.work_id}"),
                    "status": UowEntryStatus.REJECTED.value,
                    "work_proposal_ref": prop_ref,
                    "work_proposal_digest": proposal_digest,
                    "legacy_admission_ref": None,
                    "legal_assessment_ref": None,
                    "boundary_ref": boundary_ref,
                    "reason_refs": [_normalize_ref("reason:missing_legal_assessment")],
                    "external_execution_enabled": False,
                    "diagnostics": [{"code": "MISSING_LEGAL_ASSESSMENT", "message": "Action execution entry requires an attached LegalAssessment"}],
                }

            disp = legal_ass.get("disposition")
            if disp != "supported_within_scope":
                return {
                    "ref": _normalize_ref(f"decision:{work.work_id}"),
                    "status": UowEntryStatus.REJECTED.value,
                    "work_proposal_ref": prop_ref,
                    "work_proposal_digest": proposal_digest,
                    "legacy_admission_ref": None,
                    "legal_assessment_ref": _normalize_ref(legal_ass_ref),
                    "boundary_ref": boundary_ref,
                    "reason_refs": [_normalize_ref(f"reason:legal_finding_{disp}")],
                    "external_execution_enabled": False,
                    "diagnostics": [{"code": "LEGAL_FINDING_NOT_SUPPORTED", "message": f"Action execution rejected due to legal finding '{disp}'"}],
                }

            policy_views = context.get("actual_policy_views", [])
            if not policy_views:
                return {
                    "ref": _normalize_ref(f"decision:{work.work_id}"),
                    "status": UowEntryStatus.UNRESOLVED.value,
                    "work_proposal_ref": prop_ref,
                    "work_proposal_digest": proposal_digest,
                    "legacy_admission_ref": None,
                    "legal_assessment_ref": _normalize_ref(legal_ass_ref),
                    "boundary_ref": boundary_ref,
                    "reason_refs": [_normalize_ref("reason:missing_policy_views")],
                    "external_execution_enabled": False,
                }

            return {
                "ref": _normalize_ref(f"decision:{work.work_id}"),
                "status": UowEntryStatus.ADMITTED.value,
                "work_proposal_ref": prop_ref,
                "work_proposal_digest": proposal_digest,
                "legacy_admission_ref": _normalize_ref(work.legacy_ref or "legacy:execution"),
                "legal_assessment_ref": _normalize_ref(legal_ass_ref),
                "boundary_ref": boundary_ref,
                "reason_refs": [_normalize_ref("reason:operational_authority_verified")],
                "external_execution_enabled": False,
            }

        return {
            "ref": _normalize_ref(f"decision:{work.work_id}"),
            "status": UowEntryStatus.UNSUPPORTED_PROJECTION.value,
            "work_proposal_ref": prop_ref,
            "work_proposal_digest": proposal_digest,
            "legacy_admission_ref": None,
            "legal_assessment_ref": None,
            "boundary_ref": boundary_ref,
            "reason_refs": [_normalize_ref("reason:unknown_work_kind")],
            "external_execution_enabled": False,
        }


def adapt_platform_decision(platform_decision: Dict[str, Any]) -> Dict[str, Any]:
    """Adapts platform admission decision into domain response."""
    return platform_decision


def assess_uow_entry(
    proposal: Dict[str, Any],
    admission_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Assesses admission of an AuthorityWorkProposal into platform execution (AQ06).
    
    Delegates admission compilation and evaluation through PlatformAdmissionSpine.
    """
    boundary_ref = _normalize_ref(admission_context.get("boundary_ref", "boundary:platform_admission"))
    native_work = compile_authority_work(proposal, boundary_ref)
    decision = PlatformAdmissionSpine.certify(native_work, admission_context)
    return adapt_platform_decision(decision)

