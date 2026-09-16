from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
import hashlib
import json
from typing import Any, Mapping, Sequence

from .model import GoalSpec, SolveTrace, VerificationResult
from .operators import OperatorSpec


@dataclass(frozen=True)
class CertifiedMacroSpec:
    macro_id: str
    primitive_ids: tuple[str, ...]
    witness_goal_ids: frozenset[str]
    witness_trace_digests: tuple[str, ...]
    entry_input_types: tuple[str, ...]
    terminal_output_type: str
    terminal_representation_class: str
    terminal_exactness_class: str


def _macro_digest(path: tuple[str, ...]) -> str:
    return hashlib.sha256("->".join(path).encode("utf-8")).hexdigest()[:16]


def _trace_digest(trace: SolveTrace) -> str:
    payload = {
        "goal_id": trace.goal_id,
        "operator_path": list(trace.operator_path),
        "verdict": trace.final_verdict,
        "candidate": repr(trace.candidate_artifact.value) if trace.candidate_artifact else None,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def synthesize_certified_macros(
    calibration_goals: Sequence[GoalSpec],
    primitive_traces: Sequence[SolveTrace],
    registry: Mapping[str, OperatorSpec],
    *,
    min_distinct_goals: int = 2,
    min_length: int = 2,
    max_length: int = 4,
) -> tuple[CertifiedMacroSpec, ...]:
    """Synthesize macros strictly certified against already-discovered primitive witnesses.
    
    Every macro must be accompanied by the exact trace digests of passing primitive
    executions on calibration goals.
    """
    calibration_ids = {goal.goal_id for goal in calibration_goals}
    support_goals: dict[tuple[str, ...], set[str]] = defaultdict(set)
    support_traces: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for trace in primitive_traces:
        if trace.goal_id not in calibration_ids:
            raise ValueError(f"non-calibration trace supplied to macro certification: {trace.goal_id}")
        if trace.final_verdict != "PASS" or not trace.verifier_chain or not trace.verifier_chain[-1].passed:
            continue
        primitive_path = tuple(op_id for op_id in trace.operator_path if op_id in registry)
        digest = _trace_digest(trace)
        for width in range(min_length, min(max_length, len(primitive_path)) + 1):
            for start in range(0, len(primitive_path) - width + 1):
                window = primitive_path[start : start + width]
                support_goals[window].add(trace.goal_id)
                support_traces[window].append(digest)

    macros: list[CertifiedMacroSpec] = []
    for path, goal_ids in sorted(support_goals.items(), key=lambda item: (len(item[0]), item[0])):
        if len(goal_ids) < min_distinct_goals:
            continue
        if any(op_id not in registry for op_id in path):
            continue
        first = registry[path[0]]
        last = registry[path[-1]]
        macros.append(
            CertifiedMacroSpec(
                macro_id=f"CERT_MACRO:{_macro_digest(path)}",
                primitive_ids=path,
                witness_goal_ids=frozenset(goal_ids),
                witness_trace_digests=tuple(sorted(set(support_traces[path]))),
                entry_input_types=first.input_types,
                terminal_output_type=last.output_type,
                terminal_representation_class=last.representation_class,
                terminal_exactness_class=last.exactness_class,
            )
        )
    return tuple(macros)


def evaluate_macro_safety_and_efficiency(
    primitive_case: dict[str, Any],
    macro_case: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate anti-MACRO_RESCUE safety and 4-way exact certificate conservation.
    
    Dimensions checked:
    1. Anti-Macro Rescue: If primitive fails/refuses and macro passes -> MACRO_RESCUE (hard fail).
    2. Exact Output Equivalence: primitive observed == macro observed.
    3. Refusal Parity: if one refuses, both must refuse with identical refusal codes.
    4. Derived Obligation Parity: both satisfy identical derived representation types.
    """
    prim_verdict = primitive_case.get("verdict")
    macro_verdict = macro_case.get("verdict")
    prim_correct = primitive_case.get("correct", False)
    macro_correct = macro_case.get("correct", False)

    # 1. Check for MACRO_RESCUE
    is_macro_rescue = (not prim_correct) and macro_correct
    
    # 2. Output and observed state equivalence
    same_verdict = (prim_verdict == macro_verdict)
    same_correctness = (prim_correct == macro_correct)
    same_observed = (primitive_case.get("observed") == macro_case.get("observed"))
    
    # 3. Refusal parity
    prim_refusal = primitive_case.get("refusal_reason")
    macro_refusal = macro_case.get("refusal_reason")
    same_refusal = (prim_refusal == macro_refusal)
    
    # 4. Derived obligations parity
    prim_obligations = set(primitive_case.get("satisfied_derived_types", []))
    macro_obligations = set(macro_case.get("satisfied_derived_types", []))
    same_obligations = (prim_obligations == macro_obligations)

    full_parity = (
        same_verdict
        and same_correctness
        and same_observed
        and same_refusal
        and same_obligations
        and not is_macro_rescue
    )

    work_reduced = (
        macro_case.get("expanded_state_count", 0) < primitive_case.get("expanded_state_count", 0)
        or macro_case.get("primitive_execution_count", 0) < primitive_case.get("primitive_execution_count", 0)
    )

    credit_allowed = full_parity and prim_correct and work_reduced

    return {
        "goal_id": primitive_case.get("goal_id"),
        "family": primitive_case.get("family"),
        "macro_rescue": is_macro_rescue,
        "full_parity": full_parity,
        "same_verdict": same_verdict,
        "same_observed": same_observed,
        "same_refusal": same_refusal,
        "same_obligations": same_obligations,
        "primitive_correct": prim_correct,
        "macro_correct": macro_correct,
        "work_reduced": work_reduced,
        "credit_allowed": credit_allowed,
        "state_savings": max(0, primitive_case.get("expanded_state_count", 0) - macro_case.get("expanded_state_count", 0)),
        "primitive_call_savings": max(0, primitive_case.get("primitive_execution_count", 0) - macro_case.get("primitive_execution_count", 0)),
    }
