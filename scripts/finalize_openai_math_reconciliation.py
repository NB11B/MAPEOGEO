#!/usr/bin/env python3
"""Finalize OpenAI/math canonical reconciliation without semantic overclaiming.

Consumes the complete integrated graph and emits a reconciliation receipt.
CANDIDATE_REPRESENTS edges are evidence-bearing retrieval bridges. This pass
classifies canonical coverage and only promotes a candidate to REPRESENTS when
it has an exact canonical-name token signature in the Lean declaration name.
All other candidates remain candidates; objects without an exact promotion are
explicit unresolved deficits in the receipt.
"""
from __future__ import annotations
import argparse,gzip,json,re,hashlib
from collections import Counter,defaultdict
from pathlib import Path
import ijson

GENERIC={"theorem","formula","procedure","operator","space","spaces","vector","linear","of","for","and","internal","fundamental","have","a","an","the"}
def tokens(s): return {x.lower() for x in re.findall(r"[A-Za-z]+",s)}
def core(name):
    t={x for x in tokens(name) if x not in GENERIC}
    return t or {x for x in tokens(name) if x not in {"of","for","and","a","an","the"}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--graph",type=Path,required=True);p.add_argument("--registry",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    reg=json.loads(a.registry.read_text())["canonical_objects"]; by={x["id"]:x for x in reg}; cand=defaultdict(list); source_names={}
    with gzip.open(a.graph,"rb") as f:
        for n in ijson.items(f,"nodes.item"):
            if n.get("type")=="SOURCE_RECORD": source_names[n["id"]]=n.get("label","")
    with gzip.open(a.graph,"rb") as f:
        for e in ijson.items(f,"edges.item"):
            if e.get("type")=="CANDIDATE_REPRESENTS": cand[e["target"]].append(e["source"])
    accepted=[]; unresolved=[]; ambiguous=[]
    for cid,obj in sorted(by.items()):
        c=core(obj["name"]); exact=[]
        for sid in cand.get(cid,[]):
            dt=tokens(source_names.get(sid,"").replace("_"," "))
            if c and c<=dt: exact.append(sid)
        if len(exact)==1:
            accepted.append({"canonical_id":cid,"canonical_name":obj["name"],"source_record":exact[0],
                "relation":"REPRESENTS","evidence_status":"EXACT_CANONICAL_NAME_SIGNATURE",
                "semantic_equivalence_status":"NOT_CLAIMED","kernel_verification_status":"UNTESTED"})
        elif len(exact)>1:
            ambiguous.append({"canonical_id":cid,"canonical_name":obj["name"],"exact_candidates":len(exact),
                "status":"UNRESOLVED_AMBIGUITY"})
        else:
            unresolved.append({"canonical_id":cid,"canonical_name":obj["name"],"candidate_count":len(cand.get(cid,[])),
                "status":"UNRESOLVED_DEFICIT","requires":"STATEMENT_TYPE_SCOPE_REVIEW"})
    receipt={"experiment":"OPENAI_MATH_CANONICAL_RECONCILIATION_FINAL_V1",
      "policy":"Exact canonical-name signature may establish REPRESENTS only; never SAME_SEMANTICS or proof validity.",
      "canonical_objects":len(reg),"objects_with_candidate_edges":sum(bool(cand.get(x["id"])) for x in reg),
      "accepted_represents":len(accepted),"ambiguous":len(ambiguous),"unresolved":len(unresolved),
      "accepted":accepted,"ambiguous_objects":ambiguous,"unresolved_objects":unresolved,
      "completion_status":"PASS" if len(accepted)+len(ambiguous)+len(unresolved)==len(reg) else "FAIL",
      "claim_boundary":{"represents_means":"source declaration name exactly carries the canonical concept signature","does_not_mean":["same theorem statement","same semantics","proof verified","kernel verified"]}}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:receipt[k] for k in ("completion_status","canonical_objects","objects_with_candidate_edges","accepted_represents","ambiguous","unresolved")},indent=2))
    raise SystemExit(0 if receipt["completion_status"]=="PASS" else 1)
if __name__=="__main__":main()
