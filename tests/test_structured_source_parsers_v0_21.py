from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "structured_source_parsers_v0_21.py"
FORBIDDEN = {"statement_text", "proof_text", "source_prose", "page_image", "statement", "body"}


def _load_module():
    assert MODULE_PATH.exists(), "structured parser module must exist"
    spec = importlib.util.spec_from_file_location("structured_source_parsers_v0_21", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _spec(source_id: str, parser: str, include: tuple[str, ...]):
    return SimpleNamespace(
        source_id=source_id,
        repository="example/source",
        revision="1" * 40,
        parser=parser,
        include_globs=include,
        exclude_globs=(),
    )


def test_pretext_extracts_only_structured_statements_and_persists_no_prose(tmp_path: Path):
    module = _load_module()
    source = tmp_path / "book.ptx"
    source.write_text(
        """<pretext>\n"
        "  <section xml:id=\"s1\">\n"
        "    <p>This ordinary paragraph must not become a declaration.</p>\n"
        "    <definition xml:id=\"def-group\"><statement><p>A group has an identity element.</p></statement></definition>\n"
        "    <theorem xml:id=\"thm-cancel\"><statement><p>Cancellation holds in every group.</p></statement><proof><p>source proof</p></proof></theorem>\n"
        "  </section>\n"
        "</pretext>\n""",
        encoding="utf-8",
    )
    decls = module.extract_pretext_declarations(tmp_path, _spec("TEST_PRETEXT", "pretext", ("*.ptx",)))
    assert [d.structured_id for d in decls] == ["def-group", "thm-cancel"]
    assert [d.decl_type for d in decls] == ["DEFINITION", "THEOREM"]
    assert all(d.source_path == "book.ptx" for d in decls)
    assert all(d.line_start >= 1 and d.line_end >= d.line_start for d in decls)
    assert all(len(d.statement_sha256) == 64 and d.char_count > 0 for d in decls)
    metadata = [d.to_metadata() for d in decls]
    assert all(FORBIDDEN.isdisjoint(row) for row in metadata)
    assert all(row["canonical_status"] == "UNRESOLVED" for row in metadata)


def test_latex_extracts_registered_environments_labels_and_crlf_stably(tmp_path: Path):
    module = _load_module()
    tex = (
        "% ignored comment\r\n"
        "\\begin{definition}\r\n"
        "\\label{def:metric}\r\n"
        "A metric is a function satisfying the metric axioms.\r\n"
        "\\end{definition}\r\n"
        "\\begin{theorem}\r\n"
        "Every convergent sequence is Cauchy.\r\n"
        "\\end{theorem}\r\n"
    )
    (tmp_path / "chapter.tex").write_bytes(tex.encode("utf-8"))
    spec = _spec("TEST_LATEX", "latex", ("*.tex",))
    first = module.extract_latex_declarations(tmp_path, spec)
    second = module.extract_latex_declarations(tmp_path, spec)
    assert len(first) == 2
    assert first[0].structured_id == "def:metric"
    assert first[0].decl_type == "DEFINITION"
    assert first[1].structured_id.startswith("chapter.tex#theorem-")
    assert [d.statement_sha256 for d in first] == [d.statement_sha256 for d in second]
    assert [d.node_id for d in first] == [d.node_id for d in second]
    assert all(FORBIDDEN.isdisjoint(d.to_metadata()) for d in first)


def test_latex_hash_normalizes_only_newline_encoding(tmp_path: Path):
    module = _load_module()
    body = "\\label{lem:x}\nIf x = y then y = x.\n"
    (tmp_path / "a.tex").write_bytes(("\\begin{lemma}\r\n" + body.replace("\n", "\r\n") + "\\end{lemma}\r\n").encode())
    decl = module.extract_latex_declarations(tmp_path, _spec("TEST_LATEX", "latex", ("*.tex",)))[0]
    expected_body = "\\label{lem:x}\nIf x = y then y = x.\n"
    assert decl.statement_sha256 == hashlib.sha256(expected_body.encode("utf-8")).hexdigest()


def test_latex_fails_closed_on_unbalanced_supported_environment(tmp_path: Path):
    module = _load_module()
    (tmp_path / "bad.tex").write_text("\\begin{theorem}\nNo matching end.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unbalanced theorem-like environment"):
        module.extract_latex_declarations(tmp_path, _spec("TEST_LATEX", "latex", ("*.tex",)))
