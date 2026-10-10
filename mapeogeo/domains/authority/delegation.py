"""Delegation Chains, Scope Attenuation, and Revocation Propagation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from experiments.authority_assessment.v0_1.intel_authority.delegation import (
    DelegationState,
    DelegationVerificationResult,
    DelegationVerifier as _DelegationVerifierImpl,
    verify_scope_attenuation as _verify_scope_attenuation_impl,
)


class DelegationChainEvaluator:
    """Evaluates delegation chains, scope attenuation, and revocations."""

    def __init__(self, grants: Optional[List[Dict[str, Any]]] = None) -> None:
        self.grants = grants or []
        self._verifier = _DelegationVerifierImpl(grants=self.grants)

    def verify_grant_chain(
        self,
        terminal_grant_ref: Dict[str, Any] | str,
        expected_actor_ref: Dict[str, Any] | str,
        expected_operation_ref: Dict[str, Any] | str,
    ) -> DelegationVerificationResult:
        """Traces and validates a delegation path from terminal grant up to originating root."""
        return self._verifier.verify_grant_chain(
            terminal_grant_ref=terminal_grant_ref,
            expected_actor_ref=expected_actor_ref,
            expected_operation_ref=expected_operation_ref,
        )

    def verify_scope_attenuation(
        self,
        parent_scope: Dict[str, Any],
        child_scope: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """Verifies that child scope strictly narrows or preserves parent scope."""
        return _verify_scope_attenuation_impl(parent_scope, child_scope)
