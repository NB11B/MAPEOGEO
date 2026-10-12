from __future__ import annotations

import pytest

from sovctx.node.falsification_audit import FalsificationAuditEngine
from sovctx.node.graph_controls import GraphControlsEngine
from sovctx.node.relational_duality import RelationalDualityEngine
from sovctx.node.school_fingerprints import SchoolFingerprintEngine
from sovctx.node.western_benchmark import WesternBenchmarkSpecification


def test_target_grammar_multi_resolution_accounting() -> None:
    engine = RelationalDualityEngine()
    audits = engine.audit_target_grammar_sequences()
    assert len(audits) == 3

    s1 = audits[0]
    assert s1.target_sequence == "OBSERVE -> INVERT -> CONSTRAIN -> STABILIZE"
    assert s1.raw_path_count == 1648
    assert len(s1.unique_source_publications) == 3
    assert "PUB:TIKHONOV_1963_ILLPOSED" in s1.unique_source_publications
    assert "PUB:GELFAND_LEVITAN_1951" in s1.unique_source_publications
    assert len(s1.unique_equation_families) == 2
    assert len(s1.unique_equations) == 7
    assert s1.structural_compression_ratio > 100.0

    s2 = audits[1]
    assert s2.target_sequence == "REPRESENT -> PERTURB -> STABILIZE -> CONTROL"
    assert s2.raw_path_count == 378
    assert len(s2.unique_source_publications) == 2
    assert len(s2.unique_equation_families) == 2
    assert len(s2.unique_equations) == 6
    assert s2.structural_compression_ratio == 63.0

    s3 = audits[2]
    assert s3.target_sequence == "REPRESENT -> REDUCE -> EVOLVE -> RECONSTRUCT"
    assert s3.raw_path_count == 260
    assert len(s3.unique_source_publications) == 3
    assert len(s3.unique_equation_families) == 1
    assert len(s3.unique_equations) == 4
    assert s3.structural_compression_ratio == 65.0


def test_relation_graph_entropy_metrics() -> None:
    engine = RelationalDualityEngine()
    comp = engine.compare_graph_compression()

    assert comp.entity_graph_entropy_bits in {21.80, 22.41, 22.47, 22.52, 22.56, 22.87}
    assert comp.marginal_verb_entropy_bits in {3.05, 3.10, 3.12, 3.13}
    assert comp.relation_graph_entropy_bits in {2.96, 2.97}
    assert comp.relation_transition_entropy_reduction_percent in {2.59, 4.16, 4.94, 5.11}
    assert comp.structural_entropy_reduction_percent in {86.41, 86.73, 86.77, 86.80, 86.82, 87.00}


def test_control_e_relation_semantics_permutation_fast() -> None:
    controls = GraphControlsEngine(seed=123)
    res_e = controls.run_control_e(iterations=5)

    assert res_e.control_id == "CONTROL-E"
    assert len(res_e.statistics) == 3
    for stat in res_e.statistics:
        assert stat.iterations == 5
        assert stat.control_mean >= 0.0


def test_loso_falsification_audit() -> None:
    audit_engine = FalsificationAuditEngine()
    loso_results = audit_engine.run_loso_audit()

    assert len(loso_results) == len(FalsificationAuditEngine.CANONICAL_SCHOOLS)
    res_map = {r.omitted_school: r for r in loso_results}

    # S1 without Tikhonov must retain Gelfand-Levitan paths
    tikh = res_map["TIKHONOV"]
    s1_tikh = tikh.grammar_retentions[0]
    assert s1_tikh.surviving_paths == 840
    assert s1_tikh.retention_rate_pct > 50.0
    assert not s1_tikh.is_falsified

    # S1 without Gelfand must retain Tikhonov paths
    gelf = res_map["GELFAND"]
    s1_gelf = gelf.grammar_retentions[0]
    assert s1_gelf.surviving_paths == 96
    assert not s1_gelf.is_falsified

    # S2 requires both Lyapunov and Pontryagin
    lyap = res_map["LYAPUNOV"]
    assert lyap.grammar_retentions[1].is_falsified
    pont = res_map["PONTRYAGIN"]
    assert pont.grammar_retentions[1].is_falsified

    # S2 without Chebyshev remains 100%
    cheb = res_map["CHEBYSHEV"]
    assert cheb.grammar_retentions[1].surviving_paths == 378


def test_loeo_falsification_audit() -> None:
    audit_engine = FalsificationAuditEngine()
    loeo_results = audit_engine.run_loeo_audit()

    assert len(loeo_results) == 6
    loeo_map = {r.omitted_slice_id: r for r in loeo_results}

    # Slice 1 (1750-1850) omission preserves 100% across all 3
    s1 = loeo_map["SLICE_1_1750_1850"]
    for ret in s1.grammar_retentions:
        assert ret.retention_rate_pct == 100.0

    # Slice 4 (1945-1970) omission eliminates S1 and S2
    s4 = loeo_map["SLICE_4_1945_1970"]
    assert s4.grammar_retentions[0].surviving_paths == 0
    assert s4.grammar_retentions[1].surviving_paths == 0


def test_school_relational_fingerprints_and_clustering() -> None:
    fp_engine = SchoolFingerprintEngine()
    fps = fp_engine.compute_school_fingerprints()

    assert len(fps) == 12
    for s, fp in fps.items():
        assert len(fp.verb_fingerprint_vector) == 17
        assert abs(sum(fp.verb_fingerprint_vector) - 1.0) < 1e-3

    distances = fp_engine.compute_distance_matrix(fps)
    assert len(distances) == 66  # 12 choose 2 = 66 pairs

    # Lyapunov and Pontryagin must have small cosine distance
    lp_dist = next(d for d in distances if set([d.school_a, d.school_b]) == {"LYAPUNOV", "PONTRYAGIN"})
    assert lp_dist.cosine_distance < 0.10
    assert lp_dist.is_intra_cluster

    # Tikhonov and Gelfand-Levitan must have small cosine distance
    tg_dist = next(d for d in distances if set([d.school_a, d.school_b]) == {"TIKHONOV", "GELFAND_LEVITAN"})
    assert tg_dist.cosine_distance < 0.15
    assert tg_dist.is_intra_cluster


def test_western_comparison_specification_structure() -> None:
    benchmark = WesternBenchmarkSpecification()
    assert len(benchmark.MATCHED_PAIRS) == 4
    assert len(benchmark.FORMAL_HYPOTHESES) == 4

    fields = [p.domain_field for p in benchmark.MATCHED_PAIRS]
    assert "DYNAMICAL_SYSTEMS_AND_OPTIMAL_CONTROL" in fields
    assert "INVERSE_PROBLEMS_AND_REGULARIZATION" in fields
    assert "COLLECTIVE_KINETICS_AND_PLASMA_PHYSICS" in fields
    assert "APPROXIMATION_AND_NUMERICAL_SYNTHESIS" in fields

    h_ids = [h.hypothesis_id for h in benchmark.FORMAL_HYPOTHESES]
    assert "H1_TRANSITION_ENTROPY_DIFFERENTIAL" in h_ids
    assert "H2_TARGET_GRAMMAR_EPISODE_DENSITY" in h_ids
    assert "H3_RELATIONAL_OPERATOR_DIVERGENCE" in h_ids
    assert "H4_CROSS_DOMAIN_RECURRENCE" in h_ids
