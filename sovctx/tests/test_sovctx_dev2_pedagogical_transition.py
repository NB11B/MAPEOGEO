#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-DEV2: Pedagogical Transition & Transfer Test.

Verifies:
1. Agency Progression: Supplied -> Hinted -> Invented trajectory across all 13 active primitives.
2. Transfer Demand Progression: Same_Form -> Near -> Far transfer rates across curricular stages.
3. Scaffolding Depth Coupling: Strict coupling between ScaffoldingDepth and TransferRequirement.
4. M6.2 Grammar Concordance: 100% concordance with the M6.2 16x16 Noncommutative Grammar Matrix.
5. High-Gamma Operation Ordering: Preservation of mathematical structure when Gamma >= 2.
6. Teacher Doctrine vs. Pupil Text Ordering Divergence: Epistemic contrast in operation sequencing.
"""

import pytest
from sovctx.node.developmental_schema import ScaffoldingDepth, TransferRequirement
from sovctx.node.developmental_transition_engine import (
    DevelopmentalTransitionEngine,
    DevelopmentalTransitionSummary,
)


@pytest.fixture(scope="module")
def dev2_summary() -> DevelopmentalTransitionSummary:
    engine = DevelopmentalTransitionEngine()
    return engine.run_transition_test()


def test_dev2_engine_initialization(dev2_summary: DevelopmentalTransitionSummary):
    """Verifies that 87 dense episodes and 13 active primitives are analyzed."""
    assert dev2_summary.total_episodes_analyzed == 87
    assert dev2_summary.active_primitives_count == 13
    assert "Rs" in dev2_summary.tracked_primitives
    assert "Ax" in dev2_summary.tracked_primitives
    assert "Sr" in dev2_summary.tracked_primitives
    assert "I" in dev2_summary.tracked_primitives


def test_dev2_agency_trajectories_all_primitives(dev2_summary: DevelopmentalTransitionSummary):
    """
    Verifies that within the currently extracted ordinary-school sample (Stages 1-3),
    no episode required fully unscaffolded invention of tracked primitives,
    and invention reaches 100% in Stage 4 (Olympiad Circles).
    """
    trajectories = dev2_summary.agency_trajectories
    for sym, traj in trajectories.items():
        assert traj.is_monotonically_scaffold_stripping

        # School stages (1, 2, 3) must have 0% invented
        for st_name in ["STAGE_1_GRADE_1", "STAGE_2_GRADES_2_4", "STAGE_3_GRADES_6_8"]:
            m = traj.stage_metrics.get(st_name)
            if m and m.sample_size > 0:
                assert m.pct_invented == 0.0, f"Primitive {sym} had unexpected invention in {st_name}"

        # Olympiad stage must have 100% invented if primitive appears
        m_olymp = traj.stage_metrics.get("STAGE_4_OLYMPIAD_CIRCLES")
        if m_olymp and m_olymp.sample_size > 0:
            assert m_olymp.pct_invented == 1.0, f"Primitive {sym} was not 100% invented in Olympiads"
            assert traj.invention_onset_stage == "STAGE_4_OLYMPIAD_CIRCLES"


def test_dev2_transfer_demand_progression(dev2_summary: DevelopmentalTransitionSummary):
    """
    Verifies the transfer demand progression:
    - Stage 1: Combination of Same_Form and Near_Transfer.
    - Stage 2: Heavy dominance of Near_Transfer (> 90%).
    - Stage 4: 100% Far_Transfer.
    - Standard school stages (1, 2, 3) have strictly 0.0% Far_Transfer.
    """
    stages = dev2_summary.transfer_demand_by_stage

    s1 = stages["STAGE_1_GRADE_1"]
    assert s1.pct_same_form > 0.20
    assert s1.pct_near_transfer > 0.70
    assert s1.pct_far_transfer == 0.0

    s2 = stages["STAGE_2_GRADES_2_4"]
    assert s2.pct_near_transfer > 0.90
    assert s2.pct_far_transfer == 0.0

    s3 = stages["STAGE_3_GRADES_6_8"]
    assert s3.pct_same_form > 0.50
    assert s3.pct_far_transfer == 0.0

    s4 = stages["STAGE_4_OLYMPIAD_CIRCLES"]
    assert s4.pct_far_transfer == 1.0
    assert s4.pct_same_form == 0.0


def test_dev2_scaffolding_transfer_coupling(dev2_summary: DevelopmentalTransitionSummary):
    """
    Verifies that scaffolding depth strictly predicts transfer demand:
    - PARTIAL scaffolding couples 100% with NEAR_TRANSFER.
    - NONE scaffolding couples 100% with FAR_TRANSFER.
    """
    coupling = dev2_summary.scaffolding_transfer_coupling

    partial = coupling[ScaffoldingDepth.PARTIAL.value]
    assert partial.pct_near_transfer == 1.0
    assert partial.pct_same_form == 0.0
    assert partial.pct_far_transfer == 0.0

    none_scaff = coupling[ScaffoldingDepth.NONE.value]
    assert none_scaff.pct_far_transfer == 1.0
    assert none_scaff.pct_same_form == 0.0
    assert none_scaff.pct_near_transfer == 0.0


def test_dev2_noncommutative_grammar_concordance(dev2_summary: DevelopmentalTransitionSummary):
    """
    Verifies alignment with the M6.2 Noncommutative Methodological Grammar Matrix:
    - 172 directed transitions evaluated.
    - Zero contract-violating / invalid compositions.
    - 100% grammar concordance rate.
    - 100% structure-preserving rate.
    """
    assert dev2_summary.total_directed_transitions == 172
    assert dev2_summary.transitions_evaluated_against_m6_2 == 172
    assert dev2_summary.gamma_level_counts.get("INVALID", 0) == 0
    assert dev2_summary.grammar_concordance_rate == 1.0
    assert dev2_summary.structure_preserving_rate == 1.0


def test_dev2_high_gamma_episodes(dev2_summary: DevelopmentalTransitionSummary):
    """
    Verifies that all transitions with Gamma >= 2 (epistemic / conclusion-changing)
    preserve mathematical structure in both pupil and teacher materials.
    """
    assert dev2_summary.high_gamma_episodes_count >= 5
    assert dev2_summary.high_gamma_concordance_rate == 1.0


def test_dev2_teacher_doctrine_vs_pupil_ordering():
    """
    Verifies that teacher doctrine manuals introduce the invariant first (I -> Sr),
    whereas pupil texts execute state reduction first (Sr -> I).
    """
    engine = DevelopmentalTransitionEngine()
    matches, _ = engine._analyze_educational_grammar_concordance()

    pupil_sr_i = [
        m for m in matches
        if m.primitive_from == "Sr" and m.primitive_to == "I"
    ]
    doctrine_i_sr = [
        m for m in matches
        if m.primitive_from == "I" and m.primitive_to == "Sr"
        and "DOCTRINE" in m.episode_id
    ]

    assert len(pupil_sr_i) >= 4
    assert len(doctrine_i_sr) >= 1
    for m in pupil_sr_i:
        assert m.m6_2_gamma_level == 2
    for m in doctrine_i_sr:
        assert m.m6_2_gamma_level == 2
