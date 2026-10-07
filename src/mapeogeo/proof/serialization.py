"""Deterministic Serialization for Proof Contracts, Certificates, and Audits."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mapeogeo.proof.audit import AdmissionAuditRecord, GenerationAuditRecord, ProofAudit
from mapeogeo.proof.contracts import (
    Evidence,
    NoveltyClassification,
    ProofCertificate,
    ProofClaim,
    ProofObligation,
    ProofStatus,
    canonical_json_bytes,
)
from mapeogeo.proof.replay import ReplayResult, ReplayStatus


def proof_claim_to_dict(claim: ProofClaim) -> dict[str, Any]:
    return {
        "claim_id": claim.claim_id,
        "subject": claim.subject,
        "predicate": claim.predicate,
        "source_id": claim.source_id,
        "target_id": claim.target_id,
        "source_identity_sha256": claim.source_identity_sha256,
        "target_identity_sha256": claim.target_identity_sha256,
        "claim_scope": claim.claim_scope,
        "metadata": dict(claim.metadata),
    }


def proof_claim_from_dict(data: Mapping[str, Any]) -> ProofClaim:
    return ProofClaim(
        claim_id=str(data["claim_id"]),
        subject=str(data["subject"]),
        predicate=str(data["predicate"]),
        source_id=str(data["source_id"]),
        target_id=str(data["target_id"]),
        source_identity_sha256=str(data["source_identity_sha256"]),
        target_identity_sha256=str(data["target_identity_sha256"]),
        claim_scope=str(data["claim_scope"]),
        metadata=dict(data.get("metadata", {})),
    )


def proof_obligation_to_dict(ob: ProofObligation) -> dict[str, Any]:
    return {
        "obligation_id": ob.obligation_id,
        "claim": proof_claim_to_dict(ob.claim),
        "premises": list(ob.premises),
        "status": ob.status,
        "deadline_steps": ob.deadline_steps,
        "metadata": dict(ob.metadata),
    }


def proof_obligation_from_dict(data: Mapping[str, Any]) -> ProofObligation:
    return ProofObligation(
        obligation_id=str(data["obligation_id"]),
        claim=proof_claim_from_dict(data["claim"]),
        premises=tuple(str(p) for p in data.get("premises", ())),
        status=str(data.get("status", "PENDING")),
        deadline_steps=data.get("deadline_steps"),
        metadata=dict(data.get("metadata", {})),
    )


def evidence_to_dict(ev: Evidence) -> dict[str, Any]:
    return {
        "evidence_id": ev.evidence_id,
        "evidence_type": ev.evidence_type,
        "verifier_id": ev.verifier_id,
        "payload": dict(ev.payload),
        "digest": ev.digest,
        "created_at_utc": ev.created_at_utc,
        "metadata": dict(ev.metadata),
    }


def evidence_from_dict(data: Mapping[str, Any]) -> Evidence:
    return Evidence(
        evidence_id=str(data["evidence_id"]),
        evidence_type=str(data["evidence_type"]),
        verifier_id=str(data["verifier_id"]),
        payload=dict(data.get("payload", {})),
        digest=str(data["digest"]),
        created_at_utc=str(data.get("created_at_utc", "")),
        metadata=dict(data.get("metadata", {})),
    )


def proof_certificate_to_dict(cert: ProofCertificate) -> dict[str, Any]:
    return {
        "certificate_id": cert.certificate_id,
        "claim": proof_claim_to_dict(cert.claim),
        "status": cert.status.value,
        "novelty": cert.novelty.value,
        "evidence": [evidence_to_dict(e) for e in cert.evidence],
        "verifier_id": cert.verifier_id,
        "verifier_semantic_id": cert.verifier_semantic_id,
        "hardware_coverage": dict(cert.hardware_coverage),
        "proof_payload_digest": cert.proof_payload_digest,
        "certificate_digest": cert.certificate_digest,
        "admitted": cert.admitted,
        "metadata": dict(cert.metadata),
    }


def proof_certificate_from_dict(data: Mapping[str, Any]) -> ProofCertificate:
    return ProofCertificate(
        certificate_id=str(data["certificate_id"]),
        claim=proof_claim_from_dict(data["claim"]),
        status=ProofStatus(str(data["status"])),
        novelty=NoveltyClassification(str(data["novelty"])),
        evidence=tuple(evidence_from_dict(e) for e in data.get("evidence", ())),
        verifier_id=str(data["verifier_id"]),
        verifier_semantic_id=str(data["verifier_semantic_id"]),
        hardware_coverage=dict(data.get("hardware_coverage", {})),
        proof_payload_digest=str(data.get("proof_payload_digest", "")),
        certificate_digest=str(data.get("certificate_digest", "")),
        admitted=bool(data.get("admitted", False)),
        metadata=dict(data.get("metadata", {})),
    )


def replay_result_to_dict(res: ReplayResult) -> dict[str, Any]:
    return {
        "status": res.status.value,
        "verifier_id": res.verifier_id,
        "proof_status": res.proof_status.value,
        "message": res.message,
        "steps_evaluated": res.steps_evaluated,
        "payload_digest": res.payload_digest,
        "replay_hash": res.replay_hash,
    }


def replay_result_from_dict(data: Mapping[str, Any]) -> ReplayResult:
    return ReplayResult(
        status=ReplayStatus(str(data["status"])),
        verifier_id=str(data["verifier_id"]),
        proof_status=ProofStatus(str(data["proof_status"])),
        message=str(data.get("message", "")),
        steps_evaluated=int(data.get("steps_evaluated", 0)),
        payload_digest=str(data.get("payload_digest", "")),
        replay_hash=str(data.get("replay_hash", "")),
    )


def proof_audit_to_dict(audit: ProofAudit) -> dict[str, Any]:
    out: dict[str, Any] = {
        "audit_id": audit.audit_id,
        "certificate_id": audit.certificate_id,
        "metadata": dict(audit.metadata),
    }
    if audit.generation_audit:
        out["generation_audit"] = {
            "generator_id": audit.generation_audit.generator_id,
            "trace_id": audit.generation_audit.trace_id,
            "steps_evaluated": audit.generation_audit.steps_evaluated,
            "pruned_branches": audit.generation_audit.pruned_branches,
            "cost_consumed": audit.generation_audit.cost_consumed,
            "generation_passed": audit.generation_audit.generation_passed,
            "timestamp_utc": audit.generation_audit.timestamp_utc,
            "metadata": dict(audit.generation_audit.metadata),
        }
    if audit.admission_audit:
        out["admission_audit"] = {
            "auditor_id": audit.admission_audit.auditor_id,
            "passed": audit.admission_audit.passed,
            "reasons": list(audit.admission_audit.reasons),
            "verified_claim_digest": audit.admission_audit.verified_claim_digest,
            "verified_certificate_digest": audit.admission_audit.verified_certificate_digest,
            "replay_result": (
                replay_result_to_dict(audit.admission_audit.replay_result)
                if audit.admission_audit.replay_result
                else None
            ),
            "admitted_at_utc": audit.admission_audit.admitted_at_utc,
            "metadata": dict(audit.admission_audit.metadata),
        }
    return out


def proof_audit_from_dict(data: Mapping[str, Any]) -> ProofAudit:
    gen_rec = None
    if "generation_audit" in data and data["generation_audit"]:
        g = data["generation_audit"]
        gen_rec = GenerationAuditRecord(
            generator_id=str(g["generator_id"]),
            trace_id=str(g["trace_id"]),
            steps_evaluated=int(g["steps_evaluated"]),
            pruned_branches=int(g["pruned_branches"]),
            cost_consumed=float(g["cost_consumed"]),
            generation_passed=bool(g["generation_passed"]),
            timestamp_utc=str(g["timestamp_utc"]),
            metadata=dict(g.get("metadata", {})),
        )

    adm_rec = None
    if "admission_audit" in data and data["admission_audit"]:
        a = data["admission_audit"]
        res = replay_result_from_dict(a["replay_result"]) if a.get("replay_result") else None
        adm_rec = AdmissionAuditRecord(
            auditor_id=str(a["auditor_id"]),
            passed=bool(a["passed"]),
            reasons=tuple(str(r) for r in a.get("reasons", ())),
            verified_claim_digest=str(a["verified_claim_digest"]),
            verified_certificate_digest=str(a["verified_certificate_digest"]),
            replay_result=res,
            admitted_at_utc=str(a.get("admitted_at_utc", "")),
            metadata=dict(a.get("metadata", {})),
        )

    return ProofAudit(
        audit_id=str(data["audit_id"]),
        certificate_id=str(data["certificate_id"]),
        generation_audit=gen_rec,
        admission_audit=adm_rec,
        metadata=dict(data.get("metadata", {})),
    )


def to_canonical_json_string(obj: Any) -> str:
    """Serialize object to deterministic canonical JSON string."""
    return canonical_json_bytes(obj).decode("utf-8")
