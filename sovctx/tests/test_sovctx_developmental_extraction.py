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
    PrimitiveMappingRecord,
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
    assert dataset["total_episodes"] >= 8
    assert len(dataset["episodes"]) == dataset["total_episodes"]
    assert len(dataset["primitive_mappings"]) == dataset["total_episodes"]
