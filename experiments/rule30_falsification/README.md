# Rule 30 Falsification Suite (MAPEOGEO Integration — E1 through R30-E5)

Python 3.10+, no third-party runtime dependencies; Lean 4 (`v4.33.1`) kernel-verified.

```bash
# Run the standalone suite and 7-test unittest regression
python experiments/rule30_falsification/rule30_suite.py --depth 6 --benchmark 256
python -m unittest discover -s experiments/rule30_falsification -p "test_suite.py" -v

# Run the extended MAPEOGEO E1–E5 qualification suite (including live Lean 4 kernel checks)
pytest tests/test_rule30_falsification.py -v

# Run the Lean 4 kernel directly on both formal modules
lean experiments/rule30_falsification/Rule30Core.lean
lean MAPEOGEOFormal/Rule30Falsification.lean
```

## Five Bounded Falsification Studies

- **E1 (`e1` / `run_e1_exact_reconstruction`):** Exact local forward and left-permutive sideways identities, right-neighbor screening ($x_i(t)=1$), seed-cone boundary checks, and recursive left-column reconstruction $\mathcal{S}_L^k$ from the two central columns $(\mathbf{c}_0, \mathbf{c}_1)$.
- **E2 (`e2` / `run_e2_geometric_quotient`):**
  1. **Temporal Central-Trace Readout Quotient (`rule30_suite.py`):** Evaluates equivalence of width-$(2k+1)$ initial states producing the same central-cell trace $(x_0(0), \dots, x_0(k))$ over $t=0 \dots k$. Across all $2^{2k+1}$ initial states, there are **always** $2^{k+1}$ reachable traces, each with a uniform preimage class size of exactly $2^k$.
  2. **Observationally Scoped Single-Step Spatial Quotient (`benchmark.py`):** Compares Left-to-Right vs. Right-to-Left variable orderings for the single target cell $c_k = x_0(k)$, demonstrating directional asymmetry from $x_i(t)=1$ rightward screening (e.g., $8 \to 3$ at $k=2$, $128 \to 20$ at $k=6$).
- **E3 (`e3` / `run_e3_composition_closure`):** Exact Algebraic Normal Form (ANF) over $\mathbb{F}_2$ via Boolean Möbius transform (`rule30_suite.py`) and symbolic polynomial composition (`benchmark.py`). Forward ANF degree satisfies $\deg(\Psi \circ \mathcal{F}^k) = 2k - 1$ for $k \ge 2$ with monomial counts $1, 4, 10, 30, 122, 346, 1360, 4852$ ($k=0 \dots 7$), while sideways ANF $\mathcal{S}_L^k$ has strictly lower degree and up to $4.5\times$ fewer monomials ($4, 7, 18, 31, 112, 337, 1088$ for $k=1 \dots 7$).
- **E4 (`e4` / `run_e4_computational_shortcut`):** Exact central-cell agreement through step $256$ across fixed-width scalar simulation, causal-diamond + right-screen short-circuit pruning, and bit-packed integer evolution, with separate primitive-operation counts and wall-clock timings.
- **R30-E5 (`run_e5_persistent_equivalence`):** Distinguishes transient single-step screening from persistent multi-step observational equivalence across horizons $k=1 \dots N$:
  1. **Single-Time vs. Full Temporal-Trace Classes on $R_k \in \{0,1\}^{k+1}$:** At every horizon $k=1 \dots 6$, full temporal trace equivalence ($3, 5, 7, 11, 16, 25$ classes) is a strict refinement of single-time readout equivalence ($2, 3, 4, 9, 11, 20$ classes).
  2. **Refinement vs. Stabilization on Fixed Spatial Patches $P_m = (x_0, \dots, x_m)$:**
     - Under an **unrestricted outer right environment** ($x_{>m}(0) \in \{0,1\}$), single-step classes **refine until complete separation** (for $m=2$, $3 \to 5 \to 7 \to 8$ trace classes by $k=4$), falsifying naive persistence when external right inputs reflect hidden bits back toward the center.
     - Under a **zero-vacuum right exterior** ($x_{>m}(0) = 0$), the equivalence classes refine once ($5 \to 6$ at $k=3$ for $m=2$; $7 \to 10$ at $k=4$ for $m=3$) and **permanently stabilize** ($6$ classes for all $k \ge 3$ at $m=2$; $10$ classes for all $k \ge 4$ at $m=3$).
  3. **Proven 2-Cycle Wavefront Congruence & PSMSL Work-Equivalence Reduction:** Connects permanent stabilization under a zero exterior to the analytic $O(1)$ wavefront projection operator $\Pi_{\text{wavefront}}$ (`apply_wavefront_quotient_operator`), verified against MAPEOGEO's `work_relative_information_loss == 0.0` across all horizons.

## Lean 4 Kernel Verification (`KERNEL_VERIFIED`)

Both [`Rule30Core.lean`](Rule30Core.lean) (14 theorems) and [`MAPEOGEOFormal/Rule30Falsification.lean`](../../MAPEOGEOFormal/Rule30Falsification.lean) (19 theorems) are **compiled and verified by the Lean 4.33.1 kernel** with **zero `sorry`s and zero axioms** (`does not depend on any axioms`):

1. **Arbitrary-Depth E1 Finite-Cone Sideways Reconstruction (`rule30_left_cone_nat_reconstruction`):** Proves by induction on $k \in \mathbb{N}$ that $k$ iterations of `sidewaysColumnIter` starting from $(X_0, X_1)$ reconstruct $(X_{-k}, X_{-(k-1)})$ for all $k, t \in \mathbb{N}$.
2. **Complete Arbitrary-Depth E2 Bridge (`rule30_cone_leftmost_xor_bridge` & `rule30_central_trace_bijection_all_k`):** Proves for **every** depth $k \in \mathbb{N}$ that `rule30ConeEval k w = bne (w 0) (rule30ConeEval k (clearLeftmost w))` ($c_k = x_{-k}(0) \oplus F_k$ with $F_k$ independent of $x_{-k}(0)$), and connects `rule30ConeEval` directly to `e2_triangular_step_bijection` to prove that `rule30CentralTraceDirect k R` is a two-sided bijection on `BoolVec k` ($\{0,1\}^{k+1}$) for every $k \in \mathbb{N}$ and every right-half state $R$.
3. **R30-E5 Persistent 2-Cycle Wavefront Congruence (`e5_persistent_wavefront_modeA_to_modeB` & `e5_persistent_wavefront_modeB_to_modeA`):** Proves that the right-wavefront pairs Mode A $((0,1,0,0,\dots) \text{ vs } (0,1,1,0,\dots))$ at anchor $m$ and Mode B $((1,1,0,0,\dots) \text{ vs } (1,0,1,0,\dots))$ at anchor $m+1$ form a closed 2-periodic transition congruence under Rule 30 that advects the discrepancy rightward at speed $+1$ ($m \to m+1 \to m+2 \to \dots$) while keeping all interior cells $\le m+t$ identical forever.

## Preserved Failure Ledger

The initial regression in `test_suite.py` asserted `69` ANF monomials at $k=4$; exact Boolean Möbius computation gave `122`. The original failing run is preserved in [`test_results.txt`](test_results.txt), and the corrected passing run is preserved in [`test_results_corrected.txt`](test_results_corrected.txt).

## Official Wolfram Rule 30 Prize Qualification (`R30-PRIZE-G0` through `G9`)

[`Rule30Submission.lean`](Rule30Submission.lean) is compiled against official `Rule30PrizeKit` commit `cc1e0e0e7c1ae8c971aec5c14aaabb47c7b8c554` in `leanprover/lean4:v4.35.0` and verified by `Check.lean` (`"verdict": "pass"`, `"replay": {"constants": 593, "ok": true}`, `"newAxioms": []`, **82/82** headline theorems verified in [`check_verdict.json`](check_verdict.json)):

```bash
# External reproduction against official Wolfram Rule30PrizeKit
git clone https://github.com/WolframInstitute/Rule30PrizeKit.git experiments/rule30_falsification/Rule30PrizeKit
cd experiments/rule30_falsification/Rule30PrizeKit
git checkout cc1e0e0e7c1ae8c971aec5c14aaabb47c7b8c554
cp ../Rule30Submission.lean ./Rule30Submission.lean
cd lean && lake build Ruliology.CellularAutomata.Rule30Prize Ruliology.CellularAutomata.Rule30Realization Ruliology.CellularAutomata.Rule30MaskedJen Ruliology.CellularAutomata.Rule30Diagonals Ruliology.CellularAutomata.Rule30BlackRuns && cd ..
LEAN_PATH="lean/.lake/build/lib/lean" lean -R . -o lean/.lake/build/lib/lean/Rule30Submission.olean Rule30Submission.lean
LEAN_PATH="lean/.lake/build/lib/lean" lean --run Check.lean Rule30Submission --claim partial \
  --headline Rule30Submission.g2_rule30_separates_controls_90_150_210 \
  --headline Rule30Submission.g210_origin_cancellation_evolG \
  --headline Rule30Submission.e5_two_step_wavefront_shield_evol \
  --headline Rule30Submission.e5_wavefront_separates_controls \
  --headline Rule30Submission.g3_modeA_next_step_iff \
  --headline Rule30Submission.g3_modeA_step_dichotomy \
  --headline Rule30Submission.g3_modeA_persists_during_black_run \
  --headline Rule30Submission.g3_single_seed_infinite_diagonal_modeA_modeB_cycles \
  --headline Rule30Submission.g3_modeA_at_center_white_onsets_implies_problem1 \
  --headline Rule30Submission.g3_pre_onset_wavefront_implies_problem1 \
  --headline Rule30Submission.g3_single_seed_white_onset_counterexample_t6 \
  --headline Rule30Submission.evol_seed_zero_eq_prize_center \
  --headline Rule30Submission.g4_p1_every_step_has_modeADepth \
  --headline Rule30Submission.g4_p1_t6_counterexample_resolved_by_modeADepth \
  --headline Rule30Submission.g4_p1_modeADepth_white_run_lock \
  --headline Rule30Submission.g4_p1_modeADepth_at_white_onsets_implies_problem1 \
  --headline Rule30Submission.g4_p1_modeADepth_unique \
  --headline Rule30Submission.g4_p1_white_onset_depths_vary_on_single_seed \
  --headline Rule30Submission.g4_p1_composed_reduction_of_problem1 \
  --headline Rule30Submission.g4_p2_discrepancy_succ \
  --headline Rule30Submission.g4_p2_blackCount_add_whiteCount \
  --headline Rule30Submission.g4_p2_modeADepth_locks_both_neighbors \
  --headline Rule30Submission.g4_p2_locked_white_interior_forces_double_black_neighbors \
  --headline Rule30Submission.g4_p2_sublinear_rate_implies_problem2 \
  --headline Rule30Submission.g4_p2_bounded_discrepancy_implies_problem2 \
  --headline Rule30Submission.g4_p3_evol_causal_cone \
  --headline Rule30Submission.g4_p3_center_universal_left_sensitivity \
  --headline Rule30Submission.g4_p3_center_right_edge_sensitivity \
  --headline Rule30Submission.g4_p3_evol_add \
  --headline Rule30Submission.g4_p3_evolBlock2_eq_evol_double \
  --headline Rule30Submission.g5_p1_modeADepth_after_white_run \
  --headline Rule30Submission.g5_p1_clipped_depth_observational_equivalence \
  --headline Rule30Submission.g5_p1_clipped_depth_alignment_implies_problem1 \
  --headline Rule30Submission.g5_p2_white_run_discrepancy_shift \
  --headline Rule30Submission.g5_p2_black_run_discrepancy_shift \
  --headline Rule30Submission.g5_p2_white_black_cycle_discrepancy \
  --headline Rule30Submission.g5_p2_first_white_black_cycle_net_drift_plus_two \
  --headline Rule30Submission.g5_p3_evolPow2_eq_evol_pow2 \
  --headline Rule30Submission.g5_p3_evolPow2_universal_left_sensitivity \
  --headline Rule30Submission.g6_p1_one_black_step_from_overshoot_ge2 \
  --headline Rule30Submission.g6_p1_one_black_step_from_z1 \
  --headline Rule30Submission.g6_p1_cycle_return_map_0r1_early_lock \
  --headline Rule30Submission.g6_p1_cycle_return_map_0r1_overshoot \
  --headline Rule30Submission.g6_p1_modeADepth_two_is_fixed_point_of_0r1 \
  --headline Rule30Submission.g6_p1_constant_onset_depth_excludes_white_black_period \
  --headline Rule30Submission.g6_p1_no_periodic_0r1_from_outside_window \
  --headline Rule30Submission.g6_p2_two_cycle_discrepancy_telescoping \
  --headline Rule30Submission.g6_p2_periodic_cycle_linear_discrepancy_drift \
  --headline Rule30Submission.g6_p2_locked_white_run_neighbor_black_window \
  --headline Rule30Submission.g6_p3_evol_left_edge_xor_decomposition \
  --headline Rule30Submission.g6_p3_evolPow2_left_linear_decomposition \
  --headline Rule30Submission.g7_p1_depth_alone_not_closed_under_cycle_01 \
  --headline Rule30Submission.g7_p1_depth_one_not_closed_under_cycle_01 \
  --headline Rule30Submission.g7_p1_black_step_from_z0_to_depth1_iff \
  --headline Rule30Submission.g7_p1_black_step_from_z0_to_depth2_iff \
  --headline Rule30Submission.g7_p1_cycle_0r1_at_boundary_ell_eq_r_forces_next_ge_two \
  --headline Rule30Submission.g7_p1_long_black_run_resets_to_modeADepth_one \
  --headline Rule30Submission.g7_p1_right_cone_agree_bounded \
  --headline Rule30Submission.g7_p1_refined_window_state_closes_cycle_transition \
  --headline Rule30Submission.g7_p1_no_periodic_0r_1b_for_b_ge_9 \
  --headline Rule30Submission.g7_p2_weighted_event_operator_composition \
  --headline Rule30Submission.g8_p1_every_step_realizes_symbolic_state \
  --headline Rule30Submission.g8_p1_runWord_rowAt \
  --headline Rule30Submission.g8_p1_rowAt_append_split \
  --headline Rule30Submission.g8_p1_symbolic_refinement_preserves_realizability \
  --headline Rule30Submission.g8_p1_symbolic_runWord_resolves_g7_collision \
  --headline Rule30Submission.g8_p1_runWord_append \
  --headline Rule30Submission.g8_p1_col0Word_append \
  --headline Rule30Submission.g8_p1_symbolic_prefix_synchronization_excludes_arbitrary_period \
  --headline Rule30Submission.g8_p1_multi_run_period_with_long_black_and_white_excluded \
  --headline Rule30Submission.g8_p2_wordDiscrepancyWeight_append \
  --headline Rule30Submission.g9_p1_iterPeriodReturn_rowAt \
  --headline Rule30Submission.g9_p1_orColWord_rowAt \
  --headline Rule30Submission.g9_p1_prefix_eq_implies_masked_equiv_strict \
  --headline Rule30Submission.g9_p1_masked_equiv_diverges_after_one_period \
  --headline Rule30Submission.g9_p1_ether_c7_period_two_center_breaks_one_period_sync_but_syncs_at_two_periods \
  --headline Rule30Submission.g9_p1_truncated_ether_c7cut_survives_arbitrarily_many_periods \
  --headline Rule30Submission.g9_p1_deterministic_theta_forcing_beyond_support \
  --headline Rule30Submission.g9_p1_subharmonic_masked_return_synchronization_excludes_arbitrary_period \
  --headline Rule30Submission.g9_p1_period_return_masked_synchronization_implies_problem1 \
  --headline Rule30Submission.g9_p2_col0Word_discrepancy_identity \
  --headline Rule30Submission.g9_p2_p3_periodic_word_discrepancy_and_width_consumption
```

- **Gates G0–G2 (`run_g0_g2_prize_qualification`):** Audits 65 official catalog modules + 25 public submissions ([`g0_novelty_audit.json`](g0_novelty_audit.json)) and proves on `evolG` (`Rule30Realization.evol`) that Rule 30 uniquely reaches 3 depth-2 response classes (`xm2`, `!xm2`, `xor xm2 xm1`) and Mode A/B wavefront shielding, whereas all three `Rule30Realization` counterexample controls (`g90`, `g150`, and nonlinear `g210`) collapse to rank-1 (`g2_rule30_separates_controls_90_150_210`, `g210_origin_cancellation_evolG`, `e5_wavefront_separates_controls`).
- **Gate G3 (`run_g3_infinite_horizon_wavefront`):** Proves infinite-horizon Mode A $\leftrightarrow$ Mode B 2-cycles on both single-seed diagonals (`g3_single_seed_infinite_diagonal_modeA_modeB_cycles`), exact 1-step precursor and dichotomy `iff` laws (`g3_modeA_next_step_iff`, `g3_modeA_step_dichotomy`), conditional implications to `Rule30Prize.Problem1` (`g3_modeA_at_center_white_onsets_implies_problem1`, `g3_pre_onset_wavefront_implies_problem1`), and the preserved fixed-column counterexample at $t=6$ (`g3_single_seed_white_onset_counterexample_t6`).
- **Gate G4 (`run_g4_multi_prize_qualification`):**
  - **Prize 1 (`G4-P1`):** Generalizes `ModeA` ($\ell=1$) to the depth-indexed boundary grammar `ModeADepth t ℓ`, proving uniqueness (`g4_p1_modeADepth_unique`), 100% single-seed completeness for all $t \ge 1$ (`g4_p1_every_step_has_modeADepth`), resolution of the $t=6$ counterexample (`g4_p1_t6_counterexample_resolved_by_modeADepth`), the quantifier alternation audit (`g4_p1_white_onset_depths_vary_on_single_seed`), the unified white-run lock formula `cell (w + k) 1 = decide (ℓ ≤ k)` (`g4_p1_modeADepth_white_run_lock`), and the composed reduction of `Rule30Prize.Problem1` (`g4_p1_composed_reduction_of_problem1`).
  - **Prize 2 (`G4-P2`):** Establishes exact step recurrence, signed discrepancy, sublinear envelope sufficiency (`g4_p2_sublinear_rate_implies_problem2`, `g4_p2_bounded_discrepancy_implies_problem2`), and black/white partition laws for `Rule30Prize.blackCount`, and proves that `ModeADepth w ℓ` locks both neighbor columns $+1$ and $-1$ (`g4_p2_modeADepth_locks_both_neighbors`, `g4_p2_locked_white_interior_forces_double_black_neighbors`).
  - **Prize 3 (`G4-P3`):** Formalizes single-bit input perturbation `flipInput` and 2-step block composition `evolBlock2` on `Rule30Realization.evol`, proving causal light-cone locality $[-t, +t]$ (`g4_p3_evol_causal_cone`), universal left-edge sensitivity (`g4_p3_center_universal_left_sensitivity`), active right-edge sensitivity (`g4_p3_center_right_edge_sensitivity`), semigroup composition (`g4_p3_evol_add`), and `evolBlock2 x k p = evol x (2 * k) p` (`g4_p3_evolBlock2_eq_evol_double`).
- **Gate G5 (`run_g5_three_prize_continuation`):**
  - **Prize 1 (`G5-P1`):** Proves the white-run monus transition law `ModeADepth (w + r) (ℓ - r)` (`g5_p1_modeADepth_after_white_run`), clipped-depth observational equivalence `clipDepth ℓ (K + 1)` (`g5_p1_clipped_depth_observational_equivalence`), and the finite-state clipped-depth reduction of `Rule30Prize.Problem1` (`g5_p1_clipped_depth_alignment_implies_problem1`).
  - **Prize 2 (`G5-P2`):** Proves exact white-run (`-r`), black-run (`+b`), and full-cycle (`+(b - r)`) discrepancy shift formulas (`g5_p2_white_black_cycle_discrepancy`) and falsifies strict cycle-by-cycle cancellation (`g5_p2_first_white_black_cycle_net_drift_plus_two`).
  - **Prize 3 (`G5-P3`):** Formalizes the recursive operator-doubling hierarchy `evolPow2 d` ($T, T^2, T^4, T^8, \dots$), proves `evolPow2 d x p = evol x (2^d) p` (`g5_p3_evolPow2_eq_evol_pow2`) and universal left-edge sensitivity (`g5_p3_evolPow2_universal_left_sensitivity`), and demonstrates empirically that representation growth ($2^{2b+1}$ table entries and $3^b$ unmemoized tree calls vs. $b^2$ causal-diamond updates) eliminates naive logarithmic-depth doubling shortcuts.
- **Gate G6 (`run_g6_prize_mechanism_qualification`):**
  - **Prize 1 (`G6-P1`):** Establishes the complete white/black cycle return map on `ModeADepth` across 1-step black runs (`g6_p1_one_black_step_from_overshoot_ge2`, `g6_p1_one_black_step_from_z1`, `g6_p1_cycle_return_map_0r1_early_lock`, `g6_p1_cycle_return_map_0r1_overshoot`), proves that $\ell = 2$ (`ModeADepth · 2`) is an absorbing fixed point for every `0^r 1` cycle with $r \ge 10$ (`g6_p1_modeADepth_two_is_fixed_point_of_0r1`), proves that any `0^r 1^b` periodic trajectory with eventually constant onset depth is impossible (`g6_p1_constant_onset_depth_excludes_white_black_period`), and proves that no `0^r 1` trajectory ($r \ge 10$) can ever visit `[0, r - 8] ∪ [r + 1, ∞)` (`g6_p1_no_periodic_0r1_from_outside_window`).
  - **Prize 2 (`G6-P2`):** Proves two-cycle and multi-cycle periodic discrepancy telescoping $\Delta(A + M(r+b)) = \Delta(A) + M(b - r)$ (`g6_p2_two_cycle_discrepancy_telescoping`, `g6_p2_periodic_cycle_linear_discrepancy_drift`) and proves that every locked white run forces simultaneous bilateral neighbor black runs of length $r - \ell - 1$ on columns $+1$ and $-1$ (`g6_p2_locked_white_run_neighbor_black_window`).
  - **Prize 3 (`G6-P3`):** Proves the exact left-edge XOR linear decomposition `evol x t 0 = xor (x (-t)) (evol (setInputFalse x (-t)) t 0)` for all $t$ and all doubling scales `evolPow2 d` (`g6_p3_evol_left_edge_xor_decomposition`, `g6_p3_evolPow2_left_linear_decomposition`), and benchmarks shared pyramid DAG evaluation ($b^2$ `rule` gate calls vs. $(3^b-1)/2$ unmemoized tree calls) and canonical ROBDD decision-node growth ($5 \to 11 \to 53$ left-to-right; $4 \to 7 \to 28$ right-to-left).
- **Gate G7 (`run_g7_collatz_return_map_transfer` — `rule30_collatz_transfer`):**
  - **G7.1 (Macro-State Sufficiency Falsification):** Proves that scalar boundary depth $\ell$ alone is **not** a closed deterministic event state across short white-black cycles (`g7_p1_depth_alone_not_closed_under_cycle_01` at $\ell_0=0$ and `g7_p1_depth_one_not_closed_under_cycle_01` at $\ell_0=1$), and preserves the minimal single-seed collision pairs ($w_1=38 \text{ vs } w_2=115$ at $\ell=0, (r,b)=(1,1) \to \ell_{\text{next}} \in \{2, 1\}$; and $w_1=20 \text{ vs } w_2=31$ at $\ell=1, (r,b)=(2,3) \to \ell_{\text{next}} \in \{3, 4\}$ with 6 shared right-hand cells `1..6`, differing first at column $7$).
  - **G7.2 (Phase-Normalized Operator Library):** Proves exact `iff` branching laws on the local boundary tail $\sigma = (\mathrm{cell}\,a\,2, \mathrm{cell}\,a\,3, \mathrm{cell}\,a\,4)$ when a black step opens a locked wall `ModeADepth a 0` (`g7_p1_black_step_from_z0_to_depth1_iff`, `g7_p1_black_step_from_z0_to_depth2_iff`), proves that the critical boundary $\ell = r \ge 1$ under `0^r 1` forces $\ell_{\text{next}} \ge 2$ (`g7_p1_cycle_0r1_at_boundary_ell_eq_r_forces_next_ge_two`), and proves that any black run of length $b \ge 9$ on column $0$ is a universal constant-$1$ reset macro (`g7_p1_long_black_run_resets_to_modeADepth_one`).
  - **G7.3 (Closure of the Refined Window State):** Proves bounded right-cone agreement (`g7_p1_right_cone_agree_bounded`) and proves that refining the event state to $S = (\ell, \sigma_N)$ of width $N = \ell_{\text{next}} + 1 + L$ closes the $L$-step cycle transition deterministically (`g7_p1_refined_window_state_closes_cycle_transition`).
  - **G7.4 (Periodic-Word Exclusion):** Composes `g7_p1_long_black_run_resets_to_modeADepth_one` with `g6_p1_constant_onset_depth_excludes_white_black_period` to exclude every periodic word $0^r 1^b$ ($r \ge 1, b \ge 9$) after any transient $A$ (`g7_p1_no_periodic_0r_1b_for_b_ge_9`).
  - **G7.5 (Weighted & Costed Event Operators):** Proves additive composition of the discrepancy-weighted event operator `applyCycleWeight` (`g7_p2_weighted_event_operator_composition`) and accounts for the 4-part cost $C_{\text{total}} = C_{\text{construct}} + C_{\text{evaluate}} + C_{\text{recover}} + C_{\text{storage}}$, showing that maintaining the refined tail $\sigma_N$ requires $C_{\text{recover}} = \Theta(N^2)$ bit operations.
- **Gate G8 (`run_g8_symbolic_return_machine_qualification` — `G8.1` through `G8.6`):**
  - **G8.1 (Variable-Length Symbolic Event State):** Represents the event state as $S = (\ell, \tau)$ (`RealizesSymbolicState t ℓ τ`) where $\ell \in \mathbb{N}$ is the first-black right-boundary depth and $\tau : \mathrm{List\ Bool}$ is a variable-length right-neighbor tail word `rowAt t (ℓ + 2) τ.length`, proving universal realizability across all single-seed steps $t \ge 1$ (`g8_p1_every_step_realizes_symbolic_state`).
  - **G8.2 (Certified Word-Driven Event Transitions & Three-Outcome Classifier):** Defines `stepRow` and `runWord`, proves exact soundness against Rule 30 spacetime evolution (`g8_p1_runWord_rowAt`: `runWord (col0Word t L) (rowAt t p (n + L)) = rowAt (t + L) p n`), and classifies candidate transitions into `EXACT_CLOSURE`, `AMBIGUOUS_CLOSURE`, and `CONTRADICTION`.
  - **G8.3 (Counterexample-Guided Symbolic State Refinement):** Proves prefix splitting (`g8_p1_rowAt_append_split`), realizability preservation under prefix extension (`g8_p1_symbolic_refinement_preserves_realizability`), and exact `runWord` resolution of the G7 collision pair (`g8_p1_symbolic_runWord_resolves_g7_collision`), and verifies that iterative prefix refinement resolves all 7 ambiguous `(ell, r, b)` buckets across the 106 single-seed event cycles ($t \le 450$) with 0 remaining collisions.
  - **G8.4 (Composing Arbitrary Multi-Run Periodic Center Words):** Proves associative composition of `runWord` (`g8_p1_runWord_append`: `runWord (w₁ ++ w₂) σ = runWord w₂ (runWord w₁ σ)`) and concatenation of center-column words (`g8_p1_col0Word_append`).
  - **G8.5 (Cyclic Abstract Witness Search & Multi-Run Period Exclusions):** Proves that for **any** hypothetical period $P > 0$ of `Rule30Prize.center` (with arbitrarily many white and black runs), synchronizing the length-$P$ symbolic right-boundary prefix across periods forces column $1$ to be $P$-periodic and contradicts `not_adjacent 0` (`g8_p1_symbolic_prefix_synchronization_excludes_arbitrary_period`), and proves unconditional exclusion of multi-run periods containing a long black run $1^s$ ($s \ge 9$) followed by a white run $0^r$ even when arbitrary additional runs of total length $P - s - r$ follow in the period (`g8_p1_multi_run_period_with_long_black_and_white_excluded`).
  - **G8.6 (Discrepancy & Cost Observables on the Symbolic Return Machine):** Defines `wordDiscrepancyWeight : List Bool → Int`, proves the exact additive homomorphism `wordDiscrepancyWeight (w₁ ++ w₂) = wordDiscrepancyWeight w₁ + wordDiscrepancyWeight w₂` (`g8_p2_wordDiscrepancyWeight_append`), and tracks step and cell evaluation costs across the symbolic machine.
- **Gate G9 (`run_g9_period_return_dynamics_qualification` — `G9.1` through `G9.5`):**
  - **G9.1 (`iterPeriodReturn` & `orColWord`):** Defines the $m$-period return operator `iterPeriodReturn w m` ($F_w^m$) and the masked period-observation operator `orColWord w`, proving exact agreement with cellular evolution (`g9_p1_iterPeriodReturn_rowAt`, `g9_p1_orColWord_rowAt`).
  - **G9.2 (Smallest 1-Period Observational Equivalence & Meta-Stable Quasi-Periods):** Defines `MaskedPeriodEquiv w σ₁ σ₂` (`orColWord w σ₁ = orColWord w σ₂`), proves it strictly coarsens spatial prefix equality (`g9_p1_prefix_eq_implies_masked_equiv_strict`), falsifies un-shielded 1-period equivalence by exhibiting explicit depth-0 states that are `MaskedPeriodEquiv` in period 1 but diverge in period 2 (`g9_p1_masked_equiv_diverges_after_one_period`), and documents the **145-period ($290$-step) meta-stable period-7 trap** for $w = [1, 0]$ from `init = {1, 2}` (which reaches a spatial prefix agreement width of $W = 17$ before breaking at step $305$).
  - **G9.3 (Orbit Trichotomy, Sub-Harmonic $q = 2$ Ether `c7`, and ZBL Post-Support Forcing):** Proves that the infinite $7 \times 4$ Ether `c7` realizes an exact period-2 center column that breaks 1-period ($P = 2$) right-boundary synchronization (`evol c7 0 1 = false ≠ true = evol c7 2 1`) and synchronizes only at the sub-harmonic $q = 2$ ($2P = 4$) (`g9_p1_ether_c7_period_two_center_breaks_one_period_sync_but_syncs_at_two_periods`), proves that finite-support truncations `c7cut N` survive with an alternating center column for arbitrarily many steps $t \le 7N$ (`g9_p1_truncated_ether_c7cut_survives_arbitrarily_many_periods`), and proves via the Zero-Boundary Left-Half (ZBL) triangular map `zblTheta` that beyond any finite support width $W$, free bits have zero branching (`f j = g j`, `g9_p1_deterministic_theta_forcing_beyond_support`).
  - **G9.4 & G9.5 (Sub-Harmonic Period-Return Exclusion, `Problem1` Reduction, and Prizes 2 & 3):** Proves that for any period $P > 0$ and any sub-harmonic period multiple $q > 0$, discrete period-return masked synchronization contradicts `orCol_not_eventuallyPeriodic 0` (`g9_p1_subharmonic_masked_return_synchronization_excludes_arbitrary_period`), connects this directly to `Rule30Prize.Problem1` (`g9_p1_period_return_masked_synchronization_implies_problem1`), and proves exact multi-period word discrepancy telescoping and boundary width consumption (`g9_p2_col0Word_discrepancy_identity`, `g9_p2_p3_periodic_word_discrepancy_and_width_consumption`).

