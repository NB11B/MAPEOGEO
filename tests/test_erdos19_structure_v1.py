from mapeogeo.erdos19_constructor import EFLInstance,valid_shared_coloring
from mapeogeo.erdos19_structure import conflict_graph,degeneracy_coloring,greedy_degeneracy_order


def test_conflict_graph_triangle_example():
    inst=EFLInstance(3,(
        frozenset({"ab","ac","a"}),
        frozenset({"ab","bc","b"}),
        frozenset({"ac","bc","c"}),
    ))
    g=conflict_graph(inst)
    assert all(len(g[v])==2 for v in g)
    c,d=degeneracy_coloring(inst)
    assert d==2
    assert valid_shared_coloring(inst,c)


def test_common_vertex_conflict_graph_is_isolated():
    inst=EFLInstance(4,(
        frozenset({"x","a1","a2","a3"}),frozenset({"x","b1","b2","b3"}),
        frozenset({"x","c1","c2","c3"}),frozenset({"x","d1","d2","d3"}),
    ))
    c,d=degeneracy_coloring(inst)
    assert d==0
    assert valid_shared_coloring(inst,c)


def test_degeneracy_route_is_conditional_not_universal_claim():
    # API explicitly returns degeneracy so caller must verify d<n.
    inst=EFLInstance(2,(frozenset({"x","a"}),frozenset({"x","b"})))
    c,d=degeneracy_coloring(inst)
    assert d < inst.n
    assert valid_shared_coloring(inst,c)
