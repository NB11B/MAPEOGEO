"""Real cross-repository De Morgan bridge round trip.

This uses the actual MAPEOGEO foundation declaration generator and alignment
metadata, then replays a certificate locally. An optional second case checks the real
GFYProof producer when its sibling checkout is available.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

try:
    from math2.bridge.mapeogeo import build_edge_certificate
    HAS_MATH2 = True
except ImportError:
    build_edge_certificate = None
    HAS_MATH2 = False

from mapeogeo.gfyproof_bridge import (
    apply_gfyproof_certificate, canonical_sha256, claim_contract_digest,
)
from scripts.compute_foundation_depth import node_identity_sha256
from scripts.compute_foundation_depth import compute_foundation_metrics
from scripts.foundation_contracts import build_foundation_contract_evidence
from scripts.foundation_intake import (
    STAGE,
    ingest_foundation_declarations,
)
from scripts.import_foundation_backfill import generate_foundation_declarations


ROOT = Path(__file__).resolve().parents[1]
GFYPROOF_COMMIT = "f3604eb65fb5f88456c66fd34521fc046ffede6c"

DE_MORGAN_ID = "srcdecl:foundation:logic:de_morgan_logic"
FOUNDATION_ID = "canonical:foundation:logic:propositional_calculus"
ADVANCED_ID = "canonical:linear_algebra:vector_space"


def _robdd_demorgan_payload() -> dict:
    # Law 1: not (p and q) == (not p) or (not q)
    return {
        "left": [
            "not",
            [
                "and",
                ["var", "p"],
                ["var", "q"],
            ],
        ],
        "right": [
            "or",
            ["not", ["var", "p"]],
            ["not", ["var", "q"]],
        ],
        "variable_order": ["p", "q"],
    }


def _real_foundation_slice() -> tuple[dict, dict, dict]:
    declarations = generate_foundation_declarations()
    evidence = build_foundation_contract_evidence(declarations)
    evidence_by_subject = {
        subject_id: item
        for item in evidence
        for subject_id in item.subject_ids
    }

    graph = {
        "nodes": [],
        "edges": [],
    }
    ingest_foundation_declarations(
        graph,
        declarations,
        evidence_by_subject=evidence_by_subject,
    )

    alignment_data = json.loads(
        (
            ROOT
            / "formal"
            / "foundation_alignments.json"
        ).read_text(
            encoding="utf-8"
        )
    )
    canonical_spec = next(
        item
        for item
        in alignment_data[
            "canonical_objects"
        ]
        if item["id"] == FOUNDATION_ID
    )
    representation_kinds = canonical_spec.get(
        "representation_kinds",
        ["abstract"],
    )
    foundation_node = {
        "id": canonical_spec["id"],
        "type": "CANONICAL_OBJECT",
        "label": canonical_spec["name"],
        "attributes": {
            "domain": canonical_spec.get(
                "domain",
                "Mathematical Foundations",
            ),
            "description": canonical_spec.get(
                "description",
                "",
            ),
            "is_foundation": True,
            "representation_diversity": representation_kinds,
            "diversity_count": len(
                representation_kinds
            ),
            "stage": STAGE,
        },
    }
    graph["nodes"].append(
        foundation_node
    )

    # Keep one real advanced ID in the slice so the grounding metric can
    # demonstrate that raw topology is not proof grounding.
    advanced_node = {
        "id": ADVANCED_ID,
        "type": "CANONICAL_OBJECT",
        "label": "Vector Space",
        "attributes": {
            "domain": "Linear Algebra",
            "is_foundation": False,
        },
    }
    graph["nodes"].append(
        advanced_node
    )

    source_node = next(
        node
        for node in graph["nodes"]
        if node["id"] == DE_MORGAN_ID
    )

    alignment = next(
        item
        for item
        in canonical_spec[
            "alignments"
        ]
        if item["source"]
        == DE_MORGAN_ID
    )
    rep_edge_id = (
        f"e:rep:{DE_MORGAN_ID}:{FOUNDATION_ID}"
    )
    graph["edges"].append(
        {
            "id": rep_edge_id,
            "type": "REPRESENTS",
            "source": DE_MORGAN_ID,
            "target": FOUNDATION_ID,
            "attributes": {
                "corpus": alignment[
                    "corpus"
                ],
                "cross_source_status": alignment.get(
                    "status",
                    "CROSS_SOURCE_SAME",
                ),
                "source_statement_sha256": source_node[
                    "attributes"
                ][
                    "statement_sha256"
                ],
                "stage": STAGE,
                "evidence_status": "UNVERIFIED",
            },
        }
    )

    # This is the real structural candidate from foundation_alignments.json.
    # It intentionally remains UNVERIFIED in this experiment.
    assert (
        ADVANCED_ID
        in canonical_spec[
            "upward_dependencies"
        ]
    )
    graph["edges"].append(
        {
            "id": (
                f"e:upward_dep:{FOUNDATION_ID}:{ADVANCED_ID}"
            ),
            "type": "UPWARD_FOUNDATION_DEPENDENCY",
            "source": FOUNDATION_ID,
            "target": ADVANCED_ID,
            "attributes": {
                "relation": "FOUNDATION_GROUNDS_ADVANCED",
                "relation_status": "STRUCTURAL_CANDIDATE",
                "evidence_status": "UNVERIFIED",
                "stage": STAGE,
            },
        }
    )

    return (
        graph,
        source_node,
        foundation_node,
    )


def _local_fixture_certificate(**kwargs) -> dict:
    """A synthetic envelope over real endpoints; not an authenticated producer."""
    source, target = kwargs["source_node"], kwargs["target_node"]
    claim = {
        "edge_type": kwargs["edge_type"],
        "source_id": source["id"], "target_id": target["id"],
        "source_identity_sha256": node_identity_sha256(source),
        "target_identity_sha256": node_identity_sha256(target),
        "claim_scope": kwargs["claim_scope"],
    }
    body = {
        **claim, "schema": "mapeogeo.gfyproof.edge-certificate.v2",
        "edge_id": kwargs["edge_id"],
        "claim_contract_digest": claim_contract_digest(**claim),
        "verifier_semantic_id": kwargs["verifier_semantic_id"],
        "verifier_scope": "finite Boolean equivalence fixture",
        "implementation_provenance": {"class": "local integration fixture"},
        "hardware_coverage": {"status": "HARDWARE_NOT_BOUND"},
        "proof_payload_digest": canonical_sha256(kwargs["proof_payload"], domain="gfyproof-mapeogeo-semantic-proof-payload-v2"),
        "proof_verdict": "PASS", "promotion_class": "PROOF_ELIGIBLE",
        "artifact_ref": kwargs["artifact_ref"],
        "producer": {"repository": "NB11B/GFYProof", "commit": kwargs["producer_commit"],
                     "verifier_id": "GFYPROOF_MAPEOGEO_SEMANTIC_BRIDGE_V2"},
    }
    return {**body, "certificate_digest": canonical_sha256(body, domain="gfyproof-mapeogeo-semantic-edge-certificate-v2")}


@pytest.mark.parametrize("producer", ["local_fixture", "external_gfyproof"])
def test_real_demorgan_round_trip_promotes_only_the_supported_edge(producer: str) -> None:
    if producer == "external_gfyproof" and not HAS_MATH2:
        pytest.skip("Optional external GFYProof producer is not installed; local replay is tested separately")
    make_certificate = build_edge_certificate if producer == "external_gfyproof" else _local_fixture_certificate
    (
        graph,
        source_node,
        foundation_node,
    ) = _real_foundation_slice()
    registry = {}

    before = compute_foundation_metrics(
        graph,
        edge_evidence_registry=registry,
        validated_root_ids={
            DE_MORGAN_ID
        },
    )
    assert before[
        "raw_topology_reachability"
    ][
        "advanced_canonical_objects_reachable"
    ] == 1
    assert before[
        "proof_eligible_grounding"
    ][
        "advanced_canonical_objects_reachable"
    ] == 0
    assert before[
        "diagnostics"
    ][
        "proof_eligible"
    ][
        "eligible_edges"
    ] == 0

    certificate = make_certificate(
        edge_id=(
            f"e:rep:{DE_MORGAN_ID}:{FOUNDATION_ID}"
        ),
        edge_type="REPRESENTS",
        source_node=source_node,
        target_node=foundation_node,
        claim_scope=(
            "De Morgan law 1 over all four Boolean assignments; "
            "independent ROBDD canonical equivalence"
        ),
        verifier_semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        proof_payload=_robdd_demorgan_payload(),
        producer_commit=GFYPROOF_COMMIT,
        artifact_ref=(
            "MAPEOGEO:"
            "foundation.logic.de_morgan.truth_table"
        ),
    )

    apply_gfyproof_certificate(
        graph,
        registry,
        certificate,
        proof_payload=_robdd_demorgan_payload(),
    )

    promoted = next(
        edge
        for edge in graph["edges"]
        if edge["id"]
        == (
            f"e:rep:{DE_MORGAN_ID}:{FOUNDATION_ID}"
        )
    )
    assert promoted[
        "attributes"
    ][
        "evidence_status"
    ] == "VERIFIED"
    assert promoted[
        "attributes"
    ][
        "cross_source_status"
    ] == "CROSS_SOURCE_SAME"
    assert promoted[
        "attributes"
    ][
        "external_verifier"
    ] == "GFYPROOF"

    after = compute_foundation_metrics(
        graph,
        edge_evidence_registry=registry,
        validated_root_ids={
            DE_MORGAN_ID
        },
    )

    # The real REP edge is now proof-eligible.
    assert after[
        "diagnostics"
    ][
        "proof_eligible"
    ][
        "eligible_edges"
    ] == 1

    # But the advanced vector-space dependency remains only structural, so
    # GFYProof must not inflate the advanced grounding metric.
    assert after[
        "proof_eligible_grounding"
    ][
        "advanced_canonical_objects_reachable"
    ] == 0

    evidence_nodes = [
        node
        for node in graph["nodes"]
        if node.get(
            "type"
        )
        == "EXECUTABLE_EVIDENCE"
    ]
    assert len(
        evidence_nodes
    ) == 1
    assert evidence_nodes[
        0
    ][
        "attributes"
    ][
        "verifier_semantic_id"
    ] == "GFY.ROBDD_EQUIVALENCE.v1"
