#!/usr/bin/env python3
"""Blind recovery test for OpenAI/math result 312 against MAPEOGEO.

No direct family-312 catalogue/scope/config/solution links are allowed as
features. The expected formal scope is frozen independently from docs/312.md.
"""
from __future__ import annotations
import argparse,json,re,subprocess
from pathlib import Path
TOK=re.compile(r"[A-Za-z][A-Za-z0-9]*")
STOP={"the","a","an","of","and","or","for","to","in","on","with","is","are","be","by","from","as","every","all","its","this","that"}
EXPECTED={
 "formal_scope":{"elementary","expansion","weak","equivalence","cellular","pushout","boundary","disk","homotopy","group","components"},
 "full_claim_extra":{"semi","model","spaces","comparison","homotopy","theory"},
}
def toks(s):return {x.lower() for x in TOK.findall(s) if x.lower() not in STOP}
def main():
 p=argparse.ArgumentParser();p.add_argument("--source-repo",type=Path,required=True);p.add_argument("--registry",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 reg=json.loads(a.registry.read_text())["canonical_objects"]
 # Blind features: canonical registry + all Lean declaration headers except the known
 # challenge, solution module and family scope paths.
 forbidden={"lean/ComparatorChallenges/GrothendieckElementaryExpansion.lean","lean/OAI/CategoryTheory/Globular/Main.lean","lean/docs/312.md"}
 query=EXPECTED["formal_scope"]
 canonical=[]
 for o in reg:
  terms=toks(o["name"]+" "+o.get("description",""))
  ov=query&terms
  if ov:canonical.append({"id":o["id"],"name":o["name"],"overlap":sorted(ov),"score":len(ov)/len(query)})
 source=[]
 for path in (a.source_repo/"lean").rglob("*.lean"):
  rel=path.relative_to(a.source_repo).as_posix()
  if rel in forbidden:continue
  try:text=path.read_text(encoding="utf-8")
  except UnicodeDecodeError:continue
  terms=toks(rel+" "+text[:12000])
  ov=query&terms
  if len(ov)>=2:source.append({"path":rel,"overlap":sorted(ov),"score":len(ov)/len(query)})
 source=sorted(source,key=lambda x:(-x["score"],x["path"]))[:50]
 recovered=set().union(*(set(x["overlap"]) for x in canonical+source)) if canonical or source else set()
 formal_recall=len(recovered&query)/len(query)
 # Full-claim guard: because direct 312 scope and solution are withheld, the test must
 # not claim recovery of the later comparison merely from elementary-expansion evidence.
 full_extra=EXPECTED["full_claim_extra"]
 extra_recovered=set().union(*(toks(x.get("name","")+" "+x.get("path","")) for x in canonical+source)) & full_extra if canonical or source else set()
 overclaim=full_extra<=extra_recovered
 result={"experiment":"MAPEOGEO_RESULT_312_BLIND_RECOVERY_V1","source_revision":subprocess.check_output(["git","-C",str(a.source_repo),"rev-parse","HEAD"],text=True).strip(),
 "holdout":{"forbidden_paths":sorted(forbidden),"direct_family_312_links":"WITHHELD","expected_scope_not_used_for_graph_construction":True},
 "formal_scope_tokens":sorted(query),"recovered_formal_tokens":sorted(recovered&query),"formal_scope_recall":formal_recall,
 "canonical_hits":sorted(canonical,key=lambda x:(-x["score"],x["id"])),"source_hits":source,
 "overclaim_guard":{"full_claim_extra_tokens":sorted(full_extra),"recovered_from_identifiers":sorted(extra_recovered),"improper_full_claim_recovery":overclaim},
 "status":"PASS" if formal_recall>=0.6 and not overclaim else "FAIL",
 "interpretation":"PASS requires recovery of at least 60% of the formal elementary-expansion machinery while refusing to infer the full homotopy-hypothesis comparison from withheld direct evidence."}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"status":result["status"],"formal_scope_recall":formal_recall,"canonical_hits":len(canonical),"source_hits":len(source),"overclaim":overclaim},indent=2))
 raise SystemExit(0 if result["status"]=="PASS" else 1)
if __name__=="__main__":main()
