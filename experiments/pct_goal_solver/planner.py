from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import heapq
import itertools
from typing import Any, Iterable, Mapping

import networkx as nx
import sympy as sp
from shapely.geometry import Polygon

from .model import Artifact, OperatorFailure, SolveTrace, SolverVisibleGoal, VerificationResult
from .operators import OperatorSpec


_META_OPERATOR_IDS = frozenset({"FINITE_COUNTEREXAMPLE_SEARCH", "SEPARATION_ESCALATE", "FALSIFY_CANDIDATE", "VERIFY_CANDIDATE"})


@dataclass(frozen=True)
class _SearchNode:
    artifacts: tuple[tuple[str, Artifact], ...]
    path: tuple[str, ...]
    verifiers: tuple[VerificationResult, ...]
    cost: int
    primitive_executions: int
    macro_ids: tuple[str, ...] = ()

    def mapping(self) -> dict[str, Artifact]:
        return dict(self.artifacts)


def _value_signature(value: Any) -> str:
    if isinstance(value, sp.Basic):
        return sp.srepr(value)
    return repr(value)


def _artifact_signature(artifact: Artifact) -> tuple[str, str, str, str, str]:
    return (
        artifact.semantic_type,
        artifact.representation_class,
        artifact.exactness_class,
        _value_signature(artifact.value),
        repr(tuple(artifact.metadata)),
    )


def _state_signature(artifacts: Mapping[str, Artifact]) -> tuple[tuple[str, str, str, str, str], ...]:
    return tuple(sorted(_artifact_signature(artifact) for artifact in artifacts.values()))


def _available_counts(artifacts: Mapping[str, Artifact]) -> Counter[str]:
    return Counter(artifact.semantic_type for artifact in artifacts.values())


def _requirements_met(spec: OperatorSpec, artifacts: Mapping[str, Artifact]) -> bool:
    required = Counter(spec.input_types)
    available = _available_counts(artifacts)
    return all(available[name] >= count for name, count in required.items())


def _single_input_alias(operator_id: str) -> str | None:
    return {
        "EXACT_MATRIX_RANK_Q": "matrix",
        "EXACT_NULLSPACE_Q": "matrix",
        "GF2_RANK": "matrix",
        "ZETA_TRANSFORM_BOOLEAN": "atomic",
        "MOBIUS_INVERT_BOOLEAN": "cumulative",
        "BARCODE_TO_BETTI": "barcode",
        "BETTI_TO_EULER": "betti",
        "GRAPH_EULER_BETTI": "graph",
        "GRAPH_DEGREE_SIGNATURE": "graph",
        "GRAPH_LAPLACIAN_SIGNATURE": "graph",
        "GRAPH_WL_SIGNATURE": "graph",
        "SYMBOLIC_SIMPLIFY": "expression",
        "NILPOTENCY_CHECK": "generator",
        "GAUSSIAN_EXPONENT_REWRITE": "lhs",
        "NUMERIC_MATRIX_RANK": "matrix",
        "CONDITIONING_RISK_CHECK": "matrix",
        "SUPPORT_FUNCTION_SAMPLE": "body",
        "SUPPORT_SPECTRUM": "samples",
        "CONVEXITY_CHECK": "body",
        "NUMERIC_RELATION_FIT": "trajectory",
    }.get(operator_id)


def _invocations(spec: OperatorSpec, artifacts: Mapping[str, Artifact]) -> tuple[dict[str, Artifact], ...]:
    if len(spec.input_types) == 1:
        semantic = spec.input_types[0]
        alias = _single_input_alias(spec.operator_id)
        rows: list[dict[str, Artifact]] = []
        for key, artifact in sorted(artifacts.items()):
            if artifact.semantic_type != semantic:
                continue
            invocation = {key: artifact}
            if alias is not None:
                invocation[alias] = artifact
            rows.append(invocation)
        return tuple(rows)
    return (dict(artifacts),)


def _derived_key(operator_id: str, artifact: Artifact, artifacts: Mapping[str, Artifact]) -> str:
    base = f"derived:{operator_id}:{artifact.semantic_type}"
    index = sum(key.startswith(base) for key in artifacts)
    return f"{base}:{index:03d}"


def _has_equivalent(artifact: Artifact, artifacts: Mapping[str, Artifact]) -> bool:
    signature = _artifact_signature(artifact)
    return any(_artifact_signature(existing) == signature for existing in artifacts.values())


def _required_derived_types(goal: SolverVisibleGoal) -> Counter[str]:
    raw = dict(goal.constraints).get("required_derived_types", ())
    if raw is None:
        return Counter()
    if isinstance(raw, str):
        return Counter((raw,))
    return Counter(tuple(raw))


def _missing_derived_evidence(goal: SolverVisibleGoal, artifacts: Mapping[str, Artifact]) -> Counter[str]:
    required = _required_derived_types(goal)
    if not required:
        return Counter()
    produced = Counter(
        artifact.semantic_type
        for artifact in artifacts.values()
        if artifact.provenance
    )
    return Counter({
        semantic_type: needed - produced[semantic_type]
        for semantic_type, needed in required.items()
        if produced[semantic_type] < needed
    })


def _evidence_obligations_satisfied(goal: SolverVisibleGoal, artifacts: Mapping[str, Artifact]) -> bool:
    return not _missing_derived_evidence(goal, artifacts)


def _required_evidence_needs_output(
    goal: SolverVisibleGoal,
    output: Artifact,
    artifacts: Mapping[str, Artifact],
) -> bool:
    """Allow a provenance-bearing duplicate when it closes an evidence obligation."""
    return _missing_derived_evidence(goal, artifacts)[output.semantic_type] > 0


def _candidate_from_state(goal: SolverVisibleGoal, artifacts: Mapping[str, Artifact]) -> Artifact | None:
    for _, artifact in sorted(artifacts.items()):
        if artifact.semantic_type == goal.target.semantic_type:
            return artifact
    return _comparison_candidate(goal, artifacts)


def _comparison_candidate(goal: SolverVisibleGoal, artifacts: Mapping[str, Artifact]) -> Artifact | None:
    if goal.family == "G4":
        by_type: dict[str, list[Artifact]] = defaultdict(list)
        for artifact in artifacts.values():
            if artifact.semantic_type in {"BETTI_CURVE", "EULER_CURVE"}:
                by_type[artifact.semantic_type].append(artifact)
        if len(by_type["BETTI_CURVE"]) < 2 or len(by_type["EULER_CURVE"]) < 2:
            return None
        euler = by_type["EULER_CURVE"][:2]
        betti = by_type["BETTI_CURVE"][:2]
        if euler[0].value != euler[1].value:
            level = "EULER"
        elif betti[0].value != betti[1].value:
            level = "BETTI"
        else:
            barcodes = [a for a in artifacts.values() if a.semantic_type == "BARCODE"]
            level = "BARCODE" if len(barcodes) >= 2 and barcodes[0].value != barcodes[1].value else "NONE"
        return Artifact(
            artifact_id=f"candidate:{goal.goal_id}:separation",
            semantic_type=goal.target.semantic_type,
            representation_class="PERSISTENCE",
            value={"level": level, "distinct": level != "NONE"},
            exactness_class="EXACT",
            provenance=tuple(a.artifact_id for a in euler + betti),
        )

    if goal.family == "G5":
        signatures = [a for a in artifacts.values() if a.semantic_type == "GRAPH_SIGNATURE"]
        by_level: dict[str, list[Artifact]] = defaultdict(list)
        for artifact in signatures:
            by_level[str(artifact.metadata_dict().get("level", "UNKNOWN"))].append(artifact)
        for level in ("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL"):
            rows = by_level[level]
            if len(rows) >= 2 and rows[0].value != rows[1].value:
                return Artifact(
                    artifact_id=f"candidate:{goal.goal_id}:graph:{level}",
                    semantic_type=goal.target.semantic_type,
                    representation_class="GRAPH",
                    value={"distinct": True, "level": level},
                    exactness_class="EXACT" if level != "LAPLACIAN" else "NUMERICAL",
                    provenance=tuple(row.artifact_id for row in rows[:2]),
                )
        if all(len(by_level[level]) >= 2 for level in ("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL")):
            return Artifact(
                artifact_id=f"candidate:{goal.goal_id}:graph:none",
                semantic_type=goal.target.semantic_type,
                representation_class="GRAPH",
                value={"distinct": False, "level": "EXHAUSTED_BANK"},
                exactness_class="EXACT",
                provenance=tuple(a.artifact_id for a in signatures),
            )
    return None


def _zeta(values: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sum(values[s] for s in range(len(values)) if s & t == s) for t in range(len(values)))


def _matrix(value: Any) -> sp.Matrix:
    return sp.Matrix([[sp.sympify(v) for v in row] for row in value])


def _verify_goal(goal: SolverVisibleGoal, candidate: Artifact) -> VerificationResult:
    try:
        if goal.family == "G1":
            cumulative = goal.inputs["cumulative"].value
            passed = _zeta(tuple(int(v) for v in candidate.value)) == tuple(cumulative)
            return VerificationResult(passed, "INDEPENDENT_ZETA_ROUND_TRIP", "round trip" if passed else "round trip mismatch")
        if goal.family == "G2":
            matrix = _matrix(goal.inputs["observation_matrix"].value)
            nullity = len(matrix.nullspace())
            value = candidate.value
            passed = isinstance(value, dict) and int(value.get("nullity", -1)) == nullity and bool(value.get("unique")) == (nullity == 0)
            return VerificationResult(passed, "INDEPENDENT_NULLSPACE", f"nullity={nullity}")
        if goal.family == "G3":
            ds = _matrix(goal.inputs["source_boundary"].value)
            dt = _matrix(goal.inputs["target_boundary"].value)
            f0 = _matrix(goal.inputs["vertex_map"].value)
            f1 = _matrix(goal.inputs["edge_map"].value)
            expected = dt * f1 == f0 * ds
            return VerificationResult(bool(candidate.value) == bool(expected), "INDEPENDENT_CHAIN_COMMUTATION", f"expected={bool(expected)}")
        if goal.family == "G4":
            value = candidate.value
            passed = isinstance(value, dict) and value.get("level") in {"EULER", "BETTI", "BARCODE", "NONE"}
            return VerificationResult(passed, "INDEPENDENT_INFORMATION_ORDER", str(value))
        if goal.family == "G5":
            ga = nx.Graph(); ga.add_edges_from(goal.inputs["graph_a"].value)
            gb = nx.Graph(); gb.add_edges_from(goal.inputs["graph_b"].value)
            expected = not nx.is_isomorphic(ga, gb)
            observed = bool(candidate.value.get("distinct")) if isinstance(candidate.value, dict) else bool(candidate.value)
            return VerificationResult(observed == expected, "INDEPENDENT_GRAPH_ISOMORPHISM", f"expected_distinct={expected}")
        if goal.family == "G6":
            rank = int(_matrix(goal.inputs["exact_matrix"].value).rank())
            return VerificationResult(int(candidate.value) == rank, "INDEPENDENT_EXACT_RANK", f"rank={rank}")
        if goal.family == "G7":
            A, P, c = sp.symbols("A P c")
            invariant = sp.sympify(goal.inputs["candidate_invariant"].value, locals={"A": A, "P": P, "c": c})
            vector_field = sp.Matrix([P, 2 * sp.pi * c, 0])
            gradient = sp.Matrix([sp.diff(invariant, variable) for variable in (A, P, c)])
            expected = sp.simplify((gradient.T * vector_field)[0]) == 0
            return VerificationResult(bool(candidate.value) == bool(expected), "INDEPENDENT_LIE_DERIVATIVE", f"conserved={expected}")
        if goal.family == "G8":
            k = float(candidate.value)
            trajectory = goal.inputs["trajectory"].value
            values = [p * p + k * c * area for _, area, p, c in trajectory]
            residual = max(abs(v - values[0]) for v in values)
            return VerificationResult(residual <= goal.allowed_numeric_tolerance, "INDEPENDENT_TRAJECTORY_RESIDUAL", f"residual={residual}", residual=residual)
        if goal.family == "G9":
            poly = Polygon(goal.inputs["body"].value)
            s = float(goal.inputs["offset"].value)
            reference = float(poly.buffer(s, quad_segs=256).area)
            residual = abs(float(candidate.value) - reference)
            return VerificationResult(residual <= goal.allowed_numeric_tolerance, "INDEPENDENT_BUFFER_AREA", f"residual={residual}", residual=residual)
        if goal.family == "G10":
            observed = candidate.value.get("order") if isinstance(candidate.value, dict) else candidate.value
            poly = Polygon(goal.inputs["body"].value)
            expected = len(list(poly.exterior.coords)[:-1])
            passed = int(observed) == expected if observed is not None else False
            return VerificationResult(passed, "INDEPENDENT_ROTATIONAL_VERTEX_ORBIT", f"expected={expected}")
        if goal.family == "G11":
            observed = candidate.value.get("homothetic") if isinstance(candidate.value, dict) else bool(candidate.value)
            a = Polygon(goal.inputs["body_a"].value)
            b = Polygon(goal.inputs["body_b"].value)
            expected = len(list(a.exterior.coords)[:-1]) == len(list(b.exterior.coords)[:-1])
            return VerificationResult(bool(observed) == expected, "INDEPENDENT_POLYGON_COMBINATORICS", f"expected={expected}")
        if goal.family == "G12":
            lhs = sp.sympify(goal.inputs["lhs"].value)
            rhs = sp.sympify(goal.inputs["rhs"].value)
            expected = sp.simplify(lhs - rhs) == 0
            return VerificationResult(bool(candidate.value) == bool(expected), "INDEPENDENT_SYMBOLIC_IDENTITY", f"identity={expected}")
    except Exception as exc:
        return VerificationResult(False, "INDEPENDENT_VERIFIER_ERROR", str(exc))
    return VerificationResult(False, "UNSUPPORTED_GOAL_VERIFIER", goal.family)


def _node_priority(goal: SolverVisibleGoal, node: _SearchNode) -> tuple[Any, ...]:
    mapping = node.mapping()
    candidate_missing = int(_candidate_from_state(goal, mapping) is None)
    evidence_missing = sum(_missing_derived_evidence(goal, mapping).values())
    unresolved = candidate_missing + evidence_missing
    derived_count = sum(key.startswith("derived:") for key in mapping)
    return (unresolved, node.cost, derived_count, len(node.path), node.path)


def _make_trace(
    goal: SolverVisibleGoal,
    mode: str,
    node: _SearchNode,
    *,
    expanded: int,
    candidate: Artifact | None,
    verdict: str,
    terminal_verifier: VerificationResult | None = None,
    path_suffix: tuple[str, ...] = (),
    reason: str = "",
) -> SolveTrace:
    verifiers = node.verifiers + ((terminal_verifier,) if terminal_verifier is not None else ())
    return SolveTrace(
        goal_id=goal.goal_id,
        mode=mode,
        operator_path=node.path + path_suffix,
        expanded_state_count=expanded,
        primitive_execution_count=node.primitive_executions,
        macro_ids=node.macro_ids,
        candidate_artifact=candidate,
        verifier_chain=verifiers,
        falsification_events=(),
        final_verdict=verdict,
        failure_reason=reason,
    )


def _ordered_operator_ids(typing_mode: str, registry: Mapping[str, OperatorSpec], artifacts: Mapping[str, Artifact], compatibility_model: Any | None) -> tuple[str, ...]:
    if typing_mode == "EXPLICIT":
        return tuple(sorted(registry))
    if compatibility_model is None:
        raise ValueError(f"{typing_mode} mode requires a compatibility model")
    return tuple(compatibility_model.ordered_operator_ids(registry, artifacts))


def _apply_macro(
    macro: Any,
    node: _SearchNode,
    registry: Mapping[str, OperatorSpec],
    bindings: tuple[tuple[str, Any], ...],
    typing_mode: str,
) -> _SearchNode | None:
    artifacts = node.mapping()
    path = node.path
    verifiers = node.verifiers
    cost = node.cost
    executions = node.primitive_executions
    for operator_id in tuple(macro.primitive_ids):
        spec = registry.get(operator_id)
        if spec is None or operator_id in _META_OPERATOR_IDS:
            return None
        if typing_mode in {"EXPLICIT", "HYBRID"} and not _requirements_met(spec, artifacts):
            return None
        applied = False
        for invocation in _invocations(spec, artifacts):
            applicability = spec.applicability(invocation, bindings)
            if not applicability.applicable:
                continue
            output = spec.execute(invocation, bindings)
            executions += 1
            if isinstance(output, OperatorFailure):
                continue
            step_verifier = spec.verify(tuple(invocation.values()), output)
            if not step_verifier.passed or _has_equivalent(output, artifacts):
                continue
            artifacts = dict(artifacts)
            artifacts[_derived_key(operator_id, output, artifacts)] = output
            path = path + (operator_id,)
            verifiers = verifiers + (step_verifier,)
            cost += spec.cost
            applied = True
            break
        if not applied:
            return None
    return _SearchNode(
        artifacts=tuple(sorted(artifacts.items())),
        path=path,
        verifiers=verifiers,
        cost=cost,
        primitive_executions=executions,
        macro_ids=node.macro_ids + (str(macro.macro_id),),
    )


def solve(
    goal: SolverVisibleGoal,
    registry: Mapping[str, OperatorSpec],
    *,
    typing_mode: str = "EXPLICIT",
    compatibility_model: Any | None = None,
    macros: Iterable[Any] = (),
) -> SolveTrace:
    if typing_mode not in {"EXPLICIT", "INFERRED", "HYBRID"}:
        raise ValueError(f"unknown typing mode: {typing_mode}")
    if typing_mode != "EXPLICIT" and compatibility_model is None:
        raise ValueError(f"{typing_mode} mode requires a compatibility model")

    macro_bank = tuple(sorted(tuple(macros), key=lambda macro: str(macro.macro_id)))
    mode = f"{typing_mode}/{'SYNTHESIZED' if macro_bank else 'PRIMITIVE'}"
    initial = _SearchNode(tuple(sorted(goal.inputs.items())), (), (), 0, 0, ())
    if goal.search_budget <= 0:
        return _make_trace(goal, mode, initial, expanded=0, candidate=None, verdict="NOT_ESTABLISHED", reason="SEARCH_BUDGET_EXHAUSTED")

    queue: list[tuple[tuple[Any, ...], int, _SearchNode]] = []
    serial = itertools.count()
    heapq.heappush(queue, (_node_priority(goal, initial), next(serial), initial))
    seen = {_state_signature(initial.mapping())}
    expanded = 0
    first_relevant_not_applicable: tuple[_SearchNode, str] | None = None
    bindings = tuple(goal.constraints)

    while queue and expanded < goal.search_budget:
        _, _, node = heapq.heappop(queue)
        expanded += 1
        artifacts = node.mapping()

        candidate = _candidate_from_state(goal, artifacts)
        if candidate is not None and _evidence_obligations_satisfied(goal, artifacts):
            terminal = _verify_goal(goal, candidate)
            if terminal.passed:
                return _make_trace(goal, mode, node, expanded=expanded, candidate=candidate, verdict="PASS", terminal_verifier=terminal, path_suffix=("VERIFY_CANDIDATE",))

        # Macros are expanded to the exact primitive sequence and checked at every
        # internal step. They skip intermediate search states, not primitive work.
        for macro in macro_bank:
            child = _apply_macro(macro, node, registry, bindings, typing_mode)
            if child is None:
                continue
            signature = _state_signature(child.mapping())
            if signature in seen:
                continue
            seen.add(signature)
            heapq.heappush(queue, (_node_priority(goal, child), next(serial), child))

        for operator_id in _ordered_operator_ids(typing_mode, registry, artifacts, compatibility_model):
            spec = registry[operator_id]
            if operator_id in _META_OPERATOR_IDS:
                continue
            if typing_mode in {"EXPLICIT", "HYBRID"} and not _requirements_met(spec, artifacts):
                continue
            invocations = _invocations(spec, artifacts)
            if not invocations and typing_mode == "INFERRED":
                continue
            for invocation in invocations:
                applicability = spec.applicability(invocation, bindings)
                if not applicability.applicable:
                    if applicability.verdict == "NOT_APPLICABLE" and spec.output_type == goal.target.semantic_type:
                        probe_node = _SearchNode(node.artifacts, node.path + (operator_id,), node.verifiers, node.cost + spec.cost, node.primitive_executions, node.macro_ids)
                        if first_relevant_not_applicable is None:
                            first_relevant_not_applicable = (probe_node, applicability.reason)
                    continue
                output = spec.execute(invocation, bindings)
                executions = node.primitive_executions + 1
                if isinstance(output, OperatorFailure):
                    if output.verdict == "NOT_APPLICABLE" and spec.output_type == goal.target.semantic_type:
                        probe_node = _SearchNode(node.artifacts, node.path + (operator_id,), node.verifiers, node.cost + spec.cost, executions, node.macro_ids)
                        if first_relevant_not_applicable is None:
                            first_relevant_not_applicable = (probe_node, output.reason)
                    continue
                step_verifier = spec.verify(tuple(invocation.values()), output)
                equivalent = _has_equivalent(output, artifacts)
                if not step_verifier.passed or (equivalent and not _required_evidence_needs_output(goal, output, artifacts)):
                    continue
                new_artifacts = dict(artifacts)
                new_artifacts[_derived_key(operator_id, output, artifacts)] = output
                signature = _state_signature(new_artifacts)
                if signature in seen:
                    continue
                seen.add(signature)
                child = _SearchNode(
                    tuple(sorted(new_artifacts.items())),
                    node.path + (operator_id,),
                    node.verifiers + (step_verifier,),
                    node.cost + spec.cost,
                    executions,
                    node.macro_ids,
                )
                heapq.heappush(queue, (_node_priority(goal, child), next(serial), child))

    if first_relevant_not_applicable is not None:
        node, reason = first_relevant_not_applicable
        return _make_trace(goal, mode, node, expanded=expanded, candidate=None, verdict="NOT_APPLICABLE", reason=reason)
    return _make_trace(goal, mode, initial, expanded=expanded, candidate=None, verdict="NOT_ESTABLISHED", reason="SEARCH_BUDGET_EXHAUSTED" if expanded >= goal.search_budget else "NO_ADMISSIBLE_PATH")