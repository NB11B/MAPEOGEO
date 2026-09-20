"""Post-hardening proof-replay counterexample.

Uses a verifier that remains legitimately relation-capable after the scope
hardening. The desired behavior is rejection of an envelope-only PASS because
MAPEOGEO has no replayable proof payload.
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


def _certificate(source: dict, target: dict) -> dict:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)
    scope = "audit: no proof payload is available for replay"
    body = {
        "schema": "mapeogeo.gfyproof.edge-certificate.v2",
        "edge_id": "edge:audit:robdd-envelope-only",
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
        # SHA-shaped metadata only. No proof payload is supplied.
        "proof_payload_digest": "2" * 64,
        "proof_verdict": "PASS",
        "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": "",
        "producer": {
            "repository": "NB11B/GFYProof",
            "commit": "a" * 40,
            "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2",
        },
    }
    cert = dict(body)
    cert["certificate_digest"] = canonical_sha256(
        body,
        domain="gfyproof-mapeogeo-semantic-edge-certificate-v2",
    )
    return cert


@pytest.mark.xfail(
    strict=True,
    reason=(
        "certificate v2 still validates a proof digest/PASS envelope without "
        "independent proof-payload replay"
    ),
)
def test_relation_capable_envelope_without_proof_payload_is_rejected() -> None:
    source = {
        "id": "src:audit:logic:a",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "a" * 64},
    }
    target = {
        "id": "src:audit:logic:b",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "b" * 64},
    }
    graph = {"nodes": [source, target], "edges": []}
    registry = {}

    with pytest.raises(GFYProofBridgeError):
        apply_gfyproof_certificate(
            graph,
            registry,
            _certificate(source, target),
        )

    assert graph["edges"] == []
    assert registry == {}
