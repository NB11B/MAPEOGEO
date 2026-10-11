from __future__ import annotations

import argparse
import json
from collections import deque
from typing import Any

from graph_io import load_records, split_records


DOCUMENTARY_EDGE_TYPES = {
    "AUTHORED",
    "COAUTHORED",
    "PUBLISHED_IN",
    "PUBLISHED_BY",
    "AFFILIATED_WITH",
    "PRESENTED_AT",
    "CITES",
    "MENTIONS",
    "CORRESPONDED_WITH",
    "RESPONDED_TO",
    "ASSERTS",
    "SUPPORTS",
    "EXTRACTED_FROM",
    "DOCUMENTED_INFLUENCE",
    "USES_CONCEPT_FROM",
    "USES_EQUATION_FROM",
}

SOURCE_NATIVE_NAMESPACES = {"SOV", "RUS", "CASE", "OPEN"}


def load() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    records = load_records()
    nodes, edges = split_records(records)
    return {node["id"]: node for node in nodes}, edges


def dump(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def edge_allowed(
    edge: dict[str, Any],
    *,
    documented_only: bool,
    source_native_only: bool,
) -> bool:
    if documented_only and edge["edge_type"] not in DOCUMENTARY_EDGE_TYPES:
        return False
    if source_native_only and edge.get("namespace") not in SOURCE_NATIVE_NAMESPACES:
        return False
    return True


def neighbors(
    node_id: str,
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    direction: str,
    edge_types: set[str] | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for edge in edges:
        if edge_types and edge["edge_type"] not in edge_types:
            continue
        match_out = direction in {"out", "both"} and edge["source"] == node_id
        match_in = direction in {"in", "both"} and edge["target"] == node_id
        if not (match_out or match_in):
            continue
        other = edge["target"] if match_out else edge["source"]
        out.append({"edge": edge, "other": nodes.get(other)})
    return out


def shortest_path(
    start: str,
    end: str,
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    max_depth: int,
    documented_only: bool,
    source_native_only: bool,
) -> list[dict[str, Any]] | None:
    adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for edge in edges:
        if not edge_allowed(
            edge,
            documented_only=documented_only,
            source_native_only=source_native_only,
        ):
            continue
        adjacency.setdefault(edge["source"], []).append((edge["target"], edge))
        adjacency.setdefault(edge["target"], []).append((edge["source"], edge))

    queue = deque([(start, [])])
    seen = {start}
    while queue:
        current, path = queue.popleft()
        if len(path) >= max_depth:
            continue
        for nxt, edge in adjacency.get(current, []):
            if nxt in seen:
                continue
            next_path = path + [{"from": current, "edge": edge, "to": nxt}]
            if nxt == end:
                return next_path
            seen.add(nxt)
            queue.append((nxt, next_path))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Query canonical SOVCTX-KG JSONL.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stats")

    p_node = sub.add_parser("node")
    p_node.add_argument("id")

    p_neigh = sub.add_parser("neighbors")
    p_neigh.add_argument("id")
    p_neigh.add_argument("--direction", choices=("in", "out", "both"), default="both")
    p_neigh.add_argument("--edge-type", action="append", default=[])

    p_op = sub.add_parser("operator")
    p_op.add_argument("id")

    sub.add_parser("open")

    p_claims = sub.add_parser("claims")
    p_claims.add_argument("--source")

    p_path = sub.add_parser("path")
    p_path.add_argument("start")
    p_path.add_argument("end")
    p_path.add_argument("--max-depth", type=int, default=6)
    p_path.add_argument("--documented-only", action="store_true")
    p_path.add_argument("--source-native-only", action="store_true")

    args = parser.parse_args()
    nodes, edges = load()

    if args.command == "stats":
        type_counts: dict[str, int] = {}
        ns_counts: dict[str, int] = {}
        for node in nodes.values():
            type_counts[node["type"]] = type_counts.get(node["type"], 0) + 1
            ns_counts[node["namespace"]] = ns_counts.get(node["namespace"], 0) + 1
        dump({"nodes": len(nodes), "edges": len(edges), "types": type_counts, "namespaces": ns_counts})
        return 0

    if args.command == "node":
        if args.id not in nodes:
            raise SystemExit(f"unknown node: {args.id}")
        dump(nodes[args.id])
        return 0

    if args.command == "neighbors":
        if args.id not in nodes:
            raise SystemExit(f"unknown node: {args.id}")
        dump(
            neighbors(
                args.id,
                nodes,
                edges,
                args.direction,
                set(args.edge_type) or None,
            )
        )
        return 0

    if args.command == "operator":
        if args.id not in nodes or nodes[args.id].get("type") != "OPERATOR":
            raise SystemExit(f"unknown operator: {args.id}")
        matches = [
            {"edge": edge, "source": nodes.get(edge["source"])}
            for edge in edges
            if edge["edge_type"] == "USES_OPERATOR" and edge["target"] == args.id
        ]
        dump({"operator": nodes[args.id], "uses": matches})
        return 0

    if args.command == "open":
        dump(sorted(
            [node for node in nodes.values() if node["type"] == "OPEN_QUESTION"],
            key=lambda node: node["id"],
        ))
        return 0

    if args.command == "claims":
        claims = [node for node in nodes.values() if node["type"] == "CLAIM"]
        if args.source:
            claims = [claim for claim in claims if args.source in claim.get("source_ids", [])]
        dump(sorted(claims, key=lambda claim: claim["id"]))
        return 0

    if args.command == "path":
        for node_id in (args.start, args.end):
            if node_id not in nodes:
                raise SystemExit(f"unknown node: {node_id}")
        path = shortest_path(
            args.start,
            args.end,
            nodes,
            edges,
            args.max_depth,
            args.documented_only,
            args.source_native_only,
        )
        dump({"start": args.start, "end": args.end, "path": path})
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
