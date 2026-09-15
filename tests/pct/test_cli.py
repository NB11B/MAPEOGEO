"""Unit and smoke tests for PCT v0.10 CLI runner and artifact validator."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_cli_runner_and_validator(tmp_path: Path):
    manifest_path = Path("evidence/v0_10_pct_preregistration.json")
    out_dir = tmp_path / "pct_out"

    cmd_runner = [
        sys.executable,
        "scripts/pct_v0_10.py",
        "--manifest",
        str(manifest_path),
        "--out-dir",
        str(out_dir),
        "--repository-commit",
        "TEST_COMMIT_CLI",
    ]
    res_runner = subprocess.run(cmd_runner, capture_output=True, text=True)
    assert res_runner.returncode == 0, f"Runner failed:\nSTDOUT: {res_runner.stdout}\nSTDERR: {res_runner.stderr}"

    validity_data = json.loads((out_dir / "validity.json").read_text(encoding="utf-8"))
    assert validity_data["ENGINE_VALIDITY"] == "PASS"

    # Run validator
    cmd_val = [
        sys.executable,
        "tests/validate_pct_v0_10.py",
        str(out_dir),
    ]
    res_val = subprocess.run(cmd_val, capture_output=True, text=True)
    assert res_val.returncode == 0, f"Validator failed:\nSTDOUT: {res_val.stdout}\nSTDERR: {res_val.stderr}"
    assert "MAPEOGEO_PCT_V0_10_ARTIFACT_VALIDATION: PASS" in res_val.stdout
