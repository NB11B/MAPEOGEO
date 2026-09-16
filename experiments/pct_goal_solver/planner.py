from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass, replace
import heapq
import itertools
import math
from typing import Any, Iterable, Mapping

from .canonical import canonical_sha256
from .compatibility import (
    CompatibilityModel,
    RoutingDecision,
    authoritative_routing_decision,
)
from .goal_verifiers import (
    normalize_historical_barcode,
    validate_historical_goal_contract,
    verify_historical_goal,
)
from .lineage import DerivedOrigin, TrackedArtifact, artifact_content_digest, derive_artifact, track_roots
from .model import (
    Applicability,
    Artifact,
    ArtifactType,
    CandidateLineageObligation,
    DerivedArtifactRecord,
    DerivationStep,
    DerivedObligation,
    LineageReceipt,
    OperatorFailure,
    Refusal,
    RootOrigin,
    RoutingReceipt,
    SolveTrace,
    SolverVisibleGoal,
    TargetSpec,
    VerificationResult,
    APPLICABILITY_VERDICTS,
    EXACTNESS_CLASSES,
)
from .operators import OperatorSpec, callable_contract_digest, operator_registry_digest
from .v0_20_contracts import NEW_V0_20_FAMILIES, STRICT_V0_20_VERIFIER_CLASS
from .v0_20_verifiers import validate_v0_20_goal_contract, verify_v0_20_goal


_MAX_EXCEPTION_TEXT_LENGTH = 512
_EXCEPTION_TEXT_FALLBACK = "exception message unavailable"
_EXCEPTION_TEXT_TRUNCATION = "...[truncated]"
_OPERATOR_FAILURE_VERDICTS = frozenset(
    {"NOT_APPLICABLE", "INVALID", "ERROR", "NUMERICALLY_UNSAFE"}
)


def _safe_exception_text(exc: BaseException) -> str:
    """Return deterministic, bounded text without trusting ``exc.__str__``.

    Operator, verifier, compatibility-model, and evidence code all execute
    outside the planner's trust boundary.  In particular, formatting an
    exception from that code is itself an untrusted call and must never turn a
    structured refusal into an escaping exception.
    """

    try:
        message = str(exc)
        if type(message) is not str:
            return _EXCEPTION_TEXT_FALLBACK
        if len(message) <= _MAX_EXCEPTION_TEXT_LENGTH:
            return message
        keep = _MAX_EXCEPTION_TEXT_LENGTH - len(_EXCEPTION_TEXT_TRUNCATION)
        return message[:keep] + _EXCEPTION_TEXT_TRUNCATION
    except BaseException:
        return _EXCEPTION_TEXT_FALLBACK


def _is_bounded_text(value: object, *, allow_empty: bool = True) -> bool:
    return (
        type(value) is str
        and (allow_empty or bool(value))
        and len(value) <= _MAX_EXCEPTION_TEXT_LENGTH
    )


def _has_valid_verification_fields(value: object) -> bool:
    try:
        return (
            type(value) is VerificationResult
            and type(value.passed) is bool
            and _is_bounded_text(value.verifier_class, allow_empty=False)
            and _is_bounded_text(value.reason)
            and (
                value.residual is None
                or (type(value.residual) is float and math.isfinite(value.residual))
            )
            and type(value.evidence) is tuple
            and _is_bounded_text(value.stage)
            and _is_bounded_text(value.subject_id)
        )
    except Exception:
        return False


@dataclass(frozen=True)
class _SearchNode:
    artifacts: tuple[tuple[str, TrackedArtifact], ...]
    path: tuple[str, ...]
    verifiers: tuple[VerificationResult, ...]
    cost: int
    derivations: tuple[DerivationStep, ...] = ()

    def mapping(self) -> dict[str, Artifact]:
        return {key: tracked.artifact for key, tracked in self.artifacts}

    def tracked_mapping(self) -> dict[str, TrackedArtifact]:
        return dict(self.artifacts)


@dataclass(frozen=True)
class _CandidateChoice:
    tracked: TrackedArtifact
    supplemental_steps: tuple[DerivationStep, ...] = ()
    supplemental_verifiers: tuple[VerificationResult, ...] = ()


@dataclass(frozen=True)
class _PlannerComparisonContract:
    family: str
    operator_id: str
    output: ArtifactType
    objective: str
    evidence_types: frozenset[str]
    verifier_id: str


_PLANNER_COMPARISON_CONTRACTS = {
    "G4": _PlannerComparisonContract(
        family="G4",
        operator_id="PLANNER_COMPARISON_G4_V1",
        output=ArtifactType("REPRESENTATION_SEPARATION", "PERSISTENCE", "EXACT"),
        objective="FIND_FINEST_NEEDED",
        evidence_types=frozenset({"BARCODE", "BETTI_CURVE", "EULER_CURVE"}),
        verifier_id="pct.planner-comparison.g4.v1",
    ),
    "G5": _PlannerComparisonContract(
        family="G5",
        operator_id="PLANNER_COMPARISON_G5_V1",
        output=ArtifactType("GRAPH_DISTINGUISHABILITY", "GRAPH", "EXACT"),
        objective="DISTINGUISH",
        evidence_types=frozenset({"GRAPH_SIGNATURE"}),
        verifier_id="pct.planner-comparison.g5.v1",
    ),
}


def _value_signature(value: Any) -> str:
    return canonical_sha256(value, domain="pct-value-signature-v1")


def _artifact_signature(artifact: Artifact) -> tuple[str, str, str, str, str]:
    return (
        artifact.semantic_type,
        artifact.representation_class,
        artifact.exactness_class,
        _value_signature(artifact.value),
        canonical_sha256(artifact.metadata, domain="pct-metadata-signature-v1"),
    )


def _state_signature(artifacts: Mapping[str, TrackedArtifact]) -> tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...]:
    return tuple(
        sorted(
            (
                tracked.instance_id,
                _value_signature(tracked.artifact.value),
                tuple(sorted(tracked.root_input_keys)),
                tracked.derivation_step_ids,
            )
            for tracked in artifacts.values()
        )
    )


def _view_for_contract(artifact: Artifact, artifact_type: ArtifactType) -> Artifact:
    if artifact.artifact_type == artifact_type:
        return artifact
    return Artifact(
        artifact_id=artifact.artifact_id,
        semantic_type=artifact_type.semantic_type,
        representation_class=artifact_type.representation_class,
        value=artifact.value,
        exactness_class=artifact_type.exactness_class,
        metadata=artifact.metadata,
        provenance=artifact.provenance,
    )


def _tracked_port_bindings(
    spec: OperatorSpec,
    artifacts: Mapping[str, TrackedArtifact],
    effective_root_types: Mapping[str, ArtifactType] | None = None,
) -> tuple[tuple[dict[str, Artifact], dict[str, TrackedArtifact]], ...]:
    if not spec.input_ports:
        return (({}, {}),)
    effective_root_types = effective_root_types or {}
    candidates: list[list[tuple[str, TrackedArtifact, Artifact]]] = []
    for port in spec.input_ports:
        rows: list[tuple[str, TrackedArtifact, Artifact]] = []
        for key, tracked in sorted(artifacts.items()):
            effective = effective_root_types.get(key, tracked.artifact.artifact_type)
            if effective != port.artifact_type:
                continue
            rows.append((key, tracked, _view_for_contract(tracked.artifact, port.artifact_type)))
        if not rows:
            return ()
        candidates.append(rows)
    bindings: list[tuple[dict[str, Artifact], dict[str, TrackedArtifact]]] = []
    for selection in itertools.product(*candidates):
        state_keys = tuple(row[0] for row in selection)
        if len(state_keys) != len(set(state_keys)):
            continue
        invocation = {port.port_id: row[2] for port, row in zip(spec.input_ports, selection)}
        tracked_inputs = {port.port_id: row[1] for port, row in zip(spec.input_ports, selection)}
        bindings.append((invocation, tracked_inputs))
    return tuple(bindings)


def enumerate_port_bindings(
    spec: OperatorSpec,
    artifacts: Mapping[str, Artifact],
) -> tuple[dict[str, Artifact], ...]:
    """Public contract probe used by adversarial tests and registry audits."""
    tracked = dict(track_roots(artifacts))
    return tuple(invocation for invocation, _ in _tracked_port_bindings(spec, tracked))


def _derived_key(operator_id: str, tracked: TrackedArtifact, artifacts: Mapping[str, TrackedArtifact]) -> str:
    base = f"derived:{operator_id}:{tracked.artifact.semantic_type}:{tracked.instance_id[-12:]}"
    index = sum(key.startswith(base) for key in artifacts)
    return f"{base}:{index:03d}"


def _lineage_progress(
    goal: SolverVisibleGoal,
    tracked: TrackedArtifact,
    artifacts: Mapping[str, TrackedArtifact],
) -> int:
    obligation = goal.lineage_obligation
    if obligation is None or not obligation.ordered_stage_types:
        return 0
    by_instance = {
        row.instance_id: row
        for row in (*artifacts.values(), tracked)
    }
    stage_anchors = obligation.stage_required_input_keys or tuple(
        frozenset() for _ in obligation.ordered_stage_types
    )
    cache: dict[str, frozenset[int]] = {}
    active: set[str] = set()

    def reachable_progress(instance_id: str) -> frozenset[int]:
        if instance_id in cache:
            return cache[instance_id]
        current = by_instance.get(instance_id)
        if current is None or instance_id in active:
            return frozenset({0})
        if not isinstance(current.origin, DerivedOrigin):
            cache[instance_id] = frozenset({0})
            return cache[instance_id]

        active.add(instance_id)
        inherited: set[int] = set()
        for _, parent_instance_id in current.origin.parents:
            inherited.update(reachable_progress(parent_instance_id))
        active.remove(instance_id)
        if not inherited:
            inherited.add(0)

        reached = set(inherited)
        for progress in inherited:
            if progress >= len(obligation.ordered_stage_types):
                continue
            if current.artifact.artifact_type != obligation.ordered_stage_types[progress]:
                continue
            if not stage_anchors[progress] <= current.root_input_keys:
                continue
            reached.add(progress + 1)
        cache[instance_id] = frozenset(reached)
        return cache[instance_id]

    return max(reachable_progress(tracked.instance_id))


def _has_equivalent(
    goal: SolverVisibleGoal,
    candidate: TrackedArtifact,
    artifacts: Mapping[str, TrackedArtifact],
) -> bool:
    signature = _artifact_signature(candidate.artifact)
    lineage_pool = {**artifacts, "__candidate__": candidate}
    candidate_progress = _lineage_progress(goal, candidate, lineage_pool)
    return any(
        _artifact_signature(existing.artifact) == signature
        and existing.root_input_keys == candidate.root_input_keys
        and existing.producer_objectives == candidate.producer_objectives
        and _lineage_progress(goal, existing, lineage_pool) == candidate_progress
        for existing in artifacts.values()
    )


def _required_derived_types(goal: SolverVisibleGoal) -> Counter[str]:
    raw = dict(goal.constraints).get("required_derived_types", ())
    if raw is None:
        return Counter()
    if isinstance(raw, str):
        return Counter((raw,))
    return Counter(tuple(raw))


def _missing_derived_evidence(goal: SolverVisibleGoal, artifacts: Mapping[str, TrackedArtifact]) -> Counter[str]:
    required = _required_derived_types(goal)
    if not required:
        return Counter()
    produced = Counter(
        tracked.artifact.semantic_type
        for tracked in artifacts.values()
        if isinstance(tracked.origin, DerivedOrigin)
    )
    return Counter({
        semantic_type: needed - produced[semantic_type]
        for semantic_type, needed in required.items()
        if produced[semantic_type] < needed
    })


def _candidate_obligations(
    goal: SolverVisibleGoal,
    candidate: TrackedArtifact,
    derivations: tuple[DerivationStep, ...],
) -> tuple[DerivedObligation, ...] | None:
    obligation = goal.lineage_obligation
    if obligation is None:
        return ()
    if not obligation.required_input_keys <= candidate.root_input_keys:
        return None
    by_id = {step.step_id: step for step in derivations}
    lineage_steps = [
        by_id[step_id]
        for step_id in candidate.derivation_step_ids
        if step_id in by_id
    ]
    stage_anchors = obligation.stage_required_input_keys or tuple(
        frozenset() for _ in obligation.ordered_stage_types
    )
    step_by_output = {step.output_instance_id: step for step in lineage_steps}
    ancestry_cache: dict[tuple[str, str], bool] = {}

    def is_ancestor(ancestor_instance_id: str, descendant_instance_id: str) -> bool:
        key = (ancestor_instance_id, descendant_instance_id)
        if key in ancestry_cache:
            return ancestry_cache[key]
        if ancestor_instance_id == descendant_instance_id:
            ancestry_cache[key] = True
            return True
        descendant_step = step_by_output.get(descendant_instance_id)
        if descendant_step is None:
            ancestry_cache[key] = False
            return False
        result = any(
            is_ancestor(ancestor_instance_id, parent_instance_id)
            for _, parent_instance_id in descendant_step.input_bindings
        )
        ancestry_cache[key] = result
        return result

    def choose_stage_path(
        order_index: int,
        previous_instance_id: str | None,
        selected_step_ids: frozenset[str],
    ) -> tuple[DerivationStep, ...] | None:
        if order_index == len(obligation.ordered_stage_types):
            if previous_instance_id is None or is_ancestor(
                previous_instance_id,
                candidate.instance_id,
            ):
                return ()
            return None
        required_type = obligation.ordered_stage_types[order_index]
        required_stage_roots = stage_anchors[order_index]
        for step in lineage_steps:
            if step.step_id in selected_step_ids:
                continue
            if step.output_type != required_type:
                continue
            if not required_stage_roots <= step.root_input_keys:
                continue
            if previous_instance_id is not None and not is_ancestor(
                previous_instance_id,
                step.output_instance_id,
            ):
                continue
            suffix = choose_stage_path(
                order_index + 1,
                step.output_instance_id,
                selected_step_ids | {step.step_id},
            )
            if suffix is not None:
                return (step,) + suffix
        return None

    selected = choose_stage_path(0, None, frozenset())
    if selected is None:
        return None
    return tuple(
        DerivedObligation(
            required_type.semantic_type,
            step.output_instance_id,
            step.step_id,
            order_index,
        )
        for order_index, (required_type, step) in enumerate(
            zip(obligation.ordered_stage_types, selected)
        )
    )


def _required_evidence_needs_output(
    goal: SolverVisibleGoal,
    output: TrackedArtifact,
    artifacts: Mapping[str, TrackedArtifact],
) -> bool:
    """Allow a provenance-bearing duplicate when it closes an evidence obligation."""
    return _missing_derived_evidence(goal, artifacts)[output.artifact.semantic_type] > 0


def _candidate_ready_for_priority(
    goal: SolverVisibleGoal,
    artifacts: Mapping[str, TrackedArtifact],
) -> bool:
    target_type = goal.target.artifact_type
    if target_type is not None and any(
        tracked.artifact.artifact_type == target_type
        and goal.target.objective in tracked.producer_objectives
        for tracked in artifacts.values()
    ):
        return True
    if goal.family == "G4":
        counts = Counter(tracked.artifact.semantic_type for tracked in artifacts.values())
        return counts["BETTI_CURVE"] >= 2 and counts["EULER_CURVE"] >= 2
    if goal.family == "G5":
        levels = Counter(
            str(tracked.artifact.metadata_dict().get("level", "UNKNOWN"))
            for tracked in artifacts.values()
            if tracked.artifact.semantic_type == "GRAPH_SIGNATURE"
        )
        return any(
            levels[level] >= 2
            for level in ("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL")
        )
    return False


def _candidates_from_state(
    goal: SolverVisibleGoal,
    artifacts: Mapping[str, TrackedArtifact],
    counters: _WorkCounters | None = None,
    effective_root_types: Mapping[str, ArtifactType] | None = None,
) -> tuple[_CandidateChoice, ...]:
    target_type = goal.target.artifact_type
    if target_type is None:
        return ()
    rows = [
        _CandidateChoice(tracked)
        for _, tracked in sorted(artifacts.items())
        if tracked.artifact.artifact_type == target_type
        and goal.target.objective in tracked.producer_objectives
    ]
    contract = _PLANNER_COMPARISON_CONTRACTS.get(goal.family)
    if contract is not None and counters is not None:
        counters.attempted += 1
    effective_root_types = effective_root_types or {}
    comparison_artifacts = {
        key: _view_for_contract(
            tracked.artifact,
            effective_root_types.get(key, tracked.artifact.artifact_type),
        )
        for key, tracked in artifacts.items()
    }
    comparison = _comparison_candidate(goal, comparison_artifacts)
    if (
        contract is not None
        and comparison is not None
        and comparison.artifact_type == contract.output
        and target_type == contract.output
        and goal.target.objective == contract.objective
    ):
        if counters is not None:
            counters.executed += 1
        evidence_rows = tuple(
            (key, tracked, comparison_artifacts[key])
            for key, tracked in sorted(artifacts.items())
            if comparison_artifacts[key].semantic_type in contract.evidence_types
        )
        bound_inputs = {
            f"evidence_{index:03d}": tracked
            for index, (_, tracked, _) in enumerate(evidence_rows)
        }
        construction = _verify_comparison_candidate(
            contract,
            tuple(artifact for _, _, artifact in evidence_rows),
            comparison,
        )
        if counters is not None:
            counters.verified += 1
        if construction.passed:
            tracked_comparison, step = derive_artifact(
                operator_id=contract.operator_id,
                output=comparison,
                bound_inputs=bound_inputs,
                verifier=construction,
                objectives=(contract.objective,),
            )
            rows.append(_CandidateChoice(tracked_comparison, (step,), (construction,)))
    return tuple(sorted(rows, key=lambda choice: choice.tracked.instance_id))


def _comparison_candidate(goal: SolverVisibleGoal, artifacts: Mapping[str, Artifact]) -> Artifact | None:
    contract = _PLANNER_COMPARISON_CONTRACTS.get(goal.family)
    if contract is None:
        return None
    value_and_provenance = _comparison_value(goal.family, artifacts)
    if value_and_provenance is None:
        return None
    value, provenance = value_and_provenance
    return Artifact(
        artifact_id=f"candidate:{goal.goal_id}:comparison:{value.get('level', 'unknown')}",
        semantic_type=contract.output.semantic_type,
        representation_class=contract.output.representation_class,
        value=value,
        exactness_class=contract.output.exactness_class,
        provenance=provenance,
    )


def _comparison_value(
    family: str,
    artifacts: Mapping[str, Artifact],
) -> tuple[dict[str, Any], tuple[str, ...]] | None:
    if family == "G4":
        by_type: dict[str, list[Artifact]] = defaultdict(list)
        for artifact in artifacts.values():
            if artifact.semantic_type in {"BETTI_CURVE", "EULER_CURVE"}:
                by_type[artifact.semantic_type].append(artifact)
        if len(by_type["BETTI_CURVE"]) < 2 or len(by_type["EULER_CURVE"]) < 2:
            return None
        barcodes = sorted(
            (artifact for artifact in artifacts.values() if artifact.semantic_type == "BARCODE"),
            key=lambda artifact: artifact.artifact_id,
        )
        if len(barcodes) < 2:
            return None

        # Curves emitted by primitive operators may use each barcode's local
        # endpoint grid.  Comparing those tuples directly is unsound (notably
        # when one barcode is empty).  Recompute both representations on one
        # common grid, matching the independent terminal authority.
        barcode_values = tuple(
            normalize_historical_barcode(artifact.value)
            for artifact in barcodes[:2]
        )
        grid = tuple(sorted({
            endpoint
            for barcode in barcode_values
            for _, birth, death in barcode
            for endpoint in (birth, death)
        }))
        degrees = tuple(sorted({
            degree
            for barcode in barcode_values
            for degree, _, _ in barcode
        }))

        def common_betti(barcode: tuple[Any, ...]) -> tuple[tuple[int, ...], ...]:
            return tuple(
                tuple(
                    sum(
                        interval_degree == degree and birth <= point < death
                        for interval_degree, birth, death in barcode
                    )
                    for degree in degrees
                )
                for point in grid
            )

        betti_values = tuple(common_betti(barcode) for barcode in barcode_values)
        euler_values = tuple(
            tuple(
                sum((-1) ** degree * count for degree, count in zip(degrees, row))
                for row in curve
            )
            for curve in betti_values
        )
        euler = sorted(by_type["EULER_CURVE"], key=lambda artifact: artifact.artifact_id)[:2]
        betti = sorted(by_type["BETTI_CURVE"], key=lambda artifact: artifact.artifact_id)[:2]
        if euler_values[0] != euler_values[1]:
            level = "EULER"
        elif betti_values[0] != betti_values[1]:
            level = "BETTI"
        else:
            level = "BARCODE" if barcode_values[0] != barcode_values[1] else "NONE"
        return (
            {"level": level, "distinct": level != "NONE"},
            tuple(a.artifact_id for a in euler + betti),
        )

    if family == "G5":
        signatures = [a for a in artifacts.values() if a.semantic_type == "GRAPH_SIGNATURE"]
        by_level: dict[str, list[Artifact]] = defaultdict(list)
        for artifact in signatures:
            by_level[str(artifact.metadata_dict().get("level", "UNKNOWN"))].append(artifact)
        for level in ("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL"):
            rows = by_level[level]
            if len(rows) >= 2 and rows[0].value != rows[1].value:
                return (
                    {"distinct": True},
                    tuple(row.artifact_id for row in rows[:2]),
                )
        if all(len(by_level[level]) >= 2 for level in ("EULER_BETTI", "DEGREE", "LAPLACIAN", "WL")):
            return (
                {"distinct": False},
                tuple(a.artifact_id for a in signatures),
            )
    return None


def _verify_comparison_candidate(
    contract: _PlannerComparisonContract,
    inputs: tuple[Artifact, ...],
    output: Artifact,
) -> VerificationResult:
    expected = _comparison_value(
        contract.family,
        {f"evidence_{index:03d}": artifact for index, artifact in enumerate(inputs)},
    )
    passed = (
        expected is not None
        and output.artifact_type == contract.output
        and output.value == expected[0]
    )
    return VerificationResult(
        passed,
        "PLANNER_COMPARISON_CONSTRUCTION",
        f"registered {contract.family} comparison contract",
        stage="OPERATOR",
        subject_id=contract.operator_id,
        evidence=(("registered_implementation_id", contract.verifier_id),),
    )


def verify_terminal_candidate(
    goal: SolverVisibleGoal,
    candidate: Artifact,
) -> VerificationResult:
    """Run the registered, root-recomputed terminal authority.

    Historical families are dispatched through the closed G1--G12 contract
    registry.  The seven prospective v0.20 families are dispatched through
    their separate strict typed-certificate authority.  Every other family
    fails closed; there is no permissive terminal fallback.
    """
    if type(goal) is not SolverVisibleGoal or type(candidate) is not Artifact:
        return VerificationResult(
            False,
            "UNSUPPORTED_TERMINAL_VERIFIER",
            "goal and candidate must have exact public types",
        )
    if goal.family in {f"G{index}" for index in range(1, 13)}:
        return verify_historical_goal(goal, candidate)
    if goal.family in NEW_V0_20_FAMILIES:
        return verify_v0_20_goal(goal, candidate)
    return VerificationResult(
        False,
        "UNSUPPORTED_TERMINAL_VERIFIER",
        f"no registered strict terminal verifier for {goal.family}",
    )


# Private compatibility alias retained for instrumentation in older tests.
_verify_goal = verify_terminal_candidate


def _terminal_goal_view(
    goal: SolverVisibleGoal,
    effective_root_types: Mapping[str, ArtifactType],
    routing_receipt: RoutingReceipt,
) -> tuple[SolverVisibleGoal | None, str | None]:
    """Bind inferred root labels to a self-consistent routing receipt.

    Retyping changes only the semantic contract presented to the terminal
    verifier; values, artifact identities, metadata, and all mathematical roots
    remain byte-for-byte/canonically identical to the solver-owned snapshot.
    """
    if type(routing_receipt) is not RoutingReceipt:
        return None, "routing receipt must have the exact public type"
    if routing_receipt.typing_mode not in {"INFERRED", "HYBRID"}:
        return None, "routing receipt has an invalid typing mode"
    inferred_rows = routing_receipt.inferred_root_types
    if (
        type(inferred_rows) is not tuple
        or any(
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or type(row[1]) is not ArtifactType
            for row in inferred_rows
        )
    ):
        return None, "routing receipt has malformed inferred root types"
    inferred = dict(inferred_rows)
    if len(inferred) != len(inferred_rows) or set(inferred) != set(goal.inputs):
        return None, "routing receipt root keys do not exactly match the goal"
    try:
        expected_decision_digest = canonical_sha256(
            {
                "inferred_root_types": inferred_rows,
                "ordered_operator_ids": routing_receipt.ordered_operator_ids,
                "ambiguous_input_keys": routing_receipt.ambiguous_input_keys,
                "compatibility_model_digest": routing_receipt.compatibility_model_digest,
            },
            domain="pct-routing-decision-v1",
        )
    except Exception as exc:
        return None, (
            "routing receipt is noncanonical: "
            f"{_safe_exception_text(exc)}"
        )
    if expected_decision_digest != routing_receipt.decision_digest:
        return None, "routing decision digest mismatch"
    terminal_ambiguities = tuple(
        key
        for key in routing_receipt.ambiguous_input_keys
        if routing_receipt.typing_mode == "INFERRED"
        or goal.inputs[key].semantic_type == "BLINDED_INPUT_TYPE"
    )
    if terminal_ambiguities:
        return None, "ambiguous routing receipt cannot authorize terminal retyping"
    if set(effective_root_types) != set(goal.inputs):
        return None, "effective root types do not exactly cover the goal"
    if routing_receipt.typing_mode == "INFERRED":
        if dict(effective_root_types) != inferred:
            return None, "effective inferred types disagree with the routing receipt"
    else:
        for key, artifact in goal.inputs.items():
            expected = (
                inferred[key]
                if artifact.semantic_type == "BLINDED_INPUT_TYPE"
                else artifact.artifact_type
            )
            if effective_root_types[key] != expected or (
                artifact.semantic_type != "BLINDED_INPUT_TYPE"
                and inferred[key] != artifact.artifact_type
            ):
                return None, f"hybrid type conflict for root {key}"
    typed_inputs = {
        key: _view_for_contract(goal.inputs[key], effective_root_types[key])
        for key in sorted(goal.inputs)
    }
    return replace(goal, inputs=typed_inputs), None


def _node_priority(goal: SolverVisibleGoal, node: _SearchNode) -> tuple[Any, ...]:
    mapping = node.tracked_mapping()
    candidate_missing = int(not _candidate_ready_for_priority(goal, mapping))
    evidence_missing = sum(_missing_derived_evidence(goal, mapping).values())
    unresolved = candidate_missing + evidence_missing
    derived_count = sum(key.startswith("derived:") for key in mapping)
    return (unresolved, node.cost, derived_count, len(node.path), node.path)


@dataclass
class _WorkCounters:
    attempted: int = 0
    executed: int = 0
    verified: int = 0


_KNOWN_VERIFIER_CLASSES = frozenset(
    {
        "EXACT_EQUALITY",
        "EXACT_LINEAR_ALGEBRA",
        "CHAIN_RESIDUAL",
        "GRAPH_ISOMORPHISM_CONTROL",
        "SYMBOLIC_IDENTITY",
        "NUMERIC_THEN_SYMBOLIC",
        "GEOMETRIC_NUMERICAL",
        "SPECTRAL_NUMERICAL",
        "NUMERIC_RESIDUAL_WITHIN_TOLERANCE",
        "CERTIFIED_INTERVAL",
        STRICT_V0_20_VERIFIER_CLASS,
    }
)

_TERMINAL_VERIFIER_CLASS_BY_FAMILY = {
    "G1": "EXACT_EQUALITY",
    "G2": "EXACT_LINEAR_ALGEBRA",
    "G3": "CHAIN_RESIDUAL",
    "G4": "EXACT_EQUALITY",
    "G5": "GRAPH_ISOMORPHISM_CONTROL",
    "G6": "EXACT_LINEAR_ALGEBRA",
    "G7": "SYMBOLIC_IDENTITY",
    "G8": "NUMERIC_THEN_SYMBOLIC",
    "G9": "GEOMETRIC_NUMERICAL",
    "G10": "SPECTRAL_NUMERICAL",
    "G11": "GEOMETRIC_NUMERICAL",
    "G12": "SYMBOLIC_IDENTITY",
    **{family: STRICT_V0_20_VERIFIER_CLASS for family in NEW_V0_20_FAMILIES},
}

_TERMINAL_VERIFIER_IMPLEMENTATION_BY_FAMILY = {
    family: f"pct.goal-verifier.{family.lower()}.v1"
    for family in _TERMINAL_VERIFIER_CLASS_BY_FAMILY
}
_TERMINAL_VERIFIER_IMPLEMENTATION_BY_FAMILY.update(
    {
        family: "pct.v0_20_verifiers.verify_v0_20_goal.v1"
        for family in NEW_V0_20_FAMILIES
    }
)


def _validate_named_metadata(
    rows: Any,
    *,
    label: str,
) -> str | None:
    if type(rows) is not tuple:
        return f"{label} must be a tuple"
    keys: list[str] = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            return f"{label} rows must be two-tuples"
        key, value = row
        if type(key) is not str or not key:
            return f"{label} keys must be nonempty strings"
        keys.append(key)
        try:
            canonical_sha256(value, domain=f"pct-{label}-value-v1")
        except Exception as exc:
            return (
                f"{label} value for {key!r} is not canonical: "
                f"{_safe_exception_text(exc)}"
            )
    if len(keys) != len(set(keys)):
        return f"{label} contains duplicate keys"
    return None


_BOOLEAN_CONSTRAINTS = frozenset(
    {
        "allow_exact_escalation",
        "area_normalize",
        "localize_if_invalid",
        "require_unique",
        "requires_convexity",
    }
)
_TEXT_CONSTRAINTS = frozenset(
    {
        "exactness_target",
        "flow_parameter",
        "relation_form",
    }
)
_POSITIVE_INTEGER_CONSTRAINTS = frozenset({"lattice_rank", "samples"})
_TEXT_TUPLE_CONSTRAINTS = frozenset(
    {
        "levels",
        "required_derived_types",
        "signature_bank",
        "symbols",
    }
)


def _validate_known_constraint_shapes(rows: tuple[tuple[str, Any], ...]) -> str | None:
    for key, value in rows:
        if key in _BOOLEAN_CONSTRAINTS and type(value) is not bool:
            return f"goal constraint {key!r} must be an exact bool"
        if key in _TEXT_CONSTRAINTS and (type(value) is not str or not value):
            return f"goal constraint {key!r} must be a nonempty exact string"
        if key in _POSITIVE_INTEGER_CONSTRAINTS and (
            type(value) is not int or value <= 0
        ):
            return f"goal constraint {key!r} must be a positive exact integer"
        if key in _TEXT_TUPLE_CONSTRAINTS:
            if type(value) is not tuple or any(
                type(item) is not str or not item for item in value
            ):
                return f"goal constraint {key!r} must be a tuple of nonempty exact strings"
            if key != "required_derived_types" and not value:
                return f"goal constraint {key!r} must not be empty"
        if key == "tolerance" and (
            type(value) is not float
            or not math.isfinite(value)
            or value < 0.0
        ):
            return "goal constraint 'tolerance' must be a finite nonnegative exact float"
    return None


def _validate_goal_schema(goal: SolverVisibleGoal) -> str | None:
    if type(goal) is not SolverVisibleGoal:
        return "goal must be an exact SolverVisibleGoal"
    for label, value in (
        ("goal_id", goal.goal_id),
        ("family", goal.family),
        ("required_verifier_class", goal.required_verifier_class),
    ):
        if type(value) is not str or not value:
            return f"{label} must be a nonempty string"
    if type(goal.search_budget) is not int:
        return "search_budget must be an exact integer"
    if type(goal.allowed_numeric_tolerance) is not float:
        return "allowed_numeric_tolerance must be an exact float"
    if not math.isfinite(goal.allowed_numeric_tolerance) or goal.allowed_numeric_tolerance < 0.0:
        return "allowed_numeric_tolerance must be finite and nonnegative"
    if type(goal.inputs) is not dict or not goal.inputs:
        return "inputs must be a nonempty dictionary"
    for input_key, artifact in goal.inputs.items():
        if type(input_key) is not str or not input_key:
            return "input keys must be nonempty strings"
        if type(artifact) is not Artifact:
            return f"input {input_key!r} must be an exact Artifact"
        for label, value in (
            ("artifact_id", artifact.artifact_id),
            ("semantic_type", artifact.semantic_type),
            ("representation_class", artifact.representation_class),
            ("exactness_class", artifact.exactness_class),
        ):
            if type(value) is not str or not value:
                return f"input {input_key!r} {label} must be a nonempty string"
        if artifact.exactness_class not in EXACTNESS_CLASSES:
            return f"input {input_key!r} exactness_class is not registered"
        metadata_error = _validate_named_metadata(
            artifact.metadata,
            label=f"input-{input_key}-metadata",
        )
        if metadata_error is not None:
            return metadata_error
        if type(artifact.provenance) is not tuple or any(
            type(value) is not str or not value for value in artifact.provenance
        ):
            return f"input {input_key!r} provenance must be a tuple of nonempty strings"
    if type(goal.target) is not TargetSpec:
        return "target must be an exact TargetSpec"
    for label, value in (
        ("target_id", goal.target.target_id),
        ("target.semantic_type", goal.target.semantic_type),
        ("target.representation_class", goal.target.representation_class),
        ("target.objective", goal.target.objective),
    ):
        if type(value) is not str or not value:
            return f"{label} must be a nonempty string"
    if goal.target.exactness_class is not None and (
        type(goal.target.exactness_class) is not str
        or goal.target.exactness_class not in EXACTNESS_CLASSES
    ):
        return "target.exactness_class must be a registered exactness string or None"
    target_metadata_error = _validate_named_metadata(
        goal.target.metadata,
        label="target-metadata",
    )
    if target_metadata_error is not None:
        return target_metadata_error
    constraint_error = _validate_named_metadata(
        goal.constraints,
        label="goal-constraints",
    )
    if constraint_error is not None:
        return constraint_error
    known_constraint_error = _validate_known_constraint_shapes(goal.constraints)
    if known_constraint_error is not None:
        return known_constraint_error
    obligation = goal.lineage_obligation
    if obligation is not None:
        if type(obligation) is not CandidateLineageObligation:
            return "lineage_obligation must be an exact CandidateLineageObligation"
        if type(obligation.required_input_keys) is not frozenset or any(
            type(key) is not str or not key for key in obligation.required_input_keys
        ):
            return "lineage required_input_keys must be a frozenset of nonempty strings"
        if not obligation.required_input_keys <= frozenset(goal.inputs):
            return "lineage required_input_keys must refer to declared inputs"
        if type(obligation.ordered_stage_types) is not tuple or any(
            type(stage_type) is not ArtifactType
            for stage_type in obligation.ordered_stage_types
        ):
            return "lineage ordered_stage_types must contain exact ArtifactType values"
        if type(obligation.stage_required_input_keys) is not tuple:
            return "lineage stage_required_input_keys must be a tuple"
        if obligation.stage_required_input_keys and len(
            obligation.stage_required_input_keys
        ) != len(obligation.ordered_stage_types):
            return "lineage stage root anchors must parallel ordered_stage_types"
        for stage_roots in obligation.stage_required_input_keys:
            if type(stage_roots) is not frozenset or any(
                type(key) is not str or not key for key in stage_roots
            ):
                return "lineage stage root anchors must be frozensets of nonempty strings"
            if not stage_roots <= frozenset(goal.inputs):
                return "lineage stage root anchors must refer to declared inputs"
    return None


def _registry_digest(registry: Mapping[str, OperatorSpec]) -> str:
    return canonical_sha256(
        {
            "operator_registry_digest": operator_registry_digest(registry),
            "terminal_verifiers": _TERMINAL_VERIFIER_IMPLEMENTATION_BY_FAMILY,
            "terminal_verifier_code_digest": callable_contract_digest(
                _verify_goal,
                implementation_id="pct.goal-verifier.dispatch.v1",
            ),
            "comparison_contracts": tuple(
                (
                    family,
                    contract.operator_id,
                    contract.output,
                    contract.objective,
                    contract.evidence_types,
                    contract.verifier_id,
                )
                for family, contract in sorted(_PLANNER_COMPARISON_CONTRACTS.items())
            ),
            "comparison_code_digest": callable_contract_digest(
                _comparison_candidate,
                implementation_id="pct.planner-comparison.dispatch.v1",
            ),
            "comparison_verifier_code_digest": callable_contract_digest(
                _verify_comparison_candidate,
                implementation_id="pct.planner-comparison.verifier-dispatch.v1",
            ),
        },
        domain="pct-registry-contract-v2",
    )


def _candidate_lineage(
    candidate: TrackedArtifact | None,
    registry: Mapping[str, OperatorSpec],
    goal: SolverVisibleGoal,
    derived_obligations: tuple[DerivedObligation, ...],
) -> LineageReceipt | None:
    if candidate is None:
        return None
    return LineageReceipt(
        candidate_instance_id=candidate.instance_id,
        root_input_keys=candidate.root_input_keys,
        stage_instance_ids=tuple(
            obligation.artifact_instance_id for obligation in derived_obligations
        ),
        registry_digest=_registry_digest(registry),
        obligation_digest=canonical_sha256(
            {"goal_id": goal.goal_id, "lineage_obligation": goal.lineage_obligation},
            domain="pct-goal-obligation-v1",
        ),
    )


def _derived_artifact_records(
    node: _SearchNode,
    candidate: TrackedArtifact | None,
) -> tuple[DerivedArtifactRecord, ...]:
    by_instance = {
        tracked.instance_id: tracked
        for _, tracked in node.artifacts
    }
    if candidate is not None:
        by_instance[candidate.instance_id] = candidate
    records: list[DerivedArtifactRecord] = []
    for step in node.derivations:
        tracked = by_instance.get(step.output_instance_id)
        if tracked is None:
            continue
        records.append(
            DerivedArtifactRecord(
                instance_id=tracked.instance_id,
                derivation_step_id=step.step_id,
                artifact=tracked.artifact,
            )
        )
    return tuple(records)


def _make_trace(
    goal: SolverVisibleGoal,
    mode: str,
    node: _SearchNode,
    *,
    expanded: int,
    candidate: TrackedArtifact | None,
    verdict: str,
    registry: Mapping[str, OperatorSpec],
    counters: _WorkCounters,
    root_origins: tuple[RootOrigin, ...],
    events: tuple[tuple[str, Any], ...],
    terminal_verifier: VerificationResult | None = None,
    path_suffix: tuple[str, ...] = (),
    reason: str = "",
    refusal: Refusal | None = None,
    derived_obligations: tuple[DerivedObligation, ...] = (),
    routing_receipt: RoutingReceipt | None = None,
) -> SolveTrace:
    verifiers = node.verifiers + ((terminal_verifier,) if terminal_verifier is not None else ())
    return SolveTrace(
        goal_id=goal.goal_id,
        mode=mode,
        operator_path=node.path + path_suffix,
        expanded_state_count=expanded,
        primitive_execution_count=counters.executed,
        macro_ids=(),
        candidate_artifact=candidate.artifact if candidate is not None else None,
        verifier_chain=verifiers,
        falsification_events=events,
        final_verdict=verdict,
        failure_reason=reason,
        refusal=refusal,
        root_origins=root_origins,
        derivations=tuple(node.derivations),
        derived_artifacts=_derived_artifact_records(node, candidate),
        derived_obligations=derived_obligations,
        candidate_lineage=_candidate_lineage(candidate, registry, goal, derived_obligations),
        macro_bindings=(),
        attempted_operator_count=counters.attempted,
        verifier_execution_count=counters.verified,
        routing_receipt=routing_receipt,
    )


def _ordered_operator_ids(
    typing_mode: str,
    registry: Mapping[str, OperatorSpec],
    routing_order: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if typing_mode == "EXPLICIT":
        return tuple(sorted(registry))
    if routing_order is None:
        raise ValueError(f"{typing_mode} mode requires a routing decision")
    return routing_order


def _routing_decision_error(
    decision: object,
    goal: SolverVisibleGoal,
    registry: Mapping[str, OperatorSpec],
    compatibility_model: object,
) -> str | None:
    """Validate an untrusted compatibility decision before using any field."""

    if type(compatibility_model) is not CompatibilityModel:
        return "compatibility model must be an exact CompatibilityModel"
    if type(decision) is not RoutingDecision:
        return "routing decision must be an exact RoutingDecision"
    rows = decision.inferred_root_types
    if type(rows) is not tuple or len(rows) != len(goal.inputs):
        return "inferred root types must be a complete tuple"
    inferred: dict[str, ArtifactType] = {}
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            return "inferred root type rows must be two-tuples"
        key, artifact_type = row
        if type(key) is not str or not key or key in inferred:
            return "inferred root keys must be unique nonempty strings"
        if type(artifact_type) is not ArtifactType:
            return "inferred root values must be exact ArtifactType values"
        if any(
            type(value) is not str or not value
            for value in (
                artifact_type.semantic_type,
                artifact_type.representation_class,
                artifact_type.exactness_class,
            )
        ) or artifact_type.exactness_class not in EXACTNESS_CLASSES:
            return "inferred root artifact type fields must be registered strings"
        inferred[key] = artifact_type
    if set(inferred) != set(goal.inputs):
        return "inferred root keys must exactly match goal inputs"
    for key, artifact_type in inferred.items():
        root = goal.inputs[key]
        if (
            artifact_type.representation_class != root.representation_class
            or artifact_type.exactness_class != root.exactness_class
        ):
            return "inference may not alter structural root classes"

    order = decision.ordered_operator_ids
    if (
        type(order) is not tuple
        or any(type(operator_id) is not str or not operator_id for operator_id in order)
        or len(order) != len(set(order))
        or len(order) != len(registry)
        or set(order) != set(registry)
    ):
        return "operator order must be a duplicate-free permutation of the live registry"
    ambiguous = decision.ambiguous_input_keys
    if (
        type(ambiguous) is not tuple
        or any(type(key) is not str or not key for key in ambiguous)
        or len(ambiguous) != len(set(ambiguous))
        or not set(ambiguous) <= set(goal.inputs)
    ):
        return "ambiguous input keys must be a unique subset of goal inputs"
    try:
        model_digest = compatibility_model.model_digest
    except Exception:
        return "compatibility model digest is unavailable"
    if (
        type(decision.compatibility_model_digest) is not str
        or len(decision.compatibility_model_digest) != 64
        or decision.compatibility_model_digest != model_digest
    ):
        return "compatibility model digest mismatch"
    try:
        expected_decision_digest = canonical_sha256(
            {
                "inferred_root_types": rows,
                "ordered_operator_ids": order,
                "ambiguous_input_keys": ambiguous,
                "compatibility_model_digest": model_digest,
            },
            domain="pct-routing-decision-v1",
        )
    except Exception as exc:
        return (
            "routing decision is noncanonical: "
            f"{_safe_exception_text(exc)}"
        )
    if (
        type(decision.decision_digest) is not str
        or len(decision.decision_digest) != 64
        or any(
            character not in "0123456789abcdef"
            for character in decision.decision_digest
        )
        or decision.decision_digest != expected_decision_digest
    ):
        return "routing decision digest mismatch"
    try:
        authoritative = authoritative_routing_decision(
            compatibility_model,
            goal.inputs,
            registry,
        )
    except Exception:
        return "authoritative routing decision could not be recomputed"
    if decision != authoritative:
        return "routing decision differs from authoritative model derivation"
    return None


def _decorate_step_verifier(result: VerificationResult, operator_id: str) -> VerificationResult:
    return replace(result, stage="OPERATOR", subject_id=operator_id)


def _root_integrity_failure(artifacts: Mapping[str, TrackedArtifact]) -> tuple[str, str] | None:
    for tracked in artifacts.values():
        if not isinstance(tracked.origin, RootOrigin):
            continue
        observed = artifact_content_digest(tracked.artifact)
        if observed != tracked.origin.content_digest:
            return tracked.origin.input_key, observed
    return None


def _invocation_digest(invocation: Any, *, domain: str) -> str:
    return canonical_sha256(invocation, domain=domain)


def _transition_children(
    *,
    goal: SolverVisibleGoal,
    node: _SearchNode,
    spec: OperatorSpec,
    bindings: tuple[tuple[str, Any], ...],
    effective_root_types: Mapping[str, ArtifactType],
    counters: _WorkCounters,
    events: list[tuple[str, Any]],
) -> tuple[_SearchNode, ...]:
    artifacts = node.tracked_mapping()
    children: list[_SearchNode] = []
    port_bindings = _tracked_port_bindings(spec, artifacts, effective_root_types)
    for invocation, tracked_inputs in port_bindings:
        counters.attempted += 1
        try:
            applicability_inputs = deepcopy(invocation)
            applicability_before = _invocation_digest(
                applicability_inputs,
                domain="pct-applicability-input-v1",
            )
        except Exception as exc:
            events.append(
                (
                    "APPLICABILITY_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        try:
            applicability = spec.applicability(applicability_inputs, deepcopy(bindings))
        except Exception as exc:
            events.append(
                (
                    "APPLICABILITY_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        try:
            applicability_after = _invocation_digest(
                applicability_inputs,
                domain="pct-applicability-input-v1",
            )
        except Exception as exc:
            events.append(
                (
                    "APPLICABILITY_INPUT_MUTATION",
                    {
                        "operator_id": spec.operator_id,
                        "reason": (
                            "applicability produced noncanonical input evidence: "
                            f"{_safe_exception_text(exc)}"
                        ),
                    },
                )
            )
            continue
        if applicability_after != applicability_before:
            events.append(
                (
                    "APPLICABILITY_INPUT_MUTATION",
                    {"operator_id": spec.operator_id, "reason": "applicability mutated isolated inputs"},
                )
            )
            continue
        try:
            valid_applicability = (
                type(applicability) is Applicability
                and type(applicability.verdict) is str
                and applicability.verdict in APPLICABILITY_VERDICTS
                and _is_bounded_text(applicability.reason)
            )
        except Exception:
            valid_applicability = False
        if not valid_applicability:
            events.append(
                (
                    "APPLICABILITY_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": "invalid applicability result fields",
                    },
                )
            )
            continue
        if not applicability.applicable:
            events.append(
                (
                    f"APPLICABILITY_{applicability.verdict}",
                    {"operator_id": spec.operator_id, "reason": applicability.reason},
                )
            )
            continue
        counters.executed += 1
        try:
            execution_inputs = deepcopy(invocation)
            execution_before = _invocation_digest(
                execution_inputs,
                domain="pct-execution-input-v1",
            )
        except Exception as exc:
            events.append(
                (
                    "EXECUTION_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        try:
            output = spec.execute(execution_inputs, deepcopy(bindings))
        except Exception as exc:
            events.append(
                (
                    "EXECUTION_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        try:
            execution_after = _invocation_digest(
                execution_inputs,
                domain="pct-execution-input-v1",
            )
        except Exception as exc:
            events.append(
                (
                    "OPERATOR_INPUT_MUTATION",
                    {
                        "operator_id": spec.operator_id,
                        "reason": (
                            "execution produced noncanonical input evidence: "
                            f"{_safe_exception_text(exc)}"
                        ),
                    },
                )
            )
            continue
        if execution_after != execution_before:
            events.append(
                (
                    "OPERATOR_INPUT_MUTATION",
                    {"operator_id": spec.operator_id, "reason": "execution mutated isolated inputs"},
                )
            )
            continue
        if type(output) is OperatorFailure:
            try:
                valid_failure = (
                    type(output.verdict) is str
                    and output.verdict in _OPERATOR_FAILURE_VERDICTS
                    and _is_bounded_text(output.reason)
                    and _is_bounded_text(output.operator_id, allow_empty=False)
                    and output.operator_id == spec.operator_id
                )
            except Exception:
                valid_failure = False
            if not valid_failure:
                events.append(
                    (
                        "EXECUTION_INVALID",
                        {
                            "operator_id": spec.operator_id,
                            "reason": "invalid operator failure result fields",
                        },
                    )
                )
                continue
            events.append(
                (
                    f"EXECUTION_{output.verdict}",
                    {"operator_id": spec.operator_id, "reason": output.reason},
                )
            )
            continue
        if type(output) is not Artifact:
            events.append(
                (
                    "EXECUTION_INVALID",
                    {"operator_id": spec.operator_id, "reason": "operator returned a non-artifact"},
                )
            )
            continue
        try:
            output = deepcopy(output)
        except Exception as exc:
            events.append(
                (
                    "NONCANONICAL_OPERATOR_EVIDENCE",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        if output.artifact_type != spec.output:
            events.append(
                (
                    "OUTPUT_CONTRACT_MISMATCH",
                    {
                        "operator_id": spec.operator_id,
                        "declared": spec.output,
                        "observed": output.artifact_type,
                    },
                )
            )
            continue
        try:
            _invocation_digest(output, domain="pct-operator-output-evidence-v1")
        except Exception as exc:
            events.append(
                (
                    "NONCANONICAL_OPERATOR_EVIDENCE",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        counters.verified += 1
        try:
            verifier_inputs = deepcopy(tuple(execution_inputs.values()))
            verifier_output = deepcopy(output)
            verifier_before = _invocation_digest(
                (verifier_inputs, verifier_output),
                domain="pct-verifier-input-v1",
            )
        except Exception as exc:
            events.append(
                (
                    "VERIFIER_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        try:
            raw_verifier = spec.verify(verifier_inputs, verifier_output)
        except Exception as exc:
            events.append(
                (
                    "VERIFIER_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        try:
            verifier_after = _invocation_digest(
                (verifier_inputs, verifier_output),
                domain="pct-verifier-input-v1",
            )
        except Exception as exc:
            events.append(
                (
                    "VERIFIER_INPUT_MUTATION",
                    {
                        "operator_id": spec.operator_id,
                        "reason": (
                            "verifier produced noncanonical input evidence: "
                            f"{_safe_exception_text(exc)}"
                        ),
                    },
                )
            )
            continue
        if verifier_after != verifier_before:
            events.append(
                (
                    "VERIFIER_INPUT_MUTATION",
                    {"operator_id": spec.operator_id, "reason": "verifier mutated isolated evidence"},
                )
            )
            continue
        if not _has_valid_verification_fields(raw_verifier):
            events.append(
                (
                    "VERIFIER_ERROR",
                    {
                        "operator_id": spec.operator_id,
                        "reason": "invalid verifier result fields",
                    },
                )
            )
            continue
        step_verifier = _decorate_step_verifier(raw_verifier, spec.operator_id)
        try:
            _invocation_digest(
                step_verifier,
                domain="pct-operator-verifier-evidence-v1",
            )
        except Exception as exc:
            events.append(
                (
                    "NONCANONICAL_OPERATOR_EVIDENCE",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        if not step_verifier.passed:
            events.append(
                (
                    "STEP_VERIFIER_REJECTED",
                    {"operator_id": spec.operator_id, "reason": step_verifier.reason},
                )
            )
            continue
        try:
            tracked_output, step = derive_artifact(
                operator_id=spec.operator_id,
                output=output,
                bound_inputs=tracked_inputs,
                verifier=step_verifier,
                objectives=spec.objectives,
            )
        except Exception as exc:
            events.append(
                (
                    "NONCANONICAL_OPERATOR_EVIDENCE",
                    {
                        "operator_id": spec.operator_id,
                        "reason": _safe_exception_text(exc),
                    },
                )
            )
            continue
        equivalent = _has_equivalent(goal, tracked_output, artifacts)
        if equivalent and not _required_evidence_needs_output(goal, tracked_output, artifacts):
            continue
        new_artifacts = dict(artifacts)
        new_artifacts[_derived_key(spec.operator_id, tracked_output, artifacts)] = tracked_output
        children.append(
            _SearchNode(
                artifacts=tuple(sorted(new_artifacts.items())),
                path=node.path + (spec.operator_id,),
                verifiers=node.verifiers + (step_verifier,),
                cost=node.cost + spec.cost,
                derivations=node.derivations + (step,),
            )
        )
    return tuple(children)


def solve(
    goal: SolverVisibleGoal,
    registry: Mapping[str, OperatorSpec],
    *,
    typing_mode: str = "EXPLICIT",
    compatibility_model: Any | None = None,
    macros: Iterable[Any] = (),
) -> SolveTrace:
    """Return the authoritative primitive result.

    ``macros`` is retained as an API-compatibility placeholder but is never
    inspected or executed.  Macro proposals are untrusted side-channel data;
    callers may inspect them *after* this function returns with
    ``macros.audit_macro_proposals``.  This ordering makes macro rescue
    impossible, including when the primitive search budget is insufficient.
    """

    if typing_mode not in {"EXPLICIT", "INFERRED", "HYBRID"}:
        raise ValueError(f"unknown typing mode: {typing_mode}")
    if typing_mode != "EXPLICIT" and compatibility_model is None:
        raise ValueError(f"{typing_mode} mode requires a compatibility model")

    # Do not iterate, sort, inspect, or otherwise execute caller-controlled
    # macro values on the authoritative solve path.
    mode = f"{typing_mode}/PRIMITIVE"

    schema_error = _validate_goal_schema(goal)
    if schema_error is not None:
        goal_id = (
            goal.goal_id
            if type(goal) is SolverVisibleGoal
            and type(goal.goal_id) is str
            and goal.goal_id
            else "INVALID_GOAL"
        )
        return SolveTrace(
            goal_id=goal_id,
            mode=mode,
            operator_path=(),
            expanded_state_count=0,
            primitive_execution_count=0,
            macro_ids=(),
            candidate_artifact=None,
            verifier_chain=(),
            falsification_events=(("INVALID_GOAL_SCHEMA", {"reason": schema_error}),),
            final_verdict="INVALID",
            failure_reason=schema_error,
            refusal=Refusal("INVALID_GOAL_SCHEMA", schema_error),
        )

    # The solver owns an immutable-by-isolation snapshot. Operator code never
    # receives an alias to the caller's problem statement.
    try:
        goal = replace(
            goal,
            inputs=deepcopy(goal.inputs),
            target=deepcopy(goal.target),
            constraints=deepcopy(goal.constraints),
            lineage_obligation=deepcopy(goal.lineage_obligation),
        )
        tracked_roots = track_roots(goal.inputs)
    except Exception as exc:
        reason = _safe_exception_text(exc)
        return SolveTrace(
            goal_id=goal.goal_id,
            mode=mode,
            operator_path=(),
            expanded_state_count=0,
            primitive_execution_count=0,
            macro_ids=(),
            candidate_artifact=None,
            verifier_chain=(),
            falsification_events=(("NONCANONICAL_ROOT", {"reason": reason}),),
            final_verdict="INVALID",
            failure_reason=reason,
            refusal=Refusal("NONCANONICAL_ROOT", reason),
        )
    root_origins = tuple(
        tracked.origin for _, tracked in tracked_roots if isinstance(tracked.origin, RootOrigin)
    )
    initial = _SearchNode(tracked_roots, (), (), 0)
    counters = _WorkCounters()
    events: list[tuple[str, Any]] = []
    routing_receipt: RoutingReceipt | None = None

    def finish(
        node: _SearchNode,
        *,
        expanded: int,
        candidate: TrackedArtifact | None,
        verdict: str,
        code: str | None = None,
        reason: str = "",
        terminal: VerificationResult | None = None,
        suffix: tuple[str, ...] = (),
        operator_id: str | None = None,
        obligations: tuple[DerivedObligation, ...] = (),
    ) -> SolveTrace:
        refusal = Refusal(code, reason, operator_id) if code is not None else None
        return _make_trace(
            goal,
            mode,
            node,
            expanded=expanded,
            candidate=candidate,
            verdict=verdict,
            registry=registry,
            counters=counters,
            root_origins=root_origins,
            events=tuple(events),
            terminal_verifier=terminal,
            path_suffix=suffix,
            reason=reason,
            refusal=refusal,
            derived_obligations=obligations,
            routing_receipt=routing_receipt,
        )

    schema_error = _validate_goal_schema(goal)
    if schema_error is not None:
        return finish(
            initial,
            expanded=0,
            candidate=None,
            verdict="INVALID",
            code="INVALID_GOAL_SCHEMA",
            reason=schema_error,
        )
    comparison_contract = _PLANNER_COMPARISON_CONTRACTS.get(goal.family)
    if comparison_contract is not None and (
        goal.target.artifact_type != comparison_contract.output
        or goal.target.objective != comparison_contract.objective
    ):
        return finish(
            initial,
            expanded=0,
            candidate=None,
            verdict="INVALID",
            code="GOAL_TARGET_CONTRACT_MISMATCH",
            reason=(
                f"expected {comparison_contract.output}/{comparison_contract.objective}; "
                f"received {goal.target.artifact_type}/{goal.target.objective}"
            ),
        )

    if goal.target.artifact_type is None:
        return finish(
            initial,
            expanded=0,
            candidate=None,
            verdict="INVALID",
            code="INCOMPLETE_TARGET_CONTRACT",
            reason="target exactness is required",
        )
    expected_verifier_class = _TERMINAL_VERIFIER_CLASS_BY_FAMILY.get(goal.family)
    if expected_verifier_class is None:
        return finish(
            initial,
            expanded=0,
            candidate=None,
            verdict="INVALID",
            code="UNSUPPORTED_GOAL_VERIFIER",
            reason=goal.family,
        )
    if goal.required_verifier_class not in _KNOWN_VERIFIER_CLASSES:
        return finish(
            initial,
            expanded=0,
            candidate=None,
            verdict="INVALID",
            code="UNKNOWN_VERIFIER_CLASS",
            reason=goal.required_verifier_class,
        )
    if goal.required_verifier_class != expected_verifier_class:
        return finish(
            initial,
            expanded=0,
            candidate=None,
            verdict="INVALID",
            code="VERIFIER_CONTRACT_MISMATCH",
            reason=f"expected {expected_verifier_class}; received {goal.required_verifier_class}",
        )
    if typing_mode == "EXPLICIT" and (
        goal.family in {f"G{index}" for index in range(1, 13)}
        or goal.family in NEW_V0_20_FAMILIES
    ):
        contract_check = (
            validate_historical_goal_contract(goal)
            if goal.family.startswith("G")
            else validate_v0_20_goal_contract(goal)
        )
        if not contract_check.passed:
            return finish(
                initial,
                expanded=0,
                candidate=None,
                verdict="INVALID",
                code="INVALID_GOAL_CONTRACT",
                reason=contract_check.reason,
            )
    if goal.search_budget <= 0:
        return finish(
            initial,
            expanded=0,
            candidate=None,
            verdict="NOT_ESTABLISHED",
            code="SEARCH_BUDGET_EXHAUSTED",
            reason="SEARCH_BUDGET_EXHAUSTED",
        )

    effective_root_types: dict[str, ArtifactType] = {}
    routing_order: tuple[str, ...] | None = None
    if typing_mode != "EXPLICIT":
        if type(compatibility_model) is not CompatibilityModel:
            return finish(
                initial,
                expanded=0,
                candidate=None,
                verdict="INVALID",
                code="INVALID_COMPATIBILITY_MODEL",
                reason="compatibility model must be an exact CompatibilityModel",
            )
        try:
            decision = compatibility_model.routing_decision(goal.inputs, registry)
        except Exception as exc:
            try:
                declared_code = getattr(exc, "refusal_code", "ROUTING_ERROR")
            except BaseException:
                declared_code = "ROUTING_ERROR"
            refusal_code = (
                declared_code
                if type(declared_code) is str and declared_code
                else "ROUTING_ERROR"
            )
            return finish(
                initial,
                expanded=0,
                candidate=None,
                verdict="INVALID",
                code=refusal_code,
                reason=_safe_exception_text(exc),
            )
        routing_error = _routing_decision_error(
            decision,
            goal,
            registry,
            compatibility_model,
        )
        if routing_error is not None:
            return finish(
                initial,
                expanded=0,
                candidate=None,
                verdict="INVALID",
                code="INVALID_ROUTING_DECISION",
                reason=routing_error,
            )
        inferred = dict(decision.inferred_root_types)
        routing_order = decision.ordered_operator_ids
        routing_receipt = RoutingReceipt(
            typing_mode,
            decision.inferred_root_types,
            decision.ordered_operator_ids,
            decision.ambiguous_input_keys,
            decision.compatibility_model_digest,
            decision.decision_digest,
        )
        ambiguous = tuple(
            key
            for key in decision.ambiguous_input_keys
            if typing_mode == "INFERRED" or goal.inputs[key].semantic_type == "BLINDED_INPUT_TYPE"
        )
        if ambiguous:
            return finish(
                initial,
                expanded=0,
                candidate=None,
                verdict="INVALID",
                code="AMBIGUOUS_TYPE_INFERENCE",
                reason=",".join(ambiguous),
            )
        if typing_mode == "INFERRED":
            effective_root_types = inferred
        else:
            for key, artifact in goal.inputs.items():
                inferred_type = inferred.get(key, artifact.artifact_type)
                if artifact.semantic_type == "BLINDED_INPUT_TYPE" and (
                    artifact.representation_class,
                    artifact.exactness_class,
                ) == (inferred_type.representation_class, inferred_type.exactness_class):
                    effective_root_types[key] = inferred_type
                elif artifact.artifact_type == inferred_type:
                    effective_root_types[key] = artifact.artifact_type
                else:
                    effective_root_types[key] = ArtifactType(
                        "HYBRID_TYPE_CONFLICT",
                        artifact.representation_class,
                        artifact.exactness_class,
                    )
                    events.append(
                        (
                            "HYBRID_ROOT_TYPE_CONFLICT",
                            {"input_key": key, "explicit": artifact.artifact_type, "inferred": inferred_type},
                        )
                    )

    terminal_goal = goal
    if routing_receipt is not None:
        terminal_goal, routing_error = _terminal_goal_view(
            goal,
            effective_root_types,
            routing_receipt,
        )
        if terminal_goal is None:
            return finish(
                initial,
                expanded=0,
                candidate=None,
                verdict="INVALID",
                code="INVALID_ROUTING_RECEIPT",
                reason=str(routing_error),
            )
        if (
            terminal_goal.family in {f"G{index}" for index in range(1, 13)}
            or terminal_goal.family in NEW_V0_20_FAMILIES
        ):
            contract_check = (
                validate_historical_goal_contract(terminal_goal)
                if terminal_goal.family.startswith("G")
                else validate_v0_20_goal_contract(terminal_goal)
            )
            if not contract_check.passed:
                return finish(
                    initial,
                    expanded=0,
                    candidate=None,
                    verdict="INVALID",
                    code="INVALID_GOAL_CONTRACT",
                    reason=contract_check.reason,
                )

    queue: list[tuple[tuple[Any, ...], int, _SearchNode]] = []
    serial = itertools.count()
    heapq.heappush(queue, (_node_priority(goal, initial), next(serial), initial))
    seen = {_state_signature(initial.tracked_mapping())}
    expanded = 0
    best_attempt = initial
    first_relevant_not_applicable: tuple[_SearchNode, str] | None = None
    bindings = tuple(goal.constraints)

    while queue and expanded < goal.search_budget:
        _, _, node = heapq.heappop(queue)
        expanded += 1
        tracked = node.tracked_mapping()

        root_failure = _root_integrity_failure(tracked)
        if root_failure is not None:
            input_key, observed_digest = root_failure
            return finish(
                node,
                expanded=expanded,
                candidate=None,
                verdict="INVALID",
                code="ROOT_INPUT_MUTATION",
                reason=f"{input_key}:{observed_digest}",
            )

        for choice in _candidates_from_state(
            goal,
            tracked,
            counters,
            effective_root_types,
        ):
            candidate = choice.tracked
            candidate_node = replace(
                node,
                path=node.path + tuple(
                    verifier.subject_id for verifier in choice.supplemental_verifiers
                ),
                verifiers=node.verifiers + choice.supplemental_verifiers,
                derivations=node.derivations + choice.supplemental_steps,
            )
            obligations = _candidate_obligations(
                goal,
                candidate,
                candidate_node.derivations,
            )
            if obligations is None:
                events.append(
                    (
                        "CANDIDATE_LINEAGE_REJECTED",
                        {"candidate_instance_id": candidate.instance_id},
                    )
                )
                continue
            counters.verified += 1
            try:
                independent = _verify_goal(
                    terminal_goal,
                    deepcopy(candidate.artifact),
                )
            except Exception as exc:
                events.append(
                    (
                        "TERMINAL_VERIFIER_ERROR",
                        {
                            "candidate_instance_id": candidate.instance_id,
                            "reason": _safe_exception_text(exc),
                        },
                    )
                )
                continue
            if not _has_valid_verification_fields(independent):
                events.append(
                    (
                        "TERMINAL_VERIFIER_ERROR",
                        {
                            "candidate_instance_id": candidate.instance_id,
                            "reason": "invalid terminal verifier result fields",
                        },
                    )
                )
                continue
            terminal = replace(
                independent,
                verifier_class=expected_verifier_class,
                stage="TERMINAL",
                subject_id=goal.goal_id,
                evidence=independent.evidence
                + (
                    ("independent_check_id", independent.verifier_class),
                    (
                        "registered_implementation_id",
                        _TERMINAL_VERIFIER_IMPLEMENTATION_BY_FAMILY[goal.family],
                    ),
                ),
            )
            if terminal.passed:
                return finish(
                    candidate_node,
                    expanded=expanded,
                    candidate=candidate,
                    verdict="PASS",
                    terminal=terminal,
                    suffix=("VERIFY_CANDIDATE",),
                    obligations=obligations,
                )
            events.append(
                (
                    "TERMINAL_VERIFIER_REJECTED",
                    {"candidate_instance_id": candidate.instance_id, "reason": terminal.reason},
                )
            )

        for operator_id in _ordered_operator_ids(typing_mode, registry, routing_order):
            spec = registry[operator_id]
            if spec.execution_kind != "PRIMITIVE":
                continue
            attempted_before = counters.attempted
            event_start = len(events)
            children = _transition_children(
                goal=goal,
                node=node,
                spec=spec,
                bindings=bindings,
                effective_root_types=effective_root_types,
                counters=counters,
                events=events,
            )
            if counters.attempted > attempted_before:
                attempted_node = replace(node, path=node.path + (operator_id,), cost=node.cost + spec.cost)
                if len(attempted_node.path) > len(best_attempt.path):
                    best_attempt = attempted_node
                relevant_events = events[event_start:]
                not_applicable = next(
                    (
                        payload.get("reason", "NOT_APPLICABLE")
                        for code, payload in relevant_events
                        if code in {"APPLICABILITY_NOT_APPLICABLE", "EXECUTION_NOT_APPLICABLE"}
                    ),
                    None,
                )
                if (
                    not_applicable is not None
                    and spec.output == goal.target.artifact_type
                    and first_relevant_not_applicable is None
                ):
                    if _is_bounded_text(not_applicable):
                        first_relevant_not_applicable = (
                            attempted_node,
                            not_applicable,
                        )
                    else:
                        events.append(
                            (
                                "APPLICABILITY_ERROR",
                                {
                                    "operator_id": spec.operator_id,
                                    "reason": "invalid not-applicable reason",
                                },
                            )
                        )
            for child in children:
                signature = _state_signature(child.tracked_mapping())
                if signature in seen:
                    continue
                seen.add(signature)
                if len(child.path) > len(best_attempt.path):
                    best_attempt = child
                heapq.heappush(queue, (_node_priority(goal, child), next(serial), child))

    structured_failures = {
        "APPLICABILITY_ERROR": ("INVALID", "APPLICABILITY_ERROR"),
        "APPLICABILITY_INVALID_INPUT": ("INVALID", "INVALID_INPUT"),
        "APPLICABILITY_INPUT_MUTATION": ("INVALID", "APPLICABILITY_INPUT_MUTATION"),
        "EXECUTION_INVALID": ("INVALID", "EXECUTION_INVALID"),
        "EXECUTION_ERROR": ("INVALID", "EXECUTION_ERROR"),
        "OPERATOR_INPUT_MUTATION": ("INVALID", "OPERATOR_INPUT_MUTATION"),
        "OUTPUT_CONTRACT_MISMATCH": ("INVALID", "OUTPUT_CONTRACT_MISMATCH"),
        "NONCANONICAL_OPERATOR_EVIDENCE": (
            "INVALID",
            "NONCANONICAL_OPERATOR_EVIDENCE",
        ),
        "VERIFIER_ERROR": ("INVALID", "VERIFIER_ERROR"),
        "VERIFIER_INPUT_MUTATION": ("INVALID", "VERIFIER_INPUT_MUTATION"),
        "TERMINAL_VERIFIER_ERROR": ("INVALID", "TERMINAL_VERIFIER_ERROR"),
        "APPLICABILITY_NUMERICALLY_UNSAFE": ("NOT_ESTABLISHED", "NUMERICALLY_UNSAFE"),
        "EXECUTION_NUMERICALLY_UNSAFE": ("NOT_ESTABLISHED", "NUMERICALLY_UNSAFE"),
    }
    for event_code, payload in events:
        if event_code not in structured_failures:
            continue
        verdict, refusal_code = structured_failures[event_code]
        payload_reason = payload.get("reason", event_code)
        reason = (
            payload_reason
            if _is_bounded_text(payload_reason)
            else "invalid structured failure reason"
        )
        payload_operator_id = payload.get("operator_id")
        operator_id = (
            payload_operator_id
            if _is_bounded_text(payload_operator_id, allow_empty=False)
            else None
        )
        return finish(
            best_attempt,
            expanded=expanded,
            candidate=None,
            verdict=verdict,
            code=refusal_code,
            reason=reason,
            operator_id=operator_id,
        )
    if first_relevant_not_applicable is not None:
        refused_node, reason = first_relevant_not_applicable
        operator_id = refused_node.path[-1] if refused_node.path else None
        return finish(
            refused_node,
            expanded=expanded,
            candidate=None,
            verdict="NOT_APPLICABLE",
            code="GOAL_NOT_APPLICABLE",
            reason=reason,
            operator_id=operator_id,
        )
    code = "SEARCH_BUDGET_EXHAUSTED" if expanded >= goal.search_budget else "NO_ADMISSIBLE_PATH"
    return finish(
        best_attempt,
        expanded=expanded,
        candidate=None,
        verdict="NOT_ESTABLISHED",
        code=code,
        reason=code,
    )
