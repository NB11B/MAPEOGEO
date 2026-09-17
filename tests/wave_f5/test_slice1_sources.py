from __future__ import annotations

import json
from pathlib import Path
import jsonschema

from scripts.wave_f5_source_pins import audit_source_registry, load_source_registry

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_SOURCE_KEYS = {"VN", "TE", "LR", "LD", "AX", "HU", "FN", "AR"}


def test_source_registry_schema_and_keys():
    schema_file = ROOT / "schema" / "wave-f5-source.schema.json"
    assert schema_file.is_file(), "schema/wave-f5-source.schema.json missing"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    registry_file = ROOT / "formal" / "wave_f5" / "source_registry.json"
    assert registry_file.is_file(), "formal/wave_f5/source_registry.json missing"
    data = load_source_registry(registry_file)

    # Validate against schema
    jsonschema.validate(instance=data, schema=schema)

    # Verify presence of primary sources
    sources_by_key = {s["source_key"]: s for s in data["sources"]}
    assert REQUIRED_SOURCE_KEYS.issubset(set(sources_by_key.keys()))

    # Verify export policy rules
    for s in data["sources"]:
        assert s["export_policy"] in {
            "METADATA_LOCATORS_AND_SUMMARIES_ONLY",
            "OPEN_SOURCE_RESTRICTED_REDISTRIBUTION",
            "OPEN_ACCESS_CREATIVE_COMMONS",
            "PHYSICAL_HOLDINGS_OCR_LOCATORS_ONLY",
        }


def test_source_audit_passes_cleanly():
    res = audit_source_registry()
    assert res.all_passed is True
    assert len(res.errors) == 0
    assert len(res.verified_sources) >= 8
