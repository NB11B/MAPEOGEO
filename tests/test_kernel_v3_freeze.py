"""Test Suite: Cryptographic and Architectural Freeze Verification for Kernel v3."""

import pytest
import json
import hashlib
from pathlib import Path

from experiments.kernel_v3_release import assemble_kernel_v3_release, get_file_sha256

def test_kernel_v3_release_assembly(tmp_path):
    output_dir = tmp_path / "kernel_v3_release_test"
    manifest = assemble_kernel_v3_release(output_dir)

    assert manifest["release_version"] == "v3.0.0"
    assert manifest["grammar_architecture"] == "M6^{++++}"
    assert manifest["dimension_d"] == 6
    assert manifest["alphabet_a"] == 40
    assert manifest["max_composition_depth_c"] == 6
    assert manifest["boundary_population"] == 2416
    assert manifest["boundary_share_percentage"] == 2.09
    assert manifest["regression_baseline_clean_transformations"] == 55800
    assert manifest["total_regressions"] == 0
    assert manifest["status"] == "PRODUCTION_SEALED"

    # Check manifest files exist and hashes match
    for fname, meta in manifest["files"].items():
        fpath = output_dir / fname
        assert fpath.exists(), f"Missing file: {fname}"
        actual_hash = get_file_sha256(fpath)
        assert actual_hash == meta["sha256"], f"Hash mismatch for {fname}"

    # Check sha256 checksum file
    manifest_sha = output_dir / "KERNEL_V3_RELEASE_MANIFEST.sha256"
    assert manifest_sha.exists()
    computed_manifest_hash = get_file_sha256(output_dir / "KERNEL_V3_RELEASE_MANIFEST.json")
    with open(manifest_sha, "r", encoding="utf-8") as f:
        stored_hash = f.read().split()[0]
    assert computed_manifest_hash == stored_hash
