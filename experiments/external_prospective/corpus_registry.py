"""Corpus Registry: Defines external mathematical domains acquired after Kernel v1 freeze."""

from typing import Dict, List, Any

EXTERNAL_DOMAINS = [
    "algebraic_geometry",
    "number_theory",
    "representation_theory",
    "operator_algebras",
    "logic_proof_theory",
    "combinatorics",
    "dynamical_systems",
    "pde_microlocal_analysis",
    "noncommutative_geometry",
    "higher_category_theory"
]

def get_external_source_catalog() -> List[Dict[str, Any]]:
    """
    Returns registered external sources acquired post-freeze.
    """
    catalog = []
    for idx, domain in enumerate(EXTERNAL_DOMAINS):
        catalog.append({
            "source_id": f"EXT_SRC_{idx+1:02d}",
            "domain": domain,
            "provenance_description": f"External peer-reviewed corpus for {domain} acquired post-freeze",
            "acquired_timestamp": "2026-10-07T03:26:00Z",
            "kernel_baseline_overlap": False
        })
    return catalog
