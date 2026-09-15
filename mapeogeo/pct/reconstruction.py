"""Deterministic convex polygon reconstruction from support probes via halfspace clipping."""

from __future__ import annotations

import math
from typing import Any
from shapely.geometry import Polygon

from mapeogeo.pct.geometry import euler_of_geometry
from mapeogeo.pct.probes import support_samples


def clip_polygon_halfspace(
    vertices: list[tuple[float, float]],
    normal: tuple[float, float],
    bound: float,
    eps: float = 1e-12,
) -> list[tuple[float, float]]:
    """Clip a convex polygon with a halfspace normal * (x, y) <= bound using Sutherland-Hodgman."""
    if not vertices:
        return []

    nx, ny = normal
    out_vertices: list[tuple[float, float]] = []

    def is_inside(p: tuple[float, float]) -> bool:
        return (nx * p[0] + ny * p[1]) <= bound + eps

    def line_intersection(
        p1: tuple[float, float],
        p2: tuple[float, float],
    ) -> tuple[float, float]:
        d1 = nx * p1[0] + ny * p1[1] - bound
        d2 = nx * p2[0] + ny * p2[1] - bound
        t = d1 / (d1 - d2) if (d1 - d2) != 0.0 else 0.0
        ix = p1[0] + t * (p2[0] - p1[0])
        iy = p1[1] + t * (p2[1] - p1[1])
        return (ix, iy)

    n = len(vertices)
    for i in range(n):
        s = vertices[i]
        e = vertices[(i + 1) % n]

        s_in = is_inside(s)
        e_in = is_inside(e)

        if e_in:
            if s_in:
                out_vertices.append(e)
            else:
                out_vertices.append(line_intersection(s, e))
                out_vertices.append(e)
        else:
            if s_in:
                out_vertices.append(line_intersection(s, e))

    return out_vertices


def reconstruct_from_support(
    samples: dict[float, float],
    initial_extent: float = 10.0,
) -> Polygon:
    """Reconstruct convex polygon from support function samples."""
    # Start with bounding box [-initial_extent, initial_extent]^2
    vertices = [
        (-initial_extent, -initial_extent),
        (initial_extent, -initial_extent),
        (initial_extent, initial_extent),
        (-initial_extent, initial_extent),
    ]

    for th, h in samples.items():
        normal = (math.cos(th), math.sin(th))
        vertices = clip_polygon_halfspace(vertices, normal, h)
        if len(vertices) < 3:
            return Polygon()

    # Deduplicate consecutive points
    cleaned: list[tuple[float, float]] = []
    for v in vertices:
        if not cleaned or (abs(v[0] - cleaned[-1][0]) > 1e-12 or abs(v[1] - cleaned[-1][1]) > 1e-12):
            cleaned.append(v)
    if len(cleaned) >= 3 and (abs(cleaned[0][0] - cleaned[-1][0]) < 1e-12 and abs(cleaned[0][1] - cleaned[-1][1]) < 1e-12):
        cleaned.pop()

    if len(cleaned) < 3:
        return Polygon()

    poly = Polygon(cleaned)
    return poly if poly.is_valid else poly.buffer(0)


def reconstruction_metrics(original: Polygon, reconstructed: Polygon) -> dict[str, Any]:
    """Compute Hausdorff distance, area error, perimeter error, and Euler match."""
    if reconstructed is None or reconstructed.is_empty:
        return {
            "hausdorff": float("inf"),
            "area_error": -float(original.area),
            "abs_area_error": float(original.area),
            "perimeter_error": -float(original.length),
            "abs_perimeter_error": float(original.length),
            "euler_match": False,
            "original_area": float(original.area),
            "reconstructed_area": 0.0,
        }

    h_dist = float(original.hausdorff_distance(reconstructed))
    a_err = float(reconstructed.area - original.area)
    p_err = float(reconstructed.length - original.length)
    e_match = (euler_of_geometry(original) == euler_of_geometry(reconstructed))

    return {
        "hausdorff": h_dist,
        "area_error": a_err,
        "abs_area_error": abs(a_err),
        "perimeter_error": p_err,
        "abs_perimeter_error": abs(p_err),
        "euler_match": e_match,
        "original_area": float(original.area),
        "reconstructed_area": float(reconstructed.area),
    }


def one_probe_ablations(
    geom: Polygon,
    directions: list[float],
    initial_extent: float = 10.0,
) -> list[dict[str, Any]]:
    """Enumerate all single-probe erasure ablations and record metrics."""
    full_samples = support_samples(geom, directions)
    ablations: list[dict[str, Any]] = []

    for th_omitted in directions:
        subset_samples = {th: h for th, h in full_samples.items() if th != th_omitted}
        reconstructed = reconstruct_from_support(subset_samples, initial_extent=initial_extent)
        metrics = reconstruction_metrics(geom, reconstructed)
        ablations.append({
            "omitted_direction": th_omitted,
            "metrics": metrics,
        })

    return ablations
