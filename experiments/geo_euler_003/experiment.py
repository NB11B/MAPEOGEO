"""GEO-EULER-003: opaque successor-world reference used by GEO-EULER-004."""
import random
from dataclasses import dataclass

@dataclass
class World:
    successor: dict
    zero: int
    one: int
    tables: dict
    decode: dict

def world(size=31,seed=47,impostor=False):
    if size<8: raise ValueError("domain too small")
    rng=random.Random(seed)
    ids=list(range(1000,1000+size));rng.shuffle(ids)
    enc=dict(enumerate(ids))
    succ={enc[n]:enc[n+1] for n in range(size-1)}
    add={(enc[x],enc[y]):enc[x+y] for x in range(size) for y in range(size-x)}
    mult={(enc[x],enc[y]):enc[x*y] for x in range(size) for y in range(size) if x*y<size}
    if impostor:
        mult={(enc[x],enc[y]):enc[max(x,y)] for x in range(size) for y in range(size)}
    return World(succ,enc[0],enc[1],{"opaque-X":mult,"opaque-Y":add},{v:k for k,v in enc.items()})

def chain(successor,zero):
    path=[zero];seen={zero}
    while path[-1] in successor:
        nxt=successor[path[-1]]
        if nxt in seen: raise ValueError("cyclic successor")
        path.append(nxt);seen.add(nxt)
    return path
