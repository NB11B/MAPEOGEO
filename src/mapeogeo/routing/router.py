"""Deterministic Work Router with Typed Composition and Multi-Constraint Enforcement.

The Router answers:
    Given certified state G_t and required work Q, what admissible work path should execute?

Boundary:
    D_t(Q) -> Router -> {R_1, ..., R_n} -> P/U -> R* -> C -> A
The Router proposes legal ways to perform work; Wave 4 kernel decides utility,
certification, and admission.
"""

from __future__ import annotations

from mapeogeo.routing.contracts import (
    RoutingBudget,
    WorkContract,
)
from mapeogeo.routing.registry import RouteRegistry
from mapeogeo.routing.route import Route, RouteCandidate


class Router:
    """Deterministic work router enforcing composition, resources, authority, and invariants."""

    def __init__(self, registry: RouteRegistry) -> None:
        self.registry = registry

    def find_routes(
        self,
        target: str,
        available_capabilities: set[str] | frozenset[str],
        budget: RoutingBudget | None = None,
        granted_roles: set[str] | frozenset[str] | None = None,
        granted_scopes: set[str] | frozenset[str] | None = None,
        has_audit_receipt: bool = False,
        prohibited_invariants: set[str] | frozenset[str] | None = None,
        tolerance: float = float("inf"),
        max_depth: int = 10,
    ) -> list[RouteCandidate]:
        """Discover and qualify candidate routes leading to target."""
        eff_budget = budget or RoutingBudget()
        roles = frozenset(granted_roles or set())
        scopes = frozenset(granted_scopes or set())
        bad_invs = frozenset(prohibited_invariants or set())
        available = frozenset(available_capabilities)

        # 1. Trivial check: target is already in available capabilities
        if target in available:
            trivial_route = Route.trivial(target)
            return [
                RouteCandidate(
                    candidate_id=f"cand-trivial-{target}",
                    route=trivial_route,
                    status="ADMISSIBLE",
                    rejection_reasons=(),
                )
            ]

        # 2. Search for route paths from available capabilities to target using Dijkstra / BFS
        raw_routes = self._search_paths(available, target, max_depth=max_depth)
        candidates: list[RouteCandidate] = []

        for idx, route in enumerate(raw_routes):
            cand_id = f"cand-{target}-{idx}-{'-'.join(c.contract_id for c in route.contracts)}"
            status, reasons = self._qualify_route(
                route=route,
                budget=eff_budget,
                roles=roles,
                scopes=scopes,
                has_audit_receipt=has_audit_receipt,
                bad_invs=bad_invs,
                tolerance=tolerance,
            )
            candidates.append(
                RouteCandidate(
                    candidate_id=cand_id,
                    route=route,
                    status=status,
                    rejection_reasons=tuple(reasons),
                )
            )

        # 3. Deterministic sort order:
        # (is_admissible descending, cost ascending, error ascending, candidate_id ascending)
        candidates.sort(
            key=lambda c: (
                0 if c.is_admissible else 1,
                c.route.total_cost,
                c.route.total_error,
                c.candidate_id,
            )
        )
        return candidates

    def _search_paths(
        self,
        starts: frozenset[str],
        target: str,
        max_depth: int,
    ) -> list[Route]:
        """Search for paths from starts to target with deterministic ordering."""
        # Queue item: (cost, current_node, contracts_tuple)
        queue: list[tuple[float, str, tuple[WorkContract, ...]]] = []
        for s in sorted(starts):
            queue.append((0.0, s, ()))

        discovered_routes: list[Route] = []
        visited_paths: set[tuple[str, ...]] = set()

        while queue:
            cost, current_node, contracts = queue.pop(0)

            if current_node == target and contracts:
                route = Route.from_contracts(contracts)
                discovered_routes.append(route)
                continue

            if len(contracts) >= max_depth:
                continue

            # Deterministic iteration over outgoing contracts
            outgoing = self.registry.find_by_source(current_node)
            for c in outgoing:
                path_key = tuple(x.contract_id for x in contracts) + (c.contract_id,)
                # Prevent simple cycles
                if any(x.target == c.target for x in contracts):
                    continue
                if path_key in visited_paths:
                    continue
                visited_paths.add(path_key)

                queue.append((cost + c.cost, c.target, contracts + (c,)))

        return discovered_routes

    def _qualify_route(
        self,
        route: Route,
        budget: RoutingBudget,
        roles: frozenset[str],
        scopes: frozenset[str],
        has_audit_receipt: bool,
        bad_invs: frozenset[str],
        tolerance: float,
    ) -> tuple[str, list[str]]:
        """Evaluate route against typed composition, authority, resources, and invariants."""
        reasons: list[str] = []

        # Gate A: Typed composition pre/post-conditions
        valid_comp, comp_err = route.is_valid_composition()
        if not valid_comp:
            return "INCOMPATIBLE_CONTRACTS", [comp_err or "Invalid contract composition"]

        # Gate B: Authority Boundary (Independent of capability!)
        for c in route.contracts:
            if not c.authority.is_authorized(roles, scopes, has_audit_receipt):
                reasons.append(
                    f"Insufficient authority for contract '{c.contract_id}': "
                    f"requires role='{c.authority.required_role}' "
                    f"scopes={sorted(c.authority.allowed_scopes)}"
                )
        if reasons:
            return "BLOCKED_AUTHORITY", reasons

        # Gate C: Resource and Cost Budget
        if route.total_cost > budget.max_cost:
            reasons.append(f"Route cost {route.total_cost} exceeds max budget {budget.max_cost}")
        if not route.total_resources.fits_in(budget):
            reasons.append("Route resources exceed allowed routing budget envelope")
        if reasons:
            return "BLOCKED_RESOURCE", reasons

        # Gate D: Invariant Enforcement
        for c in route.contracts:
            violated = set(c.invariants) & bad_invs
            if violated:
                reasons.append(
                    f"Contract '{c.contract_id}' violates invariants: {sorted(violated)}"
                )
        if reasons:
            return "BLOCKED_INVARIANT", reasons

        # Gate E: Tolerance
        if route.total_error > tolerance or route.total_error > budget.max_tolerance:
            reasons.append(
                f"Route error {route.total_error} exceeds tolerance limit "
                f"(requested {tolerance}, budget {budget.max_tolerance})"
            )
            return "BLOCKED_RESOURCE", reasons

        # Gate F: Certification
        if not route.certified:
            return "UNCERTIFIED", ["Route contains uncertified contracts"]

        return "ADMISSIBLE", []
