import math
from mapeogeo.latent_waveform_identifiability_v2 import constant_frequency_inverse,varying_amplitude_equation

def test_known_rate_plus_derivative_recovers_amplitude_and_phase():
    A=7.3;theta=1.1;omega=2.4
    y=A*math.sin(theta);dy=A*omega*math.cos(theta)
    r=constant_frequency_inverse(y,dy,omega)
    assert r.identifiable and not r.branch_ambiguous
    assert math.isclose(r.amplitude,A,rel_tol=1e-12)
    assert math.isclose(r.theta_mod_2pi,theta,rel_tol=1e-12)

def test_zero_amplitude_leaves_phase_undefined():
    r=constant_frequency_inverse(0,0,3)
    assert not r.identifiable and r.reason=="ZERO_AMPLITUDE_PHASE_UNDEFINED"

def test_varying_amplitude_derivative_contains_both_scale_and_rotation_work():
    A=4;theta=.7;dA=.5;dtheta=1.2
    y=A*math.sin(theta)
    dy=dA*math.sin(theta)+A*dtheta*math.cos(theta)
    e1,e2=varying_amplitude_equation(y,dy,A,theta,dA,dtheta)
    assert e1<1e-12 and e2<1e-12
