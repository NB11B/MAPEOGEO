#!/usr/bin/env python3
"""MAPEOGEO Foundation Depth and Reachability Calculator.

Computes scientific metrics for vertical grounding depth:
  - Vertical Mathematical Depth: d_foundation(M) = min_{p in P_foundation} dist_graph(p, M)
  - Global Foundation Reachability: fraction of advanced canonical objects reachable from foundation primitives.
"""

from __future__ import annotations

import collections
import gzip
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def compute_foundation_metrics(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Identify foundation primitives
    foundation_source_ids = {n["id"] for n in nodes if n["id"].startswith("srcdecl:foundation:")}
    foundation_canonical_ids = {n["id"] for n in nodes if n["id"].startswith("canonical:foundation:")}
    foundation_primitives = foundation_source_ids | foundation_canonical_ids

    advanced_canonical_objs = [
        n for n in nodes
        if n.get("type") == "CANONICAL_OBJECT" and not n["id"].startswith("canonical:foundation:")
    ]
    advanced_canonical_ids = {n["id"] for n in advanced_canonical_objs}

    # Build adjacency list
    adj: dict[str, list[str]] = collections.defaultdict(list)
    for e in edges:
        u = e.get("source")
        v = e.get("target")
        if u and v:
            # Directed edges for upward dependency and traversal
            adj[u].append(v)
            # Typed semantic bridge and equivalence edges are bidirectional
            if e.get("type") in ("SAME_SEMANTICS", "SCOPED_OVERLAP", "RELATED_TO", "REPRESENTS"):
                adj[v].append(u)

    # Multi-source BFS from all foundation primitives
    distances: dict[str, int] = {}
    queue = collections.deque()

    for p in foundation_primitives:
        distances[p] = 0
        queue.append(p)

    while queue:
        curr = queue.popleft()
        curr_dist = distances[curr]
        for neighbor in adj[curr]:
            if neighbor not in distances:
                distances[neighbor] = curr_dist + 1
                queue.append(neighbor)

    # Evaluate reachability and depths for advanced canonical objects
    reachable_advanced = [cid for cid in advanced_canonical_ids if cid in distances]
    unreachable_advanced = [cid for cid in advanced_canonical_ids if cid not in distances]

    reachability_ratio = len(reachable_advanced) / max(1, len(advanced_canonical_ids))
    reachability_pct = round(reachability_ratio * 100, 2)

    depths = [distances[cid] for cid in reachable_advanced]
    avg_depth = round(sum(depths) / max(1, len(depths)), 3) if depths else 0.0
    min_depth = min(depths) if depths else 0
    max_depth = max(depths) if depths else 0

    # Depth distribution by domain
    domain_depths: dict[str, list[int]] = collections.defaultdict(list)
    for co in advanced_canonical_objs:
        cid = co["id"]
        dom = co.get("attributes", {}).get("domain", "Unknown")
        if cid in distances:
            domain_depths[dom].append(distances[cid])

    domain_summary = {}
    for dom, d_list in sorted(domain_depths.items()):
        domain_summary[dom] = {
            "count": len(d_list),
            "avg_depth": round(sum(d_list) / max(1, len(d_list)), 2),
            "min_depth": min(d_list),
            "max_depth": max(d_list),
        }

    return {
        "foundation_primitives_count": len(foundation_primitives),
        "foundation_source_declarations": len(foundation_source_ids),
        "foundation_canonical_objects": len(foundation_canonical_ids),
        "advanced_canonical_objects_total": len(advanced_canonical_ids),
        "advanced_canonical_objects_reachable": len(reachable_advanced),
        "advanced_canonical_objects_unreachable": len(unreachable_advanced),
        "foundation_reachability_pct": reachability_pct,
        "vertical_depth_stats": {
            "min_depth": min_depth,
            "max_depth": max_depth,
            "avg_depth": avg_depth,
        },
        "depth_by_domain": domain_summary,
    }


def main() -> int:
    graph_path = ROOT / "artifacts" / "foundation_backfill" / "mapeogeo_foundation_graph.json.gz"
    if not graph_path.exists():
        print(f"Graph not found at {graph_path}, run foundation_intake.py first.")
        return 1

    with gzip.open(graph_path, "rt", encoding="utf-8") as f:
        graph = json.load(f)

    metrics = compute_foundation_metrics(graph)
    print("==========================================================")
    print("  MAPEOGEO Foundation Depth & Reachability Metrics")
    print("==========================================================")
    print(f"  Foundation Primitives:     {metrics['foundation_primitives_count']}")
    print(f"  Advanced Canonical Objects: {metrics['advanced_canonical_objects_total']}")
    print(f"  Reachable Canonical Count: {metrics['advanced_canonical_objects_reachable']} ({metrics['foundation_reachability_pct']}%)")
    print(f"  Vertical Depth (min/avg/max): {metrics['vertical_depth_stats']['min_depth']} / {metrics['vertical_depth_stats']['avg_depth']} / {metrics['vertical_depth_stats']['max_depth']}")
    print("\n  Depth by Domain:")
    for dom, stats in metrics["depth_by_domain"].items():
        print(f"    - {dom:35s}: count={stats['count']:3d}, avg_depth={stats['avg_depth']:.2f}, range=[{stats['min_depth']}, {stats['max_depth']}]")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    main()
