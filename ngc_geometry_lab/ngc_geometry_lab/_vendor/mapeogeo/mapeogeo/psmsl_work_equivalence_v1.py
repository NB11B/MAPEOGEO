"""Work-relative PSMSL operator equivalence and commutation."""
from __future__ import annotations
from dataclasses import dataclass
from .psmsl_operator_algebra_v1 import matmul,matsub,frobenius,commutator

@dataclass(frozen=True)
class WorkEquivalence:
    exact_difference:float
    observed_difference:float
    tolerance:float
    equivalent_for_work:bool
    exact_equal:bool

def work_relative_commutation(A,B,observation=None,tolerance=0.0):
    AB=matmul(A,B);BA=matmul(B,A)
    exact=frobenius(matsub(AB,BA))
    if observation is None:
        observed=exact
    else:
        observed=frobenius(matsub(matmul(observation,AB),matmul(observation,BA)))
    return WorkEquivalence(exact,observed,tolerance,observed<=tolerance,exact<=1e-12)

def work_relative_information_loss(T,observation_before=None,observation_after=None,tolerance=1e-12):
    """Compare whether T changes the requested observable map.

    If observation_after*T == observation_before, T may lose global information
    while preserving all information required by this work.
    """
    if observation_before is None or observation_after is None:
        raise ValueError("both observable maps required")
    composed=matmul(observation_after,T)
    d=frobenius(matsub(composed,observation_before))
    return d,d<=tolerance
