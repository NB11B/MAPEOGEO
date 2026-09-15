from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_math_deep", ROOT / "scripts" / "import_math_deep.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def make_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(36, 36, 560, 760),
        "\n".join(
            [
                "Definition 2.1 A synthetic declaration used only for parser testing.",
                "This line carries fixture material.",
                "Proposition 2.2 A second synthetic declaration.",
                "Proof. By Definition 2.1 the fixture closes.",
                "Theorem 2.3 A synthetic theorem.",
                "Proof. Proposition 2.2 and Definition 2.1 are used.",
            ]
        ),
        fontsize=11,
    )
    doc.save(path)
    doc.close()


def test_declaration_and_dependency_extraction(tmp_path: Path) -> None:
    pdf = tmp_path / "fixture.pdf"
    make_pdf(pdf)
    lines, meta = mod.extract_line_stream(pdf)
    raw = mod.find_declarations(lines)
    decls, dropped = mod.dedupe_declarations(raw)

    assert meta["pdf_pages"] == 1
    assert len(decls) == 3
    assert dropped == []

    by_key = {(d["kind"], d["number"]): d for d in decls}
    assert by_key[("Definition", "2.1")]["proof_present"] is False
    assert by_key[("Proposition", "2.2")]["proof_present"] is True
    assert by_key[("Theorem", "2.3")]["proof_present"] is True
    refs = {(r["kind"], r["number"]) for r in by_key[("Theorem", "2.3")]["proof_references"]}
    assert refs == {("Proposition", "2.2"), ("Definition", "2.1")}

    graph, stats = mod.merge_declarations_into_graph(
        {
            "graph_id": "fixture",
            "schema_version": "0",
            "required_views": ["EO", "GEO"],
            "nodes": [],
            "edges": [],
        },
        decls,
    )
    assert stats["resolved_dependency_references"] == 3
    assert stats["unresolved_dependency_references"] == 0

    edges = graph["edges"]
    dep_edges = [e for e in edges if e["type"] == "DEPENDS_ON"]
    assert len(dep_edges) == 3

    proof_nodes = [n for n in graph["nodes"] if n["type"] == "PROOF_STEP"]
    assert len(proof_nodes) == 2

    audit = mod.audit_graph(graph)
    assert audit["unique_node_ids"]
    assert audit["unique_edge_ids"]
    assert audit["all_edge_endpoints_exist"]
    assert audit["no_copyright_payload_fields"]


def test_duplicate_semantic_key_prefers_larger_segment() -> None:
    small = {
        "kind": "Theorem", "number": "6.16", "chapter": 6, "chapter_title": "Direct Sums",
        "pdf_page_start": 10, "pdf_page_end": 10, "source_segment_sha256": "a",
        "source_segment_chars": 100, "proof_present": False, "proof_sha256": None,
        "proof_chars": 0, "proof_references": [],
    }
    large = {**small, "pdf_page_start": 100, "pdf_page_end": 101, "source_segment_sha256": "b", "source_segment_chars": 900}
    kept, dropped = mod.dedupe_declarations([small, large])
    assert len(kept) == 1
    assert kept[0]["source_segment_sha256"] == "b"
    assert len(dropped) == 1
    assert dropped[0]["winner_pdf_page_start"] == 100


def test_no_source_prose_is_serialized_in_graph() -> None:
    decl = {
        "kind": "Theorem", "number": "47.9", "chapter": 47,
        "chapter_title": "Linear Programming and Duality",
        "pdf_page_start": 1000, "pdf_page_end": 1001,
        "source_segment_sha256": "deadbeef", "source_segment_chars": 500,
        "proof_present": True, "proof_sha256": "feedface", "proof_chars": 250,
        "proof_references": [],
    }
    graph, _ = mod.merge_declarations_into_graph(
        {"graph_id":"x","schema_version":"0","required_views":["EO","GEO"],"nodes":[],"edges":[]},
        [decl],
    )
    serialized = json.dumps(graph)
    assert "statement_text" not in serialized
    assert "proof_text" not in serialized
    assert '"excerpt"' not in serialized
    assert mod.audit_graph(graph)["no_copyright_payload_fields"]
