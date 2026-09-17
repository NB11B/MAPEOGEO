from __future__ import annotations

import json
from pathlib import Path
from mapeogeo.models.view_slots import (
    EXECUTABLE_VIEW_SLOTS,
    PROVENANCE_VIEW,
    compute_node_view_slots,
    ViewSlotSummary,
)

ROOT = Path(__file__).resolve().parents[1]


def test_view_slots_definition_and_isolation():
    # Exactly 4 executable slots
    assert set(EXECUTABLE_VIEW_SLOTS) == {"eo", "geo", "pct", "formal"}
    # NATURAL is provenance, not an executable view slot
    assert PROVENANCE_VIEW == "NATURAL"
    assert "natural" not in EXECUTABLE_VIEW_SLOTS
    assert "NATURAL" not in EXECUTABLE_VIEW_SLOTS


def test_node_view_slots_computation():
    # Example node with EO, GEO, and FORMAL representation
    mock_node = {
        "id": "srcdecl:test:01",
        "type": "DECLARATION",
        "attributes": {
            "independent_profile": {
                "direct_status": "DUAL_DIRECT",
                "statement_sha256": "12345678" * 8,
            },
            "source_provenance": {
                "source_view": "NATURAL",
                "pdf_reference": "Test Page 10",
            },
            "formal_decl": "MAPEOGEOFormal.test_decl",
            "kernel_verified": True,
        },
    }

    slots = compute_node_view_slots(mock_node)
    assert isinstance(slots, ViewSlotSummary)
    assert slots.eo.status == "WITNESSED"
    assert slots.geo.status == "WITNESSED"
    assert slots.pct.status == "ABSENT"
    assert slots.formal.status == "VERIFIED"
    assert slots.provenance == "NATURAL"

    # Ensure to_dict formats correctly for schemas
    d = slots.to_dict()
    assert set(d.keys()) == {"eo", "geo", "pct", "formal", "provenance"}
    assert d["eo"]["status"] == "WITNESSED"
    assert d["geo"]["status"] == "WITNESSED"
    assert d["pct"]["status"] == "ABSENT"
    assert d["formal"]["status"] == "VERIFIED"


def test_no_auto_same_semantics_promotion():
    # Ensure view slot summary rejects or prevents any SAME_SEMANTICS tagging
    mock_node = {
        "id": "srcdecl:test:02",
        "type": "DECLARATION",
        "attributes": {
            "independent_profile": {"direct_status": "DUAL_DIRECT"},
        },
    }
    slots = compute_node_view_slots(mock_node)
    assert "SAME_SEMANTICS" not in json.dumps(slots.to_dict())
