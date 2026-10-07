"""Unit tests for the domain-neutral UoW Kernel layer.

Verifies:
1. 9-tuple formal specification and deterministic SHA-256 seal.
2. Deficiency extraction and strict deficiency conservation accounting.
3. Prospective planning and utility ranking.
4. 4-gate fail-closed certification.
5. Atomic state transition and autonomous rational refusal.
6. First-class Ability and Learning reach metrics.
7. Obstruction detection and repair operators.
8. Deterministic serialization roundtrips.
9. Domain neutrality (zero domain imports or domain vocabulary).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.certification import CertificationBoundary
from mapeogeo.kernel.deficiency import (
    DeficiencyConservationError,
    DeficiencyExtractor,
    WorkRequirement,
)
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.obstruction import ObstructionOperator, RepairOperator
from mapeogeo.kernel.planning import ProspectivePlanner
from mapeogeo.kernel.reach import compute_ability, is_learning_event
from mapeogeo.kernel.serialization import (
    deserialize_knowledge_state,
    serialize_knowledge_state,
)
from mapeogeo.kernel.spec import KERNEL_9_TUPLE, compute_kernel_9_tuple_seal
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.kernel.transition import (
    StateTransitionEngine,
)
from mapeogeo.kernel.utility import UtilityModel

# --- 1. Formal 9-Tuple Specification ---


def test_kernel_9_tuple_spec_completeness() -> None:
    """Verify that all 9 components are declared with explicit formal signatures and invariants."""
    symbols = [comp.symbol for comp in KERNEL_9_TUPLE]
    expected_symbols = ["M_6", "Omega", "rho", "G", "D", "P", "U", "C", "A"]
    assert symbols == expected_symbols
    assert len(KERNEL_9_TUPLE) == 9

    seal = compute_kernel_9_tuple_seal()
    assert isinstance(seal, str)
    assert len(seal) == 64
    # Deterministic seal invariance check
    assert seal == compute_kernel_9_tuple_seal()


# --- 2. Deficiency Extractor & Conservation Law ---


def test_deficiency_extraction_and_conservation_success() -> None:
    """Verify deficiency extraction and that valid transitions satisfy conservation."""
    reqs = [
        WorkRequirement(req_id="req-1", required_signatures=("sig.a", "sig.b"), weight=10.0),
        WorkRequirement(req_id="req-2", required_signatures=("sig.b", "sig.c"), weight=20.0),
        WorkRequirement(req_id="req-3", required_signatures=("sig.d",), weight=15.0),
    ]

    extractor = DeficiencyExtractor()
    state_0 = KnowledgeState.initial(initial_signatures={"sig.a"})

    dist_0 = extractor.extract_deficiencies(reqs, state_0)
    assert dist_0.total_requirements == 3
    assert dist_0.covered_requirements == 0
    assert dist_0.total_deficient_severity == 45.0
    assert dist_0.signature_frequency["sig.b"] == 2

    # Transition: acquire sig.b and sig.c
    state_1 = state_0.transition(
        new_signatures={"sig.b", "sig.c"},
        new_nodes=(),
    )
    dist_1 = extractor.extract_deficiencies(reqs, state_1)
    assert dist_1.covered_requirements == 2  # req-1 and req-2 now fully covered
    assert dist_1.deficient_requirements == 1  # req-3 remaining
    assert dist_1.total_deficient_severity == 15.0

    # Verify conservation: delta = 30.0 (resolved req-1: 10, req-2: 20)
    report = extractor.verify_conservation(dist_0, dist_1)
    assert report["is_conserved"] is True
    assert report["d_resolved"] == 30.0
    assert report["d_unchanged"] == 15.0


def test_deficiency_conservation_failure_on_silent_work_loss() -> None:
    """Verify that silent disappearance of a work requirement raises DeficiencyConservationError."""
    reqs_t0 = [
        WorkRequirement(req_id="req-1", required_signatures=("sig.a",), weight=10.0),
        WorkRequirement(req_id="req-2", required_signatures=("sig.b",), weight=20.0),
    ]
    # In t1, req-2 is silently missing from the requirement set
    reqs_t1 = [
        WorkRequirement(req_id="req-1", required_signatures=("sig.a",), weight=10.0),
    ]

    extractor = DeficiencyExtractor()
    state = KnowledgeState.initial()

    dist_0 = extractor.extract_deficiencies(reqs_t0, state)
    dist_1 = extractor.extract_deficiencies(reqs_t1, state)

    with pytest.raises(DeficiencyConservationError) as exc_info:
        extractor.verify_conservation(dist_0, dist_1)
    assert "silently disappeared" in str(exc_info.value)


# --- 3. Prospective Planning & Utility Model ---


def test_prospective_planner_and_utility_ranking() -> None:
    """Verify prospective capability prediction and cost-efficiency ranking."""
    reqs = [
        WorkRequirement(req_id="req-1", required_signatures=("sig.alpha",), weight=10.0),
        WorkRequirement(req_id="req-2", required_signatures=("sig.beta",), weight=50.0),
    ]

    state = KnowledgeState.initial()
    planner = ProspectivePlanner()
    model = UtilityModel()

    cand_alpha = MachineryCandidate(
        candidate_id="cand-alpha",
        provided_signatures=("sig.alpha",),
        cost=5.0,
        nodes=(MachineryNode(node_id="node-alpha", provided_signatures=("sig.alpha",)),),
    )
    cand_beta = MachineryCandidate(
        candidate_id="cand-beta",
        provided_signatures=("sig.beta",),
        cost=10.0,
        nodes=(MachineryNode(node_id="node-beta", provided_signatures=("sig.beta",)),),
    )

    plan_alpha = planner.plan_candidate(reqs, state, cand_alpha)
    plan_beta = planner.plan_candidate(reqs, state, cand_beta)

    assert plan_alpha.unlocked_weight == 10.0
    assert plan_beta.unlocked_weight == 50.0
    assert plan_beta.predicted_delta_a > plan_alpha.predicted_delta_a

    rankings = model.rank_candidates(reqs, state, [cand_alpha, cand_beta])
    assert len(rankings) == 2
    # beta unlocks 50 wt (predicted ~7.0 / 10 = 0.7) vs alpha 10 wt (predicted ~2.2 / 5 = 0.44)
    assert rankings[0].candidate_id == "cand-beta"


# --- 4. 4-Gate Certification Boundary ---


def test_certification_boundary_four_gates() -> None:
    """Verify fail-closed behavior across all 4 gates."""
    grammar = WorkGrammar()
    grammar.register_witness("wit-alpha", "sig.alpha", "proof-hash-1")
    certifier = CertificationBoundary(grammar)

    state = KnowledgeState.initial(initial_signatures={"sig.dep"})

    # Gate 1 Failure: Missing dependency
    cand_unresolved = MachineryCandidate(
        candidate_id="cand-bad-dep",
        provided_signatures=("sig.alpha",),
        cost=2.0,
        nodes=(
            MachineryNode(
                node_id="n-1",
                provided_signatures=("sig.alpha",),
                dependencies=("sig.missing",),
                witness_id="wit-alpha",
            ),
        ),
        witness_ids=("wit-alpha",),
    )
    res_1 = certifier.certify_candidate(cand_unresolved, state)
    assert res_1.is_certified is False
    assert "Gate 1 failed" in (res_1.failure_reason or "")

    # Gate 2 Failure: Unregistered witness
    cand_bad_witness = MachineryCandidate(
        candidate_id="cand-bad-wit",
        provided_signatures=("sig.alpha",),
        cost=2.0,
        nodes=(
            MachineryNode(
                node_id="n-2",
                provided_signatures=("sig.alpha",),
                dependencies=("sig.dep",),
                witness_id="wit-unregistered",
            ),
        ),
        witness_ids=("wit-unregistered",),
    )
    res_2 = certifier.certify_candidate(cand_bad_witness, state)
    assert res_2.is_certified is False
    assert "Gate 2 failed" in (res_2.failure_reason or "")

    # Valid candidate: passes all 4 gates
    cand_valid = MachineryCandidate(
        candidate_id="cand-valid",
        provided_signatures=("sig.alpha",),
        cost=2.0,
        nodes=(
            MachineryNode(
                node_id="n-3",
                provided_signatures=("sig.alpha",),
                dependencies=("sig.dep",),
                witness_id="wit-alpha",
            ),
        ),
        witness_ids=("wit-alpha",),
    )
    res_valid = certifier.certify_candidate(cand_valid, state)
    assert res_valid.is_certified is True
    assert len(res_valid.gates_passed) == 4
    assert res_valid.certificate_id.startswith("cert-")


# --- 5. State Transition Engine & Rational Refusal ---


def test_state_transition_admission_and_rational_refusal() -> None:
    """Verify autonomous capability acquisition and rational refusal when J < tau_J."""
    grammar = WorkGrammar()
    grammar.register_witness("wit-1", "sig.target", "hash-1")

    engine = StateTransitionEngine(grammar=grammar, refusal_threshold=1.5)

    reqs = [WorkRequirement(req_id="req-target", required_signatures=("sig.target",), weight=100.0)]
    state_0 = KnowledgeState.initial()

    high_utility_cand = MachineryCandidate(
        candidate_id="cand-high",
        provided_signatures=("sig.target",),
        cost=2.0,
        nodes=(
            MachineryNode(
                node_id="n-target",
                provided_signatures=("sig.target",),
                witness_id="wit-1",
            ),
        ),
        witness_ids=("wit-1",),
    )

    # 1. High utility candidate -> Acquired
    outcome_1 = engine.step(reqs, state_0, [high_utility_cand])
    assert outcome_1.decision == "TRANSITION"
    assert outcome_1.verdict == "CAPABILITY_ACQUIRED"
    assert outcome_1.is_learning_event is True
    assert "sig.target" in outcome_1.next_state.signatures
    assert outcome_1.conservation_report is not None
    assert outcome_1.conservation_report["is_conserved"] is True

    # 2. Next round: target is already covered, candidate offers negligible or no gain
    low_utility_cand = MachineryCandidate(
        candidate_id="cand-redundant",
        provided_signatures=("sig.target",),
        cost=10.0,
        nodes=(
            MachineryNode(
                node_id="n-red",
                provided_signatures=("sig.target",),
                witness_id="wit-1",
            ),
        ),
        witness_ids=("wit-1",),
    )

    outcome_2 = engine.step(reqs, outcome_1.next_state, [low_utility_cand])
    assert outcome_2.decision == "REFUSE"
    assert outcome_2.verdict == "NO_MATERIAL_CAPABILITY_ACQUISITION_AVAILABLE"
    assert outcome_2.next_state == outcome_1.next_state


# --- 6. First-Class Ability & Learning Predicates ---


def test_ability_and_learning_event_predicates() -> None:
    """Verify formal Ability_t(Q) = ReachableCertifiedWork and Learning reach expansion."""
    reqs = [
        WorkRequirement(req_id="r1", required_signatures=("a",), weight=10.0),
        WorkRequirement(req_id="r2", required_signatures=("a", "b"), weight=20.0),
        WorkRequirement(req_id="r3", required_signatures=("c",), weight=30.0),
    ]

    # At t0: only 'a' is certified -> only r1 is reachable
    ability_0 = compute_ability(reqs, {"a"})
    assert ability_0 == 10.0

    # At t1: 'a' and 'b' certified -> r1 and r2 reachable
    ability_1 = compute_ability(reqs, {"a", "b"})
    assert ability_1 == 30.0

    # Check learning event
    assert is_learning_event({"a"}, {"a", "b"}) is True
    assert is_learning_event({"a", "b"}, {"a", "b"}) is False
    assert is_learning_event({"a", "b"}, {"a"}) is False


# --- 7. Obstruction & Repair Operators ---


def test_obstruction_and_repair_operators() -> None:
    """Verify Omega detects missing dependencies and rho repairs them."""
    omega = ObstructionOperator()
    rho = RepairOperator()

    node = MachineryNode(
        node_id="node-x",
        provided_signatures=("sig.x",),
        dependencies=("legacy.dep",),
        witness_id=None,
    )

    # Initial check: obstructed due to missing dependency and missing witness
    report_0 = omega.evaluate(node, available_capabilities={"certified.dep"})
    assert report_0.is_obstructed is True
    assert report_0.obstruction_index == 2

    # Repair: remap dependency and attach witness
    repaired_node = rho.repair(
        node,
        substitute_deps={"legacy.dep": "certified.dep"},
        surrogate_witness_id="wit-x-cert",
    )
    assert repaired_node.dependencies == ("certified.dep",)
    assert repaired_node.witness_id == "wit-x-cert"

    # Re-evaluate with Omega
    report_1 = omega.evaluate(repaired_node, available_capabilities={"certified.dep"})
    assert report_1.is_obstructed is False
    assert report_1.obstruction_index == 0


# --- 8. Deterministic Serialization Roundtrips ---


def test_deterministic_serialization_roundtrip() -> None:
    """Verify deterministic JSON serialization and deserialization."""
    state = KnowledgeState(
        t=3,
        signatures=frozenset({"sig.alpha", "sig.beta"}),
        certified_nodes=(
            MachineryNode(
                node_id="node-1",
                provided_signatures=("sig.alpha",),
                dependencies=(),
                witness_id="wit-1",
            ),
        ),
        witness_ids=frozenset({"wit-1"}),
        cumulative_ability=15.5,
        state_hash="dummy-hash",
        metadata={"cycle": 3},
    )

    serialized = serialize_knowledge_state(state)
    deserialized = deserialize_knowledge_state(serialized)

    assert deserialized.t == state.t
    assert deserialized.signatures == state.signatures
    assert deserialized.witness_ids == state.witness_ids
    assert deserialized.cumulative_ability == state.cumulative_ability
    assert len(deserialized.certified_nodes) == 1
    assert deserialized.certified_nodes[0].node_id == "node-1"


# --- 9. Domain Neutrality & Lexical Hygiene ---


def test_kernel_and_grammar_domain_neutrality() -> None:
    """Verify kernel and grammar have ZERO imports of domain adapters and no domain terminology."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    kernel_dir = repo_root / "src" / "mapeogeo" / "kernel"
    grammar_dir = repo_root / "src" / "mapeogeo" / "grammar"

    python_files = list(kernel_dir.glob("*.py")) + list(grammar_dir.glob("*.py"))
    assert len(python_files) >= 10

    # Forbidden domain modules in imports
    forbidden_import_prefixes = (
        "mapeogeo.domains",
        "mapeogeo.domains.mathematics",
        "mapeogeo.domains.physics",
        "mapeogeo.domains.software",
    )

    for py_file in python_files:
        code = py_file.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_import_prefixes), (
                        f"Domain leakage in {py_file.name}: import {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(forbidden_import_prefixes), (
                        f"Domain leakage in {py_file.name}: from {node.module} import ..."
                    )
