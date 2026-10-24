"""Independent, exact Rule 30 falsification suite. Python >=3.10; stdlib only.
Run: python rule30_suite.py --depth 6 --benchmark 256
"""
from __future__ import annotations
import argparse, json, time
from collections import Counter


def rule30(left:int, center:int, right:int)->int:
    return left ^ (center | right)


def sideways_left(next_center:int, center:int, right:int)->int:
    return next_center ^ (center | right)


def step(row:dict[int,int], radius:int)->dict[int,int]:
    return {i:rule30(row.get(i-1,0),row.get(i,0),row.get(i+1,0)) for i in range(-radius,radius+1)}


def history(depth:int, seed:dict[int,int]|None=None)->list[dict[int,int]]:
    radius=depth+1
    rows=[{i:(seed or {0:1}).get(i,0) for i in range(-radius,radius+1)}]
    for _ in range(depth):
        rows.append(step(rows[-1],radius))
    return rows


def packed_history(depth:int)->list[int]:
    width=2*depth+3; center=depth+1
    mask=(1<<width)-1
    rows=[1<<center]
    for _ in range(depth):
        z=rows[-1]
        rows.append((((z<<1)&mask) ^ (z | (z>>1))) & mask)
    return rows


def e1(depth:int)->dict:
    rows=history(depth)
    verified=0; screens=0; right_unscreened=0
    for t in range(depth):
        for i in range(-depth+t+1,depth-t):
            a,b,c=rows[t][i-1],rows[t][i],rows[t][i+1]
            out=rows[t+1][i]
            assert sideways_left(out,b,c)==a
            assert rule30(a,b,c)==out
            verified+=1
            if b:
                assert rule30(a,b,0)==rule30(a,b,1)
                screens+=1
            else:
                assert rule30(a,b,0)!=rule30(a,b,1)
                right_unscreened+=1
    boundary_checks=0
    for t in range(depth+1):
        for k in range(1,depth+1):
            if -k in rows[t]:
                if t<k: assert rows[t][-k]==0
                if t==k: assert rows[t][-k]==1
                boundary_checks+=1
    # Transfer using two adjacent columns, triangular causal horizon shrinks by one.
    center=[rows[t][0] for t in range(depth+1)]
    right=[rows[t][1] for t in range(depth+1)]
    for k in range(1,depth+1):
        new=[sideways_left(center[t+1],center[t],right[t]) for t in range(len(center)-1)]
        assert new==[rows[t][-k] for t in range(depth-k+1)]
        right,center=center[:-1],new
    return dict(identity_checks=verified,boundary_checks=boundary_checks,screened_sites=screens,unscreened_sites=right_unscreened,sideways_columns=depth,status='PASS')


def central_trace(initial:int,k:int)->tuple[int,...]:
    width=2*k+1; mask=(1<<width)-1
    z=initial
    trace=[]
    for t in range(k+1):
        trace.append((z>>k)&1)
        z=(((z<<1)&mask) ^ (z | (z>>1)))&mask
    return tuple(trace)


def e2(depth:int)->dict:
    series=[]
    # Exact finite-horizon equivalence on entire initial states for the central temporal trace.
    # Quotient is a READOUT quotient, not a transition congruence or proof of compression.
    for k in range(1,min(depth,7)+1):
        counts=Counter(central_trace(z,k) for z in range(1<<(2*k+1)))
        classes=len(counts); states=1<<(2*k+1)
        series.append(dict(k=k,raw_states=states,observational_classes=classes,ratio=classes/states,largest_class=max(counts.values()),smallest_class=min(counts.values())))
    return dict(status='PASS',definition='equal central-cell traces over times 0..k, from zero-padded initial finite windows',series=series)


def anf_properties(k:int)->dict:
    variables=2*k+1; size=1<<variables
    values=bytearray((central_trace(x,k)[-1] for x in range(size)))
    for bit in range(variables):
        jump=1<<bit
        for base in range(0,size,2*jump):
            for i in range(base+jump,base+2*jump):
                values[i]^=values[i-jump]
    monomials=[x for x,v in enumerate(values) if v]
    return dict(k=k,variables=variables,degree=max((x.bit_count() for x in monomials),default=0),monomials=len(monomials),total_monomials=size)


def e3(depth:int)->dict:
    return dict(status='PASS',model='Boolean-ring ANF exact Mobius transform; no inferred BDD/tensor-rank results',series=[anf_properties(k) for k in range(min(depth,6)+1)])


def e4(depth:int,benchmark:int)->dict:
    # Two exact algorithms, one scalar cell update, one packed word update.
    assert benchmark>=1
    t0=time.perf_counter()
    scalar=history(benchmark)
    elapsed_scalar=time.perf_counter()-t0
    t0=time.perf_counter()
    packed=packed_history(benchmark)
    elapsed_packed=time.perf_counter()-t0
    for t in range(benchmark+1):
        assert scalar[t][0]==((packed[t]>>(benchmark+1))&1)
    # Scalar work reports actual update counts in this fixed-width implementation.
    # Packed work reports row primitives, NOT bit operations; word lengths grow with n.
    width=2*benchmark+3
    scalar_evaluations=benchmark*width
    packed_shifts=2*benchmark; packed_bitwise=3*benchmark
    return dict(status='PASS',benchmark_depth=benchmark,central_cells_agree=benchmark+1,
        scalar_cell_updates=scalar_evaluations,packed_bigint_shifts=packed_shifts,
        packed_bigint_bitwise=packed_bitwise,packed_bit_width=width,
        scalar_seconds=round(elapsed_scalar,6),packed_seconds=round(elapsed_packed,6),
        qualification='No asymptotic speedup claim: Python arbitrary-precision operations have nonconstant bit cost')


def run(depth:int=6,benchmark:int=256)->dict:
    assert 1<=depth<=7 and 1<=benchmark<=1024
    return {'parameters':{'depth':depth,'benchmark':benchmark},'E1':e1(depth),'E2':e2(depth),'E3':e3(depth),'E4':e4(depth,benchmark)}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--depth',type=int,default=6);ap.add_argument('--benchmark',type=int,default=256)
    args=ap.parse_args();print(json.dumps(run(args.depth,args.benchmark),indent=2))
