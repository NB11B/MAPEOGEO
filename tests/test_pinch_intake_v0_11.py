import json
from pathlib import Path

from scripts.formal_bridge_v0_8 import proof_escape_hits


def test_v011_lean_file_has_no_escape_hatches():
    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")
    assert proof_escape_hits(text) == []


def test_all_frozen_scopes_have_fixed_decl_names():
    cfg = json.loads(
        Path("formal/pinch_bindings_v0_11.json")
        .read_text(encoding="utf-8")
    )

    text = Path("MAPEOGEOFormal/PinchV011.lean").read_text(encoding="utf-8")

    expected = [
        x["formal_decl"].split(".")[-1]
        for x in cfg["targets"]
        if x["scope_status"] == "FROZEN"
    ]

    assert len(expected) == 4
    assert all(name in text for name in expected)
