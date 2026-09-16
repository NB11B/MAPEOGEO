#!/usr/bin/env python3
"""MAPEOGEO v0.17 Measure Theory, Lebesgue Integration, and Probability Expansion Runner.

Mathematics Expansion across Gallier (S_A), Axler (S_B), VMLS (S_C), CVX (S_D), and Billingsley (S_E)
establishing the connective measure-theoretic, integral, and probabilistic foundation bridging
Topology, Linear Algebra, Real Analysis, Convexity, and Probability.

Dashboard Metrics:
- N_source_total: Total source declarations across S_A, S_B, S_C, S_D, S_E (disjoint partition)
- N_section_anchors_total: Total section anchors (segregated from source declarations)
- N_canonical_total: Total canonical mathematical objects
- N_2_source_bridges, N_3_source_bridges, N_4_source_bridges, N_5_source_bridges: Multi-source convergence
- D_domains_count, domains_list: Distinct mathematical domains (6 domains)
- representation_diversity: Average representation richness r_bar across 6 modalities
- edges_summary: Exact typed semantic bridge counts (SAME_SEMANTICS, SCOPED_OVERLAP, RELATED_TO)
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

from scripts.import_billingsley_v0_17 import (
    FORBIDDEN_PERSISTED_KEYS,
    BillingsleyDeclaration,
    generate_billingsley_declarations,
)
from scripts.io_utils import atomic_write_deterministic_json_gzip

STAGE = "v0.17"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"
BILLINGSLEY_SOURCE_ID = "BILLINGSLEY_PROB_MEASURE_1995"

VALID_SOURCE_IDS = {
    GALLIER_SOURCE_ID,
    AXLER_SOURCE_ID,
    VMLS_SOURCE_ID,
    CVX_SOURCE_ID,
    BILLINGSLEY_SOURCE_ID,
}


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


def ingest_billingsley_declarations(
    graph: dict[str, Any],
    declarations: list[BillingsleyDeclaration],
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
                "corpus": "BILLINGSLEY",
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

        # Internal dependency edges within Billingsley
        for ref in decl.structural_refs:
            dep_edge_id = f"e:dep:{decl.node_id}:{ref}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": dep_edge_id,
                    "type": "DEPENDS_ON",
                    "source": decl.node_id,
                    "target": ref,
                    "attributes": {
                        "corpus": "BILLINGSLEY",
                        "stage": STAGE,
                    },
                },
            )

    return graph


def ingest_v0_17_alignments(
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
        "five_source_canonical_objects": 0,
        "total_alignments": 0,
        "gallier_alignments": 0,
        "axler_alignments": 0,
        "vmls_alignments": 0,
        "cvx_alignments": 0,
        "billingsley_alignments": 0,
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
        domain = co.get("domain", "Measure Theory & Probability")
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
        billingsley_sources = []

        for al in alignments:
            src_id = al["source"]
            corpus = al["corpus"]
            status = al.get("status", "CROSS_SOURCE_SAME")

            alignment_summary["total_alignments"] += 1

            # Fail-closed provenance check: verify source declaration node exists in graph
            if src_id not in by_id:
                raise ValueError(
                    f"Fail-closed provenance error: Source declaration '{src_id}' referenced in canonical object '{cid}' ({corpus}) is not present in graph!"
                )

            # Verify corpus consistency
            if corpus == "GALLIER":
                if any(k in src_id for k in (":axler:", ":vmls:", ":cvx:", ":billingsley:")):
                    raise ValueError(f"Provenance mismatch for node '{src_id}': declared corpus is 'GALLIER', but node is '{src_id}'")
            elif corpus == "AXLER":
                if ":axler:" not in src_id:
                    raise ValueError(f"Provenance mismatch for node '{src_id}': declared corpus is 'AXLER', but node is '{src_id}'")
            elif corpus == "VMLS":
                if ":vmls:" not in src_id:
                    raise ValueError(f"Provenance mismatch for node '{src_id}': declared corpus is 'VMLS', but node is '{src_id}'")
            elif corpus == "CVX":
                if ":cvx:" not in src_id:
                    raise ValueError(f"Provenance mismatch for node '{src_id}': declared corpus is 'CVX', but node is '{src_id}'")
            elif corpus == "BILLINGSLEY":
                if ":billingsley:" not in src_id:
                    raise ValueError(f"Provenance mismatch for node '{src_id}': declared corpus is 'BILLINGSLEY', but node is '{src_id}'")

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
            elif corpus == "BILLINGSLEY":
                alignment_summary["billingsley_alignments"] += 1
                billingsley_sources.append((src_id, status))

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
            1 if len(billingsley_sources) > 0 else 0,
        ])
        if represented_sources >= 2:
            alignment_summary["two_source_canonical_objects"] += 1
        if represented_sources >= 3:
            alignment_summary["three_source_canonical_objects"] += 1
        if represented_sources >= 4:
            alignment_summary["four_source_canonical_objects"] += 1
        if represented_sources >= 5:
            alignment_summary["five_source_canonical_objects"] += 1

        # Emit typed semantic bridge edges across all pairs of grounded sources
        all_aligned_sources = [(s, "GALLIER", st) for s, st in gallier_sources] + \
                              [(s, "AXLER", st) for s, st in axler_sources] + \
                              [(s, "VMLS", st) for s, st in vmls_sources] + \
                              [(s, "CVX", st) for s, st in cvx_sources] + \
                              [(s, "BILLINGSLEY", st) for s, st in billingsley_sources]

        for i in range(len(all_aligned_sources)):
            for j in range(i + 1, len(all_aligned_sources)):
                src_a, corp_a, stat_a = all_aligned_sources[i]
                src_b, corp_b, stat_b = all_aligned_sources[j]
                if corp_a != corp_b:
                    if stat_a == "UNRESOLVED" or stat_b == "UNRESOLVED":
                        continue

                    if stat_a == "CROSS_SOURCE_SAME" and stat_b == "CROSS_SOURCE_SAME":
                        if by_id[src_a].get("type") == "SOURCE_SECTION_ANCHOR" or by_id[src_b].get("type") == "SOURCE_SECTION_ANCHOR":
                            edge_type = "SCOPED_OVERLAP"
                        else:
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
            "sources_count": len(alignments),
            "corpora_represented": represented_sources,
            "richness_count": diversity_count,
            "representation_kinds": rep_diversity,
            "formal_decl": formal_decl,
        })

    alignment_summary["domains"] = sorted(list(alignment_summary["domains"]))
    return graph, alignment_summary


def compute_v0_17_dashboard(
    graph: dict[str, Any],
    alignment_summary: dict[str, Any],
) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    source_decls = [
        n for n in nodes
        if n.get("type") in ("SOURCE_DECLARATION", "STATEMENT")
        and n["id"].startswith("srcdecl:")
        and n.get("type") != "SOURCE_SECTION_ANCHOR"
    ]
    section_anchors = [n for n in nodes if n.get("type") == "SOURCE_SECTION_ANCHOR"]
    canonical_objs = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    # Strict disjoint partitioning by corpus namespace across all 5 corpora
    gallier_decls = [n for n in source_decls if not any(k in n["id"] for k in (":axler:", ":vmls:", ":cvx:", ":billingsley:"))]
    axler_decls = [n for n in source_decls if ":axler:" in n["id"]]
    vmls_decls = [n for n in source_decls if ":vmls:" in n["id"]]
    cvx_decls = [n for n in source_decls if ":cvx:" in n["id"]]
    billingsley_decls = [n for n in source_decls if ":billingsley:" in n["id"]]

    # Verify disjoint partition completeness
    total_partitioned = len(gallier_decls) + len(axler_decls) + len(vmls_decls) + len(cvx_decls) + len(billingsley_decls)
    if total_partitioned != len(source_decls):
        raise ValueError(
            f"Provenance integrity violation: disjoint partition sum ({total_partitioned}) != total source declarations ({len(source_decls)})"
        )

    def get_status(n: dict) -> str:
        return n.get("attributes", {}).get("direct_status") or n.get("attributes", {}).get("independent_profile", {}).get("direct_status", "")

    eo_candidates = [n for n in source_decls if "EO" in get_status(n)]
    geo_candidates = [n for n in source_decls if "GEO" in get_status(n)]
    dual_candidates = [n for n in source_decls if get_status(n) == "DUAL_DIRECT"]

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
        "N_section_anchors_total": len(section_anchors),
        "source_breakdown": {
            "S_A_gallier": len(gallier_decls),
            "S_B_axler": len(axler_decls),
            "S_C_vmls": len(vmls_decls),
            "S_D_cvx": len(cvx_decls),
            "S_E_billingsley": len(billingsley_decls),
        },
        "N_canonical_total": len(canonical_objs),
        "N_2_source_bridges": alignment_summary["two_source_canonical_objects"],
        "N_3_source_bridges": alignment_summary["three_source_canonical_objects"],
        "N_4_source_bridges": alignment_summary["four_source_canonical_objects"],
        "N_5_source_bridges": alignment_summary["five_source_canonical_objects"],
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


def run_measure_intake_v0_17(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    print(f"=== Running MAPEOGEO {STAGE} Measure Theory, Integration & Probability Expansion ===")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load base graph (v0.16 graph)
    print(f"Loading base graph from {base_graph_path}...")
    graph = load_json_or_gz(base_graph_path)

    # 2. Ingest Source E (Billingsley 1995) declarations
    print("Ingesting Source E (Billingsley 1995) declarations...")
    decls = generate_billingsley_declarations()
    graph = ingest_billingsley_declarations(graph, decls)

    # 3. Ingest alignments and build canonical objects / semantic bridges
    print(f"Ingesting alignments from {alignments_path}...")
    alignments_data = json.loads(alignments_path.read_text(encoding="utf-8"))
    graph, summary = ingest_v0_17_alignments(graph, alignments_data)

    # 4. Compute Dashboard
    print("Computing v0.17 expansion dashboard...")
    dashboard = compute_v0_17_dashboard(graph, summary)

    # 5. Save Graph Artifact & Reports
    graph_out = out_dir / "mapeogeo_v0_17_graph.json.gz"
    print(f"Saving expanded graph to {graph_out}...")
    save_graph_gz(graph, graph_out)

    dashboard_out = out_dir / "measure_expansion_dashboard.json"
    dashboard_out.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    print(f"Saved dashboard to {dashboard_out}")

    summary_out = out_dir / "measure_alignments_summary.json"
    summary_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    evidence_out = ROOT / "evidence" / "v0_17_scientific_results.json"
    evidence_out.parent.mkdir(parents=True, exist_ok=True)
    evidence_out.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    print(f"Saved evidence record to {evidence_out}")

    print("\n=== MAPEOGEO v0.17 Measure & Probability Expansion Completed Successfully ===")
    print(f"  - Source Declarations (Total): {dashboard['N_source_total']}")
    print(f"    * Gallier (S_A):     {dashboard['source_breakdown']['S_A_gallier']}")
    print(f"    * Axler (S_B):       {dashboard['source_breakdown']['S_B_axler']}")
    print(f"    * VMLS (S_C):        {dashboard['source_breakdown']['S_C_vmls']}")
    print(f"    * CVX (S_D):         {dashboard['source_breakdown']['S_D_cvx']}")
    print(f"    * Billingsley (S_E): {dashboard['source_breakdown']['S_E_billingsley']}")
    print(f"  - Section Anchors: {dashboard['N_section_anchors_total']}")
    print(f"  - Canonical Objects: {dashboard['N_canonical_total']}")
    print(f"    * 2-Source: {dashboard['N_2_source_bridges']}")
    print(f"    * 3-Source: {dashboard['N_3_source_bridges']}")
    print(f"    * 4-Source: {dashboard['N_4_source_bridges']}")
    print(f"    * 5-Source: {dashboard['N_5_source_bridges']}")
    print(f"  - Distinct Domains ({dashboard['D_domains_count']}): {dashboard['domains_list']}")
    print(f"  - Representation Richness r_bar: {dashboard['representation_diversity']['average_richness_r_bar']}")
    print(f"  - Semantic Bridges (Total: {dashboard['edges_summary']['total_cross_source_bridges']}):")
    print(f"    * SAME_SEMANTICS: {dashboard['edges_summary']['SAME_SEMANTICS_bridges']}")
    print(f"    * SCOPED_OVERLAP: {dashboard['edges_summary']['SCOPED_OVERLAP_bridges']}")
    print(f"    * RELATED_TO:     {dashboard['edges_summary']['RELATED_TO_bridges']}")
    print(f"  - Total Graph Edges: {dashboard['edges_summary']['total_edges']}")

    return graph, dashboard, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO v0.17 Measure & Probability Expansion Runner")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "topology_v0_16" / "mapeogeo_v0_16_graph.json.gz",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "cross_source_alignments_v0_17.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "measure_v0_17",
    )
    args = parser.parse_args()

    run_measure_intake_v0_17(args.base_graph, args.alignments, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
