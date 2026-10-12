#!/usr/bin/env python3
"""
Work Plane Unit Tests for Milestone SOVCTX-M2 (Method Episodes & Lossy Normalization).
Executed locally and on Jetson Nano ARM Cortex-A57.
"""

from pathlib import Path
import pytest

from sovctx.node.lossy_normalization import (
    LossyNormalizationWorker,
    CompressionTier,
    MethodEpisode,
    ErasureVector,
    CODE_MAPPINGS,
)


@pytest.fixture
def worker() -> LossyNormalizationWorker:
    w = LossyNormalizationWorker()
    w.load_episodes()
    return w


def test_load_canonical_method_episodes(worker: LossyNormalizationWorker) -> None:
    assert len(worker.episodes) == 7
    expected_ids = {
        "EP:LYAPUNOV_1892_STABILITY",
        "EP:TIKHONOV_1963_REGULARIZATION",
        "EP:PONTRYAGIN_1960_MAXIMUM_PRINCIPLE",
        "EP:GELFAND_LEVITAN_1951_INVERSE_SPECTRAL",
        "EP:VLASOV_1938_COLLECTIVE_FIELD",
        "EP:CHEBYSHEV_1853_MINIMAX_APPROXIMATION",
        "EP:BOCKER_2025_INFINITESIMAL_COVARIANCE",
    }
    assert set(worker.episodes.keys()) == expected_ids


def test_episode_components_complete(worker: LossyNormalizationWorker) -> None:
    for ep_id, ep in worker.episodes.items():
        # S0
        assert ep.s0_initial_problem.get("problem_statement")
        assert ep.s0_initial_problem.get("state_space")
        assert len(ep.s0_initial_problem.get("visible_equations", [])) >= 1

        # Q
        assert ep.q_deficiency.get("why_direct_solution_fails")

        # A
        assert ep.a_admissibility.get("permissible_domain")
        assert ep.a_admissibility.get("admissibility_class")

        # X
        assert ep.x_auxiliary_construction.get("auxiliary_object_name")
        assert ep.x_auxiliary_construction.get("auxiliary_representation_space")
        assert ep.x_auxiliary_construction.get("space_change")

        # C
        assert len(ep.c_constraints_invariants.get("invariants", [])) >= 1
        assert ep.c_constraints_invariants.get("admissibility_bounds")

        # T
        assert ep.t_transformation_decision.get("decision_description")
        assert len(ep.t_transformation_decision.get("operator_ids", [])) >= 1
        assert ep.t_transformation_decision.get("computation_on_auxiliary")

        # S1
        assert ep.s1_resulting_conclusion.get("conclusion_statement")
        assert len(ep.s1_resulting_conclusion.get("certified_properties", [])) >= 1

        # Negative Information Ledger
        neg = ep.negative_information
        assert len(neg.get("what_need_not_be_computed", [])) >= 2
        assert len(neg.get("excluded_alternatives", [])) >= 2


def test_native_entropy_calculation(worker: LossyNormalizationWorker) -> None:
    for ep in worker.episodes.values():
        h = ep.compute_native_entropy()
        assert h >= 25.0, f"Episode {ep.id} entropy {h} is lower than minimum theoretical threshold"
        assert h <= 60.0, f"Episode {ep.id} entropy {h} is unexpectedly high"


def test_monotonic_erasure_ladder(worker: LossyNormalizationWorker) -> None:
    for ep in worker.episodes.values():
        results = worker.evaluate_ladder_for_episode(ep)
        assert len(results) == 5

        distortions = [r.erasure_vector.total_distortion for r in results]
        fidelities = [r.reconstruction_fidelity for r in results]

        # Monotonic distortion increase
        for i in range(len(distortions) - 1):
            assert distortions[i] <= distortions[i + 1], (
                f"Episode {ep.id}: Distortion did not increase monotonically from tier {results[i].tier} to {results[i+1].tier}"
            )
            assert fidelities[i] >= fidelities[i + 1], (
                f"Episode {ep.id}: Fidelity did not decrease monotonically from tier {results[i].tier} to {results[i+1].tier}"
            )

        # Tier 1 must be perfectly lossless
        assert distortions[0] == 0.0
        assert fidelities[0] == 1.0

        # Tier 5 must exhibit severe distortion (> 0.90)
        assert distortions[-1] >= 0.90
        assert fidelities[-1] <= 0.10


def test_negative_information_total_erasure_in_code(worker: LossyNormalizationWorker) -> None:
    for ep in worker.episodes.values():
        res = worker.evaluate_episode_tier(ep, CompressionTier.CODE_FUNCTION)
        assert res.erasure_vector.delta_negative_info == 1.0, (
            f"Episode {ep.id}: delta_neg in CODE_FUNCTION must be 1.0 (complete loss)"
        )


def test_auxiliary_object_preservation_tiers(worker: LossyNormalizationWorker) -> None:
    for ep in worker.episodes.values():
        res_t1 = worker.evaluate_episode_tier(ep, CompressionTier.PRIMARY_ORIGINAL)
        res_t5 = worker.evaluate_episode_tier(ep, CompressionTier.CODE_FUNCTION)
        assert res_t1.erasure_vector.delta_auxiliary == 0.0
        assert res_t5.erasure_vector.delta_auxiliary >= 0.90


def test_epistemic_inversion_audit(worker: LossyNormalizationWorker) -> None:
    for ep in worker.episodes.values():
        # Test Tier 1 inversion
        norm_t1 = worker.project_to_normalized(ep, CompressionTier.PRIMARY_ORIGINAL)
        audit_t1 = worker.attempt_epistemic_reconstruction(norm_t1, ep)
        assert audit_t1["is_lossless"] is True
        assert audit_t1["epistemic_verdict"] == "LOSSLESS_PRESERVATION"
        assert len(audit_t1["erased_components"]) == 0

        # Test Tier 5 inversion
        norm_t5 = worker.project_to_normalized(ep, CompressionTier.CODE_FUNCTION)
        audit_t5 = worker.attempt_epistemic_reconstruction(norm_t5, ep)
        assert audit_t5["is_lossless"] is False
        assert audit_t5["epistemic_verdict"] == "BLACK_BOX_EXTINCTION"
        assert "negative_information.what_need_not_be_computed" in audit_t5["erased_components"]
        assert "negative_information.excluded_alternatives" in audit_t5["erased_components"]


def test_authority_boundary_work_plane(worker: LossyNormalizationWorker) -> None:
    report = worker.run_full_audit()
    assert report["authority"] == "WORK_PLANE"
    assert report["status"] == "PROPOSED"
    assert report["milestone"] == "SOVCTX-M2"
    assert report["ladder_monotonicity_verified"] is True
    assert report["all_code_negative_info_erased"] is True
    assert len(report["ladder_evaluations"]) == 35
