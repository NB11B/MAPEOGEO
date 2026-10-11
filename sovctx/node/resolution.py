from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .citations import ReferenceCandidateRecord


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ReferenceResolutionAttempt:
    reference_id: str
    candidate_source_id: Optional[str] = None
    resolution_state: str = "UNRESOLVED"
    confidence: float = 0.0
    resolved_url: Optional[str] = None
    author_score: float = 0.0
    title_score: float = 0.0
    year_score: float = 0.0
    identifier_score: float = 0.0
    attempted_at: str = ""
    details_json: Optional[str] = None
    id: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _stem_russian(word: str) -> str:
    suffixes = (
        "ость", "ости", "остью", "остях",
        "ского", "скому", "ским", "ском", "ских", "скими", "ские", "ской", "ская", "ское",
        "ного", "ному", "ным", "ном", "ных", "ными", "ные", "ной", "ная", "ное",
        "того", "тому", "тым", "том", "тых", "тыми", "тые", "той", "тая", "тое",
        "ями", "ами", "ях", "ах", "ов", "ев", "ей", "ем", "ом", "ам", "ям",
        "ых", "их", "ые", "ие", "ой", "ей", "ая", "яя", "ое", "ее",
        "ы", "и", "а", "я", "у", "ю", "е", "о",
    )
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= 4:
            return word[:-len(suf)]
    return word


def _normalize_tokens(text: Optional[str]) -> set[str]:
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = set()
    for w in cleaned.split():
        if len(w) > 1:
            tokens.add(_stem_russian(w))
    return tokens


def _compute_jaccard(tokens1: set[str], tokens2: set[str]) -> float:
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union) if union else 0.0


def score_author_match(ref_authors: list[str], target_authors: list[str]) -> float:
    if not ref_authors or not target_authors:
        return 0.0

    # Extract surnames
    def _surnames(names: list[str]) -> set[str]:
        res: set[str] = set()
        for name in names:
            parts = [p.strip(" .") for p in name.split() if len(p.strip(" .")) > 1]
            if parts:
                res.add(parts[0].lower())
        return res

    ref_s = _surnames(ref_authors)
    tgt_s = _surnames(target_authors)
    if not ref_s or not tgt_s:
        return 0.0
    return len(ref_s.intersection(tgt_s)) / len(ref_s)


def score_title_match(ref_title: Optional[str], target_title: Optional[str]) -> float:
    t1 = _normalize_tokens(ref_title)
    t2 = _normalize_tokens(target_title)
    if not t1 or not t2:
        return 0.0
    jaccard = _compute_jaccard(t1, t2)
    containment = len(t1.intersection(t2)) / min(len(t1), len(t2))
    return round(0.5 * jaccard + 0.5 * containment, 3)


def score_year_match(ref_year: Optional[int], target_year: Optional[int]) -> float:
    if ref_year is None or target_year is None:
        return 0.0
    diff = abs(ref_year - target_year)
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.5
    elif diff >= 5:
        return -1.0
    return 0.0


def score_identifier_match(ref_id: Optional[str], target_id: Optional[str]) -> float:
    if not ref_id or not target_id:
        return 0.0
    norm_ref = ref_id.strip().lower()
    norm_tgt = target_id.strip().lower()
    return 1.0 if norm_ref == norm_tgt else -1.0


def resolve_reference(
    reference: ReferenceCandidateRecord,
    candidate_sources: list[dict[str, Any]],
) -> ReferenceResolutionAttempt:
    """Resolve a reference candidate against a pool of candidate sources with strict identifier dominance."""
    attempted_at = utc_now_iso()

    if not candidate_sources:
        return ReferenceResolutionAttempt(
            reference_id=reference.id,
            candidate_source_id=None,
            resolution_state="NOT_PUBLICLY_LOCATED",
            confidence=0.0,
            resolved_url=None,
            attempted_at=attempted_at,
            details_json=json.dumps({"reason": "empty_candidate_pool"}),
        )

    ref_authors = reference.authors_list()
    scored_candidates: list[tuple[float, dict[str, Any], dict[str, float]]] = []

    for cand in candidate_sources:
        cand_id = cand.get("id") or cand.get("source_id")
        cand_url = cand.get("url") or cand.get("source_url")
        cand_title = cand.get("title")
        cand_authors = cand.get("authors") or []
        if isinstance(cand_authors, str):
            try:
                cand_authors = json.loads(cand_authors)
            except Exception:
                cand_authors = [cand_authors]
        cand_year = cand.get("year")
        cand_identifier = cand.get("identifier") or cand.get("doi") or cand.get("mathnet_id")

        i_score = score_identifier_match(reference.identifier_raw, cand_identifier)
        a_score = score_author_match(ref_authors, cand_authors)
        t_score = score_title_match(reference.title_raw, cand_title)
        y_score = score_year_match(reference.year_raw, cand_year)
        p_score = 0.8 if reference.publication_raw and cand.get("publication") and reference.publication_raw.lower() in cand.get("publication", "").lower() else 0.0

        # Exact identifier dominance rule:
        # If exact identifier matches, confidence is immediately >= 0.95
        if i_score == 1.0:
            total_conf = 0.95 + 0.05 * max(a_score, t_score)
        elif i_score == -1.0:
            # Conflicting persistent identifier: hard contradiction
            total_conf = 0.0
        elif y_score < 0:
            # Year divergence >= 5 years without identifier cannot match
            total_conf = 0.15 * max(0.0, a_score)
        else:
            # Weighted resolution formula: C_resolve = 0.35 A + 0.35 T + 0.20 Y + 0.10 P
            total_conf = (0.35 * a_score) + (0.35 * t_score) + (0.20 * y_score) + (0.10 * p_score)

        breakdown = {
            "author_score": round(a_score, 3),
            "title_score": round(t_score, 3),
            "year_score": round(y_score, 3),
            "identifier_score": round(i_score, 3),
            "publication_score": round(p_score, 3),
        }
        scored_candidates.append((round(total_conf, 3), cand, breakdown))

    # Sort descending by confidence
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    best_conf, best_cand, best_breakdown = scored_candidates[0]

    # Check for conflicting matches if top 2 are both high and close
    if len(scored_candidates) > 1:
        second_conf, _, _ = scored_candidates[1]
        if best_conf >= 0.70 and second_conf >= 0.70 and abs(best_conf - second_conf) < 0.05:
            return ReferenceResolutionAttempt(
                reference_id=reference.id,
                candidate_source_id=best_cand.get("id"),
                resolution_state="CONFLICTING_MATCHES",
                confidence=best_conf,
                resolved_url=best_cand.get("url") or best_cand.get("source_url"),
                author_score=best_breakdown["author_score"],
                title_score=best_breakdown["title_score"],
                year_score=best_breakdown["year_score"],
                identifier_score=best_breakdown["identifier_score"],
                attempted_at=attempted_at,
                details_json=json.dumps({"top_two_scores": [best_conf, second_conf]}),
            )

    # State thresholds
    if best_conf >= 0.90 or best_breakdown["identifier_score"] == 1.0:
        state = "EXACT_MATCH"
    elif best_conf >= 0.70:
        state = "PROBABLE_MATCH"
    elif best_conf >= 0.45:
        state = "PARTIAL_MATCH"
    else:
        state = "UNRESOLVED"

    return ReferenceResolutionAttempt(
        reference_id=reference.id,
        candidate_source_id=best_cand.get("id"),
        resolution_state=state,
        confidence=best_conf,
        resolved_url=best_cand.get("url") or best_cand.get("source_url"),
        author_score=best_breakdown["author_score"],
        title_score=best_breakdown["title_score"],
        year_score=best_breakdown["year_score"],
        identifier_score=best_breakdown["identifier_score"],
        attempted_at=attempted_at,
        details_json=json.dumps(best_breakdown),
    )
