from mapeogeo.erdos19_rank_decomposition import greedy_linear_families
from mapeogeo.erdos19_residual_list_coloring import verify_coloring
from mapeogeo.erdos19_factor_replacement_v5 import replacement_coloring,replacement_coloring_over_relabelings


def test_fixed_factorization_is_falsified():
    failures=[]
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            c=replacement_coloring(n,fam)
            if c is None or not verify_coloring(n,fam,c):failures.append((n,fam))
    assert failures


def test_relabeling_factorization_on_bounded_rank3_surface():
    failures=[];checked=0
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            checked+=1
            c=replacement_coloring_over_relabelings(n,fam)
            if c is None or not verify_coloring(n,fam,c):failures.append((n,fam))
    assert checked>0
    assert failures, "expected relabeling-only factorization route to fail on n=6 families"
