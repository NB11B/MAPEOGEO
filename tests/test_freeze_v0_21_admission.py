from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "freeze_v0_21_admission.py"


def _load_module():
    assert MODULE_PATH.exists(), "v0.21 freeze module must exist"
    spec = importlib.util.spec_from_file_location("freeze_v0_21_admission", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(node_id: str, structured_id: str, digest: str) -> dict:
    return {
        "node_id": node_id,
        "node_type": "SOURCE_DECLARATION",
        "source_id": "SRC",
        "repository": "owner/repo",
        "revision": "1" * 40,
        "structured_id": structured_id,
        "decl_type": "THEOREM",
        "source_path": "chapter.tex",
        "line_start": 1,
        "line_end": 2,
        "statement_sha256": digest,
        "char_count": 10,
        "extraction_method": "latex-theorem-environment",
        "parser_version": "v0.21.1",
        "canonical_status": "UNRESOLVED",
        "formal_status": "UNFORMALIZED",
        "executable_status": "UNTESTED",
    }


def test_freeze_records_occurrences_unique_statements_and_duplicate_groups(tmp_path: Path):
    module = _load_module()
    report = {
        "schema_version": "v0.21",
        "source_count": 1,
        "admitted_declaration_count": 3,
        "counts_by_source": {"SRC": 3},
        "sources": [{
            "source_id": "SRC",
            "repository": "owner/repo",
            "revision": "1" * 40,
            "parser": "latex",
            "license": "CC-BY-4.0",
            "scope": "test",
        }],
        "declarations": [
            _row("n1", "t1", "a" * 64),
            _row("n2", "t2", "a" * 64),
            _row("n3", "t3", "b" * 64),
        ],
    }
    report_path = tmp_path / "live.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    declarations_path = tmp_path / "declarations.json.gz"
    evidence_path = tmp_path / "manifest.json"

    manifest = module.freeze_admission_report(report_path, declarations_path, evidence_path)
    assert manifest["admitted_source_occurrences"] == 3
    assert manifest["unique_statement_bodies"] == 2
    assert manifest["duplicate_statement_occurrences"] == 1
    assert manifest["duplicate_statement_hash_groups"] == 1
    assert manifest["per_source"]["SRC"]["admitted_source_occurrences"] == 3
    assert manifest["per_source"]["SRC"]["unique_statement_bodies"] == 2

    with gzip.open(declarations_path, "rt", encoding="utf-8") as handle:
        frozen = json.load(handle)
    assert frozen["schema_version"] == "v0.21"
    assert len(frozen["declarations"]) == 3
    assert all("statement_text" not in row and "body" not in row for row in frozen["declarations"])
    assert json.loads(evidence_path.read_text(encoding="utf-8")) == manifest


def test_freeze_is_byte_deterministic(tmp_path: Path):
    module = _load_module()
    report = {
        "schema_version": "v0.21",
        "source_count": 1,
        "admitted_declaration_count": 1,
        "counts_by_source": {"SRC": 1},
        "sources": [{
            "source_id": "SRC",
            "repository": "owner/repo",
            "revision": "1" * 40,
            "parser": "latex",
            "license": "CC-BY-4.0",
            "scope": "test",
        }],
        "declarations": [_row("n1", "t1", "a" * 64)],
    }
    report_path = tmp_path / "live.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    a_gz, b_gz = tmp_path / "a.gz", tmp_path / "b.gz"
    a_ev, b_ev = tmp_path / "a.json", tmp_path / "b.json"
    module.freeze_admission_report(report_path, a_gz, a_ev)
    module.freeze_admission_report(report_path, b_gz, b_ev)
    assert a_gz.read_bytes() == b_gz.read_bytes()
    assert a_ev.read_bytes() == b_ev.read_bytes()
