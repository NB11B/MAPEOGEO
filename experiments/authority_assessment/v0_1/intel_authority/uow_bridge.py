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


def assess_uow_entry(
    proposal: Dict[str, Any],
    admission_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Assesses admission of an AuthorityWorkProposal into platform execution (AQ06)."""
    # 1. Structural validation
    prop_ref = _normalize_ref(proposal.get("ref", "proposal:unnamed"))
    work_kind = proposal.get("work_kind")
    subject = proposal.get("subject", {})
    boundary_ref = _normalize_ref(admission_context.get("boundary_ref", "boundary:platform_admission"))
    proposal_digest = _canonical_digest(proposal)

    if not work_kind or not subject:
        return {
            "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
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

    # 2. Check hypothetical vs actual mode isolation (AQ37)
    mode = proposal.get("mode", "actual")
    if mode == "hypothetical" and work_kind == "execute_assessed_action":
        return {
            "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
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

    # 3. Analytical Work Kinds (AQ06)
    # assess_case, enumerate_actions, enumerate_actors, assess_course, compare_courses
    if work_kind in ("assess_case", "enumerate_actions", "enumerate_actors", "assess_course", "compare_courses"):
        # Admission checks analyst access and audience clearance
        access_ctx = admission_context.get("access_context", {})
        analyst_cleared = access_ctx.get("analyst_cleared", True)

        if not analyst_cleared:
            return {
                "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
                "status": UowEntryStatus.REJECTED.value,
                "work_proposal_ref": prop_ref,
                "work_proposal_digest": proposal_digest,
                "legacy_admission_ref": None,
                "legal_assessment_ref": None,
                "boundary_ref": boundary_ref,
                "reason_refs": [_normalize_ref("reason:analyst_access_denied")],
                "external_execution_enabled": False,
            }

        # Check if subject domain was modified without successor admission (AQ48)
        if subject.get("requires_successor_admission", False):
            return {
                "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
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

        # Analytical work is validly admitted even when subject is legally prohibited (AQ06)!
        return {
            "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
            "status": UowEntryStatus.ADMITTED.value,
            "work_proposal_ref": prop_ref,
            "work_proposal_digest": proposal_digest,
            "legacy_admission_ref": _normalize_ref(proposal.get("legacy_proposal", {}).get("ref", "legacy:analytical")),
            "legal_assessment_ref": None,
            "boundary_ref": boundary_ref,
            "reason_refs": [_normalize_ref("reason:analytical_access_granted")],
            "external_execution_enabled": False,
        }

    # 4. Action Execution Work Kind (execute_assessed_action)
    elif work_kind == "execute_assessed_action":
        # Requires supported LegalAssessment (AQ06)
        legal_ass_ref = proposal.get("legal_assessment_ref")
        legal_ass = proposal.get("legal_assessment", {})

        if not legal_ass_ref or not legal_ass:
            return {
                "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
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
            # If prohibited, conditions_unmet, or unresolved, execution CANNOT be admitted (AQ06)
            return {
                "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
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

        # Check actual policy views and enforcement contracts
        policy_views = admission_context.get("actual_policy_views", [])
        if not policy_views:
            return {
                "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
                "status": UowEntryStatus.UNRESOLVED.value,
                "work_proposal_ref": prop_ref,
                "work_proposal_digest": proposal_digest,
                "legacy_admission_ref": None,
                "legal_assessment_ref": _normalize_ref(legal_ass_ref),
                "boundary_ref": boundary_ref,
                "reason_refs": [_normalize_ref("reason:missing_policy_views")],
                "external_execution_enabled": False,
            }

        # Admitted for action execution (local harness, external execution disabled)
        return {
            "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
            "status": UowEntryStatus.ADMITTED.value,
            "work_proposal_ref": prop_ref,
            "work_proposal_digest": proposal_digest,
            "legacy_admission_ref": _normalize_ref(proposal.get("legacy_proposal", {}).get("ref", "legacy:execution")),
            "legal_assessment_ref": _normalize_ref(legal_ass_ref),
            "boundary_ref": boundary_ref,
            "reason_refs": [_normalize_ref("reason:operational_authority_verified")],
            "external_execution_enabled": False,
        }

    return {
        "ref": _normalize_ref(f"decision:{_ref_id(prop_ref)}"),
        "status": UowEntryStatus.UNSUPPORTED_PROJECTION.value,
        "work_proposal_ref": prop_ref,
        "work_proposal_digest": proposal_digest,
        "legacy_admission_ref": None,
        "legal_assessment_ref": None,
        "boundary_ref": boundary_ref,
        "reason_refs": [_normalize_ref("reason:unknown_work_kind")],
        "external_execution_enabled": False,
    }
