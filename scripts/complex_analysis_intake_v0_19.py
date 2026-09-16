#!/usr/bin/env python3
"""MAPEOGEO v0.19 Complex Analysis, Several Complex Variables & Riemann Surfaces Expansion Runner.

Mathematics Expansion across Gallier (S_A), Axler (S_B), VMLS (S_C), CVX (S_D), Billingsley (S_E), Lee (S_F),
and Ahlfors/Krantz/Conway (S_G) establishing the connective complex-analytic, harmonic, conformal, several complex
variables, and Riemann surface foundation bridging Holomorphic Functions, Cauchy Theory, Residues, Conformal Mappings,
Hartogs Extension, Dolbeault Complex, and the Riemann-Roch Theorem.

Dashboard Metrics:
- N_source_total: Total source declarations across S_A, S_B, S_C, S_D, S_E, S_F, S_G (disjoint partition)
- N_section_anchors_total: Total section anchors (segregated from source declarations)
- N_canonical_total: Total canonical mathematical objects
- N_2_source_bridges, N_3_source_bridges, N_4_source_bridges, N_5_source_bridges, N_6_source_bridges, N_7_source_bridges
- D_domains_count, domains_list: Distinct mathematical domains (8 domains)
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

from scripts.import_complex_analysis_v0_19 import (
    FORBIDDEN_PERSISTED_KEYS,
    ComplexAnalysisDeclaration,
    build_complex_declarations,
)

STAGE = "v0.19"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"
BILLINGSLEY_SOURCE_ID = "BILLINGSLEY_PROB_MEASURE_1995"
LEE_SOURCE_ID = "LEE_SMOOTH_MANIFOLDS_2013"
AHLFORS_SOURCE_ID = "AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979"
FOUNDATION_SOURCE_ID = "FOUNDATION_MATHEMATICS_BASE"

VALID_SOURCE_IDS = {
    GALLIER_SOURCE_ID,
    AXLER_SOURCE_ID,
    VMLS_SOURCE_ID,
    CVX_SOURCE_ID,
    BILLINGSLEY_SOURCE_ID,
    LEE_SOURCE_ID,
    AHLFORS_SOURCE_ID,
    FOUNDATION_SOURCE_ID,
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


def ingest_complex_declarations(
    graph: dict[str, Any],
    declarations: list[ComplexAnalysisDeclaration],
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
                "corpus": "AHLFORS",
                "decl_type": decl.decl_type,
                "chapter_section": decl.chapter_section,
                "page": decl.page,
                "statement_sha256": decl.statement_sha256,
                "statement_chars": decl.char_count,
                "direct_status": decl.representation_profile.get("direct_status", "THEORETIC_DIRECT"),
                "eo_tags": decl.representation_profile.get("eo_tags", []),
                "geo_tags": decl.representation_profile.get("geo_tags", []),
                "representation_kinds": decl.representation_profile.get("representation_kinds", []),
                "diversity_count": len(decl.representation_profile.get("representation_kinds", [])),
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


def ingest_v0_19_canonical_alignments(
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
        "ahlfors_alignments": 0,
        "cross_source_same": 0,
        "cross_source_scoped_overlap": 0,
        "cross_source_related": 0,
        "unresolved": 0,
        "two_source_canonical_objects": 0,
        "three_source_canonical_objects": 0,
        "four_source_canonical_objects": 0,
        "five_source_canonical_objects": 0,
        "six_source_canonical_objects": 0,
        "seven_source_canonical_objects": 0,
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
        ahlfors_sources = []

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
            elif corpus == "AHLFORS":
                alignment_summary["ahlfors_alignments"] += 1
                ahlfors_sources.append((src_id, status))

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
                        "alignment_status": status,
                        "stage": STAGE,
                    },
                },
            )

        # Multi-source multi-corpus tracking
        active_corpora = set()
        if gallier_sources:
            active_corpora.add("GALLIER")
        if axler_sources:
            active_corpora.add("AXLER")
        if vmls_sources:
            active_corpora.add("VMLS")
        if cvx_sources:
            active_corpora.add("CVX")
        if billingsley_sources:
            active_corpora.add("BILLINGSLEY")
        if lee_sources:
            active_corpora.add("LEE")
        if ahlfors_sources:
            active_corpora.add("AHLFORS")

        num_corpora = len(active_corpora)
        if num_corpora >= 2:
            alignment_summary["two_source_canonical_objects"] += 1
        if num_corpora >= 3:
            alignment_summary["three_source_canonical_objects"] += 1
        if num_corpora >= 4:
            alignment_summary["four_source_canonical_objects"] += 1
        if num_corpora >= 5:
            alignment_summary["five_source_canonical_objects"] += 1
        if num_corpora >= 6:
            alignment_summary["six_source_canonical_objects"] += 1
        if num_corpora >= 7:
            alignment_summary["seven_source_canonical_objects"] += 1

        # Synthesize typed semantic bridge edges between distinct corpora under this canonical object
        all_sources = []
        for s, st in gallier_sources:
            all_sources.append((s, "GALLIER", st))
        for s, st in axler_sources:
            all_sources.append((s, "AXLER", st))
        for s, st in vmls_sources:
            all_sources.append((s, "VMLS", st))
        for s, st in cvx_sources:
            all_sources.append((s, "CVX", st))
        for s, st in billingsley_sources:
            all_sources.append((s, "BILLINGSLEY", st))
        for s, st in lee_sources:
            all_sources.append((s, "LEE", st))
        for s, st in ahlfors_sources:
            all_sources.append((s, "AHLFORS", st))

        for i in range(len(all_sources)):
            src_a, corp_a, stat_a = all_sources[i]
            for j in range(i + 1, len(all_sources)):
                src_b, corp_b, stat_b = all_sources[j]
                if corp_a != corp_b:
                    if stat_a == "CROSS_SOURCE_SAME" and stat_b == "CROSS_SOURCE_SAME":
                        edge_type = "SAME_SEMANTICS"
                    elif "CROSS_SOURCE_SCOPED_OVERLAP" in (stat_a, stat_b):
                        edge_type = "SCOPED_OVERLAP"
                    else:
                        edge_type = "RELATED_TO"

                    bridge_edge_id = f"e:bridge:{src_a}:{src_b}"
                    add_edge(
                        edges,
                        edge_ids,
                        {
                            "id": bridge_edge_id,
                            "type": edge_type,
                            "source": src_a,
                            "target": src_b,
                            "attributes": {
                                "canonical_id": cid,
                                "source_corpora": [corp_a, corp_b],
                                "stage": STAGE,
                            },
                        },
                    )

    graph["_alignment_summary_v0_19"] = alignment_summary
    return graph


def normalize_domain(name: str) -> str:
    mapping = {
        "Linear Algebra": "Linear Algebra",
        "Applied Linear Algebra": "Applied Linear Algebra & Optimization",
        "Applied Linear Algebra & Optimization": "Applied Linear Algebra & Optimization",
        "Convex Analysis & Optimization": "Convex Analysis & Optimization",
        "Differential Calculus & Real Analysis": "Differential Calculus & Real Analysis",
        "Topology & Metric Spaces": "Topology & Metric Spaces",
        "Measure Theory & Probability": "Measure Theory & Probability",
        "Differential Geometry & Lie Groups": "Differential Geometry & Lie Groups",
        "Complex Analysis & Riemann Surfaces": "Complex Analysis & Riemann Surfaces",
        "Foundational Mathematics": "Foundational Mathematics",
    }
    return mapping.get(name, name)


def run_v0_19_intake(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    print(f"[{STAGE} Intake] Loading base graph: {base_graph_path}")
    base_graph = load_json_or_gz(base_graph_path)

    print(f"[{STAGE} Intake] Extracting Source G (Complex Analysis, SCV & Riemann Surfaces) declarations...")
    complex_decls = build_complex_declarations()
    print(f"[{STAGE} Intake] Ingesting {len(complex_decls)} Source G declarations...")
    graph = ingest_complex_declarations(base_graph, complex_decls)

    print(f"[{STAGE} Intake] Ingesting canonical cross-source alignments from: {alignments_path}")
    graph = ingest_v0_19_canonical_alignments(graph, alignments_path)

    # Compute graph metrics
    nodes = graph["nodes"]
    edges = graph["edges"]

    source_nodes = [
        n for n in nodes
        if n.get("type") in ("SOURCE_DECLARATION", "STATEMENT")
        and (n.get("id", "").startswith("srcdecl:") or n.get("id", "").startswith("decl:"))
        and n.get("type") != "SOURCE_SECTION_ANCHOR"
    ]
    section_anchor_nodes = [n for n in nodes if n.get("type") == "SOURCE_SECTION_ANCHOR"]
    canonical_nodes = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    # Strict disjoint partitioning by corpus namespace across all corpora
    gallier_decls = [
        n for n in source_nodes
        if not any(k in n["id"] for k in (":axler:", ":vmls:", ":cvx:", ":billingsley:", ":diffgeom:", ":AHLFORS_KRANTZ_", ":FOUNDATION_MATHEMATICS_BASE:", "srcdecl:foundation:"))
    ]
    axler_decls = [n for n in source_nodes if ":axler:" in n["id"]]
    vmls_decls = [n for n in source_nodes if ":vmls:" in n["id"]]
    cvx_decls = [n for n in source_nodes if ":cvx:" in n["id"]]
    billingsley_decls = [n for n in source_nodes if ":billingsley:" in n["id"]]
    lee_decls = [n for n in source_nodes if ":diffgeom:" in n["id"]]
    ahlfors_decls = [n for n in source_nodes if ":AHLFORS_KRANTZ_" in n["id"]]
    foundation_decls = [n for n in source_nodes if ":FOUNDATION_MATHEMATICS_BASE:" in n["id"] or "srcdecl:foundation:" in n["id"]]

    source_counts = {
        "S_0_foundation": len(foundation_decls),
        "S_A_gallier": len(gallier_decls),
        "S_B_axler": len(axler_decls),
        "S_C_vmls": len(vmls_decls),
        "S_D_cvx": len(cvx_decls),
        "S_E_billingsley": len(billingsley_decls),
        "S_F_lee": len(lee_decls),
        "S_G_ahlfors": len(ahlfors_decls),
    }

    # Verify disjoint partition completeness
    sum_sources = sum(source_counts.values())
    if sum_sources != len(source_nodes):
        raise ValueError(
            f"Provenance integrity violation: disjoint partition sum ({sum_sources}) != total source declarations ({len(source_nodes)})"
        )

    # Multi-source canonical count
    domains_set = set()
    total_rep_kinds = 0
    multi_source_counts = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    # Map canonical objects to connected corpora
    canonical_corpora_map: dict[str, set[str]] = {}
    for e in edges:
        if e.get("type") == "REPRESENTS":
            cid = e.get("target")
            corp = e.get("attributes", {}).get("corpus")
            if cid and corp:
                canonical_corpora_map.setdefault(cid, set()).add(corp)

    for co in canonical_nodes:
        attrs = co.get("attributes", {})
        dom = attrs.get("domain")
        if dom:
            domains_set.add(normalize_domain(dom))
        rk_list = attrs.get("representation_diversity", [])
        total_rep_kinds += len(rk_list) if rk_list else 1

        connected_corps = canonical_corpora_map.get(co["id"], set())
        nc = len(connected_corps)
        for k in range(2, 8):
            if nc >= k:
                multi_source_counts[k] += 1

    r_bar = round(total_rep_kinds / max(len(canonical_nodes), 1), 3)

    # Bridge counts
    bridge_same = sum(1 for e in edges if e.get("type") == "SAME_SEMANTICS")
    bridge_scoped = sum(1 for e in edges if e.get("type") == "SCOPED_OVERLAP")
    bridge_related = sum(1 for e in edges if e.get("type") == "RELATED_TO")
    total_cross_bridges = bridge_same + bridge_scoped + bridge_related

    edge_type_counts = {}
    for e in edges:
        et = e.get("type", "UNKNOWN")
        edge_type_counts[et] = edge_type_counts.get(et, 0) + 1

    dashboard = {
        "stage": STAGE,
        "N_source_total": len(source_nodes),
        "source_breakdown": source_counts,
        "disjoint_partition_verified": True,
        "N_section_anchors_total": len(section_anchor_nodes),
        "N_canonical_total": len(canonical_nodes),
        "multi_source_bridges": {
            "two_source_or_more": multi_source_counts[2],
            "three_source_or_more": multi_source_counts[3],
            "four_source_or_more": multi_source_counts[4],
            "five_source_or_more": multi_source_counts[5],
            "six_source_or_more": multi_source_counts[6],
            "seven_source_or_more": multi_source_counts[7],
        },
        "domains": {
            "count": len(domains_set),
            "list": sorted(list(domains_set)),
        },
        "representation_diversity": {
            "average_richness_r_bar": r_bar,
        },
        "edges_summary": {
            "total_edges": len(edges),
            "SAME_SEMANTICS": bridge_same,
            "SCOPED_OVERLAP": bridge_scoped,
            "RELATED_TO": bridge_related,
            "total_cross_source_bridges": total_cross_bridges,
            "edge_types": edge_type_counts,
        },
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    graph_out = out_dir / "mapeogeo_v0_19_graph.json.gz"
    dashboard_out = out_dir / "complex_analysis_v0_19_dashboard.json"
    evidence_out = ROOT / "evidence" / "v0_19_scientific_results.json"

    print(f"[{STAGE} Intake] Saving compressed graph to {graph_out}")
    save_graph_gz(graph, graph_out)

    print(f"[{STAGE} Intake] Saving dashboard to {dashboard_out}")
    with open(dashboard_out, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2)

    print(f"[{STAGE} Intake] Saving scientific evidence to {evidence_out}")
    evidence_out.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_out, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2)

    print(f"[{STAGE} Intake] Success! Total nodes: {len(nodes)}, Total edges: {len(edges)}")
    print(f"[{STAGE} Intake] Semantic Bridges: {total_cross_bridges} (SAME: {bridge_same}, SCOPED: {bridge_scoped}, REL: {bridge_related})")
    print(f"[{STAGE} Intake] Distinct Domains: {len(domains_set)} -> {sorted(list(domains_set))}")
    return dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO v0.19 Complex Analysis Intake Pipeline")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "diffgeom_v0_18" / "mapeogeo_v0_18_graph.json.gz",
        help="Path to previous stage graph (v0.18 or foundation backfill)",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "cross_source_alignments_v0_19.json",
        help="Path to v0.19 canonical alignments JSON",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "complex_analysis_v0_19",
        help="Directory to save v0.19 graph and dashboard",
    )
    args = parser.parse_args()

    run_v0_19_intake(args.base_graph, args.alignments, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
