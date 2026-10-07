from __future__ import annotations

import gzip
import hashlib
import importlib
import json
from pathlib import Path
import subprocess

import pytest


def module():
    try:
        return importlib.import_module("scripts.openai_math_intake")
    except ModuleNotFoundError:
        pytest.fail("complete repository intake implementation is absent")


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def committed_source(tmp_path: Path):
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "README.md").write_text("# Source parser test\n", encoding="utf-8")
    (repo / "unicode-π.txt").write_text("π\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Intake Test", "-c", "user.email=intake-test@example.invalid",
        "commit", "-qm", "source fixture")
    return repo, git(repo, "rev-parse", "HEAD")


def test_inventory_binds_every_tracked_path_and_detects_modified_bytes(tmp_path):
    mod = module()
    repo, revision = committed_source(tmp_path)
    entries = mod.git_inventory(repo, revision)
    assert {entry["path"] for entry in entries} == {"README.md", "unicode-π.txt"}
    unicode_entry = next(entry for entry in entries if entry["path"] == "unicode-π.txt")
    assert mod.source_bytes(repo, unicode_entry) == "π\n".encode()
    (repo / "unicode-π.txt").write_text("different\n", encoding="utf-8")
    with pytest.raises(ValueError, match="blob|content|identity"):
        mod.source_bytes(repo, unicode_entry)


def test_inventory_rejects_wrong_revision(tmp_path):
    mod = module()
    repo, _revision = committed_source(tmp_path)
    with pytest.raises(ValueError, match="revision|HEAD|commit"):
        mod.git_inventory(repo, "0" * 40)


def test_catalogue_preserves_noncontiguous_family_ids_and_balanced_pdf_paths():
    mod = module()
    # Real syntax and IDs from the upstream catalogue, with prose omitted.
    contents = (
        "**044. Family heading.**\n"
        "&emsp;[Main paper](preprints/A-Paper/main.pdf)\n"
        "**046. Next family heading.**\n"
        "&emsp;[CAT(0) paper](preprints/Sharp-integral-fillings-in-CAT(0)-spaces-September-23-2026/paper.pdf)\n"
    )
    families = mod.parse_catalogue(contents)
    assert [row["family_id"] for row in families] == ["044", "046"]
    assert families[1]["manuscripts"][0]["pdf_path"].endswith("CAT(0)-spaces-September-23-2026/paper.pdf")


def test_no_prose_validation_recurses_and_does_not_reject_source_hashes():
    mod = module()
    mod.assert_metadata_only({"attributes": {"statement_sha256": "a" * 64}})
    for key in ("statement_text", "proof_text", "source_prose", "excerpt", "page_image", "raw_content"):
        with pytest.raises(ValueError, match="payload|prose|forbidden"):
            mod.assert_metadata_only({"records": [{"nested": {key: "not permitted"}}]})


def base_graph():
    return {
        "graph_id": "preserved-baseline",
        "nodes": [{"id": "base:source", "type": "SOURCE", "attributes": {"source_sha256": "a" * 64}}],
        "edges": [],
    }


def source_node():
    return {"id": "oam:test:resource", "type": "SOURCE_RESOURCE", "attributes": {"verification_status": "UNTESTED"}}


def test_stream_preserves_base_and_replays_identically_across_output_names(tmp_path):
    mod = module()
    base = base_graph()
    expected_base = json.loads(json.dumps(base))
    paths = [tmp_path / "one.json.gz", tmp_path / "two.json.gz"]
    for path in paths:
        with mod.GraphStream(path, base, {"repository": "openai/math", "revision": "a" * 40}) as stream:
            stream.add_node(source_node())
            stream.add_node(source_node())  # Exact replay must not duplicate it.
            stream.add_edge({"id": "oam:test:edge", "type": "HAS_SOURCE_RESOURCE", "source": "base:source", "target": "oam:test:resource", "attributes": {}})
    assert paths[0].read_bytes() == paths[1].read_bytes()
    graph = json.load(gzip.open(paths[0], "rt"))
    assert graph["nodes"][0] == expected_base["nodes"][0]
    assert base == expected_base
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1


def test_stream_rejects_conflicting_id_and_leaves_existing_output_intact(tmp_path):
    mod = module()
    out = tmp_path / "graph.json.gz"
    out.write_bytes(b"previous output")
    with pytest.raises(ValueError, match="conflict|collision"):
        with mod.GraphStream(out, base_graph(), {}) as stream:
            stream.add_node(source_node())
            stream.add_node({**source_node(), "label": "changed identity"})
    assert out.read_bytes() == b"previous output"


def test_stream_rejects_dangling_edges_atomically(tmp_path):
    mod = module()
    out = tmp_path / "graph.json.gz"
    out.write_bytes(b"previous output")
    with pytest.raises(ValueError, match="endpoint|dangling"):
        with mod.GraphStream(out, base_graph(), {}) as stream:
            stream.add_edge({"id": "oam:test:missing", "type": "SOURCE_REFERENCE", "source": "base:source", "target": "missing", "attributes": {}})
    assert out.read_bytes() == b"previous output"


def test_source_import_cannot_create_verification_or_equivalence(tmp_path):
    mod = module()
    for node in (
        {"id": "oam:test:cert", "type": "CERTIFICATE", "attributes": {}},
        {"id": "oam:test:record", "type": "SOURCE_RECORD", "attributes": {"verification_status": "KERNEL_VERIFIED"}},
    ):
        with pytest.raises(ValueError, match="promotion|verification|certificate"):
            with mod.GraphStream(tmp_path / "graph.json.gz", base_graph(), {}) as stream:
                stream.add_node(node)
    with pytest.raises(ValueError, match="promotion|equivalence|semantic"):
        with mod.GraphStream(tmp_path / "graph.json.gz", base_graph(), {}) as stream:
            stream.add_edge({"id": "oam:test:eq", "type": "SAME_SEMANTICS", "source": "base:source", "target": "base:source", "attributes": {}})


def test_binary_source_hash_has_git_blob_header_not_plain_file_sha(tmp_path):
    mod = module()
    payload = b"\x00\xff\x10"
    (tmp_path / "source.bin").write_bytes(payload)
    entry = {"path": "source.bin", "mode": "100644", "type": "blob", "size": 3,
             "sha": hashlib.sha1(b"blob 3\0" + payload).hexdigest()}
    assert mod.source_bytes(tmp_path, entry) == payload
    entry["sha"] = hashlib.sha1(payload).hexdigest()
    with pytest.raises(ValueError, match="blob|content|identity"):
        mod.source_bytes(tmp_path, entry)


def test_complete_intake_links_actual_scanned_records_and_replays(tmp_path, monkeypatch):
    """A small committed software fixture exercises the complete production path."""
    mod = module()
    repo, _revision = committed_source(tmp_path)
    files = {
        "CONTENTS.md": "**046. Fixture family.**\n&emsp;[Fixture paper](preprints/Paper/main.pdf)\n",
        "preprints/Paper/main.pdf": b"%PDF-fixture-for-identity-only\n",
        "preprints/Paper/main.tex": "\\begin{theorem}a=b\\end{theorem}\n",
        "lean/Example.lean": "namespace Fixture\ntheorem sample : True := True.intro\nend Fixture\n",
        "lean/ComparatorChallenges/Example.lean": "namespace Fixture\naxiom sample : True\nend Fixture\n",
        "lean/ComparatorChallenges/Example.json": json.dumps({
            "challenge_module": "ComparatorChallenges.Example", "solution_module": "Example",
            "theorem_names": ["Fixture.sample"], "permitted_axioms": ["propext"],
        }),
        "lean/docs/046.md": "# Scope fixture\n",
        "lean/formalization.yaml": (
            "status:\n  scope: Partial progress.\n  main_results:\n"
            "    - declaration: Fixture.sample\n      file: Example.lean\n"
            "      comparator_config: ComparatorChallenges/Example.json\nreview:\n  status: unchecked\n"
        ),
    }
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Intake Test", "-c", "user.email=intake-test@example.invalid",
        "commit", "-qm", "complete intake software fixture")
    revision = git(repo, "rev-parse", "HEAD")
    inventory = mod.git_inventory(repo, revision)
    pin = tmp_path / "pin.json"
    pin.write_text(json.dumps({
        "repository": "fixture/source", "url": "https://example.invalid/fixture/source",
        "revision": revision, "tree": git(repo, "rev-parse", "HEAD^{tree}"), "license": "FIXTURE",
        "expected": {"tracked_files": len(inventory), "tracked_bytes": sum(row["size"] for row in inventory),
                     "families": 1, "manuscripts": 1, "scope_documents": 1,
                     "comparator_configurations": 1, "selected_theorem_occurrences": 1,
                     "catalogue_main_results": 1},
    }))
    monkeypatch.setattr(mod, "PIN_PATH", pin)
    base = tmp_path / "base.json"
    base.write_text(json.dumps(base_graph()))
    reports = [mod.run_intake(repo, base, tmp_path / folder) for folder in ("first", "second", "first")]
    assert reports[0] == reports[1] == reports[2]
    report = reports[0]
    assert report["status"] == "PASS"
    assert report["coverage"]["tracked_files"] == len(inventory)
    assert report["extraction"]["unique_lexical_target_matches"] == 1
    graph = json.load(gzip.open(tmp_path / "first/mapeogeo_openai_math_graph.json.gz", "rt"))
    records = [node for node in graph["nodes"] if node["type"] == "SOURCE_RECORD"]
    assert {node["attributes"]["kind"] for node in records} >= {"theorem", "axiom"}
    assert any(node["attributes"]["source_resource"].endswith("main.tex") for node in records)
    assert all(node["attributes"]["kernel_verification_status"] == "UNTESTED" for node in records)
    assert graph["nodes"][0] == base_graph()["nodes"][0]
    preserved = {p.name: p.read_bytes() for p in (tmp_path / "first").iterdir()}

    def receipt_failure(*_args):
        raise OSError("injected receipt publication failure after graph sealing")

    monkeypatch.setattr(mod, "_write_json", receipt_failure)
    with pytest.raises(OSError, match="receipt publication"):
        mod.run_intake(repo, base, tmp_path / "first")
    assert {p.name: p.read_bytes() for p in (tmp_path / "first").iterdir()} == preserved
    assert not list(tmp_path.glob(".openai-math-intake-*"))


def test_proof_status_guard_handles_structured_verification_metadata():
    mod = module()
    mod._assert_no_promotion({"type": "SOURCE_RESOURCE", "attributes": {"verification_metadata": {"ran": False}}})


@pytest.mark.parametrize("target", ["thm:main", "main.tex", "", "https://example.invalid"])
def test_tex_labels_are_symbolic_anchors_even_when_the_name_looks_like_a_link(target):
    mod = module()
    assert mod._resolve_reference("preprints/Paper/main.tex", {"kind": "tex_label", "target": target},
                                  {"preprints/Paper/main.tex"}) == (None, "SYMBOLIC_LABEL")


def test_duplicate_base_identity_is_rejected_instead_of_changing_historical_counts(tmp_path):
    mod = module()
    base = base_graph()
    base["nodes"] = base["nodes"] * 2
    with pytest.raises(ValueError, match="duplicate.*base|base.*duplicate"):
        with mod.GraphStream(tmp_path / "graph.json.gz", base, {}):
            pass


@pytest.mark.parametrize("kind", ["tex_input", "tex_include"])
def test_parameterized_tex_input_is_unresolved_instead_of_a_local_anchor(kind):
    mod = module()
    assert mod._resolve_reference("preprints/Paper/main.tex", {"kind": kind, "target": "#1\\relax#2"},
                                  {"preprints/Paper/main.tex"}) == (None, "SYMBOLIC_REFERENCE")
    assert mod._resolve_reference("preprints/Paper/main.tex", {"kind": kind, "target": "chapter"},
                                  {"preprints/Paper/chapter.tex"}) == ("preprints/Paper/chapter.tex", "RESOLVED")
