from mapeogeo.erdos19_future_core_v12 import future_core_bounds

def test_empty_core_is_possible():
    assert future_core_bounds((),()).feasible

def test_invalid_core_index_rejected():
    r=future_core_bounds(({0,1},),(1,))
    assert not r.feasible

def test_bound_is_upper_not_current_degree():
    lines=({0,1,2},{0,3})
    r=future_core_bounds(lines,(0,))
    assert r.feasible
    assert r.max_possible_core_degree[0]>=13
