from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AcquisitionCausalityRecord:
    source_id: str
    generation: int
    nomination_id: Optional[str] = None
    frontier_id: Optional[str] = None
    origin_source_id: Optional[str] = None
    origin_passage_id: Optional[str] = None
    frontier_type: Optional[str] = None
    reason: Optional[str] = None
    resolution_state: Optional[str] = None
    parent_path: list[str] = field(default_factory=list)
    recorded_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProvenanceTracker:
    """Tracks, stores, and audits strict acquisition causality and discovery depth across crawler generations."""

    def __init__(self, db: Any) -> None:
        self.db = db

    def record_causality(self, record: AcquisitionCausalityRecord) -> None:
        """Persist acquisition causality chain in DB."""
        with self.db.get_connection() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO acquisition_provenance (
                    source_id, generation, nomination_id, frontier_id,
                    origin_source_id, origin_passage_id, frontier_type,
                    reason, resolution_state, parent_path_json, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.source_id,
                    record.generation,
                    record.nomination_id,
                    record.frontier_id,
                    record.origin_source_id,
                    record.origin_passage_id,
                    record.frontier_type,
                    record.reason,
                    record.resolution_state,
                    json.dumps(record.parent_path),
                    record.recorded_at,
                ),
            )
            con.commit()

    def get_causality(self, source_id: str) -> Optional[AcquisitionCausalityRecord]:
        with self.db.get_connection() as con:
            row = con.execute(
                "SELECT * FROM acquisition_provenance WHERE source_id = ?", (source_id,)
            ).fetchone()
            if not row:
                return None
            return AcquisitionCausalityRecord(
                source_id=row["source_id"],
                generation=row["generation"],
                nomination_id=row["nomination_id"],
                frontier_id=row["frontier_id"],
                origin_source_id=row["origin_source_id"],
                origin_passage_id=row["origin_passage_id"],
                frontier_type=row["frontier_type"],
                reason=row["reason"],
                resolution_state=row["resolution_state"],
                parent_path=json.loads(row["parent_path_json"] or "[]"),
                recorded_at=row["recorded_at"],
            )

    def audit_causality(self, admitted_source_ids: list[str]) -> dict[str, Any]:
        """Audit that every admitted source (with generation > 0) has an unbroken causality chain back to seed."""
        orphaned: list[str] = []
        valid_chains: list[dict[str, Any]] = []

        for sid in admitted_source_ids:
            causality = self.get_causality(sid)
            if not causality:
                orphaned.append(sid)
                continue
            if causality.generation > 0:
                if not (causality.nomination_id and causality.frontier_id and causality.origin_source_id):
                    orphaned.append(sid)
                    continue
            valid_chains.append(causality.to_dict())

        return {
            "total_sources_checked": len(admitted_source_ids),
            "valid_chains_count": len(valid_chains),
            "orphaned_sources": orphaned,
            "orphaned_count": len(orphaned),
            "is_valid": len(orphaned) == 0,
        }

    def trace_lineage_path(self, target_source_id: str) -> list[str]:
        """Trace hop-by-hop ancestry path from target back to Generation 0 seed."""
        path: list[str] = [target_source_id]
        curr = target_source_id
        visited: set[str] = {curr}

        while True:
            c = self.get_causality(curr)
            if not c or c.generation == 0 or not c.origin_source_id:
                break
            origin = c.origin_source_id
            if origin in visited:
                # Cycle detected
                break
            visited.add(origin)
            path.append(origin)
            curr = origin

        path.reverse()
        return path

    def export_provenance_paths(self, output_path: Path) -> int:
        """Export line-delimited JSON of all discovery provenance paths."""
        paths_exported = 0
        with self.db.get_connection() as con:
            rows = con.execute("SELECT source_id, generation FROM acquisition_provenance").fetchall()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for r in rows:
                sid = r[0]
                gen = r[1]
                path = self.trace_lineage_path(sid)
                c = self.get_causality(sid)
                line_data = {
                    "source_id": sid,
                    "generation": gen,
                    "hops_to_seed": len(path) - 1,
                    "full_path": path,
                    "nomination_id": c.nomination_id if c else None,
                    "frontier_id": c.frontier_id if c else None,
                    "frontier_type": c.frontier_type if c else None,
                    "reason": c.reason if c else "Seed Generation 0",
                }
                f.write(json.dumps(line_data, ensure_ascii=False) + "\n")
                paths_exported += 1

        return paths_exported
