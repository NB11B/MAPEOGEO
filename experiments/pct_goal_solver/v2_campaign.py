"""Fail-closed boundary around the immutable historical V2 campaign.

V2 was executed and sealed under an older solver implementation. The current
runtime has different goal builders, closed mathematical contracts, terminal
verification, routing, and macro authority. Re-executing the old campaign
entry point here would therefore be a new experiment mislabeled as the frozen
one. The historical implementation remains available from its exact commit;
this module records that identity and refuses current-runtime rescoring.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping, NoReturn


V2_FROZEN_EXECUTION_COMMIT = "f2e8cc73ef6665e9329d9b3901f7f8672e4dc4e5"
V2_FROZEN_IDENTITY: Mapping[str, str] = MappingProxyType(
    {
        "actions_run_id": "35059952763",
        "artifact_archive_sha256": "baf020fa8007e3f721b44264c168249c4abf6689787f23db76f0ba4adee60235",
        "artifact_expires_at": "2026-12-15T05:32:57Z",
        "artifact_id": "10431654598",
        "commit": V2_FROZEN_EXECUTION_COMMIT,
        "current_validation_status": "NOT_VALID_UNDER_CURRENT_STANDARD",
        "record_status": "RECORDED_LEGACY",
        "repository_archive_path": "evidence/historical_invalid_v2/pct-goal-solver-v2-results.zip",
    }
)

class FrozenV2ReplayError(RuntimeError):
    """Raised when current code attempts to rescore the frozen V2 protocol."""


def run_v2_campaign() -> NoReturn:
    """Refuse to reinterpret frozen V2 evidence under the current runtime."""
    identity = V2_FROZEN_IDENTITY
    raise FrozenV2ReplayError(
        "frozen V2 replay is quarantined: current code is not the sealed "
        f"runtime; inspect {identity['repository_archive_path']} from commit "
        f"{identity['commit']} (Actions run {identity['actions_run_id']}, "
        f"artifact {identity['artifact_id']}, archive SHA-256 "
        f"{identity['artifact_archive_sha256']})"
    )
