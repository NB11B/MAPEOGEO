from mapeogeo.erdos19_finite_class_closure_v7 import close_finite_class


def test_finite_class_closes_when_coverage_and_coloring_both_verify():
    # Both are pair-covering linear spaces on 3 points; first two are isomorphic.
    raw=[
      ({0,1},{0,2},{1,2}),
      ({1,2},{1,0},{2,0}),
      ({0,1,2},),
    ]
    r=close_finite_class(3,raw)
    assert r.raw_count==3
    assert r.representative_count==2
    assert r.raw_coverage_verified
    assert r.all_representatives_colored
    assert r.state=="FINITE_CLASS_CLOSED"
