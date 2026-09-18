from __future__ import annotations

import copy
import gzip
import hashlib
import json
from pathlib import Path
import pytest

from mapeogeo.gfyproof_bridge import (
    apply_gfyproof_certificate,
    canonical_sha256,
    claim_contract_digest,
    validate_gfyproof_certificate,
)
from mapeogeo.farkas_contracts_v1 import (
    FARKAS_SPECS,
    FarkasContractError,
    apply_farkas_endpoint_overlay,
    build_farkas_endpoint_overlay,
)

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_GRAPH_PATH = ROOT / 'artifacts' / 'foundation_backfill' / 'mapeogeo_foundation_graph.json.gz'


def test_farkas_specs_count_and_structure():
    assert len(FARKAS_SPECS) >= 10
    for spec in FARKAS_SPECS:
        assert spec.semantic_id == 'GFY.FARKAS_IMPLICATION.v1'
        assert spec.contract_id.startswith('mapeogeo.farkas.')
        assert 'matrix' in spec.payload
        assert 'bounds' in spec.payload
        assert 'multipliers' in spec.payload


def test_farkas_overlay_builds_and_applies_on_foundation_graph():
    if not FOUNDATION_GRAPH_PATH.exists():
        pytest.skip('Foundation graph not present')

    with gzip.open(FOUNDATION_GRAPH_PATH, 'rt', encoding='utf-8') as f:
        graph = json.load(f)

    overlay = build_farkas_endpoint_overlay(graph)
    assert overlay['schema'] == 'mapeogeo.endpoint-semantic-overlay.v1'
    assert len(overlay['contracts']) == len(FARKAS_SPECS)
    assert 'overlay_digest' in overlay

    enriched = apply_farkas_endpoint_overlay(graph, overlay)
    nodes = {n['id']: n for n in enriched['nodes']}

    for spec in FARKAS_SPECS:
        p_node = nodes[spec.premise_id]
        c_node = nodes[spec.conclusion_id]
        p_contracts = p_node.get('attributes', {}).get('semantic_contracts', [])
        c_contracts = c_node.get('attributes', {}).get('semantic_contracts', [])
        assert any(c['contract_id'] == spec.contract_id for c in p_contracts)
        assert any(c['contract_id'] == spec.contract_id for c in c_contracts)
