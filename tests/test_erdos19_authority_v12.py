from mapeogeo.erdos19_authority_v12 import AuthorityDependency,n13_authority_closed,REQUIRED_IDS
def test_authority_fails_closed():
    assert not n13_authority_closed([])
def test_all_named_artifacts_close_authority():
    assert n13_authority_closed([AuthorityDependency(i,i,True,"d"*64) for i in REQUIRED_IDS])
