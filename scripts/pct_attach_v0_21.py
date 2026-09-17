#!/usr/bin/env python3
"""MAPEOGEO Subject-Bound PCT Attachment Runner (v0.21).

Runs registered PCT attachments against graph subject nodes and outputs
an execution receipt ledger.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapeogeo.pct.attach import PCTAttachment, execute_attachment
from mapeogeo.pct.attachments.stokes_simplex import (
    SimplicialComplex,
    verify_incidence_transpose,
    verify_nilpotency,
    verify_stokes_duality,
)


def run_all_attachments(out_ledger: Path = ROOT / "evidence" / "pct_v0_21_attachment_receipts.json") -> dict:
    # 1. Simplicial Stokes attachment for EO subject
    def validate_stokes():
        K2 = SimplicialComplex.standard_simplex(2)
        K3 = SimplicialComplex.standard_simplex(3)
        return (
            verify_nilpotency(K2, "boundary")
            and verify_nilpotency(K3, "boundary")
            and verify_nilpotency(K2, "coboundary")
            and verify_nilpotency(K3, "coboundary")
            and verify_stokes_duality(K2)
            and verify_stokes_duality(K3)
            and verify_incidence_transpose(K2)
            and verify_incidence_transpose(K3)
        )

    stokes_att = PCTAttachment(
        attachment_id="pct:stokes:simplex_attachment",
        subject_node_id="srcdecl:stokes_simplex_eo",
        contract_type="B4_BOUNDARY_COMMUTING",
        scope={
            "domain": "SIMPLICIAL_COMPLEX",
            "dimension": "k",
            "coefficient_ring": "RAT",
            "regularity": "DISCRETE",
            "orientation_convention": "INDUCED_SIMPLEX_ORDER",
            "boundary_convention": "STANDARD_ALTERNATING_SUM",
            "parameter_range": "k >= 1",
            "exceptional_cases": "k = 0 has zero boundary",
        },
        validator=validate_stokes,
    )

    receipt = execute_attachment(stokes_att)

    data = {
        "schema_version": "0.21",
        "description": "Ledger of executed subject-bound PCT attachments",
        "receipts": [receipt.to_dict()],
    }

    out_ledger.parent.mkdir(parents=True, exist_ok=True)
    out_ledger.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Run subject-bound PCT attachments")
    parser.add_argument("--out-ledger", type=Path, default=ROOT / "evidence" / "pct_v0_21_attachment_receipts.json")
    args = parser.parse_args()

    data = run_all_attachments(args.out_ledger)
    print(f"Executed {len(data['receipts'])} attachment(s) -> {args.out_ledger}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
