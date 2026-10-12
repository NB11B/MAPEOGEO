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
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from sovctx.node.guard import ResourceGuard
from sovctx.node.leibniz_bocker import (
    DiagnosticRegime,
    LeibnizBockerDiagnostics,
    LeibnizBockerTracker,
    SubspaceIdentifiability,
)
from sovctx.node.research_question import QuestionStatus, ResearchQuestion


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
class CandidateRelation:
    """Proposed relationship between nodes awaiting control plane admission."""
    source_id: str
    target_id: str
    verb: str  # One of normalized verbs: STABILIZE, CONTROL, INVERT, etc.
    rationale: str
    evidence_fragment_ids: List[str]


@dataclass
class CandidateQuestion:
    """Proposed open research question formulated from anomalies or bridges."""
    question_id: str
    thread_id: str
    question_text: str
    target_channel: str
    originating_evidence: str


@dataclass
class CandidateBundle:
    """Proposed graph modifications emitted by the research work plane.
    
    Invariant: PROPOSED != AUTHORIZED. The Nano never writes directly to canonical state.
    """
    uow_id: str
    parent_uow_id: Optional[str]
    sequence_idx: int
    sources: List[CandidateSource] = field(default_factory=list)
    relations: List[CandidateRelation] = field(default_factory=list)
    questions: List[CandidateQuestion] = field(default_factory=list)
    content_hash: str = ""

    def compute_hash(self) -> str:
        payload = json.dumps(
            {
                "uow_id": self.uow_id,
                "sources": [asdict(s) for s in self.sources],
                "relations": [asdict(r) for r in self.relations],
                "questions": [asdict(q) for q in self.questions],
            },
            sort_keys=True,
        )
        self.content_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return self.content_hash


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
            "STABILIZE", "CONTROL", "INVERT", "CONSTRAIN",
            "PROBE", "REPRESENT", "OBSERVE", "UPDATE", "ADAPT", "REGULARIZE",
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
    ) -> None:
        self.worker_id = worker_id
        self.shadow_mode = shadow_mode
        self.output_telemetry_dir = output_telemetry_dir
        self.output_telemetry_dir.mkdir(parents=True, exist_ok=True)

        self.guard = ResourceGuard()
        self.tracker = LeibnizBockerTracker(k=tracker_k, alpha=tracker_alpha, dt=1.0)
        self.state_history: List[np.ndarray] = []
        self.sequence_idx = 0
        self.current_state = "IDLE"

    def process_work_unit(
        self,
        uow_id: str,
        parent_uow_id: Optional[str],
        questions_to_probe: List[ResearchQuestion],
        simulated_discoveries: Optional[Dict[str, Any]] = None,
    ) -> NanoWorkPlaneTelemetry:
        """Executes a bounded research work unit and returns proposed candidates + telemetry."""
        self.sequence_idx += 1
        causal_seq = self.sequence_idx

        # 1. ACQUIRE & EXTRACT & RELATE & PROBE
        self.current_state = "PROBING"
        thread_counts: Dict[str, int] = {f"T{i}": 0 for i in range(1, 13)}
        verb_counts: Dict[str, int] = {}
        candidate_sources: List[CandidateSource] = []
        candidate_relations: List[CandidateRelation] = []
        candidate_questions: List[CandidateQuestion] = []

        max_depth = 0
        bridge_count = 0

        for q in questions_to_probe:
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
            for v in ["STABILIZE", "CONTROL", "INVERT", "CONSTRAIN", "OBSERVE", "REPRESENT"]:
                if v in q.relation_under_test:
                    verb_counts[v] = verb_counts.get(v, 0) + 1

        # Process any simulated discoveries / extractions passed to the work unit
        if simulated_discoveries:
            for s in simulated_discoveries.get("sources", []):
                candidate_sources.append(
                    CandidateSource(
                        source_id=s["id"],
                        label=s["label"],
                        authors=s.get("authors", []),
                        year=s.get("year", 1960),
                        provenance_path=s.get("path", ""),
                        content_hash=hashlib.sha256(s["id"].encode()).hexdigest(),
                    )
                )
            for r in simulated_discoveries.get("relations", []):
                candidate_relations.append(
                    CandidateRelation(
                        source_id=r["source"],
                        target_id=r["target"],
                        verb=r["verb"],
                        rationale=r.get("rationale", ""),
                        evidence_fragment_ids=r.get("fragments", []),
                    )
                )
            for q_new in simulated_discoveries.get("questions", []):
                candidate_questions.append(
                    CandidateQuestion(
                        question_id=q_new["id"],
                        thread_id=q_new["thread_id"],
                        question_text=q_new["text"],
                        target_channel=q_new.get("channel", "MATHEMATICAL"),
                        originating_evidence=q_new.get("origin", ""),
                    )
                )

        # 2. PROPOSE GRAPH CHANGES (PROPOSED != AUTHORIZED)
        self.current_state = "PROPOSING"
        bundle = CandidateBundle(
            uow_id=uow_id,
            parent_uow_id=parent_uow_id,
            sequence_idx=causal_seq,
            sources=candidate_sources,
            relations=candidate_relations,
            questions=candidate_questions,
        )
        bundle.compute_hash()

        # 3. G1 GEOMETRIC OBSERVER (Self-Observation)
        self.current_state = "OBSERVING"
        state_vec = ResearchStateVectorBuilder.build_vector(
            thread_counts=thread_counts,
            verb_counts=verb_counts,
            bridge_count=bridge_count,
            max_descendant_depth=max_depth,
            institution_counts={"Steklov": 2, "IAT": 3},
            question_type_counts={
                "spines": max(0, len(questions_to_probe) - bridge_count),
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

        # 4. RESOURCE TELEMETRY & BACKPRESSURE
        sample = self.guard.sample()
        ram_avail = sample.ram_available_mb if sample.ram_available_mb is not None else 1024.0
        worker_rss = sample.worker_rss_mb if sample.worker_rss_mb is not None else 64.0
        thermal = sample.thermal_max_c if sample.thermal_max_c is not None else 45.0
        backpressure = (ram_avail < 256.0) or (sample.verdict == "STOP")

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
