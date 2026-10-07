"""Proof and Certification Engine Subsystem.

Provides formal obligation handling, independent proof replay, cryptographic
certificate verification, dual-audit accounting, and fail-closed admission.
"""

from __future__ import annotations

from mapeogeo.proof.audit import (
    AdmissionAuditRecord,
    GenerationAuditRecord,
    ProofAudit,
)
from mapeogeo.proof.bridge import (
    GFYProofBridgeError,
    apply_gfyproof_certificate,
    bound_edge_evidence_sha256,
    claim_contract_digest,
    gfyproof_edge_contract_digest,
    materialize_gfyproof_edge,
    node_identity_sha256,
    validate_gfyproof_certificate,
)
from mapeogeo.proof.contracts import (
    CertificationPolicy,
    Evidence,
    NoveltyClassification,
    ProofCertificate,
    ProofClaim,
    ProofObligation,
    ProofStatus,
    canonical_json_bytes,
    canonical_sha256,
)
from mapeogeo.proof.replay import (
    BooleanROBDDReplayer,
    FarkasImplicationReplayer,
    ProofReplayer,
    ProofReplayRegistry,
    ReplayResult,
    ReplayStatus,
    TautologyDFAEqualityReplayer,
)
from mapeogeo.proof.serialization import (
    evidence_from_dict,
    evidence_to_dict,
    proof_audit_from_dict,
    proof_audit_to_dict,
    proof_certificate_from_dict,
    proof_certificate_to_dict,
    proof_claim_from_dict,
    proof_claim_to_dict,
    proof_obligation_from_dict,
    proof_obligation_to_dict,
    replay_result_from_dict,
    replay_result_to_dict,
)
from mapeogeo.proof.verifier import ProofEngine, ProofVerifierError

__all__ = [
    "AdmissionAuditRecord",
    "BooleanROBDDReplayer",
    "CertificationPolicy",
    "Evidence",
    "FarkasImplicationReplayer",
    "GFYProofBridgeError",
    "GenerationAuditRecord",
    "NoveltyClassification",
    "ProofAudit",
    "ProofCertificate",
    "ProofClaim",
    "ProofEngine",
    "ProofObligation",
    "ProofReplayRegistry",
    "ProofReplayer",
    "ProofStatus",
    "ProofVerifierError",
    "ReplayResult",
    "ReplayStatus",
    "TautologyDFAEqualityReplayer",
    "apply_gfyproof_certificate",
    "bound_edge_evidence_sha256",
    "canonical_json_bytes",
    "canonical_sha256",
    "claim_contract_digest",
    "evidence_from_dict",
    "evidence_to_dict",
    "gfyproof_edge_contract_digest",
    "materialize_gfyproof_edge",
    "node_identity_sha256",
    "proof_audit_from_dict",
    "proof_audit_to_dict",
    "proof_certificate_from_dict",
    "proof_certificate_to_dict",
    "proof_claim_from_dict",
    "proof_claim_to_dict",
    "proof_obligation_from_dict",
    "proof_obligation_to_dict",
    "replay_result_from_dict",
    "replay_result_to_dict",
    "validate_gfyproof_certificate",
]
