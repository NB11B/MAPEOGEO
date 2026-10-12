"""SOVCTX Two-Node Control Plane (Regulatory Node / UNO Q).

Owns authority, issuance, scheduling, admission, and canonical mutation:
- Fundamental Law: PROPOSED != AUTHORIZED (Nano proposes, UNO Q admits)
- Issuance Ledger: Tracks (worker_id, uow_id, issued_sequence, parent_uow_id, expected_state, disposition)
- Causal Validity: Validity is (UoW was issued AND not dispositioned AND parent state still valid),
  NOT completion-order dependent (supports concurrent execution C in {1, 2, 4})
- Dual-Tier Hash Verification:
  - H_E (Evidence Payload Hash): verified against scientific payload
  - H_X (Execution Envelope Hash): verified against operational envelope
  - Recognizes independent replication when H_E is identical under different H_X
- Epistemic Gating: Downgrades ungrounded claims to HYPOTHETICAL
- Referential Integrity: Quarantines dangling references
- Authority Enforcement: Refuses direct canonical write attempts or scheduler overrides
- Backpressure Feedback: Pauses task issuance when worker signals resource pressure
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple


class AdmissionVerdict(str, Enum):
    """Regulatory admission verdicts emitted by UNO Q control plane."""

    ADMIT = "ADMIT"
    QUARANTINE = "QUARANTINE"
    DOWNGRADE = "DOWNGRADE"
    REJECT = "REJECT"
    REJECT_IDEMPOTENT = "REJECT_IDEMPOTENT"
    DEDUP = "DEDUP"
    REFUSE = "REFUSE"
    UNRESOLVED = "UNRESOLVED"


@dataclass
class AdmissionDecision:
    """Regulatory admission decision produced by the control plane."""

    verdict: AdmissionVerdict
    reason: str
    uow_id: str = ""
    evidence_hash: str = ""
    execution_hash: str = ""
    is_replication: bool = False
    admitted_bundle: Optional[Any] = None
    quarantined_items: List[Dict[str, Any]] = field(default_factory=list)
    downgraded_items: List[Dict[str, Any]] = field(default_factory=list)
    deduplicated_items: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "reason": self.reason,
            "uow_id": self.uow_id,
            "evidence_hash": self.evidence_hash,
            "execution_hash": self.execution_hash,
            "is_replication": self.is_replication,
            "quarantined_items": self.quarantined_items,
            "downgraded_items": self.downgraded_items,
            "deduplicated_items": self.deduplicated_items,
        }


@dataclass
class UoWIssuanceRecord:
    """Entry in the control-plane issuance ledger tracking a unit of work."""

    uow_id: str
    worker_id: str
    issued_sequence: int
    parent_uow_id: Optional[str] = None
    expected_state: str = ""
    target_query: str = ""
    issued_at: float = field(default_factory=time.time)
    is_superseded: bool = False
    superseded_reason: str = ""
    disposition: Optional[AdmissionVerdict] = None
    disposition_reason: str = ""
    evidence_hash: Optional[str] = None
    execution_hash: Optional[str] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.disposition:
            d["disposition"] = self.disposition.value
        return d


class UoWIssuanceLedger:
    """Authority issuance ledger tracking active, completed, and superseded UoWs.

    Decouples causal validity from completion arrival order.
    """

    def __init__(self, ledger_file: Optional[Path] = None) -> None:
        self.ledger_file = ledger_file
        self.records: Dict[str, UoWIssuanceRecord] = {}
        self.sequence_counter: int = 0
        if self.ledger_file and self.ledger_file.exists():
            self._load()

    def issue_uow(
        self,
        uow_id: str,
        worker_id: str = "nano-jetson-01",
        parent_uow_id: Optional[str] = None,
        expected_state: str = "",
        target_query: str = "",
    ) -> UoWIssuanceRecord:
        """Issues a new bounded UoW with a monotonic sequence number."""
        self.sequence_counter += 1
        rec = UoWIssuanceRecord(
            uow_id=uow_id,
            worker_id=worker_id,
            issued_sequence=self.sequence_counter,
            parent_uow_id=parent_uow_id,
            expected_state=expected_state,
            target_query=target_query,
            issued_at=time.time(),
        )
        self.records[uow_id] = rec
        self._persist()
        return rec

    def is_issued(self, uow_id: str) -> bool:
        return uow_id in self.records

    def is_dispositioned(self, uow_id: str) -> bool:
        rec = self.records.get(uow_id)
        return rec is not None and rec.disposition is not None

    def is_parent_valid(self, parent_uow_id: Optional[str]) -> Tuple[bool, str]:
        """Validates that a parent UoW has not been superseded or rejected."""
        if not parent_uow_id:
            return True, "No parent required"
        if parent_uow_id not in self.records:
            return False, f"Parent UoW '{parent_uow_id}' was never issued in ledger"
        p = self.records[parent_uow_id]
        if p.is_superseded:
            return False, f"Parent UoW '{parent_uow_id}' has been superseded: {p.superseded_reason}"
        if p.disposition in {AdmissionVerdict.REJECT, AdmissionVerdict.REFUSE}:
            return False, f"Parent UoW '{parent_uow_id}' was rejected: {p.disposition_reason}"
        return True, "Parent state valid"

    def supersede_uow(self, uow_id: str, reason: str) -> None:
        """Marks a UoW or parent question as superseded and cascades to dependent un-dispositioned children."""
        if uow_id in self.records:
            self.records[uow_id].is_superseded = True
            self.records[uow_id].superseded_reason = reason
        # Cascade to uncompleted children
        for rec in self.records.values():
            if rec.parent_uow_id == uow_id and rec.disposition is None:
                rec.is_superseded = True
                rec.superseded_reason = f"Cascaded from parent {uow_id}: {reason}"
        self._persist()

    def record_disposition(
        self,
        uow_id: str,
        decision: AdmissionDecision,
        evidence_hash: str = "",
        execution_hash: str = "",
    ) -> None:
        """Records admission disposition in the ledger."""
        if uow_id in self.records:
            rec = self.records[uow_id]
            rec.disposition = decision.verdict
            rec.disposition_reason = decision.reason
            rec.evidence_hash = evidence_hash or decision.evidence_hash
            rec.execution_hash = execution_hash or decision.execution_hash
            rec.completed_at = time.time()
            self._persist()

    def _persist(self) -> None:
        if not self.ledger_file:
            return
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "sequence_counter": self.sequence_counter,
            "records": {k: v.to_dict() for k, v in self.records.items()},
        }
        self.ledger_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not self.ledger_file or not self.ledger_file.exists():
            return
        try:
            data = json.loads(self.ledger_file.read_text(encoding="utf-8"))
            self.sequence_counter = data.get("sequence_counter", 0)
            for k, d in data.get("records", {}).items():
                disp = AdmissionVerdict(d["disposition"]) if d.get("disposition") else None
                rec = UoWIssuanceRecord(
                    uow_id=d["uow_id"],
                    worker_id=d.get("worker_id", "nano-jetson-01"),
                    issued_sequence=d.get("issued_sequence", 0),
                    parent_uow_id=d.get("parent_uow_id"),
                    expected_state=d.get("expected_state", ""),
                    target_query=d.get("target_query", ""),
                    issued_at=d.get("issued_at", time.time()),
                    is_superseded=d.get("is_superseded", False),
                    superseded_reason=d.get("superseded_reason", ""),
                    disposition=disp,
                    disposition_reason=d.get("disposition_reason", ""),
                    evidence_hash=d.get("evidence_hash"),
                    execution_hash=d.get("execution_hash"),
                    completed_at=d.get("completed_at"),
                )
                self.records[k] = rec
        except Exception:
            pass


class UnoQControlPlaneGateway:
    """Regulatory control plane node (e.g. UNO Q).

    Enforces the absolute separation of research work plane and canonical authority.
    Validates dual-tier hashes (H_E, H_X), causal issuance, referential integrity,
    epistemic grounding, deduplication/replication, and resource backpressure.
    """

    def __init__(
        self,
        ledger: Optional[UoWIssuanceLedger] = None,
        allowed_software_commits: Optional[Set[str]] = None,
        canonical_entities: Optional[Set[str]] = None,
        canonical_relations: Optional[Set[Tuple[str, str, str]]] = None,
        canonical_claims: Optional[Set[Tuple[str, str, str]]] = None,
        log_file: Optional[Path] = None,
        enforce_issuance: Optional[bool] = None,
    ) -> None:
        self.ledger = ledger or UoWIssuanceLedger()
        self.enforce_issuance = (ledger is not None) if enforce_issuance is None else enforce_issuance
        self.highest_causal_sequence: int = 0
        self.allowed_software_commits = allowed_software_commits
        self.canonical_entities = set(canonical_entities) if canonical_entities else set()
        self.canonical_relations = set(canonical_relations) if canonical_relations else set()
        self.canonical_claims = set(canonical_claims) if canonical_claims else set()
        self.log_file = log_file

        # Replication & deduplication index: H_E -> list of H_X
        self.admitted_evidence_hashes: Dict[str, List[str]] = {}
        self.admitted_execution_hashes: Set[str] = set()
        self.admitted_uow_ids: Set[str] = set()

        # Operational state
        self.backpressure_active: bool = False

    def verify_bundle(self, bundle: Any) -> AdmissionDecision:
        """Evaluates an incoming CandidateBundle against all control plane validation gates."""
        uow_id = getattr(bundle, "uow_id", "UNKNOWN_UOW")

        # 1. Dual-Tier Hash Integrity Check (H_E and H_X)
        h_e_expected = getattr(bundle, "evidence_hash", "")
        h_x_expected = getattr(bundle, "execution_hash", "") or getattr(bundle, "candidate_bundle_hash", "")

        if not h_e_expected and hasattr(bundle, "compute_evidence_hash"):
            h_e_expected = bundle.compute_evidence_hash(update=True)
        if not h_x_expected and hasattr(bundle, "compute_execution_hash"):
            h_x_expected = bundle.compute_execution_hash(update=True)

        if not h_e_expected or not h_x_expected:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.REJECT,
                    reason="REJECT: Missing evidence hash (H_E) or execution hash (H_X) in candidate bundle.",
                    uow_id=uow_id,
                )
            )

        # Verify H_E
        h_e_computed = bundle.compute_evidence_hash(update=False) if hasattr(bundle, "compute_evidence_hash") else ""
        if h_e_computed and h_e_computed != h_e_expected:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.REJECT,
                    reason=f"REJECT: Hash mismatch / payload tampering detected: Evidence payload hash mismatch (H_E computed {h_e_computed[:12]} != bundle {h_e_expected[:12]}).",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                )
            )

        # Verify H_X
        h_x_computed = bundle.compute_execution_hash(update=False) if hasattr(bundle, "compute_execution_hash") else ""
        if h_x_computed and h_x_computed != h_x_expected:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.REJECT,
                    reason=f"REJECT: Hash mismatch / payload tampering detected: Execution envelope hash mismatch (H_X computed {h_x_computed[:12]} != bundle {h_x_expected[:12]}).",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                )
            )

        # 2. Software Commit Qualification Check
        commit = getattr(bundle, "software_commit", "")
        if self.allowed_software_commits is not None:
            if commit not in self.allowed_software_commits:
                return self._record_and_return(
                    AdmissionDecision(
                        verdict=AdmissionVerdict.REJECT,
                        reason=f"REJECT: Software commit '{commit}' is not qualified. Allowed: {sorted(self.allowed_software_commits)}",
                        uow_id=uow_id,
                        evidence_hash=h_e_expected,
                        execution_hash=h_x_expected,
                    )
                )

        # 3. Authority Boundary & Shadow Mode Check (Immediate REFUSE on violation)
        obs = getattr(bundle, "observer_state", {})
        if obs.get("shadow_mode") is False:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.REFUSE,
                    reason="REFUSE: Authority violation. Jetson Nano work plane must execute in SHADOW_MODE=True.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                )
            )
        if obs.get("mutate_schedule_direct") is True or obs.get("request_canonical_write") is True:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.REFUSE,
                    reason="REFUSE: Authority violation. Work plane worker cannot issue canonical mutations or override control plane schedule.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                )
            )

        # 4. Replay Detection
        is_already_dispositioned = (
            (self.ledger.is_dispositioned(uow_id) if self.enforce_issuance else (uow_id in self.admitted_uow_ids))
            or h_x_expected in self.admitted_execution_hashes
        )
        if is_already_dispositioned:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.REJECT_IDEMPOTENT,
                    reason=f"REJECT_IDEMPOTENT: BUNDLE_REPLAY: UoW '{uow_id}' or execution hash H_X has already been admitted.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                    admitted_bundle=bundle,
                )
            )

        # Backward compatibility for single-node monotonic sequence high-water check
        causal_seq = getattr(bundle, "causal_sequence_id", 0)
        if self.highest_causal_sequence > 0 and causal_seq <= self.highest_causal_sequence:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.REJECT,
                    reason=f"REJECT: Superseded UoW arrival. Sequence {causal_seq} <= high-water mark {self.highest_causal_sequence}.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                )
            )

        # 5. Issuance Ledger & Causal Validity Check (when enforce_issuance is enabled)
        if self.enforce_issuance:
            if not self.ledger.is_issued(uow_id):
                return self._record_and_return(
                    AdmissionDecision(
                        verdict=AdmissionVerdict.REJECT,
                        reason=f"REJECT: Unissued UoW '{uow_id}'. Work was not scheduled or issued by UNO Q control plane.",
                        uow_id=uow_id,
                        evidence_hash=h_e_expected,
                        execution_hash=h_x_expected,
                    )
                )

            # Check if parent state is valid
            parent_id = getattr(bundle, "parent_uow_id", None)
            parent_valid, parent_reason = self.ledger.is_parent_valid(parent_id)
            if not parent_valid:
                return self._record_and_return(
                    AdmissionDecision(
                        verdict=AdmissionVerdict.REJECT,
                        reason=f"REJECT: Superseded parent state. {parent_reason}",
                        uow_id=uow_id,
                        evidence_hash=h_e_expected,
                        execution_hash=h_x_expected,
                    )
                )

        # 6. Check if target question was unresolved
        candidate_claims = getattr(bundle, "candidate_claims", [])
        candidate_relations = getattr(bundle, "candidate_relations", [])
        candidate_entities = getattr(bundle, "candidate_entities", [])
        candidate_questions = getattr(bundle, "candidate_questions", [])

        if not candidate_claims and not candidate_relations and not candidate_entities:
            # Clean inquiry returned no candidate mutations -> UNRESOLVED
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.UNRESOLVED,
                    reason=f"UNRESOLVED: UoW '{uow_id}' probed open question but returned zero candidate mutations.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                    admitted_bundle=bundle,
                )
            )

        # 5. Referential Integrity Check
        cand_ent_ids = {getattr(e, "entity_id", "") for e in candidate_entities}
        known_entities = self.canonical_entities | cand_ent_ids
        quarantined_items: List[Dict[str, Any]] = []

        for rel in candidate_relations:
            s_id = getattr(rel, "source_id", "")
            t_id = getattr(rel, "target_id", "")
            if s_id not in known_entities or t_id not in known_entities:
                quarantined_items.append(
                    {
                        "type": "RELATION",
                        "item": asdict(rel) if hasattr(rel, "__dataclass_fields__") else rel,
                        "reason": f"DANGLING_REFERENCE: source '{s_id}' or target '{t_id}' not in canonical graph or candidate entities.",
                    }
                )

        for claim in candidate_claims:
            sub_id = getattr(claim, "subject_id", "")
            if sub_id not in known_entities:
                quarantined_items.append(
                    {
                        "type": "CLAIM",
                        "item": asdict(claim) if hasattr(claim, "__dataclass_fields__") else claim,
                        "reason": f"DANGLING_REFERENCE: subject '{sub_id}' not in canonical graph or candidate entities.",
                    }
                )

        if quarantined_items:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.QUARANTINE,
                    reason=f"QUARANTINE: DANGLING_REFERENCE: {len(quarantined_items)} items contain dangling references to nonexistent canonical entities.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                    quarantined_items=quarantined_items,
                )
            )

        # 6. Epistemic Evidence Gating Check
        source_fragments = getattr(bundle, "source_fragments", [])
        fragment_map = {getattr(f, "fragment_id", ""): f for f in source_fragments}
        downgraded_items: List[Dict[str, Any]] = []
        strong_statuses = {"HISTORICALLY_SUPPORTED", "DIRECT_GENEALOGY", "GROUND_TRUTH"}

        for claim in candidate_claims:
            st = getattr(claim, "epistemic_status", "")
            if st in strong_statuses:
                fr_ids = getattr(claim, "evidence_fragment_ids", [])
                valid_frags = [
                    fid for fid in fr_ids if fid in fragment_map and getattr(fragment_map[fid], "text", "").strip()
                ]
                if not valid_frags:
                    claim.epistemic_status = "HYPOTHETICAL"
                    downgraded_items.append(
                        {
                            "claim_id": getattr(claim, "claim_id", ""),
                            "original_status": st,
                            "new_status": "HYPOTHETICAL",
                            "reason": "EPISTEMIC_OVERPROMOTION: Strong historical assertion lacks primary-source evidence fragments.",
                        }
                    )

        # 7. Deduplication vs. Replication Recognition
        is_replication = False
        if h_e_expected in self.admitted_evidence_hashes:
            is_replication = True
            # Same evidence produced across different execution envelopes
            self.admitted_evidence_hashes[h_e_expected].append(h_x_expected)
        else:
            self.admitted_evidence_hashes[h_e_expected] = [h_x_expected]

        deduplicated_items: List[Dict[str, Any]] = []
        valid_relations = []
        for rel in candidate_relations:
            s_id = getattr(rel, "source_id", "")
            t_id = getattr(rel, "target_id", "")
            v_val = getattr(rel, "verb", "")
            key = (s_id, t_id, v_val)
            if key in self.canonical_relations:
                deduplicated_items.append({"type": "RELATION", "key": key, "reason": "ALREADY_CANONICAL"})
            else:
                valid_relations.append(rel)

        valid_claims = []
        for claim in candidate_claims:
            s_id = getattr(claim, "subject_id", "")
            p_val = getattr(claim, "predicate", "")
            o_val = getattr(claim, "object_val", "")
            key = (s_id, p_val, o_val)
            if key in self.canonical_claims:
                deduplicated_items.append({"type": "CLAIM", "key": key, "reason": "ALREADY_CANONICAL"})
            else:
                valid_claims.append(claim)

        # 8. Resource & Backpressure Feedback
        res_state = getattr(bundle, "resource_state", {})
        if res_state.get("backpressure_flag") is True or res_state.get("ram_available_mb", 1024.0) < 512.0:
            self.backpressure_active = True
        else:
            self.backpressure_active = False

        # Record admission in state
        self.admitted_execution_hashes.add(h_x_expected)
        self.admitted_uow_ids.add(uow_id)

        # Apply canonical mutations (control plane only)
        for e in candidate_entities:
            self.canonical_entities.add(getattr(e, "entity_id", ""))
        for r in valid_relations:
            self.canonical_relations.add((getattr(r, "source_id", ""), getattr(r, "target_id", ""), getattr(r, "verb", "")))
        for c in valid_claims:
            self.canonical_claims.add((getattr(c, "subject_id", ""), getattr(c, "predicate", ""), getattr(c, "object_val", "")))

        # 9. Return Decision
        if is_replication:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.DEDUP,
                    reason="DEDUP: Independent evidence replication verified (identical H_E across distinct H_X).",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                    is_replication=True,
                    admitted_bundle=bundle,
                    deduplicated_items=deduplicated_items,
                )
            )

        if downgraded_items:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.DOWNGRADE,
                    reason=f"DOWNGRADE: Admitted with {len(downgraded_items)} claims downgraded due to ungrounded epistemic status.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                    admitted_bundle=bundle,
                    downgraded_items=downgraded_items,
                    deduplicated_items=deduplicated_items,
                )
            )

        if deduplicated_items and not valid_relations and not valid_claims and not candidate_entities:
            return self._record_and_return(
                AdmissionDecision(
                    verdict=AdmissionVerdict.DEDUP,
                    reason=f"DEDUP: All {len(deduplicated_items)} candidates were duplicates of existing canonical records.",
                    uow_id=uow_id,
                    evidence_hash=h_e_expected,
                    execution_hash=h_x_expected,
                    admitted_bundle=bundle,
                    deduplicated_items=deduplicated_items,
                )
            )

        return self._record_and_return(
            AdmissionDecision(
                verdict=AdmissionVerdict.ADMIT,
                reason="ADMIT: Passed all cryptographic, causal, referential, authority, and epistemic gates.",
                uow_id=uow_id,
                evidence_hash=h_e_expected,
                execution_hash=h_x_expected,
                admitted_bundle=bundle,
                deduplicated_items=deduplicated_items,
            )
        )

    def _record_and_return(self, decision: AdmissionDecision) -> AdmissionDecision:
        self.ledger.record_disposition(
            uow_id=decision.uow_id,
            decision=decision,
            evidence_hash=decision.evidence_hash,
            execution_hash=decision.execution_hash,
        )
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(decision.to_dict()) + "\n")
        return decision
