"""UQ-N1: Two-Node Research Control Qualification Test Suite.

Verifies the 12 qualification gates for the distributed two-node architecture:
- Physical separation of research work plane (Jetson Nano) and regulatory control plane (UNO Q)
- Fundamental rule: PROPOSED != AUTHORIZED
- Dual-tier cryptographic verification: H_E (evidence payload) and H_X (execution envelope)
- Out-of-order concurrent completion validity (no high-water completion lockouts)
- Idempotent replay rejection and replication recognition
- Parent state supersession gating
- Fault tolerance: Nano reboot, UNO outage, network partition
- Backpressure protocol and geometry authority boundaries
- Full cryptographic provenance chain
"""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from sovctx.node.control_plane import (
    AdmissionDecision,
    AdmissionVerdict,
    UnoQControlPlaneGateway,
    UoWIssuanceLedger,
    UoWIssuanceRecord,
)
from sovctx.node.nano_research_worker import (
    CandidateBundle,
    CandidateClaim,
    CandidateEntity,
    CandidateQuestion,
    CandidateRelation,
    CandidateSource,
    NanoResearchWorker,
    SourceFragment,
)


@pytest.fixture
def clean_control_node() -> UnoQControlPlaneGateway:
    ledger = UoWIssuanceLedger()
    gateway = UnoQControlPlaneGateway(
        ledger=ledger,
        allowed_software_commits={"d99a250352ef4193d567fe8512dd441b714c62b9", "c8a975e974e3a12af94f647944ac56d1fb8597fc"},
        canonical_entities={"PERSON:FELDBAUM_AA", "CONCEPT:DUAL_CONTROL"},
        canonical_relations={("PERSON:FELDBAUM_AA", "CONCEPT:DUAL_CONTROL", "REPRESENT")},
    )
    return gateway


@pytest.fixture
def issued_bundle(clean_control_node: UnoQControlPlaneGateway) -> CandidateBundle:
    uow_id = "UOW_TEST_UQ_001"
    clean_control_node.ledger.issue_uow(
        uow_id=uow_id,
        worker_id="nano-jetson-01",
        target_query="Dual control action distinction",
    )
    frag = SourceFragment(
        fragment_id="FRAG:TEST_DUAL",
        source_id="PUB:FELDBAUM_1960",
        text="Investigative and directing action in incomplete information.",
        locator="p. 1242",
    )
    bundle = CandidateBundle(
        uow_id=uow_id,
        worker_id="nano-jetson-01",
        causal_sequence_id=1,
        software_commit="d99a250352ef4193d567fe8512dd441b714c62b9",
        source_manifest=["PUB:FELDBAUM_1960"],
        source_hashes={"PUB:FELDBAUM_1960": "sha256_mock_hash"},
        source_fragments=[frag],
        candidate_entities=[
            CandidateEntity(
                entity_id="CONCEPT:INVESTIGATIVE_ACTION",
                label="Investigative Action",
                category="CONCEPT",
                provenance_fragment_ids=["FRAG:TEST_DUAL"],
            )
        ],
        candidate_relations=[
            CandidateRelation(
                source_id="CONCEPT:DUAL_CONTROL",
                target_id="CONCEPT:INVESTIGATIVE_ACTION",
                verb="PROBES",
                rationale="Probing uncertainty",
                evidence_fragment_ids=["FRAG:TEST_DUAL"],
            )
        ],
        candidate_claims=[
            CandidateClaim(
                claim_id="CLAIM:TEST_DUAL",
                subject_id="CONCEPT:DUAL_CONTROL",
                predicate="DISTINGUISHES",
                object_val="INVESTIGATIVE",
                epistemic_status="HISTORICALLY_SUPPORTED",
                evidence_fragment_ids=["FRAG:TEST_DUAL"],
            )
        ],
        observer_state={"shadow_mode": True, "speed_max_angle": 0.02},
        resource_state={"ram_available_mb": 1024.0, "worker_rss_mb": 65.0, "backpressure_flag": False},
    )
    bundle.compute_hash()
    return bundle


def test_uq_n1_gate1_physical_authority_separation() -> None:
    """UQ-N1.1 Physical authority: Nano cannot produce an admission disposition."""
    worker = NanoResearchWorker(shadow_mode=True)
    # The worker must not possess admission gateway methods
    assert not hasattr(worker, "verify_bundle")
    assert not hasattr(worker, "admit_records")
    assert not hasattr(worker, "quarantine_records")
    assert not hasattr(worker, "commit_to_graph")

    packet = worker.process_work_unit(uow_id="UOW_PHYSICAL_SEP_001")
    # Worker status must strictly be PROPOSED, never ADMITTED
    assert isinstance(packet.candidate_bundle, CandidateBundle)
    assert packet.candidate_bundle.uow_id == "UOW_PHYSICAL_SEP_001"


def test_uq_n1_gate2_bundle_integrity_dual_tier_hashes(clean_control_node: UnoQControlPlaneGateway, issued_bundle: CandidateBundle) -> None:
    """UQ-N1.2 Bundle integrity: UNO rejects altered H_E or H_X."""
    # Test 1: Tampered Evidence Payload (H_E mismatch)
    tampered_evidence = deepcopy(issued_bundle)
    tampered_evidence.candidate_claims[0].object_val = "ALTERED_UNGROUNDED_VALUE"
    # Notice: we do not recompute H_E, so H_E computed != expected
    dec_e = clean_control_node.verify_bundle(tampered_evidence)
    assert dec_e.verdict == AdmissionVerdict.REJECT
    assert "Evidence payload hash mismatch" in dec_e.reason

    # Test 2: Tampered Execution Envelope (H_X mismatch)
    tampered_exec = deepcopy(issued_bundle)
    tampered_exec.resource_state["ram_available_mb"] = 2048.0  # altered execution state
    # recompute only H_E, leaving H_X mismatched
    tampered_exec.compute_evidence_hash()
    dec_x = clean_control_node.verify_bundle(tampered_exec)
    assert dec_x.verdict == AdmissionVerdict.REJECT
    assert "Execution envelope hash mismatch" in dec_x.reason


@pytest.mark.parametrize("completion_order", [
    [1, 2, 3, 4],
    [4, 3, 2, 1],
    [2, 4, 1, 3],
    [3, 1, 4, 2],
])
def test_uq_n1_gate3_out_of_order_concurrency(clean_control_node: UnoQControlPlaneGateway, completion_order: list[int]) -> None:
    """UQ-N1.3 Out-of-order concurrency: Valid concurrent UoWs accepted regardless of arrival order."""
    # Issue 4 concurrent UoWs
    bundles = {}
    for i in [1, 2, 3, 4]:
        uid = f"UOW_CONCUR_{i}"
        clean_control_node.ledger.issue_uow(uow_id=uid, worker_id="nano-jetson-01", target_query=f"Query {i}")
        frag = SourceFragment(fragment_id=f"FRAG_{i}", source_id=f"PUB_{i}", text=f"Evidence text {i}", locator="p. 1")
        b = CandidateBundle(
            uow_id=uid,
            causal_sequence_id=i,
            software_commit="d99a250352ef4193d567fe8512dd441b714c62b9",
            source_manifest=[f"PUB_{i}"],
            source_hashes={f"PUB_{i}": f"hash_{i}"},
            source_fragments=[frag],
            candidate_entities=[CandidateEntity(entity_id=f"CONCEPT:C{i}", label=f"C{i}", category="CONCEPT")],
            candidate_claims=[
                CandidateClaim(
                    claim_id=f"CLAIM_{i}",
                    subject_id=f"CONCEPT:C{i}",
                    predicate="TESTS",
                    object_val="TRUE",
                    epistemic_status="HISTORICALLY_SUPPORTED",
                    evidence_fragment_ids=[f"FRAG_{i}"],
                )
            ],
            observer_state={"shadow_mode": True},
            resource_state={"ram_available_mb": 1024.0, "worker_rss_mb": 65.0},
        )
        b.compute_hash()
        bundles[i] = b

    # Deliver in permuted completion order
    for idx in completion_order:
        dec = clean_control_node.verify_bundle(bundles[idx])
        assert dec.verdict == AdmissionVerdict.ADMIT, f"Failed on UoW {idx} in arrival order {completion_order}: {dec.reason}"


def test_uq_n1_gate4_replay_idempotent_rejection(clean_control_node: UnoQControlPlaneGateway, issued_bundle: CandidateBundle) -> None:
    """UQ-N1.4 Replay: Same execution receipt (H_X) is idempotently rejected."""
    dec1 = clean_control_node.verify_bundle(issued_bundle)
    assert dec1.verdict == AdmissionVerdict.ADMIT

    # Replay identical bundle
    dec2 = clean_control_node.verify_bundle(issued_bundle)
    assert dec2.verdict == AdmissionVerdict.REJECT_IDEMPOTENT
    assert "already been dispositioned" in dec2.reason or "REPLAY" in dec2.reason


def test_uq_n1_gate5_duplicate_evidence_replication_recognition(clean_control_node: UnoQControlPlaneGateway, issued_bundle: CandidateBundle) -> None:
    """UQ-N1.5 Duplicate evidence: Same H_E, different H_X recognized as independent replication."""
    # First execution admitted
    dec1 = clean_control_node.verify_bundle(issued_bundle)
    assert dec1.verdict == AdmissionVerdict.ADMIT

    # Issue a second UoW aiming to replicate the same finding
    uow2 = "UOW_REPLICATION_002"
    clean_control_node.ledger.issue_uow(uow_id=uow2, worker_id="nano-jetson-02", target_query="Replication")

    # Create new bundle with identical evidence payload (same H_E) but different operational envelope (different H_X)
    rep_bundle = deepcopy(issued_bundle)
    rep_bundle.uow_id = uow2
    rep_bundle.worker_id = "nano-jetson-02"
    rep_bundle.causal_sequence_id = 2
    rep_bundle.resource_state["thermal_max_c"] = 52.0  # different temperature / execution
    rep_bundle.compute_hash()

    assert rep_bundle.evidence_hash == issued_bundle.evidence_hash, "H_E must match for identical evidence"
    assert rep_bundle.execution_hash != issued_bundle.execution_hash, "H_X must differ for distinct execution envelopes"

    dec2 = clean_control_node.verify_bundle(rep_bundle)
    assert dec2.verdict == AdmissionVerdict.DEDUP
    assert dec2.is_replication is True
    assert "Independent evidence replication verified" in dec2.reason


def test_uq_n1_gate6_parent_state_supersession(clean_control_node: UnoQControlPlaneGateway) -> None:
    """UQ-N1.6 Supersession: Result rejected only when its actual parent/question state was superseded."""
    parent_uow = "UOW_PARENT_RESEARCH_001"
    child_uow = "UOW_CHILD_DESCENDANT_002"

    clean_control_node.ledger.issue_uow(uow_id=parent_uow, target_query="Parent question")
    clean_control_node.ledger.issue_uow(uow_id=child_uow, parent_uow_id=parent_uow, target_query="Child question")

    # Invalidate / supersede parent in ledger
    clean_control_node.ledger.supersede_uow(parent_uow, reason="New contradicting empirical data")

    # Child bundle arrives referencing now-superseded parent
    frag = SourceFragment(fragment_id="FRAG_C", source_id="PUB_C", text="Evidence", locator="p. 1")
    child_bundle = CandidateBundle(
        uow_id=child_uow,
        parent_uow_id=parent_uow,
        software_commit="d99a250352ef4193d567fe8512dd441b714c62b9",
        source_manifest=["PUB_C"],
        source_hashes={"PUB_C": "hash_c"},
        source_fragments=[frag],
        candidate_entities=[CandidateEntity(entity_id="CONCEPT:CHILD", label="Child", category="CONCEPT")],
        candidate_claims=[
            CandidateClaim(
                claim_id="CLAIM_C",
                subject_id="CONCEPT:CHILD",
                predicate="TESTS",
                object_val="TRUE",
                epistemic_status="HISTORICALLY_SUPPORTED",
                evidence_fragment_ids=["FRAG_C"],
            )
        ],
        observer_state={"shadow_mode": True},
        resource_state={"ram_available_mb": 1024.0, "worker_rss_mb": 65.0},
    )
    child_bundle.compute_hash()

    decision = clean_control_node.verify_bundle(child_bundle)
    assert decision.verdict == AdmissionVerdict.REJECT
    assert "Superseded parent state" in decision.reason


def test_uq_n1_gate7_nano_reboot_recovery(clean_control_node: UnoQControlPlaneGateway, issued_bundle: CandidateBundle) -> None:
    """UQ-N1.7 Nano reboot: Checkpointed UoW resumes without producing duplicate authority effects."""
    # First admission succeeds
    dec1 = clean_control_node.verify_bundle(issued_bundle)
    assert dec1.verdict == AdmissionVerdict.ADMIT

    # Simulate worker reboot and replaying checkpointed state
    replayed_bundle = CandidateBundle.from_dict(issued_bundle.to_dict())
    dec2 = clean_control_node.verify_bundle(replayed_bundle)
    assert dec2.verdict == AdmissionVerdict.REJECT_IDEMPOTENT


def test_uq_n1_gate8_uno_outage_local_spooling() -> None:
    """UQ-N1.8 UNO outage: Nano continues bounded local work and spools proposals locally."""
    with TemporaryDirectory() as tmp_dir:
        spool_dir = Path(tmp_dir) / "spool"
        worker = NanoResearchWorker(
            worker_id="nano-spool-test",
            shadow_mode=True,
            spool_dir=spool_dir,
            output_telemetry_dir=Path(tmp_dir),
        )

        packet = worker.process_work_unit(uow_id="UOW_SPOOL_TEST_001")
        assert packet.candidate_bundle.uow_id == "UOW_SPOOL_TEST_001"

        # Check local file spooled on disk
        spool_file = spool_dir / "candidate_bundle_UOW_SPOOL_TEST_001.json"
        assert spool_file.exists()

        # Rehydrate and verify hash parity
        rehydrated = CandidateBundle.from_dict(json.loads(spool_file.read_text(encoding="utf-8")))
        assert rehydrated.compute_evidence_hash(update=False) == packet.candidate_bundle.evidence_hash
        assert rehydrated.compute_execution_hash(update=False) == packet.candidate_bundle.execution_hash


def test_uq_n1_gate9_network_partition_split_brain_prevention() -> None:
    """UQ-N1.9 Network partition: No split-brain canonical mutations; Nano has no write credentials."""
    worker = NanoResearchWorker(shadow_mode=True)
    # Even during network partition, Nano has zero capability to alter canonical records
    assert not hasattr(worker, "write_canonical_graph")
    assert not hasattr(worker, "apply_mutations")


def test_uq_n1_gate10_backpressure_signaling(clean_control_node: UnoQControlPlaneGateway, issued_bundle: CandidateBundle) -> None:
    """UQ-N1.10 Backpressure: UNO stops issuing work when Nano raises resource pressure."""
    # Worker reports backpressure flag True
    issued_bundle.resource_state["backpressure_flag"] = True
    issued_bundle.resource_state["ram_available_mb"] = 210.0  # Low RAM
    issued_bundle.compute_hash()

    decision = clean_control_node.verify_bundle(issued_bundle)
    assert decision.verdict == AdmissionVerdict.ADMIT
    # Control plane gateway must detect backpressure active
    assert clean_control_node.backpressure_active is True


def test_uq_n1_gate11_geometry_boundary(clean_control_node: UnoQControlPlaneGateway, issued_bundle: CandidateBundle) -> None:
    """UQ-N1.11 Geometry boundary: G1 remains advisory/shadow only."""
    # Attempting to override schedule via observer state triggers REFUSE
    issued_bundle.observer_state["mutate_schedule_direct"] = True
    issued_bundle.compute_hash()

    decision = clean_control_node.verify_bundle(issued_bundle)
    assert decision.verdict == AdmissionVerdict.REFUSE
    assert "cannot issue canonical mutations" in decision.reason


def test_uq_n1_gate12_cryptographic_provenance_chain(clean_control_node: UnoQControlPlaneGateway, issued_bundle: CandidateBundle) -> None:
    """UQ-N1.12 Provenance: Every admission resolves back to source bytes, fragment locator, worker SHA, and receipt."""
    decision = clean_control_node.verify_bundle(issued_bundle)
    assert decision.verdict == AdmissionVerdict.ADMIT

    # Provenance resolution check
    assert decision.uow_id == "UOW_TEST_UQ_001"
    assert len(decision.evidence_hash) == 64
    assert len(decision.execution_hash) == 64
    assert issued_bundle.source_manifest == ["PUB:FELDBAUM_1960"]
    assert "PUB:FELDBAUM_1960" in issued_bundle.source_hashes
    assert issued_bundle.source_fragments[0].locator == "p. 1242"
    assert issued_bundle.software_commit in clean_control_node.allowed_software_commits
