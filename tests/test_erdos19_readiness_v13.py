from mapeogeo.erdos19_readiness_v13 import audit
def test_readiness_is_structured():
    r=audit()
    assert isinstance(r.missing,tuple)
    assert r.ready==(len(r.missing)==0)
