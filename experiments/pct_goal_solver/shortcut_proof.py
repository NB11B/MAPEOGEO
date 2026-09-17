"""Finite, replayable structural proofs for candidate-lineage obligations.

This module proves a deliberately structural claim.  It computes the closure of
the complete typed operator hypergraph while tracking (a) which named problem
roots reach each artifact and (b) how far an ordered lineage obligation has
advanced along an actual ancestor chain.  Applicability predicates and values
are intentionally over-approximated: an operator whose port types can be met is
treated as reachable.  Consequently, ``PROVED`` is conservative -- it means
that even this larger structural search space has no target shortcut.

The SHA-256 values emitted here are deterministic identities, not signatures or
authorization.  Validation always recomputes the closure from the live registry
contract and its implementation digests.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from enum import Enum
from fractions import Fraction
import hashlib
import itertools
import json
import math
from typing import Any, Mapping, Sequence


_EXACTNESS_CLASSES = frozenset({"EXACT", "SYMBOLIC", "NUMERICAL"})


@dataclass(frozen=True, order=True)
class TypeNode:
    semantic_type: str
    representation_class: str
    exactness_class: str

    def __post_init__(self) -> None:
        if type(self.semantic_type) is not str or not self.semantic_type:
            raise ValueError("semantic_type must be a nonempty string")
        if type(self.representation_class) is not str or not self.representation_class:
            raise ValueError("representation_class must be a nonempty string")
        if self.exactness_class not in _EXACTNESS_CLASSES:
            raise ValueError(f"unknown exactness class: {self.exactness_class}")


@dataclass(frozen=True)
class LineageObligation:
    required_input_keys: frozenset[str]
    ordered_stage_types: tuple[TypeNode, ...]
    stage_required_input_keys: tuple[frozenset[str], ...]

    def __post_init__(self) -> None:
        if not self.required_input_keys:
            raise ValueError("lineage obligation must name at least one required root")
        if any(type(key) is not str or not key for key in self.required_input_keys):
            raise ValueError("required root keys must be nonempty strings")
        if not self.ordered_stage_types:
            raise ValueError("lineage obligation must contain at least one ordered stage")
        if any(not isinstance(stage, TypeNode) for stage in self.ordered_stage_types):
            raise TypeError("ordered stages must be TypeNode values")
        if len(self.stage_required_input_keys) != len(self.ordered_stage_types):
            raise ValueError("every ordered stage must have a root requirement")
        for required in self.stage_required_input_keys:
            if not required:
                raise ValueError("each ordered stage must be anchored to at least one root")
            if any(type(key) is not str or not key for key in required):
                raise ValueError("stage root keys must be nonempty strings")
            if not required <= self.required_input_keys:
                raise ValueError("stage roots must be included in the final required roots")


class ProofStatus(str, Enum):
    PROVED = "PROVED"
    REFUTED = "REFUTED"
    UNREACHABLE = "UNREACHABLE"


@dataclass(frozen=True)
class WitnessNode:
    node_id: str
    artifact_type: TypeNode
    root_keys: frozenset[str]
    stage_progress: int
    operator_id: str | None
    input_node_ids: tuple[str, ...]


@dataclass(frozen=True)
class LineageWitness:
    nodes: tuple[WitnessNode, ...]
    final_node_id: str
    final_root_keys: frozenset[str]
    final_stage_progress: int

    @property
    def operator_path(self) -> tuple[str, ...]:
        return tuple(node.operator_id for node in self.nodes if node.operator_id is not None)


@dataclass(frozen=True)
class LineageProof:
    status: ProofStatus
    registry_digest: str
    goal_contract_digest: str
    obligation_digest: str
    explored_state_count: int
    safe_witness: LineageWitness | None
    counterexample: LineageWitness | None
    reason: str
    proof_digest: str


@dataclass(frozen=True)
class _Edge:
    operator_id: str
    input_ports: tuple[tuple[str, TypeNode], ...]
    output: TypeNode
    implementation_digest: str
    execution_kind: str


@dataclass(frozen=True)
class _Recipe:
    final: WitnessNode
    nodes: tuple[WitnessNode, ...]

    @property
    def length(self) -> int:
        return sum(node.operator_id is not None for node in self.nodes)


_StateKey = tuple[TypeNode, frozenset[str], int]


def _type_node(value: object, *, field: str) -> TypeNode:
    if isinstance(value, TypeNode):
        return value
    try:
        semantic_type = getattr(value, "semantic_type")
        representation_class = getattr(value, "representation_class")
        exactness_class = getattr(value, "exactness_class")
    except AttributeError as exc:
        raise TypeError(f"{field} does not expose a complete artifact type") from exc
    return TypeNode(semantic_type, representation_class, exactness_class)


def _normalize_registry(registry: Mapping[str, object]) -> tuple[_Edge, ...]:
    if not isinstance(registry, Mapping) or not registry:
        raise ValueError("registry must be a nonempty mapping")
    edges: list[_Edge] = []
    for registry_key, spec in sorted(registry.items(), key=lambda item: item[0]):
        if type(registry_key) is not str or not registry_key:
            raise ValueError("registry keys must be nonempty strings")
        operator_id = getattr(spec, "operator_id", None)
        if operator_id != registry_key:
            raise ValueError(f"registry key/operator mismatch: {registry_key!r} != {operator_id!r}")
        implementation_digest = getattr(spec, "implementation_digest", None)
        if type(implementation_digest) is not str or not implementation_digest:
            raise ValueError(f"operator {operator_id} lacks an implementation digest")
        execution_kind = getattr(spec, "execution_kind", None)
        if execution_kind not in {"PRIMITIVE", "META"}:
            raise ValueError(f"operator {operator_id} has an unknown execution kind")
        raw_ports = getattr(spec, "input_ports", None)
        if not isinstance(raw_ports, tuple):
            raise TypeError(f"operator {operator_id} lacks a frozen complete input-port contract")
        ports: list[tuple[str, TypeNode]] = []
        for index, port in enumerate(raw_ports):
            port_id = getattr(port, "port_id", None)
            if type(port_id) is not str or not port_id:
                raise ValueError(f"operator {operator_id} has an invalid input port at index {index}")
            ports.append((port_id, _type_node(getattr(port, "artifact_type", None), field=f"{operator_id}.{port_id}")))
        if len({port_id for port_id, _ in ports}) != len(ports):
            raise ValueError(f"operator {operator_id} has duplicate port IDs")
        output = _type_node(getattr(spec, "output", None), field=f"{operator_id}.output")
        edges.append(
            _Edge(
                operator_id=operator_id,
                input_ports=tuple(ports),
                output=output,
                implementation_digest=implementation_digest,
                execution_kind=execution_kind,
            )
        )
    return tuple(edges)


def _canonical_node(value: Any) -> Any:
    if value is None:
        return ["none"]
    if type(value) is bool:
        return ["bool", value]
    if type(value) is int:
        return ["int", str(value)]
    if type(value) is str:
        return ["str", value]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("nonfinite floats are not canonical")
        return ["float", value.hex()]
    if type(value) is Fraction:
        return ["fraction", str(value.numerator), str(value.denominator)]
    if isinstance(value, TypeNode):
        return [
            "type",
            value.semantic_type,
            value.representation_class,
            value.exactness_class,
        ]
    if type(value) is tuple:
        return ["tuple", [_canonical_node(item) for item in value]]
    if type(value) is list:
        return ["list", [_canonical_node(item) for item in value]]
    if type(value) in {set, frozenset}:
        members = [_canonical_node(item) for item in value]
        members.sort(key=_json_bytes)
        if any(_json_bytes(left) == _json_bytes(right) for left, right in zip(members, members[1:])):
            raise ValueError("canonical set-member collision")
        return ["set" if type(value) is set else "frozenset", members]
    if type(value) is dict or isinstance(value, Mapping):
        entries = [(_canonical_node(key), _canonical_node(item)) for key, item in value.items()]
        entries.sort(key=lambda pair: _json_bytes(pair[0]))
        if any(
            _json_bytes(left[0]) == _json_bytes(right[0])
            for left, right in zip(entries, entries[1:])
        ):
            raise ValueError("canonical mapping-key collision")
        return ["mapping", [[key, item] for key, item in entries]]
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")


def _digest(value: Any, *, domain: str) -> str:
    payload = domain.encode("ascii") + b"\x00" + _json_bytes(_canonical_node(value))
    return hashlib.sha256(payload).hexdigest()


def _edge_payload(edge: _Edge) -> dict[str, Any]:
    return {
        "operator_id": edge.operator_id,
        "input_ports": tuple(edge.input_ports),
        "output": edge.output,
        "implementation_digest": edge.implementation_digest,
        "execution_kind": edge.execution_kind,
    }


def _state_sort_key(state: _StateKey) -> tuple[Any, ...]:
    artifact_type, roots, progress = state
    return (
        artifact_type.semantic_type,
        artifact_type.representation_class,
        artifact_type.exactness_class,
        tuple(sorted(roots)),
        progress,
    )


def _recipe_sort_key(recipe: _Recipe) -> tuple[Any, ...]:
    return (recipe.length, tuple(node.operator_id or "" for node in recipe.nodes), recipe.final.node_id)


def _merge_nodes(recipes: Sequence[_Recipe], final: WitnessNode) -> tuple[WitnessNode, ...]:
    ordered: list[WitnessNode] = []
    seen: set[str] = set()
    for recipe in recipes:
        for node in recipe.nodes:
            if node.node_id not in seen:
                seen.add(node.node_id)
                ordered.append(node)
    if final.node_id not in seen:
        ordered.append(final)
    return tuple(ordered)


def _root_recipe(input_key: str, artifact_type: TypeNode) -> _Recipe:
    node = WitnessNode(
        node_id=f"root:{input_key}",
        artifact_type=artifact_type,
        root_keys=frozenset({input_key}),
        stage_progress=0,
        operator_id=None,
        input_node_ids=(),
    )
    return _Recipe(node, (node,))


def _apply_edge(
    edge: _Edge,
    inputs: Sequence[_Recipe],
    stages: tuple[TypeNode, ...],
    stage_roots: tuple[frozenset[str], ...],
) -> _Recipe:
    roots = frozenset().union(*(recipe.final.root_keys for recipe in inputs))
    progress = max((recipe.final.stage_progress for recipe in inputs), default=0)
    if (
        progress < len(stages)
        and edge.output == stages[progress]
        and stage_roots[progress] <= roots
    ):
        progress += 1
    input_ids = tuple(recipe.final.node_id for recipe in inputs)
    node_identity = {
        "operator_id": edge.operator_id,
        "input_node_ids": input_ids,
        "output": edge.output,
        "roots": roots,
        "progress": progress,
    }
    node = WitnessNode(
        node_id=f"derived:{_digest(node_identity, domain='pct-lineage-node-v1')}",
        artifact_type=edge.output,
        root_keys=roots,
        stage_progress=progress,
        operator_id=edge.operator_id,
        input_node_ids=input_ids,
    )
    return _Recipe(node, _merge_nodes(inputs, node))


def _witness(recipe: _Recipe) -> LineageWitness:
    return LineageWitness(
        nodes=recipe.nodes,
        final_node_id=recipe.final.node_id,
        final_root_keys=recipe.final.root_keys,
        final_stage_progress=recipe.final.stage_progress,
    )


def _witness_payload(value: LineageWitness | None) -> Any:
    if value is None:
        return None
    return {
        "nodes": tuple(
            {
                "node_id": node.node_id,
                "artifact_type": node.artifact_type,
                "root_keys": node.root_keys,
                "stage_progress": node.stage_progress,
                "operator_id": node.operator_id,
                "input_node_ids": node.input_node_ids,
            }
            for node in value.nodes
        ),
        "final_node_id": value.final_node_id,
        "final_root_keys": value.final_root_keys,
        "final_stage_progress": value.final_stage_progress,
    }


def prove_lineage_obligation(
    *,
    root_types: Mapping[str, object],
    target_type: object,
    obligation: LineageObligation,
    registry: Mapping[str, object],
    goal_contract: Mapping[str, Any],
) -> LineageProof:
    """Compute a conservative proof over the live, complete type hypergraph.

    ``REFUTED`` takes precedence if *any* target-typed structural route omits a
    required root or ordered stage.  ``PROVED`` therefore requires both a safe
    route and the absence of all such shortcuts.  ``UNREACHABLE`` means no
    target route was found at all (or only safe completion was impossible).
    """

    if not isinstance(obligation, LineageObligation):
        raise TypeError("obligation must be a LineageObligation")
    if not isinstance(root_types, Mapping) or not root_types:
        raise ValueError("root_types must be a nonempty mapping")
    normalized_roots: dict[str, TypeNode] = {}
    for input_key, raw_type in sorted(root_types.items(), key=lambda item: item[0]):
        if type(input_key) is not str or not input_key:
            raise ValueError("root input keys must be nonempty strings")
        normalized_roots[input_key] = _type_node(raw_type, field=f"root {input_key}")
    missing = obligation.required_input_keys - normalized_roots.keys()
    if missing:
        raise ValueError(f"missing required root(s): {','.join(sorted(missing))}")
    target = _type_node(target_type, field="target")
    edges = _normalize_registry(registry)
    if not isinstance(goal_contract, Mapping) or not goal_contract:
        raise ValueError("goal_contract must be a nonempty mapping")

    registry_digest = _digest(tuple(_edge_payload(edge) for edge in edges), domain="pct-lineage-registry-v1")
    goal_contract_digest = _digest(dict(goal_contract), domain="pct-lineage-goal-contract-v1")
    obligation_digest = _digest(
        {
            "required_input_keys": obligation.required_input_keys,
            "ordered_stage_types": obligation.ordered_stage_types,
            "stage_required_input_keys": obligation.stage_required_input_keys,
            "root_types": normalized_roots,
            "target_type": target,
        },
        domain="pct-lineage-obligation-v1",
    )

    # Operators are non-consuming: for structural reachability it is sufficient
    # to retain as many distinct witnesses per abstract state as the largest
    # repeated-type port multiplicity in any single application.  Keeping the
    # shortest deterministic witnesses makes cycles finite without allowing one
    # artifact instance to occupy two named ports.
    recipe_capacity = max(
        (
            max(Counter(port_type for _, port_type in edge.input_ports).values(), default=1)
            for edge in edges
        ),
        default=1,
    )
    states: dict[_StateKey, list[_Recipe]] = {}
    for input_key, artifact_type in normalized_roots.items():
        recipe = _root_recipe(input_key, artifact_type)
        states.setdefault((artifact_type, recipe.final.root_keys, 0), []).append(recipe)

    changed = True
    while changed:
        changed = False
        snapshot = tuple(
            (key, tuple(recipes))
            for key, recipes in sorted(states.items(), key=lambda item: _state_sort_key(item[0]))
        )
        by_type: dict[TypeNode, tuple[_Recipe, ...]] = {}
        for artifact_type in sorted({key[0] for key, _ in snapshot}):
            recipes = tuple(
                recipe
                for key, state_recipes in snapshot
                if key[0] == artifact_type
                for recipe in state_recipes
            )
            by_type[artifact_type] = tuple(sorted(recipes, key=_recipe_sort_key))
        for edge in edges:
            choices = [by_type.get(port_type, ()) for _, port_type in edge.input_ports]
            if any(not options for options in choices):
                continue
            combinations = itertools.product(*choices) if choices else ((),)
            for combination in combinations:
                if len({recipe.final.node_id for recipe in combination}) != len(combination):
                    continue
                recipe = _apply_edge(
                    edge,
                    combination,
                    obligation.ordered_stage_types,
                    obligation.stage_required_input_keys,
                )
                key = (edge.output, recipe.final.root_keys, recipe.final.stage_progress)
                previous = states.get(key, [])
                if any(item.final.node_id == recipe.final.node_id for item in previous):
                    continue
                updated = sorted(previous + [recipe], key=_recipe_sort_key)[:recipe_capacity]
                if updated != previous:
                    states[key] = updated
                    changed = True

    target_recipes = [
        recipe
        for key, state_recipes in states.items()
        if key[0] == target
        for recipe in state_recipes
    ]
    safe = [
        recipe
        for recipe in target_recipes
        if obligation.required_input_keys <= recipe.final.root_keys
        and recipe.final.stage_progress == len(obligation.ordered_stage_types)
    ]
    unsafe = [recipe for recipe in target_recipes if recipe not in safe]
    safe.sort(key=_recipe_sort_key)
    unsafe.sort(key=_recipe_sort_key)

    if unsafe:
        status = ProofStatus.REFUTED
        safe_witness = _witness(safe[0]) if safe else None
        counterexample = _witness(unsafe[0])
        reason = "a target-typed structural route bypasses a required root or ordered stage"
    elif safe:
        status = ProofStatus.PROVED
        safe_witness = _witness(safe[0])
        counterexample = None
        reason = "safe route exists and the over-approximated type closure contains no shortcut"
    else:
        status = ProofStatus.UNREACHABLE
        safe_witness = None
        counterexample = None
        reason = "no obligation-satisfying target route exists"

    proof_payload = {
        "status": status.value,
        "registry_digest": registry_digest,
        "goal_contract_digest": goal_contract_digest,
        "obligation_digest": obligation_digest,
        "explored_state_count": sum(len(recipes) for recipes in states.values()),
        "safe_witness": _witness_payload(safe_witness),
        "counterexample": _witness_payload(counterexample),
        "reason": reason,
    }
    return LineageProof(
        status=status,
        registry_digest=registry_digest,
        goal_contract_digest=goal_contract_digest,
        obligation_digest=obligation_digest,
        explored_state_count=sum(len(recipes) for recipes in states.values()),
        safe_witness=safe_witness,
        counterexample=counterexample,
        reason=reason,
        proof_digest=_digest(proof_payload, domain="pct-lineage-proof-v1"),
    )


def validate_lineage_witness(
    witness: LineageWitness,
    *,
    root_types: Mapping[str, object],
    target_type: object,
    obligation: LineageObligation,
    registry: Mapping[str, object],
    expect_safe: bool,
) -> bool:
    """Replay every witness node against the registry's typed hyperedges."""

    if (
        not isinstance(witness, LineageWitness)
        or type(expect_safe) is not bool
        or type(witness.nodes) is not tuple
        or type(witness.final_node_id) is not str
        or type(witness.final_root_keys) is not frozenset
        or type(witness.final_stage_progress) is not int
        or not isinstance(obligation, LineageObligation)
    ):
        return False
    try:
        roots = {
            key: _type_node(value, field=f"root {key}")
            for key, value in sorted(root_types.items(), key=lambda item: item[0])
        }
        target = _type_node(target_type, field="target")
        edges = {edge.operator_id: edge for edge in _normalize_registry(registry)}
    except (AttributeError, TypeError, ValueError):
        return False
    if obligation.required_input_keys - roots.keys():
        return False

    replayed: dict[str, WitnessNode] = {}
    for node in witness.nodes:
        if (
            not isinstance(node, WitnessNode)
            or type(node.node_id) is not str
            or not node.node_id
            or type(node.root_keys) is not frozenset
            or any(type(key) is not str for key in node.root_keys)
            or type(node.stage_progress) is not int
            or not 0 <= node.stage_progress <= len(obligation.ordered_stage_types)
            or (node.operator_id is not None and type(node.operator_id) is not str)
            or type(node.input_node_ids) is not tuple
            or any(type(node_id) is not str for node_id in node.input_node_ids)
            or node.node_id in replayed
        ):
            return False
        if node.operator_id is None:
            if not node.node_id.startswith("root:"):
                return False
            input_key = node.node_id.removeprefix("root:")
            expected_type = roots.get(input_key)
            expected = WitnessNode(
                node_id=node.node_id,
                artifact_type=expected_type,
                root_keys=frozenset({input_key}),
                stage_progress=0,
                operator_id=None,
                input_node_ids=(),
            ) if expected_type is not None else None
            if node != expected:
                return False
        else:
            edge = edges.get(node.operator_id)
            if edge is None or len(node.input_node_ids) != len(edge.input_ports):
                return False
            if len(set(node.input_node_ids)) != len(node.input_node_ids):
                return False
            if any(input_id not in replayed for input_id in node.input_node_ids):
                return False
            inputs = tuple(replayed[input_id] for input_id in node.input_node_ids)
            if any(
                input_node.artifact_type != port_type
                for input_node, (_, port_type) in zip(inputs, edge.input_ports)
            ):
                return False
            input_recipes = tuple(_Recipe(input_node, (input_node,)) for input_node in inputs)
            expected_recipe = _apply_edge(
                edge,
                input_recipes,
                obligation.ordered_stage_types,
                obligation.stage_required_input_keys,
            )
            if node != expected_recipe.final:
                return False
        replayed[node.node_id] = node

    final = replayed.get(witness.final_node_id)
    if final is None or final.artifact_type != target:
        return False
    if (
        witness.final_root_keys != final.root_keys
        or witness.final_stage_progress != final.stage_progress
    ):
        return False
    safe = (
        obligation.required_input_keys <= final.root_keys
        and final.stage_progress == len(obligation.ordered_stage_types)
    )
    if safe is not expect_safe:
        return False

    ancestors: set[str] = set()
    frontier = [final.node_id]
    while frontier:
        node_id = frontier.pop()
        if node_id in ancestors:
            continue
        ancestors.add(node_id)
        frontier.extend(replayed[node_id].input_node_ids)
    return ancestors == set(replayed)


def validate_lineage_proof(
    proof: LineageProof,
    *,
    root_types: Mapping[str, object],
    target_type: object,
    obligation: LineageObligation,
    registry: Mapping[str, object],
    goal_contract: Mapping[str, Any],
) -> bool:
    """Recompute a proof; stored hashes alone are never treated as authority."""

    def digest_field(value: object) -> bool:
        return (
            type(value) is str
            and len(value) == 64
            and value == value.lower()
            and all(character in "0123456789abcdef" for character in value)
        )

    if (
        type(proof) is not LineageProof
        or type(proof.status) is not ProofStatus
        or not digest_field(proof.registry_digest)
        or not digest_field(proof.goal_contract_digest)
        or not digest_field(proof.obligation_digest)
        or type(proof.explored_state_count) is not int
        or proof.explored_state_count < 0
        or (proof.safe_witness is not None and type(proof.safe_witness) is not LineageWitness)
        or (proof.counterexample is not None and type(proof.counterexample) is not LineageWitness)
        or type(proof.reason) is not str
        or not proof.reason
        or not digest_field(proof.proof_digest)
    ):
        return False
    if proof.status is ProofStatus.PROVED and not (
        proof.safe_witness is not None and proof.counterexample is None
    ):
        return False
    if proof.status is ProofStatus.REFUTED and proof.counterexample is None:
        return False
    if proof.status is ProofStatus.UNREACHABLE and not (
        proof.safe_witness is None and proof.counterexample is None
    ):
        return False
    if proof.safe_witness is not None and not validate_lineage_witness(
        proof.safe_witness,
        root_types=root_types,
        target_type=target_type,
        obligation=obligation,
        registry=registry,
        expect_safe=True,
    ):
        return False
    if proof.counterexample is not None and not validate_lineage_witness(
        proof.counterexample,
        root_types=root_types,
        target_type=target_type,
        obligation=obligation,
        registry=registry,
        expect_safe=False,
    ):
        return False
    stored_payload = {
        "status": proof.status.value,
        "registry_digest": proof.registry_digest,
        "goal_contract_digest": proof.goal_contract_digest,
        "obligation_digest": proof.obligation_digest,
        "explored_state_count": proof.explored_state_count,
        "safe_witness": _witness_payload(proof.safe_witness),
        "counterexample": _witness_payload(proof.counterexample),
        "reason": proof.reason,
    }
    try:
        if _digest(stored_payload, domain="pct-lineage-proof-v1") != proof.proof_digest:
            return False
    except (TypeError, ValueError):
        return False
    try:
        replay = prove_lineage_obligation(
            root_types=root_types,
            target_type=target_type,
            obligation=obligation,
            registry=registry,
            goal_contract=goal_contract,
        )
    except (TypeError, ValueError):
        return False
    return replay.proof_digest == proof.proof_digest
