from mapeogeo.latent_generator_v1 import linear_inverse
from mapeogeo.latent_generator_qualification_v1 import qualify_linear

def test_qualification_preserves_nullity_and_source_boundary():
    P=((1,0,0),(0,1,0));y=(1,2)
    r=linear_inverse(P,y)
    q=qualify_linear(P,y,r)
    assert q.passed and q.nullity==1 and not q.overidentified_source
