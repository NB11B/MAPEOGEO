import gzip
import json
import math
from pathlib import Path

from mapeogeo.contract_primitive_loader import load_primitives, router_from_contracts
from mapeogeo.semantic_contracts_v03 import build_endpoint_overlay
from mapeogeo.v03_implementation_registry import (
    cyclic_compose,eigenpair_residual,gaussian_gram,graph_laplacian,
    orthogonal_project,projective_normalize,so3_apply,strong_duality_gap,
    v03_implementation_registry,
)
from mapeogeo.work_router import Outcome, WorkRequest

ROOT=Path(__file__).resolve().parents[1]


def overlay():
    with gzip.open(ROOT/"data"/"gallier_quaintance_graph_v0_3.json.gz","rt",encoding="utf-8") as h:
        graph=json.load(h)
    results=json.loads((ROOT/"data"/"gallier_quaintance_results_v0_3.json").read_text())
    return build_endpoint_overlay(graph,results)


def test_all_eight_frozen_contracts_auto_bind():
    loaded=load_primitives(overlay(),v03_implementation_registry())
    assert len(loaded)==8
    assert all(x.executable and x.edge.certified and len(x.contract_digest)==64 for x in loaded)


def test_registry_primitives_execute_expected_fixture_semantics():
    assert cyclic_compose({"val_a":5,"val_b":11,"modulus":17})==4
    assert so3_apply([[0,-1,0],[1,0,0],[0,0,1]],[1,0,0])==(0.0,1.0,0.0)
    assert eigenpair_residual([[2,1],[1,2]],3,[1,1])<1e-12
    assert graph_laplacian([[0,1],[1,0]])==((1.0,-1.0),(-1.0,1.0))
    assert projective_normalize([5,10,15])==(1/3,2/3,1.0)
    assert strong_duality_gap(3.0,3.0)==0.0
    assert orthogonal_project([[.5,.5],[.5,.5]],[3,1])==(2.0,2.0)
    g=gaussian_gram([[0,0],[1,0]],1.0)
    assert math.isclose(g[0][1],math.exp(-.5),rel_tol=1e-12)


def test_auto_loaded_router_exposes_all_eight_targets():
    r=router_from_contracts(overlay(),v03_implementation_registry())
    for impl in v03_implementation_registry():
        d=r.decide(WorkRequest(impl.target),available={impl.source})
        assert d.outcome==Outcome.EXECUTE
        assert d.route.certified
        assert d.route.edges[0].edge_id==f"contract:{impl.semantic_id}"
