from __future__ import annotations

import copy
import gzip
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "rigor_expansion_v0_21.py"
FORBIDDEN_RELATIONS = {
    "SAME_SEMANTICS",
    "SCOPED_OVERLAP",
    "RELATED_TO",
    "REPRESENTS",
    "FORMAL_LINKED",
    "KERNEL_VERIFIED",
    "PROOF_DEPENDENCY",
}


def _load_module():
    assert MODULE_PATH.exists(), "v0.21 graph intake module must exist"
    spec = importlib.util.spec_from_file_location("rigor_expansion_v0_21", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _spec():
    return SimpleNamespace(
        source_id="SRC",
        repository="owner/repo",
        revision="1" * 40,
        parser="latex",
        license="CC-BY-4.0",
        scope="test_scope",
    )


def _row(node_id="srcdecl:v0_21:src:abc", structured_id="thm:x", **changes):
    row = {
        "node_id": node_id,
        "node_type": "SOURCE_DECLARATION",
        "source_id": "SRC",
        "repository": "owner/repo",
        "revision": "1" * 40,
        "structured_id": structured_id,
        "decl_type": "THEOREM",
        "source_path": "chapter.tex",
        "line_start": 10,
        "line_end": 12,
        "statement_sha256": "a" * 64,
        "char_count": 120,
        "extraction_method": "latex-theorem-environment",
        "parser_version": "v0.21.1",
        "canonical_status": "UNRESOLVED",
        "formal_status": "UNFORMALIZED",
        "executable_status": "UNTESTED",
    }
    row.update(changes)
    return row


def _base_graph():
    return {
        "nodes": [
            {"id": "canonical:existing", "type": "CANONICAL_OBJECT", "label": "Existing", "attributes": {"stage": "v0.20"}}
        ],
        "edges": [
            {"id": "e:old", "type": "SAME_SEMANTICS", "source": "old:a", "target": "old:b", "attributes": {"stage": "v0.20"}}
        ],
    }


def test_quarantined_intake_adds_only_provenance_structure():
    module = _load_module()
    graph = module.integrate_quarantined_sources(copy.deepcopy(_base_graph()), [_spec()], [_row()])
    by_id = {node["id"]: node for node in graph["nodes"]}
    decl = by_id["srcdecl:v0_21:src:abc"]
    assert decl["type"] == "SOURCE_DECLARATION"
    attrs = decl["attributes"]
    assert attrs["canonical_status"] == "UNRESOLVED"
    assert attrs["formal_status"] == "UNFORMALIZED"
    assert attrs["executable_status"] == "UNTESTED"
    assert attrs["statement_sha256"] == "a" * 64
    assert "statement_text" not in attrs
    source_root = by_id["source:v0_21:SRC"]
    assert source_root["type"] == "SOURCE_CORPUS"

    new_edges = [edge for edge in graph["edges"] if edge.get("attributes", {}).get("stage") == "v0.21"]
    assert len(new_edges) == 1
    assert new_edges[0]["type"] == "SOURCE_CONTAINS_DECLARATION"
    assert new_edges[0]["source"] == "source:v0_21:SRC"
    assert new_edges[0]["target"] == "srcdecl:v0_21:src:abc"
    assert not any(edge["type"] in FORBIDDEN_RELATIONS for edge in new_edges)


def test_quarantined_intake_does_not_mutate_existing_graph_payloads():
    module = _load_module()
    original = _base_graph()
    graph = module.integrate_quarantined_sources(copy.deepcopy(original), [_spec()], [_row()])
    assert graph["nodes"][0] == original["nodes"][0]
    assert graph["edges"][0] == original["edges"][0]


def test_quarantined_intake_rejects_unregistered_source():
    module = _load_module()
    with pytest.raises(ValueError, match="unregistered v0.21 source"):
        module.integrate_quarantined_sources(_base_graph(), [_spec()], [_row(source_id="OTHER")])


def test_quarantined_intake_rejects_status_promotion():
    module = _load_module()
    with pytest.raises(ValueError, match="cannot auto-promote canonical status"):
        module.integrate_quarantined_sources(_base_graph(), [_spec()], [_row(canonical_status="SAME_SEMANTICS")])


def test_quarantined_intake_fails_on_node_id_collision():
    module = _load_module()
    graph = _base_graph()
    row = _row(node_id="canonical:existing")
    with pytest.raises(ValueError, match="node ID collision"):
        module.integrate_quarantined_sources(graph, [_spec()], [row])


def test_build_v0_21_graph_accepts_frozen_gzip_declaration_manifest(tmp_path: Path):
    module = _load_module()
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps({
            "schema_version": "v0.21",
            "sources": [{
                "source_id": "SRC",
                "repository": "owner/repo",
                "revision": "1" * 40,
                "parser": "latex",
                "license": "CC-BY-4.0",
                "status": "ACTIVE",
                "scope": "test_scope",
                "include_globs": ["**/*.tex"],
                "exclude_globs": [],
            }],
        }),
        encoding="utf-8",
    )
    declarations = tmp_path / "declarations.json.gz"
    with gzip.open(declarations, "wt", encoding="utf-8") as handle:
        json.dump({"schema_version": "v0.21", "declarations": [_row()]}, handle)
    graph = module.build_v0_21_graph(_base_graph(), registry, declarations)
    assert any(node["id"] == "srcdecl:v0_21:src:abc" for node in graph["nodes"])
