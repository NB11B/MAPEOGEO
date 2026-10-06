"""Conservative top-level proof-shape classifier for Lean theorem signatures."""
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ProofShape:
    shape: str
    features: tuple[str,...]


def classify_signature(signature:str)->ProofShape:
    s=" ".join(signature.split())
    f=[]
    if "answer(sorry) ↔" in s: f.append("ANSWER_EQUIV")
    if "∀ᶠ" in s or " atTop" in s: f.append("EVENTUALLY")
    if "=O[" in s or "=o[" in s or "IsBigO" in s or "IsLittleO" in s: f.append("ASYMPTOTIC")
    if "∀" in s: f.append("FORALL")
    if "∃" in s: f.append("EXISTS")
    # order only when explicit unicode quantifiers occur in the signature
    q=[(m.start(),m.group()) for m in re.finditer(r"[∀∃]",s)]
    if q:
        order="".join("A" if x[1]=="∀" else "E" for x in q)
        f.append("QORDER_"+order[:8])
    if "↔" in s: f.append("IFF")
    if "→" in s: f.append("IMPLIES")
    if "sInf" in s or "iInf" in s: f.append("INFIMUM")
    if "sSup" in s or "iSup" in s: f.append("SUPREMUM")
    if "ncard" in s or ".card" in s: f.append("CARDINAL")
    if not f: return ProofShape("ATOMIC_OR_PARAMETERIZED",())
    if "ASYMPTOTIC" in f: shape="ASYMPTOTIC"
    elif "EVENTUALLY" in f: shape="EVENTUAL"
    elif "FORALL" in f and "EXISTS" in f: shape="MIXED_QUANTIFIER"
    elif "FORALL" in f: shape="UNIVERSAL"
    elif "EXISTS" in f: shape="EXISTENTIAL"
    elif "IFF" in f: shape="EQUIVALENCE"
    else: shape="COMPOSITE"
    return ProofShape(shape,tuple(f))
