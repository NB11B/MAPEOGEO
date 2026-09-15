#!/usr/bin/env python3
"""MAPEOGEO v0.12 Cross-Source Mathematics Expansion Runner.

Ingests Sheldon Axler's "Linear Algebra Done Right" (4th Edition) as Source B alongside
Gallier-Quaintance (Source A), establishes the 3-layer ontology (Source Declarations ->
Canonical Objects -> Formal / Executable Views), computes dashboard metrics, and produces
scientific convergence evidence.
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

from scripts.import_axler_v0_12 import (
    DEFAULT_CACHE_PATH,
    FORBIDDEN_PERSISTED_KEYS,
    AxlerDeclaration,
    get_axler_declarations,
)
from scripts.import_gallier_v0_12 import (
    GallierDeclaration,
    get_gallier_declarations,
    ingest_gallier_declarations,
)

STAGE = "v0.12"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"


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


def ingest_gallier_declarations(
    graph: dict[str, Any],
    declarations: list[GallierDeclaration],
) -> dict[str, Any]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    book_node_id = "src:book"
    for decl in declarations:
        node_dict = {
            "id": decl.node_id,
            "type": "SOURCE_DECLARATION",
            "label": decl.label,
            "attributes": {
                "source_id": decl.source_id,
                "corpus": "GALLIER",
                "decl_type": decl.decl_type,
                "chapter_section": decl.chapter_section,
                "page": decl.page,
                "statement_sha256": decl.statement_sha256,
                "statement_chars": decl.char_count,
                "direct_status": decl.representation_profile.get("direct_status", "DUAL_DIRECT"),
                "eo_tags": decl.representation_profile.get("eo_tags", []),
                "geo_tags": decl.representation_profile.get("geo_tags", []),
                "representation_kinds": decl.representation_profile.get("representation_kinds", []),
                "diversity_count": decl.representation_profile.get("diversity_count", 1),
                "stage": STAGE,
            },
        }
        add_node(nodes, by_id, node_dict)

        if book_node_id in by_id:
            edge_id = f"e:src:{decl.node_id}:{book_node_id}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": edge_id,
                    "type": "SOURCED_FROM",
                    "source": decl.node_id,
                    "target": book_node_id,
                    "attributes": {
                        "corpus": "GALLIER",
                        "chapter_section": decl.chapter_section,
                        "stage": STAGE,
                    },
                },
            )
    return graph


def ingest_axler_declarations(
    graph: dict[str, Any],
    declarations: list[AxlerDeclaration],
) -> dict[str, Any]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    # Register Axler source book container
    axler_book_id = "src:axler_book"
    add_node(
        nodes,
        by_id,
        {
            "id": axler_book_id,
            "type": "SOURCE",
            "label": "Linear Algebra Done Right (4th Edition, 2026-08-16)",
            "attributes": {
                "source_id": AXLER_SOURCE_ID,
                "authors": ["Sheldon Axler"],
                "edition": "Fourth Edition",
                "version_date": "2026-08-16",
                "license": "CC BY-NC 4.0",
                "url": "https://linear.axler.net/LADR4e.pdf",
                "stage": STAGE,
            },
        },
    )

    # Ingest individual Axler declarations
    for decl in declarations:
        node_dict = {
            "id": decl.node_id,
            "type": "SOURCE_DECLARATION",
            "label": decl.label,
            "attributes": {
                "source_id": decl.source_id,
                "corpus": "AXLER",
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

        # Connect to Axler book container
        edge_id = f"e:src:{decl.node_id}:{axler_book_id}"
        add_edge(
            edges,
            edge_ids,
            {
                "id": edge_id,
                "type": "SOURCED_FROM",
                "source": decl.node_id,
                "target": axler_book_id,
                "attributes": {
                    "corpus": "AXLER",
                    "chapter_section": decl.chapter_section,
                    "stage": STAGE,
                },
            },
        )

    # Establish internal structural dependency edges for Axler
    axler_node_map = {
        d.node_id.split(":")[-1].replace("_", "."): d.node_id
        for d in declarations
    }
    for decl in declarations:
        for ref_num in decl.structural_refs:
            if ref_num in axler_node_map:
                target_node_id = axler_node_map[ref_num]
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
                            "corpus": "AXLER",
                            "reference_type": "STRUCTURAL_CITATION",
                            "stage": STAGE,
                        },
                    },
                )

    return graph


def ingest_canonical_alignments(
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
        "aligned_canonical_objects": 0,
        "total_alignments": 0,
        "axler_alignments": 0,
        "gallier_alignments": 0,
        "cross_source_same": 0,
        "cross_source_scoped_overlap": 0,
        "cross_source_related": 0,
        "unresolved": 0,
        "canonical_details": [],
    }

    for co in canonical_objects:
        cid = co["id"]
        cname = co["name"]
        domain = co.get("domain", "Linear Algebra")
        desc = co.get("description", "")
        formal_decl = co.get("formal_decl")
        rep_diversity = co.get("representation_kinds") or co.get("representation_diversity", ["abstract", "algebraic"])

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
                    "diversity_count": len(rep_diversity),
                    "stage": STAGE,
                },
            },
        )

        alignments = co.get("alignments", [])
        gallier_sources = []
        axler_sources = []

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

            if status == "CROSS_SOURCE_SAME":
                alignment_summary["cross_source_same"] += 1
            elif status == "CROSS_SOURCE_SCOPED_OVERLAP":
                alignment_summary["cross_source_scoped_overlap"] += 1
            elif status == "CROSS_SOURCE_RELATED_NOT_SAME":
                alignment_summary["cross_source_related"] += 1
            elif status == "UNRESOLVED":
                alignment_summary["unresolved"] += 1

            # Fail-closed provenance: verify source node exists in graph
            if src_id not in by_id:
                raise ValueError(
                    f"Fail-closed provenance error: Source declaration '{src_id}' referenced in canonical object '{cid}' ({corpus}) is not present in graph!"
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

        # Cross-Source Bridge (S_A <-> S_B)
        if gallier_sources and axler_sources:
            alignment_summary["aligned_canonical_objects"] += 1
            for g_id, g_stat in gallier_sources:
                for a_id, a_stat in axler_sources:
                    if g_stat == "UNRESOLVED" or a_stat == "UNRESOLVED":
                        continue

                    if g_stat == "CROSS_SOURCE_SAME" and a_stat == "CROSS_SOURCE_SAME":
                        bridge_type = "SAME_SEMANTICS"
                    elif g_stat == "CROSS_SOURCE_SCOPED_OVERLAP" or a_stat == "CROSS_SOURCE_SCOPED_OVERLAP":
                        bridge_type = "SCOPED_OVERLAP"
                    else:
                        bridge_type = "RELATED_TO"

                    bridge_edge_id = f"e:{bridge_type.lower()}:{g_id}:{a_id}"
                    add_edge(
                        edges,
                        edge_ids,
                        {
                            "id": bridge_edge_id,
                            "type": bridge_type,
                            "source": g_id,
                            "target": a_id,
                            "attributes": {
                                "canonical_object": cid,
                                "gallier_status": g_stat,
                                "axler_status": a_stat,
                                "relation_type": bridge_type,
                                "stage": STAGE,
                            },
                        },
                    )

        alignment_summary["canonical_details"].append({
            "id": cid,
            "name": cname,
            "domain": domain,
            "has_gallier": len(gallier_sources) > 0,
            "has_axler": len(axler_sources) > 0,
            "has_formal": formal_decl is not None,
            "is_cross_source": len(gallier_sources) > 0 and len(axler_sources) > 0,
        })

    return graph, alignment_summary


def compute_expansion_metrics(
    graph: dict[str, Any],
    alignment_summary: dict[str, Any],
) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    source_decls = [n for n in nodes if n.get("type") == "SOURCE_DECLARATION"]
    canonical_objs = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    gallier_decls = [n for n in source_decls if n.get("attributes", {}).get("source_id") == GALLIER_SOURCE_ID]
    axler_decls = [n for n in source_decls if n.get("attributes", {}).get("source_id") == AXLER_SOURCE_ID]

    # Verify disjoint partition
    assert len(gallier_decls) + len(axler_decls) == len(source_decls), "Disjoint source declaration partition violated"

    eo_decls = [n for n in source_decls if "EO" in n.get("attributes", {}).get("direct_status", "")]
    geo_decls = [n for n in source_decls if "GEO" in n.get("attributes", {}).get("direct_status", "")]
    formal_linked = [co for co in canonical_objs if co.get("attributes", {}).get("formal_decl")]

    same_semantics_edges = [e for e in edges if e.get("type") == "SAME_SEMANTICS"]
    scoped_overlap_edges = [e for e in edges if e.get("type") == "SCOPED_OVERLAP"]
    related_to_edges = [e for e in edges if e.get("type") == "RELATED_TO"]
    represents_edges = [e for e in edges if e.get("type") == "REPRESENTS"]
    depends_on_edges = [e for e in edges if e.get("type") == "DEPENDS_ON"]
    sourced_from_edges = [e for e in edges if e.get("type") == "SOURCED_FROM"]

    total_bridge_edges = len(same_semantics_edges) + len(scoped_overlap_edges) + len(related_to_edges)
    total_paths = len(depends_on_edges) + len(represents_edges) + total_bridge_edges

    domains = sorted(list(set(co.get("attributes", {}).get("domain", "Linear Algebra") for co in canonical_objs)))

    return {
        "stage": STAGE,
        "primary_dashboard": {
            "N_source": len(source_decls),
            "source_breakdown": {
                "S_A_gallier": len(gallier_decls),
                "S_B_axler": len(axler_decls),
            },
            "N_canonical": len(canonical_objs),
            "N_cross_source": alignment_summary["aligned_canonical_objects"],
            "N_EO": len(eo_decls),
            "N_GEO": len(geo_decls),
            "N_formal": len(formal_linked),
            "N_paths": total_paths,
            "D_domains": domains,
            "D_domains_count": len(domains),
        },
        "coverage_metrics": {
            "cross_source_coverage_rate": alignment_summary["aligned_canonical_objects"] / max(len(canonical_objs), 1),
            "unresolved_rate": alignment_summary["unresolved"] / max(alignment_summary["total_alignments"], 1),
            "total_alignments": alignment_summary["total_alignments"],
            "same_semantics_bridges": len(same_semantics_edges),
            "scoped_overlap_bridges": len(scoped_overlap_edges),
            "related_to_bridges": len(related_to_edges),
            "total_cross_source_bridges": total_bridge_edges,
        },
        "edges_summary": {
            "total_edges": len(edges),
            "SAME_SEMANTICS": len(same_semantics_edges),
            "SCOPED_OVERLAP": len(scoped_overlap_edges),
            "RELATED_TO": len(related_to_edges),
            "REPRESENTS": len(represents_edges),
            "DEPENDS_ON": len(depends_on_edges),
            "SOURCED_FROM": len(sourced_from_edges),
        },
    }


def validate_against_preregistration(
    metrics: dict[str, Any],
    prereg_path: Path,
) -> dict[str, Any]:
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    tolerances = prereg.get("tolerances", {})
    dash = metrics["primary_dashboard"]
    coverage = metrics.get("coverage_metrics", {})

    min_axler = tolerances.get("min_axler_declarations", 30)
    min_canonical = tolerances.get("min_canonical_objects", 25)
    min_matches = tolerances.get("min_cross_source_matches", 15)
    max_unresolved = tolerances.get("max_unresolved_rate", 0.50)

    unresolved_rate = coverage.get("unresolved_rate", 0.0)

    checks = {
        "N_source_ge_min": dash["N_source"] >= min_axler,
        "N_canonical_ge_min": dash["N_canonical"] >= min_canonical,
        "N_cross_source_ge_min": dash["N_cross_source"] >= min_matches,
        "unresolved_rate_le_max": unresolved_rate <= max_unresolved,
    }

    all_passed = all(checks.values())
    return {
        "engine_validity": "VALID",
        "scientific_result": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO v0.12 Cross-Source Mathematics Expansion Runner")
    parser.add_argument("--base-graph", type=Path, default=ROOT / "data" / "gallier_quaintance_graph_v0_3.json.gz")
    parser.add_argument("--alignments", type=Path, default=ROOT / "formal" / "cross_source_alignments_v0_12.json")
    parser.add_argument("--preregistration", type=Path, default=ROOT / "evidence" / "v0_12_preregistration.json")
    parser.add_argument("--pdf-path", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "cross_source_v0_12")
    parser.add_argument("--mock", action="store_true", help="Use mock Axler declarations")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load base graph
    if args.base_graph.exists():
        graph = load_json_or_gz(args.base_graph)
    else:
        graph = {"nodes": [], "edges": []}

    # 2. Ingest Gallier declarations
    gallier_decls = get_gallier_declarations()
    graph = ingest_gallier_declarations(graph, gallier_decls)

    # 3. Extract & Ingest Axler declarations
    axler_decls = get_axler_declarations(
        pdf_path=args.pdf_path,
        use_mock=args.mock,
        auto_download=True,
    )
    graph = ingest_axler_declarations(graph, axler_decls)

    # 4. Ingest canonical objects and cross-source alignments (fail-closed)
    alignments_data = json.loads(args.alignments.read_text(encoding="utf-8"))
    graph, align_summary = ingest_canonical_alignments(graph, alignments_data)

    # 5. Compute primary dashboard metrics
    metrics = compute_expansion_metrics(graph, align_summary)

    # 6. Validate against preregistration
    eval_result = validate_against_preregistration(metrics, args.preregistration)

    # 7. Emit artifacts
    graph_out = args.out_dir / "mapeogeo_v0_12_graph.json.gz"
    save_graph_gz(graph, graph_out)

    align_out = args.out_dir / "cross_source_alignments.json"
    align_out.write_text(json.dumps(align_summary, indent=2), encoding="utf-8")

    metrics_out = args.out_dir / "expansion_metrics.json"
    metrics_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    results_out = args.out_dir / "scientific_results.json"
    results_payload = {
        "stage": STAGE,
        "run_id": "MAPEOGEO-CROSS-SOURCE-V0.12",
        "governing_law": "build a broad, source-grounded mathematical map with EO and GEO as executable views, FORMAL as a verified view, and relationships between mathematics as the primary object",
        "evaluation": eval_result,
        "primary_dashboard": metrics["primary_dashboard"],
        "coverage_metrics": metrics["coverage_metrics"],
    }
    results_out.write_text(json.dumps(results_payload, indent=2), encoding="utf-8")

    print("=== MAPEOGEO v0.12 Cross-Source Expansion Complete ===")
    print(f"Engine Validity:    {eval_result['engine_validity']}")
    print(f"Scientific Result:  {eval_result['scientific_result']}")
    print(f"N_source:           {metrics['primary_dashboard']['N_source']}")
    print(f"  - Gallier:        {metrics['primary_dashboard']['source_breakdown']['S_A_gallier']}")
    print(f"  - Axler:          {metrics['primary_dashboard']['source_breakdown']['S_B_axler']}")
    print(f"N_canonical:        {metrics['primary_dashboard']['N_canonical']}")
    print(f"N_cross_source:     {metrics['primary_dashboard']['N_cross_source']}")
    print(f"N_EO:               {metrics['primary_dashboard']['N_EO']}")
    print(f"N_GEO:              {metrics['primary_dashboard']['N_GEO']}")
    print(f"N_formal:           {metrics['primary_dashboard']['N_formal']}")
    print(f"N_paths:            {metrics['primary_dashboard']['N_paths']}")
    print(f"Domains ({metrics['primary_dashboard']['D_domains_count']}):       {metrics['primary_dashboard']['D_domains']}")
    print(f"Saved artifacts to: {args.out_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
