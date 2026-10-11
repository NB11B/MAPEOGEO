from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from sovctx.node.schema import WORK_SCHEMA_VERSION
from sovctx.node.work_db import CandidateSource, WorkDatabase


def test_work_db_schema_initialization() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_work.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        expected_tables = {
            "work_metadata",
            "fetch_queue",
            "fetch_attempts",
            "source_blobs",
            "candidate_sources",
            "candidate_fragments",
            "candidate_equations",
            "candidate_symbols",
            "candidate_claims",
            "candidate_edges",
            "behavior_runs",
            "promotion_queue",
            "quarantine",
            "daemon_runs",
            "resource_samples",
            "candidate_terms",
            "candidate_term_occurrences",
            "candidate_term_relations",
            "candidate_definition_spans",
            "candidate_symbol_occurrences",
            "candidate_equation_witnesses",
            "reference_candidates",
            "reference_resolution_attempts",
            "frontier_items",
            "frontier_evidence",
            "source_nominations",
            "entity_mentions",
        }
        assert len(expected_tables) == 27

        with db.get_connection() as con:
            cur = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
            found_tables = {row[0] for row in cur.fetchall()}
            assert expected_tables.issubset(found_tables)

            version = con.execute(
                "SELECT value FROM work_metadata WHERE key='schema_version'"
            ).fetchone()[0]
            assert version == WORK_SCHEMA_VERSION


def test_queue_priority_and_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_work.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        # Enqueue P2 first, then P0, then P1
        id_p2 = db.enqueue("https://example.org/p2", priority="P2", goal="Low prio")
        id_p0 = db.enqueue("https://example.org/p0", priority="P0", goal="Urgent primary")
        id_p1 = db.enqueue("https://example.org/p1", priority="P1", goal="Normal")

        # First pop must be P0
        item1 = db.get_next_queue_item(mark_in_progress=True)
        assert item1 is not None
        assert item1.id == id_p0
        assert item1.priority == "P0"
        assert item1.status == "IN_PROGRESS"

        # Second pop must be P1
        item2 = db.get_next_queue_item(mark_in_progress=True)
        assert item2 is not None
        assert item2.id == id_p1
        assert item2.priority == "P1"

        # Third pop must be P2
        item3 = db.get_next_queue_item(mark_in_progress=True)
        assert item3 is not None
        assert item3.id == id_p2
        assert item3.priority == "P2"

        # No more queued items
        assert db.get_next_queue_item() is None

        # Reset in-progress items on recovery
        reset_count = db.reset_in_progress_items()
        assert reset_count == 3

        # P0 should be popped again first
        re_pop = db.get_next_queue_item()
        assert re_pop is not None
        assert re_pop.id == id_p0


def test_fetch_attempts_and_blobs() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_work.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        qid = db.enqueue("https://example.org/doc", priority="P0")
        assert db.get_attempt_count(qid) == 0

        # Attempt 1: 500 error
        db.record_fetch_attempt(
            queue_id=qid,
            url="https://example.org/doc",
            attempt_number=1,
            status_code=500,
            headers={"server": "test"},
            bytes_downloaded=0,
            sha256=None,
            elapsed_sec=0.1,
            error_message="Internal Server Error",
        )
        assert db.get_attempt_count(qid) == 1

        # Attempt 2: 200 OK
        sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        db.register_blob(
            sha256=sha,
            storage_path="e3/e3b0c442...",
            byte_size=1024,
            content_type="text/html",
            inferred_type="html",
            url="https://example.org/doc",
        )
        assert db.has_blob(sha)

        blob = db.get_blob(sha)
        assert blob is not None
        assert blob.byte_size == 1024
        assert blob.inferred_type == "html"


def test_candidate_foreign_key_enforcement() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_work.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        sha = "a1b2c3d4e5f60000000000000000000000000000000000000000000000000000"
        cand = CandidateSource(
            id="CAND_SRC:001",
            source_url="https://example.org/paper",
            sha256=sha,
            acquired_at="2026-10-11T12:00:00Z",
            parser_version="0.1",
            originating_queue_item="QUEUE:001",
            candidate_json="{}",
        )

        # Should fail foreign key check because blob does not exist in source_blobs
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_candidate_source(cand)

        # Register blob first
        db.register_blob(
            sha256=sha,
            storage_path="a1/a1b2c3...",
            byte_size=500,
            content_type="application/pdf",
            inferred_type="pdf",
            url="https://example.org/paper",
        )

        # Now insertion succeeds
        db.insert_candidate_source(cand)

        with db.get_connection() as con:
            count = con.execute("SELECT COUNT(*) FROM candidate_sources").fetchone()[0]
            assert count == 1


def test_canonical_queue_import() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(__file__).resolve().parents[1]
        q_path = root / "corpus" / "ingestion_queue.jsonl"
        s_path = root / "corpus" / "sources.jsonl"

        db_path = Path(tmp_dir) / "test_work.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        imported = db.import_canonical_queue(q_path, s_path)
        assert imported > 0

        stats = db.get_queue_stats()
        assert stats.get("QUEUED", 0) == imported

        # Gelfand-Levitan 1951 or Pontryagin 1960 should be in the queue
        with db.get_connection() as con:
            p0_items = con.execute(
                "SELECT COUNT(*) FROM fetch_queue WHERE priority='P0'"
            ).fetchone()[0]
            assert p0_items > 0
