"""Mutation tests for raw topology versus proof-eligible grounding."""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.compute_foundation_depth import (
    bound_edge_evidence_sha256,
    build_registered_edge_evidence,
    compute_foundation_metrics,
    node_identity_sha256,
)
from scripts.foundation_intake import (
    add_edge,
    compute_foundation_dashboard,
    ingest_foundation_canonical_alignments,
    partition_source_declarations,
    resolve_foundation_evidence_path,
    save_graph_gz,
)
from scripts.complex_analysis_intake_v0_19 import authoritative_source_registry


HEX = hashlib.sha256(b"evidence").hexdigest()


def _node(node_id: str, node_type: str, **attrs: object) -> dict:
    return {"id": node_id, "type": node_type, "attributes": attrs}


def _graph(edges: list[dict]) -> dict:
    return {
        "nodes": [
            _node(
                "srcdecl:foundation:logic:de_morgan_logic",
                "SOURCE_DECLARATION",
                source_id="FOUNDATION_MATHEMATICS_BASE",
                corpus="FOUNDATION",
                statement_sha256="a45048e4567c3a6ba39ca5ed4674f68d2d1aef830429319c6e3754c7ab245152",
            ),
            _node("canonical:foundation:logic", "CANONICAL_OBJECT", is_foundation=True),
            _node("canonical:advanced:target", "CANONICAL_OBJECT", domain="Test"),
            _node("wound:test", "WOUND"),
        ],
        "edges": edges,
    }


def _edge(edge_id: str, edge_type: str, source: str, target: str, **attrs: object) -> dict:
    return {"id": edge_id, "type": edge_type, "source": source, "target": target, "attributes": attrs}


def test_wound_only_path_never_establishes_proof_grounding() -> None:
    graph = _graph([
        _edge("w1", "HAS_WOUND", "srcdecl:foundation:logic:de_morgan_logic", "wound:test"),
        _edge("w2", "RELATED_TO", "wound:test", "canonical:advanced:target"),
    ])
    metrics = compute_foundation_metrics(graph)
    assert metrics["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0


def test_rejected_reverse_dangling_and_unverified_edges_are_ineligible() -> None:
    graph = _graph([
        _edge("rejected", "UPWARD_FOUNDATION_DEPENDENCY", "canonical:foundation:logic", "canonical:advanced:target", status="REJECTED"),
        _edge("reverse", "UPWARD_FOUNDATION_DEPENDENCY", "canonical:advanced:target", "canonical:foundation:logic", evidence_status="VERIFIED", evidence_digest=HEX, evidence_subject_ids=["canonical:advanced:target", "canonical:foundation:logic"]),
        _edge("related", "RELATED_TO", "canonical:foundation:logic", "canonical:advanced:target"),
        _edge("dangling", "SAME_SEMANTICS", "canonical:foundation:logic", "missing:node", evidence_status="VERIFIED", evidence_digest=HEX, evidence_subject_ids=["canonical:foundation:logic", "missing:node"]),
    ])
    metrics = compute_foundation_metrics(graph)
    assert metrics["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0
    assert metrics["diagnostics"]["dangling_edges"] == 1


def test_verified_directional_chain_is_proof_eligible() -> None:
    source = "srcdecl:foundation:logic:de_morgan_logic"
    foundation = "canonical:foundation:logic"
    target = "canonical:advanced:target"
    source_hash = "a45048e4567c3a6ba39ca5ed4674f68d2d1aef830429319c6e3754c7ab245152"
    graph = _graph([])
    nodes = {node["id"]: node for node in graph["nodes"]}

    rep, rep_record = build_registered_edge_evidence(
        edge_id="rep",
        edge_type="REPRESENTS",
        source=source,
        target=foundation,
        nodes=nodes,
        source_statement_sha256=source_hash,
    )
    up, up_record = build_registered_edge_evidence(
        edge_id="up",
        edge_type="UPWARD_FOUNDATION_DEPENDENCY",
        source=foundation,
        target=target,
        nodes=nodes,
    )
    graph["edges"] = [rep, up]
    registry = {
        rep_record.evidence_digest: rep_record,
        up_record.evidence_digest: up_record,
    }
    metrics = compute_foundation_metrics(
        graph,
        edge_evidence_registry=registry,
        validated_root_ids={source},
    )
    proof = metrics["proof_eligible_grounding"]
    assert proof["advanced_canonical_objects_reachable"] == 1
    assert proof["foundation_reachability_pct"] == 100.0


def test_source_partition_uses_registry_metadata_and_includes_decl_namespace() -> None:
    registry = authoritative_source_registry()
    gallier = "srcdecl:definition:2_1"
    ahlfors = "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:5.4"
    nodes = [
        _node(
            gallier,
            "STATEMENT",
            source="GALLIER_QUAINTANCE_MATH_DEEP",
            source_segment_sha256="1" * 64,
            independent_profile={"statement_sha256": registry[gallier]["statement_sha256"]},
        ),
        _node(
            ahlfors,
            "SOURCE_DECLARATION",
            source_id="AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979",
            corpus="AHLFORS",
            statement_sha256=registry[ahlfors]["statement_sha256"],
        ),
        _node(
            "srcdecl:foundation:logic:de_morgan_logic",
            "SOURCE_DECLARATION",
            source_id="FOUNDATION_MATHEMATICS_BASE",
            corpus="FOUNDATION",
            statement_sha256="a45048e4567c3a6ba39ca5ed4674f68d2d1aef830429319c6e3754c7ab245152",
        ),
    ]
    partition = partition_source_declarations(nodes)
    assert partition["gallier_quaintance_SA"] == 1
    assert partition["ahlfors_krantz_SG"] == 1
    assert partition["foundation_base_S0"] == 1


def test_dashboard_never_filters_registered_declarations_by_id_prefix() -> None:
    node_id = "decl:AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979:THEOREM:5.4"
    graph = {
        "nodes": [
            _node(
                node_id,
                "SOURCE_DECLARATION",
                source_id="AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979",
                corpus="AHLFORS",
                statement_sha256=authoritative_source_registry()[node_id]["statement_sha256"],
            )
        ],
        "edges": [],
    }
    dashboard = compute_foundation_dashboard(
        graph,
        {
            "total_foundation_canonical_objects": 0,
            "representation_diversity": {},
        },
        compute_foundation_metrics(graph),
        {
            "verified_declarations": 0,
            "unverified_declarations": 0,
            "kernel_verified_declarations": 0,
        },
    )
    assert dashboard["N_source_total"] == 1
    assert dashboard["N_source_breakdown"]["ahlfors_krantz_SG"] == 1


def test_source_partition_rejects_unregistered_identity_even_with_known_source_metadata() -> None:
    with pytest.raises(ValueError, match="authoritative source registry"):
        partition_source_declarations(
            [
                _node(
                    "opaque-source-identity",
                    "SOURCE_DECLARATION",
                    source_id="AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979",
                    corpus="AHLFORS",
                    statement_sha256="2" * 64,
                )
            ]
        )


def test_forged_endpoint_binding_is_not_proof_eligible() -> None:
    source = "srcdecl:foundation:logic:de_morgan_logic"
    target = "canonical:advanced:target"
    graph = _graph([
        _edge(
            "forged",
            "SAME_SEMANTICS",
            source,
            target,
            evidence_status="VERIFIED",
            evidence_digest=HEX,
            evidence_contract_digest=HEX,
            evidence_subject_ids=[source, target],
            endpoint_identity_sha256={source: "0" * 64, target: "0" * 64},
        )
    ])
    metrics = compute_foundation_metrics(graph)
    assert metrics["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0


def test_foundation_canonical_is_not_an_unproved_proof_root() -> None:
    foundation = "canonical:foundation:logic"
    target = "canonical:advanced:target"
    graph = _graph([])
    nodes = {node["id"]: node for node in graph["nodes"]}
    endpoints = {
        foundation: node_identity_sha256(nodes[foundation]),
        target: node_identity_sha256(nodes[target]),
    }
    graph["edges"] = [
        _edge(
            "verified-up-only",
            "UPWARD_FOUNDATION_DEPENDENCY",
            foundation,
            target,
            evidence_status="VERIFIED",
            evidence_contract_digest=HEX,
            evidence_subject_ids=[foundation, target],
            endpoint_identity_sha256=endpoints,
            evidence_digest=bound_edge_evidence_sha256(
                "UPWARD_FOUNDATION_DEPENDENCY", foundation, target, endpoints, HEX
            ),
        )
    ]
    metrics = compute_foundation_metrics(graph)
    assert metrics["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0


def test_self_signed_unknown_edge_evidence_and_unverified_root_are_rejected() -> None:
    source = "srcdecl:foundation:logic:de_morgan_logic"
    foundation = "canonical:foundation:logic"
    target = "canonical:advanced:target"
    graph = _graph([])
    nodes = {node["id"]: node for node in graph["nodes"]}

    def forged(edge_type: str, edge_source: str, edge_target: str) -> dict:
        endpoint_hashes = {
            edge_source: node_identity_sha256(nodes[edge_source]),
            edge_target: node_identity_sha256(nodes[edge_target]),
        }
        return {
            "evidence_status": "VERIFIED",
            "evidence_contract_digest": HEX,
            "evidence_subject_ids": [edge_source, edge_target],
            "endpoint_identity_sha256": endpoint_hashes,
            "evidence_digest": bound_edge_evidence_sha256(
                edge_type, edge_source, edge_target, endpoint_hashes, HEX
            ),
        }

    graph["edges"] = [
        _edge(
            "rep",
            "REPRESENTS",
            source,
            foundation,
            **forged("REPRESENTS", source, foundation),
            source_statement_sha256=nodes[source]["attributes"]["statement_sha256"],
        ),
        _edge(
            "up",
            "UPWARD_FOUNDATION_DEPENDENCY",
            foundation,
            target,
            **forged("UPWARD_FOUNDATION_DEPENDENCY", foundation, target),
        ),
    ]
    assert compute_foundation_metrics(graph)["proof_eligible_grounding"][
        "advanced_canonical_objects_reachable"
    ] == 0
    assert compute_foundation_metrics(
        graph,
        edge_evidence_registry={},
        validated_root_ids={source},
    )["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0


def test_relation_status_rejected_cannot_be_hidden_by_verified_wrapper() -> None:
    source = "srcdecl:foundation:logic:de_morgan_logic"
    target = "canonical:advanced:target"
    graph = _graph([])
    nodes = {node["id"]: node for node in graph["nodes"]}
    edge, record = build_registered_edge_evidence(
        edge_id="same",
        edge_type="SAME_SEMANTICS",
        source=source,
        target=target,
        nodes=nodes,
    )
    edge["attributes"]["relation_status"] = "REJECTED"
    graph["edges"] = [edge]
    metrics = compute_foundation_metrics(
        graph,
        edge_evidence_registry={record.evidence_digest: record},
        validated_root_ids={source},
    )
    assert metrics["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0


def test_semantic_edge_type_must_match_endpoint_node_types() -> None:
    source = "srcdecl:foundation:logic:de_morgan_logic"
    target = "canonical:advanced:target"
    graph = _graph([])
    nodes = {node["id"]: node for node in graph["nodes"]}
    edge, record = build_registered_edge_evidence(
        edge_id="ill-typed-same",
        edge_type="SAME_SEMANTICS",
        source=source,
        target=target,
        nodes=nodes,
    )
    graph["edges"] = [edge]
    metrics = compute_foundation_metrics(
        graph,
        edge_evidence_registry={record.evidence_digest: record},
        validated_root_ids={source},
    )
    assert metrics["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0


def test_duplicate_edge_id_requires_an_identical_payload() -> None:
    original = _edge("same-id", "RELATED_TO", "a", "b", status="ACTIVE")
    edges = [original]
    edge_ids = {"same-id"}
    assert add_edge(edges, edge_ids, dict(original)) is False
    with pytest.raises(ValueError, match="edge ID collision"):
        add_edge(
            edges,
            edge_ids,
            _edge("same-id", "SAME_SEMANTICS", "a", "b", status="ACTIVE"),
        )


def test_missing_upward_dependency_target_fails_closed(tmp_path) -> None:
    source = _node(
        "srcdecl:foundation:test",
        "SOURCE_DECLARATION",
        source_id="FOUNDATION_MATHEMATICS_BASE",
        statement_sha256="3" * 64,
    )
    alignments = {
        "canonical_objects": [
            {
                "id": "canonical:foundation:test",
                "name": "Test",
                "alignments": [
                    {
                        "source": source["id"],
                        "corpus": "FOUNDATION",
                        "status": "CROSS_SOURCE_SAME",
                    }
                ],
                "upward_dependencies": ["canonical:missing"],
            }
        ]
    }
    path = tmp_path / "alignments.json"
    path.write_text(json.dumps(alignments), encoding="utf-8")
    with pytest.raises(ValueError, match="Upward target.*not found"):
        ingest_foundation_canonical_alignments(
            {"nodes": [source], "edges": []},
            path,
        )


def test_foundation_test_runs_write_evidence_only_to_the_requested_output(tmp_path) -> None:
    assert resolve_foundation_evidence_path(tmp_path, None).parent == tmp_path


def test_foundation_graph_serialization_is_deterministic(tmp_path) -> None:
    graph = {"nodes": [{"id": "n", "type": "CANONICAL_OBJECT", "attributes": {}}], "edges": []}
    first = tmp_path / "a.json.gz"
    second = tmp_path / "b.json.gz"
    save_graph_gz(graph, first)
    save_graph_gz(graph, second)
    assert first.read_bytes() == second.read_bytes()
