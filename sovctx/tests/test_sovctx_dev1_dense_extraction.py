#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-DEV1: Dense Developmental Extraction.
Verifies consecutive chapter blocks, pedagogical agency progression,
teacher doctrine segregation, and multidimensional grammar transitions.
"""

import pytest
from sovctx.node.developmental_dense_extractor import DevelopmentalDenseExtractor
from sovctx.node.developmental_schema import (
    CorpusBatch,
    DevelopmentalEpisode,
    DevelopmentalStage,
    EpisodeType,
    MoveOrigin,
    ScaffoldingDepth,
    SubstitutionMode,
    TransferRequirement,
)


@pytest.fixture
def dense_extractor() -> DevelopmentalDenseExtractor:
    return DevelopmentalDenseExtractor()


def test_dense_volume_and_batch_distribution(dense_extractor: DevelopmentalDenseExtractor):
    assert len(dense_extractor.episodes) >= 80
    batch_a = dense_extractor.list_episodes_by_batch(CorpusBatch.BATCH_A_ORDINARY_PROGRESSION)
    batch_b = dense_extractor.list_episodes_by_batch(CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT)
    batch_c = dense_extractor.list_episodes_by_batch(CorpusBatch.BATCH_C_KOLMOGOROV_REFORM)

    assert len(batch_a) == 65
    assert len(batch_b) == 12
    assert len(batch_c) == 10


def test_consecutive_blocks_coverage(dense_extractor: DevelopmentalDenseExtractor):
    ep_ids = set(dense_extractor.episodes.keys())

    # Block 1: Popova first decade numbers 2 through 10
    for n in range(2, 11):
        assert f"DENSE-A1-POP-NUM-{n}" in ep_ids

    # Block 2: Popova decade crossings
    assert "DENSE-A1-POP-ADD_8_5" in ep_ids
    assert "DENSE-A1-POP-SUB_13_5" in ep_ids

    # Block 3: Pchelko mult/div reversible pairs
    assert "DENSE-A2-PCH-PAIR_3_4" in ep_ids
    assert "DENSE-A2-PCH-PAIR_5_8" in ep_ids

    # Block 4: Pchelko mental arithmetic shortcuts
    assert "DENSE-A2-PCH-MULT_5" in ep_ids
    assert "DENSE-A2-PCH-DIV_25" in ep_ids

    # Block 5: Pchelko word problems & false assumption
    assert "DENSE-A2-PCH-FALSE_ASSUMP_VEHICLES" in ep_ids
    assert "DENSE-A2-PCH-MOTION_MEETING" in ep_ids

    # Block 6: Kiselev planimetry theorems
    assert "DENSE-A5-KIS-THM_ISOSCELES" in ep_ids
    assert "DENSE-A5-KIS-THM_PYTHAGORAS_SHEAR" in ep_ids

    # Block 7: Kiselev algebra factoring and quadratics
    assert "DENSE-A6-KIS-FACTOR_GROUPING" in ep_ids
    assert "DENSE-A6-KIS-COMPLETE_SQUARE_MONIC" in ep_ids


def test_sampling_protocol_fidelity(dense_extractor: DevelopmentalDenseExtractor):
    for ep in dense_extractor.episodes.values():
        assert len(ep.source_id) > 0
        assert len(ep.problem_presented) > 5
        assert len(ep.key_mathematical_move) > 5
        assert ep.computational_substitution is not None
        assert len(ep.computational_substitution) > 5
        assert ep.episode_type in EpisodeType
        assert ep.substitution_mode in SubstitutionMode
        assert ep.move_origin in MoveOrigin
        assert ep.scaffolding_depth in ScaffoldingDepth
        assert ep.transfer_requirement in TransferRequirement


def test_teacher_doctrine_segregation(dense_extractor: DevelopmentalDenseExtractor):
    pupil_eps = dense_extractor.list_pupil_episodes()
    doctrine_eps = dense_extractor.list_doctrine_episodes()

    assert len(pupil_eps) == 79  # 57 from Batch A + 12 from Batch B + 10 from Batch C
    assert len(doctrine_eps) == 8  # Exactly 8 from Teacher Doctrine sources A3, A4, A7

    for ep in doctrine_eps:
        assert ep.is_teacher_doctrine is True
        assert ep.source_id in (
            "A3_PCHELKO_TEACHER_METHODOLOGY_1949",
            "A4_PCHELKO_PROBLEM_SOLVING_1949",
            "A7_LYAPIN_SECONDARY_METHODOLOGY_1956",
        )

    for ep in pupil_eps:
        assert ep.is_teacher_doctrine is False


def test_agency_progression_metrics(dense_extractor: DevelopmentalDenseExtractor):
    prog_rs = dense_extractor.compute_agency_progression("Rs")
    assert "GRADE_1" in prog_rs
    assert "GRADE_2_4" in prog_rs
    assert "GRADE_6_8" in prog_rs
    assert "OLYMPIAD_ENRICHMENT" in prog_rs

    # In elementary grades, students are never expected to originate without scaffold
    assert prog_rs["GRADE_1"]["STUDENT_EXPECTED_TO_INVENT"] == 0.0
    assert prog_rs["GRADE_2_4"]["STUDENT_EXPECTED_TO_INVENT"] == 0.0
    assert prog_rs["GRADE_6_8"]["STUDENT_EXPECTED_TO_INVENT"] == 0.0

    # In Olympiad enrichment, 100% of Rs moves require independent student invention
    assert prog_rs["OLYMPIAD_ENRICHMENT"]["STUDENT_EXPECTED_TO_INVENT"] == 1.0


def test_multidimensional_grammar_structure(dense_extractor: DevelopmentalDenseExtractor):
    grammar = dense_extractor.compute_multidimensional_grammar()
    assert "Rs" in grammar
    assert "DIRECT" in grammar["Rs"] or "PARTIAL" in grammar["Rs"]
    assert "NONE" in grammar["Rs"]
    # Under NONE scaffolding (Olympiad regime), Rs connects strongly to I and E
    assert "I" in grammar["Rs"]["NONE"]


def test_export_dense_dataset_structure(dense_extractor: DevelopmentalDenseExtractor):
    data = dense_extractor.export_dense_dataset()
    assert data["total_episodes"] >= 80
    assert data["pupil_episodes"] >= 75
    assert data["doctrine_episodes"] == 8
    assert "substitution_mode_distribution" in data
    assert "normalized_primitive_rates" in data
    assert "segregated_doctrine_comparison" in data
    assert "rs_agency_progression" in data
    assert "ax_agency_progression" in data
    assert "multidimensional_grammar" in data
