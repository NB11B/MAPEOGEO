from __future__ import annotations

from pathlib import Path

from experiments.pct_e26_e31.corpus import load_knowledge_corpus
from experiments.pct_e26_e31.e27 import run_e27
from experiments.pct_e26_e31.e29 import (
    CandidateRule,
    TrainingRow,
    enumerate_candidate_rules,
    falsify_rule,
    run_e29,
)


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"


def _row(edge: str, canonical: str, relation: str, flag: str, extra: int = 1) -> TrainingRow:
    return TrainingRow(
        edge_id=edge,
        canonical_id=canonical,
        relation=relation,
        probes=(("flag", flag), ("extra", extra)),
    )


def test_rule_requires_three_edges_and_two_canonical_objects() -> None:
    rows = [
        _row("e1", "c1", "SAME_SEMANTICS", "x"),
        _row("e2", "c1", "SAME_SEMANTICS", "x"),
        _row("e3", "c2", "SAME_SEMANTICS", "x"),
        _row("e4", "c3", "SCOPED_OVERLAP", "y"),
    ]
    rules = enumerate_candidate_rules(
        rows,
        max_width=2,
        min_support_edges=3,
        min_canonical_objects=2,
        probe_keys=("flag", "extra"),
    )
    assert rules
    assert all(rule.support_edge_count >= 3 for rule in rules)
    assert all(rule.support_canonical_count >= 2 for rule in rules)


def test_one_counterexample_defeats_universal_rule() -> None:
    rule = CandidateRule(
        rule_id="rule:test",
        antecedents=(("flag", "x"),),
        consequent="SAME_SEMANTICS",
        support_edge_count=3,
        support_canonical_count=2,
        support_edge_ids=("e1", "e2", "e3"),
        support_canonical_ids=("c1", "c2"),
    )
    rows = [
        _row("e1", "c1", "SAME_SEMANTICS", "x"),
        _row("e2", "c1", "SAME_SEMANTICS", "x"),
        _row("e3", "c2", "SAME_SEMANTICS", "x"),
        _row("e4", "c3", "SCOPED_OVERLAP", "x"),
    ]
    audit = falsify_rule(rule, rows)
    assert audit.status == "DEFEATED_BY_COUNTEREXAMPLE"
    assert audit.counterexample_edge_ids == ("e4",)


def test_surviving_rule_is_candidate_not_theorem() -> None:
    rule = CandidateRule(
        rule_id="rule:survivor",
        antecedents=(("flag", "x"),),
        consequent="SAME_SEMANTICS",
        support_edge_count=3,
        support_canonical_count=2,
        support_edge_ids=("e1", "e2", "e3"),
        support_canonical_ids=("c1", "c2"),
    )
    audit = falsify_rule(
        rule,
        [
            _row("e1", "c1", "SAME_SEMANTICS", "x"),
            _row("e2", "c1", "SAME_SEMANTICS", "x"),
            _row("e3", "c2", "SAME_SEMANTICS", "x"),
        ],
    )
    assert audit.status == "CANDIDATE_SURVIVED_VISIBLE_SEARCH"
    assert audit.theorem_status is False


def test_e29_actual_corpus_run_is_deterministic_and_fail_closed() -> None:
    corpus = load_knowledge_corpus(FROZEN_MAIN, ROOT)
    e27 = run_e27(corpus, ROOT)
    first = run_e29(corpus, e27, ROOT)
    second = run_e29(corpus, e27, ROOT)
    assert first == second
    assert first["status"] == "PASS"
    assert first["candidate_rules_generated"] >= first["rules_survived_visible_search"]
    assert all(row["theorem_status"] is False for row in first["surviving_rules"])
