"""Fail-closed provenance for the active v0.20 integrity report."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_mathematical_integrity_report.py"
FOUNDATION_AMENDMENTS_SHA256 = (
    "ffa3cbbc4b6a2b1f580df71d61ad24522d5aafcc1e5062de6cb559e28b16adae"
)
DEPENDENCY_LOCK_SHA256 = (
    "d04d5fc31fd029919377fd445048e3911bebb984e4fddec3e63eaaad268023f9"
)


def _run_generator(output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--out", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_generator_binds_live_foundation_and_executable_registries(tmp_path: Path) -> None:
    """Removing live-registry provenance must make report regeneration fail this test."""

    output = tmp_path / "report.json"
    completed = _run_generator(output)
    assert completed.returncode == 0, completed.stderr

    report = json.loads(output.read_text(encoding="utf-8"))
    provenance = report["provenance"]
    assert provenance["foundation_amendment_manifest"]["raw_sha256"] == (
        FOUNDATION_AMENDMENTS_SHA256
    )
    assert provenance["foundation_amendment_manifest"]["amendment_count"] == 84
    assert provenance["foundation_amendment_manifest"]["historical_row_count"] == 176
    assert provenance["foundation_declaration_registry"]["entry_count"] == 176
    assert provenance["foundation_contract_registry"]["entry_count"] == 1
    assert provenance["foundation_contract_registry"]["verified_subject_count"] == 1
    assert provenance["runtime_dependency_lock"] == {
        "path": "requirements-math-rigor-v0-20.lock",
        "raw_sha256": DEPENDENCY_LOCK_SHA256,
    }


def test_generator_binds_producer_tree_without_self_referential_commit(
    tmp_path: Path,
) -> None:
    """Replacing producer code must change a content identity, never a Git label."""

    output = tmp_path / "report.json"
    completed = _run_generator(output)
    assert completed.returncode == 0, completed.stderr
    provenance = json.loads(output.read_text(encoding="utf-8"))["provenance"]

    source = provenance["producer_source_tree"]
    assert source["file_count"] > 20
    assert len(source["sha256"]) == 64
    assert int(source["sha256"], 16) >= 0
    assert "scripts/import_foundation_backfill.py" in source["files"]
    assert "scripts/foundation_contracts.py" in source["files"]
    assert "scripts/generate_mathematical_integrity_report.py" in source["files"]
    assert not any("commit" in key.lower() for key in provenance)


def test_generator_is_byte_deterministic_and_ends_with_newline(tmp_path: Path) -> None:
    """Nondeterministic ordering or formatting must change this observable output."""

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first_run = _run_generator(first)
    second_run = _run_generator(second)
    assert first_run.returncode == 0, first_run.stderr
    assert second_run.returncode == 0, second_run.stderr
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().endswith(b"\n")


def test_generator_replaces_forged_provenance_in_base_report(tmp_path: Path) -> None:
    """A hand-edited provenance block must not survive regeneration."""

    base = tmp_path / "base.json"
    report = json.loads(
        (ROOT / "evidence" / "v0_20_mathematical_integrity_report.json").read_text(
            encoding="utf-8"
        )
    )
    report["provenance"] = {
        "foundation_amendment_manifest": {
            "raw_sha256": "0" * 64,
        }
    }
    base.write_text(json.dumps(report), encoding="utf-8")
    output = tmp_path / "report.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--base-report",
            str(base),
            "--out",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    generated = json.loads(output.read_text(encoding="utf-8"))
    assert generated["provenance"]["foundation_amendment_manifest"][
        "raw_sha256"
    ] == FOUNDATION_AMENDMENTS_SHA256


def test_generator_rejects_forged_scientific_body_and_writes_nothing(
    tmp_path: Path,
) -> None:
    """Provenance regeneration must not bless a forged scientific claim body."""

    base = tmp_path / "forged.json"
    report = json.loads(
        (ROOT / "evidence" / "v0_20_mathematical_integrity_report.json").read_text(
            encoding="utf-8"
        )
    )
    report["sealed_inputs"]["v0_11_graph_sha256"] = "0" * 64
    base.write_text(json.dumps(report), encoding="utf-8")
    output = tmp_path / "report.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--base-report",
            str(base),
            "--out",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "scientific report body differs" in completed.stderr
    assert not output.exists()


def test_generator_rejects_duplicate_keys_and_writes_nothing(tmp_path: Path) -> None:
    """JSON duplicate-key ambiguity must fail before publishing evidence."""

    base = tmp_path / "duplicate.json"
    base.write_text(
        '{"schema_version":"v0.20-mathematical-integrity-report",'
        '"schema_version":"forged"}\n',
        encoding="utf-8",
    )
    output = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--base-report",
            str(base),
            "--out",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "duplicate JSON key" in completed.stderr
    assert not output.exists()


def test_committed_report_is_exact_generator_output(tmp_path: Path) -> None:
    """Stale hand-edited evidence must differ from the generated candidate."""

    output = tmp_path / "report.json"
    completed = _run_generator(output)
    assert completed.returncode == 0, completed.stderr
    committed = ROOT / "evidence" / "v0_20_mathematical_integrity_report.json"
    assert output.read_bytes() == committed.read_bytes()


def test_foundation_manifest_literal_matches_raw_repository_bytes() -> None:
    """The frozen cross-branch digest must bind raw bytes, not parsed JSON."""

    path = ROOT / "formal" / "foundation_mathematical_amendments_v0_20.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == FOUNDATION_AMENDMENTS_SHA256
