from mapeogeo.erdos19_frontier13_v5 import LINES_33,exact_edge_coloring,verify_edge_coloring,verify_linear_space


def test_public_m33_seed_is_13_point_linear_space():
    assert len(LINES_33)==33
    assert verify_linear_space(13,LINES_33)


def test_exact_constructor_colors_public_frontier_witness():
    c=exact_edge_coloring(13,LINES_33)
    assert verify_edge_coloring(13,LINES_33,c)
    assert max(c)<13
