"""GEO-BSL-007: unknown finite-dimensional generators from trajectory observations.

Generator matrices are withheld from the inference path. Experiment IDs identify
transition streams; no numerical operator identity is supplied to the estimator.
"""
import json
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"geo_bsl_006"))
from adapter import infer_linear,discover_basis
def observe(generator, rng, count=50):
    x=rng.normal(size=(count,2))
    return x,x@generator.T
def experiment():
    rng=np.random.default_rng(707)
    unknown=(np.array([[1.,1.],[0.,1.]]),
             np.array([[0.,-1.],[1.,0.]]),
             np.array([[2.,2.],[0.,2.]]))
    discovered=[]
    for matrix in unknown:
        x,y=observe(matrix,rng)
        tx,ty=observe(matrix,rng,25)
        discovered.append(infer_linear(x,y,tx,ty))
    basis=discover_basis(discovered)
    bad_x=np.column_stack([np.ones(40),np.ones(40)])
    deficient=infer_linear(bad_x,bad_x@unknown[0].T,
                            np.eye(2),np.eye(2)@unknown[0].T)
    x=rng.normal(size=(75,2))
    xh=rng.normal(size=(35,2))
    nonlinear=infer_linear(x,np.sin(x),xh,np.sin(xh))
    return dict(qualified=[q.accepted for q in discovered],
        basis_indices=list(basis.basis_indices),
        redundant=list(basis.redundant_indices),
        maximum_holdout_error=max(q.holdout_rmse for q in discovered),
        rank_deficient_refused=not deficient.accepted,
        nonlinear_refused=not nonlinear.accepted,
        claim_boundary="Known vector coordinates and labeled streams; unknown matrices and basis independence.")
if __name__=="__main__":print(json.dumps(experiment(),indent=2))
