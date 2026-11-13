"""Fail-closed regression coverage for the former envelope-only ingest gap.

Hashes authenticate neither a producer nor a theorem: even a self-consistent
PASS envelope must carry a replayable mathematical witness. These tests use
real replay, not a stand-in verifier.
"""
from __future__ import annotations

import copy
import sys

import pytest

from mapeogeo.gfyproof_bridge import (
    GFYProofBridgeError,
    apply_gfyproof_certificate,
    canonical_sha256,
    claim_contract_digest,
    materialize_gfyproof_edge,
)
from scripts.compute_foundation_depth import node_identity_sha256

PAYLOAD_DOMAIN = "gfyproof-mapeogeo-semantic-proof-payload-v2"
CERTIFICATE_DOMAIN = "gfyproof-mapeogeo-semantic-edge-certificate-v2"


def _seal(certificate: dict) -> dict:
    body = {k: v for k, v in certificate.items() if k != "certificate_digest"}
    return {**body, "certificate_digest": canonical_sha256(body, domain=CERTIFICATE_DOMAIN)}


def _case() -> tuple[dict, dict]:
    source = {"id": "source", "type": "SOURCE_DECLARATION", "attributes": {"statement_sha256": "1" * 64}}
    target = {"id": "target", "type": "CANONICAL_OBJECT", "attributes": {}}
    graph = {"nodes": [source, target], "edges": []}
    payload = {"left": ["not", ["and", ["var", "p"], ["var", "q"]]],
               "right": ["or", ["not", ["var", "p"]], ["not", ["var", "q"]]],
               "variable_order": ["p", "q"]}
    cert = {"schema": "mapeogeo.gfyproof.edge-certificate.v2", "edge_id": "claim",
            "edge_type": "REPRESENTS", "source_id": "source", "target_id": "target",
            "source_identity_sha256": node_identity_sha256(source),
            "target_identity_sha256": node_identity_sha256(target),
            "claim_scope": "De Morgan over all Boolean assignments",
            "verifier_semantic_id": "GFY.ROBDD_EQUIVALENCE.v1", "verifier_scope": "finite Boolean equivalence",
            "implementation_provenance": {"experiment_id": "audit"},
            "hardware_coverage": {"status": "HARDWARE_NOT_BOUND"},
            "proof_payload": payload, "proof_payload_digest": canonical_sha256(payload, domain=PAYLOAD_DOMAIN),
            "proof_verdict": "PASS", "promotion_class": "PROOF_ELIGIBLE",
            "producer": {"repository": "NB11B/GFYProof", "commit": "a" * 40,
                         "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2"}}
    return graph, _rebind(graph, cert)


def _rebind(graph: dict, cert: dict) -> dict:
    source, target = graph["nodes"][:2]
    cert["source_identity_sha256"] = node_identity_sha256(source)
    cert["target_identity_sha256"] = node_identity_sha256(target)
    cert["claim_contract_digest"] = claim_contract_digest(**{
        key: cert[key] for key in ("edge_type", "source_id", "target_id",
                                  "source_identity_sha256", "target_identity_sha256", "claim_scope")})
    return _seal(cert)


def _rejects_without_mutation(graph: dict, cert: dict, match: str, **kwargs) -> None:
    before = copy.deepcopy(graph)
    registry = {}
    with pytest.raises(GFYProofBridgeError, match=match):
        apply_gfyproof_certificate(graph, registry, cert, **kwargs)
    assert graph == before
    assert registry == {}


def test_self_consistent_false_proof_is_rejected() -> None:
    graph, cert = _case()
    cert["proof_payload"]["right"] = ["var", "p"]
    cert["proof_payload_digest"] = canonical_sha256(cert["proof_payload"], domain=PAYLOAD_DOMAIN)
    _rejects_without_mutation(graph, _seal(cert), "mathematical verification failed")


@pytest.mark.parametrize("payload", [None, {}, [], "PASS"])
def test_pass_envelope_requires_replayable_payload(payload) -> None:
    graph, cert = _case()
    cert["proof_payload"] = payload
    _rejects_without_mutation(graph, _seal(cert), "Replayable proof payload required")


def test_payload_digest_mismatch_is_rejected() -> None:
    graph, cert = _case()
    cert["proof_payload"]["right"] = ["var", "p"]
    _rejects_without_mutation(graph, _seal(cert), "proof payload digest mismatch")


def test_detached_payload_is_replayed_and_not_just_hash_checked() -> None:
    graph, cert = _case()
    payload = cert.pop("proof_payload")
    digest = apply_gfyproof_certificate(graph, {}, _seal(cert), proof_payload=payload)
    assert len(digest) == 64
    graph, cert = _case()
    payload = {**cert.pop("proof_payload"), "right": ["var", "p"]}
    cert["proof_payload_digest"] = canonical_sha256(payload, domain=PAYLOAD_DOMAIN)
    _rejects_without_mutation(graph, _seal(cert), "mathematical verification failed", proof_payload=payload)


def test_unknown_semantics_are_rejected() -> None:
    graph, cert = _case()
    cert["verifier_semantic_id"] = "GFY.UNKNOWN.v1"
    _rejects_without_mutation(graph, _seal(cert), "unknown GFYProof semantic verifier ID")


def test_external_only_family_fails_closed_without_engine(monkeypatch) -> None:
    graph, cert = _case()
    cert["verifier_semantic_id"] = "GFY.DFA_EQUIVALENCE.v1"
    monkeypatch.setitem(sys.modules, "math2.bridge.mapeogeo", None)
    _rejects_without_mutation(graph, _seal(cert), "verifier engine is required")


def test_local_replay_does_not_require_private_engine(monkeypatch) -> None:
    graph, cert = _case()
    monkeypatch.setitem(sys.modules, "math2.bridge.mapeogeo", None)
    registry = {}
    apply_gfyproof_certificate(graph, registry, cert)
    assert len(registry) == 1
    assert graph["nodes"][-1]["attributes"]["replay_backend"] == "MAPEOGEO_LOCAL_FINITE_V1"
    assert [n["type"] for n in graph["nodes"]] == ["SOURCE_DECLARATION", "CANONICAL_OBJECT", "EXECUTABLE_EVIDENCE"]
    assert "KERNEL_VERIFIED" not in str(graph)
    assert "FORMAL_LINKED" not in str(graph)


def test_candidate_promotion_is_idempotent_and_preserves_metadata() -> None:
    graph, cert = _case()
    graph["edges"].append({"id": "claim", "type": "REPRESENTS", "source": "source", "target": "target",
                           "attributes": {"evidence_status": "UNVERIFIED", "corpus": "retained"}})
    registry = {}
    first = apply_gfyproof_certificate(graph, registry, cert)
    before = copy.deepcopy(graph)
    assert apply_gfyproof_certificate(graph, registry, cert) == first
    assert graph == before
    assert graph["edges"][0]["attributes"]["corpus"] == "retained"
    assert len(registry) == 1


@pytest.mark.parametrize("collision", ["node", "attachment", "registry"])
def test_collision_rejection_is_atomic(collision: str) -> None:
    graph, cert = _case()
    _, record, node, attachment = materialize_gfyproof_edge(cert, graph=graph)
    registry = {}
    if collision == "node":
        graph["nodes"].append({**node, "type": "WOUND"})
    elif collision == "attachment":
        graph["edges"].append({**attachment, "target": "source"})
    else:
        registry[record.evidence_digest] = "conflicting record"
    before = copy.deepcopy((graph, registry))
    with pytest.raises(GFYProofBridgeError, match="collision"):
        apply_gfyproof_certificate(graph, registry, cert)
    assert (graph, registry) == before


def test_incomplete_contracts_cannot_override_endpoint_types() -> None:
    graph, cert = _case()
    for node, role in zip(graph["nodes"], ("eo", "object")):
        node["type"] = "WOUND"
        node["attributes"]["semantic_contracts"] = [{"binding_mode": "ENDPOINT_CONTRACT_BOUND", "role": role}]
    _rejects_without_mutation(graph, _rebind(graph, cert), "source must be source-bound or endpoint-contract-bound")


def test_unrelated_true_payload_cannot_replace_endpoint_contract_payload() -> None:
    graph, cert = _case()
    for node, role in zip(graph["nodes"], ("eo", "object")):
        node["type"] = "OPERATOR" if role == "eo" else "CANONICAL_OBJECT"
        node["attributes"]["semantic_contracts"] = [{
            "binding_mode": "ENDPOINT_CONTRACT_BOUND", "role": role,
            "contract_id": "demorgan", "contract_digest": "b" * 64,
            "semantic_id": cert["verifier_semantic_id"],
            "semantic_payload": copy.deepcopy(cert["proof_payload"]),
            "semantic_payload_sha256": canonical_sha256(cert["proof_payload"], domain="mapeogeo-endpoint-semantic-payload-v1")}]
    cert["proof_payload"] = {"left": ["var", "p"], "right": ["var", "p"], "variable_order": ["p"]}
    cert["proof_payload_digest"] = canonical_sha256(cert["proof_payload"], domain=PAYLOAD_DOMAIN)
    _rejects_without_mutation(graph, _rebind(graph, cert), "endpoint semantic contract")
