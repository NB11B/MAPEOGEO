"""Parameterized geometric probes and response consistency checks."""

from __future__ import annotations

import math
from typing import Any
from shapely.geometry import LineString, MultiPolygon, Polygon

from mapeogeo.pct.geometry import euler_of_geometry


def line_euler_response(
    geom: Any,
    theta: float,
    offset: float,
    extent: float = 10.0,
) -> int:
    """Compute Euler characteristic of the intersection of geom with line(theta, offset)."""
    if geom is None or geom.is_empty:
        return 0

    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    px = offset * cos_t
    py = offset * sin_t

    # Tangent vector: (-sin_t, cos_t)
    p1 = (px + extent * sin_t, py - extent * cos_t)
    p2 = (px - extent * sin_t, py + extent * cos_t)

    line = LineString([p1, p2])
    inter = geom.intersection(line)
    return euler_of_geometry(inter)


def line_response_field(
    geom: Any,
    directions: list[float],
    offsets: list[float],
    extent: float = 10.0,
) -> dict[str, Any]:
    """Compute 2-D line Euler response field over given directions and offsets."""
    sorted_offsets = sorted(offsets)
    responses: dict[float, list[int]] = {}

    for th in directions:
        row = [line_euler_response(geom, th, off, extent) for off in sorted_offsets]
        responses[th] = row

    return {
        "directions": directions,
        "offsets": sorted_offsets,
        "responses": responses,
    }


def support_samples(geom: Any, directions: list[float]) -> dict[float, float]:
    """Compute exact support function values h(theta) = max_{(x,y) in geom} (x*cos(th) + y*sin(th))."""
    if geom is None or geom.is_empty:
        return {th: 0.0 for th in directions}

    vertices: list[tuple[float, float]] = []
    if isinstance(geom, Polygon):
        vertices.extend(list(geom.exterior.coords))
    elif isinstance(geom, MultiPolygon):
        for p in geom.geoms:
            vertices.extend(list(p.exterior.coords))
    else:
        # Fallback coordinate extraction
        if hasattr(geom, "coords"):
            vertices.extend(list(geom.coords))
        else:
            vertices.extend(list(geom.convex_hull.exterior.coords))

    samples: dict[float, float] = {}
    for th in directions:
        cos_t = math.cos(th)
        sin_t = math.sin(th)
        max_proj = max(x * cos_t + y * sin_t for x, y in vertices)
        samples[th] = max_proj

    return samples


def validate_convex_line_response(field_data: dict[str, Any]) -> dict[str, Any]:
    """Verify that every direction's nonzero responses form at most one contiguous block."""
    responses: dict[float, list[int]] = field_data.get("responses", {})
    failing_directions: list[float] = []
    details: dict[float, dict[str, Any]] = {}

    for th, row in responses.items():
        nonzero_indices = [i for i, val in enumerate(row) if val > 0]
        if not nonzero_indices:
            details[th] = {"contiguous": True, "num_blocks": 0}
            continue

        # Check if indices form a single contiguous sequence
        min_idx = nonzero_indices[0]
        max_idx = nonzero_indices[-1]
        expected_len = max_idx - min_idx + 1
        is_contiguous = (len(nonzero_indices) == expected_len)

        if not is_contiguous:
            failing_directions.append(th)
            details[th] = {
                "contiguous": False,
                "nonzero_indices": nonzero_indices,
                "span": (min_idx, max_idx),
            }
        else:
            details[th] = {
                "contiguous": True,
                "span": (min_idx, max_idx),
            }

    return {
        "valid": len(failing_directions) == 0,
        "failing_directions": failing_directions,
        "details": details,
    }
