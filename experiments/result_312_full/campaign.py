from __future__ import annotations
import argparse,json
from pathlib import Path
from .common import *
from .derive import derive
from .evaluate import evaluate

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--graph",type=Path,required=True)
 p.add_argument("--source-repo",type=Path,required=True)
 p.add_argument("--registry",type=Path,required=True)
 p.add_argument("--output-dir",type=Path,required=True)
 a=p.parse_args()
 out=a.output_dir
 out.mkdir(parents=True,exist_ok=True)
 source_commit=git(a.source_repo,"rev-parse","HEAD")
 graph_sha=shafile(a.graph)
 custody={
  "baseline_mapeogeo_commit":BASELINE_COMMIT,
  "baseline_workflow_run":BASELINE_RUN,
  "integrated_graph_sha256":graph_sha,
  "openai_math_commit":source_commit,
  "registry_sha256":shafile(a.registry),
  "production_graph_modified":False,
 }
 custody["identity_status"]="PASS" if graph_sha==GRAPH_SHA and source_commit==SRC_COMMIT else "FAIL"
 (out/"custody.json").write_bytes(cjson(custody)+b"\n")
 if custody["identity_status"]!="PASS":
  result={"verdict":"BLOCKED","reason":"BASELINE_IDENTITY_MISMATCH","custody":custody}
  (out/"result.json").write_bytes(cjson(result)+b"\n")
  print(json.dumps(result,indent=2))
  return 2
 state=derive(a.graph,a.source_repo,a.registry,out)
 result=evaluate(state,a.source_repo,out,custody)
 print(json.dumps({"verdict":result["verdict"],"corpus":result["corpus"],"operator_family_counts":result["operator_family_counts"],"controls":result["controls"],"heldout_312":result["holdout_312"],"other_openai_math":result["other_openai_math"],"gates":result["gates"],"frozen_grammar_sha256":result["frozen_grammar_sha256"]},indent=2))
 return 0 if result["verdict"]=="PASS" else 2 if result["verdict"]=="BLOCKED" else 1

if __name__=="__main__":
 raise SystemExit(main())
