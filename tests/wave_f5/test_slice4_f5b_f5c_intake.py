from __future__ import annotations

import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[2]


def test_batch_f5b_functional_analysis():
    schema_file = ROOT / "schema" / "wave-f5-batch.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8")) if schema_file.is_file() else {}

    batch_file = ROOT / "formal" / "wave_f5" / "batches" / "batch_f5b_functional_analysis.json"
    assert batch_file.is_file(), "batch_f5b_functional_analysis.json missing"
    data = json.loads(batch_file.read_text(encoding="utf-8"))

    jsonschema.validate(instance=data, schema=schema)
    assert data["package_code"] == "F5B"
    assert len(data["declarations"]) >= 16

    # Verify B01-B16 coverage
    family_codes = {d["family_code"] for d in data["declarations"]}
    for i in range(1, 17):
        assert f"B{i:02d}" in family_codes


def test_batch_f5c_operator_theory():
    schema_file = ROOT / "schema" / "wave-f5-batch.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8")) if schema_file.is_file() else {}

    batch_file = ROOT / "formal" / "wave_f5" / "batches" / "batch_f5c_operator_theory.json"
    assert batch_file.is_file(), "batch_f5c_operator_theory.json missing"
    data = json.loads(batch_file.read_text(encoding="utf-8"))

    jsonschema.validate(instance=data, schema=schema)
    assert data["package_code"] == "F5C"
    assert len(data["declarations"]) >= 14

    # Verify C01-C14 coverage
    family_codes = {d["family_code"] for d in data["declarations"]}
    for i in range(1, 15):
        assert f"C{i:02d}" in family_codes
