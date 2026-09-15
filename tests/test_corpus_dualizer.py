from __future__ import annotations

import importlib.util
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dual", ROOT / "scripts" / "corpus_dualize_v0_5.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def line(text: str, n: int = 1):
    return {"pdf_page": 1, "local_line": n, "text": mod.normalize_text(text)}


def test_nfkc_recovers_definition_ligature():
    assert mod.normalize_text("Deﬁnition 2.1") == "Definition 2.1"
    starts = mod.declaration_starts([line("Deﬁnition 2.1 A test")])
    assert len(starts) == 1
    assert starts[0].kind == "Definition"
    assert starts[0].number == "2.1"


def test_split_heading_recovers_kind_and_number():
    lines = [line("Definition", 1), line("2.7 A split heading", 2), line("Proposition 2.8 Next", 3)]
    starts = mod.declaration_starts(lines)
    assert [(s.kind, s.number, s.heading_mode) for s in starts] == [
        ("Definition", "2.7", "SPLIT_LINE"),
        ("Proposition", "2.8", "SAME_LINE"),
    ]


def test_controlled_profile_is_dual_candidate():
    p = mod.profile_segment("The graph Laplacian is a matrix operator on vertices and edges.", 20)
    assert "GRAPH_RELATION" in p["direct_concepts"]
    assert "GRAPH_LAPLACIAN_OPERATOR" in p["eo_candidate_families"]
    assert "INCIDENCE_RELATIONAL_GEOMETRY" in p["geo_candidate_families"]
    assert p["dualization_status"] == "DUAL_CANDIDATE"
    assert p["evidence"] == "DIRECT_TEXT"


def test_chapter_prior_is_distinguished_from_direct_text():
    p = mod.profile_segment("Let x be arbitrary.", 54)
    assert p["direct_concepts"] == []
    assert "KERNEL_SIMILARITY" in p["chapter_prior_concepts"]
    assert p["evidence"] == "CHAPTER_PRIOR"
    assert p["dualization_status"] == "DUAL_CANDIDATE"


def test_source_graph_contains_no_prose_payload_fields(tmp_path: Path):
    decl = {
        "kind":"Definition", "number":"20.1", "chapter":20, "chapter_title":mod.CHAPTERS[19],
        "pdf_page_start":1, "pdf_page_end":1, "heading_mode":"SAME_LINE",
        "source_segment_sha256":"abc", "source_segment_chars":123,
        "proof_present":False, "proof_sha256":None, "proof_chars":0, "proof_references":[],
        "semantic_profile":mod.profile_segment("graph Laplacian vertex edge",20),
    }
    base={"graph_id":"x","schema_version":"0","required_views":["EO","GEO"],"nodes":[],"edges":[]}
    graph, deps = mod.merge_into_graph(base,[decl])
    assert deps["resolved_dependency_references"] == 0
    audit = mod.audit_graph(graph)
    assert audit["no_copyright_payload_fields"]
    statement = next(n for n in graph["nodes"] if n["id"] == "srcdecl:definition:20_1")
    assert statement["attributes"]["dualization_status"] == "DUAL_CANDIDATE"
    assert "text" not in statement["attributes"]


def test_pdf_extraction_detects_ligature_and_split_definition(tmp_path: Path):
    pdf = tmp_path / "fixture.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(36, 36, 560, 760),
        "Definition\n2.1 A split definition about groups.\nProposition 2.2 A group proposition.\nProof. By Definition 2.1.",
        fontsize=11,
    )
    doc.save(pdf); doc.close()
    lines, _ = mod.extract_line_stream(pdf)
    raw = mod.find_declarations(lines)
    kept, _ = mod.dedupe_declarations(raw)
    assert [(d["kind"], d["number"]) for d in kept] == [("Definition","2.1"),("Proposition","2.2")]
    assert kept[1]["proof_present"]
    assert kept[1]["proof_references"] == [{"kind":"Definition","number":"2.1"}]
