import math
from mapeogeo.latent_generator_v1 import linear_inverse,forward,sinusoid_generator,radial_angular_velocity


def test_full_rank_inverse_is_identifiable_but_not_source_identity():
    P=((1,0),(0,1));y=(3,4)
    r=linear_inverse(P,y)
    assert r.identifiable_rank==2 and r.null_basis==()
    assert forward(P,r.generator)==y
    assert not r.source_identified


def test_projection_returns_equivalence_class_not_invented_dimension():
    P=((1,0,0),(0,1,0));y=(2,-1)
    r=linear_inverse(P,y)
    assert r.identifiable_rank==2
    assert len(r.null_basis)==1
    assert r.null_basis[0]==(0.0,0.0,1.0)
    assert forward(P,r.generator)==y


def test_scalar_sine_observation_is_underdetermined_in_planar_generator():
    # y is the second coordinate only.
    q=sinusoid_generator(5,0.7)
    r=linear_inverse(((0,1),),(q[1],))
    assert r.identifiable_rank==1 and len(r.null_basis)==1
    assert math.isclose(forward(((0,1),),r.generator)[0],q[1],rel_tol=1e-12)


def test_calculus_radial_plus_angular_matches_direct_derivative_formula():
    A=3.2;th=.4;dA=.7;dth=-1.3
    radial,angular,total=radial_angular_velocity(A,th,dA,dth)
    expected=(dA*math.cos(th)-A*dth*math.sin(th),dA*math.sin(th)+A*dth*math.cos(th))
    assert all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(total,expected))
