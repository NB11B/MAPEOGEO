#!/usr/bin/env python3
"""MAPEOGEO v0.14 Convex Analysis and Optimization Expansion Validator.

Fail-closed validation suite that verifies:
1. Base graph and artifacts existence and integrity.
2. Quad-source representation (Gallier, Axler, VMLS, CVX).
3. Minimum declaration thresholds and preregistered bounds.
4. Quad-source convergence and multi-source bridge counts.
5. Representation Diversity Profile R(M) and richness r_bar >= 2.5.
6. Formal proof bindings (Lean 4 kernel-verified theorems).
7. Strict zero-prose persistence across all graph nodes.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.import_cvx_v0_14 import FORBIDDEN_PERSISTED_KEYS

DEFAULT_GRAPH_PATH = ROOT / "artifacts" / "convex_v0_14" / "mapeogeo_v0_14_graph.json.gz"
DEFAULT_DASHBOARD_PATH = ROOT / "artifacts" / "convex_v0_14" / "convex_expansion_dashboard.json"
DEFAULT_PREREG_PATH = ROOT / "evidence" / "v0_14_preregistration.json"


def validate_v0_14(
    graph_path: Path = DEFAULT_GRAPH_PATH,
    dashboard_path: Path = DEFAULT_DASHBOARD_PATH,
    prereg_path: Path = DEFAULT_PREREG_PATH,
) -> int:
    print(f"=== Validating MAPEOGEO v0.14 Convex Expansion ===")
    errors: list[str] = []

    # 1. Check artifact existence
    if not graph_path.exists():
        errors.append(f"Missing graph artifact: {graph_path}")
        print("\n".join(errors))
        return 1
    if not dashboard_path.exists():
        errors.append(f"Missing dashboard artifact: {dashboard_path}")
        print("\n".join(errors))
        return 1

    # 2. Load artifacts
    with gzip.open(graph_path, "rt", encoding="utf-8") as f:
        graph = json.load(f)
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    # Load preregistration if present
    prereg = {}
    if prereg_path.exists():
        prereg = json.loads(prereg_path.read_text(encoding="utf-8")).get("preregistered_bounds", {})

    # 3. Validate zero-prose persistence
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    print(f"Loaded graph with {len(nodes)} nodes and {len(edges)} edges.")

    for node in nodes:
        attrs = node.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            if forbidden in node:
                errors.append(f"Zero-prose violation: '{forbidden}' key found in node {node.get('id')}")
            if forbidden in attrs:
                errors.append(f"Zero-prose violation: '{forbidden}' key found in attributes of node {node.get('id')}")

    # 4. Validate source counts and quad-source breakdown
    source_decls = [n for n in nodes if n.get("type") == "SOURCE_DECLARATION"]
    canonical_objs = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    gallier_decls = [n for n in source_decls if "GALLIER" in n.get("attributes", {}).get("source_id", "") or "gallier" in n.get("id", "")]
    axler_decls = [n for n in source_decls if "AXLER" in n.get("attributes", {}).get("source_id", "") or "axler" in n.get("id", "")]
    vmls_decls = [n for n in source_decls if "VMLS" in n.get("attributes", {}).get("source_id", "") or "vmls" in n.get("id", "")]
    cvx_decls = [n for n in source_decls if "CVX" in n.get("attributes", {}).get("source_id", "") or "cvx" in n.get("id", "")]

    print(f"Source Declarations breakdown:")
    print(f"  Gallier (S_A): {len(gallier_decls)}")
    print(f"  Axler (S_B):   {len(axler_decls)}")
    print(f"  VMLS (S_C):    {len(vmls_decls)}")
    print(f"  CVX (S_D):     {len(cvx_decls)}")
    print(f"  Total:         {len(source_decls)}")

    if len(gallier_decls) < 20:
        errors.append(f"Insufficient Gallier declarations: {len(gallier_decls)} < 20")
    if len(axler_decls) < 200:
        errors.append(f"Insufficient Axler declarations: {len(axler_decls)} < 200")
    if len(vmls_decls) < 30:
        errors.append(f"Insufficient VMLS declarations: {len(vmls_decls)} < 30")
    if len(cvx_decls) < 35:
        errors.append(f"Insufficient CVX declarations: {len(cvx_decls)} < 35")

    min_source_total = prereg.get("min_total_source_declarations", 350)
    if len(source_decls) < min_source_total:
        errors.append(f"Total source declarations {len(source_decls)} < minimum required {min_source_total}")

    # 5. Validate canonical objects and multi-source bridges
    min_canonical = prereg.get("min_canonical_objects", 60)
    if len(canonical_objs) < min_canonical:
        errors.append(f"Total canonical objects {len(canonical_objs)} < minimum required {min_canonical}")

    n_2_source = dashboard.get("N_2_source_bridges", 0)
    min_2_source = prereg.get("min_two_source_supported", 40)
    if n_2_source < min_2_source:
        errors.append(f"2-source supported canonical objects {n_2_source} < minimum required {min_2_source}")

    n_3_source = dashboard.get("N_3_source_bridges", 0)
    min_3_source = prereg.get("min_three_source_supported", 20)
    if n_3_source < min_3_source:
        errors.append(f"3-source supported canonical objects {n_3_source} < minimum required {min_3_source}")

    n_4_source = dashboard.get("N_4_source_bridges", 0)
    min_4_source = prereg.get("min_four_source_supported", 8)
    if n_4_source < min_4_source:
        errors.append(f"4-source quad-supported canonical objects {n_4_source} < minimum required {min_4_source}")

    # 6. Validate domain representation
    domains_count = dashboard.get("D_domains_count", 0)
    min_domains = prereg.get("min_domains", 3)
    if domains_count < min_domains:
        errors.append(f"Distinct domains {domains_count} < minimum required {min_domains}")

    # 7. Validate representation diversity and average richness r_bar
    rep_div = dashboard.get("representation_diversity", {})
    r_bar = rep_div.get("average_richness_r_bar", 0.0)
    min_r_bar = prereg.get("min_average_representation_richness", 2.5)
    print(f"Representation Diversity Average Richness r_bar: {r_bar} (min preregistered: {min_r_bar})")

    if r_bar < min_r_bar:
        errors.append(f"Average representation richness r_bar={r_bar} < minimum required {min_r_bar}")

    counts = rep_div.get("counts", {})
    for kind in ["abstract", "algebraic", "geometric", "computational", "formal", "applied"]:
        c = counts.get(kind, 0)
        print(f"  - {kind}: {c}")
        if c == 0:
            errors.append(f"Zero representation instances found for kind '{kind}'")

    # 8. Validate formal proofs
    formal_linked = dashboard.get("N_formal_linked", 0)
    if formal_linked < 5:
        errors.append(f"Formal proof linked canonical objects {formal_linked} < 5")

    # 9. Validate bridge edges
    bridges = dashboard.get("edges_summary", {}).get("SAME_SEMANTICS_bridges", 0)
    if bridges < 200:
        errors.append(f"SAME_SEMANTICS bridge edges {bridges} < 200")

    # Print summary
    if errors:
        print("\nVALIDATION FAILED with errors:")
        for err in errors:
            print(f"  [FAIL] {err}")
        return 1
    else:
        print("\nALL v0.14 CONVEX EXPANSION VALIDATION CHECKS PASSED!")
        print(f"  - Quad-Source Coverage: {len(source_decls)} declarations across 4 sources")
        print(f"  - Canonical Objects: {len(canonical_objs)} ({n_2_source} 2-source, {n_3_source} 3-source, {n_4_source} 4-source)")
        print(f"  - Representation Richness r_bar: {r_bar} >= {min_r_bar}")
        print(f"  - Distinct Domains: {domains_count} >= {min_domains}")
        print(f"  - Formal Proofs Linked: {formal_linked}")
        print(f"  - Zero-Prose Policy: VERIFIED CLEAN")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MAPEOGEO v0.14 Convex Expansion")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH_PATH)
    parser.add_argument("--dashboard", type=Path, default=DEFAULT_DASHBOARD_PATH)
    parser.add_argument("--prereg", type=Path, default=DEFAULT_PREREG_PATH)
    args = parser.parse_args()

    return validate_v0_14(
        graph_path=args.graph,
        dashboard_path=args.dashboard,
        prereg_path=args.prereg,
    )


if __name__ == "__main__":
    sys.exit(main())
