"""Incidence-graph refinement and bounded canonical augmentation for linear spaces."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json


@dataclass(frozen=True)
class RefinementSignature:
    digest:str
    ambiguous:bool
    point_colors:tuple[int,...]
    line_colors:tuple[int,...]


def incidence_refinement(n,lines):
    lines=tuple(frozenset(e) for e in lines)
    # Initial colors preserve bipartition and line size.
    pc=[0]*n
    sizes=sorted(set(map(len,lines)))
    size_color={s:i+1 for i,s in enumerate(sizes)}
    lc=[size_color[len(e)] for e in lines]
    changed=True
    while changed:
        pkeys=[]
        for v in range(n):
            neigh=sorted(lc[i] for i,e in enumerate(lines) if v in e)
            pkeys.append(("P",pc[v],tuple(neigh)))
        lkeys=[]
        for i,e in enumerate(lines):
            neigh=sorted(pc[v] for v in e)
            lkeys.append(("L",lc[i],tuple(neigh)))
        allkeys=sorted(set(pkeys+lkeys),key=repr)
        cmap={k:i for i,k in enumerate(allkeys)}
        npc=[cmap[k] for k in pkeys];nlc=[cmap[k] for k in lkeys]
        changed=(npc!=pc or nlc!=lc);pc,lc=npc,nlc
    # Invariant quotient summary; not a full canonical label when cells remain.
    summary={
      "point_cells":sorted(sorted(pc).count(c) for c in set(pc)),
      "line_cells":sorted(sorted(lc).count(c) for c in set(lc)),
      "line_sizes":sorted(map(len,lines)),
      "incidence_profiles":sorted((pc[v],tuple(sorted(lc[i] for i,e in enumerate(lines) if v in e))) for v in range(n)),
    }
    digest=hashlib.sha256(json.dumps(summary,separators=(",",":"),sort_keys=True).encode()).hexdigest()
    ambiguous=(len(set(pc))<n) or (len(set(lc))<len(lines))
    return RefinementSignature(digest,ambiguous,tuple(pc),tuple(lc))


def augmentation_key(n,parent,child):
    ps=incidence_refinement(n,parent);cs=incidence_refinement(n,child)
    return hashlib.sha256((ps.digest+"->"+cs.digest).encode()).hexdigest()


def canonical_augmentation_status(n,parent,child):
    c=incidence_refinement(n,child)
    return "NEEDS_CANONICAL_BACKEND" if c.ambiguous else "REFINEMENT_UNIQUE"
