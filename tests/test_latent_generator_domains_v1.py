import math
from mapeogeo.latent_generator_domains_v1 import iq_state,iq_forward,projected_3d,modal_inverse,electrical_operator


def test_iq_roundtrip_and_phase_generator():
    s=iq_state(3,4)
    assert math.isclose(s.amplitude,5)
    i,q=iq_forward(s)
    assert math.isclose(i,3,abs_tol=1e-12) and math.isclose(q,4,abs_tol=1e-12)


def test_3d_projection_reports_unobservable_axis():
    r=projected_3d(((1,0,0),(0,0,1)),(7,9))
    assert r.identifiable_rank==2 and len(r.null_basis)==1
    assert r.null_basis[0]==(0.0,1.0,0.0)


def test_modal_full_rank_reconstruction():
    M=((1,1),(1,-1));y=(5,1)
    r=modal_inverse(M,y)
    assert r.null_basis==()
    assert all(math.isclose(a,b,abs_tol=1e-12) for a,b in zip(r.generator,(3,2)))


def test_electrical_operator_recovers_work_relation_not_source():
    e=electrical_operator(120+0j,10-5j)
    assert e.identifiable and not e.source_identified
    assert abs(e.impedance-(9.6+4.8j))<1e-12
    assert e.complex_power==1200+600j


def test_zero_current_leaves_impedance_unidentified():
    e=electrical_operator(120+0j,0j)
    assert e.impedance is None and not e.identifiable
