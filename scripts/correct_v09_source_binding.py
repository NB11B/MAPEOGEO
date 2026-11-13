#!/usr/bin/env python3
"""Audited, separately qualified repair of one mislabeled source declaration.

Source text exists only transiently. This does not mutate frozen acceptance data
or claim to formalize the whole cited theorem. The corrected semantic profile
is deliberately statement-only, matching independent-profile evidence scope;
the superseded combined-segment profile remains preserved in the audit.
"""
from __future__ import annotations
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEMMA='srcdecl:lemma:3_6'
PROP='srcdecl:proposition:6_7'
THEOREM='srcdecl:theorem:3_7'
PDF_SHA='a1f91e337445851d27f2f4adb61e8ccc0f8fac941f9e0254ad94ba6b91c7c49b'
PDF_SIZE=24629575
STATEMENT='7b23d4bb370df45d743d82405c8339622c804dee0a3d0575ace2638bde9fd955'
PROOF='c69f7b6d625ee206a14eed6da8b8ceee01b3646d49035cb3e4ec607cd75ba67b'
COMBINED='81d32dea618aa9d5eaa7b1ec254052632e4f9e92bf55a7be31cb4f931938df8b'
OLD_LEMMA='8c777553c7ec6a145870e89011cdfa811bd9fbb7d04b666620c963849224cbb3'
PROP_HASH='ed9e437c8a539615e0759d0f6ccfea972afe87ad106a304c780d9e6ff59895d3'
THEOREM_HASH='308a9240278368e4f17acc97d6385aa540d05688bda5d8aae87a5b75a11333de'
THEOREM_PROOF='78344260dd7d2b6119687907f86fe4f0f82980b84107a3da3b3de3bfd0c43190'
BOUNDARIES={'statement':{'pdf_page':77,'lines_zero_based_half_open':[35,38]},'proof':{'pdf_page':77,'lines_zero_based_half_open':[38,44]},'theorem_statement':{'pdf_page':78,'lines_zero_based_half_open':[7,10]},'theorem_proof':{'pdf_page':78,'lines_zero_based_half_open':[10,17]}}

def require(condition,message):
    if not condition:raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def modules():
    spec=importlib.util.spec_from_file_location('correction_v06',ROOT/'scripts/independent_dual_view_v0_6.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def validate_spans(spans):
    require(set(spans)==set(BOUNDARIES),'unexpected source fields')
    for key,expected in [('statement',STATEMENT),('proof',PROOF),('theorem_statement',THEOREM_HASH),('theorem_proof',THEOREM_PROOF)]:
        require(isinstance(spans[key],str) and sha(spans[key].encode())==expected,'source span mismatch: '+key)
    require(len(spans['statement'])==248 and len(spans['proof'])==386,'source span length mismatch')
    require(sha((spans['statement']+'\n'+spans['proof']).encode())==COMBINED,'combined source mismatch')
    require('Lemma 3.6' in spans['theorem_proof'],'missing actual source citation')

def extract_source(pdf):
    """Extract exact audited physical lines, never the ambiguous global heading scan."""
    raw=Path(pdf).read_bytes()
    require(len(raw)==PDF_SIZE and sha(raw)==PDF_SHA,'source PDF identity mismatch')
    import fitz
    require(fitz.VersionBind=='1.28.2','extractor must be PyMuPDF 1.28.2')
    v06=modules();spans={}
    with fitz.open(pdf) as doc:
        for key,b in BOUNDARIES.items():
            lo,hi=b['lines_zero_based_half_open']
            lines=doc[b['pdf_page']-1].get_text('text',sort=True).splitlines()[lo:hi]
            spans[key]='\n'.join(v06.v05.normalize_text(line) for line in lines)
    validate_spans(spans)
    return spans

def correct_graph(base_graph,bindings,original_bindings,spans,*,base_graph_sha256,bindings_sha256):
    """Pure fail-closed correction; inputs and historical evidence remain untouched."""
    validate_spans(spans)
    for h in (base_graph_sha256,bindings_sha256):
        require(isinstance(h,str) and len(h)==64 and all(c in '0123456789abcdef' for c in h),'invalid input digest')
    expected=copy.deepcopy(original_bindings)
    for sid,h in ((LEMMA,STATEMENT),(PROP,PROP_HASH)):
        matches=[r for r in expected['support_frontier'] if r['source_id']==sid]
        require(len(matches)==1,'nonunique original binding')
        matches[0]['statement_sha256']=h
    expected['qualification_variant']='CORRECTED_SOURCE_V1'
    require(bindings==expected,'unapproved binding change')
    graph=copy.deepcopy(base_graph)
    require('source_correction_audit' not in graph,'already corrected graph')
    nodes=graph['nodes'];edges=graph['edges'];by={n['id']:n for n in nodes}
    require(len(by)==len(nodes) and len({e['id'] for e in edges})==len(edges),'duplicate graph IDs')
    require(all(sid in by for sid in (LEMMA,PROP,THEOREM)),'missing declaration')
    for sid,h,start,end,chars in [(LEMMA,OLD_LEMMA,97,98,1777),(PROP,PROP_HASH,176,177,1009)]:
        a=by[sid]['attributes'];p=a['independent_profile']
        require(by[sid]['type']=='STATEMENT' and a['pdf_page_start']==start and a['pdf_page_end']==end and a['source_segment_sha256']==h and a['source_segment_chars']==chars and p['statement_sha256']==h and p['statement_chars']==chars,'base declaration mismatch: '+sid)
    require(by[THEOREM]['attributes']['independent_profile']['statement_sha256']==THEOREM_HASH,'theorem binding mismatch')
    require(any(e['type']=='DEPENDS_ON' and e['source']==THEOREM and e['target']==LEMMA for e in edges),'missing theorem dependency')
    require(not any(e['type']=='DEPENDS_ON' and e['source']==LEMMA for e in edges),'lemma has outgoing dependencies needing broader repair')
    pid='proof:lemma:3_6';eid='e:proof:lemma:3_6:produces'
    require(pid not in by and not any(e['id']==eid or (e['type']=='PRODUCES' and e['target']==LEMMA) for e in edges),'preexisting lemma proof')
    a=by[LEMMA]['attributes'];old=copy.deepcopy(by[LEMMA]);v06=modules()
    require(a['proof_present'] is False and a['proof_chars']==0 and a['proof_sha256'] is None,'base lemma proof metadata mismatch')
    semantic=v06.v05.profile_segment(spans['statement'],3)
    eo=v06.detect(v06.EO_BANK,spans['statement']);geo=v06.detect(v06.GEO_BANK,spans['statement'])
    status='DUAL_DIRECT' if eo and geo else ('EO_ONLY_DIRECT' if eo else ('GEO_ONLY_DIRECT' if geo else 'NO_DIRECT_VIEW'))
    for key,value in [('eo_direct_families',eo),('geo_direct_families',geo),('direct_status',status)]:
        require(a['independent_profile'][key]==value,'family change requires broader repair')
    for key in ('selected_concepts','eo_candidate_families','geo_candidate_families','dualization_status'):
        require(a['semantic_profile'][key]==semantic[key],'ontology change requires broader repair')
    expected_edges=[]
    for kind,prefix,key,attrs in [
        ('HAS_CONCEPT','concept','selected_concepts',{'evidence':semantic['evidence']}),
        ('CANDIDATE_EO','eo','eo_candidate_families',{'status':'HEURISTIC_CANDIDATE','evidence':semantic['evidence']}),
        ('CANDIDATE_GEO','geo','geo_candidate_families',{'status':'HEURISTIC_CANDIDATE','evidence':semantic['evidence']}),
    ]:
        for value in semantic[key]:
            expected_edges.append((kind,'ontology:'+prefix+':'+value.lower(),attrs))
    for kind,prefix,values in [('INDEPENDENT_EO_EVIDENCE','independent-eo',eo),('INDEPENDENT_GEO_EVIDENCE','independent-geo',geo)]:
        for value in values:
            expected_edges.append((kind,'ontology:'+prefix+':'+value.lower(),{'evidence':'STATEMENT_DIRECT'}))
    edge_types={'HAS_CONCEPT','CANDIDATE_EO','CANDIDATE_GEO','INDEPENDENT_EO_EVIDENCE','INDEPENDENT_GEO_EVIDENCE'}
    actual_edges=[(e['type'],e['target'],e.get('attributes',{})) for e in edges if e['source']==LEMMA and e['type'] in edge_types]
    require(sorted(actual_edges,key=repr)==sorted(expected_edges,key=repr),'ontology/family edge set mismatch')
    a.update(pdf_page_start=77,pdf_page_end=77,source_segment_sha256=COMBINED,source_segment_chars=635,proof_present=True,proof_sha256=PROOF,proof_chars=386,semantic_profile=semantic,dualization_status=semantic['dualization_status'])
    a['independent_profile'].update(statement_sha256=STATEMENT,statement_chars=248,eo_direct_families=eo,geo_direct_families=geo,direct_status=status)
    nodes.append({'id':pid,'type':'PROOF_STEP','label':'Proof block for Lemma 3.6','attributes':{'status':'SOURCE_PROOF_BLOCK','proof_sha256':PROOF,'proof_chars':386,'source_statement':LEMMA}})
    edges.append({'id':eid,'type':'PRODUCES','source':pid,'target':LEMMA,'attributes':{'evidence':'SOURCE_PROOF_BLOCK'}})
    audit={'schema':'V09_SOURCE_CORRECTION_V1','status':'PASS','qualification_variant':'CORRECTED_SOURCE_V1','source_pdf':{'sha256':PDF_SHA,'bytes':PDF_SIZE},'extractor_version':'1.28.2','semantic_profile_scope':'CORRECTED_STATEMENT_ONLY','base_graph_sha256':base_graph_sha256,'bindings_sha256':bindings_sha256,'superseded_node':old,'invalid_reason':'CITATION_MISPARSED_AS_DECLARATION','corrected_statement_sha256':STATEMENT,'corrected_proof_sha256':PROOF,'corrected_segment_sha256':COMBINED,'boundaries':copy.deepcopy(BOUNDARIES),'theorem_statement_sha256':THEOREM_HASH,'theorem_proof_sha256':THEOREM_PROOF,'claim_scope':'SCOPED_EXISTING_LEAN_CONTRACT_NOT_FULL_SOURCE_THEOREM'}
    audit['canonical_graph_sha256']=canonical_graph_sha256(graph)
    graph['source_correction_audit']=copy.deepcopy(audit)
    return graph,audit

def canonical_graph_sha256(graph):
    payload={k:v for k,v in graph.items() if k!='source_correction_audit'}
    return sha(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())

def validate_corrected_graph(graph,bindings_path):
    """Validate graph content and all reviewed correction metadata, not a PASS label."""
    try:
        a=graph['source_correction_audit']
        expected={'schema':'V09_SOURCE_CORRECTION_V1','status':'PASS','qualification_variant':'CORRECTED_SOURCE_V1','source_pdf':{'sha256':PDF_SHA,'bytes':PDF_SIZE},'extractor_version':'1.28.2','semantic_profile_scope':'CORRECTED_STATEMENT_ONLY','bindings_sha256':sha(Path(bindings_path).read_bytes()),'invalid_reason':'CITATION_MISPARSED_AS_DECLARATION','corrected_statement_sha256':STATEMENT,'corrected_proof_sha256':PROOF,'corrected_segment_sha256':COMBINED,'boundaries':BOUNDARIES,'theorem_statement_sha256':THEOREM_HASH,'theorem_proof_sha256':THEOREM_PROOF,'claim_scope':'SCOPED_EXISTING_LEAN_CONTRACT_NOT_FULL_SOURCE_THEOREM','canonical_graph_sha256':canonical_graph_sha256(graph)}
        require(set(a)==set(expected)|{'base_graph_sha256','superseded_node'},'unexpected audit fields')
        require(all(a[k]==v for k,v in expected.items()),'audit content mismatch')
        h=a['base_graph_sha256'];require(isinstance(h,str) and len(h)==64 and all(c in '0123456789abcdef' for c in h),'invalid base digest')
        cfg=load(bindings_path);original=load(ROOT/'formal/proof_paths_v0_9.json')
        for sid,h in ((LEMMA,STATEMENT),(PROP,PROP_HASH)):
            rows=[r for r in original['support_frontier'] if r['source_id']==sid]
            require(len(rows)==1,'invalid original bindings');rows[0]['statement_sha256']=h
        original['qualification_variant']='CORRECTED_SOURCE_V1'
        require(cfg==original,'unapproved corrected bindings')
        nodes=graph['nodes'];edges=graph['edges'];by={n['id']:n for n in nodes}
        require(len(by)==len(nodes) and len({e['id'] for e in edges})==len(edges),'duplicate IDs')
        old=a['superseded_node'];oa=old['attributes']
        require(old['id']==LEMMA and old['type']=='STATEMENT' and oa['pdf_page_start']==97 and oa['pdf_page_end']==98 and oa['source_segment_sha256']==OLD_LEMMA and oa['source_segment_chars']==1777 and oa['independent_profile']['statement_sha256']==OLD_LEMMA and oa['independent_profile']['statement_chars']==1777 and oa['proof_present'] is False and oa['proof_sha256'] is None and oa['proof_chars']==0,'superseded declaration mismatch')
        node=by[LEMMA];na=node['attributes'];ip=na['independent_profile']
        require(node['type']=='STATEMENT' and na['pdf_page_start']==77 and na['pdf_page_end']==77 and na['source_segment_sha256']==COMBINED and na['source_segment_chars']==635 and na['proof_present'] is True and na['proof_sha256']==PROOF and na['proof_chars']==386 and ip['statement_sha256']==STATEMENT and ip['statement_chars']==248,'corrected declaration mismatch')
        require(ip['eo_direct_families']==['EO_LINEAR_TRANSFORM'] and ip['geo_direct_families']==['GEO_SUBSPACE'] and ip['direct_status']=='DUAL_DIRECT','corrected families mismatch')
        expected_semantic={'direct_concepts':['VECTOR_SPACE'],'chapter_prior_concepts':['VECTOR_SPACE'],'selected_concepts':['VECTOR_SPACE'],'evidence':'DIRECT_TEXT','eo_candidate_families':['LINEAR_OPERATOR'],'geo_candidate_families':['SUBSPACE_GEOMETRY'],'dualization_status':'DUAL_CANDIDATE'}
        require(na['semantic_profile']==expected_semantic and na['dualization_status']=='DUAL_CANDIDATE','semantic scope mismatch')
        require(by['proof:lemma:3_6']=={'id':'proof:lemma:3_6','type':'PROOF_STEP','label':'Proof block for Lemma 3.6','attributes':{'status':'SOURCE_PROOF_BLOCK','proof_sha256':PROOF,'proof_chars':386,'source_statement':LEMMA}},'proof node mismatch')
        produces=[e for e in edges if e['type']=='PRODUCES' and e['target']==LEMMA]
        require(produces==[{'id':'e:proof:lemma:3_6:produces','type':'PRODUCES','source':'proof:lemma:3_6','target':LEMMA,'attributes':{'evidence':'SOURCE_PROOF_BLOCK'}}],'produces edge mismatch')
        require(by[THEOREM]['attributes']['independent_profile']['statement_sha256']==THEOREM_HASH and any(e['type']=='DEPENDS_ON' and e['source']==THEOREM and e['target']==LEMMA and e.get('attributes',{}).get('evidence')=='SOURCE_PROOF_CROSS_REFERENCE' for e in edges),'actual citation edge missing')
        require(not any(e['type']=='DEPENDS_ON' and e['source']==LEMMA for e in edges),'unexpected lemma dependencies')
        prop=by[PROP]['attributes'];require(prop['independent_profile']['statement_sha256']==PROP_HASH and prop['source_segment_sha256']==PROP_HASH and prop['pdf_page_start']==176 and prop['pdf_page_end']==177 and prop['source_segment_chars']==1009,'proposition binding mismatch')
        # The correction must preserve the prior ontology metadata and edge destinations.
        for key in ('selected_concepts','eo_candidate_families','geo_candidate_families','dualization_status'):
            require(oa['semantic_profile'][key]==expected_semantic[key],'superseded ontology mismatch')
        families={'HAS_CONCEPT':['ontology:concept:vector_space'],'CANDIDATE_EO':['ontology:eo:linear_operator'],'CANDIDATE_GEO':['ontology:geo:subspace_geometry'],'INDEPENDENT_EO_EVIDENCE':['ontology:independent-eo:eo_linear_transform'],'INDEPENDENT_GEO_EVIDENCE':['ontology:independent-geo:geo_subspace']}
        for kind,targets in families.items():require(sorted(e['target'] for e in edges if e['source']==LEMMA and e['type']==kind)==targets,'ontology edge mismatch')
        return True
    except (KeyError,TypeError,AttributeError,IndexError) as exc:
        raise ValueError('malformed corrected graph') from exc

def load(path):
    raw=Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)

def generate(pdf,base_graph_path,bindings_path):
    spans=extract_source(pdf)
    return correct_graph(load(base_graph_path),load(bindings_path),load(ROOT/'formal/proof_paths_v0_9.json'),spans,base_graph_sha256=sha(Path(base_graph_path).read_bytes()),bindings_sha256=sha(Path(bindings_path).read_bytes()))

def write(path,obj):
    raw=(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
    Path(path).write_bytes(gzip.compress(raw,mtime=0) if str(path).endswith('.gz') else raw)

def main():
    ap=argparse.ArgumentParser()
    for name in ('pdf','base-graph','bindings','out-graph','out-audit'):ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args()
    paths=[args.pdf,args.base_graph,args.bindings,args.out_graph,args.out_audit,ROOT/'formal/proof_paths_v0_9.json']
    require(len({p.resolve() for p in paths})==len(paths),'input/output paths must be distinct')
    graph,audit=generate(args.pdf,args.base_graph,args.bindings)
    validate_corrected_graph(graph,args.bindings)
    write(args.out_graph,graph);write(args.out_audit,audit)
    return 0

if __name__=='__main__':raise SystemExit(main())
