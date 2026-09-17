from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ScopeComparisonOutcome(str, Enum):
    EQUAL = "EQUAL"
    CHECKED_RESTRICTION = "CHECKED_RESTRICTION"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class StructuredScopeRecord:
    space_type: str
    scalar_field: str
    topology_or_norm: str
    dimension_bound: str
    operator_domain: str
    regularity: str
    quantifier_structure: str
    parameter_box: str = "NONE"
    exceptions: str = "NONE"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StructuredScopeRecord:
        return cls(
            space_type=str(data.get("space_type", data.get("domain", "GENERAL"))),
            scalar_field=str(data.get("scalar_field", data.get("coefficient_ring", "GENERAL"))),
            topology_or_norm=str(data.get("topology_or_norm", data.get("norm", "GENERAL"))),
            dimension_bound=str(data.get("dimension_bound", data.get("dimension", "GENERAL"))),
            operator_domain=str(data.get("operator_domain", data.get("boundary_convention", "GENERAL"))),
            regularity=str(data.get("regularity", "GENERAL")),
            quantifier_structure=str(data.get("quantifier_structure", data.get("orientation_convention", "GENERAL"))),
            parameter_box=str(data.get("parameter_box", data.get("parameter_range", "NONE"))),
            exceptions=str(data.get("exceptions", data.get("exceptional_cases", "NONE"))),
        )


TypedScopeRecord = StructuredScopeRecord


@dataclass(frozen=True)
class StructuredScopeComparisonResult:
    outcome: ScopeComparisonOutcome
    mismatches: list[str]


def compare_structured_scopes(
    s1: StructuredScopeRecord,
    s2: StructuredScopeRecord,
) -> StructuredScopeComparisonResult:
    mismatches = []
    fields = [
        "space_type",
        "scalar_field",
        "topology_or_norm",
        "dimension_bound",
        "operator_domain",
        "regularity",
        "quantifier_structure",
        "parameter_box",
        "exceptions",
    ]

    for f in fields:
        v1 = getattr(s1, f)
        v2 = getattr(s2, f)
        if v1 != v2:
            mismatches.append(f)

    if not mismatches:
        return StructuredScopeComparisonResult(outcome=ScopeComparisonOutcome.EQUAL, mismatches=[])

    # Check valid restrictions
    is_restriction = False
    if set(mismatches) == {"dimension_bound"}:
        if s1.dimension_bound in ("INFINITE_OR_FINITE", "GENERAL", "infinite") and s2.dimension_bound in ("FINITE_DIMENSIONAL", "EXACT_N", "finite"):
            is_restriction = True
    elif set(mismatches) == {"operator_domain"}:
        if s1.operator_domain in ("ENTIRE_SPACE", "GENERAL") and s2.operator_domain in ("COMPACT_SUBSET", "CLOSED_SUBSET", "CONVEX_SUBSET"):
            is_restriction = True

    outcome = ScopeComparisonOutcome.CHECKED_RESTRICTION if is_restriction else ScopeComparisonOutcome.INCOMPATIBLE

    return StructuredScopeComparisonResult(
        outcome=outcome,
        mismatches=mismatches,
    )


def compare_scopes(s1: Any, s2: Any) -> StructuredScopeComparisonResult:
    r1 = s1 if isinstance(s1, StructuredScopeRecord) else StructuredScopeRecord.from_dict(s1)
    r2 = s2 if isinstance(s2, StructuredScopeRecord) else StructuredScopeRecord.from_dict(s2)
    return compare_structured_scopes(r1, r2)
