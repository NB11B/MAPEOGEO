"""Goal and Goal Constraint Specifications for Work Decomposition.

Goals specify target capability signatures, multi-resource budgets, authority credentials,
and invariant constraints to be solved by the GoalSolver.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mapeogeo.routing.contracts import RoutingBudget


@dataclass(frozen=True)
class GoalConstraint:
    """Constraint applied to goal solving and route exploration."""

    constraint_id: str
    kind: str  # "RESOURCE", "AUTHORITY", "INVARIANT", "EXCLUSION"
    prohibited_invariants: tuple[str, ...] = ()
    excluded_contracts: tuple[str, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        if not self.constraint_id:
            raise ValueError("constraint_id must be non-empty")


@dataclass(frozen=True)
class Goal:
    """A formal objective specification composed of target signatures and constraints."""

    goal_id: str
    target_signatures: tuple[str, ...]
    constraints: tuple[GoalConstraint, ...] = ()
    budget: RoutingBudget = field(default_factory=RoutingBudget)
    allowed_tolerance: float = 0.0
    authority_roles: frozenset[str] = frozenset()
    authority_scopes: frozenset[str] = frozenset()
    has_audit_receipt: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.goal_id:
            raise ValueError("goal_id must be non-empty")
        if not self.target_signatures:
            raise ValueError("target_signatures must be non-empty")
        if self.allowed_tolerance < 0:
            raise ValueError("allowed_tolerance must be non-negative")

    @property
    def prohibited_invariants(self) -> frozenset[str]:
        """Aggregate all prohibited invariants across constraints."""
        prohibited: set[str] = set()
        for c in self.constraints:
            prohibited.update(c.prohibited_invariants)
        return frozenset(prohibited)

    @property
    def excluded_contracts(self) -> frozenset[str]:
        """Aggregate all excluded contracts across constraints."""
        excluded: set[str] = set()
        for c in self.constraints:
            excluded.update(c.excluded_contracts)
        return frozenset(excluded)
