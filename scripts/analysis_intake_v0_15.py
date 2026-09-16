#!/usr/bin/env python3
"""MAPEOGEO v0.15 Real Analysis and Differential Calculus Expansion Runner.

Ingests Real Analysis, Multivariable Calculus, and Curvature/Optimality structures,
establishes the canonical cross-domain spine (Linear Maps -> Derivatives -> Gradients -> Hessians -> Convexity -> Optimization),
enforces fail-closed provenance and typed semantic bridge edge taxonomy,
computes dashboard metrics (N_source, N_canonical, N_2-source, N_3-source, N_4-source, D_domains, r_bar),
and produces scientific evidence artifacts.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.import_analysis_v0_15 import (
    FORBIDDEN_PERSISTED_KEYS,
    AnalysisDeclaration,
    generate_additional_analysis_declarations,
)
from scripts.io_utils import atomic_write_deterministic_json_gzip

STAGE = "v0.15"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"


def load_json_or_gz(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def save_graph_gz(graph: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for node in graph.get("nodes", []):
        attrs = node.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            if forbidden in node or forbidden in attrs:
                raise ValueError(f"Zero-prose violation in node {node.get('id')}: found key '{forbidden}'")

    atomic_write_deterministic_json_gzip(out_path, graph)


def add_node(nodes: list[dict], by_id: dict[str, dict], node: dict) -> bool:
    nid = node["id"]
    if nid not in by_id:
        nodes.append(node)
        by_id[nid] = node
        return True
    else:
        existing = by_id[nid]
        if "attributes" in node:
            existing.setdefault("attributes", {}).update(node["attributes"])
        return False


def add_edge(edges: list[dict], edge_ids: set[str], edge: dict) -> bool:
    eid = edge["id"]
    if eid not in edge_ids:
        edges.append(edge)
        edge_ids.add(eid)
        return True
    return False


def ingest_analysis_declarations(
    graph: dict[str, Any],
    declarations: list[AnalysisDeclaration],
) -> dict[str, Any]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    for decl in declarations:
        node_dict = {
            "id": decl.node_id,
            "type": "SOURCE_DECLARATION",
            "label": decl.label,
            "attributes": {
                "source_id": decl.source_id,
                "decl_type": decl.decl_type,
                "chapter_section": decl.chapter_section,
                "page": decl.page,
                "statement_sha256": decl.statement_sha256,
                "statement_chars": decl.char_count,
                "direct_status": decl.representation_profile.get("direct_status", "THEORETIC_DIRECT"),
                "eo_tags": decl.representation_profile.get("eo_tags", []),
                "geo_tags": decl.representation_profile.get("geo_tags", []),
                "representation_kinds": decl.representation_profile.get("representation_kinds", []),
                "diversity_count": decl.representation_profile.get("diversity_count", 1),
                "structural_refs": decl.structural_refs,
                "stage": STAGE,
            },
        }
        add_node(nodes, by_id, node_dict)

    return graph


def ingest_v0_15_alignments(
    graph: dict[str, Any],
    alignments_data: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    canonical_objects = alignments_data.get("canonical_objects", [])
    alignment_summary = {
        "total_canonical_objects": len(canonical_objects),
        "two_source_canonical_objects": 0,
        "three_source_canonical_objects": 0,
        "four_source_canonical_objects": 0,
        "total_alignments": 0,
        "gallier_alignments": 0,
        "axler_alignments": 0,
        "vmls_alignments": 0,
        "cvx_alignments": 0,
        "cross_source_same": 0,
        "cross_source_scoped_overlap": 0,
        "cross_source_related": 0,
        "unresolved": 0,
        "ungrounded_sources": [],
        "domains": set(),
        "representation_diversity": {
            "abstract": 0,
            "algebraic": 0,
            "geometric": 0,
            "computational": 0,
            "formal": 0,
            "applied": 0,
        },
        "richness_scores": [],
        "canonical_details": [],
    }

    for co in canonical_objects:
        cid = co["id"]
        cname = co["name"]
        domain = co.get("domain", "Linear Algebra")
        desc = co.get("description", "")
        formal_decl = co.get("formal_decl")
        rep_diversity = co.get("representation_kinds") or co.get("representation_diversity", ["abstract"])
        diversity_count = len(rep_diversity)

        alignment_summary["domains"].add(domain)
        alignment_summary["richness_scores"].append(diversity_count)
        for rk in rep_diversity:
            if rk in alignment_summary["representation_diversity"]:
                alignment_summary["representation_diversity"][rk] += 1

        # Canonical Object Node
        add_node(
            nodes,
            by_id,
            {
                "id": cid,
                "type": "CANONICAL_OBJECT",
                "label": cname,
                "attributes": {
                    "domain": domain,
                    "description": desc,
                    "formal_decl": formal_decl,
                    "representation_diversity": rep_diversity,
                    "diversity_count": diversity_count,
                    "stage": STAGE,
                },
            },
        )

        alignments = co.get("alignments", [])
        gallier_sources = []
        axler_sources = []
        vmls_sources = []
        cvx_sources = []

        for al in alignments:
            src_id = al["source"]
            corpus = al["corpus"]
            status = al.get("status", "CROSS_SOURCE_SAME")

            alignment_summary["total_alignments"] += 1

            # Fail-closed provenance check: do not manufacture missing source declarations
            if src_id not in by_id:
                alignment_summary["ungrounded_sources"].append({
                    "canonical_object": cid,
                    "corpus": corpus,
                    "source": src_id,
                    "status": status,
                })
                continue

            if corpus == "AXLER":
                alignment_summary["axler_alignments"] += 1
                axler_sources.append((src_id, status))
            elif corpus == "GALLIER":
                alignment_summary["gallier_alignments"] += 1
                gallier_sources.append((src_id, status))
            elif corpus == "VMLS":
                alignment_summary["vmls_alignments"] += 1
                vmls_sources.append((src_id, status))
            elif corpus == "CVX":
                alignment_summary["cvx_alignments"] += 1
                cvx_sources.append((src_id, status))

            if status == "CROSS_SOURCE_SAME":
                alignment_summary["cross_source_same"] += 1
            elif status == "CROSS_SOURCE_SCOPED_OVERLAP":
                alignment_summary["cross_source_scoped_overlap"] += 1
            elif status == "CROSS_SOURCE_RELATED_NOT_SAME":
                alignment_summary["cross_source_related"] += 1
            elif status == "UNRESOLVED":
                alignment_summary["unresolved"] += 1

            # REPRESENTS edge: Source Declaration -> Canonical Object
            rep_edge_id = f"e:rep:{src_id}:{cid}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": rep_edge_id,
                    "type": "REPRESENTS",
                    "source": src_id,
                    "target": cid,
                    "attributes": {
                        "corpus": corpus,
                        "cross_source_status": status,
                        "stage": STAGE,
                    },
                },
            )

        # Multi-Source Bridge Counting over grounded source declarations
        represented_sources = sum([
            1 if len(gallier_sources) > 0 else 0,
            1 if len(axler_sources) > 0 else 0,
            1 if len(vmls_sources) > 0 else 0,
            1 if len(cvx_sources) > 0 else 0,
        ])
        if represented_sources >= 2:
            alignment_summary["two_source_canonical_objects"] += 1
        if represented_sources >= 3:
            alignment_summary["three_source_canonical_objects"] += 1
        if represented_sources >= 4:
            alignment_summary["four_source_canonical_objects"] += 1

        # Emit typed semantic bridge edges across all pairs of grounded sources
        all_aligned_sources = [(s, "GALLIER", st) for s, st in gallier_sources] + \
                              [(s, "AXLER", st) for s, st in axler_sources] + \
                              [(s, "VMLS", st) for s, st in vmls_sources] + \
                              [(s, "CVX", st) for s, st in cvx_sources]

        for i in range(len(all_aligned_sources)):
            for j in range(i + 1, len(all_aligned_sources)):
                src_a, corp_a, stat_a = all_aligned_sources[i]
                src_b, corp_b, stat_b = all_aligned_sources[j]
                if corp_a != corp_b:
                    if stat_a == "UNRESOLVED" or stat_b == "UNRESOLVED":
                        continue

                    if stat_a == "CROSS_SOURCE_SAME" and stat_b == "CROSS_SOURCE_SAME":
                        edge_type = "SAME_SEMANTICS"
                    elif stat_a == "CROSS_SOURCE_RELATED_NOT_SAME" or stat_b == "CROSS_SOURCE_RELATED_NOT_SAME":
                        edge_type = "RELATED_TO"
                    elif stat_a == "CROSS_SOURCE_SCOPED_OVERLAP" or stat_b == "CROSS_SOURCE_SCOPED_OVERLAP":
                        edge_type = "SCOPED_OVERLAP"
                    else:
                        edge_type = "RELATED_TO"

                    bridge_edge_id = f"e:{edge_type.lower()}:{src_a}:{src_b}"
                    add_edge(
                        edges,
                        edge_ids,
                        {
                            "id": bridge_edge_id,
                            "type": edge_type,
                            "source": src_a,
                            "target": src_b,
                            "attributes": {
                                "canonical_object": cid,
                                "corpus_a": corp_a,
                                "corpus_b": corp_b,
                                "status_a": stat_a,
                                "status_b": stat_b,
                                "stage": STAGE,
                            },
                        },
                    )

        alignment_summary["canonical_details"].append({
            "id": cid,
            "name": cname,
            "domain": domain,
            "sources_count": represented_sources,
            "has_formal": formal_decl is not None,
            "representation_diversity": rep_diversity,
            "richness": diversity_count,
        })

    alignment_summary["domains"] = sorted(alignment_summary["domains"])
    return graph, alignment_summary


def compute_v0_15_metrics(graph: dict[str, Any], alignment_summary: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    source_decls = [n for n in nodes if n.get("type") == "SOURCE_DECLARATION"]
    canonical_objs = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    gallier_decls = [n for n in source_decls if n.get("attributes", {}).get("source_id") == GALLIER_SOURCE_ID or "gallier" in n.get("id", "")]
    axler_decls = [n for n in source_decls if n.get("attributes", {}).get("source_id") == AXLER_SOURCE_ID or "axler" in n.get("id", "")]
    vmls_decls = [n for n in source_decls if n.get("attributes", {}).get("source_id") == VMLS_SOURCE_ID or "vmls" in n.get("id", "")]
    cvx_decls = [n for n in source_decls if n.get("attributes", {}).get("source_id") == CVX_SOURCE_ID or "cvx" in n.get("id", "")]

    eo_candidates = [n for n in source_decls if "EO" in n.get("attributes", {}).get("direct_status", "")]
    geo_candidates = [n for n in source_decls if "GEO" in n.get("attributes", {}).get("direct_status", "")]
    dual_candidates = [n for n in source_decls if n.get("attributes", {}).get("direct_status") == "DUAL_DIRECT"]

    formal_linked = [co for co in canonical_objs if co.get("attributes", {}).get("formal_decl")]

    richness_scores = alignment_summary.get("richness_scores", [])
    avg_richness = sum(richness_scores) / len(richness_scores) if richness_scores else 0.0

    same_semantics_edges = [e for e in edges if e.get("type") == "SAME_SEMANTICS"]
    scoped_overlap_edges = [e for e in edges if e.get("type") == "SCOPED_OVERLAP"]
    related_to_edges = [e for e in edges if e.get("type") == "RELATED_TO"]
    represents_edges = [e for e in edges if e.get("type") == "REPRESENTS"]
    depends_on_edges = [e for e in edges if e.get("type") == "DEPENDS_ON"]
    sourced_from_edges = [e for e in edges if e.get("type") == "SOURCED_FROM"]

    total_bridge_edges = len(same_semantics_edges) + len(scoped_overlap_edges) + len(related_to_edges)

    return {
        "stage": STAGE,
        "N_source_total": len(source_decls),
        "source_breakdown": {
            "S_A_gallier": len(gallier_decls),
            "S_B_axler": len(axler_decls),
            "S_C_vmls": len(vmls_decls),
            "S_D_cvx": len(cvx_decls),
        },
        "N_canonical_total": len(canonical_objs),
        "N_2_source_bridges": alignment_summary["two_source_canonical_objects"],
        "N_3_source_bridges": alignment_summary["three_source_canonical_objects"],
        "N_4_source_bridges": alignment_summary["four_source_canonical_objects"],
        "D_domains_count": len(alignment_summary["domains"]),
        "domains_list": alignment_summary["domains"],
        "representation_diversity": {
            "counts": alignment_summary["representation_diversity"],
            "average_richness_r_bar": round(avg_richness, 3),
            "richness_distribution": {
                f"richness_{k}": sum(1 for r in richness_scores if r == k)
                for k in range(1, 7)
            },
        },
        "representation_views": {
            "N_EO_candidates": len(eo_candidates),
            "N_GEO_candidates": len(geo_candidates),
            "N_DUAL_candidates": len(dual_candidates),
        },
        "N_formal_linked": len(formal_linked),
        "edges_summary": {
            "total_edges": len(edges),
            "SAME_SEMANTICS_bridges": len(same_semantics_edges),
            "SCOPED_OVERLAP_bridges": len(scoped_overlap_edges),
            "RELATED_TO_bridges": len(related_to_edges),
            "total_cross_source_bridges": total_bridge_edges,
            "REPRESENTS": len(represents_edges),
            "DEPENDS_ON": len(depends_on_edges),
            "SOURCED_FROM": len(sourced_from_edges),
        },
    }


def run_analysis_intake(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    print(f"=== Running MAPEOGEO {STAGE} Analysis and Differential Calculus Expansion ===")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load base graph (v0.14 convex graph)
    print(f"Loading base graph from {base_graph_path}...")
    graph = load_json_or_gz(base_graph_path)
    print(f"Base graph loaded: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges.")

    # 2. Extract and ingest analysis declarations
    print("Ingesting Analysis and Differential Calculus declarations...")
    analysis_decls = generate_additional_analysis_declarations()
    graph = ingest_analysis_declarations(graph, analysis_decls)

    # 3. Load v0.15 alignments
    print(f"Loading v0.15 alignments from {alignments_path}...")
    alignments_data = json.loads(alignments_path.read_text(encoding="utf-8"))

    # 4. Ingest alignments & canonical objects
    print("Ingesting canonical objects and typed semantic bridge edges...")
    graph, alignment_summary = ingest_v0_15_alignments(graph, alignments_data)

    # 5. Compute metrics
    metrics = compute_v0_15_metrics(graph, alignment_summary)

    # 6. Save graph artifact
    out_graph_gz = out_dir / "mapeogeo_v0_15_graph.json.gz"
    print(f"Saving graph artifact to {out_graph_gz}...")
    save_graph_gz(graph, out_graph_gz)

    # 7. Save dashboard & diversity reports
    dashboard_path = out_dir / "analysis_expansion_dashboard.json"
    diversity_report_path = out_dir / "representation_diversity_report.json"
    with open(dashboard_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(diversity_report_path, "w", encoding="utf-8") as f:
        json.dump({
            "stage": STAGE,
            "average_richness_r_bar": metrics["representation_diversity"]["average_richness_r_bar"],
            "profile_counts": metrics["representation_diversity"]["counts"],
            "richness_distribution": metrics["representation_diversity"]["richness_distribution"],
            "canonical_details": alignment_summary["canonical_details"],
        }, f, indent=2)

    # 8. Save scientific evidence
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    scientific_results_path = evidence_dir / "v0_15_scientific_results.json"
    with open(scientific_results_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{STAGE} Ingestion Complete!")
    print(f"  Total Source Declarations: {metrics['N_source_total']}")
    print(f"    - Gallier (S_A): {metrics['source_breakdown']['S_A_gallier']}")
    print(f"    - Axler (S_B):   {metrics['source_breakdown']['S_B_axler']}")
    print(f"    - VMLS (S_C):    {metrics['source_breakdown']['S_C_vmls']}")
    print(f"    - CVX (S_D):     {metrics['source_breakdown']['S_D_cvx']}")
    print(f"  Total Canonical Objects:   {metrics['N_canonical_total']}")
    print(f"    - 2-Source Support:      {metrics['N_2_source_bridges']}")
    print(f"    - 3-Source Support:      {metrics['N_3_source_bridges']}")
    print(f"    - 4-Source Quad-Support: {metrics['N_4_source_bridges']}")
    print(f"  Distinct Domains:          {metrics['D_domains_count']} ({', '.join(metrics['domains_list'])})")
    print(f"  Avg Representation Richness r_bar: {metrics['representation_diversity']['average_richness_r_bar']}")
    print(f"  Candidate Views: EO={metrics['representation_views']['N_EO_candidates']}, GEO={metrics['representation_views']['N_GEO_candidates']}, Dual={metrics['representation_views']['N_DUAL_candidates']}")
    print(f"  Formal Proof Linked:       {metrics['N_formal_linked']}")
    print(f"  Total Graph Edges:         {metrics['edges_summary']['total_edges']}")
    print(f"    - SAME_SEMANTICS:        {metrics['edges_summary']['SAME_SEMANTICS_bridges']}")
    print(f"    - SCOPED_OVERLAP:        {metrics['edges_summary']['SCOPED_OVERLAP_bridges']}")
    print(f"    - RELATED_TO:            {metrics['edges_summary']['RELATED_TO_bridges']}")
    print(f"    - Total Cross-Bridges:   {metrics['edges_summary']['total_cross_source_bridges']}")

    return graph, metrics, alignment_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MAPEOGEO v0.15 Real Analysis and Differential Calculus Expansion")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "convex_v0_14" / "mapeogeo_v0_14_graph.json.gz",
        help="Path to base v0.14 graph",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "analysis_alignments_v0_15.json",
        help="Path to v0.15 analysis alignments JSON",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "analysis_v0_15",
        help="Output directory for v0.15 artifacts",
    )
    args = parser.parse_args()

    run_analysis_intake(
        base_graph_path=args.base_graph,
        alignments_path=args.alignments,
        out_dir=args.out_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
