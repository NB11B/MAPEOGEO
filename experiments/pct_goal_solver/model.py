from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


FINAL_VERDICTS = frozenset({"PASS", "NOT_ESTABLISHED", "NOT_APPLICABLE", "INVALID", "ERROR"})
APPLICABILITY_VERDICTS = frozenset(
    {"APPLICABLE", "NOT_APPLICABLE", "MISSING_PRECONDITION", "INVALID_INPUT", "NUMERICALLY_UNSAFE"}
)
EXACTNESS_CLASSES = frozenset({"EXACT", "SYMBOLIC", "NUMERICAL"})


@dataclass(frozen=True, order=True)
class ArtifactType:
    semantic_type: str
    representation_class: str
    exactness_class: str

    def __post_init__(self) -> None:
        if not self.semantic_type or not self.representation_class:
            raise ValueError("artifact type fields must be nonempty")
        if self.exactness_class not in EXACTNESS_CLASSES:
            raise ValueError(f"unknown exactness class: {self.exactness_class}")


@dataclass(frozen=True, order=True)
class InputPort:
    port_id: str
    artifact_type: ArtifactType

    def __post_init__(self) -> None:
        if not self.port_id:
            raise ValueError("input port id must be nonempty")


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    semantic_type: str
    representation_class: str
    value: Any
    exactness_class: str
    metadata: tuple[tuple[str, Any], ...] = ()
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.exactness_class not in EXACTNESS_CLASSES:
            raise ValueError(f"unknown exactness class: {self.exactness_class}")

    def metadata_dict(self) -> dict[str, Any]:
        return dict(self.metadata)

    @property
    def artifact_type(self) -> ArtifactType:
        return ArtifactType(self.semantic_type, self.representation_class, self.exactness_class)


@dataclass(frozen=True)
class TargetSpec:
    target_id: str
    semantic_type: str
    representation_class: str
    objective: str
    exactness_class: str | None = None
    metadata: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.exactness_class is not None and self.exactness_class not in EXACTNESS_CLASSES:
            raise ValueError(f"unknown target exactness class: {self.exactness_class}")

    @property
    def artifact_type(self) -> ArtifactType | None:
        if self.exactness_class is None:
            return None
        return ArtifactType(self.semantic_type, self.representation_class, self.exactness_class)


@dataclass(frozen=True)
class CandidateLineageObligation:
    required_input_keys: frozenset[str]
    ordered_stage_types: tuple[ArtifactType, ...]
    stage_required_input_keys: tuple[frozenset[str], ...] = ()

    def __post_init__(self) -> None:
        if self.stage_required_input_keys and (
            len(self.stage_required_input_keys) != len(self.ordered_stage_types)
        ):
            raise ValueError("stage root anchors must be parallel to ordered stage types")


@dataclass(frozen=True)
class SolverVisibleGoal:
    goal_id: str
    family: str
    inputs: Mapping[str, Artifact]
    target: TargetSpec
    constraints: tuple[tuple[str, Any], ...]
    allowed_numeric_tolerance: float
    required_verifier_class: str
    search_budget: int
    lineage_obligation: CandidateLineageObligation | None = None


@dataclass(frozen=True)
class GoalSpec:
    goal_id: str
    family: str
    inputs: Mapping[str, Artifact]
    target: TargetSpec
    constraints: tuple[tuple[str, Any], ...]
    allowed_numeric_tolerance: float
    required_verifier_class: str
    search_budget: int
    sealed_expected_result: Any
    sealed_reference_path: tuple[str, ...]
    lineage_obligation: CandidateLineageObligation | None = None

    def solver_visible(self) -> SolverVisibleGoal:
        return SolverVisibleGoal(
            goal_id=self.goal_id,
            family=self.family,
            inputs=dict(self.inputs),
            target=self.target,
            constraints=tuple(self.constraints),
            allowed_numeric_tolerance=self.allowed_numeric_tolerance,
            required_verifier_class=self.required_verifier_class,
            search_budget=self.search_budget,
            lineage_obligation=self.lineage_obligation,
        )


@dataclass(frozen=True)
class Applicability:
    verdict: str
    reason: str = ""

    def __post_init__(self) -> None:
        if self.verdict not in APPLICABILITY_VERDICTS:
            raise ValueError(f"unknown applicability verdict: {self.verdict}")

    @property
    def applicable(self) -> bool:
        return self.verdict == "APPLICABLE"


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    verifier_class: str
    reason: str = ""
    residual: float | None = None
    evidence: tuple[tuple[str, Any], ...] = ()
    stage: str = "UNSPECIFIED"
    subject_id: str = ""


@dataclass(frozen=True)
class Refusal:
    code: str
    reason: str
    operator_id: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("refusal code must be nonempty")


@dataclass(frozen=True)
class RootOrigin:
    input_key: str
    instance_id: str
    artifact_id: str
    content_digest: str = ""


@dataclass(frozen=True)
class DerivationStep:
    step_id: str
    operator_id: str
    input_bindings: tuple[tuple[str, str], ...]
    output_instance_id: str
    output_artifact_id: str
    output_type: ArtifactType
    verifier: VerificationResult
    root_input_keys: frozenset[str] = frozenset()


@dataclass(frozen=True)
class DerivedArtifactRecord:
    """Materialized output bound to one planner derivation step."""

    instance_id: str
    derivation_step_id: str
    artifact: Artifact


@dataclass(frozen=True)
class DerivedObligation:
    semantic_type: str
    artifact_instance_id: str
    derivation_step_id: str
    order_index: int = 0


@dataclass(frozen=True)
class RoutingReceipt:
    typing_mode: str
    inferred_root_types: tuple[tuple[str, ArtifactType], ...]
    ordered_operator_ids: tuple[str, ...]
    ambiguous_input_keys: tuple[str, ...]
    compatibility_model_digest: str
    decision_digest: str


@dataclass(frozen=True)
class LineageReceipt:
    candidate_instance_id: str
    root_input_keys: frozenset[str]
    stage_instance_ids: tuple[str, ...]
    registry_digest: str = ""
    obligation_digest: str = ""


@dataclass(frozen=True)
class RuntimeMacroBinding:
    macro_id: str
    primitive_ids: tuple[str, ...]
    derivation_step_ids: tuple[str, ...]
    certificate_digest: str = ""


@dataclass(frozen=True)
class OperatorFailure:
    verdict: str
    reason: str
    operator_id: str

    def __post_init__(self) -> None:
        if self.verdict not in {"NOT_APPLICABLE", "INVALID", "ERROR", "NUMERICALLY_UNSAFE"}:
            raise ValueError(f"invalid operator failure verdict: {self.verdict}")


@dataclass(frozen=True)
class SolveTrace:
    goal_id: str
    mode: str
    operator_path: tuple[str, ...]
    expanded_state_count: int
    primitive_execution_count: int
    macro_ids: tuple[str, ...]
    candidate_artifact: Artifact | None
    verifier_chain: tuple[VerificationResult, ...]
    falsification_events: tuple[tuple[str, Any], ...]
    final_verdict: str
    failure_reason: str = ""
    refusal: Refusal | None = None
    root_origins: tuple[RootOrigin, ...] = ()
    derivations: tuple[DerivationStep, ...] = ()
    derived_artifacts: tuple[DerivedArtifactRecord, ...] = ()
    derived_obligations: tuple[DerivedObligation, ...] = ()
    candidate_lineage: LineageReceipt | None = None
    macro_bindings: tuple[RuntimeMacroBinding, ...] = ()
    attempted_operator_count: int = 0
    verifier_execution_count: int = 0
    routing_receipt: RoutingReceipt | None = None

    def __post_init__(self) -> None:
        if self.final_verdict not in FINAL_VERDICTS:
            raise ValueError(f"unknown final verdict: {self.final_verdict}")
        if self.final_verdict == "PASS":
            if self.candidate_artifact is None:
                raise ValueError("PASS trace requires a candidate artifact")
            if not self.verifier_chain or not self.verifier_chain[-1].passed:
                raise ValueError("PASS trace requires a passing terminal verifier")
