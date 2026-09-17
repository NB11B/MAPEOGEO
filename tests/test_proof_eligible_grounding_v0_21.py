from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_proof_eligible_grounding_registry():
    pe_file = ROOT / "formal" / "proof_eligible_edges_v0_21.json"
    assert pe_file.is_file(), "formal/proof_eligible_edges_v0_21.json missing"

    data = json.loads(pe_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == "0.21"

    # Proof-eligible objects must remain 0 / 235
    assert data["proof_eligible_objects_count"] == 0
    assert data["total_grounding_objects_denominator"] == 235

    # Exactly 1 proof-eligible edge: Gallier Rank-Nullity (srcdecl:theorem:6_16)
    edges = data["proof_eligible_edges"]
    assert len(edges) == 1
    edge = edges[0]
    assert edge["source_id"] == "srcdecl:theorem:6_16"
    assert edge["formal_decl"] == "MAPEOGEOFormal.theorem_6_16_rank_nullity"
    assert edge["relationship"] in ("SCOPED_OVERLAP", "SCOPED_TRANSFER")
    assert edge["relationship"] != "SAME_SEMANTICS"
