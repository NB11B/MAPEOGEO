"""Boundary Ledger: Enforces exact conservation invariant and terminal status assignment
for all 3,218 original frozen B5 records.

Conservation invariant:
N_B5 = N_resolved + N_awaiting_independent_evidence + N_counterexample + N_ambiguous + N_out_of_scope
No record disappears. No status remains UNRESOLVED.
"""

from typing import Dict, List, Any
from pathlib import Path
import json

from experiments.boundary_resolution import ALLOWED_TERMINAL_STATUSES

class BoundaryLedger:
    def __init__(self, expected_total: int = 3218):
        self.expected_total = expected_total
        self.ledger: Dict[str, Dict[str, Any]] = {}

    def load_b5_boundary(self, b5_jsonl_path: Path) -> None:
        """Loads all original frozen B5 records."""
        with open(b5_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    bid = rec["boundary_id"]
                    self.ledger[bid] = {
                        "boundary_id": bid,
                        "domain": rec["domain"],
                        "failure_projection": rec["failure_projection"],
                        "failure_mechanism": rec["failure_mechanism"],
                        "status": "UNRESOLVED",
                        "adjudication_type": None,
                        "resolution_details": None
                    }

    def record_adjudication(
        self,
        boundary_id: str,
        status: str,
        adjudication_type: str,
        details: str
    ) -> None:
        """Assigns an adjudicated terminal status to a specific B5 record."""
        if boundary_id not in self.ledger:
            raise KeyError(f"Unknown boundary_id: {boundary_id}")
        if status not in ALLOWED_TERMINAL_STATUSES:
            raise ValueError(f"Status '{status}' not in ALLOWED_TERMINAL_STATUSES: {ALLOWED_TERMINAL_STATUSES}")
        
        self.ledger[boundary_id]["status"] = status
        self.ledger[boundary_id]["adjudication_type"] = adjudication_type
        self.ledger[boundary_id]["resolution_details"] = details

    def verify_conservation(self) -> Dict[str, Any]:
        """Verifies that all expected records exist, none are UNRESOLVED, and counts match exactly."""
        total_records = len(self.ledger)
        if total_records != self.expected_total:
            raise ValueError(f"Conservation violated! Expected {self.expected_total}, got {total_records}")

        status_counts: Dict[str, int] = {}
        unresolved_ids = []

        for bid, entry in self.ledger.items():
            s = entry["status"]
            if s == "UNRESOLVED":
                unresolved_ids.append(bid)
            status_counts[s] = status_counts.get(s, 0) + 1

        if unresolved_ids:
            raise ValueError(f"{len(unresolved_ids)} records remained UNRESOLVED! e.g., {unresolved_ids[:5]}")

        return {
            "total_records": total_records,
            "status_distribution": status_counts,
            "unresolved_count": len(unresolved_ids),
            "conservation_satisfied": True
        }

    def export_ledger(self, output_path: Path) -> None:
        """Exports the verified ledger as a deterministic JSONL file."""
        self.verify_conservation()
        with open(output_path, "w", encoding="utf-8") as f:
            for bid in sorted(self.ledger.keys()):
                f.write(json.dumps(self.ledger[bid]) + "\n")
