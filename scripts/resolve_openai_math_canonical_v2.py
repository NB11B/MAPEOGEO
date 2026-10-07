#!/usr/bin/env python3
"""Resolve all remaining OpenAI/math canonical reconciliation cases.

Uses declaration header tokens, source/module context, and canonical concept
signatures. Produces a total disposition for every canonical object. It never
asserts SAME_SEMANTICS or kernel verification.
"""
from __future__ import annotations
import argparse,json,re,subprocess
from pathlib import Path
from collections import defaultdict,Counter
WORD=re.compile(r"[A-Za-z][A-Za-z0-9]*")
DECL=re.compile(r"(?m)^\s*(?:@\[[^\n]*\]\s*)*(?:private\s+|protected\s+|noncomputable\s+|unsafe\s+|partial\s+|nonrec\s+|local\s+)*(?P<kind>theorem|lemma|def|abbrev|structure|inductive|class|axiom)\s+(?P<name>[^\s(:={}\[\],;|]+)(?P<header>[^\n]*(?:\n(?!\s*(?:theorem|lemma|def|abbrev|structure|inductive|class|axiom)\s)[^\n]*){0,8})")
STOP={"the","a","an","of","and","or","for","to","in","on","with","is","are","be","by","from","as","any","all","its","into","iff","if","then","where","let","have","show","this","that","true","false"}
GENERIC={"theorem","formula","procedure","operator","space","spaces","vector","linear","map","maps","set","function","property","existence"}
def toks(s): return {x.lower() for x in WORD.findall(s) if x.lower() not in STOP and len(x)>1}
def concept(obj):
    name={x for x in toks(obj["name"]) if x not in GENERIC}
    desc=toks(obj.get("description",""))
    return name, name|desc
def score(obj,name,module,header):
    core,full=concept(obj); nt=toks(name.replace("_"," ")); mt=toks(module.replace("."," ")); ht=toks(header)
    exact=1.0 if core and core<=nt|ht else 0.0
    header_overlap=len(full&ht)/max(1,len(full))
    name_overlap=len(full&nt)/max(1,len(full))
    module_overlap=len(full&mt)/max(1,len(full))
    return 4*exact+2*header_overlap+name_overlap+.5*module_overlap, exact, sorted(full&ht)
def main():
    p=argparse.ArgumentParser();p.add_argument("--source-repo",type=Path,required=True);p.add_argument("--registry",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--topk",type=int,default=8);a=p.parse_args()
    objs=json.loads(a.registry.read_text())["canonical_objects"]; index=defaultdict(set); sig={}
    for o in objs:
        c,f=concept(o);sig[o["id"]]=(c,f)
        for x in f:index[x].add(o["id"])
    by={o["id"]:o for o in objs}; best=defaultdict(list); scanned=0
    for path in (a.source_repo/"lean").rglob("*.lean"):
        module=path.relative_to(a.source_repo/"lean").as_posix()[:-5].replace("/",".")
        try:text=path.read_text(encoding="utf-8")
        except UnicodeDecodeError:continue
        for m in DECL.finditer(text):
            scanned+=1; name=m.group("name"); header=m.group("header")[:4000]
            terms=toks(name.replace("_"," ")+" "+module.replace("."," ")+" "+header)
            ids=set()
            for x in terms:ids.update(index.get(x,()))
            for cid in ids:
                s,ex,ov=score(by[cid],name,module,header)
                if s<0.35:continue
                row={"module":module,"name":name,"kind":m.group("kind"),"score":round(s,6),"exact_core":bool(ex),"header_overlap":ov}
                best[cid].append(row)
    dispositions=[]; counts=Counter()
    for o in objs:
        rows=sorted(best[o["id"]],key=lambda x:(-x["score"],x["module"],x["name"]))[:a.topk]
        if not rows:
            status="REJECTED_NO_EVIDENCE";relation=None;reason="No declaration reached the preregistered multi-field evidence floor."
        else:
            top=rows[0]; second=rows[1]["score"] if len(rows)>1 else 0; margin=top["score"]-second
            # Strong exact concept in header/name with separation: representation.
            if top["exact_core"] and top["score"]>=4.8 and margin>=0.35:
                status="RESOLVED";relation="REPRESENTS";reason="Exact canonical concept signature plus header/context evidence with separated top candidate."
            # Strong but nonunique evidence: related, not same.
            elif top["score"]>=2.0:
                status="RESOLVED";relation="RELATED_TO";reason="Substantial statement/context overlap, insufficient for identity; relation conservatively bounded to RELATED_TO."
            else:
                status="REJECTED_INSUFFICIENT_EVIDENCE";relation=None;reason="Candidate evidence remained below conservative relation threshold."
        counts[relation or status]+=1
        dispositions.append({"canonical_id":o["id"],"canonical_name":o["name"],"status":status,"relation":relation,"reason":reason,"top_candidates":rows})
    receipt={"experiment":"OPENAI_MATH_CANONICAL_TOTAL_RECONCILIATION_V2","source_revision":subprocess.check_output(["git","-C",str(a.source_repo),"rev-parse","HEAD"],text=True).strip(),
      "canonical_objects":len(objs),"lean_declarations_scanned":scanned,"counts":dict(counts),"dispositions":dispositions,
      "total_disposition_complete":len(dispositions)==len(objs),
      "claim_boundary":{"REPRESENTS":"concept represented by source declaration under exact concept/header evidence","RELATED_TO":"mathematically related by bounded lexical/type-context evidence; not same semantics","REJECTED":"no graph relation asserted","never_asserted":["SAME_SEMANTICS","KERNEL_VERIFIED","proof equivalence"]}}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"canonical_objects":len(objs),"declarations":scanned,"counts":dict(counts),"complete":receipt["total_disposition_complete"]},indent=2))
if __name__=="__main__":main()
