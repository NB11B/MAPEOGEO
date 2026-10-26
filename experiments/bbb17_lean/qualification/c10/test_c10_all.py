"""Unified COLLATZ-C10 Qualification & Falsification Test Suite (Gates G0-G6).

Executes all five workstreams (`WS1`-`WS5`) and generates the deterministic C10
qualification artifacts under `experiments/bbb17_lean/artifacts/c10/`.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from qualification.c10.candidate_potential_tests import (
    verify_potential_falsifications_and_drawdown,
)
from qualification.c10.exact_oracle import (
    nondescent_sandwich_check,
    parity_word_of,
    word_A,
    word_B,
    word_D,
    word_ones,
)
from qualification.c10.lift_falsification import (
    run_trajectory_falsification_sweep,
    verify_first_crossing_tree,
    verify_lifting_recurrences,
)
from qualification.c10.spectral_path_search import analyze_spectral_near_collisions
from qualification.c10.valuation_sequence_search import (
    verify_constructed_valuation_sequences,
    verify_steiner_one_circuit_obstruction,
)
from qualification.c10.unified_transition_discovery import (
    verify_mechanism_a_delayed_descent_and_quotient_collapse,
    verify_normalized_reservoir_and_exponential_decay,
    verify_projective_fixed_point_laws,
    verify_psmsl_matrix_algebra,
    verify_section9_trichotomy_and_two_point_shift,
    verify_section10_divergent_orbit_and_valuation_laws,
    verify_section11_ordered_valuation_goodstein_four_color_and_falsification,
    verify_section12_rotation_reducibility_and_goodstein_falsification,
    verify_section13_adversarial_first_crossing_and_no_crossing_branch,
    verify_section14_sharpened_cap_s40_certificate_and_excess_valuation,
    verify_section15_surplus_diophantine_and_self_similarity_coupling,
    verify_section16_surplus_reduced_cap_mod3_lock_and_post_crossing_operator,
    verify_signed_projective_gap_and_surviving_lifts,
    verify_unified_transition_conservation,
)


class TestCollatzC10All(unittest.TestCase):
    """Unified test suite for COLLATZ-C10 (Gates G0-G6)."""

    def test_ws1_lifting_recurrences(self) -> None:
        res = verify_lifting_recurrences(max_depth=14)
        self.assertEqual(res["failures"], 0)
        self.assertEqual(res["total_words_checked"], (1 << 15) - 2)

    def test_ws1_first_crossing_tree_and_pincer_exceptions(self) -> None:
        res = verify_first_crossing_tree(max_depth=18)
        self.assertEqual(res["true_deficit_exceptions_count"], 0)
        self.assertEqual(res["pre_crossing_mismatches"], 0)
        self.assertEqual(res["coarse_pincer_exceptions_count"], 3)
        pincer_m_vals = sorted(x["m_min"] for x in res["coarse_pincer_exceptions"])
        self.assertEqual(pincer_m_vals, [27, 47, 63])

    def test_ws1_trajectory_sweep_and_nondescent_sandwich(self) -> None:
        res = run_trajectory_falsification_sweep(limit_n=50000)
        self.assertEqual(res["first_crossing_nondescent_count"], 0)
        self.assertEqual(res["sandwich_violations"], 0)

    def test_ws2_spectral_near_collisions_and_eliahou_window(self) -> None:
        res = analyze_spectral_near_collisions(max_a=1500, n0_bound=1024)
        self.assertEqual(res["spectral_band_violations"], 0)
        self.assertEqual(res["window_hits_r_le_64"], 0)
        self.assertIsNotNone(res["first_window_hit_for_n0_1024"])

    def test_ws3_potentials_and_peak_drawdown(self) -> None:
        res = verify_potential_falsifications_and_drawdown(limit_n=5000)
        self.assertTrue(res["v2_succ_even_step_jump_verified"])
        self.assertEqual(res["drawdown_failures"], 0)
        self.assertEqual(res["power_threshold_descent_failures"], 0)

    def test_ws4_steiner_and_constructed_cycles(self) -> None:
        steiner = verify_steiner_one_circuit_obstruction(max_a=500)
        self.assertEqual(steiner["formula_mismatches"], 0)
        self.assertEqual(steiner["integral_nontrivial_cycles_count"], 0)
        self.assertEqual(len(steiner["steiner_survivors"]), 1)
        self.assertEqual(steiner["steiner_survivors"][0]["a"], 1)
        val_seq = verify_constructed_valuation_sequences(max_odd_steps=128)
        self.assertEqual(val_seq["nontrivial_cycles_found"], 0)

    def test_ws5_infinite_nondescent_sandwich_on_27(self) -> None:
        # Track n = 27 up to its first descent step (r = 59 accelerated steps; at r=58 it is still >= 27)
        for r in range(1, 59):
            chk = nondescent_sandwich_check(27, r)
            self.assertTrue(chk["fr_ge_n"], f"Expected F^{r}(27) >= 27")
            self.assertTrue(chk["lower_bound_holds"])
            self.assertTrue(chk["upper_bound_holds"])
            self.assertTrue(chk["power_ratio_holds"])

    def test_ws6_unified_psmsl_mapeogeo_transition_system(self) -> None:
        psmsl = verify_psmsl_matrix_algebra(max_depth=8)
        self.assertEqual(psmsl["failures"], 0)
        trans = verify_unified_transition_conservation(limit_n=2000)
        self.assertEqual(trans["conservation_failures"], 0)
        self.assertEqual(trans["sharpened_bound_failures"], 0)

    def test_ws6_normalized_reservoir_and_exponential_decay(self) -> None:
        norm_res = verify_normalized_reservoir_and_exponential_decay(limit_n=1000)
        self.assertEqual(norm_res["increment_mismatches"], 0)
        self.assertEqual(norm_res["monotonicity_failures"], 0)
        self.assertEqual(norm_res["telescoping_mismatches"], 0)
        self.assertEqual(norm_res["threshold_descent_mismatches"], 0)
        self.assertEqual(norm_res["exponential_decay_failures"], 0)

    def test_ws6_projective_fixed_point_laws(self) -> None:
        fp_res = verify_projective_fixed_point_laws(max_n=2000)
        self.assertEqual(fp_res["step_extension_mismatches"], 0)
        self.assertEqual(fp_res["fixed_point_dichotomy_mismatches"], 0)
        self.assertEqual(fp_res["universal_offset_bound_failures"], 0)
        self.assertEqual(fp_res["post_crossing_nondescent_prefixes"], 0)

    def test_ws6_signed_projective_gap_and_surviving_lifts(self) -> None:
        gap_res = verify_signed_projective_gap_and_surviving_lifts(max_n=1000)
        self.assertEqual(gap_res["gap_identity_mismatches"], 0)
        self.assertEqual(gap_res["gap_recurrence_mismatches"], 0)
        self.assertEqual(gap_res["modular_branch_lock_mismatches"], 0)
        self.assertEqual(gap_res["descent_band_mismatches"], 0)
        self.assertEqual(gap_res["reservoir_gap_identity_mismatches"], 0)
        self.assertEqual(gap_res["surviving_lift_cap_failures"], 0)

    def test_ws6_mechanism_a_delayed_descent_and_quotient_collapse(self) -> None:
        mech_a = verify_mechanism_a_delayed_descent_and_quotient_collapse(max_n=1000)
        self.assertEqual(mech_a["orbit_shift_mismatches"], 0)
        self.assertEqual(mech_a["parity_flip_mismatches"], 0)
        self.assertEqual(mech_a["delayed_descent_lock_failures"], 0)

    def test_ws6_section9_trichotomy_and_two_point_shift(self) -> None:
        sec9 = verify_section9_trichotomy_and_two_point_shift(max_n=500)
        self.assertGreater(sec9["two_point_pairs_checked"], 0)
        self.assertEqual(sec9["two_point_shift_mismatches"], 0)
        self.assertEqual(sec9["two_point_parity_flip_mismatches"], 0)
        self.assertEqual(sec9["interior_gap_ge4_failures"], 0)

    def test_ws6_section10_divergent_orbit_and_valuation_laws(self) -> None:
        sec10 = verify_section10_divergent_orbit_and_valuation_laws(max_n=1000)
        self.assertGreater(sec10["odd_blocks_checked"], 0)
        self.assertEqual(sec10["single_block_dichotomy_failures"], 0)
        self.assertEqual(sec10["return_map_conservation_mismatches"], 0)
        self.assertEqual(sec10["excursion_power_shift_failures"], 0)

    def test_ws6_section11_ordered_valuation_goodstein_four_color_and_falsification(self) -> None:
        sec11 = verify_section11_ordered_valuation_goodstein_four_color_and_falsification(max_s=7)
        self.assertGreater(sec11["compositions_checked"], 0)
        self.assertEqual(sec11["offset_recurrence_mismatches"], 0)
        self.assertEqual(sec11["sandwich_failures"], 0)
        self.assertEqual(sec11["swap_law_mismatches"], 0)
        self.assertEqual(sec11["nontrivial_integer_cycle_quotients"], 0)
        self.assertGreater(sec11["trivial_cycle_repeat_quotients"], 0)
        self.assertEqual(sec11["goodstein_plus_one_mismatches"], 0)
        self.assertEqual(sec11["four_color_one_circuit_descent_failures"], 0)
        self.assertTrue(sec11["ce06_contracting_block_survival_verified"])

    def test_ws6_section12_rotation_reducibility_and_goodstein_falsification(self) -> None:
        sec12 = verify_section12_rotation_reducibility_and_goodstein_falsification(max_s=7)
        self.assertEqual(sec12["cyclic_shift_mismatches"], 0)
        self.assertEqual(sec12["one_block_rotation_mismatches"], 0)
        self.assertEqual(sec12["universal_sandwich_reducible_mismatches"], 0)
        self.assertEqual(sec12["nondescent_odd_return_crossing_exceptions"], 0)
        self.assertEqual(sec12["goodstein_mod4_dichotomy_mismatches"], 0)
        self.assertTrue(sec12["ce07_rotation_order_verified"])
        self.assertTrue(sec12["ce08_contracting_survival_at_165_verified"])
        self.assertTrue(sec12["ce09_goodstein_tail_reset_at_27_verified"])

    def test_ws6_section13_adversarial_first_crossing_and_no_crossing_branch(self) -> None:
        sec13 = verify_section13_adversarial_first_crossing_and_no_crossing_branch(
            max_s_words=12, max_s_cap=306
        )
        self.assertEqual(sec13["first_crossing_words_checked"], 4879)
        self.assertEqual(sec13["offset_cap_violations"], 0)
        self.assertEqual(sec13["sharpened_offset_cap_violations"], 0)
        self.assertEqual(sec13["surviving_representatives_found"], 0)
        self.assertEqual(sec13["pre_crossing_growth_violations"], 0)
        self.assertEqual(sec13["benchmark_mismatches"], 0)
        self.assertEqual(sec13["max_coarse_survivor_cap_le_306"], 99729)
        self.assertEqual(sec13["max_sharpened_survivor_cap_le_306"], 99567)

    def test_ws6_section14_sharpened_cap_s40_certificate_and_excess_valuation(self) -> None:
        sec14 = verify_section14_sharpened_cap_s40_certificate_and_excess_valuation()
        self.assertEqual(sec14["cap_reconciliation_mismatches"], 0)
        self.assertEqual(sec14["max_coarse_cap_le_40"], 381)
        self.assertEqual(sec14["max_sharpened_cap_le_40"], 375)
        self.assertTrue(sec14["s40_below_1024_verified"])
        self.assertTrue(sec14["ce10_non_monotone_odd_returns_verified"])

    def test_ws6_section15_surplus_diophantine_and_self_similarity_coupling(self) -> None:
        sec15 = verify_section15_surplus_diophantine_and_self_similarity_coupling(
            max_s_direct=12, max_s_duality=970
        )
        self.assertEqual(sec15["precrossing_prefixes_checked"], 4403)
        self.assertEqual(sec15["precrossing_diophantine_solutions_found"], 0)
        self.assertEqual(sec15["max_sharpened_cap_le_970"], 99597)
        self.assertEqual(sec15["v2_eq_one_two_step_descent_mismatches"], 0)
        self.assertTrue(sec15["ce11_v2_ge_two_no_three_step_descent_verified"])
        self.assertTrue(sec15["ce12_non_precrossing_diophantine_witness_verified"])

    def test_ws6_section16_surplus_reduced_cap_mod3_lock_and_post_crossing_operator(self) -> None:
        sec16 = verify_section16_surplus_reduced_cap_mod3_lock_and_post_crossing_operator(max_s=12)
        self.assertEqual(sec16["prefixes_verified"], 4403)
        self.assertEqual(sec16["final_block_reduction_mismatches"], 0)
        self.assertEqual(sec16["mod3_lock_mismatches"], 0)
        self.assertGreater(sec16["v2_eq_two_branches_checked"], 0)
        self.assertEqual(sec16["v2_eq_two_four_step_mismatches"], 0)
        self.assertTrue(sec16["witness_15_19_verified"])


def generate_c10_artifacts() -> None:
    """Run full C10 verification suite and write deterministic JSON/JSONL artifacts."""
    artifacts_dir = ROOT_DIR / "artifacts" / "c10"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    ws1_lifts = verify_lifting_recurrences(max_depth=14)
    ws1_tree = verify_first_crossing_tree(max_depth=18)
    ws1_sweep = run_trajectory_falsification_sweep(limit_n=100000)
    ws2_spec = analyze_spectral_near_collisions(max_a=2000, n0_bound=1024)
    ws3_pot = verify_potential_falsifications_and_drawdown(limit_n=10000)
    ws4_steiner = verify_steiner_one_circuit_obstruction(max_a=500)
    ws4_val = verify_constructed_valuation_sequences(max_odd_steps=128)
    ws6_psmsl = verify_psmsl_matrix_algebra(max_depth=8)
    ws6_trans = verify_unified_transition_conservation(limit_n=2000)

    baseline_manifest = {
        "campaign": "COLLATZ-C10",
        "active_branch": "research/collatz-c10-proof-closure",
        "preserved_branches": {
            "research/bbb17-lean-proof": "fbf5d2b",
            "research/collatz-three-tracks": "dbf40bb",
            "research/collatz-c6-adaptive-descent": "48e6502",
        },
        "lean_toolchain": "leanprover/lean4:v4.29.0-rc8",
        "frozen_base_module": "ThreeTracks.lean",
        "c10_modules": [
            "CollatzProofClosure/Definitions.lean",
            "CollatzProofClosure/DeficitLifting.lean",
            "CollatzProofClosure/SpectralCrossing.lean",
            "CollatzProofClosure/GlobalDescent.lean",
            "CollatzProofClosure/CycleObstructions.lean",
            "CollatzProofClosure/UnifiedTransitionSystem.lean",
            "CollatzProofClosure/MainTheorem.lean",
        ],
    }
    (artifacts_dir / "baseline_manifest.json").write_text(
        json.dumps(baseline_manifest, indent=2) + "\n", encoding="utf-8"
    )

    experiment_manifest = {
        "campaign": "COLLATZ-C10",
        "workstreams": {
            "WS1_deficit_lifting": {
                "lifting_depth_exhaustive": 14,
                "first_crossing_depth_exhaustive": 18,
                "lean_kernel_depth_certified": 64,
                "trajectory_sweep_limit_n": 100000,
            },
            "WS2_spectral_crossing": {
                "max_odd_steps_convergents": 2000,
                "eliahou_n0_bound": 1024,
                "lean_kernel_empty_window_max_r": 64,
            },
            "WS3_global_descent_potentials": {
                "peak_drawdown_limit_n": 10000,
                "power_threshold_limit_n": 2000,
            },
            "WS4_cycle_obstructions": {
                "steiner_one_circuit_max_a": 500,
                "constructed_valuation_max_odd_steps": 128,
                "lean_kernel_cycle_exclusion_max_r": 64,
            },
        },
    }
    (artifacts_dir / "experiment_manifest.json").write_text(
        json.dumps(experiment_manifest, indent=2) + "\n", encoding="utf-8"
    )

    counterexamples = [
        {
            "id": "CE-C10-01",
            "workstream": "WS1",
            "hypothesis_tested": "Coarse C8 spectral pincer 3 * m_min(w) * Delta(w) > a(w) * A(w) holds for all first-crossing words w",
            "status": "FALSIFIED",
            "witnesses": ws1_tree["coarse_pincer_exceptions"],
            "lean_theorem": "BBB17.pincer_hypothesis_strictly_stronger_at_47",
            "resolution": "Replaced coarse linear upper bound 3*B <= a*A with exact 2-adic pre-crossing deficit recurrence (2*y_0 + 1 < 2*m_0 + l*(2*D_0 - A_0)), which has 0 exceptions.",
        },
        {
            "id": "CE-C10-02",
            "workstream": "WS3",
            "hypothesis_tested": "2-adic tail valuation v_2(n + 1) is non-increasing across all Collatz steps",
            "status": "FALSIFIED",
            "witnesses": [{"n": 62, "next_n": 31, "v2_n_plus_1": 0, "v2_next_plus_1": 5}],
            "lean_theorem": "BBB17.CollatzProofClosure.v2_succ_potential_even_step_jump_witness",
            "resolution": "Replaced single-step v_2(n+1) monotony with multi-step exit theorem every_nat_exits_allTrue_branch and universal peak drawdown every_nat_experiences_peak_drawdown.",
        },
        {
            "id": "CE-C10-03",
            "workstream": "WS3",
            "hypothesis_tested": "Positive linear combination alpha*u + beta*v (alpha > 0) in canonical (j, u, v) coordinates strictly decreases across positive-register phases",
            "status": "FALSIFIED",
            "witnesses": [{"j": 0, "u": 2, "v": 0, "next_j": 0, "next_u": 4, "next_v": 0}],
            "lean_theorem": "BBB17.CollatzProofClosure.positive_linear_uv_potential_strict_increase",
            "resolution": "Replaced single-phase linear (u, v) potentials with the non-descent multiplicative power bound 2^r * n^{a_r} * F^r(n) <= n * (3n + 1)^{a_r}.",
        },
        {
            "id": "CE-C10-04",
            "workstream": "WS4",
            "hypothesis_tested": "Steiner 1-circuit inequality (2^{a+k} - 3^a)*(2^a - 1) <= 3^a - 2^a alone excludes all a >= 2 without integrality check",
            "status": "FALSIFIED",
            "witnesses": [{"a": 2, "k": 2, "r": 4, "delta": 7, "wordB": 5, "min_m": 3, "equation": "7 * m = 5"}],
            "lean_theorem": "BBB17.CollatzProofClosure.no_two_odd_block_cycle",
            "resolution": "Discharged a = 2 for all k >= 0 via exact Diophantine non-divisibility in no_two_odd_block_cycle.",
        },
        {
            "id": "CE-C10-05",
            "workstream": "WS6_Track1_Cycles",
            "hypothesis_tested": "Threshold-free offset non-divisibility (2^K - 3^s) does not divide B(returnMapWord ks) for all s >= 2 with 2^K > 3^s",
            "status": "FALSIFIED",
            "witnesses": [
                {"ks": [1, 1], "s": 2, "K": 4, "delta": 7, "wordB": 7, "quotient_n": 1},
                {"word": [False, True], "r": 2, "a": 1, "delta": 1, "wordB": 2, "quotient_n": 2},
            ],
            "lean_theorem": "BBB17.CollatzProofClosure.trivial_cycle_repeat_divides_offset_witness",
            "resolution": "Added exact threshold B(w) > 2 * Delta(w) (and B(w) > Delta(w) for odd-starting returnMapWord ks) in noNontrivialCycle_iff_offset_nondivisibility.",
        },
        {
            "id": "CE-C10-06",
            "workstream": "WS6_Track2_DivergentOrbits",
            "hypothesis_tested": "Encountering a contracting odd-to-odd return block (k_j >= 1, so u_{j+1} < u_j) immediately forces descent below the initial integer n",
            "status": "FALSIFIED",
            "witnesses": [{"n": 27, "ks": [0, 1], "u_0": 27, "u_1": 41, "u_2": 31}],
            "lean_theorem": "BBB17.CollatzProofClosure.contracting_odd_block_survives_above_initial_at_27",
            "resolution": "Replaced single-block contraction descent with Goodstein 2-adic tail rank decay allTrueWord_goodstein_plus_one_law and Four-Color 1-circuit reducibility oneCircuitWord_reducible_descent.",
        },
        {
            "id": "CE-C10-07",
            "workstream": "WS6_Section12_RotationDivisibility",
            "hypothesis_tested": "Requiring Delta(w) | B(rot_j(w)) across all cyclic rotations rot_j(w) imposes independent modular divisibility constraints beyond Delta(w) | B(w)",
            "status": "FALSIFIED",
            "witnesses": [{"ks_rotations": [[0, 1, 2], [1, 2, 0], [2, 0, 1]], "delta": 37, "B_rotations": [23, 53, 49], "identity": "2^(k+1)*B(rot_1(ks)) = 3*B(ks) + Delta"}],
            "lean_theorem": "BBB17.CollatzProofClosure.cyclic_rotation_preserves_divisibility_and_shifts_offset_witness",
            "resolution": "Proved wordB_cyclic_shift_identity and cycle_rotation_quotient_shift_and_divisibility: because gcd(D_1, Delta) = 1, modular divisibility is invariant under cyclic rotation, while integer ordering n_0 <= n_1 <=> B(w1++w2) <= B(w2++w1) forces k_min = 0 and k_max >= 1.",
        },
        {
            "id": "CE-C10-08",
            "workstream": "WS6_Section12_UnavoidableReducibility",
            "hypothesis_tested": "Every globally contracting complete odd-to-odd return sequence (validOddReturnSeq n ks with 2^{K_s} > 3^s and n > 1) forces u_s < n without prefix non-descent",
            "status": "FALSIFIED",
            "witnesses": [{"n": 165, "s": 17, "K": 27, "ks": [3, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 2], "u_1": 31, "u_17": 167}],
            "lean_theorem": "BBB17.CollatzProofClosure.contracting_odd_return_word_survives_at_165_witness",
            "resolution": "Proved returnMap_universal_sandwich_reducible_descent, nondescent_prefix_reservoir_threshold_reducible_descent, and first_crossing_linear_offset_exclusion.",
        },
        {
            "id": "CE-C10-09",
            "workstream": "WS6_Section12_GlobalValuationRank",
            "hypothesis_tested": "A purely local coordinatewise lexicographic rank on (u_s, v_2(u_s + 1)) is non-increasing across completed odd-to-odd circuits",
            "status": "FALSIFIED",
            "witnesses": [{"n": 27, "ks": [0, 1], "u_0": 27, "v2_u0_plus_1": 2, "u_1": 41, "v2_u1_plus_1": 1, "u_2": 31, "v2_u2_plus_1": 5}],
            "lean_theorem": "BBB17.CollatzProofClosure.goodstein_tail_rank_resets_above_initial_at_27_witness",
            "resolution": "Proved odd_step_goodstein_branch_dichotomy and singleOddWord_shifted_plus_one_identity, showing that coordinatewise monotonicity fails across k >= 1 resets.",
        },
        {
            "id": "CE-C10-10",
            "workstream": "WS6_Section14_NoCrossingBranch",
            "hypothesis_tested": "Inside the No-First-Crossing branch (2^{K_s} <= 3^s), consecutive odd returns u_0 < u_1 < u_2 < ... are stepwise monotonically increasing",
            "status": "FALSIFIED",
            "witnesses": [{"n": 27, "ks": [0, 1], "s": 2, "K_2": 3, "u_0": 27, "u_1": 41, "u_2": 31}],
            "lean_theorem": "BBB17.CollatzProofClosure.no_crossing_branch_not_stepwise_monotone_at_27_witness",
            "resolution": "Distinguished relative-to-start expansion (u_s > n, proved in no_first_crossing_shifted_growth_and_nondescent) from stepwise monotonicity (u_{s+1} > u_s).",
        },
        {
            "id": "CE-C10-11",
            "workstream": "WS6_Section15_SelfSimilarityCoupling",
            "hypothesis_tested": "Forced parity divergence at step v = v_2(t) of a first-crossing surplus u_s = n + t immediately forces descent T^{v+1}(u_s) < n for all v >= 1",
            "status": "FALSIFIED",
            "witnesses": [{"n": 7, "t": 4, "v": 2, "u_s": 11, "T2_n": 17, "T2_us": 26, "T3_us": 13}],
            "lean_theorem": "BBB17.CollatzProofClosure.surplus_v2_ge_two_no_three_step_descent_witness",
            "resolution": "Proved first_crossing_surplus_v2_eq_one_forced_two_step_descent for v_2(t) = 1 (where 2^2 = 4 > 3^1 forces T^2(u_s) < n for all n > 3t + 1), while for v_2(t) >= 2, k_0 = 0 forces a_2 = 2 so 3^2 = 9 > 8 = 2^3 prevents 3-step descent.",
        },
        {
            "id": "CE-C10-12",
            "workstream": "WS6_Section15_SurplusDiophantine",
            "hypothesis_tested": "Formal solutions to B_s = Delta_s * n + 2^{K_s} * t with n > 1 and 0 <= t < s/3 do not exist even when PreCrossingReturnSeq ks is omitted",
            "status": "FALSIFIED",
            "witnesses": [{"ks": [0, 0, 1, 2, 0], "s": 5, "K_5": 8, "delta_5": 13, "B_5": 347, "n": 7, "t": 1, "u_4": 5, "u_5": 8}],
            "lean_theorem": "BBB17.CollatzProofClosure.non_preCrossing_diophantine_solution_at_s5_witness",
            "resolution": "Proved first_crossing_surplus_diophantine_iff_admissible_survivor: under PreCrossingReturnSeq ks, any integer solution automatically satisfies 2-adic word admissibility and intermediate non-descent u_j > n, whereas omitting PreCrossingReturnSeq allows solutions whose earlier crossing prefix already descended.",
        },
    ]
    with (artifacts_dir / "counterexamples.jsonl").open("w", encoding="utf-8") as f:
        for item in counterexamples:
            f.write(json.dumps(item) + "\n")

    corrections = [
        {
            "id": "CORR-C10-01",
            "workstream": "WS1",
            "from_formulation": "Prefix-expanding upper bound 3 * B(w) <= a(w) * A(w) (valid only up to first spectral crossing)",
            "to_formulation": "Universal Non-Descent Multiplicative Power Bound 2^r * n^{a_r} * F^r(n) <= n * (3n + 1)^{a_r} and Two-Sided Diophantine Sandwich (valid across all non-descending prefixes of any length r, even after arbitrarily many spectral crossings)",
            "lean_theorems": [
                "BBB17.CollatzProofClosure.nondescent_prefix_power_bound",
                "BBB17.CollatzProofClosure.nondescent_diophantine_sandwich",
            ],
        },
        {
            "id": "CORR-C10-02",
            "workstream": "WS2",
            "from_formulation": "Treating Obligation A (EveryNatCrossesSpectrally) solely as a sufficient hypothesis in two_obligations_imply_collatz",
            "to_formulation": "Proving Obligation A is strictly necessary for CollatzConjecture (CollatzConjecture -> EveryNatCrossesSpectrally) because every non-crossing prefix strictly grows",
            "lean_theorems": [
                "BBB17.CollatzProofClosure.noncrossing_prefix_strict_growth",
                "BBB17.CollatzProofClosure.descent_forces_prior_firstCrossing",
                "BBB17.CollatzProofClosure.collatz_implies_everyNatCrossesSpectrally",
            ],
        },
        {
            "id": "CORR-C10-03",
            "workstream": "WS4_WS5",
            "from_formulation": "Finite parity-word enumeration (which scales as O(2^r)) for cycle and contraction exclusion",
            "to_formulation": "Polynomial O(r^2) Eliahou/C10 power-ratio window exclusion (2^r * 1024^a <= 3073^a), discharging all 2^64 parity words of length 1 <= r <= 64 in Lean 4 kernel decide",
            "lean_theorems": [
                "BBB17.CollatzProofClosure.checkEliahouWindow1024_64",
                "BBB17.CollatzProofClosure.no_nontrivial_cycle_length_le_64",
                "BBB17.CollatzProofClosure.infinite_nondescent_diophantine_obstruction_system",
            ],
        },
    ]
    with (artifacts_dir / "corrections.jsonl").open("w", encoding="utf-8") as f:
        for item in corrections:
            f.write(json.dumps(item) + "\n")

    independent_results = {
        "ws1_lifting_recurrences": ws1_lifts,
        "ws1_first_crossing_tree": ws1_tree,
        "ws1_trajectory_sweep": ws1_sweep,
        "ws2_spectral_near_collisions": ws2_spec,
        "ws3_potentials_and_drawdown": ws3_pot,
        "ws4_steiner_one_circuit": ws4_steiner,
        "ws4_constructed_valuation_sequences": ws4_val,
        "ws6_psmsl_matrix_algebra": ws6_psmsl,
        "ws6_unified_transition_conservation": ws6_trans,
    }
    (artifacts_dir / "independent_check_results.json").write_text(
        json.dumps(independent_results, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    generate_c10_artifacts()
    unittest.main()
