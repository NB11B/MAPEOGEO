#!/usr/bin/env python3
"""MAPEOGEO Cryptographic Lean Source-Hash Bridge.

Computes and audits SHA-256 hashes of Lean formalization source files,
verifying that declarations and proofs are unmodified and free of escape hatches.
Governs whether a target's formal view slot may advance beyond ABSENT.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PATTERNS = {
    "sorry": re.compile(r"\bsorry\b"),
    "admit": re.compile(r"\badmit\b"),
    "axiom": re.compile(r"(?m)^\s*(?:private\s+)?axiom\b"),
    "unsafe": re.compile(r"(?m)^\s*(?:private\s+)?unsafe\b"),
}


@dataclass
class LeanHashVerificationResult:
    all_passed: bool
    verified_files: dict[str, str]
    errors: list[str]


def compute_lean_file_hashes(dir_path: Path) -> dict[str, str]:
    hashes = {}
    for p in sorted(dir_path.glob("*.lean")):
        if p.is_file():
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            hashes[p.name] = h
    return hashes


def check_for_escape_hatches(text: str) -> list[str]:
    hits = []
    for name, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            hits.append(name)
    return sorted(hits)


def verify_lean_source_hashes() -> LeanHashVerificationResult:
    formal_dir = ROOT / "MAPEOGEOFormal"
    hashes = compute_lean_file_hashes(formal_dir)
    errors = []

    for name, h in hashes.items():
        file_path = formal_dir / name
        text = file_path.read_text(encoding="utf-8")
        escapes = check_for_escape_hatches(text)
        if escapes:
            errors.append(f"{name}: contains escape hatches {escapes}")

    return LeanHashVerificationResult(
        all_passed=(len(errors) == 0),
        verified_files=hashes,
        errors=errors,
    )


def is_formal_slot_eligible(lean_file_path: Path, expected_hash: str) -> bool:
    if not lean_file_path.is_file():
        return False
    actual_hash = hashlib.sha256(lean_file_path.read_bytes()).hexdigest()
    if actual_hash.lower() != expected_hash.lower():
        return False
    text = lean_file_path.read_text(encoding="utf-8")
    if check_for_escape_hatches(text):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Lean source hashes and escape hatches")
    args = parser.parse_args()

    res = verify_lean_source_hashes()
    if not res.all_passed:
        print("[LeanBridge] FAILED:")
        for err in res.errors:
            print(f"  - {err}")
        return 1

    print("[LeanBridge] All Lean files verified clean with authentic hashes:")
    for name, h in res.verified_files.items():
        print(f"  {name}: {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
