from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .constants import SEMANTIC_RELATION_TYPES
from .corpus import KnowledgeCorpus


def _canonical_digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _unordered_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


@dataclass(frozen=True)
class HeldoutCase:
    case_id: str
    tier: str
    edge_id: str
    source_id: str
    target_id: str
    sealed_relation: str
    hidden_edge_ids: tuple[str, ...]
    verifier_metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SanitizedCase:
    case_id: str
    tier: str
    source_id: str
    target_id: str
    visible_graph: dict[str, Any]
    visible_edge_ids: tuple[str, ...]
    direct_target_labels: tuple[str, ...]
    metadata: dict[str, Any]


def _is_cross_source_source_declaration_edge(
    corpus: KnowledgeCorpus, edge: dict[str, Any]
) -> bool:
    if edge.get("type") not in SEMANTIC_RELATION_TYPES:
        return False
    source = corpus.node_by_id.get(str(edge.get("source")))
    target = corpus.node_by_id.get(str(edge.get("target")))
    if not source or not target:
        return False
    if source.get("type") != "SOURCE_DECLARATION" or target.get("type") != "SOURCE_DECLARATION":
        return False
    source_corpus = source.get("attributes", {}).get("source_id")
    target_corpus = target.get("attributes", {}).get("source_id")
    return bool(source_corpus and target_corpus and source_corpus != target_corpus)


def _semantic_edges_for_pair(
    corpus: KnowledgeCorpus, source_id: str, target_id: str
) -> tuple[str, ...]:
    pair = _unordered_pair(source_id, target_id)
    return tuple(
        sorted(
            str(edge["id"])
            for edge in corpus.semantic_edges
            if _unordered_pair(str(edge.get("source")), str(edge.get("target"))) == pair
        )
    )


def build_r1_cases(corpus: KnowledgeCorpus) -> list[HeldoutCase]:
    cases: list[HeldoutCase] = []
    for edge in sorted(corpus.semantic_edges, key=lambda row: str(row.get("id", ""))):
        if not _is_cross_source_source_declaration_edge(corpus, edge):
            continue
        source_id = str(edge["source"])
        target_id = str(edge["target"])
        payload = {
            "tier": "R1",
            "edge_id": str(edge["id"]),
            "source_id": source_id,
            "target_id": target_id,
            "sealed_relation": str(edge["type"]),
        }
        canonical_hint = (
            edge.get("attributes", {}).get("canonical_id")
            or edge.get("attributes", {}).get("canonical_object")
            or ""
        )
        cases.append(
            HeldoutCase(
                case_id=_canonical_digest(payload),
                tier="R1",
                edge_id=str(edge["id"]),
                source_id=source_id,
                target_id=target_id,
                sealed_relation=str(edge["type"]),
                # Remove every semantic label directly joining the queried endpoints.
                # Parallel semantic edges can legitimately encode distinct canonical
                # contexts; leaving any one of them visible would leak a target label.
                hidden_edge_ids=_semantic_edges_for_pair(corpus, source_id, target_id),
                verifier_metadata=(("canonical_hint", str(canonical_hint)),),
            )
        )
    return cases


def sanitize_case(corpus: KnowledgeCorpus, case: HeldoutCase) -> SanitizedCase:
    hidden = set(case.hidden_edge_ids)
    visible_edges: list[dict[str, Any]] = []
    for original in corpus.graph.get("edges", []):
        edge_id = str(original.get("id", ""))
        if edge_id in hidden:
            continue
        edge = deepcopy(original)
        # cross_source_status is a redundant answer label carried on REPRESENTS
        # edges in the expanded graph. Remove it globally from solver-visible data.
        if edge.get("type") == "REPRESENTS":
            attrs = dict(edge.get("attributes", {}))
            attrs.pop("cross_source_status", None)
            edge["attributes"] = attrs
        visible_edges.append(edge)

    visible_graph = {
        key: deepcopy(value)
        for key, value in corpus.graph.items()
        if key not in {"edges"}
    }
    visible_graph["edges"] = visible_edges

    pair = _unordered_pair(case.source_id, case.target_id)
    direct_labels = tuple(
        sorted(
            str(edge["type"])
            for edge in visible_edges
            if edge.get("type") in SEMANTIC_RELATION_TYPES
            and _unordered_pair(str(edge.get("source")), str(edge.get("target"))) == pair
        )
    )

    return SanitizedCase(
        case_id=case.case_id,
        tier=case.tier,
        source_id=case.source_id,
        target_id=case.target_id,
        visible_graph=visible_graph,
        visible_edge_ids=tuple(sorted(str(edge.get("id", "")) for edge in visible_edges)),
        direct_target_labels=direct_labels,
        metadata={"tier": case.tier, "task": "RELATION_CLASSIFICATION"},
    )
