"""Planar geometry, Euler-of-geometry calculations, and scale-event scans."""

from __future__ import annotations

import math
from typing import Any
from shapely.geometry import (
    GeometryCollection,
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from mapeogeo.pct.contracts import make_verdict, require_applicable
from mapeogeo.pct.models import Applicability, Verdict, VerdictRecord


def buffer_compat(geom: Any, distance: float, quad_segs: int = 64) -> Any:
    """Helper for geometry buffer using quad_segs without deprecated warnings."""
    if distance == 0.0:
        return geom
    try:
        return geom.buffer(distance, quad_segs=quad_segs)
    except TypeError:
        return geom.buffer(distance, resolution=quad_segs)


def component_hole_counts(geom: Any) -> tuple[int, int]:
    """Compute (connected_components, interior_holes) for Shapely planar geometry."""
    if geom is None or geom.is_empty:
        return (0, 0)

    if isinstance(geom, Polygon):
        return (1, len(geom.interiors))
    elif isinstance(geom, MultiPolygon):
        n_comp = len(geom.geoms)
        n_holes = sum(len(p.interiors) for p in geom.geoms)
        return (n_comp, n_holes)
    elif isinstance(geom, (LineString, LinearRing, Point)):
        return (1, 0)
    elif isinstance(geom, (MultiLineString, MultiPoint)):
        return (len(geom.geoms), 0)
    elif isinstance(geom, GeometryCollection):
        n_comp = 0
        n_holes = 0
        for g in geom.geoms:
            c, h = component_hole_counts(g)
            n_comp += c
            n_holes += h
        return (n_comp, n_holes)
    else:
        # Fallback for other geometry types
        return (1 if not geom.is_empty else 0, 0)


def euler_of_geometry(geom: Any) -> int:
    """Compute Euler characteristic of planar geometry chi = components - holes."""
    if geom is None or geom.is_empty:
        return 0
    if isinstance(geom, LinearRing):
        return 0
    comp, holes = component_hole_counts(geom)
    return comp - holes


def parallel_metrics(geom: Any, scales: list[float]) -> list[dict[str, Any]]:
    """Compute area, perimeter, and Euler characteristic across scale buffer schedule."""
    records: list[dict[str, Any]] = []
    for s in scales:
        buffered = buffer_compat(geom, s, quad_segs=64)
        comp, holes = component_hole_counts(buffered)
        chi = euler_of_geometry(buffered)
        records.append({
            "scale": s,
            "area": float(buffered.area),
            "perimeter": float(buffered.length),
            "components": comp,
            "holes": holes,
            "euler": chi,
        })
    return records


def check_convex_steiner(
    geom: Any,
    scales: list[float],
    tol: float = 1e-4,
    is_convex: bool = True,
) -> VerdictRecord:
    """Verify Steiner formula A(s) = A0 + P0*s + pi*s^2 for convex planar domains."""
    if not is_convex:
        return require_applicable(
            check_id="convex_steiner_formula",
            is_applicable=False,
            provenance={"reason": "NON_CONVEX_GEOMETRY_INAPPLICABLE"},
        )

    if geom is None or geom.is_empty:
        return require_applicable(
            check_id="convex_steiner_formula",
            is_applicable=False,
            provenance={"reason": "EMPTY_GEOMETRY"},
        )

    a0 = float(geom.area)
    p0 = float(geom.length)

    max_err = 0.0
    for s in scales:
        buffered = buffer_compat(geom, s, quad_segs=256)
        a_meas = float(buffered.area)
        a_exp = a0 + p0 * s + math.pi * (s ** 2)
        err = abs(a_meas - a_exp)
        if err > max_err:
            max_err = err

    verdict = Verdict.PASS if max_err <= tol else Verdict.FAIL
    return make_verdict(
        check_id="convex_steiner_formula",
        applicability=Applicability.APPLICABLE,
        verdict=verdict,
        measured=max_err,
        expected=0.0,
        tolerance_or_exact_rule=f"ERROR_LE_{tol}",
        provenance={"a0": a0, "p0": p0, "max_error": max_err, "scales": scales},
    )


def scan_topology_events(geom: Any, scales: list[float]) -> list[dict[str, Any]]:
    """Scan for Euler characteristic transition events across an ordered scale schedule."""
    sorted_scales = sorted(scales)
    events: list[dict[str, Any]] = []

    last_scale = sorted_scales[0]
    last_geom = buffer_compat(geom, last_scale, quad_segs=64)
    last_euler = euler_of_geometry(last_geom)

    for s in sorted_scales[1:]:
        buf = buffer_compat(geom, s, quad_segs=64)
        cur_euler = euler_of_geometry(buf)
        if cur_euler != last_euler:
            events.append({
                "scale_before": last_scale,
                "scale_after": s,
                "euler_before": last_euler,
                "euler_after": cur_euler,
                "event_scale_approx": (last_scale + s) / 2.0,
            })
        last_scale = s
        last_euler = cur_euler

    return events
