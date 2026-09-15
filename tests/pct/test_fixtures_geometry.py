"""Unit tests for the PCT control fixtures and initial geometry properties."""

from __future__ import annotations

import math
from mapeogeo.pct.chain import betti_numbers, check_chain_condition, euler_from_chains, euler_from_homology
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.models import Applicability, CoefficientField, EquivalenceContract


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


def test_scale_event_and_nonconvex_applicability():
    corpus = build_control_corpus()

    annulus = corpus["square_annulus"]
    assert annulus.is_convex is False
    assert annulus.applicability == Applicability.NOT_APPLICABLE

    sep_sq = corpus["two_separated_squares"]
    assert sep_sq.is_convex is False
    assert sep_sq.applicability == Applicability.NOT_APPLICABLE

    reentrant = corpus["reentrant_control"]
    assert reentrant.is_convex is False
    assert reentrant.applicability == Applicability.NOT_APPLICABLE
