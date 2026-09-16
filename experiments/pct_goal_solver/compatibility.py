from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Mapping, MutableMapping, Sequence

from .model import Artifact, GoalSpec, SolveTrace
from .operators import OperatorSpec


def _shape_token(value: Any) -> str:
    if isinstance(value, dict):
        return f"map:{len(value)}"
    if isinstance(value, (tuple, list)):
        if not value:
            return "sequence:0"
        first = value[0]
        if isinstance(first, (tuple, list)):
            width = len(first)
            return f"nested:{len(value)}x{width}"
        return f"sequence:{len(value)}"
    if isinstance(value, bool):
        return "scalar:bool"
    if isinstance(value, int):
        return "scalar:int"
    if isinstance(value, float):
        return "scalar:float"
    if isinstance(value, str):
        return "scalar:str"
    return f"object:{type(value).__name__.lower()}"


def artifact_descriptors(artifact: Artifact) -> frozenset[str]:
    """Structural artifact features with semantic labels deliberately omitted."""
    tokens = {
        f"rep:{artifact.representation_class}",
        f"exact:{artifact.exactness_class}",
        f"shape:{_shape_token(artifact.value)}",
    }
    for key, value in artifact.metadata:
        tokens.add(f"meta:{key}")
        # Low-cardinality role metadata is structural. Raw mathematical values are
        # intentionally excluded so type inference cannot memorize answers.
        if isinstance(value, (str, bool)):
            tokens.add(f"meta_value:{key}:{value}")
    return frozenset(tokens)


def structural_descriptors(artifacts: Mapping[str, Artifact]) -> frozenset[str]:
    """Return compatibility features that deliberately omit semantic type names."""
    tokens: set[str] = {f"artifact_count:{len(artifacts)}"}
    representation_counts: dict[str, int] = {}
    exactness_counts: dict[str, int] = {}
    for artifact in artifacts.values():
        representation_counts[artifact.representation_class] = representation_counts.get(artifact.representation_class, 0) + 1
        exactness_counts[artifact.exactness_class] = exactness_counts.get(artifact.exactness_class, 0) + 1
        tokens.update(artifact_descriptors(artifact))
    for name, count in sorted(representation_counts.items()):
        tokens.add(f"rep_count:{name}:{count}")
    for name, count in sorted(exactness_counts.items()):
        tokens.add(f"exact_count:{name}:{count}")
    return frozenset(tokens)


def _contextual_artifact_descriptors(
    artifact: Artifact,
    artifacts: Mapping[str, Artifact],
) -> frozenset[str]:
    local = set(artifact_descriptors(artifact))
    local.update(f"context:{token}" for token in structural_descriptors(artifacts))
    return frozenset(local)


@dataclass(frozen=True)
class CompatibilityModel:
    goal_ids: frozenset[str]
    operator_contexts: Mapping[str, tuple[frozenset[str], ...]]
    operator_support: Mapping[str, int]
    type_contexts: Mapping[str, tuple[frozenset[str], ...]]
    type_support: Mapping[str, int]
    type_max_count: Mapping[str, int]

    @classmethod
    def fit(
        cls,
        calibration_goals: Sequence[GoalSpec],
        traces: Sequence[SolveTrace],
        registry: Mapping[str, OperatorSpec],
    ) -> "CompatibilityModel":
        by_goal = {goal.goal_id: goal for goal in calibration_goals}
        contexts: dict[str, list[frozenset[str]]] = {operator_id: [] for operator_id in registry}
        type_contexts: dict[str, list[frozenset[str]]] = {}
        type_max_count: dict[str, int] = {}

        # Semantic labels are available only during calibration. They supervise a
        # structural type model; sealed inference later sees descriptors only.
        for goal in calibration_goals:
            counts = Counter(artifact.semantic_type for artifact in goal.inputs.values())
            for semantic_type, count in counts.items():
                type_max_count[semantic_type] = max(type_max_count.get(semantic_type, 0), count)
            for artifact in goal.inputs.values():
                type_contexts.setdefault(artifact.semantic_type, []).append(
                    _contextual_artifact_descriptors(artifact, goal.inputs)
                )

        for trace in traces:
            goal = by_goal.get(trace.goal_id)
            if goal is None:
                raise ValueError(f"trace is not from supplied calibration set: {trace.goal_id}")
            descriptor = structural_descriptors(goal.solver_visible().inputs)
            for operator_id in trace.operator_path:
                if operator_id in registry:
                    contexts[operator_id].append(descriptor)

        frozen = {
            operator_id: tuple(rows)
            for operator_id, rows in contexts.items()
            if rows
        }
        frozen_types = {
            semantic_type: tuple(rows)
            for semantic_type, rows in type_contexts.items()
            if rows
        }
        return cls(
            goal_ids=frozenset(by_goal),
            operator_contexts=frozen,
            operator_support={operator_id: len(rows) for operator_id, rows in frozen.items()},
            type_contexts=frozen_types,
            type_support={semantic_type: len(rows) for semantic_type, rows in frozen_types.items()},
            type_max_count=dict(type_max_count),
        )

    def _type_rank(
        self,
        artifact: Artifact,
        artifacts: Mapping[str, Artifact],
        semantic_type: str,
    ) -> tuple[int, int, str]:
        current = _contextual_artifact_descriptors(artifact, artifacts)
        contexts = self.type_contexts.get(semantic_type, ())
        if not contexts:
            return (10_000, 0, semantic_type)
        distance = min(len(current.symmetric_difference(context)) for context in contexts)
        return (distance, -int(self.type_support.get(semantic_type, 0)), semantic_type)

    def infer_semantic_type(
        self,
        artifact: Artifact,
        artifacts: Mapping[str, Artifact] | None = None,
    ) -> str:
        """Infer one input type from calibration structure, never from its label."""
        state = artifacts or {"input": artifact}
        candidates = [self._type_rank(artifact, state, semantic_type) for semantic_type in self.type_contexts]
        if not candidates:
            return artifact.semantic_type
        return min(candidates)[2]

    def resolve_input_types(self, artifacts: Mapping[str, Artifact]) -> dict[str, Artifact]:
        """Jointly infer original-input labels under calibration cardinalities.

        Global context distinguishes structurally similar values used in different
        goal families. A learned per-type capacity prevents identical artifacts in
        one state from all collapsing onto the same label (for example the two
        degree maps in a chain-map problem). Derived artifacts retain the output
        contract of the operator that created them.
        """
        resolved: dict[str, Artifact] = {}
        remaining = dict(self.type_max_count)
        originals = [(key, artifact) for key, artifact in artifacts.items() if not artifact.provenance]

        for key, artifact in artifacts.items():
            if artifact.provenance:
                resolved[key] = artifact

        # Harder/less ambiguous assignments first: prefer artifacts whose best
        # structural match is separated furthest from the runner-up. Input order is
        # retained only as the final deterministic tie-break.
        ranked_originals: list[tuple[int, int, str, Artifact, list[tuple[int, int, str]]]] = []
        for order, (key, artifact) in enumerate(originals):
            ranks = sorted(self._type_rank(artifact, artifacts, semantic_type) for semantic_type in self.type_contexts)
            margin = (ranks[1][0] - ranks[0][0]) if len(ranks) > 1 else 10_000
            ranked_originals.append((-margin, order, key, artifact, ranks))

        for _, _, key, artifact, ranks in sorted(ranked_originals):
            chosen = None
            for _, _, semantic_type in ranks:
                if remaining.get(semantic_type, 0) > 0:
                    chosen = semantic_type
                    break
            if chosen is None:
                chosen = ranks[0][2] if ranks else artifact.semantic_type
            remaining[chosen] = max(0, remaining.get(chosen, 0) - 1)
            resolved[key] = replace(artifact, semantic_type=chosen)

        # Preserve the original state iteration order.
        return {key: resolved[key] for key in artifacts}

    def rank_operator(self, operator_id: str, artifacts: Mapping[str, Artifact]) -> tuple[int, int, str]:
        current = structural_descriptors(artifacts)
        contexts = self.operator_contexts.get(operator_id, ())
        if not contexts:
            return (10_000, 0, operator_id)
        distance = min(len(current.symmetric_difference(context)) for context in contexts)
        return (distance, -int(self.operator_support.get(operator_id, 0)), operator_id)

    def ordered_operator_ids(
        self,
        registry: Mapping[str, OperatorSpec],
        artifacts: Mapping[str, Artifact],
    ) -> tuple[str, ...]:
        # The planner passes a mutable per-state mapping. Resolve original input
        # types before invocation selection; inferred typing is therefore an
        # execution condition, not merely an operator-ranking heuristic.
        resolved = self.resolve_input_types(artifacts)
        if isinstance(artifacts, MutableMapping):
            artifacts.clear()
            artifacts.update(resolved)
            ranked_artifacts: Mapping[str, Artifact] = artifacts
        else:
            ranked_artifacts = resolved
        return tuple(sorted(registry, key=lambda operator_id: self.rank_operator(operator_id, ranked_artifacts)))
