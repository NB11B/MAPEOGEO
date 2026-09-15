"""B0-B5 baseline views and scientific capability scoring for PCT."""

from __future__ import annotations

from typing import Any
from mapeogeo.pct.chain import betti_numbers, boundary_matrix, euler_from_chains, simplices_by_degree
from mapeogeo.pct.fixtures import ControlFixture
from mapeogeo.pct.geometry import euler_of_geometry
from mapeogeo.pct.models import CoefficientField


ORDERED_BASELINES = ["B0", "B1", "B2", "B3", "B4", "B5"]


def baseline_features(
    baseline_name: str,
    fixture: ControlFixture,
    probe_data: dict[str, Any] | None = None,
    persistence_data: list[Any] | None = None,
    map_data: dict[str, Any] | None = None,
    field: CoefficientField = CoefficientField.Q,
) -> Any:
    """Extract representation for a given baseline B0-B5."""
    if baseline_name == "B0":
        # Global Euler characteristic
        if fixture.complex is not None:
            return euler_from_chains(fixture.complex)
        elif fixture.geometry is not None:
            return euler_of_geometry(fixture.geometry)
        elif fixture.expected_euler is not None:
            return fixture.expected_euler
        return None

    elif baseline_name == "B1":
        # Ordered Betti tuple
        if fixture.complex is not None:
            betti = betti_numbers(fixture.complex, field)
            return tuple(betti.get(k, 0) for k in range(max(betti.keys()) + 1))
        elif fixture.expected_betti is not None:
            eb = fixture.expected_betti
            return tuple(eb.get(k, 0) for k in range(max(eb.keys()) + 1))
        return None

    elif baseline_name == "B2":
        # Sorted persistence tuples (dimension, birth, death, essential)
        if persistence_data is not None:
            pairs = []
            for p in persistence_data:
                # p can be PersistencePair or dict
                if hasattr(p, "dimension"):
                    pairs.append((p.dimension, p.birth, p.death, p.essential))
                elif isinstance(p, dict):
                    pairs.append((p["dimension"], p["birth"], p["death"], p["essential"]))
            return tuple(sorted(pairs, key=lambda x: (x[0], x[1], str(x[2]), x[3])))
        return None

    elif baseline_name == "B3":
        # Parameterized Euler response field
        if probe_data is not None and "responses" in probe_data:
            resps = probe_data["responses"]
            # Return tuple of sorted-direction responses
            return tuple((th, tuple(resps[th])) for th in sorted(resps.keys()))
        return None

    elif baseline_name == "B4":
        # Chain dimensions + exact boundary matrices (no maps)
        if fixture.complex is not None:
            deg_map = simplices_by_degree(fixture.complex)
            dims = tuple(len(deg_map.get(k, [])) for k in range(max(deg_map.keys()) + 1))
            matrices = []
            for k in range(1, max(deg_map.keys()) + 1):
                mat = boundary_matrix(fixture.complex, k)
                matrices.append(tuple(tuple(int(mat[r, c]) for c in range(mat.cols)) for r in range(mat.rows)))
            return (dims, tuple(matrices))
        return None

    elif baseline_name == "B5":
        # B4 + chain-map matrices/residuals + event provenance
        b4 = baseline_features("B4", fixture, probe_data, persistence_data, map_data, field)
        map_repr = None
        if map_data is not None:
            # Map residual nonzeros and pass status
            map_repr = (
                map_data.get("pass", False),
                tuple(sorted(map_data.get("residual_nonzero_entries", {}).items())),
            )
        return (b4, map_repr)

    else:
        raise ValueError(f"Unknown baseline: {baseline_name}")


def lowest_capable_baseline(capability_results: dict[str, bool]) -> str | None:
    """Return the lowest capable baseline in B0-B5 hierarchy."""
    for b in ORDERED_BASELINES:
        if capability_results.get(b, False):
            return b
    return None
