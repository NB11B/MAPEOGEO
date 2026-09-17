from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .canonical import canonical_sha256
from .model import GoalSpec, SolveTrace
from .operators import OperatorSpec, operator_registry_digest


@dataclass(frozen=True)
class MacroSpec:
    """A calibration-derived proposal, never executable solver authority.

    The digest fields identify the proposal and its calibration witnesses.  They
    do not identify all Python code, globals, transitive dependencies, routing
    state, or request data needed to authorize an optimized execution.
    """

    macro_id: str
    primitive_ids: tuple[str, ...]
    support_goal_ids: frozenset[str]
    entry_input_types: tuple[str, ...]
    terminal_output_type: str
    terminal_representation_class: str
    terminal_exactness_class: str
    witness_trace_digests: tuple[str, ...] = ()
    operator_registry_digest: str = ""
    certificate_digest: str = ""


@dataclass(frozen=True)
class MacroDiscard:
    proposal_id: str
    reason: str


@dataclass(frozen=True)
class MacroAuditReport:
    """Non-authoritative side-channel result.

    No replay is attempted until the repository has a complete executable
    authority and an immutable request/receipt schema.  Consequently every
    proposal is discarded, no counterfactual is credited, and the charged work
    is the full authoritative primitive work.
    """

    authoritative_trace_digest: str
    proposal_count: int
    replay_count: int
    counterfactual_credit_count: int
    actual_work_savings: int
    total_work_charged: int
    discarded: tuple[MacroDiscard, ...]


def _macro_id(path: tuple[str, ...]) -> str:
    digest = canonical_sha256(path, domain="pct-macro-path-v1")[:16]
    return f"MACRO:{digest}"


def _trace_digest(trace: SolveTrace) -> str:
    return canonical_sha256(trace, domain="pct-primitive-witness-trace-v1")


def _certificate_digest(
    *,
    macro_id: str,
    primitive_ids: tuple[str, ...],
    support_goal_ids: frozenset[str],
    witness_trace_digests: tuple[str, ...],
    registry_digest: str,
) -> str:
    return canonical_sha256(
        {
            "macro_id": macro_id,
            "primitive_ids": primitive_ids,
            "support_goal_ids": support_goal_ids,
            "witness_trace_digests": witness_trace_digests,
            "operator_registry_digest": registry_digest,
        },
        domain="pct-macro-certificate-v1",
    )


def _valid_digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def validate_macro_proposal(
    macro: object,
    registry: Mapping[str, OperatorSpec],
) -> tuple[bool, str]:
    """Validate proposal identity only; this never grants execution authority."""

    if type(macro) is not MacroSpec:
        return False, "UNTYPED_MACRO_PROPOSAL"
    if type(macro.macro_id) is not str or not macro.macro_id:
        return False, "INVALID_MACRO_ID"
    if type(macro.primitive_ids) is not tuple or not macro.primitive_ids or any(
        type(operator_id) is not str or not operator_id
        for operator_id in macro.primitive_ids
    ):
        return False, "INVALID_MACRO_PRIMITIVE_PATH"
    if type(macro.support_goal_ids) is not frozenset or not macro.support_goal_ids or any(
        type(goal_id) is not str or not goal_id
        for goal_id in macro.support_goal_ids
    ):
        return False, "INVALID_MACRO_SUPPORT"
    if (
        type(macro.witness_trace_digests) is not tuple
        or not macro.witness_trace_digests
        or any(not _valid_digest(digest) for digest in macro.witness_trace_digests)
    ):
        return False, "INVALID_MACRO_WITNESSES"
    if type(registry) is not dict:
        return False, "UNTYPED_OPERATOR_REGISTRY"
    try:
        expected_registry = operator_registry_digest(registry)
    except Exception as error:
        return False, f"INVALID_OPERATOR_REGISTRY:{type(error).__name__}"
    if macro.operator_registry_digest != expected_registry:
        return False, "MACRO_REGISTRY_DIGEST_MISMATCH"
    if any(
        operator_id not in registry or registry[operator_id].execution_kind != "PRIMITIVE"
        for operator_id in macro.primitive_ids
    ):
        return False, "INVALID_MACRO_PRIMITIVE_PATH"
    first = registry[macro.primitive_ids[0]]
    last = registry[macro.primitive_ids[-1]]
    if (
        macro.entry_input_types != first.input_types
        or macro.terminal_output_type != last.output_type
        or macro.terminal_representation_class != last.representation_class
        or macro.terminal_exactness_class != last.exactness_class
    ):
        return False, "MACRO_INTERFACE_MISMATCH"
    expected_certificate = _certificate_digest(
        macro_id=macro.macro_id,
        primitive_ids=macro.primitive_ids,
        support_goal_ids=macro.support_goal_ids,
        witness_trace_digests=macro.witness_trace_digests,
        registry_digest=macro.operator_registry_digest,
    )
    if macro.certificate_digest != expected_certificate:
        return False, "MACRO_PROPOSAL_DIGEST_MISMATCH"
    return True, ""


def validate_runtime_macro(
    macro: object,
    registry: Mapping[str, OperatorSpec],
) -> tuple[bool, str]:
    """Fail closed: a ``MacroSpec`` is not executable runtime authority.

    A sound runtime certificate must bind the complete executable closure, the
    exact request (including routing configuration and budget), and complete
    replay receipts.  ``MacroSpec`` does not contain those fields.  Treating its
    calibration digest as authority would make a forged or stale object capable
    of changing a solve result.
    """

    proposal_valid, reason = validate_macro_proposal(macro, registry)
    if not proposal_valid:
        return False, reason
    return False, "MACRO_EXECUTABLE_AUTHORITY_UNAVAILABLE"


def _trace_work(trace: SolveTrace) -> int | None:
    counters = (
        trace.expanded_state_count,
        trace.attempted_operator_count,
        trace.primitive_execution_count,
        trace.verifier_execution_count,
    )
    if any(type(value) is not int or value < 0 for value in counters):
        return None
    return sum(counters)


def audit_macro_proposals(
    primitive_trace: SolveTrace,
    proposals: Iterable[object],
    registry: Mapping[str, OperatorSpec],
) -> MacroAuditReport:
    """Inspect macro proposals after solving without executing or crediting them.

    This function is deliberately outside :func:`planner.solve`.  It cannot
    alter the authoritative trace.  It also makes no speedup claim: if replay is
    added later, reported total work must charge both baseline and replay work;
    any smaller replay search would be labelled counterfactual compression.
    """

    if type(primitive_trace) is not SolveTrace:
        return MacroAuditReport(
            "", 0, 0, 0, 0, 0,
            (MacroDiscard("", "UNTYPED_PRIMITIVE_TRACE"),),
        )
    discarded: list[MacroDiscard] = []
    try:
        trace_digest = canonical_sha256(
            primitive_trace,
            domain="pct-authoritative-trace-v1",
        )
    except Exception:
        trace_digest = ""
        discarded.append(MacroDiscard("", "NONCANONICAL_PRIMITIVE_TRACE"))
    work = _trace_work(primitive_trace)
    if work is None:
        discarded.append(MacroDiscard("", "INVALID_PRIMITIVE_WORK_COUNTERS"))
        work = 0
    try:
        proposal_rows = tuple(proposals)
    except Exception as error:
        return MacroAuditReport(
            trace_digest,
            0,
            0,
            0,
            0,
            work,
            tuple(discarded)
            + (MacroDiscard("", f"MACRO_PROPOSAL_ITERATION_FAILED:{type(error).__name__}"),),
        )

    for proposal in proposal_rows:
        if type(proposal) is not MacroSpec:
            discarded.append(MacroDiscard("", "UNTYPED_MACRO_PROPOSAL"))
            continue
        valid, reason = validate_runtime_macro(proposal, registry)
        discarded.append(MacroDiscard(proposal.macro_id, reason if not valid else "MACRO_REPLAY_NOT_RUN"))

    return MacroAuditReport(
        authoritative_trace_digest=trace_digest,
        proposal_count=len(proposal_rows),
        replay_count=0,
        counterfactual_credit_count=0,
        actual_work_savings=0,
        total_work_charged=work,
        discarded=tuple(discarded),
    )


def synthesize_macros(
    calibration_goals: Sequence[GoalSpec],
    traces: Sequence[SolveTrace],
    registry: Mapping[str, OperatorSpec],
    *,
    min_distinct_goals: int = 2,
    min_length: int = 2,
    max_length: int = 4,
) -> tuple[MacroSpec, ...]:
    """Discover repeated verified primitive windows in calibration traces only.

    Macros are aliases for already verified primitive sequences; they add no new
    mathematics. A sequence must recur in distinct calibration goals and every
    contributing trace must have closed with a passing independent verifier.
    """
    calibration_ids = {goal.goal_id for goal in calibration_goals}
    support: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for trace in traces:
        if trace.goal_id not in calibration_ids:
            raise ValueError(f"non-calibration trace supplied to macro synthesis: {trace.goal_id}")
        if trace.final_verdict != "PASS" or not trace.verifier_chain or not trace.verifier_chain[-1].passed:
            continue
        primitive_path = tuple(
            operator_id
            for operator_id in trace.operator_path
            if operator_id in registry and registry[operator_id].execution_kind == "PRIMITIVE"
        )
        for width in range(min_length, min(max_length, len(primitive_path)) + 1):
            for start in range(0, len(primitive_path) - width + 1):
                window = primitive_path[start : start + width]
                support[window].add(trace.goal_id)

    macros: list[MacroSpec] = []
    registry_digest = operator_registry_digest(registry)
    for path, goal_ids in sorted(support.items(), key=lambda item: (len(item[0]), item[0])):
        if len(goal_ids) < min_distinct_goals:
            continue
        if any(operator_id not in registry for operator_id in path):
            continue
        first = registry[path[0]]
        last = registry[path[-1]]
        macro_id = _macro_id(path)
        witness_trace_digests = tuple(
            sorted(
                _trace_digest(trace)
                for trace in traces
                if trace.goal_id in goal_ids
                and trace.final_verdict == "PASS"
                and all(operator_id in trace.operator_path for operator_id in path)
            )
        )
        certificate_digest = _certificate_digest(
            macro_id=macro_id,
            primitive_ids=path,
            support_goal_ids=frozenset(goal_ids),
            witness_trace_digests=witness_trace_digests,
            registry_digest=registry_digest,
        )
        macros.append(
            MacroSpec(
                macro_id=macro_id,
                primitive_ids=path,
                support_goal_ids=frozenset(goal_ids),
                entry_input_types=first.input_types,
                terminal_output_type=last.output_type,
                terminal_representation_class=last.representation_class,
                terminal_exactness_class=last.exactness_class,
                witness_trace_digests=witness_trace_digests,
                operator_registry_digest=registry_digest,
                certificate_digest=certificate_digest,
            )
        )
    return tuple(macros)
