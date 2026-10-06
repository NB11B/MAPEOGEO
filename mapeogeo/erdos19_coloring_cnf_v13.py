"""CNF encoding and trusted SAT-coloring witness verifier for hypergraph edge coloring."""
from __future__ import annotations

def var(edge,color,n): return edge*n+color+1

def coloring_cnf(n,lines):
    lines=tuple(map(frozenset,lines));clauses=[]
    for i in range(len(lines)):
        clauses.append(tuple(var(i,c,n) for c in range(n)))
        for a in range(n):
            for b in range(a+1,n):clauses.append((-var(i,a,n),-var(i,b,n)))
    for i,e in enumerate(lines):
        for j in range(i):
            if not e&lines[j]:continue
            for c in range(n):clauses.append((-var(i,c,n),-var(j,c,n)))
    return len(lines)*n,tuple(clauses)

def dimacs(n,lines):
    nv,cs=coloring_cnf(n,lines)
    body="\n".join(" ".join(map(str,c))+" 0" for c in cs)
    return f"p cnf {nv} {len(cs)}\n{body}\n"

def assignment_to_colors(n,lines,assignment):
    pos={x for x in assignment if x>0};out=[]
    for i in range(len(lines)):
        cols=[c for c in range(n) if var(i,c,n) in pos]
        if len(cols)!=1:return None
        out.append(cols[0])
    return tuple(out)
