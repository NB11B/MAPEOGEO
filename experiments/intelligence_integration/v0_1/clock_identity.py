"""Unambiguous canonical clock identity codec for multi-domain event streams.

Encodes (domain_id, local_actor) pairs into a canonical, versioned string
representation that is strictly bijective under the declared domain:
    D(E(d, a)) = (d, a)
    E(d1, a1) = E(d2, a2) ==> (d1, a1) = (d2, a2)

Components are preserved as a canonical JSON pair with prefix 'uow-clock:v1:'.
Component boundaries are unambiguous regardless of characters contained in
domain_id or local_actor (including colons, quotation marks, slashes, whitespace,
and Unicode characters).
"""

from __future__ import annotations

import json
from typing import Tuple

CLOCK_IDENTITY_PREFIX = "uow-clock:v1:"


def _validate_scalar_string(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str, got {type(value).__name__}")
    if not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    for ch in value:
        cp = ord(ch)
        if 0xD800 <= cp <= 0xDFFF:
            raise ValueError(f"{field_name} contains invalid surrogate code point: U+{cp:04X}")


def encode_clock_identity(domain_id: str, local_actor: str) -> str:
    """Encodes domain_id and local_actor into canonical 'uow-clock:v1:[d,a]'.

    Accepts nonempty strings containing valid Unicode scalar values.
    Preserves case, whitespace, spelling, and Unicode normalization exactly.
    """
    _validate_scalar_string(domain_id, "domain_id")
    _validate_scalar_string(local_actor, "local_actor")
    payload = json.dumps(
        [domain_id, local_actor],
        ensure_ascii=False,
        separators=(',', ':'),
        allow_nan=False,
    )
    return f"{CLOCK_IDENTITY_PREFIX}{payload}"


def decode_clock_identity(encoded: str) -> Tuple[str, str]:
    """Decodes a canonical clock identity string back into (domain_id, local_actor).

    Accepts only the declared canonical format and verifies that decoding and
    re-encoding produce the identical representation.
    """
    if not isinstance(encoded, str):
        raise TypeError(f"encoded must be a str, got {type(encoded).__name__}")
    if not encoded.startswith(CLOCK_IDENTITY_PREFIX):
        raise ValueError(f"encoded identity must start with '{CLOCK_IDENTITY_PREFIX}', got: {encoded!r}")
    
    payload = encoded[len(CLOCK_IDENTITY_PREFIX):]
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON payload in clock identity: {exc}") from exc

    if not isinstance(data, list) or len(data) != 2:
        raise ValueError("payload must be a 2-element list [domain_id, local_actor]")

    domain_id, local_actor = data
    _validate_scalar_string(domain_id, "domain_id")
    _validate_scalar_string(local_actor, "local_actor")

    expected_payload = json.dumps(
        [domain_id, local_actor],
        ensure_ascii=False,
        separators=(',', ':'),
        allow_nan=False,
    )
    if payload != expected_payload:
        raise ValueError("non-canonical encoding detected")

    return domain_id, local_actor
