from __future__ import annotations

import json
from pathlib import Path
import pytest
import jsonschema

from mapeogeo.analysis.scope_comparator import TypedScopeRecord, compare_scopes
from scripts.correspondence_certificate import (
    CorrespondenceCertificate,
    generate_correspondence_certificate,
    verify_certificate_quorum,
)

ROOT = Path(__file__).resolve().parents[1]


def test_scope_comparator_exact_match():
    s1 = TypedScopeRecord(
        domain="SIMPLICIAL_COMPLEX",
        dimension="k",
        coefficient_ring="RAT",
        regularity="DISCRETE",
        orientation_convention="INDUCED_SIMPLEX_ORDER",
        boundary_convention="STANDARD_ALTERNATING_SUM",
        parameter_range="k >= 1",
        exceptional_cases="k = 0 has zero boundary",
    )
    s2 = TypedScopeRecord(
        domain="SIMPLICIAL_COMPLEX",
        dimension="k",
        coefficient_ring="RAT",
        regularity="DISCRETE",
        orientation_convention="INDUCED_SIMPLEX_ORDER",
        boundary_convention="STANDARD_ALTERNATING_SUM",
        parameter_range="k >= 1",
        exceptional_cases="k = 0 has zero boundary",
    )
    result = compare_scopes(s1, s2)
    assert result.is_compatible
    assert len(result.mismatches) == 0


def test_scope_comparator_mismatch():
    s1 = TypedScopeRecord(
        domain="SIMPLICIAL_COMPLEX",
        dimension="k",
        coefficient_ring="RAT",
        regularity="DISCRETE",
        orientation_convention="INDUCED_SIMPLEX_ORDER",
        boundary_convention="STANDARD_ALTERNATING_SUM",
        parameter_range="k >= 1",
        exceptional_cases="k = 0 has zero boundary",
    )
    s2 = TypedScopeRecord(
        domain="SMOOTH_MANIFOLD",
        dimension="n",
        coefficient_ring="REAL",
        regularity="C_INFINITY",
        orientation_convention="POSITIVE_VOLUME_FORM",
        boundary_convention="STOKES_BOUNDARY",
        parameter_range="n >= 1",
        exceptional_cases="NONE",
    )
    result = compare_scopes(s1, s2)
    assert not result.is_compatible
    assert "domain" in result.mismatches
    assert "coefficient_ring" in result.mismatches


def test_quorum_rule_requires_two_independent_witnesses():
    scope = TypedScopeRecord(
        domain="SIMPLICIAL_COMPLEX",
        dimension="k",
        coefficient_ring="RAT",
        regularity="DISCRETE",
        orientation_convention="INDUCED_SIMPLEX_ORDER",
        boundary_convention="STANDARD_ALTERNATING_SUM",
        parameter_range="k >= 1",
        exceptional_cases="k = 0 has zero boundary",
    )
    # Case 1: 2 independent views (EO with hash1, GEO with hash2) -> CERTIFIED
    cert = generate_correspondence_certificate(
        certificate_id="cert:test:valid",
        target_concept="stokes_duality",
        relationship="SCOPED_OVERLAP",
        scope=scope,
        eo_slot={"status": "WITNESSED", "statement_sha256": "1" * 64, "view_ref": "ref_eo"},
        geo_slot={"status": "WITNESSED", "statement_sha256": "2" * 64, "view_ref": "ref_geo"},
        pct_slot={"status": "ABSENT"},
        formal_slot={"status": "ABSENT"},
    )
    assert cert.verification_status == "CERTIFIED"
    assert cert.quorum_count == 2


def test_quorum_rejects_identical_digests_and_unverified_formal():
    scope = TypedScopeRecord(
        domain="SIMPLICIAL_COMPLEX",
        dimension="k",
        coefficient_ring="RAT",
        regularity="DISCRETE",
        orientation_convention="INDUCED_SIMPLEX_ORDER",
        boundary_convention="STANDARD_ALTERNATING_SUM",
        parameter_range="k >= 1",
        exceptional_cases="k = 0 has zero boundary",
    )
    # Case 2: Identical digest / alias across EO and GEO -> Fails independent quorum (counts as 1 witness)
    cert_duplicate = generate_correspondence_certificate(
        certificate_id="cert:test:dup",
        target_concept="stokes_duality",
        relationship="SCOPED_OVERLAP",
        scope=scope,
        eo_slot={"status": "WITNESSED", "statement_sha256": "1" * 64, "view_ref": "ref_eo"},
        geo_slot={"status": "WITNESSED", "statement_sha256": "1" * 64, "view_ref": "ref_eo_alias"},
        pct_slot={"status": "ABSENT"},
        formal_slot={"status": "ABSENT"},
    )
    assert cert_duplicate.verification_status == "INSUFFICIENT_QUORUM"
    assert cert_duplicate.quorum_count == 1

    # Case 3: Formal linked but NOT kernel verified -> does NOT count towards quorum
    cert_unverified_formal = generate_correspondence_certificate(
        certificate_id="cert:test:unverified",
        target_concept="stokes_duality",
        relationship="SCOPED_OVERLAP",
        scope=scope,
        eo_slot={"status": "WITNESSED", "statement_sha256": "1" * 64, "view_ref": "ref_eo"},
        geo_slot={"status": "ABSENT"},
        pct_slot={"status": "ABSENT"},
        formal_slot={"status": "REPRESENTED", "kernel_verified": False, "view_ref": "unverified_lean"},
    )
    assert cert_unverified_formal.verification_status == "INSUFFICIENT_QUORUM"
    assert cert_unverified_formal.quorum_count == 1


def test_correspondence_certificate_file_schema_valid():
    cert_file = ROOT / "formal" / "correspondence_certificates_v0_21.json"
    if cert_file.is_file():
        schema = json.loads((ROOT / "schema" / "mapeogeo-certificate.schema.json").read_text(encoding="utf-8"))
        data = json.loads(cert_file.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)
