import math

from mapeogeo.composed_work_v0_8 import (
    composition_router,execute_graph_connectivity,execute_kernel_spectral_radius,
    graph_laplacian,gaussian_gram,symmetric_eigenvalues_2x2,
)
from mapeogeo.work_router import Outcome, WorkRequest


def test_router_discovers_unregistered_graph_connectivity_route():
    d=composition_router().decide(
        WorkRequest("work.algebraic_connectivity"),
        available={"geo.graph_adjacency"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["auto.graph-laplacian","prim.laplacian.lambda2"]


def test_connected_vs_disconnected_graph_useful_answer():
    connected=[[0,1],[1,0]]
    disconnected=[[0,0],[0,0]]
    assert math.isclose(execute_graph_connectivity(connected),2.0,abs_tol=1e-12)
    assert math.isclose(execute_graph_connectivity(disconnected),0.0,abs_tol=1e-12)


def test_graph_composition_matches_direct_eigen_calculation():
    a=[[0,2],[2,0]]
    L=graph_laplacian(a)
    direct=symmetric_eigenvalues_2x2(L)[1]
    assert math.isclose(execute_graph_connectivity(a),direct,rel_tol=1e-12)


def test_router_discovers_unregistered_kernel_spectral_route():
    d=composition_router().decide(
        WorkRequest("work.kernel_spectral_radius"),
        available={"geo.point_cloud_sigma"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["auto.gaussian-gram","prim.gram.spectral-radius"]


def test_kernel_composition_matches_direct_closed_form():
    pts=[[0,0],[1,0]]
    rho=execute_kernel_spectral_radius(pts,1.0)
    k=math.exp(-0.5)
    # eigenvalues of [[1,k],[k,1]] are 1-k,1+k
    assert math.isclose(rho,1+k,rel_tol=1e-12)
