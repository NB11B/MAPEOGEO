from mapeogeo.erdos19_coloring_cnf_v13 import coloring_cnf,assignment_to_colors,var
from mapeogeo.erdos19_frontier13_v5 import LINES_33,exact_edge_coloring,verify_edge_coloring

def test_cnf_witness_roundtrip_on_frontier_seed():
    colors=exact_edge_coloring(13,LINES_33)
    assignment=[]
    for i,c in enumerate(colors):
        for k in range(13):assignment.append(var(i,k,13) if k==c else -var(i,k,13))
    decoded=assignment_to_colors(13,LINES_33,assignment)
    assert decoded==colors and verify_edge_coloring(13,LINES_33,decoded)
    nv,clauses=coloring_cnf(13,LINES_33)
    assert nv==33*13 and clauses
