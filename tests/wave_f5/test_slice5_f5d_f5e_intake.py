from __future__ import annotations

import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[2]


def test_batch_f5d_ode_wellposedness():
    schema_file = ROOT / "schema" / "wave-f5-batch.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8")) if schema_file.is_file() else {}

    batch_file = ROOT / "formal" / "wave_f5" / "batches" / "batch_f5d_ode_wellposedness.json"
    assert batch_file.is_file(), "batch_f5d_ode_wellposedness.json missing"
    data = json.loads(batch_file.read_text(encoding="utf-8"))

    jsonschema.validate(instance=data, schema=schema)
    assert data["package_code"] == "F5D"
    assert len(data["declarations"]) >= 14

    # Verify D01-D14 coverage
    family_codes = {d["family_code"] for d in data["declarations"]}
    for i in range(1, 15):
        assert f"D{i:02d}" in family_codes


def test_batch_f5e_stability_dynamics():
    schema_file = ROOT / "schema" / "wave-f5-batch.schema.json"
    schema = json.loads(schema_file.read_text(encoding="utf-8")) if schema_file.is_file() else {}

    batch_file = ROOT / "formal" / "wave_f5" / "batches" / "batch_f5e_stability_dynamics.json"
    assert batch_file.is_file(), "batch_f5e_stability_dynamics.json missing"
    data = json.loads(batch_file.read_text(encoding="utf-8"))

    jsonschema.validate(instance=data, schema=schema)
    assert data["package_code"] == "F5E"
    assert len(data["declarations"]) >= 14

    # Verify E01-E14 coverage
    family_codes = {d["family_code"] for d in data["declarations"]}
    for i in range(1, 15):
        assert f"E{i:02d}" in family_codes
