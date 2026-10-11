from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import SQLiteSettings
from .schema import WORK_PRAGMAS, WORK_SCHEMA, WORK_SCHEMA_VERSION


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class QueueItem:
    id: str
    source_id: str | None
    url: str
    priority: str
    status: str
    goal: str | None
    etag: str | None
    last_modified: str | None
    depth: int
    nominated_by: str | None
    created_at: str
    updated_at: str


@dataclass
class SourceBlob:
    sha256: str
    storage_path: str
    byte_size: int
    content_type: str | None
    inferred_type: str | None
    first_acquired_at: str
    first_url: str
    verified_hash: int = 1


@dataclass
class CandidateSource:
    id: str
    source_url: str
    sha256: str
    acquired_at: str
    parser_version: str
    originating_queue_item: str | None
    candidate_json: str
    status: str = "CANDIDATE"
    rejection_reason: str | None = None


from contextlib import contextmanager

class WorkDatabase:
    def __init__(self, db_path: Path | str, sqlite_settings: SQLiteSettings | None = None) -> None:
        self.db_path = Path(db_path)
        self.settings = sqlite_settings or SQLiteSettings()

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(
            str(self.db_path),
            timeout=self.settings.busy_timeout_ms / 1000.0,
            check_same_thread=False,
        )
        con.row_factory = sqlite3.Row
        con.execute(f"PRAGMA journal_mode = {self.settings.journal_mode};")
        con.execute(f"PRAGMA synchronous = {self.settings.synchronous};")
        con.execute(f"PRAGMA temp_store = {self.settings.temp_store};")
        con.execute(f"PRAGMA cache_size = -{self.settings.cache_kib};")
        con.execute(f"PRAGMA mmap_size = {self.settings.mmap_bytes};")
        con.execute(f"PRAGMA busy_timeout = {self.settings.busy_timeout_ms};")
        con.execute("PRAGMA foreign_keys = ON;")
        return con

    @contextmanager
    def get_connection(self):
        con = self.connect()
        try:
            yield con
        finally:
            con.close()

    def init_db(self) -> None:
        with self.get_connection() as con:
            con.executescript(WORK_SCHEMA)
            con.execute(
                """
                INSERT OR REPLACE INTO work_metadata (key, value)
                VALUES (?, ?)
                """,
                ("schema_version", WORK_SCHEMA_VERSION),
            )
            con.execute(
                """
                INSERT OR IGNORE INTO work_metadata (key, value)
                VALUES (?, ?)
                """,
                ("created_at", utc_now_iso()),
            )
            con.commit()

    def checkpoint_wal(self, mode: str = "PASSIVE") -> tuple[int, int, int]:
        with self.get_connection() as con:
            cur = con.execute(f"PRAGMA wal_checkpoint({mode});")
            row = cur.fetchone()
            if row:
                return (row[0], row[1], row[2])
            return (0, 0, 0)

    # ------------------------------------------------------------------
    # Queue Management
    # ------------------------------------------------------------------

    def make_queue_id(self, url: str) -> str:
        digest = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:16]
        return f"QUEUE:{digest}"

    def enqueue(
        self,
        url: str,
        priority: str = "P1",
        goal: str | None = None,
        source_id: str | None = None,
        depth: int = 0,
        nominated_by: str | None = None,
    ) -> str:
        url_clean = url.strip()
        queue_id = self.make_queue_id(url_clean)
        now = utc_now_iso()

        with self.get_connection() as con:
            con.execute(
                """
                INSERT INTO fetch_queue (
                    id, source_id, url, priority, status, goal, depth,
                    nominated_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'QUEUED', ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    priority = CASE
                        WHEN excluded.priority < fetch_queue.priority THEN excluded.priority
                        ELSE fetch_queue.priority
                    END,
                    source_id = COALESCE(excluded.source_id, fetch_queue.source_id),
                    goal = COALESCE(excluded.goal, fetch_queue.goal),
                    updated_at = excluded.updated_at
                """,
                (queue_id, source_id, url_clean, priority, goal, depth, nominated_by, now, now),
            )
            con.commit()
        return queue_id

    def get_next_queue_item(self, mark_in_progress: bool = True) -> QueueItem | None:
        now = utc_now_iso()
        with self.get_connection() as con:
            cur = con.execute(
                """
                SELECT * FROM fetch_queue
                WHERE status = 'QUEUED'
                ORDER BY
                    CASE priority
                        WHEN 'P0' THEN 0
                        WHEN 'P1' THEN 1
                        WHEN 'P2' THEN 2
                        ELSE 3
                    END ASC,
                    created_at ASC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                return None

            item = QueueItem(
                id=row["id"],
                source_id=row["source_id"],
                url=row["url"],
                priority=row["priority"],
                status=row["status"],
                goal=row["goal"],
                etag=row["etag"],
                last_modified=row["last_modified"],
                depth=row["depth"],
                nominated_by=row["nominated_by"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

            if mark_in_progress:
                con.execute(
                    """
                    UPDATE fetch_queue
                    SET status = 'IN_PROGRESS', updated_at = ?
                    WHERE id = ?
                    """,
                    (now, item.id),
                )
                con.commit()
                item.status = "IN_PROGRESS"
                item.updated_at = now

            return item

    def update_queue_status(
        self,
        queue_id: str,
        status: str,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        now = utc_now_iso()
        with self.get_connection() as con:
            con.execute(
                """
                UPDATE fetch_queue
                SET status = ?,
                    etag = COALESCE(?, etag),
                    last_modified = COALESCE(?, last_modified),
                    updated_at = ?
                WHERE id = ?
                """,
                (status, etag, last_modified, now, queue_id),
            )
            con.commit()

    def reset_in_progress_items(self) -> int:
        now = utc_now_iso()
        with self.get_connection() as con:
            cur = con.execute(
                """
                UPDATE fetch_queue
                SET status = 'QUEUED', updated_at = ?
                WHERE status = 'IN_PROGRESS'
                """,
                (now,),
            )
            con.commit()
            return cur.rowcount

    def get_queue_stats(self) -> dict[str, int]:
        with self.get_connection() as con:
            cur = con.execute(
                """
                SELECT status, COUNT(*) as c
                FROM fetch_queue
                GROUP BY status
                """
            )
            return {row["status"]: row["c"] for row in cur.fetchall()}

    # ------------------------------------------------------------------
    # Fetch Attempts
    # ------------------------------------------------------------------

    def record_fetch_attempt(
        self,
        queue_id: str,
        url: str,
        attempt_number: int,
        status_code: int | None,
        headers: dict[str, Any] | None,
        bytes_downloaded: int | None,
        sha256: str | None,
        elapsed_sec: float | None,
        error_message: str | None,
    ) -> int:
        now = utc_now_iso()
        headers_json = json.dumps(headers, ensure_ascii=False) if headers else None

        with self.get_connection() as con:
            cur = con.execute(
                """
                INSERT INTO fetch_attempts (
                    queue_id, url, attempt_number, status_code, headers_json,
                    bytes_downloaded, sha256, elapsed_sec, error_message, attempted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    queue_id,
                    url,
                    attempt_number,
                    status_code,
                    headers_json,
                    bytes_downloaded,
                    sha256,
                    elapsed_sec,
                    error_message,
                    now,
                ),
            )
            con.commit()
            return cur.lastrowid or 0

    def get_attempt_count(self, queue_id: str) -> int:
        with self.get_connection() as con:
            cur = con.execute(
                "SELECT COUNT(*) FROM fetch_attempts WHERE queue_id = ?",
                (queue_id,),
            )
            row = cur.fetchone()
            return row[0] if row else 0

    # ------------------------------------------------------------------
    # Content-Addressed Blob Store Registry
    # ------------------------------------------------------------------

    def register_blob(
        self,
        sha256: str,
        storage_path: str,
        byte_size: int,
        content_type: str | None,
        inferred_type: str | None,
        url: str,
    ) -> None:
        now = utc_now_iso()
        with self.get_connection() as con:
            con.execute(
                """
                INSERT OR IGNORE INTO source_blobs (
                    sha256, storage_path, byte_size, content_type,
                    inferred_type, first_acquired_at, first_url, verified_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (sha256, storage_path, byte_size, content_type, inferred_type, now, url),
            )
            con.commit()

    def get_blob(self, sha256: str) -> SourceBlob | None:
        with self.get_connection() as con:
            cur = con.execute(
                "SELECT * FROM source_blobs WHERE sha256 = ?",
                (sha256,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return SourceBlob(
                sha256=row["sha256"],
                storage_path=row["storage_path"],
                byte_size=row["byte_size"],
                content_type=row["content_type"],
                inferred_type=row["inferred_type"],
                first_acquired_at=row["first_acquired_at"],
                first_url=row["first_url"],
                verified_hash=row["verified_hash"],
            )

    def has_blob(self, sha256: str) -> bool:
        with self.get_connection() as con:
            cur = con.execute(
                "SELECT 1 FROM source_blobs WHERE sha256 = ?",
                (sha256,),
            )
            return cur.fetchone() is not None

    # ------------------------------------------------------------------
    # Quarantine
    # ------------------------------------------------------------------

    def record_quarantine(
        self,
        quarantine_reason: str,
        url: str | None = None,
        sha256: str | None = None,
        file_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        now = utc_now_iso()
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        with self.get_connection() as con:
            cur = con.execute(
                """
                INSERT INTO quarantine (
                    url, sha256, quarantine_reason, file_path, quarantined_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (url, sha256, quarantine_reason, file_path, now, metadata_json),
            )
            con.commit()
            return cur.lastrowid or 0

    # ------------------------------------------------------------------
    # Daemon Lifecycle
    # ------------------------------------------------------------------

    def start_daemon_run(self, daemon_name: str, run_id: str) -> None:
        now = utc_now_iso()
        with self.get_connection() as con:
            con.execute(
                """
                INSERT INTO daemon_runs (
                    daemon_name, run_id, status, started_at
                ) VALUES (?, ?, 'RUNNING', ?)
                """,
                (daemon_name, run_id, now),
            )
            con.commit()

    def update_daemon_run(
        self,
        run_id: str,
        status: str,
        processed_delta: int = 0,
        succeeded_delta: int = 0,
        failed_delta: int = 0,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        metrics_json = json.dumps(metrics, ensure_ascii=False) if metrics else None
        with self.get_connection() as con:
            con.execute(
                """
                UPDATE daemon_runs
                SET status = ?,
                    items_processed = items_processed + ?,
                    items_succeeded = items_succeeded + ?,
                    items_failed = items_failed + ?,
                    metrics_json = COALESCE(?, metrics_json)
                WHERE run_id = ?
                """,
                (status, processed_delta, succeeded_delta, failed_delta, metrics_json, run_id),
            )
            con.commit()

    def finish_daemon_run(
        self,
        run_id: str,
        status: str = "COMPLETED",
        metrics: dict[str, Any] | None = None,
    ) -> None:
        now = utc_now_iso()
        metrics_json = json.dumps(metrics, ensure_ascii=False) if metrics else None
        with self.get_connection() as con:
            con.execute(
                """
                UPDATE daemon_runs
                SET status = ?,
                    stopped_at = ?,
                    metrics_json = COALESCE(?, metrics_json)
                WHERE run_id = ?
                """,
                (status, now, metrics_json, run_id),
            )
            con.commit()

    # ------------------------------------------------------------------
    # Hardware Telemetry Samples
    # ------------------------------------------------------------------

    def record_resource_sample(
        self,
        sampled_at: str,
        disk_free_gb: float,
        ram_available_mb: float,
        swap_used_gb: float,
        thermal_max_c: float | None,
        load_1m: float | None,
        worker_rss_mb: float | None,
        guard_verdict: str,
        guard_reasons: list[str] | None = None,
    ) -> int:
        reasons_text = "; ".join(guard_reasons) if guard_reasons else None
        with self.get_connection() as con:
            cur = con.execute(
                """
                INSERT INTO resource_samples (
                    sampled_at, disk_free_gb, ram_available_mb, swap_used_gb,
                    thermal_max_c, load_1m, worker_rss_mb, guard_verdict, guard_reasons
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sampled_at,
                    disk_free_gb,
                    ram_available_mb,
                    swap_used_gb,
                    thermal_max_c,
                    load_1m,
                    worker_rss_mb,
                    guard_verdict,
                    reasons_text,
                ),
            )
            con.commit()
            return cur.lastrowid or 0

    # ------------------------------------------------------------------
    # Candidates
    # ------------------------------------------------------------------

    def insert_candidate_source(self, candidate: CandidateSource) -> None:
        with self.get_connection() as con:
            con.execute(
                """
                INSERT INTO candidate_sources (
                    id, source_url, sha256, acquired_at, parser_version,
                    originating_queue_item, candidate_json, status, rejection_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.id,
                    candidate.source_url,
                    candidate.sha256,
                    candidate.acquired_at,
                    candidate.parser_version,
                    candidate.originating_queue_item,
                    candidate.candidate_json,
                    candidate.status,
                    candidate.rejection_reason,
                ),
            )
            con.commit()

    def insert_candidate_terms_batch(
        self,
        terms: list[Any],
        occurrences: list[Any],
        relations: list[Any],
        definitions: list[Any],
        symbols: list[Any],
        equations: list[Any],
    ) -> None:
        with self.get_connection() as con:
            for t in terms:
                con.execute(
                    """
                    INSERT OR REPLACE INTO candidate_terms (
                        id, surface_form, normalized_unicode, language, script,
                        term_type, technicality_score, signals_json, status, rejection_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        t.id,
                        t.surface_form,
                        t.normalized_unicode,
                        t.language,
                        t.script,
                        t.term_type,
                        t.technicality_score,
                        json.dumps(t.signals, ensure_ascii=False),
                        t.status,
                        t.rejection_reason,
                    ),
                )

            for o in occurrences:
                con.execute(
                    """
                    INSERT OR REPLACE INTO candidate_term_occurrences (
                        id, term_id, passage_id, source_id, surface_form,
                        char_start, char_end, sentence_index, context_snippet
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        o.id,
                        o.term_id,
                        o.passage_id,
                        o.source_id,
                        o.surface_form,
                        o.char_start,
                        o.char_end,
                        o.sentence_index,
                        o.context_snippet,
                    ),
                )

            for r in relations:
                con.execute(
                    """
                    INSERT OR REPLACE INTO candidate_term_relations (
                        id, from_term_id, to_term_id, relation_type, method, confidence, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r.id,
                        r.from_term_id,
                        r.to_term_id,
                        r.relation_type,
                        r.method,
                        r.confidence,
                        json.dumps(r.details, ensure_ascii=False),
                    ),
                )

            for d in definitions:
                con.execute(
                    """
                    INSERT OR REPLACE INTO candidate_definition_spans (
                        id, passage_id, source_id, subject_term_id, trigger, defining_span, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        d.id,
                        d.passage_id,
                        d.source_id,
                        d.subject_term_id,
                        d.trigger,
                        d.defining_span,
                        d.confidence,
                    ),
                )

            for s in symbols:
                con.execute(
                    """
                    INSERT OR REPLACE INTO candidate_symbol_occurrences (
                        id, symbol, source_id, passage_id, equation_witness_id, surface_context, meaning_candidate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        s.id,
                        s.symbol,
                        s.source_id,
                        s.passage_id,
                        s.equation_witness_id,
                        s.surface_context,
                        s.meaning_candidate,
                    ),
                )

            for e in equations:
                con.execute(
                    """
                    INSERT OR REPLACE INTO candidate_equation_witnesses (
                        id, source_id, passage_id, page_physical, surface_representation,
                        locator, neighboring_terms_json, neighboring_symbols_json,
                        extraction_method, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        e.id,
                        e.source_id,
                        e.passage_id,
                        e.page_physical,
                        e.surface_representation,
                        e.locator,
                        json.dumps(e.neighboring_terms, ensure_ascii=False),
                        json.dumps(e.neighboring_symbols, ensure_ascii=False),
                        e.extraction_method,
                        e.confidence,
                    ),
                )
            con.commit()

    def get_terminology_stats(self) -> dict[str, int]:
        with self.get_connection() as con:
            return {
                "terms": con.execute("SELECT COUNT(*) FROM candidate_terms").fetchone()[0],
                "occurrences": con.execute("SELECT COUNT(*) FROM candidate_term_occurrences").fetchone()[0],
                "relations": con.execute("SELECT COUNT(*) FROM candidate_term_relations").fetchone()[0],
                "definitions": con.execute("SELECT COUNT(*) FROM candidate_definition_spans").fetchone()[0],
                "symbols": con.execute("SELECT COUNT(*) FROM candidate_symbol_occurrences").fetchone()[0],
                "equation_witnesses": con.execute("SELECT COUNT(*) FROM candidate_equation_witnesses").fetchone()[0],
            }


    # Canonical Ingestion Queue Importer
    # ------------------------------------------------------------------

    def import_canonical_queue(
        self,
        ingestion_queue_path: Path,
        sources_path: Path | None = None,
    ) -> int:
        if not ingestion_queue_path.exists():
            return 0

        source_url_map: dict[str, str] = {}
        if sources_path and sources_path.exists():
            for line in sources_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                src = json.loads(line)
                sid = src.get("id")
                url = src.get("url")
                if sid and url:
                    source_url_map[sid] = url.strip()

        enqueued_count = 0
        for line in ingestion_queue_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            source_id = item.get("source_id")
            priority = item.get("priority", "P1")
            goal = item.get("goal")

            url = source_url_map.get(source_id) if source_id else None
            if not url and item.get("url"):
                url = item.get("url")

            if url:
                self.enqueue(
                    url=url,
                    priority=priority,
                    goal=goal,
                    source_id=source_id,
                    depth=0,
                    nominated_by="canonical:ingestion_queue",
                )
                enqueued_count += 1

        return enqueued_count
