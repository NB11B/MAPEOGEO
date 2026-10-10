"""Delegation Chains, Scope Attenuation, and Revocation Propagation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from experiments.authority_assessment.v0_1.intel_authority.delegation import (
    DelegationVerifier as _DelegationVerifierImpl,
)


class DelegationChainEvaluator:
    """Evaluates delegation chains, scope attenuation, and revocations."""

    def __init__(self, grants: Optional[List[Dict[str, Any]]] = None) -> None:
        self._verifier = _DelegationVerifierImpl(grants=grants)

    def verify_delegation(
        self,
        principal_id: str,
        delegate_id: str,
        operation: str,
        scope: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Verifies if delegate_id possesses valid delegated authority from principal_id."""
        return self._verifier.verify(principal_id, delegate_id, operation, scope)
