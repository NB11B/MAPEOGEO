"""Historical Source Registry and Temporal Verification for t <= 1950."""

import json
from pathlib import Path
from typing import Dict, List, Any

HISTORICAL_PRE_1950_SOURCES = [
    {"source_id": "SRC_1895_POINCARE", "title": "Analysis Situs", "year": 1895, "domain": "algebraic_topology"},
    {"source_id": "SRC_1900_HILBERT", "title": "Mathematical Problems", "year": 1900, "domain": "foundations_and_algebra"},
    {"source_id": "SRC_1910_STEINITZ", "title": "Algebraische Theorie der Körper", "year": 1910, "domain": "field_theory"},
    {"source_id": "SRC_1921_NOETHER", "title": "Idealtheorie in Ringbereichen", "year": 1921, "domain": "commutative_algebra"},
    {"source_id": "SRC_1926_LEFSCHETZ", "title": "Intersections and Transformations of Complexes", "year": 1926, "domain": "topology_intersection"},
    {"source_id": "SRC_1931_DE_RHAM", "title": "Sur l'analyse situs des variétés à n dimensions", "year": 1931, "domain": "differential_forms"},
    {"source_id": "SRC_1932_BANACH", "title": "Théorie des opérations linéaires", "year": 1932, "domain": "functional_analysis"},
    {"source_id": "SRC_1934_PONTRYAGIN", "title": "The Theory of Topological Commutative Groups", "year": 1934, "domain": "duality_theory"},
    {"source_id": "SRC_1935_HUREWICZ", "title": "Homotopie und Homologiegruppen", "year": 1935, "domain": "homotopy_theory"},
    {"source_id": "SRC_1941_HODGE", "title": "The Theory and Applications of Harmonic Integrals", "year": 1941, "domain": "harmonic_integrals"},
    {"source_id": "SRC_1945_EILENBERG_MACLANE", "title": "General Theory of Natural Equivalences", "year": 1945, "domain": "early_category_theory"},
    {"source_id": "SRC_1946_WEIL", "title": "Foundations of Algebraic Geometry", "year": 1946, "domain": "algebraic_geometry"},
    {"source_id": "SRC_1950_SCHWARTZ", "title": "Théorie des distributions", "year": 1950, "domain": "generalized_functions"},
    {"source_id": "SRC_1950_CARTAN", "title": "Cohomologie des groupes, suite spectrale, faisceaux", "year": 1950, "domain": "early_sheaves"}
]

def verify_and_manifest_sources(output_dir: Path, cutoff_year: int = 1950) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    verified_sources = []
    for s in HISTORICAL_PRE_1950_SOURCES:
        assert s["year"] <= cutoff_year, f"Temporal violation: {s['source_id']} has year {s['year']} > {cutoff_year}"
        verified_sources.append({**s, "temporal_status": "VERIFIED_PRE_CUTOFF"})

    manifest = {
        "cutoff_year": cutoff_year,
        "verified_source_count": len(verified_sources),
        "sources": verified_sources,
        "earliest_year": min(s["year"] for s in verified_sources),
        "latest_year": max(s["year"] for s in verified_sources),
        "verified_immutable": True
    }

    with open(output_dir / "historical_source_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest
