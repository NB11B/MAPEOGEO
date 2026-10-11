from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def make_source_id(sha256: str) -> str:
    """Format canonical immutable source identity independent of URLs or titles."""
    clean_sha = sha256.strip().lower()
    return f"SOVSRC:{clean_sha}"


@dataclass
class SourceRecord:
    source_id: str
    sha256: str
    byte_size: int
    format: str  # "pdf", "html", "text", "ocr_candidate", "quarantined"
    acquired_urls: list[str] = field(default_factory=list)
    first_acquired_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    title: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    status: str = "EXTRACTED"  # "EXTRACTED", "OCR_CANDIDATE", "QUARANTINED"
    passage_count: int = 0
    quarantine_reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_candidate_source(self, parser_version: str = "n1-v0.1") -> dict[str, Any]:
        primary_url = self.acquired_urls[0] if self.acquired_urls else ""
        return {
            "id": self.source_id,
            "source_url": primary_url,
            "sha256": self.sha256,
            "acquired_at": self.first_acquired_at,
            "parser_version": parser_version,
            "originating_queue_item": None,
            "candidate_json": json.dumps(self.to_dict(), ensure_ascii=False),
            "status": "CANDIDATE" if self.status != "QUARANTINED" else "QUARANTINED",
            "rejection_reason": self.quarantine_reason,
        }
