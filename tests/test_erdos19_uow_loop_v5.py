from mapeogeo.erdos19_rank_decomposition import greedy_linear_families
from mapeogeo.erdos19_uow_loop_v5 import candidate_bound_holds,residual_is_colorable,best_high_coloring


def test_candidate_local_bound_on_bounded_generated_families():
    failures=[]
    checked=0
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            checked+=1
            if not candidate_bound_holds(n,fam):failures.append((n,fam))
    assert checked>0
    assert failures==[]


def test_residual_coloring_closes_on_same_surface():
    for n in range(3,7):
        for fam in greedy_linear_families(n,min(3,n)):
            assert residual_is_colorable(n,fam)


def test_saturated_rank3_example_has_nonnegative_best_slack():
    fam=({0,1,2},{0,3},{1,3},{2,3})
    _,rows=best_high_coloring(4,fam)
    assert all(r["slack_max_plus_one"]>=0 for r in rows)
