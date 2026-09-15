"""Unit tests for PCT baseline hierarchy, validity gates V0-V8, and scientific tests S1-S10."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from mapeogeo.pct.baselines import baseline_features, lowest_capable_baseline
from mapeogeo.pct.experiment import run_pct_experiment
from mapeogeo.pct.fixtures import build_control_corpus
from mapeogeo.pct.maps import check_chain_map, triangle_subdivision_map
from mapeogeo.pct.models import Verdict


def load_preregistration_manifest() -> dict:
    manifest_path = Path("evidence/v0_10_pct_preregistration.json")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


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

    # B5 includes map data
    b5_valid = baseline_features("B5", coarse, map_data=res_valid)
    b5_corrupt = baseline_features("B5", coarse, map_data=res_corrupt)
    assert b5_valid != b5_corrupt
    assert b5_valid[1][0] is True   # pass is True
    assert b5_corrupt[1][0] is False  # pass is False

    cap = {"B0": False, "B1": False, "B2": False, "B3": False, "B4": False, "B5": True}
    assert lowest_capable_baseline(cap) == "B5"


def test_full_experiment_orchestration():
    manifest = load_preregistration_manifest()
    result = run_pct_experiment(manifest, repository_commit="TEST_COMMIT_SHA")

    # Engine validity
    assert result["engine_validity"] == "PASS"

    # All required V0-V8 gates present and passing
    required_v = ["V0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]
    for v_id in required_v:
        assert v_id in result["validity_gates"]
        assert result["validity_gates"][v_id].verdict == Verdict.PASS

    # All S1-S10 tests present and passing
    required_s = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
    for s_id in required_s:
        assert s_id in result["scientific_tests"]
        assert result["scientific_tests"][s_id].verdict == Verdict.PASS

    # Scientific result
    assert result["scientific_result"] == "H1_SUPPORTED"


def test_corrupted_engine_fails_validity():
    manifest = load_preregistration_manifest()
    # If tolerances are impossibly strict (e.g. 0.0 for float buffer), gates catch it
    bad_manifest = dict(manifest)
    bad_manifest["tolerances"] = dict(manifest["tolerances"])
    bad_manifest["tolerances"]["reconstruction_hausdorff"] = 1e-25  # impossible for float

    result = run_pct_experiment(bad_manifest, repository_commit="TEST_COMMIT_SHA")
    # S4 should fail under 1e-25
    assert result["scientific_tests"]["S4"].verdict == Verdict.FAIL
