from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from experiments.pct_goal_solver.generate_v0_20_report import (
    REPORT_FILENAME,
    canonical_report_bytes,
    write_v0_20_report,
)


def test_canonical_report_bytes_are_order_independent_and_newline_terminated() -> None:
    a = {"z": [3, 2, 1], "a": {"beta": False, "alpha": 1}}
    b = {"a": {"alpha": 1, "beta": False}, "z": [3, 2, 1]}
    assert canonical_report_bytes(a) == canonical_report_bytes(b)
    assert canonical_report_bytes(a).endswith(b"\n")
    assert json.loads(canonical_report_bytes(a)) == a


def test_writer_uses_explicit_directory_and_binds_sha256(tmp_path) -> None:
    report = {"scientific_status": "EVIDENCE_PARTIAL", "gates": {"example": False}}
    report_path, digest_path = write_v0_20_report(report, tmp_path)
    payload = report_path.read_bytes()
    expected_digest = hashlib.sha256(payload).hexdigest()
    assert report_path == tmp_path / REPORT_FILENAME
    assert digest_path == tmp_path / f"{REPORT_FILENAME}.sha256"
    assert digest_path.read_text(encoding="ascii") == f"{expected_digest}  {REPORT_FILENAME}\n"


def test_canonical_bytes_are_identical_across_python_hash_seeds() -> None:
    repository = Path(__file__).resolve().parents[2]
    script = """
import sys
from experiments.pct_goal_solver.generate_v0_20_report import canonical_report_bytes
from experiments.pct_goal_solver.v0_20_campaign import execute_v0_20_campaign
sys.stdout.buffer.write(canonical_report_bytes(execute_v0_20_campaign()))
"""
    outputs = []
    for seed in ("1", "8271"):
        environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-c", script],
                cwd=repository,
                env=environment,
            )
        )
    assert outputs[0] == outputs[1]
