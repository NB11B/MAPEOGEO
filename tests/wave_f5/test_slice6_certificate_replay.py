"""Slice 6 Tests: Certificate Replay, Lineage, Scope Verification & Quorum Integration."""

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path

from mapeogeo.wave_f5.certificates import (
    validate_certificate,
    validate_joint,
    compute_quorum,
    WaveF5CertificateVerifier,
    REGISTERED_JOINT_TYPES,
)
from mapeogeo.wave_f5.scopes import TypedScopeRecord, ScopeComparisonOutcome

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schema"
CERT_SCHEMA_PATH = SCHEMA_DIR / "wave-f5-certificate.schema.json"


@pytest.fixture
def cert_schema():
    with open(CERT_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_scope():
    return {
        "domain": "function_space:C([0,1/4])",
        "dimension": "infinite",
        "coefficient_ring": "real",
        "regularity": "C1",
        "orientation_convention": "standard",
        "boundary_convention": "initial_point",
        "parameter_range": "t_in_[0,1/4]",
        "exceptional_cases": "none",
    }


def test_schema_wave_f5_certificate_valid(cert_schema, sample_scope):
    valid_doc = {
        "schema_version": "0.22",
        "certificates": [
            {
                "certificate_id": "cert:f5:picard_contract_01",
                "target_concept": "canonical:fa:banach_contraction_theorem",
                "relationship": "CONTRACTION_OF",
                "scope": sample_scope,
                "evidence_kind": "EXACT_RATIONAL",
                "view_slots": {
                    "eo": {
                        "status": "VERIFIED",
                        "view_ref": "view:eo:picard_operator_step",
                        "producer_id": "producer:eo:rational_contract_engine_v1",
                        "statement_sha256": "a" * 64,
                        "execution_digest": "b" * 64,
                        "witness_payload": {"q": "1/4", "ball_radius": "1/2", "hM": "3/8"},
                    },
                    "geo": {
                        "status": "VERIFIED",
                        "view_ref": "view:geo:picard_interval_flow",
                        "producer_id": "producer:geo:symbolic_algebra_v2",
                        "statement_sha256": "a" * 64,
                        "execution_digest": "c" * 64,
                        "witness_payload": {"contraction_factor": "1/4", "invariance_margin": "1/8"},
                    },
                    "pct": {
                        "status": "ABSENT",
                        "notes": "PCT chain complex not applicable for scalar contraction metric",
                    },
                    "formal": {
                        "status": "ABSENT",
                        "notes": "Formal general proof tracked under Lean 4 mathlib milestone",
                    },
                },
                "quorum_count": 2,
                "verification_status": "CERTIFIED",
            }
        ],
    }
    validate(instance=valid_doc, schema=cert_schema)


def test_reject_auto_promotion_identity(cert_schema, sample_scope):
    invalid_doc = {
        "schema_version": "0.22",
        "certificates": [
            {
                "certificate_id": "cert:f5:invalid_identity",
                "target_concept": "canonical:fa:banach_contraction_theorem",
                "relationship": "SAME_SEMANTICS",
                "scope": sample_scope,
                "evidence_kind": "EXACT_RATIONAL",
                "view_slots": {
                    "eo": {"status": "ABSENT"},
                    "geo": {"status": "ABSENT"},
                    "pct": {"status": "ABSENT"},
                    "formal": {"status": "ABSENT"},
                },
                "quorum_count": 0,
                "verification_status": "REJECTED",
            }
        ],
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_doc, schema=cert_schema)


def test_reject_fake_formal_boolean(sample_scope):
    """A formal slot with kernel_verified: True but no formal build/axiom receipt is rejected."""
    cert = {
        "certificate_id": "cert:f5:fake_formal",
        "target_concept": "canonical:fa:banach_contraction_theorem",
        "relationship": "CONTRACTION_OF",
        "scope": sample_scope,
        "evidence_kind": "FORMAL_GENERAL",
        "view_slots": {
            "eo": {"status": "ABSENT"},
            "geo": {"status": "ABSENT"},
            "pct": {"status": "ABSENT"},
            "formal": {
                "status": "VERIFIED",
                "view_ref": "view:formal:lean_fake",
                "kernel_verified": True,
            },
        },
        "verification_status": "CERTIFIED",
    }
    verifier = WaveF5CertificateVerifier(active_concepts={"canonical:fa:banach_contraction_theorem"})
    result = verifier.verify_certificate(cert)
    assert result["verification_status"] != "CERTIFIED"
    assert "missing formal build/axiom receipt" in result.get("rejection_reason", "").lower() or result["computed_quorum"] == 0


def test_reject_aliased_witness_quorum(sample_scope):
    """Identical execution digest / witness payload from the same producer cannot claim independent quorum."""
    cert = {
        "certificate_id": "cert:f5:aliased_quorum",
        "target_concept": "canonical:fa:banach_contraction_theorem",
        "relationship": "CONTRACTION_OF",
        "scope": sample_scope,
        "evidence_kind": "EXACT_RATIONAL",
        "view_slots": {
            "eo": {
                "status": "VERIFIED",
                "view_ref": "view:eo:shared",
                "producer_id": "producer:shared_table_v1",
                "statement_sha256": "a" * 64,
                "execution_digest": "e" * 64,
                "witness_payload": {"val": 42},
            },
            "geo": {
                "status": "VERIFIED",
                "view_ref": "view:geo:shared",
                "producer_id": "producer:shared_table_v1",
                "statement_sha256": "a" * 64,
                "execution_digest": "e" * 64,
                "witness_payload": {"val": 42},
            },
            "pct": {"status": "ABSENT"},
            "formal": {"status": "ABSENT"},
        },
        "verification_status": "CERTIFIED",
    }
    verifier = WaveF5CertificateVerifier(active_concepts={"canonical:fa:banach_contraction_theorem"})
    result = verifier.verify_certificate(cert)
    assert result["computed_quorum"] < 2
    assert result["verification_status"] != "CERTIFIED"


def test_compute_quorum_independent_views(sample_scope):
    """Independent EO and GEO witnesses yield computed quorum 2 -> CERTIFIED."""
    cert = {
        "certificate_id": "cert:f5:picard_valid",
        "target_concept": "canonical:fa:banach_contraction_theorem",
        "relationship": "CONTRACTION_OF",
        "scope": sample_scope,
        "evidence_kind": "EXACT_RATIONAL",
        "view_slots": {
            "eo": {
                "status": "VERIFIED",
                "view_ref": "view:eo:picard_step",
                "producer_id": "producer:eo:picard_engine",
                "statement_sha256": "a" * 64,
                "execution_digest": "1" * 64,
                "witness_payload": {"step": "picard", "q": 0.25},
            },
            "geo": {
                "status": "VERIFIED",
                "view_ref": "view:geo:ball_flow",
                "producer_id": "producer:geo:flow_engine",
                "statement_sha256": "a" * 64,
                "execution_digest": "2" * 64,
                "witness_payload": {"ball_invariance": True},
            },
            "pct": {"status": "ABSENT"},
            "formal": {"status": "ABSENT"},
        },
        "verification_status": "CERTIFIED",
    }
    verifier = WaveF5CertificateVerifier(active_concepts={"canonical:fa:banach_contraction_theorem"})
    result = verifier.verify_certificate(cert)
    assert result["computed_quorum"] == 2
    assert result["verification_status"] == "CERTIFIED"


def test_validate_new_mechanism_joint_types():
    assert "OPERATOR_ACTION" in REGISTERED_JOINT_TYPES
    assert "FIXED_POINT_CONSTRUCTION" in REGISTERED_JOINT_TYPES
    assert "EVOLUTION_FLOW" in REGISTERED_JOINT_TYPES
    assert "LINEARIZATION" in REGISTERED_JOINT_TYPES
    assert "CONTINUOUS_DEPENDENCE" in REGISTERED_JOINT_TYPES


def test_reject_rotation_as_gradient_flow():
    joint = {
        "joint_id": "joint:f5:harmonic_oscillator_flow",
        "joint_type": "GRADIENT_FLOW",
        "relationship": "ACTS_ON",
        "feet": [
            {"node_id": "canonical:ode:harmonic_oscillator", "role": "system"},
            {"node_id": "canonical:geometry:planar_rotations", "role": "flow"},
        ],
        "metadata": {"system_type": "conservative_hamiltonian_rotation"},
    }
    result = validate_joint(joint, active_concepts={"canonical:ode:harmonic_oscillator", "canonical:geometry:planar_rotations"})
    assert result["valid"] is False
    assert "rotation cannot be typed as gradient_flow" in result["error"].lower()
