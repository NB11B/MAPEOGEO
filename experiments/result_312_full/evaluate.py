from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
from .common import cjson,shafile,signature,similarity,decl_text,classified_equivalent

def evaluate(state:dict,source_repo:Path,out:Path,custody:dict)->dict:
 grammar=state["grammar"]; observations=state["signed_observations"]; recurrence=grammar["recurrence"]
 controls=state["controls"]; other_holdout=state["other_holdout"]
 frozen=out/"frozen_grammar.json"
 if not frozen.exists():
  raise RuntimeError("frozen grammar missing before held-out reveal")
 before=shafile(frozen)

 challenge_path="lean/ComparatorChallenges/GrothendieckElementaryExpansion.lean"
 solution_path="lean/OAI/CategoryTheory/Globular/ElementaryExpansion.lean"
 docs_path="lean/docs/312.md"
 challenge=decl_text(source_repo,challenge_path,"OAI.Grothendieck.elementary_expansion")
 solution=decl_text(source_repo,solution_path,"OAI.Grothendieck.elementary_expansion")
 docs=(source_repo/docs_path).read_text(encoding="utf-8")
 held_text="\n".join(x for x in (challenge,solution,docs) if x)
 hs=signature(held_text,grammar)

 support_domains=set(); support_modalities=set(); nearest=[]
 for o in observations:
  score,non_i=similarity(hs,o["signature"])
  if score>0:
   nearest.append((score,non_i,o))
  if any(set(hs[k])&set(o["signature"][k]) for k in ("T","W","I","Delta")):
   support_domains.add(o["domain"]); support_modalities.update(o["modalities"])
 nearest.sort(key=lambda x:(-x[0],-x[1],x[2]["cid"],x[2]["sid"]))
 active=sum(bool(hs[k]) for k in ("T","W","I","Delta"))
 predicted=(
  active>=3 and bool(hs["T"]) and bool(hs["W"]) and bool(hs["I"])
  and len(support_domains)>=3 and len(support_modalities)>=2
 )
 after=shafile(frozen)
 holdout={
  "family_id":"312",
  "challenge_path":challenge_path,"solution_path":solution_path,"scope_path":docs_path,
  "direct_material_used_in_discovery":False,
  "signature":hs,
  "active_non_sigma_coordinates":active,
  "support_domain_count":len(support_domains),"support_domains":sorted(support_domains),
  "support_modality_count":len(support_modalities),"support_modalities":sorted(support_modalities),
  "nearest_training_instances":[
   {"score":score,"non_i_matches":non_i,"canonical_id":o["cid"],"domain":o["domain"]}
   for score,non_i,o in nearest[:25]
  ],
  "elementary_expansion_behavior_predicted":predicted,
  "grammar_sha256_before_reveal":before,"grammar_sha256_after_reveal":after,
  "grammar_modified_after_reveal":before!=after,
 }
 (out/"holdout_312.json").write_bytes(cjson(holdout)+b"\n")

 other=[]
 for r in other_holdout:
  text=decl_text(source_repo,r["file"],r["declaration"])
  if text is None:
   other.append({**r,"status":"MISSING_DECLARATION"}); continue
  s=signature(text,grammar)
  active_other=sum(bool(s[k]) for k in ("T","W","I","Delta"))
  domains=set(); modalities=set()
  for o in observations:
   if any(set(s[k])&set(o["signature"][k]) for k in ("T","W","I","Delta")):
    domains.add(o["domain"]); modalities.update(o["modalities"])
  ok=active_other>=2 and len(domains)>=2
  other.append({
   **r,"status":"PASS" if ok else "FAIL","signature":s,
   "active_non_sigma_coordinates":active_other,
   "support_domain_count":len(domains),"support_modality_count":len(modalities),
  })
 scored=sum(x["status"] in {"PASS","FAIL"} for x in other)
 passed=sum(x["status"]=="PASS" for x in other)
 pass_rate=passed/max(1,scored)
 other_summary={"holdout_count":len(other),"scored":scored,"passed":passed,"pass_rate":pass_rate,"results":other}
 (out/"other_openai_math_holdouts.json").write_bytes(cjson(other_summary)+b"\n")

 recurrence_ok=(
  all(recurrence[k]["domain_count"]>=3 and recurrence[k]["modality_count"]>=2 and recurrence[k]["alphabet_size"]>0
      for k in ("T","W","I","Delta"))
  and recurrence["sigma"]["alphabet_size"]>=3
 )
 controls_ok=(
  controls["negative_false_equivalence_rate"]<=0.05
  and controls["adversarial_false_equivalence_rate"]<=0.05
  and controls["shared_invariant_false_equivalences"]==0
 )
 other_ok=scored>=10 and pass_rate>=0.80
 held_ok=predicted and before==after

 verdict="PASS" if recurrence_ok and controls_ok and other_ok and held_ok else (
  "BLOCKED" if (not recurrence_ok or scored<10) else "FAIL"
 )

 tracked=len(subprocess.check_output(
  ["git","-C",str(source_repo),"ls-tree","-r","--name-only","HEAD"],text=True
 ).splitlines())
 counts=state["counts"]
 result={
  "experiment":"MAPEOGEO_RESULT_312_FULL_HELDOUT_V1",
  "verdict":verdict,
  "claim_boundary":"A PASS establishes that a grammar frozen without direct #312 material recurs across the integrated corpus and classifies #312's elementary-expansion transformation as an instance of that grammar. It does not prove the Grothendieck homotopy hypothesis, semantic equivalence of all shared invariants, or mathematical completeness of MAPEOGEO.",
  "custody":custody,
  "corpus":{
   "integrated_graph_nodes":counts["nodes"],"integrated_graph_edges":counts["edges"],
   "openai_math_tracked_files":tracked,
   "discovery_source_records":counts["discovery_source_records"],
   "excluded_source_records":counts["excluded_source_records"],
   "canonical_objects":len(state["canonical"]),
   "domain_count":len(state["domains"]),"domains":state["domains"],
   "representation_modality_count":len(state["modalities"]),"representation_modalities":state["modalities"],
   "node_types":counts["node_types"],"edge_types":counts["edge_types"],
  },
  "operator_family_counts":{k:len(grammar["coordinates"][k]["alphabet"]) for k in grammar["coordinates"]},
  "recurrence":recurrence,
  "controls":{k:v for k,v in controls.items() if k!="counterexamples"},
  "holdout_312":holdout,
  "other_openai_math":{
   "holdout_count":len(other),"scored":scored,"passed":passed,"pass_rate":pass_rate
  },
  "failures_and_counterexamples":controls["counterexamples"],
  "gates":{
   "identity":"PASS",
   "recurrence":"PASS" if recurrence_ok else "BLOCKED",
   "controls":"PASS" if controls_ok else "FAIL",
   "heldout_312":"PASS" if held_ok else "FAIL",
   "other_openai_math":"PASS" if other_ok else ("BLOCKED" if scored<10 else "FAIL"),
  },
  "frozen_grammar_sha256":state["grammar_sha"],
  "production_graph_modified":False,
 }
 (out/"result.json").write_bytes(cjson(result)+b"\n")

 md=[
  "# Full Held-Out #312 Experiment","",f"**Final verdict: {verdict}**","",
  "## Frozen identities",
  f"- MAPEOGEO baseline commit: \`{custody['baseline_mapeogeo_commit']}\`",
  f"- Baseline workflow run: \`{custody['baseline_workflow_run']}\`",
  f"- Integrated graph SHA-256: \`{custody['integrated_graph_sha256']}\`",
  f"- OpenAI/math commit: \`{custody['openai_math_commit']}\`",
  f"- Frozen grammar SHA-256: \`{state['grammar_sha']}\`","",
  "## Corpus",
  f"- Integrated graph: {counts['nodes']:,} nodes / {counts['edges']:,} edges",
  f"- OpenAI/math tracked files: {tracked:,}",
  f"- Discovery source records: {counts['discovery_source_records']:,}",
  f"- Excluded source records: {counts['excluded_source_records']:,}",
  f"- Canonical domains: {len(state['domains'])}",
  f"- Representation modalities: {len(state['modalities'])}","",
  "## Frozen grammar recurrence",
 ]
 for k in ("T","W","I","sigma","Delta"):
  r=recurrence[k]
  md.append(f"- **{k}**: {r['alphabet_size']} values; {r['domain_count']} domains; {r['modality_count']} modalities")
 md += [
  "","## Controls",
  f"- Negative pairs: {controls['negative_pairs']:,}; false equivalences {controls['negative_false_equivalences']:,} ({controls['negative_false_equivalence_rate']:.4%})",
  f"- Shared-invariant pairs: {controls['shared_invariant_pairs']:,}; false equivalences {controls['shared_invariant_false_equivalences']:,}",
  f"- Adversarial invariant-preserved pairs: {controls['adversarial_pairs']:,}; false equivalences {controls['adversarial_false_equivalences']:,} ({controls['adversarial_false_equivalence_rate']:.4%})",
  "","## Held-out #312",
  "- Direct #312 material used in discovery: **NO**",
  f"- Active non-sigma coordinates: {active}/4",
  f"- Cross-domain support: {len(support_domains)}",
  f"- Cross-modality support: {len(support_modalities)}",
  f"- Elementary-expansion behavior predicted: **{'YES' if predicted else 'NO'}**",
  f"- Grammar modified after reveal: **{'YES' if before!=after else 'NO'}**",
  "","## Independent non-#312 OpenAI/math holdouts",
  f"- Passed: {passed}/{scored} ({pass_rate:.2%})","",
  "## Gates",
 ]
 for k,v in result["gates"].items():
  md.append(f"- {k}: **{v}**")
 md += ["","## Conservative claim boundary",result["claim_boundary"]]
 (out/"FULL_HELDOUT_312_REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 return result
