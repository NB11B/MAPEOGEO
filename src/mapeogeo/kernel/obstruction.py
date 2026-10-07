"""Obstruction Operator (Omega) and Repair Operator (rho).

Omega:
    Evaluates obstructions on proposed machinery nodes.
rho:
    Repairs obstructed nodes by rewiring dependencies or attaching valid certificates.
"""

from __future__ import annotations

from dataclasses import dataclass

from mapeogeo.kernel.machinery import MachineryNode


@dataclass(frozen=True)
class ObstructionReport:
    """Diagnostic report on obstructions detected for a machinery node."""

    node_id: str
    is_obstructed: bool
    obstruction_index: int
    obstructions: tuple[str, ...]


class ObstructionOperator:
    """Evaluates obstructions on proposed machinery nodes."""

    def evaluate(
        self,
        node: MachineryNode,
        available_capabilities: set[str],
    ) -> ObstructionReport:
        """Check dependencies and constructive witness completeness."""
        obstructions: list[str] = []

        # Check unresolved dependencies
        dep_set = set(node.dependencies)
        missing_deps = dep_set - available_capabilities
        if missing_deps:
            obstructions.append(f"UNRESOLVED_DEPENDENCIES: {sorted(missing_deps)}")

        # Check constructive witness
        if not node.witness_id:
            obstructions.append("MISSING_CONSTRUCTIVE_WITNESS")

        is_obstructed = len(obstructions) > 0
        return ObstructionReport(
            node_id=node.node_id,
            is_obstructed=is_obstructed,
            obstruction_index=len(obstructions),
            obstructions=tuple(obstructions),
        )


class RepairOperator:
    """Repairs obstructed nodes by dependency rewiring or surrogate witness assignment."""

    def repair(
        self,
        node: MachineryNode,
        substitute_deps: dict[str, str] | None = None,
        surrogate_witness_id: str | None = None,
    ) -> MachineryNode:
        """Construct a repaired MachineryNode satisfying dependency invariants."""
        substitutes = substitute_deps or {}
        repaired_deps = [substitutes.get(d, d) for d in node.dependencies]
        witness_id = surrogate_witness_id or node.witness_id

        return MachineryNode(
            node_id=node.node_id,
            provided_signatures=node.provided_signatures,
            dependencies=tuple(repaired_deps),
            witness_id=witness_id,
            metadata=dict(node.metadata),
        )
