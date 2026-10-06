import math
from mapeogeo.latent_nonlinear_identifiability_v2 import local_identifiability

def test_scalar_sine_measurement_has_one_dimensional_local_nullspace():
    def f(x):
        A,th=x
        return (A*math.sin(th),)
    J,rank,null=local_identifiability(f,(3,.8))
    assert rank==1 and len(null)==1

def test_waveform_and_known_rate_derivative_are_locally_full_rank():
    omega=2
    def f(x):
        A,th=x
        return (A*math.sin(th),A*omega*math.cos(th))
    J,rank,null=local_identifiability(f,(3,.8))
    assert rank==2 and null==()
