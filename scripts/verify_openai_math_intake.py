#!/usr/bin/env python3
"""Independent streaming audit of the OpenAI math intake. Requires ijson.

No intake implementation is imported, and no merged graph is loaded wholesale.
SQLite stores exact identities, payload digests, endpoints and source coverage.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import resource as process_resource
import sqlite3
import subprocess
import tempfile
import time
import ijson
import yaml
from ijson.common import ObjectBuilder

FORBIDDEN_KEYS = {'statement_text','proof_text','source_prose','page_image','excerpt',
                  'raw_content','raw_text','raw_bytes','source_text','full_text'}
ALLOWED_NODE_TYPES = {'SOURCE_REPOSITORY','SOURCE_FAMILY','SOURCE_DOCUMENT',
    'FORMAL_CHECK_CONFIGURATION','FORMAL_TARGET','FORMAL_CATALOGUE_RECORD',
    'SOURCE_RESOURCE','SOURCE_RECORD','SOURCE_REFERENCE_RECORD','UNRESOLVED_DEFICIT'}
ALLOWED_EDGE_TYPES = {'CONTAINS_SOURCE_RECORD','SOURCE_DOCUMENTS','HAS_SOURCE_RESOURCE',
    'CONFIGURES_SOURCE_CHECK','SELECTS_FORMAL_TARGET','HAS_SCOPE_DOCUMENT',
    'LEXICALLY_MATCHES_TARGET','SOURCE_REFERENCE','HAS_UNRESOLVED_REFERENCE','HAS_WOUND','CANDIDATE_REPRESENTS'}
VERIFIED_VALUES = {'VERIFIED','PASS','KERNEL_VERIFIED','EXECUTABLE_VERIFIED'}

def canonical(value):
    return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def filehash(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):digest.update(chunk)
    return digest.hexdigest()

def openjson(path):
    return gzip.open(path,'rb') if path.suffix=='.gz' else path.open('rb')

def graph_items(path):
    """Yield nodes and edges in physical order in one decompression pass."""
    with openjson(path) as f:
        builder=None; depth=0; kind=None
        for prefix,event,value in ijson.parse(f,use_float=True):
            if builder is None:
                if prefix in {'nodes.item','edges.item'}:
                    if event!='start_map':raise ValueError('graph item must be an object')
                    kind=prefix.split('.')[0];builder=ObjectBuilder();depth=0
                else:continue
            builder.event(event,value)
            if event in {'start_map','start_array'}:depth+=1
            elif event in {'end_map','end_array'}:depth-=1
            if depth==0:
                yield kind,builder.value
                builder=None

def check_payload(item,edge=False):
    allowed=ALLOWED_EDGE_TYPES if edge else ALLOWED_NODE_TYPES
    if item.get('type') not in allowed:raise ValueError('unexpected imported type '+str(item.get('type')))
    def walk(value):
        if isinstance(value,dict):
            for key,child in value.items():
                if key.lower() in FORBIDDEN_KEYS:raise ValueError('source prose payload '+key)
                if ('verification' in key or key=='evidence_status') and isinstance(child,str) and child in VERIFIED_VALUES:
                    raise ValueError('verification promotion '+key)
                walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(item)
    if item.get('attributes',{}).get('stage')!='openai_math':raise ValueError('import lacks stage provenance')
    if edge:
        require(item['attributes'].get('evidence_status')=='UNVERIFIED','imported edge evidence level promoted')
    else:
        require(item['attributes'].get('verification_status')=='UNTESTED','imported node verification level promoted')
    attrs=item['attributes']
    if edge and item.get('type')=='CANDIDATE_REPRESENTS':
        require(attrs.get('reconciliation_status')=='CANDIDATE_ONLY','canonical candidate promoted beyond candidate-only')
        require(attrs.get('semantic_equivalence_status')=='NOT_ESTABLISHED','canonical candidate asserts semantic equivalence')
        require(str(item.get('target','')).startswith('canonical:'),'canonical candidate target is not canonical')
        require(str(item.get('source','')).startswith('oam:'),'canonical candidate source is not imported source record')
    if attrs.get('reference_kind')=='tex_label':
        require(item.get('type')!='SOURCE_REFERENCE','TeX symbolic label incorrectly resolved as file edge')
        require(attrs.get('resolution_status')=='SYMBOLIC_LABEL','TeX label classified as external/file reference')
    target=attrs.get('target_identifier')
    if attrs.get('reference_kind') in {'tex_input','tex_include'} and isinstance(target,str):
        if not target or any(marker in target for marker in ('#','\\','{','}')):
            require(attrs.get('resolution_status')=='SYMBOLIC_REFERENCE','TeX macro argument classified as file reference')

def require(condition,message):
    if not condition:raise ValueError(message)

def audit(args):
    started=time.time();revision=args.revision;prefix='oam:'+revision
    require(re.fullmatch('[0-9a-f]{40}',revision),'full revision SHA required')
    def git(*a):return subprocess.check_output(['git','-C',str(args.source_repo),*a])
    require(git('rev-parse','HEAD').decode().strip()==revision,'source HEAD differs')
    tree=git('rev-parse',revision+'^{tree}').decode().strip()
    work=tempfile.TemporaryDirectory(prefix='independent-oam-audit-',dir=args.sqlite_dir)
    db=sqlite3.connect(str(Path(work.name)/'audit.sqlite'))
    db.executescript('''PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA temp_store=FILE;
      PRAGMA cache_size=-65536;
      CREATE TABLE nodes(id TEXT PRIMARY KEY,digest BLOB,base INTEGER,seen INTEGER) WITHOUT ROWID;
      CREATE TABLE edges(id TEXT PRIMARY KEY,digest BLOB,base INTEGER,seen INTEGER,source TEXT,target TEXT) WITHOUT ROWID;
      CREATE TABLE resources(path TEXT PRIMARY KEY,gitsha TEXT,size INTEGER,mode TEXT,sha256 TEXT,manifest INTEGER DEFAULT 0,graph INTEGER DEFAULT 0,disposition TEXT,records INTEGER,refs INTEGER) WITHOUT ROWID;
      CREATE TABLE families(id TEXT PRIMARY KEY,seen INTEGER DEFAULT 0) WITHOUT ROWID;
      CREATE TABLE papers(path TEXT PRIMARY KEY,family TEXT,seen INTEGER DEFAULT 0) WITHOUT ROWID;
      CREATE TABLE configs(id TEXT PRIMARY KEY,path TEXT,seen INTEGER DEFAULT 0) WITHOUT ROWID;
      CREATE TABLE targets(id TEXT PRIMARY KEY,theorem TEXT,config TEXT,ordinal INTEGER,seen INTEGER DEFAULT 0) WITHOUT ROWID;
      CREATE TABLE main_results(id TEXT PRIMARY KEY,theorem TEXT,ordinal INTEGER,seen INTEGER DEFAULT 0) WITHOUT ROWID;
    ''')
    counts=Counter();types={'nodes':Counter(),'edges':Counter()};digests={'nodes':hashlib.sha256(),'edges':hashlib.sha256()}
    for kind,item in graph_items(args.base_graph):
        require(isinstance(item.get('id'),str) and item['id'],'base item identity missing')
        table='nodes' if kind=='nodes' else 'edges';payload=canonical(item)
        if table=='nodes':db.execute('INSERT INTO nodes VALUES(?,?,1,0)',(item['id'],hashlib.sha256(payload).digest()))
        else:db.execute('INSERT INTO edges VALUES(?,?,1,0,?,?)',(item['id'],hashlib.sha256(payload).digest(),item['source'],item['target']))
        counts['base_'+kind]+=1
    entries=git('ls-tree','-r','-z','-l',revision)
    for entry in entries.split(b'\0'):
        if not entry:continue
        header,path=entry.split(b'\t',1);mode,kind,sha,size=header.decode().split();path=path.decode()
        require(kind=='blob' and mode in {'100644','100755'},'unsupported Git entry')
        raw=(args.source_repo/path).read_bytes()
        require(len(raw)==int(size),'source size changed '+path)
        require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==sha,'source blob changed '+path)
        db.execute('INSERT INTO resources(path,gitsha,size,mode,sha256) VALUES(?,?,?,?,?)',(path,sha,int(size),mode,hashlib.sha256(raw).hexdigest()))
        counts['tracked_files']+=1;counts['tracked_bytes']+=len(raw)
    del entries,raw
    text=(args.source_repo/'CONTENTS.md').read_text();headers=list(re.finditer(r'^\*\*(\d{3})\.\s+(.+?)\*\*',text,re.M))
    for i,h in enumerate(headers):
        fid=h.group(1);db.execute('INSERT INTO families(id) VALUES(?)',(fid,))
        body=text[h.start():headers[i+1].start() if i+1<len(headers) else len(text)]
        for path in re.findall(r'&emsp;\[[^\n]+?\]\((preprints/[^\n]+?\.pdf)\)',body):db.execute('INSERT INTO papers(path,family) VALUES(?,?)',(path,fid))
    counts['families']=db.execute('SELECT COUNT(*) FROM families').fetchone()[0]
    counts['manuscripts']=db.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
    for path in sorted((args.source_repo/'lean/ComparatorChallenges').glob('*.json')):
        c=json.loads(path.read_text());relative=path.relative_to(args.source_repo).as_posix();cid=prefix+':configuration:'+relative
        db.execute('INSERT INTO configs(id,path) VALUES(?,?)',(cid,relative))
        for ordinal,theorem in enumerate(c['theorem_names']):db.execute('INSERT INTO targets(id,theorem,config,ordinal) VALUES(?,?,?,?)',(cid+':target:'+str(ordinal),theorem,cid,ordinal))
    formal=yaml.safe_load((args.source_repo/'lean/formalization.yaml').read_text())
    for ordinal,result in enumerate(formal['status']['main_results']):db.execute('INSERT INTO main_results(id,theorem,ordinal) VALUES(?,?,?)',(prefix+':catalogue-result:'+str(ordinal),result['declaration'],ordinal))
    counts['comparator_configurations']=db.execute('SELECT COUNT(*) FROM configs').fetchone()[0]
    counts['selected_theorem_occurrences']=db.execute('SELECT COUNT(*) FROM targets').fetchone()[0]
    counts['catalogue_main_results']=db.execute('SELECT COUNT(*) FROM main_results').fetchone()[0]
    counts['scope_documents']=sum(bool(re.fullmatch(r'\d{3}\.md',p.name)) for p in (args.source_repo/'lean/docs').glob('*.md'))
    manifest_digest=hashlib.sha256()
    with openjson(args.manifest) as f:
        for resource in ijson.items(f,'resources.item',use_float=True):
            path=resource['path'];row=db.execute('SELECT gitsha,size,mode,sha256,manifest FROM resources WHERE path=?',(path,)).fetchone()
            require(row is not None,'manifest extra path '+path)
            require(row[:4]==(resource['sha'],resource['size'],resource['mode'],resource['sha256']),'manifest source identity mismatch '+path)
            require(row[4]==0,'duplicate manifest path '+path)
            db.execute('UPDATE resources SET manifest=1,disposition=?,records=?,refs=? WHERE path=?',(resource['disposition'],resource['lexical_records'],resource['references'],path))
            manifest_digest.update(canonical(resource)+b'\n');counts['manifest_resources']+=1
    raw=None;current_resource=None;raw_hash=None;resource_record_counts=Counter()
    for kind,item in graph_items(args.graph):
        counts[kind]+=1;types[kind][item.get('type','UNKNOWN')]+=1;payload=canonical(item);digests[kind].update(payload+b'\n')
        identity=item.get('id');require(isinstance(identity,str) and identity,'graph item identity missing')
        signature=hashlib.sha256(payload).digest();table=kind
        imported=identity.startswith(prefix+':') if kind=='nodes' else identity.startswith('oam:edge:')
        if imported:
            check_payload(item,edge=kind=='edges')
            if kind=='edges':
                extra={k:v for k,v in item['attributes'].items() if k not in {'stage','evidence_status'}}
                expected='oam:edge:'+hashlib.sha256(canonical([item['type'],item['source'],item['target'],extra])).hexdigest()
                require(identity==expected,'imported edge content identity differs')
            if kind=='nodes':db.execute('INSERT INTO nodes VALUES(?,?,0,1)',(identity,signature))
            else:db.execute('INSERT INTO edges VALUES(?,?,0,1,?,?)',(identity,signature,item['source'],item['target']))
            counts['imported_'+kind]+=1
        else:
            row=db.execute('SELECT digest,base,seen FROM '+table+' WHERE id=?',(identity,)).fetchone()
            require(row is not None and row[1]==1,'unexpected nonimport identity '+identity)
            require(row[0]==signature and row[2]==0,'changed or duplicated historical payload '+identity)
            db.execute('UPDATE '+table+' SET seen=1 WHERE id=?',(identity,))
        if kind!='nodes' or not imported:continue
        attrs=item.get('attributes',{});typ=item['type']
        if typ=='SOURCE_REPOSITORY':
            require(attrs['revision']==revision and attrs['root_tree']==tree,'repository identity mismatch')
            require(attrs['tracked_files']==counts['tracked_files'] and attrs['tracked_bytes']==counts['tracked_bytes'],'repository scope mismatch')
            counts['repositories']+=1
        elif typ=='SOURCE_RESOURCE':
            path=attrs['path'];row=db.execute('SELECT gitsha,size,mode,sha256,graph,disposition,records FROM resources WHERE path=?',(path,)).fetchone()
            require(row is not None,'extra graph source path '+path)
            require(row[:4]==(attrs['git_blob_sha'],attrs['size_bytes'],attrs['mode'],attrs['sha256']),'graph resource identity mismatch '+path)
            require(row[4]==0 and row[5:]==(attrs['extraction_disposition'],attrs['lexical_record_count']),'graph resource duplication/disposition mismatch '+path)
            require(identity==prefix+':file:'+path and attrs['repository_revision']==revision,'resource ID/revision mismatch')
            db.execute('UPDATE resources SET graph=1 WHERE path=?',(path,));counts['graph_resources']+=1
        elif typ=='SOURCE_FAMILY':
            require(db.execute('UPDATE families SET seen=seen+1 WHERE id=?',(attrs['family_id'],)).rowcount==1,'extra family ID')
        elif typ=='SOURCE_DOCUMENT':
            require(db.execute('UPDATE papers SET seen=seen+1 WHERE path=? AND family=?',(attrs['catalogue_pdf'],attrs['family_id'])).rowcount==1,'extra manuscript')
        elif typ=='FORMAL_CHECK_CONFIGURATION':
            row=db.execute('SELECT path,seen FROM configs WHERE id=?',(identity,)).fetchone();require(row is not None and row[1]==0,'extra/duplicate configuration')
            expected=json.loads((args.source_repo/row[0]).read_text())
            for key in ['challenge_module','solution_module','permitted_axioms','definition_names']:
                require(attrs.get(key)==expected.get(key,[]),'configuration field differs '+key)
            require(attrs['selected_theorem_names']==expected['theorem_names'],'selected theorem list differs')
            require(attrs['independent_run_status']=='NOT_RUN' and attrs['statement_correspondence_status']=='UNREVIEWED','config promoted')
            require(attrs['external_checker_configuration']=={k:expected[k] for k in ['enable_nanoda','external_kernels'] if k in expected},'external checker settings differ')
            db.execute('UPDATE configs SET seen=1 WHERE id=?',(identity,))
        elif typ=='FORMAL_TARGET':
            row=db.execute('SELECT theorem,config,ordinal,seen FROM targets WHERE id=?',(identity,)).fetchone()
            require(row is not None and row[:3]==(attrs['theorem_name'],attrs['configuration'],attrs['target_ordinal']) and row[3]==0,'formal target identity differs')
            require(attrs['kernel_verification_status']=='UNTESTED' and attrs['correspondence_status']=='UNREVIEWED','formal target promoted')
            db.execute('UPDATE targets SET seen=1 WHERE id=?',(identity,))
        elif typ=='FORMAL_CATALOGUE_RECORD':
            row=db.execute('SELECT theorem,ordinal,seen FROM main_results WHERE id=?',(identity,)).fetchone()
            require(row is not None and row[:2]==(attrs['theorem_name'],attrs['catalogue_ordinal']) and row[2]==0,'main catalogue record differs')
            require(attrs['upstream_scope']==formal['status'].get('scope') and attrs['upstream_review_status']==formal.get('review',{}).get('status'),'upstream review/scope metadata differs')
            db.execute('UPDATE main_results SET seen=1 WHERE id=?',(identity,))
        elif typ=='SOURCE_RECORD':
            rid=attrs['source_resource'];require(rid.startswith(prefix+':file:'),'record resource identity')
            path=rid[len(prefix+':file:'):]
            if rid!=current_resource:raw=(args.source_repo/path).read_bytes();current_resource=rid;raw_hash=hashlib.sha256(raw).hexdigest()
            require(attrs['source_sha256']==raw_hash and attrs['context_sha256']==attrs['source_sha256'],'record context hash mismatch')
            start,end=attrs['start_byte'],attrs['end_byte'];require(0<=start<=end<=len(raw),'invalid byte span')
            require(hashlib.sha256(raw[start:end]).hexdigest()==attrs['span_sha256'],'record span hash mismatch')
            require(attrs['extraction_status']=='LEXICAL_CANDIDATE' and attrs['kernel_verification_status']=='UNTESTED','record promoted')
            counts['audited_source_spans']+=1
            resource_record_counts[path]+=1
        if counts[kind]%500000==0:print('Audited',counts[kind],kind,flush=True);db.commit()
    db.commit()
    for table in ['nodes','edges']:require(db.execute('SELECT COUNT(*) FROM '+table+' WHERE base=1 AND seen!=1').fetchone()[0]==0,'historical '+table+' missing')
    require(db.execute('SELECT COUNT(*) FROM resources WHERE manifest!=1 OR graph!=1').fetchone()[0]==0,'incomplete tracked-source coverage')
    require(db.execute('SELECT COUNT(*) FROM families WHERE seen!=1').fetchone()[0]==0,'family coverage mismatch')
    require(db.execute('SELECT COUNT(*) FROM papers WHERE seen!=1').fetchone()[0]==0,'manuscript coverage mismatch')
    for table in ['configs','targets','main_results']:require(db.execute('SELECT COUNT(*) FROM '+table+' WHERE seen!=1').fetchone()[0]==0,table+' coverage mismatch')
    for path,expected in db.execute('SELECT path,records FROM resources'):require(resource_record_counts[path]==expected,'lexical record count differs '+path)
    require(db.execute('SELECT COUNT(*) FROM edges e LEFT JOIN nodes s ON s.id=e.source LEFT JOIN nodes t ON t.id=e.target WHERE s.id IS NULL OR t.id IS NULL').fetchone()[0]==0,'dangling graph endpoints')
    with args.report.open() as f:report=json.load(f) # Small report only.
    with openjson(args.graph) as f:
        intake_metadata=next(ijson.items(f,'source_intakes.item',use_float=True),None)
    with openjson(args.manifest) as f:
        manifest_metadata=next(ijson.items(f,'source',use_float=True),None)
    require(intake_metadata==report['source']==manifest_metadata,'graph/manifest/report provenance metadata differs')
    require(report['source']['revision']==revision and report['source']['tree']==tree,'reported source identity differs')
    implementation_root=Path(__file__).resolve().parents[1]
    for relative,expected in report['source'].get('implementation_sha256',{}).items():
        require(filehash(implementation_root/relative)==expected,'implementation code digest differs '+relative)
    pin=implementation_root/'formal/openai_math_source_pin.json'
    # Fixture pins live outside the repository; production revision uses the
    # committed pin and must also match its recorded identity.
    if revision=='adc7f1241b42e322a6451854ab7e4b4c146bf78a':
        require(filehash(pin)==report['source']['source_pin_sha256'],'source pin digest differs')
    require(report['coverage']=={key:counts[key] for key in ['tracked_files','tracked_bytes','families','manuscripts','scope_documents','comparator_configurations','selected_theorem_occurrences','catalogue_main_results']},'reported source coverage differs')
    require(report['graph']['nodes']==counts['nodes'] and report['graph']['edges']==counts['edges'],'reported counts differ')
    require(report['graph']['node_types']==dict(types['nodes']) and report['graph']['edge_types']==dict(types['edges']),'reported type counts differ')
    require(report['graph']['nodes_payload_sha256']==digests['nodes'].hexdigest(),'node payload stream digest differs')
    require(report['graph']['edges_payload_sha256']==digests['edges'].hexdigest(),'edge payload stream digest differs')
    require(report['source_manifest']['inventory_sha256']==manifest_digest.hexdigest(),'manifest digest differs')
    artifact_hashes={}
    for name,path,expected in [('graph',args.graph,report['graph']['sha256']),('source_manifest',args.manifest,report['source_manifest']['sha256']),('base_graph',args.base_graph,report['base']['sha256'])]:
        actual=filehash(path);require(actual==expected,'file digest differs '+str(path));artifact_hashes[name]=actual
    require(counts['repositories']==1,'repository node count mismatch')
    result={'status':'PASS','scope':'INDEPENDENT_STREAMING_OUTPUT_AUDIT','revision':revision,'tree':tree,
      'verifier_sha256':filehash(Path(__file__).resolve()),'counts':dict(counts),
      'artifact_sha256':artifact_hashes,'peak_rss_kib':process_resource.getrusage(process_resource.RUSAGE_SELF).ru_maxrss,
      'nodes_payload_sha256':digests['nodes'].hexdigest(),'edges_payload_sha256':digests['edges'].hexdigest(),
      'manifest_payload_sha256':manifest_digest.hexdigest(),'node_types':dict(types['nodes']),'edge_types':dict(types['edges']),
      'checks':['exact historical node and edge payload preservation','all Git paths, modes, sizes, SHA1 and SHA256 identities',
        'all catalogue families and manuscripts','all source span hashes','exact unique identities and endpoint existence',
        'allowed source-only types and unverified evidence levels','report counts and payload/file digests'],
      'limitations':['lexical header hashes are not re-elaborated','no proof checker execution','no natural-language/formal statement equivalence certification'],
      'elapsed_seconds':round(time.time()-started,2)}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');db.close();work.cleanup();return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source-repo','base-graph','graph','manifest','report','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--revision',default='adc7f1241b42e322a6451854ab7e4b4c146bf78a');p.add_argument('--sqlite-dir',type=Path)
    args=p.parse_args();result=audit(args);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
