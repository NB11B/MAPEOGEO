"""Unit tests for deterministic convex polygon reconstruction and probe ablations."""

from __future__ import annotations

import math
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.probes import support_samples
from mapeogeo.pct.reconstruction import (
    one_probe_ablations,
    reconstruct_from_support,
    reconstruction_metrics,
)


DIRECTIONS = [k * math.pi / 6.0 for k in range(12)]


def test_equal_area_square_reconstruction():
    corpus = build_control_corpus()
    sq = corpus["equal_area_square"].geometry
    assert sq is not None

    samples = support_samples(sq, DIRECTIONS)
    reconstructed = reconstruct_from_support(samples)
    metrics = reconstruction_metrics(sq, reconstructed)

    assert metrics["hausdorff"] <= 1e-9, f"Hausdorff: {metrics['hausdorff']}"
    assert abs(metrics["area_error"]) <= 1e-9, f"Area error: {metrics['area_error']}"
    assert metrics["euler_match"] is True


def test_equal_area_triangle_reconstruction():
    corpus = build_control_corpus()
    tri = corpus["equal_area_triangle"].geometry
    assert tri is not None

    samples = support_samples(tri, DIRECTIONS)
    reconstructed = reconstruct_from_support(samples)
    metrics = reconstruction_metrics(tri, reconstructed)

    assert metrics["hausdorff"] <= 1e-9, f"Hausdorff: {metrics['hausdorff']}"
    assert abs(metrics["area_error"]) <= 1e-9, f"Area error: {metrics['area_error']}"
    assert metrics["euler_match"] is True


def test_one_probe_ablations_enumeration():
    corpus = build_control_corpus()
    sq = corpus["equal_area_square"].geometry
    assert sq is not None

    ablations = one_probe_ablations(sq, DIRECTIONS)
    assert len(ablations) == len(DIRECTIONS)
    assert all("omitted_direction" in ab for ab in ablations)
    assert all("metrics" in ab for ab in ablations)
