import math
from mapeogeo.latent_generator_observability_v2 import trajectory_inverse,observability_matrix,dynamic_initial_state_inverse

def test_rotating_projection_collapses_instantaneous_nullspace():
    q=(3.0,4.0)
    Ps=(((1,0),),((0,1),))
    ys=((3.0,),(4.0,))
    r=trajectory_inverse(Ps,ys)
    assert r.identifiable_rank==2 and r.null_basis==()
    assert all(math.isclose(a,b) for a,b in zip(r.generator,q))

def test_repeated_same_projection_preserves_nullspace():
    r=trajectory_inverse((((1,0),),((1,0),)),((3,),(3,)))
    assert r.identifiable_rank==1 and len(r.null_basis)==1

def test_control_observability_matrix_recovers_hidden_state_over_time():
    A=((0,-1),(1,0));C=((1,0),)
    O=observability_matrix(A,C,2)
    assert O==((1.0,0.0),(0.0,-1.0))
    # q0=(2,3): observations Cq0=2, CAq0=-3.
    r=dynamic_initial_state_inverse(A,C,((2,),(-3,)))
    assert r.null_basis==()
    assert all(math.isclose(a,b,abs_tol=1e-12) for a,b in zip(r.generator,(2,3)))
