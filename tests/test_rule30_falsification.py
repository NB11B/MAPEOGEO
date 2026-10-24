"""Unit and qualification tests for the Rule 30 Falsification Benchmark."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import pytest

from experiments.rule30_falsification.benchmark import (
    ANFPolynomial,
    evaluate_center_after_k_steps,
    extract_column,
    rule30_forward_anf,
    rule30_forward_cell,
    rule30_left_sideways_cell,
    rule30_right_sideways_relation,
    run_e1_exact_reconstruction,
    run_e2_geometric_quotient,
    run_e3_composition_closure,
    run_e4_computational_shortcut,
    run_e5_persistent_equivalence,
    run_full_campaign,
    run_g0_g2_prize_qualification,
    run_g3_infinite_horizon_wavefront,
    run_g4_multi_prize_qualification,
    run_g5_three_prize_continuation,
    run_g6_prize_mechanism_qualification,
    run_g7_collatz_return_map_transfer,
    run_g8_symbolic_return_machine_qualification,
    run_g9_period_return_dynamics_qualification,
    run_g10_psmsl_future_work_qualification,
    run_g11_information_boundary_qualification,
    sideways_left_iterated,
    sideways_left_step,
    simulate_spacetime_cone,
)


def test_local_rule30_boolean_and_anf_equivalence() -> None:
    """Verify Rule 30 truth table (00011110_2 = 30) and GF(2) ANF identity."""
    expected_rule30 = {
        (1, 1, 1): 0,
        (1, 1, 0): 0,
        (1, 0, 1): 0,
        (1, 0, 0): 1,
        (0, 1, 1): 1,
        (0, 1, 0): 1,
        (0, 0, 1): 1,
        (0, 0, 0): 0,
    }
    rule_number = 0
    for idx, ((l, c, r), expected) in enumerate(expected_rule30.items()):
        val_bool = rule30_forward_cell(l, c, r)
        val_anf = rule30_forward_anf(l, c, r)
        assert val_bool == expected
        assert val_anf == expected
        rule_number |= expected << (7 - idx)
    assert rule_number == 30


def test_left_sideways_left_permutive_inversion() -> None:
    """Verify leftward sideways reconstruction is an exact involution in the left argument."""
    for l in (0, 1):
        for c in (0, 1):
            for r in (0, 1):
                next_c = rule30_forward_cell(l, c, r)
                reconstructed_l = rule30_left_sideways_cell(next_c, c, r)
                assert reconstructed_l == l


def test_right_sideways_observational_screen_and_wall_invariant() -> None:
    """Verify x_i(t)=0 is transparent (rank 1) and x_i(t)=1 screens x_{i+1}(t) (rank 0)."""
    for l in (0, 1):
        for r in (0, 1):
            # Case 1: c == 0 (transparent window)
            next_c0 = rule30_forward_cell(l, 0, r)
            rank0, adm0 = rule30_right_sideways_relation(l, 0, next_c0)
            assert rank0 == 1
            assert adm0 == (r,)

            # Case 2: c == 1 (information screen)
            next_c1 = rule30_forward_cell(l, 1, r)
            assert next_c1 == (l ^ 1)  # hard wall invariant
            rank1, adm1 = rule30_right_sideways_relation(l, 1, next_c1)
            assert rank1 == 0
            assert adm1 == (0, 1)

            # Negative control: violating the wall invariant when c == 1 yields rank -1
            bad_next = next_c1 ^ 1
            rank_bad, adm_bad = rule30_right_sideways_relation(l, 1, bad_next)
            assert rank_bad == -1
            assert adm_bad == ()


def test_e1_exact_reconstruction_gate() -> None:
    """Verify E1 exact leftward reconstruction and rightward wall invariant over 32 steps."""
    res = run_e1_exact_reconstruction(steps=32)
    assert res.gate_passed is True
    assert res.anf_truth_table_matches == 8
    assert res.left_sideways_mismatches == 0
    assert res.left_zero_cone_boundary_satisfied is True
    assert res.left_diagonal_unit_boundary_satisfied is True
    assert res.right_wall_invariant_violations == 0
    assert 0.45 < res.right_screen_fraction < 0.60


def test_e2_geometric_quotient_asymmetry_and_compression() -> None:
    """Verify E2 LTR vs RTL Myhill-Nerode quotient asymmetry and right-half compression."""
    res = run_e2_geometric_quotient(max_k=5)
    assert res.gate_passed is True
    assert res.ltr_first_cut_always_two is True
    assert res.nontrivial_right_quotient_exists is True
    assert res.asymmetry_verified is True

    # At k=5, right-half raw states = 64, quotient states = 11
    p5 = res.profiles[-1]
    assert p5.k == 5
    assert p5.right_half_raw_size == 64
    assert p5.right_half_quotient_size == 11
    assert p5.rtl_total_bdd_nodes < p5.ltr_total_bdd_nodes


def test_e3_composition_closure_and_autoregressive_identity() -> None:
    """Verify E3 ANF degree growth (2k-1), unique linear invariant, and sideways identity."""
    res = run_e3_composition_closure(max_k=6)
    assert res.gate_passed is True
    assert res.forward_degree_matches_2k_minus_1 is True
    assert res.unique_linear_invariant_verified is True
    assert res.sideways_strictly_sparser_than_forward is True
    assert res.finite_linear_closure_falsified is True
    assert res.sideways_autoregressive_identity_verified is True


def test_e4_computational_shortcut_and_cost_model() -> None:
    """Verify E4 exact equivalence across all 3 methods and honest Theta(N^2) classification."""
    res = run_e4_computational_shortcut(step_sizes=(16, 32, 64))
    assert res.gate_passed is True
    assert res.exact_equivalence_across_all_methods is True
    assert res.constant_factor_reduction_verified is True
    assert res.sub_quadratic_shortcut_found is False


def test_e5_persistent_observational_equivalence_and_psmsl_loss() -> None:
    """Verify R30-E5 persistent vs transient observational equivalence and PSMSL work loss."""
    res = run_e5_persistent_equivalence(max_k=5)
    assert res.gate_passed is True
    assert res.trace_always_refines_single_time is True
    assert res.unrestricted_env_refines_to_full_separation is True
    assert res.zero_vacuum_stabilizes_permanently is True
    assert res.wavefront_congruence_zero_mismatches == 0
    assert res.psmsl_work_equivalence_verified is True

    # Check exact class counts on R_k for k=1..5:
    # Single-time: [2, 3, 4, 9, 11]
    # Temporal-trace: [3, 5, 7, 11, 16]
    assert [h.single_time_classes for h in res.horizon_quotients] == [2, 3, 4, 9, 11]
    assert [h.temporal_trace_classes for h in res.horizon_quotients] == [3, 5, 7, 11, 16]

    # Check patch m=2 (8 states) stabilization at 6 classes for k >= 3 under zero-vacuum
    assert [p.zero_vacuum_trace_classes for p in res.patch_m2_trajectory] == [3, 5, 6, 6, 6]
    assert [p.unrestricted_env_trace_classes for p in res.patch_m2_trajectory] == [3, 5, 7, 8, 8]
    assert all(p.work_relative_loss_zero_vacuum == 0.0 for p in res.patch_m2_trajectory)


def test_full_campaign_integration(tmp_path) -> None:
    """Verify end-to-end campaign runner and JSON serialization."""
    out_file = tmp_path / "rule30_campaign.json"
    campaign = run_full_campaign(
        e1_steps=24,
        e2_max_k=4,
        e3_max_k=5,
        e4_steps=(16, 32),
        e5_max_k=5,
        output_json=out_file,
    )
    assert campaign.all_gates_passed is True
    assert out_file.exists()


def test_lean_formal_file_has_no_escape_hatches() -> None:
    """Verify MAPEOGEOFormal/Rule30Falsification.lean has all 19 theorems and zero escape hatches."""
    lean_file = Path(__file__).resolve().parents[1] / "MAPEOGEOFormal" / "Rule30Falsification.lean"
    assert lean_file.exists()
    text = lean_file.read_text(encoding="utf-8")

    forbidden = {
        "sorry": re.compile(r"\bsorry\b"),
        "admit": re.compile(r"\badmit\b"),
        "axiom_declaration": re.compile(r"(?m)^\s*(?:private\s+)?axiom\b"),
        "unsafe_declaration": re.compile(r"(?m)^\s*(?:private\s+)?unsafe\b"),
    }
    hits = [name for name, pattern in forbidden.items() if pattern.search(text)]
    assert not hits, f"Forbidden escape hatches found: {hits}"

    expected_theorems = [
        "rule30_forward_eq_anf",
        "rule30_left_sideways_reconstructs",
        "rule30_forward_reconstructs_from_sideways",
        "rule30_left_permutive_bijection",
        "rule30_right_screen_when_center_true",
        "rule30_wall_invariant_when_center_true",
        "rule30_right_transparent_when_center_false",
        "rule30_step2_leftmost_linear_decomposition",
        "rule30_step2_right_screen_when_x1_true",
        "rule30_step2_eight_to_three_right_quotient",
        "rule30_sideways_autoregressive_step1",
        "rule30_sideways_autoregressive_step2",
        "rule30_left_cone_nat_reconstruction",
        "e2_trace_bijection_depth2",
        "e2_triangular_step_bijection",
        "rule30_cone_leftmost_xor_bridge",
        "rule30_central_trace_bijection_all_k",
        "e5_persistent_wavefront_modeA_to_modeB",
        "e5_persistent_wavefront_modeB_to_modeA",
    ]
    for thm in expected_theorems:
        assert f"theorem {thm}" in text

    if shutil.which("lean") is not None:
        proc = subprocess.run(
            ["lean", str(lean_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"Lean kernel failed:\n{proc.stdout}\n{proc.stderr}"
        for thm in expected_theorems:
            assert (
                f"'MAPEOGEOFormal.{thm}' does not depend on any axioms" in proc.stdout
            )


def test_uploaded_suite_and_rule30_core_lean_kernel() -> None:
    """Verify the uploaded rule30_suite.py, test_suite.py, failure ledger, and Rule30Core.lean."""
    pkg_dir = Path(__file__).resolve().parents[1] / "experiments" / "rule30_falsification"
    core_lean = pkg_dir / "Rule30Core.lean"
    assert core_lean.exists()
    assert (pkg_dir / "test_results.txt").exists()
    assert (pkg_dir / "test_results_corrected.txt").exists()
    assert (pkg_dir / "results.json").exists()

    # Run unittest suite from experiments/rule30_falsification/test_suite.py
    proc_py = subprocess.run(
        ["python", "-m", "unittest", "discover", "-s", str(pkg_dir), "-p", "test_suite.py", "-v"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_py.returncode == 0, f"test_suite.py failed:\n{proc_py.stdout}\n{proc_py.stderr}"

    # Verify Rule30Core.lean in the Lean 4 kernel
    if shutil.which("lean") is not None:
        proc_lean = subprocess.run(
            ["lean", str(core_lean)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_lean.returncode == 0, f"Rule30Core.lean failed:\n{proc_lean.stdout}\n{proc_lean.stderr}"
        core_theorems = [
            "rule30_left_reconstruct",
            "rule30_step_reconstruct",
            "rule30_sideways_iff",
            "rule30_right_screen",
            "rule30_right_unscreen",
            "rule30_screen_identity",
            "rule30_left_cone_nat_reconstruction",
            "e2_trace_bijection_depth1",
            "e2_trace_bijection_depth2",
            "e2_triangular_step_bijection",
            "rule30_cone_leftmost_xor_bridge",
            "rule30_central_trace_bijection_all_k",
            "e5_persistent_wavefront_modeA_to_modeB",
            "e5_persistent_wavefront_modeB_to_modeA",
        ]
        for thm in core_theorems:
            assert f"'{thm}' does not depend on any axioms" in proc_lean.stdout


def test_g0_g2_prize_qualification_and_official_check_lean() -> None:
    """Verify G0 novelty audit, G2 control separation (Rules 90, 150, 210 vs 30), and Rule30Submission.lean."""
    res = run_g0_g2_prize_qualification(max_k=5)
    assert res.gate_passed is True
    assert res.kit_commit == "cc1e0e0e7c1ae8c971aec5c14aaabb47c7b8c554"
    assert res.lean_version == "4.35.0"
    assert res.public_submissions_audited == 25
    assert res.baseline_equivalents_labeled == 2
    assert res.new_partial_results_labeled == 7
    assert res.controls_collapse_to_rank_one_point_quotient is True
    assert res.rule30_uniquely_reaches_three_depth2_classes is True
    assert res.rule30_uniquely_satisfies_mode_a_and_b_wavefront is True
    assert res.check_lean_verdict_pass is True
    assert res.check_lean_replay_ok is True
    assert res.check_lean_new_axioms_empty is True
    assert len(res.check_lean_verified_headlines) == 103

    by_name = {p.rule_name: p for p in res.control_profiles}
    assert list(by_name["g90"].point_quotient_sizes) == [2, 2, 2, 2, 2]
    assert list(by_name["g150"].point_quotient_sizes) == [2, 2, 2, 2, 2]
    assert list(by_name["g210"].point_quotient_sizes) == [2, 2, 2, 2, 2]
    assert list(by_name["g30"].point_quotient_sizes) == [2, 3, 4, 9, 11]
    assert by_name["g210"].origin_cancels_at_depth2 is True
    assert by_name["g30"].origin_cancels_at_depth2 is False

    pkg_dir = Path(__file__).resolve().parents[1] / "experiments" / "rule30_falsification"
    sub_lean = pkg_dir / "Rule30Submission.lean"
    assert sub_lean.exists()
    sub_text = sub_lean.read_text(encoding="utf-8")
    forbidden = {
        "sorry": re.compile(r"\bsorry\b"),
        "admit": re.compile(r"\badmit\b"),
        "axiom_declaration": re.compile(r"(?m)^\s*(?:private\s+)?axiom\b"),
        "unsafe_declaration": re.compile(r"(?m)^\s*(?:private\s+)?unsafe\b"),
        "native_decide": re.compile(r"\bnative_decide\b"),
        "bv_decide": re.compile(r"\bbv_decide\b"),
    }
    hits = [name for name, pattern in forbidden.items() if pattern.search(sub_text)]
    assert not hits, f"Forbidden tokens in Rule30Submission.lean: {hits}"


def test_g3_infinite_horizon_wavefront_qualification() -> None:
    """Verify Gate G3: infinite-horizon diagonal 2-cycles, iff laws, Problem 1 bridge, and t=6 counterexample."""
    g3 = run_g3_infinite_horizon_wavefront(steps=120)
    assert g3.gate_passed is True
    assert g3.right_diagonal_2cycle_mismatches == 0
    assert g3.left_diagonal_2cycle_mismatches == 0
    assert g3.precursor_iff_mismatches == 0
    assert g3.dichotomy_iff_mismatches == 0
    assert g3.counterexample_t6_verified is True
    assert g3.white_run_lock_mismatches == 0
    assert len(g3.g3_headlines_verified) == 7


def test_g4_multi_prize_qualification() -> None:
    """Verify Gate G4 across P1 (ModeADepth boundary grammar), P2 (discrepancy & bilateral lock), and P3 (sensitivity)."""
    g4 = run_g4_multi_prize_qualification(steps=180, sensitivity_max_t=4)
    assert g4.gate_passed is True
    assert g4.unclassified_steps == 0
    assert g4.unclassified_white_onsets == 0
    assert g4.t6_depth_is_two_and_t7_depth_is_one is True
    assert g4.onset_depths_vary_t2_vs_t6 is True
    assert g4.mode_a_depth_white_run_lock_mismatches == 0
    assert g4.short_white_runs_k_lt_ell_count > 0
    assert g4.discrepancy_step_mismatches == 0
    assert g4.partition_identity_mismatches == 0
    assert g4.bilateral_neighbor_lock_mismatches == 0
    assert g4.locked_white_interior_double_black_steps > 0
    assert g4.black_count_at_horizon + g4.white_count_at_horizon == 180
    assert g4.signed_discrepancy_at_horizon == 2 * g4.black_count_at_horizon - 180
    assert g4.universal_left_sensitivity_mismatches == 0
    assert g4.right_edge_sensitivity_mismatches == 0
    assert g4.block2_composition_mismatches == 0
    assert len(g4.g4_headlines_verified) == 18


def test_g5_three_prize_continuation() -> None:
    """Verify Gate G5: P1 clipped-depth alignment, P2 run-cycle discrepancy, and P3 operator-doubling hierarchy."""
    g5 = run_g5_three_prize_continuation(steps=180)
    assert g5.gate_passed is True
    assert g5.white_run_depth_monus_mismatches == 0
    assert g5.clipped_depth_equiv_mismatches == 0
    assert g5.periodic_driver_0_10_11_locks_halign is True
    assert g5.engineered_infinite_right_countermodel_violates_halign is True
    assert g5.run_cycle_discrepancy_mismatches == 0
    assert g5.first_cycle_net_drift == 2
    assert g5.non_cancelling_cycles_count > 0
    assert g5.doubling_hierarchy_mismatches == 0
    assert [lvl.step_span_b for lvl in g5.doubling_hierarchy] == [1, 2, 4, 8]
    assert [lvl.window_width for lvl in g5.doubling_hierarchy] == [3, 5, 9, 17]
    assert [lvl.truth_table_entries for lvl in g5.doubling_hierarchy] == [8, 32, 512, 131072]
    assert [lvl.anf_degree for lvl in g5.doubling_hierarchy] == [2, 3, 7, 15]
    assert g5.representation_growth_eliminates_naive_shortcut is True
    assert len(g5.g5_headlines_verified) == 9


def test_g6_prize_mechanism_qualification() -> None:
    """Verify Gate G6: P1 cycle return map & 0^r 1 fixed-point exclusion, P2 multi-cycle drift, P3 DAG/ROBDD."""
    g6 = run_g6_prize_mechanism_qualification(steps=180)
    assert g6.gate_passed is True
    assert g6.black_step_overshoot_ge2_mismatches == 0
    assert g6.black_step_z1_mismatches == 0
    assert g6.cycle_0_10_1_early_lock_absorbs_to_ell2_in_one_period is True
    assert g6.cycle_0_10_1_overshoot_absorbs_to_ell2_in_two_periods is True
    assert g6.cycle_0_10_1_transient_window_absorbs_on_vacuum_in_three_periods is True
    assert g6.two_cycle_telescoping_mismatches == 0
    assert g6.multi_cycle_prefix_telescoping_mismatches == 0
    assert g6.locked_neighbor_black_window_checks > 0
    assert g6.locked_neighbor_black_window_mismatches == 0
    assert [p.unmemoized_tree_rule_gates for p in g6.compression_profiles] == [1, 4, 40, 3280]
    assert [p.shared_pyramid_dag_rule_gates for p in g6.compression_profiles] == [1, 4, 16, 64]
    assert g6.dag_sharing_eliminates_tree_blowup_to_quadratic_pyramid is True
    assert g6.robdd_grows_exponentially_with_right_half_depth is True
    assert g6.left_edge_xor_total_mismatches == 0
    assert len(g6.g6_headlines_verified) == 12


def test_g7_collatz_return_map_transfer() -> None:
    """Verify Gate G7 (rule30_collatz_transfer — G7.1 through G7.5)."""
    g7 = run_g7_collatz_return_map_transfer(steps=450)
    assert g7.gate_passed is True
    assert g7.scalar_ell_alone_is_closed is False
    assert g7.scalar_ell_collision_buckets_count >= 5
    assert g7.minimal_collision_witness_ell0_01.w1 == 38
    assert g7.minimal_collision_witness_ell0_01.w2 == 115
    assert (
        g7.minimal_collision_witness_ell0_01.ell_next_1,
        g7.minimal_collision_witness_ell0_01.ell_next_2,
    ) == (2, 1)
    assert g7.minimal_collision_witness_ell1_23.w1 == 20
    assert g7.minimal_collision_witness_ell1_23.w2 == 31
    assert g7.minimal_collision_witness_ell1_23.shared_right_prefix_len == 6
    assert g7.minimal_collision_witness_ell1_23.first_differing_right_column == 7
    assert g7.z0_branch_to_depth1_iff_mismatches == 0
    assert g7.z0_branch_to_depth2_iff_mismatches == 0
    assert g7.critical_boundary_ell_eq_r_ge2_mismatches == 0
    assert g7.long_black_run_reset_to_depth1_mismatches == 0
    assert g7.residue_parity_alone_is_closed is False
    assert g7.refined_window_closure_mismatches == 0
    assert g7.periodic_0r_1b_ge9_all_reset_to_depth1_in_one_period is True
    assert g7.weighted_operator_composition_mismatches == 0
    assert g7.honest_cost_prevents_unjustified_p3_shortcut is True
    assert len(g7.g7_headlines_verified) == 10


def test_g8_symbolic_return_machine_qualification() -> None:
    """Verify Gate R30-PRIZE-G8 (G8.1-G8.6) exact symbolic return-machine qualification."""
    g8 = run_g8_symbolic_return_machine_qualification(steps=450)
    assert g8.gate_passed is True
    assert g8.symbolic_state_checks >= 500
    assert g8.symbolic_state_mismatches == 0
    assert g8.run_word_soundness_checks >= 100
    assert g8.run_word_soundness_mismatches == 0
    assert g8.exact_closure_transitions_count > 0
    assert g8.ambiguous_closure_transitions_count > 0
    assert g8.contradiction_transitions_rejected_count > 0
    assert g8.initial_ambiguous_buckets_at_tau0 == 7
    assert g8.remaining_ambiguous_buckets_after_refinement == 0
    assert g8.max_refined_tail_length_needed >= 4
    assert g8.refinement_preserves_all_realizable_trajectories is True
    assert g8.multi_run_composition_checks >= 100
    assert g8.multi_run_composition_mismatches == 0
    assert g8.multi_run_periods_excluded_count >= 8
    assert g8.spurious_coarse_cycles_eliminated_by_prefix_sync >= 8
    assert g8.word_discrepancy_homomorphism_checks >= 100
    assert g8.word_discrepancy_homomorphism_mismatches == 0
    assert g8.symbolic_machine_step_evaluations > 0
    assert g8.symbolic_machine_cell_updates > g8.symbolic_machine_step_evaluations
    assert len(g8.g8_headlines_verified) == 10


def test_g9_period_return_dynamics_qualification() -> None:
    """Verify Gate R30-PRIZE-G9 (G9.1-G9.5) period-return dynamics qualification."""
    g9 = run_g9_period_return_dynamics_qualification(steps=450)
    assert g9.gate_passed is True
    assert g9.iter_period_return_checks >= 32
    assert g9.iter_period_return_mismatches == 0
    assert g9.or_col_word_checks >= 200
    assert g9.or_col_word_mismatches == 0
    assert g9.masked_equiv_strictly_coarser_than_prefix_eq is True
    assert g9.depth_zero_one_period_masked_equiv_diverges_in_period_two is True
    assert g9.period2_meta_stable_trap_periods == 145
    assert g9.period2_meta_stable_max_spatial_prefix_width == 17
    assert g9.period2_meta_stable_break_step == 305
    assert g9.word_0_1_7_syncs_or_col_without_depth_stabilization is True
    assert g9.ether_c7_breaks_one_period_sync_but_syncs_at_subharmonic_q2 is True
    assert g9.truncated_ether_c7cut_survival_checks >= 40
    assert g9.truncated_ether_c7cut_survival_mismatches == 0
    assert g9.zbl_post_support_zero_branching_verified is True
    assert g9.zbl_max_odd_survival_depth_by_support == {
        "4": 7,
        "6": 11,
        "8": 13,
        "10": 19,
    }
    assert g9.col0_word_discrepancy_checks >= 150
    assert g9.col0_word_discrepancy_mismatches == 0
    assert g9.periodic_width_consumption_exact is True
    assert len(g9.symbolic_return_machine_vs_pyramid_profiles) == 4
    assert all(
        p["symbolic_return_machine_cell_updates"]
        < p["shared_causal_pyramid_cell_updates"]
        for p in g9.symbolic_return_machine_vs_pyramid_profiles
    )
    assert len(g9.g9_headlines_verified) == 11


def test_g10_psmsl_future_work_qualification() -> None:
    """Verify Gate R30-PRIZE-G10 (G10.1-G10.6) PSMSL future-work qualification."""
    g10 = run_g10_psmsl_future_work_qualification(steps=450)
    assert g10.gate_passed is True
    assert g10.vendor_row2_projection_is_work_equivalent is True
    assert g10.vendor_row1_projection_is_not_work_equivalent is True
    assert g10.vendor_information_loss_projection_lossless is True
    assert g10.boolean_right_screen_work_lossless is True
    assert g10.boolean_truth_table_audit_checks >= 512
    assert g10.boolean_truth_table_audit_mismatches == 0
    assert g10.all_tested_words_exhibit_strict_horizon_refinement is True
    assert [w.reentry_horizon_k for w in g10.minimal_reentry_witnesses] == [1, 2, 3]
    assert g10.g9_metastable_trap_reentry_horizon_k == 138
    assert g10.g9_metastable_trap_first_differing_column_at_t14_vs_t28 == 14
    assert g10.quotient_shift_congruence_checks >= 700
    assert g10.quotient_shift_congruence_mismatches == 0
    assert g10.ether_c7_quotient_period_q == 2
    assert g10.finitely_supported_right_half_r6_persistent_equiv_to_ether_c7 is True
    assert g10.two_sided_truncated_ether_c7cut_reentry_steps_by_n == {
        "1": 15,
        "2": 22,
        "3": 29,
    }
    assert g10.single_seed_active_support_grows_linearly is True
    assert g10.quotient_discrepancy_invariance_checks >= 12
    assert g10.quotient_discrepancy_invariance_mismatches == 0
    assert g10.quotient_work_compression_savings_ratio_m3 > 0.9
    assert len(g10.g10_headlines_verified) == 11


def test_g11_information_boundary_qualification() -> None:
    """Verify Gate R30-PRIZE-G11 (G11.1-G11.4) PSMSL information-boundary obstruction."""
    g11 = run_g11_information_boundary_qualification(steps=450)
    assert g11.gate_passed is True
    assert g11.ether_block_homomorphism_checks >= 60
    assert g11.ether_block_homomorphism_mismatches == 0
    assert g11.ether_peeling_law_checks >= 45
    assert g11.ether_peeling_law_mismatches == 0
    assert g11.ether_chain_all_horizon_checks >= 150
    assert g11.ether_chain_all_horizon_mismatches == 0
    assert g11.single_block_r6_vs_r6_9_reentry_horizon_k == 7
    assert g11.r_cut6_u14_v14_alternation_verified_periods == 120
    assert g11.u14_adversarial_right_tail_break_periods == 19
    assert g11.right_chain_guaranteed_screening_horizons_by_blocks == {
        "1": 1,
        "2": 3,
        "3": 5,
        "4": 7,
        "5": 9,
    }
    assert g11.left_edge_universal_zero_screening_checks >= 20
    assert g11.left_edge_universal_zero_screening_mismatches == 0
    assert g11.zbl_post_support_zero_screening_checks >= 14
    assert g11.zbl_post_support_zero_screening_mismatches == 0
    assert g11.or_col_word_length_invariance_checks == 12
    assert g11.or_col_word_length_invariance_mismatches == 0
    assert len(g11.single_seed_finite_collision_reentry_samples) == 3
    assert g11.all_tested_orbit_collisions_eventually_reenter is True
    assert g11.quotient_width_saving_checks == 15
    assert g11.quotient_width_saving_mismatches == 0
    assert g11.balanced_word_zero_drift_verified is True
    assert len(g11.g11_headlines_verified) == 10
    assert g11.total_headlines_verified == 103
    assert g11.replayed_constants == 693



