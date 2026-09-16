from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
import math
from statistics import mean
from typing import Any, Mapping

from .compatibility import CompatibilityModel
from .goals import FAMILIES, GoalSpec, build_goal_corpus
from .macros import MacroSpec, synthesize_macros
from .model import SolveTrace
from .operators import OperatorSpec, build_operator_registry
from .planner import solve


MODE_CONFIGS = (
    ("EXPLICIT/PRIMITIVE", "EXPLICIT", False),
    ("EXPLICIT/SYNTHESIZED", "EXPLICIT", True),
    ("INFERRED/PRIMITIVE", "INFERRED", False),
    ("INFERRED/SYNTHESIZED", "INFERRED", True),
    ("HYBRID/PRIMITIVE", "HYBRID", False),
    ("HYBRID/SYNTHESIZED", "HYBRID", True),
)
MODE_NAMES = tuple(row[0] for row in MODE_CONFIGS)

FAMILY_CLASS = {
    "G1": "EXACT",
    "G2": "EXACT",
    "G3": "EXACT",
    "G4": "EXACT",
    "G5": "EXACT",
    "G6": "EXACT",
    "G7": "SYMBOLIC",
    "G8": "NUMERICAL",
    "G9": "NUMERICAL",
    "G10": "NUMERICAL",
    "G11": "NUMERICAL",
    "G12": "SYMBOLIC",
}


def _close_numeric(actual: Any, expected: Any, tolerance: float) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except (TypeError, ValueError, OverflowError):
        return False


def _g4_reference_level(goal: GoalSpec) -> str:
    """Independently reconstruct the first persistence representation that separates.

    This scorer never uses solver-produced intermediate artifacts. The goal builder's
    original broad answer label predates this exact-level verifier, so the verifier
    reconstructs the answer from the two sealed barcodes.
    """
    barcodes = (goal.inputs["barcode_a"].value, goal.inputs["barcode_b"].value)
    max_death = max(int(d) for barcode in barcodes for _, _, d in barcode)
    grid = tuple(range(max_death))

    def betti(barcode):
        return tuple(
            (
                sum(int(deg) == 0 and b <= t < d for deg, b, d in barcode),
                sum(int(deg) == 1 and b <= t < d for deg, b, d in barcode),
            )
            for t in grid
        )

    a_betti, b_betti = (betti(barcode) for barcode in barcodes)
    a_euler = tuple(b0 - b1 for b0, b1 in a_betti)
    b_euler = tuple(b0 - b1 for b0, b1 in b_betti)
    if a_euler != b_euler:
        return "EULER"
    if a_betti != b_betti:
        return "BETTI"
    if barcodes[0] != barcodes[1]:
        return "BARCODE"
    return "NONE"


def _is_control(goal: GoalSpec) -> bool:
    if goal.family == "G2":
        return not bool(goal.sealed_expected_result["unique"])
    if goal.family == "G3":
        return not bool(goal.sealed_expected_result["is_chain_map"])
    if goal.family == "G5":
        return not bool(goal.sealed_expected_result)
    if goal.family == "G9":
        return goal.sealed_expected_result == "NOT_APPLICABLE"
    if goal.family == "G11":
        return not bool(goal.sealed_expected_result)
    return False


def _observed_value(goal: GoalSpec, trace: SolveTrace) -> Any:
    if trace.candidate_artifact is None:
        return None
    value = trace.candidate_artifact.value
    if goal.family == "G2" and isinstance(value, dict):
        return {"unique": value.get("unique"), "nullity": value.get("nullity")}
    if goal.family == "G4" and isinstance(value, dict):
        return value.get("level")
    if goal.family == "G5" and isinstance(value, dict):
        return value.get("distinct")
    if goal.family == "G10" and isinstance(value, dict):
        return value.get("order")
    if goal.family == "G11" and isinstance(value, dict):
        return value.get("homothetic")
    return value


def _expected_value(goal: GoalSpec) -> Any:
    if goal.family == "G3":
        return goal.sealed_expected_result["is_chain_map"]
    if goal.family == "G4":
        return _g4_reference_level(goal)
    return goal.sealed_expected_result


def _correct_pass(goal: GoalSpec, trace: SolveTrace) -> bool:
    if trace.final_verdict != "PASS" or trace.candidate_artifact is None:
        return False
    actual = _observed_value(goal, trace)
    expected = _expected_value(goal)
    if goal.family in {"G8", "G9"}:
        if expected == "NOT_APPLICABLE":
            return False
        return _close_numeric(actual, expected, goal.allowed_numeric_tolerance)
    if goal.family == "G2":
        return actual == {
            "unique": goal.sealed_expected_result["unique"],
            "nullity": goal.sealed_expected_result["nullity"],
        }
    return actual == expected


def score_trace(goal: GoalSpec, trace: SolveTrace) -> dict[str, Any]:
    """Score a completed trace against sealed evidence loaded only after solving."""
    answered = trace.final_verdict == "PASS"
    correct_pass = _correct_pass(goal, trace)
    correct_refusal = goal.sealed_expected_result == "NOT_APPLICABLE" and trace.final_verdict == "NOT_APPLICABLE"
    correct = correct_pass or correct_refusal
    terminal_verified = bool(
        trace.final_verdict != "PASS"
        or (trace.verifier_chain and trace.verifier_chain[-1].passed)
    )
    return {
        "goal_id": goal.goal_id,
        "family": goal.family,
        "family_class": FAMILY_CLASS[goal.family],
        "verdict": trace.final_verdict,
        "answered": answered,
        "correct": bool(correct),
        "correct_pass": bool(correct_pass),
        "wrong_positive": bool(answered and not correct_pass),
        "control": _is_control(goal),
        "terminal_verifier_passed": terminal_verified,
        "observed": _safe_value(_observed_value(goal, trace)),
        "expected": _safe_value(_expected_value(goal)),
        "operator_path": list(trace.operator_path),
        "macro_ids": list(trace.macro_ids),
        "expanded_state_count": trace.expanded_state_count,
        "primitive_execution_count": trace.primitive_execution_count,
        "failure_reason": trace.failure_reason,
    }


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return repr(value)
    if isinstance(value, dict):
        return {str(k): _safe_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_safe_value(v) for v in value]
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return repr(value)


def _primitive_path(case: Mapping[str, Any], registry: Mapping[str, OperatorSpec]) -> tuple[str, ...]:
    return tuple(operator_id for operator_id in case["operator_path"] if operator_id in registry and operator_id != "VERIFY_CANDIDATE")


def _path_classes(case: Mapping[str, Any], registry: Mapping[str, OperatorSpec]) -> tuple[set[str], set[str]]:
    path = _primitive_path(case, registry)
    exactness = {registry[operator_id].exactness_class for operator_id in path}
    representations = {registry[operator_id].representation_class for operator_id in path}
    return exactness, representations


def _summarize_mode(cases: list[dict[str, Any]], registry: Mapping[str, OperatorSpec]) -> dict[str, Any]:
    solved_families = sorted({case["family"] for case in cases if case["correct_pass"]})
    multi_step = sorted({
        case["family"]
        for case in cases
        if case["correct_pass"] and len(_primitive_path(case, registry)) >= 2
    })
    cross_class = []
    for case in cases:
        if not case["correct_pass"]:
            continue
        exactness, representations = _path_classes(case, registry)
        if len(exactness) > 1 or len(representations) > 1:
            cross_class.append(case["family"])
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for case in cases:
        if case["wrong_positive"]:
            outcome = "wrong_positive"
        elif case["correct_pass"]:
            outcome = "correct_pass"
        elif case["correct"]:
            outcome = "correct_refusal"
        else:
            outcome = case["verdict"].lower()
        by_family[case["family"]][outcome] += 1
    return {
        "total": len(cases),
        "pass_count": sum(case["verdict"] == "PASS" for case in cases),
        "correct_pass_count": sum(case["correct_pass"] for case in cases),
        "correct_outcome_count": sum(case["correct"] for case in cases),
        "wrong_positive_count": sum(case["wrong_positive"] for case in cases),
        "control_wrong_positive_count": sum(case["wrong_positive"] and case["control"] for case in cases),
        "not_established_count": sum(case["verdict"] == "NOT_ESTABLISHED" for case in cases),
        "not_applicable_count": sum(case["verdict"] == "NOT_APPLICABLE" for case in cases),
        "all_positive_results_independently_verified": all(
            case["terminal_verifier_passed"] for case in cases if case["verdict"] == "PASS"
        ),
        "solved_families": solved_families,
        "solved_family_count": len(solved_families),
        "multi_step_solved_families": multi_step,
        "multi_step_solved_family_count": len(multi_step),
        "cross_class_solved_families": sorted(set(cross_class)),
        "cross_class_solved_family_count": len(set(cross_class)),
        "mean_expanded_states": mean(case["expanded_state_count"] for case in cases) if cases else 0.0,
        "mean_primitive_executions": mean(case["primitive_execution_count"] for case in cases) if cases else 0.0,
        "by_family": {family: dict(sorted(counter.items())) for family, counter in sorted(by_family.items())},
        "cases": cases,
    }


def _run_split(
    goals: list[GoalSpec],
    registry: Mapping[str, OperatorSpec],
    compatibility_model: CompatibilityModel,
    macros: tuple[MacroSpec, ...],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for mode_name, typing_mode, synthesized in MODE_CONFIGS:
        mode_cases = []
        for goal in goals:
            trace = solve(
                goal.solver_visible(),
                registry,
                typing_mode=typing_mode,
                compatibility_model=compatibility_model if typing_mode != "EXPLICIT" else None,
                macros=macros if synthesized else (),
            )
            # Only after solve() returns is sealed_expected_result consulted.
            mode_cases.append(score_trace(goal, trace))
        result[mode_name] = _summarize_mode(mode_cases, registry)
    return result


def _macro_comparison(modes: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    pairs = (
        ("EXPLICIT/PRIMITIVE", "EXPLICIT/SYNTHESIZED"),
        ("INFERRED/PRIMITIVE", "INFERRED/SYNTHESIZED"),
        ("HYBRID/PRIMITIVE", "HYBRID/SYNTHESIZED"),
    )
    semantic_changes = 0
    reductions = 0
    macro_use = 0
    rows = []
    for primitive_name, synthesized_name in pairs:
        primitive = {case["goal_id"]: case for case in modes[primitive_name]["cases"]}
        synthesized = {case["goal_id"]: case for case in modes[synthesized_name]["cases"]}
        for goal_id in sorted(primitive):
            a, b = primitive[goal_id], synthesized[goal_id]
            same_semantics = (
                a["verdict"] == b["verdict"]
                and a["correct"] == b["correct"]
                and a["observed"] == b["observed"]
            )
            reduced = (
                b["expanded_state_count"] < a["expanded_state_count"]
                or b["primitive_execution_count"] < a["primitive_execution_count"]
            )
            used = bool(b["macro_ids"])
            semantic_changes += not same_semantics
            reductions += bool(same_semantics and reduced and used)
            macro_use += used
            if used or not same_semantics:
                rows.append({
                    "mode_pair": [primitive_name, synthesized_name],
                    "goal_id": goal_id,
                    "macro_ids": b["macro_ids"],
                    "same_semantics": same_semantics,
                    "reduced_work": reduced,
                    "primitive_expanded": a["expanded_state_count"],
                    "synthesized_expanded": b["expanded_state_count"],
                    "primitive_executions": a["primitive_execution_count"],
                    "synthesized_executions": b["primitive_execution_count"],
                })
    return {
        "semantic_change_count": semantic_changes,
        "reduction_with_macro_count": reductions,
        "macro_used_case_count": macro_use,
        "supported": semantic_changes == 0 and reductions > 0,
        "cases": rows,
    }


def _inferred_class_coverage(mode: Mapping[str, Any]) -> dict[str, int]:
    counts = Counter()
    for case in mode["cases"]:
        if case["correct_pass"]:
            counts[case["family_class"]] += 1
    return {name: int(counts[name]) for name in ("EXACT", "SYMBOLIC", "NUMERICAL")}


@lru_cache(maxsize=1)
def run_campaign() -> dict[str, Any]:
    corpus = build_goal_corpus()
    registry = build_operator_registry()

    # Calibration is frozen before any validation or sealed execution.
    calibration_traces = tuple(
        solve(goal.solver_visible(), registry, typing_mode="EXPLICIT")
        for goal in corpus["CALIBRATION"]
    )
    compatibility = CompatibilityModel.fit(corpus["CALIBRATION"], calibration_traces, registry)
    macros = synthesize_macros(corpus["CALIBRATION"], calibration_traces, registry, min_distinct_goals=2)

    # Validation smoke happens before sealed scoring. No parameters are changed afterward.
    validation = _run_split(corpus["VALIDATION"], registry, compatibility, macros)
    sealed = _run_split(corpus["SEALED"], registry, compatibility, macros)

    explicit = sealed["EXPLICIT/PRIMITIVE"]
    inferred = sealed["INFERRED/PRIMITIVE"]
    hybrid = sealed["HYBRID/PRIMITIVE"]
    inferred_classes = _inferred_class_coverage(inferred)
    macro = _macro_comparison(sealed)

    gates = {
        "explicit_all_12_families": explicit["solved_family_count"] == len(FAMILIES),
        "explicit_zero_wrong_positives": explicit["wrong_positive_count"] == 0,
        "explicit_six_multistep_families": explicit["multi_step_solved_family_count"] >= 6,
        "three_cross_class_families": explicit["cross_class_solved_family_count"] >= 3,
        "inferred_nonzero_exact_symbolic_numeric": all(inferred_classes[name] > 0 for name in ("EXACT", "SYMBOLIC", "NUMERICAL")),
        "inferred_no_control_wrong_positive_increase": inferred["control_wrong_positive_count"] <= explicit["control_wrong_positive_count"],
        "hybrid_preserves_controls_and_family_coverage": (
            hybrid["control_wrong_positive_count"] == 0
            and hybrid["solved_family_count"] >= inferred["solved_family_count"]
        ),
        "macro_reduces_search_without_semantic_change": bool(macro["supported"]),
        "all_positive_results_independently_verified": all(
            mode["all_positive_results_independently_verified"] for mode in sealed.values()
        ),
    }

    conclusions = {
        "GOAL_DIRECTED_SOLVING": {
            "status": "SUPPORTED" if gates["explicit_all_12_families"] and gates["explicit_zero_wrong_positives"] else "NOT_SUPPORTED",
            "solved_families": explicit["solved_families"],
            "wrong_positive_count": explicit["wrong_positive_count"],
        },
        "INFERRED_COMPATIBILITY": {
            "status": "SUPPORTED" if gates["inferred_nonzero_exact_symbolic_numeric"] and gates["inferred_no_control_wrong_positive_increase"] else "NOT_SUPPORTED",
            "class_coverage": inferred_classes,
            "solved_families": inferred["solved_families"],
            "wrong_positive_count": inferred["wrong_positive_count"],
        },
        "MIXED_DOMAIN_COMPOSITION": {
            "status": "SUPPORTED" if gates["explicit_six_multistep_families"] and gates["three_cross_class_families"] else "NOT_SUPPORTED",
            "multi_step_families": explicit["multi_step_solved_families"],
            "cross_class_families": explicit["cross_class_solved_families"],
        },
        "MACRO_SYNTHESIS": {
            "status": "SUPPORTED" if gates["macro_reduces_search_without_semantic_change"] else "NOT_SUPPORTED",
            **macro,
        },
    }

    supported_count = sum(row["status"] == "SUPPORTED" for row in conclusions.values())
    scientific_status = "SUPPORTED" if supported_count == len(conclusions) else "PARTIAL" if supported_count else "NOT_SUPPORTED"

    return {
        "experiment_id": "PCT_GOAL_DIRECTED_MIXED_DOMAIN_SOLVER",
        "protocol": "CALIBRATION_THEN_VALIDATION_THEN_SEALED_NO_RETUNING",
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
            "supported_scope": "structured finite/exact/symbolic/numerical goals in the frozen G1-G12 executable corpus",
            "not_claimed": [
                "natural-language mathematical understanding",
                "universal theorem proving",
                "correctness outside the frozen operator and verifier universe",
                "novel theorem status for synthesized macros",
            ],
        },
    }
