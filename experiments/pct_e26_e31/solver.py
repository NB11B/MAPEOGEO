from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable

from .cases import SanitizedCase
from .constants import SEMANTIC_RELATION_TYPES
from .probes import B4_PROBE_KEYS, build_graph_index, pair_probe_values


@dataclass(frozen=True)
class SolverResult:
    verdict: str
    predicted_relation: str | None
    ambiguity_set: tuple[str, ...]
    evidence_keys: tuple[str, ...]
    unsupported_probe_keys: tuple[str, ...]
    trace_digest: str


def _canonical_digest(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _eligible_training_edge(
    edge: dict[str, Any], nodes: dict[str, dict[str, Any]]
) -> bool:
    if edge.get("type") not in SEMANTIC_RELATION_TYPES:
        return False
    source = nodes.get(str(edge.get("source")))
    target = nodes.get(str(edge.get("target")))
    if not source or not target:
        return False
    if source.get("type") != "SOURCE_DECLARATION" or target.get("type") != "SOURCE_DECLARATION":
        return False
    a = source.get("attributes", {}).get("source_id")
    b = target.get("attributes", {}).get("source_id")
    return bool(a and b and a != b)


def _training_supports(
    case: SanitizedCase,
    selected_keys: tuple[str, ...],
) -> tuple[
    dict[str, dict[Any, frozenset[str]]],
    dict[str, dict[Any, int]],
]:
    graph = case.visible_graph
    index = build_graph_index(graph)
    nodes = index.nodes
    pair_cache: dict[tuple[str, str], dict[str, Any]] = {}
    class_support: dict[str, dict[Any, set[str]]] = {
        key: defaultdict(set) for key in selected_keys
    }
    value_counts: dict[str, Counter[Any]] = {key: Counter() for key in selected_keys}

    for edge in graph.get("edges", []):
        if not _eligible_training_edge(edge, nodes):
            continue
        source = str(edge["source"])
        target = str(edge["target"])
        pair = tuple(sorted((source, target)))
        if pair not in pair_cache:
            pair_cache[pair] = pair_probe_values(graph, source, target, index=index)
        features = pair_cache[pair]
        relation = str(edge["type"])
        for key in selected_keys:
            value = features[key]
            class_support[key][value].add(relation)
            value_counts[key][value] += 1

    frozen_support = {
        key: {value: frozenset(classes) for value, classes in values.items()}
        for key, values in class_support.items()
    }
    frozen_counts = {
        key: dict(counts) for key, counts in value_counts.items()
    }
    return frozen_support, frozen_counts


def compute_probe_vector(
    case: SanitizedCase,
    probe_keys: Iterable[str] | None = None,
) -> tuple[tuple[str, Any], ...]:
    keys = tuple(B4_PROBE_KEYS if probe_keys is None else probe_keys)
    index = build_graph_index(case.visible_graph)
    values = pair_probe_values(
        case.visible_graph,
        case.source_id,
        case.target_id,
        index=index,
    )
    return tuple((key, values[key]) for key in keys)


def solve_case(
    case: SanitizedCase,
    probe_keys: Iterable[str] | None = None,
) -> SolverResult:
    selected_keys = tuple(B4_PROBE_KEYS if probe_keys is None else probe_keys)
    candidates = set(SEMANTIC_RELATION_TYPES)
    evidence_keys: list[str] = []
    unsupported: list[str] = []
    trace_rows: list[dict[str, Any]] = []

    if selected_keys:
        supports, counts = _training_supports(case, selected_keys)
        target_vector = dict(compute_probe_vector(case, selected_keys))
        for key in selected_keys:
            value = target_vector[key]
            supported_classes = set(supports[key].get(value, frozenset()))
            support_count = counts[key].get(value, 0)
            if not supported_classes:
                unsupported.append(key)
                trace_rows.append(
                    {
                        "key": key,
                        "value": repr(value),
                        "support_count": 0,
                        "supported_classes": [],
                        "binding": False,
                    }
                )
                continue

            binding = supported_classes != set(SEMANTIC_RELATION_TYPES)
            if binding:
                evidence_keys.append(key)
                candidates &= supported_classes
            trace_rows.append(
                {
                    "key": key,
                    "value": repr(value),
                    "support_count": support_count,
                    "supported_classes": sorted(supported_classes),
                    "binding": binding,
                }
            )

    ambiguity = tuple(sorted(candidates))
    if len(ambiguity) == 1:
        verdict = "PASS"
        predicted = ambiguity[0]
    else:
        verdict = "NOT_ESTABLISHED"
        predicted = None

    trace_digest = _canonical_digest(
        {
            "case_id": case.case_id,
            "source_id": case.source_id,
            "target_id": case.target_id,
            "probe_keys": list(selected_keys),
            "trace": trace_rows,
            "ambiguity_set": list(ambiguity),
            "verdict": verdict,
        }
    )
    return SolverResult(
        verdict=verdict,
        predicted_relation=predicted,
        ambiguity_set=ambiguity,
        evidence_keys=tuple(evidence_keys),
        unsupported_probe_keys=tuple(unsupported),
        trace_digest=trace_digest,
    )
