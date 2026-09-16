from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "source_admission_v0_21.py"


def _load_module():
    assert MODULE_PATH.exists(), "source admission module must exist"
    spec = importlib.util.spec_from_file_location("source_admission_v0_21", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(node_id: str, structured_id: str, **extra) -> dict:
    row = {
        "node_id": node_id,
        "node_type": "SOURCE_DECLARATION",
        "source_id": "SRC",
        "repository": "owner/repo",
        "revision": "1" * 40,
        "structured_id": structured_id,
        "decl_type": "THEOREM",
        "source_path": "chapter.tex",
        "line_start": 1,
        "line_end": 3,
        "statement_sha256": "a" * 64,
        "char_count": 10,
        "extraction_method": "latex-theorem-environment",
        "parser_version": "v0.21.1",
        "canonical_status": "UNRESOLVED",
        "formal_status": "UNFORMALIZED",
        "executable_status": "UNTESTED",
    }
    row.update(extra)
    return row


def test_admission_rejects_duplicate_node_identity():
    module = _load_module()
    rows = [_row("same", "a"), _row("same", "b")]
    with pytest.raises(ValueError, match="duplicate node_id"):
        module.validate_admitted_metadata(rows)


def test_admission_rejects_duplicate_structured_source_identity():
    module = _load_module()
    rows = [_row("n1", "same"), _row("n2", "same")]
    with pytest.raises(ValueError, match="duplicate source declaration identity"):
        module.validate_admitted_metadata(rows)


def test_admission_rejects_persisted_prose_keys():
    module = _load_module()
    rows = [_row("n1", "a", statement_text="invented prose")]
    with pytest.raises(ValueError, match="forbidden persisted source prose"):
        module.validate_admitted_metadata(rows)


def test_admission_sort_is_deterministic():
    module = _load_module()
    rows = [
        _row("n2", "z", source_path="b.tex", line_start=9),
        _row("n1", "a", source_path="a.tex", line_start=2),
    ]
    assert [row["node_id"] for row in module.sort_admitted_metadata(rows)] == ["n1", "n2"]


def test_checkout_fetches_exact_sha_and_fails_on_revision_mismatch(tmp_path: Path, monkeypatch):
    module = _load_module()
    calls = []

    def fake_git(cwd: Path, *args: str) -> str:
        calls.append(args)
        if args == ("rev-parse", "HEAD"):
            return "f" * 40
        return ""

    monkeypatch.setattr(module, "_run_git", fake_git)
    spec = SimpleNamespace(
        source_id="PINNED",
        repository="owner/repo",
        revision="1" * 40,
    )
    with pytest.raises(ValueError, match="revision mismatch"):
        module.checkout_pinned_source(spec, tmp_path)
    assert ("fetch", "--depth=1", "origin", "1" * 40) in calls
    assert ("checkout", "--detach", "FETCH_HEAD") in calls
