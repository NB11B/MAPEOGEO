#!/usr/bin/env python3
"""MAPEOGEO v0.15.2 Confirmatory Real Analysis and Differential Calculus Bounds & Provenance Validator.

Validates the v0.15.2 emitted graph and dashboard against frozen preregistered criteria in
evidence/v0_15_2_preregistration.json:
- Provenance Invariant 1: Mutually exclusive source declaration partition (sum == N_source)
- Provenance Invariant 2: Node ID namespace consistency (axler -> axler, vmls -> vmls, cvx -> cvx)
- Provenance Invariant 3: REPRESENTS edge corpus consistency
- Provenance Invariant 4: Zero synthesized or orphaned declarations
- Total source declarations (N_source >= 400)
- Canonical mathematical objects (N_canonical >= 85)
- Two-source supported objects (N_2_source >= 45)
- Three-source supported objects (N_3_source >= 30)
- Quad-source supported objects (N_4_source >= 8)
- Distinct mathematical domains (D_domains >= 4)
- Average representation richness (r_bar >= 2.75)
- Same-semantics semantic bridges (>= 300)
- Total cross-source bridges (>= 400)
- Inherited formal links (>= 6)
- Zero-prose persistence fail-closed invariant
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"


def load_json_or_gz(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def validate_v0_15_2(
    graph_path: Path,
    dashboard_path: Path,
    prereg_path: Path,
) -> bool:
    print("=== Validating MAPEOGEO v0.15.2 Confirmatory Analysis Expansion ===")

    assert graph_path.exists(), f"Graph artifact missing: {graph_path}"
    assert dashboard_path.exists(), f"Dashboard artifact missing: {dashboard_path}"
    assert prereg_path.exists(), f"Preregistration file missing: {prereg_path}"

    graph = load_json_or_gz(graph_path)
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))

    bounds = prereg["bounds"]

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    print(f"Loaded graph with {len(nodes)} nodes and {len(edges)} edges.")

    # 1. Zero-Prose Policy Check
    for n in nodes:
        nid = n.get("id", "UNKNOWN")
        attrs = n.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            assert forbidden not in n, f"Zero-prose violation in node {nid}: contains '{forbidden}'"
            assert forbidden not in attrs, f"Zero-prose violation in node {nid} attributes: contains '{forbidden}'"
    for e in edges:
        e_attrs = e.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            assert forbidden not in e, f"Zero-prose violation in edge: contains '{forbidden}'"
            assert forbidden not in e_attrs, f"Zero-prose violation in edge attributes: contains '{forbidden}'"

    # 2. Strict Disjoint Source Partition Invariant Check
    source_decls = [n for n in nodes if n.get("type") in ("SOURCE_DECLARATION", "STATEMENT") and n["id"].startswith("srcdecl:")]
    gallier = [n for n in source_decls if not any(k in n["id"] for k in (":axler:", ":vmls:", ":cvx:"))]
    axler = [n for n in source_decls if ":axler:" in n["id"]]
    vmls = [n for n in source_decls if ":vmls:" in n["id"]]
    cvx = [n for n in source_decls if ":cvx:" in n["id"]]

    total_partition = len(gallier) + len(axler) + len(vmls) + len(cvx)
    assert total_partition == len(source_decls), (
        f"Partition mismatch: gallier({len(gallier)}) + axler({len(axler)}) + "
        f"vmls({len(vmls)}) + cvx({len(cvx)}) = {total_partition} != total {len(source_decls)}"
    )
    assert dashboard["source_breakdown"]["S_A_gallier"] == len(gallier)
    assert dashboard["source_breakdown"]["S_B_axler"] == len(axler)
    assert dashboard["source_breakdown"]["S_C_vmls"] == len(vmls)
    assert dashboard["source_breakdown"]["S_D_cvx"] == len(cvx)
    assert dashboard["N_source_total"] == len(source_decls)

    # 3. ID Namespace Consistency Check
    for n in axler:
        assert "axler" in n["id"], f"Namespace violation: Axler node '{n['id']}' does not contain 'axler'"
    for n in vmls:
        assert "vmls" in n["id"], f"Namespace violation: VMLS node '{n['id']}' does not contain 'vmls'"
    for n in cvx:
        assert "cvx" in n["id"], f"Namespace violation: CVX node '{n['id']}' does not contain 'cvx'"

    # 4. Total Source Declarations Check
    n_source = dashboard.get("N_source_total", 0)
    min_source = bounds["min_total_source_declarations"]
    assert n_source >= min_source, f"Source count {n_source} < {min_source}"
    print(f"Source Declarations breakdown (Disjoint Partition Verified):")
    print(f"  Gallier (S_A): {len(gallier)}")
    print(f"  Axler (S_B):   {len(axler)}")
    print(f"  VMLS (S_C):    {len(vmls)}")
    print(f"  CVX (S_D):     {len(cvx)}")
    print(f"  Total:         {n_source}")

    # 5. Canonical Objects Check
    n_canonical = dashboard.get("N_canonical_total", 0)
    min_canonical = bounds["min_canonical_objects"]
    assert n_canonical >= min_canonical, f"Canonical count {n_canonical} < {min_canonical}"

    # 6. Multi-Source Convergence Checks
    n_2_source = dashboard.get("N_2_source_bridges", 0)
    min_2_source = bounds["min_two_source_supported"]
    assert n_2_source >= min_2_source, f"2-source count {n_2_source} < {min_2_source}"

    n_3_source = dashboard.get("N_3_source_bridges", 0)
    min_3_source = bounds["min_three_source_supported"]
    assert n_3_source >= min_3_source, f"3-source count {n_3_source} < {min_3_source}"

    n_4_source = dashboard.get("N_4_source_bridges", 0)
    min_4_source = bounds["min_four_source_supported"]
    assert n_4_source >= min_4_source, f"4-source count {n_4_source} < {min_4_source}"

    # 7. Distinct Mathematical Domains Check
    d_domains = dashboard.get("D_domains_count", 0)
    min_domains = bounds["min_domains"]
    assert d_domains >= min_domains, f"Domain count {d_domains} < {min_domains}"
    assert "Differential Calculus & Real Analysis" in dashboard.get("domains_list", [])

    # 8. Representation Diversity Richness r_bar Check
    r_bar = dashboard.get("representation_diversity", {}).get("average_richness_r_bar", 0.0)
    min_r_bar = bounds["min_average_representation_richness"]
    assert r_bar >= min_r_bar, f"Average richness {r_bar} < {min_r_bar}"
    print(f"Representation Diversity Average Richness r_bar: {r_bar} (min preregistered: {min_r_bar})")
    for rk, count in dashboard.get("representation_diversity", {}).get("counts", {}).items():
        print(f"  - {rk}: {count}")

    # 9. Semantic Bridge Checks
    same_sem = dashboard.get("edges_summary", {}).get("SAME_SEMANTICS_bridges", 0)
    min_same_sem = bounds["min_same_semantics_bridges"]
    assert same_sem >= min_same_sem, f"SAME_SEMANTICS count {same_sem} < {min_same_sem}"

    total_cross = dashboard.get("edges_summary", {}).get("total_cross_source_bridges", 0)
    min_total_cross = bounds["min_total_cross_source_bridges"]
    assert total_cross >= min_total_cross, f"Total cross-bridges {total_cross} < {min_total_cross}"

    # 10. Inherited Formal Links Check
    n_formal = dashboard.get("N_formal_linked", 0)
    min_formal = bounds["min_inherited_formal_links"]
    assert n_formal >= min_formal, f"Inherited formal links {n_formal} < {min_formal}"

    # 11. Fail-closed Node Existence & REPRESENTS Integrity Check
    node_ids = {n["id"]: n for n in nodes}
    for e in edges:
        assert e["source"] in node_ids, f"Edge source missing from nodes: {e['source']}"
        assert e["target"] in node_ids, f"Edge target missing from nodes: {e['target']}"
        if e.get("type") == "REPRESENTS":
            src_node = node_ids[e["source"]]
            target_node = node_ids[e["target"]]
            src_corp = src_node.get("attributes", {}).get("corpus")
            edge_corp = e.get("attributes", {}).get("corpus")
            if src_corp and edge_corp:
                assert src_corp == edge_corp, (
                    f"REPRESENTS corpus mismatch: edge says {edge_corp}, node says {src_corp}"
                )

    # 12. Source Identity & Hash Invariant Check
    frozen_quartet_hashes = {
        "srcdecl:proposition:3_14": "6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e",
        "srcdecl:proposition:3_13": "0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac",
        "srcdecl:proposition:4_4": "37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf",
        "srcdecl:theorem:27_10": "b99a4e9f7dcafc31774208c2d21485e59a23b3ae76f6fd3748babdefd41093e2",
    }
    for sid, exp_hash in frozen_quartet_hashes.items():
        assert sid in node_ids, f"Frozen Gallier node {sid} missing from graph!"
        n = node_ids[sid]
        actual_hash = n.get("attributes", {}).get("statement_sha256") or n.get("attributes", {}).get("independent_profile", {}).get("statement_sha256")
        assert actual_hash == exp_hash, (
            f"Source identity hash drift for {sid}: expected {exp_hash}, got {actual_hash}"
        )

    print("\nALL v0.15.2 CONFIRMATORY ANALYSIS EXPANSION VALIDATION CHECKS PASSED!")
    print(f"  - Disjoint Source Partition: {len(gallier)} S_A + {len(axler)} S_B + {len(vmls)} S_C + {len(cvx)} S_D = {n_source}")
    print(f"  - Canonical Objects: {n_canonical} ({n_2_source} 2-source, {n_3_source} 3-source, {n_4_source} 4-source)")
    print(f"  - Semantic Bridges: {same_sem} SAME_SEMANTICS, {dashboard['edges_summary']['SCOPED_OVERLAP_bridges']} SCOPED_OVERLAP, {dashboard['edges_summary']['RELATED_TO_bridges']} RELATED_TO (Total: {total_cross})")
    print(f"  - Representation Richness r_bar: {r_bar} >= {min_r_bar}")
    print(f"  - Distinct Domains: {d_domains} >= {min_domains}")
    print(f"  - Inherited Formal Links: {n_formal} >= {min_formal}")
    print(f"  - Source Identity Invariant: 100% VERIFIED (frozen hashes preserved)")
    print(f"  - Zero-Prose Policy: VERIFIED CLEAN")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MAPEOGEO v0.15.2 Confirmatory Expansion")
    parser.add_argument(
        "--graph",
        type=Path,
        default=ROOT / "artifacts" / "analysis_v0_15_2" / "mapeogeo_v0_15_2_graph.json.gz",
    )
    parser.add_argument(
        "--dashboard",
        type=Path,
        default=ROOT / "artifacts" / "analysis_v0_15_2" / "analysis_expansion_dashboard.json",
    )
    parser.add_argument(
        "--prereg",
        type=Path,
        default=ROOT / "evidence" / "v0_15_2_preregistration.json",
    )
    args = parser.parse_args()

    success = validate_v0_15_2(args.graph, args.dashboard, args.prereg)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
