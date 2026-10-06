"""Cross-domain latent-generator adapters built on the generic inverse contract."""
from __future__ import annotations
from dataclasses import dataclass
import cmath,math
from .latent_generator_v1 import linear_inverse,forward

@dataclass(frozen=True)
class ComplexState:
    amplitude:float
    phase:float

def iq_state(i,q):
    z=complex(i,q)
    return ComplexState(abs(z),cmath.phase(z))

def iq_forward(state):
    return (state.amplitude*math.cos(state.phase),state.amplitude*math.sin(state.phase))

def projected_3d(P,y):
    return linear_inverse(P,y)

def modal_inverse(mode_matrix,observation):
    return linear_inverse(mode_matrix,observation)

@dataclass(frozen=True)
class ElectricalOperator:
    impedance:complex|None
    complex_power:complex
    identifiable:bool
    source_identified:bool=False

def electrical_operator(voltage:complex,current:complex,tol=1e-12):
    power=voltage*current.conjugate()
    if abs(current)<=tol:
        return ElectricalOperator(None,power,False,False)
    return ElectricalOperator(voltage/current,power,True,False)
