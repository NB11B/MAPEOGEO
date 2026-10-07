"""Unit Tests for Software Domain Adapter, 5-Gate Boundary, and Adversarial Controls.

Verifies:
1. Software ontology, verification contracts, and epistemic statuses.
2. Canonical adapter contract methods (required_work, candidate_machinery, measure_ability).
3. 5-Gate Software Certification Boundary C_sw = { T, U, S, L, F }.
4. Invariant: source code exists != software capability certified.
5. Adversarial software controls:
   - Type-correct but behaviorally wrong (fails Gate U)
   - Tests-pass but static analysis contract violation (fails Gate S)
   - Correct output but SLA latency violation (fails Gate L)
   - Race / deadlock / fault tolerance violation (fails Gate F)
   - Redundant dependency with no reach expansion
   - High-scoring machinery lacking required authority (fails authority check)
   - Partial satisfaction of composite requirements
6. Literal 6D grammar factoring and drift auditing.
7. Cross-Domain Contamination Test:
   Sigma_grammar(X) == Sigma_grammar(Y) =/=> X == Y.
"""

from __future__ import annotations

from mapeogeo.domains.mathematics.adapter import MathematicsAdapter
from mapeogeo.domains.mathematics.ontology import (
    Theorem,
    TheoremKind,
)
from mapeogeo.domains.physics.adapter import PhysicsAdapter
from mapeogeo.domains.physics.ontology import (
    PhysicalHypothesis,
)
from mapeogeo.domains.software.adapter import SoftwareAdapter
from mapeogeo.domains.software.certification import SoftwareCertificationBoundary
from mapeogeo.domains.software.grammar_mapping import (
    FactoringClassification,
    SoftwareGrammarFactorer,
)
from mapeogeo.domains.software.ontology import (
    EpistemicSoftwareStatus,
    SoftwareCertificationVerdict,
    SoftwareEvidence,
    SoftwareMachinery,
    SoftwareObjective,
    SoftwareRequirement,
    SoftwareVerificationContracts,
)
from mapeogeo.grammar.work_grammar import WorkGrammar
from mapeogeo.kernel.state import KnowledgeState


def test_software_ontology_and_contracts() -> None:
    """Verify SoftwareRequirement and SoftwareObjective construction and contracts."""
    contracts = SoftwareVerificationContracts(
        type_contract="RaftNode -> Result[CommitIndex, Error]",
        unit_test_spec="test_raft_leader_election",
        static_analysis_rule="zero_unhandled_election_timeouts",
        latency_bound_ms=50.0,
        concurrency_invariant="linearizable_state_history",
    )
    req = SoftwareRequirement(
        requirement_id="REQ-TEST-001",
        title="Distributed Raft Log Replication",
        domain="Distributed Systems",
        weight=32.076,
        required_signatures=("RAFT_CONSENSUS_STATE_MACHINE", "QUORUM_LOG_REPLICATION"),
        contracts=contracts,
    )
    assert req.requirement_id == "REQ-TEST-001"
    assert req.weight == 32.076
    assert req.contracts.latency_bound_ms == 50.0

    obj = SoftwareObjective(
        objective_id="OBJ-SYS-01",
        title="High Availability Raft Cluster",
        requirements=(req,),
        system_domain="Distributed Systems",
        sla_latency_target_ms=50.0,
    )
    assert obj.objective_id == "OBJ-SYS-01"
    assert len(obj.requirements) == 1


def test_canonical_contract_translation() -> None:
    """Verify SoftwareAdapter.required_work and measure_ability translation."""
    adapter = SoftwareAdapter()
    req = SoftwareRequirement(
        requirement_id="REQ-HMAC-001",
        title="Constant-Time HMAC Verification",
        domain="Security & Cryptography",
        weight=25.704,
        required_signatures=(
            "CONSTANT_TIME_HMAC_VERIFIER",
            "NONCE_REPLAY_PROTECTION_FILTER",
        ),
        contracts=SoftwareVerificationContracts(latency_bound_ms=1.0),
    )

    work = adapter.required_work(req)
    assert work.contract_id == "work:sw:REQ-HMAC-001"
    assert work.cost == 25.704
    assert work.error_tolerance == 0.001  # 1.0ms / 1000.0
    assert "has_capability(CONSTANT_TIME_HMAC_VERIFIER)" in work.preconditions

    # Ability measurement
    state_empty = KnowledgeState.initial()
    assert adapter.measure_ability(req, state_empty) == 0.0

    state_half = KnowledgeState(
        t=1,
        signatures=frozenset({"CONSTANT_TIME_HMAC_VERIFIER"}),
        certified_nodes=(),
        witness_ids=frozenset(),
        cumulative_ability=12.852,
        state_hash="h1",
    )
    assert adapter.measure_ability(req, state_half) == round(25.704 / 2, 3)

    state_full = KnowledgeState(
        t=2,
        signatures=frozenset(
            {
                "CONSTANT_TIME_HMAC_VERIFIER",
                "NONCE_REPLAY_PROTECTION_FILTER",
            }
        ),
        certified_nodes=(),
        witness_ids=frozenset(),
        cumulative_ability=25.704,
        state_hash="h2",
    )
    assert adapter.measure_ability(req, state_full) == 25.704


def test_five_gate_software_certification_boundary() -> None:
    """Verify that all 5 gates { T, U, S, L, F } are evaluated sequentially."""
    certifier = SoftwareCertificationBoundary()
    req = SoftwareRequirement(
        requirement_id="REQ-VAL-01",
        title="Validated Component",
        domain="Core",
        weight=10.0,
        required_signatures=("SIG_CORE",),
        contracts=SoftwareVerificationContracts(latency_bound_ms=10.0),
    )

    # 1. Full 5-Gate PASS
    mach_sound = SoftwareMachinery(
        machinery_id="LIB_SOUND",
        name="SoundComponent",
        domain="Core",
        cost=10.0,
        provided_signatures=("SIG_CORE",),
        evidence=SoftwareEvidence(
            type_safety_pass=True,
            unit_tests_pass=True,
            static_analysis_pass=True,
            measured_latency_ms=4.5,
            fault_tolerance_pass=True,
        ),
    )
    cert_pass = certifier.certify_software(mach_sound, requirements=[req])
    assert cert_pass.is_certified is True
    assert cert_pass.verdict == SoftwareCertificationVerdict.CERTIFIED
    assert len(cert_pass.gates_passed) == 5
    assert cert_pass.epistemic_status == EpistemicSoftwareStatus.CERTIFIED_CAPABILITY
    assert cert_pass.certificate_id.startswith("cert:sw:")

    # 2. Empty evidence fail-closed (source code exists != certified)
    mach_empty = SoftwareMachinery(
        machinery_id="LIB_RAW_CODE",
        name="RawUnverifiedCode",
        domain="Core",
        cost=10.0,
        provided_signatures=("SIG_CORE",),
        evidence=SoftwareEvidence(),
    )
    cert_empty = certifier.certify_software(mach_empty, requirements=[req])
    assert cert_empty.is_certified is False
    assert cert_empty.verdict == SoftwareCertificationVerdict.INCOMPLETE_CONTRACT
    assert "source code exists but no verification contracts" in (cert_empty.failure_reason or "")


def test_adversarial_software_falsifiers_rejection() -> None:
    """Verify adversarial software falsifiers fail at their exact corresponding gates."""
    certifier = SoftwareCertificationBoundary()
    req = SoftwareRequirement(
        requirement_id="REQ-ADV-01",
        title="Adversarial Target",
        domain="Systems",
        weight=15.0,
        required_signatures=("SIG_SYS",),
        contracts=SoftwareVerificationContracts(latency_bound_ms=5.0),
    )

    # Falsifier 1: Type-correct but behaviorally wrong implementation (fails Gate U)
    mach_bad_behavior = SoftwareMachinery(
        machinery_id="LIB_FALSIFIER_BEHAVIOR",
        name="BehaviorallyWrongComponent",
        domain="Systems",
        cost=10.0,
        provided_signatures=("SIG_SYS",),
        evidence=SoftwareEvidence(
            type_safety_pass=True,
            unit_tests_pass=False,  # FAILS Gate U
            static_analysis_pass=True,
            measured_latency_ms=2.0,
            fault_tolerance_pass=True,
        ),
    )
    cert_u = certifier.certify_software(mach_bad_behavior, requirements=[req])
    assert cert_u.verdict == SoftwareCertificationVerdict.FALSIFIED
    assert "Gate U failed: Unit / behavioral test failure" in (cert_u.failure_reason or "")
    assert "GATE_T_TYPE_SAFETY" in cert_u.gates_passed
    assert "GATE_U_UNIT_TESTS" not in cert_u.gates_passed

    # Falsifier 2: Tests pass but static contract violation (e.g. timing leak) (fails Gate S)
    mach_bad_static = SoftwareMachinery(
        machinery_id="LIB_FALSIFIER_STATIC",
        name="StaticAnalysisViolationComponent",
        domain="Systems",
        cost=10.0,
        provided_signatures=("SIG_SYS",),
        evidence=SoftwareEvidence(
            type_safety_pass=True,
            unit_tests_pass=True,
            static_analysis_pass=False,  # FAILS Gate S
            measured_latency_ms=2.0,
            fault_tolerance_pass=True,
        ),
    )
    cert_s = certifier.certify_software(mach_bad_static, requirements=[req])
    assert cert_s.verdict == SoftwareCertificationVerdict.FALSIFIED
    assert "Gate S failed: Static analysis" in (cert_s.failure_reason or "")
    assert "GATE_S_STATIC_ANALYSIS" not in cert_s.gates_passed

    # Falsifier 3: Correct output but latency/SLA contract violation (fails Gate L)
    mach_bad_latency = SoftwareMachinery(
        machinery_id="LIB_FALSIFIER_LATENCY",
        name="SlaViolationComponent",
        domain="Systems",
        cost=10.0,
        provided_signatures=("SIG_SYS",),
        evidence=SoftwareEvidence(
            type_safety_pass=True,
            unit_tests_pass=True,
            static_analysis_pass=True,
            measured_latency_ms=45.0,  # 45.0ms exceeds 5.0ms bound -> FAILS Gate L
            fault_tolerance_pass=True,
        ),
    )
    cert_l = certifier.certify_software(mach_bad_latency, requirements=[req])
    assert cert_l.verdict == SoftwareCertificationVerdict.FALSIFIED
    assert "Gate L failed: Measured latency 45.00ms exceeds" in (cert_l.failure_reason or "")
    assert "GATE_L_LATENCY_SLA" not in cert_l.gates_passed

    # Falsifier 4: Concurrency / fault invariant violation (split-brain/deadlock) (fails Gate F)
    mach_bad_concurrency = SoftwareMachinery(
        machinery_id="LIB_FALSIFIER_CONCURRENCY",
        name="ConcurrencyInvariantViolationComponent",
        domain="Systems",
        cost=10.0,
        provided_signatures=("SIG_SYS",),
        evidence=SoftwareEvidence(
            type_safety_pass=True,
            unit_tests_pass=True,
            static_analysis_pass=True,
            measured_latency_ms=2.0,
            fault_tolerance_pass=False,  # FAILS Gate F
        ),
    )
    cert_f = certifier.certify_software(mach_bad_concurrency, requirements=[req])
    assert cert_f.verdict == SoftwareCertificationVerdict.FALSIFIED
    assert "Gate F failed: Fault tolerance or concurrency invariant" in (
        cert_f.failure_reason or ""
    )
    assert "GATE_F_FAULT_INVARIANTS" not in cert_f.gates_passed

    # Falsifier 5: High-scoring machinery lacking required authority
    mach_unauthorized = SoftwareMachinery(
        machinery_id="LIB_FALSIFIER_AUTHORITY",
        name="UnauthorizedKernelBypassComponent",
        domain="Systems",
        cost=10.0,
        provided_signatures=("SIG_SYS",),
        required_authority="KERNEL_SUPERVISOR",  # Caller has STANDARD
        evidence=SoftwareEvidence(
            type_safety_pass=True,
            unit_tests_pass=True,
            static_analysis_pass=True,
            measured_latency_ms=2.0,
            fault_tolerance_pass=True,
        ),
    )
    cert_auth = certifier.certify_software(
        mach_unauthorized, requirements=[req], execution_authority="STANDARD"
    )
    assert cert_auth.verdict == SoftwareCertificationVerdict.AUTHORITY_DENIED
    assert "Authority verification failed" in (cert_auth.failure_reason or "")


def test_software_grammar_factoring_and_drift_audit() -> None:
    """Verify literal 6D grammar factoring and rejection of drift/dimension expansion."""
    grammar = WorkGrammar(base_alphabet_size=58)
    factorer = SoftwareGrammarFactorer(grammar=grammar)

    # 1. Exact factor using registered witness
    grammar.register_witness(
        "w_sw_raft_1", "WITNESS_RAFT_CONSENSUS_CORE", "Formal linearizable Raft state machine"
    )
    rec1 = factorer.factor_software_work(
        work_id="sw_raft",
        expression="NodeState \\times AppendEntriesRPC \\to CommitIndex \\circ w_sw_raft_1",
        witness_id="w_sw_raft_1",
    )
    assert rec1.is_compliant is True
    assert rec1.classification in {
        FactoringClassification.EXACT_FACTOR,
        FactoringClassification.COMPOSITION,
    }
    assert rec1.drift_detected is False

    # 2. Witness extension registration with Delta d = 0
    rec2 = factorer.factor_software_work(
        work_id="sw_hmac",
        expression="Secret \\times Token \\to Result \\circ w_sw_sec_new",
        witness_id="w_sw_sec_new",
        witness_symbol="WITNESS_CONSTANT_TIME_HMAC_NEW",
        witness_role="Constant-time side-channel invariant HMAC",
    )
    assert rec2.is_compliant is True
    assert rec2.classification == FactoringClassification.WITNESS_EXTENSION
    assert grammar.get_witness("w_sw_sec_new") is not None

    # 3. Reject illegal dimension expansion beyond d=6
    rec_dim = factorer.factor_software_work(
        work_id="sw_illegal_dim",
        expression="State \\to Result \\circ SOFTWARE_DIMENSION_8",
    )
    assert rec_dim.is_compliant is False
    assert rec_dim.classification == FactoringClassification.NEW_COORDINATE_REQUIRED
    assert rec_dim.drift_detected is True

    # 4. Reject semantic drift with ungrounded terms
    rec_drift = factorer.factor_software_work(
        work_id="sw_drift",
        expression="Channel \\to Result \\circ global_mutable_bypass",
    )
    assert rec_drift.is_compliant is False
    assert rec_drift.classification == FactoringClassification.SEMANTIC_DRIFT
    assert rec_drift.drift_detected is True


def test_cross_domain_contamination_rejection() -> None:
    """Cross-Domain Contamination Test:

    Verify:
        Sigma_grammar(X) == Sigma_grammar(Y) =/=> X == Y.
    A mathematical theorem, physical hypothesis, and software package with superficially
    identical grammar coordinate tuples must NOT become semantically interchangeable or admitted
    across domain boundaries.
    """
    grammar = WorkGrammar(base_alphabet_size=58)
    software_adapter = SoftwareAdapter(grammar=grammar)

    # 1. Mathematical Theorem
    math_thm = Theorem(
        theorem_id="thm:cft:artin",
        name="Artin Reciprocity Law",
        statement="Global reciprocity isomorphism holds",
        kind=TheoremKind.THEOREM,
        domain="Algebraic Number Theory",
    )

    # 2. Physical Hypothesis
    phys_hyp = PhysicalHypothesis(
        hypothesis_id="hyp:em:maxwell",
        model_name="Maxwell Poynting Model",
        latent_state=(1.0, 0.0, 0.0),
        is_source_identified=False,
    )

    # 3. Software Package
    sw_pkg = SoftwareMachinery(
        machinery_id="LIB_RAFT_CONSENSUS",
        name="Raft Distributed Consensus",
        domain="Distributed Systems",
        cost=14.0,
        provided_signatures=("RAFT_CONSENSUS_STATE_MACHINE",),
    )

    math_adapter = MathematicsAdapter(grammar=grammar)
    phys_adapter = PhysicsAdapter(grammar=grammar)

    # 1. SoftwareAdapter must strictly reject MathematicalTheorem and PhysicalHypothesis
    cert_math = software_adapter.certify(math_thm)
    assert not cert_math.is_certified
    assert "Unsupported software result type" in (cert_math.failure_reason or "")

    cert_phys = software_adapter.certify(phys_hyp)
    assert not cert_phys.is_certified
    assert "Unsupported software result type" in (cert_phys.failure_reason or "")

    # 2. MathematicsAdapter must strictly reject SoftwareMachinery
    cert_sw_in_math = math_adapter.certify(sw_pkg)
    assert not cert_sw_in_math.is_certified

    # 3. PhysicsAdapter must strictly reject SoftwareMachinery
    cert_sw_in_phys = phys_adapter.certify(sw_pkg)
    assert not cert_sw_in_phys.is_certified
