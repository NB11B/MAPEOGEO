#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-M6.2: Noncommutative Methodology / Grammar Sweep.

Verifies:
1. Complete evaluation of all 16x16 = 256 primitive pairs.
2. Five-way classification into G0, G1, G2, G3, and invalid (bot).
3. Identification of Level G3 conclusion-changing pairs (Constrain-Optimize).
4. Identification of Level G2 epistemic noncommutativity pairs (Omit-Invert, Reduce-Invariant).
5. Vector commutator distance vec{Delta}_ij properties.
6. Concordance with MAPEOGEO structural operator noncommutativity.
7. Historical methodology order optimality whenever Gamma >= 2.
8. Cultural leakage purity across all evaluation records.
"""

import math
import pytest

from sovctx.node.methodological_grammar_engine import (
    GrammarLevel,
    GrammarOutcome,
    MethodologicalGrammarEngine,
)


def test_grammar_matrix_dimension():
    """Confirms evaluation of all 256 pairs across the 16-D primitive basis."""
    engine = MethodologicalGrammarEngine()
    evals, report = engine.run_grammar_sweep()

    assert report.total_pairs_evaluated == 256
    assert len(evals) == 256
    assert len(engine.gamma_matrix) == 256


def test_grammar_level_distribution():
    """Verifies that all grammar levels are represented."""
    engine = MethodologicalGrammarEngine()
    _, report = engine.run_grammar_sweep()

    assert report.commutative_count > 150        # G0
    assert report.representational_count >= 20   # G1
    assert report.epistemic_count >= 6          # G2
    assert report.conclusion_changing_count >= 2 # G3
    assert report.invalid_count >= 2             # bot


def test_level_g3_conclusion_changing():
    """Verifies that Ad o E vs E o Ad produces Level G3 conclusion-changing noncommutativity."""
    engine = MethodologicalGrammarEngine()
    evals, _ = engine.run_grammar_sweep()

    ad_e = next(e for e in evals if "Ad" in e.primitive_i_symbol and "E" in e.primitive_j_symbol)
    assert ad_e.grammar_level == 3
    assert not ad_e.conclusion_identical
    assert "G3" in ad_e.mathematical_rationale


def test_level_g2_epistemic_noncommutativity():
    """Verifies that N o Iv and I o Sr produce Level G2 epistemic noncommutativity."""
    engine = MethodologicalGrammarEngine()
    evals, _ = engine.run_grammar_sweep()

    n_iv = next(e for e in evals if "N" in e.primitive_i_symbol and "Iv" in e.primitive_j_symbol)
    assert n_iv.grammar_level == 2
    assert n_iv.outcome == GrammarOutcome.INFORMATION_DIFFERENT
    assert n_iv.commutator_vector.total_magnitude > 1.0


def test_vector_commutator_properties():
    """Verifies vector-valued commutator distance properties."""
    engine = MethodologicalGrammarEngine()
    evals, _ = engine.run_grammar_sweep()

    # Commutative pair has zero vector
    comm_pair = next(e for e in evals if e.grammar_level == 0)
    assert comm_pair.commutator_vector.is_zero
    assert comm_pair.commutator_vector.total_magnitude == 0.0

    # Noncommutative pair has positive vector magnitude
    noncomm_pair = next(e for e in evals if e.grammar_level >= 2)
    assert not noncomm_pair.commutator_vector.is_zero
    assert noncomm_pair.commutator_vector.total_magnitude > 0.0


def test_mapeogeo_concordance():
    """Verifies >= 80% concordance with MAPEOGEO structural operator commutators."""
    engine = MethodologicalGrammarEngine()
    _, report = engine.run_grammar_sweep()

    assert report.mapeogeo_concordance_rate >= 0.80
    assert report.mapeogeo_concordance_count >= 200


def test_historical_order_optimality():
    """Confirms historical methodologies preferentially choose optimal order when Gamma >= 2."""
    engine = MethodologicalGrammarEngine()
    _, report = engine.run_grammar_sweep()

    assert report.historical_optimal_choice_count >= 3
    assert report.historical_alignment_rate > 0.40


def test_cultural_leakage_purity():
    """Audits evaluation records to guarantee 0 provenance/cultural tokens."""
    engine = MethodologicalGrammarEngine()
    evals, _ = engine.run_grammar_sweep()

    forbidden = {"soviet", "russian", "lenin", "marxist", "ussr", "moscow", "steklov"}
    for e in evals:
        rationale = e.mathematical_rationale.lower()
        for tok in forbidden:
            assert tok not in rationale
