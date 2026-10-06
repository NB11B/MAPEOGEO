"""Local identifiability of amplitude/phase generators from waveform derivatives."""
from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class WaveformLocalInverse:
    amplitude:float|None
    theta_mod_2pi:float|None
    branch_ambiguous:bool
    identifiable:bool
    reason:str

def constant_frequency_inverse(y,dy,omega,tol=1e-12):
    """For y=A sin(theta), dy=A*omega*cos(theta), with constant A and known nonzero omega."""
    if abs(omega)<=tol:return WaveformLocalInverse(None,None,True,False,"ZERO_OR_UNKNOWN_RATE")
    x=dy/omega
    A=math.hypot(x,y)
    if A<=tol:return WaveformLocalInverse(0.0,None,True,False,"ZERO_AMPLITUDE_PHASE_UNDEFINED")
    theta=math.atan2(y,x)%(2*math.pi)
    return WaveformLocalInverse(A,theta,False,True,"IDENTIFIED_MOD_2PI")

def varying_amplitude_equation(y,dy,A,theta,dA,dtheta):
    return abs(y-A*math.sin(theta)), abs(dy-(dA*math.sin(theta)+A*dtheta*math.cos(theta)))
