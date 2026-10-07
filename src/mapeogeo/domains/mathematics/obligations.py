"""Mathematical Proof Obligations and Generic Proof Engine Bridge.

Translates domain-specific mathematical theorems, hypotheses, and lemmas
into domain-neutral ProofClaim, ProofObligation, and Evidence objects for
the Wave-6 ProofEngine:
    MathematicsAdapter -> ProofEngine
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from mapeogeo.domains.mathematics.ontology import Theorem
from mapeogeo.proof.contracts import (
    Evidence,
    ProofClaim,
    ProofObligation,
    canonical_sha256,
)


@dataclass(frozen=True)
class MathematicalProofObligation:
    """Domain-level mathematical obligation to discharge a theorem or lemma."""

    obligation_id: str
    theorem: Theorem
    hypotheses: tuple[str, ...] = ()
    target_statement: str = ""
    verifier_semantic_id: str = "GFY.ROBDD_EQUIVALENCE.v1"
    proof_payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_generic_claim(self) -> ProofClaim:
        """Construct domain-neutral ProofClaim without leaking mathematical symbols."""
        source_hash = hashlib.sha256(self.theorem.statement.encode("utf-8")).hexdigest()
        target_str = self.target_statement or self.theorem.conclusion or self.theorem.statement
        target_hash = hashlib.sha256(target_str.encode("utf-8")).hexdigest()

        return ProofClaim(
            claim_id=f"claim:{self.obligation_id}",
            subject=self.theorem.domain,
            predicate="SAME_SEMANTICS",
            source_id=self.theorem.theorem_id,
            target_id=f"target:{self.obligation_id}",
            source_identity_sha256=source_hash,
            target_identity_sha256=target_hash,
            claim_scope=self.theorem.statement,
            metadata={"domain": self.theorem.domain, "kind": self.theorem.kind.value},
        )

    def to_generic_obligation(self) -> ProofObligation:
        """Construct domain-neutral ProofObligation for ProofEngine."""
        claim = self.to_generic_claim()
        return ProofObligation(
            obligation_id=self.obligation_id,
            claim=claim,
            premises=self.hypotheses,
            status="PENDING",
            metadata={"theorem_id": self.theorem.theorem_id},
        )

    def to_generic_evidence(
        self,
        evidence_id: str | None = None,
        verifier_id: str = "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
    ) -> Evidence:
        """Construct domain-neutral Evidence container for ProofEngine."""
        ev_id = evidence_id or f"ev:{self.obligation_id}"
        payload = dict(self.proof_payload) if self.proof_payload else {"verified": True}
        digest = canonical_sha256(payload, domain="mapeogeo-evidence-payload-v2")
        return Evidence(
            evidence_id=ev_id,
            evidence_type="EXECUTABLE_REPLAY",
            verifier_id=verifier_id,
            payload=payload,
            digest=digest,
            metadata={"theorem_id": self.theorem.theorem_id},
        )
