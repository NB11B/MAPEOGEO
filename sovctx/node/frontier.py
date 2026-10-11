from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .calibration import is_negative_control_phrase
from .entities import is_institution_entity


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Frontier Classes F0 - F9
# ---------------------------------------------------------------------------

FRONTIER_CLASSES = {
    "F0_CITATION_DIRECT": "Direct citation resolution from references",
    "F1_AUTHOR_BIBLIOGRAPHY": "Author bibliography expansion",
    "F2_INSTITUTION_VENUE": "Core Soviet institutional venues and journals",
    "F3_NATIVE_TERMINOLOGY": "Native Russian terminology frontier (F(t) >= 0.65)",
    "F4_EQUATION_FAMILY": "Equation and invariant families",
    "F5_METHOD_OPERATOR": "Method and operator expansion",
    "F6_ARCHIVAL_SCAN": "Archival/physical scan acquisition",
    "F7_BIBLIOGRAPHIC_VERIFICATION": "Bibliographic verification targets",
    "F8_CALIBRATION_PROBE": "Calibration and negative control probes",
    "F9_SEED_DISCOVERY": "Seed and ad-hoc discovery",
}


def make_dedup_key(
    frontier_type: str,
    normalized_target: str,
    namespace: str = "sovctx",
) -> str:
    """Deterministic deduplication key preventing duplicate frontier items and recursive loops: K = H(type || target || ns)."""
    preimage = f"{frontier_type.strip().upper()}\0{normalized_target.strip().lower()}\0{namespace.strip().lower()}"
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


def make_frontier_id(dedup_key: str) -> str:
    """Generate deterministic frontier item ID bound to dedup_key."""
    return f"SOVFRONT:{dedup_key[:20]}"


def make_nomination_id(frontier_id: str, nominated_url: str) -> str:
    """Generate deterministic source nomination ID."""
    preimage = f"{frontier_id}\0{nominated_url.strip()}"
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:20]
    return f"SOVNOM:{digest}"


@dataclass
class FrontierItemRecord:
    id: str
    frontier_type: str
    priority: str
    dedup_key: str
    target_label: str
    normalized_target: str
    origin_source_id: str
    origin_passage_id: Optional[str] = None
    raw_support_count: int = 1
    independent_source_count: int = 1
    status: str = "OPEN"
    attempt_count: int = 0
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FrontierEvidenceRecord:
    frontier_id: str
    evidence_type: str  # CITATION, TERM, ENTITY, EQUATION
    evidence_id: str
    source_id: str
    passage_id: Optional[str] = None
    weight: float = 1.0
    observed_at: str = field(default_factory=utc_now_iso)
    id: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceNominationRecord:
    id: str
    frontier_id: str
    nominated_url: str
    goal: str
    priority: str = "P1"
    nomination_reason: str = "frontier_expansion"
    nominated_at: str = field(default_factory=utc_now_iso)
    status: str = "PENDING"
    acquired_source_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TerminologyFrontierScore:
    score: float
    r_score: float  # Repetition across independent sources
    d_score: float  # Definition witness
    e_score: float  # Equation co-occurrence
    s_score: float  # Technicality
    h_score: float  # Historical orthography
    i_score: float  # Institutional diversity
    qualifies_for_frontier: bool
    is_negative_control: bool
    explanation: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_terminology_frontier_score(
    term: str,
    independent_source_count: int,
    occurs_in_definition: bool,
    near_equation: bool,
    technicality_score: float,
    has_historical_orthography: bool = False,
    institutions_count: int = 0,
) -> TerminologyFrontierScore:
    """Compute conservative evidence-weighted terminology score: F(t) = w1*R + w2*D + w3*E + w4*S + w5*H + w6*I."""
    explanation: list[str] = []

    # Negative control check: generic conversational phrases must score < 0.30
    if is_negative_control_phrase(term):
        return TerminologyFrontierScore(
            score=0.15,
            r_score=0.0,
            d_score=0.0,
            e_score=0.0,
            s_score=0.15,
            h_score=0.0,
            i_score=0.0,
            qualifies_for_frontier=False,
            is_negative_control=True,
            explanation=["negative_control_discourse_phrase_rejected"],
        )

    # 1. R: Repetition across independent sources (normalized, min 1, target 2+)
    r_score = min(1.0, max(0.0, independent_source_count / 2.0))
    if independent_source_count >= 2:
        explanation.append(f"repeated_in_{independent_source_count}_independent_sources")

    # 2. D: Definition presence
    d_score = 1.0 if occurs_in_definition else 0.0
    if occurs_in_definition:
        explanation.append("witnessed_in_formal_definition")

    # 3. E: Equation co-occurrence
    e_score = 1.0 if near_equation else 0.0
    if near_equation:
        explanation.append("co_occurs_with_equation_witness")

    # 4. S: Technicality score
    s_score = max(0.0, min(1.0, technicality_score))
    explanation.append(f"technicality_{s_score:.2f}")

    # 5. H: Historical orthography
    h_score = 1.0 if has_historical_orthography else 0.0
    if has_historical_orthography:
        explanation.append("historical_orthography_witnessed")

    # 6. I: Institutional diversity
    i_score = min(1.0, max(0.0, institutions_count / 2.0))
    if institutions_count > 0:
        explanation.append(f"associated_with_{institutions_count}_institutions")

    # Weights: w1=0.25, w2=0.20, w3=0.15, w4=0.20, w5=0.10, w6=0.10 (Sum = 1.00)
    score = (
        (0.25 * r_score)
        + (0.20 * d_score)
        + (0.15 * e_score)
        + (0.20 * s_score)
        + (0.10 * h_score)
        + (0.10 * i_score)
    )
    score = round(score, 3)

    # Strict conservative qualification threshold: F(t) >= 0.65
    qualifies = score >= 0.65

    return TerminologyFrontierScore(
        score=score,
        r_score=round(r_score, 3),
        d_score=round(d_score, 3),
        e_score=round(e_score, 3),
        s_score=round(s_score, 3),
        h_score=round(h_score, 3),
        i_score=round(i_score, 3),
        qualifies_for_frontier=qualifies,
        is_negative_control=False,
        explanation=explanation,
    )
