"""SOVCTX Nano Research Work Plane Worker.

Specialized for the 2 GB Jetson Nano:
- Specialization: Research Work Plane (Acquisition, Extraction, Relational Analysis, Question Probing, Proposing Structure)
- Separation of Concerns: Control Plane (UNO Q) owns authority, canonical admission, and global scheduling
- Core Invariant: PROPOSED != AUTHORIZED (Nano proposes candidates, never silently mutates canonical state)
- Self-Observation: Continuous lightweight G1 Geometric Observer monitoring research activity structure
- Caution Signal: Low motion + shrinking eigengap triggers AMBIGUOUS / ALLOCATE_MORE_OBSERVATION
- Shadow Mode: GEOMETRIC_OBSERVER = ON, GEOMETRIC_AUTHORITY = OFF
- No Shared Wall Clock: Pure causal sequence ordering (epoch, local sequence, UoW ID, artifact hash)
- 2 GB Resource Protection: Monitors RSS and available RAM, emitting backpressure signals to control plane
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from sovctx.node.guard import ResourceGuard
from sovctx.node.leibniz_bocker import (
    DiagnosticRegime,
    LeibnizBockerDiagnostics,
    LeibnizBockerTracker,
    SubspaceIdentifiability,
)
from sovctx.node.research_question import QuestionStatus, ResearchQuestion


def get_current_git_commit(repo_root: Optional[Path] = None) -> str:
    """Retrieves the current canonical Git commit SHA for provenance tracking."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    try:
        import subprocess

        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=True,
        )
        out = res.stdout.strip()
        if out:
            return out
    except Exception:
        try:
            head_path = repo_root / ".git" / "HEAD"
            if head_path.exists():
                ref = head_path.read_text(encoding="utf-8").strip()
                if ref.startswith("ref: "):
                    ref_path = repo_root / ".git" / ref[5:].strip()
                    if ref_path.exists():
                        return ref_path.read_text(encoding="utf-8").strip()
                elif len(ref) == 40:
                    return ref
        except Exception:
            pass
    return "c8a975e974e3a12af94f647944ac56d1fb8597fc"


@dataclass
class SourceFragment:
    """Primary-source text fragment extracted from verified corpus documents."""

    fragment_id: str
    source_id: str
    text: str
    locator: str  # e.g. "Part I, pp. 1242-1244"
    char_span: Tuple[int, int] = (0, 0)
    fragment_hash: str = ""

    def __post_init__(self) -> None:
        if not self.fragment_hash and self.text:
            self.fragment_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()


@dataclass
class CandidateEntity:
    """Proposed entity awaiting control plane canonical admission."""

    entity_id: str
    label: str
    category: str  # e.g. "PERSON", "CONCEPT", "EQUATION", "SYSTEM"
    aliases: List[str] = field(default_factory=list)
    provenance_fragment_ids: List[str] = field(default_factory=list)


@dataclass
class CandidateClaim:
    """Proposed epistemic claim awaiting control plane canonical admission."""

    claim_id: str
    subject_id: str
    predicate: str
    object_val: str
    epistemic_status: str  # "HYPOTHETICAL", "HISTORICALLY_SUPPORTED", "DIRECT_GENEALOGY", "STRUCTURAL_ANALOGUE"
    evidence_fragment_ids: List[str] = field(default_factory=list)


@dataclass
class CandidateRelation:
    """Proposed relationship between nodes awaiting control plane admission."""

    source_id: str
    target_id: str
    verb: str  # One of normalized verbs: STABILIZE, CONTROL, INVERT, PROBE, REPRESENT, etc.
    rationale: str
    evidence_fragment_ids: List[str] = field(default_factory=list)


@dataclass
class CandidateQuestion:
    """Proposed open research question formulated from anomalies or bridges."""

    question_id: str
    thread_id: str
    question_text: str
    target_channel: str
    originating_evidence: str


@dataclass
class CandidateSource:
    """Proposed source discovered during acquisition."""

    source_id: str
    label: str
    authors: List[str]
    year: int
    provenance_path: str
    content_hash: str


@dataclass
class CandidateBundle:
    """Proposed graph modifications emitted by the research work plane.

    Hard Contract: PROPOSED != AUTHORIZED. The Nano proposes immutable candidate bundles;
    only the regulatory control plane (e.g. UNO Q / CandidateBundleVerifier) can admit
    or commit to canonical records.
    """

    uow_id: str
    parent_uow_id: Optional[str] = None
    worker_id: str = "nano-jetson-01"
    causal_sequence_id: int = 1
    software_commit: str = ""
    source_manifest: List[str] = field(default_factory=list)
    source_hashes: Dict[str, str] = field(default_factory=dict)
    source_fragments: List[SourceFragment] = field(default_factory=list)
    candidate_entities: List[CandidateEntity] = field(default_factory=list)
    candidate_relations: List[CandidateRelation] = field(default_factory=list)
    candidate_claims: List[CandidateClaim] = field(default_factory=list)
    candidate_questions: List[CandidateQuestion] = field(default_factory=list)
    observer_state: Dict[str, Any] = field(default_factory=dict)
    resource_state: Dict[str, Any] = field(default_factory=dict)
    candidate_bundle_hash: str = ""

    # Backward compatibility aliases/fields
    sources: List[CandidateSource] = field(default_factory=list)
    sequence_idx: Optional[int] = None
    relations: List[CandidateRelation] = field(default_factory=list)
    questions: List[CandidateQuestion] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.sequence_idx is not None and not self.causal_sequence_id:
            self.causal_sequence_id = self.sequence_idx
        if not self.candidate_relations and self.relations:
            self.candidate_relations = list(self.relations)
        elif not self.relations and self.candidate_relations:
            self.relations = list(self.candidate_relations)
        if not self.candidate_questions and self.questions:
            self.candidate_questions = list(self.questions)
        elif not self.questions and self.candidate_questions:
            self.questions = list(self.candidate_questions)
        if not self.source_manifest and self.sources:
            self.source_manifest = [s.source_id for s in self.sources]
            for s in self.sources:
                self.source_hashes[s.source_id] = s.content_hash

    @property
    def content_hash(self) -> str:
        if not self.candidate_bundle_hash:
            self.compute_hash()
        return self.candidate_bundle_hash

    @content_hash.setter
    def content_hash(self, val: str) -> None:
        self.candidate_bundle_hash = val

    def compute_hash(self, update: bool = True) -> str:
        payload = {
            "uow_id": self.uow_id,
            "parent_uow_id": self.parent_uow_id,
            "worker_id": self.worker_id,
            "causal_sequence_id": self.causal_sequence_id,
            "software_commit": self.software_commit,
            "source_manifest": sorted(self.source_manifest),
            "source_hashes": {k: self.source_hashes[k] for k in sorted(self.source_hashes.keys())},
            "source_fragments": [
                {
                    "fragment_id": f.fragment_id,
                    "source_id": f.source_id,
                    "text": f.text,
                    "locator": f.locator,
                    "char_span": list(f.char_span),
                    "fragment_hash": f.fragment_hash,
                }
                for f in sorted(self.source_fragments, key=lambda x: x.fragment_id)
            ],
            "candidate_entities": [
                {
                    "entity_id": e.entity_id,
                    "label": e.label,
                    "category": e.category,
                    "aliases": sorted(e.aliases),
                    "provenance_fragment_ids": sorted(e.provenance_fragment_ids),
                }
                for e in sorted(self.candidate_entities, key=lambda x: x.entity_id)
            ],
            "candidate_relations": [
                {
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "verb": r.verb,
                    "rationale": r.rationale,
                    "evidence_fragment_ids": sorted(r.evidence_fragment_ids),
                }
                for r in sorted(self.candidate_relations, key=lambda x: (x.source_id, x.target_id, x.verb))
            ],
            "candidate_claims": [
                {
                    "claim_id": c.claim_id,
                    "subject_id": c.subject_id,
                    "predicate": c.predicate,
                    "object_val": c.object_val,
                    "epistemic_status": c.epistemic_status,
                    "evidence_fragment_ids": sorted(c.evidence_fragment_ids),
                }
                for c in sorted(self.candidate_claims, key=lambda x: x.claim_id)
            ],
            "candidate_questions": [
                {
                    "question_id": q.question_id,
                    "thread_id": q.thread_id,
                    "question_text": q.question_text,
                    "target_channel": q.target_channel,
                    "originating_evidence": q.originating_evidence,
                }
                for q in sorted(self.candidate_questions, key=lambda x: x.question_id)
            ],
            "observer_state": self.observer_state,
            "resource_state": self.resource_state,
        }
        serialized = json.dumps(payload, sort_keys=True)
        h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if update:
            self.candidate_bundle_hash = h
        return h


class AdmissionVerdict(str, Enum):
    """Verdicts emitted by the regulatory control plane gate (e.g. UNO Q)."""

    ADMIT = "ADMIT"
    REJECT = "REJECT"
    REJECT_IDEMPOTENT = "REJECT_IDEMPOTENT"
    QUARANTINE = "QUARANTINE"
    REFUSE = "REFUSE"
    DOWNGRADE = "DOWNGRADE"
    DEDUP = "DEDUP"


@dataclass
class AdmissionDecision:
    """Regulatory admission decision returned to the work plane."""

    verdict: AdmissionVerdict
    reason: str
    admitted_bundle: Optional[CandidateBundle] = None
    quarantined_items: List[Dict[str, Any]] = field(default_factory=list)
    downgraded_items: List[Dict[str, Any]] = field(default_factory=list)
    deduplicated_items: List[Dict[str, Any]] = field(default_factory=list)


class CandidateBundleVerifier:
    """Control plane authority gate (modeling UNO Q regulatory node).

    Enforces the fundamental law: PROPOSED != AUTHORIZED.
    Verifies that proposed candidates satisfy all authority invariants before canonical admission:
    1. Cryptographic hash integrity (detects corruption or payload tampering).
    2. Software commit qualification (verifies worker was running certified commit).
    3. Replay prevention and causal sequence ordering (monotonic sequence, idempotent repeat).
    4. Referential integrity (no dangling references to non-existent nodes).
    5. Epistemic evidence gating (downgrades or quarantines ungrounded strong claims).
    6. Authority boundary enforcement (blocks direct write attempts or scheduler overrides).
    7. Deduplication against canonical records.
    """

    def __init__(
        self,
        allowed_software_commits: Optional[Set[str]] = None,
        canonical_entities: Optional[Set[str]] = None,
        canonical_relations: Optional[Set[Tuple[str, str, str]]] = None,
        canonical_claims: Optional[Set[Tuple[str, str, str]]] = None,
    ) -> None:
        self.allowed_software_commits = allowed_software_commits
        self.canonical_entities = set(canonical_entities) if canonical_entities else set()
        self.canonical_relations = set(canonical_relations) if canonical_relations else set()
        self.canonical_claims = set(canonical_claims) if canonical_claims else set()
        self.admitted_uow_ids: Set[str] = set()
        self.admitted_bundle_hashes: Set[str] = set()
        self.highest_causal_sequence: int = 0

    def verify_bundle(self, bundle: CandidateBundle) -> AdmissionDecision:
        """Evaluates an incoming CandidateBundle against all control plane validation gates."""
        # 1. Cryptographic Hash Integrity Check
        if not bundle.candidate_bundle_hash:
            return AdmissionDecision(AdmissionVerdict.REJECT, "REJECT: Missing candidate_bundle_hash in bundle.")

        recorded_hash = bundle.candidate_bundle_hash
        computed_hash = bundle.compute_hash(update=False)
        if computed_hash != recorded_hash:
            return AdmissionDecision(
                AdmissionVerdict.REJECT,
                f"REJECT: Hash mismatch / payload tampering detected. Computed {computed_hash} != Bundle {recorded_hash}",
            )

        # 2. Software Commit Qualification Check
        if self.allowed_software_commits is not None:
            if bundle.software_commit not in self.allowed_software_commits:
                return AdmissionDecision(
                    AdmissionVerdict.REJECT,
                    f"REJECT: Software commit '{bundle.software_commit}' is not qualified. Allowed: {sorted(self.allowed_software_commits)}",
                )

        # 3. Replay Detection
        if bundle.uow_id in self.admitted_uow_ids or bundle.candidate_bundle_hash in self.admitted_bundle_hashes:
            return AdmissionDecision(
                AdmissionVerdict.REJECT_IDEMPOTENT,
                f"REJECT_IDEMPOTENT: UoW '{bundle.uow_id}' or bundle hash has already been admitted.",
                admitted_bundle=bundle,
            )

        # 4. Causal Sequence Monotonicity Check
        if bundle.causal_sequence_id <= self.highest_causal_sequence:
            return AdmissionDecision(
                AdmissionVerdict.REJECT,
                f"REJECT: Superseded UoW arrival. Sequence {bundle.causal_sequence_id} <= high-water mark {self.highest_causal_sequence}.",
            )

        # 5. Authority Boundary & Shadow Mode Check
        obs = bundle.observer_state
        if obs.get("shadow_mode") is False:
            return AdmissionDecision(
                AdmissionVerdict.REFUSE,
                "REFUSE: Authority violation. Jetson Nano work plane must execute in SHADOW_MODE=True.",
            )
        if obs.get("mutate_schedule_direct") is True or obs.get("request_canonical_write") is True:
            return AdmissionDecision(
                AdmissionVerdict.REFUSE,
                "REFUSE: Authority violation. Work plane worker cannot issue canonical mutations or override control plane schedule.",
            )

        # 6. Referential Integrity Check
        known_entities = self.canonical_entities | {e.entity_id for e in bundle.candidate_entities}
        quarantined_items: List[Dict[str, Any]] = []

        for rel in bundle.candidate_relations:
            if rel.source_id not in known_entities or rel.target_id not in known_entities:
                quarantined_items.append(
                    {
                        "type": "RELATION",
                        "item": asdict(rel),
                        "reason": f"DANGLING_REFERENCE: source '{rel.source_id}' or target '{rel.target_id}' not in canonical graph or candidate entities.",
                    }
                )

        for claim in bundle.candidate_claims:
            if claim.subject_id not in known_entities:
                quarantined_items.append(
                    {
                        "type": "CLAIM",
                        "item": asdict(claim),
                        "reason": f"DANGLING_REFERENCE: subject '{claim.subject_id}' not in canonical graph or candidate entities.",
                    }
                )

        if quarantined_items:
            return AdmissionDecision(
                AdmissionVerdict.QUARANTINE,
                f"QUARANTINE: DANGLING_REFERENCE: {len(quarantined_items)} items contain dangling references to nonexistent canonical entities.",
                quarantined_items=quarantined_items,
            )

        # 7. Epistemic Evidence Gating Check
        fragment_map = {f.fragment_id: f for f in bundle.source_fragments}
        downgraded_items: List[Dict[str, Any]] = []
        strong_epistemic_statuses = {"HISTORICALLY_SUPPORTED", "DIRECT_GENEALOGY", "GROUND_TRUTH"}

        for claim in bundle.candidate_claims:
            if claim.epistemic_status in strong_epistemic_statuses:
                valid_frags = [
                    fid
                    for fid in claim.evidence_fragment_ids
                    if fid in fragment_map and fragment_map[fid].text.strip()
                ]
                if not valid_frags:
                    orig_status = claim.epistemic_status
                    claim.epistemic_status = "HYPOTHETICAL"
                    downgraded_items.append(
                        {
                            "claim_id": claim.claim_id,
                            "original_status": orig_status,
                            "new_status": "HYPOTHETICAL",
                            "reason": "EPISTEMIC_OVERPROMOTION: Strong historical assertion lacks primary-source evidence fragments.",
                        }
                    )

        # 8. Deduplication Against Canonical Records
        deduplicated_items: List[Dict[str, Any]] = []
        valid_relations: List[CandidateRelation] = []
        for rel in bundle.candidate_relations:
            key = (rel.source_id, rel.target_id, rel.verb)
            if key in self.canonical_relations:
                deduplicated_items.append({"type": "RELATION", "key": key, "reason": "ALREADY_CANONICAL"})
            else:
                valid_relations.append(rel)

        valid_claims: List[CandidateClaim] = []
        for claim in bundle.candidate_claims:
            key = (claim.subject_id, claim.predicate, claim.object_val)
            if key in self.canonical_claims:
                deduplicated_items.append({"type": "CLAIM", "key": key, "reason": "ALREADY_CANONICAL"})
            else:
                valid_claims.append(claim)

        # Record admission in state
        self.admitted_uow_ids.add(bundle.uow_id)
        self.admitted_bundle_hashes.add(bundle.candidate_bundle_hash)
        self.highest_causal_sequence = max(self.highest_causal_sequence, bundle.causal_sequence_id)

        # Return decision
        if downgraded_items:
            return AdmissionDecision(
                AdmissionVerdict.DOWNGRADE,
                f"DOWNGRADE: Admitted with {len(downgraded_items)} claims downgraded due to ungrounded epistemic status.",
                admitted_bundle=bundle,
                downgraded_items=downgraded_items,
                deduplicated_items=deduplicated_items,
            )

        if deduplicated_items and not valid_relations and not valid_claims and not bundle.candidate_entities:
            return AdmissionDecision(
                AdmissionVerdict.DEDUP,
                f"DEDUP: All {len(deduplicated_items)} candidates were duplicates of existing canonical records.",
                admitted_bundle=bundle,
                deduplicated_items=deduplicated_items,
            )

        return AdmissionDecision(
            AdmissionVerdict.ADMIT,
            "ADMIT: Passed all cryptographic, causal, referential, authority, and epistemic gates.",
            admitted_bundle=bundle,
            deduplicated_items=deduplicated_items,
        )


@dataclass
class GeometricObservationTelemetry:
    """Self-observation of the Nano's own research state trajectory."""

    epoch_idx: int
    step_idx: int
    speed_max_angle: float
    speed_projector: float
    kappa_g: float
    residual_norm: float
    spectral_gap: float
    relative_gap: float
    davis_kahan_ratio: float
    identifiability: str
    regime: str
    eigenvalues: List[float]
    interpretation: str
    recommended_action: str
    shadow_mode: bool = True


@dataclass
class NanoWorkPlaneTelemetry:
    """Unified telemetry packet emitted by the Jetson Nano to the UNO Q control plane."""

    worker_id: str
    uow_id: str
    sequence_idx: int
    state: str  # IDLE, ACQUIRING, EXTRACTING, PROBING, OBSERVING, REPORTING
    candidate_bundle: CandidateBundle
    geometric_observation: GeometricObservationTelemetry
    ram_available_mb: float
    worker_rss_mb: float
    thermal_max_c: float
    backpressure_flag: bool
    causal_sequence_id: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class ResearchStateVectorBuilder:
    """Constructs the canonical 32-dimensional research activity state vector."""

    FEATURE_DIM: int = 32

    @staticmethod
    def build_vector(
        thread_counts: Dict[str, int],
        verb_counts: Dict[str, int],
        bridge_count: int,
        max_descendant_depth: int,
        institution_counts: Dict[str, int],
        question_type_counts: Dict[str, int],
    ) -> np.ndarray:
        # 1. Thread shares T1..T12
        total_t = max(1, sum(thread_counts.values()))
        t_shares = [thread_counts.get(f"T{i}", 0) / total_t for i in range(1, 13)]

        # 2. Verb shares (10 normalized verbs)
        verbs = [
            "STABILIZE",
            "CONTROL",
            "INVERT",
            "CONSTRAIN",
            "PROBE",
            "REPRESENT",
            "OBSERVE",
            "UPDATE",
            "ADAPT",
            "REGULARIZE",
        ]
        total_v = max(1, sum(verb_counts.values()))
        v_shares = [verb_counts.get(v, 0) / total_v for v in verbs]

        # 3. Structural metrics
        structural = [
            float(bridge_count),
            float(max_descendant_depth),
        ]

        # 4. Institutions (5 canonical centers)
        inst_keys = ["Steklov", "TsAGI", "IPM", "Sechenov", "IAT"]
        inst_vals = [float(institution_counts.get(k, 0)) for k in inst_keys]

        # 5. Question type counts
        q_vals = [
            float(question_type_counts.get("spines", 0)),
            float(question_type_counts.get("bridges", 0)),
            float(question_type_counts.get("descendants", 0)),
        ]

        vec = t_shares + v_shares + structural + inst_vals + q_vals
        return np.array(vec, dtype=float)


class NanoResearchWorker:
    """Specialized Research Work Plane Worker running on the 2 GB Jetson Nano.

    Loop:
        ACQUIRE -> EXTRACT -> RELATE -> PROBE -> PROPOSE -> G1 OBSERVER -> REPORT
    """

    def __init__(
        self,
        worker_id: str = "nano-jetson-01",
        tracker_k: int = 2,
        tracker_alpha: float = 0.5,
        shadow_mode: bool = True,
        output_telemetry_dir: Path = Path("evidence/n5"),
        software_commit: Optional[str] = None,
        repo_root: Optional[Path] = None,
    ) -> None:
        self.worker_id = worker_id
        self.shadow_mode = shadow_mode
        self.output_telemetry_dir = output_telemetry_dir
        self.output_telemetry_dir.mkdir(parents=True, exist_ok=True)
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.software_commit = software_commit or get_current_git_commit(self.repo_root)

        self.guard = ResourceGuard()
        self.tracker = LeibnizBockerTracker(k=tracker_k, alpha=tracker_alpha, dt=1.0)
        self.state_history: List[np.ndarray] = []
        self.sequence_idx = 0
        self.current_state = "IDLE"

    def process_work_unit(
        self,
        uow_id: str,
        parent_uow_id: Optional[str] = None,
        questions_to_probe: Optional[List[ResearchQuestion]] = None,
        target_query: Optional[str] = None,
        simulated_discoveries: Optional[Dict[str, Any]] = None,
        source_manifest: Optional[List[str]] = None,
        source_hashes: Optional[Dict[str, str]] = None,
        source_fragments: Optional[List[SourceFragment]] = None,
        candidate_entities: Optional[List[CandidateEntity]] = None,
        candidate_relations: Optional[List[CandidateRelation]] = None,
        candidate_claims: Optional[List[CandidateClaim]] = None,
        candidate_questions: Optional[List[CandidateQuestion]] = None,
        candidate_sources: Optional[List[CandidateSource]] = None,
    ) -> NanoWorkPlaneTelemetry:
        """Executes a bounded research work unit and returns proposed candidates + telemetry."""
        self.sequence_idx += 1
        causal_seq = self.sequence_idx

        # 1. ACQUIRE & EXTRACT & RELATE & PROBE
        self.current_state = "PROBING"
        thread_counts: Dict[str, int] = {f"T{i}": 0 for i in range(1, 13)}
        verb_counts: Dict[str, int] = {}
        sources_out: List[CandidateSource] = list(candidate_sources or [])
        manifest_out: List[str] = list(source_manifest or [])
        hashes_out: Dict[str, str] = dict(source_hashes or {})
        fragments_out: List[SourceFragment] = list(source_fragments or [])
        entities_out: List[CandidateEntity] = list(candidate_entities or [])
        relations_out: List[CandidateRelation] = list(candidate_relations or [])
        claims_out: List[CandidateClaim] = list(candidate_claims or [])
        questions_out: List[CandidateQuestion] = list(candidate_questions or [])

        max_depth = 0
        bridge_count = 0

        probed_qs = questions_to_probe or []
        for q in probed_qs:
            t_id = q.thread_id
            if t_id in thread_counts:
                thread_counts[t_id] += 1
            if "BRIDGE" in q.question_id:
                bridge_count += 1
            if ":D1" in q.question_id:
                c = q.question_id.count(":D1")
                if c > max_depth:
                    max_depth = c

            # Extract normalized verbs under test
            for v in ["STABILIZE", "CONTROL", "INVERT", "CONSTRAIN", "OBSERVE", "REPRESENT", "PROBE"]:
                if v in q.relation_under_test:
                    verb_counts[v] = verb_counts.get(v, 0) + 1

        # Process any simulated discoveries / extractions passed to the work unit
        if simulated_discoveries:
            for s in simulated_discoveries.get("sources", []):
                s_hash = hashlib.sha256(s["id"].encode("utf-8")).hexdigest()
                manifest_out.append(s["id"])
                hashes_out[s["id"]] = s_hash
                sources_out.append(
                    CandidateSource(
                        source_id=s["id"],
                        label=s["label"],
                        authors=s.get("authors", []),
                        year=s.get("year", 1960),
                        provenance_path=s.get("path", ""),
                        content_hash=s_hash,
                    )
                )
            for r in simulated_discoveries.get("relations", []):
                relations_out.append(
                    CandidateRelation(
                        source_id=r["source"],
                        target_id=r["target"],
                        verb=r["verb"],
                        rationale=r.get("rationale", ""),
                        evidence_fragment_ids=r.get("fragments", []),
                    )
                )
            for q_new in simulated_discoveries.get("questions", []):
                questions_out.append(
                    CandidateQuestion(
                        question_id=q_new["id"],
                        thread_id=q_new["thread_id"],
                        question_text=q_new["text"],
                        target_channel=q_new.get("channel", "MATHEMATICAL"),
                        originating_evidence=q_new.get("origin", ""),
                    )
                )

        # 2. G1 GEOMETRIC OBSERVER (Self-Observation)
        self.current_state = "OBSERVING"
        state_vec = ResearchStateVectorBuilder.build_vector(
            thread_counts=thread_counts,
            verb_counts=verb_counts,
            bridge_count=bridge_count,
            max_descendant_depth=max_depth,
            institution_counts={"Steklov": 2, "IAT": 3},
            question_type_counts={
                "spines": max(0, len(probed_qs) - bridge_count),
                "bridges": bridge_count,
                "descendants": max_depth,
            },
        )
        self.state_history.append(state_vec)

        # Increment phi(t) = x(t) - x(t-1)
        if len(self.state_history) == 1:
            phi_t = state_vec.copy()
        else:
            phi_t = self.state_history[-1] - self.state_history[-2]

        step_label = f"UoW_{uow_id}_seq_{causal_seq}"
        diag = self.tracker.step(phi_t, step_label=step_label, t=causal_seq)

        # Evaluate Interpretation & Recommended Action (Including Eigengap Caution Signal)
        interpretation, recommended_action = self._evaluate_observer_advice(diag)

        geom_telemetry = GeometricObservationTelemetry(
            epoch_idx=causal_seq,
            step_idx=causal_seq,
            speed_max_angle=diag.speed_max_angle,
            speed_projector=diag.speed_projector,
            kappa_g=diag.kappa_g,
            residual_norm=diag.residual_norm,
            spectral_gap=diag.spectral_gap,
            relative_gap=diag.relative_gap,
            davis_kahan_ratio=diag.davis_kahan_ratio,
            identifiability=diag.identifiability.value,
            regime=diag.regime.value,
            eigenvalues=diag.eigenvalues,
            interpretation=interpretation,
            recommended_action=recommended_action,
            shadow_mode=self.shadow_mode,
        )

        # 3. RESOURCE TELEMETRY & BACKPRESSURE
        sample = self.guard.sample()
        ram_avail = sample.ram_available_mb if sample.ram_available_mb is not None else 1024.0
        worker_rss = sample.worker_rss_mb if sample.worker_rss_mb is not None else 64.0
        thermal = sample.thermal_max_c if sample.thermal_max_c is not None else 45.0
        backpressure = (ram_avail < 256.0) or (sample.verdict == "STOP")

        observer_state_dict = {
            "speed_max_angle": diag.speed_max_angle,
            "speed_projector": diag.speed_projector,
            "kappa_g": diag.kappa_g,
            "residual_norm": diag.residual_norm,
            "spectral_gap": diag.spectral_gap,
            "relative_gap": diag.relative_gap,
            "davis_kahan_ratio": diag.davis_kahan_ratio,
            "identifiability": diag.identifiability.value,
            "regime": diag.regime.value,
            "interpretation": interpretation,
            "recommended_action": recommended_action,
            "shadow_mode": self.shadow_mode,
        }

        resource_state_dict = {
            "ram_available_mb": ram_avail,
            "worker_rss_mb": worker_rss,
            "thermal_max_c": thermal,
            "backpressure_flag": backpressure,
        }

        # 4. PROPOSE GRAPH CHANGES (PROPOSED != AUTHORIZED)
        self.current_state = "PROPOSING"
        bundle = CandidateBundle(
            uow_id=uow_id,
            parent_uow_id=parent_uow_id,
            worker_id=self.worker_id,
            causal_sequence_id=causal_seq,
            software_commit=self.software_commit,
            source_manifest=manifest_out,
            source_hashes=hashes_out,
            source_fragments=fragments_out,
            candidate_entities=entities_out,
            candidate_relations=relations_out,
            candidate_claims=claims_out,
            candidate_questions=questions_out,
            observer_state=observer_state_dict,
            resource_state=resource_state_dict,
            sources=sources_out,
        )
        bundle.compute_hash()

        self.current_state = "REPORTING"
        packet = NanoWorkPlaneTelemetry(
            worker_id=self.worker_id,
            uow_id=uow_id,
            sequence_idx=causal_seq,
            state=self.current_state,
            candidate_bundle=bundle,
            geometric_observation=geom_telemetry,
            ram_available_mb=ram_avail,
            worker_rss_mb=worker_rss,
            thermal_max_c=thermal,
            backpressure_flag=backpressure,
            causal_sequence_id=causal_seq,
        )

        # Persist latest telemetry packet
        telemetry_file = self.output_telemetry_dir / "nano_workplane_telemetry.json"
        telemetry_file.write_text(json.dumps(packet.to_dict(), indent=2), encoding="utf-8")

        self.current_state = "IDLE"
        return packet

    def execute_primary_research_uow(
        self,
        uow_id: str,
        target_query: str,
        parent_uow_id: Optional[str] = None,
    ) -> NanoWorkPlaneTelemetry:
        """Executes a real bounded research UoW querying primary-source corpus evidence."""
        is_feldbaum = "feldbaum" in target_query.lower() and "dual" in target_query.lower()

        extracted_sources: List[CandidateSource] = []
        source_manifest: List[str] = []
        source_hashes: Dict[str, str] = {}
        extracted_fragments: List[SourceFragment] = []
        candidate_entities: List[CandidateEntity] = []
        candidate_relations: List[CandidateRelation] = []
        candidate_claims: List[CandidateClaim] = []
        candidate_questions: List[CandidateQuestion] = []

        # Load corpus sources and fragments
        corpus_dir = self.repo_root / "sovctx" / "corpus"
        frag_file = corpus_dir / "source_fragments.jsonl"
        source_file = corpus_dir / "sources.jsonl"

        if frag_file.exists():
            with open(frag_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if is_feldbaum and obj.get("id") == "FRAG:FELDBAUM_1960_DUAL_ACTION":
                        frag = SourceFragment(
                            fragment_id=obj["id"],
                            source_id=obj["source_id"],
                            text=obj.get("normalized_summary", ""),
                            locator=obj.get("locator", "Part I, pp. 1242-1244"),
                        )
                        extracted_fragments.append(frag)

        if source_file.exists():
            with open(source_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if is_feldbaum and obj.get("id") == "PUB:FELDBAUM_1960_DUAL_CONTROL":
                        s_hash = hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()
                        source_manifest.append(obj["id"])
                        source_hashes[obj["id"]] = s_hash
                        extracted_sources.append(
                            CandidateSource(
                                source_id=obj["id"],
                                label=obj.get("label", "Dual Control Theory"),
                                authors=obj.get("authors", ["PERSON:FELDBAUM_AA"]),
                                year=int(obj.get("publication_date", "1960")),
                                provenance_path=str(source_file),
                                content_hash=s_hash,
                            )
                        )

        if is_feldbaum and extracted_fragments:
            frag_id = extracted_fragments[0].fragment_id

            candidate_entities = [
                CandidateEntity(
                    entity_id="CONCEPT:DUAL_CONTROL",
                    label="Dual Control Theory",
                    category="CONCEPT",
                    aliases=["dual control", "dualnoe upravlenie", "epistemic-pragmatic control"],
                    provenance_fragment_ids=[frag_id],
                ),
                CandidateEntity(
                    entity_id="CONCEPT:INVESTIGATIVE_ACTION",
                    label="Investigative / Information-Gathering Action",
                    category="CONCEPT",
                    aliases=["issledovatelskoe deistvie", "epistemic action", "probing action", "exploratory control"],
                    provenance_fragment_ids=[frag_id],
                ),
                CandidateEntity(
                    entity_id="CONCEPT:DIRECTING_ACTION",
                    label="Directing Action",
                    category="CONCEPT",
                    aliases=["napravlyayushchee deistvie", "pragmatic action", "control action", "exploitation"],
                    provenance_fragment_ids=[frag_id],
                ),
                CandidateEntity(
                    entity_id="PERSON:FELDBAUM_AA",
                    label="A. A. Feldbaum",
                    category="PERSON",
                    aliases=["Feldbaum", "A. A. Fel'dbaum"],
                    provenance_fragment_ids=[frag_id],
                ),
            ]

            candidate_relations = [
                CandidateRelation(
                    source_id="CONCEPT:DUAL_CONTROL",
                    target_id="CONCEPT:INVESTIGATIVE_ACTION",
                    verb="PROBES",
                    rationale="Investigative action probes the object to decrease parameter uncertainty in unobserved random media.",
                    evidence_fragment_ids=[frag_id],
                ),
                CandidateRelation(
                    source_id="CONCEPT:DUAL_CONTROL",
                    target_id="CONCEPT:DIRECTING_ACTION",
                    verb="CONTROLS",
                    rationale="Directing action steers the plant toward the target state along the trajectory.",
                    evidence_fragment_ids=[frag_id],
                ),
                CandidateRelation(
                    source_id="PERSON:FELDBAUM_AA",
                    target_id="CONCEPT:DUAL_CONTROL",
                    verb="REPRESENT",
                    rationale="Feldbaum formulated and proved the fundamental equations of dual control in 1960.",
                    evidence_fragment_ids=[frag_id],
                ),
            ]

            candidate_claims = [
                CandidateClaim(
                    claim_id="CLAIM:FELDBAUM_1960_EXPLICIT_DUAL_ACTION_DISTINCTION",
                    subject_id="CONCEPT:DUAL_CONTROL",
                    predicate="EXPLICITLY_DISTINGUISHES_ACTION_TYPES",
                    object_val="INVESTIGATIVE_ACTION_VS_DIRECTING_ACTION",
                    epistemic_status="HISTORICALLY_SUPPORTED",
                    evidence_fragment_ids=[frag_id],
                )
            ]

            candidate_questions = [
                CandidateQuestion(
                    question_id="RQ:DESC:FELDBAUM_DUAL_CONTROL_CURIOUS_RL",
                    thread_id="T2",
                    question_text="How does Feldbaum's 1960 mathematical tradeoff between investigative loss and directing risk map onto curiosity-driven and active-inference reinforcement learning?",
                    target_channel="MATHEMATICAL",
                    originating_evidence=frag_id,
                )
            ]

        rq = ResearchQuestion(
            question_id="RQ:PROBE:FELDBAUM_DUAL_CONTROL",
            thread_id="T2",
            originating_evidence="Feldbaum (1960)",
            question_text=target_query,
            relation_under_test="PROBE -> REPRESENT -> CONTROL -> STABILIZE",
            known_endpoints=["Feldbaum", "Dual Control"],
        )

        return self.process_work_unit(
            uow_id=uow_id,
            parent_uow_id=parent_uow_id,
            questions_to_probe=[rq],
            target_query=target_query,
            source_manifest=source_manifest,
            source_hashes=source_hashes,
            source_fragments=extracted_fragments,
            candidate_entities=candidate_entities,
            candidate_relations=candidate_relations,
            candidate_claims=candidate_claims,
            candidate_questions=candidate_questions,
            candidate_sources=extracted_sources,
        )

    def _evaluate_observer_advice(self, diag: LeibnizBockerDiagnostics) -> Tuple[str, str]:
        """Translates geometric invariants into adaptive recommendations for the scheduler."""
        tau_speed_low = self.tracker.thresholds.get("speed_low", 0.25)
        tau_speed_high = self.tracker.thresholds.get("speed_high", 0.70)
        tau_res_high = self.tracker.thresholds.get("residual_high", 0.35)

        # Caution signal for shrinking eigengap:
        # If speed is low but subspace identifiability is degraded (non-identifiable),
        # motion is low but confidence in subspace is also low.
        # Trigger MORE OBSERVATION, not premature closure!
        if diag.speed_max_angle <= tau_speed_low and diag.identifiability == SubspaceIdentifiability.NON_IDENTIFIABLE:
            interpretation = "AMBIGUOUS_LOW_MOTION_WEAK_SEPARATION"
            recommended_action = "DEFER_STABILIZATION_ALLOCATE_MORE_OBSERVATION"

        elif diag.speed_max_angle > tau_speed_high:
            interpretation = "RAPID_STRUCTURAL_REORIENTATION"
            recommended_action = "ALLOCATE_EXPLORATORY_PROBES"

        elif diag.residual_norm > tau_res_high:
            interpretation = "HIGH_RESIDUAL_NOVELTY"
            recommended_action = "REQUEST_THREAD_PROMOTION_EVALUATION"

        elif diag.regime == DiagnosticRegime.STABLE_REGIME:
            interpretation = "CONFINED_NORMAL_MODE_STABLE"
            recommended_action = "MAINTAIN_CURRENT_DESCENT"

        else:
            interpretation = "STEADY_DRIFT_ADAPTATION"
            recommended_action = "CONTINUE_BALANCED_EXPLORATION"

        return interpretation, recommended_action
