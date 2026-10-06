from mapeogeo.erdos19_rank_decomposition import greedy_linear_families
from mapeogeo.erdos19_uow_loop_v5 import candidate_bound_holds,residual_is_colorable,best_high_coloring,global_delta_bound_holds


def test_strong_local_bound_is_falsified_but_residual_still_colors():
    failures=[];checked=0
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            checked+=1
            if not candidate_bound_holds(n,fam):failures.append((n,fam))
            assert residual_is_colorable(n,fam)
    assert checked>0
    assert failures, "expected strong local bound to be falsified"


def test_weaker_global_delta_bound_on_bounded_surface():
    failures=[]
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            if not global_delta_bound_holds(n,fam):failures.append((n,fam))
    assert failures, "expected global Delta bound to be falsified at n=6"


def test_saturated_rank3_example_falsifies_plus_one_but_meets_delta():
    fam=({0,1,2},{0,3},{1,3},{2,3})
    _,rows=best_high_coloring(4,fam)
    assert any(r["slack_max_plus_one"]<0 for r in rows)
    assert global_delta_bound_holds(4,fam)
