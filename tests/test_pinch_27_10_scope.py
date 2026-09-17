from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lean_decl_renamed_to_fixed_direction_split():
    quartet_text = (ROOT / "MAPEOGEOFormal" / "PinchQuartet.lean").read_text(encoding="utf-8")
    assert "affine_map_split_along_fixed_direction" in quartet_text
    assert "theorem_27_10_affine_isometry_canonical_decomposition" not in quartet_text

    v011_text = (ROOT / "MAPEOGEOFormal" / "PinchV011.lean").read_text(encoding="utf-8")
    assert "affine_map_split_along_fixed_direction" in v011_text


def test_gallier_27_10_binding_demoted_to_scoped_overlap_with_wound():
    bindings_path = ROOT / "formal" / "pinch_bindings_v0_11.json"
    bindings = json.loads(bindings_path.read_text(encoding="utf-8"))

    t27_10 = next((t for t in bindings["targets"] if t["source_id"] == "srcdecl:theorem:27_10"), None)
    assert t27_10 is not None, "srcdecl:theorem:27_10 not found in pinch_bindings_v0_11.json"

    # Must be SCOPED_OVERLAP, never SAME_SEMANTICS or FORMALLY_PROVEN_GENERAL
    assert t27_10.get("relationship") == "SCOPED_OVERLAP"
    assert t27_10.get("relationship") != "SAME_SEMANTICS"
    assert t27_10.get("relationship") != "FORMALLY_PROVEN_GENERAL"

    # Must record WOUND with reason CONTRACT_NARROWER_THAN_SOURCE
    assert "wound" in t27_10
    wound = t27_10["wound"]
    assert wound.get("reason") == "CONTRACT_NARROWER_THAN_SOURCE"
    assert "affine fixed-point split" in wound.get("detail", "").lower() or "fixed direction" in wound.get("detail", "").lower()

    # Formal decl points to the narrowed theorem name
    assert "affine_map_split_along_fixed_direction" in t27_10.get("formal_decl", "")


def test_h_split_requires_explicit_fixed_direction_hypothesis():
    quartet_text = (ROOT / "MAPEOGEOFormal" / "PinchQuartet.lean").read_text(encoding="utf-8")
    # Verify the theorem requires an explicit split witness hypothesis h_split
    assert "h_split : ∃ tau x0 : V, A tau = tau" in quartet_text
