#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-M4: Typed Partial Composition Algebra.
Verifies the 16-primitive basis, 256 composition matrix, commutators,
canonical normal forms, 7 MAPEOGEO closure gates, 6 UNO Q falsification attacks,
historical reconstruction recall (>= 0.8), and novel synthetic lens qualification.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from sovctx.node.perspective_synthesis import (
    PerspectiveSynthesisEngine,
    MethodPrimitive,
    PrimitiveCompositionRecord,
    LensNormalFormRule,
    SyntheticLensRecord,
    ClosureGateReport,
    EpistemicUtilityReport,
    FalsificationAttackReport,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def engine() -> PerspectiveSynthesisEngine:
    return PerspectiveSynthesisEngine()


def test_16_primitive_vocabulary_and_typed_contracts(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies that the frozen 16-dimensional vocabulary has complete typed contracts."""
    expected_symbols = {
        "Rs", "Ax", "Ad", "I", "N", "G", "L", "F", "Iv", "Ds", "Ii", "Sr", "Sa", "C", "E", "Sc"
    }
    assert len(engine.primitives) == 16
    assert set(engine.symbol_to_id.keys()) == expected_symbols

    for prim_id, p in engine.primitives.items():
        assert isinstance(p, MethodPrimitive)
        assert p.id.startswith("PRIM:")
        assert len(p.symbol) in (1, 2)
        assert len(p.label) > 3
        assert len(p.description) > 15
        assert len(p.input_state_type) > 3
        assert len(p.output_state_type) > 3
        assert len(p.preconditions) >= 1
        assert len(p.preserved_invariants) >= 1
        assert len(p.introduced_structures) >= 1
        assert len(p.omitted_information) >= 1
        assert p.complexity_weight > 0.0
        assert p.verification_status == "verified_scan"


def test_256_pairwise_composition_matrix_and_commutators(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies the 16x16 = 256 pairwise composition matrix and non-commutative commutators."""
    assert len(engine.compositions) == 256

    statuses = set()
    comm_types = set()
    for (p1, p2), comp in engine.compositions.items():
        assert isinstance(comp, PrimitiveCompositionRecord)
        statuses.add(comp.composition_status)
        comm_types.add(comp.commutation_type)
        assert len(comp.notes) > 5

    # Partial composition discipline: not all pairs compose
    assert "CONFLICT" in statuses
    assert "INCOMPATIBLE" in comm_types
    assert "ORDER_SENSITIVE" in comm_types
    assert "COMMUTES" in comm_types
    assert "ONE_DIRECTION_ONLY" in comm_types

    # Specific commutator tests
    comm_sr_i, _ = engine.compute_commutator("PRIM:STATE_REDUCTION", "PRIM:INVARIANT_REASONING")
    assert comm_sr_i == "ORDER_SENSITIVE"

    comm_ds_ii, _ = engine.compute_commutator("PRIM:DIRECT_SOLUTION", "PRIM:INDIRECT_INFERENCE")
    assert comm_ds_ii == "INCOMPATIBLE"

    comm_sa_e, _ = engine.compute_commutator("PRIM:STATE_AUGMENTATION", "PRIM:EXTREMAL_REASONING")
    assert comm_sa_e == "ONE_DIRECTION_ONLY"


def test_lens_normal_form_rewriting_and_termination(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies canonical normal form reductions N(L) and bounded termination."""
    assert len(engine.rules) >= 4

    # Rule 1: Collapse nested state reductions
    seq1 = ["PRIM:STATE_REDUCTION", "PRIM:STATE_REDUCTION"]
    norm1 = engine.normalize_sequence(seq1)
    assert norm1 == ["PRIM:STATE_REDUCTION"]

    # Rule 2: Intersect sequential admissibility constraints
    seq2 = ["PRIM:ADMISSIBILITY", "PRIM:ADMISSIBILITY"]
    norm2 = engine.normalize_sequence(seq2)
    assert norm2 == ["PRIM:ADMISSIBILITY"]

    # Rule 3: Merge negative information ledgers
    seq3 = ["PRIM:NEGATIVE_INFORMATION", "PRIM:NEGATIVE_INFORMATION"]
    norm3 = engine.normalize_sequence(seq3)
    assert norm3 == ["PRIM:NEGATIVE_INFORMATION"]

    # Termination on longer sequence
    seq4 = [
        "PRIM:STATE_REDUCTION",
        "PRIM:STATE_REDUCTION",
        "PRIM:ADMISSIBILITY",
        "PRIM:ADMISSIBILITY",
        "PRIM:INVARIANT_REASONING",
    ]
    norm4 = engine.normalize_sequence(seq4)
    assert norm4 == ["PRIM:STATE_REDUCTION", "PRIM:ADMISSIBILITY", "PRIM:INVARIANT_REASONING"]


def test_mapeogeo_7_structural_closure_gates(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies that the 7 MAPEOGEO structural closure gates correctly qualify sequences."""
    # Well-formed valid sequence
    valid_seq = ["PRIM:STATE_REDUCTION", "PRIM:INVARIANT_REASONING", "PRIM:CONTROL_INTERVENTION"]
    closure_valid = engine.verify_mapeogeo_closure(valid_seq, is_synthetic=True)
    assert closure_valid.overall_passed
    assert closure_valid.c1_type_compatibility
    assert closure_valid.c2_assumption_satisfiability
    assert closure_valid.c3_invariant_accounting
    assert closure_valid.c4_information_accounting
    assert closure_valid.c5_canonical_normalization
    assert closure_valid.c6_termination
    assert closure_valid.c7_provenance_closure

    # Contradictory sequence (fails C2)
    invalid_seq = ["PRIM:DIRECT_SOLUTION", "PRIM:INDIRECT_INFERENCE"]
    closure_invalid = engine.verify_mapeogeo_closure(invalid_seq, is_synthetic=True)
    assert not closure_invalid.overall_passed
    assert not closure_invalid.c2_assumption_satisfiability

    # Non-normalized sequence (fails C5)
    unnormalized_seq = ["PRIM:STATE_REDUCTION", "PRIM:STATE_REDUCTION"]
    closure_unnorm = engine.verify_mapeogeo_closure(unnormalized_seq, is_synthetic=True)
    assert not closure_unnorm.overall_passed
    assert not closure_unnorm.c5_canonical_normalization


def test_uno_q_epistemic_utility_and_falsification_attacks(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies penalized utility formula and the 6 falsification attack vectors."""
    seq = ["PRIM:STATE_REDUCTION", "PRIM:SELF_CONSISTENT_CLOSURE", "PRIM:INVARIANT_REASONING", "PRIM:CONTROL_INTERVENTION"]
    prob_id = "PROBLEM:NON_HOLONOMIC_ROBOTIC_SWARM"

    u_rep = engine.evaluate_epistemic_utility(seq, prob_id)
    assert isinstance(u_rep, EpistemicUtilityReport)
    assert u_rep.raw_structure_score > 0.0
    assert u_rep.complexity_penalty > 0.0
    assert u_rep.net_utility > 0.0
    assert u_rep.passes_mdl_gate

    # Duplicate sequence gets redundancy penalty
    redundant_seq = ["PRIM:STATE_REDUCTION", "PRIM:STATE_REDUCTION", "PRIM:INVARIANT_REASONING"]
    u_red = engine.evaluate_epistemic_utility(redundant_seq, prob_id)
    assert u_red.redundancy_penalty > 0.0

    # 6 Attack vectors
    attacks = engine.run_falsification_attacks(seq, prob_id)
    assert len(attacks) == 6
    for a in attacks:
        assert isinstance(a, FalsificationAttackReport)
        assert a.passed, f"Attack {a.attack_id} failed: {a.rationale}"
        assert a.penalty == 0.0


def test_method_reconstruction_recall_calibration(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies Method Reconstruction Recall R_method >= 0.8 across the 7 historical lenses."""
    recon = engine.evaluate_method_reconstruction_recall()
    assert recon["qualification_passed"]
    assert recon["mean_recall"] >= 0.80

    for rec in recon["reconstruction_records"]:
        assert rec["passed"], f"Reconstruction failed for {rec['episode_id']}"
        assert rec["recall"] >= 0.80
        assert rec["overlap_count"] >= 3


def test_novel_synthetic_lenses_super_additive_qualification(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies that the 3 novel synthetic lenses achieve super-additive epistemic utility on held-out problems."""
    synth_res = engine.evaluate_synthetic_lenses_on_held_out()
    assert synth_res["milestone_m4_qualified"]
    assert synth_res["all_closure_passed"]
    assert synth_res["all_attacks_passed"]
    assert synth_res["all_super_additive"]

    for ev in synth_res["evaluations"]:
        assert ev["closure_passed"]
        assert ev["attacks_passed"]
        assert ev["is_super_additive"]
        assert ev["super_additive_synergy_gain"] > 0.0
        assert ev["net_epistemic_utility"] > ev["max_constituent_utility"]


def test_cultural_neutrality_of_synthetic_lenses(engine: PerspectiveSynthesisEngine) -> None:
    """Verifies complete cultural neutrality and historical_origin == 'NONE'."""
    banned = ["soviet", "russian", "leningrad", "moscow", "steklov", "ussr", "western"]
    for s_id, lens in engine.synthetic_lenses.items():
        assert lens.historical_origin == "NONE"
        assert lens.status == "QUALIFIED_SYNTHETIC_LENS"
        text = f"{lens.label} {lens.core_question} {lens.constructed_object}".lower()
        for kw in banned:
            assert kw not in text, f"Cultural keyword '{kw}' found in {s_id}"
