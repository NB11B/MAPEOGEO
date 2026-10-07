"""Historical Regression and Audit Replay Tests for Proof Subsystem.

Replays:
1. Historical Post-Hardening Proof Replay Gap:
   Envelope-only PASS certificates without replayable payloads must be rejected.
2. Historical Final Mathematical Replay Gap (Closed):
   Digest-consistent payloads that are mathematically false (e.g. True == False)
   must be independently replayed and rejected.
3. Endpoint Mutation Invariance:
   Tampering with endpoint node attributes invalidates the certificate.
4. Producer Authentication:
   Spoofed producer repository or malformed commit SHA is rejected.
5. Authoritative Relation Binding:
   Verifiers cannot be reused for non-authoritative relation types.
6. Real De Morgan Round-Trip:
   Sound propositional equivalence proof payload is verified and ingested.
"""

from __future__ import annotations

from typing import Any

import pytest

from mapeogeo.proof import (
    GFYProofBridgeError,
    apply_gfyproof_certificate,
    canonical_sha256,
    claim_contract_digest,
    node_identity_sha256,
)

COMMIT = "a" * 40


def _build_nodes() -> tuple[dict[str, Any], dict[str, Any]]:
    source = {
        "id": "src:audit:logic:a",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "1" * 64},
    }
    target = {
        "id": "src:audit:logic:b",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "2" * 64},
    }
    return source, target


def _envelope_only_cert(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)
    scope = "audit: envelope only with no replayable proof payload"
    body = {
        "schema": "mapeogeo.gfyproof.edge-certificate.v2",
        "edge_id": "edge:audit:envelope-only",
        "edge_type": "SAME_SEMANTICS",
        "source_id": source["id"],
        "target_id": target["id"],
        "source_identity_sha256": source_hash,
        "target_identity_sha256": target_hash,
        "claim_scope": scope,
        "claim_contract_digest": claim_contract_digest(
            edge_type="SAME_SEMANTICS",
            source_id=source["id"],
            target_id=target["id"],
            source_identity_sha256=source_hash,
            target_identity_sha256=target_hash,
            claim_scope=scope,
        ),
        "verifier_semantic_id": "GFY.ROBDD_EQUIVALENCE.v1",
        "verifier_scope": "finite Boolean expressions over one fixed finite variable order",
        "implementation_provenance": {
            "experiment_id": "AUDIT_ONLY",
            "class": "not-a-replayed-proof",
        },
        "hardware_coverage": {
            "status": "HARDWARE_NOT_BOUND",
            "contract_id": "",
            "scope": "",
        },
        "proof_payload_digest": "2" * 64,
        "proof_verdict": "PASS",
        "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": "",
        "producer": {
            "repository": "NB11B/GFYProof",
            "commit": COMMIT,
            "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        },
    }
    cert = dict(body)
    cert["certificate_digest"] = canonical_sha256(
        body, domain="gfyproof-mapeogeo-semantic-edge-certificate-v2"
    )
    return cert


def _false_robdd_cert(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)
    scope = "audit false Boolean equivalence with digest-consistent payload"
    payload = {
        "left": ["const", True],
        "right": ["const", False],
        "variable_order": [],
    }
    proof_digest = canonical_sha256(payload, domain="gfyproof-mapeogeo-semantic-proof-payload-v2")
    body = {
        "schema": "mapeogeo.gfyproof.edge-certificate.v2",
        "edge_id": "edge:audit:false-robdd",
        "edge_type": "SAME_SEMANTICS",
        "source_id": source["id"],
        "target_id": target["id"],
        "source_identity_sha256": source_hash,
        "target_identity_sha256": target_hash,
        "claim_scope": scope,
        "claim_contract_digest": claim_contract_digest(
            edge_type="SAME_SEMANTICS",
            source_id=source["id"],
            target_id=target["id"],
            source_identity_sha256=source_hash,
            target_identity_sha256=target_hash,
            claim_scope=scope,
        ),
        "verifier_semantic_id": "GFY.ROBDD_EQUIVALENCE.v1",
        "verifier_scope": "finite Boolean expressions over one fixed finite variable order",
        "implementation_provenance": {
            "experiment_id": "AUDIT_FALSE_PROOF",
            "class": "audit.false",
        },
        "hardware_coverage": {
            "status": "HARDWARE_NOT_BOUND",
            "contract_id": "",
            "scope": "",
        },
        "proof_payload_digest": proof_digest,
        "proof_payload": payload,
        "proof_verdict": "PASS",
        "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": "",
        "producer": {
            "repository": "NB11B/GFYProof",
            "commit": COMMIT,
            "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        },
    }
    cert = dict(body)
    cert["certificate_digest"] = canonical_sha256(
        body, domain="gfyproof-mapeogeo-semantic-edge-certificate-v2"
    )
    return cert


def _sound_demorgan_cert(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)
    scope = "sound De Morgan equivalence"
    payload = {
        "left": ["not", ["and", "A", "B"]],
        "right": ["or", ["not", "A"], ["not", "B"]],
        "variable_order": ["A", "B"],
    }
    proof_digest = canonical_sha256(payload, domain="gfyproof-mapeogeo-semantic-proof-payload-v2")
    body = {
        "schema": "mapeogeo.gfyproof.edge-certificate.v2",
        "edge_id": "edge:audit:demorgan",
        "edge_type": "SAME_SEMANTICS",
        "source_id": source["id"],
        "target_id": target["id"],
        "source_identity_sha256": source_hash,
        "target_identity_sha256": target_hash,
        "claim_scope": scope,
        "claim_contract_digest": claim_contract_digest(
            edge_type="SAME_SEMANTICS",
            source_id=source["id"],
            target_id=target["id"],
            source_identity_sha256=source_hash,
            target_identity_sha256=target_hash,
            claim_scope=scope,
        ),
        "verifier_semantic_id": "GFY.ROBDD_EQUIVALENCE.v1",
        "verifier_scope": "finite Boolean expressions over one fixed finite variable order",
        "implementation_provenance": {
            "experiment_id": "EXP_SOUND_LOGIC",
            "class": "logic.propositional",
        },
        "hardware_coverage": {
            "status": "HARDWARE_NOT_BOUND",
            "contract_id": "",
            "scope": "",
        },
        "proof_payload_digest": proof_digest,
        "proof_payload": payload,
        "proof_verdict": "PASS",
        "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": "",
        "producer": {
            "repository": "NB11B/GFYProof",
            "commit": COMMIT,
            "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        },
    }
    cert = dict(body)
    cert["certificate_digest"] = canonical_sha256(
        body, domain="gfyproof-mapeogeo-semantic-edge-certificate-v2"
    )
    return cert


def test_envelope_only_pass_is_strictly_rejected() -> None:
    """Historical Gap Replay: Envelope-only certificate lacks proof payload."""
    source, target = _build_nodes()
    graph: dict[str, Any] = {"nodes": [source, target], "edges": []}
    registry: dict[str, Any] = {}

    with pytest.raises(GFYProofBridgeError, match="Replayable proof payload required"):
        apply_gfyproof_certificate(graph, registry, _envelope_only_cert(source, target))

    assert graph["edges"] == []
    assert registry == {}


def test_digest_consistent_false_robdd_payload_is_rejected() -> None:
    """Historical Gap Closed: Digest-consistent false payload must be rejected by replay."""
    source, target = _build_nodes()
    graph: dict[str, Any] = {"nodes": [source, target], "edges": []}
    registry: dict[str, Any] = {}

    with pytest.raises(GFYProofBridgeError, match="Independent proof replay rejected"):
        apply_gfyproof_certificate(graph, registry, _false_robdd_cert(source, target))

    assert graph["edges"] == []
    assert registry == {}


def test_endpoint_mutation_invalidates_semantic_certificate() -> None:
    source, target = _build_nodes()
    cert = _sound_demorgan_cert(source, target)

    # Mutate target
    mutated_target = dict(target)
    mutated_target["attributes"] = {"statement_sha256": "9" * 64}
    graph: dict[str, Any] = {"nodes": [source, mutated_target], "edges": []}
    registry: dict[str, Any] = {}

    with pytest.raises(GFYProofBridgeError, match="target endpoint identity changed"):
        apply_gfyproof_certificate(graph, registry, cert)


def test_spoofed_repository_is_rejected() -> None:
    source, target = _build_nodes()
    cert = _sound_demorgan_cert(source, target)
    cert["producer"]["repository"] = "attacker/repo"
    # Recompute digest
    body = dict(cert)
    body.pop("certificate_digest")
    cert["certificate_digest"] = canonical_sha256(
        body, domain="gfyproof-mapeogeo-semantic-edge-certificate-v2"
    )

    graph: dict[str, Any] = {"nodes": [source, target], "edges": []}
    registry: dict[str, Any] = {}

    with pytest.raises(GFYProofBridgeError, match="trusted GFYProof repository"):
        apply_gfyproof_certificate(graph, registry, cert)


def test_semantic_verifier_cannot_be_reused_for_wrong_relation() -> None:
    source, target = _build_nodes()
    cert = _sound_demorgan_cert(source, target)
    # ROBDD equivalence verifier is NOT authoritative for UPWARD_FOUNDATION_DEPENDENCY
    cert["edge_type"] = "UPWARD_FOUNDATION_DEPENDENCY"
    body = dict(cert)
    body.pop("certificate_digest")
    cert["certificate_digest"] = canonical_sha256(
        body, domain="gfyproof-mapeogeo-semantic-edge-certificate-v2"
    )

    graph: dict[str, Any] = {"nodes": [source, target], "edges": []}
    registry: dict[str, Any] = {}

    with pytest.raises(GFYProofBridgeError, match="not authoritative for this edge type"):
        apply_gfyproof_certificate(graph, registry, cert)


def test_sound_demorgan_proof_roundtrip_accepted() -> None:
    """Sound verification test: valid payload is replayed and admitted."""
    source, target = _build_nodes()
    graph: dict[str, Any] = {"nodes": [source, target], "edges": []}
    registry: dict[str, Any] = {}

    cert = _sound_demorgan_cert(source, target)
    evidence_digest = apply_gfyproof_certificate(graph, registry, cert)

    assert evidence_digest in registry
    assert len(graph["edges"]) == 2  # Claim edge + Evidence attachment edge
    claim_edge = next(e for e in graph["edges"] if e["id"] == "edge:audit:demorgan")
    assert claim_edge["attributes"]["evidence_status"] == "VERIFIED"
    assert claim_edge["attributes"]["relation_status"] == "VERIFIED"
