import math
from mapeogeo.psmsl_operator_algebra_v1 import information_semantics,ordering_semantics,commutator,fuse

def test_projection_declares_information_loss():
    P=((1,0,0),(0,1,0))
    s=information_semantics(P)
    assert s.rank==2 and s.nullity==1 and s.information_loss
    assert s.surjective and not s.injective and not s.invertible

def test_rotation_is_information_preserving():
    R=((0,-1),(1,0))
    s=information_semantics(R)
    assert s.rank==2 and s.nullity==0 and s.invertible and not s.information_loss

def test_uniform_scale_commutes_with_rotation():
    S=((2,0),(0,2));R=((0,-1),(1,0))
    o=ordering_semantics(S,R)
    assert o.commutes and o.reorder_safe and o.parallel_candidate

def test_anisotropic_scale_does_not_commute_with_rotation():
    S=((2,0),(0,1));R=((0,-1),(1,0))
    o=ordering_semantics(S,R)
    assert not o.commutes and not o.reorder_safe
    assert o.commutator_norm>0

def test_fusion_preserves_declared_order():
    A=((2,0),(0,1));B=((0,-1),(1,0))
    assert fuse(A,B)==((0,-1),(2,0))
