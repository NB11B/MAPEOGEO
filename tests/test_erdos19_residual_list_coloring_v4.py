from mapeogeo.erdos19_rank_decomposition import greedy_linear_families
from mapeogeo.erdos19_residual_list_coloring import decompose_color,verify_coloring


def test_exhaustive_high_first_decomposition_on_generated_rank3_families():
    checked=0
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            c=decompose_color(n,fam,exhaustive_high=True)
            assert c is not None, (n,fam)
            assert verify_coloring(n,fam,c)
            checked+=1
    assert checked>0


def test_saturated_rank3_plus_pairs_example():
    fam=({0,1,2},{0,3},{1,3},{2,3})
    c=decompose_color(4,fam,exhaustive_high=True)
    assert verify_coloring(4,fam,c)


def test_pair_only_family_still_routes_through_residual_solver():
    fam=tuple({i,j} for i in range(5) for j in range(i+1,5))
    c=decompose_color(5,fam,exhaustive_high=True)
    assert verify_coloring(5,fam,c)
