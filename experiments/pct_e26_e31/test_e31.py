from __future__ import annotations

from pathlib import Path

import pytest

from experiments.pct_e25ij.receipts import canonical_sha256
from experiments.pct_e26_e31.corpus import load_knowledge_corpus
from experiments.pct_e26_e31.e27 import run_e27
from experiments.pct_e26_e31.e30 import run_e30
from experiments.pct_e26_e31.e31 import derive_e31_closure, run_e31


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"


@pytest.fixture(scope="module")
def e31_report():
    corpus = load_knowledge_corpus(FROZEN_MAIN, ROOT)
    e27 = run_e27(corpus, ROOT)
    e30 = run_e30(ROOT, FROZEN_MAIN)
    before = canonical_sha256(corpus.graph)
    report = run_e31(corpus, e27, e30, ROOT)
    after = canonical_sha256(corpus.graph)
    assert before == after
    return report


def test_every_scored_result_has_complete_immutable_receipt_chain(e31_report) -> None:
    assert e31_report["status"] == "PASS"
    assert e31_report["direction_a_component_count"] > 0
    assert e31_report["direction_b_component_count"] > 0

    receipts = e31_report["ledger"]["receipts"]
    for receipt in receipts:
        payload = {key: value for key, value in receipt.items() if key != "receipt_id"}
        assert receipt["receipt_id"] == canonical_sha256(payload)

    by_component: dict[str, set[str]] = {}
    for receipt in receipts:
        by_component.setdefault(receipt["component_id"], set()).add(receipt["role"])
    for component in e31_report["ledger"]["components"]:
        roles = by_component[component["component_id"]]
        assert {"C0_IDENTITY", "C1_ANSWER_BINDING", "C2_EXECUTABLE_RESULT", "C5A_EXACT_RESULT", "C5B_PROVENANCE_BINDING", "C5_ELIGIBILITY"} <= roles


def test_bindings_cover_baselines_harness_recipe_input_output_and_answer(e31_report) -> None:
    for component in e31_report["ledger"]["components"]:
        bindings = component["bindings"]
        assert len(bindings["solver_baseline_sha"]) == 40
        assert len(bindings["knowledge_baseline_sha"]) == 40
        for key in (
            "campaign_harness_sha",
            "solver_recipe_sha256",
            "input_sha256",
            "output_sha256",
            "answer_sha256",
            "artifact_sha256",
        ):
            assert len(bindings[key]) == 64
            int(bindings[key], 16)


def test_c3_c4_are_explicit_and_never_implicit_pass(e31_report) -> None:
    snapshot = e31_report["derived_closure"]
    allowed = {"PASS", "NOT_APPLICABLE", "NOT_ESTABLISHED"}
    for component in snapshot["components"]:
        for layer in ("C3", "C4"):
            assert component["closure"][layer]["state"] in allowed
            assert component["closure"][layer]["state"] != "PASS" or component["closure"][layer].get("receipt_id")


def test_lifecycle_binding_changes_stale_descendants_without_resurrection(e31_report) -> None:
    checks = e31_report["lifecycle_checks"]
    assert {"solver_baseline_change", "knowledge_baseline_change", "harness_change", "recipe_change", "artifact_change"} <= set(checks)
    for row in checks.values():
        assert row["affected_component_count"] > 0
        assert row["descendants_staled"] is True
        assert row["old_c5_reactivated"] is False


def test_closure_replay_is_deterministic(e31_report) -> None:
    first = derive_e31_closure(e31_report["ledger"])
    second = derive_e31_closure(e31_report["ledger"])
    assert first == second == e31_report["derived_closure"]
