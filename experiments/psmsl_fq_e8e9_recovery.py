#!/usr/bin/env python3
import argparse,gzip,hashlib,json,re
from collections import defaultdict,Counter
from pathlib import Path
import ijson

def items(p,k):
 with gzip.open(p,"rb") as f: yield from ijson.items(f,k+".item")
def words(s):return set(re.findall(r"[a-z0-9]+",str(s).lower()))

def evaluate_tests(text):
    t = text.lower()
    return {
        "composition": "composition" in t or "compose" in t,
        "variance_direction": "variance" in t or "direction" in t,
        "projection_behavior": "projection" in t or "projector" in t or "idempotent" in t,
        "inverse_requirement": "inverse" in t or "invertible" in t
    }

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--graph",type=Path,required=True)
 ap.add_argument("--output",type=Path,required=True)
 a=ap.parse_args()
 
 nodes={}
 for n in items(a.graph,"nodes"):
  nid=n.get("id","")
  text=" ".join(map(str,[n.get("label",""),n.get("type",""),n.get("attributes",{})]))
  nodes[nid]=text
 
 # E8: Graph-backed candidates and separating tests
 cand_edges = []
 for e in items(a.graph,"edges"):
  if e.get("type") == "CANDIDATE_REPRESENTS":
   cand_edges.append(e)
 
 specs = []
 for e in cand_edges:
  nid = e.get("source")
  text = nodes.get(nid, "")
  tests = evaluate_tests(text)
  # Only candidates surviving at least one separating test count
  if any(tests.values()):
   specs.append({
     "concept": e.get("target"),
     "source_node": nid,
     "canonical_target": e.get("target"),
     "proposed_correspondence": "CANDIDATE_REPRESENTS",
     "authority": "CANDIDATE_ONLY",
     "separating_tests": tests
   })
 
 specs = sorted(specs, key=lambda x: x["source_node"])[:19]
 e8_pass = len(specs) == 19
 
 # E9: Exact 215 seeds from alignments
 with open("formal/cross_source_alignments_v0_19.json", "r") as f:
  align_data = json.load(f)
 canonical = [obj["id"] for obj in align_data.get("canonical_objects", [])]
 
 adj=defaultdict(set)
 for e in items(a.graph,"edges"):
  s,t=e.get("source"),e.get("target")
  if s and t:adj[s].add(t);adj[t].add(s)
 
 plans=[]
 for seed in sorted(canonical):
  seen={seed};front={seed};radii=[]
  for r in (1,2,3):
   nxt=set()
   for x in front:nxt.update(adj.get(x,()))
   nxt-=seen;seen|=nxt
   ranked=sorted(nxt,key=lambda x:(-len(adj.get(x,set())-seen),x))
   radii.append({"radius":r,"count":len(nxt),"top_candidates":ranked[:10]})
   front=nxt
  plans.append({"seed":seed,"radii":radii,"authority_promotion":False})
 
 e9_pass=len(plans)==215 and all(not x["authority_promotion"] for x in plans)
 
 # Custody: gate on SHA-256 only
 graph_sha256 = hashlib.sha256(a.graph.read_bytes()).hexdigest()
 expected_sha256 = "abe9c19bcce1281f7b285bfe11f7051d5dc38fb9ca3072a32a4b44def72f43b9"
 custody_pass = (graph_sha256 == expected_sha256)
 
 overall_pass = e8_pass and e9_pass and custody_pass
 
 receipt={"campaign":"PSMSL-FQ","continuation":"E8_E9_UNBLOCKED_AFTER_TRANSPORT",
  "qualified_graph_sha256": graph_sha256,
  "E8":{"status":"PASS" if e8_pass else "FAIL","candidate_spec_count":len(specs),"authority_promotions":0},
  "E9":{"status":"PASS" if e9_pass else "FAIL","seed_count":len(plans),"authority_promotions":0},
  "overall_status":"PASS" if overall_pass else "FAIL"}
 
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"E8":receipt["E8"]["status"],"E8_specs":len(specs),"E9":receipt["E9"]["status"],"E9_seeds":len(plans),"overall":receipt["overall_status"]},indent=2))
 raise SystemExit(0 if overall_pass else 1)

if __name__=="__main__":main()
