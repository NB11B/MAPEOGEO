from itertools import combinations
from mapeogeo.erdos19_pair_budget import high_rank_credit,pair_budget_valid,pair_consumption,pair_slack


def test_pair_family_saturates_pair_budget():
    n=5
    fam=tuple(combinations(range(n),2))
    assert pair_consumption(fam)==10
    assert pair_slack(n,fam)==0


def test_rank3_edge_consumes_three_pair_slots():
    fam=({0,1,2},{0,3},{1,3},{2,3})
    assert pair_consumption(fam)==6
    assert pair_slack(4,fam)==0
    assert high_rank_credit(fam)==2


def test_linear_family_budget_cannot_exceed_complete_pair_count():
    examples=[
      (4,({0,1,2},{0,3},{1,3},{2,3})),
      (5,({0,1,2},{0,3},{1,4},{2,4},{3,4})),
    ]
    assert all(pair_budget_valid(n,f) for n,f in examples)
