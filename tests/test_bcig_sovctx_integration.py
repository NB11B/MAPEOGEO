"""Unit and Integration Tests for BCIG-8 Soviet Adaptive Control Synthesis."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from bcig.bridges.sovctx_bridge import (
    CANONICAL_SOVCTX_BCIG_BRIDGES,
    EXPANDED_SOVCTX_BCIG_BRIDGES,
    get_expanded_sovctx_bridges,
    get_sovctx_bridges,
)
from bcig.campaigns.bcig8_adaptive_control_synthesis import (
    BCIG8AdaptiveControlSynthesisEngine,
    EXTENDED_PRINCIPLE_AUDITS,
)
from bcig.ontology.descendant_state import DescendantState


def test_sovctx_bridges_compatibility() -> None:
    # Baseline compatibility
    canonical = get_sovctx_bridges()
    assert len(canonical) == 4

    # Expanded bridges from Jetson Nano shakedown run
    expanded = get_expanded_sovctx_bridges()
    assert len(expanded) == 8

    # Verify each newly discovered bridge
    b5 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_05")
    assert "FELDBAUM" in b5.sovctx_entity_id
    assert "DUAL_CONTROL" in b5.bcig_entity_id

    b6 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_06")
    assert "KRASOVSKII" in b6.sovctx_entity_id
    assert "ROBUST_SAFE_REGULATION" in b6.bcig_entity_id

    b7 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_07")
    assert "VLASOV" in b7.sovctx_entity_id
    assert "FUNCTIONAL_SYSTEM" in b7.bcig_entity_id

    b8 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_08")
    assert "SAMARSKII" in b8.sovctx_entity_id
    assert "FINITE_PRECISION_REGULARIZATION" in b8.bcig_entity_id


def test_bcig8_synthesis_engine() -> None:
    engine = BCIG8AdaptiveControlSynthesisEngine()
    dossier = engine.run_synthesis()

    assert dossier["grounded_bridges_count"] == 8
    assert len(dossier["new_bridges_integrated"]) == 4

    census = dossier["census_comparison"]
    assert census["baseline_principles_evaluated"] == 8
    assert census["extended_principles_evaluated"] == 12

    # Verify Rediscovery surge
    base_rediscovered = census["baseline_counts"].get(DescendantState.REDISCOVERED.value, 0)
    ext_rediscovered = census["extended_counts"].get(DescendantState.REDISCOVERED.value, 0)
    assert base_rediscovered == 2
    assert ext_rediscovered == 4
    assert census["extended_percentages"][DescendantState.REDISCOVERED.value] == 33.33

    # Verify Adaptive Closure scores
    rankings = dossier["adaptive_closure_ranking"]
    assert len(rankings) >= 11

    # Check Anokhin remains absolute biological apex
    apex = rankings[0]
    assert "Anokhin" in apex["name"]
    assert apex["adaptive_closure_index"] == 1.0000

    # Check Active Inference and Feldbaum
    actinf = next(r for r in rankings if "Active Inference" in r["name"])
    assert actinf["adaptive_closure_index"] == 0.9667

    feldbaum = next(r for r in rankings if "Feldbaum" in r["name"])
    assert feldbaum["adaptive_closure_index"] == 0.8333

    # Check feedforward NN remains at 0
    alexnet = next(r for r in rankings if "AlexNet" in r["name"])
    assert alexnet["adaptive_closure_index"] == 0.0000


def test_bcig8_export_dossier() -> None:
    with TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir)
        engine = BCIG8AdaptiveControlSynthesisEngine()
        exported_file = engine.export_dossier(out_path)

        assert exported_file.is_file()
        data = json.loads(exported_file.read_text(encoding="utf-8"))
        assert data["campaign"] == "BCIG-8: Soviet Adaptive Control & Modern AI Synthesis"
        assert len(data["new_bridges_integrated"]) == 4
