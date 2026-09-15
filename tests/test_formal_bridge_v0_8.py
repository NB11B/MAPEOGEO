from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN = {
    "sorry": re.compile(r"\bsorry\b"),
    "admit": re.compile(r"\badmit\b"),
    "axiom_declaration": re.compile(r"(?m)^\s*(?:private\s+)?axiom\b"),
    "unsafe_declaration": re.compile(r"(?m)^\s*(?:private\s+)?unsafe\b"),
}


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
    hits = [name for name, pattern in FORBIDDEN.items() if pattern.search(text)]
    assert not hits, hits


def test_toolchain_and_mathlib_are_pinned_together():
    assert (ROOT / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.33.1"
    lake = (ROOT / "lakefile.lean").read_text()
    assert 'package MAPEOGEOFormal' in lake
    assert 'require mathlib from git "https://github.com/leanprover-community/mathlib4.git" @ "v4.33.1"' in lake
    manifest = json.loads((ROOT / "lake-manifest.json").read_text())
    mathlib = next(p for p in manifest["packages"] if p["name"] == "mathlib")
    assert mathlib["inputRev"] == "v4.33.1"
