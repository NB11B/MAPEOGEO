"""Emit selected interaction coefficient into a Lean theorem from measured pairs."""
from pathlib import Path
import hashlib,json
from experiment import observed_coefficient
ROOT=Path(__file__).resolve().parents[2]
def emit(coefficient=None):
    c=observed_coefficient() if coefficient is None else coefficient
    if type(c) is not int or not 0<=c<=100:raise ValueError("invalid coefficient")
    # Keep c unchanged: a wrong selection must make the theorem fail.
    text=f"""import Mathlib

namespace MAPEOGEOFormal.GeoEuler

def discoveredInteraction (a b : Nat) : Nat :=
  ((a+b)^2 - a^2 - b^2) / {c}

theorem discoveredInteraction_eq_mul (a b : Nat) :
    discoveredInteraction a b = a*b := by
  have h : a^2 + b^2 + 2*(a*b) = (a+b)^2 := by ring
  unfold discoveredInteraction
  omega

end MAPEOGEOFormal.GeoEuler
#print axioms MAPEOGEOFormal.GeoEuler.discoveredInteraction_eq_mul
"""
    path=ROOT/"MAPEOGEOFormal"/"GeoPrimeInferred.lean"
    path.write_text(text,encoding="utf-8")
    return {"coefficient":c,"sha256":hashlib.sha256(text.encode()).hexdigest(),"source":str(path)}
if __name__=="__main__":print(json.dumps(emit(),indent=2))
