from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from typing import Any, Mapping

from .campaign import MODE_CONFIGS, _summarize_mode, score_trace
from .compatibility import CompatibilityModel
from .macros import MacroSpec, synthesize_macros
from .model import GoalSpec
from .operators import OperatorSpec
from .planner import solve
from .v2 import build_v2_corpus, build_v2_operator_registry


V2_MODE_NAMES = tuple(row[0] for row in MODE_CONFIGS)
_ALL_FAMILIES = {f"G{i}" for i in range(1, 13)}


def _blind_input_semantic_types(goal_visible):
    """Hide all original input type labels from inferred/hybrid V2 execution."""
    return replace(
        goal_visible,
        inputs={
            key: replace(artifact, semantic_type="BLINDED_INPUT_TYPE")
            for key, artifact in goal_visible.inputs.items()
        },
    )


def _correct_outcome_families(cases: list[dict[str, Any]]) -> list[str]:
    return sorted({case["family"] for case in cases if case["correct"]})


def _run_v2_split(
    goals: list[GoalSpec],
    registry: Mapping[str, OperatorSpec],
    compatibility_model: CompatibilityModel,
    macros: tuple[MacroSpec, ...],
) -> dict[str, dict[str, Any]]:
    """Execute all six modes; expected answers are consulted only after solve()."""
    result: dict[str, dict[str, Any]] = {}
    for mode_name, typing_mode, synthesized in MODE_CONFIGS:
        blinded = typing_mode != "EXPLICIT"
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
                macros=macros if synthesized else (),
            )
            # Sealed expected results remain outside solve(). Scoring begins only
            # after the trace has been finalized.
            case = score_trace(goal, trace)
            case["input_semantic_types_blinded"] = blinded
            mode_cases.append(case)

        summary = _summarize_mode(mode_cases, registry)
        outcome_families = _correct_outcome_families(mode_cases)
        summary["correct_outcome_families"] = outcome_families
        summary["correct_outcome_family_count"] = len(outcome_families)
        summary["input_semantic_types_blinded"] = blinded
        result[mode_name] = summary
    return result


def _macro_comparison_v2(modes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Credit macro savings only when the primitive baseline is already correct."""
    pairs = (
        ("EXPLICIT/PRIMITIVE", "EXPLICIT/SYNTHESIZED"),
        ("INFERRED/PRIMITIVE", "INFERRED/SYNTHESIZED"),
        ("HYBRID/PRIMITIVE", "HYBRID/SYNTHESIZED"),
    )
    rows: list[dict[str, Any]] = []
    credited: list[dict[str, Any]] = []
    correct_primitive_semantic_changes = 0
    all_semantic_changes = 0
    macro_used_case_count = 0
    incorrect_primitive_credit_count = 0

    for primitive_name, synthesized_name in pairs:
        primitive = {case["goal_id"]: case for case in modes[primitive_name]["cases"]}
        synthesized = {case["goal_id"]: case for case in modes[synthesized_name]["cases"]}
        for goal_id in sorted(primitive):
            a = primitive[goal_id]
            b = synthesized[goal_id]
            same_semantics = (
                a["verdict"] == b["verdict"]
                and a["correct"] == b["correct"]
                and a["observed"] == b["observed"]
            )
            reduced_work = (
                b["expanded_state_count"] < a["expanded_state_count"]
                or b["primitive_execution_count"] < a["primitive_execution_count"]
            )
            macro_ids = list(b["macro_ids"])
            used = bool(macro_ids)
            primitive_correct = bool(a["correct"])
            synthesized_correct = bool(b["correct"])

            all_semantic_changes += int(not same_semantics)
            if primitive_correct and not same_semantics:
                correct_primitive_semantic_changes += 1
            macro_used_case_count += int(used)

            row = {
                "mode_pair": [primitive_name, synthesized_name],
                "goal_id": goal_id,
                "family": a["family"],
                "primitive_correct": primitive_correct,
                "synthesized_correct": synthesized_correct,
                "same_semantics": bool(same_semantics),
                "reduced_work": bool(reduced_work),
                "macro_ids": macro_ids,
                "primitive_expanded": a["expanded_state_count"],
                "synthesized_expanded": b["expanded_state_count"],
                "primitive_executions": a["primitive_execution_count"],
                "synthesized_executions": b["primitive_execution_count"],
            }
            if used or not same_semantics:
                rows.append(row)

            credit = primitive_correct and synthesized_correct and same_semantics and used and reduced_work
            if credit:
                credited.append(row)
                if not primitive_correct:
                    incorrect_primitive_credit_count += 1

    return {
        "correct_primitive_semantic_change_count": correct_primitive_semantic_changes,
        "all_semantic_change_count": all_semantic_changes,
        "macro_used_case_count": macro_used_case_count,
        "incorrect_primitive_credit_count": incorrect_primitive_credit_count,
        "credited_reduction_count": len(credited),
        "credited_reductions": credited,
        "cases": rows,
    }


def _cross_class_target_gate(explicit_mode: Mapping[str, Any]) -> bool:
    return {"G6", "G8", "G9"} <= set(explicit_mode["cross_class_solved_families"])


@lru_cache(maxsize=1)
def run_v2_campaign() -> dict[str, Any]:
    """Run the prospective V2 campaign exactly once per process.

    The order is calibration -> validation -> frozen sealed execution. No sealed
    outcome is available to the compatibility model, macro synthesizer, registry,
    evidence obligations, or search policy.
    """
    corpus = build_v2_corpus()
    registry = build_v2_operator_registry()

    calibration_traces = tuple(
        solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        for goal in corpus["CALIBRATION_V2"]
    )
    compatibility = CompatibilityModel.fit(
        corpus["CALIBRATION_V2"], calibration_traces, registry
    )
    macros = synthesize_macros(
        corpus["CALIBRATION_V2"], calibration_traces, registry, min_distinct_goals=2
    )

    # Validation is execution-only. Nothing is selected or modified from its
    # result; the frozen machinery is carried directly into SEALED_V2.
    validation = _run_v2_split(
        corpus["VALIDATION_V2"], registry, compatibility, macros
    )

    # FIRST SCIENTIFIC SEALED EXECUTION. Results from this line onward are final
    # evidence for V2 and must not be used to retune the V2 architecture.
    sealed = _run_v2_split(corpus["SEALED_V2"], registry, compatibility, macros)

    explicit = sealed["EXPLICIT/PRIMITIVE"]
    inferred = sealed["INFERRED/PRIMITIVE"]
    hybrid = sealed["HYBRID/PRIMITIVE"]
    macro = _macro_comparison_v2(sealed)

    gates = {
        "explicit_zero_wrong_positives": explicit["wrong_positive_count"] == 0,
        "explicit_ten_multistep_families": explicit["multi_step_solved_family_count"] >= 10,
        "three_cross_class_families": explicit["cross_class_solved_family_count"] >= 3,
        "g6_g8_g9_cross_class": _cross_class_target_gate(explicit),
        "all_positive_results_independently_verified": all(
            mode["all_positive_results_independently_verified"] for mode in sealed.values()
        ),
        "inferred_all_12_families_type_blind": (
            inferred["correct_outcome_family_count"] == len(_ALL_FAMILIES)
            and bool(inferred["input_semantic_types_blinded"])
        ),
        "inferred_zero_control_wrong_positives": inferred["control_wrong_positive_count"] == 0,
        "hybrid_preserves_controls_and_family_coverage": (
            hybrid["control_wrong_positive_count"] == 0
            and hybrid["correct_outcome_family_count"] >= inferred["correct_outcome_family_count"]
            and bool(hybrid["input_semantic_types_blinded"])
        ),
        "macro_preserves_correct_primitive_semantics": (
            macro["correct_primitive_semantic_change_count"] == 0
            and macro["incorrect_primitive_credit_count"] == 0
        ),
        "macro_reduces_search_on_correct_cases": macro["credited_reduction_count"] > 0,
    }

    conclusions = {
        "COMPOSITION_DEPTH": {
            "status": "SUPPORTED" if (
                gates["explicit_zero_wrong_positives"]
                and gates["explicit_ten_multistep_families"]
                and gates["all_positive_results_independently_verified"]
            ) else "NOT_SUPPORTED",
            "multi_step_families": explicit["multi_step_solved_families"],
            "multi_step_family_count": explicit["multi_step_solved_family_count"],
            "wrong_positive_count": explicit["wrong_positive_count"],
        },
        "CROSS_REPRESENTATION_COMPOSITION": {
            "status": "SUPPORTED" if (
                gates["three_cross_class_families"]
                and gates["g6_g8_g9_cross_class"]
                and gates["all_positive_results_independently_verified"]
            ) else "NOT_SUPPORTED",
            "cross_class_families": explicit["cross_class_solved_families"],
            "cross_class_family_count": explicit["cross_class_solved_family_count"],
            "required_cross_class_families": ["G6", "G8", "G9"],
        },
        "TYPE_BLIND_ROUTING": {
            "status": "SUPPORTED" if (
                gates["inferred_all_12_families_type_blind"]
                and gates["inferred_zero_control_wrong_positives"]
                and gates["hybrid_preserves_controls_and_family_coverage"]
            ) else "NOT_SUPPORTED",
            "inferred_correct_outcome_families": inferred["correct_outcome_families"],
            "inferred_wrong_positive_count": inferred["wrong_positive_count"],
            "inferred_control_wrong_positive_count": inferred["control_wrong_positive_count"],
            "hybrid_correct_outcome_families": hybrid["correct_outcome_families"],
        },
        "MACRO_PRESERVATION": {
            "status": "SUPPORTED" if (
                gates["macro_preserves_correct_primitive_semantics"]
                and gates["macro_reduces_search_on_correct_cases"]
            ) else "NOT_SUPPORTED",
            "correct_primitive_semantic_change_count": macro["correct_primitive_semantic_change_count"],
            "credited_reduction_count": macro["credited_reduction_count"],
            "macro_used_case_count": macro["macro_used_case_count"],
        },
    }

    supported_count = sum(
        payload["status"] == "SUPPORTED" for payload in conclusions.values()
    )
    if supported_count == len(conclusions):
        scientific_status = "SUPPORTED"
    elif supported_count:
        scientific_status = "PARTIAL"
    else:
        scientific_status = "NOT_SUPPORTED"

    return {
        "experiment_id": "PCT_GOAL_SOLVER_V2_COMPOSITION_STRESS",
        "protocol": "V2_CALIBRATION_VALIDATION_FREEZE_THEN_SEALED_NO_RETUNING",
        "sealed_result_frozen": True,
        "corpus_counts": {split: len(rows) for split, rows in corpus.items()},
        "operator_count": len(registry),
        "macro_count": len(macros),
        "compatibility_training_goal_count": len(compatibility.goal_ids),
        "validation": validation,
        "modes": sealed,
        "macro_comparison": macro,
        "gates": gates,
        "conclusions": conclusions,
        "scientific_status": scientific_status,
        "claim_boundary": {
            "supported_scope": "structured G1-G12 exact/symbolic/numerical goals under frozen V2 evidence obligations and the 35-operator executable universe",
            "not_claimed": [
                "natural-language mathematical understanding",
                "unrestricted theorem proving",
                "correctness outside the frozen operator/verifier contracts",
                "novel theorem status for macros or representation bridges",
            ],
        },
    }
