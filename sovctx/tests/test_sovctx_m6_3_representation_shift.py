#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-M6.3 Representation-Shift Discovery Engine.
"""

import pytest
from sovctx.node.representation_shift_engine import (
    DecidabilityStatus,
    RepresentationCategory,
    RepresentationShiftContract,
    RepresentationShiftEngine,
    ShiftClassification,
    ShiftEvaluationResult,
)


@pytest.fixture
def shift_engine() -> RepresentationShiftEngine:
    return RepresentationShiftEngine()


def test_canonical_shift_catalog_completeness(shift_engine: RepresentationShiftEngine):
    shifts = shift_engine.list_shifts()
    assert len(shifts) >= 10
    shift_ids = {s.shift_id for s in shifts}
    assert "SHIFT-LYAPUNOV-POTENTIAL" in shift_ids
    assert "SHIFT-PONTRYAGIN-COSTATE" in shift_ids
    assert "SHIFT-MARCHENKO-KERNEL" in shift_ids
    assert "SHIFT-VLASOV-KINETIC" in shift_ids
    assert "SHIFT-GRASSMANNIAN-SUBSPACE" in shift_ids
    assert "SHIFT-CASIMIR-QUOTIENT" in shift_ids
    assert "SHIFT-FOURIER-DUALITY" in shift_ids
    assert "SHIFT-OPERATOR-SVD" in shift_ids
    assert "SHIFT-ISOMORPHIC-ROTATION" in shift_ids
    assert "SHIFT-ABSTRACTION-DOWNSAMPLE" in shift_ids


def test_four_landmark_shifts_present(shift_engine: RepresentationShiftEngine):
    landmarks = [
        "SHIFT-LYAPUNOV-POTENTIAL",
        "SHIFT-PONTRYAGIN-COSTATE",
        "SHIFT-MARCHENKO-KERNEL",
        "SHIFT-VLASOV-KINETIC",
    ]
    for lid in landmarks:
        shift = shift_engine.get_shift(lid)
        assert shift is not None
        assert shift.classification == ShiftClassification.STRUCTURE_REVEALING
        assert len(shift.revealed_structure) >= 2
        assert len(shift.preserved_invariants) >= 2


def test_lyapunov_shift_structure(shift_engine: RepresentationShiftEngine):
    shift = shift_engine.get_shift("SHIFT-LYAPUNOV-POTENTIAL")
    assert shift is not None
    assert shift.source_rep == RepresentationCategory.STATE_TRAJECTORY
    assert shift.target_rep == RepresentationCategory.SCALAR_POTENTIAL
    assert not shift.is_invertible

    revealed_labels = {p.label for p in shift.revealed_structure}
    assert "Global Basin of Attraction Boundary" in revealed_labels
    assert "Uniform Contraction Metric & Decay Rate" in revealed_labels

    concealed_labels = {p.label for p in shift.concealed_structure}
    assert "Exact Pointwise Trajectory Coordinates" in concealed_labels

    assert shift.decidability_transition == DecidabilityStatus.INTRACTABLE_TO_DECIDABLE


def test_pontryagin_shift_structure(shift_engine: RepresentationShiftEngine):
    shift = shift_engine.get_shift("SHIFT-PONTRYAGIN-COSTATE")
    assert shift is not None
    assert shift.source_rep == RepresentationCategory.STATE_TRAJECTORY
    assert shift.target_rep == RepresentationCategory.COTANGENT_PHASE_SPACE
    assert shift.is_invertible  # Canonical projection pi: T*M -> M recovers primal

    revealed_labels = {p.label for p in shift.revealed_structure}
    assert "Hamiltonian Conservation First Integral" in revealed_labels
    assert "Pointwise Extremal Control Characterization" in revealed_labels


def test_marchenko_and_vlasov_landmarks(shift_engine: RepresentationShiftEngine):
    marc = shift_engine.get_shift("SHIFT-MARCHENKO-KERNEL")
    assert marc is not None
    assert marc.source_rep == RepresentationCategory.SCATTERING_SPECTRAL_DATA
    assert marc.target_rep == RepresentationCategory.INTEGRAL_KERNEL
    revealed_marc = {p.label for p in marc.revealed_structure}
    assert "Direct Spatial Potential Profile" in revealed_marc

    vlas = shift_engine.get_shift("SHIFT-VLASOV-KINETIC")
    assert vlas is not None
    assert vlas.source_rep == RepresentationCategory.PARTICLE_ENSEMBLE
    assert vlas.target_rep == RepresentationCategory.KINETIC_DISTRIBUTION
    revealed_vlas = {p.label for p in vlas.revealed_structure}
    assert "Collisionless Landau Damping Resonances" in revealed_vlas
    assert "Collective Plasma Dispersion Relation" in revealed_vlas


def test_four_tier_classification_coverage(shift_engine: RepresentationShiftEngine):
    shifts = shift_engine.list_shifts()
    classes = {s.classification for s in shifts}
    assert ShiftClassification.STRUCTURE_REVEALING in classes
    assert ShiftClassification.ISOMORPHIC_TRANSLATION in classes
    assert ShiftClassification.ABSTRACTION_COLLAPSE in classes
    assert ShiftClassification.COMPLEMENTARY_DUALITY in classes


def test_graph_sweep_execution(shift_engine: RepresentationShiftEngine):
    mock_subjects = [
        {
            "id": "SUBJ_DYN_01",
            "label": "Nonlinear Duffing Oscillator",
            "domain": "DYNAMICAL_SYSTEMS",
            "questions": [
                {"id": "Q_DYN_01", "label": "Global limit cycle stability"}
            ],
        },
        {
            "id": "SUBJ_INV_01",
            "label": "Schroedinger Inverse Potential Identification",
            "domain": "INVERSE_PROBLEMS",
            "questions": [
                {"id": "Q_INV_01", "label": "Reconstruction of compact potential"}
            ],
        },
        {
            "id": "SUBJ_KIN_01",
            "label": "Vlasov-Poisson Plasma System",
            "domain": "KINETIC_DISPERSIVE_WAVES",
            "questions": [
                {"id": "Q_KIN_01", "label": "Landau damping decay exponent"}
            ],
        },
    ]

    evaluations, summary = shift_engine.sweep_graph_subjects(mock_subjects)
    assert len(evaluations) >= 9
    assert summary.total_subjects_evaluated == 3
    assert summary.structure_revealing_count >= 6
    assert summary.revealed_features_total > 0
    assert summary.provenance_isolated is True
    assert summary.cultural_leakage_detected is False


def test_cultural_leakage_purity(shift_engine: RepresentationShiftEngine):
    shifts = shift_engine.list_shifts()
    forbidden = ["soviet", "russian", "western", "marxist", "lenin", "cold_war"]
    for s in shifts:
        text = f"{s.shift_id} {s.label} {s.transformation_morphism} {s.notes}".lower()
        for tok in forbidden:
            assert tok not in text, f"Cultural leakage '{tok}' found in shift {s.shift_id}"
