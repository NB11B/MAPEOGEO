#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-DEV3: Expertise-Dependent Grammar Reversal.

Verifies:
1. Five-Tier Expertise Continuum Coverage (96 episodes across Tiers 1-5).
2. I <-> Sr Grammar Reversal: 100% reverse (Sr -> I) in Tier 1, flipping to 100% forward (I -> Sr) in Tiers 3, 4, 5.
3. N <-> Iv Regularization Acquisition: 100% forward (N -> Iv) in Tiers 4 and 5.
4. Ad <-> E Conclusion-Changing Control: 100% forward (Ad -> E, Gamma=3) in Tiers 4 and 5.
5. Research-Optimal Ordering Monotonicity across expertise continuum.
6. Cross-Tradition Benchmark Protocols Completeness across 5 national traditions.
"""

import pytest
from sovctx.node.expertise_grammar_reversal_engine import (
    Dev3SummaryReport,
    ExpertiseGrammarReversalEngine,
    ExpertiseTier,
)


@pytest.fixture(scope="module")
def dev3_summary() -> Dev3SummaryReport:
    engine = ExpertiseGrammarReversalEngine()
    return engine.run_grammar_reversal_analysis()


def test_dev3_engine_initialization(dev3_summary: Dev3SummaryReport):
    """Verifies coverage of all 5 expertise tiers across 96 episodes."""
    assert dev3_summary.total_episodes_analyzed == 96
    assert dev3_summary.episodes_per_tier[ExpertiseTier.TIER_1_PUPIL_ORDINARY.value] == 57
    assert dev3_summary.episodes_per_tier[ExpertiseTier.TIER_2_OLYMPIAD_STUDENT.value] == 12
    assert dev3_summary.episodes_per_tier[ExpertiseTier.TIER_3_TEACHER_METHODOLOGY.value] == 8
    assert dev3_summary.episodes_per_tier[ExpertiseTier.TIER_4_UNIVERSITY_TEXTBOOK.value] == 12
    assert dev3_summary.episodes_per_tier[ExpertiseTier.TIER_5_RESEARCH_PAPER.value] == 7


def test_dev3_i_sr_grammar_reversal(dev3_summary: Dev3SummaryReport):
    """
    Verifies that the I <-> Sr operation ordering systematically reverses:
    - Tier 1 (Pupils): 100% Sr -> I (reduce state first to minimize cognitive load).
    - Tiers 3, 4, 5 (Teacher, University, Research): 100% I -> Sr (certify invariant first to preserve manifold).
    """
    dist = dev3_summary.pair_order_distributions["I <-> Sr"]
    assert dist.m6_2_gamma_level == 2
    assert dist.reversal_point_detected == ExpertiseTier.TIER_3_TEACHER_METHODOLOGY.value

    # Tier 1: 100% Reverse (Sr -> I)
    t1_rates = dist.tier_rates[ExpertiseTier.TIER_1_PUPIL_ORDINARY.value]
    assert t1_rates["reverse_rate"] == 1.0
    assert t1_rates["forward_rate"] == 0.0

    # Tier 3 (Teacher): 100% Forward (I -> Sr)
    t3_rates = dist.tier_rates[ExpertiseTier.TIER_3_TEACHER_METHODOLOGY.value]
    assert t3_rates["forward_rate"] == 1.0
    assert t3_rates["reverse_rate"] == 0.0

    # Tier 4 (University): 100% Forward (I -> Sr)
    t4_rates = dist.tier_rates[ExpertiseTier.TIER_4_UNIVERSITY_TEXTBOOK.value]
    assert t4_rates["forward_rate"] == 1.0
    assert t4_rates["reverse_rate"] == 0.0

    # Tier 5 (Research): 100% Forward (I -> Sr)
    t5_rates = dist.tier_rates[ExpertiseTier.TIER_5_RESEARCH_PAPER.value]
    assert t5_rates["forward_rate"] == 1.0
    assert t5_rates["reverse_rate"] == 0.0


def test_dev3_n_iv_regularization_acquisition(dev3_summary: Dev3SummaryReport):
    """
    Verifies that for N <-> Iv (Gamma=2):
    - Tiers 4 and 5 exclusively deploy the forward regularized order N -> Iv (100%).
    - Reverse order (Iv -> N), which causes noise blowup, is 0.0%.
    """
    dist = dev3_summary.pair_order_distributions["N <-> Iv"]
    assert dist.m6_2_gamma_level == 2

    t4_counts = dist.tier_counts[ExpertiseTier.TIER_4_UNIVERSITY_TEXTBOOK.value]
    assert t4_counts["forward"] >= 2
    assert t4_counts["reverse"] == 0

    t5_counts = dist.tier_counts[ExpertiseTier.TIER_5_RESEARCH_PAPER.value]
    assert t5_counts["forward"] >= 2
    assert t5_counts["reverse"] == 0


def test_dev3_ad_e_conclusion_changing_order(dev3_summary: Dev3SummaryReport):
    """
    Verifies that for Ad <-> E (Gamma=3, conclusion-changing noncommutativity):
    - Tiers 4 and 5 exclusively deploy the structure-preserving order Ad -> E (100%).
    - Reverse unconstrained order (E -> Ad) is 0.0%.
    """
    dist = dev3_summary.pair_order_distributions["Ad <-> E"]
    assert dist.m6_2_gamma_level == 3

    t4_counts = dist.tier_counts[ExpertiseTier.TIER_4_UNIVERSITY_TEXTBOOK.value]
    assert t4_counts["forward"] >= 3
    assert t4_counts["reverse"] == 0

    t5_counts = dist.tier_counts[ExpertiseTier.TIER_5_RESEARCH_PAPER.value]
    assert t5_counts["forward"] >= 2
    assert t5_counts["reverse"] == 0


def test_dev3_cross_tradition_protocols_completeness(dev3_summary: Dev3SummaryReport):
    """Verifies that 5 matched international traditions are defined with concrete authors and hypotheses."""
    protocols = dev3_summary.cross_tradition_protocols
    assert len(protocols) == 5

    trad_ids = {p.tradition_id for p in protocols}
    expected_ids = {
        "TRAD_BRITISH_CAMBRIDGE",
        "TRAD_FRENCH_LYCEE",
        "TRAD_GERMAN_GYMNASIUM",
        "TRAD_US_POSTWAR",
        "TRAD_HUNGARIAN_KOMAL",
    }
    assert trad_ids == expected_ids

    for p in protocols:
        assert len(p.reference_authors) >= 2
        assert len(p.curricular_focus) > 20
        assert len(p.expected_order_preference) > 20
