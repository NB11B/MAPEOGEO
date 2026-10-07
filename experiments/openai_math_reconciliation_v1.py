#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from collections import defaultdict
WORD=re.compile(r"[A-Za-z][A-Za-z0-9]*")
STOP={"the","a","an","of","and","or","for","to","in","on","with","is","are","be","by","from","as","any","all","its","into"}
DECL=re.compile(r"(?m)^\s*(?:@\[[^\n]*\]\s*)*(?:private\s+|protected\s+|noncomputable\s+|unsafe\s+|partial\s+|nonrec\s+|local\s+)*(?P<kind>theorem|lemma|def|abbrev|structure|inductive|class|axiom)\s+(?P<name>[^\s(:={}\[\],;|]+)")
def toks(s): return {x.lower() for x in WORD.findall(s) if x.lower() not in STOP and len(x)>1}
def build_index(objs):
    signatures={}; inverted=defaultdict(set); by_id={}
    for o in objs:
        by_id[o["id"]]=o
        q=toks(o["name"]+" "+o.get("description","")+" "+o["id"].replace(":"," "))
        signatures[o["id"]]=q
        for token in q: inverted[token].add(o["id"])
    return signatures,inverted,by_id
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source-repo",type=Path,required=True);ap.add_argument("--alignments",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);ap.add_argument("--topk",type=int,default=25);a=ap.parse_args()
    objs=json.loads(a.alignments.read_text())["canonical_objects"]; candidates=defaultdict(list); total=0
    signatures,inverted,by_id=build_index(objs)
    assert signatures and inverted and by_id
    for p in (a.source_repo/"lean").rglob("*.lean"):
        module=p.relative_to(a.source_repo/"lean").as_posix()[:-5].replace("/",".")
        try:text=p.read_text(encoding="utf-8")
        except UnicodeDecodeError:continue
        line=1; last=0
        for m in DECL.finditer(text):
            line += text.count("\n",last,m.start()); last=m.start()
            total+=1; name=m.group("name")
            nt=toks(name.replace("_"," ")+" "+module.replace("."," "))
            object_ids=set()
            for token in nt: object_ids.update(inverted.get(token,()))
            for oid in object_ids:
                o=by_id[oid]; q=signatures[oid]; inter=q&nt
                name_tokens=toks(o["name"])
                s=(len(inter)/max(1,len(q)))+(len(inter)/max(1,len(nt)))+(1.0 if name_tokens and name_tokens<=nt else 0.0)
                candidates[oid].append({"source_module":module,"declaration_kind":m.group("kind"),"declaration_name":name,"start_line":line,"score":round(s,8),
                  "evidence":{"lexical_overlap":sorted(inter),"formal_target_hint":bool(o.get("formal_decl"))},"status":"CANDIDATE_REPRESENTS","verification_status":"UNTESTED"})
    out=[]
    for o in objs:
        rows=sorted(candidates[o["id"]],key=lambda x:(-x["score"],x["source_module"],x["declaration_name"]))[:a.topk]
        out.append({"canonical_id":o["id"],"canonical_name":o["name"],"domain":o["domain"],"formal_decl":o.get("formal_decl"),"candidate_count_total":len(candidates[o["id"]]),"top_candidates":rows})
    result={"experiment":"OPENAI_MATH_CANONICAL_RECONCILIATION_CANDIDATES_V1","status":"CANDIDATES_ONLY","source_revision":"adc7f1241b42e322a6451854ab7e4b4c146bf78a","canonical_objects":len(objs),"lean_declarations_scanned":total,"promotion_policy":"NONE; candidates require independent statement/scope review before any canonical edge","objects":out}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"objects":len(objs),"declarations":total,"objects_with_candidates":sum(bool(x["top_candidates"]) for x in out)},indent=2))
if __name__=="__main__":main()
