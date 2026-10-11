from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sovctx.node.checkpoint import CheckpointSubsystem
from sovctx.node.config import load_config
from sovctx.node.endurance import CampaignCeilings, EnduranceSupervisor
from sovctx.node.endurance_metrics import (
    EnduranceMetricsTracker,
    EpistemicPause,
    ResourcePause,
)
from sovctx.node.recovery import RecoveryManager
from sovctx.node.work_db import WorkDatabase
from sovctx.tools.qualify_n5 import run_n5_qualification


def test_parent_baseline_manifest() -> None:
    manifest_path = Path(__file__).resolve().parents[1] / "manifests" / "n5_parent_baseline.json"
    assert manifest_path.exists(), "Parent baseline manifest must exist"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["gate"] == "N5_AUTONOMOUS_ENDURANCE_EXPANSION"
    assert data["status"] == "SUBSTRATE_FROZEN"
    assert data["schema_version"] == "0.5"

    gates = data["sealed_gate_manifests"]
    expected_gates = [
        "N0_PHYSICAL_ISOLATION",
        "N0_5_PHYSICAL_SMOKE",
        "N1_SOURCE_INGESTION",
        "N1_5_NATIVE_TERMINOLOGY",
        "N2_CITATION_TERMINOLOGY_FRONTIER",
        "N3_BEHAVIORAL_QUALIFICATION",
        "N4_BOUNDED_RECURSIVE_EXPANSION",
        "N4_5_EPISTEMIC_SYNTHESIS",
    ]
    for eg in expected_gates:
        assert eg in gates
        assert gates[eg]["status"] == "PASS"


def test_endurance_metrics_rates_and_entropy() -> None:
    with tempfile.TemporaryDirectory() as td:
        tracker = EnduranceMetricsTracker(Path(td))

        # Rates computation
        rates = tracker.compute_rates(
            delta_sources=10,
            delta_frontier=40,
            delta_unresolved=5,
            delta_duplicates=2,
            delta_contradictions=1,
            delta_epistemic_errors=0,
            delta_seconds=10.0,
        )
        assert rates["r_sources"] == 1.0
        assert rates["r_frontier"] == 4.0
        assert rates["r_unresolved"] == 0.5
        assert rates["r_duplicates"] == 0.2
        assert rates["r_contradictions"] == 0.1
        assert rates["r_epistemic_errors"] == 0.0

        # Frontier entropy
        counts = {"CITATION": 50, "PERSON": 25, "METHOD": 25}
        entropy = tracker.compute_frontier_entropy(counts)
        assert entropy > 1.0  # H_F > 1.0 for balanced multi-class distribution

        # Single class entropy must be 0
        single_counts = {"CITATION": 100}
        assert tracker.compute_frontier_entropy(single_counts) == 0.0

        # Growth efficiency
        eff = tracker.compute_growth_efficiency(useful_items=20, acquisition_attempts=25)
        assert eff == 0.8


def test_circuit_breakers_resource_and_epistemic() -> None:
    with tempfile.TemporaryDirectory() as td:
        tracker = EnduranceMetricsTracker(Path(td))

        # Resource Pause: thermal breach
        class ThermalBreachSample:
            thermal_max_c = 78.0
            ram_available_mb = 1200.0
            swap_used_gb = 0.1
            worker_rss_mb = 50.0

        with pytest.raises(ResourcePause):
            tracker.check_circuit_breakers(ThermalBreachSample(), {}, {})

        assert (Path(td) / "RESOURCE_PAUSE").exists()

        # Epistemic Pause: canonical promotion violation
        with pytest.raises(EpistemicPause):
            tracker.check_circuit_breakers(None, {"canonical_promotion_violations": 1}, {})

        assert (Path(td) / "EPISTEMIC_PAUSE").exists()


def test_checkpoint_subsystem_and_dirty_bits() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "chk_test.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()

        sub = CheckpointSubsystem(db, Path(td) / "checkpoints")

        # Dirty bits
        sub.mark_synthesis_dirty("TIKHONOV")
        sub.mark_synthesis_dirty("PONTRYAGIN")
        assert "TIKHONOV" in sub.dirty_synthesis_keys
        assert "PONTRYAGIN" in sub.dirty_synthesis_keys

        # Create checkpoint
        chk = sub.create_checkpoint(epoch_index=1, sentinel_states={"TIKHONOV": "HISTORICALLY_ATTESTED"})
        assert chk.epoch_index == 1
        assert "TIKHONOV" in chk.dirty_synthesis_keys
        assert len(chk.db_state_hash) == 64

        # Clear dirty bit
        sub.clear_synthesis_dirty("TIKHONOV")
        assert "TIKHONOV" not in sub.dirty_synthesis_keys
        assert "PONTRYAGIN" in sub.dirty_synthesis_keys

        # Load latest
        latest = sub.load_latest_checkpoint()
        assert latest is not None
        assert latest.checkpoint_id == chk.checkpoint_id


def test_recovery_manager_crash_and_idempotency() -> None:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "rec_test.sqlite3"
        db = WorkDatabase(db_path)
        db.init_db()
        config = load_config()

        sub = CheckpointSubsystem(db, Path(td) / "checkpoints")
        mgr = RecoveryManager(config, db, sub)

        # Inject incomplete claimed item into queue
        with db.get_connection() as con:
            con.execute(
                """
                INSERT INTO fetch_queue (id, url, status, created_at, updated_at)
                VALUES ('Q1', 'https://mathnet.ru/test.pdf', 'CLAIMED', '2026-10-11T00:00:00Z', '2026-10-11T00:00:00Z')
                """
            )
            con.commit()

        # Perform startup recovery
        rep = mgr.perform_startup_recovery()
        assert rep.status == "PASS"
        assert rep.queue_items_reset == 1

        # Verify Q1 reset to QUEUED
        with db.get_connection() as con:
            status = con.execute("SELECT status FROM fetch_queue WHERE id = 'Q1'").fetchone()[0]
            assert status == "QUEUED"


def test_full_n5_qualification_harness() -> None:
    res = run_n5_qualification()
    assert res["verdict"] == "PASS"
    for t_name, passed in res["thresholds"].items():
        assert passed is True, f"Threshold failed: {t_name}"


def test_paced_campaign_execution() -> None:
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        db_path = temp_dir / "pace_test.sqlite3"
        db = WorkDatabase(db_path)
        config = load_config()
        config.data_root = temp_dir

        ceilings = CampaignCeilings(max_sources=10, max_blobs=20)
        supervisor = EnduranceSupervisor(
            config=config,
            db=db,
            duration_seconds=2,
            epoch_duration_seconds=1,
            ceilings=ceilings,
            pace_seconds=0.05,
        )
        receipt = supervisor.run_campaign()
        assert receipt["verdict"] == "PASS"
        assert receipt["epochs_completed"] >= 1
        assert receipt["total_sources_admitted"] > 0
