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


def test_pinch_quartet_bindings_are_valid():
    cfg = json.loads((ROOT / "formal" / "pinch_quartet_v0_10.json").read_text(encoding="utf-8"))
    assert cfg["schema_version"] == "0.10"
    assert cfg["stage"] == "S4_PINCH_QUARTET_PROMOTION"
    assert len(cfg["pinch_targets"]) == 4
    targets = cfg["pinch_targets"]
    assert len({t["source_id"] for t in targets}) == 4
    assert len({t["lean_decl"] for t in targets}) == 4
    assert all(len(t["statement_sha256"]) == 64 for t in targets)


def test_pinch_quartet_lean_file_has_all_declarations_and_no_escape_hatches():
    text = (ROOT / "MAPEOGEOFormal" / "PinchQuartet.lean").read_text(encoding="utf-8")
    cfg = json.loads((ROOT / "formal" / "pinch_quartet_v0_10.json").read_text(encoding="utf-8"))
    for t in cfg["pinch_targets"]:
        short_name = t["lean_decl"].split(".")[-1]
        assert short_name in text, f"Missing declaration: {short_name}"
    hits = [name for name, pattern in FORBIDDEN.items() if pattern.search(text)]
    assert not hits, hits


def test_view_shear_resolution_preserves_eo_only_and_dual_direct():
    cfg = json.loads((ROOT / "formal" / "pinch_quartet_v0_10.json").read_text(encoding="utf-8"))
    by_id = {t["source_id"]: t for t in cfg["pinch_targets"]}
    assert by_id["srcdecl:proposition:3_14"]["view_shear_resolution"] == "PRESERVED_EO_ONLY"
    assert by_id["srcdecl:proposition:3_13"]["view_shear_resolution"] == "PRESERVED_EO_ONLY"
    assert by_id["srcdecl:proposition:4_4"]["view_shear_resolution"] == "PRESERVED_EO_ONLY"
    assert by_id["srcdecl:theorem:27_10"]["view_shear_resolution"] == "CONFIRMED_DUAL_DIRECT"
