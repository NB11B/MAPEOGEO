"""GEO-BSL-003 candidate-family inference with held-out bases and integers."""
import json
import numpy as np

TRAIN_BASES=(3,5,7,10,12)
HELD_BASES=(2,4,8,11,16)
TRAIN_N=tuple(range(1,321))
TEST_N=tuple(range(321,641))
CANDIDATES=(0,1,2,3,4)

def digits(n,b):
    if n<0 or b<2: raise ValueError("n/base")
    if n==0: return (0,)
    ds=[]
    while n:
        ds.append(n%b); n//=b
    return tuple(ds[::-1])

def oracle(n,b):
    return sum(d*d for d in digits(n,b))

def features(n,b,p):
    return sum((int(d!=0) if p==0 else d**p) for d in digits(n,b))

def fit():
    data=[(n,b,oracle(n,b)) for b in TRAIN_BASES for n in TRAIN_N]
    y=np.array([z for _,_,z in data],float)
    scores={}
    for p in CANDIDATES:
        x=np.array([features(n,b,p) for n,b,_ in data],float)
        scale=float(np.dot(x,y)/np.dot(x,x))
        scores[p]=(float(np.sqrt(np.mean((scale*x-y)**2))),scale)
    return min(scores,key=lambda p:(scores[p][0],p)),scores

def evaluate(p,scale,bases,ns):
    errors=np.array([scale*features(n,b,p)-oracle(n,b) for b in bases for n in ns])
    return {"n":len(errors),"max_error":float(np.max(abs(errors))),"rmse":float(np.sqrt(np.mean(errors**2)))}

def baseline():
    x=np.array([[1,n,b,n/b] for b in TRAIN_BASES for n in TRAIN_N],float)
    y=np.array([oracle(n,b) for b in TRAIN_BASES for n in TRAIN_N],float)
    beta=np.linalg.lstsq(x,y,rcond=None)[0]
    xx=np.array([[1,n,b,n/b] for b in HELD_BASES for n in TEST_N],float)
    yy=np.array([oracle(n,b) for b in HELD_BASES for n in TEST_N],float)
    return float(np.sqrt(np.mean((xx@beta-yy)**2)))

def shuffled_control():
    y=np.array([oracle(n,b) for b in TRAIN_BASES for n in TRAIN_N],float)
    np.random.default_rng(12217).shuffle(y)
    scores=[]
    for p in CANDIDATES:
        x=np.array([features(n,b,p) for b in TRAIN_BASES for n in TRAIN_N],float)
        scale=float(np.dot(x,y)/np.dot(x,x))
        scores.append(float(np.sqrt(np.mean((scale*x-y)**2))))
    return min(scores)

def run():
    p,scores=fit(); scale=scores[p][1]
    return {"train_bases":TRAIN_BASES,"held_out_bases":HELD_BASES,
        "train_integer_range":[1,320],"test_integer_range":[321,640],
        "candidate_powers":CANDIDATES,"winner":p,"winner_scale":scale,
        "training_rmse_by_power":{str(q):scores[q][0] for q in scores},
        "seen_bases_held_integers":evaluate(p,scale,TRAIN_BASES,TEST_N),
        "unseen_bases_held_integers":evaluate(p,scale,HELD_BASES,TEST_N),
        "baseline_unseen_rmse":baseline(),"shuffled_train_best_rmse":shuffled_control()}

if __name__=="__main__": print(json.dumps(run(),indent=2))
