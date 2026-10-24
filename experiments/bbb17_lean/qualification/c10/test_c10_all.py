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
