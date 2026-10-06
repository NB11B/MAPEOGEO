"""Independently validate a canonical-augmentation generator on small linear spaces."""
from __future__ import annotations
from itertools import combinations
from .erdos19_exact_canonical_v8 import exact_canonical_digest


def pairset(line):
    return frozenset(frozenset(p) for p in combinations(sorted(line),2))


def admissible_add(parent,line):
    used=set()
    for e in parent:used.update(pairset(e))
    return not (used & set(pairset(line)))


def complete_pair_cover(n,lines):
    used=set()
    for e in lines:
        ps=pairset(e)
        if used & set(ps):return False
        used.update(ps)
    return len(used)==n*(n-1)//2


def candidate_lines(n,min_size=2):
    return tuple(frozenset(s) for r in range(min_size,n+1) for s in combinations(range(n),r))


def canonical_generation(n,max_states=200000):
    """Generate one representative per partial isomorphism class at every depth."""
    cand=candidate_lines(n)
    frontier=[()]
    seen={exact_canonical_digest(n,(),max_states=max_states)[0]}
    leaves={}
    while frontier:
        parent=frontier.pop()
        if complete_pair_cover(n,parent):
            d,_=exact_canonical_digest(n,parent,max_states=max_states)
            leaves[d]=parent
            continue
        for line in cand:
            if not admissible_add(parent,line):continue
            child=parent+(line,)
            d,_=exact_canonical_digest(n,child,max_states=max_states)
            if d in seen:continue
            seen.add(d);frontier.append(child)
    return leaves


def brute_force_exact_covers(n,max_states=200000):
    """Independent exact-cover recursion, quotient only after complete labeled covers."""
    pairs=tuple(frozenset(p) for p in combinations(range(n),2))
    cand=candidate_lines(n)
    lp={e:pairset(e) for e in cand}
    covers=[]

    def rec(uncovered,chosen,start_key=()):
        if not uncovered:
            covers.append(tuple(chosen));return
        p=min(uncovered,key=lambda x:tuple(sorted(x)))
        for e in cand:
            if p not in lp[e]:continue
            if not set(lp[e])<=set(uncovered):continue
            rec(frozenset(set(uncovered)-set(lp[e])),chosen+[e])
    rec(frozenset(pairs),[])
    reps={}
    for c in covers:
        d,_=exact_canonical_digest(n,c,max_states=max_states)
        reps[d]=c
    return reps,len(covers)
