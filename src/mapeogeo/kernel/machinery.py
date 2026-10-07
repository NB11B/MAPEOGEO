"""Machinery candidate and node representations (M).

Domain-neutral units of capability that can be evaluated, certified, and acquired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MachineryNode:
    """An atomic structural unit within a proposed machinery package."""

    node_id: str
    provided_signatures: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    witness_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id must be non-empty")


@dataclass(frozen=True)
class MachineryCandidate:
    """A proposed capability acquisition package M."""

    candidate_id: str
    provided_signatures: tuple[str, ...]
    cost: float
    nodes: tuple[MachineryNode, ...]
    witness_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be non-empty")
        if not self.provided_signatures:
            raise ValueError("provided_signatures must be non-empty")
        if self.cost <= 0:
            raise ValueError("cost must be strictly positive")
