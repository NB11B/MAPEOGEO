from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_bindings_are_unique_and_complete():
    b = json.loads((ROOT / "formal" / "source_bindings_v0_8.json").read_text())
    assert len(b) == 4
    assert len({x["source_id"] for x in b}) == 4
    assert len({x["lean_decl"] for x in b}) == 4
    assert all(len(x["statement_sha256"]) == 64 for x in b)


def test_formal_file_has_all_bound_declarations_and_no_escape_hatches():
    text = (ROOT / "MAPEOGEOFormal" / "SourceBound.lean").read_text()
    b = json.loads((ROOT / "formal" / "source_bindings_v0_8.json").read_text())
    for x in b:
        assert x["lean_decl"].split(".")[-1] in text
    lowered = text.lower()
    for token in ("sorry", "admit", "axiom", "unsafe"):
        assert token not in lowered


def test_toolchain_and_mathlib_are_pinned_together():
    assert (ROOT / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.33.1"
    lake = (ROOT / "lakefile.toml").read_text()
    assert 'rev = "v4.33.1"' in lake
