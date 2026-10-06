from mapeogeo.derived_routes import primitive_router
from mapeogeo.work_router import Outcome, WorkRequest


def test_derives_vector_norm_from_primitives():
    d=primitive_router().decide(WorkRequest("work.vector_norm"),available={"sensor.vector3"})
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==[
        "prim.vector.dot-self","prim.sqrt.norm","prim.norm.alias"
    ]


def test_derives_general_stability_and_rejects_short_uncertified_trap():
    d=primitive_router().decide(WorkRequest("work.asymptotically_stable"),available={"control.state_matrix"})
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==[
        "prim.eigenvalues","prim.realparts","prim.max","prim.spectral.stability"
    ]
    assert d.route.certified


def test_same_stability_target_discovers_shorter_psmsl_route():
    d=primitive_router().decide(WorkRequest("work.asymptotically_stable"),available={"psmsl.generator_g"})
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==[
        "prim.generator.realpart","prim.spectral.stability"
    ]
    assert not d.route.materializes


def test_derives_area_without_phi_or_matrix_materialization():
    d=primitive_router().decide(WorkRequest("work.area_expanding"),available={"psmsl.directional_scales"})
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["prim.scale.sum","prim.logarea.sign"]
    assert not d.route.materializes


def test_derives_spectral_route_when_required():
    d=primitive_router().decide(WorkRequest("work.dominant_frequency"),available={"vibration.window"})
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["prim.vibration.fft","prim.spectrum.argmax"]
    assert d.route.materializes


def test_uncertified_only_route_returns_certify():
    d=primitive_router().decide(WorkRequest("work.voltage_thd"),available={"work.voltage_rms"})
    assert d.outcome==Outcome.CERTIFY
    assert [e.edge_id for e in d.route.edges]==["trap.rms.thd"]


def test_missing_threshold_is_observe_on_derived_norm_route():
    d=primitive_router().decide(WorkRequest("work.norm_above_threshold"),available={"sensor.vector3"})
    assert d.outcome==Outcome.OBSERVE
    assert d.missing==("work.norm_threshold",)
