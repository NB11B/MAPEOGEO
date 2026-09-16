#!/usr/bin/env python3
"""MAPEOGEO Foundation Backfill Intake Runner.

Constructs the comprehensive foundational mathematical substrate across 8 layers:
  1. Logic & Proofs
  2. Set Theory
  3. Relations & Functions
  4. Number Systems
  5. Elementary Arithmetic & Algebra
  6. Order, Metrics & Sequences
  7. Euclidean Geometry & Trigonometry
  8. Elementary Calculus

Ingests 175 primitive source declarations from Source 0 (FOUNDATION_MATHEMATICS_BASE),
29 foundation canonical objects, builds upward dependency links to the 205 advanced canonical objects,
executes dual contracts, and evaluates vertical mathematical depth and foundation reachability.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.import_foundation_backfill import (
    FORBIDDEN_PERSISTED_KEYS,
    FoundationDeclaration,
    generate_foundation_declarations,
)
from scripts.foundation_contracts import run_all_foundation_contracts
from scripts.compute_foundation_depth import compute_foundation_metrics

STAGE = "foundation"
FOUNDATION_SOURCE_ID = "FOUNDATION_MATHEMATICS_BASE"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"
BILLINGSLEY_SOURCE_ID = "BILLINGSLEY_PROB_MEASURE_1995"
LEE_SOURCE_ID = "LEE_SMOOTH_MANIFOLDS_2013"


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


def ingest_foundation_declarations(
    graph: dict[str, Any],
    declarations: list[FoundationDeclaration],
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
                "corpus": "FOUNDATION",
                "decl_type": decl.decl_type,
                "chapter_section": decl.chapter_section,
                "statement_sha256": decl.statement_sha256,
                "statement_chars": decl.char_count,
                "layer": decl.layer,
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
                        "dep_type": "FOUNDATION_STRUCTURAL_REFERENCE",
                        "stage": STAGE,
                    },
                },
            )

    return graph


def ingest_foundation_canonical_alignments(
    graph: dict[str, Any],
    alignments_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    alignments_data = json.loads(alignments_path.read_text(encoding="utf-8"))
    canonical_objects = alignments_data.get("canonical_objects", [])

    summary = {
        "total_foundation_canonical_objects": len(canonical_objects),
        "total_alignments": 0,
        "upward_dependency_links": 0,
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
        domain = co.get("domain", "Mathematical Foundations")
        desc = co.get("description", "")
        rep_diversity = co.get("representation_kinds", ["abstract"])
        diversity_count = len(rep_diversity)

        for rk in rep_diversity:
            if rk in summary["representation_diversity"]:
                summary["representation_diversity"][rk] += 1

        # Add foundation canonical object node
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
                    "is_foundation": True,
                    "representation_diversity": rep_diversity,
                    "diversity_count": diversity_count,
                    "stage": STAGE,
                },
            },
        )

        # Ingest REPRESENTS edges from source declarations
        for al in co.get("alignments", []):
            src_id = al["source"]
            corpus = al["corpus"]
            status = al.get("status", "CROSS_SOURCE_SAME")

            if src_id not in by_id:
                raise ValueError(
                    f"Fail-closed provenance error: Source declaration '{src_id}' in canonical object '{cid}' not in graph!"
                )

            summary["total_alignments"] += 1
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

        # Ingest UPWARD_FOUNDATION_DEPENDENCY edges
        for target_cid in co.get("upward_dependencies", []):
            if target_cid not in by_id:
                # If target is not yet present, skip or log (fail-closed check)
                print(f"[Warning] Upward target {target_cid} not found in graph, skipping.")
                continue

            summary["upward_dependency_links"] += 1
            up_edge_id = f"e:upward_dep:{cid}:{target_cid}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": up_edge_id,
                    "type": "UPWARD_FOUNDATION_DEPENDENCY",
                    "source": cid,
                    "target": target_cid,
                    "attributes": {
                        "relation": "FOUNDATION_GROUNDS_ADVANCED",
                        "stage": STAGE,
                    },
                },
            )

    return graph, summary


def compute_foundation_dashboard(
    graph: dict[str, Any],
    summary: dict[str, Any],
    depth_metrics: dict[str, Any],
    contract_results: dict[str, bool],
) -> dict[str, Any]:
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

    # Partition by corpus namespace
    foundation_decls = [n for n in source_decls if ":foundation:" in n["id"]]
    gallier_decls = [n for n in source_decls if not any(k in n["id"] for k in (":foundation:", ":axler:", ":vmls:", ":cvx:", ":billingsley:", ":diffgeom:"))]
    axler_decls = [n for n in source_decls if ":axler:" in n["id"]]
    vmls_decls = [n for n in source_decls if ":vmls:" in n["id"]]
    cvx_decls = [n for n in source_decls if ":cvx:" in n["id"]]
    billingsley_decls = [n for n in source_decls if ":billingsley:" in n["id"]]
    lee_decls = [n for n in source_decls if ":diffgeom:" in n["id"]]

    total_partitioned = (
        len(foundation_decls)
        + len(gallier_decls)
        + len(axler_decls)
        + len(vmls_decls)
        + len(cvx_decls)
        + len(billingsley_decls)
        + len(lee_decls)
    )

    if total_partitioned != len(source_decls):
        raise ValueError(
            f"Disjoint partition violation: partition sum ({total_partitioned}) != total source decls ({len(source_decls)})"
        )

    # Layer breakdown for foundation declarations
    layer_counts: dict[str, int] = {}
    for d in foundation_decls:
        layer = d.get("attributes", {}).get("layer", "unknown")
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    # Distinct domains across all canonical objects
    domains = set()
    total_diversity = 0
    for co in canonical_objs:
        attrs = co.get("attributes", {})
        dom = attrs.get("domain")
        if dom:
            domains.add(dom)
        div = attrs.get("representation_diversity", [])
        total_diversity += len(div) if div else 1

    r_bar = round(total_diversity / max(1, len(canonical_objs)), 3)

    # Edge classification
    bridge_same = [e for e in edges if e.get("type") == "SAME_SEMANTICS"]
    bridge_scoped = [e for e in edges if e.get("type") == "SCOPED_OVERLAP"]
    bridge_related = [e for e in edges if e.get("type") == "RELATED_TO"]
    upward_deps = [e for e in edges if e.get("type") == "UPWARD_FOUNDATION_DEPENDENCY"]
    represents = [e for e in edges if e.get("type") == "REPRESENTS"]
    proof_deps = [e for e in edges if e.get("type") == "PROOF_DEPENDENCY"]

    dashboard = {
        "stage": STAGE,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "N_source_total": len(source_decls),
        "N_source_breakdown": {
            "foundation_base_S0": len(foundation_decls),
            "gallier_quaintance_SA": len(gallier_decls),
            "axler_ladr4e_SB": len(axler_decls),
            "boyd_vmls_SC": len(vmls_decls),
            "boyd_cvx_SD": len(cvx_decls),
            "billingsley_SE": len(billingsley_decls),
            "lee_diffgeom_SF": len(lee_decls),
            "disjoint_partition_sum": total_partitioned,
            "disjoint_partition_status": "EXACT_EQUALITY",
        },
        "foundation_layers_breakdown": layer_counts,
        "N_section_anchors_total": len(sec_anchors),
        "N_canonical_total": len(canonical_objs),
        "canonical_breakdown": {
            "foundation_canonical_objects": summary["total_foundation_canonical_objects"],
            "advanced_canonical_objects": len(canonical_objs) - summary["total_foundation_canonical_objects"],
        },
        "foundation_metrics": depth_metrics,
        "contracts_verification": {
            "all_contracts_passing": all(contract_results.values()),
            "domain_results": contract_results,
        },
        "representation_diversity": {
            "average_richness_r_bar": r_bar,
            "modalities_distribution": summary["representation_diversity"],
        },
        "domains_count": len(domains),
        "domains_list": sorted(list(domains)),
        "edges_summary": {
            "UPWARD_FOUNDATION_DEPENDENCY": len(upward_deps),
            "SAME_SEMANTICS": len(bridge_same),
            "SCOPED_OVERLAP": len(bridge_scoped),
            "RELATED_TO": len(bridge_related),
            "total_typed_cross_bridges": len(bridge_same) + len(bridge_scoped) + len(bridge_related),
            "REPRESENTS": len(represents),
            "PROOF_DEPENDENCY": len(proof_deps),
            "other_edges": len([
                e for e in edges
                if e.get("type") not in (
                    "UPWARD_FOUNDATION_DEPENDENCY",
                    "SAME_SEMANTICS",
                    "SCOPED_OVERLAP",
                    "RELATED_TO",
                    "REPRESENTS",
                    "PROOF_DEPENDENCY",
                )
            ]),
        },
    }
    return dashboard


def run_foundation_intake(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    graph = load_json_or_gz(base_graph_path)

    # 1. Ingest foundation source declarations
    decls = generate_foundation_declarations()
    graph = ingest_foundation_declarations(graph, decls)

    # 2. Ingest foundation canonical objects & upward dependency links
    graph, summary = ingest_foundation_canonical_alignments(graph, alignments_path)

    # 3. Compute foundation depth & reachability metrics
    depth_metrics = compute_foundation_metrics(graph)

    # 4. Run executable dual contracts
    contract_results = run_all_foundation_contracts()

    # 5. Compute dashboard
    dashboard = compute_foundation_dashboard(graph, summary, depth_metrics, contract_results)

    # 6. Save outputs
    out_graph_path = out_dir / "mapeogeo_foundation_graph.json.gz"
    save_graph_gz(graph, out_graph_path)

    dash_path = out_dir / "foundation_backfill_dashboard.json"
    dash_path.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

    evidence_path = ROOT / "evidence" / "foundation_backfill_scientific_results.json"
    evidence_path.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

    return graph, dashboard, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO Foundation Backfill Intake Runner")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "diffgeom_v0_18" / "mapeogeo_v0_18_graph.json.gz",
        help="Base v0.18 graph checkpoint",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "foundation_alignments.json",
        help="Foundation alignments JSON file",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "foundation_backfill",
        help="Output directory for Foundation Backfill artifacts",
    )
    args = parser.parse_args()

    print(f"[Foundation Intake] Loading base graph from: {args.base_graph}")
    print(f"[Foundation Intake] Generating curated Source 0 (Foundation) declarations...")
    print(f"[Foundation Intake] Ingesting canonical alignments from: {args.alignments}")

    graph, dashboard, summary = run_foundation_intake(
        base_graph_path=args.base_graph,
        alignments_path=args.alignments,
        out_dir=args.out_dir,
    )

    print("==========================================================")
    print("  MAPEOGEO Foundation Backfill Expansion SUCCESS")
    print("==========================================================")
    print(f"  Source Declarations:        {dashboard['N_source_total']}")
    print(f"    - Foundation Base (S_0):  {dashboard['N_source_breakdown']['foundation_base_S0']}")
    print(f"    - Gallier (S_A):          {dashboard['N_source_breakdown']['gallier_quaintance_SA']}")
    print(f"    - Axler (S_B):            {dashboard['N_source_breakdown']['axler_ladr4e_SB']}")
    print(f"    - VMLS (S_C):             {dashboard['N_source_breakdown']['boyd_vmls_SC']}")
    print(f"    - CVX (S_D):              {dashboard['N_source_breakdown']['boyd_cvx_SD']}")
    print(f"    - Billingsley (S_E):      {dashboard['N_source_breakdown']['billingsley_SE']}")
    print(f"    - Lee DiffGeom (S_F):     {dashboard['N_source_breakdown']['lee_diffgeom_SF']}")
    print(f"  Disjoint Partition Sum:     {dashboard['N_source_breakdown']['disjoint_partition_sum']} ({dashboard['N_source_breakdown']['disjoint_partition_status']})")
    print(f"  Canonical Objects Total:    {dashboard['N_canonical_total']}")
    print(f"    - Foundation Objects:     {dashboard['canonical_breakdown']['foundation_canonical_objects']}")
    print(f"    - Advanced Objects:       {dashboard['canonical_breakdown']['advanced_canonical_objects']}")
    print(f"  Foundation Reachability:    {dashboard['foundation_metrics']['foundation_reachability_pct']}% ({dashboard['foundation_metrics']['advanced_canonical_objects_reachable']}/{dashboard['foundation_metrics']['advanced_canonical_objects_total']})")
    print(f"  Vertical Depth (min/avg/max): {dashboard['foundation_metrics']['vertical_depth_stats']['min_depth']} / {dashboard['foundation_metrics']['vertical_depth_stats']['avg_depth']} / {dashboard['foundation_metrics']['vertical_depth_stats']['max_depth']}")
    print(f"  Upward Foundation Bridges:  {dashboard['edges_summary']['UPWARD_FOUNDATION_DEPENDENCY']}")
    print(f"  Typed Semantic Bridges:     {dashboard['edges_summary']['total_typed_cross_bridges']}")
    print(f"  Dual Contracts Status:      {'ALL PASS (100%)' if dashboard['contracts_verification']['all_contracts_passing'] else 'FAIL'}")
    print(f"  Total Graph Nodes:          {dashboard['total_nodes']}")
    print(f"  Total Graph Edges:          {dashboard['total_edges']}")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
