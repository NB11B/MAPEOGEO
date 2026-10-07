"""Knowledge and Machinery State Component (G).

Represents the certified available capabilities and machinery state:
    G_t = (Signatures_t, Witnesses_t, Machinery_t)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mapeogeo.kernel.machinery import MachineryNode
from mapeogeo.kernel.reach import compute_ability

if TYPE_CHECKING:
    from mapeogeo.kernel.deficiency import WorkRequirement


@dataclass(frozen=True)
class KnowledgeState:
    """Certified available knowledge and machinery state G_t."""

    t: int
    signatures: frozenset[str]
    certified_nodes: tuple[MachineryNode, ...]
    witness_ids: frozenset[str]
    cumulative_ability: float = 0.0
    state_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def initial(
        cls,
        initial_signatures: set[str] | frozenset[str] | None = None,
        initial_witnesses: set[str] | frozenset[str] | None = None,
    ) -> KnowledgeState:
        sigs = frozenset(initial_signatures or set())
        wits = frozenset(initial_witnesses or set())
        hasher = hashlib.sha256()
        for s in sorted(sigs):
            hasher.update(s.encode())
        return cls(
            t=0,
            signatures=sigs,
            certified_nodes=(),
            witness_ids=wits,
            cumulative_ability=0.0,
            state_hash=hasher.hexdigest(),
        )

    def reachable_certified_work(self, requirements: list[WorkRequirement]) -> float:
        """Evaluate certified reachable work under current state G_t."""
        return compute_ability(requirements, set(self.signatures))

    def transition(
        self,
        new_signatures: set[str] | frozenset[str] | tuple[str, ...] | list[str],
        new_nodes: list[MachineryNode] | tuple[MachineryNode, ...],
        new_witnesses: set[str] | frozenset[str] | tuple[str, ...] | list[str] | None = None,
        new_ability: float | None = None,
    ) -> KnowledgeState:
        """Execute an atomic certified state transition G_t -> G_{t+1}."""
        updated_sigs = self.signatures | frozenset(new_signatures)
        updated_nodes = self.certified_nodes + tuple(new_nodes)
        updated_wits = self.witness_ids | frozenset(new_witnesses or set())

        hasher = hashlib.sha256()
        for s in sorted(updated_sigs):
            hasher.update(s.encode())
        for w in sorted(updated_wits):
            hasher.update(w.encode())

        ability = (
            new_ability if new_ability is not None else self.cumulative_ability + len(new_nodes)
        )

        return KnowledgeState(
            t=self.t + 1,
            signatures=updated_sigs,
            certified_nodes=updated_nodes,
            witness_ids=updated_wits,
            cumulative_ability=round(ability, 4),
            state_hash=hasher.hexdigest(),
            metadata=dict(self.metadata),
        )

    def clone(self) -> KnowledgeState:
        """Return an exact clone of the current state."""
        return KnowledgeState(
            t=self.t,
            signatures=self.signatures,
            certified_nodes=self.certified_nodes,
            witness_ids=self.witness_ids,
            cumulative_ability=self.cumulative_ability,
            state_hash=self.state_hash,
            metadata=dict(self.metadata),
        )
