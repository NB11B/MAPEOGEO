"""Fail-closed certified mathematical work router.

Discovery edges may propose routes, but only certified edges are executable.
Runtime availability is separate from mathematical reachability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import heapq
from typing import Iterable, Mapping


class Outcome(str, Enum):
    ANSWER = "ANSWER"
    EXECUTE = "EXECUTE"
    OBSERVE = "OBSERVE"
    CERTIFY = "CERTIFY"
    MATERIALIZE = "MATERIALIZE"
    UNRESOLVABLE = "UNRESOLVABLE"


@dataclass(frozen=True)
class RouteEdge:
    edge_id: str
    source: str
    target: str
    cost: float
    certified: bool
    operation: str
    requires: tuple[str, ...] = ()
    materializes: bool = False

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("route edge cost must be nonnegative")
        if not self.edge_id or not self.source or not self.target:
            raise ValueError("route edge identity and endpoints are required")


@dataclass(frozen=True)
class Route:
    nodes: tuple[str, ...]
    edges: tuple[RouteEdge, ...]
    cost: float

    @property
    def certified(self) -> bool:
        return all(edge.certified for edge in self.edges)

    @property
    def materializes(self) -> bool:
        return any(edge.materializes for edge in self.edges)


@dataclass(frozen=True)
class WorkRequest:
    target: str
    tolerance: float = 0.0
    require_materialized: bool = False

    def __post_init__(self) -> None:
        if self.tolerance < 0:
            raise ValueError("work tolerance must be nonnegative")


@dataclass(frozen=True)
class WorkDecision:
    outcome: Outcome
    target: str
    route: Route | None
    missing: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class RouteCertificate:
    target: str
    route_edge_ids: tuple[str, ...]
    input_nodes: tuple[str, ...]
    output_node: str
    total_cost: float
    certified: bool
    materialized: bool


class WorkRouter:
    """Route work with validity > resolvability > cost ordering."""

    def __init__(self, edges: Iterable[RouteEdge]) -> None:
        self._edges = tuple(edges)
        self._by_source: dict[str, list[RouteEdge]] = {}
        for edge in self._edges:
            self._by_source.setdefault(edge.source, []).append(edge)

    def _shortest(
        self,
        starts: Iterable[str],
        target: str,
        *,
        certified_only: bool,
    ) -> Route | None:
        starts = tuple(sorted(set(starts)))
        if target in starts:
            return Route((target,), (), 0.0)

        heap: list[tuple[float, str, tuple[str, ...], tuple[RouteEdge, ...]]] = []
        best: dict[str, float] = {}
        for start in starts:
            heapq.heappush(heap, (0.0, start, (start,), ()))
            best[start] = 0.0

        while heap:
            cost, node, nodes, edges = heapq.heappop(heap)
            if cost > best.get(node, float("inf")):
                continue
            if node == target:
                return Route(nodes, edges, cost)
            for edge in sorted(self._by_source.get(node, ()), key=lambda e: e.edge_id):
                if certified_only and not edge.certified:
                    continue
                next_cost = cost + edge.cost
                if next_cost >= best.get(edge.target, float("inf")):
                    continue
                best[edge.target] = next_cost
                heapq.heappush(
                    heap,
                    (next_cost, edge.target, nodes + (edge.target,), edges + (edge,)),
                )
        return None

    @staticmethod
    def _missing_requirements(route: Route, available: set[str]) -> tuple[str, ...]:
        missing: set[str] = set()
        reachable = set(available)
        for edge in route.edges:
            for requirement in edge.requires:
                if requirement not in reachable:
                    missing.add(requirement)
            if edge.source in reachable and not missing:
                reachable.add(edge.target)
        return tuple(sorted(missing))

    def decide(
        self,
        request: WorkRequest,
        *,
        available: Iterable[str],
        known_answers: Iterable[str] = (),
    ) -> WorkDecision:
        available_set = set(available)
        known_set = set(known_answers)

        if request.target in known_set:
            if request.require_materialized and request.target not in available_set:
                return WorkDecision(
                    Outcome.MATERIALIZE,
                    request.target,
                    None,
                    reason="answer known but requested representation is not materialized",
                )
            return WorkDecision(
                Outcome.ANSWER,
                request.target,
                Route((request.target,), (), 0.0),
                reason="target answer already available",
            )

        certified = self._shortest(available_set, request.target, certified_only=True)
        if certified is not None:
            missing = self._missing_requirements(certified, available_set)
            if missing:
                return WorkDecision(
                    Outcome.OBSERVE,
                    request.target,
                    certified,
                    missing,
                    "certified route exists but required information is unavailable",
                )
            if request.require_materialized and not certified.materializes:
                return WorkDecision(
                    Outcome.MATERIALIZE,
                    request.target,
                    certified,
                    reason="certified mathematical answer is derivable but output materialization is required",
                )
            return WorkDecision(
                Outcome.EXECUTE,
                request.target,
                certified,
                reason="lowest-cost certified route is executable",
            )

        discovery = self._shortest(available_set, request.target, certified_only=False)
        if discovery is not None:
            return WorkDecision(
                Outcome.CERTIFY,
                request.target,
                discovery,
                self._missing_requirements(discovery, available_set),
                "candidate route exists but at least one edge is not certified",
            )

        return WorkDecision(
            Outcome.UNRESOLVABLE,
            request.target,
            None,
            reason="no route exists from available state",
        )

    @staticmethod
    def certificate(
        decision: WorkDecision,
        *,
        input_nodes: Iterable[str],
    ) -> RouteCertificate:
        if decision.outcome not in {Outcome.ANSWER, Outcome.EXECUTE, Outcome.MATERIALIZE}:
            raise ValueError("non-executable decision cannot produce a route certificate")
        route = decision.route or Route((decision.target,), (), 0.0)
        return RouteCertificate(
            target=decision.target,
            route_edge_ids=tuple(edge.edge_id for edge in route.edges),
            input_nodes=tuple(sorted(set(input_nodes))),
            output_node=decision.target,
            total_cost=route.cost,
            certified=route.certified,
            materialized=route.materializes,
        )


def qualified_v01_edges() -> tuple[RouteEdge, ...]:
    """Bounded v0.1 overlay for the six qualified PSMSL/MAPEOGEO work queries.

    These edges are local executable contracts. They do not promote or rewrite
    the underlying MAPEOGEO graph and do not claim whole-corpus equivalence.
    """
    return (
        RouteEdge("wr.area.sum", "psmsl.directional_scales", "work.area_exponent", 1.0, True, "n1+n2"),
        RouteEdge("wr.area.sign", "work.area_exponent", "work.area_expanding", 1.0, True, "compare > 0"),
        RouteEdge("wr.area.materialize", "work.area_exponent", "eo.determinant", 8.0, True, "phi**exponent", materializes=True),
        RouteEdge("wr.orientation.class", "psmsl.positive_scale_proper_rotation", "work.orientation_preserving", 0.1, True, "class invariant"),
        RouteEdge("wr.stability.realpart", "psmsl.generator_g", "work.stable", 0.5, True, "compare g < 0"),
        RouteEdge("wr.phase.accumulate", "psmsl.phase_steps", "work.phase", 1.0, True, "sum phase modulo 2pi"),
        RouteEdge("wr.amplitude.threshold", "psmsl.scale_n", "work.amplitude_above_threshold", 0.5, True, "compare n > n_threshold", requires=("work.amplitude_threshold_n",)),
        RouteEdge("wr.projection.residual", "psmsl.vector_subspace_pair", "work.projection_membership", 3.0, True, "orthogonal residual norm"),
        # Deliberately cheaper but uncertified shortcut used to enforce fail-closed routing.
        RouteEdge("wr.unsafe.det-shortcut", "psmsl.directional_scales", "work.area_expanding", 0.01, False, "semantic shortcut"),
    )
