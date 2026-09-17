from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EXECUTABLE_VIEW_SLOTS = ("eo", "geo", "pct", "formal")
PROVENANCE_VIEW = "NATURAL"


@dataclass
class ViewSlotRecord:
    status: str  # "ABSENT" | "WITNESSED" | "REPRESENTED" | "VERIFIED" | "REFUSED"
    view_ref: str | None = None
    statement_sha256: str | None = None
    execution_digest: str | None = None
    kernel_verified: bool | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"status": self.status}
        if self.view_ref is not None:
            d["view_ref"] = self.view_ref
        if self.statement_sha256 is not None:
            d["statement_sha256"] = self.statement_sha256
        if self.execution_digest is not None:
            d["execution_digest"] = self.execution_digest
        if self.kernel_verified is not None:
            d["kernel_verified"] = self.kernel_verified
        if self.notes is not None:
            d["notes"] = self.notes
        return d


@dataclass
class ViewSlotSummary:
    eo: ViewSlotRecord
    geo: ViewSlotRecord
    pct: ViewSlotRecord
    formal: ViewSlotRecord
    provenance: str = PROVENANCE_VIEW

    def to_dict(self) -> dict[str, Any]:
        return {
            "eo": self.eo.to_dict(),
            "geo": self.geo.to_dict(),
            "pct": self.pct.to_dict(),
            "formal": self.formal.to_dict(),
            "provenance": self.provenance,
        }


def compute_node_view_slots(node: dict[str, Any]) -> ViewSlotSummary:
    attrs = node.get("attributes", {})
    prof = attrs.get("independent_profile", {})
    node_id = node.get("id", "")

    # 1. Provenance
    provenance = attrs.get("source_provenance", {}).get("source_view", PROVENANCE_VIEW)

    # 2. EO & GEO direct status
    direct_status = prof.get("direct_status", "")
    stmt_hash = prof.get("statement_sha256")
    eo_fams = prof.get("eo_direct_families", [])
    geo_fams = prof.get("geo_direct_families", [])

    eo_witnessed = direct_status in ("EO_ONLY_DIRECT", "DUAL_DIRECT", "EO_ONLY", "DUAL_COVERAGE") or bool(eo_fams)
    geo_witnessed = direct_status in ("GEO_ONLY_DIRECT", "DUAL_DIRECT", "GEO_ONLY", "DUAL_COVERAGE") or bool(geo_fams)

    eo_slot = ViewSlotRecord(
        status="WITNESSED" if eo_witnessed else "ABSENT",
        view_ref=f"{node_id}:eo" if eo_witnessed else None,
        statement_sha256=stmt_hash if eo_witnessed else None,
    )
    geo_slot = ViewSlotRecord(
        status="WITNESSED" if geo_witnessed else "ABSENT",
        view_ref=f"{node_id}:geo" if geo_witnessed else None,
        statement_sha256=stmt_hash if geo_witnessed else None,
    )

    # 3. PCT slot
    pct_status = attrs.get("pct_status") or attrs.get("pct_attachment_status")
    pct_digest = attrs.get("pct_digest") or attrs.get("pct_execution_digest")
    pct_slot = ViewSlotRecord(
        status="WITNESSED" if pct_status in ("WITNESSED", "PASS", "ATTACHED") else "ABSENT",
        view_ref=f"{node_id}:pct" if pct_status in ("WITNESSED", "PASS", "ATTACHED") else None,
        execution_digest=pct_digest,
    )

    # 4. Formal slot
    formal_decl = attrs.get("formal_decl")
    kernel_verified = attrs.get("kernel_verified", False)
    if kernel_verified:
        formal_status = "VERIFIED"
    elif formal_decl:
        formal_status = "REPRESENTED"
    else:
        formal_status = "ABSENT"

    formal_slot = ViewSlotRecord(
        status=formal_status,
        view_ref=formal_decl,
        kernel_verified=kernel_verified if formal_status != "ABSENT" else None,
    )

    return ViewSlotSummary(
        eo=eo_slot,
        geo=geo_slot,
        pct=pct_slot,
        formal=formal_slot,
        provenance=provenance,
    )
