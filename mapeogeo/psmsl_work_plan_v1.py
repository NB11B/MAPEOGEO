"""Derive execution consequences from PSMSL operator semantics."""
from __future__ import annotations
from dataclasses import dataclass
from .psmsl_operator_algebra_v1 import ordering_semantics,information_semantics

@dataclass(frozen=True)
class WorkPlanSemantics:
    reorder_safe:bool
    parallelizable:bool
    fusion_allowed:bool
    irreversible_steps:tuple[int,...]

def derive_plan(operators,tol=1e-10):
    irreversible=tuple(i for i,A in enumerate(operators) if information_semantics(A,tol).information_loss)
    all_commute=True
    for i,A in enumerate(operators):
        for B in operators[i+1:]:
            if len(A)==len(A[0])==len(B)==len(B[0]) and len(A)==len(B):
                if not ordering_semantics(A,B,tol).commutes:all_commute=False
            else:all_commute=False
    return WorkPlanSemantics(all_commute,all_commute,True,irreversible)
