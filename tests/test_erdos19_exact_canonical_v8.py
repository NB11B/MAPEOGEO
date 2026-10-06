from mapeogeo.erdos19_exact_canonical_v8 import exact_canonical_digest


def test_exact_canonical_collapses_symmetric_relabelings():
    a=({0,1},{0,2},{1,2})
    b=({1,2},{1,0},{2,0})
    da,_=exact_canonical_digest(3,a)
    db,_=exact_canonical_digest(3,b)
    assert da==db


def test_exact_canonical_separates_nonisomorphic_spaces():
    a=({0,1},{0,2},{1,2})
    b=({0,1,2},)
    assert exact_canonical_digest(3,a)[0]!=exact_canonical_digest(3,b)[0]


def test_state_limit_fails_closed():
    try:
        exact_canonical_digest(5,tuple({i,j} for i in range(5) for j in range(i+1,5)),max_states=1)
    except RuntimeError as e:
        assert str(e)=="CANONICAL_STATE_LIMIT"
    else:
        raise AssertionError("expected bounded canonicalizer to fail closed")
