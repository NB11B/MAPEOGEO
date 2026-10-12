#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-M6.4 Perspective Emergence Discovery Engine.
"""

import pytest
from sovctx.node.perspective_emergence_engine import (
    CombinationMode,
    EmergenceClassification,
    EmergenceEvaluationResult,
    EmergentProperty,
    PerspectiveEmergenceEngine,
    SynergyPairContract,
)


@pytest.fixture
def emergence_engine() -> PerspectiveEmergenceEngine:
    return PerspectiveEmergenceEngine()


def test_synergy_catalog_completeness(emergence_engine: PerspectiveEmergenceEngine):
    synergies = emergence_engine.list_synergies()
    assert len(synergies) >= 7
    ids = {s.pair_id for s in synergies}
    assert "SYN-LAX-INVERSE-SCATTERING" in ids
    assert "SYN-KAM-HAMILTONIAN-DIOPHANTINE" in ids
    assert "SYN-PONTRYAGIN-LYAPUNOV-CLF" in ids
    assert "SYN-BBGKY-KINETIC-CLOSURE" in ids
    assert "SYN-MOROZOV-DISCREPANCY-REGULARIZATION" in ids
    assert "SYN-INDEPENDENT-COORDINATE-ROTATION" in ids
    assert "SYN-REDUNDANT-REDUCTION" in ids


def test_landmark_lax_pair_emergence(emergence_engine: PerspectiveEmergenceEngine):
    lax = emergence_engine.get_synergy("SYN-LAX-INVERSE-SCATTERING")
    assert lax is not None
    assert lax.classification == EmergenceClassification.SYNERGISTIC_EMERGENCE
    assert len(lax.emergent_properties) == 3
    emergent_labels = {p.label for p in lax.emergent_properties}
    assert "Isospectral Lax Pair Evolution Operator" in emergent_labels
    assert "Infinite Hierarchy of Commuting First Integrals in Involution" in emergent_labels
    assert "Exact N-Soliton Elastic Collision Phase Shift Formula" in emergent_labels


def test_landmark_kam_invariance_emergence(emergence_engine: PerspectiveEmergenceEngine):
    kam = emergence_engine.get_synergy("SYN-KAM-HAMILTONIAN-DIOPHANTINE")
    assert kam is not None
    assert kam.classification == EmergenceClassification.SYNERGISTIC_EMERGENCE
    assert len(kam.emergent_properties) == 3
    emergent_labels = {p.label for p in kam.emergent_properties}
    assert "Persistent Invariant Quasi-Periodic KAM Tori of Positive Measure" in emergent_labels
    assert "Quadratic Superconvergence Coordinate Scheme" in emergent_labels
    assert "Cantor-Like Phase Space Foliation Boundary" in emergent_labels


def test_landmark_clf_synthesis_emergence(emergence_engine: PerspectiveEmergenceEngine):
    clf = emergence_engine.get_synergy("SYN-PONTRYAGIN-LYAPUNOV-CLF")
    assert clf is not None
    assert clf.classification == EmergenceClassification.SYNERGISTIC_EMERGENCE
    assert len(clf.emergent_properties) == 3
    emergent_labels = {p.label for p in clf.emergent_properties}
    assert "Control Lyapunov Function (CLF) Universal Value Field" in emergent_labels
    assert "Sontag Analytic Closed-Loop Feedback Control Law" in emergent_labels
    assert "Hamilton-Jacobi-Bellman Viscosity Solution Uniqueness" in emergent_labels


def test_landmark_bbgky_closure_emergence(emergence_engine: PerspectiveEmergenceEngine):
    bbgky = emergence_engine.get_synergy("SYN-BBGKY-KINETIC-CLOSURE")
    assert bbgky is not None
    assert bbgky.classification == EmergenceClassification.SYNERGISTIC_EMERGENCE
    assert len(bbgky.emergent_properties) == 3
    emergent_labels = {p.label for p in bbgky.emergent_properties}
    assert "Boltzmann Collision Integral & Stosszahlansatz Validity Boundary" in emergent_labels
    assert "Boltzmann H-Theorem Irreversible Entropy Production" in emergent_labels


def test_landmark_morozov_discrepancy_emergence(emergence_engine: PerspectiveEmergenceEngine):
    mor = emergence_engine.get_synergy("SYN-MOROZOV-DISCREPANCY-REGULARIZATION")
    assert mor is not None
    assert mor.classification == EmergenceClassification.SYNERGISTIC_EMERGENCE
    assert len(mor.emergent_properties) == 3
    emergent_labels = {p.label for p in mor.emergent_properties}
    assert "Morozov Discrepancy Principle Root Equation" in emergent_labels
    assert "Minimax Order-Optimal Convergence Rate" in emergent_labels


def test_three_tier_classification_coverage(emergence_engine: PerspectiveEmergenceEngine):
    synergies = emergence_engine.list_synergies()
    classes = {s.classification for s in synergies}
    assert EmergenceClassification.SYNERGISTIC_EMERGENCE in classes
    assert EmergenceClassification.INDEPENDENT_SUPERPOSITION in classes
    assert EmergenceClassification.SUB_ADDITIVE_REDUNDANCY in classes


def test_graph_sweep_emergence_discovery(emergence_engine: PerspectiveEmergenceEngine):
    mock_subjects = [
        {
            "id": "SUBJ_DYN_01",
            "label": "Hamiltonian Perturbed System",
            "domain": "DYNAMICAL_SYSTEMS",
        },
        {
            "id": "SUBJ_INV_01",
            "label": "Fredholm Ill-Posed Inverse Problem",
            "domain": "INVERSE_PROBLEMS",
        },
        {
            "id": "SUBJ_KIN_01",
            "label": "Vlasov-Poisson Kinetic Plasma",
            "domain": "KINETIC_DISPERSIVE_WAVES",
        },
    ]

    evaluations, summary = emergence_engine.sweep_graph_subjects(mock_subjects)
    assert len(evaluations) >= 9
    assert summary.total_subjects_evaluated == 3
    assert summary.synergistic_emergence_count >= 6
    assert summary.total_emergent_features_discovered > 0
    assert summary.provenance_isolated is True
    assert summary.cultural_leakage_detected is False


def test_cultural_leakage_purity(emergence_engine: PerspectiveEmergenceEngine):
    synergies = emergence_engine.list_synergies()
    forbidden = ["soviet", "russian", "western", "marxist", "lenin", "cold_war"]
    for s in synergies:
        text = f"{s.pair_id} {s.label} {s.notes}".lower()
        for tok in forbidden:
            assert tok not in text, f"Cultural leakage '{tok}' found in synergy {s.pair_id}"
