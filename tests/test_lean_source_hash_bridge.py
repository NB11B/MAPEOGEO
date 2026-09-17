from __future__ import annotations

import hashlib
import json
from pathlib import Path
from scripts.check_lean_source_hashes import (
    compute_lean_file_hashes,
    verify_lean_source_hashes,
    is_formal_slot_eligible,
)

ROOT = Path(__file__).resolve().parents[1]


def test_lean_source_hash_computation():
    hashes = compute_lean_file_hashes(ROOT / "MAPEOGEOFormal")
    assert len(hashes) > 0
    assert "PinchQuartet.lean" in hashes
    assert len(hashes["PinchQuartet.lean"]) == 64


def test_lean_source_hash_verification():
    res = verify_lean_source_hashes()
    assert res.all_passed is True
    assert len(res.verified_files) > 0


def test_formal_slot_governance_rule():
    # If lean file is verified and hash matches, formal slot is eligible
    pinch_file = ROOT / "MAPEOGEOFormal" / "PinchQuartet.lean"
    pinch_hash = hashlib.sha256(pinch_file.read_bytes()).hexdigest()

    assert is_formal_slot_eligible(pinch_file, pinch_hash) is True

    # If hash mismatches or file has escape hatch, formal slot is NOT eligible (must remain ABSENT)
    assert is_formal_slot_eligible(pinch_file, "0" * 64) is False
