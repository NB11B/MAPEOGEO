from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "formal" / "source_registry_v0_21.json"
MODULE_PATH = ROOT / "scripts" / "source_registry_v0_21.py"

EXPECTED = {
    "OPEN_LOGIC_PROJECT": ("OpenLogicProject/OpenLogic", "1e960beff9ed7835bf3e3f1335e21af3439cd107", "latex"),
    "LEVIN_DISCRETE": ("oscarlevin/discrete-book", "e258a377b4ef7ab63c647457430e98fbb4c7c3bb", "pretext"),
    "JUDSON_AATA": ("twjudson/aata", "3069910e3ded72ff5e18837a97a0e810c92790e2", "pretext"),
    "LEBL_BASIC_ANALYSIS": ("jirilebl/ra", "e21ec524ca7d54f800c693b948020c188d21d01f", "latex"),
    "LEBL_DIFFYQS": ("jirilebl/diffyqs", "658bcae9fb710f3fae2c9da4ca4524ce157453af", "latex"),
}


def _load_module():
    assert MODULE_PATH.exists(), "source registry validator module must exist"
    spec = importlib.util.spec_from_file_location("source_registry_v0_21", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registry_is_exactly_pinned_to_reviewed_sources():
    assert REGISTRY_PATH.exists(), "v0.21 source registry must exist"
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    records = {row["source_id"]: row for row in data["sources"]}
    assert set(records) == set(EXPECTED)
    for source_id, (repo, revision, parser) in EXPECTED.items():
        row = records[source_id]
        assert row["repository"] == repo
        assert row["revision"] == revision
        assert len(row["revision"]) == 40
        int(row["revision"], 16)
        assert row["parser"] == parser
        assert row["license"]
        assert row["status"] == "ACTIVE"


def test_registry_validator_rejects_moving_refs(tmp_path: Path):
    module = _load_module()
    bad = {
        "schema_version": "v0.21",
        "sources": [{
            "source_id": "BAD",
            "repository": "owner/repo",
            "revision": "main",
            "parser": "latex",
            "license": "CC-BY-4.0",
            "status": "ACTIVE",
            "include_globs": ["**/*.tex"],
            "exclude_globs": [],
        }],
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="40-character commit SHA"):
        module.load_source_registry(path)


def test_registry_validator_rejects_unknown_parser(tmp_path: Path):
    module = _load_module()
    bad = {
        "schema_version": "v0.21",
        "sources": [{
            "source_id": "BAD",
            "repository": "owner/repo",
            "revision": "0" * 40,
            "parser": "llm",
            "license": "CC-BY-4.0",
            "status": "ACTIVE",
            "include_globs": ["**/*"],
            "exclude_globs": [],
        }],
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported parser"):
        module.load_source_registry(path)
