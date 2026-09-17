from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import KNOWLEDGE_BASELINE_SHA
from .identity import compute_harness_sha
from .main_adapter import classify_main_capabilities, invoke_main_pct


REPLAY_OPERATIONS: dict[str, dict[str, Any]] = {
    "E5_DIRECT_CHAIN_MAP_CORRUPTION": {"op": "chain_map_corruption"},
    "E9_APPLICABILITY_REFUSAL": {"op": "applicability_refusal"},
    "E14_PERSISTENCE_INFORMATION_LOSS": {"op": "persistence_information_loss"},
    "E17_EXACT_VS_FLOAT_RANK": {"op": "exact_rank_float_control", "n": 11},
}


def _evaluate(replay_id: str, result: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if replay_id == "E5_DIRECT_CHAIN_MAP_CORRUPTION":
        passed = result.get("valid_map_pass") is True and result.get("corrupt_map_pass") is False
        expected = {"valid_map_pass": True, "corrupt_map_pass": False}
    elif replay_id == "E9_APPLICABILITY_REFUSAL":
        passed = (
            result.get("reentrant_verdict") == "NOT_APPLICABLE"
            and result.get("square_verdict") == "PASS"
        )
        expected = {"reentrant_verdict": "NOT_APPLICABLE", "square_verdict": "PASS"}
    elif replay_id == "E14_PERSISTENCE_INFORMATION_LOSS":
        passed = (
            result.get("same_euler") is True
            and result.get("different_betti") is True
            and result.get("different_persistence") is True
        )
        expected = {
            "same_euler": True,
            "different_betti": True,
            "different_persistence": True,
        }
    elif replay_id == "E17_EXACT_VS_FLOAT_RANK":
        exact = result.get("exact_rank")
        floating = result.get("float_rank")
        passed = isinstance(exact, int) and isinstance(floating, int) and exact > floating
        expected = {"exact_rank_gt_float_rank": True, "n": 11}
    else:
        raise ValueError(f"No scored E30 evaluator for {replay_id}")
    return ("PASS" if passed else "FAIL"), expected


def run_e30(repo_root: Path, main_root: Path) -> dict[str, Any]:
    matrix = classify_main_capabilities(main_root)
    runtime = invoke_main_pct(repo_root, main_root, {"op": "runtime_identity"})

    replays: list[dict[str, Any]] = []
    for replay_id, classification in matrix.items():
        scored = classification in {"DIRECT_REPLAY", "ADAPTER_REQUIRED"}
        if scored:
            request = REPLAY_OPERATIONS[replay_id]
            result = invoke_main_pct(repo_root, main_root, request)
            verdict, expected = _evaluate(replay_id, result)
            replays.append(
                {
                    "replay_id": replay_id,
                    "classification": classification,
                    "scored": True,
                    "verdict": verdict,
                    "request": request,
                    "expected": expected,
                    "result": result,
                }
            )
        else:
            replays.append(
                {
                    "replay_id": replay_id,
                    "classification": classification,
                    "scored": False,
                    "verdict": "NOT_ESTABLISHED",
                    "reason": "FROZEN_MAIN_PCT_CAPABILITY_NOT_EXPOSED",
                    "result": None,
                }
            )

    scored_rows = [row for row in replays if row["scored"]]
    failed_rows = [row for row in scored_rows if row["verdict"] != "PASS"]
    coverage = {
        "total_replay_rows": len(replays),
        "scored": len(scored_rows),
        "direct_replay": sum(row["classification"] == "DIRECT_REPLAY" for row in replays),
        "adapter_required": sum(row["classification"] == "ADAPTER_REQUIRED" for row in replays),
        "capability_not_exposed": sum(
            row["classification"] == "CAPABILITY_NOT_EXPOSED" for row in replays
        ),
        "not_applicable": sum(row["classification"] == "NOT_APPLICABLE" for row in replays),
    }
    return {
        "experiment_id": "E30_MAIN_PCT_ADVERSARIAL_REPLAY",
        "status": "PASS" if not failed_rows else "FAIL",
        "knowledge_baseline_sha": KNOWLEDGE_BASELINE_SHA,
        "campaign_harness_sha": compute_harness_sha(repo_root),
        "runtime_identity": runtime,
        "capability_matrix": matrix,
        "coverage": coverage,
        "scored_replay_count": len(scored_rows),
        "failed_scored_replay_count": len(failed_rows),
        "replays": replays,
        "claim_boundary": (
            "CAPABILITY_NOT_EXPOSED_IS_A_COVERAGE_FINDING_NOT_A_NEGATIVE_SCIENTIFIC_RESULT"
        ),
    }
