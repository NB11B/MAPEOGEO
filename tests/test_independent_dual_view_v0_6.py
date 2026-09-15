from __future__ import annotations
import importlib.util
from pathlib import Path
import fitz

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("v06",ROOT/"scripts"/"independent_dual_view_v0_6.py")
mod=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(mod)


def test_banks_are_independent_objects_and_detect_dual_graph_statement():
    text="The graph Laplacian maps vertex data and is defined by edges and an incidence matrix."
    eo=mod.detect(mod.EO_BANK,text); geo=mod.detect(mod.GEO_BANK,text)
    assert "EO_GRAPH_OPERATOR" in eo
    assert "GEO_GRAPH" in geo
    assert set(mod.EO_BANK).isdisjoint(set(mod.GEO_BANK))


def test_statement_only_excludes_proof_material(tmp_path:Path):
    pdf=tmp_path/"fixture.pdf"; d=fitz.open(); p=d.new_page()
    p.insert_textbox(fitz.Rect(36,36,560,760),"Theorem 20.1 A graph theorem about vertices and edges.\nProof. The derivative and convex kernel appear only in this proof.\nTheorem 20.2 Another graph theorem.",fontsize=11)
    d.save(pdf); d.close()
    lines,_=mod.v05.extract_line_stream(pdf)
    raw=mod.v05.find_declarations(lines); decls,_=mod.v05.dedupe_declarations(raw)
    prof=mod.add_independent_profiles(decls,lines)
    first=next(x for x in prof if x['number']=='20.1')
    assert "GEO_GRAPH" in first['independent_profile']['geo_direct_families']
    assert "EO_DIFFERENTIAL" not in first['independent_profile']['eo_direct_families']
    assert "EO_KERNEL_GRAM" not in first['independent_profile']['eo_direct_families']
    assert "GEO_CONVEX_POLYHEDRAL" not in first['independent_profile']['geo_direct_families']


def test_fixture_recovery_is_20_of_20():
    base=mod.v05.load_json_any(ROOT / 'data' / 'gallier_quaintance_graph_v0_3.json.gz')
    r=mod.fixture_recovery(base)
    assert r['total']==20
    assert r['recovered']==20, r


def test_jaccard():
    assert mod.jaccard({'a'},{'a','b'})==0.5
    assert mod.jaccard(set(),{'a'})==0.0
    assert mod.jaccard(set(),set())==1.0
