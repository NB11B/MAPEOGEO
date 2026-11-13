import importlib.util
from pathlib import Path
import copy
import hashlib
import json
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v09',ROOT/'scripts/proof_paths_v0_9.py')
v09=importlib.util.module_from_spec(spec);spec.loader.exec_module(v09)

def check(graph,cfg,path):
    fn=getattr(v09,'source_correction_gate',None)
    assert callable(fn),'explicit correction provenance gate missing'
    return fn(graph,cfg,path)

def case(tmp_path):
    path=tmp_path/'bindings.json'
    path.write_bytes((ROOT/'formal/proof_paths_v0_9_corrected_v1.json').read_bytes())
    cfg=json.loads(path.read_text())
    graph=json.loads((ROOT/'tests/fixtures/v09_corrected_source_metadata.json').read_text())
    return graph,cfg,path

def test_original_mode_cannot_silently_inherit_correction(tmp_path):
    graph,cfg,path=case(tmp_path)
    assert check({}, {},path)
    assert not check(graph,{},path)

def test_corrected_mode_requires_exact_provenance(tmp_path):
    graph,cfg,path=case(tmp_path)
    assert check(graph,cfg,path)
    assert not check({},cfg,path)
    path.write_text('changed')
    assert not check(graph,cfg,path)

@pytest.mark.parametrize('field,value',[('status','FAIL'),('schema','other'),('extractor_version','1.26.6'),('qualification_variant','other'),('source_pdf',{'sha256':'0'*64,'bytes':24629575})])
def test_provenance_mutations_fail_closed(tmp_path,field,value):
    graph,cfg,path=case(tmp_path);graph['source_correction_audit'][field]=value
    assert not check(graph,cfg,path)

def test_unknown_variant_fails_closed(tmp_path):
    graph,cfg,path=case(tmp_path);cfg['qualification_variant']='other'
    assert not check(graph,cfg,path)


def test_copied_metadata_without_corrected_payload_is_rejected(tmp_path):
    graph,cfg,path=case(tmp_path)
    assert not check({'source_correction_audit':graph['source_correction_audit']},cfg,path)

@pytest.mark.parametrize('mutation',['page','proof','boundary','scope','citation','stale_payload'])
def test_corrected_graph_mutations_fail_even_with_rehashed_payload(tmp_path,mutation):
    graph,cfg,path=case(tmp_path)
    spec=importlib.util.spec_from_file_location('source_correction',ROOT/'scripts/correct_v09_source_binding.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if mutation=='page': next(n for n in graph['nodes'] if n['id']==module.LEMMA)['attributes']['pdf_page_start']=97
    elif mutation=='proof': next(n for n in graph['nodes'] if n['id']=='proof:lemma:3_6')['attributes']['proof_sha256']='0'*64
    elif mutation=='boundary': graph['source_correction_audit']['boundaries']['statement']['pdf_page']=97
    elif mutation=='scope': graph['source_correction_audit']['semantic_profile_scope']='WHOLE_PROOF'
    elif mutation=='citation': graph['edges']=[e for e in graph['edges'] if e['type']!='DEPENDS_ON']
    else: graph['nodes'][0]['label']='changed'
    if mutation!='stale_payload':graph['source_correction_audit']['canonical_graph_sha256']=module.canonical_graph_sha256(graph)
    assert not check(graph,cfg,path)
