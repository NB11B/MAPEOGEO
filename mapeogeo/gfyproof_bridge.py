"""Fail-closed ingestion for GFYProof proof-carrying certificates.

GFYProof is treated as an independent executable verifier, not as a source
corpus and not as a Lean kernel. Successful ingestion may add executable
evidence and registered proof-eligible edges, but never SOURCE_DECLARATION or
KERNEL_VERIFIED status.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, MutableMapping

from scripts.compute_foundation_depth import (
    RegisteredEdgeEvidence,
    bound_edge_evidence_sha256,
    node_identity_sha256,
)


BRIDGE_SCHEMA = "mapeogeo.gfyproof.edge-certificate.v2"
PRODUCER_REPOSITORY = "NB11B/GFYProof"
VERIFIER_ID = "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SEMANTIC_VERIFIER_EDGE_TYPES: dict[str, frozenset[str]] = {
    "GFY.DFA_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.ROBDD_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.CYCLIC_GROUP_COMPOSITION.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.SO3_ROTATION.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.EIGENPAIR_RESIDUAL.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.ORTHOGONAL_PROJECTION.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.GRAPH_LAPLACIAN_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.PROJECTIVE_HOMOGENEOUS_EQUIVALENCE.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.LP_STRONG_DUALITY_1D.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.GAUSSIAN_KERNEL_EQUIVALENCE_PSD.v1": frozenset({"REPRESENTS", "SAME_SEMANTICS"}),
    "GFY.FARKAS_IMPLICATION.v1": frozenset(
        {"UPWARD_FOUNDATION_DEPENDENCY", "PROOF_DEPENDENCY"}
    ),
    "GFY.TOPOLOGICAL_IMPLICATION.v1": frozenset(
        {
            "UPWARD_FOUNDATION_DEPENDENCY",
            "PROOF_DEPENDENCY",
            "CANDIDATE_EO",
            "CANDIDATE_GEO",
        }
    ),
    "GFY.POLYNOMIAL_IDEAL_MEMBERSHIP.v1": frozenset(
        {"UPWARD_FOUNDATION_DEPENDENCY", "PROOF_DEPENDENCY"}
    ),
}


class GFYProofBridgeError(ValueError):
    """Raised when external proof evidence cannot be safely ingested."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any, *, domain: str) -> str:
    return hashlib.sha256(
        domain.encode("utf-8")
        + b"\0"
        + canonical_json_bytes(value)
    ).hexdigest()


def claim_contract_digest(
    *,
    edge_type: str,
    source_id: str,
    target_id: str,
    source_identity_sha256: str,
    target_identity_sha256: str,
    claim_scope: str,
) -> str:
    return canonical_sha256(
        {
            "edge_type": str(edge_type),
            "source_id": str(source_id),
            "target_id": str(target_id),
            "source_identity_sha256": str(
                source_identity_sha256
            ),
            "target_identity_sha256": str(
                target_identity_sha256
            ),
            "claim_scope": str(claim_scope),
        },
        domain="mapeogeo-gfyproof-semantic-claim-v2",
    )


def gfyproof_edge_contract_digest(
    certificate_digest: str,
) -> str:
    if not SHA256_RE.fullmatch(
        str(certificate_digest)
    ):
        raise GFYProofBridgeError(
            "malformed GFYProof certificate digest"
        )
    return hashlib.sha256(
        b"MAPEOGEO:GFYPROOF:semantic-edge-evidence:v2\0"
        + certificate_digest.encode(
            "ascii"
        )
    ).hexdigest()


def _statement_hash(
    node: Mapping[str, Any],
) -> str | None:
    attrs = node.get(
        "attributes",
        {},
    )
    direct = (
        attrs.get(
            "statement_sha256"
        )
        or attrs.get(
            "source_segment_sha256"
        )
    )
    if direct:
        return str(direct)
    profile = attrs.get(
        "independent_profile",
        {},
    )
    if isinstance(profile, dict):
        value = profile.get(
            "statement_sha256"
        )
        return (
            str(value)
            if value
            else None
        )
    return None


def _shared_endpoint_contract_roles(
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> tuple[str, str] | None:
    def records(node: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        attrs = node.get("attributes", {})
        if not isinstance(attrs, dict):
            return []
        raw = attrs.get("semantic_contracts", [])
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    for left in records(source):
        for right in records(target):
            if (
                left.get("binding_mode") == "ENDPOINT_CONTRACT_BOUND"
                and right.get("binding_mode") == "ENDPOINT_CONTRACT_BOUND"
                and left.get("contract_id") == right.get("contract_id")
                and left.get("contract_digest") == right.get("contract_digest")
                and left.get("semantic_id") == right.get("semantic_id")
            ):
                return str(left.get("role", "")), str(right.get("role", ""))
    return None


def _validate_endpoint_semantics(
    edge_type: str,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> None:
    source_type = source.get(
        "type"
    )
    target_type = target.get(
        "type"
    )

    if edge_type == "REPRESENTS":
        roles = _shared_endpoint_contract_roles(source, target)
        if roles in {("eo", "object"), ("geo", "object")}:
            return

        if source_type not in {
            "SOURCE_DECLARATION",
            "STATEMENT",
        }:
            raise GFYProofBridgeError(
                "REPRESENTS source must be source-bound or endpoint-contract-bound"
            )
        if target_type != "CANONICAL_OBJECT":
            raise GFYProofBridgeError(
                "REPRESENTS target must be canonical"
            )
        statement_hash = _statement_hash(
            source
        )
        if (
            not statement_hash
            or not SHA256_RE.fullmatch(
                statement_hash
            )
        ):
            raise GFYProofBridgeError(
                "REPRESENTS source lacks a valid statement hash"
            )

    elif edge_type == "SAME_SEMANTICS":
        roles = _shared_endpoint_contract_roles(source, target)
        if roles is not None and set(roles) == {"eo", "geo"}:
            return

        if (
            source_type
            not in {
                "SOURCE_DECLARATION",
                "STATEMENT",
            }
            or target_type
            not in {
                "SOURCE_DECLARATION",
                "STATEMENT",
            }
        ):
            raise GFYProofBridgeError(
                "SAME_SEMANTICS requires source-bound or endpoint-contract-bound endpoints"
            )

    elif edge_type == "UPWARD_FOUNDATION_DEPENDENCY":
        if source_type != "CANONICAL_OBJECT":
            raise GFYProofBridgeError(
                "upward dependency source must be canonical"
            )
        if not source.get(
            "attributes",
            {},
        ).get(
            "is_foundation",
            False,
        ):
            raise GFYProofBridgeError(
                "upward dependency source must be a foundation object"
            )
        if target_type != "CANONICAL_OBJECT":
            raise GFYProofBridgeError(
                "upward dependency target must be canonical"
            )

    elif edge_type == "PROOF_DEPENDENCY":
        if source_type == "WOUND" or target_type == "WOUND":
            raise GFYProofBridgeError(
                "proof dependencies cannot use wound endpoints"
            )

    elif edge_type in {"CANDIDATE_EO", "CANDIDATE_GEO"}:
        if source_type not in {"SOURCE_DECLARATION", "STATEMENT"}:
            raise GFYProofBridgeError(
                f"{edge_type} source must be a source declaration"
            )
        if target_type not in {"OPERATOR", "CANONICAL_OBJECT"}:
            raise GFYProofBridgeError(
                f"{edge_type} target must be an operator or canonical object"
            )
        statement_hash = _statement_hash(source)
        if not statement_hash or not SHA256_RE.fullmatch(statement_hash):
            raise GFYProofBridgeError(
                f"{edge_type} source lacks a valid statement hash"
            )

    else:
        raise GFYProofBridgeError(
            f"unsupported proof edge type: {edge_type}"
        )


def validate_gfyproof_certificate(
    certificate: Mapping[str, Any],
    *,
    source_node: Mapping[str, Any],
    target_node: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a GFYProof envelope against the current graph node identities."""
    try:
        cert = dict(
            certificate
        )
        digest = cert.pop(
            "certificate_digest"
        )
    except (
        TypeError,
        KeyError,
    ) as exc:
        raise GFYProofBridgeError(
            "malformed GFYProof certificate"
        ) from exc

    if (
        not isinstance(
            digest,
            str,
        )
        or not SHA256_RE.fullmatch(
            digest
        )
    ):
        raise GFYProofBridgeError(
            "malformed certificate digest"
        )

    expected_digest = canonical_sha256(
        cert,
        domain="gfyproof-mapeogeo-semantic-edge-certificate-v2",
    )
    if digest != expected_digest:
        raise GFYProofBridgeError(
            "certificate digest mismatch"
        )

    if cert.get(
        "schema"
    ) != BRIDGE_SCHEMA:
        raise GFYProofBridgeError(
            "unsupported bridge schema"
        )
    if cert.get(
        "proof_verdict"
    ) != "PASS":
        raise GFYProofBridgeError(
            "only passing GFYProof certificates are admissible"
        )
    if cert.get(
        "promotion_class"
    ) != "PROOF_ELIGIBLE":
        raise GFYProofBridgeError(
            "certificate is not proof-eligible"
        )

    producer = cert.get(
        "producer"
    )
    if not isinstance(
        producer,
        dict,
    ):
        raise GFYProofBridgeError(
            "certificate producer is missing"
        )
    if producer.get(
        "repository"
    ) != PRODUCER_REPOSITORY:
        raise GFYProofBridgeError(
            "certificate was not produced by the trusted GFYProof repository"
        )
    if producer.get(
        "verifier_id"
    ) != VERIFIER_ID:
        raise GFYProofBridgeError(
            "unknown GFYProof verifier class"
        )
    producer_commit = str(
        producer.get(
            "commit",
            "",
        )
    )
    if not GIT_SHA_RE.fullmatch(
        producer_commit
    ):
        raise GFYProofBridgeError(
            "invalid GFYProof producer commit"
        )

    source_id = str(
        source_node.get(
            "id",
            "",
        )
    )
    target_id = str(
        target_node.get(
            "id",
            "",
        )
    )
    if cert.get(
        "source_id"
    ) != source_id:
        raise GFYProofBridgeError(
            "source endpoint ID mismatch"
        )
    if cert.get(
        "target_id"
    ) != target_id:
        raise GFYProofBridgeError(
            "target endpoint ID mismatch"
        )

    source_hash = (
        node_identity_sha256(
            dict(
                source_node
            )
        )
    )
    target_hash = (
        node_identity_sha256(
            dict(
                target_node
            )
        )
    )

    if cert.get(
        "source_identity_sha256"
    ) != source_hash:
        raise GFYProofBridgeError(
            "source endpoint identity changed"
        )
    if cert.get(
        "target_identity_sha256"
    ) != target_hash:
        raise GFYProofBridgeError(
            "target endpoint identity changed"
        )

    edge_type = str(
        cert.get(
            "edge_type",
            "",
        )
    )
    verifier_semantic_id = str(
        cert.get(
            "verifier_semantic_id",
            "",
        )
    )
    allowed = (
        SEMANTIC_VERIFIER_EDGE_TYPES.get(
            verifier_semantic_id
        )
    )
    if allowed is None:
        raise GFYProofBridgeError(
            "unknown GFYProof semantic verifier ID"
        )
    if edge_type not in allowed:
        raise GFYProofBridgeError(
            "semantic verifier is not authoritative for this edge type"
        )
    implementation = cert.get(
        "implementation_provenance"
    )
    if not isinstance(
        implementation,
        dict,
    ):
        raise GFYProofBridgeError(
            "implementation provenance is missing"
        )
    hardware_coverage = cert.get(
        "hardware_coverage"
    )
    if not isinstance(
        hardware_coverage,
        dict,
    ):
        raise GFYProofBridgeError(
            "hardware coverage provenance is missing"
        )

    _validate_endpoint_semantics(
        edge_type,
        source_node,
        target_node,
    )

    claim_scope = str(
        cert.get(
            "claim_scope",
            "",
        )
    )
    if not claim_scope:
        raise GFYProofBridgeError(
            "claim scope is missing"
        )

    expected_claim = (
        claim_contract_digest(
            edge_type=edge_type,
            source_id=source_id,
            target_id=target_id,
            source_identity_sha256=source_hash,
            target_identity_sha256=target_hash,
            claim_scope=claim_scope,
        )
    )
    if cert.get(
        "claim_contract_digest"
    ) != expected_claim:
        raise GFYProofBridgeError(
            "claim contract digest mismatch"
        )

    proof_payload_digest = cert.get(
        "proof_payload_digest"
    )
    if (
        not isinstance(
            proof_payload_digest,
            str,
        )
        or not SHA256_RE.fullmatch(
            proof_payload_digest
        )
    ):
        raise GFYProofBridgeError(
            "malformed proof payload digest"
        )

    validated = dict(
        cert
    )
    validated[
        "certificate_digest"
    ] = digest
    return validated


def materialize_gfyproof_edge(
    certificate: Mapping[str, Any],
    *,
    graph: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    RegisteredEdgeEvidence,
    dict[str, Any],
    dict[str, Any],
]:
    """Convert a validated GFYProof certificate into MAPEOGEO graph evidence."""
    nodes = {
        node["id"]: node
        for node
        in graph.get(
            "nodes",
            [],
        )
        if node.get(
            "id"
        )
    }
    source_id = str(
        certificate.get(
            "source_id",
            "",
        )
    )
    target_id = str(
        certificate.get(
            "target_id",
            "",
        )
    )
    if source_id not in nodes or target_id not in nodes:
        raise GFYProofBridgeError(
            "certificate endpoint is not present in the graph"
        )

    validated = (
        validate_gfyproof_certificate(
            certificate,
            source_node=nodes[
                source_id
            ],
            target_node=nodes[
                target_id
            ],
        )
    )

    endpoint_hashes = {
        source_id: validated[
            "source_identity_sha256"
        ],
        target_id: validated[
            "target_identity_sha256"
        ],
    }
    certificate_digest = validated[
        "certificate_digest"
    ]
    contract_digest = (
        gfyproof_edge_contract_digest(
            certificate_digest
        )
    )
    evidence_digest = (
        bound_edge_evidence_sha256(
            validated[
                "edge_type"
            ],
            source_id,
            target_id,
            endpoint_hashes,
            contract_digest,
        )
    )

    source_statement_sha256 = None
    if (
        validated[
            "edge_type"
        ]
        == "REPRESENTS"
    ):
        source_statement_sha256 = (
            _statement_hash(
                nodes[
                    source_id
                ]
            )
        )

    attributes: dict[
        str,
        Any,
    ] = {
        "relation_status": "VERIFIED",
        "evidence_status": "VERIFIED",
        "evidence_digest": evidence_digest,
        "evidence_contract_digest": contract_digest,
        "evidence_subject_ids": [
            source_id,
            target_id,
        ],
        "endpoint_identity_sha256": endpoint_hashes,
        "external_verifier": "GFYPROOF",
        "gfyproof_certificate_digest": certificate_digest,
        "gfyproof_verifier_semantic_id": validated[
            "verifier_semantic_id"
        ],
        "gfyproof_implementation": validated[
            "implementation_provenance"
        ],
        "gfyproof_hardware_coverage": validated[
            "hardware_coverage"
        ],
        "gfyproof_proof_payload_digest": validated[
            "proof_payload_digest"
        ],
        "gfyproof_claim_contract_digest": validated[
            "claim_contract_digest"
        ],
        "gfyproof_claim_scope": validated[
            "claim_scope"
        ],
        "gfyproof_producer_commit": validated[
            "producer"
        ][
            "commit"
        ],
        "gfyproof_artifact_ref": validated.get(
            "artifact_ref",
            "",
        ),
    }
    if (
        source_statement_sha256
        is not None
    ):
        attributes[
            "source_statement_sha256"
        ] = (
            source_statement_sha256
        )

    edge = {
        "id": validated[
            "edge_id"
        ],
        "type": validated[
            "edge_type"
        ],
        "source": source_id,
        "target": target_id,
        "attributes": attributes,
    }

    record = RegisteredEdgeEvidence(
        edge_id=str(
            edge[
                "id"
            ]
        ),
        edge_type=str(
            edge[
                "type"
            ]
        ),
        source=source_id,
        target=target_id,
        endpoint_identity_sha256=tuple(
            sorted(
                endpoint_hashes.items()
            )
        ),
        evidence_contract_digest=contract_digest,
        source_statement_sha256=source_statement_sha256,
        evidence_digest=evidence_digest,
    )

    evidence_node_id = (
        "evidence:gfyproof:"
        + certificate_digest[
            :24
        ]
    )
    evidence_node = {
        "id": evidence_node_id,
        "type": "EXECUTABLE_EVIDENCE",
        "attributes": {
            "verifier": "GFYPROOF",
            "verifier_id": VERIFIER_ID,
            "certificate_digest": certificate_digest,
            "verifier_semantic_id": validated[
                "verifier_semantic_id"
            ],
            "implementation": validated[
                "implementation_provenance"
            ],
            "hardware_coverage": validated[
                "hardware_coverage"
            ],
            "proof_payload_digest": validated[
                "proof_payload_digest"
            ],
            "claim_contract_digest": validated[
                "claim_contract_digest"
            ],
            "claim_scope": validated[
                "claim_scope"
            ],
            "producer_repository": PRODUCER_REPOSITORY,
            "producer_commit": validated[
                "producer"
            ][
                "commit"
            ],
            "artifact_ref": validated.get(
                "artifact_ref",
                "",
            ),
            "subject_ids": [
                source_id,
                target_id,
            ],
            "status": "VERIFIED",
        },
    }
    evidence_edge = {
        "id": (
            "e:gfyproof:"
            + certificate_digest[
                :24
            ]
        ),
        "type": "EXECUTABLE_EVIDENCE_FOR",
        "source": evidence_node_id,
        "target": target_id,
        "attributes": {
            "status": "VERIFIED",
            "certificate_digest": certificate_digest,
        },
    }

    return (
        edge,
        record,
        evidence_node,
        evidence_edge,
    )


def _merge_promotable_existing_edge(
    existing: Mapping[str, Any],
    verified: Mapping[str, Any],
) -> dict[str, Any]:
    """Promote an existing unverified candidate without changing its identity."""
    for field in ("id", "type", "source", "target"):
        if existing.get(field) != verified.get(field):
            raise GFYProofBridgeError(
                f"existing edge {field} does not match certified claim"
            )

    attrs = existing.get("attributes", {})
    if not isinstance(attrs, dict):
        raise GFYProofBridgeError(
            "existing edge attributes must be a mapping"
        )

    inactive = {
        "REJECTED",
        "SUPERSEDED",
        "UNRESOLVED",
        "WOUND",
    }
    for field in (
        "status",
        "alignment_status",
        "cross_source_status",
        "relation_status",
        "evidence_status",
    ):
        value = str(attrs.get(field, "")).upper()
        if value in inactive:
            raise GFYProofBridgeError(
                "inactive/rejected edge cannot be promoted"
            )

    if str(attrs.get("evidence_status", "")).upper() == "VERIFIED":
        if existing != verified:
            raise GFYProofBridgeError(
                "existing edge is already verified under different evidence"
            )
        return dict(existing)

    merged = dict(existing)
    merged_attrs = dict(attrs)
    merged_attrs.update(
        verified.get("attributes", {})
    )
    merged["attributes"] = merged_attrs
    return merged


def apply_gfyproof_certificate(
    graph: MutableMapping[
        str,
        Any,
    ],
    edge_evidence_registry: MutableMapping[
        str,
        RegisteredEdgeEvidence,
    ],
    certificate: Mapping[
        str,
        Any,
    ],
) -> str:
    """Atomically add or promote one external proof certificate."""
    (
        edge,
        record,
        evidence_node,
        evidence_edge,
    ) = materialize_gfyproof_edge(
        certificate,
        graph=graph,
    )

    nodes = graph.setdefault(
        "nodes",
        [],
    )
    edges = graph.setdefault(
        "edges",
        [],
    )

    existing_nodes = {
        node.get("id"): node
        for node in nodes
    }
    existing_edges = {
        item.get("id"): item
        for item in edges
    }

    existing_evidence_node = existing_nodes.get(
        evidence_node["id"]
    )
    if (
        existing_evidence_node is not None
        and existing_evidence_node != evidence_node
    ):
        raise GFYProofBridgeError(
            "evidence node ID collision"
        )

    existing_claim_edge = existing_edges.get(
        edge["id"]
    )
    promoted_edge = edge
    if existing_claim_edge is not None:
        promoted_edge = _merge_promotable_existing_edge(
            existing_claim_edge,
            edge,
        )

    existing_attachment = existing_edges.get(
        evidence_edge["id"]
    )
    if (
        existing_attachment is not None
        and existing_attachment != evidence_edge
    ):
        raise GFYProofBridgeError(
            "evidence attachment edge ID collision"
        )

    current_record = edge_evidence_registry.get(
        record.evidence_digest
    )
    if (
        current_record is not None
        and current_record != record
    ):
        raise GFYProofBridgeError(
            "edge evidence registry collision"
        )

    if existing_evidence_node is None:
        nodes.append(
            evidence_node
        )

    if existing_claim_edge is None:
        edges.append(
            promoted_edge
        )
    elif promoted_edge != existing_claim_edge:
        for index, item in enumerate(edges):
            if item.get("id") == edge["id"]:
                edges[index] = promoted_edge
                break

    if existing_attachment is None:
        edges.append(
            evidence_edge
        )

    edge_evidence_registry[
        record.evidence_digest
    ] = record

    return record.evidence_digest

