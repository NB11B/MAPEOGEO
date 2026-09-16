from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

import networkx as nx

from .canonical import canonical_sha256
from .model import Artifact, ArtifactType, GoalSpec, SolveTrace
from .operators import OperatorSpec


class InfeasibleTypeInferenceError(ValueError):
    refusal_code = "INFEASIBLE_TYPE_INFERENCE"


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
class RoutingDecision:
    inferred_root_types: tuple[tuple[str, ArtifactType], ...]
    ordered_operator_ids: tuple[str, ...]
    ambiguous_input_keys: tuple[str, ...]
    compatibility_model_digest: str
    decision_digest: str


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

    @property
    def model_digest(self) -> str:
        return canonical_sha256(
            {
                "goal_ids": self.goal_ids,
                "operator_contexts": self.operator_contexts,
                "operator_support": self.operator_support,
                "type_contexts": self.type_contexts,
                "type_support": self.type_support,
                "type_max_count": self.type_max_count,
            },
            domain="pct-compatibility-model-v1",
        )

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
        state = artifacts or {"input": artifact}
        resolved, _ = self._joint_resolution(state)
        key = next(
            key
            for key, candidate in state.items()
            if candidate is artifact
        ) if artifacts is not None else "input"
        return resolved[key].semantic_type

    def _assignment_costs(
        self,
        artifacts: Mapping[str, Artifact],
        semantic_types: tuple[str, ...],
    ) -> dict[tuple[str, str], int]:
        max_support = max(
            (int(self.type_support.get(semantic_type, 0)) for semantic_type in semantic_types),
            default=0,
        )
        scale = len(artifacts) * max(1, max_support) + 1
        return {
            (key, semantic_type): (
                self._type_rank(artifact, artifacts, semantic_type)[0] * scale
                + max_support
                - int(self.type_support.get(semantic_type, 0))
            )
            for key, artifact in sorted(artifacts.items())
            for semantic_type in semantic_types
        }

    def _minimum_assignment(
        self,
        artifacts: Mapping[str, Artifact],
        semantic_types: tuple[str, ...],
        costs: Mapping[tuple[str, str], int],
        forced: Mapping[str, str],
    ) -> tuple[int, dict[str, str]] | None:
        capacities: dict[str, int] = {}
        for semantic_type in semantic_types:
            capacity = self.type_max_count.get(semantic_type)
            if type(capacity) is not int or capacity <= 0:
                continue
            capacities[semantic_type] = capacity

        fixed_cost = 0
        assignment = dict(forced)
        for key, semantic_type in sorted(forced.items()):
            if key not in artifacts or capacities.get(semantic_type, 0) <= 0:
                return None
            capacities[semantic_type] -= 1
            fixed_cost += costs[(key, semantic_type)]

        remaining_keys = tuple(key for key in sorted(artifacts) if key not in forced)
        if sum(capacities.values()) < len(remaining_keys):
            return None
        if not remaining_keys:
            return fixed_cost, assignment

        source = ("source", "")
        sink = ("sink", "")
        graph = nx.DiGraph()
        graph.add_node(source, demand=-len(remaining_keys))
        graph.add_node(sink, demand=len(remaining_keys))
        for key in remaining_keys:
            root_node = ("root", key)
            graph.add_node(root_node, demand=0)
            graph.add_edge(source, root_node, capacity=1, weight=0)
            for semantic_type in semantic_types:
                if capacities.get(semantic_type, 0) <= 0:
                    continue
                type_node = ("type", semantic_type)
                graph.add_node(type_node, demand=0)
                graph.add_edge(
                    root_node,
                    type_node,
                    capacity=1,
                    weight=costs[(key, semantic_type)],
                )
        for semantic_type in semantic_types:
            capacity = capacities.get(semantic_type, 0)
            if capacity <= 0:
                continue
            graph.add_edge(("type", semantic_type), sink, capacity=capacity, weight=0)
        try:
            flow_cost, flow = nx.network_simplex(graph)
        except (nx.NetworkXError, nx.NetworkXUnfeasible):
            return None
        for key in remaining_keys:
            root_node = ("root", key)
            chosen = [
                node[1]
                for node, amount in flow[root_node].items()
                if node[0] == "type" and amount == 1
            ]
            if len(chosen) != 1:
                return None
            assignment[key] = chosen[0]
        return fixed_cost + int(flow_cost), assignment

    def _joint_resolution(
        self,
        artifacts: Mapping[str, Artifact],
    ) -> tuple[dict[str, Artifact], tuple[str, ...]]:
        if not artifacts:
            raise InfeasibleTypeInferenceError("no root artifacts supplied for inference")
        semantic_types = tuple(
            sorted(
                semantic_type
                for semantic_type, contexts in self.type_contexts.items()
                if contexts and self.type_max_count.get(semantic_type, 0) > 0
            )
        )
        if not semantic_types:
            raise InfeasibleTypeInferenceError("compatibility model has no supported semantic types")
        costs = self._assignment_costs(artifacts, semantic_types)
        optimum = self._minimum_assignment(
            artifacts,
            semantic_types,
            costs,
            forced={},
        )
        if optimum is None:
            raise InfeasibleTypeInferenceError(
                "compatibility type capacities cannot cover all root artifacts"
            )
        optimum_cost, _ = optimum

        possible_types: dict[str, set[str]] = {key: set() for key in artifacts}
        for key in sorted(artifacts):
            for semantic_type in semantic_types:
                candidate = self._minimum_assignment(
                    artifacts,
                    semantic_types,
                    costs,
                    forced={key: semantic_type},
                )
                if candidate is not None and candidate[0] == optimum_cost:
                    possible_types[key].add(semantic_type)
        if any(not rows for rows in possible_types.values()):
            raise InfeasibleTypeInferenceError("no optimal type assignment covers every root")

        # Select the lexicographically first globally optimal assignment while
        # preserving all earlier choices. This makes the receipt independent of
        # caller mapping order without pretending equal optima are unambiguous.
        forced: dict[str, str] = {}
        for key in sorted(artifacts):
            for semantic_type in sorted(possible_types[key]):
                candidate_forced = {**forced, key: semantic_type}
                candidate = self._minimum_assignment(
                    artifacts,
                    semantic_types,
                    costs,
                    forced=candidate_forced,
                )
                if candidate is not None and candidate[0] == optimum_cost:
                    forced[key] = semantic_type
                    break
            if key not in forced:
                raise InfeasibleTypeInferenceError("failed to construct deterministic optimum")

        resolved = {
            key: replace(artifact, semantic_type=forced[key])
            for key, artifact in sorted(artifacts.items())
        }
        ambiguous = tuple(
            key for key in sorted(artifacts) if len(possible_types[key]) > 1
        )
        return resolved, ambiguous

    def resolve_input_types(self, artifacts: Mapping[str, Artifact]) -> dict[str, Artifact]:
        """Jointly infer original-input labels under a stable original-input context.

        Derived artifacts must not perturb the structural context used to retype the
        original problem statement. Without this separation, a correct first
        derivation can change the inferred input labels and make a valid multi-step
        path disappear on its second step.
        """
        resolved, _ = self._joint_resolution(artifacts)
        return resolved

    def ambiguous_input_keys(self, artifacts: Mapping[str, Artifact]) -> tuple[str, ...]:
        _, ambiguous = self._joint_resolution(artifacts)
        return ambiguous

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
        resolved = self.resolve_input_types(artifacts)
        return tuple(sorted(registry, key=lambda operator_id: self.rank_operator(operator_id, resolved)))

    def routing_decision(
        self,
        artifacts: Mapping[str, Artifact],
        registry: Mapping[str, OperatorSpec],
    ) -> RoutingDecision:
        return authoritative_routing_decision(self, artifacts, registry)


def authoritative_routing_decision(
    model: CompatibilityModel,
    artifacts: Mapping[str, Artifact],
    registry: Mapping[str, OperatorSpec],
) -> RoutingDecision:
    """Derive the unique receipt directly from frozen model state.

    The planner treats ``CompatibilityModel.routing_decision`` as an untrusted
    adapter boundary and compares its result with this independent derivation.
    Keeping the derivation outside that overridable method prevents a caller
    from laundering changed inferred labels or suppressed ambiguity merely by
    recomputing the public receipt hash.
    """

    if type(model) is not CompatibilityModel:
        raise TypeError("model must be an exact CompatibilityModel")
    resolved, ambiguous = CompatibilityModel._joint_resolution(model, artifacts)
    inferred_root_types = tuple(
        (key, artifact.artifact_type) for key, artifact in sorted(resolved.items())
    )
    ordered_operator_ids = tuple(
        sorted(
            registry,
            key=lambda operator_id: CompatibilityModel.rank_operator(
                model,
                operator_id,
                resolved,
            ),
        )
    )
    model_digest = CompatibilityModel.model_digest.__get__(model, CompatibilityModel)
    decision_digest = canonical_sha256(
        {
            "inferred_root_types": inferred_root_types,
            "ordered_operator_ids": ordered_operator_ids,
            "ambiguous_input_keys": ambiguous,
            "compatibility_model_digest": model_digest,
        },
        domain="pct-routing-decision-v1",
    )
    return RoutingDecision(
        inferred_root_types=inferred_root_types,
        ordered_operator_ids=ordered_operator_ids,
        ambiguous_input_keys=ambiguous,
        compatibility_model_digest=model_digest,
        decision_digest=decision_digest,
    )
