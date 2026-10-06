from mapeogeo.execution_contracts_v0_9 import ExecutionContract, ToleranceRouter
from mapeogeo.work_router import RouteEdge


def router():
    edges=[
        RouteEdge("cheap.a","x","mid",1.0,True,"cheap approximation"),
        RouteEdge("cheap.b","mid","answer",1.0,True,"cheap approximation"),
        RouteEdge("accurate","x","answer",8.0,True,"accurate direct"),
        RouteEdge("invalid","x","answer",0.1,True,"domain-limited"),
        RouteEdge("unsafe","x","answer",0.01,False,"uncertified"),
    ]
    contracts=[
        ExecutionContract("cheap.a",0.03),
        ExecutionContract("cheap.b",0.03),
        ExecutionContract("accurate",0.005),
        ExecutionContract("invalid",0.0,lambda c:c.get("allow_invalid_domain",False)),
        ExecutionContract("unsafe",0.0),
    ]
    return ToleranceRouter(edges,contracts)


def test_loose_tolerance_selects_cheapest_valid_route():
    q=router().shortest_qualified({"x"},"answer",context={},tolerance=.1)
    assert [e.edge_id for e in q.route.edges]==["cheap.a","cheap.b"]
    assert q.composed_error==.06
    assert q.route.cost==2.0


def test_tight_tolerance_selects_expensive_accurate_route():
    q=router().shortest_qualified({"x"},"answer",context={},tolerance=.01)
    assert [e.edge_id for e in q.route.edges]==["accurate"]
    assert q.composed_error==.005


def test_impossible_tolerance_returns_none():
    assert router().shortest_qualified({"x"},"answer",context={},tolerance=.001) is None


def test_invalid_domain_route_is_excluded_even_if_cheapest():
    q=router().shortest_qualified({"x"},"answer",context={},tolerance=.1)
    assert "invalid" not in [e.edge_id for e in q.route.edges]


def test_domain_route_becomes_eligible_when_context_satisfies_contract():
    q=router().shortest_qualified({"x"},"answer",context={"allow_invalid_domain":True},tolerance=.1)
    assert [e.edge_id for e in q.route.edges]==["invalid"]


def test_uncertified_route_never_executes_even_with_zero_error():
    q=router().shortest_qualified({"x"},"answer",context={},tolerance=0.0)
    assert q is None
