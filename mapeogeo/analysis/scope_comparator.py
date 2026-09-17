from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TypedScopeRecord:
    domain: str
    dimension: str
    coefficient_ring: str
    regularity: str
    orientation_convention: str
    boundary_convention: str
    parameter_range: str
    exceptional_cases: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TypedScopeRecord:
        return cls(
            domain=str(data["domain"]),
            dimension=str(data["dimension"]),
            coefficient_ring=str(data["coefficient_ring"]),
            regularity=str(data["regularity"]),
            orientation_convention=str(data["orientation_convention"]),
            boundary_convention=str(data["boundary_convention"]),
            parameter_range=str(data["parameter_range"]),
            exceptional_cases=str(data["exceptional_cases"]),
        )


@dataclass(frozen=True)
class ScopeComparisonResult:
    is_compatible: bool
    mismatches: list[str]


def compare_scopes(s1: TypedScopeRecord, s2: TypedScopeRecord) -> ScopeComparisonResult:
    mismatches = []
    fields = [
        "domain",
        "dimension",
        "coefficient_ring",
        "regularity",
        "orientation_convention",
        "boundary_convention",
        "parameter_range",
        "exceptional_cases",
    ]
    for field_name in fields:
        val1 = getattr(s1, field_name)
        val2 = getattr(s2, field_name)
        if val1 != val2:
            mismatches.append(field_name)

    return ScopeComparisonResult(
        is_compatible=(len(mismatches) == 0),
        mismatches=mismatches,
    )
