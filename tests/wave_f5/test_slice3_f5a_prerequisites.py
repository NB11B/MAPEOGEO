from __future__ import annotations

import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[2]


def test_batch_f5a_topology_function_spaces():
    schema_file = ROOT / "schema" / "wave-f5-batch.schema.json"
    assert schema_file.is_file(), "schema/wave-f5-batch.schema.json missing"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    batch_file = ROOT / "formal" / "wave_f5" / "batches" / "batch_f5a_topology_function_spaces.json"
    assert batch_file.is_file(), "batch_f5a_topology_function_spaces.json missing"
    data = json.loads(batch_file.read_text(encoding="utf-8"))

    jsonschema.validate(instance=data, schema=schema)
    assert data["package_code"] == "F5A"
    assert len(data["declarations"]) >= 14

    # Check that critical families A01-A14 are covered
    family_codes = {d["family_code"] for d in data["declarations"]}
    for i in range(1, 15):
        assert f"A{i:02d}" in family_codes


def test_dependencies_registry():
    deps_file = ROOT / "formal" / "wave_f5" / "dependencies.json"
    assert deps_file.is_file(), "dependencies.json missing"
    data = json.loads(deps_file.read_text(encoding="utf-8"))

    assert data["schema_version"] == "0.22"
    assert len(data["dependencies"]) > 0
