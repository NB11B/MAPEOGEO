from mapeogeo.invariant_queries import Invariant, InvariantQuery, resolve_invariant
from mapeogeo.power_control_routes import power_control_router
from mapeogeo.work_router import Outcome, WorkRouter, qualified_v01_edges


def base():
    return WorkRouter(qualified_v01_edges())


def test_magnitude_routes_differ_by_representation_without_common_materialization():
    v=resolve_invariant(base(),InvariantQuery(Invariant.MAGNITUDE,"vector"),available={"sensor.vector3"})
    p=resolve_invariant(base(),InvariantQuery(Invariant.MAGNITUDE,"power"),available={"power.voltage_current_magnitudes"})
    assert v.outcome==p.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in v.route.edges]==["imu.norm"]
    assert [e.edge_id for e in p.route.edges]==["power.apparent"]
    assert not v.route.materializes and not p.route.materializes


def test_stability_converges_on_same_target_from_different_sources():
    ps=resolve_invariant(base(),InvariantQuery(Invariant.STABILITY,"psmsl"),available={"psmsl.generator_g"})
    ctl=resolve_invariant(base(),InvariantQuery(Invariant.STABILITY,"control"),available={"control.state_matrix"})
    assert ps.target==ctl.target=="work.asymptotically_stable"
    assert [e.edge_id for e in ps.route.edges]==["control.generator-stability"]
    assert [e.edge_id for e in ctl.route.edges]==["control.eigs","control.spectral-abscissa","control.stability"]
    assert not ps.route.materializes
    assert ctl.route.materializes


def test_spectral_intent_materializes_only_where_mathematically_required():
    vib=resolve_invariant(base(),InvariantQuery(Invariant.SPECTRAL_CONTENT,"vibration"),available={"vibration.window"})
    power=resolve_invariant(base(),InvariantQuery(Invariant.SPECTRAL_CONTENT,"power"),available={"power.voltage_window"})
    assert vib.outcome==power.outcome==Outcome.EXECUTE
    assert vib.route.materializes and power.route.materializes


def test_alignment_uses_domain_specific_invariant():
    vec=resolve_invariant(base(),InvariantQuery(Invariant.ALIGNMENT,"vector"),available={"sensor.vector_pair3"})
    pwr=resolve_invariant(base(),InvariantQuery(Invariant.ALIGNMENT,"power"),available={"power.voltage_current_phasors"})
    assert [e.edge_id for e in vec.route.edges]==["imu.alignment"]
    assert [e.edge_id for e in pwr.route.edges]==["power.factor"]


def test_unsupported_invariant_fails_closed():
    d=resolve_invariant(base(),InvariantQuery(Invariant.AREA_CHANGE,"vector"),available={"sensor.vector3"})
    assert d.outcome==Outcome.UNRESOLVABLE
