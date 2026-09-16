from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
from typing import Mapping, Sequence

from .model import GoalSpec, SolveTrace
from .operators import OperatorSpec


@dataclass(frozen=True)
class MacroSpec:
    macro_id: str
    primitive_ids: tuple[str, ...]
    support_goal_ids: frozenset[str]
    entry_input_types: tuple[str, ...]
    terminal_output_type: str
    terminal_representation_class: str
    terminal_exactness_class: str


def _macro_id(path: tuple[str, ...]) -> str:
    digest = hashlib.sha256("->".join(path).encode("utf-8")).hexdigest()[:16]
    return f"MACRO:{digest}"


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
        primitive_path = tuple(operator_id for operator_id in trace.operator_path if operator_id in registry)
        for width in range(min_length, min(max_length, len(primitive_path)) + 1):
            for start in range(0, len(primitive_path) - width + 1):
                window = primitive_path[start : start + width]
                support[window].add(trace.goal_id)

    macros: list[MacroSpec] = []
    for path, goal_ids in sorted(support.items(), key=lambda item: (len(item[0]), item[0])):
        if len(goal_ids) < min_distinct_goals:
            continue
        if any(operator_id not in registry for operator_id in path):
            continue
        first = registry[path[0]]
        last = registry[path[-1]]
        macros.append(
            MacroSpec(
                macro_id=_macro_id(path),
                primitive_ids=path,
                support_goal_ids=frozenset(goal_ids),
                entry_input_types=first.input_types,
                terminal_output_type=last.output_type,
                terminal_representation_class=last.representation_class,
                terminal_exactness_class=last.exactness_class,
            )
        )
    return tuple(macros)
