"""Generate Lean identities from actually discovered interaction coefficients."""
from pathlib import Path
from discover import discover
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def emit():
    results=[discover(2),discover(3)]
    lines=["import Mathlib","namespace MAPEOGEOFormal.GeoOPR"]
    for result in results:
        d=result["degree"];coeff=result["coefficients"]
        if len(coeff)!=d-1 or any(type(c) is not int for c in coeff):
            raise ValueError("invalid coefficient shape")
        interaction=" + ".join(f"{c}*a^{d-j}*b^{j}" for j,c in enumerate(coeff,start=1))
        name={2:"square",3:"cube"}[d]
        lines.append(f"theorem inferred_{name} (a b : Nat) :")
        lines.append(f"    (a+b)^{d} = a^{d} + b^{d} + {interaction} := by ring")
    lines.extend(["end MAPEOGEOFormal.GeoOPR",
                  "#print axioms MAPEOGEOFormal.GeoOPR.inferred_square",
                  "#print axioms MAPEOGEOFormal.GeoOPR.inferred_cube",""])
    code="\n".join(lines)
    target=ROOT/"MAPEOGEOFormal"/"GeoOPRInferred.lean"
    target.write_text(code,encoding="utf-8")
    return {"coefficients":results,"sha256":hashlib.sha256(code.encode()).hexdigest()}
if __name__=="__main__":print(json.dumps(emit(),indent=2))
