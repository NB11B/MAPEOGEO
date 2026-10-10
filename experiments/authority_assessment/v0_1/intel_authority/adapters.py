"""Narrow format, reference, value, and clock adapters for Task T01.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.catalog (Reference, _refs, _reference, _revision)
   - experiments.intelligence_integration.v0_1.clock_identity (encode/decode_clock_identity)
2. Interface Reused:
   - _reference, _revision validation functions
   - encode_clock_identity, decode_clock_identity
3. Additional Semantic Responsibility:
   - Strict bijective mapping between authority Reference format {"id", "revision"}
     and base catalog reference format {"record_id", "revision"}.
   - TypedValue translation and validation across declared primitives (string,
     integer, decimal, boolean, reference, reference_set) preserving exact types
     without truthiness coercion or default fabrication.
   - Clock stream adapter binding execution perimeters and local actors to
     canonical 'uow-clock:v1:[domain_id, local_actor]' streams.
4. Qualification Evidence Delta:
   - Bijective round-trip unit tests.
   - AQ41 (boundary overlap preservation across distinct streams).
================================================================================
"""

from __future__ import annotations

from decimal import Decimal
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.intelligence_integration.v0_1.clock_identity import (
    CLOCK_IDENTITY_PREFIX,
    decode_clock_identity,
    encode_clock_identity,
)


class ReferenceAdapterError(ValueError):
    """Raised when reference adaptation or validation fails."""


class TypedValueError(ValueError):
    """Raised when TypedValue validation or conversion fails."""


# ==============================================================================
# 1. REFERENCE ADAPTER
# ==============================================================================

def validate_authority_reference(ref: Any) -> Tuple[bool, Optional[str]]:
    """Validates an authority-format reference {"id": nonempty_string, "revision": positive_integer}."""
    if not isinstance(ref, dict):
        return False, "Reference must be an object/dict"
    ref_id = ref.get("id")
    if not isinstance(ref_id, str) or not ref_id:
        return False, "Reference 'id' must be a nonempty string"
    rev = ref.get("revision")
    if not isinstance(rev, int) or rev <= 0:
        return False, "Reference 'revision' must be a positive integer"
    return True, None


def validate_base_reference(ref: Any) -> Tuple[bool, Optional[str]]:
    """Validates a base-catalog reference {"record_id": nonempty_string, "revision": positive_integer}."""
    if not isinstance(ref, dict):
        return False, "Reference must be an object/dict"
    rec_id = ref.get("record_id")
    if not isinstance(rec_id, str) or not rec_id:
        return False, "Reference 'record_id' must be a nonempty string"
    rev = ref.get("revision")
    if not isinstance(rev, int) or rev <= 0:
        return False, "Reference 'revision' must be a positive integer"
    return True, None


def authority_to_base_ref(auth_ref: Dict[str, Any]) -> Dict[str, Any]:
    """Converts an authority Reference to a base-catalog Reference."""
    valid, err = validate_authority_reference(auth_ref)
    if not valid:
        raise ReferenceAdapterError(f"Cannot convert invalid authority reference: {err} in {auth_ref}")
    return {
        "record_id": auth_ref["id"],
        "revision": auth_ref["revision"],
    }


def base_to_authority_ref(base_ref: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a base-catalog Reference to an authority Reference."""
    valid, err = validate_base_reference(base_ref)
    if not valid:
        raise ReferenceAdapterError(f"Cannot convert invalid base reference: {err} in {base_ref}")
    return {
        "id": base_ref["record_id"],
        "revision": base_ref["revision"],
    }


# ==============================================================================
# 2. TYPED VALUE ADAPTER
# ==============================================================================

ALLOWED_TYPED_VALUE_TYPES = {
    "string",
    "integer",
    "decimal",
    "boolean",
    "reference",
    "reference_set",
}


def create_typed_value(
    val_type: str,
    raw_value: Any,
    unit_ref: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Creates and validates a TypedValue conforming to authority_contracts_v0_1.json."""
    if val_type not in ALLOWED_TYPED_VALUE_TYPES:
        raise TypedValueError(f"Unsupported TypedValue type: {val_type!r}. Allowed: {ALLOWED_TYPED_VALUE_TYPES}")

    if unit_ref is not None:
        valid, err = validate_authority_reference(unit_ref)
        if not valid:
            raise TypedValueError(f"Invalid unit_ref in TypedValue: {err}")

    # Zero-fabrication & strict type checking
    if val_type == "string":
        if not isinstance(raw_value, str):
            raise TypedValueError(f"Expected str for type 'string', got {type(raw_value).__name__}")
    elif val_type == "integer":
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise TypedValueError(f"Expected int (non-bool) for type 'integer', got {type(raw_value).__name__}")
    elif val_type == "decimal":
        if not isinstance(raw_value, (str, Decimal, int, float)):
            raise TypedValueError(f"Expected decimal representation for type 'decimal', got {type(raw_value).__name__}")
        # Standardize decimal string
        try:
            Decimal(str(raw_value))
        except Exception as exc:
            raise TypedValueError(f"Invalid decimal value: {raw_value!r}") from exc
    elif val_type == "boolean":
        if not isinstance(raw_value, bool):
            raise TypedValueError(f"Expected bool for type 'boolean', got {type(raw_value).__name__}")
    elif val_type == "reference":
        valid, err = validate_authority_reference(raw_value)
        if not valid:
            raise TypedValueError(f"Expected authority Reference for type 'reference': {err}")
    elif val_type == "reference_set":
        if not isinstance(raw_value, list):
            raise TypedValueError(f"Expected list for type 'reference_set', got {type(raw_value).__name__}")
        for r in raw_value:
            valid, err = validate_authority_reference(r)
            if not valid:
                raise TypedValueError(f"Element in 'reference_set' is not a valid reference: {err}")

    return {
        "type": val_type,
        "value": raw_value,
        "unit_ref": unit_ref,
    }


def extract_typed_value(typed_val: Dict[str, Any]) -> Any:
    """Extracts raw value from TypedValue structure with verification."""
    if not isinstance(typed_val, dict) or "type" not in typed_val or "value" not in typed_val:
        raise TypedValueError(f"Malformed TypedValue structure: {typed_val}")
    return typed_val["value"]


# ==============================================================================
# 3. CLOCK IDENTITY ADAPTER (AQ41)
# ==============================================================================

class ClockStreamAdapter:
    """Adapts local clock streams and execution perimeters into unambiguous clock identities.

    Reuses encode_clock_identity / decode_clock_identity from intelligence_integration.
    """

    def __init__(self, domain_id: str, owner_boundary: str) -> None:
        if not domain_id or not isinstance(domain_id, str):
            raise ValueError(f"domain_id must be a nonempty string, got: {domain_id!r}")
        if not owner_boundary or not isinstance(owner_boundary, str):
            raise ValueError(f"owner_boundary must be a nonempty string, got: {owner_boundary!r}")
        self.domain_id = domain_id
        self.owner_boundary = owner_boundary

    def encode_actor(self, local_actor: str) -> str:
        """Bijectively encodes (domain_id, local_actor) to prevent cross-stream collisions."""
        return encode_clock_identity(self.domain_id, local_actor)

    @staticmethod
    def decode_actor(encoded_actor: str) -> Tuple[str, str]:
        """Decodes canonical 'uow-clock:v1:[domain_id, local_actor]' back into constituent parts."""
        return decode_clock_identity(encoded_actor)

    def format_event_id(self, local_event_id: str) -> str:
        """Formats an event identifier scoped to this domain."""
        return f"{self.domain_id}:{local_event_id}"
