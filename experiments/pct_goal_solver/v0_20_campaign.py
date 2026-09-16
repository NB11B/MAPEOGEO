from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from typing import Any, Mapping

from .campaign import MODE_CONFIGS, _summarize_mode, score_trace
from .compatibility import CompatibilityModel
from .macros import MacroSpec
from .model import GoalSpec
from .operators import OperatorSpec
from .planner import solve
from .v0_20_goals import (
    ALL_V0_20_FAMILIES,
    FOUNDATIONAL_FAMILIES,
    COMPLEX_FAMILIES,
    CROSS_CLASS_FAMILIES,
    V1_FAMILIES,
    build_v0_20_corpus,
    prove_no_same_class_shortcut,
)
from .v0_20_macros import (
    CertifiedMacroSpec,
    synthesize_certified_macros,
    evaluate_macro_safety_and_efficiency,
)
from .v0_20_operators import build_v0_20_operator_registry


def _blind_input_semantic_types(goal_visible):
    """Hide all original input type labels from inferred/hybrid execution."""
    return replace(
        goal_visible,
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in goal_visible.inputs.items()
        },
    )


def _to_macro_spec(c: CertifiedMacroSpec) -> MacroSpec:
    return MacroSpec(
        macro_id=c.macro_id,
        primitive_ids=c.primitive_ids,
        support_goal_ids=c.witness_goal_ids,
        entry_input_types=c.entry_input_types,
        terminal_output_type=c.terminal_output_type,
        terminal_representation_class=c.terminal_representation_class,
        terminal_exactness_class=c.terminal_exactness_class,
    )


def _run_v0_20_split(
    goals: list[GoalSpec],
    registry: Mapping[str, OperatorSpec],
    compatibility_model: CompatibilityModel,
    certified_macros: tuple[CertifiedMacroSpec, ...],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    macro_specs = tuple(_to_macro_spec(c) for c in certified_macros)

    for mode_name, typing_mode, synthesized in MODE_CONFIGS:
        blinded = (typing_mode != "EXPLICIT")
        mode_cases: list[dict[str, Any]] = []
        for goal in goals:
            visible = goal.solver_visible()
            if blinded:
                visible = _blind_input_semantic_types(visible)
            trace = solve(
                visible,
                registry,
                typing_mode=typing_mode,
                compatibility_model=compatibility_model if typing_mode != "EXPLICIT" else None,
                macros=macro_specs if synthesized else (),
            )
            case = score_trace(goal, trace)
            case["input_semantic_types_blinded"] = blinded
            mode_cases.append(case)

        summary = _summarize_mode(mode_cases, registry)
        correct_families = sorted({c["family"] for c in mode_cases if c["correct"]})
        summary["correct_outcome_families"] = correct_families
        summary["correct_outcome_family_count"] = len(correct_families)
        summary["input_semantic_types_blinded"] = blinded
        result[mode_name] = summary

    return result


def _segregated_macro_analysis(
    modes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    pairs = (
        ("EXPLICIT/PRIMITIVE", "EXPLICIT/SYNTHESIZED"),
        ("INFERRED/PRIMITIVE", "INFERRED/SYNTHESIZED"),
        ("HYBRID/PRIMITIVE", "HYBRID/SYNTHESIZED"),
    )
    all_evaluations: list[dict[str, Any]] = []
    total_macro_rescues = 0
    total_credited = 0
    total_state_savings = 0
    total_primitive_call_savings = 0

    for prim_name, synth_name in pairs:
        prim_map = {c["goal_id"]: c for c in modes[prim_name]["cases"]}
        synth_map = {c["goal_id"]: c for c in modes[synth_name]["cases"]}
        for goal_id, prim_case in sorted(prim_map.items()):
            synth_case = synth_map[goal_id]
            eval_res = evaluate_macro_safety_and_efficiency(prim_case, synth_case)
            eval_res["mode_pair"] = f"{prim_name} -> {synth_name}"
            all_evaluations.append(eval_res)
            if eval_res["macro_rescue"]:
                total_macro_rescues += 1
            if eval_res["credit_allowed"]:
                total_credited += 1
                total_state_savings += eval_res["state_savings"]
                total_primitive_call_savings += eval_res["primitive_call_savings"]

    return {
        "evaluations": all_evaluations,
        "total_comparisons": len(all_evaluations),
        "total_macro_rescues": total_macro_rescues,
        "zero_macro_rescues": total_macro_rescues == 0,
        "total_credited_cases": total_credited,
        "total_state_savings": total_state_savings,
        "total_primitive_call_savings": total_primitive_call_savings,
    }


def execute_v0_20_campaign() -> dict[str, Any]:
    """Execute full v0.20 campaign with segregated reporting and scientific gates."""
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()

    # 1. Calibration phase: train compatibility and synthesize certified macros
    calibration_goals = corpus["CALIBRATION_V0_20"]
    calib_traces = [
        solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        for goal in calibration_goals
    ]
    compatibility_model = CompatibilityModel.fit(calibration_goals, calib_traces, registry)
    certified_macros = synthesize_certified_macros(calibration_goals, calib_traces, registry)

    # 2. Run splits
    calib_split = _run_v0_20_split(calibration_goals, registry, compatibility_model, certified_macros)
    val_split = _run_v0_20_split(corpus["VALIDATION_V0_20"], registry, compatibility_model, certified_macros)
    sealed_split = _run_v0_20_split(corpus["SEALED_V0_20"], registry, compatibility_model, certified_macros)

    # 3. Shortcut proofs for sealed cross-class goals
    sealed_shortcut_proofs = [
        prove_no_same_class_shortcut(goal, registry)
        for goal in corpus["SEALED_V0_20"]
        if goal.family in CROSS_CLASS_FAMILIES
    ]

    # 4. Segregated reporting channels
    # Channel 1: Historical Regression
    explicit_sealed_cases = sealed_split["EXPLICIT/PRIMITIVE"]["cases"]
    hist_cases = [c for c in explicit_sealed_cases if c["family"] in V1_FAMILIES]
    hist_correct_count = sum(1 for c in hist_cases if c["correct"])
    hist_families_covered = sorted({c["family"] for c in hist_cases if c["correct"]})

    # Channel 2: Cross-Class Composition & Math Surface
    foundational_cases = [c for c in explicit_sealed_cases if c["family"] in FOUNDATIONAL_FAMILIES]
    foundational_correct = sum(1 for c in foundational_cases if c["correct"])

    complex_cases = [c for c in explicit_sealed_cases if c["family"] in COMPLEX_FAMILIES]
    complex_correct = sum(1 for c in complex_cases if c["correct"])

    cross_class_cases = [c for c in explicit_sealed_cases if c["family"] in CROSS_CLASS_FAMILIES]
    cross_class_correct = sum(1 for c in cross_class_cases if c["correct"])

    # Channel 3: Macro Conservation & Safety
    macro_analysis = _segregated_macro_analysis(sealed_split)

    # Scientific Gates
    total_wrong_positives = sum(
        mode_data["wrong_positive_count"]
        for mode_data in sealed_split.values()
    )

    gates = {
        "zero_wrong_positives": total_wrong_positives == 0,
        "zero_macro_rescues": macro_analysis["zero_macro_rescues"],
        "historical_g1_g12_coverage": len(hist_families_covered) == len(V1_FAMILIES),
        "foundational_f1_f3_coverage": foundational_correct == len(foundational_cases),
        "complex_c1_c2_coverage": complex_correct == len(complex_cases),
        "cross_class_x1_x2_coverage": cross_class_correct == len(cross_class_cases),
        "no_same_class_shortcuts_proven": all(p["proven_no_shortcut"] for p in sealed_shortcut_proofs),
        "type_blind_routing_inferred": len(sealed_split["INFERRED/PRIMITIVE"]["correct_outcome_families"]) == len(ALL_V0_20_FAMILIES),
        "type_blind_routing_hybrid": len(sealed_split["HYBRID/PRIMITIVE"]["correct_outcome_families"]) == len(ALL_V0_20_FAMILIES),
        "certified_macro_witness_bound": len(certified_macros) > 0 and all(len(m.witness_trace_digests) > 0 for m in certified_macros),
    }

    all_gates_passed = all(gates.values())

    return {
        "campaign_id": "PCT_GOAL_SOLVER_CROSS_CLASS_V0_20",
        "scientific_status": "SUPPORTED" if all_gates_passed else "PARTIAL",
        "gates": gates,
        "gates_passed": sum(1 for v in gates.values() if v),
        "gates_total": len(gates),
        "total_wrong_positives": total_wrong_positives,
        "channels": {
            "historical_regression": {
                "baseline_families_count": len(V1_FAMILIES),
                "solved_families_count": len(hist_families_covered),
                "solved_families": hist_families_covered,
                "cases_correct": hist_correct_count,
                "cases_total": len(hist_cases),
            },
            "cross_class_composition": {
                "foundational_f1_f3": {"correct": foundational_correct, "total": len(foundational_cases)},
                "complex_c1_c2": {"correct": complex_correct, "total": len(complex_cases)},
                "cross_class_x1_x2": {"correct": cross_class_correct, "total": len(cross_class_cases)},
                "shortcut_proofs": sealed_shortcut_proofs,
            },
            "macro_conservation": macro_analysis,
        },
        "certified_macros": [
            {
                "macro_id": m.macro_id,
                "primitives": list(m.primitive_ids),
                "witness_goals": sorted(m.witness_goal_ids),
                "witness_digests": list(m.witness_trace_digests),
            }
            for m in certified_macros
        ],
        "splits": {
            "CALIBRATION_V0_20": calib_split,
            "VALIDATION_V0_20": val_split,
            "SEALED_V0_20": sealed_split,
        },
    }
