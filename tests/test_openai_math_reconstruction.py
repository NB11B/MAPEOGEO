"""Explicit, source-independent dispatch for the complete repository intake."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts import reconstruct_pipeline as pipeline


@pytest.fixture
def isolated_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Keep pipeline orchestration real, replacing only costly stage subprocesses."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "mapeogeo_v0_11_graph.json.gz").write_bytes(b"sealed-fixture")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    commands: list[list[str]] = []

    def unexpected_download(*args: object, **kwargs: object) -> None:
        pytest.fail("source validation or sealed reconstruction attempted a PDF download")

    monkeypatch.setattr(pipeline.urllib.request, "urlretrieve", unexpected_download)

    def execute(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert kwargs["cwd"] == tmp_path
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="stage fixture completed\n", stderr="")

    monkeypatch.setattr(pipeline.subprocess, "run", execute)
    return commands


@pytest.mark.parametrize("source_kind", ["omitted", "missing", "file"])
def test_openai_math_source_rejected_before_historical_work(
    source_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_pipeline: list[list[str]],
) -> None:
    argv = ["reconstruct_pipeline.py", "--target-stage", "openai-math", "--from-scratch"]
    if source_kind != "omitted":
        source = tmp_path / "upstream"
        if source_kind == "file":
            source.write_text("not a checkout", encoding="utf-8")
        argv += ["--openai-math-source", str(source)]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as error:
        pipeline.main()
    assert error.value.code == 2
    assert "--openai-math-source" in capsys.readouterr().err
    assert isolated_pipeline == []
    assert not (tmp_path / "artifacts").exists()


def test_openai_math_dispatches_after_foundation_with_explicit_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_pipeline: list[list[str]],
) -> None:
    source = tmp_path / "upstream checkout"
    source.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["reconstruct_pipeline.py", "--target-stage", "openai-math", "--openai-math-source", str(source)],
    )
    assert pipeline.main() == 0
    scripts = [Path(command[1]).name for command in isolated_pipeline]
    assert scripts[-2:] == ["foundation_intake.py", "openai_math_intake.py"]
    assert scripts.count("openai_math_intake.py") == 1
    assert isolated_pipeline[-1] == [
        sys.executable,
        str(tmp_path / "scripts" / "openai_math_intake.py"),
        "--source-repo",
        str(source),
        "--base-graph",
        str(tmp_path / "artifacts" / "foundation_backfill" / "mapeogeo_foundation_graph.json.gz"),
        "--out-dir",
        str(tmp_path / "artifacts" / "openai_math"),
    ]


@pytest.mark.parametrize("target", [None, "v0.19", "foundation"])
def test_existing_targets_require_no_source_and_do_not_dispatch_intake(
    target: str | None,
    monkeypatch: pytest.MonkeyPatch,
    isolated_pipeline: list[list[str]],
) -> None:
    argv = ["reconstruct_pipeline.py"]
    if target is not None:
        argv += ["--target-stage", target]
    monkeypatch.setattr(sys, "argv", argv)
    assert pipeline.main() == 0
    scripts = [Path(command[1]).name for command in isolated_pipeline]
    assert "openai_math_intake.py" not in scripts
    assert scripts[-1] == (
        "foundation_intake.py" if target == "foundation" else "complex_analysis_intake_v0_19.py"
    )
