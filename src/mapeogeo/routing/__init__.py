"""Routing and Goal-Solving Subsystem.

The router answers:
    Given certified state G_t and required work Q, what admissible work path should execute?

Boundary:
    D_t(Q) -> Router -> {R_1, ..., R_n} -> P/U -> R* -> C -> A
The kernel decides what work is valuable and admissible;
routing decides how that work can be performed.
"""

from __future__ import annotations

from mapeogeo.routing.contracts import (
    AuthorityRequirement,
    ResourceRequirement,
    RoutingBudget,
    WorkContract,
)
from mapeogeo.routing.goal import Goal, GoalConstraint
from mapeogeo.routing.registry import RouteRegistry
from mapeogeo.routing.route import (
    Route,
    RouteCandidate,
    RouteCertificate,
    create_route_certificate,
)
from mapeogeo.routing.router import Router
from mapeogeo.routing.serialization import (
    deserialize_work_contract,
    serialize_route_certificate,
    serialize_work_contract,
)
from mapeogeo.routing.solver import GoalSolution, GoalSolver

__all__ = [
    "AuthorityRequirement",
    "Goal",
    "GoalConstraint",
    "GoalSolution",
    "GoalSolver",
    "ResourceRequirement",
    "Route",
    "RouteCandidate",
    "RouteCertificate",
    "RouteRegistry",
    "Router",
    "RoutingBudget",
    "WorkContract",
    "create_route_certificate",
    "deserialize_work_contract",
    "serialize_route_certificate",
    "serialize_work_contract",
]
