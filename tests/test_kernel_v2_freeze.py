"""Unit test suite for Kernel v2 release and B5 -> B6 boundary transformation."""

import pytest
from pathlib import Path
import json

from experiments.kernel_v2_release import assemble_kernel_v2_release, get_file_sha256

def test_kernel_v2_assembly_and_conservation(tmp_path: Path):
    res = assemble_kernel_v2_release(tmp_path)
    assert res["b6_count"] == 3034

    # Verify B6 manifest
    b6_manifest_file = tmp_path / "B6_freeze_manifest.json"
    assert b6_manifest_file.exists()
    with open(b6_manifest_file, "r", encoding="utf-8") as f:
        b6_data = json.load(f)

    trans = b6_data["transition_summary"]
    assert trans["b5_total"] == 3218
    assert trans["resolved_by_gamma"] == 184
    assert trans["still_ambiguous"] == 128
    assert trans["not_applicable"] == 2906
    assert trans["b6_total"] == 3034
    assert trans["resolved_by_gamma"] + trans["still_ambiguous"] + trans["not_applicable"] == 3218

    # Verify M6 grammar spec
    m6_file = tmp_path / "M6_grammar_specification.json"
    assert m6_file.exists()
    with open(m6_file, "r", encoding="utf-8") as f:
        m6_data = json.load(f)
    assert "Gamma" in m6_data["coordinates"]
    assert m6_data["coordinates"]["Gamma"]["alphabet"] == ["even", "odd", "graded_mixed", "ungraded"]

    # Verify master manifest
    manifest_file = tmp_path / "KERNEL_V2_RELEASE_MANIFEST.json"
    assert manifest_file.exists()
    computed_hash = get_file_sha256(manifest_file)
    assert computed_hash == res["master_v2_sha256"]

    sha_file = tmp_path / "KERNEL_V2_RELEASE_MANIFEST.sha256"
    assert sha_file.exists()
    assert computed_hash in sha_file.read_text(encoding="utf-8")

def test_original_b5_remains_unmutated():
    b5_orig = Path("artifacts/residual_analysis/B5_explanatory_boundary.jsonl")
    h = get_file_sha256(b5_orig)
    assert h == "24fcf1f051f00fa437041ffc81a0c72cc3f9a782cbb688d71866d9fe50fda5dd"
