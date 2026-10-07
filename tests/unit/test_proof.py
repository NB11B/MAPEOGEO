"""Unit Tests for Proof and Certification Engine Subsystem.

Tests:
1. Proof contracts, claims, obligations, and cryptographic certificate sealing.
2. Distinct proof statuses and novelty classification.
3. The core architectural invariant: generation audit != admission audit.
4. Independent Boolean / ROBDD proof replay with counterexample discovery.
5. Independent Farkas linear implication proof replay.
6. ProofEngine discharge and atomic admission to DecisionGraph.
7. Proof serialization round-trip.
"""

from __future__ import annotations

from typing import Any

from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.node import Node, NodeKind, NodeRole
from mapeogeo.proof import (
    AdmissionAuditRecord,
    BooleanROBDDReplayer,
    Evidence,
    FarkasImplicationReplayer,
    GenerationAuditRecord,
    NoveltyClassification,
    ProofAudit,
    ProofCertificate,
    ProofClaim,
    ProofEngine,
    ProofObligation,
    ProofStatus,
    ReplayResult,
    ReplayStatus,
    proof_audit_from_dict,
    proof_audit_to_dict,
    proof_certificate_from_dict,
    proof_certificate_to_dict,
    proof_claim_from_dict,
    proof_claim_to_dict,
    proof_obligation_from_dict,
    proof_obligation_to_dict,
)


def _sample_claim() -> ProofClaim:
    return ProofClaim(
        claim_id="claim:logic:demorgan:01",
        subject="logic.propositional",
        predicate="SAME_SEMANTICS",
        source_id="src:prop:demorgan_lhs",
        target_id="src:prop:demorgan_rhs",
        source_identity_sha256="a" * 64,
        target_identity_sha256="b" * 64,
        claim_scope="propositional Boolean logic over finite variables",
    )


def test_proof_contracts_and_sealing() -> None:
    claim = _sample_claim()
    claim_digest = claim.compute_claim_digest()
    assert len(claim_digest) == 64

    evidence = Evidence.create(
        evidence_id="ev:01",
        evidence_type="EXECUTABLE_REPLAY",
        verifier_id="GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        payload={"left": "A", "right": "A"},
    )
    assert len(evidence.digest) == 64

    cert = ProofCertificate(
        certificate_id="cert:test:01",
        claim=claim,
        status=ProofStatus.FORMALLY_CHECKED,
        novelty=NoveltyClassification.CANONICAL_SYNONYM,
        evidence=(evidence,),
        verifier_id=evidence.verifier_id,
        verifier_semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        proof_payload_digest=evidence.digest,
        admitted=True,
    )
    # Unsealed certificate should fail verify_seal
    assert not cert.verify_seal()

    sealed_digest = cert.compute_certificate_digest()
    sealed_cert = ProofCertificate(
        certificate_id=cert.certificate_id,
        claim=cert.claim,
        status=cert.status,
        novelty=cert.novelty,
        evidence=cert.evidence,
        verifier_id=cert.verifier_id,
        verifier_semantic_id=cert.verifier_semantic_id,
        proof_payload_digest=cert.proof_payload_digest,
        certificate_digest=sealed_digest,
        admitted=True,
    )
    assert sealed_cert.verify_seal()


def test_proof_status_and_novelty_properties() -> None:
    assert ProofStatus.PROVEN_IN_SOURCE.is_sound
    assert ProofStatus.DERIVED_FROM_PROVEN_RESULTS.is_sound
    assert ProofStatus.NOVEL_PROOF_COMPLETE.is_sound
    assert ProofStatus.FORMALLY_CHECKED.is_sound
    assert not ProofStatus.PROOF_GAP.is_sound
    assert not ProofStatus.COUNTEREXAMPLE.is_sound
    assert not ProofStatus.FALSE_AS_STATED.is_sound

    assert ProofStatus.COUNTEREXAMPLE.is_refutation
    assert ProofStatus.FALSE_AS_STATED.is_refutation
    assert not ProofStatus.NOVEL_PROOF_COMPLETE.is_refutation


def test_generation_audit_differs_from_admission_audit() -> None:
    """Core Architectural Invariant:

    generation audit != admission audit. Passing generation search audit
    never implies admission into the certified substrate.
    """
    gen_audit = GenerationAuditRecord(
        generator_id="search_engine_heuristic_v1",
        trace_id="trace:999",
        steps_evaluated=450,
        pruned_branches=32,
        cost_consumed=1.85,
        generation_passed=True,
        timestamp_utc="2026-10-07T12:00:00Z",
    )

    # 1. Audit with only generation audit passed
    audit_unadmitted = ProofAudit(
        audit_id="audit:01",
        certificate_id="cert:test:01",
        generation_audit=gen_audit,
        admission_audit=None,
    )
    assert not audit_unadmitted.is_fully_certified

    # 2. Audit with generation passed, but admission audit failed
    adm_failed = AdmissionAuditRecord(
        auditor_id="mapeogeo.proof.ProofEngine",
        passed=False,
        reasons=("Mathematical proof replay failed",),
        verified_claim_digest="a" * 64,
        verified_certificate_digest="b" * 64,
        replay_result=None,
        admitted_at_utc="",
    )
    audit_rejected = ProofAudit(
        audit_id="audit:02",
        certificate_id="cert:test:01",
        generation_audit=gen_audit,
        admission_audit=adm_failed,
    )
    assert not audit_rejected.is_fully_certified

    # 3. Audit with passing admission audit
    adm_passed = AdmissionAuditRecord(
        auditor_id="mapeogeo.proof.ProofEngine",
        passed=True,
        reasons=("Independent replay verified",),
        verified_claim_digest="a" * 64,
        verified_certificate_digest="b" * 64,
        replay_result=None,
        admitted_at_utc="2026-10-07T12:05:00Z",
    )
    audit_certified = ProofAudit(
        audit_id="audit:03",
        certificate_id="cert:test:01",
        generation_audit=gen_audit,
        admission_audit=adm_passed,
    )
    assert audit_certified.is_fully_certified


def test_boolean_robdd_replayer_verified() -> None:
    claim = _sample_claim()
    replayer = BooleanROBDDReplayer()

    # De Morgan's Law: not (A and B) <=> (not A) or (not B)
    payload = {
        "left": ["not", ["and", "A", "B"]],
        "right": ["or", ["not", "A"], ["not", "B"]],
        "variable_order": ["A", "B"],
    }
    result = replayer.replay(claim, payload)
    assert result.passed
    assert result.status == ReplayStatus.VERIFIED
    assert result.proof_status == ProofStatus.FORMALLY_CHECKED
    assert result.steps_evaluated == 4


def test_boolean_robdd_replayer_counterexample() -> None:
    claim = _sample_claim()
    replayer = BooleanROBDDReplayer()

    # False statement: True <=> False
    payload = {
        "left": ["const", True],
        "right": ["const", False],
        "variable_order": [],
    }
    result = replayer.replay(claim, payload)
    assert not result.passed
    assert result.status == ReplayStatus.REJECTED
    assert result.proof_status == ProofStatus.COUNTEREXAMPLE
    assert "Equivalence disproven" in result.message


def test_farkas_implication_replayer_verified() -> None:
    claim = _sample_claim()
    replayer = FarkasImplicationReplayer()

    # System:
    # row 0: -x1 <= 0  (x1 >= 0)
    # row 1: -x2 <= 0  (x2 >= 0)
    # row 2: x1 + x2 <= 1
    # Goal: x1 + 2*x2 <= 2
    # Combination with multipliers [0, 0, 2]:
    # 2*(x1 + x2) = 2*x1 + 2*x2 <= 2.
    # Target coefficients are [1, 2].
    # But for an exact Farkas equality: y^T A = c^T.
    # Let matrix be [[1, 0], [0, 1]], bounds [1, 2], target [1, 2], target_bound 3.
    # multipliers [1, 2]: 1*[1, 0] + 2*[0, 1] = [1, 2], bound: 1*1 + 2*2 = 5 <= 5.
    payload = {
        "matrix": [[1.0, 0.0], [0.0, 1.0]],
        "bounds": [1.0, 2.0],
        "target_coefficients": [1.0, 2.0],
        "target_bound": 5.0,
        "multipliers": [1.0, 2.0],
    }
    result = replayer.replay(claim, payload)
    assert result.passed
    assert result.status == ReplayStatus.VERIFIED
    assert result.proof_status == ProofStatus.FORMALLY_CHECKED


def test_farkas_implication_replayer_counterexample() -> None:
    claim = _sample_claim()
    replayer = FarkasImplicationReplayer()

    # Invalid multipliers exceeding target bound
    payload = {
        "matrix": [[1.0, 0.0], [0.0, 1.0]],
        "bounds": [10.0, 20.0],
        "target_coefficients": [1.0, 2.0],
        "target_bound": 5.0,
        "multipliers": [1.0, 2.0],
    }
    result = replayer.replay(claim, payload)
    assert not result.passed
    assert result.status == ReplayStatus.REJECTED
    assert result.proof_status == ProofStatus.COUNTEREXAMPLE


def test_proof_engine_discharge_and_graph_admission() -> None:
    engine = ProofEngine()
    claim = _sample_claim()
    obligation = ProofObligation(
        obligation_id="ob:01",
        claim=claim,
    )
    evidence = Evidence.create(
        evidence_id="ev:01",
        evidence_type="EXECUTABLE_REPLAY",
        verifier_id="GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        payload={
            "left": ["xor", "A", "B"],
            "right": ["and", ["or", "A", "B"], ["not", ["and", "A", "B"]]],
            "variable_order": ["A", "B"],
        },
    )

    cert, audit = engine.discharge_obligation(
        obligation,
        evidence,
        verifier_semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        novelty=NoveltyClassification.INDEPENDENT_DISCOVERY,
    )
    assert cert.admitted
    assert cert.status == ProofStatus.FORMALLY_CHECKED
    assert cert.verify_seal()
    assert audit.is_fully_certified

    # Set up decision graph substrate
    graph = DecisionGraph("g:proof_test")
    tx = graph.begin_transaction()
    tx.add_node(Node(claim.source_id, kind=NodeKind.QUERY, role=NodeRole.PASS_THROUGH))
    tx.add_node(Node(claim.target_id, kind=NodeKind.QUERY, role=NodeRole.PASS_THROUGH))
    cert_tx = tx.validate()
    graph.apply_snapshot(tx.commit(cert_tx))

    registry: dict[str, Any] = {}
    seal = engine.admit_to_graph(cert, graph, edge_evidence_registry=registry)
    assert seal == cert.certificate_digest
    assert len(graph.edges) == 2
    assert (claim.source_id, claim.target_id) in [(e.source_id, e.target_id) for e in graph.edges]
    assert evidence.digest in registry


def test_proof_serialization_roundtrip() -> None:
    claim = _sample_claim()
    ob = ProofObligation(obligation_id="ob:ser", claim=claim, premises=("p1", "p2"))
    ev = Evidence.create("ev:ser", "TEST_TYPE", "v_id", {"key": "val"})
    cert = ProofCertificate(
        certificate_id="cert:ser",
        claim=claim,
        status=ProofStatus.PROVEN_IN_SOURCE,
        novelty=NoveltyClassification.KNOWN_REPRESENTATION,
        evidence=(ev,),
        verifier_id="v_id",
        verifier_semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        proof_payload_digest=ev.digest,
        admitted=True,
    )
    sealed_cert = ProofCertificate(
        certificate_id=cert.certificate_id,
        claim=cert.claim,
        status=cert.status,
        novelty=cert.novelty,
        evidence=cert.evidence,
        verifier_id=cert.verifier_id,
        verifier_semantic_id=cert.verifier_semantic_id,
        proof_payload_digest=cert.proof_payload_digest,
        certificate_digest=cert.compute_certificate_digest(),
        admitted=True,
    )

    # Claim roundtrip
    claim_dict = proof_claim_to_dict(claim)
    assert proof_claim_from_dict(claim_dict) == claim

    # Obligation roundtrip
    ob_dict = proof_obligation_to_dict(ob)
    assert proof_obligation_from_dict(ob_dict) == ob

    # Certificate roundtrip
    cert_dict = proof_certificate_to_dict(sealed_cert)
    restored_cert = proof_certificate_from_dict(cert_dict)
    assert restored_cert == sealed_cert
    assert restored_cert.verify_seal()

    # Audit roundtrip
    adm_rec = AdmissionAuditRecord(
        auditor_id="engine",
        passed=True,
        reasons=("All tests passed",),
        verified_claim_digest=claim.compute_claim_digest(),
        verified_certificate_digest=sealed_cert.certificate_digest,
        replay_result=ReplayResult(
            status=ReplayStatus.VERIFIED,
            verifier_id="v_id",
            proof_status=ProofStatus.PROVEN_IN_SOURCE,
            message="OK",
        ),
        admitted_at_utc="2026-10-07T12:00:00Z",
    )
    audit = ProofAudit(
        audit_id="audit:ser",
        certificate_id=sealed_cert.certificate_id,
        admission_audit=adm_rec,
    )
    audit_dict = proof_audit_to_dict(audit)
    restored_audit = proof_audit_from_dict(audit_dict)
    assert restored_audit.audit_id == audit.audit_id
    assert restored_audit.is_fully_certified
