"""Extract research-open theorem signatures from Lean source text."""
from __future__ import annotations
import re
from .proof_shape import classify_signature


def research_open_signatures(source:str):
    out=[]
    marker="@[category research open"
    pos=0
    while True:
        i=source.find(marker,pos)
        if i<0: break
        t=source.find("theorem ",i)
        if t<0: break
        by=source.find(":= by",t)
        if by<0:
            by=source.find(" := by",t)
        if by<0: break
        sig=source[t:by]
        name=(re.match(r"theorem\s+([^\s:]+)",sig) or [None,"UNKNOWN"])[1]
        out.append((name,sig,classify_signature(sig)))
        pos=by+4
    return tuple(out)
