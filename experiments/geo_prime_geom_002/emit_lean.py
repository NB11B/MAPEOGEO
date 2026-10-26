"""Translate actual affine recurrence coefficients to Pell coordinates and Lean."""
from fractions import Fraction
from pathlib import Path
from infer import discover
def source(coeff):
    (a,b,k),(d,e,f)=coeff
    vals=(a,2*b,2*k+1-a,Fraction(d,2),e,f-Fraction(d,2))
    if any(v.denominator!=1 for v in vals):raise ValueError("nonintegral coordinate map")
    A,B,K,D,E,F=map(int,vals)
    if K or F:raise ValueError("nonzero Pell offsets")
    return f"""import Mathlib
namespace MAPEOGEOFormal.GeoPrimePellInferred
theorem inferred_norm (x c : ℤ) :
    ({A}*x+{B}*c)^2 - 2*({D}*x+{E}*c)^2 = x^2 - 2*c^2 := by
  ring
end MAPEOGEOFormal.GeoPrimePellInferred
#print axioms MAPEOGEOFormal.GeoPrimePellInferred.inferred_norm
"""
def emit(path,mutation=False):
    coeff,_=discover()
    if mutation:coeff=((coeff[0][0],coeff[0][1]+1,coeff[0][2]),coeff[1])
    p=Path(path);p.write_text(source(coeff),encoding="utf-8");return p
if __name__=="__main__":
    print(emit(Path(__file__).resolve().parents[2]/"MAPEOGEOFormal"/"GeoPrimePellInferred.lean"))
