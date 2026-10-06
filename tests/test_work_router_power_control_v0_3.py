import cmath
import math

from mapeogeo.power_control_routes import power_control_router
from mapeogeo.work_router import Outcome, WorkRequest


def test_real_power_routes_through_complex_power_without_waveform():
    d=power_control_router().decide(
        WorkRequest("work.real_power"),
        available={"power.voltage_current_phasors"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["power.complex","power.real"]
    assert not d.route.materializes


def test_apparent_power_needs_only_magnitudes():
    d=power_control_router().decide(
        WorkRequest("work.apparent_power"),
        available={"power.voltage_current_magnitudes"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["power.apparent"]


def test_rms_cannot_certify_thd():
    d=power_control_router().decide(
        WorkRequest("work.voltage_thd"),
        available={"work.voltage_rms"},
    )
    assert d.outcome==Outcome.CERTIFY
    assert not d.route.certified


def test_thd_from_waveform_requires_spectrum_materialization():
    d=power_control_router().decide(
        WorkRequest("work.voltage_thd", require_materialized=True),
        available={"power.voltage_window"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert d.route.materializes
    assert [e.edge_id for e in d.route.edges]==["power.thd.spectrum","power.thd"]


def test_generator_stability_avoids_eigensolver():
    d=power_control_router().decide(
        WorkRequest("work.asymptotically_stable"),
        available={"psmsl.generator_g"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==["control.generator-stability"]
    assert not d.route.materializes


def test_general_state_matrix_stability_routes_through_eigenvalues():
    d=power_control_router().decide(
        WorkRequest("work.asymptotically_stable"),
        available={"control.state_matrix"},
    )
    assert d.outcome==Outcome.EXECUTE
    assert [e.edge_id for e in d.route.edges]==[
        "control.eigs","control.spectral-abscissa","control.stability"
    ]
    assert d.route.materializes


def test_trajectory_requires_initial_state():
    d=power_control_router().decide(
        WorkRequest("work.time_trajectory"),
        available={"control.state_matrix"},
    )
    assert d.outcome==Outcome.OBSERVE
    assert d.missing==("control.initial_state",)


def test_phasor_identity_matches_direct_power():
    v=120*cmath.exp(1j*math.radians(10))
    i=5*cmath.exp(1j*math.radians(-20))
    s=v*i.conjugate()
    assert math.isclose(s.real,120*5*math.cos(math.radians(30)),rel_tol=1e-12)
    assert math.isclose(s.imag,120*5*math.sin(math.radians(30)),rel_tol=1e-12)
