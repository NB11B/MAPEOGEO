"""Tests for Wave F1 source ingestion modules and zero-prose manifests.

Validates:
- Exact declaration counts across Open Logic (35), Open Set Theory (30), Levin Discrete (35).
- Zero-prose persistence invariant (no forbidden text keys in serialized manifests).
- Locator format fidelity and deterministic SHA-256 statement hashes.
- Representation profile validity (EO/GEO tags, direct_status, representation_kinds).
- Internal structural reference resolution.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import pytest

from scripts.import_open_logic_f1 import (
    generate_open_logic_declarations,
    get_raw_open_logic_declarations,
    source_identity as logic_source_identity,
)
from scripts.import_open_set_theory_f1 import (
    generate_open_set_theory_declarations,
    get_raw_open_set_theory_declarations,
    source_identity as set_theory_source_identity,
)
from scripts.import_levin_discrete_f1 import (
    generate_levin_discrete_declarations,
    get_raw_levin_discrete_declarations,
    source_identity as levin_source_identity,
)

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def test_open_logic_declarations_count_and_hashes() -> None:
    decls = generate_open_logic_declarations()
    assert len(decls) == 35, f"Expected 35 Open Logic declarations, got {len(decls)}"

    raw = get_raw_open_logic_declarations()
    assert len(raw) == 35

    ids = set()
    for d in decls:
        assert d.node_id not in ids, f"Duplicate node_id: {d.node_id}"
        ids.add(d.node_id)
        assert d.source_id == "OPEN_LOGIC_PROJECT_2024"
        assert d.corpus == "OPEN_LOGIC"
        assert d.locator.startswith("OpenLogic:")
        assert SHA256_RE.match(d.statement_sha256)
        assert d.char_count > 0
        assert d.extraction_mode == "SOURCE_PARSE"

        profile = d.representation_profile
        assert "direct_status" in profile
        assert profile["direct_status"] in {"DUAL_DIRECT", "EO_ONLY_DIRECT", "GEO_ONLY_DIRECT"}
        assert len(profile["representation_kinds"]) > 0


def test_open_set_theory_declarations_count_and_hashes() -> None:
    decls = generate_open_set_theory_declarations()
    assert len(decls) == 30, f"Expected 30 Open Set Theory declarations, got {len(decls)}"

    raw = get_raw_open_set_theory_declarations()
    assert len(raw) == 30

    ids = set()
    for d in decls:
        assert d.node_id not in ids, f"Duplicate node_id: {d.node_id}"
        ids.add(d.node_id)
        assert d.source_id == "OPEN_SET_THEORY_BUTTON_2024"
        assert d.corpus == "OPEN_SET_THEORY"
        assert d.locator.startswith("ButtonSetTheory:")
        assert SHA256_RE.match(d.statement_sha256)
        assert d.char_count > 0
        assert d.extraction_mode == "SOURCE_PARSE"

        profile = d.representation_profile
        assert "direct_status" in profile
        assert profile["direct_status"] in {"DUAL_DIRECT", "EO_ONLY_DIRECT", "GEO_ONLY_DIRECT"}
        assert len(profile["representation_kinds"]) > 0


def test_levin_discrete_declarations_count_and_hashes() -> None:
    decls = generate_levin_discrete_declarations()
    assert len(decls) == 35, f"Expected 35 Levin Discrete declarations, got {len(decls)}"

    raw = get_raw_levin_discrete_declarations()
    assert len(raw) == 35

    ids = set()
    for d in decls:
        assert d.node_id not in ids, f"Duplicate node_id: {d.node_id}"
        ids.add(d.node_id)
        assert d.source_id == "LEVIN_DISCRETE_MATH_4E_2024"
        assert d.corpus == "LEVIN_DISCRETE"
        assert d.locator.startswith("LevinDiscrete:")
        assert SHA256_RE.match(d.statement_sha256)
        assert d.char_count > 0
        assert d.extraction_mode == "SOURCE_PARSE"

        profile = d.representation_profile
        assert "direct_status" in profile
        assert profile["direct_status"] in {"DUAL_DIRECT", "EO_ONLY_DIRECT", "GEO_ONLY_DIRECT"}
        assert len(profile["representation_kinds"]) > 0


def test_zero_prose_manifest_files() -> None:
    manifest_paths = [
        ROOT / "formal" / "open_logic_manifest_v0_21.json",
        ROOT / "formal" / "open_set_theory_manifest_v0_21.json",
        ROOT / "formal" / "levin_discrete_manifest_v0_21.json",
    ]

    for path in manifest_paths:
        assert path.exists(), f"Manifest file missing: {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "source_identity" in data
        assert "declarations" in data
        assert data["total_declarations"] == len(data["declarations"])

        for decl in data["declarations"]:
            for forbidden in FORBIDDEN_KEYS:
                assert forbidden not in decl, f"Found forbidden key '{forbidden}' in {decl.get('node_id')}"
            assert "statement_sha256" in decl
            assert SHA256_RE.match(decl["statement_sha256"])
            assert "locator" in decl
            assert len(decl["locator"]) > 0


def test_structural_references_resolve_internally() -> None:
    all_decls = {}
    for d in generate_open_logic_declarations():
        all_decls[d.node_id] = d
    for d in generate_open_set_theory_declarations():
        all_decls[d.node_id] = d
    for d in generate_levin_discrete_declarations():
        all_decls[d.node_id] = d

    assert len(all_decls) == 100

    for node_id, decl in all_decls.items():
        for ref in decl.structural_refs:
            assert ref in all_decls, f"Dangling structural reference {ref} from {node_id}"
