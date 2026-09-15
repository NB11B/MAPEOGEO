"""Unit tests for PCT models and contracts."""

from __future__ import annotations

from mapeogeo.pct.contracts import make_verdict, require_applicable
from mapeogeo.pct.models import (
    Applicability,
    ChainMap,
    CoefficientField,
    EquivalenceContract,
    FiniteComplex,
    ProbeState,
    Simplex,
    Verdict,
    VerdictRecord,
)


def test_contract_enums_are_stable_strings():
    assert CoefficientField.GF2.value == "GF2"
    assert CoefficientField.Q.value == "Q"
    assert Verdict.NOT_APPLICABLE.value == "NOT_APPLICABLE"
    assert Verdict.PASS.value == "PASS"
    assert Verdict.FAIL.value == "FAIL"
    assert Verdict.INVALID.value == "INVALID"
    assert Verdict.ERROR.value == "ERROR"
    assert Verdict.INCONCLUSIVE.value == "INCONCLUSIVE"
    assert EquivalenceContract.EXACT.value == "EXACT"
    assert EquivalenceContract.SUBDIVISION.value == "SUBDIVISION"
    assert EquivalenceContract.RELABELING.value == "RELABELING"
    assert EquivalenceContract.RIGID_MOTION_2D.value == "RIGID_MOTION_2D"
    assert EquivalenceContract.RIGID_MOTION_AND_SCALE_2D.value == "RIGID_MOTION_AND_SCALE_2D"
    assert EquivalenceContract.HOMEOMORPHISM_CONTROL.value == "HOMEOMORPHISM_CONTROL"
    assert EquivalenceContract.CHAIN_HOMOTOPY_CONTROL.value == "CHAIN_HOMOTOPY_CONTROL"
    assert Applicability.APPLICABLE.value == "APPLICABLE"
    assert Applicability.NOT_APPLICABLE.value == "NOT_APPLICABLE"


def test_simplex_is_canonical_and_oriented():
    s = Simplex(vertices=(2, 0, 1))
    assert s.vertices == (2, 0, 1)
    assert s.dimension == 2


def test_probe_state_serializes_scientific_parameters():
    p = ProbeState(
        probe_id="probe:theta0:p0",
        probe_family="LINE_EULER",
        parameters={"theta": 0.0, "offset": 0.0},
        scale=0.0,
        observation_operator="INTERSECTION",
        coefficient_backend=CoefficientField.GF2,
        applicability_contract="PLANAR_TAME_GEOMETRY",
    )
    assert p.parameters["theta"] == 0.0
    assert p.probe_family == "LINE_EULER"


def test_non_applicable_never_becomes_pass():
    r = require_applicable("tube", False, provenance={"fixture": "reentrant"})
    assert r.verdict is Verdict.NOT_APPLICABLE
    assert r.applicability is Applicability.NOT_APPLICABLE


def test_make_verdict_constructs_record():
    r = make_verdict(
        check_id="check1",
        applicability=Applicability.APPLICABLE,
        verdict=Verdict.PASS,
        measured=0,
        expected=0,
        tolerance_or_exact_rule="EXACT_EQUALITY",
    )
    assert r.check_id == "check1"
    assert r.verdict == Verdict.PASS
    assert r.applicability == Applicability.APPLICABLE
