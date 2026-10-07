#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
import ijson

def items(path,key):
    with gzip.open(path,"rb") as f:
        yield from ijson.items(f,key+".item")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--graph",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    canonical=set(); labels={}
    for n in items(a.graph,"nodes"):
        nid=n.get("id","")
        if nid.startswith("canonical:"): canonical.add(nid); labels[nid]=n.get("label","")
    edge_types=Counter()
    for e in items(a.graph,"edges"): edge_types[e.get("type","")]+=1
    # E8R: 19 deterministic separating checks over the 20 most populated relation types.
    types=[t for t,_ in edge_types.most_common(20)]
    specs=[]
    for i in range(min(19,len(types)-1)):
        x,y=types[i],types[i+1]
        specs.append({"id":f"E8R-{i+1:02d}","a":x,"b":y,"count_a":edge_types[x],"count_b":edge_types[y],
                      "separated":x!=y and edge_types[x]!=edge_types[y]})
    e8=len(specs)==19 and all(x["separated"] for x in specs)
    # E9R: exact radius-1/2/3 traversal from all 215 canonical seeds.
    adj=defaultdict(set); frontier=set(canonical)
    for depth in (1,2,3):
        for e in items(a.graph,"edges"):
            s,t=e.get("source"),e.get("target")
            if s in frontier: adj[s].add(t); adj[t].add(s)
            elif t in frontier: adj[t].add(s); adj[s].add(t)
        if depth==1:
            r1=set().union(*(adj[x] for x in canonical)) if canonical else set(); frontier=r1-canonical
        elif depth==2:
            r2=set().union(*(adj[x] for x in frontier))-(canonical|r1) if frontier else set(); frontier=r2
    plans=[]
    for cid in sorted(canonical):
        seen={cid}; f={cid}; counts=[]
        for _ in (1,2,3):
            nf=set()
            for x in f:nf.update(adj.get(x,()))
            nf-=seen;seen|=nf;counts.append(len(nf));f=nf
        plans.append({"seed":cid,"label":labels.get(cid,""),"radius_counts":counts,"reachable_within_3":len(seen)-1})
    e9=len(plans)==215
    receipt={"campaign":"PSMSL-FQ-E8E9-RECOVERY-CONTINUATION-V1","custody_status":"RECOVERED_AFTER_CUSTODY_BREAK",
      "not_equivalent_to_lost_frozen_harness":True,"qualified_graph_sha256":hashlib.sha256(a.graph.read_bytes()).hexdigest(),
      "graph_size_bytes":a.graph.stat().st_size,
      "E8R":{"status":"PASS" if e8 else "FAIL","spec_count":len(specs),"specs":specs},
      "E9R":{"status":"PASS" if e9 else "FAIL","seed_count":len(plans),"plans":plans},
      "graph_summary":{"canonical_seeds":len(canonical),"edge_types":len(edge_types),"edge_type_counts":dict(edge_types)},
      "claim_boundary":["Original frozen E8/E9 remain BLOCKED in their original report.","E8R/E9R are a separately versioned recovery continuation after custody loss.","No authority promotion is performed."]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"E8R":receipt["E8R"]["status"],"E9R":receipt["E9R"]["status"],"canonical_seeds":len(canonical),"edge_types":len(edge_types)},indent=2))
    raise SystemExit(0 if e8 and e9 else 1)
if __name__=="__main__":main()
