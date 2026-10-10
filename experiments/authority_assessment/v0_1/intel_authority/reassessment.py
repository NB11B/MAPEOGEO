"""Reassessment Change Detection and Historical Pinning for Task T08.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.analysis (dependency tracking, cache invalidation)
   - intel_uow.catalog (Record envelope, Reference, Diagnostic)
2. Interface Reused:
   - Reference and TypedValue adapters (intel_authority.adapters)
   - LegalAssessment (intel_authority.evaluator)
3. Additional Semantic Responsibility:
   - AQ21: Pinned assessments preserve original source/rule digest; successor
     arrival does not overwrite prior assessment.
   - AQ30: Incompatible positive reuse is prevented when material dependencies change.
   - AQ43: Historical assessments remain replayable and recoverable.
   - AQ44: Revocation affects successor use without rewriting historical records.
   - find_reassessment evaluates dependency changes and newly relevant sources.
4. Qualification Evidence Delta:
   - AQ21, AQ30, AQ43, AQ44 qualification assertions.
================================================================================
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Set

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    validate_authority_reference,
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


def find_reassessment(
    prior_assessment: Dict[str, Any],
    current_context: Dict[str, Any],
    new_candidates: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Determines whether a prior assessment must be reassessed under current context (AQ21, AQ30, AQ44)."""
    prior_ref = _normalize_ref(prior_assessment.get("ref", "assessment:prior"))
    prior_ctx_digest = prior_assessment.get("context_digest")
    current_ctx_digest = _canonical_digest(current_context)

    changed_refs: List[Dict[str, Any]] = []
    newly_relevant_refs: List[Dict[str, Any]] = []
    reasons: List[Dict[str, Any]] = []

    # 1. Context digest check
    if prior_ctx_digest and prior_ctx_digest != current_ctx_digest:
        reasons.append({
            "code": "CONTEXT_DIGEST_CHANGED",
            "message": f"Context digest changed from '{prior_ctx_digest[:8]}' to '{current_ctx_digest[:8]}'",
            "severity": "info",
        })

    # 2. Check pinned dependency rules
    prior_dep_refs = {_ref_id(r) for r in prior_assessment.get("dependency_refs", [])}
    current_pack_rules: Dict[str, Dict[str, Any]] = {}
    for pack in current_context.get("packs", []):
        for r in pack.get("rules", []):
            r_id = _ref_id(r.get("ref"))
            current_pack_rules[r_id] = r

    for dep_id in prior_dep_refs:
        if dep_id in current_pack_rules:
            curr_rule = current_pack_rules[dep_id]
            # Check if rule was modified or revoked
            if curr_rule.get("revoked", False):
                changed_refs.append(_normalize_ref(dep_id))
                reasons.append({
                    "code": "DEPENDENCY_RULE_REVOKED",
                    "message": f"Pinned dependency rule '{dep_id}' has been revoked",
                    "severity": "warning",
                })
        else:
            changed_refs.append(_normalize_ref(dep_id))
            reasons.append({
                "code": "DEPENDENCY_RULE_MISSING",
                "message": f"Pinned dependency rule '{dep_id}' is no longer present in current context",
                "severity": "warning",
            })

    # 3. Check newly relevant candidates
    if new_candidates:
        for cand in new_candidates:
            newly_relevant_refs.append(_normalize_ref(cand))
            reasons.append({
                "code": "NEW_CANDIDATE_ARRIVED",
                "message": f"New candidate source or rule '{_ref_id(cand)}' arrived",
                "severity": "info",
            })

    reassessment_required = bool(changed_refs or newly_relevant_refs or (prior_ctx_digest and prior_ctx_digest != current_ctx_digest))

    return {
        "required": reassessment_required,
        "changed_refs": changed_refs,
        "newly_relevant_refs": newly_relevant_refs,
        "prior_assessment_ref": prior_ref,
        "reasons": reasons,
    }
