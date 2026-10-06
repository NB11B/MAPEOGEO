from mapeogeo.erdos19_edge_coloring_route import (
    round_robin_edge_coloring_complete_graph,verify_pair_family_coloring,
)


def test_pair_family_has_n_color_constructor_even_when_degeneracy_route_fails():
    for n in range(2,9):
        c=round_robin_edge_coloring_complete_graph(n)
        assert verify_pair_family_coloring(n,c)


def test_n4_uses_at_most_n_colors():
    c=round_robin_edge_coloring_complete_graph(4)
    assert max(c.values())<4
    assert len(set(c.values()))==3
