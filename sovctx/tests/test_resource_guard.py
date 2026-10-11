from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sovctx.node.config import IsolationConfig, NanoConfig, ResourceLimits
from sovctx.node.guard import (
    IsolationViolationError,
    ResourceGuard,
    ResourcePressurePause,
)
from sovctx.node.work_db import WorkDatabase


def test_resource_guard_evaluation_thresholds() -> None:
    config = NanoConfig(root=Path("."), data_root=Path("."))
    guard = ResourceGuard(config)

    # 1. All GREEN
    verdict, reasons = guard.evaluate(
        disk_free_gb=25.0,
        ram_available_mb=1200.0,
        swap_used_gb=0.2,
        thermal_max_c=45.0,
        load_1m=0.5,
        worker_rss_mb=120.0,
    )
    assert verdict == "GREEN"
    assert not reasons

    # 2. Disk Warn
    verdict, reasons = guard.evaluate(
        disk_free_gb=17.5,
        ram_available_mb=1200.0,
        swap_used_gb=0.2,
        thermal_max_c=45.0,
        load_1m=0.5,
        worker_rss_mb=120.0,
    )
    assert verdict == "WARN"
    assert any("Disk free space" in r for r in reasons)

    # 3. Disk Stop
    verdict, reasons = guard.evaluate(
        disk_free_gb=13.5,
        ram_available_mb=1200.0,
        swap_used_gb=0.2,
        thermal_max_c=45.0,
        load_1m=0.5,
        worker_rss_mb=120.0,
    )
    assert verdict == "STOP"
    assert any("stop threshold" in r for r in reasons)

    # 4. RAM Stop
    verdict, reasons = guard.evaluate(
        disk_free_gb=25.0,
        ram_available_mb=250.0,
        swap_used_gb=0.2,
        thermal_max_c=45.0,
        load_1m=0.5,
        worker_rss_mb=120.0,
    )
    assert verdict == "STOP"
    assert any("RAM available" in r for r in reasons)

    # 5. Swap Stop
    verdict, reasons = guard.evaluate(
        disk_free_gb=25.0,
        ram_available_mb=1000.0,
        swap_used_gb=2.6,
        thermal_max_c=45.0,
        load_1m=0.5,
        worker_rss_mb=120.0,
    )
    assert verdict == "STOP"
    assert any("Swap used" in r for r in reasons)

    # 6. Thermal Warn and Stop
    verdict_warn, _ = guard.evaluate(
        disk_free_gb=25.0,
        ram_available_mb=1000.0,
        swap_used_gb=0.2,
        thermal_max_c=72.0,
        load_1m=0.5,
        worker_rss_mb=120.0,
    )
    assert verdict_warn == "WARN"

    verdict_stop, _ = guard.evaluate(
        disk_free_gb=25.0,
        ram_available_mb=1000.0,
        swap_used_gb=0.2,
        thermal_max_c=78.0,
        load_1m=0.5,
        worker_rss_mb=120.0,
    )
    assert verdict_stop == "STOP"

    # 7. Load: transient spike gives WARN, persistent spike (3 samples) gives STOP
    guard.consecutive_load_breaches = 0
    # First breach: WARN
    v1, r1 = guard.evaluate(
        disk_free_gb=25.0, ram_available_mb=1000.0, swap_used_gb=0.2,
        thermal_max_c=45.0, load_1m=3.5, worker_rss_mb=120.0,
    )
    assert v1 == "WARN"
    assert any("breach 1/3" in r for r in r1)

    # Second breach: WARN
    v2, r2 = guard.evaluate(
        disk_free_gb=25.0, ram_available_mb=1000.0, swap_used_gb=0.2,
        thermal_max_c=45.0, load_1m=3.5, worker_rss_mb=120.0,
    )
    assert v2 == "WARN"
    assert any("breach 2/3" in r for r in r2)

    # Third consecutive breach: STOP
    v3, r3 = guard.evaluate(
        disk_free_gb=25.0, ram_available_mb=1000.0, swap_used_gb=0.2,
        thermal_max_c=45.0, load_1m=3.5, worker_rss_mb=120.0,
    )
    assert v3 == "STOP"
    assert any("3 consecutive samples" in r for r in r3)

    # Recovery resets counter
    v4, _ = guard.evaluate(
        disk_free_gb=25.0, ram_available_mb=1000.0, swap_used_gb=0.2,
        thermal_max_c=45.0, load_1m=1.0, worker_rss_mb=120.0,
    )
    assert v4 == "GREEN"
    assert guard.consecutive_load_breaches == 0

    # 8. Worker RSS Stop
    verdict, reasons = guard.evaluate(
        disk_free_gb=25.0,
        ram_available_mb=1000.0,
        swap_used_gb=0.2,
        thermal_max_c=45.0,
        load_1m=0.5,
        worker_rss_mb=680.0,
    )
    assert verdict == "STOP"
    assert any("Worker RSS" in r for r in reasons)


def test_resource_guard_pause_signaling_and_recovery() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(root=data_root, data_root=data_root)
        guard = ResourceGuard(config)

        assert not guard.is_paused()
        guard.assert_not_paused()

        # Trigger STOP
        guard.set_pause(["Simulated thermal stop"])
        assert guard.is_paused()
        assert guard.pause_file.exists()

        with pytest.raises(ResourcePressurePause) as exc:
            guard.assert_not_paused()
        assert "Simulated thermal stop" in str(exc.value)

        # Clear pause on recovery
        guard.clear_pause()
        assert not guard.is_paused()
        guard.assert_not_paused()


def test_resource_guard_samples_written_to_db() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(root=data_root, data_root=data_root)
        guard = ResourceGuard(config)
        db = WorkDatabase(config.work_db_path)
        db.init_db()

        sample = guard.sample(db=db)
        assert sample.verdict in ("GREEN", "WARN", "STOP")

        with db.get_connection() as con:
            row = con.execute("SELECT * FROM resource_samples").fetchone()
            assert row is not None
            assert row["disk_free_gb"] == sample.disk_free_gb
            assert row["guard_verdict"] == sample.verdict


def test_physical_isolation_enforcement() -> None:
    config = NanoConfig(
        root=Path("."),
        data_root=Path("."),
        isolation=IsolationConfig(
            forbidden_write_paths=[
                "/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3"
            ],
            forbidden_read_paths=[
                "/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3"
            ],
            normal_runtime_reads_mapeogeo=False,
        ),
    )
    guard = ResourceGuard(config)

    # Forbidden path must raise
    with pytest.raises(IsolationViolationError):
        guard.assert_isolation("/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3", is_write=False)

    with pytest.raises(IsolationViolationError):
        guard.assert_isolation("/home/uow/mapeogeo-m0/evidence/mapeogeo_canonical_graph_indexed.sqlite3", is_write=True)

    # Allowed SOVCTX paths must pass
    guard.assert_isolation("/home/uow/sovctx-data/db/sovctx_work.sqlite3", is_write=True)
    guard.assert_isolation("/home/uow/sovctx-data/raw/12/123456", is_write=False)
