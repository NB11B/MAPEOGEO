"""Exact active identification of finite permutation generators; no priors on group relations."""
from itertools import permutations, product
from collections import Counter

def version_space(n,names,observations):
    candidates=tuple(permutations(range(n)));spaces={}
    for a in names:
        obs=[(s,t) for name,s,t in observations if name==a]
        if any(not (0<=s<n and 0<=t<n) for s,t in obs):return None
        spaces[a]=tuple(p for p in candidates if all(p[s]==t for s,t in obs))
        if not spaces[a]:return None
    return spaces

def probe(spaces,n,names):
    scores=[]
    for name in names:
        for state in range(n):
            hist=Counter(p[state] for p in spaces[name])
            worst=max(hist.values())
            scores.append((len(spaces[name])-worst,name,state,dict(hist)))
    best=max(score for score,*_ in scores)
    if best==0:return None
    return next((name,state,hist) for score,name,state,hist in scores if score==best)

def train(n,generators,strategy='active',budget=8):
    names=tuple(generators);observed=[];history=[]
    for t in range(budget):
        spaces=version_space(n,names,observed)
        if spaces is None:return {'status':'contradiction','history':history}
        if all(len(spaces[x])==1 for x in names):break
        if strategy=='active':
            choice=probe(spaces,n,names)
            if choice is None:break
            name,state,_=choice
        elif strategy=='passive':
            name=names[t%len(names)];state=0
        else:raise ValueError(strategy)
        output=generators[name][state]
        observed.append((name,state,output));history.append((name,state,output))
    spaces=version_space(n,names,observed)
    identified=all(len(spaces[a])==1 for a in names)
    return {'status':'identified' if identified else 'ambiguous',
            'counts':{a:len(spaces[a]) for a in names},'history':history,
            'generators':{a:spaces[a][0] for a in names} if identified else None}

def heldout(n,oracle,inferred):
    if inferred['status']!='identified':return None
    errors=0;total=0
    for length in range(1,6):
        for word in product(oracle,repeat=length):
            for initial in range(n):
                a=b=initial
                for name in word:
                    a=oracle[name][a];b=inferred['generators'][name][b]
                errors+=a!=b;total+=1
    return errors,total

def campaign():
    systems={'D4':{'r':(1,2,3,0),'f':(0,3,2,1)},
             'V4':{'a':(1,0,3,2),'b':(2,3,0,1)},
             'C4':{'r':(1,2,3,0),'i':(0,1,2,3)}}
    results={}
    for name,g in systems.items():
        active=train(4,g,'active',8);passive=train(4,g,'passive',8)
        results[name]={'active':active['status'],'active_queries':len(active['history']),
          'passive':passive['status'],'passive_remaining':passive['counts'],
          'heldout':heldout(4,g,active)}
    return results
if __name__=='__main__':
    import json
    print(json.dumps(campaign(),indent=2))
