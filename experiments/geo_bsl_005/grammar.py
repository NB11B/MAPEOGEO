"""GEO-BSL-005: constrained compositional operator search."""
import json
import numpy as np
TRAIN_BASES=(5,7,10,12)
TEST_BASES=(6,8,11,14)
TRAIN_N=range(120,421)
TEST_N=range(421,721)
FAMILIES=('additive','positional','pair','combined')
def digits(n,b):
    if n<0 or b<2: raise ValueError('invalid n/base')
    if n==0: return [0]
    a=[]
    while n: a.append(n%b); n//=b
    return a[::-1]
def features(n,b,family):
    ds=digits(n,b)
    additive=[sum(d**p for d in ds) for p in (1,2,3)]
    if family=='additive': return additive
    positional=[sum(i*d**p for i,d in enumerate(ds)) for p in (1,2,3)]
    if family=='positional': return additive+positional
    pair=[sum(ds[i]**p*ds[i+1]**q for i in range(len(ds)-1)) for p,q in ((1,1),(1,2),(2,1))]
    if family=='pair': return additive+pair
    if family=='combined': return additive+positional+pair
    raise ValueError(family)
def truth(n,b,rule):
    f=np.asarray(features(n,b,'combined'))
    if rule=='additive':return float(f[1])
    if rule=='positional':return float(f[1]+0.5*f[4])
    if rule=='pair':return float(f[1]+0.25*f[6])
    if rule=='combined':return float(f[1]+0.5*f[4]+0.25*f[6])
    if rule=='parity':return float(f[1]+13*(n%2))
    raise ValueError(rule)
def discover(rule):
    train=[(n,b) for b in TRAIN_BASES for n in TRAIN_N]
    test=[(n,b) for b in TEST_BASES for n in TEST_N]
    yt=np.array([truth(n,b,rule) for n,b in train])
    yh=np.array([truth(n,b,rule) for n,b in test])
    stats={}
    for family in FAMILIES:
        x=np.array([features(n,b,family) for n,b in train],float)
        xx=np.array([features(n,b,family) for n,b in test],float)
        beta=np.linalg.lstsq(x,yt,rcond=None)[0]
        r=yt-x@beta
        e=yh-xx@beta
        stats[family]={'train_rmse':float(np.sqrt(np.mean(r*r))),
                       'test_rmse':float(np.sqrt(np.mean(e*e))),
                       'rank':int(np.linalg.matrix_rank(x)),
                       'columns':int(x.shape[1]),
                       'coef':[float(v) for v in beta]}
    eligible=[f for f in FAMILIES if stats[f]['train_rmse']<1e-8 and stats[f]['rank']==stats[f]['columns']]
    chosen=min(eligible,key=lambda f:(stats[f]['columns'],FAMILIES.index(f))) if eligible else None
    return {'rule':rule,'selected':chosen,'models':stats,'train_bases':TRAIN_BASES,'heldout_bases':TEST_BASES,
            'train_n':[min(TRAIN_N),max(TRAIN_N)],'heldout_n':[min(TEST_N),max(TEST_N)]}
def run():return {rule:discover(rule) for rule in ('additive','positional','pair','combined','parity')}
if __name__=='__main__':print(json.dumps(run(),indent=2))
