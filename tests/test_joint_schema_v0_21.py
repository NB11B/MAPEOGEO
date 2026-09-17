from __future__ import annotations

import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[1]

VALID_JOINT_TYPES = {
    "METRIC_CONTRACTION",
    "GRADIENT_FLOW",
    "TOPOLOGICAL_SURGERY",
    "MONOTONICITY_FORMULA",
    "ASYMPTOTIC_BLOWUP",
    "VARIATIONAL_COUPLING",
    "BOUNDARY_DUALITY",
    "SPECTRAL_PROJECTION",
    "HOMOLOGICAL_COMPLEX",
    "COBORDISM",
}


def test_joint_schema_exists_and_validates_10_joint_types():
    schema_path = ROOT / "schema" / "mapeogeo-joint.schema.json"
    assert schema_path.is_file(), "schema/mapeogeo-joint.schema.json missing"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Validate registry against schema
    registry_path = ROOT / "formal" / "joint_type_registry_v0_21.json"
    assert registry_path.is_file(), "formal/joint_type_registry_v0_21.json missing"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    jsonschema.validate(instance=registry, schema=schema)
    registered_types = {j["joint_type"] for j in registry["joint_types"]}
    assert registered_types == VALID_JOINT_TYPES


def test_joint_schema_rejects_same_semantics():
    schema_path = ROOT / "schema" / "mapeogeo-joint.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    invalid_joint_instance = {
        "schema_version": "0.21",
        "joints": [
            {
                "joint_id": "joint:test:invalid",
                "joint_type": "METRIC_CONTRACTION",
                "relationship": "SAME_SEMANTICS",  # FORBIDDEN!
                "feet": [
                    {"endpoint_id": "srcdecl:test1", "role": "source_metric"},
                    {"endpoint_id": "srcdecl:test2", "role": "contracted_tensor"},
                ],
            }
        ]
    }
    # Attempting to validate a joint containing SAME_SEMANTICS must fail schema validation
    try:
        jsonschema.validate(instance=invalid_joint_instance, schema=schema)
        assert False, "Schema should have rejected SAME_SEMANTICS on joint"
    except jsonschema.ValidationError:
        pass


def test_certificate_schema_validates_quorum_and_typed_scope():
    schema_path = ROOT / "schema" / "mapeogeo-certificate.schema.json"
    assert schema_path.is_file(), "schema/mapeogeo-certificate.schema.json missing"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    valid_cert = {
        "schema_version": "0.21",
        "certificates": [
            {
                "certificate_id": "cert:stokes:simplicial_duality_v0_21",
                "target_concept": "simplicial_boundary_exterior_derivative_duality",
                "relationship": "SCOPED_OVERLAP",
                "scope": {
                    "domain": "SIMPLICIAL_COMPLEX",
                    "dimension": "k",
                    "coefficient_ring": "RAT",
                    "regularity": "DISCRETE",
                    "orientation_convention": "INDUCED_SIMPLEX_ORDER",
                    "boundary_convention": "STANDARD_ALTERNATING_SUM",
                    "parameter_range": "k >= 1",
                    "exceptional_cases": "k = 0 has zero boundary",
                },
                "view_slots": {
                    "eo": {
                        "status": "WITNESSED",
                        "statement_sha256": "a" * 64,
                        "view_ref": "srcdecl:stokes_simplex_eo",
                    },
                    "geo": {
                        "status": "WITNESSED",
                        "statement_sha256": "b" * 64,
                        "view_ref": "srcdecl:stokes_simplex_geo",
                    },
                    "pct": {
                        "status": "ABSENT",
                    },
                    "formal": {
                        "status": "ABSENT",
                    },
                },
                "quorum_count": 2,
                "verification_status": "CERTIFIED",
            }
        ]
    }
    jsonschema.validate(instance=valid_cert, schema=schema)


def test_certificate_schema_rejects_same_semantics():
    schema_path = ROOT / "schema" / "mapeogeo-certificate.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    invalid_cert = {
        "schema_version": "0.21",
        "certificates": [
            {
                "certificate_id": "cert:invalid",
                "target_concept": "invalid",
                "relationship": "SAME_SEMANTICS",  # FORBIDDEN!
                "scope": {
                    "domain": "SIMPLICIAL_COMPLEX",
                    "dimension": "k",
                    "coefficient_ring": "RAT",
                    "regularity": "DISCRETE",
                    "orientation_convention": "INDUCED",
                    "boundary_convention": "STANDARD",
                    "parameter_range": "ALL",
                    "exceptional_cases": "NONE",
                },
                "view_slots": {
                    "eo": {"status": "WITNESSED", "statement_sha256": "a"*64, "view_ref": "ref1"},
                    "geo": {"status": "WITNESSED", "statement_sha256": "b"*64, "view_ref": "ref2"},
                    "pct": {"status": "ABSENT"},
                    "formal": {"status": "ABSENT"},
                },
                "quorum_count": 2,
                "verification_status": "CERTIFIED",
            }
        ]
    }
    try:
        jsonschema.validate(instance=invalid_cert, schema=schema)
        assert False, "Certificate schema should have rejected SAME_SEMANTICS"
    except jsonschema.ValidationError:
        pass
