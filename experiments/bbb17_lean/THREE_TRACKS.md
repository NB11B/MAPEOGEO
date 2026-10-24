# Collatz three-track falsification campaign

Parent: certified equivalence checkpoint `fbf5d2b`. This branch MUST NOT assert the Collatz conjecture.

1. **Recurrence:** `orbit(n,cap)` distinguishes observed arrival at 1, a detected nontrivial cycle, and a bound-exhausted trajectory. A cap result is NOT a divergence proof. Global beep recurrence remains unproved.
2. **Canonical geometry:** `S=u+v` is exactly conserved by the even-input phase (`u` odd). In the odd-input phase it is nondecreasing: the reservoir is exhausted when `v<k+1`, producing **strict growth**. Thus S is NOT a global descending potential. Preserve this counterexample to any naive Lyapunov claim.
3. **Parity composition:** A valid length-r accelerated parity word yields an affine map `(A*n+B)/2^r`. Prefix parity validity is checked separately. This is an exact arithmetic identity on its parity cylinder; it does not imply all orbits terminate.

Run `python -m unittest -v test_three_tracks.py` and `python three_tracks.py --starts 10000 --cap 10000 --depth 8`.

Next Lean gate: prove `S` conservation/nondecrease and parity affine composition for arbitrary natural inputs; retain explicit parity preconditions. Any recurrence potential must reject observed cycles and be well-founded.

## Lean 4 Certification (`ThreeTracks.lean`)

`ThreeTracks.lean` formally proves all three next-gate obligations and all five `BBB17-R7-001` formal qualification gates over all natural numbers without `sorry` or non-standard axioms:

- **Track B & R7-D / R7-F (Universal Max-Plus High-Water Law, `(j, u, S)` Conjugacy, Semilattice Fold & Linear No-Go)**:
  - `evenPhase_highWater_eq`, `oddPhase_highWater_eq_max`, `resetPhase_highWater_eq_max`: Exact phase laws for $S = u + v$.
  - `nextCanonicalTriple_highWater_eq_max` & `nextCanonicalTriple_highWater_nondecreasing`: Universal 3-branch identity $S' = \max(S, u')$ and global monotonicity $S' \ge S$ across all canonical phases ($u = 0$, $u = 2k+1$, $u = 2k > 0$).
  - `toHighWaterTriple_nextCanonicalTriple`, `fromHighWaterTriple_toHighWaterTriple`, `toHighWaterTriple_fromHighWaterTriple`: Exact coordinate bijection $(j, u, v) \leftrightarrow (j, u, S)$ ($S \ge u$) and exact operator conjugacy with `nextHighWaterTriple`.
  - `highWaterOp_comp`, `highWaterOp_comm`, `highWaterOp_idem`, & `iterateCanonicalTriple_highWater_eq_fold`: Join-semilattice laws $H_b(H_a(S)) = H_{\max(a,b)}(S)$ and multi-step compositional fold $S_r = \max(S_0, u_1, \ldots, u_r)$.
  - `oddPhase_highWater_strict_growth_iff`, `posReg_highWater_strict_growth_iff_record`, & `posReg_highWater_conserved_when_bounded`: Exact characterization of reservoir exhaustion ($S' > S \iff v < k + 1 \iff u' > S$).
  - `no_nontrivial_linear_invariant`: Universal 3-witness no-go theorem proving that any linear form $a j + b u + c v$ preserved by $(0,1,0)\to(0,0,1)$, $(0,2,0)\to(0,4,0)$, and $(0,0,0)\to(1,1,0)$ satisfies $a = b = c = 0$.
- **Track R7-E (Corrected Reset Execution Cost $T_{\mathrm{reset}}(j) = 2j^2 + 8j + 6$ & Handoff Refutation)**:
  - `reset_loop_run_exact_cost_and_beeps` & `resetPhase_exact_cost_and_beeps`: Kernel-checked proof that from `canonConfig j 0 v`, the literal BBB17 machine executes in **exactly $2j^2 + 8j + 6$ steps**, emits **exactly $j + 1$ beeps** (terminal beep at step $2j^2 + 8j + 5$), and arrives at `canonConfig (j+1) (j+1) (v - (j+1))`.
  - `resetPhaseSteps_sub_handoffResetPoly` & `resetPhaseSteps_ne_handoffResetPoly`: Formal proof that $T_{\mathrm{reset}}(j) - (j^2 + 8j + 6) = j^2$, refuting the earlier $j^2 + 8j + 6$ handoff polynomial for all $j > 0$.
- **Track C & R7-C (Affine Parity-Word Operator Composition, Modulo-$2^r$ Bijection & Length-7 Catalog)**:
  - `parityWord_affine_identity`, `parityWord_divisibility`, & `parityWord_residue_shift`: Exact affine identity $2^{|w|} \cdot \operatorname{applyParityWord}(m, w) = 3^{\operatorname{ones}(w)} \cdot m + B(w)$ and shift periodicity modulo $2^{|w|}$.
  - `wordResidue_spec`, `validParityWord_iff_mod_eq_wordResidue`, `parityWordOf_wordResidue`, & `wordResidue_parityWordOf`: Constructive canonical residue representative $\operatorname{wordResidue}(w) < 2^{|w|}$ and **exact bijection** between length-$r$ parity words and residue classes modulo $2^r$.
  - `length7_catalog_size`, `length7_all_reject_pos_cycle`, & `length7_no_positive_fixed_point`: Mechanized kernel check across all $2^7 = 128$ parity words of length 7 certifying that no positive integer $m > 0$ is a valid fixed point of any length-7 parity word.
  - `base7_odd_shift_breaks_parityWord`, `base7_unit_shift_breaks_parityWord`, & `base7_binary_compatible_shift`: Any odd Base-7 shift $m + 7(2k+1)$ breaks `validParityWord` at step 1, whereas multiples of $7 \cdot 2^{|w|}$ preserve it.
- **Tracks R7-A & R7-B (Reset Control-Cycle Spectrum & Odd-Modulus Singleton Generalization)**:
  - `reset_six_state_cycle_certified`, `reset_five_state_cycle_certified`, & `reset_subsystem_cycle_spectrum`: Formal proof that the 7-state reset subsystem $\{A,L,M,N,O,P,Q\}$ has primitive simple cycles of lengths $1, 5, 6$ and **no simple 7-state cycle**.
  - `oddModulus_singleton_iff`: Universal theorem for all odd moduli $q = 2k+1$ proving $(3r+1) \bmod (2k+1) = r \bmod (2k+1) \iff r = k = (q-1)/2$ for all $r < 2k+1$, showing that the mod-7 singleton $r = 3$ is an instance of the general odd-modulus law.
- **Track A (Cycle Algebra & Conditional Well-Founded Potential Gate)**:
  - `parityWord_cycle_equation`, `no_cycle_when_wordA_ge_wordD`, `contracting_cycle_gap_eq`, `contracting_cycle_unique`, `contracting_cycle_eq_quotient`, `no_cycle_when_gap_not_dvd_B`, `no_cycle_when_quotient_invalid`, `no_nontrivial_cycle_when_quotient_le_one`, and `wellFounded_potential_forces_reset`.
- **Collatz Convergence Program: Gates C1–C5**:
  - **Gate C1 (Symbolic Parity-Word Classification)**: `applyParityWord_parityWordOf`, `iterateAccelerated_exact_affine`, and `applyParityWord_on_residue_class` (coupled with `validParityWord_iff_mod_eq_wordResidue`, `parityWordOf_wordResidue`, and `wordResidue_parityWordOf`).
  - **Gate C2 (Arbitrary-Period Cycle Obstructions)**: `wordB_eq_zero_iff_wordA_eq_one`, `cycle_pos_forces_wordB_pos`, `cycle_pos_forces_contracting` (every cycle of a positive integer along any non-empty parity word satisfies $2^{|w|} > 3^{\operatorname{ones}(w)}$), and `no_single_odd_cycle_above_one` (arbitrary-period exclusion of 1-circuit cycles `true :: replicate k false` for all $k \in \mathbb{N}$ and all $m > 1$).
  - **Gate C3 (Cylinder Descent Thresholds & Asymptotic Contraction)**: `contracting_word_descent_iff` ($F_w(m) < m \iff (2^r - 3^a) m > B(w)$) and `contracting_word_asymptotic_descent` (every contracting parity cylinder strictly decreases all $m = \operatorname{wordResidue}(w) + q \cdot 2^r$ with $q > B(w)$).
  - **Gates C4 & C5 (Universal Descent Equivalences & Residue Frontier Reduction)**: `universalCollatzDescent_iff_collatz`, `universalAcceleratedDescent_iff_collatz`, unconditional descent theorems (`collatz_descent_even`, `collatz_descent_mod4_eq1`, `collatz_descent_mod16_eq3`, `collatz_descent_mod32_eq11`, `collatz_descent_mod32_eq23`), and `collatz_iff_mod32_frontier_descent` (reducing `CollatzConjecture` to descent on the unresolved residue classes modulo 32).
  - **COLLATZ-C6 (Adaptive Residue Descent & Tree Well-Foundedness Analysis)**:
    - `collatz_descent_mod32_eq19` & `collatz_iff_mod32_four_class_frontier`: Discharges $19 \pmod{32}$ (since $19 \equiv 3 \pmod{16}$ descends in 6 steps and also in 8 steps) and reduces the modulo-32 frontier from 5 classes to the **4 spectrally expanding classes** $\{7, 15, 27, 31\} \pmod{32}$.
    - `cylinderCert` & `cylinderCert_sound`: Universal decidable cylinder descent certificate and soundness proof for arbitrary depth $r$ and residue $r_0 \bmod 2^r$.
    - `dischargedByDepth8_sound`, `adaptive_refinement_catalog_certified`, `mod256_partition_certified`, & `collatz_iff_mod256_frontier_descent`: Refines the 4-class modulo-32 frontier across moduli 64, 128 (discharging $\{7, 15, 59\} \pmod{128}$), and 256 (discharging $\{39, 79, 95, 123, 175, 199, 219\} \pmod{256}$), certifying unconditional descent for **237 of 256 residue classes ($92.58\%$)** and reducing `CollatzConjecture` to the **19-class expanding frontier modulo 256**.
    - `expanding_word_strict_growth`, `allTrueWord_never_descends_at_depth`, `staircase_no_discharge_when_wordA_gt_two_wordD`, `validParityWord_allTrueWord_div`, `validParityWord_allTrueWord_ge`, & `every_nat_exits_allTrue_branch`: Proves that while the 2-adic residue tree is not well-founded (the rightmost path `allTrueWord r` expands at every depth $r \ge 1$ and converges 2-adically to $-1 \in \mathbb{Z}_2$), every positive integer $n \in \mathbb{N}$ along `allTrueWord r` satisfies $2^r \mid (n + 1)$ and therefore **exits the infinite all-odd branch in at most $n$ steps**.
  - **COLLATZ-C7 (Odd-to-Odd Return-Map Qualification & Cross-Branch Dynamics)**:
    - **C7.1 (Exact Return-Map Composition)**: `validParityWord_append`, `applyParityWord_append`, `wordA_append`, `wordD_append`, `wordB_append` (exact affine cocycle $\operatorname{wordB}(w_1 \mathbin{++} w_2) = A(w_2)B(w_1) + D(w_1)B(w_2)$), `returnMapWord`, and `returnMap_exact_affine` ($2^{K_r} T^r(n) = 3^r n + B_r$).
    - **C7.2 (Arithmetic Constraints on Valuation Sequences)**: `returnMapWord_admissible_iff`, `returnMapWord_input_odd`, `wordB_allTrueWord_add_wordD` ($B_r = 3^r - 2^r$), `applyParityWord_allTrueWord_base`, `applyParityWord_allTrueWord_exact`, and `no_nat_realizes_replicate_zero_self`.
    - **C7.3 (Cross-Branch Compensation)**: `cross_branch_descent_iff` ($F_{w_2}(F_{w_1}(n)) < n \iff (D_1 D_2 - A_1 A_2)n > A_2 B_1 + D_1 B_2$).
    - **C7.4 & Section 5 (Minimal-Crossing Structure & Infinite-Path Obstruction)**: `minimal_crossing_terminal_step_even` and `eventuallyHitsContractingCylinder_iff_collatz` ($\operatorname{CollatzConjecture} \iff \forall n > 1, \operatorname{EventuallyHitsContractingCylinder}(n)$).
