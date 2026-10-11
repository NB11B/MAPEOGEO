from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sovctx.node.acquire import AcquisitionDaemon
from sovctx.node.cas import BlobStore
from sovctx.node.config import (
    DEFAULT_FORBIDDEN_PATHS,
    IsolationConfig,
    NanoConfig,
    load_config,
)
from sovctx.node.guard import IsolationViolationError, ResourceGuard
from sovctx.node.work_db import WorkDatabase
from sovctx.tools import validate_graph


def test_gate_n0_directory_and_database_isolation() -> None:
    config = load_config()

    # 1. Configured paths must point to dedicated SOVCTX runtime and data roots
    assert "sovctx" in str(config.data_root).lower()

    # 2. Database paths must be dedicated SOVCTX databases
    assert config.work_db_path.name == "sovctx_work.sqlite3"
    assert config.graph_db_path.name == "sovctx_graph.sqlite3"

    # 3. Forbidden MAPEOGEO paths must be sealed
    forbidden = config.isolation.forbidden_write_paths
    assert any("mapeogeo_canonical_graph_indexed.sqlite3" in p for p in forbidden)

    # 4. Normal runtime must not read MAPEOGEO canonical graph
    assert config.isolation.normal_runtime_reads_mapeogeo is False


def test_gate_n0_guard_blocks_mapeogeo_access() -> None:
    config = load_config()
    guard = ResourceGuard(config)

    mapeogeo_db = "/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3"

    # Read attempt must raise
    with pytest.raises(IsolationViolationError):
        guard.assert_isolation(mapeogeo_db, is_write=False)

    # Write attempt must raise
    with pytest.raises(IsolationViolationError):
        guard.assert_isolation(mapeogeo_db, is_write=True)

    # Directory traversal under MAPEOGEO evidence must also be blocked
    with pytest.raises(IsolationViolationError):
        guard.assert_isolation(
            "/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3-wal",
            is_write=True,
        )


def test_gate_n0_acquisition_quarantines_forbidden_access() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(
            root=data_root,
            data_root=data_root,
            isolation=IsolationConfig(
                forbidden_write_paths=list(DEFAULT_FORBIDDEN_PATHS),
                forbidden_read_paths=list(DEFAULT_FORBIDDEN_PATHS),
                normal_runtime_reads_mapeogeo=False,
            ),
        )
        daemon = AcquisitionDaemon(config)

        # Attempt to acquire a URL targeting the forbidden path
        forbidden_target = "file:///home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3"
        qid = daemon.db.enqueue(forbidden_target, priority="P0")
        item = daemon.db.get_next_queue_item()

        res = daemon.fetch_single(item)
        assert res.status == "QUARANTINED"
        assert "Physical isolation violation" in (res.error_message or "")

        # Queue item must be quarantined, never ACQUIRED
        with daemon.db.get_connection() as con:
            row = con.execute("SELECT status FROM fetch_queue WHERE id=?", (qid,)).fetchone()
            assert row["status"] == "QUARANTINED"

            q_entry = con.execute("SELECT * FROM quarantine").fetchone()
            assert q_entry is not None
            assert q_entry["quarantine_reason"] == "ISOLATION_VIOLATION_FORBIDDEN_PATH"


def test_gate_n0_work_db_and_cas_integrity() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(root=data_root, data_root=data_root)
        config.ensure_directories()

        db = WorkDatabase(config.work_db_path, config.sqlite)
        db.init_db()

        # Check all 15 tables exist
        with db.get_connection() as con:
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            required = {
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
            }
            assert len(required) == 15
            assert required.issubset(tables)

        # CAS verification
        cas = BlobStore(config.raw_dir, max_payload_bytes=100 * 1024 * 1024)
        sample_bytes = b"SOVCTX N0 Candidate Isolation Test"
        sha, path, size, is_new = cas.store_bytes(sample_bytes)
        assert is_new is True
        assert cas.verify_blob(sha)


def test_gate_n0_canonical_graph_validates() -> None:
    # Ensure current canonical graph passes full integrity check
    ret = validate_graph.main()
    assert ret == 0
