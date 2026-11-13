import copy
import importlib.util
import json
import os
from pathlib import Path
import pytest

ROOT=Path(__file__).parents[1]

def mod():
    path=ROOT/'scripts/correct_v09_source_binding.py'
    assert path.exists(), 'correction implementation missing'
    s=importlib.util.spec_from_file_location('correction',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_wrong_source_rejected(tmp_path):
    pdf=tmp_path/'source.pdf';pdf.write_bytes(b'wrong')
    with pytest.raises(ValueError):mod().extract_source(pdf)

@pytest.fixture
def inputs():
    m=mod()
    pdf=Path(os.environ.get('MAPEOGEO_TEST_PDF','/tmp/math-edition-check/math-deep.pdf'))
    graph=Path(os.environ.get('MAPEOGEO_TEST_GRAPH','/tmp/math-edition-check/v06-hosted/mapeogeo_independent_graph.json'))
    if not pdf.exists() or not graph.exists():
        if 'MAPEOGEO_TEST_PDF' in os.environ or 'MAPEOGEO_TEST_GRAPH' in os.environ:pytest.fail('explicit private replay inputs missing')
        pytest.skip('private exact-source replay inputs unavailable')
    spans=m.extract_source(pdf);base=m.load(graph);original=json.loads((ROOT/'formal/proof_paths_v0_9.json').read_text());bindings=copy.deepcopy(original)
    for row in bindings['support_frontier']:
        if row['source_id']==m.LEMMA:row['statement_sha256']=m.STATEMENT
        if row['source_id']==m.PROP:row['statement_sha256']=m.PROP_HASH
    bindings['qualification_variant']='CORRECTED_SOURCE_V1'
    return m,base,bindings,original,spans

def run(inputs):
    m,g,b,o,s=inputs
    return m.correct_graph(g,b,o,s,base_graph_sha256='a'*64,bindings_sha256='b'*64)

def test_correction_preserves_all_other_nodes_and_edges(inputs):
    m,g,b,o,s=inputs;before=copy.deepcopy((g,b,o,s));out,audit=run(inputs)
    assert (g,b,o,s)==before
    assert out['source_correction_audit']==audit
    assert audit['semantic_profile_scope']=='CORRECTED_STATEMENT_ONLY'
    assert audit['superseded_node']==next(n for n in g['nodes'] if n['id']==m.LEMMA)
    assert [n for n in out['nodes'] if n['id'] not in (m.LEMMA,'proof:lemma:3_6')]==[n for n in g['nodes'] if n['id']!=m.LEMMA]
    assert out['edges'][:-1]==g['edges']
    assert out['edges'][-1]['type']=='PRODUCES'
    node=next(n for n in out['nodes'] if n['id']==m.LEMMA)
    assert node['attributes']['pdf_page_start']==node['attributes']['pdf_page_end']==77
    assert node['attributes']['independent_profile']['statement_sha256']==m.STATEMENT
    assert node['attributes']['proof_sha256']==m.PROOF
    assert node['attributes']['source_segment_chars']==635
    assert run(inputs)==(out,audit)
    assert 'Lemma 3.6.' not in json.dumps(out)

@pytest.mark.parametrize('bad',['pin','variant','other_config','lemma_hash','prop_hash','missing_dependency','outgoing_dependency','existing_proof','span','families','ontology_edge'])
def test_fail_closed(inputs,bad):
    m,g,b,o,s=inputs
    if bad=='pin':next(r for r in b['support_frontier'] if r['source_id']==m.LEMMA)['statement_sha256']='0'*64
    elif bad=='variant':b.pop('qualification_variant')
    elif bad=='other_config':b['stage']='OTHER'
    elif bad in ('lemma_hash','prop_hash','families'):
        node=next(n for n in g['nodes'] if n['id']==(m.PROP if bad=='prop_hash' else m.LEMMA))
        if bad=='families':node['attributes']['independent_profile']['eo_direct_families']=[]
        else:node['attributes']['independent_profile']['statement_sha256']='0'*64
    elif bad=='missing_dependency':g['edges']=[e for e in g['edges'] if not(e['type']=='DEPENDS_ON' and e['source']==m.THEOREM and e['target']==m.LEMMA)]
    elif bad=='outgoing_dependency':g['edges'].append({'id':'bad','type':'DEPENDS_ON','source':m.LEMMA,'target':m.THEOREM})
    elif bad=='existing_proof':g['nodes'].append({'id':'proof:lemma:3_6'})
    elif bad=='span':s['statement']+=' '
    elif bad=='ontology_edge':next(e for e in g['edges'] if e['source']==m.LEMMA and e['type']=='HAS_CONCEPT')['target']='ontology:concept:wrong'
    with pytest.raises(ValueError):run(inputs)


def test_validator_rejects_metadata_only_forgery(tmp_path):
    m=mod();bindings=tmp_path/'bindings.json';bindings.write_text('{}')
    with pytest.raises(ValueError):m.validate_corrected_graph({'nodes':[],'edges':[],'source_correction_audit':{'status':'PASS','qualification_variant':'CORRECTED_SOURCE_V1'}},bindings)


def test_validator_rejects_mutations(inputs,tmp_path):
    m,g,b,o,s=inputs;path=tmp_path/'bindings.json';path.write_text(json.dumps(b))
    graph,audit=m.correct_graph(g,b,o,s,base_graph_sha256='a'*64,bindings_sha256=m.sha(path.read_bytes()))
    assert m.validate_corrected_graph(graph,path) is True
    for mutation in ('digest','node','proof','edge','old','boundary','scope','version','binding'):
        bad=copy.deepcopy(graph);a=bad['source_correction_audit']
        if mutation=='digest':a['canonical_graph_sha256']='0'*64
        elif mutation=='node':next(n for n in bad['nodes'] if n['id']==m.LEMMA)['attributes']['proof_chars']=0
        elif mutation=='proof':bad['nodes']=[n for n in bad['nodes'] if n['id']!='proof:lemma:3_6']
        elif mutation=='edge':bad['edges']=bad['edges'][:-1]
        elif mutation=='old':a['superseded_node']['attributes']['pdf_page_start']=77
        elif mutation=='boundary':a['boundaries']['statement']['pdf_page']=97
        elif mutation=='scope':a['semantic_profile_scope']='COMBINED'
        elif mutation=='version':a['extractor_version']='1.26.6'
        else:a['bindings_sha256']='0'*64
        if mutation in ('node','proof','edge'):
            a['canonical_graph_sha256']=m.canonical_graph_sha256(bad)
        with pytest.raises(ValueError):m.validate_corrected_graph(bad,path)


def test_real_source_boundary_and_citation(inputs):
    m,g,b,o,s=inputs
    assert m.sha(s['statement'].encode())==m.STATEMENT
    assert m.sha(s['proof'].encode())==m.PROOF
    assert m.sha(s['theorem_statement'].encode())==m.THEOREM_HASH
    assert m.sha(s['theorem_proof'].encode())==m.THEOREM_PROOF
    assert 'Lemma 3.6' in s['theorem_proof']
    assert len(s['statement'])==248 and len(s['proof'])==386
