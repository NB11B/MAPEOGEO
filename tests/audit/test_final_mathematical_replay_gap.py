"""Final proof-replay counterexample after bridge hardening.

A digest-consistent payload that is mathematically false must still be rejected.
If it is accepted, the bridge is validating payload presence/integrity rather
than independently replaying the mathematical verifier.
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


def _false_robdd_certificate(source: dict, target: dict) -> dict:
    source_hash = node_identity_sha256(source)
    target_hash = node_identity_sha256(target)
    scope = "audit false Boolean equivalence with digest-consistent payload"
    payload = {
        "left": ["const", True],
        "right": ["const", False],
        "variable_order": [],
    }
    proof_digest = canonical_sha256(
        payload,
        domain="gfyproof-mapeogeo-semantic-proof-payload-v2",
    )
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
        "bridge currently checks replay-payload presence/digest but does not "
        "independently execute the mathematical verifier"
    ),
)
def test_digest_consistent_false_robdd_payload_is_rejected() -> None:
    source = {
        "id": "src:audit:false-a",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "a" * 64},
    }
    target = {
        "id": "src:audit:false-b",
        "type": "SOURCE_DECLARATION",
        "attributes": {"statement_sha256": "b" * 64},
    }
    graph = {"nodes": [source, target], "edges": []}
    registry = {}

    with pytest.raises(GFYProofBridgeError):
        apply_gfyproof_certificate(
            graph,
            registry,
            _false_robdd_certificate(source, target),
        )

    assert graph["edges"] == []
    assert registry == {}
