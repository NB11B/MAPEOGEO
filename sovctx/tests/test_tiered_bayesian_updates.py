"""Tests for Tiered Bayesian Evidence Updating and Epistemic Separation."""

from __future__ import annotations

import pytest

from sovctx.node.prospective_control import (
    EVIDENCE_TIER_LIKELIHOODS,
    EpistemicEvidenceTier,
    HypothesisBeliefSpace,
    HypothesisStatus,
    ResearchHypothesis,
)


def test_epistemic_evidence_tier_likelihood_values() -> None:
    """Verifies calibrated likelihood values across all 6 evidence tiers."""
    assert EVIDENCE_TIER_LIKELIHOODS[EpistemicEvidenceTier.PRIMARY_EXPLICIT] == 0.90
    assert EVIDENCE_TIER_LIKELIHOODS[EpistemicEvidenceTier.PRIMARY_IMPLICIT] == 0.70
    assert EVIDENCE_TIER_LIKELIHOODS[EpistemicEvidenceTier.SECONDARY_CORROBORATED] == 0.60
    assert EVIDENCE_TIER_LIKELIHOODS[EpistemicEvidenceTier.STRUCTURAL_MATCH] == 0.35
    assert EVIDENCE_TIER_LIKELIHOODS[EpistemicEvidenceTier.ORAL_PROVENANCE] == 0.20
    assert EVIDENCE_TIER_LIKELIHOODS[EpistemicEvidenceTier.CONTRADICTORY_PRIMARY] == 0.90


def test_primary_explicit_updates_to_confirmed() -> None:
    """Primary explicit evidence (0.90) elevates prior 0.50 directly to CONFIRMED (0.90 >= 0.88)."""
    h = ResearchHypothesis(hypothesis_id="HYP:TEST", label="Test", description="Test", prior=0.50)
    belief = HypothesisBeliefSpace([h])

    new_p = belief.update_hypothesis("HYP:TEST", "SUPPORT", evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT, fragment_id="FRAG:1")
    assert new_p == pytest.approx(0.90, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.CONFIRMED


def test_secondary_corroborated_requires_multi_source() -> None:
    """Secondary corroborated evidence (0.60) does not immediately confirm; requires multi-source convergence."""
    h = ResearchHypothesis(hypothesis_id="HYP:TEST", label="Test", description="Test", prior=0.50)
    belief = HypothesisBeliefSpace([h])

    # 1. First secondary source: 0.50 -> 0.60 (UNRESOLVED)
    p1 = belief.update_hypothesis("HYP:TEST", "SUPPORT", evidence_tier=EpistemicEvidenceTier.SECONDARY_CORROBORATED, fragment_id="FRAG:SEC_1")
    assert p1 == pytest.approx(0.60, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.UNRESOLVED

    # 2. Second secondary source: 0.60 -> 0.692 (UNRESOLVED)
    p2 = belief.update_hypothesis("HYP:TEST", "SUPPORT", evidence_tier=EpistemicEvidenceTier.SECONDARY_CORROBORATED, fragment_id="FRAG:SEC_2")
    assert p2 == pytest.approx(0.6923, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.UNRESOLVED

    # 3. Third secondary source: 0.6923 -> 0.7714 (UNRESOLVED)
    p3 = belief.update_hypothesis("HYP:TEST", "SUPPORT", evidence_tier=EpistemicEvidenceTier.SECONDARY_CORROBORATED, fragment_id="FRAG:SEC_3")
    assert p3 == pytest.approx(0.7714, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.UNRESOLVED

    # 4. Fourth secondary source: 0.7714 -> 0.8349 (UNRESOLVED)
    p4 = belief.update_hypothesis("HYP:TEST", "SUPPORT", evidence_tier=EpistemicEvidenceTier.SECONDARY_CORROBORATED, fragment_id="FRAG:SEC_4")
    assert p4 == pytest.approx(0.8349, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.UNRESOLVED

    # 5. Fifth secondary source: 0.8349 -> 0.8835 (CONFIRMED >= 0.88)
    p5 = belief.update_hypothesis("HYP:TEST", "SUPPORT", evidence_tier=EpistemicEvidenceTier.SECONDARY_CORROBORATED, fragment_id="FRAG:SEC_5")
    assert p5 == pytest.approx(0.8835, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.CONFIRMED


def test_structural_match_provides_partial_weight() -> None:
    """Structural match (0.35) alone cannot confirm hypothesis."""
    h = ResearchHypothesis(hypothesis_id="HYP:TEST", label="Test", description="Test", prior=0.50)
    belief = HypothesisBeliefSpace([h])

    p1 = belief.update_hypothesis("HYP:TEST", "SUPPORT", evidence_tier=EpistemicEvidenceTier.STRUCTURAL_MATCH)
    assert p1 == pytest.approx(0.35, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.UNRESOLVED


def test_contradictory_primary_refutes_immediately() -> None:
    """Contradictory primary source drives hypothesis down to REFUTED (0.10 <= 0.12)."""
    h = ResearchHypothesis(hypothesis_id="HYP:TEST", label="Test", description="Test", prior=0.50)
    belief = HypothesisBeliefSpace([h])

    p1 = belief.update_hypothesis("HYP:TEST", "REFUTE", evidence_tier=EpistemicEvidenceTier.CONTRADICTORY_PRIMARY, fragment_id="FRAG:DISPROOF")
    assert p1 == pytest.approx(0.10, abs=1e-3)
    assert belief.hypotheses["HYP:TEST"].status == HypothesisStatus.REFUTED
