"""Typed Route Representation, Composition Invariants, and Route Certificates.

Route Composition:
    R = T_n circ ... circ T_2 circ T_1
Composition Validity:
    Post(T_i) |= Pre(T_{i+1})
No implicit coercion is permitted.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from mapeogeo.routing.contracts import ResourceRequirement, WorkContract


@dataclass(frozen=True)
class Route:
    """An executable typed sequence of composed work contracts."""

    nodes: tuple[str, ...]
    contracts: tuple[WorkContract, ...]
    total_cost: float
    total_error: float = 0.0
    total_resources: ResourceRequirement = field(default_factory=ResourceRequirement)

    @classmethod
    def trivial(cls, target: str) -> Route:
        """Trivial zero-cost route for an already-achieved target."""
        return cls(
            nodes=(target,),
            contracts=(),
            total_cost=0.0,
            total_error=0.0,
            total_resources=ResourceRequirement(),
        )

    @classmethod
    def from_contracts(cls, contracts: tuple[WorkContract, ...]) -> Route:
        """Construct a route from an ordered tuple of work contracts."""
        if not contracts:
            raise ValueError("Route must contain at least one contract")

        nodes: list[str] = [contracts[0].source]
        total_cost = 0.0
        total_error = 0.0
        res = ResourceRequirement()

        for c in contracts:
            nodes.append(c.target)
            total_cost += c.cost
            total_error += c.error_tolerance
            res = res.combine(c.resources)

        return cls(
            nodes=tuple(nodes),
            contracts=contracts,
            total_cost=round(total_cost, 4),
            total_error=round(total_error, 6),
            total_resources=res,
        )

    @property
    def certified(self) -> bool:
        """True iff every contract in the route is formally certified."""
        return all(c.is_certified for c in self.contracts)

    @property
    def materializes(self) -> bool:
        """True iff at least one contract in the route requires materialization."""
        return any(c.requires_materialization for c in self.contracts)

    def is_valid_composition(self) -> tuple[bool, str | None]:
        """Verify strict typed route composition invariant.

        Composition is valid only when:
            Post(T_i) |= Pre(T_{i+1})
        and endpoints align: Target(T_i) == Source(T_{i+1}).
        No implicit coercion is allowed.
        """
        if not self.contracts:
            return True, None

        accumulated_postconditions: set[str] = set()

        for i, contract in enumerate(self.contracts):
            # Endpoint alignment check
            if i > 0:
                prev_contract = self.contracts[i - 1]
                if prev_contract.target != contract.source:
                    return (
                        False,
                        (
                            f"Endpoint mismatch at step {i}: "
                            f"{prev_contract.target} != {contract.source}"
                        ),
                    )

            # Precondition satisfaction check: Pre(T_i) subset of accumulated postconditions
            required_pre = set(contract.preconditions)
            unmet_pre = required_pre - accumulated_postconditions
            if unmet_pre and i > 0:  # Step 0 initial preconditions checked externally
                return (
                    False,
                    f"Composition contract violation at step {i} ('{contract.contract_id}'): "
                    f"unmet preconditions {sorted(unmet_pre)}",
                )

            # Accumulate newly declared postconditions
            accumulated_postconditions.update(contract.postconditions)

        return True, None


@dataclass(frozen=True)
class RouteCertificate:
    """Cryptographic certificate for an admissible, certified route."""

    target: str
    route_contract_ids: tuple[str, ...]
    input_nodes: tuple[str, ...]
    output_node: str
    total_cost: float
    total_error: float
    certified: bool
    materialized: bool
    sha256_seal: str


@dataclass(frozen=True)
class RouteCandidate:
    """Evaluated route candidate presented to kernel planning/utility."""

    candidate_id: str
    route: Route
    status: str
    # Valid: ADMISSIBLE, BLOCKED_RESOURCE, BLOCKED_AUTHORITY,
    # BLOCKED_INVARIANT, UNCERTIFIED, INCOMPATIBLE_CONTRACTS
    rejection_reasons: tuple[str, ...] = ()

    @property
    def is_admissible(self) -> bool:
        return self.status == "ADMISSIBLE"


def create_route_certificate(
    route: Route,
    target: str,
    input_nodes: tuple[str, ...],
) -> RouteCertificate:
    """Issue a deterministic cryptographic certificate for a certified route."""
    if not route.certified:
        raise ValueError("Cannot issue RouteCertificate for an uncertified route")

    valid, err = route.is_valid_composition()
    if not valid:
        raise ValueError(f"Cannot issue RouteCertificate for invalid composition: {err}")

    hasher = hashlib.sha256()
    hasher.update(target.encode())
    for cid in [c.contract_id for c in route.contracts]:
        hasher.update(cid.encode())
    for n in sorted(input_nodes):
        hasher.update(n.encode())
    hasher.update(str(route.total_cost).encode())
    hasher.update(str(route.total_error).encode())

    return RouteCertificate(
        target=target,
        route_contract_ids=tuple(c.contract_id for c in route.contracts),
        input_nodes=tuple(sorted(set(input_nodes))),
        output_node=target,
        total_cost=route.total_cost,
        total_error=route.total_error,
        certified=True,
        materialized=route.materializes,
        sha256_seal=hasher.hexdigest(),
    )
