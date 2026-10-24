import CollatzProofClosure.Definitions
import CollatzProofClosure.SpectralCrossing

namespace BBB17
namespace CollatzProofClosure

/-! # COLLATZ-C10 Workstream 3 (Gate G4): Global Descent, Non-Descent Diophantine
    Sandwich & Geometric Reservoir Drawdown

    1. **Global Non-Descent Multiplicative & Offset Sandwich (`nondescent_prefix_power_bound`,
       `nondescent_diophantine_sandwich`)**:
       For ANY trajectory of `n > 0` that has not descended below `n` prior to step `r`
       (`∀ i < r, iterateAccelerated n i ≥ n`), even across arbitrarily many spectral crossings:
       `2^r * n^{a_r} * iterateAccelerated n r ≤ n * (3 * n + 1)^{a_r}`.
       Consequently, if `∀ i ≤ r, iterateAccelerated n i ≥ n`, then at EVERY depth `r`:
       `(2^r - 3^{a_r}) * n ≤ wordB w_r` AND `2^r * n^{a_r} ≤ (3 * n + 1)^{a_r}` AND
       `n^{a_r} * (3^{a_r} * n + wordB w_r) ≤ n * (3 * n + 1)^{a_r}`.
    2. **Universal Offset-Free Descent Criterion (`power_threshold_forces_descent`,
       `eventual_power_threshold_implies_collatz`)**:
       Whenever `2^r * n^{a_r} > (3 * n + 1)^{a_r}` holds at ANY depth `r ≥ 1`, the trajectory
       of `n` MUST have strictly descended below `n` at some step `1 ≤ i ≤ r`.
    3. **Geometric Peak Drawdown Theorem (`every_nat_experiences_peak_drawdown`)**:
       No positive integer `n > 0` can maintain a monotonically non-decreasing trajectory
       (`u_{i+1} ≥ u_i`, i.e. zero reservoir drawdown `v_i = 0`) for `n + 1` steps: every
       integer `n > 0` experiences strict local descent `iterateAccelerated n (i + 1) < iterateAccelerated n i`
       at some step `i ≤ n`.
    4. **Multi-Segment Concatenated Recovery (`two_segment_recovery_after_jump_iff`)** and
       **Formal Potential Falsifications**.
-/

/-- Single-step evolution of `iterateAccelerated`:
    `iterateAccelerated n (r + 1) = acceleratedCollatz (iterateAccelerated n r)`. -/
theorem iterateAccelerated_succ_right (n r : Nat) :
    iterateAccelerated n (r + 1) = acceleratedCollatz (iterateAccelerated n r) := by
  have h1 := applyParityWord_parityWordOf (r + 1) n
  have h2 := parityWordOf_succ_eq_append r n
  rw [h2, applyParityWord_append, applyParityWord_parityWordOf] at h1
  dsimp [applyParityWord] at h1
  exact h1.symm

/-- `iterateAccelerated` preserves positivity (`n > 0 → iterateAccelerated n r > 0`). -/
theorem iterateAccelerated_pos (n r : Nat) (hn : n > 0) :
    iterateAccelerated n r > 0 := by
  induction r with
  | zero => exact hn
  | succ r ih =>
    rw [iterateAccelerated_succ_right]
    unfold acceleratedCollatz
    by_cases hev : iterateAccelerated n r % 2 = 0
    · rw [if_pos hev]; omega
    · rw [if_neg hev]; omega

/-- Universal Non-Descent Multiplicative Power Bound (`nondescent_prefix_power_bound`):
    For ANY integer `n` and depth `r`, if `iterateAccelerated n i ≥ n` for all `0 ≤ i < r`
    (requiring NO spectral assumption `2^i ≤ 3^{a_i}`), then:
    `2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r ≤ n * (3 * n + 1) ^ wordOnes (parityWordOf r n)`. -/
theorem nondescent_prefix_power_bound (n r : Nat)
    (hge : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n) :
    2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r ≤
      n * (3 * n + 1) ^ wordOnes (parityWordOf r n) := by
  induction r with
  | zero =>
    dsimp [parityWordOf, wordOnes, iterateAccelerated]
    omega
  | succ r ih =>
    have hge_r : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n :=
      fun i hi => hge i (by omega)
    have h_ih := ih hge_r
    have hn_r : iterateAccelerated n r ≥ n := hge r (by omega)
    have hsucc_w := parityWordOf_succ_eq_append r n
    have hsucc_it := iterateAccelerated_succ_right n r
    rw [hsucc_w, wordOnes_append, hsucc_it]
    by_cases hev : iterateAccelerated n r % 2 = 0
    · have hb_false : (iterateAccelerated n r % 2 == 1) = false := by
        rw [beq_eq_false_iff_ne]; omega
      rw [hb_false]
      dsimp [wordOnes]
      have hstep : 2 * acceleratedCollatz (iterateAccelerated n r) = iterateAccelerated n r := by
        have hm : stepParityMatches (iterateAccelerated n r) false := hev
        have hs := acceleratedCollatz_step_eq (iterateAccelerated n r) false hm
        simpa using hs
      have hpow : 2 ^ (r + 1) * n ^ wordOnes (parityWordOf r n) *
          acceleratedCollatz (iterateAccelerated n r) =
          2 ^ r * n ^ wordOnes (parityWordOf r n) *
            (2 * acceleratedCollatz (iterateAccelerated n r)) := by
        rw [Nat.pow_succ, Nat.mul_assoc (2 ^ r) 2 _,
          Nat.mul_comm 2 (n ^ wordOnes (parityWordOf r n)),
          ← Nat.mul_assoc (2 ^ r) _ 2, Nat.mul_assoc]
      rw [hpow, hstep]
      exact h_ih
    · have hb_true : (iterateAccelerated n r % 2 == 1) = true := by
        rw [beq_iff_eq]; omega
      rw [hb_true]
      dsimp [wordOnes]
      have hstep : 2 * acceleratedCollatz (iterateAccelerated n r) =
          3 * iterateAccelerated n r + 1 := by
        have hm : stepParityMatches (iterateAccelerated n r) true := by
          dsimp [stepParityMatches]; omega
        have hs := acceleratedCollatz_step_eq (iterateAccelerated n r) true hm
        simpa using hs
      have hstep_ineq : n * (2 * acceleratedCollatz (iterateAccelerated n r)) ≤
          iterateAccelerated n r * (3 * n + 1) := by
        rw [hstep, Nat.mul_add, Nat.mul_one, Nat.mul_add, Nat.mul_one]
        have hcomm : n * (3 * iterateAccelerated n r) =
            iterateAccelerated n r * (3 * n) := by
          rw [Nat.mul_comm n (3 * iterateAccelerated n r),
            Nat.mul_comm 3 (iterateAccelerated n r),
            Nat.mul_assoc (iterateAccelerated n r) 3 n]
        omega
      have hlhs_eq : 2 ^ (r + 1) * n ^ (wordOnes (parityWordOf r n) + 1) *
          acceleratedCollatz (iterateAccelerated n r) =
          (2 ^ r * n ^ wordOnes (parityWordOf r n)) *
            (n * (2 * acceleratedCollatz (iterateAccelerated n r))) := by
        rw [Nat.pow_succ 2 r, Nat.pow_succ n (wordOnes (parityWordOf r n))]
        have h1 : 2 ^ r * 2 * (n ^ wordOnes (parityWordOf r n) * n) *
            acceleratedCollatz (iterateAccelerated n r) =
            2 ^ r * n ^ wordOnes (parityWordOf r n) *
              (2 * n * acceleratedCollatz (iterateAccelerated n r)) := by
          rw [Nat.mul_assoc (2 ^ r) 2 _,
            ← Nat.mul_assoc 2 (n ^ wordOnes (parityWordOf r n)) n,
            Nat.mul_comm 2 (n ^ wordOnes (parityWordOf r n)),
            Nat.mul_assoc (n ^ wordOnes (parityWordOf r n)) 2 n,
            ← Nat.mul_assoc (2 ^ r) (n ^ wordOnes (parityWordOf r n)) (2 * n),
            Nat.mul_assoc]
        have h2 : 2 * n * acceleratedCollatz (iterateAccelerated n r) =
            n * (2 * acceleratedCollatz (iterateAccelerated n r)) := by
          rw [Nat.mul_comm 2 n, Nat.mul_assoc]
        rw [h1, h2]
      have hmul1 : (2 ^ r * n ^ wordOnes (parityWordOf r n)) *
          (n * (2 * acceleratedCollatz (iterateAccelerated n r))) ≤
          (2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r) * (3 * n + 1) := by
        rw [Nat.mul_assoc (2 ^ r * n ^ wordOnes (parityWordOf r n)) (iterateAccelerated n r) (3 * n + 1)]
        exact Nat.mul_le_mul_left (2 ^ r * n ^ wordOnes (parityWordOf r n)) hstep_ineq
      have hmul2 : (2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r) * (3 * n + 1) ≤
          (n * (3 * n + 1) ^ wordOnes (parityWordOf r n)) * (3 * n + 1) :=
        Nat.mul_le_mul_right (3 * n + 1) h_ih
      rw [hlhs_eq, Nat.pow_succ (3 * n + 1) (wordOnes (parityWordOf r n)),
        ← Nat.mul_assoc n _ (3 * n + 1)]
      exact Nat.le_trans hmul1 hmul2

/-- Two-Sided Non-Descent Diophantine Sandwich (`nondescent_diophantine_sandwich`):
    Suppose `n > 0` does not descend during its first `r` accelerated steps
    (`∀ i ≤ r, iterateAccelerated n i ≥ n`). Let `w_r = parityWordOf r n` and `a_r = wordOnes w_r`.
    Then simultaneously:
    1. `(2^r - 3^{a_r}) * n ≤ wordB w_r` (exact lower bound on `B_r`),
    2. `n^{a_r} * (3^{a_r} * n + wordB w_r) ≤ n * (3 * n + 1)^{a_r}` (global upper bound on `B_r`), and
    3. `2^r * n^{a_r} ≤ (3 * n + 1)^{a_r}` (offset-free spectral ratio bound). -/
theorem nondescent_diophantine_sandwich (n r : Nat) (hn : n > 0)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let w := parityWordOf r n
    let a := wordOnes w
    (2 ^ r - 3 ^ a) * n ≤ wordB w ∧
    n ^ a * (3 ^ a * n + wordB w) ≤ n * (3 * n + 1) ^ a ∧
    2 ^ r * n ^ a ≤ (3 * n + 1) ^ a := by
  dsimp
  have hpow_bound := nondescent_prefix_power_bound n r (fun i hi => hge i (by omega))
  have hn_r : iterateAccelerated n r ≥ n := hge r (by omega)
  have haff := iterateAccelerated_exact_affine r n
  have hD_pow : wordD (parityWordOf r n) = 2 ^ r := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hA_pow : wordA (parityWordOf r n) = 3 ^ wordOnes (parityWordOf r n) :=
    wordA_eq_pow_three_wordOnes (parityWordOf r n)
  rw [hD_pow, hA_pow] at haff
  have hlower : (2 ^ r - 3 ^ wordOnes (parityWordOf r n)) * n ≤ wordB (parityWordOf r n) := by
    by_cases hgt : 2 ^ r ≥ 3 ^ wordOnes (parityWordOf r n)
    · have hsub : (2 ^ r - 3 ^ wordOnes (parityWordOf r n)) * n +
          3 ^ wordOnes (parityWordOf r n) * n = 2 ^ r * n := by
        rw [← Nat.add_mul, Nat.sub_add_cancel hgt]
      have hmul : 2 ^ r * n ≤ 2 ^ r * iterateAccelerated n r :=
        Nat.mul_le_mul_left (2 ^ r) hn_r
      omega
    · have hzero : 2 ^ r - 3 ^ wordOnes (parityWordOf r n) = 0 := by omega
      rw [hzero, Nat.zero_mul]
      omega
  have hupper : n ^ wordOnes (parityWordOf r n) *
      (3 ^ wordOnes (parityWordOf r n) * n + wordB (parityWordOf r n)) ≤
      n * (3 * n + 1) ^ wordOnes (parityWordOf r n) := by
    rw [← haff]
    have hcomm : n ^ wordOnes (parityWordOf r n) * (2 ^ r * iterateAccelerated n r) =
        2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r := by
      rw [← Nat.mul_assoc, Nat.mul_comm (n ^ wordOnes (parityWordOf r n)) (2 ^ r)]
    rw [hcomm]
    exact hpow_bound
  have hratio : 2 ^ r * n ^ wordOnes (parityWordOf r n) ≤
      (3 * n + 1) ^ wordOnes (parityWordOf r n) := by
    have hmul_n : (2 ^ r * n ^ wordOnes (parityWordOf r n)) * n ≤
        2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r :=
      Nat.mul_le_mul_left (2 ^ r * n ^ wordOnes (parityWordOf r n)) hn_r
    have hle_rhs : (2 ^ r * n ^ wordOnes (parityWordOf r n)) * n ≤
        (3 * n + 1) ^ wordOnes (parityWordOf r n) * n := by
      rw [Nat.mul_comm ((3 * n + 1) ^ wordOnes (parityWordOf r n)) n]
      exact Nat.le_trans hmul_n hpow_bound
    exact Nat.le_of_mul_le_mul_right hle_rhs hn
  exact ⟨hlower, hupper, hratio⟩

/-- Offset-Free Power-Threshold Descent Theorem (`power_threshold_forces_descent`):
    For ANY integer `n > 0` and depth `r ≥ 1`, if at depth `r` the parity word
    `w_r = parityWordOf r n` with `a_r = wordOnes w_r` satisfies
    `2 ^ r * n ^ a_r > (3 * n + 1) ^ a_r`,
    then `n` MUST strictly descend below `n` at some step `1 ≤ i ≤ r`. -/
theorem power_threshold_forces_descent (n r : Nat) (hn : n > 0)
    (hthresh : 2 ^ r * n ^ wordOnes (parityWordOf r n) >
      (3 * n + 1) ^ wordOnes (parityWordOf r n)) :
    ∃ i : Nat, 1 ≤ i ∧ i ≤ r ∧ iterateAccelerated n i < n := by
  exact Classical.byContradiction fun hnot => by
    have hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n := by
      intro i hi
      by_cases hi0 : i = 0
      · rw [hi0]; dsimp [iterateAccelerated]; omega
      · by_cases hlt : iterateAccelerated n i < n
        · exact False.elim (hnot ⟨i, by omega, hi, hlt⟩)
        · omega
    have hratio := (nondescent_diophantine_sandwich n r hn hge).2.2
    omega

/-- Global Offset-Free Sufficient Criterion for the Collatz Conjecture:
    If every integer `n > 1` eventually reaches a depth `r ≥ 1` where
    `2^r * n^{a_r} > (3n + 1)^{a_r}`, then `CollatzConjecture` holds unconditionally. -/
theorem eventual_power_threshold_implies_collatz
    (h : ∀ n : Nat, n > 1 → ∃ r : Nat, r ≥ 1 ∧
      2 ^ r * n ^ wordOnes (parityWordOf r n) >
        (3 * n + 1) ^ wordOnes (parityWordOf r n)) :
    CollatzConjecture := by
  apply universalAcceleratedDescent_iff_collatz.mp
  intro n hn1
  rcases h n hn1 with ⟨r, _, hthresh⟩
  rcases power_threshold_forces_descent n r (by omega) hthresh with ⟨i, hi1, _, hlt⟩
  exact ⟨i, by omega, hlt⟩

/-- Monotonically non-decreasing trajectories are trapped in `allTrueWord`:
    If `n > 0` satisfies `iterateAccelerated n (i + 1) ≥ iterateAccelerated n i` for all `i < r`,
    then `validParityWord n (allTrueWord r)` holds. -/
theorem monotone_nondecreasing_forces_allTrueWord (n r : Nat) (hn : n > 0) :
    (∀ i : Nat, i < r → iterateAccelerated n (i + 1) ≥ iterateAccelerated n i) →
    validParityWord n (allTrueWord r) := by
  induction r generalizing n with
  | zero =>
    intro _
    trivial
  | succ r ih =>
    intro hmono
    have h0 : iterateAccelerated n 1 ≥ n := hmono 0 (by omega)
    dsimp [iterateAccelerated] at h0
    have hodd : n % 2 = 1 := by
      by_cases hev : n % 2 = 0
      · unfold acceleratedCollatz at h0
        rw [if_pos hev] at h0
        omega
      · omega
    have hmono_next : ∀ i : Nat, i < r →
        iterateAccelerated (acceleratedCollatz n) (i + 1) ≥
          iterateAccelerated (acceleratedCollatz n) i := by
      intro i hi
      exact hmono (i + 1) (by omega)
    have hc_pos : acceleratedCollatz n > 0 := iterateAccelerated_pos n 1 hn
    dsimp [allTrueWord, List.replicate, validParityWord, stepParityMatches]
    exact ⟨hodd, ih (acceleratedCollatz n) hc_pos hmono_next⟩

/-- Geometric Peak Drawdown Theorem (`every_nat_experiences_peak_drawdown`):
    No positive integer `n > 0` can maintain a monotonically non-decreasing trajectory
    (`u_{i+1} ≥ u_i`, corresponding to zero reservoir drawdown `v_i = 0`) for `n + 1` steps:
    there always exists `i ≤ n` such that `iterateAccelerated n (i + 1) < iterateAccelerated n i`. -/
theorem every_nat_experiences_peak_drawdown (n : Nat) (hn : n > 0) :
    ∃ i : Nat, i ≤ n ∧ iterateAccelerated n (i + 1) < iterateAccelerated n i := by
  exact Classical.byContradiction fun hnot => by
    have hmono : ∀ i : Nat, i < n + 1 →
        iterateAccelerated n (i + 1) ≥ iterateAccelerated n i := by
      intro i hi
      by_cases hlt : iterateAccelerated n (i + 1) < iterateAccelerated n i
      · exact False.elim (hnot ⟨i, by omega, hlt⟩)
      · omega
    have hv := monotone_nondecreasing_forces_allTrueWord n (n + 1) hn hmono
    exact every_nat_exits_allTrue_branch n hv

/-- Exact Concatenated Affine Operator Identity (`D₁ D₂ F_{w₁ w₂}(n) = A₁ A₂ n + (A₂ B₁ + D₁ B₂)`). -/
theorem composite_operator_exact_affine (w₁ w₂ : List Bool) (n : Nat)
    (hv : validParityWord n (w₁ ++ w₂)) :
    (wordD w₁ * wordD w₂) * applyParityWord n (w₁ ++ w₂) =
      (wordA w₁ * wordA w₂) * n + (wordA w₂ * wordB w₁ + wordD w₁ * wordB w₂) := by
  have haff := parityWord_affine_identity (w₁ ++ w₂) n hv
  rw [wordD_append, wordA_append, wordB_append] at haff
  exact haff

/-- Exact Multi-Segment Recovery Theorem (`two_segment_recovery_after_jump_iff`):
    Suppose segment `w₁` fails to descend at `n` (`y₁ = applyParityWord n w₁ ≥ n`, with upward
    jump `k = y₁ - n`), and is followed by a contracting segment `w₂` (`wordD w₂ > wordA w₂`).
    Then the composite trajectory `w₁ ++ w₂` strictly descends below `n` if and only if
    the second segment's discrete deficit at `y₁` is at least `(k + 1) * wordD w₂`:
    `applyParityWord n (w₁ ++ w₂) < n ↔ wordDelta w₂ * y₁ ≥ wordB w₂ + (y₁ - n + 1) * wordD w₂`. -/
theorem two_segment_recovery_after_jump_iff (w₁ w₂ : List Bool) (n : Nat)
    (hv : validParityWord n (w₁ ++ w₂))
    (hjump : applyParityWord n w₁ ≥ n)
    (hgt₂ : wordD w₂ > wordA w₂) :
    let y₁ := applyParityWord n w₁
    let k  := y₁ - n
    applyParityWord n (w₁ ++ w₂) < n ↔
      wordDelta w₂ * y₁ ≥ wordB w₂ + (k + 1) * wordD w₂ := by
  dsimp
  have hv_split := (validParityWord_append w₁ w₂ n).mp hv
  have hv₂ : validParityWord (applyParityWord n w₁) w₂ := hv_split.2
  have happ := applyParityWord_append w₁ w₂ n
  have hbal₂ := discrete_deficit_balance w₂ (applyParityWord n w₁) hv₂ (by omega)
  have hD₂_pos : wordD w₂ > 0 := wordD_pos w₂
  rw [happ]
  constructor
  · intro hlt
    have hdiff_ge : applyParityWord n w₁ - applyParityWord (applyParityWord n w₁) w₂ ≥
        (applyParityWord n w₁ - n) + 1 := by omega
    have hle₂ : applyParityWord (applyParityWord n w₁) w₂ ≤ applyParityWord n w₁ := by omega
    have hid₂ := (discrete_deficit_descent_identity w₂ (applyParityWord n w₁) hv₂ (by omega) hle₂).1
    have hmul := Nat.mul_le_mul_left (wordD w₂) hdiff_ge
    have hcomm : wordD w₂ * ((applyParityWord n w₁ - n) + 1) =
        ((applyParityWord n w₁ - n) + 1) * wordD w₂ := Nat.mul_comm _ _
    omega
  · intro hdef
    by_cases hlt : applyParityWord (applyParityWord n w₁) w₂ < n
    · exact hlt
    · have hge_n : applyParityWord (applyParityWord n w₁) w₂ ≥ n := by omega
      have hmul : wordD w₂ * n ≤ wordD w₂ * applyParityWord (applyParityWord n w₁) w₂ :=
        Nat.mul_le_mul_left (wordD w₂) hge_n
      have hk_eq : (applyParityWord n w₁ - n + 1) * wordD w₂ =
          wordD w₂ * (applyParityWord n w₁ - n) + wordD w₂ := by
        rw [Nat.mul_comm, Nat.mul_add, Nat.mul_one]
      have hsub_mul : wordD w₂ * (applyParityWord n w₁ - n) + wordD w₂ * n =
          wordD w₂ * applyParityWord n w₁ := by
        rw [← Nat.mul_add, Nat.sub_add_cancel hjump]
      omega

/-- Equivalence of `UniversalCompositeDeficitPositive` and `CollatzConjecture`:
    Multi-segment contracting deficit positivity is both necessary and sufficient
    for universal Collatz convergence. -/
theorem universalCompositeDeficitPositive_iff_collatz :
    UniversalCompositeDeficitPositive ↔ CollatzConjecture := by
  rw [← universalAcceleratedDescent_iff_collatz]
  constructor
  · intro hcomp n hn1
    rcases hcomp n hn1 with ⟨w₁, w₂, hlen, hv, hgt, hdef⟩
    let w := w₁ ++ w₂
    have hquant := (discrete_deficit_quantization_iff w n hv hgt).2.1
    have hdesc : applyParityWord n w < n := hquant.mp hdef
    have hp_eq : parityWordOf w.length n = w :=
      (validParityWord_iff_eq_parityWordOf w n).mp hv
    have happ := applyParityWord_parityWordOf w.length n
    rw [hp_eq] at happ
    rw [happ] at hdesc
    exact ⟨w.length, hlen, hdesc⟩
  · intro hacc n hn1
    have hcol : CollatzConjecture := universalAcceleratedDescent_iff_collatz.mp hacc
    have hhit := (eventuallyHitsContractingCylinder_iff_collatz.mpr hcol) n hn1
    rcases hhit with ⟨r, hr_pos, hgt, hstrict⟩
    let w := parityWordOf r n
    have hv : validParityWord n w := parityWordOf_valid r n
    have hquant := (discrete_deficit_quantization_iff w n hv hgt).1
    have hlen : (w ++ []).length > 0 := by
      rw [List.append_nil, parityWordOf_length]
      exact hr_pos
    refine ⟨w, [], hlen, ?_, ?_, ?_⟩
    · rw [List.append_nil]; exact hv
    · rw [List.append_nil]; exact hgt
    · rw [List.append_nil]
      exact hquant.mp hstrict

/-- Formal Falsification of Monotone `v₂(n + 1)` Potential across Even Steps:
    While odd steps satisfy `acceleratedCollatz (2k + 1) + 1 = 3 * (k + 1)`, even steps can
    jump from an odd `n + 1` (`v₂(62 + 1) = 0`) to `acceleratedCollatz 62 + 1 = 32 = 2^5`. -/
theorem v2_succ_potential_even_step_jump_witness :
    (62 + 1) % 2 = 1 ∧
    acceleratedCollatz 62 + 1 = 2 ^ 5 := by
  decide

/-- Formal Falsification of Positive Linear `(u, v)` Potentials (`a * u + b * v`):
    For EVERY positive weight `a > 0` and reservoir weight `b : Nat`, the linear potential
    `P(u, v) = a * u + b * v` strictly increases on `(0, 2, 0) → (0, 4, 0)`. -/
theorem positive_linear_uv_potential_strict_increase (a b : Nat) (ha : a > 0) :
    let t₀ := (0, 2, 0)
    let t₁ := nextCanonicalTriple t₀.1 t₀.2.1 t₀.2.2
    a * t₁.2.1 + b * t₁.2.2 > a * t₀.2.1 + b * t₀.2.2 := by
  have ht₁ : nextCanonicalTriple 0 2 0 = (0, 4, 0) := by decide
  dsimp
  rw [ht₁]
  dsimp
  omega

end CollatzProofClosure
end BBB17
