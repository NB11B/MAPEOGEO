"""Tests for Wave F1 Canonical Alignments and Formulation Integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.generate_alignments_v0_21_f1 import (
    build_manifest,
    generate_alignments,
    get_canonical_objects_f1,
)
from scripts.import_open_logic_f1 import generate_open_logic_declarations
from scripts.import_open_set_theory_f1 import generate_open_set_theory_declarations
from scripts.import_levin_discrete_f1 import generate_levin_discrete_declarations

ROOT = Path(__file__).resolve().parents[1]
ALIGNMENTS_PATH = ROOT / "formal" / "cross_source_alignments_v0_21_f1.json"


def test_alignments_manifest_schema_and_counts() -> None:
    assert ALIGNMENTS_PATH.exists(), f"Alignments file missing at {ALIGNMENTS_PATH}"
    data = json.loads(ALIGNMENTS_PATH.read_text(encoding="utf-8"))

    assert data["schema_version"] == "v0.21-wave-f1-alignments"
    assert data["stage"] == "v0.21_wave_f1"
    assert data["total_canonical_objects"] == 32
    assert data["total_alignments"] == 100
    assert len(data["canonical_objects"]) == 32
    assert len(data["alignments"]) == 100


def test_every_wave_f1_declaration_has_unique_alignment() -> None:
    data = json.loads(ALIGNMENTS_PATH.read_text(encoding="utf-8"))
    alignments = data["alignments"]

    all_source_ids = set()
    for d in generate_open_logic_declarations():
        all_source_ids.add(d.node_id)
    for d in generate_open_set_theory_declarations():
        all_source_ids.add(d.node_id)
    for d in generate_levin_discrete_declarations():
        all_source_ids.add(d.node_id)

    assert len(all_source_ids) == 100

    aligned_source_ids = set()
    align_ids = set()
    canonical_ids = {c["canonical_id"] for c in data["canonical_objects"]}

    for a in alignments:
        align_id = a["alignment_id"]
        assert align_id not in align_ids, f"Duplicate alignment_id: {align_id}"
        align_ids.add(align_id)

        source_id = a["source_node_id"]
        assert source_id in all_source_ids, f"Unknown source_node_id: {source_id}"
        assert source_id not in aligned_source_ids, f"Source declared multiple primary alignments: {source_id}"
        aligned_source_ids.add(source_id)

        target_id = a["target_canonical_id"]
        assert target_id in canonical_ids, f"Unknown canonical target: {target_id}"

        rel = a["relation_type"]
        assert rel in {"SAME_SEMANTICS", "SCOPED_OVERLAP", "RELATED_TO"}

        conf = a["confidence"]
        assert 0.0 < conf <= 1.0
        if rel == "SAME_SEMANTICS":
            assert conf == 1.0
        elif rel == "SCOPED_OVERLAP":
            assert conf >= 0.9
        elif rel == "RELATED_TO":
            assert conf >= 0.8

        check = a["formulation_check"]
        assert "quantifiers_match" in check
        assert "domain_match" in check
        assert "hypotheses_match" in check
        assert len(check["quantifiers_match"]) > 0
        assert len(check["domain_match"]) > 0
        assert len(check["hypotheses_match"]) > 0

    assert aligned_source_ids == all_source_ids
