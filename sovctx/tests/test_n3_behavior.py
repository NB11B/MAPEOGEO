from __future__ import annotations

import pytest

from sovctx.node.behavior import (
    BehaviorClass,
    BehaviorEvaluationResult,
    ConfusionMatrix,
)
from sovctx.node.behavior_corpus import (
    BEHAVIORAL_CORPUS,
    evaluate_behavior_case,
)
from sovctx.node.temporal import (
    InstitutionalGenealogyEvent,
    TemporalInterval,
    resolve_institutional_state,
    validate_genealogical_edge,
)
from sovctx.tools.qualify_n3 import run_n3_qualification


def test_behavior_classes() -> None:
    expected_classes = [
        "B0_ACQUIRE",
        "B1_RESOLVE",
        "B2_NOMINATE",
        "B3_LINK_CANDIDATE",
        "B4_QUARANTINE",
        "B5_DEFER_UNRESOLVED",
        "B6_REFUSE_PROMOTION",
        "B7_DEDUPLICATE",
        "B8_ROUTE_ENTITY",
        "B9_NO_ACTION",
    ]
    actual_classes = [c.value for c in BehaviorClass]
    assert len(actual_classes) == 10
    for ec in expected_classes:
        assert ec in actual_classes


def test_confusion_matrix_tracking() -> None:
    cm = ConfusionMatrix()
    res1 = BehaviorEvaluationResult(
        case_id="T1",
        family="CITATION",
        expected_behavior=BehaviorClass.B1_RESOLVE.value,
        actual_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="EXACT_MATCH",
        actual_state="EXACT_MATCH",
        is_correct=True,
        state_correct=True,
        forbidden_violations=[],
    )
    res2 = BehaviorEvaluationResult(
        case_id="T2",
        family="CITATION",
        expected_behavior=BehaviorClass.B5_DEFER_UNRESOLVED.value,
        actual_behavior=BehaviorClass.B1_RESOLVE.value,
        expected_state="UNRESOLVED",
        actual_state="EXACT_MATCH",
        is_correct=False,
        state_correct=False,
        forbidden_violations=["FORBIDDEN_TRANSITION:UNRESOLVED_TO_EXACT"],
    )
    cm.record(res1)
    cm.record(res2)
    s = cm.summary()
    assert s["total_cases"] == 2
    assert s["correct_cases"] == 1
    assert s["overall_accuracy"] == 0.5
    assert s["critical_violations_count"] == 1
    assert any(v["violation"] == "FORBIDDEN_TRANSITION:UNRESOLVED_TO_EXACT" for v in s["critical_violations"])


def test_temporal_intervals_and_genealogy() -> None:
    t_ussr = TemporalInterval(1925, 1991)
    assert t_ussr.contains_year(1943)
    assert not t_ussr.contains_year(1917)
    assert not t_ussr.contains_year(1995)

    event = InstitutionalGenealogyEvent(
        source_entity="АН СССР",
        target_entity="РАН",
        relation_type="RENAMED_TO",
        event_year=1991,
        valid_from=1925,
        valid_to=1991,
    )
    assert event.relation_type == "RENAMED_TO"
    assert event.event_year == 1991

    st = resolve_institutional_state("АН СССР", 1960)
    assert st["status"] == "GENEALOGY_RESOLVED"
    assert st["historical_active"] is True


def test_forbidden_same_as_collapse() -> None:
    # Attempting flat SAME_AS between distinct historical institutional epochs must be rejected
    is_valid, err = validate_genealogical_edge("RENAMED_TO")
    assert is_valid is True
    assert err is None

    is_valid, err = validate_genealogical_edge("SAME_AS")
    assert is_valid is False
    assert err is not None
    assert "Forbidden collapse relation 'SAME_AS'" in err

    is_valid, err = validate_genealogical_edge("SAME_CONCEPT")
    assert is_valid is False
    assert "Forbidden collapse relation 'SAME_CONCEPT'" in err


def test_counterfactual_pairs() -> None:
    pair_cases: dict[str, list] = {}
    for case in BEHAVIORAL_CORPUS:
        if case.is_counterfactual and case.counterfactual_pair_id:
            pair_cases.setdefault(case.counterfactual_pair_id, []).append(case)

    assert len(pair_cases) >= 6
    for pair_id, cases in pair_cases.items():
        assert len(cases) == 2, f"Pair {pair_id} should have exactly 2 cases"
        results = [evaluate_behavior_case(c) for c in cases]
        for r in results:
            assert r.is_correct, f"Case {r.case_id} failed in {pair_id}"
            assert r.state_correct, f"Case {r.case_id} state failed in {pair_id}"
            assert len(r.forbidden_violations) == 0, f"Case {r.case_id} had violations: {r.forbidden_violations}"


def test_behavior_corpus_families() -> None:
    families = set(c.family for c in BEHAVIORAL_CORPUS)
    assert len(families) == 6
    for fam in families:
        fam_cases = [c for c in BEHAVIORAL_CORPUS if c.family == fam]
        assert len(fam_cases) >= 10
        for case in fam_cases:
            res = evaluate_behavior_case(case)
            assert res.is_correct, f"Family {fam} case {case.case_id} failed behavior: expected {case.expected_behavior}, got {res.actual_behavior}"
            assert res.state_correct, f"Family {fam} case {case.case_id} failed state: expected {case.expected_state}, got {res.actual_state}"
            assert len(res.forbidden_violations) == 0, f"Family {fam} case {case.case_id} had violations: {res.forbidden_violations}"


def test_full_n3_qualification_harness() -> None:
    res = run_n3_qualification()
    assert res["verdict"] == "PASS"
    assert res["overall_accuracy"] >= 0.95
    assert res["critical_violations_count"] == 0
    assert all(res["counterfactual_pairs"].values())
