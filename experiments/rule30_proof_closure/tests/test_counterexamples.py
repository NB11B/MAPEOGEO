"""Tests for Section 5 decoupling counterexamples and Section 8 diagnostic failure ledger."""

from __future__ import annotations

from experiments.rule30_proof_closure.bilateral import (
    FailureCategory,
    build_failed_claims_ledger,
    verify_checkpoint_02_bilateral_soundness,
)


def test_section_5_decoupling_counterexamples():
    passed, cex_list = verify_checkpoint_02_bilateral_soundness()
    assert passed is True
    assert len(cex_list) >= 2
    c0 = cex_list[0]
    assert c0.transient_t == 1
    assert c0.word == "01"
    assert c0.left_only_unsat_horizon == 8
    assert c0.bilateral_unsat_horizon == 1
    assert c0.obs_left[0] != c0.obs_right[0]


def test_section_8_failed_claims_diagnostic_ledger():
    ledger = build_failed_claims_ledger()
    categories = {item.category for item in ledger}
    assert FailureCategory.INSUFFICIENT_STATE_REPRESENTATION in categories
    assert FailureCategory.FALSE_PROPOSED_INVARIANT in categories
    assert FailureCategory.INCOMPLETE_CONSTRAINT_MODEL in categories
    assert FailureCategory.COMPUTATIONAL_EXPLOSION in categories
    assert FailureCategory.GENUINE_UNRESOLVED_GLOBAL_STATEMENT in categories
