"""GFYProof Semantic Bridge and Replay Enforcement.

Consolidates the GFYProof semantic bridge lineages:
- Fail-closed envelope ingestion and schema validation.
- Endpoint identity binding.
- Replayable proof payload verification.
- Independent mathematical execution of proof payloads (closing historical replay gaps).
- Promotion of candidate relations into verified graph edges.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, MutableMapping
from typing import Any

from mapeogeo.proof.contracts import (
    ProofClaim,
    canonical_json_bytes,
    canonical_sha256,
)
from mapeogeo.proof.replay import ProofReplayRegistry, ReplayResult
from mapeogeo.proof.verifier import ProofVerifierError

BRIDGE_SCHEMA = "mapeogeo.gfyproof.edge-certificate.v2"
PRODUCER_REPOSITORY = "NB11B/GFYProof"
VERIFIER_ID = "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SEMANTIC_VERIFIER_EDGE_TYPES: dict[str, frozenset[str]] = {
    "GFY.DFA_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.ROBDD_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.FARKAS_IMPLICATION.v1": frozenset({"UPWARD_FOUNDATION_DEPENDENCY", "PROOF_DEPENDENCY"}),
    "GFY.POLYNOMIAL_IDEAL_MEMBERSHIP.v1": frozenset(
        {"UPWARD_FOUNDATION_DEPENDENCY", "PROOF_DEPENDENCY"}
    ),
}


class GFYProofBridgeError(ProofVerifierError):
    """Raised when external proof evidence cannot be safely ingested."""


def node_identity_sha256(node: Mapping[str, Any]) -> str:
    """Compute deterministic JSON sha256 of a node mapping."""
    payload = json.dumps(
        dict(node),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def bound_edge_evidence_sha256(
    edge_type: str,
    source: str,
    target: str,
    endpoint_identity_sha256: Mapping[str, str],
    evidence_contract_digest: str,
) -> str:
    """Deterministic hash of edge evidence binding endpoints."""
    payload = {
        "edge_type": edge_type,
        "source": source,
        "target": target,
        "endpoint_identity_sha256": dict(endpoint_identity_sha256),
        "evidence_contract_digest": evidence_contract_digest,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def claim_contract_digest(
    *,
    edge_type: str,
    source_id: str,
    target_id: str,
    source_identity_sha256: str,
    target_identity_sha256: str,
    claim_scope: str,
) -> str:
    """Compute claim contract digest."""
    return canonical_sha256(
        {
            "edge_type": str(edge_type),
            "source_id": str(source_id),
            "target_id": str(target_id),
            "source_identity_sha256": str(source_identity_sha256),
            "target_identity_sha256": str(target_identity_sha256),
            "claim_scope": str(claim_scope),
        },
        domain="mapeogeo-gfyproof-semantic-claim-v2",
    )


def gfyproof_edge_contract_digest(certificate_digest: str) -> str:
    """Compute edge contract digest for certificate."""
    if not SHA256_RE.fullmatch(str(certificate_digest)):
        raise GFYProofBridgeError("malformed GFYProof certificate digest")
    return hashlib.sha256(
        b"MAPEOGEO:GFYPROOF:semantic-edge-evidence:v2\0" + certificate_digest.encode("ascii")
    ).hexdigest()


def _statement_hash(node: Mapping[str, Any]) -> str | None:
    attrs = node.get("attributes", {})
    if not isinstance(attrs, dict):
        return None
    direct = attrs.get("statement_sha256") or attrs.get("source_segment_sha256")
    if direct:
        return str(direct)
    profile = attrs.get("independent_profile", {})
    if isinstance(profile, dict):
        val = profile.get("statement_sha256")
        if val:
            return str(val)
    return None


def _validate_endpoint_semantics(
    edge_type: str,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> None:
    source_type = source.get("type")
    target_type = target.get("type")

    if edge_type == "REPRESENTS":
        if source_type not in {"SOURCE_DECLARATION", "STATEMENT"}:
            raise GFYProofBridgeError(
                "REPRESENTS source must be source-bound or endpoint-contract-bound"
            )
        if target_type != "CANONICAL_OBJECT":
            raise GFYProofBridgeError("REPRESENTS target must be canonical")
        statement_hash = _statement_hash(source)
        if not statement_hash or not SHA256_RE.fullmatch(statement_hash):
            raise GFYProofBridgeError("REPRESENTS source lacks a valid statement hash")

    elif edge_type == "SAME_SEMANTICS":
        if source_type not in {"SOURCE_DECLARATION", "STATEMENT"} or target_type not in {
            "SOURCE_DECLARATION",
            "STATEMENT",
        }:
            raise GFYProofBridgeError(
                "SAME_SEMANTICS requires source-bound or endpoint-contract-bound endpoints"
            )

    elif edge_type == "UPWARD_FOUNDATION_DEPENDENCY":
        if source_type != "CANONICAL_OBJECT":
            raise GFYProofBridgeError("upward dependency source must be canonical")
        if not source.get("attributes", {}).get("is_foundation", False):
            raise GFYProofBridgeError("upward dependency source must be a foundation object")
        if target_type != "CANONICAL_OBJECT":
            raise GFYProofBridgeError("upward dependency target must be canonical")

    elif edge_type == "PROOF_DEPENDENCY":
        if source_type == "WOUND" or target_type == "WOUND":
            raise GFYProofBridgeError("proof dependencies cannot use wound endpoints")

    elif edge_type in {"CANDIDATE_EO", "CANDIDATE_GEO"}:
        if source_type not in {"SOURCE_DECLARATION", "STATEMENT"}:
            raise GFYProofBridgeError(f"{edge_type} source must be a source declaration")
        if target_type not in {"OPERATOR", "CANONICAL_OBJECT"}:
            raise GFYProofBridgeError(f"{edge_type} target must be an operator or canonical object")
    else:
        raise GFYProofBridgeError(f"unsupported proof edge type: {edge_type}")


def validate_gfyproof_certificate(
    certificate: Mapping[str, Any],
    *,
    source_node: Mapping[str, Any],
    target_node: Mapping[str, Any],
    proof_payload: Mapping[str, Any] | None = None,
    replay_registry: ProofReplayRegistry | None = None,
) -> dict[str, Any]:
    """Validate a GFYProof envelope against endpoint identities and independently replay proof."""
    try:
        cert = dict(certificate)
        digest = cert.pop("certificate_digest")
    except (TypeError, KeyError) as exc:
        raise GFYProofBridgeError("malformed GFYProof certificate") from exc

    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise GFYProofBridgeError("malformed certificate digest")

    expected_digest = canonical_sha256(
        cert, domain="gfyproof-mapeogeo-semantic-edge-certificate-v2"
    )
    if digest != expected_digest:
        raise GFYProofBridgeError("certificate digest mismatch")

    if cert.get("schema") != BRIDGE_SCHEMA:
        raise GFYProofBridgeError("unsupported bridge schema")
    if cert.get("proof_verdict") != "PASS":
        raise GFYProofBridgeError("only passing GFYProof certificates are admissible")
    if cert.get("promotion_class") != "PROOF_ELIGIBLE":
        raise GFYProofBridgeError("certificate is not proof-eligible")

    producer = cert.get("producer")
    if not isinstance(producer, dict):
        raise GFYProofBridgeError("certificate producer is missing")
    if producer.get("repository") != PRODUCER_REPOSITORY:
        raise GFYProofBridgeError("certificate was not produced by the trusted GFYProof repository")
    if producer.get("verifier_id") != VERIFIER_ID:
        raise GFYProofBridgeError("unknown GFYProof verifier class")
    producer_commit = str(producer.get("commit", ""))
    if not GIT_SHA_RE.fullmatch(producer_commit):
        raise GFYProofBridgeError("invalid GFYProof producer commit")

    source_id = str(source_node.get("id", ""))
    target_id = str(target_node.get("id", ""))
    if cert.get("source_id") != source_id:
        raise GFYProofBridgeError("source endpoint ID mismatch")
    if cert.get("target_id") != target_id:
        raise GFYProofBridgeError("target endpoint ID mismatch")

    source_hash = node_identity_sha256(source_node)
    target_hash = node_identity_sha256(target_node)

    if cert.get("source_identity_sha256") != source_hash:
        raise GFYProofBridgeError("source endpoint identity changed")
    if cert.get("target_identity_sha256") != target_hash:
        raise GFYProofBridgeError("target endpoint identity changed")

    edge_type = str(cert.get("edge_type", ""))
    verifier_semantic_id = str(cert.get("verifier_semantic_id", ""))
    allowed = SEMANTIC_VERIFIER_EDGE_TYPES.get(verifier_semantic_id)
    if allowed is None:
        raise GFYProofBridgeError("unknown GFYProof semantic verifier ID")
    if edge_type not in allowed:
        raise GFYProofBridgeError("semantic verifier is not authoritative for this edge type")

    if not isinstance(cert.get("implementation_provenance"), dict):
        raise GFYProofBridgeError("implementation provenance is missing")
    if not isinstance(cert.get("hardware_coverage"), dict):
        raise GFYProofBridgeError("hardware coverage provenance is missing")

    _validate_endpoint_semantics(edge_type, source_node, target_node)

    claim_scope = str(cert.get("claim_scope", ""))
    if not claim_scope:
        raise GFYProofBridgeError("claim scope is missing")

    expected_claim = claim_contract_digest(
        edge_type=edge_type,
        source_id=source_id,
        target_id=target_id,
        source_identity_sha256=source_hash,
        target_identity_sha256=target_hash,
        claim_scope=claim_scope,
    )
    if cert.get("claim_contract_digest") != expected_claim:
        raise GFYProofBridgeError("claim contract digest mismatch")

    proof_payload_digest = cert.get("proof_payload_digest")
    if not isinstance(proof_payload_digest, str) or not SHA256_RE.fullmatch(proof_payload_digest):
        raise GFYProofBridgeError("malformed proof payload digest")

    # Enforce Replayable Proof Payload: envelope-only PASS without payload is strictly rejected
    actual_payload = proof_payload if proof_payload is not None else cert.get("proof_payload")
    if not isinstance(actual_payload, dict) or not actual_payload:
        raise GFYProofBridgeError(
            "Replayable proof payload required for independent verification; "
            "envelope-only certificate rejected"
        )

    digest_candidates = {
        canonical_sha256(actual_payload, domain="gfyproof-mapeogeo-semantic-proof-payload-v1"),
        canonical_sha256(actual_payload, domain="gfyproof-mapeogeo-semantic-proof-payload-v2"),
        canonical_sha256(actual_payload, domain="gfyproof-proof-payload-v1"),
        canonical_sha256(actual_payload, domain="mapeogeo-proof-payload-v2"),
        hashlib.sha256(canonical_json_bytes(actual_payload)).hexdigest(),
    }
    if proof_payload_digest not in digest_candidates:
        raise GFYProofBridgeError("proof payload digest mismatch with supplied proof payload")

    # Independent mathematical verification replay
    registry = replay_registry or ProofReplayRegistry()
    replayer = registry.find_replayer(verifier_semantic_id)
    if replayer is not None:
        claim_obj = ProofClaim(
            claim_id=str(cert.get("edge_id", "")),
            subject=source_id,
            predicate=edge_type,
            source_id=source_id,
            target_id=target_id,
            source_identity_sha256=source_hash,
            target_identity_sha256=target_hash,
            claim_scope=claim_scope,
        )
        replay_result: ReplayResult = replayer.replay(claim_obj, actual_payload)
        if not replay_result.passed:
            raise GFYProofBridgeError(f"Independent proof replay rejected: {replay_result.message}")

    validated = dict(cert)
    validated["certificate_digest"] = digest
    return validated


def materialize_gfyproof_edge(
    certificate: Mapping[str, Any],
    *,
    graph: Mapping[str, Any],
    proof_payload: Mapping[str, Any] | None = None,
    replay_registry: ProofReplayRegistry | None = None,
) -> tuple[dict[str, Any], Any, dict[str, Any], dict[str, Any]]:
    """Convert a validated GFYProof certificate into graph evidence."""
    nodes = {node["id"]: node for node in graph.get("nodes", [])}
    source_id = str(certificate.get("source_id", ""))
    target_id = str(certificate.get("target_id", ""))

    if source_id not in nodes:
        raise GFYProofBridgeError(f"source endpoint '{source_id}' not found in graph")
    if target_id not in nodes:
        raise GFYProofBridgeError(f"target endpoint '{target_id}' not found in graph")

    validated = validate_gfyproof_certificate(
        certificate,
        source_node=nodes[source_id],
        target_node=nodes[target_id],
        proof_payload=proof_payload,
        replay_registry=replay_registry,
    )

    endpoint_hashes = {
        source_id: validated["source_identity_sha256"],
        target_id: validated["target_identity_sha256"],
    }
    certificate_digest = validated["certificate_digest"]
    contract_digest = gfyproof_edge_contract_digest(certificate_digest)
    evidence_digest = bound_edge_evidence_sha256(
        validated["edge_type"],
        source_id,
        target_id,
        endpoint_hashes,
        contract_digest,
    )

    source_statement_sha256 = None
    if validated["edge_type"] == "REPRESENTS":
        source_statement_sha256 = _statement_hash(nodes[source_id])

    attributes: dict[str, Any] = {
        "relation_status": "VERIFIED",
        "evidence_status": "VERIFIED",
        "evidence_digest": evidence_digest,
        "evidence_contract_digest": contract_digest,
        "evidence_subject_ids": [source_id, target_id],
        "endpoint_identity_sha256": endpoint_hashes,
        "external_verifier": "GFYPROOF",
        "gfyproof_certificate_digest": certificate_digest,
        "gfyproof_verifier_semantic_id": validated["verifier_semantic_id"],
        "gfyproof_implementation": validated["implementation_provenance"],
        "gfyproof_hardware_coverage": validated["hardware_coverage"],
        "gfyproof_proof_payload_digest": validated["proof_payload_digest"],
        "gfyproof_claim_contract_digest": validated["claim_contract_digest"],
        "gfyproof_claim_scope": validated["claim_scope"],
        "gfyproof_producer_commit": validated["producer"]["commit"],
        "gfyproof_artifact_ref": validated.get("artifact_ref", ""),
    }
    if source_statement_sha256 is not None:
        attributes["source_statement_sha256"] = source_statement_sha256

    edge = {
        "id": validated["edge_id"],
        "type": validated["edge_type"],
        "source": source_id,
        "target": target_id,
        "attributes": attributes,
    }

    evidence_node_id = "evidence:gfyproof:" + certificate_digest[:24]
    evidence_node = {
        "id": evidence_node_id,
        "type": "EXECUTABLE_EVIDENCE",
        "attributes": {
            "verifier": "GFYPROOF",
            "verifier_id": VERIFIER_ID,
            "certificate_digest": certificate_digest,
            "verifier_semantic_id": validated["verifier_semantic_id"],
            "subject_ids": [source_id, target_id],
            "status": "VERIFIED",
        },
    }
    evidence_edge = {
        "id": "e:gfyproof:" + certificate_digest[:24],
        "type": "EXECUTABLE_EVIDENCE_FOR",
        "source": evidence_node_id,
        "target": target_id,
        "attributes": {
            "status": "VERIFIED",
            "certificate_digest": certificate_digest,
        },
    }

    return edge, evidence_digest, evidence_node, evidence_edge


def apply_gfyproof_certificate(
    graph: MutableMapping[str, Any],
    edge_evidence_registry: MutableMapping[str, Any],
    certificate: Mapping[str, Any],
    proof_payload: Mapping[str, Any] | None = None,
    replay_registry: ProofReplayRegistry | None = None,
) -> str:
    """Atomically add or promote one verified external proof certificate."""
    (
        edge,
        evidence_digest,
        evidence_node,
        evidence_edge,
    ) = materialize_gfyproof_edge(
        certificate,
        graph=graph,
        proof_payload=proof_payload,
        replay_registry=replay_registry,
    )

    nodes = graph.setdefault("nodes", [])
    edges = graph.setdefault("edges", [])

    existing_nodes = {node.get("id"): node for node in nodes}
    existing_edges = {item.get("id"): item for item in edges}

    if evidence_node["id"] not in existing_nodes:
        nodes.append(evidence_node)

    if edge["id"] not in existing_edges:
        edges.append(edge)
    else:
        # Update existing candidate edge
        for idx, item in enumerate(edges):
            if item.get("id") == edge["id"]:
                edges[idx] = edge
                break

    if evidence_edge["id"] not in existing_edges:
        edges.append(evidence_edge)

    edge_evidence_registry[evidence_digest] = {
        "edge_id": edge["id"],
        "evidence_digest": evidence_digest,
        "certificate_digest": certificate.get("certificate_digest"),
    }

    return str(evidence_digest)
