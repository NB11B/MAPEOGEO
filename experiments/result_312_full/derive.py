from __future__ import annotations
from collections import Counter
import gzip,hashlib,json
from pathlib import Path
import ijson
from .common import *

def edge_items(graph:Path):
 with gzip.open(graph,"rb") as f:
  yield from ijson.items(f,"edges.item")
def node_items(graph:Path):
 with gzip.open(graph,"rb") as f:
  yield from ijson.items(f,"nodes.item")

def derive(graph:Path,source_repo:Path,registry:Path,out:Path)->dict:
 reg=json.loads(registry.read_text(encoding="utf-8"))
 canonical={o["id"]:o for o in reg["canonical_objects"]}
 domains=sorted({o.get("domain","UNKNOWN") for o in canonical.values()})
 modalities=sorted({m for o in canonical.values() for m in o.get("representation_kinds",[])})
 other_holdout=choose_other_holdout(parse_results(source_repo),24)
 other_paths={r["file"] for r in other_holdout}|{r["config"] for r in other_holdout}

 candidate_edges=[]; edge_types=Counter(); total_edges=0; excluded_candidate_edges=0
 for e in edge_items(graph):
  total_edges+=1; edge_types[e.get("type","UNKNOWN")]+=1
  if e.get("type")!="CANDIDATE_REPRESENTS": continue
  path=srcpath(e.get("source",""))
  if excluded(path,other_paths):
   excluded_candidate_edges+=1; continue
  if e.get("target") in canonical:
   candidate_edges.append((e["source"],e["target"]))
 candidate_ids={s for s,_ in candidate_edges}

 labels={}; node_types=Counter(); total_nodes=0; discovery_records=0; excluded_records=0
 for n in node_items(graph):
  total_nodes+=1; typ=n.get("type","UNKNOWN"); node_types[typ]+=1
  if typ!="SOURCE_RECORD": continue
  path=srcpath(n.get("id",""))
  if excluded(path,other_paths):
   excluded_records+=1; continue
  discovery_records+=1
  if n.get("id") in candidate_ids:
   labels[n["id"]]=str(n.get("label",""))

 coord={k:Counter() for k in ("T","W","I","Delta")}; sigma_counts=Counter(); observations=[]
 for sid,cid in candidate_edges:
  if sid not in labels: continue
  obj=canonical[cid]
  text=" ".join([labels[sid],obj.get("name",""),obj.get("description","")])
  tt=toks(text)
  for k,seeds in SEEDS.items():
   for t in tt:
    if t in seeds or any(t.startswith(s) or s.startswith(t) for s in seeds if len(s)>=5):
     coord[k][t]+=1
  for al in obj.get("alignments",[]):
   status=al.get("status","")
   if status=="CROSS_SOURCE_SAME": sigma_counts["SAME_SEMANTICS"]+=1
   elif "SCOPED_OVERLAP" in status: sigma_counts["SCOPED_OVERLAP"]+=1
   else: sigma_counts["RELATED_TO"]+=1
  observations.append({"sid":sid,"cid":cid,"domain":obj.get("domain","UNKNOWN"),"modalities":obj.get("representation_kinds",[]),"text":text})
 sigma_counts["CANDIDATE_REPRESENTS"]+=len(observations)
 sigma=[x for x in ("SAME_SEMANTICS","EQUIVALENT_TO","SCOPED_OVERLAP","RELATED_TO","CANDIDATE_REPRESENTS") if x=="EQUIVALENT_TO" or sigma_counts[x]>0]
 grammar={
  "schema":"MAPEOGEO_DOMAIN_NEUTRAL_TRANSFORMATION_GRAMMAR_V1",
  "derived_without_family_312":True,
  "coordinates":{
   "T":{"meaning":"representation/transformation change","alphabet":admit(coord["T"],SEEDS["T"])},
   "W":{"meaning":"witness/certificate","alphabet":admit(coord["W"],SEEDS["W"])},
   "I":{"meaning":"preserved structure/invariant","alphabet":admit(coord["I"],SEEDS["I"])},
   "sigma":{"meaning":"scope/identification strength","alphabet":sigma},
   "Delta":{"meaning":"changed structure/change mode","alphabet":admit(coord["Delta"],SEEDS["Delta"])},
  },
  "discovery":{
   "canonical_objects":len(canonical),"domain_count":len(domains),"domains":domains,
   "modality_count":len(modalities),"modalities":modalities,
   "candidate_observations":len(observations),"source_records_scanned":discovery_records,
   "source_records_excluded":excluded_records,"candidate_edges_excluded":excluded_candidate_edges,
   "other_findings_holdout_count":len(other_holdout),"other_findings_holdout_files":sorted(other_paths),
   "direct_312_exact":sorted(EXACT_312),"direct_312_prefixes":list(PREFIX_312),
  },
 }
 cdom={k:set() for k in grammar["coordinates"]}; cmod={k:set() for k in grammar["coordinates"]}; signed=[]
 for o in observations:
  s=signature(o["text"],grammar); signed.append({**o,"signature":s})
  for k in ("T","W","I","Delta"):
   if s[k]:
    cdom[k].add(o["domain"]); cmod[k].update(o["modalities"])
  cdom["sigma"].add(o["domain"]); cmod["sigma"].update(o["modalities"])
 recurrence={k:{"domain_count":len(cdom[k]),"domains":sorted(cdom[k]),"modality_count":len(cmod[k]),"modalities":sorted(cmod[k]),"alphabet_size":len(grammar["coordinates"][k]["alphabet"])} for k in grammar["coordinates"]}
 grammar["recurrence"]=recurrence

 gb=cjson(grammar); grammar_sha=hashlib.sha256(gb).hexdigest()
 (out/"frozen_grammar.json").write_bytes(gb+b"\n")
 (out/"frozen_grammar.sha256").write_text(grammar_sha+"  frozen_grammar.json\n",encoding="utf-8")

 negatives=[]; adv_total=adv_false=shared_total=shared_false=0
 ordered=sorted(signed,key=lambda x:(x["cid"],x["sid"]))
 for i,o in enumerate(ordered[:min(5000,len(ordered))]):
  partner=None
  for off in range(1,min(200,len(ordered))):
   q=ordered[(i+37*off)%len(ordered)]
   if q["domain"]!=o["domain"] and q["cid"]!=o["cid"]:
    partner=q; break
  if partner is None: continue
  score,non_i=similarity(o["signature"],partner["signature"])
  accepted=classified_equivalent(o["signature"],partner["signature"])
  negatives.append({"a":o["cid"],"b":partner["cid"],"score":score,"non_i_matches":non_i,"accepted":accepted})
  adv={"T":partner["signature"]["T"],"W":partner["signature"]["W"],"I":o["signature"]["I"],"sigma":o["signature"]["sigma"],"Delta":partner["signature"]["Delta"]}
  adv_total+=1; adv_false+=classified_equivalent(o["signature"],adv)
  if set(o["signature"]["I"])&set(partner["signature"]["I"]):
   shared_total+=1; shared_false+=classified_equivalent(o["signature"],partner["signature"])
 neg_false=sum(x["accepted"] for x in negatives)
 controls={
  "negative_pairs":len(negatives),"negative_false_equivalences":neg_false,
  "negative_false_equivalence_rate":neg_false/max(1,len(negatives)),
  "shared_invariant_pairs":shared_total,"shared_invariant_false_equivalences":shared_false,
  "adversarial_pairs":adv_total,"adversarial_false_equivalences":adv_false,
  "adversarial_false_equivalence_rate":adv_false/max(1,adv_total),
  "threshold":{"equivalence_score":0.72,"minimum_non_invariant_coordinate_matches":3},
  "counterexamples":sorted([x for x in negatives if x["accepted"]],key=lambda x:-x["score"])[:20],
 }
 (out/"controls.json").write_bytes(cjson(controls)+b"\n")
 return {
  "canonical":canonical,"domains":domains,"modalities":modalities,"other_holdout":other_holdout,
  "signed_observations":signed,"grammar":grammar,"grammar_sha":grammar_sha,"controls":controls,
  "counts":{"nodes":total_nodes,"edges":total_edges,"node_types":dict(sorted(node_types.items())),"edge_types":dict(sorted(edge_types.items())),"discovery_source_records":discovery_records,"excluded_source_records":excluded_records},
 }
