from mapeogeo.multidomain_routes import multidomain_router
from mapeogeo.work_router import Outcome, WorkRequest


def test_vector_norm_threshold_uses_invariant_route_not_rotation():
    d=multidomain_router().decide(
        WorkRequest("work.norm_above_threshold"),
        available={"sensor.vector3","work.norm_threshold"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["imu.norm","imu.threshold"]
    assert not d.route.materializes


def test_single_vector_pair_cannot_certify_full_rotation():
    d=multidomain_router().decide(
        WorkRequest("work.rotation_matrix"),
        available={"sensor.vector_pair3"},
    )
    assert d.outcome==Outcome.CERTIFY
    assert not d.route.certified


def test_vibration_rms_threshold_avoids_spectrum():
    d=multidomain_router().decide(
        WorkRequest("work.vibration_above_threshold"),
        available={"vibration.window","vibration.window_length","work.vibration_threshold"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["vib.energy","vib.rms","vib.rms-threshold"]
    assert not d.route.materializes


def test_frequency_query_requires_spectrum_materialization():
    d=multidomain_router().decide(
        WorkRequest("work.dominant_frequency", require_materialized=True),
        available={"vibration.window"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert d.route.materializes
    assert [e.edge_id for e in d.route.edges]==["vib.spectrum","vib.dominant-frequency"]


def test_missing_threshold_requests_observation_not_spectrum():
    d=multidomain_router().decide(
        WorkRequest("work.vibration_above_threshold"),
        available={"vibration.window","vibration.window_length"},
    )
    assert d.outcome==Outcome.OBSERVE
    assert d.missing==("work.vibration_threshold",)
