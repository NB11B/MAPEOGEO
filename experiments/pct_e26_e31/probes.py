from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Any

from .constants import SEMANTIC_RELATION_TYPES


@dataclass(frozen=True)
class GraphIndex:
    nodes: dict[str, dict[str, Any]]
    rep_targets: dict[str, frozenset[str]]
    rep_sources: dict[str, frozenset[str]]
    dep_out: dict[str, frozenset[str]]
    dep_in: dict[str, frozenset[str]]
    semantic_incident: dict[str, tuple[dict[str, Any], ...]]
    nonsemantic_incident: dict[str, tuple[tuple[str, str, str], ...]]


def _freeze_value(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple((k, _freeze_value(v)) for k, v in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze_value(v) for v in value), key=repr))
    return value


def _node_attr(node: dict[str, Any], name: str, default: Any = "UNKNOWN") -> Any:
    return node.get("attributes", {}).get(name, default)


def _pair(a: Any, b: Any) -> tuple[Any, Any]:
    return tuple(sorted((_freeze_value(a), _freeze_value(b)), key=repr))


def build_graph_index(graph: dict[str, Any]) -> GraphIndex:
    nodes = {str(node["id"]): node for node in graph.get("nodes", []) if "id" in node}
    rep_targets_mut: dict[str, set[str]] = defaultdict(set)
    rep_sources_mut: dict[str, set[str]] = defaultdict(set)
    dep_out_mut: dict[str, set[str]] = defaultdict(set)
    dep_in_mut: dict[str, set[str]] = defaultdict(set)
    sem_mut: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nonsem_mut: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for edge in graph.get("edges", []):
        typ = str(edge.get("type", ""))
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if typ == "REPRESENTS":
            rep_targets_mut[source].add(target)
            rep_sources_mut[target].add(source)
        if typ == "DEPENDS_ON":
            dep_out_mut[source].add(target)
            dep_in_mut[target].add(source)
        if typ in SEMANTIC_RELATION_TYPES:
            sem_mut[source].append(edge)
            sem_mut[target].append(edge)
        else:
            nonsem_mut[source].append(("OUT", typ, target))
            nonsem_mut[target].append(("IN", typ, source))

    return GraphIndex(
        nodes=nodes,
        rep_targets={k: frozenset(v) for k, v in rep_targets_mut.items()},
        rep_sources={k: frozenset(v) for k, v in rep_sources_mut.items()},
        dep_out={k: frozenset(v) for k, v in dep_out_mut.items()},
        dep_in={k: frozenset(v) for k, v in dep_in_mut.items()},
        semantic_incident={k: tuple(v) for k, v in sem_mut.items()},
        nonsemantic_incident={k: tuple(v) for k, v in nonsem_mut.items()},
    )


def _semantic_profile(index: GraphIndex, node_id: str, other_id: str) -> tuple[int, ...]:
    counter = Counter()
    target_pair = frozenset((node_id, other_id))
    for edge in index.semantic_incident.get(node_id, ()):
        endpoints = frozenset((str(edge.get("source")), str(edge.get("target"))))
        if endpoints == target_pair:
            continue
        counter[str(edge.get("type"))] += 1
    return tuple(counter[typ] for typ in SEMANTIC_RELATION_TYPES)


def _shared_nonsemantic_path_signature(
    index: GraphIndex, source_id: str, target_id: str
) -> tuple[tuple[str, str, int], ...]:
    a: dict[str, Counter[str]] = defaultdict(Counter)
    b: dict[str, Counter[str]] = defaultdict(Counter)
    for direction, typ, neighbor in index.nonsemantic_incident.get(source_id, ()):
        a[neighbor][f"{direction}:{typ}"] += 1
    for direction, typ, neighbor in index.nonsemantic_incident.get(target_id, ()):
        b[neighbor][f"{direction}:{typ}"] += 1

    counts: Counter[tuple[str, str]] = Counter()
    for midpoint in set(a) & set(b):
        for left, lc in a[midpoint].items():
            for right, rc in b[midpoint].items():
                counts[(left, right)] += lc * rc
    return tuple(sorted((left, right, count) for (left, right), count in counts.items()))


def _shortest_nonsemantic_distance(index: GraphIndex, source_id: str, target_id: str) -> int | None:
    if source_id == target_id:
        return 0
    queue: deque[tuple[str, int]] = deque([(source_id, 0)])
    seen = {source_id}
    while queue:
        node, dist = queue.popleft()
        if dist >= 4:
            continue
        for _, _, neighbor in index.nonsemantic_incident.get(node, ()):
            if neighbor == target_id:
                return dist + 1
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, dist + 1))
    return None


def pair_probe_values(
    graph: dict[str, Any], source_id: str, target_id: str, *, index: GraphIndex | None = None
) -> dict[str, Any]:
    index = index or build_graph_index(graph)
    source = index.nodes[source_id]
    target = index.nodes[target_id]
    sa = source.get("attributes", {})
    ta = target.get("attributes", {})

    common_canonical = sorted(
        index.rep_targets.get(source_id, frozenset())
        & index.rep_targets.get(target_id, frozenset())
    )
    canonical_domains: list[str] = []
    canonical_diversity: list[int] = []
    canonical_profiles: list[tuple[str, ...]] = []
    canonical_source_multiplicity: list[int] = []
    for canonical_id in common_canonical:
        canonical = index.nodes.get(canonical_id, {})
        attrs = canonical.get("attributes", {})
        canonical_domains.append(str(attrs.get("domain", "UNKNOWN")))
        canonical_diversity.append(int(attrs.get("diversity_count", 0) or 0))
        canonical_profiles.append(
            tuple(sorted(str(v) for v in attrs.get("representation_diversity", []) or []))
        )
        represented_source_ids = {
            str(index.nodes.get(node_id, {}).get("attributes", {}).get("source_id"))
            for node_id in index.rep_sources.get(canonical_id, frozenset())
            if index.nodes.get(node_id, {}).get("type") == "SOURCE_DECLARATION"
            and index.nodes.get(node_id, {}).get("attributes", {}).get("source_id")
        }
        canonical_source_multiplicity.append(len(represented_source_ids))

    dep_forward = target_id in index.dep_out.get(source_id, frozenset())
    dep_reverse = source_id in index.dep_out.get(target_id, frozenset())
    if dep_forward and dep_reverse:
        dep_orientation = "BOTH"
    elif dep_forward:
        dep_orientation = "FORWARD"
    elif dep_reverse:
        dep_orientation = "REVERSE"
    else:
        dep_orientation = "NONE"

    source_profile = _semantic_profile(index, source_id, target_id)
    target_profile = _semantic_profile(index, target_id, source_id)

    probes = {
        "source_pair": _pair(sa.get("source_id", "UNKNOWN"), ta.get("source_id", "UNKNOWN")),
        "direct_status_pair": _pair(sa.get("direct_status", "UNKNOWN"), ta.get("direct_status", "UNKNOWN")),
        "decl_type_pair": _pair(sa.get("decl_type", "UNKNOWN"), ta.get("decl_type", "UNKNOWN")),
        "eo_tag_count_pair": _pair(len(sa.get("eo_tags", []) or []), len(ta.get("eo_tags", []) or [])),
        "geo_tag_count_pair": _pair(len(sa.get("geo_tags", []) or []), len(ta.get("geo_tags", []) or [])),
        "representation_kind_count_pair": _pair(
            len(sa.get("representation_kinds", []) or []),
            len(ta.get("representation_kinds", []) or []),
        ),
        "common_canonical_count": len(common_canonical),
        "common_canonical_domains": tuple(sorted(canonical_domains)),
        "common_canonical_diversity": tuple(sorted(canonical_diversity)),
        "common_canonical_profiles": tuple(sorted(canonical_profiles)),
        "common_canonical_source_multiplicity": tuple(sorted(canonical_source_multiplicity)),
        "dependency_orientation": dep_orientation,
        "common_dependency_targets": len(
            index.dep_out.get(source_id, frozenset())
            & index.dep_out.get(target_id, frozenset())
        ),
        "dependency_out_degree_pair": _pair(
            len(index.dep_out.get(source_id, frozenset())),
            len(index.dep_out.get(target_id, frozenset())),
        ),
        "dependency_in_degree_pair": _pair(
            len(index.dep_in.get(source_id, frozenset())),
            len(index.dep_in.get(target_id, frozenset())),
        ),
        "semantic_degree_profile_pair": _pair(source_profile, target_profile),
        "shared_nonsemantic_path_signature": _shared_nonsemantic_path_signature(
            index, source_id, target_id
        ),
        "shortest_nonsemantic_distance": _shortest_nonsemantic_distance(
            index, source_id, target_id
        ),
    }
    return {key: _freeze_value(value) for key, value in probes.items()}


B1_PROBE_KEYS = (
    "source_pair",
    "direct_status_pair",
    "decl_type_pair",
    "eo_tag_count_pair",
    "geo_tag_count_pair",
    "representation_kind_count_pair",
)

B2_PROBE_KEYS = B1_PROBE_KEYS + (
    "common_canonical_count",
    "semantic_degree_profile_pair",
)

B3_PROBE_KEYS = B2_PROBE_KEYS + (
    "dependency_orientation",
    "common_dependency_targets",
    "dependency_out_degree_pair",
    "dependency_in_degree_pair",
    "shared_nonsemantic_path_signature",
    "shortest_nonsemantic_distance",
)

B4_PROBE_KEYS = B3_PROBE_KEYS + (
    "common_canonical_domains",
    "common_canonical_diversity",
    "common_canonical_profiles",
    "common_canonical_source_multiplicity",
)
