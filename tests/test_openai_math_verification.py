"""Independent verifier acceptance and corruption checks on a tiny Git corpus."""
from argparse import Namespace
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from scripts import verify_openai_math_intake as verifier


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    # Reuse the actual importer fixture without importing its validation code
    # into the verifier. It also checks replay and atomic publication behavior.
    path=Path(__file__).with_name('test_openai_math_intake.py')
    spec=importlib.util.spec_from_file_location('verification_fixture_intake',path)
    fixture=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    fixture.test_complete_intake_links_actual_scanned_records_and_replays(tmp_path,monkeypatch)
    revision=subprocess.check_output(['git','-C',str(tmp_path/'source'),'rev-parse','HEAD'],text=True).strip()
    return Namespace(source_repo=tmp_path/'source',revision=revision,base_graph=tmp_path/'base.json',
        graph=tmp_path/'first/mapeogeo_openai_math_graph.json.gz',
        manifest=tmp_path/'first/source_manifest.json.gz',report=tmp_path/'first/intake_report.json',
        output=tmp_path/'independent_audit.json',sqlite_dir=tmp_path)


def test_independent_streaming_audit_passes_and_binds_its_code(bundle):
    result=verifier.audit(bundle)
    assert result['status']=='PASS'
    assert result['counts']['tracked_files']==10
    assert result['counts']['audited_source_spans']==3
    assert result['counts']['nodes']==23
    assert result['counts']['edges']==30
    assert result['verifier_sha256']==hashlib.sha256(Path(verifier.__file__).read_bytes()).hexdigest()


@pytest.mark.parametrize('corruption,match',[
    ('historical_payload','historical payload'),
    ('duplicate_id','UNIQUE constraint'),
    ('edge_identity','edge content identity'),
    ('certificate_promotion','unexpected imported type'),
    ('span_integrity','span hash mismatch'),
])
def test_independent_audit_rejects_corruption(bundle,corruption,match):
    # Loading is restricted to this 23-node fixture, never the production graph.
    with gzip.open(bundle.graph,'rt') as handle:
        graph=deepcopy(json.load(handle))
    if corruption=='historical_payload':graph['nodes'][0]['label']='altered'
    elif corruption=='duplicate_id':graph['nodes'].append(graph['nodes'][-1])
    elif corruption=='edge_identity':graph['edges'][0]['target']='missing'
    elif corruption=='certificate_promotion':graph['nodes'][1]['type']='CERTIFICATE'
    elif corruption=='span_integrity':
        record=next(node for node in graph['nodes'] if node['type']=='SOURCE_RECORD')
        record['attributes']['span_sha256']='0'*64
    altered=bundle.graph.with_name(corruption+'.json.gz')
    with gzip.open(altered,'wt') as handle:json.dump(graph,handle)
    bundle.graph=altered
    with pytest.raises((ValueError,sqlite3.IntegrityError),match=match):verifier.audit(bundle)
    assert not bundle.output.exists()


def test_verifier_requires_symbolic_tex_label_resolution():
    attrs={'stage':'openai_math','verification_status':'UNTESTED',
           'reference_kind':'tex_label','resolution_status':'SYMBOLIC_LABEL'}
    item={'id':'oam:test:label','type':'SOURCE_REFERENCE_RECORD','attributes':attrs}
    verifier.check_payload(item)
    for wrong in ['EXTERNAL_RESOURCE','RESOLVED','UNRESOLVED_REFERENCE']:
        with pytest.raises(ValueError,match='TeX label'):
            verifier.check_payload({**item,'attributes':{**attrs,'resolution_status':wrong}})
    with pytest.raises(ValueError,match='symbolic label'):
        verifier.check_payload({'id':'oam:edge:test','type':'SOURCE_REFERENCE',
            'attributes':{**attrs,'evidence_status':'UNVERIFIED'}},edge=True)


@pytest.mark.parametrize('kind',['tex_input','tex_include'])
def test_verifier_requires_symbolic_tex_macro_arguments(kind):
    attrs={'stage':'openai_math','verification_status':'UNTESTED','reference_kind':kind,
           'target_identifier':r'#1\relax#2','resolution_status':'SYMBOLIC_REFERENCE'}
    item={'id':'oam:test:reference','type':'SOURCE_REFERENCE_RECORD','attributes':attrs}
    verifier.check_payload(item)
    with pytest.raises(ValueError,match='macro argument'):
        verifier.check_payload({**item,'attributes':{**attrs,'resolution_status':'LOCAL_ANCHOR'}})
