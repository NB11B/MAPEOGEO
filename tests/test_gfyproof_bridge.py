"""Semantic GFYProof bridge tests against MAPEOGEO's rigor gates."""

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
DEFAULT_PROOF_PAYLOAD = {"verified": True, "evidence": "canonical_proof_payload"}
PROOF_DIGEST = canonical_sha256(
    DEFAULT_PROOF_PAYLOAD,
    domain="gfyproof-mapeogeo-semantic-proof-payload-v1",
)


def _node(node_id: str, node_type: str, **attrs: object) -> dict:
    return {"id": node_id, "type": node_type, "attributes": attrs}


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


def _valid_payload_for_semantic_id(semantic_id: str) -> dict[str, Any]:
    if semantic_id == "GFY.ROBDD_EQUIVALENCE.v1":
        return {
            "left": ["not", ["and", ["var", "p"], ["var", "q"]]],
            "right": ["or", ["not", ["var", "p"]], ["not", ["var", "q"]]],
            "variable_order": ["p", "q"],
        }
    if semantic_id in {"GFY.FARKAS_IMPLICATION.v1", "GFY.FOUNDATION_DEPENDENCY.v1"}:
        return {
            "certificate_type": "implication",
            "matrix": [[1, 0], [0, 1]],
            "bounds": [1, 2],
            "target_coefficients": [1, 2],
            "target_bound": 5,
            "multipliers": [1, 2],
        }
    if semantic_id == "GFY.SO3_ROTATION.v1":
        return {
            "matrix": [
                [0.0, -1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            "tolerance": 1e-6,
        }
    return dict(DEFAULT_PROOF_PAYLOAD)


def _certificate(
    source: dict,
    target: dict,
    *,
    edge_id: str,
    edge_type: str,
    semantic_id: str,
    scope: str,
    experiment_id: str,
    hardware_contract_id: str,
    producer_repository: str = "NB11B/GFYProof",
    proof_payload: dict | None = None,
) -> dict:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)
    payload = dict(proof_payload) if proof_payload is not None else _valid_payload_for_semantic_id(semantic_id)
    payload_digest = canonical_sha256(
        payload,
        domain="gfyproof-mapeogeo-semantic-proof-payload-v2",
    )
    body = {
        "schema": "mapeogeo.gfyproof.edge-certificate.v2",
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
        "verifier_semantic_id": semantic_id,
        "verifier_scope": "synthetic semantic scope",
        "implementation_provenance": {
            "experiment_id": experiment_id,
            "class": "example.Verifier",
        },
        "hardware_coverage": {
            "status": "HARDWARE_REDUCED_QUALIFIED",
            "contract_id": hardware_contract_id,
            "scope": "bounded reduced certificate scope",
        },
        "proof_payload": payload,
        "proof_payload_digest": payload_digest,
        "proof_verdict": "PASS",
        "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": "results/bridge/proof.json",
        "producer": {
            "repository": producer_repository,
            "commit": COMMIT,
            "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        },
    }
    result = dict(body)
    result["certificate_digest"] = canonical_sha256(
        body,
        domain="gfyproof-mapeogeo-semantic-edge-certificate-v2",
    )
    return result


def test_semantic_chain_can_establish_proof_eligible_grounding() -> None:
    graph = _graph()
    nodes = {node["id"]: node for node in graph["nodes"]}
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
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="exact executable Boolean semantics",
        experiment_id="E095",
        hardware_contract_id="C23",
    )
    apply_gfyproof_certificate(graph, registry, rep)

    up = _certificate(
        nodes["canonical:foundation"],
        nodes["canonical:advanced"],
        edge_id="edge:gfy:up",
        edge_type="UPWARD_FOUNDATION_DEPENDENCY",
        semantic_id="GFY.FARKAS_IMPLICATION.v1",
        scope="exact rational implication",
        experiment_id="historical-farkas",
        hardware_contract_id="",
    )
    apply_gfyproof_certificate(graph, registry, up)

    after = compute_foundation_metrics(
        graph,
        edge_evidence_registry=registry,
        validated_root_ids={"src:root"},
    )
    assert after["proof_eligible_grounding"][
        "advanced_canonical_objects_reachable"
    ] == 1


def test_experiment_number_is_provenance_not_semantic_identity() -> None:
    graph_a = _graph()
    graph_b = _graph()
    node_a = {node["id"]: node for node in graph_a["nodes"]}
    node_b = {node["id"]: node for node in graph_b["nodes"]}

    current = _certificate(
        node_a["src:root"],
        node_a["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="same semantic claim",
        experiment_id="E095",
        hardware_contract_id="C23",
    )
    historical = _certificate(
        node_b["src:root"],
        node_b["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="same semantic claim",
        experiment_id="E091",
        hardware_contract_id="historical",
    )

    apply_gfyproof_certificate(graph_a, {}, current)
    apply_gfyproof_certificate(graph_b, {}, historical)

    edge_a = next(e for e in graph_a["edges"] if e["id"] == "edge:gfy:rep")
    edge_b = next(e for e in graph_b["edges"] if e["id"] == "edge:gfy:rep")
    assert edge_a["attributes"]["gfyproof_verifier_semantic_id"] == (
        edge_b["attributes"]["gfyproof_verifier_semantic_id"]
    )
    assert edge_a["attributes"]["gfyproof_implementation"] != (
        edge_b["attributes"]["gfyproof_implementation"]
    )


def test_endpoint_mutation_invalidates_semantic_certificate() -> None:
    graph = _graph()
    nodes = {node["id"]: node for node in graph["nodes"]}
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="exact executable Boolean semantics",
        experiment_id="E095",
        hardware_contract_id="C23",
    )
    nodes["canonical:foundation"]["attributes"]["domain"] = "Mutated"
    with pytest.raises(GFYProofBridgeError, match="identity changed"):
        apply_gfyproof_certificate(graph, {}, certificate)


def test_spoofed_repository_is_rejected() -> None:
    graph = _graph()
    nodes = {node["id"]: node for node in graph["nodes"]}
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="exact executable Boolean semantics",
        experiment_id="E095",
        hardware_contract_id="C23",
        producer_repository="example/forged",
    )
    with pytest.raises(GFYProofBridgeError, match="trusted GFYProof repository"):
        apply_gfyproof_certificate(graph, {}, certificate)


def test_semantic_verifier_cannot_be_reused_for_wrong_relation() -> None:
    graph = _graph()
    nodes = {node["id"]: node for node in graph["nodes"]}
    certificate = _certificate(
        nodes["canonical:foundation"],
        nodes["canonical:advanced"],
        edge_id="edge:gfy:bad",
        edge_type="UPWARD_FOUNDATION_DEPENDENCY",
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="wrong semantic family",
        experiment_id="E095",
        hardware_contract_id="C23",
    )
    with pytest.raises(GFYProofBridgeError, match="not authoritative"):
        apply_gfyproof_certificate(graph, {}, certificate)


def test_certificate_digest_tamper_is_rejected() -> None:
    graph = _graph()
    nodes = {node["id"]: node for node in graph["nodes"]}
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="exact executable Boolean semantics",
        experiment_id="E095",
        hardware_contract_id="C23",
    )
    tampered = copy.deepcopy(certificate)
    tampered["claim_scope"] = "changed after signing"
    with pytest.raises(GFYProofBridgeError, match="certificate digest mismatch"):
        apply_gfyproof_certificate(graph, {}, tampered)


def test_evidence_records_semantic_and_hardware_provenance_without_kernel_status() -> None:
    graph = _graph()
    nodes = {node["id"]: node for node in graph["nodes"]}
    certificate = _certificate(
        nodes["src:root"],
        nodes["canonical:foundation"],
        edge_id="edge:gfy:rep",
        edge_type="REPRESENTS",
        semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        scope="exact executable Boolean semantics",
        experiment_id="E095",
        hardware_contract_id="C23",
    )
    apply_gfyproof_certificate(graph, {}, certificate)

    generated = [
        node
        for node in graph["nodes"]
        if node["id"].startswith("evidence:gfyproof:")
    ]
    assert len(generated) == 1
    attrs = generated[0]["attributes"]
    assert attrs["verifier_semantic_id"] == "GFY.ROBDD_EQUIVALENCE.v1"
    assert attrs["implementation"]["experiment_id"] == "E095"
    assert attrs["hardware_coverage"]["contract_id"] == "C23"
    assert generated[0]["type"] == "EXECUTABLE_EVIDENCE"
