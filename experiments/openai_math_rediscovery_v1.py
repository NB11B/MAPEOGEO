#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, random, re
from collections import Counter, defaultdict
from pathlib import Path

SEED="MAPEOGEO-OPENAI-MATH-REDISCOVERY-V1"
IMPORT_RE=re.compile(r"(?m)^\s*import\s+([^\n]+)")
TOK=re.compile(r"[A-Za-z]+|\d+")

def h(*xs): return int.from_bytes(hashlib.sha256("|".join((SEED,*map(str,xs))).encode()).digest()[:8],"big")
def hold(a,b): return h("hold",a,b)%5==0
def modules(root):
    out={}
    for p in (root/"lean").rglob("*.lean"):
        rel=p.relative_to(root/"lean").as_posix(); out[rel[:-5].replace("/",".")]=p
    return out
def imports(mods):
    edges=set()
    for m,p in mods.items():
        try: text=p.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        for x in IMPORT_RE.findall(text):
            x=x.split("--",1)[0]
            for t in x.split():
                if t in mods and t!=m: edges.add((m,t))
    return edges
def toks(s): return {x.lower() for x in TOK.findall(s)}
def jac(a,b): return len(a&b)/len(a|b) if a or b else 0.0
def features(a,b,outn,inn):
    ao,bo=outn.get(a,set()),outn.get(b,set()); ai,bi=inn.get(a,set()),inn.get(b,set())
    common_out=len(ao&bo); common_in=len(ai&bi)
    twohop=sum(1 for x in ao if b in outn.get(x,set()))
    rev_twohop=sum(1 for x in bi if x in outn.get(a,set()))
    structural=(2*twohop+rev_twohop+common_out+common_in)/(1+math.log2(2+len(ao)+len(bo)+len(ai)+len(bi)))
    return structural,jac(toks(a),toks(b))
def eval_method(cases,key):
    rr=[]; hit1=hit5=hit10=0; auc=[]
    for c in cases:
        pos=c["positive"][key]; neg=[x[key] for x in c["negatives"]]
        higher=sum(v>pos for v in neg); equal=sum(v==pos for v in neg)
        r=1+higher+equal/2
        rr.append(1/r); hit1+=r<=1; hit5+=r<=5; hit10+=r<=10
        auc.append((sum(pos>v for v in neg)+.5*sum(pos==v for v in neg))/len(neg))
    n=len(cases)
    return {"cases":n,"mrr":sum(rr)/n,"hits_at_1":hit1/n,"hits_at_5":hit5/n,"hits_at_10":hit10/n,"pairwise_auc":sum(auc)/n}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source-repo",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--negatives",type=int,default=99); ap.add_argument("--max-cases",type=int,default=5000); a=ap.parse_args()
    mods=modules(a.source_repo); all_edges=imports(mods); held={e for e in all_edges if hold(*e)}; train=all_edges-held
    outn=defaultdict(set); inn=defaultdict(set)
    for s,t in train: outn[s].add(t); inn[t].add(s)
    indeg=Counter(t for _,t in train); names=sorted(mods); sorted_deg=sorted(indeg.values())
    def bucket(x):
        d=indeg[x]
        if not sorted_deg:return 0
        return sum(d>sorted_deg[(len(sorted_deg)*q)//4] for q in (1,2,3))
    by=defaultdict(list)
    for x in names: by[(x.split(".")[0],bucket(x))].append(x)
    selected=sorted(held,key=lambda e:h("order",*e))[:a.max_cases]; cases=[]
    for s,t in selected:
        pool=[x for x in by[(t.split(".")[0],bucket(t))] if x!=s and x!=t and (s,x) not in all_edges]
        if len(pool)<a.negatives: pool=[x for x in names if x!=s and x!=t and (s,x) not in all_edges and bucket(x)==bucket(t)]
        if len(pool)<a.negatives: continue
        rng=random.Random(h("neg",s,t)); neg=rng.sample(pool,a.negatives)
        ps,pl=features(s,t,outn,inn); positive={"structural":ps,"lexical":pl,"combined":ps+pl}; negatives=[]
        for x in neg:
            ss,ll=features(s,x,outn,inn); negatives.append({"structural":ss,"lexical":ll,"combined":ss+ll})
        cases.append({"positive":positive,"negatives":negatives})
    result={"experiment":"MAPEOGEO_OPENAI_MATH_WITHHELD_RELATION_REDISCOVERY_V1","status":"PASS" if cases else "FAIL","seed":SEED,
      "source":{"modules":len(mods),"resolved_internal_import_edges":len(all_edges),"training_edges":len(train),"heldout_edges":len(held),"evaluated_cases":len(cases),"negative_candidates_per_case":a.negatives},
      "holdout":{"rule":"sha256(seed|source|target) mod 5 == 0","fraction_target":0.20,"leakage_controls":["held-out edge removed before feature construction","structural score uses only remaining import topology","lexical score uses module identifiers only","candidate negatives exclude all true source-target import edges","negative targets matched on indegree quartile and top namespace when sufficient"]},
      "results":{k:eval_method(cases,k) for k in ("structural","lexical","combined")},
      "semantic_edge_improvement_test":{"status":"STRUCTURAL_NULL_BY_CONSTRUCTION","reason":"The imported openai/math source layer has no reconciliation edges to pre-existing canonical MAPEOGEO objects. Removing or adding this disconnected source component cannot change topology-only scores between pre-existing semantic endpoints.","delta_expected":0.0,"interpretation":"The intake strengthens evidence density and creates a rediscovery substrate, but cannot yet improve canonical semantic-edge recovery until a separately validated bridge/reconciliation layer is added."},
      "claim_boundary":{"supports":["withheld internal source-relationship recovery if structural metrics beat chance","measurement of lexical versus topology contribution","identification of the missing canonical reconciliation layer"],"does_not_support":["mathematical theorem equivalence","proof validity","canonical semantic improvement from the intake alone"]}}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True)); return 0 if cases else 1
if __name__=="__main__": raise SystemExit(main())
