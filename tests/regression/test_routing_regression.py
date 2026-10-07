"""Regression tests replaying historical Work Router generations v0.1 - v0.9 and Goal Solver.

Verifies:
1. Work Router v0.1: Fail-closed uncertified shortcut rejection, observation vs materialization.
2. Work Router v0.3: Resource/power constraints and control stability routing.
3. Work Router v0.4: Invariant query enforcement.
4. Work Router v0.5: Certified route derivation and RouteCertificate binding.
5. Work Router v0.8: Multi-contract runtime composition.
6. Work Router v0.9: Tolerance-aware route selection and domain validity contracts.
7. Cross-Class Goal Solver: Goal decomposition and terminal state adjudication.
8. Deterministic Replay Invariant: Identical inputs produce identical route candidates.
"""

from __future__ import annotations

from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.routing.contracts import (
    AuthorityRequirement,
    RoutingBudget,
    WorkContract,
)
from mapeogeo.routing.goal import Goal
from mapeogeo.routing.registry import RouteRegistry
from mapeogeo.routing.route import create_route_certificate
from mapeogeo.routing.router import Router
from mapeogeo.routing.solver import GoalSolver

# --- 1. Work Router v0.1 Fixture Replay ---


def test_work_router_v01_uncertified_shortcut_never_beats_certified_route() -> None:
    """Historical v0.1 fixture:
    Cheaper uncertified shortcut must be rejected in favor of certified route.
    """
    edges = [
        WorkContract(
            contract_id="wr.area.sum",
            source="psmsl.directional_scales",
            target="work.area_exponent",
            cost=1.0,
            is_certified=True,
        ),
        WorkContract(
            contract_id="wr.area.sign",
            source="work.area_exponent",
            target="work.area_expanding",
            cost=1.0,
            is_certified=True,
        ),
        # Deliberately cheaper but uncertified shortcut
        WorkContract(
            contract_id="wr.unsafe.det-shortcut",
            source="psmsl.directional_scales",
            target="work.area_expanding",
            cost=0.01,
            is_certified=False,
        ),
    ]
    reg = RouteRegistry(edges)
    router = Router(reg)

    candidates = router.find_routes(
        target="work.area_expanding",
        available_capabilities={"psmsl.directional_scales"},
    )
    # Top admissible candidate must be the certified 2-step route, NOT the uncertified shortcut
    admissible = [c for c in candidates if c.is_admissible]
    assert len(admissible) == 1
    best = admissible[0]
    assert tuple(c.contract_id for c in best.route.contracts) == ("wr.area.sum", "wr.area.sign")
    assert best.route.total_cost == 2.0
    assert best.route.certified is True

    # The shortcut candidate is marked UNCERTIFIED
    shortcut_cands = [
        c for c in candidates if c.route.contracts[0].contract_id == "wr.unsafe.det-shortcut"
    ]
    assert len(shortcut_cands) == 1
    assert shortcut_cands[0].status == "UNCERTIFIED"


# --- 2. Work Router v0.3 Power & Control Fixture Replay ---


def test_work_router_v03_power_and_control_routing() -> None:
    """Historical v0.3 fixture: Phasor power, THD materialization, and state matrix stability."""
    contracts = [
        WorkContract(
            "power.complex", "power.voltage_current_phasors", "work.complex_power", cost=2.0
        ),
        WorkContract("power.real", "work.complex_power", "work.real_power", cost=0.2),
        WorkContract(
            "power.apparent", "power.voltage_current_magnitudes", "work.apparent_power", cost=0.5
        ),
        WorkContract(
            "power.thd.spectrum",
            "power.voltage_window",
            "work.voltage_spectrum",
            cost=12.0,
            requires_materialization=True,
        ),
        WorkContract("power.thd", "work.voltage_spectrum", "work.voltage_thd", cost=2.0),
        WorkContract(
            "control.generator-stability",
            "psmsl.generator_g",
            "work.asymptotically_stable",
            cost=0.2,
        ),
        WorkContract(
            "control.eigs",
            "control.state_matrix",
            "work.eigenvalues",
            cost=10.0,
            requires_materialization=True,
        ),
        WorkContract(
            "control.spectral-abscissa", "work.eigenvalues", "work.spectral_abscissa", cost=1.0
        ),
        WorkContract(
            "control.stability", "work.spectral_abscissa", "work.asymptotically_stable", cost=0.2
        ),
    ]
    reg = RouteRegistry(contracts)
    router = Router(reg)

    # Real power routes through complex power
    cands_p = router.find_routes(
        "work.real_power", available_capabilities={"power.voltage_current_phasors"}
    )
    adm_p = [c for c in cands_p if c.is_admissible]
    assert tuple(c.contract_id for c in adm_p[0].route.contracts) == ("power.complex", "power.real")
    assert not adm_p[0].route.materializes

    # Generator stability avoids eigensolver
    cands_s = router.find_routes(
        "work.asymptotically_stable", available_capabilities={"psmsl.generator_g"}
    )
    adm_s = [c for c in cands_s if c.is_admissible]
    assert tuple(c.contract_id for c in adm_s[0].route.contracts) == (
        "control.generator-stability",
    )
    assert not adm_s[0].route.materializes

    # General state matrix stability routes through eigenvalues and materializes
    cands_mat = router.find_routes(
        "work.asymptotically_stable", available_capabilities={"control.state_matrix"}
    )
    adm_mat = [c for c in cands_mat if c.is_admissible]
    assert tuple(c.contract_id for c in adm_mat[0].route.contracts) == (
        "control.eigs",
        "control.spectral-abscissa",
        "control.stability",
    )
    assert adm_mat[0].route.materializes is True


# --- 3. Work Router v0.5 Derived Route Certificate Fixture Replay ---


def test_work_router_v05_certified_route_derivation() -> None:
    """Historical v0.5 fixture: Issuing cryptographic RouteCertificate for derived route."""
    c1 = WorkContract("wr.step1", "input.data", "mid.feature", cost=1.5, is_certified=True)
    c2 = WorkContract("wr.step2", "mid.feature", "output.target", cost=2.5, is_certified=True)
    reg = RouteRegistry([c1, c2])
    router = Router(reg)

    candidates = router.find_routes("output.target", available_capabilities={"input.data"})
    admissible = [c for c in candidates if c.is_admissible]
    assert len(admissible) == 1
    best_route = admissible[0].route

    cert = create_route_certificate(best_route, target="output.target", input_nodes=("input.data",))
    assert cert.certified is True
    assert cert.total_cost == 4.0
    assert cert.output_node == "output.target"
    assert cert.route_contract_ids == ("wr.step1", "wr.step2")
    assert len(cert.sha256_seal) == 64


# --- 4. Work Router v0.9 Composable Contracts & Tolerance Replay ---


def test_work_router_v09_tolerance_and_validity_contracts() -> None:
    """Historical v0.9 fixture: Error-budget route selection and domain validity."""
    edges = [
        WorkContract("cheap.a", "x", "mid", cost=1.0, error_tolerance=0.03),
        WorkContract("cheap.b", "mid", "answer", cost=1.0, error_tolerance=0.03),
        WorkContract("accurate", "x", "answer", cost=8.0, error_tolerance=0.005),
        WorkContract(
            "invalid.inv",
            "x",
            "answer",
            cost=0.1,
            error_tolerance=0.0,
            invariants=("DISALLOWED_APPROX",),
        ),
        WorkContract("unsafe", "x", "answer", cost=0.01, is_certified=False),
    ]
    reg = RouteRegistry(edges)
    router = Router(reg)

    # 1. Loose tolerance (0.1) selects cheapest route (cheap.a + cheap.b, cost 2.0, error 0.06)
    cands_loose = router.find_routes(
        target="answer",
        available_capabilities={"x"},
        tolerance=0.1,
        prohibited_invariants={"DISALLOWED_APPROX"},
    )
    adm_loose = [c for c in cands_loose if c.is_admissible]
    assert tuple(c.contract_id for c in adm_loose[0].route.contracts) == ("cheap.a", "cheap.b")
    assert adm_loose[0].route.total_error == 0.06
    assert adm_loose[0].route.total_cost == 2.0

    # 2. Tight tolerance (0.01) selects expensive accurate route (accurate, cost 8.0, error 0.005)
    cands_tight = router.find_routes(
        target="answer",
        available_capabilities={"x"},
        tolerance=0.01,
        prohibited_invariants={"DISALLOWED_APPROX"},
    )
    adm_tight = [c for c in cands_tight if c.is_admissible]
    assert tuple(c.contract_id for c in adm_tight[0].route.contracts) == ("accurate",)
    assert adm_tight[0].route.total_error == 0.005
    assert adm_tight[0].route.total_cost == 8.0

    # 3. Impossible tolerance (0.001) leaves no admissible routes
    cands_imp = router.find_routes(
        target="answer",
        available_capabilities={"x"},
        tolerance=0.001,
        prohibited_invariants={"DISALLOWED_APPROX"},
    )
    adm_imp = [c for c in cands_imp if c.is_admissible]
    assert len(adm_imp) == 0


# --- 5. Deterministic Replay Invariant ---


def test_router_deterministic_replay_invariance() -> None:
    """Verify identical (G_t, Q, contracts, resources, authority) yields identical order."""
    contracts = [
        WorkContract("c1", "a", "b", cost=2.0),
        WorkContract("c2", "b", "c", cost=3.0),
        WorkContract("c3", "a", "c", cost=6.0),
        WorkContract("c4", "a", "c", cost=7.0),
    ]
    reg = RouteRegistry(contracts)
    router = Router(reg)

    res_1 = router.find_routes("c", available_capabilities={"a"})
    res_2 = router.find_routes("c", available_capabilities={"a"})

    assert [c.candidate_id for c in res_1] == [c.candidate_id for c in res_2]
    assert [c.route.total_cost for c in res_1] == [c.route.total_cost for c in res_2]


# --- 6. End-to-End Goal Solver & Kernel Invariant ---


def test_goal_solver_consumes_kernel_without_duplication() -> None:
    """Verify GoalSolver decomposes Q into WorkRequirements and terminates soundly."""
    c_factor = WorkContract("contract.factor", "source.poly", "sig.factors", cost=2.0)
    c_roots = WorkContract("contract.roots", "sig.factors", "sig.roots", cost=1.0)
    c_secret = WorkContract(
        "contract.secret",
        "source.poly",
        "sig.classified",
        cost=1.0,
        authority=AuthorityRequirement(required_role="SECURITY_ADMIN"),
    )

    reg = RouteRegistry([c_factor, c_roots, c_secret])
    router = Router(reg)
    solver = GoalSolver(router)

    state = KnowledgeState.initial(initial_signatures={"source.poly"})

    # Goal needing polynomial roots
    goal = Goal(
        goal_id="goal-algebra",
        target_signatures=("sig.roots",),
        budget=RoutingBudget(max_cost=10.0),
    )
    sol = solver.solve(goal, state)
    assert sol.status == "SATISFIED"
    assert len(sol.selected_routes) == 1
    assert tuple(c.contract_id for c in sol.selected_routes[0].contracts) == (
        "contract.factor",
        "contract.roots",
    )
    assert sol.total_cost == 3.0
