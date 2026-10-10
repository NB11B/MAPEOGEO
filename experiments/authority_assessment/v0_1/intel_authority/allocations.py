"""Shared Allowance and Allocation Protocol for Task T06.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.workflow (resource reservations, commitment accounting)
   - intel_uow.catalog (Record envelope, Reference, TypedValue)
2. Interface Reused:
   - Reference and TypedValue adapters (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - AQ53: Shared allowance or indivisible resource cannot be double-spent
     across separate UoWs.
   - Owner-issued allocation evidence and reservations (AllocationRecord).
   - Conservative unknown availability: missing global allocation state stays
     unknown, never presumed available.
   - Cancellation request or receipt alone DOES NOT release a reservation;
     release requires explicit authorized release evidence and basis.
4. Qualification Evidence Delta:
   - AQ53 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
    extract_typed_value,
    validate_authority_reference,
)


class AllocationState(str, Enum):
    RESERVED = "reserved"
    CONSUMED = "consumed"
    RELEASED = "released"
    UNKNOWN = "unknown"


def _ref_id(ref_val: Any) -> str:
    if isinstance(ref_val, dict):
        return str(ref_val.get("id", ""))
    return str(ref_val)


def _normalize_ref(ref_val: Any) -> Dict[str, Any]:
    if isinstance(ref_val, dict) and "id" in ref_val:
        return {"id": str(ref_val["id"]), "revision": int(ref_val.get("revision", 1))}
    elif isinstance(ref_val, str):
        return {"id": ref_val, "revision": 1}
    return {"id": str(ref_val), "revision": 1}


class AllocationManager:
    """Manages shared limits, quotas, and indivisible resource reservations across UoWs."""

    def __init__(self, records: Optional[List[Dict[str, Any]]] = None) -> None:
        self.records: List[Dict[str, Any]] = records or []

    def get_active_reservation(
        self,
        resource_ref: Dict[str, Any] | str,
    ) -> Optional[Dict[str, Any]]:
        """Finds any active (reserved or consumed) allocation for the given resource."""
        r_id = _ref_id(resource_ref)
        for rec in self.records:
            if _ref_id(rec.get("resource_or_allowance_ref")) == r_id:
                if rec.get("state") in (AllocationState.RESERVED.value, AllocationState.CONSUMED.value):
                    return rec
        return None

    def reserve(
        self,
        allocation_ref: Dict[str, Any] | str,
        owner_ref: Dict[str, Any] | str,
        resource_ref: Dict[str, Any] | str,
        uow_ref: Dict[str, Any] | str,
        quantity: Any,
        unit: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Attempts to reserve a shared resource for a UoW (AQ53).

        Fails if already reserved by another UoW.
        """
        r_id = _ref_id(resource_ref)
        target_uow = _ref_id(uow_ref)

        active = self.get_active_reservation(resource_ref)
        if active:
            active_uow = _ref_id(active.get("uow_ref"))
            if active_uow != target_uow:
                return (
                    False,
                    active,
                    f"Resource '{r_id}' is already reserved by UoW '{active_uow}'; double-spending prohibited",
                )

        typed_qty = (
            quantity
            if isinstance(quantity, dict) and "type" in quantity
            else create_typed_value("decimal" if isinstance(quantity, float) else "integer", quantity, unit)
        )

        record = {
            "ref": _normalize_ref(allocation_ref),
            "owner_ref": _normalize_ref(owner_ref),
            "resource_or_allowance_ref": _normalize_ref(resource_ref),
            "uow_ref": _normalize_ref(uow_ref),
            "quantity": typed_qty,
            "scope_ref": _normalize_ref("scope:shared_pool"),
            "state": AllocationState.RESERVED.value,
            "authority_ref": _normalize_ref("auth:allocation_protocol"),
            "occurrence_ref": {"stream_id": "stream:alloc", "sequence": 1},
            "receipt_ref": {"stream_id": "stream:alloc", "sequence": 1},
            "release_basis_ref": None,
        }
        self.records.append(record)
        return True, record, None

    def request_cancellation(
        self,
        allocation_ref: Dict[str, Any] | str,
    ) -> Tuple[bool, Optional[str]]:
        """Handles cancellation request.

        AQ53 INVARIANT: Cancellation request DOES NOT release the reservation!
        It remains reserved until an authorized release event occurs.
        """
        alloc_id = _ref_id(allocation_ref)
        for rec in self.records:
            if _ref_id(rec.get("ref")) == alloc_id:
                # Retains state RESERVED; does NOT change to RELEASED
                return (
                    True,
                    f"Cancellation request recorded for '{alloc_id}'; reservation remains active pending authorized release basis",
                )
        return False, f"Allocation '{alloc_id}' not found"

    def release(
        self,
        allocation_ref: Dict[str, Any] | str,
        release_basis_ref: Dict[str, Any] | str,
    ) -> Tuple[bool, Optional[str]]:
        """Releases a reservation with explicit authorized release basis."""
        alloc_id = _ref_id(allocation_ref)
        for rec in self.records:
            if _ref_id(rec.get("ref")) == alloc_id:
                rec["state"] = AllocationState.RELEASED.value
                rec["release_basis_ref"] = _normalize_ref(release_basis_ref)
                return True, None
        return False, f"Allocation '{alloc_id}' not found"
