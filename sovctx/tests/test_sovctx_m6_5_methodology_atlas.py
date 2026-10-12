#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-M6.5 Methodology Atlas Engine.
"""

import pytest
from sovctx.node.graph_perspective_sweep import GraphPerspectiveSweepEngine
from sovctx.node.methodology_atlas_engine import (
    AtlasSummaryReport,
    DomainEnrichmentProfile,
    MathematicalDomain,
    MethodologyAtlasEngine,
)


@pytest.fixture
def atlas_engine() -> MethodologyAtlasEngine:
    return MethodologyAtlasEngine()


def test_atlas_engine_initialization(atlas_engine: MethodologyAtlasEngine):
    assert len(atlas_engine.domains) == 6
    assert MathematicalDomain.DYNAMICAL_SYSTEMS in atlas_engine.domains
    assert MathematicalDomain.INVERSE_PROBLEMS in atlas_engine.domains
    assert MathematicalDomain.VARIATIONAL_OPTIMAL_CONTROL in atlas_engine.domains
    assert MathematicalDomain.KINETIC_DISPERSIVE_WAVES in atlas_engine.domains
    assert MathematicalDomain.SPECTRAL_APPROXIMATION in atlas_engine.domains
    assert MathematicalDomain.GEOMETRIC_ALGEBRAIC in atlas_engine.domains


def test_atlas_synthesis_on_gm(atlas_engine: MethodologyAtlasEngine):
    sweep_engine = GraphPerspectiveSweepEngine()
    subjects = [s.to_dict() for s in sweep_engine.subjects.values()]

    report = atlas_engine.synthesize_atlas(subjects)
    assert report.total_subjects_evaluated == 134
    assert report.total_questions_evaluated == 421
    assert report.baseline_features_total > 1000
    assert report.total_discovered_structure > 4000
    assert report.enriched_features_total > report.baseline_features_total
    assert report.global_structural_gain_ratio > 4.0
    assert len(report.domain_profiles) == 6
    assert report.provenance_isolated is True
    assert report.cultural_leakage_detected is False


def test_domain_enrichment_profiles(atlas_engine: MethodologyAtlasEngine):
    sweep_engine = GraphPerspectiveSweepEngine()
    subjects = [s.to_dict() for s in sweep_engine.subjects.values()]

    report = atlas_engine.synthesize_atlas(subjects)
    for prof in report.domain_profiles:
        assert prof.subject_count > 0
        assert prof.question_count > 0
        assert prof.omission_relations_certified > 0
        assert prof.revealed_representation_features > 0
        assert prof.structural_gain_ratio > 3.0


def test_cultural_leakage_purity(atlas_engine: MethodologyAtlasEngine):
    sweep_engine = GraphPerspectiveSweepEngine()
    subjects = [s.to_dict() for s in sweep_engine.subjects.values()]
    report = atlas_engine.synthesize_atlas(subjects)
    assert report.provenance_isolated is True
    assert report.cultural_leakage_detected is False
