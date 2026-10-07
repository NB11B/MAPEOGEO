"""Formal Proof Contracts, Claims, Obligations, and Certificates.

Canonical proof representations for the UoW architecture:
- ProofClaim: Domain-neutral formal claim subject to proof verification.
- ProofObligation: Explicit discharge requirement for open goals or lemmas.
- Evidence: Verifiable cryptographic evidence backing a claim.
- ProofCertificate: Immutable cryptographic container binding claim, verifier,
  payload digest, and proof status.
- CertificationPolicy: Configurable fail-closed admission policy.
- ProofStatus: Fine-grained status enum distinguishing source-grounded,
  derived, novel, checked, gap, and refuted claims.
- NoveltyClassification: Independent categorization of epistemic novelty.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """Deterministic JSON serialization in UTF-8."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any, *, domain: str) -> str:
    """Domain-separated SHA-256 digest of canonical JSON bytes."""
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + canonical_json_bytes(value)).hexdigest()


class ProofStatus(StrEnum):
    """Fine-grained proof status distinguishing grounding and proof closure."""

    PROVEN_IN_SOURCE = "PROVEN_IN_SOURCE"
    DERIVED_FROM_PROVEN_RESULTS = "DERIVED_FROM_PROVEN_RESULTS"
    NOVEL_PROOF_COMPLETE = "NOVEL_PROOF_COMPLETE"
    FORMALLY_CHECKED = "FORMALLY_CHECKED"
    PROOF_GAP = "PROOF_GAP"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    FALSE_AS_STATED = "FALSE_AS_STATED"

    @property
    def is_sound(self) -> bool:
        """True if the status represents a valid, closed proof."""
        return self in {
            ProofStatus.PROVEN_IN_SOURCE,
            ProofStatus.DERIVED_FROM_PROVEN_RESULTS,
            ProofStatus.NOVEL_PROOF_COMPLETE,
            ProofStatus.FORMALLY_CHECKED,
        }

    @property
    def is_refutation(self) -> bool:
        """True if the status represents a refuted claim."""
        return self in {ProofStatus.COUNTEREXAMPLE, ProofStatus.FALSE_AS_STATED}


class NoveltyClassification(StrEnum):
    """Independent classification of novelty separate from verification."""

    KNOWN_REPRESENTATION = "KNOWN_REPRESENTATION"
    CANONICAL_SYNONYM = "CANONICAL_SYNONYM"
    INDEPENDENT_DISCOVERY = "INDEPENDENT_DISCOVERY"
    CROSS_DOMAIN_ANALOGY = "CROSS_DOMAIN_ANALOGY"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(frozen=True)
class ProofClaim:
    """Formal claim subject to verification."""

    claim_id: str
    subject: str
    predicate: str
    source_id: str
    target_id: str
    source_identity_sha256: str
    target_identity_sha256: str
    claim_scope: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def compute_claim_digest(self) -> str:
        """Compute domain-separated cryptographic digest of the claim."""
        body = {
            "claim_id": self.claim_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_identity_sha256": self.source_identity_sha256,
            "target_identity_sha256": self.target_identity_sha256,
            "claim_scope": self.claim_scope,
        }
        return canonical_sha256(body, domain="mapeogeo-proof-claim-v2")


@dataclass(frozen=True)
class ProofObligation:
    """Explicit discharge requirement for an unproved claim or goal."""

    obligation_id: str
    claim: ProofClaim
    premises: tuple[str, ...] = ()
    status: str = "PENDING"
    deadline_steps: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    """Verifiable structured evidence supporting a claim."""

    evidence_id: str
    evidence_type: str
    verifier_id: str
    payload: Mapping[str, Any]
    digest: str
    created_at_utc: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        evidence_id: str,
        evidence_type: str,
        verifier_id: str,
        payload: Mapping[str, Any],
        created_at_utc: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> Evidence:
        digest = canonical_sha256(payload, domain="mapeogeo-evidence-payload-v2")
        return cls(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            verifier_id=verifier_id,
            payload=payload,
            digest=digest,
            created_at_utc=created_at_utc,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class ProofCertificate:
    """Immutable cryptographic container binding claim, verifier, payload, and status."""

    certificate_id: str
    claim: ProofClaim
    status: ProofStatus
    novelty: NoveltyClassification
    evidence: tuple[Evidence, ...]
    verifier_id: str
    verifier_semantic_id: str
    hardware_coverage: Mapping[str, Any] = field(default_factory=dict)
    proof_payload_digest: str = ""
    certificate_digest: str = ""
    admitted: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def compute_certificate_digest(self) -> str:
        """Compute deterministic digest of the certificate envelope."""
        body = {
            "certificate_id": self.certificate_id,
            "claim_digest": self.claim.compute_claim_digest(),
            "status": self.status.value,
            "novelty": self.novelty.value,
            "evidence_digests": [e.digest for e in self.evidence],
            "verifier_id": self.verifier_id,
            "verifier_semantic_id": self.verifier_semantic_id,
            "hardware_coverage": dict(self.hardware_coverage),
            "proof_payload_digest": self.proof_payload_digest,
            "admitted": self.admitted,
        }
        return canonical_sha256(body, domain="mapeogeo-proof-certificate-v2")

    def verify_seal(self) -> bool:
        """Verify that certificate_digest matches internal state."""
        if not self.certificate_digest:
            return False
        return self.certificate_digest == self.compute_certificate_digest()


@dataclass(frozen=True)
class CertificationPolicy:
    """Configurable fail-closed policy for proof admission."""

    policy_id: str = "default_strict"
    required_verifiers: tuple[str, ...] = ()
    require_payload: bool = True
    require_endpoint_binding: bool = True
    disallow_unverified: bool = True
    disallow_gaps: bool = True
    max_replay_steps: int = 10000
    allowed_edge_types: frozenset[str] = frozenset(
        {
            "REPRESENTS",
            "SAME_SEMANTICS",
            "UPWARD_FOUNDATION_DEPENDENCY",
            "PROOF_DEPENDENCY",
            "CANDIDATE_EO",
            "CANDIDATE_GEO",
        }
    )
