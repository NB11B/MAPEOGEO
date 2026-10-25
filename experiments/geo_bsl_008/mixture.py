"""GEO-BSL-008 unlabeled linear-mixture recovery with native PSMSL basis."""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"geo_bsl_006"))
from adapter import discover_basis,Qualification

def fixture(seed=921,n=120,mode="distinct"):
    rng=np.random.default_rng(seed)
    A=np.array([[1.,1.],[0.,1.]])
    B=np.array([[0.,-1.],[1.,0.]]) if mode!="identical" else A.copy()
    Q=np.array([[1.4,.25],[-.3,.8]])
    z=rng.normal(size=(n,2))
    labels=rng.integers(0,2,n)
    x=z@Q.T
    y=np.array([Q@((A if k==0 else B)@v) for v,k in zip(z,labels)])
    if mode=="nonlinear":y=y+0.2*x*x
    if mode=="rank_deficient":x[:,1]=2*x[:,0]
    return x,y,labels,[Q@A@np.linalg.inv(Q),Q@B@np.linalg.inv(Q)]

def fit(x,y):
    if np.linalg.matrix_rank(x)<2:raise ValueError("rank deficient")
    return np.linalg.lstsq(x,y,rcond=None)[0].T

def discover(x,y,seed=26,trials=400,tol=1e-7):
    x=np.asarray(x,float);y=np.asarray(y,float);n=len(x)
    if x.shape!=y.shape or x.ndim!=2 or x.shape[1]!=2 or n<24 or not np.isfinite(x).all() or not np.isfinite(y).all():
        return None
    if np.linalg.matrix_rank(x)<2:return None
    rng=np.random.default_rng(seed)
    candidates=[]
    for _ in range(trials):
        ix=rng.choice(n,2,replace=False)
        if abs(np.linalg.det(x[ix]))>1e-3:candidates.append(fit(x[ix],y[ix]))
    if not candidates:return None
    residual=np.array([np.sum((x@a.T-y)**2,axis=1) for a in candidates])
    support=(residual<tol**2).sum(axis=1)
    shortlist=np.argsort(-support,kind="stable")[:60]
    best=None
    for i in shortlist:
        for j in shortlist:
            if i==j or np.linalg.norm(candidates[i]-candidates[j])<1e-5:continue
            score=float(np.mean(np.minimum(residual[i],residual[j])))
            if best is None or score<best[0]:best=(score,candidates[i],candidates[j])
    if best is None:return None
    ops=[best[1],best[2]]
    for _ in range(30):
        errors=np.stack([np.sum((x@a.T-y)**2,axis=1) for a in ops],axis=1)
        labels=np.argmin(errors,axis=1)
        if min(np.bincount(labels,minlength=2))<12:return None
        try:new=[fit(x[labels==k],y[labels==k]) for k in range(2)]
        except ValueError:return None
        if max(np.linalg.norm(a-b) for a,b in zip(ops,new))<1e-11:ops=new;break
        ops=new
    err=np.stack([np.sum((x@a.T-y)**2,axis=1) for a in ops],axis=1)
    rmse=float(np.sqrt(np.mean(np.min(err,axis=1))/2))
    if rmse>=tol or np.linalg.norm(ops[0]-ops[1])<1e-5:return None
    return ops,np.argmin(err,axis=1),rmse

def run():
    x,y,truth,expected=fixture()
    result=discover(x,y)
    if result is None:raise AssertionError("nominal mechanism failed")
    ops,labels,error=result
    # Native API: test independence of the recovered, not original, generators.
    qs=[Qualification(True,"qualified",error,error,tuple(tuple(float(v) for v in row) for row in m)) for m in ops]
    basis=discover_basis(qs)
    from itertools import permutations
    gauge=min(max(float(np.linalg.norm(ops[i]-expected[p[i]])) for i in range(2)) for p in permutations(range(2)))
    xx,yy,_,_=fixture(seed=922)
    held=np.stack([np.sum((xx@m.T-yy)**2,axis=1) for m in ops])
    return {"qualified":True,"native_basis_rank":basis.rank,"gauge_equivalent_operator_error":gauge,
       "train_rmse":error,"heldout_rmse":float(np.sqrt(np.mean(np.min(held,axis=0))/2)),
       "assignment_accuracy":float(max(np.mean(labels==truth),np.mean(labels!=truth))),
       "identical_refused":discover(*fixture(mode="identical")[:2]) is None,
       "nonlinear_refused":discover(*fixture(mode="nonlinear")[:2]) is None,
       "rank_deficient_refused":discover(*fixture(mode="rank_deficient")[:2]) is None,
       "small_sample_refused":discover(*fixture(n=10)[:2]) is None}
if __name__=="__main__":print(json.dumps(run(),indent=2))
