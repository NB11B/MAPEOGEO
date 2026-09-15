"""Unit tests for PCT chain maps and correspondence failure detection."""

from __future__ import annotations

from mapeogeo.pct.chain import betti_numbers, euler_from_homology
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.maps import (
    chain_map_residual,
    check_chain_map,
    triangle_subdivision_map,
)
from mapeogeo.pct.models import CoefficientField


def test_valid_subdivision_commutes_with_boundary():
    corpus = build_control_corpus()
    coarse = corpus["triangle_loop"].complex
    fine = corpus["triangle_loop_subdivided"].complex
    assert coarse is not None and fine is not None

    f = triangle_subdivision_map(corrupt=False)
    result = check_chain_map(coarse, fine, f)
    assert result["pass"] is True
    assert all(v == 0 for v in result["residual_nonzero_entries"].values())


def test_corrupted_map_is_detected_while_state_invariants_match():
    corpus = build_control_corpus()
    coarse = corpus["triangle_loop"].complex
    fine = corpus["triangle_loop_subdivided"].complex
    assert coarse is not None and fine is not None

    f_corrupt = triangle_subdivision_map(corrupt=True)
    result = check_chain_map(coarse, fine, f_corrupt)
    assert result["pass"] is False
    assert result["residual_nonzero_entries"][1] > 0

    # Ensure state-level invariants are identical
    assert betti_numbers(coarse, CoefficientField.Q) == betti_numbers(fine, CoefficientField.Q)
    assert euler_from_homology(coarse, CoefficientField.Q) == 0
    assert euler_from_homology(fine, CoefficientField.Q) == 0
