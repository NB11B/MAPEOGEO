#!/usr/bin/env python3
"""MAPEOGEO v0.14 Convex Analysis and Optimization Expansion Runner.

Ingests Boyd & Vandenberghe's "Convex Optimization" (2004) as Source D (S_D) alongside
Gallier-Quaintance (S_A), Sheldon Axler's LADR4e (S_B), and Boyd & Vandenberghe's VMLS (S_C),
establishes the quad-source convergence ontology (Source Declarations -> Canonical Objects -> Views),
evaluates the Representation Diversity Profile R(M) and richness r_bar, computes primary dashboard
metrics (N_source, N_canonical, N_2-source, N_3-source, N_4-source, D_domains, r_bar),
and emits scientific evidence artifacts.
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

from scripts.import_cvx_v0_14 import (
    DEFAULT_CACHE_PATH as DEFAULT_CVX_PDF,
    FORBIDDEN_PERSISTED_KEYS,
    CvxDeclaration,
    get_cvx_declarations,
)

STAGE = "v0.14"
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

    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)


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


def ingest_cvx_declarations(
    graph: dict[str, Any],
    declarations: list[CvxDeclaration],
) -> dict[str, Any]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    # Register CVX source book container
    cvx_book_id = "src:cvx_book"
    add_node(
        nodes,
        by_id,
        {
            "id": cvx_book_id,
            "type": "SOURCE",
            "label": "Convex Optimization (Boyd & Vandenberghe, 2004)",
            "attributes": {
                "source_id": CVX_SOURCE_ID,
                "authors": ["Stephen Boyd", "Lieven Vandenberghe"],
                "publisher": "Cambridge University Press",
                "year": 2004,
                "url": "https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf",
                "stage": STAGE,
            },
        },
    )

    # Ingest individual CVX declarations
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

        # Connect to CVX book container
        edge_id = f"e:src:{decl.node_id}:{cvx_book_id}"
        add_edge(
            edges,
            edge_ids,
            {
                "id": edge_id,
                "type": "SOURCED_FROM",
                "source": decl.node_id,
                "target": cvx_book_id,
                "attributes": {
                    "corpus": "CVX",
                    "chapter_section": decl.chapter_section,
                    "stage": STAGE,
                },
            },
        )

    # Establish internal structural dependency edges for CVX
    cvx_node_map = {
        d.node_id.split(":")[-1].replace("_", "."): d.node_id
        for d in declarations
    }
    for decl in declarations:
        for ref_num in decl.structural_refs:
            if ref_num in cvx_node_map:
                target_node_id = cvx_node_map[ref_num]
                dep_edge_id = f"e:dep:{decl.node_id}:{target_node_id}"
                add_edge(
                    edges,
                    edge_ids,
                    {
                        "id": dep_edge_id,
                        "type": "DEPENDS_ON",
                        "source": decl.node_id,
                        "target": target_node_id,
                        "attributes": {
                            "corpus": "CVX",
                            "reference_type": "STRUCTURAL_CITATION",
                            "stage": STAGE,
                        },
                    },
                )

    return graph


def ingest_quad_source_alignments(
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

            # Ensure source declaration node exists in graph
            if src_id not in by_id:
                label_parts = src_id.split(":")
                kind = label_parts[1] if len(label_parts) > 2 else "declaration"
                num = label_parts[2].replace("_", ".") if len(label_parts) > 2 else ""
                if corpus == "GALLIER":
                    src_id_attr = GALLIER_SOURCE_ID
                elif corpus == "AXLER":
                    src_id_attr = AXLER_SOURCE_ID
                elif corpus == "VMLS":
                    src_id_attr = VMLS_SOURCE_ID
                else:
                    src_id_attr = CVX_SOURCE_ID

                add_node(
                    nodes,
                    by_id,
                    {
                        "id": src_id,
                        "type": "SOURCE_DECLARATION",
                        "label": f"{corpus} {kind.capitalize()} {num}",
                        "attributes": {
                            "source_id": src_id_attr,
                            "corpus": corpus,
                            "direct_status": "EO_ONLY_DIRECT",
                            "stage": STAGE,
                        },
                    },
                )

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

        # Multi-Source Bridge Counting
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

        # Emit SAME_SEMANTICS bridge edges across all pairs of sources
        all_aligned_sources = [(s, "GALLIER") for s, _ in gallier_sources] + \
                              [(s, "AXLER") for s, _ in axler_sources] + \
                              [(s, "VMLS") for s, _ in vmls_sources] + \
                              [(s, "CVX") for s, _ in cvx_sources]

        for i in range(len(all_aligned_sources)):
            for j in range(i + 1, len(all_aligned_sources)):
                src_a, corp_a = all_aligned_sources[i]
                src_b, corp_b = all_aligned_sources[j]
                if corp_a != corp_b:
                    bridge_edge_id = f"e:same:{src_a}:{src_b}"
                    add_edge(
                        edges,
                        edge_ids,
                        {
                            "id": bridge_edge_id,
                            "type": "SAME_SEMANTICS",
                            "source": src_a,
                            "target": src_b,
                            "attributes": {
                                "canonical_object": cid,
                                "corpus_a": corp_a,
                                "corpus_b": corp_b,
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


def compute_v0_14_metrics(graph: dict[str, Any], alignment_summary: dict[str, Any]) -> dict[str, Any]:
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

    bridge_edges = [e for e in edges if e.get("type") == "SAME_SEMANTICS"]
    represents_edges = [e for e in edges if e.get("type") == "REPRESENTS"]
    depends_on_edges = [e for e in edges if e.get("type") == "DEPENDS_ON"]

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
            "SAME_SEMANTICS_bridges": len(bridge_edges),
            "REPRESENTS": len(represents_edges),
            "DEPENDS_ON": len(depends_on_edges),
        },
    }


def run_convex_intake(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
    pdf_path: Path | None = None,
    use_mock: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    print(f"=== Running MAPEOGEO {STAGE} Convex Optimization Expansion ===")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load base graph (v0.13 tri-source graph)
    print(f"Loading base graph from {base_graph_path}...")
    graph = load_json_or_gz(base_graph_path)
    print(f"Base graph loaded: {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges.")

    # 2. Extract CVX declarations
    print("Extracting Convex Optimization declarations...")
    cvx_decls = get_cvx_declarations(pdf_path=pdf_path, use_mock=use_mock)
    print(f"Extracted {len(cvx_decls)} CVX declarations.")

    # 3. Ingest CVX declarations into graph
    print("Ingesting CVX declarations into graph...")
    graph = ingest_cvx_declarations(graph, cvx_decls)

    # 4. Load quad-source alignments
    print(f"Loading quad-source alignments from {alignments_path}...")
    alignments_data = json.loads(alignments_path.read_text(encoding="utf-8"))

    # 5. Ingest alignments & canonical objects
    print("Ingesting quad-source canonical alignments...")
    graph, alignment_summary = ingest_quad_source_alignments(graph, alignments_data)

    # 6. Compute metrics
    metrics = compute_v0_14_metrics(graph, alignment_summary)

    # 7. Save graph artifact
    out_graph_gz = out_dir / "mapeogeo_v0_14_graph.json.gz"
    print(f"Saving graph artifact to {out_graph_gz}...")
    save_graph_gz(graph, out_graph_gz)

    # 8. Save dashboard & diversity reports
    dashboard_path = out_dir / "convex_expansion_dashboard.json"
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

    # 9. Save scientific evidence
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    scientific_results_path = evidence_dir / "v0_14_scientific_results.json"
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
    print(f"  Total Graph Edges:         {metrics['edges_summary']['total_edges']} (Bridges: {metrics['edges_summary']['SAME_SEMANTICS_bridges']})")

    return graph, metrics, alignment_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MAPEOGEO v0.14 Convex Optimization Expansion")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "tri_source_v0_13" / "mapeogeo_v0_13_graph.json.gz",
        help="Path to base v0.13 graph",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "convex_alignments_v0_14.json",
        help="Path to quad-source convex alignments JSON",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "convex_v0_14",
        help="Output directory for v0.14 artifacts",
    )
    parser.add_argument(
        "--pdf-path",
        type=Path,
        default=DEFAULT_CVX_PDF,
        help="Path to Convex Optimization PDF",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic mock declarations instead of PDF",
    )
    args = parser.parse_args()

    run_convex_intake(
        base_graph_path=args.base_graph,
        alignments_path=args.alignments,
        out_dir=args.out_dir,
        pdf_path=args.pdf_path,
        use_mock=args.mock,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
