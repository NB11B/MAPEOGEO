from mapeogeo.erdos19_partial_feasibility_v11 import partial_feasible13

def test_pair_reuse_prunes_soundly():
    r=partial_feasible13(({0,1,2},{0,1,3}))
    assert not r.feasible and r.reason=="PAIR_REUSED"

def test_too_many_lines_prunes_soundly():
    lines=tuple({i%13,(i+1)%13} for i in range(55))
    r=partial_feasible13(lines)
    assert not r.feasible

def test_empty_partial_remains_possible():
    assert partial_feasible13(()).feasible
