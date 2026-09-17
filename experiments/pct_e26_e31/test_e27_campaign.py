from __future__ import annotations

from pathlib import Path

from experiments.pct_e26_e31.cases import sanitize_case
from experiments.pct_e26_e31.corpus import load_knowledge_corpus
from experiments.pct_e26_e31.e27 import (
    build_r2_cluster_cases,
    build_r3_domain_cases,
    evaluate_solver_signal,
    run_e27,
)


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"


def _corpus():
    return load_knowledge_corpus(FROZEN_MAIN, ROOT)


def test_r2_holdout_group_is_verifier_only_and_hides_cluster_answers() -> None:
    corpus = _corpus()
    cases = build_r2_cluster_cases(corpus)
    assert cases
    case = cases[0]
    sanitized = sanitize_case(corpus, case)
    assert "canonical_holdout_group" not in sanitized.metadata
    assert case.edge_id in case.hidden_edge_ids
    assert len(case.hidden_edge_ids) >= 1


def test_r3_domain_holdout_hides_more_than_target_when_domain_has_redundancy() -> None:
    corpus = _corpus()
    cases = build_r3_domain_cases(corpus)
    assert cases
    redundant = [case for case in cases if len(case.hidden_edge_ids) > 1]
    assert redundant
    sanitized = sanitize_case(corpus, redundant[0])
    assert "domain_holdout_group" not in sanitized.metadata
    assert redundant[0].edge_id not in sanitized.visible_edge_ids


def test_r4_corruption_controls_have_zero_false_certainty() -> None:
    corpus = _corpus()
    report = run_e27(corpus, ROOT)
    assert report["R4"]["total"] > 0
    assert report["R4"]["false_certainty_count"] == 0


def test_e27_metrics_and_solver_signal_are_deterministic() -> None:
    corpus = _corpus()
    first = run_e27(corpus, ROOT)
    second = run_e27(corpus, ROOT)
    assert first == second
    signal = evaluate_solver_signal(first)
    assert set(signal) >= {
        "r4_zero_false_certainty",
        "r2_b4_strictly_exceeds_simpler",
        "r3_b4_strictly_exceeds_simpler",
        "coverage_gain_without_wrong_positive_increase",
        "positive_traces_reproducible",
        "h1_supported",
    }
    assert isinstance(signal["h1_supported"], bool)
