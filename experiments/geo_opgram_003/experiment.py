"""Fair active/coverage/random baselines for learning permutation generators."""
import random
from itertools import permutations
SYSTEMS={'C4':{'r':(1,2,3,0),'i':(0,1,2,3)},'V4':{'a':(1,0,3,2),'b':(2,3,0,1)},'D4':{'r':(1,2,3,0),'f':(0,3,2,1)}}
def candidates(n,observations,action):
    known=[(s,t) for a,s,t in observations if a==action]
    return [p for p in permutations(range(n)) if all(p[s]==t for s,t in known)]
def choose_query(n,names,obs,strategy,rng):
    spaces={a:candidates(n,obs,a) for a in names}
    if any(not x for x in spaces.values()) or all(len(x)==1 for x in spaces.values()):return None
    old={(a,s) for a,s,_ in obs}
    remaining=[(a,s) for a in names for s in range(n) if (a,s) not in old]
    if strategy=='coverage':
        counts={a:sum(x==a for x,_,_ in obs) for a in names}
        return min(remaining,key=lambda q:(counts[q[0]],q[0],q[1]))
    if strategy=='random_coverage':return rng.choice(remaining)
    if strategy=='active':
        def score(q):
            a,s=q
            return len(spaces[a])-max(sum(p[s]==t for p in spaces[a]) for t in range(n))
        return max(remaining,key=score)
    raise ValueError(strategy)
def run_trial(ops,strategy,seed=0,corruption=None):
    n=len(next(iter(ops.values())));names=tuple(sorted(ops));rng=random.Random(seed);obs=[]
    while len(obs)<n*len(names):
        q=choose_query(n,names,obs,strategy,rng)
        if q is None:break
        a,s=q;dst=ops[a][s]
        if corruption==(a,s):dst=(dst+1)%n
        obs.append((a,s,dst))
    spaces={a:candidates(n,obs,a) for a in names}
    status='inconsistent' if any(not v for v in spaces.values()) else ('identified' if all(len(v)==1 for v in spaces.values()) else 'ambiguous')
    correct=status=='identified' and all(spaces[a][0]==ops[a] for a in names)
    return {'queries':len(obs),'status':status,'correct':correct,'observations':obs}
def campaign(seeds=100):
    result={}
    for name,ops in SYSTEMS.items():
        result[name]={}
        for strategy in ('active','coverage','random_coverage'):
            trials=[run_trial(ops,strategy,seed) for seed in range(seeds)]
            result[name][strategy]={'mean_queries':sum(r['queries'] for r in trials)/seeds,
                'all_correct':all(r['correct'] for r in trials),
                'min_queries':min(r['queries'] for r in trials),
                'max_queries':max(r['queries'] for r in trials)}
    return result
if __name__=='__main__':
    import json
    print(json.dumps(campaign(),indent=2))
