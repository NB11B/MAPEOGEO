from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .resolution import _normalize_tokens, _compute_jaccard, score_author_match, score_title_match, score_year_match


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_CYR_LAT_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _transliterate_cyrillic(text: str) -> str:
    return "".join(_CYR_LAT_MAP.get(c, c) for c in text.lower())


FAMILY_RELATIONSHIPS = (
    "IDENTICAL_BLOB",
    "SAME_SCAN",
    "SAME_EDITION",
    "SAME_WORK",
    "TRANSLATION_OF",
    "DERIVED_FROM",
    "UNKNOWN_RELATION",
)


@dataclass
class SourceFamilyRelation:
    source_id_a: str
    source_id_b: str
    relationship: str
    confidence: float
    details: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkFamilyCluster:
    canonical_work_id: str
    canonical_title: str
    primary_authors: list[str]
    member_source_ids: list[str] = field(default_factory=list)
    member_relationships: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceFamilyClassifier:
    """Classifies relationships between acquired sources to prevent duplicate editions or mirror scans from distorting support counts."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def classify_pair(self, s1: dict[str, Any], s2: dict[str, Any]) -> SourceFamilyRelation:
        id_a = s1.get("id") or s1.get("source_id", "")
        id_b = s2.get("id") or s2.get("source_id", "")
        sha_a = s1.get("sha256", "")
        sha_b = s2.get("sha256", "")

        # 1. Identical Blob
        if sha_a and sha_b and sha_a == sha_b:
            return SourceFamilyRelation(
                source_id_a=id_a,
                source_id_b=id_b,
                relationship="IDENTICAL_BLOB",
                confidence=1.0,
                details={"reason": "exact_sha256_match", "sha256": sha_a},
            )

        title_a = s1.get("title", "")
        title_b = s2.get("title", "")
        authors_a = s1.get("authors") or []
        authors_b = s2.get("authors") or []
        year_a = s1.get("year")
        year_b = s2.get("year")
        lang_a = s1.get("language", "ru")
        lang_b = s2.get("language", "ru")

        # 2. Check for Translation
        # If one is Russian and one is English/Latin, with matching author surnames and title semantics
        is_trans = False
        if (lang_a == "ru" and lang_b == "en") or (lang_a == "en" and lang_b == "ru"):
            ru_authors = authors_a if lang_a == "ru" else authors_b
            en_authors = authors_b if lang_a == "ru" else authors_a
            ru_translit = [_transliterate_cyrillic(a) for a in ru_authors]
            a_score = score_author_match(ru_translit, en_authors)
            if a_score >= 0.8:
                return SourceFamilyRelation(
                    source_id_a=id_a,
                    source_id_b=id_b,
                    relationship="TRANSLATION_OF",
                    confidence=0.92,
                    details={"languages": [lang_a, lang_b], "author_score": a_score},
                )

        t_score = score_title_match(title_a, title_b)
        a_score = score_author_match(authors_a, authors_b)
        y_diff = abs(year_a - year_b) if (year_a is not None and year_b is not None) else None

        # 3. Same Scan (high text signature overlap + same title/author/year)
        text_jaccard = 0.0
        txt_a = s1.get("sample_text", "")
        txt_b = s2.get("sample_text", "")
        if txt_a and txt_b:
            tok_a = _normalize_tokens(txt_a)
            tok_b = _normalize_tokens(txt_b)
            text_jaccard = _compute_jaccard(tok_a, tok_b)

        if text_jaccard >= 0.90:
            return SourceFamilyRelation(
                source_id_a=id_a,
                source_id_b=id_b,
                relationship="SAME_SCAN",
                confidence=round(text_jaccard, 3),
                details={"text_jaccard": round(text_jaccard, 3)},
            )

        # 4. Same Edition: high title + high author + same year
        if a_score >= 0.80 and t_score >= 0.85 and y_diff == 0:
            return SourceFamilyRelation(
                source_id_a=id_a,
                source_id_b=id_b,
                relationship="SAME_EDITION",
                confidence=0.95,
                details={"title_score": t_score, "author_score": a_score, "year_diff": 0},
            )

        # 5. Same Work: high title + high author + different year (reprint, subsequent edition)
        if a_score >= 0.80 and t_score >= 0.80:
            return SourceFamilyRelation(
                source_id_a=id_a,
                source_id_b=id_b,
                relationship="SAME_WORK",
                confidence=0.90,
                details={"title_score": t_score, "author_score": a_score, "year_diff": y_diff},
            )

        # 6. Derived From (title containment or textbook excerpt)
        if a_score >= 0.50 and t_score >= 0.50:
            return SourceFamilyRelation(
                source_id_a=id_a,
                source_id_b=id_b,
                relationship="DERIVED_FROM",
                confidence=0.75,
                details={"title_score": t_score, "author_score": a_score},
            )

        return SourceFamilyRelation(
            source_id_a=id_a,
            source_id_b=id_b,
            relationship="UNKNOWN_RELATION",
            confidence=0.0,
            details={"title_score": t_score, "author_score": a_score},
        )

    def record_relation(self, rel: SourceFamilyRelation) -> None:
        if rel.relationship == "UNKNOWN_RELATION":
            return
        with self.db.get_connection() as con:
            con.execute(
                """
                INSERT INTO source_family_relations (
                    source_id_a, source_id_b, relationship, confidence, details_json, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    rel.source_id_a,
                    rel.source_id_b,
                    rel.relationship,
                    rel.confidence,
                    json.dumps(rel.details),
                    rel.observed_at,
                ),
            )
            con.commit()

    def cluster_sources(self, sources: list[dict[str, Any]]) -> list[WorkFamilyCluster]:
        """Cluster sources into distinct intellectual works to avoid skewed support counts."""
        clusters: list[WorkFamilyCluster] = []
        visited: set[str] = set()

        for i, s1 in enumerate(sources):
            id_1 = s1.get("id") or s1.get("source_id", "")
            if id_1 in visited:
                continue
            visited.add(id_1)

            current_cluster = WorkFamilyCluster(
                canonical_work_id=f"SOVWORK:{id_1}",
                canonical_title=s1.get("title", f"Work_{id_1}"),
                primary_authors=s1.get("authors") or [],
                member_source_ids=[id_1],
                member_relationships=[],
            )

            for j in range(i + 1, len(sources)):
                s2 = sources[j]
                id_2 = s2.get("id") or s2.get("source_id", "")
                rel = self.classify_pair(s1, s2)
                if rel.relationship in ("IDENTICAL_BLOB", "SAME_SCAN", "SAME_EDITION", "SAME_WORK"):
                    current_cluster.member_source_ids.append(id_2)
                    current_cluster.member_relationships.append(rel.to_dict())
                    visited.add(id_2)
                    self.record_relation(rel)

            clusters.append(current_cluster)

        return clusters

    def export_duplicate_families(self, output_path: Path, clusters: list[WorkFamilyCluster]) -> int:
        """Export JSON structure of duplicate families and work clusters."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "total_clusters": len(clusters),
            "multi_member_clusters": [c.to_dict() for c in clusters if len(c.member_source_ids) > 1],
            "single_member_clusters_count": sum(1 for c in clusters if len(c.member_source_ids) == 1),
            "total_sources_accounted": sum(len(c.member_source_ids) for c in clusters),
        }
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return len(data["multi_member_clusters"])
