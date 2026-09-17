from __future__ import annotations

from pathlib import Path

from experiments.pct_e26_e31.cases import build_r1_cases, sanitize_case
from experiments.pct_e26_e31.corpus import load_knowledge_corpus
from experiments.pct_e26_e31.solver import solve_case


ROOT = Path(__file__).resolve().parents[2]
FROZEN_MAIN = ROOT / ".crossbranch" / "frozen-main"


def _corpus():
    return load_knowledge_corpus(FROZEN_MAIN, ROOT)


def test_r1_population_is_source_declaration_cross_source_only() -> None:
    corpus = _corpus()
    cases = build_r1_cases(corpus)
    assert cases
    for case in cases:
        source = corpus.node_by_id[case.source_id]
        target = corpus.node_by_id[case.target_id]
        assert source["type"] == "SOURCE_DECLARATION"
        assert target["type"] == "SOURCE_DECLARATION"
        assert source["attributes"]["source_id"] != target["attributes"]["source_id"]


def test_sanitized_case_removes_direct_target_answer_and_status_leakage() -> None:
    corpus = _corpus()
    case = build_r1_cases(corpus)[0]
    sanitized = sanitize_case(corpus, case)
    assert case.edge_id not in sanitized.visible_edge_ids
    assert sanitized.direct_target_labels == ()

    for edge in sanitized.visible_graph["edges"]:
        if edge.get("type") != "REPRESENTS":
            continue
        if edge.get("source") in {case.source_id, case.target_id}:
            assert "cross_source_status" not in edge.get("attributes", {})


def test_solver_refuses_when_probe_bank_is_erased() -> None:
    corpus = _corpus()
    case = sanitize_case(corpus, build_r1_cases(corpus)[0])
    result = solve_case(case, probe_keys=())
    assert result.verdict == "NOT_ESTABLISHED"
    assert set(result.ambiguity_set) == {
        "SAME_SEMANTICS",
        "SCOPED_OVERLAP",
        "RELATED_TO",
    }


def test_solver_is_deterministic_for_same_sanitized_case() -> None:
    corpus = _corpus()
    case = sanitize_case(corpus, build_r1_cases(corpus)[0])
    assert solve_case(case) == solve_case(case)
