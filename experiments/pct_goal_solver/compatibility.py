from __future__ import annotations

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
        # Low-cardinality structural metadata is useful for role inference while
        # avoiding raw mathematical answer values.
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


@dataclass(frozen=True)
class CompatibilityModel:
    goal_ids: frozenset[str]
    operator_contexts: Mapping[str, tuple[frozenset[str], ...]]
    operator_support: Mapping[str, int]
    type_contexts: Mapping[str, tuple[frozenset[str], ...]]
    type_support: Mapping[str, int]

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

        # Semantic labels are available only during calibration.  They supervise a
        # structural type model; inference later uses descriptors only.
        for goal in calibration_goals:
            for artifact in goal.inputs.values():
                type_contexts.setdefault(artifact.semantic_type, []).append(artifact_descriptors(artifact))

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
        )

    def infer_semantic_type(self, artifact: Artifact) -> str:
        """Infer an input type from calibration structure, never from its label."""
        current = artifact_descriptors(artifact)
        candidates: list[tuple[int, int, str]] = []
        for semantic_type, contexts in self.type_contexts.items():
            distance = min(len(current.symmetric_difference(context)) for context in contexts)
            candidates.append((distance, -int(self.type_support.get(semantic_type, 0)), semantic_type))
        if not candidates:
            return artifact.semantic_type
        return min(candidates)[2]

    def resolve_input_types(self, artifacts: Mapping[str, Artifact]) -> dict[str, Artifact]:
        """Replace original-input labels with structurally inferred labels.

        Derived artifacts retain the output contract of the operator that created
        them.  Original inputs are always retyped, even when their supplied label
        is correct, so INFERRED/HYBRID routing cannot silently consume explicit
        input semantic labels.
        """
        resolved: dict[str, Artifact] = {}
        for key, artifact in artifacts.items():
            if artifact.provenance:
                resolved[key] = artifact
                continue
            inferred = self.infer_semantic_type(artifact)
            resolved[key] = replace(artifact, semantic_type=inferred)
        return resolved

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
        # The planner passes a mutable per-state mapping.  Resolve original input
        # types here before invocation selection; this makes inferred typing an
        # actual execution condition rather than merely a ranking heuristic.
        resolved = self.resolve_input_types(artifacts)
        if isinstance(artifacts, MutableMapping):
            artifacts.clear()
            artifacts.update(resolved)
            ranked_artifacts: Mapping[str, Artifact] = artifacts
        else:
            ranked_artifacts = resolved
        return tuple(sorted(registry, key=lambda operator_id: self.rank_operator(operator_id, ranked_artifacts)))
