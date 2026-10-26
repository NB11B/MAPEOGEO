"""GEO-BSL-006: adapter to the repository's actual PSMSL operator-basis API.

Observations are pairs (input vector, output vector). No digit parser or number base.
A least-squares linear operator is inferred per task, and the native basis selector
determines independent matrix operators. Holdouts and nonlinear negatives are blind
to fitting.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys
import numpy as np

_VENDOR=Path(__file__).resolve().parents[2]/"ngc_geometry_lab"/"ngc_geometry_lab"/"_vendor"/"mapeogeo"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0,str(_VENDOR))
from mapeogeo.psmsl_operator_basis_v1 import discover_linear_operator_basis
from mapeogeo.psmsl_operator_algebra_v1 import ordering_semantics

@dataclass(frozen=True)
class Qualification:
    accepted: bool
    reason: str
    train_rmse: float
    holdout_rmse: float
    operator: tuple

def infer_linear(inputs, outputs, holdout_inputs, holdout_outputs,
                 threshold=1e-8):
    x=np.asarray(inputs,dtype=float)
    y=np.asarray(outputs,dtype=float)
    xt=np.asarray(holdout_inputs,dtype=float)
    yt=np.asarray(holdout_outputs,dtype=float)
    if x.ndim!=2 or y.ndim!=2 or xt.ndim!=2 or yt.ndim!=2:
        raise ValueError("observations must be rank-2 arrays")
    if x.shape[0]!=y.shape[0] or xt.shape[0]!=yt.shape[0] or x.shape[1]!=xt.shape[1] or y.shape[1]!=yt.shape[1]:
        raise ValueError("observation shape mismatch")
    if np.linalg.matrix_rank(x)<x.shape[1]:
        return Qualification(False,"unidentifiable inputs",float("inf"),float("inf"),())
    coefficients=np.linalg.lstsq(x,y,rcond=None)[0]
    matrix=coefficients.T
    train=float(np.sqrt(np.mean((x@coefficients-y)**2)))
    holdout=float(np.sqrt(np.mean((xt@coefficients-yt)**2)))
    valid=train<=threshold and holdout<=threshold
    return Qualification(valid,"qualified" if valid else "model mismatch",
                         train,holdout,tuple(tuple(float(v) for v in row) for row in matrix))

def discover_basis(qualifications):
    qualified=[q.operator for q in qualifications if q.accepted]
    if not qualified:
        return discover_linear_operator_basis(())
    return discover_linear_operator_basis(tuple(qualified))

def run():
    rng=np.random.default_rng(20261025)
    x=rng.normal(size=(80,2)); xt=rng.normal(size=(40,2))
    a=np.array([[1.,2.],[0.,1.]])
    b=np.array([[0.,1.],[-1.,0.]])
    qs=[infer_linear(x,x@m.T,xt,xt@m.T) for m in (a,b,2*a)]
    nonlinear=infer_linear(x,x*x,xt,xt*xt)
    under=infer_linear(np.ones((80,2)),np.ones((80,2)),xt,xt)
    basis=discover_basis(qs+[nonlinear,under])
    sem=ordering_semantics(qs[0].operator,qs[1].operator)
    return {"native_api":"mapeogeo.psmsl_operator_basis_v1.discover_linear_operator_basis",
            "accepted":[q.accepted for q in qs],
            "nonlinear_rejected":not nonlinear.accepted,
            "rank_deficient_rejected":not under.accepted,
            "basis_indices":list(basis.basis_indices),
            "basis_rank":basis.rank,
            "redundant_indices":list(basis.redundant_indices),
            "ordering_commutes":sem.commutes,
            "max_linear_holdout_rmse":max(q.holdout_rmse for q in qs)}
if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2))
