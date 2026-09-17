from __future__ import annotations

import json
from pathlib import Path
from scripts.coverage_inventory import generate_coverage_inventory, load_legacy_reconciliation

ROOT = Path(__file__).resolve().parents[2]


def test_coverage_inventory_reconciles_graph_and_campaigns():
    out_file = ROOT / "formal" / "wave_f5" / "legacy_reconciliation_v0_22.json"
    res = generate_coverage_inventory(out_file=out_file)
    assert res.all_passed is True

    assert out_file.is_file(), "legacy_reconciliation_v0_22.json missing"
    data = load_legacy_reconciliation(out_file)

    # Check structural accounting
    assert data["schema_version"] == "0.22"
    assert "graph_nodes_count" in data
    assert "campaign_manifests" in data
    assert "reconciled_items" in data
    assert len(data["reconciled_items"]) > 0

    # Every item must have an explicit disposition
    valid_dispositions = {
        "REUSE_EXACT",
        "REFINE_SCOPE",
        "SPLIT_COMPOSITE",
        "ADD_VARIANT",
        "NEW",
        "UNRESOLVED",
    }
    for item in data["reconciled_items"]:
        assert item["disposition"] in valid_dispositions
        assert "source_id" in item
        assert "target_canonical_id" in item or item["disposition"] == "UNRESOLVED"
