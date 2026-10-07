"""Formal Proof Verification and Engine Subsystem.

Provides:
- ProofEngine: Orchestrator for obligations, independent replay verification,
  dual-audit accounting, and certified graph admission.
- Fail-closed admission gates enforcing policy, integrity, and replay checks.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping, MutableMapping
from typing import Any

from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node, NodeKind, NodeRole
from mapeogeo.graph.relation import RelationType
from mapeogeo.proof.audit import AdmissionAuditRecord, ProofAudit
from mapeogeo.proof.contracts import (
    CertificationPolicy,
    Evidence,
    NoveltyClassification,
    ProofCertificate,
    ProofObligation,
    ProofStatus,
)
from mapeogeo.proof.replay import (
    ProofReplayRegistry,
    ReplayResult,
)


class ProofVerifierError(ValueError):
    """Raised when proof verification or admission fails."""


class ProofEngine:
    """Canonical proof engine orchestrating discharge, replay, and admission."""

    def __init__(
        self,
        registry: ProofReplayRegistry | None = None,
        default_policy: CertificationPolicy | None = None,
    ) -> None:
        self.registry = registry or ProofReplayRegistry()
        self.default_policy = default_policy or CertificationPolicy()

    def discharge_obligation(
        self,
        obligation: ProofObligation,
        evidence: Evidence,
        verifier_semantic_id: str,
        novelty: NoveltyClassification = NoveltyClassification.UNCLASSIFIED,
        hardware_coverage: Mapping[str, Any] | None = None,
        policy: CertificationPolicy | None = None,
    ) -> tuple[ProofCertificate, ProofAudit]:
        """Discharge an open proof obligation with verified evidence."""
        active_policy = policy or self.default_policy

        # Replay independent verifier on payload
        replay_res: ReplayResult = self.registry.replay(
            verifier_semantic_id=verifier_semantic_id,
            claim=obligation.claim,
            payload=evidence.payload,
        )

        now_str = datetime.datetime.now(datetime.UTC).isoformat()
        reasons: list[str] = []

        if not replay_res.passed:
            reasons.append(f"Replay rejected: {replay_res.message}")
            status = replay_res.proof_status
            admitted = False
        else:
            status = replay_res.proof_status
            admitted = True

        if active_policy.disallow_gaps and status == ProofStatus.PROOF_GAP:
            reasons.append("Proof gaps disallowed by policy")
            admitted = False

        if active_policy.disallow_unverified and not status.is_sound:
            reasons.append(f"Unsound proof status '{status.value}' disallowed")
            admitted = False

        cert_id = f"cert:{obligation.claim.claim_id}:{evidence.evidence_id[:16]}"
        cert = ProofCertificate(
            certificate_id=cert_id,
            claim=obligation.claim,
            status=status,
            novelty=novelty,
            evidence=(evidence,),
            verifier_id=evidence.verifier_id,
            verifier_semantic_id=verifier_semantic_id,
            hardware_coverage=dict(hardware_coverage or {}),
            proof_payload_digest=evidence.digest,
            admitted=admitted,
        )

        # Seal the certificate
        sealed_digest = cert.compute_certificate_digest()
        sealed_cert = ProofCertificate(
            certificate_id=cert.certificate_id,
            claim=cert.claim,
            status=cert.status,
            novelty=cert.novelty,
            evidence=cert.evidence,
            verifier_id=cert.verifier_id,
            verifier_semantic_id=cert.verifier_semantic_id,
            hardware_coverage=cert.hardware_coverage,
            proof_payload_digest=cert.proof_payload_digest,
            certificate_digest=sealed_digest,
            admitted=cert.admitted,
            metadata=cert.metadata,
        )

        # Admission Audit
        audit_rec = AdmissionAuditRecord(
            auditor_id="mapeogeo.proof.ProofEngine",
            passed=admitted,
            reasons=tuple(reasons) if reasons else ("Independent replay verified",),
            verified_claim_digest=obligation.claim.compute_claim_digest(),
            verified_certificate_digest=sealed_digest,
            replay_result=replay_res,
            admitted_at_utc=now_str if admitted else "",
        )

        audit = ProofAudit(
            audit_id=f"audit:{cert_id}",
            certificate_id=cert_id,
            admission_audit=audit_rec,
        )

        return sealed_cert, audit

    def admit_to_graph(
        self,
        certificate: ProofCertificate,
        graph: DecisionGraph,
        edge_evidence_registry: MutableMapping[str, Any] | None = None,
    ) -> str:
        """Admit a certified proof claim into the decision graph substrate."""
        if not certificate.admitted or not certificate.verify_seal():
            raise ProofVerifierError("cannot admit uncertified or unsealed certificate")

        claim = certificate.claim

        # Verify endpoint presence
        if graph.get_node(claim.source_id) is None:
            raise ProofVerifierError(f"source endpoint '{claim.source_id}' missing in graph")
        if graph.get_node(claim.target_id) is None:
            raise ProofVerifierError(f"target endpoint '{claim.target_id}' missing in graph")

        evidence_node_id = f"evidence:proof:{certificate.certificate_digest[:24]}"
        evidence_node = Node(
            node_id=evidence_node_id,
            kind=NodeKind.GUARD,
            role=NodeRole.ATOMIC_JUDGMENT,
            metadata={
                "proof_kind": "PROOF_EVIDENCE",
                "verifier_id": certificate.verifier_id,
                "verifier_semantic_id": certificate.verifier_semantic_id,
                "certificate_digest": certificate.certificate_digest,
                "proof_status": certificate.status.value,
                "novelty": certificate.novelty.value,
            },
        )

        # Map relation
        rel_str = claim.predicate.upper()
        try:
            rel = RelationType[rel_str]
        except KeyError:
            rel = RelationType.REPRESENTS

        claim_edge = Edge(
            source_id=claim.source_id,
            target_id=claim.target_id,
            relation=rel,
            contract=EdgeContract(
                contract_id=f"c:{claim.claim_id}",
                required_relation=rel,
                is_certified=True,
                certificate_id=certificate.certificate_id,
            ),
            metadata={
                "evidence_digest": certificate.proof_payload_digest,
                "certificate_digest": certificate.certificate_digest,
                "proof_status": certificate.status.value,
            },
        )

        evidence_edge = Edge(
            source_id=evidence_node_id,
            target_id=claim.target_id,
            relation=RelationType.REPRESENTS,
            contract=EdgeContract(
                contract_id=f"c:ev:{certificate.certificate_id}",
                required_relation=RelationType.REPRESENTS,
                is_certified=True,
                certificate_id=certificate.certificate_id,
            ),
            metadata={"certificate_digest": certificate.certificate_digest},
        )

        # Execute atomic graph mutation
        tx = graph.begin_transaction()
        tx.add_node(evidence_node)
        tx.add_edge(claim_edge)
        tx.add_edge(evidence_edge)

        try:
            cert = tx.validate()
            snapshot = tx.commit(cert)
            graph.apply_snapshot(snapshot)
        except Exception as exc:
            raise ProofVerifierError(f"graph transaction commit failed: {exc}") from exc

        if edge_evidence_registry is not None:
            edge_evidence_registry[certificate.proof_payload_digest] = {
                "claim_id": claim.claim_id,
                "certificate_digest": certificate.certificate_digest,
                "verifier_id": certificate.verifier_id,
            }

        return certificate.certificate_digest
