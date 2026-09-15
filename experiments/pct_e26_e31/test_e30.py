from __future__ import annotations

from pathlib import Path

from experiments.pct_e26_e31.constants import KNOWLEDGE_BASELINE_SHA
from experiments.pct_e26_e31.e30 import run_e30
from experiments.pct_e26_e31.main_adapter import (
    classify_main_capabilities,
    invoke_main_pct,
)


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"


def test_main_invocation_is_frozen_and_isolated() -> None:
    out = invoke_main_pct(ROOT, FROZEN_MAIN, {"op": "runtime_identity"})
    assert out["checkout_sha"] == KNOWLEDGE_BASELINE_SHA
    assert out["experimental_branch_on_sys_path"] is False
    assert str(FROZEN_MAIN.resolve()) in out["pct_module_path"]


def test_capability_matrix_is_preclassified_without_adapter_overreach() -> None:
    matrix = classify_main_capabilities(FROZEN_MAIN)
    assert matrix["E5_DIRECT_CHAIN_MAP_CORRUPTION"] == "DIRECT_REPLAY"
    assert matrix["E9_APPLICABILITY_REFUSAL"] == "DIRECT_REPLAY"
    assert matrix["E14_PERSISTENCE_INFORMATION_LOSS"] == "DIRECT_REPLAY"
    assert matrix["E17_EXACT_VS_FLOAT_RANK"] == "ADAPTER_REQUIRED"
    assert matrix["E16_CROSS_VIEW_CORRESPONDENCE"] == "CAPABILITY_NOT_EXPOSED"
    assert matrix["E23_GENERIC_COUNTEREXAMPLE_SEARCH"] == "CAPABILITY_NOT_EXPOSED"


def test_unexposed_capability_is_not_scored_failure() -> None:
    report = run_e30(ROOT, FROZEN_MAIN)
    assert report["status"] == "PASS"
    assert report["scored_replay_count"] > 0
    for row in report["replays"]:
        if row["classification"] in {"CAPABILITY_NOT_EXPOSED", "NOT_APPLICABLE"}:
            assert row["scored"] is False
            assert row["verdict"] not in {"FAIL", "ERROR"}


def test_scored_replays_use_main_operations_and_pass_expected_controls() -> None:
    report = run_e30(ROOT, FROZEN_MAIN)
    scored = [row for row in report["replays"] if row["scored"]]
    assert scored
    assert all(row["verdict"] == "PASS" for row in scored)

    by_id = {row["replay_id"]: row for row in scored}
    assert by_id["E5_DIRECT_CHAIN_MAP_CORRUPTION"]["result"]["valid_map_pass"] is True
    assert by_id["E5_DIRECT_CHAIN_MAP_CORRUPTION"]["result"]["corrupt_map_pass"] is False
    assert by_id["E9_APPLICABILITY_REFUSAL"]["result"]["reentrant_verdict"] == "NOT_APPLICABLE"
    assert by_id["E14_PERSISTENCE_INFORMATION_LOSS"]["result"]["same_euler"] is True
    assert by_id["E14_PERSISTENCE_INFORMATION_LOSS"]["result"]["different_betti"] is True
    assert by_id["E17_EXACT_VS_FLOAT_RANK"]["result"]["exact_rank"] > by_id["E17_EXACT_VS_FLOAT_RANK"]["result"]["float_rank"]
