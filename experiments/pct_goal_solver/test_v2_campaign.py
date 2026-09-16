import hashlib
from pathlib import Path

import pytest

from experiments.pct_goal_solver.generate_v2_report import generate
from experiments.pct_goal_solver.v2_campaign import (
    FrozenV2ReplayError,
    V2_FROZEN_IDENTITY,
    V2_FROZEN_EXECUTION_COMMIT,
    run_v2_campaign,
)

def test_v2_replay_is_pinned_to_the_frozen_execution_commit():
    assert V2_FROZEN_EXECUTION_COMMIT == "f2e8cc73ef6665e9329d9b3901f7f8672e4dc4e5"
    assert dict(V2_FROZEN_IDENTITY) == {
        "actions_run_id": "35059952763",
        "artifact_archive_sha256": "baf020fa8007e3f721b44264c168249c4abf6689787f23db76f0ba4adee60235",
        "artifact_expires_at": "2026-12-15T05:32:57Z",
        "artifact_id": "10431654598",
        "commit": V2_FROZEN_EXECUTION_COMMIT,
        "current_validation_status": "NOT_VALID_UNDER_CURRENT_STANDARD",
        "record_status": "RECORDED_LEGACY",
        "repository_archive_path": "evidence/historical_invalid_v2/pct-goal-solver-v2-results.zip",
    }


def test_historical_v2_archive_is_preserved_by_content_digest():
    root = Path(__file__).resolve().parents[2]
    archive = root / V2_FROZEN_IDENTITY["repository_archive_path"]
    assert archive.is_file()
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == (
        V2_FROZEN_IDENTITY["artifact_archive_sha256"]
    )
    warning = (archive.parent / "README.md").read_text(encoding="utf-8")
    assert V2_FROZEN_IDENTITY["current_validation_status"] in warning
    assert V2_FROZEN_IDENTITY["artifact_archive_sha256"] in warning
    assert "G8/G9" in warning and "G4/G10/G11" in warning


def test_current_runtime_cannot_rescore_the_frozen_v2_protocol():
    with pytest.raises(FrozenV2ReplayError, match=V2_FROZEN_EXECUTION_COMMIT):
        run_v2_campaign()


def test_v2_report_generator_refuses_before_writing_output(tmp_path):
    output = tmp_path / "must-not-exist"
    with pytest.raises(FrozenV2ReplayError, match=V2_FROZEN_EXECUTION_COMMIT):
        generate(output)
    assert not output.exists()
