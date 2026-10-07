# SPDX-License-Identifier: MIT
"""Unit tests for PDI-135M JSON grammar and schema validation."""

import pytest
from pdi.adapter.schema_validator import PDISchemaValidator


@pytest.fixture
def validator():
    return PDISchemaValidator()


def test_canonical_propose_valid(validator):
    raw = """
    {
      "schema_version": 1,
      "kind": "PROPOSE",
      "operator_id": 12,
      "object_refs": [10, 11],
      "parameters": [
        {
          "type": "u32",
          "value": 100
        }
      ],
      "goal_ref": 25,
      "assumed_state_version": 9938
    }
    """
    res = validator.validate_json_string(raw)
    assert res.is_valid, f"Validation errors: {res.errors}"
    assert res.normalized["operator_id"] == 12
    assert res.normalized["kind"] == "PROPOSE"


def test_canonical_observe_valid(validator):
    raw = {
        "schema_version": 1,
        "kind": "OBSERVE",
        "projection_type": "GRAPH",
        "target_refs": [101, 102],
        "radius": 2,
    }
    res = validator.validate_dict(raw)
    assert res.is_valid


def test_canonical_compare_valid(validator):
    raw = {
        "schema_version": 1,
        "kind": "COMPARE",
        "left_ref": 5,
        "right_ref": 6,
        "comparator": "EQ",
    }
    res = validator.validate_dict(raw)
    assert res.is_valid


def test_canonical_clarify_valid(validator):
    raw = {
        "schema_version": 1,
        "kind": "CLARIFY",
        "missing_slots": ["temporal_window"],
        "ambiguity_reason": "Multiple target timestamps match input",
    }
    res = validator.validate_dict(raw)
    assert res.is_valid


def test_canonical_escalate_valid(validator):
    raw = {
        "schema_version": 1,
        "kind": "ESCALATE",
        "requested_capability": 0x00000004,
        "reason": "Requires high-precision matrix bridge permission",
    }
    res = validator.validate_dict(raw)
    assert res.is_valid


def test_invalid_operator_rejected(validator):
    raw = {
        "schema_version": 1,
        "kind": "PROPOSE",
        "operator_id": 999,  # Unregistered opcode
        "object_refs": [1, 2],
        "assumed_state_version": 10,
    }
    res = validator.validate_dict(raw)
    assert not res.is_valid
    assert any("out of bounds" in err or "not registered" in err for err in res.errors)


def test_invalid_schema_version(validator):
    raw = {
        "schema_version": 2,
        "kind": "OBSERVE",
        "projection_type": "STATE",
        "target_refs": [1],
    }
    res = validator.validate_dict(raw)
    assert not res.is_valid
    assert any("schema_version" in err for err in res.errors)


def test_missing_required_fields(validator):
    raw = {
        "schema_version": 1,
        "kind": "PROPOSE",
        # Missing operator_id and assumed_state_version
        "object_refs": [1, 2],
    }
    res = validator.validate_dict(raw)
    assert not res.is_valid
    assert any("operator_id" in err for err in res.errors)


def test_confidence_discarded(validator):
    raw = {
        "schema_version": 1,
        "kind": "PROPOSE",
        "operator_id": 5,
        "object_refs": [1, 2],
        "assumed_state_version": 42,
        "confidence": 0.9999,  # Must be ignored / stripped
    }
    res = validator.validate_dict(raw)
    assert res.is_valid
    assert "confidence" not in res.normalized
