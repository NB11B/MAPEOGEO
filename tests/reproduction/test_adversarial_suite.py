"""Permanent Release Test: Comprehensive Fail-Closed Adversarial Suite.

Combines the strongest negative controls across all 7 layers of MAPEOGEO v2:
1. Graph: cycle rejection, dangling edge rejection, relation strength ordering.
2. Kernel: deficiency conservation violation, uncertified transition refusal.
3. Routing: resource budget exceedance, authority privilege violation.
4. Proof: false replay rejection, evidence counterexample, generation/admission separation.
5. Mathematics: semantic drift rejection, unproved obligation refusal.
6. Physics: dimensional inconsistency, conservation drift, zero observations handling.
7. Software: unit test failure, latency SLA breach, concurrency violation.

Governing Release Invariant:
    N_false_acceptance == 0
"""

import pytest

from mapeogeo.domains.mathematics import FactoringClassification
from mapeogeo.domains.mathematics.adapter import MathematicsAdapter
from mapeogeo.domains.mathematics.obligations import MathematicalProofObligation
from mapeogeo.domains.mathematics.ontology import Theorem, TheoremKind
from mapeogeo.domains.physics.certification import PhysicalCertificationBoundary
from mapeogeo.domains.physics.ontology import (
    MeasuredObservation,
    PhysicalCertificationVerdict,
    PhysicalConstraint,
    PhysicalHypothesis,
)
from mapeogeo.domains.software.certification import SoftwareCertificationBoundary
from mapeogeo.domains.software.ontology import (
    SoftwareCertificationVerdict,
    SoftwareEvidence,
    SoftwareMachinery,
    SoftwareRequirement,
)
from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node
from mapeogeo.graph.relation import RelationType
from mapeogeo.kernel.deficiency import (
    DeficiencyConservationError,
    DeficiencyExtractor,
    WorkRequirement,
)
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode
from mapeogeo.kernel.state import KnowledgeState
from mapeogeo.kernel.transition import StateTransitionEngine
from mapeogeo.proof.audit import GenerationAuditRecord, ProofAudit
from mapeogeo.proof.contracts import ProofClaim, ProofStatus
from mapeogeo.proof.replay import BooleanROBDDReplayer, FarkasImplicationReplayer, ReplayStatus
from mapeogeo.routing.contracts import (
    AuthorityRequirement,
    ResourceRequirement,
    RoutingBudget,
)


def test_adversarial_graph_negative_controls() -> None:
    """1. Graph Subsystem Fail-Closed Controls."""
    # 1a. Reject dangling edge
    g_dangle = DecisionGraph(graph_id="g_dangle")
    tx_dangle = g_dangle.begin_transaction()
    tx_dangle.add_node(Node(node_id="a"))
    tx_dangle.add_edge(Edge(source_id="a", target_id="nonexistent"))
    with pytest.raises(ValueError, match="nonexistent target_id"):
        tx_dangle.validate()

    # 1b. Reject circular dependency
    g_cycle = DecisionGraph(graph_id="g_cycle")
    tx_cycle = g_cycle.begin_transaction()
    tx_cycle.add_node(Node(node_id="n1"))
    tx_cycle.add_node(Node(node_id="n2"))
    tx_cycle.add_edge(Edge(source_id="n1", target_id="n2"))
    tx_cycle.add_edge(Edge(source_id="n2", target_id="n1"))
    with pytest.raises(ValueError, match="Cycle detected"):
        tx_cycle.validate()

    # 1c. Reject uncertified equivalence
    contract_equiv = EdgeContract(
        contract_id="c_equiv", required_relation=RelationType.EQUIVALENT_TO, is_certified=False
    )
    assert not contract_equiv.validate_assertion(RelationType.EQUIVALENT_TO)


def test_adversarial_kernel_negative_controls() -> None:
    """2. Kernel Subsystem Fail-Closed Controls."""
    # 2a. Below-threshold candidate triggers rational refusal
    grammar = WorkGrammar()
    grammar.register_witness("wit-1", "sig.target", "hash-1")
    engine = StateTransitionEngine(grammar=grammar, refusal_threshold=1.5)

    reqs = [WorkRequirement(req_id="req-target", required_signatures=("sig.target",), weight=1.0)]
    state_covered = KnowledgeState.initial(initial_signatures={"sig.target"})

    low_gain_cand = MachineryCandidate(
        candidate_id="cand-low",
        provided_signatures=("sig.target",),
        cost=10.0,
        nodes=(
            MachineryNode(
                node_id="n-target",
                provided_signatures=("sig.target",),
                witness_id="wit-1",
            ),
        ),
        witness_ids=("wit-1",),
    )
    outcome = engine.step(reqs, state_covered, [low_gain_cand])
    assert outcome.decision == "REFUSE"

    # 2b. Deficiency conservation failure on silent work loss
    extractor = DeficiencyExtractor()
    dist_0 = extractor.extract_deficiencies(
        [
            WorkRequirement(req_id="r1", required_signatures=("sig.a",), weight=10.0),
            WorkRequirement(req_id="r2", required_signatures=("sig.b",), weight=20.0),
        ],
        KnowledgeState.initial(),
    )
    # Second distribution silently drops r2
    dist_1 = extractor.extract_deficiencies(
        [WorkRequirement(req_id="r1", required_signatures=("sig.a",), weight=10.0)],
        KnowledgeState.initial(),
    )
    with pytest.raises(DeficiencyConservationError, match="silently disappeared"):
        extractor.verify_conservation(dist_0, dist_1)


def test_adversarial_routing_negative_controls() -> None:
    """3. Routing Subsystem Fail-Closed Controls."""
    # 3a. Budget exceedance rejected
    r1 = ResourceRequirement(cpu_cores=4.0, ram_mb=2048.0)
    tight_budget = RoutingBudget(max_cpu_cores=2.0)
    assert not r1.fits_in(tight_budget)

    # 3b. Unauthorized execution rejected
    auth = AuthorityRequirement(
        required_role="ROLE_CERTIFIED_OPERATOR",
        allowed_scopes=frozenset({"scope:admin"}),
        requires_audit_receipt=True,
    )
    assert not auth.is_authorized(
        granted_roles={"ROLE_GUEST"},
        granted_scopes={"scope:admin"},
        has_audit_receipt=True,
    )


def test_adversarial_proof_negative_controls() -> None:
    """4. Proof Subsystem Fail-Closed Controls."""
    claim = ProofClaim(
        claim_id="claim:test",
        subject="p",
        predicate="EQUIVALENT",
        source_id="p1",
        target_id="p2",
        source_identity_sha256="a" * 64,
        target_identity_sha256="b" * 64,
        claim_scope="scope:test",
    )

    # 4a. False Boolean ROBDD replay rejected
    replayer = BooleanROBDDReplayer()
    false_robdd_payload = {
        "left": ["const", True],
        "right": ["const", False],
        "variable_order": [],
    }
    result_b = replayer.replay(claim, false_robdd_payload)
    assert not result_b.passed
    assert result_b.status == ReplayStatus.REJECTED
    assert result_b.proof_status == ProofStatus.COUNTEREXAMPLE

    # 4b. False Farkas implication counterexample rejected
    farkas = FarkasImplicationReplayer()
    false_farkas_payload = {
        "matrix": [[1.0, 0.0], [0.0, 1.0]],
        "bounds": [1.0, 2.0],
        "target_coefficients": [1.0, 2.0],
        "target_bound": 5.0,
        "multipliers": [1.0, 3.0],  # Bad multipliers: 1*1 + 3*2 = 7 > 5
    }
    result_f = farkas.replay(claim, false_farkas_payload)
    assert not result_f.passed
    assert result_f.status == ReplayStatus.REJECTED

    # 4c. Generation audit != admission audit
    gen_audit = GenerationAuditRecord(
        generator_id="search_heuristic",
        trace_id="trace:1",
        steps_evaluated=10,
        pruned_branches=2,
        cost_consumed=1.0,
        generation_passed=True,
        timestamp_utc="2026-10-07T12:00:00Z",
    )
    audit = ProofAudit(
        audit_id="audit:1",
        certificate_id="cert:1",
        generation_audit=gen_audit,
        admission_audit=None,
    )
    assert not audit.is_fully_certified


def test_adversarial_mathematics_negative_controls() -> None:
    """5. Mathematics Domain Fail-Closed Controls."""
    adapter = MathematicsAdapter()

    # 5a. Unproved obligation rejected fail-closed
    thm = Theorem(
        theorem_id="thm:goldbach",
        name="Goldbach Conjecture",
        statement="Every even integer greater than 2 is the sum of two primes",
        kind=TheoremKind.CONJECTURE,
        domain="number_theory",
    )
    unproved_ob = MathematicalProofObligation(
        obligation_id="ob:unproved_goldbach",
        theorem=thm,
        verifier_semantic_id="VERIFIER_UNKNOWN",
    )
    result = adapter.certify(unproved_ob)
    assert not result.is_certified
    assert result.failure_reason is not None

    # 5b. Semantic drift token in factoring rejected
    drift_record = adapter.factor_grammar(
        work=r"\Delta \circ HEURISTIC_HANDWAVE \circ w_1",
        witness_id="w_1",
    )
    assert not drift_record.is_compliant
    assert drift_record.classification == FactoringClassification.SEMANTIC_DRIFT


def test_adversarial_physics_negative_controls() -> None:
    """6. Physics Domain Fail-Closed Controls."""
    boundary = PhysicalCertificationBoundary()
    obs_sample = MeasuredObservation(
        observation_id="obs:sample",
        sensor_id="sensor:1",
        projection_matrix=((1.0, 0.0), (0.0, 1.0)),
        values=(1.0, 2.0),
    )

    # 6a. Dimension inconsistency rejected at Gate D
    bad_dim_hyp = PhysicalHypothesis(
        hypothesis_id="hyp:bad_dim",
        model_name="Bad Dimension Model",
        latent_state=(1.0, 2.0),
        metadata={"has_dimensional_inconsistency": True},
    )
    cert_d = boundary.certify_hypothesis(bad_dim_hyp, observations=[obs_sample])
    assert cert_d.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "GATE_D" not in cert_d.gates_passed

    # 6b. Energy drift rejected at Gate C
    bad_energy_hyp = PhysicalHypothesis(
        hypothesis_id="hyp:bad_energy",
        model_name="Leaky Energy Model",
        latent_state=(1.0, 2.0),
        metadata={"energy_drift": 0.05},
    )
    constraint = PhysicalConstraint(
        constraint_id="c:energy",
        name="Energy Conservation",
        law_type="CONSERVATION_ENERGY",
        tolerance=1e-4,
    )
    cert_c = boundary.certify_hypothesis(
        bad_energy_hyp, observations=[obs_sample], constraints=[constraint]
    )
    assert cert_c.verdict == PhysicalCertificationVerdict.FALSIFIED
    assert "GATE_C" not in cert_c.gates_passed

    # 6c. Zero observations: cannot be promoted to MEASUREMENT_SUPPORTED
    unobserved_hyp = PhysicalHypothesis(
        hypothesis_id="hyp:unobserved",
        model_name="Pure Theoretical Model",
        latent_state=(1.0, 2.0),
    )
    cert_m = boundary.certify_hypothesis(unobserved_hyp, observations=[])
    assert cert_m.verdict == PhysicalCertificationVerdict.THEORETICALLY_ADMISSIBLE


def test_adversarial_software_negative_controls() -> None:
    """7. Software Domain Fail-Closed Controls."""
    boundary = SoftwareCertificationBoundary()
    req = SoftwareRequirement(
        requirement_id="req:test",
        title="Test Req",
        domain="distributed_systems",
        weight=5.0,
        required_signatures=("SIG_API",),
    )

    # 7a. Unit test failure rejected at Gate U
    ev_unit_fail = SoftwareEvidence(
        type_safety_pass=True,
        unit_tests_pass=False,
        static_analysis_pass=True,
        measured_latency_ms=10.0,
        fault_tolerance_pass=True,
    )
    mach_unit = SoftwareMachinery(
        machinery_id="sw:pkg:test_u",
        name="test_pkg",
        domain="distributed_systems",
        provided_signatures=("SIG_API",),
        cost=5.0,
        evidence=ev_unit_fail,
    )
    cert_u = boundary.certify_software(mach_unit, requirements=[req])
    assert cert_u.verdict == SoftwareCertificationVerdict.FALSIFIED
    assert "GATE_U" not in cert_u.gates_passed

    # 7b. Latency SLA breach rejected at Gate L
    ev_sla_fail = SoftwareEvidence(
        type_safety_pass=True,
        unit_tests_pass=True,
        static_analysis_pass=True,
        measured_latency_ms=150.0,
        fault_tolerance_pass=True,
    )
    mach_sla = SoftwareMachinery(
        machinery_id="sw:pkg:test_l",
        name="test_pkg",
        domain="distributed_systems",
        provided_signatures=("SIG_API",),
        cost=5.0,
        evidence=ev_sla_fail,
    )
    cert_l = boundary.certify_software(mach_sla, requirements=[req])
    assert cert_l.verdict == SoftwareCertificationVerdict.FALSIFIED
    assert "GATE_L" not in cert_l.gates_passed

    # 7c. Race condition rejected at Gate F
    ev_race = SoftwareEvidence(
        type_safety_pass=True,
        unit_tests_pass=True,
        static_analysis_pass=True,
        measured_latency_ms=10.0,
        fault_tolerance_pass=False,
    )
    mach_race = SoftwareMachinery(
        machinery_id="sw:pkg:test_f",
        name="test_pkg",
        domain="distributed_systems",
        provided_signatures=("SIG_API",),
        cost=5.0,
        evidence=ev_race,
    )
    cert_f = boundary.certify_software(mach_race, requirements=[req])
    assert cert_f.verdict == SoftwareCertificationVerdict.FALSIFIED
    assert "GATE_F" not in cert_f.gates_passed
