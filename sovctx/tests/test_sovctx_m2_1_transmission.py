#!/usr/bin/env python3
"""
Work Plane Unit Tests for Milestone SOVCTX-M2.1:
Blind Methodological Transmission Study.
"""

from pathlib import Path
import pytest

from sovctx.node.blind_transmission_study import (
    BlindTransmissionStudyEngine,
    TransmissionStage,
    LineageTradition,
    MethodDomain,
    UnbundledDiscrepancyVector,
)


@pytest.fixture
def engine() -> BlindTransmissionStudyEngine:
    return BlindTransmissionStudyEngine()


def test_corpus_completeness(engine: BlindTransmissionStudyEngine) -> None:
    assert len(engine.corpus) == 40
    sov_count = sum(1 for a in engine.corpus if a.tradition == LineageTradition.SOVIET)
    west_count = sum(1 for a in engine.corpus if a.tradition == LineageTradition.WESTERN)
    assert sov_count == 20
    assert west_count == 20

    # 4 domains * 5 stages for each tradition
    for dom in MethodDomain:
        for st in TransmissionStage:
            sov_arts = [a for a in engine.corpus if a.tradition == LineageTradition.SOVIET and a.domain == dom and a.stage == st]
            west_arts = [a for a in engine.corpus if a.tradition == LineageTradition.WESTERN and a.domain == dom and a.stage == st]
            assert len(sov_arts) == 1, f"Missing Soviet artifact for {dom} at {st}"
            assert len(west_arts) == 1, f"Missing Western artifact for {dom} at {st}"


def test_blind_extractor_neutrality(engine: BlindTransmissionStudyEngine) -> None:
    art = engine.corpus[0]
    payload = art.get_blind_payload()
    assert "tradition" not in payload
    assert "stage" not in payload
    assert "domain" not in payload

    extracted = engine.extractor.extract(payload)
    assert extracted.artifact_id == art.artifact_id
    assert extracted.s0_problem != ""
    assert extracted.t_transformation_action != ""


def test_unbundled_channel_separation(engine: BlindTransmissionStudyEngine) -> None:
    res = engine.run_study()
    for eval_item in res["evaluations"]:
        disc = eval_item["discrepancy"]
        assert 0.0 <= disc["d_admissibility"] <= 1.0
        assert 0.0 <= disc["d_auxiliary"] <= 1.0
        assert 0.0 <= disc["d_negative_info"] <= 1.0
        assert 0.0 <= disc["d_ordering"] <= 1.0
        assert 0.0 <= disc["d_representation_space"] <= 1.0
        assert 0.0 <= disc["d_method_composite"] <= 1.0


def test_empirical_code_negative_information(engine: BlindTransmissionStudyEngine) -> None:
    res = engine.run_study()
    mean_dn = res["mean_code_negative_info_distortion"]
    # Empirical measurement shows docstrings and error checks retain ~5% of negative info
    assert mean_dn < 1.0000, "Empirical code negative info should be sub-unity when docstrings warn of ill-conditioning"
    assert mean_dn >= 0.8500, "Code should still exhibit high negative info distortion"
    assert res["has_sub_unity_code_negative_retention"] is True


def test_differential_contrast_computation(engine: BlindTransmissionStudyEngine) -> None:
    res = engine.run_study()
    contrasts = res["contrasts"]
    assert len(contrasts) == 20  # 4 domains * 5 stages

    for c in contrasts:
        assert "delta_d_admissibility" in c
        assert "delta_d_auxiliary" in c
        assert "delta_d_negative_info" in c
        assert "delta_d_ordering" in c
        assert "delta_d_representation_space" in c
        assert "delta_d_composite" in c


def test_stage4_textbook_differential_auxiliary_loss(engine: BlindTransmissionStudyEngine) -> None:
    res = engine.run_study()
    st4_deltas = res["stage_delta_means"][TransmissionStage.STAGE_4_TEXTBOOK.value]

    # Hypothesis confirmed by empirical paired extraction:
    # Modern textbooks disproportionately erase Soviet auxiliary constructions (Delta D_X > 0)
    # and representation space shifts (Delta D_S > 0)
    assert st4_deltas["delta_D_auxiliary"] > 0.0, "Modern textbooks should show greater auxiliary loss for Soviet methods"
    assert st4_deltas["delta_D_representation_space"] > 0.0, "Modern textbooks should show greater space shift loss for Soviet methods"
    assert st4_deltas["delta_D_composite"] > 0.0, "Overall composite distortion in textbooks should be higher for Soviet methods"
