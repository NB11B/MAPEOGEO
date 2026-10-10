"""Delegation and Scope Attenuation Verifier for Task T04.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.analysis (graph traversal, dependency verification)
   - intel_uow.catalog (Record envelope, Reference)
2. Interface Reused:
   - Reference and TypedValue adapters (intel_authority.adapters)
   - ActionCase bindings (intel_authority.case_bindings)
   - ConditionVerifier (intel_authority.condition_verifier)
3. Additional Semantic Responsibility:
   - AQ10: Evaluates bounded delegation paths with established originating
     authority, issuer competence, explicit delegability, and scope attenuation
     on every edge.
   - AQ12: Organizational reachability or hierarchical subordination alone
     supplies NO legal delegation without a competent, unbroken grant chain.
   - Rejects delegation cycles, requires explicit delegability at intermediate hops,
     and enforces configurable depth budget (max 16 edges). Over-depth delegation
     path stays unresolved while independent valid routes can still be assessed.
4. Qualification Evidence Delta:
   - AQ10, AQ12 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    extract_typed_value,
    validate_authority_reference,
)
from experiments.authority_assessment.v0_1.intel_authority.condition_verifier import (
    ConditionVerifier,
    EvidenceState,
)


class DelegationState(str, Enum):
    ESTABLISHED = "established"
    UNRESOLVED = "unresolved"
    DEFEATED = "defeated"
    BUDGET_EXCEEDED = "budget_exceeded"
    INVALID_CHAIN = "invalid_chain"


@dataclass
class DelegationVerificationResult:
    state: DelegationState
    originating_grant_ref: Optional[Dict[str, Any]] = None
    terminal_grant_ref: Optional[Dict[str, Any]] = None
    hops_evaluated: int = 0
    attenuated_scope: Optional[Dict[str, Any]] = None
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    grant_refs: List[Dict[str, Any]] = field(default_factory=list)


def _ref_id(ref: Any) -> str:
    if isinstance(ref, dict):
        return str(ref.get("id", ""))
    return str(ref)


def verify_scope_attenuation(
    parent_scope: Dict[str, Any],
    child_scope: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Verifies that child scope strictly narrows or preserves parent scope.

    A delegation hop CANNOT expand:
    - operations
    - purposes
    - objects
    - recipients
    - jurisdictions
    - quantity limits (child limit must be <= parent limit)
    """
    errors: List[str] = []

    # Helper for set inclusions
    def check_subset(field_name: str) -> None:
        p_items = {_ref_id(x) for x in parent_scope.get(field_name, [])}
        c_items = {_ref_id(x) for x in child_scope.get(field_name, [])}
        if p_items and not c_items.issubset(p_items):
            expanded = sorted(list(c_items - p_items))
            errors.append(f"Delegation expansion on '{field_name}': child adds {expanded}")

    check_subset("operation_refs")
    check_subset("purpose_refs")
    check_subset("object_refs")
    check_subset("recipient_refs")
    check_subset("jurisdiction_refs")

    # Quantity limits check: child limit cannot exceed parent limit
    p_limits = parent_scope.get("quantity_limits", {})
    c_limits = child_scope.get("quantity_limits", {})
    for q_key, p_val in p_limits.items():
        if q_key in c_limits:
            c_val = c_limits[q_key]
            # extract values
            p_num = extract_typed_value(p_val) if isinstance(p_val, dict) and "type" in p_val else p_val
            c_num = extract_typed_value(c_val) if isinstance(c_val, dict) and "type" in c_val else c_val
            try:
                if Decimal(str(c_num)) > Decimal(str(p_num)):
                    errors.append(
                        f"Delegation expansion on quantity limit '{q_key}': child limit {c_num} > parent limit {p_num}"
                    )
            except Exception:
                errors.append(f"Cannot compare quantity limits for '{q_key}'")

    return len(errors) == 0, errors


class DelegationVerifier:
    """Verifies grant chains and bounded delegation paths."""

    def __init__(
        self,
        grants: List[Dict[str, Any]],
        verifier: Optional[ConditionVerifier] = None,
        max_depth: int = 16,
    ) -> None:
        self.grants_by_id: Dict[str, Dict[str, Any]] = {}
        for g in grants:
            ref_id = _ref_id(g.get("ref", {}))
            if ref_id:
                self.grants_by_id[ref_id] = g
        self.verifier = verifier or ConditionVerifier()
        self.max_depth = max_depth

    def verify_grant_chain(
        self,
        terminal_grant_ref: Dict[str, Any] | str,
        expected_actor_ref: Dict[str, Any] | str,
        expected_operation_ref: Dict[str, Any] | str,
    ) -> DelegationVerificationResult:
        """Traces and validates a delegation path from terminal grant up to originating root."""
        start_id = _ref_id(terminal_grant_ref)
        target_actor = _ref_id(expected_actor_ref)
        target_op = _ref_id(expected_operation_ref)

        if start_id not in self.grants_by_id:
            return DelegationVerificationResult(
                state=DelegationState.UNRESOLVED,
                diagnostics=[{"code": "MISSING_GRANT", "message": f"Grant '{start_id}' not found in registry"}],
            )

        terminal_grant = self.grants_by_id[start_id]

        # 1. Terminal grantee must match the executing actor
        grantee = _ref_id(terminal_grant.get("grantee_ref", {}))
        if grantee != target_actor:
            return DelegationVerificationResult(
                state=DelegationState.DEFEATED,
                diagnostics=[
                    {
                        "code": "GRANTEE_MISMATCH",
                        "message": f"Terminal grant grantee '{grantee}' does not match actor '{target_actor}'",
                    }
                ],
            )

        # 2. Trace chain up to root
        chain: List[Dict[str, Any]] = []
        visited: Set[str] = set()
        curr_id: Optional[str] = start_id

        while curr_id:
            if curr_id in visited:
                # Cycle detected
                return DelegationVerificationResult(
                    state=DelegationState.DEFEATED,
                    diagnostics=[
                        {
                            "code": "DELEGATION_CYCLE",
                            "message": f"Delegation cycle detected at grant '{curr_id}'",
                        }
                    ],
                )

            if len(chain) >= self.max_depth:
                return DelegationVerificationResult(
                    state=DelegationState.BUDGET_EXCEEDED,
                    hops_evaluated=len(chain),
                    diagnostics=[
                        {
                            "code": "MAX_DELEGATION_DEPTH_EXCEEDED",
                            "message": f"Delegation path exceeded maximum depth of {self.max_depth} edges",
                        }
                    ],
                )

            visited.add(curr_id)
            if curr_id not in self.grants_by_id:
                return DelegationVerificationResult(
                    state=DelegationState.UNRESOLVED,
                    hops_evaluated=len(chain),
                    diagnostics=[
                        {
                            "code": "BROKEN_GRANT_CHAIN",
                            "message": f"Parent grant '{curr_id}' is missing from snapshot",
                        }
                    ],
                )

            curr_grant = self.grants_by_id[curr_id]
            chain.append(curr_grant)

            # Check revocation facts
            revocations = curr_grant.get("revocation_fact_refs", [])
            for r_ref in revocations:
                r_id = _ref_id(r_ref)
                s, _ = self.verifier.evaluate_leaf_proposition(r_id, _ref_id(curr_grant.get("grantee_ref", {})))
                if s == EvidenceState.SUPPORTED:
                    return DelegationVerificationResult(
                        state=DelegationState.DEFEATED,
                        diagnostics=[
                            {
                                "code": "GRANT_REVOKED",
                                "message": f"Grant '{curr_id}' has been revoked by fact '{r_id}'",
                            }
                        ],
                    )

            # Check effectiveness condition
            eff_cond = curr_grant.get("effectiveness")
            if eff_cond:
                eff_state = self.verifier.evaluate_condition_expr(eff_cond)
                if eff_state == EvidenceState.REFUTED:
                    return DelegationVerificationResult(
                        state=DelegationState.DEFEATED,
                        diagnostics=[
                            {
                                "code": "GRANT_INEFFECTIVE",
                                "message": f"Grant '{curr_id}' effectiveness condition refuted",
                            }
                        ],
                    )
                elif eff_state in (EvidenceState.UNKNOWN, EvidenceState.CONFLICTING):
                    return DelegationVerificationResult(
                        state=DelegationState.UNRESOLVED,
                        diagnostics=[
                            {
                                "code": "GRANT_EFFECTIVENESS_UNRESOLVED",
                                "message": f"Grant '{curr_id}' effectiveness condition is {eff_state.value}",
                            }
                        ],
                    )

            parent_ref = curr_grant.get("parent_grant_ref")
            if parent_ref:
                p_id = _ref_id(parent_ref)
                # Next hop
                curr_id = p_id
            else:
                curr_id = None

        # Chain is [terminal, ..., root]
        root_grant = chain[-1]
        originating_grant = root_grant

        # 3. Check originating competence
        issuer_competence = root_grant.get("issuer_competence_rule_refs", [])
        if not issuer_competence:
            return DelegationVerificationResult(
                state=DelegationState.UNRESOLVED,
                diagnostics=[
                    {
                        "code": "MISSING_ORIGINATING_COMPETENCE",
                        "message": f"Root grant '{_ref_id(root_grant.get('ref'))}' lacks issuer competence rules",
                    }
                ],
            )

        # 4. Check redelegation permissions and scope attenuation along the chain (root to terminal)
        # root -> chain[-1], chain[-2], ..., chain[0]
        reversed_chain = list(reversed(chain))
        for i in range(len(reversed_chain) - 1):
            parent = reversed_chain[i]
            child = reversed_chain[i + 1]

            # Parent issuer must match child issuer
            # Child's issuer must be the parent's grantee
            p_grantee = _ref_id(parent.get("grantee_ref", {}))
            c_issuer = _ref_id(child.get("issuer_ref", {}))
            if p_grantee != c_issuer:
                return DelegationVerificationResult(
                    state=DelegationState.INVALID_CHAIN,
                    diagnostics=[
                        {
                            "code": "ISSUER_NOT_GRANTEE",
                            "message": f"Child grant issuer '{c_issuer}' is not parent grant grantee '{p_grantee}'",
                        }
                    ],
                )

            # Parent must allow redelegation
            if not parent.get("redelegation_allowed", False):
                return DelegationVerificationResult(
                    state=DelegationState.DEFEATED,
                    diagnostics=[
                        {
                            "code": "REDELEGATION_PROHIBITED",
                            "message": f"Grant '{_ref_id(parent.get('ref'))}' does not allow redelegation",
                        }
                    ],
                )

            # Check eligible delegate list if specified
            p_scope = parent.get("scope", {})
            eligible_delegates = {_ref_id(x) for x in p_scope.get("eligible_delegate_refs", [])}
            c_grantee = _ref_id(child.get("grantee_ref", {}))
            if eligible_delegates and c_grantee not in eligible_delegates:
                return DelegationVerificationResult(
                    state=DelegationState.DEFEATED,
                    diagnostics=[
                        {
                            "code": "INELIGIBLE_DELEGATE",
                            "message": f"Child grantee '{c_grantee}' is not an eligible delegate of parent grant",
                        }
                    ],
                )

            # Check scope attenuation
            c_scope = child.get("scope", {})
            attenuated, att_errors = verify_scope_attenuation(p_scope, c_scope)
            if not attenuated:
                return DelegationVerificationResult(
                    state=DelegationState.DEFEATED,
                    diagnostics=[
                        {
                            "code": "SCOPE_EXPANSION",
                            "message": f"Scope expansion from '{_ref_id(parent.get('ref'))}' to '{_ref_id(child.get('ref'))}': {'; '.join(att_errors)}",
                        }
                    ],
                )

        # 5. Finally, verify that the operation is contained in terminal scope
        terminal_ops = {_ref_id(x) for x in terminal_grant.get("scope", {}).get("operation_refs", [])}
        if terminal_ops and target_op not in terminal_ops:
            return DelegationVerificationResult(
                state=DelegationState.DEFEATED,
                diagnostics=[
                    {
                        "code": "OPERATION_NOT_DELEGATED",
                        "message": f"Target operation '{target_op}' not in terminal grant scope {terminal_ops}",
                    }
                ],
            )

        return DelegationVerificationResult(
            state=DelegationState.ESTABLISHED,
            originating_grant_ref=originating_grant.get("ref"),
            terminal_grant_ref=terminal_grant.get("ref"),
            hops_evaluated=len(chain) - 1,
            attenuated_scope=terminal_grant.get("scope"),
            grant_refs=[g.get("ref") for g in chain],
        )
