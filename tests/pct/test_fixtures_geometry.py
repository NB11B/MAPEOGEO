"""Unit tests for PCT control fixtures, geometry properties, and scale events."""

from __future__ import annotations

import math
from mapeogeo.pct.chain import betti_numbers, check_chain_condition, euler_from_chains
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.geometry import (
    check_convex_steiner,
    euler_of_geometry,
    parallel_metrics,
    scan_topology_events,
)
from mapeogeo.pct.models import Applicability, CoefficientField, Verdict


REQUIRED = {
    "triangle_loop",
    "triangle_loop_subdivided",
    "two_loops",
    "filled_triangle",
    "equal_area_square",
    "equal_area_triangle",
    "square_annulus",
    "two_separated_squares",
    "reentrant_control",
}

SCALES = [0.0, 0.25, 0.5, 0.75, 0.99, 1.0, 1.01, 1.25]


def test_fixture_corpus_contains_all_required():
    corpus = build_control_corpus()
    assert REQUIRED.issubset(set(corpus.keys()))


def test_combinatorial_fixtures_satisfy_invariants():
    corpus = build_control_corpus()

    # triangle_loop
    t_loop = corpus["triangle_loop"]
    assert t_loop.complex is not None
    assert check_chain_condition(t_loop.complex)
    assert betti_numbers(t_loop.complex, CoefficientField.GF2) == {0: 1, 1: 1}
    assert betti_numbers(t_loop.complex, CoefficientField.Q) == {0: 1, 1: 1}
    assert euler_from_chains(t_loop.complex) == 0

    # two_loops
    two_l = corpus["two_loops"]
    assert two_l.complex is not None
    assert check_chain_condition(two_l.complex)
    assert betti_numbers(two_l.complex, CoefficientField.GF2) == {0: 2, 1: 2}
    assert betti_numbers(two_l.complex, CoefficientField.Q) == {0: 2, 1: 2}
    assert euler_from_chains(two_l.complex) == 0

    # triangle_loop_subdivided
    sub_l = corpus["triangle_loop_subdivided"]
    assert sub_l.complex is not None
    assert check_chain_condition(sub_l.complex)
    assert betti_numbers(sub_l.complex, CoefficientField.Q) == {0: 1, 1: 1}
    assert euler_from_chains(sub_l.complex) == 0

    # filled_triangle
    filled_t = corpus["filled_triangle"]
    assert filled_t.complex is not None
    assert check_chain_condition(filled_t.complex)
    assert betti_numbers(filled_t.complex, CoefficientField.Q) == {0: 1, 1: 0, 2: 0}
    assert euler_from_chains(filled_t.complex) == 1


def test_equal_area_geometries():
    corpus = build_control_corpus()

    sq = corpus["equal_area_square"]
    assert sq.geometry is not None
    assert abs(sq.geometry.area - math.pi) <= 1e-12
    assert sq.is_convex is True
    assert sq.applicability == Applicability.APPLICABLE

    tri = corpus["equal_area_triangle"]
    assert tri.geometry is not None
    assert abs(tri.geometry.area - math.pi) <= 1e-12
    assert tri.is_convex is True
    assert tri.applicability == Applicability.APPLICABLE


def test_euler_of_geometry():
    corpus = build_control_corpus()
    assert euler_of_geometry(corpus["square_annulus"].geometry) == 0
    assert euler_of_geometry(corpus["two_separated_squares"].geometry) == 2
    assert euler_of_geometry(corpus["equal_area_square"].geometry) == 1
    assert euler_of_geometry(corpus["equal_area_triangle"].geometry) == 1
    assert euler_of_geometry(corpus["reentrant_control"].geometry) == 1


def test_scale_events_annulus_and_separated_squares():
    corpus = build_control_corpus()

    # Annulus hole closes around 1.0 (between 0.99 and 1.01)
    annulus_events = scan_topology_events(corpus["square_annulus"].geometry, SCALES)
    assert len(annulus_events) == 1
    ev = annulus_events[0]
    assert ev["euler_before"] == 0
    assert ev["euler_after"] == 1
    assert abs(ev["event_scale_approx"] - 1.0) <= 0.011

    # Separated squares merge around 1.0 (between 0.99 and 1.01)
    sq_events = scan_topology_events(corpus["two_separated_squares"].geometry, SCALES)
    assert len(sq_events) == 1
    ev2 = sq_events[0]
    assert ev2["euler_before"] == 2
    assert ev2["euler_after"] == 1
    assert abs(ev2["event_scale_approx"] - 1.0) <= 0.011


def test_regular_tube_law_refuses_reentrant_control():
    corpus = build_control_corpus()
    reentrant = corpus["reentrant_control"]
    result = check_convex_steiner(reentrant.geometry, [0.1, 0.2], 1e-9, is_convex=reentrant.is_convex)
    assert result.verdict is Verdict.NOT_APPLICABLE
    assert result.applicability is Applicability.NOT_APPLICABLE


def test_convex_steiner_passes_for_convex_square():
    corpus = build_control_corpus()
    sq = corpus["equal_area_square"]
    result = check_convex_steiner(sq.geometry, [0.1, 0.2, 0.5], 1e-3, is_convex=sq.is_convex)
    assert result.verdict is Verdict.PASS
    assert result.applicability is Applicability.APPLICABLE
