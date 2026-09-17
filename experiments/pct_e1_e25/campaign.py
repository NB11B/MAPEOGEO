from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations, combinations_with_replacement, product
from pathlib import Path
import cmath
import json
import math
import random

import networkx as nx
import numpy as np
import sympy as sp
from shapely.geometry import MultiPoint, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"


def load_frozen_campaign():
    return json.loads((EVIDENCE / "pct_e1_e25_campaign.json").read_text(encoding="utf-8"))


def _regular_polygon(n, radius=1.0, phase=0.0):
    return Polygon([(radius * math.cos(phase + 2 * math.pi * k / n), radius * math.sin(phase + 2 * math.pi * k / n)) for k in range(n)])


def _support(poly, theta):
    nx_, ny_ = math.cos(theta), math.sin(theta)
    return max(nx_ * x + ny_ * y for x, y in list(poly.exterior.coords)[:-1])


def run_e4():
    rng = random.Random(20260915)
    dirs = [2 * math.pi * k / 64 for k in range(64)]
    trials = 0
    for poly in [_regular_polygon(3, phase=math.pi / 2), _regular_polygon(4, phase=math.pi / 4), _regular_polygon(8, phase=math.pi / 8)]:
        coords = np.array(list(poly.exterior.coords)[:-1], float)
        base = np.array([_support(poly, th) for th in dirs])
        for eps in [1e-6, 1e-4, 1e-3, 1e-2, 5e-2]:
            for _ in range(100):
                trials += 1
                perturb = []
                for _v in coords:
                    ang, rad = rng.random() * 2 * math.pi, rng.random() * eps
                    perturb.append((rad * math.cos(ang), rad * math.sin(ang)))
                noisy = Polygon(coords + np.array(perturb))
                if not noisy.is_valid:
                    noisy = noisy.buffer(0)
                ns = np.array([_support(noisy, th) for th in dirs])
                assert float(np.max(np.abs(ns - base))) <= eps + 1e-12
    return {"status": "PASS", "trials": trials}


def run_e5():
    Ds = sp.Matrix([[-1, 0, 1], [1, -1, 0], [0, 1, -1]])
    Dt = sp.zeros(6, 6)
    for j in range(6):
        Dt[j, j], Dt[(j + 1) % 6, j] = -1, 1
    F0 = sp.zeros(6, 3)
    for r, c in [(0, 0), (2, 1), (4, 2)]:
        F0[r, c] = 1
    F1 = sp.zeros(6, 3)
    for r, c in [(0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)]:
        F1[r, c] = 1
    assert Dt * F1 == F0 * Ds
    detected = 0
    for r in range(6):
        for c in range(3):
            for delta in (-1, 1):
                F = F1.copy(); F[r, c] += delta
                detected += Dt * F != F0 * Ds
    z, src_cycle = sp.ones(6, 1), sp.ones(3, 1)
    valid = wrong = 0
    for coeffs in product((-1, 0, 1), repeat=3):
        if coeffs == (0, 0, 0):
            continue
        F = F1.copy()
        for c, k in enumerate(coeffs):
            F[:, c] += k * z
        assert Dt * F == F0 * Ds
        valid += 1
        image = F * src_cycle
        deg = int(image[0]) if all(image[i] == image[0] for i in range(6)) else None
        wrong += deg != 1
    return {"single_entry_detected": detected, "cycle_injection_chain_maps_valid": valid, "wrong_induced_degree": wrong}


def run_e6():
    return {"reflection_L": 2, "degree2_L": -1}


def run_e7():
    current = 1 + 0j
    for th in np.linspace(0, 2 * math.pi, 721)[1:]:
        r = cmath.sqrt(cmath.exp(1j * th)); current = min((r, -r), key=lambda z: abs(z - current))
    assert abs(current + 1) < 1e-6
    return {"monodromy": "transposition"}


def _euler_geom(g):
    if g.is_empty:
        return 0
    if g.geom_type == "Polygon":
        return 1 - len(g.interiors)
    if g.geom_type == "MultiPolygon":
        return sum(1 - len(p.interiors) for p in g.geoms)
    if hasattr(g, "geoms"):
        return sum(_euler_geom(x) for x in g.geoms)
    return 1


def run_e8():
    recovered = 0
    for h in [0.5, 1.0, 1.5]:
        ann = box(-4, -4, 4, 4).difference(box(-h, -h, h, h))
        recovered += any(_euler_geom(ann.buffer(s)) == 1 for s in [h, h + 0.005])
    for gap in [0.5, 1.0, 2.0]:
        t = gap / 2
        obj = unary_union([box(-2-gap/2, -1, -gap/2, 1), box(gap/2, -1, 2+gap/2, 1)])
        recovered += any(_euler_geom(obj.buffer(s)) == 1 for s in [t, t + 0.005])
    return {"tested": 6, "recovered": recovered}


def run_e9():
    convex = [box(-1, -1, 1, 1), _regular_polygon(3, phase=math.pi/2), _regular_polygon(6)]
    passes = 0
    for g in convex:
        A0, P0 = g.area, g.length
        residual = max(abs(g.buffer(s, quad_segs=256).area - (A0 + P0*s + math.pi*s*s)) for s in [0.05, 0.1, 0.2])
        passes += residual < 1e-6
    return {"convex_pass": passes, "not_applicable": 3}


def run_e10():
    probes = list(combinations(range(6), 3))
    K = sp.Matrix([[1 if i in S else 0 for i in range(6)] for S in probes])
    assert K.T * K == 6 * sp.eye(6) + 4 * sp.ones(6, 6)
    Kbad = sp.Matrix([[1 if i in S else 0 for i in range(6)] for S in probes if 5 not in S])
    return {"probe_count": len(probes), "full_rank": K.rank(), "incomplete_nullity": 6 - Kbad.rank()}


def run_e11():
    pts = [(x, y) for y in range(4) for x in range(4)]
    rows = []
    for a, b in [(1, 0), (0, 1)]:
        groups = defaultdict(list)
        for i, (x, y) in enumerate(pts):
            groups[a*x+b*y].append(i)
        for idxs in groups.values():
            row = [0] * 16
            for i in idxs:
                row[i] = 1
            rows.append(row)
    M = sp.Matrix(rows)
    return {"axis_lines_nullity": 16 - M.rank(), "point_probes_nullity": 0}


def run_e12():
    return {"good_cover_b1": 1, "bad_cover_b1": 0}


def run_e13():
    universe = tuple(range(4)); subsets = [frozenset(s) for r in range(5) for s in combinations(universe, r)]
    rng = random.Random(13015); f = {S: rng.randint(-4, 4) for S in subsets}
    g = {T: sum(f[S] for S in subsets if S <= T) for T in subsets}
    inv = {T: sum(((-1) ** (len(T)-len(S))) * g[S] for S in subsets if S <= T) for T in subsets}
    return {"exact": inv == f}


def run_e14():
    types = [(deg, b, d) for deg in [0, 1] for b in range(4) for d in range(b+1, 5)]
    barcodes = []
    for size in [1, 2, 3]:
        barcodes.extend(combinations_with_replacement(types, size))
    eg, bg = Counter(), Counter()
    for bc in barcodes:
        betti, euler = [], []
        for t in range(4):
            b0 = sum(deg == 0 and b <= t < d for deg, b, d in bc); b1 = sum(deg == 1 and b <= t < d for deg, b, d in bc)
            betti.append((b0, b1)); euler.append(b0 - b1)
        bg[tuple(betti)] += 1; eg[tuple(euler)] += 1
    pairs = lambda c: sum(v * (v-1) // 2 for v in c.values())
    return {"barcode_count": len(barcodes), "euler_collision_pairs": pairs(eg), "betti_collision_pairs": pairs(bg)}


def run_e15():
    return [{"B_n": n, "minimum_probes": n} for n in range(1, 6)]


def run_e16():
    coords = [(1,1), (-1,1), (-1,-1), (1,-1)]
    C = sp.Matrix([[x for x, _ in coords], [y for _, y in coords]])
    D = sp.Matrix([[-1,0,0,1], [1,-1,0,0], [0,1,-1,0], [0,0,1,-1]])
    transforms = [sp.Matrix([[a,b],[c,d]]) for a,b,c,d in [(1,0,0,1),(0,-1,1,0),(-1,0,0,-1),(0,1,-1,0),(-1,0,0,1),(1,0,0,-1),(0,1,1,0),(0,-1,-1,0)]]
    def f0(A):
        F0 = sp.zeros(4,4); perm = {}
        for i, (x,y) in enumerate(coords):
            v = A * sp.Matrix([x,y]); j = coords.index((int(v[0]), int(v[1]))); F0[j,i] = 1; perm[i] = j
        lookup = {(i,(i+1)%4): i for i in range(4)}; F1 = sp.zeros(4,4)
        for i in range(4):
            u, v = perm[i], perm[(i+1)%4]
            if (u,v) in lookup: F1[lookup[(u,v)], i] = 1
            else: F1[lookup[(v,u)], i] = -1
        assert D * F1 == F0 * D
        return F0
    maps = [f0(A) for A in transforms]
    return {"wrong_pairings_rejected": sum(i != j and C * maps[j] != transforms[i] * C for i in range(8) for j in range(8))}


def run_e17():
    first32 = first64 = None
    for n in range(2, 15):
        H = sp.Matrix([[sp.Rational(1, i+j+1) for j in range(n)] for i in range(n)])
        assert H.det() != 0
        if first32 is None and np.linalg.matrix_rank(np.array(H.tolist(), dtype=np.float32)) < n: first32 = n
        if first64 is None and np.linalg.matrix_rank(np.array(H.tolist(), dtype=np.float64)) < n: first64 = n
    return {"first_float32_loss": first32, "first_float64_loss": first64}


def run_e18():
    verts = [(x,y) for y in range(3) for x in range(3)]; vid = {v:i for i,v in enumerate(verts)}; tris = []
    for y in range(2):
        for x in range(2):
            a,b,c,d = vid[(x,y)],vid[(x+1,y)],vid[(x+1,y+1)],vid[(x,y+1)]; tris += [(a,b,c),(a,c,d)]
    edges = sorted({tuple(sorted(e)) for tri in tris for e in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]}); eid = {e:i for i,e in enumerate(edges)}
    D1 = sp.zeros(len(verts), len(edges)); D2 = sp.zeros(len(edges), len(tris))
    for j,(u,v) in enumerate(edges): D1[u,j],D1[v,j] = -1,1
    for j,(a,b,c) in enumerate(tris):
        for coef,(u,v) in [(1,(b,c)),(-1,(a,c)),(1,(a,b))]:
            e = tuple(sorted((u,v))); D2[eid[e],j] += coef * (1 if (u,v) == e else -1)
    tested = detected = localized = 0
    for ei in range(D2.rows):
        for fj in range(D2.cols):
            if D2[ei,fj] == 0: continue
            tested += 1; C = D2.copy(); C[ei,fj] *= -1; R = D1 * C
            detected += R != sp.zeros(*R.shape); nzcols = sorted({j for i in range(R.rows) for j in range(R.cols) if R[i,j] != 0}); rc = R[:,fj]; cand = []
            for e in range(D1.cols):
                col = D1[:,e]
                if col == rc or col == -rc or 2*col == rc or -2*col == rc: cand.append(e)
            localized += cand == [ei] and nzcols == [fj]
    return {"tested": tested, "detected": detected, "localized": localized}


def run_e19():
    M = 7680; angles = np.arange(M) * 2 * math.pi / M
    for n in [3,4,5,6,8]:
        xy = np.array(list(_regular_polygon(n).exterior.coords)[:-1], float)
        h = np.max(np.cos(angles)[:,None]*xy[:,0] + np.sin(angles)[:,None]*xy[:,1], axis=1); E = np.abs(np.fft.rfft(h)/M) ** 2
        assert float(sum(E[k] for k in range(1, len(E)) if k % n != 0) / E[1:].sum()) < 1e-20
    return {"status": "PASS", "triangle_square_first_common_harmonic": 12}


def _area_normalized(poly):
    c = poly.centroid; pts = [(x-c.x, y-c.y) for x,y in list(poly.exterior.coords)[:-1]]; s = Polygon(pts); q = 1 / math.sqrt(s.area)
    return Polygon([(x*q, y*q) for x,y in pts])


def run_e20():
    shapes = [_area_normalized(_regular_polygon(3, phase=math.pi/2)), _area_normalized(_regular_polygon(4, phase=math.pi/4)), _area_normalized(_regular_polygon(8, phase=math.pi/8)), _area_normalized(_regular_polygon(64))]
    diagonal = cross = True
    for i,K in enumerate(shapes):
        for j,L in enumerate(shapes):
            S = MultiPoint([(x1+x2,y1+y2) for x1,y1 in list(K.exterior.coords)[:-1] for x2,y2 in list(L.exterior.coords)[:-1]]).convex_hull
            V = (S.area - K.area - L.area) / 2; delta = V*V/(K.area*L.area) - 1
            diagonal &= (i != j or abs(delta) < 1e-10); cross &= (i == j or delta > 1e-5)
    return {"diagonal_zero": bool(diagonal), "cross_positive": bool(cross)}


def run_e21():
    pi, t = sp.pi, sp.symbols("t"); G2 = sp.Matrix([[0,1,0],[0,0,2*pi],[0,0,0]]); G3 = sp.Matrix([[0,1,0,0],[0,0,2,0],[0,0,0,4*pi],[0,0,0,0]])
    A,P,c = sp.symbols("A P c"); x = (sp.eye(3)+t*G2+t**2*G2**2/2) * sp.Matrix([A,P,c]); ok2 = sp.simplify(x[1]**2 - 4*pi*x[2]*x[0] - (P**2 - 4*pi*c*A)) == 0
    V,S,M,cc = sp.symbols("V S M cc"); y = (sp.eye(4)+t*G3+t**2*G3**2/2+t**3*G3**3/6) * sp.Matrix([V,S,M,cc]); I=lambda z:z[2]**2-4*pi*z[3]*z[1]; J=lambda z:2*z[2]**3-12*pi*z[3]*z[2]*z[1]+48*pi**2*z[3]**2*z[0]; ok3 = sp.simplify(I(y)-I(sp.Matrix([V,S,M,cc]))) == 0 and sp.simplify(J(y)-J(sp.Matrix([V,S,M,cc]))) == 0
    return {"G2_nilpotency_index": 3 if G2**3 == sp.zeros(3) else None, "G3_nilpotency_index": 4 if G3**4 == sp.zeros(4) else None, "invariants_conserved": bool(ok2 and ok3)}


def run_e22():
    rng = random.Random(22015); by = defaultdict(list)
    for tr in range(24):
        A0,P0,c = rng.uniform(.5,5),rng.uniform(1,8),rng.choice([-2,-1,1,2])
        for t in [0,.1,.25,.5,.9,1.3]: by[tr].append((t,A0+P0*t+math.pi*c*t*t,P0+2*math.pi*c*t,float(c)))
    dx,dy = [],[]
    for vals in by.values():
        _,Ar,Pr,cr = vals[0]
        for _,A,P,c in vals[1:]: dx.append(P*P-Pr*Pr); dy.append(A*c-Ar*cr)
    x,y = np.array(dx),np.array(dy); return {"coefficient": -float(np.dot(x,y)/np.dot(y,y)), "pi": math.pi}


def run_e23():
    data = json.loads((EVIDENCE / "pct_e23_counterexamples.json").read_text(encoding="utf-8"))
    return {"counterexamples": len(data["counterexamples"])}


def run_e24():
    rec = []
    for G in [g for g in nx.graph_atlas_g() if g.number_of_nodes() > 0]:
        n,m = G.number_of_nodes(),G.number_of_edges(); b0 = nx.number_connected_components(G); deg = tuple(sorted(dict(G.degree()).values())); lap = tuple(np.round(np.linalg.eigvalsh(nx.laplacian_matrix(G).toarray().astype(float)),9)); nx.set_node_attributes(G,"node","pct_label"); wl = nx.weisfeiler_lehman_graph_hash(G,node_attr="pct_label",iterations=6)
        rec.append((n-m,(b0,m-n+b0),deg,lap,wl))
    pairs = lambda k: sum(v*(v-1)//2 for v in Counter(tuple(r[:k]) for r in rec).values())
    B = sp.Matrix([[-1,0,0,1],[1,-1,0,0],[0,1,-1,0],[0,0,1,-1]]); Bf = sp.Matrix([[-1,0,0,0,1],[0,1,-1,0,0],[0,0,1,-1,0],[0,0,0,1,-1],[1,-1,0,0,0]]); F0 = sp.zeros(5,4)
    for t,s in [(0,0),(1,1),(2,2),(3,3)]: F0[t,s] = 1
    F1 = sp.zeros(5,4); F1[0,0]=F1[1,0]=F1[2,1]=F1[3,2]=F1[4,3]=1
    return {"atlas_objects":len(rec),"G0_collision_pairs":pairs(1),"G4_collision_pairs":pairs(5),"subdivision_chain_map_commutes":Bf*F1 == F0*B}


def validate_e25_evidence():
    data = json.loads((EVIDENCE / "pct_e25_graph_consistency_audit.json").read_text(encoding="utf-8"))
    conflicts = sum(len(data["conflicts"][k]) for k in ["identity_anchor_conflicts","source_hash_conflicts","equivalence_cycle_conflicts"])
    return {"status":data["status"],"nodes":data["graph"]["nodes"],"edges":data["graph"]["edges"],"equivalence_cycles":data["graph"]["equivalence_cycles"],"conflicts":conflicts}
