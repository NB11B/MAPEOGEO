from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


FINAL_VERDICTS = frozenset({"PASS", "NOT_ESTABLISHED", "NOT_APPLICABLE", "INVALID", "ERROR"})
APPLICABILITY_VERDICTS = frozenset(
    {"APPLICABLE", "NOT_APPLICABLE", "MISSING_PRECONDITION", "INVALID_INPUT", "NUMERICALLY_UNSAFE"}
)
EXACTNESS_CLASSES = frozenset({"EXACT", "SYMBOLIC", "NUMERICAL"})


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

    def __post_init__(self) -> None:
        if self.final_verdict not in FINAL_VERDICTS:
            raise ValueError(f"unknown final verdict: {self.final_verdict}")
        if self.final_verdict == "PASS":
            if self.candidate_artifact is None:
                raise ValueError("PASS trace requires a candidate artifact")
            if not self.verifier_chain or not self.verifier_chain[-1].passed:
                raise ValueError("PASS trace requires a passing terminal verifier")
