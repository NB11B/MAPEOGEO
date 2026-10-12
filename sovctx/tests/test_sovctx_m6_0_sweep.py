#!/usr/bin/env python3
"""
Unit Test Suite for Milestone SOVCTX-M6.0: Graph-Wide Mathematical Perspective Sweep.

Verifies:
1. Extraction of formal mathematical subjects from G_M (equations, families, operators, invariants, assumptions, problems).
2. Domain-rigorous mathematical question set generation Q(X).
3. Type-contract compatibility selectivity (rejecting invalid combinations).
4. Structured enrichment vector extraction vec{K} = (K_inv, K_aux, K_omit, K_cons, K_quest, K_comp).
5. Composed primitive sweep P^2 validity under M4 partial composition matrix.
6. Absolute cultural/historical leakage purity during mathematical evaluation.
"""

import pytest

from sovctx.node.graph_perspective_sweep import (
    GraphPerspectiveSweepEngine,
    MathematicalDomain,
    QuestionCategory,
)


def test_mathematical_subject_extraction():
    """Confirms extraction of >= 130 formal mathematical subjects across G_M."""
    engine = GraphPerspectiveSweepEngine()
    assert len(engine.subjects) >= 130
    types = {s.subject_type for s in engine.subjects.values()}
    assert "EQUATION" in types
    assert "EQUATION_FAMILY" in types
    assert "OPERATOR" in types
    assert "INVARIANT" in types
    assert "ASSUMPTION" in types
    assert "PROBLEM" in types


def test_question_generation_coverage():
    """Verifies that every subject receives well-formed mathematical questions."""
    engine = GraphPerspectiveSweepEngine()
    for s in engine.subjects.values():
        assert len(s.questions) >= 2
        for q in s.questions:
            assert q.id.startswith("Q:")
            assert q.formal_statement
            assert q.preservation_criterion in {"EXACT", "INVARIANT", "APPROXIMATE", "QUALITATIVE"}


def test_contract_selectivity():
    """Confirms that lens and primitive contracts are selective (not accepting or rejecting trivially)."""
    engine = GraphPerspectiveSweepEngine()
    evals, report = engine.run_sweep()

    # Selectivity between 15% and 50%
    assert 0.15 <= report.lens_compatibility_rate <= 0.50
    assert 0.15 <= report.primitive_compatibility_rate <= 0.50
    assert report.compatible_lens_evaluations > 1000
    assert report.compatible_primitive_evaluations > 1500


def test_enrichment_structure():
    """Confirms that compatible evaluations generate full 6-dimensional enrichment vectors."""
    engine = GraphPerspectiveSweepEngine()
    evals, _ = engine.run_sweep()
    compat_evals = [e for e in evals if e.is_contract_compatible and e.enrichment is not None]

    assert len(compat_evals) > 0
    sample = compat_evals[0]
    enrich = sample.enrichment
    assert enrich.k_inv
    assert enrich.k_aux
    assert enrich.k_omit
    assert enrich.k_cons
    assert enrich.k_quest
    assert enrich.k_comp


def test_primitive_composition_sweep():
    """Verifies that P^2 compositions are successfully evaluated and tracked."""
    engine = GraphPerspectiveSweepEngine()
    evals, report = engine.run_sweep()

    assert report.total_composition_evaluations > 50000
    assert report.compatible_composition_evaluations > 5000


def test_cultural_leakage_purity():
    """Audits evaluation outputs for 0 cultural/historical provenance tokens."""
    engine = GraphPerspectiveSweepEngine()
    evals, _ = engine.run_sweep()

    forbidden = {"soviet", "russian", "lenin", "marxist", "ussr", "moscow", "steklov"}
    for e in evals[:500]:
        reason_lower = e.compatibility_reason.lower()
        for tok in forbidden:
            assert tok not in reason_lower
