"""Known cross-repository proof-ingestion gap.

The certificate v2 envelope is currently self-hashed but not independently
proof-replayed or producer-authenticated by MAPEOGEO. This test encodes the
desired fail-closed behavior as a strict xfail until certificate v3 is hardened.
"""

from __future__ import annotations

import pytest

from mapeogeo.gfyproof_bridge import (
    GFYProofBridgeError,
    apply_gfyproof_certificate,
    canonical_sha256,
    claim_contract_digest,
)
from scripts.compute_foundation_depth import node_identity_sha256


def _envelope_only_certificate(source: dict, target: dict) -> dict:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)
    scope = "audit envelope with no replayable proof payload"

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
        "verifier_semantic_id": "GFY.SO3_ROTATION.v1",
        "verifier_scope": "real 3x3 orthogonal matrices with determinant +1",
        "implementation_provenance": {
            "experiment_id": "AUDIT_ONLY",
            "class": "not-a-real-proof",
        },
        "hardware_coverage": {
            "status": "HARDWARE_NOT_BOUND",
            "contract_id": "",
            "scope": "",
        },
        # Deliberately no proof is supplied. This is only a SHA-shaped string.
        "proof_payload_digest": "2" * 64,
        "proof_verdict": "PASS",
        "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": "",
        "producer": {
            # These are unauthenticated strings inside the same self-hashed body.
            "repository": "NB11B/GFYProof",
            "commit": "a" * 40,
            "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        },
    }
    result = dict(body)
    result["certificate_digest"] = canonical_sha256(
        body,
        domain="gfyproof-mapeogeo-semantic-edge-certificate-v2",
    )
    return result


def test_envelope_only_pass_cannot_promote_same_semantics() -> None:
    source = {
        "id": "src:audit:a",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "a" * 64},
    }
    target = {
        "id": "src:audit:b",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "b" * 64},
    }
    graph = {"nodes": [source, target], "edges": []}
    registry = {}

    certificate = _envelope_only_certificate(source, target)

    # Desired behavior: external mathematical authority requires proof replay
    # or independently authenticated attestation, not merely a PASS field.
    with pytest.raises(GFYProofBridgeError):
        apply_gfyproof_certificate(graph, registry, certificate)

    assert graph["edges"] == []
    assert registry == {}
