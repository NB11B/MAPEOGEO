"""Unit tests for PCT parameterized probes and response consistency."""

from __future__ import annotations

import math
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.probes import (
    line_euler_response,
    line_response_field,
    support_samples,
    validate_convex_line_response,
)


DIRECTIONS = [k * math.pi / 6.0 for k in range(12)]
OFFSETS = [x / 4.0 for x in range(-16, 17)]
EXTENT = 10.0


def test_convex_fixtures_have_contiguous_line_responses():
    corpus = build_control_corpus()
    for fix_id in ["equal_area_square", "equal_area_triangle"]:
        geom = corpus[fix_id].geometry
        assert geom is not None
        field_data = line_response_field(geom, DIRECTIONS, OFFSETS, EXTENT)
        val = validate_convex_line_response(field_data)
        assert val["valid"] is True, f"Failed for {fix_id}: {val['failing_directions']}"


def test_square_annulus_hole_response_equals_two():
    corpus = build_control_corpus()
    annulus = corpus["square_annulus"].geometry
    assert annulus is not None

    # Line through origin horizontally (theta = pi/2, normal along y => horizontal line along x at y=0)
    # or theta = 0, normal along x => vertical line along y at x=0
    resp_h = line_euler_response(annulus, theta=math.pi / 2.0, offset=0.0, extent=EXTENT)
    assert resp_h == 2

    resp_v = line_euler_response(annulus, theta=0.0, offset=0.0, extent=EXTENT)
    assert resp_v == 2


def test_corrupted_response_is_detected_and_localized():
    corpus = build_control_corpus()
    sq = corpus["equal_area_square"].geometry
    assert sq is not None

    field_data = line_response_field(sq, DIRECTIONS, OFFSETS, EXTENT)
    assert validate_convex_line_response(field_data)["valid"] is True

    # Corrupt one direction: DIRECTIONS[2]
    target_dir = DIRECTIONS[2]
    row = list(field_data["responses"][target_dir])

    # Find the middle of the nonzero segment and flip 1 to 0
    nonzeros = [i for i, v in enumerate(row) if v > 0]
    assert len(nonzeros) >= 3
    mid_idx = nonzeros[len(nonzeros) // 2]
    row[mid_idx] = 0

    corrupted_field = {
        "directions": field_data["directions"],
        "offsets": field_data["offsets"],
        "responses": dict(field_data["responses"]),
    }
    corrupted_field["responses"][target_dir] = row

    val = validate_convex_line_response(corrupted_field)
    assert val["valid"] is False
    assert val["failing_directions"] == [target_dir]


def test_support_samples_are_bounded_and_consistent():
    corpus = build_control_corpus()
    sq = corpus["equal_area_square"].geometry
    assert sq is not None

    samples = support_samples(sq, DIRECTIONS)
    assert len(samples) == len(DIRECTIONS)
    # For square with side s = sqrt(pi) centered at origin, max support along axis is s/2
    s_half = math.sqrt(math.pi) / 2.0
    assert abs(samples[0.0] - s_half) <= 1e-12
