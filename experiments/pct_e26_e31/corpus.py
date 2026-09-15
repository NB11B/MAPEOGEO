from __future__ import annotations

from dataclasses import dataclass
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .constants import (
    ACCEPTANCE_MANIFEST_RELATIVE_PATH,
    ALIGNMENTS_RELATIVE_PATH,
    KNOWLEDGE_BASELINE_SHA,
    KNOWLEDGE_GRAPH_BASENAME,
    SEMANTIC_RELATION_TYPES,
    SOLVER_BASELINE_SHA,
)
from .identity import compute_harness_sha, sha256_file, verify_frozen_checkout


@dataclass(frozen=True)
class KnowledgeCorpus:
    graph_path: Path
    graph: dict[str, Any]
    acceptance_manifest: dict[str, Any]
    node_by_id: dict[str, dict[str, Any]]
    edges_by_type: dict[str, tuple[dict[str, Any], ...]]
    semantic_edges: tuple[dict[str, Any], ...]
    canonical_objects: tuple[dict[str, Any], ...]
    source_declarations: tuple[dict[str, Any], ...]
    domains: tuple[str, ...]
    artifact_digests: dict[str, str]
    direct_graph_counts: dict[str, int]
    discrepancies: tuple[dict[str, Any], ...]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_graph(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve_graph_artifact(main_root: Path, repo_root: Path) -> Path:
    sealed_root = repo_root / ".crossbranch" / "frozen-main-artifact"
    if sealed_root.exists():
        matches = sorted(sealed_root.rglob(KNOWLEDGE_GRAPH_BASENAME))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(f"Multiple sealed graph artifacts found: {matches}")

    fallback = (
        main_root
        / "artifacts"
        / "analysis_v0_15_1"
        / KNOWLEDGE_GRAPH_BASENAME
    )
    if fallback.exists():
        return fallback
    raise FileNotFoundError(
        f"Frozen v0.15.1 graph artifact {KNOWLEDGE_GRAPH_BASENAME} not found"
    )


def _count_graph(graph: dict[str, Any]) -> tuple[dict[str, int], Counter[str], Counter[str]]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_types = Counter(str(node.get("type", "")) for node in nodes)
    edge_types = Counter(str(edge.get("type", "")) for edge in edges)
    semantic_count = sum(edge_types[relation] for relation in SEMANTIC_RELATION_TYPES)
    counts = {
        "nodes": len(nodes),
        "edges": len(edges),
        "source_declarations": node_types["SOURCE_DECLARATION"],
        "canonical_objects": node_types["CANONICAL_OBJECT"],
        "semantic_bridges": semantic_count,
        "same_semantics": edge_types["SAME_SEMANTICS"],
        "scoped_overlap": edge_types["SCOPED_OVERLAP"],
        "related_to": edge_types["RELATED_TO"],
    }
    return counts, node_types, edge_types


def _manifest_discrepancies(
    acceptance: dict[str, Any], direct: dict[str, int]
) -> list[dict[str, Any]]:
    dashboard = acceptance.get("primary_dashboard", {})
    edges = dashboard.get("edges_summary", {})
    checks = {
        "source_declarations": dashboard.get("N_source"),
        "canonical_objects": dashboard.get("N_canonical"),
        "edges": edges.get("total_edges"),
        "same_semantics": edges.get("SAME_SEMANTICS_bridges"),
        "scoped_overlap": edges.get("SCOPED_OVERLAP_bridges"),
        "related_to": edges.get("RELATED_TO_bridges"),
        "semantic_bridges": edges.get("total_cross_source_bridges"),
    }
    discrepancies: list[dict[str, Any]] = []
    for field, expected in checks.items():
        if expected is None:
            continue
        actual = direct[field]
        if actual != expected:
            discrepancies.append(
                {"field": field, "manifest": expected, "direct_graph": actual}
            )
    return discrepancies


def load_knowledge_corpus(main_root: Path, repo_root: Path | None = None) -> KnowledgeCorpus:
    repo_root = repo_root or main_root
    graph_path = _resolve_graph_artifact(main_root, repo_root)
    acceptance_path = main_root / ACCEPTANCE_MANIFEST_RELATIVE_PATH
    alignments_path = main_root / ALIGNMENTS_RELATIVE_PATH

    acceptance = _load_json(acceptance_path)
    expected_artifacts = acceptance.get("artifacts", {})

    graph_digest = sha256_file(graph_path)
    expected_graph_digest = expected_artifacts.get(KNOWLEDGE_GRAPH_BASENAME)
    if not expected_graph_digest:
        raise ValueError("Acceptance manifest does not bind the v0.15.1 graph artifact")
    if graph_digest != expected_graph_digest:
        raise ValueError(
            "Frozen graph artifact digest mismatch: "
            f"expected {expected_graph_digest}, got {graph_digest}"
        )

    alignment_digest = sha256_file(alignments_path)
    expected_alignment_digest = expected_artifacts.get("analysis_alignments_v0_15.json")
    if not expected_alignment_digest:
        raise ValueError("Acceptance manifest does not bind analysis alignments")
    if alignment_digest != expected_alignment_digest:
        raise ValueError(
            "Frozen alignment digest mismatch: "
            f"expected {expected_alignment_digest}, got {alignment_digest}"
        )

    graph = _load_graph(graph_path)
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    direct_counts, _, _ = _count_graph(graph)

    edge_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        edge_groups[str(edge.get("type", ""))].append(edge)

    canonical = tuple(node for node in nodes if node.get("type") == "CANONICAL_OBJECT")
    source = tuple(node for node in nodes if node.get("type") == "SOURCE_DECLARATION")
    semantic = tuple(
        edge for edge in edges if edge.get("type") in SEMANTIC_RELATION_TYPES
    )
    domains = tuple(
        sorted(
            {
                str(node.get("attributes", {}).get("domain"))
                for node in canonical
                if node.get("attributes", {}).get("domain")
            }
        )
    )

    return KnowledgeCorpus(
        graph_path=graph_path,
        graph=graph,
        acceptance_manifest=acceptance,
        node_by_id={str(node["id"]): node for node in nodes if "id" in node},
        edges_by_type={key: tuple(value) for key, value in sorted(edge_groups.items())},
        semantic_edges=semantic,
        canonical_objects=canonical,
        source_declarations=source,
        domains=domains,
        artifact_digests={
            KNOWLEDGE_GRAPH_BASENAME: graph_digest,
            "analysis_alignments_v0_15.json": alignment_digest,
        },
        direct_graph_counts=direct_counts,
        discrepancies=tuple(_manifest_discrepancies(acceptance, direct_counts)),
    )


def build_e26_manifest(main_root: Path, repo_root: Path) -> dict[str, Any]:
    solver_root = repo_root / ".crossbranch" / "frozen-solver"
    verify_frozen_checkout(main_root, KNOWLEDGE_BASELINE_SHA)
    verify_frozen_checkout(solver_root, SOLVER_BASELINE_SHA)

    corpus = load_knowledge_corpus(main_root, repo_root)
    _, node_types, edge_types = _count_graph(corpus.graph)

    return {
        "experiment_id": "E26_CROSS_BRANCH_CORPUS_BINDING",
        "status": "PASS",
        "solver_baseline_sha": SOLVER_BASELINE_SHA,
        "knowledge_baseline_sha": KNOWLEDGE_BASELINE_SHA,
        "campaign_harness_sha": compute_harness_sha(repo_root),
        "graph_artifact": KNOWLEDGE_GRAPH_BASENAME,
        "artifact_digests": corpus.artifact_digests,
        "direct_graph_counts": corpus.direct_graph_counts,
        "node_types": dict(sorted(node_types.items())),
        "edge_types": dict(sorted(edge_types.items())),
        "semantic_relation_types": list(SEMANTIC_RELATION_TYPES),
        "domains": list(corpus.domains),
        "discrepancies": list(corpus.discrepancies),
        "validity_gates": {
            "frozen_solver_ref": True,
            "frozen_knowledge_ref": True,
            "sealed_graph_digest": True,
            "alignment_digest": True,
            "separate_checkout_paths": solver_root.resolve() != main_root.resolve(),
        },
    }
