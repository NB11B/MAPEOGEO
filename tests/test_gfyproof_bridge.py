"""Bridge tests: GFYProof evidence must obey MAPEOGEO's existing rigor gates."""

from __future__ import annotations

import copy

import pytest

from mapeogeo.gfyproof_bridge import (
    GFYProofBridgeError,
    apply_gfyproof_certificate,
    canonical_sha256,
    claim_contract_digest,
)
from scripts.compute_foundation_depth import (
    compute_foundation_metrics,
    node_identity_sha256,
)


COMMIT = "a" * 40
PROOF_DIGEST = "b" * 64


def _node(node_id: str, node_type: str, **attrs: object) -> dict:
    return {
        "id": node_id,
        "type": node_type,
        "attributes": attrs,
    }


def _graph() -> dict:
    return {
        "nodes": [
            _node(
                "src:root",
                "SOURCE_DECLARATION",
                source_id="FOUNDATION_MATHEMATICS_BASE",
                statement_sha256="1" * 64,
            ),
            _node(
                "canonical:foundation",
                "CANONICAL_OBJECT",
                is_foundation=True,
                domain="Foundations",
            ),
            _node(
                "canonical:advanced",
                "CANONICAL_OBJECT",
                is_foundation=False,
                domain="Advanced",
            ),
        ],
        "edges": [],
    }


def _certificate(
    source: dict,
    target: dict,
    *,
    edge_id: str,
    edge_type: str,
    proof_family: str,
    scope: str,
    producer_repository: str = "NB11B/GFYProof",
) -> dict:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)

    body = {
        "schema": "mapeogeo.gfyproof.edge-certificate.v1",
        "edge_id": edge_id,
        "edge_type": edge_type,
        "source_id": source["id"],
        "target_id": target["id"],
        "source_identity_sha256": source_hash,
        "target_identity_sha256": target_hash,
        "claim_scope": scope,
        "claim_contract_digest": claim_contract_digest(
            edge_type=edge_type,
            source_id=source["id"],
            target_id=target["id"],
            source_identity_sha256=source_hash,
            target_identity_sha256=target_hash,
            claim_scope=scope,
        ),
        "proof_family": proof_family,
        "proof_payload_digest": PROOF_DIGEST,
        "proof_verdict": "PASS",
        "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": "results/bridge/proof.json",
        "producer": {
            "repository": producer_repository,
            "commit": COMMIT,
            "verifier_id": "GFYPROOF_MAPEOGEO_BRIDGE_V1",
        },
    }
    result = dict(body)
    result["certificate_digest"] = canonical_sha256(
        body,
        domain="gfyproof-mapeogeo-edge-certificate-v1",
    )
    return result


def test_gfyproof_chain_can_establish_proof_eligible_grounding() -> None:
    graph = _graph()
    nodes = {
        node["id"]: node
        for node in graph["nodes"]
    }
    registry = {}

    before = compute_foundation_metrics(
        graph,
        edge_evidence_registry=registry,
        validated_root_ids={"src:root"},
    )
    assert before["proof_eligible_grounding"][
        "advanced_canonical_objects_reachable"
    ] == 0

    rep = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        proof_family="E091_ROBDD_EQUIVALENCE",
        scope="exact executable Boolean semantics",
    )
    apply_gfyproof_certificate(
        graph,
        registry,
        rep,
    )

    up = _certificate(
        nodes["canonical:foundation"],
        nodes["canonical:advanced"],
        edge_id="edge:gfy:up",
        edge_type="UPWARD_FOUNDATION_DEPENDENCY",
        proof_family="E093_FARKAS_IMPLICATION",
        scope="exact rational implication",
    )
    apply_gfyproof_certificate(
        graph,
        registry,
        up,
    )

    after = compute_foundation_metrics(
        graph,
        edge_evidence_registry=registry,
        validated_root_ids={"src:root"},
    )
    proof = after[
        "proof_eligible_grounding"
    ]
    assert proof[
        "advanced_canonical_objects_reachable"
    ] == 1
    assert proof[
        "foundation_reachability_pct"
    ] == 100.0

    evidence_nodes = [
        node
        for node in graph["nodes"]
        if node["type"]
        == "EXECUTABLE_EVIDENCE"
    ]
    assert len(evidence_nodes) == 2
    assert all(
        node["attributes"]["verifier"]
        == "GFYPROOF"
        for node in evidence_nodes
    )


def test_gfyproof_certificate_fails_after_endpoint_mutation() -> None:
    graph = _graph()
    nodes = {
        node["id"]: node
        for node in graph["nodes"]
    }
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        proof_family="E091_ROBDD_EQUIVALENCE",
        scope="exact executable Boolean semantics",
    )

    nodes[
        "canonical:foundation"
    ]["attributes"][
        "domain"
    ] = "Mutated"

    with pytest.raises(
        GFYProofBridgeError,
        match="identity changed",
    ):
        apply_gfyproof_certificate(
            graph,
            {},
            certificate,
        )


def test_gfyproof_spoofed_repository_is_rejected() -> None:
    graph = _graph()
    nodes = {
        node["id"]: node
        for node in graph["nodes"]
    }
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        proof_family="E091_ROBDD_EQUIVALENCE",
        scope="exact executable Boolean semantics",
        producer_repository="example/forged",
    )

    with pytest.raises(
        GFYProofBridgeError,
        match="trusted GFYProof repository",
    ):
        apply_gfyproof_certificate(
            graph,
            {},
            certificate,
        )


def test_gfyproof_proof_family_cannot_be_reused_for_wrong_relation() -> None:
    graph = _graph()
    nodes = {
        node["id"]: node
        for node in graph["nodes"]
    }
    certificate = _certificate(
        nodes["canonical:foundation"],
        nodes["canonical:advanced"],
        edge_id="edge:gfy:bad",
        edge_type="UPWARD_FOUNDATION_DEPENDENCY",
        proof_family="E091_ROBDD_EQUIVALENCE",
        scope="wrong proof family",
    )

    with pytest.raises(
        GFYProofBridgeError,
        match="not authoritative",
    ):
        apply_gfyproof_certificate(
            graph,
            {},
            certificate,
        )


def test_gfyproof_certificate_digest_tamper_is_rejected() -> None:
    graph = _graph()
    nodes = {
        node["id"]: node
        for node in graph["nodes"]
    }
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        proof_family="E091_ROBDD_EQUIVALENCE",
        scope="exact executable Boolean semantics",
    )
    tampered = copy.deepcopy(
        certificate
    )
    tampered[
        "claim_scope"
    ] = "changed after signing"

    with pytest.raises(
        GFYProofBridgeError,
        match="certificate digest mismatch",
    ):
        apply_gfyproof_certificate(
            graph,
            {},
            tampered,
        )


def test_gfyproof_evidence_does_not_create_source_or_kernel_status() -> None:
    graph = _graph()
    nodes = {
        node["id"]: node
        for node in graph["nodes"]
    }
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        proof_family="E091_ROBDD_EQUIVALENCE",
        scope="exact executable Boolean semantics",
    )
    apply_gfyproof_certificate(
        graph,
        {},
        certificate,
    )

    generated = [
        node
        for node in graph["nodes"]
        if node["id"].startswith(
            "evidence:gfyproof:"
        )
    ]
    assert len(generated) == 1
    assert generated[0][
        "type"
    ] == "EXECUTABLE_EVIDENCE"
    assert all(
        node["type"]
        not in {
            "KERNEL_VERIFIED",
        }
        for node in graph["nodes"]
    )
