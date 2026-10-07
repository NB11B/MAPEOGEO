from __future__ import annotations
import hashlib,json,re,subprocess
from pathlib import Path
from typing import Any
from mapeogeo.openai_math_source import scan_source

SRC_COMMIT="adc7f1241b42e322a6451854ab7e4b4c146bf78a"
GRAPH_SHA="abe9c19bcce1281f7b285bfe11f7051d5dc38fb9ca3072a32a4b44def72f43b9"
BASELINE_COMMIT="2e5ef8d12aace9b519d96f3d8214161cd87b0d7e"
BASELINE_RUN=37591827279

EXACT_312={
 "CONTENTS.md","lean/formalization.yaml","lean/docs/312.md",
 "lean/ComparatorChallenges/GrothendieckElementaryExpansion.lean",
 "lean/ComparatorChallenges/GrothendieckElementaryExpansion.json",
}
PREFIX_312=(
 "lean/OAI/CategoryTheory/Globular/",
 "preprints/The-Grothendieck-homotopy-hypothesis-via-elementary-expansions-September-24-2026/",
)
STOP=set("the a an of and or for to in on with is are be by from as this that these those let have has using where when then iff if all every some there exists type prop nat true false self mk app obj hom def theorem lemma instance structure class abbrev noncomputable namespace".split())
SEEDS={
 "T":set("map morphism homomorphism functor transform projection projector inclusion embedding quotient dual pullback pushout restriction extension compose composition equivalence isomorphism homeomorphism conjugate localization completion deformation attach attachment transport representation correspondence adjoint inverse image preimage lift descent".split()),
 "W":set("witness certificate universal adjunction bijection isomorphism exact commute commutative factorization basis determinant rank condition pushout pullback cellular coherator proof kernel diagram homotopy fibration cofibration naturality canonical unique existence".split()),
 "I":set("invariant preserve preserved conserved equivalence isomorphism homeomorphism homotopy measure norm metric topology rank determinant trace degree orientation cardinality dimension component components group homology cohomology spectrum index characteristic weak stable stability fixed identity".split()),
 "Delta":set("add addition attach attachment extend extension expansion remove removal quotient modify modification deform deformation perturb perturbation preserve preservation change refine refinement complete completion localize localization collapse split merge replace subdivide resolve lift fill filler adjoin cell".split()),
}

def cjson(x:Any)->bytes:
 return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def shafile(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()
def git(repo:Path,*args:str)->str:
 return subprocess.check_output(["git","-C",str(repo),*args],text=True).strip()
def toks(s:str)->list[str]:
 s=re.sub(r"([a-z0-9])([A-Z])",r"\1 \2",str(s).replace("_"," ").replace("-"," "))
 return [x.lower() for x in re.findall(r"[A-Za-z][A-Za-z0-9]*",s) if x.lower() not in STOP and len(x)>1]
def srcpath(node_id:str)->str|None:
 if not str(node_id).startswith("oam:file:"): return None
 return str(node_id)[9:].split(":record:",1)[0]
def direct312(path:str|None)->bool:
 return bool(path) and (path in EXACT_312 or any(path.startswith(p) for p in PREFIX_312))
def parse_results(repo:Path)->list[dict[str,str]]:
 text=(repo/"lean/formalization.yaml").read_text(encoding="utf-8")
 pat=re.compile(r"-\s+comparator_config:\s*(\S+)\s+declaration:\s*(\S+)\s+file:\s*(\S+)",re.M)
 return [{"config":"lean/"+a,"declaration":b,"file":"lean/"+c} for a,b,c in pat.findall(text)]
def choose_other_holdout(results:list[dict[str,str]],n:int=24)->list[dict[str,str]]:
 rows=[]
 for r in results:
  joined=" ".join(r.values()).lower()
  if "grothendieck" in joined or "/globular/" in joined: continue
  key=hashlib.sha256((r["declaration"]+"|"+r["file"]).encode()).hexdigest()
  rows.append((key,r))
 return [r for _,r in sorted(rows)[:n]]
def excluded(path:str|None,other:set[str])->bool:
 return direct312(path) or (path in other if path else False)
def admit(freq:dict[str,int],seeds:set[str],minimum:int=5)->list[str]:
 vals=[]
 for token,count in freq.items():
  if count<minimum: continue
  if token in seeds or any(token.startswith(s) or s.startswith(token) for s in seeds if len(s)>=5):
   vals.append((token,count))
 return [t for t,_ in sorted(vals,key=lambda x:(-x[1],x[0]))]
def signature(text:str,grammar:dict)->dict[str,list[str]]:
 ts=set(toks(text)); out={}
 for k in ("T","W","I","Delta"):
  out[k]=sorted(ts & set(grammar["coordinates"][k]["alphabet"]))
 if ts & {"equivalence","equivalent","isomorphism","homeomorphism","homotopy","weak"}: sigma="EQUIVALENT_TO"
 elif ts & {"overlap","local","restriction","partial","scope","scoped"}: sigma="SCOPED_OVERLAP"
 else: sigma="CANDIDATE_REPRESENTS"
 if sigma not in grammar["coordinates"]["sigma"]["alphabet"]: sigma=grammar["coordinates"]["sigma"]["alphabet"][0]
 out["sigma"]=[sigma]; return out
def jac(a:list[str],b:list[str])->float:
 x,y=set(a),set(b)
 return len(x&y)/max(1,len(x|y)) if x or y else 0.0
def similarity(a:dict,b:dict)->tuple[float,int]:
 w={"T":.25,"W":.20,"I":.15,"sigma":.15,"Delta":.25}
 score=sum(w[k]*jac(a[k],b[k]) for k in w)
 non_i=sum(jac(a[k],b[k])>0 for k in ("T","W","sigma","Delta"))
 return score,non_i
def classified_equivalent(a:dict,b:dict)->bool:
 score,non_i=similarity(a,b)
 return score>=.72 and non_i>=3
def decl_text(repo:Path,path:str,declaration:str)->str|None:
 fp=repo/path
 if not fp.exists(): return None
 data=fp.read_bytes(); scan=scan_source(path,data); wanted=declaration.split(".")[-1]
 for rec in scan["records"]:
  q=rec.get("qualified_name",rec.get("name",""))
  if q==declaration or q.endswith("."+wanted) or rec.get("name")==wanted:
   return data[rec["start_byte"]:rec["end_byte"]].decode("utf-8","replace")
 return None
