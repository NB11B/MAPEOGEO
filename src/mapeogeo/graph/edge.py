"""Graph edge primitives and evidentiary contracts.

Domain-neutral representation of directional connections between nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mapeogeo.graph.relation import RelationType, check_relation_strength_invariance


@dataclass(frozen=True)
class EdgeContract:
    """Contract binding the minimum required relation strength and certification."""

    contract_id: str
    required_relation: RelationType
    is_certified: bool = False
    certificate_id: str | None = None

    def validate_assertion(self, asserted_relation: RelationType) -> bool:
        """Validate whether an asserted relation satisfies this contract."""
        return check_relation_strength_invariance(
            asserted=asserted_relation,
            demanded=self.required_relation,
            is_certified=self.is_certified,
        )


@dataclass(frozen=True)
class Edge:
    """Directed edge connecting source and target nodes with a declared relation."""

    source_id: str
    target_id: str
    relation: RelationType = RelationType.CANDIDATE_REPRESENTS
    contract: EdgeContract | None = None
    port_binding: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("source_id and target_id must be non-empty strings")
        if self.source_id == self.target_id:
            raise ValueError(f"Self-loops are forbidden: {self.source_id} -> {self.target_id}")

        if self.contract is not None:
            if not self.contract.validate_assertion(self.relation):
                raise ValueError(
                    f"Edge {self.source_id}->{self.target_id} "
                    f"with relation '{self.relation.value}' "
                    f"violates contract requiring '{self.contract.required_relation.value}' "
                    f"(certified={self.contract.is_certified})"
                )

    @property
    def edge_key(self) -> tuple[str, str, str]:
        """Unique key identifying this directed connection."""
        return (self.source_id, self.target_id, self.relation.value)
