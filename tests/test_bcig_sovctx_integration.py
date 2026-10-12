"""Unit and Integration Tests for BCIG-8 Tightened Soviet Adaptive Control Synthesis."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from bcig.bridges.cross_graph_hypotheses import (
    CANONICAL_CROSS_GRAPH_HYPOTHESES,
    get_cross_graph_hypotheses,
)
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


def test_sovctx_bridges_tightened_compatibility() -> None:
    # Baseline compatibility
    canonical = get_sovctx_bridges()
    assert len(canonical) == 4

    # Expanded bridges from Jetson Nano shakedown run
    expanded = get_expanded_sovctx_bridges()
    assert len(expanded) == 8

    # Verify Bridge 5: Epistemic Action (Act-to-Know)
    b5 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_05")
    assert "FELDBAUM" in b5.sovctx_entity_id
    assert "EPISTEMIC_ACTION_PROBE" in b5.bcig_entity_id
    assert "acting to probe and reduce environmental uncertainty" in b5.epistemic_justification

    # Verify Bridge 6: Forward Set Invariance (no premature REDISCOVERED claim)
    b6 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_06")
    assert "KRASOVSKII" in b6.sovctx_entity_id
    assert "ROBUST_SAFE_REGULATION" in b6.bcig_entity_id

    # Verify Bridge 7: Macroscopic Assembly (MoE claims completely stripped)
    b7 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_07")
    assert "VLASOV" in b7.sovctx_entity_id
    assert "FUNCTIONAL_SYSTEM" in b7.bcig_entity_id
    assert "Mixture-of-Experts" not in b7.epistemic_justification

    # Verify Bridge 8: Resource-Bounded Regularization (FP8/INT4 claims stripped)
    b8 = next(b for b in expanded if b.bridge_id == "BRIDGE:SOVCTX_BCIG_08")
    assert "SAMARSKII" in b8.sovctx_entity_id
    assert "RESOURCE_BOUNDED_REGULARIZATION" in b8.bcig_entity_id
    assert "distinct from modern neural quantization" in b8.epistemic_justification


def test_cross_graph_hypotheses_layer() -> None:
    hyps = get_cross_graph_hypotheses()
    assert len(hyps) == 3

    hyp_ids = [h.hypothesis_id for h in hyps]
    assert "HYP:XGRAPH:01_EPISTEMIC_ACTION" in hyp_ids
    assert "HYP:XGRAPH:02_CLOSED_ADAPTIVE_SYSTEMS" in hyp_ids
    assert "HYP:XGRAPH:03_RESOURCE_BOUNDED_INTELLIGENCE" in hyp_ids

    # Verify relational grammar of epistemic action
    h1 = next(h for h in hyps if "01_EPISTEMIC_ACTION" in h.hypothesis_id)
    assert "PROBE (ACT_TO_KNOW)" in h1.relational_grammar


def test_bcig8_tightened_synthesis_engine() -> None:
    engine = BCIG8AdaptiveControlSynthesisEngine()
    dossier = engine.run_synthesis()

    assert dossier["grounded_bridges_count"] == 8
    assert len(dossier["cross_graph_hypotheses"]) == 3

    census = dossier["census_comparison"]
    assert census["baseline_principles_evaluated"] == 8
    assert census["extended_principles_evaluated"] == 12

    # Under tightened classification:
    # STRUCTURAL_ANALOGUE is the dominant mode (5 / 12 = 41.67%)
    ext_counts = census["extended_counts"]
    assert ext_counts[DescendantState.ANALOGOUS.value] == 5
    assert ext_counts[DescendantState.REDISCOVERED.value] == 2
    assert ext_counts[DescendantState.DIRECT.value] == 2
    assert ext_counts[DescendantState.MIGRATED.value] == 2
    assert ext_counts[DescendantState.MISSING.value] == 1

    # Verify Relational Grammar primitive
    rg = dossier["relational_grammar_primitive"]
    assert rg["primitive"] == "PROBE (ACT_TO_KNOW)"
    assert "REPRESENT -> PROBE (ACT_TO_KNOW) -> OBSERVE -> UPDATE -> CONTROL" in rg["grammar"]

    # Verify Architectural Taxonomy
    tax = dossier["architectural_taxonomy"]
    assert "externally_evaluated_systems" in tax
    assert "internally_closed_adaptive_systems" in tax

    # Verify Endogenous Self-Maintenance distinction
    esm = dossier["endogenous_self_maintenance_analysis"]
    assert esm["concept"] == "ENDOGENOUS_SELF_MAINTENANCE"
    assert len(esm["systems_with_endogenous_maintenance"]) == 3
    assert len(esm["systems_lacking_endogenous_maintenance"]) == 3

    # Verify Adaptive Closure scores
    rankings = dossier["adaptive_closure_ranking"]
    assert rankings[0]["name"] == "Anokhin Functional System Architecture"
    assert rankings[0]["adaptive_closure_index"] == 1.0000

    actinf = next(r for r in rankings if "Active Inference" in r["name"])
    assert actinf["adaptive_closure_index"] == 0.9667

    feldbaum = next(r for r in rankings if "Feldbaum" in r["name"])
    assert feldbaum["adaptive_closure_index"] == 0.8333

    kras = next(r for r in rankings if "Krasovskii" in r["name"])
    assert kras["adaptive_closure_index"] == 0.8000

    # Verify Teleological 8-Pillar Gap Analysis
    pillars = dossier["teleological_eight_pillar_gap_analysis"]["pillars"]
    assert len(pillars) == 8
    assert "2_active_information_gathering" in pillars
    assert "5_endogenous_goal_conditions" in pillars
    assert "8_endogenous_self_maintenance" in pillars


def test_bcig8_tightened_export(tmp_path: Path) -> None:
    engine = BCIG8AdaptiveControlSynthesisEngine()
    exported_file = engine.export_dossier(tmp_path)

    assert exported_file.is_file()
    data = json.loads(exported_file.read_text(encoding="utf-8"))
    assert "Tightened Formulation" in data["campaign"]
    assert data["relational_grammar_primitive"]["primitive"] == "PROBE (ACT_TO_KNOW)"
