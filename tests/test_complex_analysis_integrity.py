"""Fail-closed identity and referential checks for the v0.19 intake."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.complex_analysis_intake_v0_19 import (
    SEALED_V019_ALIGNMENT_SHA256,
    authoritative_source_registry,
    bridge_edge_id,
    ingest_complex_declarations,
    ingest_v0_19_canonical_alignments,
    load_active_alignment_projection,
    partition_v0_19_source_declarations,
    represents_edge_id,
    resolve_v0_19_evidence_path,
    save_graph_gz,
    validate_alignment_contracts,
)
from scripts.import_complex_analysis_v0_19 import (
    ComplexAnalysisDeclaration,
    build_complex_declarations,
    validate_complex_declarations,
)
from scripts.generate_alignments_v0_19 import write_active_v0_20_alignment_projection


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979"
AXLER = "AXLER_LADR4E_2026_08_16"


def _decl_by_suffix(suffix: str) -> ComplexAnalysisDeclaration:
    return next(d for d in build_complex_declarations() if d.node_id.endswith(suffix))


def _source_node(node_id: str, source_id: str, corpus: str, digest: str = "a" * 64) -> dict:
    return {
        "id": node_id,
        "type": "SOURCE_DECLARATION",
        "label": node_id,
        "attributes": {
            "source_id": source_id,
            "corpus": corpus,
            "statement_sha256": digest,
        },
    }


def _alignment(source_a: str, source_b: str, status_b: str = "CROSS_SOURCE_SAME") -> dict:
    return {
        "schema_version": "v0.19",
        "canonical_objects": [
            {
                "id": "canonical:test:one",
                "name": "Test contract",
                "domain": "Test",
                "representation_kinds": ["abstract"],
                "alignments": [
                    {"source": source_a, "corpus": "AHLFORS", "status": "CROSS_SOURCE_SAME"},
                    {"source": source_b, "corpus": "AXLER", "status": status_b},
                ],
            }
        ],
    }


def test_corrected_complex_statements_have_frozen_hashes_and_conditions() -> None:
    expected = {
        ":THEOREM:5.2": "a9eab681d425833b6d71c51dc1c336e219e1542c4ec746aac41f4ae3b44f7e77",
        ":LEMMA:5.10": "7c35e44d42045ec3635341883034ba669b17c6191e2630229d9f86bc96ece4da",
        ":THEOREM:7.4": "65e2fc0485b7164b8a39f1aebf40945c5eb8b38d84fcae5f38f23f710eba3dac",
        ":THEOREM:8.2": "14e299755838ac421a9e8754073a8a735399a2deb4547a6e97daf35699805dc1",
    }
    for suffix, digest in expected.items():
        assert _decl_by_suffix(suffix).statement_sha256 == digest

    raw = Path(ROOT / "scripts" / "import_complex_analysis_v0_19.py").read_text(encoding="utf-8")
    assert "positively oriented circle" in raw and "closed disk is contained in Omega" in raw
    assert "some nonzero z0 in D" in raw
    assert "increasing sequence of positive harmonic functions" in raw
    assert "locally uniformly" in raw
    assert "0 with multiplicity m" in raw and "with no other zeros" in raw


def test_additional_active_statement_corrections_have_required_hypotheses() -> None:
    declarations = {d.node_id: d for d in build_complex_declarations()}
    raw = Path(ROOT / "scripts" / "import_complex_analysis_v0_19.py").read_text(encoding="utf-8")
    assert "at every point of the open set" in raw
    assert "-pi < Im(Log z) < pi" in raw
    assert "open neighborhood of the closed disk" in raw
    assert "Ind_gamma(a)" in raw and "index-weighted" in raw
    assert "if and only if Omega is pseudoconvex" in raw
    assert "C^2 defining function rho" in raw
    assert "complex tangent vectors" in raw
    assert "finite-valued holomorphic limit" in raw
    for suffix in (
        ":DEFINITION:2.1",
        ":DEFINITION:3.4",
        ":THEOREM:5.3",
        ":THEOREM:5.12",
        ":THEOREM:6.8",
        ":DEFINITION:9.6",
        ":DEFINITION:9.7",
    ):
        declaration = next(item for node_id, item in declarations.items() if node_id.endswith(suffix))
        assert len(declaration.statement_sha256) == 64


def test_dolbeault_reference_is_real_and_all_structural_references_resolve() -> None:
    declarations = build_complex_declarations()
    dolbeault = next(d for d in declarations if d.node_id.endswith(":DEFINITION:9.4"))
    assert dolbeault.structural_refs == [f"decl:{SOURCE}:THEOREM:2.2"]
    validate_complex_declarations(declarations)

    graph = ingest_complex_declarations({"nodes": [], "edges": []}, declarations)
    node_ids = {node["id"] for node in graph["nodes"]}
    assert all(edge["target"] in node_ids for edge in graph["edges"] if edge["type"] == "PROOF_DEPENDENCY")


def test_declaration_validation_rejects_dangling_reference_and_bad_hash() -> None:
    declarations = build_complex_declarations()
    broken_ref = copy.deepcopy(declarations)
    broken_ref[0].structural_refs = [f"decl:{SOURCE}:THEOREM:does-not-exist"]
    with pytest.raises(ValueError, match="dangling structural reference"):
        validate_complex_declarations(broken_ref)

    broken_hash = copy.deepcopy(declarations)
    broken_hash[0].statement_sha256 = "z" * 64
    with pytest.raises(ValueError, match="statement_sha256"):
        validate_complex_declarations(broken_hash)

    valid_but_wrong_hash = copy.deepcopy(declarations)
    valid_but_wrong_hash[0].statement_sha256 = "f" * 64
    with pytest.raises(ValueError, match="authoritative|statement_sha256"):
        validate_complex_declarations(valid_but_wrong_hash)

    wrong_number = copy.deepcopy(declarations)
    wrong_number[-1].node_id = f"decl:{SOURCE}:{wrong_number[-1].decl_type}:WRONG"
    with pytest.raises(ValueError, match="authoritative|identity"):
        validate_complex_declarations(wrong_number)


def test_sealed_history_is_preserved_but_active_projection_excludes_known_defects() -> None:
    sealed_path = ROOT / "formal" / "cross_source_alignments_v0_19.json"
    assert hashlib.sha256(sealed_path.read_bytes()).hexdigest() == SEALED_V019_ALIGNMENT_SHA256
    data = json.loads(sealed_path.read_text(encoding="utf-8"))
    liouville = next(
        co for co in data["canonical_objects"]
        if co["id"] == "canonical:complex:liouville_and_fundamental_theorem_algebra"
    )
    assert "srcdecl:axler:definition:5_8" in {a["source"] for a in liouville["alignments"]}

    projection = load_active_alignment_projection(
        sealed_path,
        ROOT / "formal" / "mathematical_integrity_amendments_v0_20.json",
    )
    active_liouville = next(
        co for co in projection["canonical_objects"]
        if co["id"] == "canonical:complex:liouville_and_fundamental_theorem_algebra"
    )
    assert "srcdecl:axler:definition:5_8" not in {
        item["source"] for item in active_liouville["alignments"]
    }
    wounds = projection["integrity_wounds"]
    assert any(item["kind"] == "REJECTED_FALSE_ALIGNMENT" for item in wounds)
    assert any(item["kind"] == "DUPLICATE_ALIGNMENT" for item in wounds)
    assert sum(item["kind"] == "RELATION_CONFLICT_DOWNGRADED" for item in wounds) == 33


def test_alignment_validation_is_fail_closed_for_endpoint_corpus_hash_and_type() -> None:
    ahlfors_id = f"decl:{SOURCE}:THEOREM:5.4"
    axler_id = "srcdecl:axler:theorem:1_3"
    registry = authoritative_source_registry()
    graph = {
        "nodes": [
            _source_node(ahlfors_id, SOURCE, "AHLFORS", registry[ahlfors_id]["statement_sha256"]),
            _source_node(axler_id, AXLER, "AXLER", registry[axler_id]["statement_sha256"]),
        ],
        "edges": [],
    }
    contracts = _alignment(ahlfors_id, axler_id)
    validate_alignment_contracts(graph, contracts)

    missing = copy.deepcopy(contracts)
    missing["canonical_objects"][0]["alignments"][1]["source"] = "srcdecl:axler:missing"
    with pytest.raises(ValueError, match="not present"):
        validate_alignment_contracts(graph, missing)

    wrong_corpus = copy.deepcopy(contracts)
    wrong_corpus["canonical_objects"][0]["alignments"][1]["corpus"] = "GALLIER"
    with pytest.raises(ValueError, match="corpus mismatch"):
        validate_alignment_contracts(graph, wrong_corpus)

    bad_hash_graph = copy.deepcopy(graph)
    bad_hash_graph["nodes"][1]["attributes"]["statement_sha256"] = "z" * 64
    with pytest.raises(ValueError, match="statement_sha256"):
        validate_alignment_contracts(bad_hash_graph, contracts)

    valid_hex_but_invented = copy.deepcopy(graph)
    valid_hex_but_invented["nodes"][1]["attributes"]["statement_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="authoritative|statement_sha256"):
        validate_alignment_contracts(valid_hex_but_invented, contracts)

    wrong_type_graph = copy.deepcopy(graph)
    wrong_type_graph["nodes"][1]["type"] = "CANONICAL_OBJECT"
    with pytest.raises(ValueError, match="source declaration"):
        validate_alignment_contracts(wrong_type_graph, contracts)


def test_contract_scoped_bridge_ids_are_stable_and_do_not_silently_collapse(tmp_path: Path) -> None:
    a = f"decl:{SOURCE}:THEOREM:5.4"
    b = "srcdecl:axler:theorem:1_3"
    same = bridge_edge_id("canonical:test:one", "SAME_SEMANTICS", a, b)
    assert same == bridge_edge_id("canonical:test:one", "SAME_SEMANTICS", b, a)
    assert same != bridge_edge_id("canonical:test:two", "SAME_SEMANTICS", a, b)
    assert same != bridge_edge_id("canonical:test:one", "SCOPED_OVERLAP", a, b)

    registry = authoritative_source_registry()
    graph = {
        "nodes": [
            _source_node(a, SOURCE, "AHLFORS", registry[a]["statement_sha256"]),
            _source_node(b, AXLER, "AXLER", registry[b]["statement_sha256"]),
        ],
        "edges": [],
    }
    conflicting = _alignment(a, b)
    duplicate = copy.deepcopy(conflicting["canonical_objects"][0]["alignments"][1])
    duplicate["status"] = "CROSS_SOURCE_SCOPED_OVERLAP"
    conflicting["canonical_objects"][0]["alignments"].append(duplicate)
    with pytest.raises(ValueError, match="conflicting alignment contract"):
        validate_alignment_contracts(graph, conflicting)

    path = tmp_path / "alignments.json"
    path.write_text(json.dumps(_alignment(a, b)), encoding="utf-8")
    out = ingest_v0_19_canonical_alignments(copy.deepcopy(graph), path)
    bridges = [e for e in out["edges"] if e["type"] == "SAME_SEMANTICS"]
    assert [edge["id"] for edge in bridges] == [same]
    bridge_attrs = bridges[0]["attributes"]
    assert set(bridge_attrs["endpoint_statement_sha256"]) == {a, b}
    assert all(len(value) == 64 for value in bridge_attrs["endpoint_statement_sha256"].values())
    assert len(bridge_attrs["canonical_contract_sha256"]) == 64
    assert bridge_attrs["evidence_status"] == "CURATED_ALIGNMENT_NOT_KERNEL_VERIFIED"

    represents = [edge for edge in out["edges"] if edge["type"] == "REPRESENTS"]
    assert represents
    for edge in represents:
        attrs = edge["attributes"]
        assert len(attrs["source_statement_sha256"]) == 64
        assert len(attrs["canonical_contract_sha256"]) == 64
        assert attrs["evidence_status"] != "KERNEL_VERIFIED"


def test_represents_edge_ids_are_contract_scoped() -> None:
    first = represents_edge_id("canonical:test:one", "source:a", "a" * 64)
    assert first == represents_edge_id("canonical:test:one", "source:a", "a" * 64)
    assert first != represents_edge_id("canonical:test:one", "source:a", "b" * 64)
    assert first != represents_edge_id("canonical:test:two", "source:a", "a" * 64)
    assert first != "e:rep:source:a:canonical:test:one"


def test_cross_canonical_relation_conflicts_fail_without_explicit_projection() -> None:
    a = f"decl:{SOURCE}:THEOREM:5.4"
    b = "srcdecl:axler:theorem:1_3"
    registry = authoritative_source_registry()
    graph = {
        "nodes": [
            _source_node(a, SOURCE, "AHLFORS", registry[a]["statement_sha256"]),
            _source_node(b, AXLER, "AXLER", registry[b]["statement_sha256"]),
        ],
        "edges": [],
    }
    contracts = _alignment(a, b)
    second = copy.deepcopy(contracts["canonical_objects"][0])
    second["id"] = "canonical:test:two"
    second["alignments"][1]["status"] = "CROSS_SOURCE_SCOPED_OVERLAP"
    contracts["canonical_objects"].append(second)
    with pytest.raises(ValueError, match="cross-canonical relation conflict"):
        validate_alignment_contracts(graph, contracts)


def test_edge_id_collision_with_different_payload_fails_closed(tmp_path: Path) -> None:
    a = f"decl:{SOURCE}:THEOREM:5.4"
    b = "srcdecl:axler:theorem:1_3"
    registry = authoritative_source_registry()
    graph = {
        "nodes": [
            _source_node(a, SOURCE, "AHLFORS", registry[a]["statement_sha256"]),
            _source_node(b, AXLER, "AXLER", registry[b]["statement_sha256"]),
        ],
        "edges": [
            {
                "id": represents_edge_id(
                    "canonical:test:one",
                    a,
                    hashlib.sha256(
                        json.dumps(
                            _alignment(a, b)["canonical_objects"][0],
                            ensure_ascii=False,
                            separators=(",", ":"),
                            sort_keys=True,
                            allow_nan=False,
                        ).encode("utf-8")
                    ).hexdigest(),
                ),
                "type": "REPRESENTS",
                "source": b,
                "target": "canonical:wrong",
                "attributes": {},
            }
        ],
    }
    path = tmp_path / "alignments.json"
    path.write_text(json.dumps(_alignment(a, b)), encoding="utf-8")
    with pytest.raises(ValueError, match="edge ID collision"):
        ingest_v0_19_canonical_alignments(graph, path)


def test_generator_cannot_overwrite_sealed_v019_alignment() -> None:
    sealed = ROOT / "formal" / "cross_source_alignments_v0_19.json"
    with pytest.raises(ValueError, match="sealed"):
        write_active_v0_20_alignment_projection(sealed)


def test_active_projection_generator_runs_as_a_direct_script() -> None:
    output = ROOT / "formal" / "cross_source_alignments_v0_20_active.json"
    output.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_alignments_v0_19.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        generated = json.loads(output.read_text(encoding="utf-8"))
        assert generated["schema_version"] == "v0.20-active-alignment-projection"
        assert len(generated["integrity_wounds"]) == 35
    finally:
        output.unlink(missing_ok=True)


def test_reconstruction_routes_v019_through_explicit_amendments() -> None:
    source = (ROOT / "scripts" / "reconstruct_pipeline.py").read_text(encoding="utf-8")
    assert '"--amendments"' in source
    assert '"mathematical_integrity_amendments_v0_20.json"' in source


def test_reconstruction_uses_manifest_bound_source_declarations(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import reconstruct_pipeline

    commands: list[list[str]] = []
    monkeypatch.setattr(
        reconstruct_pipeline,
        "run_stage",
        lambda _name, command: commands.append(command),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["reconstruct_pipeline.py", "--target-stage", "v0.14"],
    )
    assert reconstruct_pipeline.main() == 0
    source_commands = [
        command
        for command in commands
        if any(
            script in " ".join(command)
            for script in (
                "cross_source_intake_v0_12.py",
                "tri_source_intake_v0_13.py",
                "convex_intake_v0_14.py",
            )
        )
    ]
    assert len(source_commands) == 3
    assert all("--mock" in command for command in source_commands)


def test_active_projection_rejects_rehashed_but_source_unbound_amendments(tmp_path: Path) -> None:
    sealed = tmp_path / "sealed.json"
    sealed.write_bytes(
        (ROOT / "formal" / "cross_source_alignments_v0_19.json").read_bytes().rstrip(b"\n")
    )
    manifest = json.loads(
        (ROOT / "formal" / "mathematical_integrity_amendments_v0_20.json").read_text(
            encoding="utf-8"
        )
    )
    duplicate = next(
        item
        for item in manifest["amendments"]
        if item["amendment_id"].endswith("duplicate-axler-6-55-alignment")
    )
    duplicate["historical_identity"]["source_statement_sha256"] = "f" * 64
    payload = {
        key: value
        for key, value in duplicate["historical_identity"].items()
        if key != "identity_sha256"
    }
    duplicate["historical_identity"]["identity_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    amendment_path = tmp_path / "amendments.json"
    amendment_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="source-hash-bound"):
        load_active_alignment_projection(sealed, amendment_path)


def test_active_intake_cannot_overwrite_sealed_v019_evidence(tmp_path: Path) -> None:
    default = resolve_v0_19_evidence_path(tmp_path, None)
    assert default.parent == tmp_path
    with pytest.raises(ValueError, match="sealed v0.19 evidence"):
        resolve_v0_19_evidence_path(
            tmp_path,
            ROOT / "evidence" / "v0_19_scientific_results.json",
        )


def test_graph_serialization_is_deterministic_and_filename_independent(tmp_path: Path) -> None:
    graph = {"nodes": [{"id": "n", "type": "CANONICAL_OBJECT", "attributes": {}}], "edges": []}
    first = tmp_path / "first.json.gz"
    second = tmp_path / "second.json.gz"
    save_graph_gz(graph, first)
    save_graph_gz(graph, second)
    assert first.read_bytes() == second.read_bytes()


def test_v019_partition_uses_authoritative_registry_not_id_substrings() -> None:
    registry = authoritative_source_registry()
    ahlfors = f"decl:{SOURCE}:THEOREM:5.4"
    axler = "srcdecl:axler:theorem:1_3"
    counts = partition_v0_19_source_declarations(
        [
            _source_node(ahlfors, SOURCE, "AHLFORS", registry[ahlfors]["statement_sha256"]),
            _source_node(axler, AXLER, "AXLER", registry[axler]["statement_sha256"]),
        ]
    )
    assert counts["S_G_ahlfors"] == 1
    assert counts["S_B_axler"] == 1
    with pytest.raises(ValueError, match="authoritative source registry"):
        partition_v0_19_source_declarations(
            [_source_node("opaque", SOURCE, "AHLFORS", "a" * 64)]
        )


def test_authoritative_registry_includes_v015_supplementary_declarations() -> None:
    from scripts.import_analysis_v0_15 import generate_additional_analysis_declarations

    registry = authoritative_source_registry()
    for declaration in generate_additional_analysis_declarations():
        assert registry[declaration.node_id]["source_id"] == declaration.source_id
        assert registry[declaration.node_id]["statement_sha256"] == declaration.statement_sha256
