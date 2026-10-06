import gzip
import json
from pathlib import Path

from mapeogeo.contract_primitive_loader import (
    PrimitiveImplementation,
    load_primitives,
    router_from_contracts,
)
from mapeogeo.semantic_contracts_v03 import build_endpoint_overlay
from mapeogeo.work_router import Outcome, WorkRequest

ROOT=Path(__file__).resolve().parents[1]


def overlay():
    with gzip.open(ROOT/"data"/"gallier_quaintance_graph_v0_3.json.gz","rt",encoding="utf-8") as h:
        graph=json.load(h)
    results=json.loads((ROOT/"data"/"gallier_quaintance_results_v0_3.json").read_text())
    return build_endpoint_overlay(graph,results)


def test_verified_contract_plus_implementation_becomes_executable():
    impl=PrimitiveImplementation(
        "GFY.ORTHOGONAL_PROJECTION.v1",
        "eo.projection",
        "geo.nearest_point",
        "orthogonal projection",
        1.0,
        function=lambda p,x:p@x,
    )
    loaded=load_primitives(overlay(),[impl])
    assert loaded[0].executable
    assert loaded[0].edge.certified
    assert len(loaded[0].contract_digest)==64


def test_contract_without_implementation_fails_closed():
    impl=PrimitiveImplementation(
        "GFY.EIGENPAIR_RESIDUAL.v1",
        "eo.eigenpair",
        "geo.invariant_direction",
        "eigenpair semantics",
        1.0,
        function=None,
    )
    d=router_from_contracts(overlay(),[impl]).decide(
        WorkRequest("geo.invariant_direction"),
        available={"eo.eigenpair"},
    )
    assert d.outcome==Outcome.CERTIFY
    assert not d.route.certified


def test_implementation_without_verified_contract_fails_closed():
    impl=PrimitiveImplementation(
        "GFY.NOT_REGISTERED.v1",
        "a","b","unbound implementation",1.0,function=lambda x:x,
    )
    d=router_from_contracts(overlay(),[impl]).decide(WorkRequest("b"),available={"a"})
    assert d.outcome==Outcome.CERTIFY
    assert not d.route.certified


def test_so3_contract_auto_binds_registered_transform():
    impl=PrimitiveImplementation(
        "GFY.SO3_ROTATION.v1",
        "eo.rotation_matrix",
        "geo.rotation",
        "matrix to geometric rotation",
        1.0,
        function=lambda matrix:matrix,
    )
    d=router_from_contracts(overlay(),[impl]).decide(
        WorkRequest("geo.rotation"),
        available={"eo.rotation_matrix"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert d.route.edges[0].edge_id=="contract:GFY.SO3_ROTATION.v1"
