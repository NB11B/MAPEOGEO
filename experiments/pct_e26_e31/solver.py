from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable

from .cases import SanitizedCase
from .constants import SEMANTIC_RELATION_TYPES
from .probes import B4_PROBE_KEYS, GraphIndex, build_graph_index, pair_probe_values


@dataclass(frozen=True)
class SolverResult:
    verdict: str
    predicted_relation: str | None
    ambiguity_set: tuple[str, ...]
    evidence_keys: tuple[str, ...]
    unsupported_probe_keys: tuple[str, ...]
    trace_digest: str


@dataclass
class SolverModel:
    selected_keys: tuple[str, ...]
    index: GraphIndex
    supports: dict[str, dict[Any, frozenset[str]]]
    counts: dict[str, dict[Any, int]]


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


def fit_solver_model(
    case: SanitizedCase,
    probe_keys: Iterable[str] | None = None,
) -> SolverModel:
    selected_keys = tuple(B4_PROBE_KEYS if probe_keys is None else probe_keys)
    graph = case.visible_graph
    index = build_graph_index(graph)
    nodes = index.nodes
    pair_cache: dict[tuple[str, str], dict[str, Any]] = {}
    class_support: dict[str, dict[Any, set[str]]] = {
        key: defaultdict(set) for key in selected_keys
    }
    value_counts: dict[str, Counter[Any]] = {
        key: Counter() for key in selected_keys
    }

    for edge in graph.get("edges", []):
        if not _eligible_training_edge(edge, nodes):
            continue
        source = str(edge["source"])
        target = str(edge["target"])
        pair = tuple(sorted((source, target)))
        if pair not in pair_cache:
            pair_cache[pair] = pair_probe_values(
                graph, source, target, index=index
            )
        features = pair_cache[pair]
        relation = str(edge["type"])
        for key in selected_keys:
            value = features[key]
            class_support[key][value].add(relation)
            value_counts[key][value] += 1

    return SolverModel(
        selected_keys=selected_keys,
        index=index,
        supports={
            key: {
                value: frozenset(classes)
                for value, classes in values.items()
            }
            for key, values in class_support.items()
        },
        counts={key: dict(counts) for key, counts in value_counts.items()},
    )


def compute_probe_vector(
    case: SanitizedCase,
    probe_keys: Iterable[str] | None = None,
    *,
    index: GraphIndex | None = None,
) -> tuple[tuple[str, Any], ...]:
    keys = tuple(B4_PROBE_KEYS if probe_keys is None else probe_keys)
    index = index or build_graph_index(case.visible_graph)
    values = pair_probe_values(
        case.visible_graph,
        case.source_id,
        case.target_id,
        index=index,
    )
    return tuple((key, values[key]) for key in keys)


def _precondition(
    case: SanitizedCase, index: GraphIndex
) -> tuple[str, str] | None:
    if case.direct_target_labels:
        return "INVALID", "DIRECT_TARGET_SEMANTIC_LABEL_PRESENT"

    source = index.nodes.get(case.source_id)
    target = index.nodes.get(case.target_id)
    if not source or not target:
        return "INVALID", "MISSING_TARGET_ENDPOINT"
    if source.get("type") != "SOURCE_DECLARATION" or target.get("type") != "SOURCE_DECLARATION":
        return "INVALID", "ENDPOINT_TYPE_MISMATCH"

    source_corpus = source.get("attributes", {}).get("source_id")
    target_corpus = target.get("attributes", {}).get("source_id")
    if not source_corpus or not target_corpus:
        return "INVALID", "MISSING_SOURCE_BINDING"
    if source_corpus == target_corpus:
        return "INVALID", "NOT_CROSS_SOURCE"

    shared_canonical = (
        index.rep_targets.get(case.source_id, frozenset())
        & index.rep_targets.get(case.target_id, frozenset())
    )
    if not shared_canonical:
        return "NOT_ESTABLISHED", "NO_SHARED_CANONICAL_SUPPORT"
    return None


def _early_result(
    case: SanitizedCase,
    selected_keys: tuple[str, ...],
    verdict: str,
    reason: str,
) -> SolverResult:
    ambiguity = (
        tuple(SEMANTIC_RELATION_TYPES)
        if verdict == "NOT_ESTABLISHED"
        else ()
    )
    return SolverResult(
        verdict=verdict,
        predicted_relation=None,
        ambiguity_set=ambiguity,
        evidence_keys=(),
        unsupported_probe_keys=(),
        trace_digest=_canonical_digest(
            {
                "case_id": case.case_id,
                "source_id": case.source_id,
                "target_id": case.target_id,
                "probe_keys": list(selected_keys),
                "verdict": verdict,
                "reason": reason,
            }
        ),
    )


def solve_with_model(
    case: SanitizedCase,
    model: SolverModel,
    probe_keys: Iterable[str] | None = None,
) -> SolverResult:
    selected_keys = tuple(model.selected_keys if probe_keys is None else probe_keys)
    unknown = set(selected_keys) - set(model.selected_keys)
    if unknown:
        raise ValueError(f"Model does not contain requested probe keys: {sorted(unknown)}")

    blocked = _precondition(case, model.index)
    if blocked is not None:
        return _early_result(case, selected_keys, blocked[0], blocked[1])

    candidates = set(SEMANTIC_RELATION_TYPES)
    evidence_keys: list[str] = []
    unsupported: list[str] = []
    trace_rows: list[dict[str, Any]] = []

    target_vector = dict(
        compute_probe_vector(case, selected_keys, index=model.index)
    )
    for key in selected_keys:
        value = target_vector[key]
        supported_classes = set(model.supports[key].get(value, frozenset()))
        support_count = model.counts[key].get(value, 0)
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


def solve_case(
    case: SanitizedCase,
    probe_keys: Iterable[str] | None = None,
) -> SolverResult:
    selected_keys = tuple(B4_PROBE_KEYS if probe_keys is None else probe_keys)
    model = fit_solver_model(case, selected_keys)
    return solve_with_model(case, model, selected_keys)
