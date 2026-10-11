from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .work_db import WorkDatabase


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CheckpointRecord:
    checkpoint_id: str
    timestamp: str
    epoch_index: int
    db_state_hash: str
    sources_count: int
    passages_count: int
    frontier_open_count: int
    unresolved_count: int
    dossiers_count: int
    dirty_synthesis_keys: list[str]
    last_committed_source_id: Optional[str]
    cas_blobs_count: int
    sentinel_states: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CheckpointSubsystem:
    """Manages periodic state checkpoints, dirty-bit synthesis tracking, and state hash verification."""

    def __init__(self, db: WorkDatabase, checkpoints_dir: Path) -> None:
        self.db = db
        self.checkpoints_dir = checkpoints_dir
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.dirty_synthesis_keys: set[str] = set()

    def mark_synthesis_dirty(self, school_key: str) -> None:
        """Mark a synthesis dossier dirty when new evidence affects its lead person, institution, or method."""
        self.dirty_synthesis_keys.add(school_key)

    def clear_synthesis_dirty(self, school_key: Optional[str] = None) -> None:
        if school_key:
            self.dirty_synthesis_keys.discard(school_key)
        else:
            self.dirty_synthesis_keys.clear()

    def compute_db_state_hash(self) -> str:
        """Compute deterministic state hash over Work DB core tables."""
        state_parts = []
        with self.db.get_connection() as con:
            for table in ("source_blobs", "candidate_sources", "candidate_fragments", "frontier_items", "reference_candidates"):
                try:
                    cnt = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    state_parts.append(f"{table}:{cnt}")
                except Exception:
                    pass
        raw = "|".join(state_parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def create_checkpoint(
        self,
        epoch_index: int,
        sentinel_states: Optional[dict[str, str]] = None,
    ) -> CheckpointRecord:
        now_str = utc_now_iso()
        chk_id = f"CHK_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        sources_cnt = 0
        passages_cnt = 0
        frontier_open = 0
        unres_cnt = 0
        dossiers_cnt = 0
        cas_cnt = 0
        last_src = None

        with self.db.get_connection() as con:
            try:
                sources_cnt = con.execute("SELECT count(*) FROM candidate_sources").fetchone()[0]
            except Exception:
                pass
            try:
                passages_cnt = con.execute("SELECT count(*) FROM candidate_fragments").fetchone()[0]
            except Exception:
                pass
            try:
                frontier_open = con.execute("SELECT count(*) FROM frontier_items WHERE status = 'OPEN'").fetchone()[0]
            except Exception:
                pass
            try:
                unres_cnt = con.execute("SELECT count(*) FROM reference_resolution_attempts WHERE resolution_state = 'UNRESOLVED'").fetchone()[0]
            except Exception:
                pass
            try:
                dossiers_cnt = con.execute("SELECT count(*) FROM historical_synthesis_dossiers").fetchone()[0]
            except Exception:
                pass
            try:
                cas_cnt = con.execute("SELECT count(*) FROM source_blobs").fetchone()[0]
            except Exception:
                pass
            try:
                last_row = con.execute("SELECT id FROM candidate_sources ORDER BY rowid DESC LIMIT 1").fetchone()
                if last_row:
                    last_src = last_row[0]
            except Exception:
                pass

        state_hash = self.compute_db_state_hash()

        record = CheckpointRecord(
            checkpoint_id=chk_id,
            timestamp=now_str,
            epoch_index=epoch_index,
            db_state_hash=state_hash,
            sources_count=sources_cnt,
            passages_count=passages_cnt,
            frontier_open_count=frontier_open,
            unresolved_count=unres_cnt,
            dossiers_count=dossiers_cnt,
            dirty_synthesis_keys=list(self.dirty_synthesis_keys),
            last_committed_source_id=last_src,
            cas_blobs_count=cas_cnt,
            sentinel_states=sentinel_states or {},
        )

        chk_file = self.checkpoints_dir / f"{chk_id}.json"
        latest_file = self.checkpoints_dir / "latest_checkpoint.json"

        chk_data = json.dumps(record.to_dict(), indent=2, ensure_ascii=False)
        chk_file.write_text(chk_data, encoding="utf-8")
        latest_file.write_text(chk_data, encoding="utf-8")

        return record

    def load_latest_checkpoint(self) -> Optional[CheckpointRecord]:
        latest_file = self.checkpoints_dir / "latest_checkpoint.json"
        if not latest_file.exists():
            return None
        try:
            data = json.loads(latest_file.read_text(encoding="utf-8"))
            return CheckpointRecord(**data)
        except Exception:
            return None
