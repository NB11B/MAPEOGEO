"""BBB17 Collatz research tracks: bounded recurrence, geometry, affine parity words.
Standard-library only. No finite scan is a proof of global Collatz.
"""
from dataclasses import dataclass
from typing import Optional

def accelerated(n: int) -> int:
    if n <= 0: raise ValueError("positive integers only")
    return n // 2 if n % 2 == 0 else (3*n + 1)//2

def register_step(u: int) -> int:
    if u < 0: raise ValueError("natural registers only")
    return u//2 if u % 2 else 3*(u//2)+1

@dataclass(frozen=True)
class Phase:
    j: int
    u: int
    v: int
    beeps: int = 0

def phase(s: Phase) -> Phase:
    j,u,v=s.j,s.u,s.v
    if min(j,u,v)<0: raise ValueError("negative canonical coordinate")
    if u==0: return Phase(j+1,j+1,max(0,v-(j+1)),j+1)
    if u%2: return Phase(j,u//2,v+(u+1)//2)
    k=u//2
    return Phase(j,3*k+1,max(0,v-k-1))

def orbit(start: int, cap: int=10000):
    """Return termination/cycle/limit diagnostics, never a universal result."""
    if start<1: raise ValueError("start must be positive")
    seen={}
    n=start
    for t in range(cap+1):
        if n==1: return {"kind":"reached_one","steps":t}
        if n in seen: return {"kind":"cycle","steps":t,"period":t-seen[n]}
        if t==cap: return {"kind":"limit","steps":t}
        seen[n]=t
        n=accelerated(n)
    raise AssertionError

def affine_word(bits: tuple[int,...]):
    """For accelerated Collatz: n -> (3^a*n + b)/2^r, on valid parity cells."""
    A,B,D=1,0,1
    for b in bits:
        if b not in (0,1): raise ValueError("parity symbols must be 0/1")
        if b: A,B=3*A,3*B+D
        D*=2
    return A,B,D

def actual_word(n: int,bits: tuple[int,...]) -> Optional[int]:
    if n < 1: raise ValueError("positive integers only")
    for b in bits:
        if n%2 != b: return None
        n=accelerated(n)
    return n

def run_campaign(max_start=10000, cap=10000, depth=8):
    kinds={}
    for n in range(1,max_start+1):
        k=orbit(n,cap)["kind"]; kinds[k]=kinds.get(k,0)+1
    words=0; matched=0
    for r in range(depth+1):
        for word in range(1<<r):
            bits=tuple((word>>i)&1 for i in range(r))
            A,B,D=affine_word(bits)
            for n in range(1,min(max_start,128)+1):
                out=actual_word(n,bits)
                if out is not None:
                    words+=1
                    assert D*out==A*n+B,(bits,n,A,B,D,out)
                    matched+=1
    # Geometry: S=u+v is unchanged on even-integer phases, nondecreasing on odd-integer phases.
    checked=0; growth=0
    for u in range(1,128):
        for v in range(128):
            s=Phase(0,u,v); t=phase(s)
            assert t.beeps==0 and t.j==0
            assert t.u+ t.v >= s.u+s.v
            if u%2: assert t.u+t.v==s.u+s.v
            if t.u+t.v > s.u+s.v: growth+=1
            checked+=1
    return {"starts":max_start,"orbit_results":kinds,
            "affine_valid_cases":matched,"geometry_cases":checked,
            "strict_S_growth_cases":growth,"universal_claim":False}

if __name__=="__main__":
    import argparse,json
    p=argparse.ArgumentParser()
    p.add_argument("--starts",type=int,default=10000)
    p.add_argument("--cap",type=int,default=10000)
    p.add_argument("--depth",type=int,default=8)
    a=p.parse_args()
    print(json.dumps(run_campaign(a.starts,a.cap,a.depth),indent=2))
