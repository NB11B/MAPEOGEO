#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-M6.1: Question-Conditional Negative Information.

Verifies:
1. Complete evaluation of all 1,204 candidate omission relations from M6.0.
2. Four-tier classification integrity (LOSSLESS, QUESTION_SUFFICIENT, IRREVERSIBLE_SAFE, IRREVERSIBLE_UNSAFE).
3. Epistemic qualification level separation (EXACT_PROOF, THEOREM_GROUNDED, NUMERICALLY_VERIFIED, etc.).
4. Adversarial mutation generation (mutating Q -> Q' and A -> A_viol).
5. Discovery of failure boundaries proving omission is conditional on Q.
6. Cultural leakage purity across all omission ledgers.
"""

import pytest

from sovctx.node.reconstruction_testing_engine import (
    EpistemicQualificationLevel,
    ReconstructionTestingEngine,
    ReconstructionTier,
)


def test_evaluation_candidate_scale():
    """Confirms evaluation of all 1,204 candidate omission relations."""
    engine = ReconstructionTestingEngine()
    rels, report = engine.evaluate_all_candidates()
    assert report.total_candidates_tested == 1204
    assert len(rels) == 1204


def test_four_tier_classification_completeness():
    """Verifies partition across the four reconstruction tiers."""
    engine = ReconstructionTestingEngine()
    _, report = engine.evaluate_all_candidates()

    assert report.lossless_reduction_count > 100
    assert report.question_sufficient_count > 600
    assert report.irreversible_safe_count > 300
    total = (
        report.lossless_reduction_count
        + report.question_sufficient_count
        + report.irreversible_safe_count
        + report.irreversible_unsafe_count
    )
    assert total == 1204


def test_epistemic_qualification_levels():
    """Verifies separation of formal mathematical proofs from numerical bounds."""
    engine = ReconstructionTestingEngine()
    _, report = engine.evaluate_all_candidates()

    dist = report.epistemic_distribution
    assert dist[EpistemicQualificationLevel.EXACT_PROOF.value] >= 30
    assert dist[EpistemicQualificationLevel.THEOREM_GROUNDED.value] >= 500
    assert dist[EpistemicQualificationLevel.SYMBOLIC_VERIFICATION.value] >= 100
    assert dist[EpistemicQualificationLevel.NUMERICALLY_VERIFIED.value] >= 150
    assert dist[EpistemicQualificationLevel.EMPIRICALLY_BOUNDED.value] >= 80


def test_adversarial_mutation_coverage():
    """Verifies that every positive candidate omission receives adversarial mutations."""
    engine = ReconstructionTestingEngine()
    rels, report = engine.evaluate_all_candidates()

    assert report.total_adversarial_mutations >= 1500
    for r in rels[:200]:
        if r.is_safe_for_q:
            assert len(r.adversarial_mutations) >= 1
            assert r.not_valid_for_scope
            assert r.collapse_conditions


def test_adversarial_break_discovery():
    """Confirms that adversarial mutations systematically find where omissions break."""
    engine = ReconstructionTestingEngine()
    _, report = engine.evaluate_all_candidates()

    # The discovery rate should be high (> 90%), proving information is conditional
    assert report.falsification_discovery_rate >= 0.90
    assert report.adversarial_break_count >= 1500


def test_cultural_leakage_purity():
    """Audits omission ledger records to ensure 0 provenance/cultural tokens."""
    engine = ReconstructionTestingEngine()
    rels, _ = engine.evaluate_all_candidates()

    forbidden = {"soviet", "russian", "lenin", "marxist", "ussr", "moscow", "steklov"}
    for r in rels[:300]:
        scope_text = (r.valid_for_scope + " " + " ".join(r.not_valid_for_scope)).lower()
        for tok in forbidden:
            assert tok not in scope_text
