from __future__ import annotations

from fractions import Fraction
import sympy as sp

from experiments.pct_goal_solver.planner import solve
from experiments.pct_goal_solver.v0_20_goals import (
    ALL_V0_20_FAMILIES,
    FOUNDATIONAL_FAMILIES,
    COMPLEX_FAMILIES,
    CROSS_CLASS_FAMILIES,
    build_v0_20_corpus,
    prove_no_same_class_shortcut,
)
from experiments.pct_goal_solver.v0_20_macros import (
    CertifiedMacroSpec,
    synthesize_certified_macros,
    evaluate_macro_safety_and_efficiency,
)
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry


def test_v0_20_corpus_covers_all_19_families_and_split_integrity():
    corpus = build_v0_20_corpus()
    assert set(corpus.keys()) == {"CALIBRATION_V0_20", "VALIDATION_V0_20", "SEALED_V0_20"}
    
    # 19 families: 12 historical + 3 foundational + 2 complex + 2 cross-class
    assert len(ALL_V0_20_FAMILIES) == 19
    
    for split, count in (("CALIBRATION_V0_20", 3), ("VALIDATION_V0_20", 1), ("SEALED_V0_20", 2)):
        goals = corpus[split]
        assert len(goals) == 19 * count
        families_in_split = {g.family for g in goals}
        assert families_in_split == set(ALL_V0_20_FAMILIES)
        # Check uniqueness of goal IDs
        assert len({g.goal_id for g in goals}) == len(goals)


def test_v0_20_operator_registry_contains_foundational_and_cross_class_operators():
    registry = build_v0_20_operator_registry()
    required_ops = {
        "DEDEKIND_CUT_BOUND",
        "DIFFERENCE_QUOTIENT_BRACKET",
        "BEZOUT_IDENTITY_GCD",
        "CAUCHY_RIEMANN_RESIDUAL",
        "MEROMORPHIC_RESIDUE_SYMBOLIC",
        "EXACT_TO_SYMBOLIC_POLYNOMIAL",
        "EXACT_LATTICE_TO_SYMBOLIC_CURVE",
        "SYMBOLIC_TO_NUMERICAL_EVALUATION",
        "SYMBOLIC_CURVE_TO_NUMERICAL_PERIODS",
        "NUMERICAL_RESIDUAL_CERTIFY",
        "NUMERICAL_PERIOD_RESIDUAL_CERTIFY",
    }
    assert required_ops <= set(registry.keys())


def test_cross_class_goals_have_no_same_class_shortcut():
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    sealed_goals = corpus["SEALED_V0_20"]
    
    cross_class_sealed = [g for g in sealed_goals if g.family in CROSS_CLASS_FAMILIES]
    assert len(cross_class_sealed) == 4  # 2 families * 2 count
    
    for goal in cross_class_sealed:
        proof = prove_no_same_class_shortcut(goal, registry)
        assert proof["is_cross_class"] is True
        assert proof["proven_no_shortcut"] is True
        assert len(proof["required_derived_types"]) >= 2
        assert proof["has_same_class_direct_input"] is False


def test_foundational_elementary_math_goals_solve_explicitly():
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    calib = corpus["CALIBRATION_V0_20"]
    
    for fam in FOUNDATIONAL_FAMILIES:
        fam_goals = [g for g in calib if g.family == fam]
        assert len(fam_goals) == 3
        for goal in fam_goals:
            trace = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
            assert trace.final_verdict == "PASS"
            assert trace.verifier_chain[-1].passed is True


def test_complex_analysis_goals_solve_explicitly():
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    calib = corpus["CALIBRATION_V0_20"]
    
    for fam in COMPLEX_FAMILIES:
        fam_goals = [g for g in calib if g.family == fam]
        assert len(fam_goals) == 3
        for goal in fam_goals:
            trace = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
            assert trace.final_verdict == "PASS"
            assert trace.verifier_chain[-1].passed is True


def test_cross_class_multi_stage_goals_solve_explicitly():
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    calib = corpus["CALIBRATION_V0_20"]
    
    for fam in CROSS_CLASS_FAMILIES:
        fam_goals = [g for g in calib if g.family == fam]
        assert len(fam_goals) == 3
        for goal in fam_goals:
            trace = solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
            assert trace.final_verdict == "PASS"
            assert trace.verifier_chain[-1].passed is True
            # Verify multi-step path
            assert len(trace.operator_path) >= 3


def test_certified_macros_require_primitive_witness_traces():
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    calib = corpus["CALIBRATION_V0_20"]
    
    traces = [solve(g.solver_visible(), registry, typing_mode="EXPLICIT") for g in calib]
    macros = synthesize_certified_macros(calib, traces, registry, min_distinct_goals=2)
    
    assert len(macros) > 0
    for macro in macros:
        assert isinstance(macro, CertifiedMacroSpec)
        assert len(macro.witness_goal_ids) >= 2
        assert len(macro.witness_trace_digests) >= 2
        for digest in macro.witness_trace_digests:
            assert len(digest) == 64


def test_anti_macro_rescue_detects_and_fails_unwitnessed_macro_success():
    # Simulated case where primitive failed but macro passed
    primitive_case = {
        "goal_id": "test:01",
        "family": "G1",
        "verdict": "NOT_ESTABLISHED",
        "correct": False,
        "observed": None,
        "refusal_reason": "NO_ADMISSIBLE_PATH",
        "satisfied_derived_types": [],
        "expanded_state_count": 50,
        "primitive_execution_count": 50,
    }
    macro_case = {
        "goal_id": "test:01",
        "family": "G1",
        "verdict": "PASS",
        "correct": True,
        "observed": 42,
        "refusal_reason": None,
        "satisfied_derived_types": ["BOOLEAN_ZETA_SIGNAL"],
        "expanded_state_count": 10,
        "primitive_execution_count": 10,
    }
    
    eval_res = evaluate_macro_safety_and_efficiency(primitive_case, macro_case)
    assert eval_res["macro_rescue"] is True
    assert eval_res["credit_allowed"] is False
    assert eval_res["full_parity"] is False


def test_macro_efficiency_is_credited_only_under_exact_4way_parity():
    # Simulated case where both passed with identical observed, refusal, obligations, and reduced work
    primitive_case = {
        "goal_id": "test:02",
        "family": "G1",
        "verdict": "PASS",
        "correct": True,
        "observed": 42,
        "refusal_reason": None,
        "satisfied_derived_types": ["BOOLEAN_ZETA_SIGNAL"],
        "expanded_state_count": 50,
        "primitive_execution_count": 50,
    }
    macro_case = {
        "goal_id": "test:02",
        "family": "G1",
        "verdict": "PASS",
        "correct": True,
        "observed": 42,
        "refusal_reason": None,
        "satisfied_derived_types": ["BOOLEAN_ZETA_SIGNAL"],
        "expanded_state_count": 20,
        "primitive_execution_count": 20,
    }
    
    eval_res = evaluate_macro_safety_and_efficiency(primitive_case, macro_case)
    assert eval_res["macro_rescue"] is False
    assert eval_res["full_parity"] is True
    assert eval_res["credit_allowed"] is True
    assert eval_res["state_savings"] == 30
    assert eval_res["primitive_call_savings"] == 30
