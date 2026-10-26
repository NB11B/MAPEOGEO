"""Fail-closed proof bridge for GEO-EULER-004 recurrence candidates.

Only a typed, allowlisted structural AST may be compiled. Output is a concrete
Lean definition of the selected recurrences and an explicit proof object.
Finite training success alone never certifies an arbitrary implementation.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

TOKEN=re.compile(r"^opaque-[A-Za-z0-9_-]+$")
def parse_selection(result):
    if result.get("status")!="qualified":
        raise ValueError("discovery did not qualify")
    a=result.get("addition");m=result.get("multiplication")
    if not isinstance(a,str) or not isinstance(m,str):
        raise ValueError("missing rules")
    ap=a.split("|");mp=m.split("|")
    if len(ap)!=2 or len(mp)!=2 or not TOKEN.fullmatch(ap[0]) or not TOKEN.fullmatch(mp[0]) or ap[0]==mp[0]:
        raise ValueError("malformed/ambiguous roles")
    # Reject bad grammar rather than silently substitute a known-good one.
    if ap[1]!="shift=1" or mp[1]!="add-left":
        raise ValueError("unsupported or non-arithmetic grammar")
    errors=result.get("holdout_errors")
    checks=result.get("holdout_checks")
    if not isinstance(errors,dict) or not isinstance(checks,dict):
        raise ValueError("missing holdout evidence")
    if any(type(errors.get(k)) is not int or errors[k]!=0 or type(checks.get(k)) is not int or checks[k]<=0 for k in (ap[0],mp[0])):
        raise ValueError("holdout qualification failed")
    return {"addition_source":ap[0],"multiplication_source":mp[0],
            "add_ast":{"zero":"first","step":"successor"},
            "mul_ast":{"zero":"zero","step":"add(previous,first)"},
            "holdout_checks":{k:checks[k] for k in (ap[0],mp[0])}}

def render(selection):
    # The definitions below are emitted only after exact AST validation.
    ast=selection["add_ast"],selection["mul_ast"]
    if ast!=({"zero":"first","step":"successor"},{"zero":"zero","step":"add(previous,first)"}):
        raise ValueError("AST not supported")
    return """import MAPEOGEOFormal.GeoEulerCertificate

namespace MAPEOGEOFormal.GeoEuler.Discovered

def selectedAdd (a : Nat) : Nat → Nat
  | 0 => a
  | b + 1 => Nat.succ (selectedAdd a b)

def selectedMul (a : Nat) : Nat → Nat
  | 0 => 0
  | b + 1 => selectedAdd (selectedMul a b) a

theorem selectedCertificate :
    RecurrenceCertificate selectedAdd selectedMul := by
  constructor
  · intro a; rfl
  · intro a b; rfl
  · intro a; rfl
  · intro a b; rfl

theorem selectedAdd_eq (a b : Nat) : selectedAdd a b = a + b :=
  certified_add_eq selectedAdd selectedMul selectedCertificate a b

theorem selectedMul_eq (a b : Nat) : selectedMul a b = a * b :=
  certified_mul_eq selectedAdd selectedMul selectedCertificate a b

end MAPEOGEOFormal.GeoEuler.Discovered

#print axioms MAPEOGEOFormal.GeoEuler.Discovered.selectedAdd_eq
#print axioms MAPEOGEOFormal.GeoEuler.Discovered.selectedMul_eq
"""

def emit(result, out_path):
    selection=parse_selection(result)
    body=render(selection)
    path=Path(out_path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(body,encoding="utf-8")
    return {"selection":selection,"sha256":hashlib.sha256(body.encode()).hexdigest(),"file":str(path)}

def main():
    # Import the actual discovery implementation, and do not synthesize results.
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"geo_euler_004"))
    from grammar import run
    result=run()
    output=emit(result,Path(__file__).resolve().parents[2]/"MAPEOGEOFormal"/"GeoEulerSelected.lean")
    print(json.dumps(output,indent=2,sort_keys=True))

if __name__=="__main__":main()
