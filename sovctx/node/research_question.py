"""SOVCTX Autonomous Research Frontier: Research Question & Thread Model.

Implements the fundamental paradigm shift:
    "The frontier item should be a research question, not a target answer."

Provides:
1. Nine canonical Thread Families (T1 through T9) + dynamic spawned threads (T10+).
2. First-class RESEARCH_QUESTION object with Open-Question Ledger.
3. Priority scoring formula: P = N + B + E + I + G - D.
4. Institutional transport channels vs citation transfer.
5. Autonomous evidence-driven branching engine (5 triggers).
6. Saturation detector: Delta new independent relations -> 0.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 1. Institutional Transport Channels
# ---------------------------------------------------------------------------

class InstitutionalChannelType(str, Enum):
    """Distinguishes the historical mechanism by which mathematical methods travel."""
    DOCUMENTED_CITATION_TRANSFER = "DOCUMENTED_CITATION_TRANSFER"
    PERSONNEL_TRANSFER = "PERSONNEL_TRANSFER"                    # Students, advisors, lab moves
    INSTITUTIONAL_CONTINUITY = "INSTITUTIONAL_CONTINUITY"        # Same institute / state program
    STRUCTURAL_MATHEMATICAL_CONTINUITY = "STRUCTURAL_MATHEMATICAL_CONTINUITY" # Parallel methods without admin tie


# ---------------------------------------------------------------------------
# 2. Canonical Thread Families T1 - T9
# ---------------------------------------------------------------------------

class ThreadFamilyId(str, Enum):
    T1 = "T1"  # Relational mathematical ancestry
    T2 = "T2"  # Stability -> control
    T3 = "T3"  # Observation -> inverse reconstruction
    T4 = "T4"  # Collective state -> reduced dynamics
    T5 = "T5"  # Approximation -> finite computation
    T6 = "T6"  # Adaptive/cybernetic organization
    T7 = "T7"  # Institutional transmission
    T8 = "T8"  # Native terminology evolution
    T9 = "T9"  # Anomaly / unknown frontier


@dataclass
class ThreadFamily:
    """An independent research thread family governed by specific starting spines and negative bounds."""
    thread_id: str
    name: str
    starting_region: str
    follow_targets: List[str]
    negative_presumptions: List[str]
    status: str = "ACTIVE"  # ACTIVE | SATURATED | PROBING | DORMANT
    is_dynamically_spawned: bool = False
    spawn_trigger: Optional[str] = None
    spawn_rationale: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


CANONICAL_THREAD_FAMILIES: Dict[str, ThreadFamily] = {
    "T1": ThreadFamily(
        thread_id="T1",
        name="Relational mathematical ancestry",
        starting_region="Leibniz -> Euler -> St. Petersburg -> Chebyshev/Markov/Lyapunov",
        follow_targets=[
            "citations", "translations", "academy lineages",
            "terminology", "operator formulations", "relational structures"
        ],
        negative_presumptions=[
            "Do NOT presume that Leibniz directly caused Soviet mathematics."
        ],
    ),
    "T2": ThreadFamily(
        thread_id="T2",
        name="Stability -> control",
        starting_region="Lyapunov -> Andronov -> Pontryagin -> Krasovskii",
        follow_targets=[
            "perturbation", "stability", "admissibility",
            "feedback", "trajectory", "regulation"
        ],
        negative_presumptions=[
            "Do NOT presume that aerospace was the inevitable endpoint."
        ],
    ),
    "T3": ThreadFamily(
        thread_id="T3",
        name="Observation -> inverse reconstruction",
        starting_region="Gelfand/Levitan -> Tikhonov -> Faddeev",
        follow_targets=[
            "inverse operators", "measurement", "regularization",
            "spectral recovery", "indirect sensing"
        ],
        negative_presumptions=[
            "Do NOT presume that radar/geophysics are the only applications."
        ],
    ),
    "T4": ThreadFamily(
        thread_id="T4",
        name="Collective state -> reduced dynamics",
        starting_region="Vlasov -> Bogolyubov -> Shafranov",
        follow_targets=[
            "distributions", "hierarchy reduction", "self-consistent fields",
            "collective variables", "equilibrium"
        ],
        negative_presumptions=[
            "Do NOT presume that plasma is the only descendant."
        ],
    ),
    "T5": ThreadFamily(
        thread_id="T5",
        name="Approximation -> finite computation",
        starting_region="Chebyshev -> Markov -> numerical schools -> BESM",
        follow_targets=[
            "minimax", "global error", "polynomial/rational representation",
            "numerical algorithms", "constructive function theory"
        ],
        negative_presumptions=[
            "Do NOT presume that computing is the principal destination."
        ],
    ),
    "T6": ThreadFamily(
        thread_id="T6",
        name="Adaptive/cybernetic organization",
        starting_region="Bernstein, Anokhin, Tsetlin, Gelfand, Glushkov",
        follow_targets=[
            "feedback", "functional systems", "non-local search",
            "hierarchy", "prediction", "adaptive control"
        ],
        negative_presumptions=[
            "Do NOT presume that these are ancestors of modern AI."
        ],
    ),
    "T7": ThreadFamily(
        thread_id="T7",
        name="Institutional transmission",
        starting_region="MIAN, LOMI, MSU, IPM, Kharkiv, JINR, Kyiv, design institutes",
        follow_targets=[
            "seminars", "students", "transfers", "laboratories",
            "journals", "translated works", "funding/programs"
        ],
        negative_presumptions=[
            "Do NOT presume that intellectual lineage follows institutional lineage."
        ],
    ),
    "T8": ThreadFamily(
        thread_id="T8",
        name="Native terminology evolution",
        starting_region="Russian mathematical and engineering vocabulary (оператор, устойчивость, грубость, инвариант, допустимость, обратная задача, регуляризация)",
        follow_targets=[
            "spelling change", "semantic drift", "co-occurrence",
            "definitions", "translation changes"
        ],
        negative_presumptions=[
            "Do NOT presume that the modern English translation preserves the historical concept."
        ],
    ),
    "T9": ThreadFamily(
        thread_id="T9",
        name="Anomaly / unknown frontier",
        starting_region="Anything that fails existing categories",
        follow_targets=[
            "unexplained recurrent relations", "contradictions", "unusual equipment",
            "unknown people", "abandoned terminology", "unexpected cross-domain bridges"
        ],
        negative_presumptions=[
            "Do NOT presume anything at all (pure discovery reserve)."
        ],
    ),
}


# ---------------------------------------------------------------------------
# 3. Question Status & First-Class RESEARCH_QUESTION
# ---------------------------------------------------------------------------

class QuestionStatus(str, Enum):
    OPEN = "OPEN"
    PROBING = "PROBING"
    RESOLVED = "RESOLVED"
    SATURATED = "SATURATED"
    CONTRADICTED = "CONTRADICTED"


@dataclass
class PriorityComponents:
    """Components of the priority scoring formula: P = N + B + E + I + G - D."""
    novelty: float = 0.5                  # N: [0.0, 1.0]
    bridge_potential: float = 0.5         # B: [0.0, 1.0]
    evidentiary_quality: float = 0.5      # E: [0.0, 1.0]
    corroboration_potential: float = 0.5  # I: [0.0, 1.0]
    historical_gap_value: float = 0.5     # G: [0.0, 1.0]
    duplication_penalty: float = 0.0      # D: [0.0, 1.0]

    @property
    def total_score(self) -> float:
        score = (
            self.novelty
            + self.bridge_potential
            + self.evidentiary_quality
            + self.corroboration_potential
            + self.historical_gap_value
            - self.duplication_penalty
        )
        return round(max(0.0, score), 4)

    def to_dict(self) -> Dict[str, float]:
        d = asdict(self)
        d["total_score"] = self.total_score
        return d


@dataclass
class ResearchQuestion:
    """A first-class research question defining what unanswered relationship to probe."""
    question_id: str
    thread_id: str
    originating_evidence: str
    question_text: str
    relation_under_test: str
    known_endpoints: List[str]
    unknown_endpoint: bool = True
    temporal_window: str = "1930-1975"
    priority_components: PriorityComponents = field(default_factory=PriorityComponents)
    priority: float = 0.0
    independent_support: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    status: QuestionStatus = QuestionStatus.OPEN
    generation: int = 0
    target_channel: InstitutionalChannelType = InstitutionalChannelType.DOCUMENTED_CITATION_TRANSFER
    resolved_endpoint: Optional[str] = None
    resolution_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = QuestionStatus(self.status)
        if isinstance(self.target_channel, str):
            self.target_channel = InstitutionalChannelType(self.target_channel)
        if self.priority == 0.0 and self.priority_components:
            self.priority = self.priority_components.total_score

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["target_channel"] = self.target_channel.value
        d["priority_components"] = self.priority_components.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResearchQuestion:
        payload = dict(data)
        if "priority_components" in payload and isinstance(payload["priority_components"], dict):
            p_dict = dict(payload["priority_components"])
            p_dict.pop("total_score", None)
            payload["priority_components"] = PriorityComponents(**p_dict)
        if "status" in payload and isinstance(payload["status"], str):
            payload["status"] = QuestionStatus(payload["status"])
        if "target_channel" in payload and isinstance(payload["target_channel"], str):
            payload["target_channel"] = InstitutionalChannelType(payload["target_channel"])
        return cls(**payload)


# ---------------------------------------------------------------------------
# 4. Open-Question Ledger
# ---------------------------------------------------------------------------

class OpenQuestionLedger:
    """Maintains and indexes all active, probing, and resolved research questions."""

    def __init__(self) -> None:
        self.questions: Dict[str, ResearchQuestion] = {}
        self.threads: Dict[str, ThreadFamily] = dict(CANONICAL_THREAD_FAMILIES)

    def add_question(self, q: ResearchQuestion) -> None:
        self.questions[q.question_id] = q

    def get_question(self, qid: str) -> Optional[ResearchQuestion]:
        return self.questions.get(qid)

    def get_by_thread(self, thread_id: str, status: Optional[QuestionStatus] = None) -> List[ResearchQuestion]:
        qs = [q for q in self.questions.values() if q.thread_id == thread_id]
        if status is not None:
            qs = [q for q in qs if q.status == status]
        return sorted(qs, key=lambda x: x.priority, reverse=True)

    def get_open_questions(self, limit: Optional[int] = None) -> List[ResearchQuestion]:
        open_qs = [
            q for q in self.questions.values()
            if q.status in (QuestionStatus.OPEN, QuestionStatus.PROBING)
        ]
        open_qs.sort(key=lambda x: x.priority, reverse=True)
        if limit is not None:
            return open_qs[:limit]
        return open_qs

    def resolve_question(
        self,
        qid: str,
        resolved_endpoint: str,
        summary: str,
        support_source: str,
    ) -> bool:
        q = self.questions.get(qid)
        if not q:
            return False
        q.status = QuestionStatus.RESOLVED
        q.resolved_endpoint = resolved_endpoint
        q.resolution_summary = summary
        if support_source not in q.independent_support:
            q.independent_support.append(support_source)
        q.updated_at = utc_now_iso()
        return True

    def record_corroboration(self, qid: str, source_id: str) -> bool:
        q = self.questions.get(qid)
        if not q:
            return False
        if source_id not in q.independent_support:
            q.independent_support.append(source_id)
            q.priority_components.corroboration_potential = min(
                1.0, q.priority_components.corroboration_potential + 0.15
            )
            q.priority = q.priority_components.total_score
            q.updated_at = utc_now_iso()
        return True

    def record_contradiction(self, qid: str, contradiction_text: str) -> bool:
        q = self.questions.get(qid)
        if not q:
            return False
        q.contradictions.append(contradiction_text)
        q.status = QuestionStatus.CONTRADICTED
        q.updated_at = utc_now_iso()
        return True


# ---------------------------------------------------------------------------
# 5. Autonomous Evidence-Driven Branching Engine
# ---------------------------------------------------------------------------

class BranchingTrigger(str, Enum):
    NEW_RECURRING_RELATION = "NEW_RECURRING_RELATION"
    NEW_CROSS_DOMAIN_BRIDGE = "NEW_CROSS_DOMAIN_BRIDGE"
    NEW_INSTITUTIONAL_BRIDGE = "NEW_INSTITUTIONAL_BRIDGE"
    NEW_CONTRADICTION = "NEW_CONTRADICTION"
    NEW_NATIVE_CONCEPT = "NEW_NATIVE_CONCEPT"
    GEOMETRIC_NOVELTY = "GEOMETRIC_NOVELTY"
    SPECTRAL_REORIENTATION = "SPECTRAL_REORIENTATION"
    SPECTRAL_GAP_COLLAPSE = "SPECTRAL_GAP_COLLAPSE"


class AutonomousBranchingEngine:
    """Spawns new thread families (T10, T11, ...) when evidence demonstrates recurring novelty."""

    def __init__(self, ledger: OpenQuestionLedger) -> None:
        self.ledger = ledger
        self.spawn_counter = 9  # T1 through T9 exist

    def evaluate_branching(
        self,
        trigger: BranchingTrigger,
        label: str,
        starting_region: str,
        follow_targets: List[str],
        rationale: str,
    ) -> ThreadFamily:
        self.spawn_counter += 1
        new_tid = f"T{self.spawn_counter}_{label.upper().replace(' ', '_')[:24]}"

        new_thread = ThreadFamily(
            thread_id=new_tid,
            name=f"{label} (Spawned via {trigger.value})",
            starting_region=starting_region,
            follow_targets=follow_targets,
            negative_presumptions=[
                f"Do NOT presume pre-determined destination for {label}. Let the graph topology decide."
            ],
            status="ACTIVE",
            is_dynamically_spawned=True,
            spawn_trigger=trigger.value,
            spawn_rationale=rationale,
        )

        self.ledger.threads[new_tid] = new_thread
        return new_thread


# ---------------------------------------------------------------------------
# 6. Thread Saturation Detector
# ---------------------------------------------------------------------------

@dataclass
class ThreadSaturationState:
    thread_id: str
    recent_acquisitions: int
    duplicate_relations: int
    new_relations: int
    is_saturated: bool
    new_relation_ratio: float
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ThreadSaturationDetector:
    """Monitors whether Delta new independent relations -> 0 even if Delta documents > 0."""

    @classmethod
    def evaluate_thread_saturation(
        cls,
        thread_id: str,
        recent_acquisitions: int,
        duplicate_relations: int,
        new_relations: int,
        min_acquisitions_threshold: int = 20,
        min_new_relation_ratio: float = 0.05,
    ) -> ThreadSaturationState:
        if recent_acquisitions < min_acquisitions_threshold:
            return ThreadSaturationState(
                thread_id=thread_id,
                recent_acquisitions=recent_acquisitions,
                duplicate_relations=duplicate_relations,
                new_relations=new_relations,
                is_saturated=False,
                new_relation_ratio=round(new_relations / float(max(1, recent_acquisitions)), 4),
                recommendation="CONTINUE_SAMPLING: Insufficient acquisition window to judge saturation.",
            )

        ratio = new_relations / float(recent_acquisitions)
        is_sat = ratio < min_new_relation_ratio

        rec = (
            f"SATURATED: Only {new_relations}/{recent_acquisitions} ({ratio*100:.1f}%) new relations found. "
            f"Reallocate acquisition budget toward cross-thread bridges or anomalous frontier."
            if is_sat
            else f"ACTIVE_DISCOVERY: {ratio*100:.1f}% new relation yield exceeds threshold."
        )

        return ThreadSaturationState(
            thread_id=thread_id,
            recent_acquisitions=recent_acquisitions,
            duplicate_relations=duplicate_relations,
            new_relations=new_relations,
            is_saturated=is_sat,
            new_relation_ratio=round(ratio, 4),
            recommendation=rec,
        )
