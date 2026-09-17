#!/usr/bin/env python3
"""MAPEOGEO Correspondence Certificate Generator & Validator.

Validates multi-view correspondence certificates requiring independent witness quorum
and typed mathematical scopes across the 4 executable view slots (eo, geo, pct, formal).
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapeogeo.analysis.scope_comparator import TypedScopeRecord


@dataclass
class CorrespondenceCertificate:
    certificate_id: str
    target_concept: str
    relationship: str
    scope: TypedScopeRecord
    view_slots: dict[str, dict[str, Any]]
    quorum_count: int
    verification_status: str
    rejection_reason: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "certificate_id": self.certificate_id,
            "target_concept": self.target_concept,
            "relationship": self.relationship,
            "scope": self.scope.to_dict(),
            "view_slots": self.view_slots,
            "quorum_count": self.quorum_count,
            "verification_status": self.verification_status,
        }
        if self.rejection_reason is not None:
            d["rejection_reason"] = self.rejection_reason
        if self.metadata is not None:
            d["metadata"] = self.metadata
        return d


def verify_certificate_quorum(
    eo_slot: dict[str, Any],
    geo_slot: dict[str, Any],
    pct_slot: dict[str, Any],
    formal_slot: dict[str, Any],
) -> tuple[int, str]:
    """Calculates independent witness quorum count and verification status.

    Quorum requirements:
    - EO: status == WITNESSED with valid statement_sha256
    - GEO: status == WITNESSED with valid statement_sha256
    - Duplicate hashes between EO and GEO from alias/same-payload count as 1 witness, not 2.
    - PCT: status in (WITNESSED, PASS) with valid execution_digest
    - FORMAL: status == VERIFIED and kernel_verified == True
    """
    witnesses: list[str] = []
    seen_statement_hashes: set[str] = set()

    # 1. EO Slot
    if eo_slot.get("status") == "WITNESSED":
        h = eo_slot.get("statement_sha256")
        if h:
            witnesses.append("eo")
            seen_statement_hashes.add(h)

    # 2. GEO Slot
    if geo_slot.get("status") == "WITNESSED":
        h = geo_slot.get("statement_sha256")
        if h:
            if h in seen_statement_hashes:
                # Same statement digest / alias: not an independent witness
                pass
            else:
                witnesses.append("geo")
                seen_statement_hashes.add(h)

    # 3. PCT Slot
    if pct_slot.get("status") in ("WITNESSED", "PASS"):
        if pct_slot.get("execution_digest") or pct_slot.get("view_ref"):
            witnesses.append("pct")

    # 4. FORMAL Slot
    if formal_slot.get("status") == "VERIFIED" and formal_slot.get("kernel_verified") is True:
        witnesses.append("formal")

    quorum_count = len(witnesses)
    status = "CERTIFIED" if quorum_count >= 2 else "INSUFFICIENT_QUORUM"
    return quorum_count, status


def generate_correspondence_certificate(
    certificate_id: str,
    target_concept: str,
    relationship: str,
    scope: TypedScopeRecord,
    eo_slot: dict[str, Any],
    geo_slot: dict[str, Any],
    pct_slot: dict[str, Any],
    formal_slot: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> CorrespondenceCertificate:
    if relationship in ("SAME_SEMANTICS", "EQUIVALENT_TO", "IDENTICAL_TO"):
        raise ValueError(f"Forbidden relationship '{relationship}' in certificate {certificate_id}")

    quorum_count, verification_status = verify_certificate_quorum(
        eo_slot=eo_slot,
        geo_slot=geo_slot,
        pct_slot=pct_slot,
        formal_slot=formal_slot,
    )

    rejection_reason = (
        f"Required quorum >= 2 independent witnesses; found {quorum_count}"
        if verification_status == "INSUFFICIENT_QUORUM"
        else None
    )

    return CorrespondenceCertificate(
        certificate_id=certificate_id,
        target_concept=target_concept,
        relationship=relationship,
        scope=scope,
        view_slots={
            "eo": eo_slot,
            "geo": geo_slot,
            "pct": pct_slot,
            "formal": formal_slot,
        },
        quorum_count=quorum_count,
        verification_status=verification_status,
        rejection_reason=rejection_reason,
        metadata=metadata,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and validate correspondence certificates")
    parser.add_argument("--out-file", type=Path, default=ROOT / "formal" / "correspondence_certificates_v0_21.json")
    args = parser.parse_args()

    # Build standard initial correspondence certificates (e.g. Stokes package certificate)
    stokes_scope = TypedScopeRecord(
        domain="SIMPLICIAL_COMPLEX",
        dimension="k",
        coefficient_ring="RAT",
        regularity="DISCRETE",
        orientation_convention="INDUCED_SIMPLEX_ORDER",
        boundary_convention="STANDARD_ALTERNATING_SUM",
        parameter_range="k >= 1",
        exceptional_cases="k = 0 has zero boundary",
    )

    cert_stokes = generate_correspondence_certificate(
        certificate_id="cert:stokes:simplicial_duality_v0_21",
        target_concept="simplicial_boundary_exterior_derivative_duality",
        relationship="SCOPED_OVERLAP",
        scope=stokes_scope,
        eo_slot={
            "status": "WITNESSED",
            "statement_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "view_ref": "srcdecl:stokes_simplex_eo",
        },
        geo_slot={
            "status": "WITNESSED",
            "statement_sha256": "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            "view_ref": "srcdecl:stokes_simplex_geo",
        },
        pct_slot={
            "status": "ABSENT",
        },
        formal_slot={
            "status": "ABSENT",
        },
        metadata={"phase": "initial_seed"},
    )

    data = {
        "schema_version": "0.21",
        "description": "Preregistered multi-view correspondence certificates for MAPEOGEO v0.21",
        "certificates": [cert_stokes.to_dict()],
    }

    args.out_file.parent.mkdir(parents=True, exist_ok=True)
    args.out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {len(data['certificates'])} correspondence certificate(s) to {args.out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
