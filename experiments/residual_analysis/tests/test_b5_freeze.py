"""Unit tests for M5 and B5 sealing and manifest integrity."""

from pathlib import Path
import json
from experiments.residual_analysis.seal_m5 import seal_m5_and_b5, sha256_file

def test_seal_m5_and_b5(tmp_path: Path):
    res = seal_m5_and_b5(tmp_path)
    assert res["b5_count"] == 3218

    # Verify manifest exists and matches hash
    manifest_file = tmp_path / "B5_freeze_manifest.json"
    assert manifest_file.exists()
    computed_hash = sha256_file(manifest_file)
    assert computed_hash == res["manifest_sha256"]

    # Verify sha256 file
    sha_file = tmp_path / "B5_freeze_manifest.sha256"
    assert sha_file.exists()
    assert computed_hash in sha_file.read_text(encoding="utf-8")

    # Verify B5 jsonl population
    b5_file = tmp_path / "B5_explanatory_boundary.jsonl"
    lines = b5_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3218
    first_record = json.loads(lines[0])
    assert "boundary_id" in first_record
    assert "failure_projection" in first_record
    assert first_record["tested_neighborhood_depth"] == 6

    # Verify M5 spec
    m5_file = tmp_path / "M5_grammar_specification.json"
    m5_data = json.loads(m5_file.read_text(encoding="utf-8"))
    assert m5_data["grammar_name"] == "M5"
    assert "Pi" in m5_data["coordinates"]
    assert m5_data["status"] == "SEALED_FROZEN"
