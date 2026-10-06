from mapeogeo.erdos_frontier_probes import (
    collinear_triple_3d,distinct_distance_count,greedy_sidon,sidon_verified,
)


def test_problem_89_grid_finite_distance_probe():
    pts=[(0,0),(1,0),(0,1),(1,1)]
    assert distinct_distance_count(pts)==2


def test_problem_193_collinear_witness_probe():
    pts=[(0,0,0),(1,1,1),(2,2,2),(0,1,0)]
    assert collinear_triple_3d(pts)==(0,1,2)
    assert collinear_triple_3d([(0,0,0),(1,0,0),(0,1,0),(0,0,1)]) is None


def test_problem_340_greedy_sidon_prefix():
    seq=greedy_sidon(10)
    assert seq==(1,2,4,8,13,21,31,45,66,81)
    assert sidon_verified(seq)


def test_finite_probes_do_not_encode_open_problem_verdicts():
    # API returns measurements/witnesses only; no solved/proved boolean exists.
    assert isinstance(distinct_distance_count([(0,0),(1,0)]),int)
    assert greedy_sidon(3)==(1,2,4)
