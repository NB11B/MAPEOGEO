"""Analytic and adversarial 2-D control corpus for PCT."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any
from shapely.geometry import Polygon, MultiPolygon, box

from mapeogeo.pct.models import (
    Applicability,
    EquivalenceContract,
    FiniteComplex,
    Simplex,
)


@dataclass(frozen=True)
class ControlFixture:
    fixture_id: str
    complex: FiniteComplex | None = None
    geometry: Any | None = None
    expected_betti: dict[int, int] | None = None
    expected_euler: int | None = None
    expected_area: float | None = None
    expected_perimeter: float | None = None
    equivalence_contract: EquivalenceContract = EquivalenceContract.EXACT
    applicability: Applicability = Applicability.APPLICABLE
    is_convex: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


def triangle_loop_complex() -> FiniteComplex:
    simplices = (
        Simplex((0,)),
        Simplex((1,)),
        Simplex((2,)),
        Simplex((0, 1)),
        Simplex((1, 2)),
        Simplex((0, 2)),
    )
    return FiniteComplex(complex_id="triangle_loop", simplices=simplices)


def triangle_loop_subdivided_complex() -> FiniteComplex:
    """Subdivided triangle loop with 6 vertices and 6 edges."""
    simplices = (
        Simplex((0,)),
        Simplex((1,)),
        Simplex((2,)),
        Simplex((3,)),
        Simplex((4,)),
        Simplex((5,)),
        Simplex((0, 1)),
        Simplex((1, 2)),
        Simplex((2, 3)),
        Simplex((3, 4)),
        Simplex((4, 5)),
        Simplex((0, 5)),
    )
    return FiniteComplex(complex_id="triangle_loop_subdivided", simplices=simplices)


def two_loops_complex() -> FiniteComplex:
    """Disjoint union of two triangle loops."""
    simplices = (
        Simplex((0,)),
        Simplex((1,)),
        Simplex((2,)),
        Simplex((0, 1)),
        Simplex((1, 2)),
        Simplex((0, 2)),
        Simplex((3,)),
        Simplex((4,)),
        Simplex((5,)),
        Simplex((3, 4)),
        Simplex((4, 5)),
        Simplex((3, 5)),
    )
    return FiniteComplex(complex_id="two_loops", simplices=simplices)


def filled_triangle_complex() -> FiniteComplex:
    simplices = (
        Simplex((0,)),
        Simplex((1,)),
        Simplex((2,)),
        Simplex((0, 1)),
        Simplex((1, 2)),
        Simplex((0, 2)),
        Simplex((0, 1, 2)),
    )
    return FiniteComplex(complex_id="filled_triangle", simplices=simplices)


def build_control_corpus() -> dict[str, ControlFixture]:
    """Construct and return the full dictionary of 9 control fixtures."""
    corpus: dict[str, ControlFixture] = {}

    # 1. triangle_loop
    corpus["triangle_loop"] = ControlFixture(
        fixture_id="triangle_loop",
        complex=triangle_loop_complex(),
        expected_betti={0: 1, 1: 1},
        expected_euler=0,
        is_convex=False,
    )

    # 2. triangle_loop_subdivided
    corpus["triangle_loop_subdivided"] = ControlFixture(
        fixture_id="triangle_loop_subdivided",
        complex=triangle_loop_subdivided_complex(),
        expected_betti={0: 1, 1: 1},
        expected_euler=0,
        equivalence_contract=EquivalenceContract.SUBDIVISION,
        is_convex=False,
    )

    # 3. two_loops
    corpus["two_loops"] = ControlFixture(
        fixture_id="two_loops",
        complex=two_loops_complex(),
        expected_betti={0: 2, 1: 2},
        expected_euler=0,
        is_convex=False,
    )

    # 4. filled_triangle
    corpus["filled_triangle"] = ControlFixture(
        fixture_id="filled_triangle",
        complex=filled_triangle_complex(),
        expected_betti={0: 1, 1: 0, 2: 0},
        expected_euler=1,
        is_convex=True,
    )

    # 5. equal_area_square (Area = pi, side = sqrt(pi))
    side_sq = math.sqrt(math.pi)
    sq_poly = box(-side_sq / 2, -side_sq / 2, side_sq / 2, side_sq / 2)
    corpus["equal_area_square"] = ControlFixture(
        fixture_id="equal_area_square",
        geometry=sq_poly,
        expected_euler=1,
        expected_area=math.pi,
        expected_perimeter=4.0 * side_sq,
        is_convex=True,
        applicability=Applicability.APPLICABLE,
    )

    # 6. equal_area_triangle (Area = pi, equilateral, centered)
    # Area = (sqrt(3)/4)*a^2 = pi  => a = sqrt(4*pi / sqrt(3))
    a_tri = math.sqrt(4.0 * math.pi / math.sqrt(3.0))
    h_tri = math.sqrt(3.0) / 2.0 * a_tri
    tri_poly = Polygon([
        (0.0, 2.0 * h_tri / 3.0),
        (-a_tri / 2.0, -h_tri / 3.0),
        (a_tri / 2.0, -h_tri / 3.0),
    ])
    corpus["equal_area_triangle"] = ControlFixture(
        fixture_id="equal_area_triangle",
        geometry=tri_poly,
        expected_euler=1,
        expected_area=math.pi,
        expected_perimeter=3.0 * a_tri,
        is_convex=True,
        applicability=Applicability.APPLICABLE,
    )

    # 7. square_annulus
    outer_box = box(-3.0, -3.0, 3.0, 3.0)
    inner_box = box(-1.0, -1.0, 1.0, 1.0)
    annulus_poly = outer_box.difference(inner_box)
    corpus["square_annulus"] = ControlFixture(
        fixture_id="square_annulus",
        geometry=annulus_poly,
        expected_euler=0,
        expected_area=outer_box.area - inner_box.area,
        is_convex=False,
        applicability=Applicability.NOT_APPLICABLE,  # Not applicable to convex Steiner
    )

    # 8. two_separated_squares
    sq1 = box(-2.0, -1.0, -1.0, 1.0)
    sq2 = box(1.0, -1.0, 2.0, 1.0)
    sep_squares = sq1.union(sq2)
    corpus["two_separated_squares"] = ControlFixture(
        fixture_id="two_separated_squares",
        geometry=sep_squares,
        expected_euler=2,
        expected_area=sq1.area + sq2.area,
        is_convex=False,
        applicability=Applicability.NOT_APPLICABLE,
    )

    # 9. reentrant_control (L-shaped polygon)
    reentrant_poly = Polygon([
        (-2.0, -2.0),
        (2.0, -2.0),
        (2.0, 0.0),
        (0.0, 0.0),
        (0.0, 2.0),
        (-2.0, 2.0),
    ])
    corpus["reentrant_control"] = ControlFixture(
        fixture_id="reentrant_control",
        geometry=reentrant_poly,
        expected_euler=1,
        expected_area=reentrant_poly.area,
        is_convex=False,
        applicability=Applicability.NOT_APPLICABLE,
    )

    return corpus
