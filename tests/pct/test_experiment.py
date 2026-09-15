"""Unit tests for PCT baseline hierarchy, validity gates, and scientific tests."""

from __future__ import annotations

from mapeogeo.pct.baselines import (
    baseline_features,
    lowest_capable_baseline,
)
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.maps import check_chain_map, triangle_subdivision_map


def test_s1_hierarchy_triangle_vs_two_loops():
    corpus = build_control_corpus()
    t_loop = corpus["triangle_loop"]
    two_l = corpus["two_loops"]

    # B0: both have Euler = 0 (collision)
    b0_t = baseline_features("B0", t_loop)
    b0_2 = baseline_features("B0", two_l)
    assert b0_t == 0 and b0_2 == 0
    can_separate_b0 = (b0_t != b0_2)
    assert can_separate_b0 is False

    # B1: (1, 1) vs (2, 2) (separated)
    b1_t = baseline_features("B1", t_loop)
    b1_2 = baseline_features("B1", two_l)
    assert b1_t == (1, 1)
    assert b1_2 == (2, 2)
    can_separate_b1 = (b1_t != b1_2)
    assert can_separate_b1 is True

    # Attribution must be B1, not B5
    cap = {"B0": False, "B1": True, "B2": True, "B3": True, "B4": True, "B5": True}
    assert lowest_capable_baseline(cap) == "B1"


def test_s3_hierarchy_correspondence_failure():
    corpus = build_control_corpus()
    coarse = corpus["triangle_loop"]
    fine = corpus["triangle_loop_subdivided"]
    assert coarse.complex is not None and fine.complex is not None

    map_valid = triangle_subdivision_map(corrupt=False)
    map_corrupt = triangle_subdivision_map(corrupt=True)

    res_valid = check_chain_map(coarse.complex, fine.complex, map_valid)
    res_corrupt = check_chain_map(coarse.complex, fine.complex, map_corrupt)

    # State features B0-B4 are identical for source and target states
    for b in ["B0", "B1", "B4"]:
        f_coarse = baseline_features(b, coarse)
        f_fine = baseline_features(b, fine)
        # In both valid and corrupted cases, the source state is coarse and target is fine
        # B0-B4 have no access to the map edge / residual, so they cannot detect the map corruption

    # B5 includes map data
    b5_valid = baseline_features("B5", coarse, map_data=res_valid)
    b5_corrupt = baseline_features("B5", coarse, map_data=res_corrupt)
    assert b5_valid != b5_corrupt
    assert b5_valid[1][0] is True   # pass is True
    assert b5_corrupt[1][0] is False  # pass is False

    cap = {"B0": False, "B1": False, "B2": False, "B3": False, "B4": False, "B5": True}
    assert lowest_capable_baseline(cap) == "B5"
