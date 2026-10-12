"""Adversarial authority boundary qualification suite.

Enforces the absolute system law: PROPOSED != AUTHORIZED.
Tests that the Jetson Nano research work plane cannot violate authority boundaries,
and that the control plane verifier (UNO Q gateway) strictly intercepts, quarantines,
downgrades, or refuses invalid, tampered, replay, or ungrounded candidate bundles:

1. Canonical direct write -> REFUSE / REJECT
2. Dangling reference -> QUARANTINE
3. Hash mismatch / tampering -> REJECT
4. Bundle replay -> REJECT_IDEMPOTENT
5. Superseded UoW arrival -> REJECT
6. Epistemic overpromotion -> DOWNGRADE / QUARANTINE
7. Geometry authority attempt -> REFUSE
8. Duplicate candidate submission -> DEDUP
"""

from copy import deepcopy
from pathlib import Path
import pytest

from sovctx.node.nano_research_worker import (
    AdmissionDecision,
    AdmissionVerdict,
    CandidateBundle,
    CandidateBundleVerifier,
    CandidateClaim,
    CandidateEntity,
    CandidateQuestion,
    CandidateRelation,
    CandidateSource,
    NanoResearchWorker,
    SourceFragment,
)


@pytest.fixture
def clean_verifier() -> CandidateBundleVerifier:
    return CandidateBundleVerifier(
        allowed_software_commits={"c8a975e974e3a12af94f647944ac56d1fb8597fc"},
        canonical_entities={"PERSON:FELDBAUM_AA", "CONCEPT:DUAL_CONTROL", "EQ:LYAPUNOV_1892"},
        canonical_relations={("PERSON:FELDBAUM_AA", "CONCEPT:DUAL_CONTROL", "REPRESENT")},
        canonical_claims={("CONCEPT:DUAL_CONTROL", "INVENTED_IN", "1960")},
    )


@pytest.fixture
def valid_bundle() -> CandidateBundle:
    frag = SourceFragment(
        fragment_id="FRAG:TEST_001",
        source_id="PUB:TEST_1960",
        text="Control action serves simultaneously to investigate and to direct.",
        locator="Section 2, p. 1242",
    )
    entity = CandidateEntity(
        entity_id="CONCEPT:INVESTIGATIVE_ACTION",
        label="Investigative Action",
        category="CONCEPT",
        provenance_fragment_ids=["FRAG:TEST_001"],
    )
    rel = CandidateRelation(
        source_id="CONCEPT:DUAL_CONTROL",
        target_id="CONCEPT:INVESTIGATIVE_ACTION",
        verb="PROBES",
        rationale="Investigative step reduces parameter uncertainty.",
        evidence_fragment_ids=["FRAG:TEST_001"],
    )
    claim = CandidateClaim(
        claim_id="CLAIM:TEST_001",
        subject_id="CONCEPT:DUAL_CONTROL",
        predicate="DISTINGUISHES_ACTION_TYPES",
        object_val="INVESTIGATIVE_VS_DIRECTING",
        epistemic_status="HISTORICALLY_SUPPORTED",
        evidence_fragment_ids=["FRAG:TEST_001"],
    )
    bundle = CandidateBundle(
        uow_id="UOW_QUAL_001",
        parent_uow_id=None,
        worker_id="nano-jetson-01",
        causal_sequence_id=1,
        software_commit="c8a975e974e3a12af94f647944ac56d1fb8597fc",
        source_manifest=["PUB:TEST_1960"],
        source_hashes={"PUB:TEST_1960": "abc123sha256"},
        source_fragments=[frag],
        candidate_entities=[entity],
        candidate_relations=[rel],
        candidate_claims=[claim],
        observer_state={"shadow_mode": True, "speed_max_angle": 0.05},
        resource_state={"ram_available_mb": 1024.0, "worker_rss_mb": 65.0},
    )
    bundle.compute_hash()
    return bundle


def test_gate1_direct_canonical_write_refusal() -> None:
    """Gate 1: Verifies that Nano research worker contains NO canonical write capabilities."""
    worker = NanoResearchWorker(shadow_mode=True)
    
    # NanoResearchWorker must not expose direct graph write or commit methods
    assert not hasattr(worker, "write_canonical_graph")
    assert not hasattr(worker, "commit_to_graph")
    assert not hasattr(worker, "admit_records")
    
    # Invariant: Output is purely a CandidateBundle, never a modified database
    packet = worker.process_work_unit(uow_id="UOW_PROPOSAL_ONLY", parent_uow_id=None)
    assert isinstance(packet.candidate_bundle, CandidateBundle)
    assert packet.candidate_bundle.uow_id == "UOW_PROPOSAL_ONLY"


def test_gate2_dangling_canonical_reference_quarantined(clean_verifier: CandidateBundleVerifier, valid_bundle: CandidateBundle) -> None:
    """Gate 2: Dangling reference to nonexistent entity triggers QUARANTINE."""
    # Introduce a dangling reference to a nonexistent entity
    bad_rel = CandidateRelation(
        source_id="CONCEPT:NONEXISTENT_GHOST_NODE_123",
        target_id="CONCEPT:DUAL_CONTROL",
        verb="PROBES",
        rationale="Ghost reference",
        evidence_fragment_ids=[],
    )
    valid_bundle.candidate_relations.append(bad_rel)
    valid_bundle.compute_hash()

    decision = clean_verifier.verify_bundle(valid_bundle)
    assert decision.verdict == AdmissionVerdict.QUARANTINE
    assert "DANGLING_REFERENCE" in decision.reason
    assert len(decision.quarantined_items) == 1
    assert "CONCEPT:NONEXISTENT_GHOST_NODE_123" in decision.quarantined_items[0]["reason"]


def test_gate3_hash_mismatch_and_payload_tampering_rejected(clean_verifier: CandidateBundleVerifier, valid_bundle: CandidateBundle) -> None:
    """Gate 3: Tampering with payload after computing candidate_bundle_hash triggers REJECT."""
    original_hash = valid_bundle.candidate_bundle_hash
    
    # Tamper with claim content without recomputing hash
    valid_bundle.candidate_claims[0].object_val = "TAMPERED_INJECTED_VALUE"
    
    decision = clean_verifier.verify_bundle(valid_bundle)
    assert decision.verdict == AdmissionVerdict.REJECT
    assert "Hash mismatch / payload tampering detected" in decision.reason


def test_gate4_bundle_replay_idempotent_rejected(clean_verifier: CandidateBundleVerifier, valid_bundle: CandidateBundle) -> None:
    """Gate 4: Replaying an already-admitted bundle triggers REJECT_IDEMPOTENT."""
    # First admission succeeds
    dec1 = clean_verifier.verify_bundle(valid_bundle)
    assert dec1.verdict == AdmissionVerdict.ADMIT
    
    # Second admission of identical bundle or UoW is detected as replay
    dec2 = clean_verifier.verify_bundle(valid_bundle)
    assert dec2.verdict == AdmissionVerdict.REJECT_IDEMPOTENT
    assert "BUNDLE_REPLAY" in dec2.reason or "already been admitted" in dec2.reason


def test_gate5_superseded_uow_arrival_rejected(clean_verifier: CandidateBundleVerifier, valid_bundle: CandidateBundle) -> None:
    """Gate 5: Stale / superseded UoW with sequence <= high-water mark triggers REJECT."""
    # First advance high water mark to sequence 5
    clean_verifier.highest_causal_sequence = 5
    
    # valid_bundle has causal_sequence_id = 1
    decision = clean_verifier.verify_bundle(valid_bundle)
    assert decision.verdict == AdmissionVerdict.REJECT
    assert "Superseded UoW arrival" in decision.reason


def test_gate6_epistemic_overpromotion_downgraded(clean_verifier: CandidateBundleVerifier, valid_bundle: CandidateBundle) -> None:
    """Gate 6: Claim asserted as HISTORICALLY_SUPPORTED without evidence fragments is DOWNGRADED."""
    # Create an ungrounded strong claim with no evidence fragments
    ungrounded_claim = CandidateClaim(
        claim_id="CLAIM:UNGROUNDED_001",
        subject_id="CONCEPT:DUAL_CONTROL",
        predicate="INVENTED_BY_ALIENS",
        object_val="TRUE",
        epistemic_status="HISTORICALLY_SUPPORTED",  # Overpromoted!
        evidence_fragment_ids=[],  # No evidence!
    )
    valid_bundle.candidate_claims.append(ungrounded_claim)
    valid_bundle.compute_hash()

    decision = clean_verifier.verify_bundle(valid_bundle)
    assert decision.verdict == AdmissionVerdict.DOWNGRADE
    assert len(decision.downgraded_items) == 1
    assert decision.downgraded_items[0]["original_status"] == "HISTORICALLY_SUPPORTED"
    assert decision.downgraded_items[0]["new_status"] == "HYPOTHETICAL"
    assert ungrounded_claim.epistemic_status == "HYPOTHETICAL"


def test_gate7_geometry_live_mutation_refusal(clean_verifier: CandidateBundleVerifier, valid_bundle: CandidateBundle) -> None:
    """Gate 7: Worker or geometry observer attempting to commandeer scheduler or disable shadow mode triggers REFUSE."""
    # Attempt 1: Disabling shadow mode
    bundle_no_shadow = deepcopy(valid_bundle)
    bundle_no_shadow.uow_id = "UOW_SHADOW_VIOLATION"
    bundle_no_shadow.observer_state["shadow_mode"] = False
    bundle_no_shadow.compute_hash()

    dec1 = clean_verifier.verify_bundle(bundle_no_shadow)
    assert dec1.verdict == AdmissionVerdict.REFUSE
    assert "SHADOW_MODE=True" in dec1.reason

    # Attempt 2: Proposing direct scheduler mutation
    bundle_override = deepcopy(valid_bundle)
    bundle_override.uow_id = "UOW_SCHEDULER_OVERRIDE"
    bundle_override.observer_state["mutate_schedule_direct"] = True
    bundle_override.compute_hash()

    dec2 = clean_verifier.verify_bundle(bundle_override)
    assert dec2.verdict == AdmissionVerdict.REFUSE
    assert "cannot issue canonical mutations" in dec2.reason


def test_gate8_duplicate_candidate_deduplicated(clean_verifier: CandidateBundleVerifier, valid_bundle: CandidateBundle) -> None:
    """Gate 8: Submitting relations/claims that already exist in canonical store triggers DEDUP."""
    # Provide a bundle that only contains the already-canonical relation and claim
    dup_bundle = CandidateBundle(
        uow_id="UOW_DUP_001",
        worker_id="nano-jetson-01",
        causal_sequence_id=2,
        software_commit="c8a975e974e3a12af94f647944ac56d1fb8597fc",
        candidate_entities=[],
        candidate_relations=[
            CandidateRelation(
                source_id="PERSON:FELDBAUM_AA",
                target_id="CONCEPT:DUAL_CONTROL",
                verb="REPRESENT",
                rationale="Existing canonical edge",
                evidence_fragment_ids=[],
            )
        ],
        candidate_claims=[
            CandidateClaim(
                claim_id="CLAIM:CANONICAL_DUP",
                subject_id="CONCEPT:DUAL_CONTROL",
                predicate="INVENTED_IN",
                object_val="1960",
                epistemic_status="HYPOTHETICAL",
                evidence_fragment_ids=[],
            )
        ],
        observer_state={"shadow_mode": True},
        resource_state={"ram_available_mb": 1024.0, "worker_rss_mb": 65.0},
    )
    dup_bundle.compute_hash()

    decision = clean_verifier.verify_bundle(dup_bundle)
    assert decision.verdict == AdmissionVerdict.DEDUP
    assert len(decision.deduplicated_items) == 2
    assert any(d["key"] == ("PERSON:FELDBAUM_AA", "CONCEPT:DUAL_CONTROL", "REPRESENT") for d in decision.deduplicated_items)
