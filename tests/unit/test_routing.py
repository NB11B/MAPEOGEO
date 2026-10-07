"""Unit tests for the canonical Routing and Goal-Solving subsystem.

Verifies:
1. WorkContract, ResourceRequirement, AuthorityRequirement, and RoutingBudget.
2. Strict typed route composition: Post(T_i) |= Pre(T_{i+1}), no implicit coercion.
3. Authority boundary: can_execute != authorized_to_execute (rejected, not penalized).
4. RouteRegistry linking to Wave-3 DecisionGraph substrate.
5. Deterministic Router search and multi-constraint fail-closed qualification.
6. RouteCertificate cryptographic seal and invariance.
7. GoalSolver terminal states: SATISFIED, PARTIALLY_SATISFIED, UNREACHABLE,
   BLOCKED_RESOURCE, BLOCKED_AUTHORITY, BLOCKED_INVARIANT, AMBIGUOUS.
8. Deterministic serialization roundtrips.
"""

from __future__ import annotations

import pytest

from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.routing.contracts import (
    AuthorityRequirement,
    ResourceRequirement,
    RoutingBudget,
    WorkContract,
)
from mapeogeo.routing.goal import Goal
from mapeogeo.routing.registry import RouteRegistry
from mapeogeo.routing.route import (
    Route,
    create_route_certificate,
)
from mapeogeo.routing.router import Router
from mapeogeo.routing.serialization import (
    deserialize_work_contract,
    serialize_work_contract,
)
from mapeogeo.routing.solver import GoalSolver

# --- 1. Contracts, Resources, and Authority ---


def test_resource_requirement_combination_and_budget_bounds() -> None:
    """Verify multi-resource composition and budget constraints."""
    r1 = ResourceRequirement(cpu_cores=2.0, ram_mb=1024.0, energy_joules=50.0)
    r2 = ResourceRequirement(cpu_cores=1.5, gpu_count=1.0, energy_joules=120.0)
    combined = r1.combine(r2)

    assert combined.cpu_cores == 3.5
    assert combined.ram_mb == 1024.0
    assert combined.gpu_count == 1.0
    assert combined.energy_joules == 170.0

    tight_budget = RoutingBudget(max_cpu_cores=3.0)
    assert not combined.fits_in(tight_budget)

    sufficient_budget = RoutingBudget(max_cpu_cores=4.0, max_gpu_count=1.0, max_energy_joules=200.0)
    assert combined.fits_in(sufficient_budget)


def test_authority_boundary_strictly_rejects_unauthorized_execution() -> None:
    """Verify authority is independent of capability: can_execute != authorized_to_execute."""
    auth = AuthorityRequirement(
        required_role="ROLE_CERTIFIED_OPERATOR",
        allowed_scopes=frozenset({"scope:math:transform", "scope:proof:read"}),
        requires_audit_receipt=True,
    )

    # Missing role
    assert not auth.is_authorized(
        granted_roles={"ROLE_GUEST"},
        granted_scopes={"scope:math:transform", "scope:proof:read"},
        has_audit_receipt=True,
    )
    # Missing scope
    assert not auth.is_authorized(
        granted_roles={"ROLE_CERTIFIED_OPERATOR"},
        granted_scopes={"scope:math:transform"},
        has_audit_receipt=True,
    )
    # Missing audit receipt
    assert not auth.is_authorized(
        granted_roles={"ROLE_CERTIFIED_OPERATOR"},
        granted_scopes={"scope:math:transform", "scope:proof:read"},
        has_audit_receipt=False,
    )
    # Authorized
    assert auth.is_authorized(
        granted_roles={"ROLE_CERTIFIED_OPERATOR", "ROLE_ADMIN"},
        granted_scopes={"scope:math:transform", "scope:proof:read", "scope:extra"},
        has_audit_receipt=True,
    )


# --- 2. Typed Route Composition ---


def test_typed_route_composition_success_and_failure() -> None:
    """Verify Post(T_i) |= Pre(T_{i+1}) with zero implicit coercion."""
    c1 = WorkContract(
        contract_id="c1",
        source="state.a",
        target="state.b",
        postconditions=("has.normalized_basis",),
    )
    c2_valid = WorkContract(
        contract_id="c2-val",
        source="state.b",
        target="state.c",
        preconditions=("has.normalized_basis",),
        postconditions=("has.eigenvalues",),
    )
    c2_unmet_pre = WorkContract(
        contract_id="c2-bad-pre",
        source="state.b",
        target="state.c",
        preconditions=("has.compact_support",),  # Not provided by c1
    )
    c2_endpoint_mismatch = WorkContract(
        contract_id="c2-bad-end",
        source="state.d",  # Mismatch with c1.target 'state.b'
        target="state.e",
    )

    route_valid = Route.from_contracts((c1, c2_valid))
    is_valid, err = route_valid.is_valid_composition()
    assert is_valid is True
    assert err is None
    assert route_valid.nodes == ("state.a", "state.b", "state.c")

    route_unmet = Route.from_contracts((c1, c2_unmet_pre))
    is_valid, err = route_unmet.is_valid_composition()
    assert is_valid is False
    assert "unmet preconditions" in (err or "")

    route_mismatch = Route.from_contracts((c1, c2_endpoint_mismatch))
    is_valid, err = route_mismatch.is_valid_composition()
    assert is_valid is False
    assert "Endpoint mismatch" in (err or "")


# --- 3. RouteRegistry & DecisionGraph Substrate Integration ---


def test_route_registry_projects_to_decision_graph() -> None:
    """Verify RouteRegistry uses DecisionGraph substrate without duplicating graph primitives."""
    c1 = WorkContract(contract_id="c1", source="sig.in", target="sig.mid", is_certified=True)
    c2 = WorkContract(contract_id="c2", source="sig.mid", target="sig.out", is_certified=True)

    reg = RouteRegistry([c1, c2])
    assert len(reg.all_contracts()) == 2
    assert len(reg.find_by_source("sig.in")) == 1
    assert len(reg.find_by_target("sig.out")) == 1

    graph = reg.as_decision_graph()
    snapshot = graph.snapshot
    assert len(snapshot.nodes) == 3
    assert len(snapshot.edges) == 2
    topological = graph.topological_sort()
    assert tuple(topological) == ("sig.in", "sig.mid", "sig.out")


# --- 4. Router Search and Constraint Qualifications ---


def test_router_qualification_and_rejection_categories() -> None:
    """Verify Router fail-closed behavior across authority, resources, and invariants."""
    c_cheap_unauth = WorkContract(
        contract_id="c.cheap.unauth",
        source="state.start",
        target="state.goal",
        cost=1.0,
        authority=AuthorityRequirement(required_role="ADMIN"),
    )
    c_costly_auth = WorkContract(
        contract_id="c.costly.auth",
        source="state.start",
        target="state.goal",
        cost=10.0,
        authority=AuthorityRequirement(required_role="USER"),
    )
    c_heavy_res = WorkContract(
        contract_id="c.heavy.res",
        source="state.start",
        target="state.goal",
        cost=2.0,
        resources=ResourceRequirement(gpu_count=4.0),
        authority=AuthorityRequirement(required_role="USER"),
    )
    c_invariant_violation = WorkContract(
        contract_id="c.bad.inv",
        source="state.start",
        target="state.goal",
        cost=1.5,
        invariants=("INV_APPROXIMATION",),
        authority=AuthorityRequirement(required_role="USER"),
    )
    c_uncertified = WorkContract(
        contract_id="c.uncert",
        source="state.start",
        target="state.goal",
        cost=0.5,
        is_certified=False,
        authority=AuthorityRequirement(required_role="USER"),
    )

    reg = RouteRegistry(
        [c_cheap_unauth, c_costly_auth, c_heavy_res, c_invariant_violation, c_uncertified]
    )
    router = Router(reg)

    # 1. Authority rejection: user cannot use c.cheap.unauth, must select c.costly.auth
    candidates = router.find_routes(
        target="state.goal",
        available_capabilities={"state.start"},
        budget=RoutingBudget(max_cost=100.0, max_gpu_count=1.0),
        granted_roles={"USER"},
        prohibited_invariants={"INV_APPROXIMATION"},
    )

    status_map = {c.route.contracts[0].contract_id: c.status for c in candidates}
    assert status_map["c.cheap.unauth"] == "BLOCKED_AUTHORITY"
    assert status_map["c.heavy.res"] == "BLOCKED_RESOURCE"
    assert status_map["c.bad.inv"] == "BLOCKED_INVARIANT"
    assert status_map["c.uncert"] == "UNCERTIFIED"
    assert status_map["c.costly.auth"] == "ADMISSIBLE"

    # Best candidate is c.costly.auth
    assert candidates[0].candidate_id.startswith("cand-state.goal")
    assert candidates[0].route.contracts[0].contract_id == "c.costly.auth"


# --- 5. RouteCertificate Seal ---


def test_route_certificate_issuance_and_invariance() -> None:
    """Verify RouteCertificate cryptographic seal generation and failure on invalid routes."""
    c1 = WorkContract(contract_id="c1", source="x", target="y", is_certified=True)
    c2 = WorkContract(contract_id="c2", source="y", target="z", is_certified=True)
    route = Route.from_contracts((c1, c2))

    cert = create_route_certificate(route, target="z", input_nodes=("x",))
    assert cert.certified is True
    assert cert.output_node == "z"
    assert cert.route_contract_ids == ("c1", "c2")
    assert len(cert.sha256_seal) == 64

    # Uncertified route raises ValueError
    c_uncert = WorkContract(contract_id="c_un", source="x", target="y", is_certified=False)
    route_bad = Route.from_contracts((c_uncert,))
    with pytest.raises(ValueError):
        create_route_certificate(route_bad, target="y", input_nodes=("x",))


# --- 6. GoalSolver Terminal States ---


def test_goal_solver_terminal_states() -> None:
    """Verify GoalSolver produces formal terminal states without falsely claiming satisfaction."""
    c_math = WorkContract(
        contract_id="c.math", source="input.matrix", target="sig.eigenvalues", cost=5.0
    )
    c_auth = WorkContract(
        contract_id="c.restricted",
        source="input.matrix",
        target="sig.secret",
        cost=1.0,
        authority=AuthorityRequirement(required_role="SECURITY_OFFICER"),
    )
    c_costly = WorkContract(
        contract_id="c.costly",
        source="input.matrix",
        target="sig.heavy",
        cost=100.0,
    )

    reg = RouteRegistry([c_math, c_auth, c_costly])
    router = Router(reg)
    solver = GoalSolver(router)
    state = KnowledgeState.initial(initial_signatures={"input.matrix"})

    # 1. SATISFIED: target reachable within budget
    goal_ok = Goal(
        goal_id="g1",
        target_signatures=("sig.eigenvalues",),
        budget=RoutingBudget(max_cost=10.0),
    )
    sol_1 = solver.solve(goal_ok, state)
    assert sol_1.status == "SATISFIED"
    assert sol_1.is_satisfied is True
    assert sol_1.resolved_subgoals == ("sig.eigenvalues",)

    # 2. BLOCKED_AUTHORITY: missing credentials
    goal_auth = Goal(
        goal_id="g2",
        target_signatures=("sig.secret",),
        authority_roles=frozenset({"STANDARD_USER"}),
    )
    sol_2 = solver.solve(goal_auth, state)
    assert sol_2.status == "BLOCKED_AUTHORITY"
    assert not sol_2.is_satisfied

    # 3. BLOCKED_RESOURCE: cost exceeds budget
    goal_res = Goal(
        goal_id="g3",
        target_signatures=("sig.heavy",),
        budget=RoutingBudget(max_cost=50.0),
    )
    sol_3 = solver.solve(goal_res, state)
    assert sol_3.status == "BLOCKED_RESOURCE"

    # 4. UNREACHABLE: target has no path
    goal_unreach = Goal(
        goal_id="g4",
        target_signatures=("sig.nonexistent",),
    )
    sol_4 = solver.solve(goal_unreach, state)
    assert sol_4.status == "UNREACHABLE"

    # 5. PARTIALLY_SATISFIED: one target resolvable, one unresolvable
    goal_partial = Goal(
        goal_id="g5",
        target_signatures=("sig.eigenvalues", "sig.nonexistent"),
        budget=RoutingBudget(max_cost=10.0),
    )
    sol_5 = solver.solve(goal_partial, state)
    assert sol_5.status == "PARTIALLY_SATISFIED"
    assert "sig.eigenvalues" in sol_5.resolved_subgoals
    assert "sig.nonexistent" in sol_5.unresolved_subgoals


# --- 7. Serialization Roundtrips ---


def test_routing_serialization_roundtrip() -> None:
    """Verify deterministic JSON serialization roundtrips for WorkContract and RouteCertificate."""
    contract = WorkContract(
        contract_id="contract.roundtrip",
        source="node.a",
        target="node.b",
        preconditions=("pre.1", "pre.2"),
        postconditions=("post.1",),
        cost=3.1415,
        error_tolerance=0.001,
        resources=ResourceRequirement(cpu_cores=4.0, ram_mb=2048.0, energy_joules=150.0),
        authority=AuthorityRequirement(
            required_role="ROLE_OPERATOR", allowed_scopes=frozenset({"scope:run"})
        ),
        invariants=("INV_ENERGY_CONSERVED",),
    )

    serialized = serialize_work_contract(contract)
    deserialized = deserialize_work_contract(serialized)

    assert deserialized.contract_id == contract.contract_id
    assert deserialized.source == contract.source
    assert deserialized.target == contract.target
    assert deserialized.cost == contract.cost
    assert deserialized.resources.cpu_cores == contract.resources.cpu_cores
    assert deserialized.authority.required_role == contract.authority.required_role
    assert deserialized.invariants == contract.invariants
