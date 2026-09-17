from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def make_receipt(
    *,
    component_id: str,
    component_epoch: int,
    layer: str,
    role: str,
    mathematical_verdict: str,
    content: object,
    dependency_receipt_ids: list[str],
    source_statement_sha256: str,
    evidence_refs: list[str],
    predecessor_receipt_id: str | None,
    issuance_revision: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "component_id": component_id,
        "component_epoch": component_epoch,
        "layer": layer,
        "role": role,
        "mathematical_verdict": mathematical_verdict,
        "content_sha256": canonical_sha256(content),
        "dependency_receipt_ids": list(dependency_receipt_ids),
        "source_statement_sha256": source_statement_sha256,
        "evidence_refs": list(evidence_refs),
        "predecessor_receipt_id": predecessor_receipt_id,
        "issuance_revision": issuance_revision,
    }
    return {"receipt_id": canonical_sha256(payload), **payload}


def make_event(
    *,
    revision: int,
    event_type: str,
    target_receipt_id: str,
    component_id: str,
    reason_code: str,
    replacement_receipt_id: str | None = None,
    new_component_epoch: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "revision": revision,
        "event_type": event_type,
        "target_receipt_id": target_receipt_id,
        "component_id": component_id,
        "reason_code": reason_code,
        "replacement_receipt_id": replacement_receipt_id,
        "new_component_epoch": new_component_epoch,
    }
    return {"event_id": canonical_sha256(payload), **payload}
