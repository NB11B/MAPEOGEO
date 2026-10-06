from mapeogeo.erdos19_functional_backends_v13 import PynautyCanonicalAdapter,CadicalColoringAdapter
def test_functional_adapters_fail_closed_or_verify():
    c=PynautyCanonicalAdapter().canonicalize(3,({0,1},{0,2},{1,2}))
    assert c.verified or c.digest==""
    s=CadicalColoringAdapter().solve(3,({0,1},{0,2},{1,2}))
    assert (s.status=="SAT" and s.verified) or s.status=="ERROR"
