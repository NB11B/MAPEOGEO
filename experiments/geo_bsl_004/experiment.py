"""GEO-BSL-004: learn digit contributions from outputs, with adversarial controls."""
import json
import numpy as np
TRAIN_BASES=(3,5,7,10,12)
UNSEEN_BASES=(2,4,8,11,16)
TRAIN_N=range(1,321)
TEST_N=range(321,641)
def digits(n,b):
    if n<0 or b<2: raise ValueError("n/base")
    if n==0: return [0]
    out=[]
    while n: out.append(n%b); n//=b
    return out[::-1]
def histogram(n,b):
    h=np.zeros(12)
    for d in digits(n,b):
        if d<12:h[d]+=1
    return h
def oracle(n,b):return sum(d*d for d in digits(n,b))
def positional_oracle(n,b):return sum((i+1)*d*d for i,d in enumerate(digits(n,b)))
def interaction_oracle(n,b):
    ds=digits(n,b)
    return oracle(n,b)+sum(ds[i]*ds[i+1] for i in range(len(ds)-1))
def learn(rule=oracle):
    x=np.array([histogram(n,b) for b in TRAIN_BASES for n in TRAIN_N])
    y=np.array([rule(n,b) for b in TRAIN_BASES for n in TRAIN_N],float)
    if np.linalg.matrix_rank(x)!=12:raise RuntimeError("not identifiable")
    weights=np.linalg.lstsq(x,y,rcond=None)[0]
    err=float(np.max(abs(x@weights-y)))
    for degree in range(5):
        coeff=np.polynomial.polynomial.polyfit(np.arange(12),weights,degree)
        if max(abs(np.polynomial.polynomial.polyval(np.arange(12),coeff)-weights))<1e-8:
            return dict(degree=degree,coeff=coeff,train_max_error=err)
    return dict(degree=None,coeff=None,train_max_error=err)
def predict(n,b,model):
    return sum(float(np.polynomial.polynomial.polyval(d,model["coeff"])) for d in digits(n,b))
def trial(rule):
    m=learn(rule)
    if m["degree"] is None: return dict(degree=None,train_max_error=m["train_max_error"],unseen_max_error=None)
    errors=[abs(predict(n,b,m)-rule(n,b)) for b in UNSEEN_BASES for n in TEST_N]
    return dict(degree=m["degree"],train_max_error=m["train_max_error"],unseen_max_error=max(errors))
def run():return dict(additive_square=trial(oracle),position_dependent_negative=trial(positional_oracle),adjacency_interaction_negative=trial(interaction_oracle),unseen_predictions=1600)
if __name__=="__main__":print(json.dumps(run(),indent=2))
