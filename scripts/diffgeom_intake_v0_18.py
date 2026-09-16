#!/usr/bin/env python3
"""MAPEOGEO v0.18 Differential Geometry, Lie Groups, and Manifolds Expansion Runner.

Mathematics Expansion across Gallier (S_A), Axler (S_B), VMLS (S_C), CVX (S_D), Billingsley (S_E), and Lee (S_F)
establishing the connective differential-geometric, exterior calculus, Riemannian, and Lie-theoretic foundation bridging
Smooth Manifolds, Tangent Bundles, Integration on Manifolds, Riemannian Metrics, and Matrix Lie Groups.

Dashboard Metrics:
- N_source_total: Total source declarations across S_A, S_B, S_C, S_D, S_E, S_F (disjoint partition)
- N_section_anchors_total: Total section anchors (segregated from source declarations)
- N_canonical_total: Total canonical mathematical objects
- N_2_source_bridges, N_3_source_bridges, N_4_source_bridges, N_5_source_bridges, N_6_source_bridges: Multi-source convergence
- D_domains_count, domains_list: Distinct mathematical domains (7 domains)
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

from scripts.import_diffgeom_v0_18 import (
    FORBIDDEN_PERSISTED_KEYS,
    DiffGeomDeclaration,
    generate_diffgeom_declarations,
)

STAGE = "v0.18"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"
BILLINGSLEY_SOURCE_ID = "BILLINGSLEY_PROB_MEASURE_1995"
LEE_SOURCE_ID = "LEE_SMOOTH_MANIFOLDS_2013"

VALID_SOURCE_IDS = {
    GALLIER_SOURCE_ID,
    AXLER_SOURCE_ID,
    VMLS_SOURCE_ID,
    CVX_SOURCE_ID,
    BILLINGSLEY_SOURCE_ID,
    LEE_SOURCE_ID,
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


def ingest_diffgeom_declarations(
    graph: dict[str, Any],
    declarations: list[DiffGeomDeclaration],
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
                "corpus": "LEE",
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
                "stage": STAGE,
            },
        }
        add_node(nodes, by_id, node_dict)

        # Structural references
        for target_id in decl.structural_refs:
            edge_id = f"e:dep:{decl.node_id}:{target_id}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": edge_id,
                    "type": "PROOF_DEPENDENCY",
                    "source": decl.node_id,
                    "target": target_id,
                    "attributes": {
                        "dep_type": "STRUCTURAL_REFERENCE",
                        "stage": STAGE,
                    },
                },
            )

    return graph


def ingest_v0_18_canonical_alignments(
    graph: dict[str, Any],
    alignments_path: Path,
) -> dict[str, Any]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    alignments_data = json.loads(alignments_path.read_text(encoding="utf-8"))
    canonical_objects = alignments_data.get("canonical_objects", [])

    alignment_summary = {
        "total_canonical_objects": len(canonical_objects),
        "total_alignments": 0,
        "gallier_alignments": 0,
        "axler_alignments": 0,
        "vmls_alignments": 0,
        "cvx_alignments": 0,
        "billingsley_alignments": 0,
        "lee_alignments": 0,
        "cross_source_same": 0,
        "cross_source_scoped_overlap": 0,
        "cross_source_related": 0,
        "unresolved": 0,
        "two_source_canonical_objects": 0,
        "three_source_canonical_objects": 0,
        "four_source_canonical_objects": 0,
        "five_source_canonical_objects": 0,
        "six_source_canonical_objects": 0,
        "representation_diversity": {
            "abstract": 0,
            "algebraic": 0,
            "geometric": 0,
            "computational": 0,
            "applied": 0,
            "formal": 0,
        },
    }

    for co in canonical_objects:
        cid = co["id"]
        cname = co["name"]
        domain = co.get("domain", "General Mathematics")
        desc = co.get("description", "")
        formal_decl = co.get("formal_decl", None)
        rep_diversity = co.get("representation_kinds", ["abstract"])
        diversity_count = len(rep_diversity)

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
        lee_sources = []

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
                if any(k in src_id for k in (":axler:", ":vmls:", ":cvx:", ":billingsley:", ":diffgeom:")):
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
            elif corpus == "LEE":
                if ":diffgeom:" not in src_id:
                    raise ValueError(f"Provenance mismatch for node '{src_id}': declared corpus is 'LEE', but node is '{src_id}'")

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
            elif corpus == "LEE":
                alignment_summary["lee_alignments"] += 1
                lee_sources.append((src_id, status))

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
            1 if len(lee_sources) > 0 else 0,
        ])
        if represented_sources >= 2:
            alignment_summary["two_source_canonical_objects"] += 1
        if represented_sources >= 3:
            alignment_summary["three_source_canonical_objects"] += 1
        if represented_sources >= 4:
            alignment_summary["four_source_canonical_objects"] += 1
        if represented_sources >= 5:
            alignment_summary["five_source_canonical_objects"] += 1
        if represented_sources >= 6:
            alignment_summary["six_source_canonical_objects"] += 1

        # Emit typed semantic bridge edges across all pairs of grounded sources
        all_aligned_sources = [(s, "GALLIER", st) for s, st in gallier_sources] + \
                              [(s, "AXLER", st) for s, st in axler_sources] + \
                              [(s, "VMLS", st) for s, st in vmls_sources] + \
                              [(s, "CVX", st) for s, st in cvx_sources] + \
                              [(s, "BILLINGSLEY", st) for s, st in billingsley_sources] + \
                              [(s, "LEE", st) for s, st in lee_sources]

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
                                "corpus_a": corp_a,
                                "corpus_b": corp_b,
                                "canonical_id": cid,
                                "stage": STAGE,
                            },
                        },
                    )

    return graph, alignment_summary


def normalize_domain(dom: str) -> str:
    if dom in ("Applied Linear Algebra & Optimization", "Applied Linear Algebra"):
        return "Applied Linear Algebra"
    return dom


def compute_v0_18_dashboard_metrics(graph: dict[str, Any], alignment_summary: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    source_decls = [
        n for n in nodes
        if n.get("type") in ("SOURCE_DECLARATION", "STATEMENT")
        and n["id"].startswith("srcdecl:")
        and n.get("type") != "SOURCE_SECTION_ANCHOR"
    ]
    sec_anchors = [n for n in nodes if n.get("type") == "SOURCE_SECTION_ANCHOR"]
    canonical_objs = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    # Strict disjoint partitioning by corpus namespace across all 6 corpora
    gallier_decls = [n for n in source_decls if not any(k in n["id"] for k in (":axler:", ":vmls:", ":cvx:", ":billingsley:", ":diffgeom:"))]
    axler_decls = [n for n in source_decls if ":axler:" in n["id"]]
    vmls_decls = [n for n in source_decls if ":vmls:" in n["id"]]
    cvx_decls = [n for n in source_decls if ":cvx:" in n["id"]]
    billingsley_decls = [n for n in source_decls if ":billingsley:" in n["id"]]
    lee_decls = [n for n in source_decls if ":diffgeom:" in n["id"]]

    # Verify disjoint partition completeness
    total_partitioned = len(gallier_decls) + len(axler_decls) + len(vmls_decls) + len(cvx_decls) + len(billingsley_decls) + len(lee_decls)
    if total_partitioned != len(source_decls):
        raise ValueError(
            f"Provenance integrity violation: disjoint partition sum ({total_partitioned}) != total source declarations ({len(source_decls)})"
        )

    def get_status(n: dict) -> str:
        return n.get("attributes", {}).get("direct_status") or n.get("attributes", {}).get("independent_profile", {}).get("direct_status", "")

    eo_only = [n for n in source_decls if "EO" in get_status(n)]
    geo_only = [n for n in source_decls if "GEO" in get_status(n)]
    dual = [n for n in source_decls if get_status(n) == "DUAL_DIRECT"]
    theoretic = [n for n in source_decls if get_status(n) == "THEORETIC_DIRECT"]

    # Domains
    domains = set()
    total_diversity = 0
    for co in canonical_objs:
        attrs = co.get("attributes", {})
        dom = attrs.get("domain")
        if dom:
            domains.add(normalize_domain(dom))
        div = attrs.get("representation_diversity", [])
        total_diversity += len(div) if div else 1

    r_bar = round(total_diversity / max(1, len(canonical_objs)), 3)

    # Edge Breakdown
    bridge_same = [e for e in edges if e.get("type") == "SAME_SEMANTICS"]
    bridge_scoped = [e for e in edges if e.get("type") == "SCOPED_OVERLAP"]
    bridge_related = [e for e in edges if e.get("type") == "RELATED_TO"]
    total_bridges = len(bridge_same) + len(bridge_scoped) + len(bridge_related)

    dashboard = {
        "stage": STAGE,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "N_source_total": len(source_decls),
        "N_source_breakdown": {
            "gallier_quaintance_SA": len(gallier_decls),
            "axler_ladr4e_SB": len(axler_decls),
            "boyd_vmls_SC": len(vmls_decls),
            "boyd_cvx_SD": len(cvx_decls),
            "billingsley_SE": len(billingsley_decls),
            "lee_diffgeom_SF": len(lee_decls),
            "disjoint_partition_sum": total_partitioned,
            "disjoint_partition_status": "EXACT_EQUALITY",
        },
        "N_section_anchors_total": len(sec_anchors),
        "N_canonical_total": len(canonical_objs),
        "multi_source_convergence": {
            "two_source_canonical_objects": alignment_summary.get("two_source_canonical_objects", 0),
            "three_source_canonical_objects": alignment_summary.get("three_source_canonical_objects", 0),
            "four_source_canonical_objects": alignment_summary.get("four_source_canonical_objects", 0),
            "five_source_canonical_objects": alignment_summary.get("five_source_canonical_objects", 0),
            "six_source_canonical_objects": alignment_summary.get("six_source_canonical_objects", 0),
            "two_source_coverage_pct": round(alignment_summary.get("two_source_canonical_objects", 0) / max(1, len(canonical_objs)) * 100, 1),
            "three_source_coverage_pct": round(alignment_summary.get("three_source_canonical_objects", 0) / max(1, len(canonical_objs)) * 100, 1),
            "four_source_coverage_pct": round(alignment_summary.get("four_source_canonical_objects", 0) / max(1, len(canonical_objs)) * 100, 1),
            "five_source_coverage_pct": round(alignment_summary.get("five_source_canonical_objects", 0) / max(1, len(canonical_objs)) * 100, 1),
            "six_source_coverage_pct": round(alignment_summary.get("six_source_canonical_objects", 0) / max(1, len(canonical_objs)) * 100, 1),
        },
        "representation_diversity": {
            "average_richness_r_bar": r_bar,
            "modalities_distribution": alignment_summary.get("representation_diversity", {}),
        },
        "candidate_views": {
            "EO_ONLY_DIRECT": len(eo_only),
            "GEO_ONLY_DIRECT": len(geo_only),
            "DUAL_DIRECT": len(dual),
            "THEORETIC_DIRECT": len(theoretic),
        },
        "domains_count": len(domains),
        "domains_list": sorted(list(domains)),
        "edges_summary": {
            "SAME_SEMANTICS": len(bridge_same),
            "SCOPED_OVERLAP": len(bridge_scoped),
            "RELATED_TO": len(bridge_related),
            "total_typed_cross_bridges": total_bridges,
            "REPRESENTS": len([e for e in edges if e.get("type") == "REPRESENTS"]),
            "PROOF_DEPENDENCY": len([e for e in edges if e.get("type") == "PROOF_DEPENDENCY"]),
            "other_edges": len([e for e in edges if e.get("type") not in ("SAME_SEMANTICS", "SCOPED_OVERLAP", "RELATED_TO", "REPRESENTS", "PROOF_DEPENDENCY")]),
        },
    }
    return dashboard


def run_diffgeom_intake_v0_18(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    graph = load_json_or_gz(base_graph_path)
    diffgeom_decls = generate_diffgeom_declarations()
    graph = ingest_diffgeom_declarations(graph, diffgeom_decls)
    graph, summary = ingest_v0_18_canonical_alignments(graph, alignments_path)
    dashboard = compute_v0_18_dashboard_metrics(graph, summary)

    out_graph_path = out_dir / "mapeogeo_v0_18_graph.json.gz"
    save_graph_gz(graph, out_graph_path)

    dash_path = out_dir / "diffgeom_expansion_dashboard.json"
    dash_path.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

    evidence_path = ROOT / "evidence" / "v0_18_scientific_results.json"
    evidence_path.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    return graph, dashboard, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO v0.18 Differential Geometry, Lie Groups, and Manifolds Expansion")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "measure_v0_17" / "mapeogeo_v0_17_graph.json.gz",
        help="Base v0.17 graph checkpoint",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "cross_source_alignments_v0_18.json",
        help="v0.18 alignments JSON file",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "diffgeom_v0_18",
        help="Output directory for v0.18 artifacts",
    )
    args = parser.parse_args()

    print(f"[v0.18 DiffGeom Intake] Loading base graph from: {args.base_graph}")
    print(f"[v0.18 DiffGeom Intake] Generating curated Source F declarations...")
    print(f"[v0.18 DiffGeom Intake] Ingesting canonical alignments from: {args.alignments}")
    graph, dashboard, summary = run_diffgeom_intake_v0_18(
        base_graph_path=args.base_graph,
        alignments_path=args.alignments,
        out_dir=args.out_dir,
    )

    print("==========================================================")
    print("  MAPEOGEO v0.18 Differential Geometry Expansion SUCCESS")
    print("==========================================================")
    print(f"  Source Declarations:        {dashboard['N_source_total']}")
    print(f"    - Gallier (S_A):          {dashboard['N_source_breakdown']['gallier_quaintance_SA']}")
    print(f"    - Axler (S_B):            {dashboard['N_source_breakdown']['axler_ladr4e_SB']}")
    print(f"    - VMLS (S_C):             {dashboard['N_source_breakdown']['boyd_vmls_SC']}")
    print(f"    - CVX (S_D):              {dashboard['N_source_breakdown']['boyd_cvx_SD']}")
    print(f"    - Billingsley (S_E):      {dashboard['N_source_breakdown']['billingsley_SE']}")
    print(f"    - Lee DiffGeom (S_F):     {dashboard['N_source_breakdown']['lee_diffgeom_SF']}")
    print(f"  Source Section Anchors:     {dashboard['N_section_anchors_total']} (segregated)")
    print(f"  Canonical Objects:          {dashboard['N_canonical_total']}")
    print(f"    - 2-Source Support:       {dashboard['multi_source_convergence']['two_source_canonical_objects']} ({dashboard['multi_source_convergence']['two_source_coverage_pct']}%)")
    print(f"    - 3-Source Support:       {dashboard['multi_source_convergence']['three_source_canonical_objects']} ({dashboard['multi_source_convergence']['three_source_coverage_pct']}%)")
    print(f"    - 4-Source Support:       {dashboard['multi_source_convergence']['four_source_canonical_objects']} ({dashboard['multi_source_convergence']['four_source_coverage_pct']}%)")
    print(f"    - 5-Source Support:       {dashboard['multi_source_convergence']['five_source_canonical_objects']} ({dashboard['multi_source_convergence']['five_source_coverage_pct']}%)")
    print(f"    - 6-Source Support:       {dashboard['multi_source_convergence']['six_source_canonical_objects']} ({dashboard['multi_source_convergence']['six_source_coverage_pct']}%)")
    print(f"  Domains ({dashboard['domains_count']}):                 {dashboard['domains_list']}")
    print(f"  Representation Richness:    r_bar = {dashboard['representation_diversity']['average_richness_r_bar']}")
    print(f"  Semantic Bridges (Total: {dashboard['edges_summary']['total_typed_cross_bridges']}):")
    print(f"    - SAME_SEMANTICS:         {dashboard['edges_summary']['SAME_SEMANTICS']}")
    print(f"    - SCOPED_OVERLAP:         {dashboard['edges_summary']['SCOPED_OVERLAP']}")
    print(f"    - RELATED_TO:             {dashboard['edges_summary']['RELATED_TO']}")
    print(f"  Total Graph Edges:          {dashboard['total_edges']}")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
