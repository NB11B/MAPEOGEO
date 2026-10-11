from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class BehaviorClass(str, Enum):
    B0_ACQUIRE = "B0_ACQUIRE"
    B1_RESOLVE = "B1_RESOLVE"
    B2_NOMINATE = "B2_NOMINATE"
    B3_LINK_CANDIDATE = "B3_LINK_CANDIDATE"
    B4_QUARANTINE = "B4_QUARANTINE"
    B5_DEFER_UNRESOLVED = "B5_DEFER_UNRESOLVED"
    B6_REFUSE_PROMOTION = "B6_REFUSE_PROMOTION"
    B7_DEDUPLICATE = "B7_DEDUPLICATE"
    B8_ROUTE_ENTITY = "B8_ROUTE_ENTITY"
    B9_NO_ACTION = "B9_NO_ACTION"


ALL_BEHAVIOR_CLASSES: list[str] = [b.value for b in BehaviorClass]


@dataclass
class BehaviorTestCase:
    case_id: str
    family: str  # CITATION, TERMINOLOGY, IDENTITY, GENEALOGY, EPISTEMIC_BOUNDARY, FRONTIER_LOOP
    description: str
    input_payload: dict[str, Any]
    expected_behavior: str
    expected_state: Optional[str] = None
    is_counterfactual: bool = False
    counterfactual_pair_id: Optional[str] = None
    forbidden_behaviors: list[str] = field(default_factory=list)
    forbidden_states: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BehaviorEvaluationResult:
    case_id: str
    family: str
    expected_behavior: str
    actual_behavior: str
    expected_state: Optional[str]
    actual_state: Optional[str]
    is_correct: bool
    state_correct: bool
    forbidden_violations: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConfusionMatrix:
    def __init__(self) -> None:
        self.classes: list[str] = list(ALL_BEHAVIOR_CLASSES)
        self.matrix: dict[str, dict[str, int]] = {
            exp: {act: 0 for act in self.classes} for exp in self.classes
        }
        self.total_cases: int = 0
        self.correct_cases: int = 0
        self.critical_violations: list[dict[str, Any]] = []

    def record(self, result: BehaviorEvaluationResult) -> None:
        exp = result.expected_behavior
        act = result.actual_behavior
        self.total_cases += 1

        if exp in self.matrix and act in self.matrix[exp]:
            self.matrix[exp][act] += 1

        if result.is_correct and result.state_correct:
            self.correct_cases += 1

        if result.forbidden_violations:
            for viol in result.forbidden_violations:
                self.critical_violations.append({
                    "case_id": result.case_id,
                    "family": result.family,
                    "violation": viol,
                    "details": result.details,
                })

    def precision(self, b_class: str) -> Optional[float]:
        tp = self.matrix[b_class][b_class]
        fp = sum(self.matrix[other][b_class] for other in self.classes if other != b_class)
        return round(tp / (tp + fp), 4) if (tp + fp) > 0 else None

    def recall(self, b_class: str) -> Optional[float]:
        tp = self.matrix[b_class][b_class]
        fn = sum(self.matrix[b_class][other] for other in self.classes if other != b_class)
        return round(tp / (tp + fn), 4) if (tp + fn) > 0 else None

    def accuracy(self) -> float:
        return round(self.correct_cases / self.total_cases, 4) if self.total_cases > 0 else 0.0

    def summary(self) -> dict[str, Any]:
        per_class: dict[str, dict[str, float]] = {}
        for b in self.classes:
            tp = self.matrix[b][b]
            total_exp = sum(self.matrix[b].values())
            per_class[b] = {
                "support": total_exp,
                "tp": tp,
                "precision": self.precision(b),
                "recall": self.recall(b),
            }

        return {
            "total_cases": self.total_cases,
            "correct_cases": self.correct_cases,
            "overall_accuracy": self.accuracy(),
            "critical_violations_count": len(self.critical_violations),
            "critical_violations": self.critical_violations,
            "per_class_metrics": per_class,
        }
