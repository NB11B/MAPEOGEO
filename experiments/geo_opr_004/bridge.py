"""Emit the actual selected AST into Lean; never replace it with a reference AST."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"geo_opr_003"))
from grammar import discover
ROOT=Path(__file__).resolve().parents[2]
OPS={"x","y","one","succ","add","mul"}
def validate(e):
    if e.op not in OPS:raise ValueError("unrecognized AST operation")
    expected=0 if e.op in ("x","y","one") else 1 if e.op=="succ" else 2
    if len(e.args)!=expected:raise ValueError("bad AST arity")
    for a in e.args:validate(a)
def lean_expr(e):
    validate(e)
    if e.op=="x":return "a"
    if e.op=="y":return "b"
    if e.op=="one":return "1"
    if e.op=="succ":return "(Nat.succ "+lean_expr(e.args[0])+")"
    symbol="+" if e.op=="add" else "*"
    return "("+lean_expr(e.args[0])+" "+symbol+" "+lean_expr(e.args[1])+")"
def selected():
    train=[(a,b,a*b+a) for a in (1,2,3) for b in (1,2,3)]
    matches=discover(train)
    if not matches:raise ValueError("no candidate")
    hold=[(a,b,a*b+a) for a in range(4,11) for b in range(4,11)]
    passed=[e for e in matches if all(e.eval(a,b)==c for a,b,c in hold)]
    if not passed:raise ValueError("holdout mismatch")
    # Freeze a deterministic candidate, not the reference formula.
    return passed[0]
def emit(e,out):
    expr=lean_expr(e)
    source=f"""import Mathlib

namespace MAPEOGEOFormal.GeoOPR

def selected (a b : Nat) : Nat := {expr}

theorem selected_spec (a b : Nat) : selected a b = a + a*b := by
  simp only [selected]
  try ring

end MAPEOGEOFormal.GeoOPR
#print axioms MAPEOGEOFormal.GeoOPR.selected_spec
"""
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(source,encoding="utf-8")
    return {"ast":e.render(),"sha256":hashlib.sha256(source.encode()).hexdigest(),"lean":str(p)}
if __name__=="__main__":
    e=selected()
    print(json.dumps(emit(e,ROOT/"MAPEOGEOFormal"/"GeoOPRSelected.lean"),indent=2))
