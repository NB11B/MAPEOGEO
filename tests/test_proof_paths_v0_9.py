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


def test_proof_paths_config_is_valid():
    cfg = json.loads((ROOT / "formal" / "proof_paths_v0_9.json").read_text(encoding="utf-8"))
    assert cfg["schema_version"] == "0.9"
    assert cfg["stage"] == "S5_PROOF_PATH"
    assert len(cfg["targets"]) == 4
    assert len(cfg["support_frontier"]) == 6
    assert len({x["source_id"] for x in cfg["support_frontier"]}) == 6
    assert len({x["lean_decl"] for x in cfg["support_frontier"]}) == 6
    assert all(len(x["statement_sha256"]) == 64 for x in cfg["support_frontier"])


def test_proof_paths_lean_file_has_all_declarations_and_no_escape_hatches():
    text = (ROOT / "MAPEOGEOFormal" / "ProofPaths.lean").read_text(encoding="utf-8")
    cfg = json.loads((ROOT / "formal" / "proof_paths_v0_9.json").read_text(encoding="utf-8"))
    for x in cfg["support_frontier"]:
        short_name = x["lean_decl"].split(".")[-1]
        assert short_name in text, f"Missing declaration: {short_name}"
    hits = [name for name, pattern in FORBIDDEN.items() if pattern.search(text)]
    assert not hits, hits


def test_v0_9_proof_edges_and_repaired_wounds():
    cfg = json.loads((ROOT / "formal" / "proof_paths_v0_9.json").read_text(encoding="utf-8"))
    assert "path_edges" in cfg
    assert len(cfg["path_edges"]) == 6
    assert "known_reference_wounds" in cfg
    assert len(cfg["known_reference_wounds"]) >= 1
    repaired = cfg["known_reference_wounds"][0]
    assert repaired["source"] == "srcdecl:proposition:6_11"
    assert repaired["audited_target"] == "srcdecl:proposition:3_15"
    assert repaired["legacy_resolved_target"] == "srcdecl:proposition:3_18"

