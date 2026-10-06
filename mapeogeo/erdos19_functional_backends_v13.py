"""Functional production adapters for pynauty canonical labeling and CaDiCaL SAT."""
from __future__ import annotations
import hashlib,subprocess,tempfile
from pathlib import Path
from .erdos19_backend_contracts_v12 import CanonicalResult,ColoringResult
from .erdos19_coloring_cnf_v13 import dimacs,assignment_to_colors
from .erdos19_frontier13_v5 import verify_edge_coloring

class PynautyCanonicalAdapter:
    def canonicalize(self,n,lines):
        try:
            import pynauty
        except ImportError:
            return CanonicalResult("","pynauty",None,False)
        lines=tuple(map(frozenset,lines));N=n+len(lines)
        adj={i:[] for i in range(N)}
        for j,e in enumerate(lines):
            lv=n+j
            for v in e:adj[v].append(lv);adj[lv].append(v)
        size_groups={}
        for j,e in enumerate(lines):size_groups.setdefault(len(e),set()).add(n+j)
        coloring=[set(range(n))]+[size_groups[k] for k in sorted(size_groups)]
        g=pynauty.Graph(number_of_vertices=N,directed=False,adjacency_dict=adj,vertex_coloring=coloring)
        try:
            cert=bytes(pynauty.certificate(g))
            lab=tuple(pynauty.canon_label(g))
        except Exception:
            return CanonicalResult("","pynauty",None,False)
        ok=bool(cert) and sorted(lab)==list(range(N))
        if not ok:return CanonicalResult("","pynauty",None,False)
        digest=hashlib.sha256(cert).hexdigest()
        return CanonicalResult(digest,"pynauty",repr(lab),True)

class CadicalColoringAdapter:
    def solve(self,n,lines):
        with tempfile.TemporaryDirectory() as td:
            cnf=Path(td)/"color.cnf";cnf.write_text(dimacs(n,lines))
            try:p=subprocess.run(["cadical",str(cnf)],capture_output=True,text=True,timeout=3600)
            except (FileNotFoundError,subprocess.TimeoutExpired):
                return ColoringResult("ERROR",None,"cadical",None,False)
            out=p.stdout.splitlines()
            if any(x.startswith("s SATISFIABLE") for x in out):
                assignment=[]
                for x in out:
                    if x.startswith("v "):assignment.extend(int(v) for v in x[2:].split() if v!="0")
                colors=assignment_to_colors(n,lines,assignment)
                ok=colors is not None and verify_edge_coloring(n,lines,colors)
                return ColoringResult("SAT",colors,"cadical",None,ok)
            if any(x.startswith("s UNSATISFIABLE") for x in out):
                # CaDiCaL result alone is deliberately not authoritative UNSAT.
                return ColoringResult("UNSAT",None,"cadical",None,False)
            return ColoringResult("ERROR",None,"cadical",None,False)

def functional_readiness():
    c=PynautyCanonicalAdapter().canonicalize(3,({0,1},{0,2},{1,2}))
    s=CadicalColoringAdapter().solve(3,({0,1},{0,2},{1,2}))
    missing=[]
    if not c.verified:missing.append("FUNCTIONAL_CANONICAL_BACKEND")
    if not s.verified:missing.append("FUNCTIONAL_SAT_BACKEND")
    return tuple(missing)
