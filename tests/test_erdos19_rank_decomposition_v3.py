from mapeogeo.erdos19_rank_decomposition import (
    greedy_linear_families,high_rank_pair_budget,incidence_degree,rank_partition,
)
from mapeogeo.erdos19_degeneracy_falsification import valid_linear_family


def test_rank_partition_separates_pair_and_high_edges():
    f=({0,1},{1,2},{0,2,3})
    p=rank_partition(f)
    assert len(p[2])==2 and len(p[3])==1


def test_high_edge_excludes_internal_pairs_by_linearity():
    # If {0,1,2} is present, none of {0,1},{0,2},{1,2} may coexist.
    fam=({0,1,2},{0,3},{1,3},{2,3})
    assert valid_linear_family(fam)
    b=high_rank_pair_budget(4,fam)
    assert next(iter(b.values()))==3


def test_generated_small_families_are_linear():
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            assert valid_linear_family(fam)


def test_incidence_degree_tracks_clique_load():
    assert incidence_degree(4,({0,1,2},{0,3},{1,3},{2,3}))==(2,2,2,3)
