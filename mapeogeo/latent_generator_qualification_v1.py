"""Common qualification gate for latent-generator routes."""
from __future__ import annotations
from dataclasses import dataclass
from .latent_generator_v1 import forward

@dataclass(frozen=True)
class Qualification:
    passed:bool
    residual:float
    nullity:int
    overidentified_source:bool

def qualify_linear(P,y,result,tolerance=1e-9):
    yh=forward(P,result.generator)
    residual=sum((float(a)-float(b))**2 for a,b in zip(yh,y))**0.5
    over=bool(result.source_identified)
    return Qualification(residual<=tolerance and not over,residual,len(result.null_basis),over)
