from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

from .canonical import canonical_sha256
from .macros import _certificate_digest
from .model import GoalSpec, SolveTrace, VerificationResult
from .operators import OperatorSpec, operator_registry_digest


@dataclass(frozen=True)
class MacroProposalSpec:
    """Calibration-bound proposal with no production execution authority."""

    macro_id: str
    primitive_ids: tuple[str, ...]
    witness_goal_ids: frozenset[str]
    witness_trace_digests: tuple[str, ...]
    entry_input_types: tuple[str, ...]
    terminal_output_type: str
    terminal_representation_class: str
    terminal_exactness_class: str
    operator_registry_digest: str
    certificate_digest: str


def _macro_digest(path: tuple[str, ...]) -> str:
    return canonical_sha256(path, domain="pct-certified-macro-path-v1")[:16]


def _trace_digest(trace: SolveTrace) -> str:
    return canonical_sha256(trace, domain="pct-primitive-witness-trace-v1")


def synthesize_macro_proposals(
    calibration_goals: Sequence[GoalSpec],
    primitive_traces: Sequence[SolveTrace],
    registry: Mapping[str, OperatorSpec],
    *,
    min_distinct_goals: int = 2,
    min_length: int = 2,
    max_length: int = 4,
) -> tuple[MacroProposalSpec, ...]:
    """Synthesize inert proposals from already-discovered primitive witnesses.

    The witness and registry digests support offline auditing only. They do not
    bind the complete runtime authority described in
    ``docs/macro-authority-v0-20.md`` and therefore cannot authorize planner
    execution or efficiency credit.
    """
    calibration_ids = {goal.goal_id for goal in calibration_goals}
    support_goals: dict[tuple[str, ...], set[str]] = defaultdict(set)
    support_traces: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for trace in primitive_traces:
        if trace.goal_id not in calibration_ids:
            raise ValueError(f"non-calibration trace supplied to macro certification: {trace.goal_id}")
        if trace.final_verdict != "PASS" or not trace.verifier_chain or not trace.verifier_chain[-1].passed:
            continue
        primitive_path = tuple(
            op_id
            for op_id in trace.operator_path
            if op_id in registry and registry[op_id].execution_kind == "PRIMITIVE"
        )
        digest = _trace_digest(trace)
        for width in range(min_length, min(max_length, len(primitive_path)) + 1):
            for start in range(0, len(primitive_path) - width + 1):
                window = primitive_path[start : start + width]
                support_goals[window].add(trace.goal_id)
                support_traces[window].append(digest)

    macros: list[MacroProposalSpec] = []
    registry_digest = operator_registry_digest(registry)
    for path, goal_ids in sorted(support_goals.items(), key=lambda item: (len(item[0]), item[0])):
        if len(goal_ids) < min_distinct_goals:
            continue
        if any(op_id not in registry for op_id in path):
            continue
        first = registry[path[0]]
        last = registry[path[-1]]
        macro_id = f"CERT_MACRO:{_macro_digest(path)}"
        witness_digests = tuple(sorted(set(support_traces[path])))
        certificate_digest = _certificate_digest(
            macro_id=macro_id,
            primitive_ids=path,
            support_goal_ids=frozenset(goal_ids),
            witness_trace_digests=witness_digests,
            registry_digest=registry_digest,
        )
        macros.append(
            MacroProposalSpec(
                macro_id=macro_id,
                primitive_ids=path,
                witness_goal_ids=frozenset(goal_ids),
                witness_trace_digests=witness_digests,
                entry_input_types=first.input_types,
                terminal_output_type=last.output_type,
                terminal_representation_class=last.representation_class,
                terminal_exactness_class=last.exactness_class,
                operator_registry_digest=registry_digest,
                certificate_digest=certificate_digest,
            )
        )
    return tuple(macros)


# Compatibility names for older diagnostic imports. They denote inert
# proposals, not production-certified executable macros.
CertifiedMacroSpec = MacroProposalSpec
synthesize_certified_macros = synthesize_macro_proposals


def evaluate_macro_safety_and_efficiency(
    primitive_case: dict[str, Any],
    macro_case: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed legacy case comparison for campaign migration.

    These dictionaries omit typed runtime certificates, complete candidates and
    lineage, refusal operators, obligation witnesses, verifier/routing receipts,
    exact request/configuration/budget bindings, and two work counters.  They can
    detect an obvious rescue and describe *counterfactual* reductions, but they
    can never authorize execution or receive efficiency credit.
    """
    if type(primitive_case) is not dict or type(macro_case) is not dict:
        return {
            "goal_id": None,
            "family": None,
            "macro_rescue": False,
            "full_parity": False,
            "semantic_parity": False,
            "same_verdict": False,
            "same_observed": False,
            "same_refusal": False,
            "same_obligations": False,
            "primitive_correct": False,
            "macro_correct": False,
            "work_reduced": False,
            "credit_allowed": False,
            "state_savings": 0,
            "primitive_call_savings": 0,
            "counterfactual_state_reduction": 0,
            "counterfactual_primitive_call_reduction": 0,
            "authority_certified": False,
            "discard_reason": "UNTYPED_MACRO_CASE",
        }
    prim_verdict = primitive_case.get("verdict")
    macro_verdict = macro_case.get("verdict")
    prim_correct = primitive_case.get("correct")
    macro_correct = macro_case.get("correct")

    identities_typed = all(
        type(value) is expected
        for value, expected in (
            (prim_verdict, str),
            (macro_verdict, str),
            (prim_correct, bool),
            (macro_correct, bool),
        )
    )

    # 1. Check for MACRO_RESCUE without truthiness coercions.
    is_macro_rescue = bool(
        identities_typed
        and prim_correct is False
        and macro_correct is True
        and macro_verdict == "PASS"
    )
    
    # 2. Output and observed state equivalence
    same_verdict = (prim_verdict == macro_verdict)
    same_correctness = identities_typed and (prim_correct == macro_correct)
    same_observed = (primitive_case.get("observed") == macro_case.get("observed"))
    
    # 3. Refusal parity
    prim_refusal = primitive_case.get("refusal_reason")
    macro_refusal = macro_case.get("refusal_reason")
    same_refusal = (prim_refusal == macro_refusal)
    
    # 4. Derived obligations parity
    prim_obligations = primitive_case.get("satisfied_derived_types")
    macro_obligations = macro_case.get("satisfied_derived_types")
    same_obligations = (prim_obligations == macro_obligations)

    semantic_parity = (
        identities_typed
        and same_verdict
        and same_correctness
        and same_observed
        and same_refusal
        and same_obligations
        and not is_macro_rescue
    )

    primitive_expanded = primitive_case.get("expanded_state_count")
    macro_expanded = macro_case.get("expanded_state_count")
    primitive_calls = primitive_case.get("primitive_execution_count")
    macro_calls = macro_case.get("primitive_execution_count")
    counters_typed = all(
        type(value) is int and value >= 0
        for value in (
            primitive_expanded,
            macro_expanded,
            primitive_calls,
            macro_calls,
        )
    )
    work_reduced = bool(
        counters_typed
        and (
            macro_expanded < primitive_expanded
            or macro_calls < primitive_calls
        )
    )
    counterfactual_state_reduction = (
        max(0, primitive_expanded - macro_expanded) if counters_typed else 0
    )
    counterfactual_call_reduction = (
        max(0, primitive_calls - macro_calls) if counters_typed else 0
    )

    return {
        "goal_id": primitive_case.get("goal_id"),
        "family": primitive_case.get("family"),
        "macro_rescue": is_macro_rescue,
        "full_parity": False,
        "semantic_parity": semantic_parity,
        "same_verdict": same_verdict,
        "same_observed": same_observed,
        "same_refusal": same_refusal,
        "same_obligations": same_obligations,
        "primitive_correct": prim_correct,
        "macro_correct": macro_correct,
        "work_reduced": work_reduced,
        "credit_allowed": False,
        "state_savings": 0,
        "primitive_call_savings": 0,
        "counterfactual_state_reduction": counterfactual_state_reduction,
        "counterfactual_primitive_call_reduction": counterfactual_call_reduction,
        "authority_certified": False,
        "discard_reason": "MACRO_EXECUTABLE_AUTHORITY_UNAVAILABLE",
    }
