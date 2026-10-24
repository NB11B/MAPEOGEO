"""Tests for Track B information frontier, linear re-entry bounds, and Track C bilateral compatibility."""

from __future__ import annotations

from experiments.rule30_proof_closure.bilateral import (
    evaluate_bilateral_hypothesis,
    evaluate_prize2_and_prize3_closure_metrics,
)
from experiments.rule30_proof_closure.core import (
    enumerate_periodic_hypotheses,
    evolve_single_seed,
)
from experiments.rule30_proof_closure.right import (
    evaluate_ether_chain_bilateral_incompatibility,
    trace_information_frontier,
    verify_bilateral_conservation_and_work_equivalence,
    verify_linear_reentry_horizon_bound,
)


def test_track_b_conservation_and_linear_reentry_bounds():
    cons = verify_bilateral_conservation_and_work_equivalence(steps=48)
    assert cons.passed is True
    assert cons.conservation_mismatches == 0
    assert cons.window_equivalence_mismatches == 0

    samples = verify_linear_reentry_horizon_bound(max_steps=180)
    assert len(samples) == 3
    for s in samples:
        assert s.bound_satisfied is True
        assert s.actual_reentry_horizon_tau <= s.theoretical_linear_upper_bound_k
        assert s.distinct_classes_at_linear_horizon == s.sample_count_m


def test_ether_chain_bilateral_incompatibility_and_frontier():
    ether_res = evaluate_ether_chain_bilateral_incompatibility(max_blocks=3, max_transient_t=4)
    assert ether_res.bilaterally_compatible_states_found == 0
    assert ether_res.right_screening_horizons_verified == {1: 1, 2: 3, 3: 5}

    frontier = trace_information_frontier((0, 1), (0, 0, 0, 0, 0, 1, 0, 0, 0, 0), periods=3)
    assert len(frontier) == 3
    assert frontier[0].leading_ether_blocks == 1


def test_bilateral_hypothesis_elimination_and_prizes_2_3():
    rows = evolve_single_seed(48)
    hyps = enumerate_periodic_hypotheses(max_period=3, transients=(0, 1, 2, 3))
    for h in hyps:
        ev = evaluate_bilateral_hypothesis(h, rows, max_horizon=24)
        assert ev.bilateral_cone_unsat_horizon_h is not None
        assert ev.left_unsat_horizon_h is not None
        assert ev.bilateral_cone_unsat_horizon_h <= ev.left_unsat_horizon_h

    p23 = evaluate_prize2_and_prize3_closure_metrics(steps=64)
    assert p23.shortcut_found is False
    assert p23.anf_max_degree_by_t[4] >= 3
