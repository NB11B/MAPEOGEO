"""Recover complete cyclic families from timestamped, opaque transition streams."""
import math,random
from collections import defaultdict

def compose(a,b):return tuple(a[b[i]] for i in range(len(a)))
def events(n,seed=0,missing=None,conflict=False):
    rng=random.Random(seed);perm=list(range(n));rng.shuffle(perm)
    inv=[0]*n
    for i,x in enumerate(perm):inv[x]=i
    names=[f"opaque-{31*i+7}" for i in range(n)];rng.shuffle(names)
    rows=[]
    for k,name in enumerate(names):
        for src in range(n):
            if missing==(k,src):continue
            rows.append((rng.randrange(1000000),name,src,perm[(inv[src]+k)%n]))
    if conflict:
        t,name,src,dst=rows[0];rows.append((t+1,name,src,(dst+1)%n))
    rng.shuffle(rows);return rows

def orbits(p):
    unseen=set(range(len(p)));out=[]
    while unseen:
        x=start=min(unseen);count=0
        while x in unseen:
            unseen.remove(x);count+=1;x=p[x]
        if x!=start:raise ValueError("invalid cycle")
        out.append(count)
    return tuple(sorted(out))

def discover(rows):
    if not rows:return {"status":"refuse","reason":"empty"}
    n=max(max(src,dst) for _,_,src,dst in rows)+1
    if n<2 or min(min(src,dst) for _,_,src,dst in rows)<0:
        return {"status":"refuse","reason":"invalid"}
    table=defaultdict(dict)
    for _,name,src,dst in sorted(rows):
        if src in table[name] and table[name][src]!=dst:
            return {"status":"refuse","reason":"conflict"}
        table[name][src]=dst
    if len(table)!=n or any(len(t)!=n for t in table.values()):
        return {"status":"refuse","reason":"incomplete"}
    ops=tuple(tuple(t[i] for i in range(n)) for t in table.values())
    group=set(ops);identity=tuple(range(n))
    if len(group)!=n or any(sorted(p)!=list(range(n)) for p in ops):
        return {"status":"refuse","reason":"invalid_operators"}
    if identity not in group or any(compose(a,b) not in group for a in ops for b in ops):
        return {"status":"refuse","reason":"not_closed"}
    lengths=[orbits(p) for p in ops if p!=identity]
    full=sum(length==(n,) for length in lengths)
    if full==0:return {"status":"refuse","reason":"noncyclic"}
    return {"status":"qualified","prime":full==n-1,"n":n,"full_orbits":full,
        "witness":next((v for v in lengths if v!=(n,)),None)}

def run(limit=20):
    failures=[]
    for n in range(2,limit+1):
        actual=discover(events(n,seed=100+n))
        reference=all(n%d for d in range(2,math.isqrt(n)+1))
        if actual["status"]!="qualified" or actual["prime"]!=reference:failures.append(n)
    return {"range":[2,limit],"mismatches":failures,
        "nine":discover(events(9)),
        "missing_refused":discover(events(9,missing=(3,4)))["status"]=="refuse",
        "conflict_refused":discover(events(9,conflict=True))["status"]=="refuse"}
if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2))
