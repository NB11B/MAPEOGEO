from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .checkpoint import CheckpointRecord, CheckpointSubsystem
from .config import NanoConfig
from .work_db import WorkDatabase


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RecoveryReport:
    timestamp: str
    status: str
    last_good_checkpoint: Optional[str]
    db_integrity_status: str
    cas_verification_status: str
    cas_blobs_checked: int
    cas_corrupt_count: int
    queue_items_reset: int
    work_discarded_count: int
    work_replayed_count: int
    integrity_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RecoveryManager:
    """Manages crash recovery, reboot qualification, idempotent replay, and DB integrity audits for Gate N5."""

    def __init__(self, config: NanoConfig, db: WorkDatabase, checkpoint_subsystem: CheckpointSubsystem) -> None:
        self.config = config
        self.db = db
        self.checkpoint_subsystem = checkpoint_subsystem
        self.recovery_dir = config.evidence_dir / "recovery"
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

    def perform_startup_recovery(self) -> RecoveryReport:
        """Execute complete startup recovery audit before launching autonomous crawler."""
        now_str = utc_now_iso()
        errors: list[str] = []

        # 1. Verify parent baseline manifest
        baseline_file = Path(self.config.root) / "sovctx" / "manifests" / "n5_parent_baseline.json"
        if not baseline_file.exists():
            # Also try relative to REPO_ROOT
            alt_baseline = Path(__file__).resolve().parents[2] / "sovctx" / "manifests" / "n5_parent_baseline.json"
            if alt_baseline.exists():
                baseline_file = alt_baseline
            else:
                errors.append("MISSING_PARENT_BASELINE_MANIFEST: n5_parent_baseline.json not found")

        # 2. SQLite Integrity Check
        db_integrity = "UNKNOWN"
        try:
            with self.db.get_connection() as con:
                row = con.execute("PRAGMA integrity_check").fetchone()
                if row and row[0].lower() == "ok":
                    db_integrity = "PASS"
                else:
                    db_integrity = "FAIL"
                    errors.append(f"SQLITE_INTEGRITY_FAIL: {row[0] if row else 'empty'}")
        except Exception as e:
            db_integrity = "ERROR"
            errors.append(f"SQLITE_INTEGRITY_EXCEPTION: {e}")

        # 3. CAS Sample Verification
        cas_checked = 0
        cas_corrupt = 0
        cas_dir = self.config.cas_dir
        if cas_dir.exists():
            # Check up to 50 blobs
            for blob_path in list(cas_dir.rglob("*"))[:50]:
                if blob_path.is_file():
                    cas_checked += 1
                    expected_sha = blob_path.name
                    hasher = hashlib.sha256()
                    try:
                        with blob_path.open("rb") as f:
                            while chunk := f.read(65536):
                                hasher.update(chunk)
                        actual_sha = hasher.hexdigest()
                        if len(expected_sha) == 64 and actual_sha != expected_sha:
                            cas_corrupt += 1
                            errors.append(f"CAS_CHECKSUM_MISMATCH: {blob_path.name}")
                    except Exception as e:
                        cas_corrupt += 1
                        errors.append(f"CAS_READ_ERROR: {blob_path} ({e})")

        cas_status = "PASS" if cas_corrupt == 0 else "FAIL"

        # 4. Reset in-progress work in fetch queue
        queue_reset_count = 0
        with self.db.get_connection() as con:
            try:
                cur = con.execute("UPDATE fetch_queue SET status = 'QUEUED' WHERE status IN ('CLAIMED', 'FETCHING', 'PROCESSING')")
                queue_reset_count = cur.rowcount
                con.commit()
            except Exception:
                pass

        # 5. Load latest checkpoint
        latest_chk = self.checkpoint_subsystem.load_latest_checkpoint()
        last_chk_id = latest_chk.checkpoint_id if latest_chk else None

        status = "PASS" if len(errors) == 0 else "FAIL"

        report = RecoveryReport(
            timestamp=now_str,
            status=status,
            last_good_checkpoint=last_chk_id,
            db_integrity_status=db_integrity,
            cas_verification_status=cas_status,
            cas_blobs_checked=cas_checked,
            cas_corrupt_count=cas_corrupt,
            queue_items_reset=queue_reset_count,
            work_discarded_count=0,
            work_replayed_count=queue_reset_count,
            integrity_errors=errors,
        )

        # Write recovery receipt
        rep_file = self.recovery_dir / "latest_recovery_report.json"
        rep_file.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

        return report
