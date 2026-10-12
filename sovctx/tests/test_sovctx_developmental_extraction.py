#!/usr/bin/env python3
"""
Unit tests for the Developmental Extraction System (Batch A Baseline).
"""

import pytest
from sovctx.node.developmental_corpus_registry import DevelopmentalCorpusRegistry
from sovctx.node.developmental_extraction_engine import DevelopmentalExtractionEngine
from sovctx.node.developmental_schema import (
    CorpusBatch,
    DevelopmentalEpisode,
    DevelopmentalStage,
    MoveOrigin,
    PrimitiveMappingRecord,
    ScaffoldingDepth,
    TransferRequirement,
)


@pytest.fixture
def registry() -> DevelopmentalCorpusRegistry:
    return DevelopmentalCorpusRegistry()


@pytest.fixture
def extraction_engine() -> DevelopmentalExtractionEngine:
    return DevelopmentalExtractionEngine()


def test_corpus_registry_completeness(registry: DevelopmentalCorpusRegistry):
    sources = list(registry.sources.values())
    assert len(sources) == 15
    batch_a = registry.list_sources_by_batch(CorpusBatch.BATCH_A_ORDINARY_PROGRESSION)
    batch_b = registry.list_sources_by_batch(CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT)
    batch_c = registry.list_sources_by_batch(CorpusBatch.BATCH_C_KOLMOGOROV_REFORM)

    assert len(batch_a) == 7
    assert len(batch_b) == 4
    assert len(batch_c) == 4


def test_batch_a_priority_ordering(registry: DevelopmentalCorpusRegistry):
    batch_a = registry.list_sources_by_batch(CorpusBatch.BATCH_A_ORDINARY_PROGRESSION)
    priorities = [s.priority_order for s in batch_a]
    assert priorities == [1, 2, 3, 4, 5, 6, 7]
    assert batch_a[0].target_id == "A1_POPOVA_1933"
    assert batch_a[1].target_id == "A2_PCHELKO_POLYAK_GRADES_1_4"
    assert batch_a[2].target_id == "A3_PCHELKO_TEACHER_METHODOLOGY_1949"
    assert batch_a[3].target_id == "A4_PCHELKO_PROBLEM_SOLVING_1949"
    assert batch_a[4].target_id == "A5_KISELEV_GEOMETRY_1938"
    assert batch_a[5].target_id == "A6_KISELEV_ALGEBRA_1938"
    assert batch_a[6].target_id == "A7_LYAPIN_SECONDARY_METHODOLOGY_1956"


def test_standardized_9_element_schema_integrity(extraction_engine: DevelopmentalExtractionEngine):
    for ep in extraction_engine.episodes.values():
        assert len(ep.episode_id) > 0
        assert len(ep.problem_presented) > 10
        assert len(ep.representation_supplied) > 10
        assert len(ep.representation_invented) > 10
        assert len(ep.allowed_operations) >= 1
        assert len(ep.hint_scaffold) > 10
        assert len(ep.key_mathematical_move) > 10
        assert len(ep.what_need_not_be_computed) > 10
        assert len(ep.expected_new_capability) > 10
        assert len(ep.pedagogical_intent) > 10


def test_batch_a_canonical_coverage(extraction_engine: DevelopmentalExtractionEngine):
    episodes = extraction_engine.list_episodes_by_batch(CorpusBatch.BATCH_A_ORDINARY_PROGRESSION)
    assert len(episodes) >= 8
    source_ids = {ep.source_id for ep in episodes}
    assert "A1_POPOVA_1933" in source_ids
    assert "A2_PCHELKO_POLYAK_GRADES_1_4" in source_ids
    assert "A3_PCHELKO_TEACHER_METHODOLOGY_1949" in source_ids
    assert "A4_PCHELKO_PROBLEM_SOLVING_1949" in source_ids
    assert "A5_KISELEV_GEOMETRY_1938" in source_ids
    assert "A6_KISELEV_ALGEBRA_1938" in source_ids
    assert "A7_LYAPIN_SECONDARY_METHODOLOGY_1956" in source_ids


def test_post_hoc_primitive_mapping(extraction_engine: DevelopmentalExtractionEngine):
    for ep_id, ep in extraction_engine.episodes.items():
        mapping = extraction_engine.get_mapping(ep_id)
        assert mapping is not None
        assert len(mapping.primitive_symbols) >= 2
        assert mapping.structural_concordance >= 0.90
        for p in mapping.primitive_symbols:
            assert p in mapping.mapping_breakdown
            assert len(mapping.mapping_breakdown[p]) > 10


def test_popova_negative_information_extraction(extraction_engine: DevelopmentalExtractionEngine):
    ep = extraction_engine.get_episode("DEV-A1-POP-01")
    assert ep is not None
    assert "without finger counting" in ep.expected_new_capability or "without counting" in ep.representation_invented
    assert "unit-by-unit" in ep.what_need_not_be_computed
    mapping = extraction_engine.get_mapping("DEV-A1-POP-01")
    assert mapping is not None
    assert "N" in mapping.primitive_symbols


def test_kiselev_auxiliary_construction_extraction(extraction_engine: DevelopmentalExtractionEngine):
    ep = extraction_engine.get_episode("DEV-A5-KIS-GEOM-01")
    assert ep is not None
    assert "auxiliary" in ep.key_mathematical_move.lower() or "bisector" in ep.representation_invented.lower()
    mapping = extraction_engine.get_mapping("DEV-A5-KIS-GEOM-01")
    assert mapping is not None
    assert "Ax" in mapping.primitive_symbols


def test_export_dataset_structure(extraction_engine: DevelopmentalExtractionEngine):
    dataset = extraction_engine.export_extraction_dataset()
    assert dataset["total_episodes"] == 20
    assert len(dataset["episodes"]) == 20
    assert len(dataset["primitive_mappings"]) == 20
    assert "cross_batch_comparison" in dataset
    assert "normalized_primitive_rates" in dataset
    assert "invention_conditioned_rates" in dataset
    assert "scaffolding_distribution" in dataset
    assert "grammar_transitions" in dataset


def test_pedagogical_agency_fields(extraction_engine: DevelopmentalExtractionEngine):
    for ep in extraction_engine.episodes.values():
        assert ep.move_origin is not None
        assert ep.scaffolding_depth is not None
        assert ep.transfer_requirement is not None
        assert ep.computational_substitution is not None
        assert len(ep.computational_substitution) > 10

    # Batch B Olympiad episodes must be student-invented with no scaffolding and far transfer
    for ep in extraction_engine.list_episodes_by_batch(CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT):
        assert ep.move_origin == MoveOrigin.STUDENT_EXPECTED_TO_INVENT
        assert ep.scaffolding_depth == ScaffoldingDepth.NONE
        assert ep.transfer_requirement == TransferRequirement.FAR_TRANSFER

    # Batch A ordinary schooling must have scaffolding
    for ep in extraction_engine.list_episodes_by_batch(CorpusBatch.BATCH_A_ORDINARY_PROGRESSION):
        assert ep.move_origin in (MoveOrigin.SUPPLIED, MoveOrigin.HINTED)
        assert ep.scaffolding_depth in (ScaffoldingDepth.DIRECT, ScaffoldingDepth.PARTIAL)


def test_normalized_rates_and_invention_conditioning(extraction_engine: DevelopmentalExtractionEngine):
    rates = extraction_engine.compute_normalized_primitive_rates()
    # P(Rs | A) = 8/12 = 0.6667
    assert rates["BATCH_A_ORDINARY_PROGRESSION"]["Rs"] == 0.6667
    # P(I | B) = 3/4 = 0.75
    assert rates["BATCH_B_OLYMPIAD_ENRICHMENT"]["I"] == 0.75
    # P(G | C) = 2/4 = 0.50
    assert rates["BATCH_C_KOLMOGOROV_REFORM"]["G"] == 0.5

    inv = extraction_engine.compute_invention_conditioned_rates()
    assert inv["total_invented_episodes"] == 4
    assert inv["total_scaffolded_episodes"] == 16
    assert inv["P_primitive_given_invented"]["I"] == 0.75
    assert inv["P_primitive_given_invented"]["N"] == 0.75


def test_scaffolding_distribution_analytics(extraction_engine: DevelopmentalExtractionEngine):
    scaff = extraction_engine.compute_scaffolding_distribution()
    batch_a_scaff = scaff["BATCH_A_ORDINARY_PROGRESSION"]
    batch_b_scaff = scaff["BATCH_B_OLYMPIAD_ENRICHMENT"]

    assert batch_a_scaff["scaffolding_depth"]["DIRECT"] == 7
    assert batch_a_scaff["scaffolding_depth"]["PARTIAL"] == 5
    assert batch_b_scaff["scaffolding_depth"]["NONE"] == 4


def test_developmental_grammar_transitions(extraction_engine: DevelopmentalExtractionEngine):
    grammar = extraction_engine.compute_developmental_grammar_transitions()
    assert "Rs" in grammar
    assert "Ax" in grammar
    assert "N" in grammar
    # Representation shift strongly connects to Invariant reasoning and Negative information
    assert grammar["Rs"]["I"] >= 5
    assert grammar["Rs"]["N"] >= 5


def test_batch_b_canonical_coverage(extraction_engine: DevelopmentalExtractionEngine):
    episodes = extraction_engine.list_episodes_by_batch(CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT)
    assert len(episodes) == 4
    ep_ids = {ep.episode_id for ep in episodes}
    assert "DEV-B1-BONCH-01" in ep_ids
    assert "DEV-B2-SHK-ARITH-01" in ep_ids
    assert "DEV-B3-SHK-GEOM-01" in ep_ids
    assert "DEV-B4-MOSCOW_OLYMPIADS_1935_1957" in ep_ids

    # Bonchkovsky Parity Invariant
    ep_b1 = extraction_engine.get_episode("DEV-B1-BONCH-01")
    assert ep_b1 is not None
    assert "parity" in ep_b1.key_mathematical_move.lower()
    mapping_b1 = extraction_engine.get_mapping("DEV-B1-BONCH-01")
    assert "I" in mapping_b1.primitive_symbols
    assert "N" in mapping_b1.primitive_symbols

    # Shklyarsky Dirichlet Pigeonhole
    ep_b2 = extraction_engine.get_episode("DEV-B2-SHK-ARITH-01")
    assert ep_b2 is not None
    assert "pigeonhole" in ep_b2.key_mathematical_move.lower() or "dirichlet" in ep_b2.pedagogical_intent.lower()
    mapping_b2 = extraction_engine.get_mapping("DEV-B2-SHK-ARITH-01")
    assert "Ii" in mapping_b2.primitive_symbols
    assert "N" in mapping_b2.primitive_symbols

    # Shklyarsky Heron Reflection
    ep_b3 = extraction_engine.get_episode("DEV-B3-SHK-GEOM-01")
    assert ep_b3 is not None
    assert "reflection" in ep_b3.key_mathematical_move.lower()
    mapping_b3 = extraction_engine.get_mapping("DEV-B3-SHK-GEOM-01")
    assert "E" in mapping_b3.primitive_symbols
    assert "Ax" in mapping_b3.primitive_symbols

    # Moscow Olympiad Central Symmetry Strategy
    ep_b4 = extraction_engine.get_episode("DEV-B4-MOSCOW_OLYMPIADS_1935_1957")
    assert ep_b4 is not None
    assert "symmetric" in ep_b4.key_mathematical_move.lower() or "symmetry" in ep_b4.hint_scaffold.lower()
    mapping_b4 = extraction_engine.get_mapping("DEV-B4-MOSCOW_OLYMPIADS_1935_1957")
    assert "C" in mapping_b4.primitive_symbols
    assert "I" in mapping_b4.primitive_symbols


def test_batch_c_canonical_coverage(extraction_engine: DevelopmentalExtractionEngine):
    episodes = extraction_engine.list_episodes_by_batch(CorpusBatch.BATCH_C_KOLMOGOROV_REFORM)
    assert len(episodes) == 4
    ep_ids = {ep.episode_id for ep in episodes}
    assert "DEV-C1-KOLM-DRAFT-01" in ep_ids
    assert "DEV-C2-KOLM-NEW_PROGRAMS_1967_1968" in ep_ids
    assert "DEV-C3-KOLMOGOROV_GEOMETRY_1979" in ep_ids
    assert "DEV-C4-KOLMOGOROV_ALGEBRA_ANALYSIS_1983" in ep_ids

    # Kolmogorov Draft Transformation Groups
    ep_c1 = extraction_engine.get_episode("DEV-C1-KOLM-DRAFT-01")
    assert ep_c1 is not None
    assert "group" in ep_c1.key_mathematical_move.lower() or "transformation" in ep_c1.pedagogical_intent.lower()
    mapping_c1 = extraction_engine.get_mapping("DEV-C1-KOLM-DRAFT-01")
    assert "G" in mapping_c1.primitive_symbols
    assert "Sc" in mapping_c1.primitive_symbols

    # Kolmogorov New Programs Function Mapping
    ep_c2 = extraction_engine.get_episode("DEV-C2-KOLM-NEW_PROGRAMS_1967_1968")
    assert ep_c2 is not None
    assert "domain" in ep_c2.key_mathematical_move.lower() or "mapping" in ep_c2.pedagogical_intent.lower()
    mapping_c2 = extraction_engine.get_mapping("DEV-C2-KOLM-NEW_PROGRAMS_1967_1968")
    assert "Rs" in mapping_c2.primitive_symbols
    assert "Ad" in mapping_c2.primitive_symbols

    # Kolmogorov Geometry Distance Preserving Isometry
    ep_c3 = extraction_engine.get_episode("DEV-C3-KOLMOGOROV_GEOMETRY_1979")
    assert ep_c3 is not None
    assert "isometry" in ep_c3.key_mathematical_move.lower() or "distance-preserving" in ep_c3.key_mathematical_move.lower()
    mapping_c3 = extraction_engine.get_mapping("DEV-C3-KOLMOGOROV_GEOMETRY_1979")
    assert "Rs" in mapping_c3.primitive_symbols
    assert "I" in mapping_c3.primitive_symbols
    assert "G" in mapping_c3.primitive_symbols

    # Kolmogorov Analysis Local Linearization
    ep_c4 = extraction_engine.get_episode("DEV-C4-KOLMOGOROV_ALGEBRA_ANALYSIS_1983")
    assert ep_c4 is not None
    assert "linear" in ep_c4.key_mathematical_move.lower()
    mapping_c4 = extraction_engine.get_mapping("DEV-C4-KOLMOGOROV_ALGEBRA_ANALYSIS_1983")
    assert "L" in mapping_c4.primitive_symbols
    assert "Sr" in mapping_c4.primitive_symbols


def test_cross_batch_comparative_table(extraction_engine: DevelopmentalExtractionEngine):
    table = extraction_engine.compute_cross_batch_comparative_table()
    assert table["batch_a_episodes"] == 12
    assert table["batch_b_episodes"] == 4
    assert table["batch_c_episodes"] == 4

    p_dist = table["primitive_distribution"]
    # Verify signature shifts
    # Batch A high in N, Ax, Rs, Sr
    assert p_dist["N"]["Batch_A_Ordinary"] == 6
    assert p_dist["Ax"]["Batch_A_Ordinary"] == 6
    assert p_dist["Rs"]["Batch_A_Ordinary"] == 8

    # Batch B introduces E and C
    assert p_dist["E"]["Batch_B_Olympiad"] == 1
    assert p_dist["C"]["Batch_B_Olympiad"] == 1
    assert p_dist["E"]["Batch_A_Ordinary"] == 0

    # Batch C introduces Sc and L, high in G
    assert p_dist["Sc"]["Batch_C_Reform"] == 1
    assert p_dist["L"]["Batch_C_Reform"] == 1
    assert p_dist["G"]["Batch_C_Reform"] == 2

