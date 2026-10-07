"""Historical Reveal: Progressively unmasks post-1950 mathematics across horizons."""

import json
from pathlib import Path
from typing import Dict, List, Any

POST_1950_HISTORICAL_REVELATIONS = [
    # Horizon 1955 (5 years)
    {
        "discovery_id": "DISC_1955_SERRE_FAC",
        "title": "Faisceaux algébriques cohérents (FAC)",
        "author": "Jean-Pierre Serre",
        "year": 1955,
        "horizon": 1955,
        "domain": "sheaf_and_cohomology",
        "structural_coordinates": {
            "Delta": "preservation",
            "I": "topology",
            "W": "universal_property",
            "sigma": "EQUIVALENT_TO",
            "Pi": "covariant",
            "Gamma": "even"
        },
        "target_prototype": "SLOT_SHEAF_COHOMOLOGY"
    },
    {
        "discovery_id": "DISC_1956_CARTAN_EILENBERG",
        "title": "Homological Algebra (Ext and Tor Functors)",
        "author": "Henri Cartan & Samuel Eilenberg",
        "year": 1956,
        "horizon": 1960,
        "domain": "homological_algebra",
        "structural_coordinates": {
            "Delta": "addition",
            "I": "algebraic_structure",
            "W": "homotopy",
            "sigma": "SAME_SEMANTICS",
            "Pi": "contravariant",
            "Gamma": "graded_mixed"
        },
        "target_prototype": "SLOT_DERIVED_FUNCTOR_EXT"
    },
    # Horizon 1960 (10 years)
    {
        "discovery_id": "DISC_1960_GROTHENDIECK_EGA",
        "title": "Éléments de géométrie algébrique (Scheme Spectrum)",
        "author": "Alexander Grothendieck",
        "year": 1960,
        "horizon": 1960,
        "domain": "algebraic_geometry",
        "structural_coordinates": {
            "Delta": "addition",
            "I": "algebraic_structure",
            "W": "universal_property",
            "sigma": "SAME_SEMANTICS",
            "Pi": "contravariant",
            "Gamma": "ungraded"
        },
        "target_prototype": "SLOT_ALGEBRAIC_SCHEME_SPECTRUM"
    },
    # Horizon 1975 (25 years)
    {
        "discovery_id": "DISC_1963_ATIYAH_SINGER",
        "title": "The Index of Elliptic Operators on Compact Manifolds",
        "author": "Michael Atiyah & Isadore Singer",
        "year": 1963,
        "horizon": 1975,
        "domain": "differential_analysis",
        "structural_coordinates": {
            "Delta": "preservation",
            "I": "metric",
            "W": "isomorphism",
            "sigma": "EQUIVALENT_TO",
            "Pi": "self-dual",
            "Gamma": "odd"
        },
        "target_prototype": "SLOT_INDEX_THEOREM"
    },
    {
        "discovery_id": "DISC_1967_QUILLEN_SPECTRAL",
        "title": "Axiomatic Homotopy Theory and Spectral Systems",
        "author": "Daniel Quillen",
        "year": 1967,
        "horizon": 1975,
        "domain": "algebraic_topology",
        "structural_coordinates": {
            "Delta": "modification",
            "I": "topology",
            "W": "commutative_diagram",
            "sigma": "SCOPED_OVERLAP",
            "Pi": "covariant",
            "Gamma": "even"
        },
        "target_prototype": "SLOT_SPECTRAL_SEQUENCE_HOMOTOPY"
    }
]

def progressive_historical_reveal(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    horizons = [1955, 1960, 1975, 2000]
    horizon_data = {}

    for h in horizons:
        unmasked = [d for d in POST_1950_HISTORICAL_REVELATIONS if d["year"] <= h]
        h_data = {
            "horizon_year": h,
            "years_elapsed": h - 1950,
            "accumulated_discoveries_count": len(unmasked),
            "discoveries": unmasked
        }
        horizon_data[h] = h_data
        with open(output_dir / f"reveal_{h}.json", "w", encoding="utf-8") as f:
            json.dump(h_data, f, indent=2)

    return horizon_data
