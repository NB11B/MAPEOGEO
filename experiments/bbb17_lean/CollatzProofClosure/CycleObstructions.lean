import CollatzProofClosure.Definitions
import CollatzProofClosure.GlobalDescent

namespace BBB17
namespace CollatzProofClosure

/-! # COLLATZ-C10 Workstream 4 (Gate G4): General Cycle Obstructions

    1. **Arbitrary-Period 2-Odd and 3-Odd Block Cycle Exclusions
       (`no_two_odd_block_cycle`, `no_three_odd_block_cycle`)**:
       Proves for all `k : Nat` and `m > 0` that no cycle can exist along
       `true :: true :: replicate k false` or `true :: true :: true :: replicate k false`.
    2. **Universal 1-Circuit Steiner Cycle Obstruction (`oneCircuitWord_steiner_obstruction`)**:
       For every `a ≥ 1` and `k : Nat`, `wordB (oneCircuitWord a k) = 3^a - 2^a`, and any
       cycle element `m > 0` along `oneCircuitWord a k` must satisfy `m ≥ 2^a - 1` and
       `(2^{a+k} - 3^a) * (2^a - 1) ≤ 3^a - 2^a`.
    3. **Universal 3-Adic Cycle Exclusion (`cycle_element_mod_three_ne_zero`)**:
       No positive integer `m > 1` in any cycle of any period `r ≥ 1` is divisible by `3`.
    4. **Universal Eliahou Cycle Minimum-Element Bound (`universal_cycle_minimum_element_bound`)**:
       For the minimum element `n > 1` of ANY cycle of period `r ≥ 1` (arbitrary parity word `w`),
       `3^a < 2^r` and `2^r * n^a ≤ (3n + 1)^a`, and for any lower bound `n ≥ N₀ > 0`,
       `2^r * N₀^a ≤ (3 N₀ + 1)^a`.
    5. **Unconditional Length-64 Universal Cycle Exclusion (`no_nontrivial_cycle_length_le_64`)**:
       Certifies in Lean 4 that no non-trivial cycle of period `1 ≤ r ≤ 64` exists across all
       `2^64` parity words.
-/

/-- 2-odd-step block word `true :: true :: replicate k false` of arbitrary period `k + 2`. -/
def twoOddBlockWord (k : Nat) : List Bool :=
  true :: true :: List.replicate k false

theorem wordA_twoOddBlockWord (k : Nat) :
    wordA (twoOddBlockWord k) = 9 := by
  dsimp [twoOddBlockWord, wordA]
  rw [wordA_replicate_false]

theorem wordB_twoOddBlockWord (k : Nat) :
    wordB (twoOddBlockWord k) = 5 := by
  dsimp [twoOddBlockWord, wordB, wordA]
  rw [wordA_replicate_false, wordB_replicate_false]

/-- Arbitrary-Period 2-Odd-Step Cycle Exclusion (`no_two_odd_block_cycle`):
    For EVERY `k : Nat` (period `r = k + 2`) and EVERY `m > 0`, no positive integer `m`
    can form a cycle along `twoOddBlockWord k = true :: true :: replicate k false`. -/
theorem no_two_odd_block_cycle (k m : Nat) (hm : m > 0)
    (hv : validParityWord m (twoOddBlockWord k)) :
    applyParityWord m (twoOddBlockWord k) ≠ m := by
  intro hc
  have heq := parityWord_cycle_equation (twoOddBlockWord k) m hv hc
  rw [wordA_twoOddBlockWord, wordB_twoOddBlockWord] at heq
  have hD_eq : wordD (twoOddBlockWord k) = 4 * 2 ^ k := by
    dsimp [twoOddBlockWord, wordD]
    rw [wordD_eq_pow_two_length, List.length_replicate]
    omega
  rw [hD_eq] at heq
  cases k with
  | zero =>
    have hmul : (4 * 2 ^ 0) * m = 4 * m := rfl
    omega
  | succ k₁ =>
    cases k₁ with
    | zero =>
      have hmul : (4 * 2 ^ 1) * m = 8 * m := rfl
      omega
    | succ k₂ =>
      change (4 * 2 ^ (k₂ + 2)) * m = 9 * m + 5 at heq
      have hpow_ge : 2 ^ (k₂ + 2) ≥ 4 := by
        rw [Nat.pow_succ, Nat.pow_succ]
        have hp : 2 ^ k₂ ≥ 1 := Nat.one_le_pow k₂ 2 (by decide)
        omega
      have hD_ge16 : 4 * 2 ^ (k₂ + 2) ≥ 16 := by omega
      have hmul : (4 * 2 ^ (k₂ + 2)) * m ≥ 16 * m :=
        Nat.mul_le_mul_right m hD_ge16
      omega

/-- 3-odd-step block word `true :: true :: true :: replicate k false` of arbitrary period `k + 3`. -/
def threeOddBlockWord (k : Nat) : List Bool :=
  true :: true :: true :: List.replicate k false

theorem wordA_threeOddBlockWord (k : Nat) :
    wordA (threeOddBlockWord k) = 27 := by
  dsimp [threeOddBlockWord, wordA]
  rw [wordA_replicate_false]

theorem wordB_threeOddBlockWord (k : Nat) :
    wordB (threeOddBlockWord k) = 19 := by
  dsimp [threeOddBlockWord, wordB, wordA]
  rw [wordA_replicate_false, wordB_replicate_false]

/-- Arbitrary-Period 3-Odd-Step Cycle Exclusion (`no_three_odd_block_cycle`):
    For EVERY `k : Nat` (period `r = k + 3`) and EVERY `m > 0`, no positive integer `m`
    can form a cycle along `threeOddBlockWord k = true :: true :: true :: replicate k false`. -/
theorem no_three_odd_block_cycle (k m : Nat) (hm : m > 0)
    (hv : validParityWord m (threeOddBlockWord k)) :
    applyParityWord m (threeOddBlockWord k) ≠ m := by
  intro hc
  have heq := parityWord_cycle_equation (threeOddBlockWord k) m hv hc
  rw [wordA_threeOddBlockWord, wordB_threeOddBlockWord] at heq
  have hD_eq : wordD (threeOddBlockWord k) = 8 * 2 ^ k := by
    dsimp [threeOddBlockWord, wordD]
    rw [wordD_eq_pow_two_length, List.length_replicate]
    omega
  rw [hD_eq] at heq
  cases k with
  | zero =>
    have hmul : (8 * 2 ^ 0) * m = 8 * m := rfl
    omega
  | succ k₁ =>
    cases k₁ with
    | zero =>
      have hmul : (8 * 2 ^ 1) * m = 16 * m := rfl
      omega
    | succ k₂ =>
      cases k₂ with
      | zero =>
        have hmul : (8 * 2 ^ 2) * m = 32 * m := rfl
        omega
      | succ k₃ =>
        change (8 * 2 ^ (k₃ + 3)) * m = 27 * m + 19 at heq
        have hpow_ge : 2 ^ (k₃ + 3) ≥ 8 := by
          rw [Nat.pow_succ, Nat.pow_succ, Nat.pow_succ]
          have hp : 2 ^ k₃ ≥ 1 := Nat.one_le_pow k₃ 2 (by decide)
          omega
        have hD_ge64 : 8 * 2 ^ (k₃ + 3) ≥ 64 := by omega
        have hmul : (8 * 2 ^ (k₃ + 3)) * m ≥ 64 * m :=
          Nat.mul_le_mul_right m hD_ge64
        omega

theorem wordA_allTrueWord_eq (a : Nat) :
    wordA (allTrueWord a) = 3 ^ a := by
  induction a with
  | zero => rfl
  | succ a ih =>
    dsimp [allTrueWord, List.replicate, wordA] at ih ⊢
    rw [ih, Nat.pow_succ]
    omega

theorem wordD_allTrueWord_eq (a : Nat) :
    wordD (allTrueWord a) = 2 ^ a := by
  rw [wordD_eq_pow_two_length]
  dsimp [allTrueWord]
  rw [List.length_replicate]

/-- Exact coefficients of the 1-circuit parity word `oneCircuitWord a k = allTrueWord a ++ replicate k false`:
    `wordA = 3^a`, `wordD = 2^{a+k}`, and `wordB = 3^a - 2^a`. -/
theorem oneCircuitWord_coefficients (a k : Nat) :
    wordA (oneCircuitWord a k) = 3 ^ a ∧
    wordD (oneCircuitWord a k) = 2 ^ (a + k) ∧
    wordB (oneCircuitWord a k) + 2 ^ a = 3 ^ a := by
  unfold oneCircuitWord
  rw [wordA_append, wordD_append, wordB_append,
    wordA_replicate_false, wordB_replicate_false]
  have hA : wordA (allTrueWord a) = 3 ^ a := wordA_allTrueWord_eq a
  have hD : wordD (allTrueWord a) = 2 ^ a := wordD_allTrueWord_eq a
  have hB := wordB_allTrueWord_add_wordD a
  have hDk : wordD (List.replicate k false) = 2 ^ k := by
    rw [wordD_eq_pow_two_length, List.length_replicate]
  rw [hA, hD, hDk, Nat.mul_one, Nat.one_mul, Nat.mul_zero, Nat.add_zero]
  rw [hA, hD] at hB
  exact ⟨rfl, (Nat.pow_add 2 a k).symm, hB⟩

/-- Universal 1-Circuit Steiner Cycle Obstruction (`oneCircuitWord_steiner_obstruction`):
    For ANY `a ≥ 1`, `k : Nat`, and `m > 0`, if `m` forms a cycle along
    `oneCircuitWord a k = allTrueWord a ++ replicate k false`, then simultaneously:
    1. `2 ^ (a + k) > 3 ^ a`,
    2. `m + 1 ≥ 2 ^ a` (`m ≥ 2^a - 1`),
    3. `(2 ^ (a + k) - 3 ^ a) * m = 3 ^ a - 2 ^ a`, and
    4. `(2 ^ (a + k) - 3 ^ a) * (2 ^ a - 1) ≤ 3 ^ a - 2 ^ a`. -/
theorem oneCircuitWord_steiner_obstruction (a k m : Nat)
    (ha : a ≥ 1) (hm : m > 0)
    (hv : validParityWord m (oneCircuitWord a k))
    (hc : applyParityWord m (oneCircuitWord a k) = m) :
    2 ^ (a + k) > 3 ^ a ∧
    m + 1 ≥ 2 ^ a ∧
    (2 ^ (a + k) - 3 ^ a) * m = 3 ^ a - 2 ^ a ∧
    (2 ^ (a + k) - 3 ^ a) * (2 ^ a - 1) ≤ 3 ^ a - 2 ^ a := by
  rcases oneCircuitWord_coefficients a k with ⟨hA, hD, hB⟩
  have hne : oneCircuitWord a k ≠ [] := by
    unfold oneCircuitWord allTrueWord
    cases a with
    | zero => omega
    | succ a' => simp [List.replicate]
  have hcont := cycle_pos_forces_contracting (oneCircuitWord a k) m hne hm hv hc
  rw [hD, hA] at hcont
  have hv_allTrue : validParityWord m (allTrueWord a) :=
    ((validParityWord_append (allTrueWord a) (List.replicate k false) m).mp hv).1
  have hm_ge : m + 1 ≥ 2 ^ a := by
    have hge := validParityWord_allTrueWord_ge a m hv_allTrue
    rw [wordD_allTrueWord_eq] at hge
    exact hge
  have hle_AD : wordA (oneCircuitWord a k) ≤ wordD (oneCircuitWord a k) := by
    rw [hD, hA]; omega
  have hgap := contracting_cycle_gap_eq (oneCircuitWord a k) m hv hle_AD hc
  rw [hD, hA] at hgap
  have hB_eq : wordB (oneCircuitWord a k) = 3 ^ a - 2 ^ a := by omega
  rw [hB_eq] at hgap
  have hm_ge' : m ≥ 2 ^ a - 1 := by omega
  have hmul : (2 ^ (a + k) - 3 ^ a) * (2 ^ a - 1) ≤ (2 ^ (a + k) - 3 ^ a) * m :=
    Nat.mul_le_mul_left (2 ^ (a + k) - 3 ^ a) hm_ge'
  exact ⟨hcont, hm_ge, hgap, by omega⟩

/-- Universal 3-Adic Cycle Exclusion (`cycle_element_mod_three_ne_zero`):
    No integer `m > 1` belonging to any positive cycle of any parity word `w` (`w ≠ []`)
    can be divisible by `3` (`m % 3 ≠ 0`). -/
theorem cycle_element_mod_three_ne_zero (w : List Bool) (m : Nat)
    (hne : w ≠ []) (hm : m > 1)
    (hv : validParityWord m w) (hc : applyParityWord m w = m) :
    m % 3 ≠ 0 := by
  have hB_pos : wordB w > 0 := cycle_pos_forces_wordB_pos w m hne (by omega) hv hc
  have hones_ge1 : wordOnes w ≥ 1 := by
    by_cases h0 : wordOnes w = 0
    · have hA1 : wordA w = 1 := by rw [wordA_eq_pow_three_wordOnes, h0]
      have hB0 : wordB w = 0 := (wordB_eq_zero_iff_wordA_eq_one w).mpr hA1
      omega
    · omega
  have hmod3 := applyParityWord_mod_three_ne_zero w m hv hones_ge1
  rw [hc] at hmod3
  exact hmod3

/-- Helper lemma: `(x * y) ^ k = x ^ k * y ^ k`. -/
theorem mul_pow_eq (x y k : Nat) : (x * y) ^ k = x ^ k * y ^ k := by
  induction k with
  | zero => rfl
  | succ k ih =>
    rw [Nat.pow_succ, Nat.pow_succ, Nat.pow_succ, ih]
    have h1 : x ^ k * y ^ k * (x * y) = x ^ k * (y ^ k * (x * y)) :=
      Nat.mul_assoc _ _ _
    have h2 : y ^ k * (x * y) = x * (y ^ k * y) := by
      rw [← Nat.mul_assoc, Nat.mul_comm (y ^ k) x, Nat.mul_assoc]
    rw [h1, h2, ← Nat.mul_assoc]

/-- Helper lemma: `x ≤ y → x ^ k ≤ y ^ k`. -/
theorem pow_le_pow_of_le (x y k : Nat) (h : x ≤ y) : x ^ k ≤ y ^ k := by
  induction k with
  | zero => exact Nat.le_refl 1
  | succ k ih =>
    rw [Nat.pow_succ, Nat.pow_succ]
    exact Nat.mul_le_mul ih h

/-- Helper lemma: `x > 0 → x ^ k > 0`. -/
theorem pow_pos_of_pos (x k : Nat) (hx : x > 0) : x ^ k > 0 := by
  induction k with
  | zero => exact Nat.zero_lt_one
  | succ k ih =>
    rw [Nat.pow_succ]
    exact Nat.mul_pos ih hx

/-- Universal Eliahou Cycle Minimum-Element Bound (`universal_cycle_minimum_element_bound`):
    Suppose `n > 1` is the minimum element of a cycle of period `r ≥ 1`
    (`∀ i ≤ r, iterateAccelerated n i ≥ n` and `iterateAccelerated n r = n`).
    Let `a = wordOnes (parityWordOf r n)`. Then for every lower bound `N₀` with `0 < N₀ ≤ n`:
    `1 ≤ a ∧ 3 ^ a < 2 ^ r ∧ 2 ^ r * n ^ a ≤ (3 * n + 1) ^ a ∧ 2 ^ r * N₀ ^ a ≤ (3 * N₀ + 1) ^ a`. -/
theorem universal_cycle_minimum_element_bound (n r N₀ : Nat)
    (hn1 : n > 1) (hr : r ≥ 1) (_hN₀_pos : N₀ > 0) (hN₀_le : N₀ ≤ n)
    (hmin : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n)
    (hcycle : iterateAccelerated n r = n) :
    let a := wordOnes (parityWordOf r n)
    1 ≤ a ∧
    3 ^ a < 2 ^ r ∧
    2 ^ r * n ^ a ≤ (3 * n + 1) ^ a ∧
    2 ^ r * N₀ ^ a ≤ (3 * N₀ + 1) ^ a := by
  dsimp
  let w := parityWordOf r n
  let a := wordOnes w
  have hne : w ≠ [] := by
    have hlen : w.length = r := parityWordOf_length r n
    intro hnil
    rw [hnil] at hlen
    dsimp at hlen
    omega
  have hv : validParityWord n w := parityWordOf_valid r n
  have hc_w : applyParityWord n w = n := by
    rw [applyParityWord_parityWordOf]
    exact hcycle
  have hcont := cycle_pos_forces_contracting w n hne (by omega) hv hc_w
  have hD_pow : wordD w = 2 ^ r := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hA_pow : wordA w = 3 ^ a := wordA_eq_pow_three_wordOnes w
  rw [hD_pow, hA_pow] at hcont
  have hB_pos : wordB w > 0 := cycle_pos_forces_wordB_pos w n hne (by omega) hv hc_w
  have ha_ge1 : 1 ≤ a := by
    by_cases ha0 : a = 0
    · have hA1 : wordA w = 1 := by rw [hA_pow, ha0]
      have hB0 : wordB w = 0 := (wordB_eq_zero_iff_wordA_eq_one w).mpr hA1
      omega
    · omega
  have hratio := (nondescent_diophantine_sandwich n r (by omega) hmin).2.2
  have hstep_N₀ : N₀ * (3 * n + 1) ≤ (3 * N₀ + 1) * n := by
    rw [Nat.mul_add, Nat.mul_one, Nat.add_mul, Nat.one_mul]
    have hcomm : N₀ * (3 * n) = 3 * N₀ * n := by
      rw [← Nat.mul_assoc, Nat.mul_comm N₀ 3, Nat.mul_assoc]
    omega
  have hpow_N₀ : N₀ ^ a * (3 * n + 1) ^ a ≤ (3 * N₀ + 1) ^ a * n ^ a := by
    rw [← mul_pow_eq N₀ (3 * n + 1) a, ← mul_pow_eq (3 * N₀ + 1) n a]
    exact pow_le_pow_of_le (N₀ * (3 * n + 1)) ((3 * N₀ + 1) * n) a hstep_N₀
  have hmul_lhs : (2 ^ r * N₀ ^ a) * n ^ a ≤ N₀ ^ a * (3 * n + 1) ^ a := by
    have hcomm : (2 ^ r * N₀ ^ a) * n ^ a = N₀ ^ a * (2 ^ r * n ^ a) := by
      rw [Nat.mul_comm (2 ^ r) (N₀ ^ a), Nat.mul_assoc]
    rw [hcomm]
    exact Nat.mul_le_mul_left (N₀ ^ a) hratio
  have hle_na : (2 ^ r * N₀ ^ a) * n ^ a ≤ (3 * N₀ + 1) ^ a * n ^ a :=
    Nat.le_trans hmul_lhs hpow_N₀
  have hna_pos : n ^ a > 0 := pow_pos_of_pos n a (by omega)
  have hratio_N₀ : 2 ^ r * N₀ ^ a ≤ (3 * N₀ + 1) ^ a :=
    Nat.le_of_mul_le_mul_right hle_na hna_pos
  exact ⟨ha_ge1, hcont, hratio, hratio_N₀⟩

/-- Boolean verifier that no `(r, a)` in `1 ≤ r ≤ maxR, 1 ≤ a ≤ r` satisfies both
    `3^a < 2^r` and `2^r * 1024^a ≤ 3073^a`. -/
def checkEliahouWindow1024 (maxR : Nat) : Bool :=
  (List.range (maxR + 1)).all fun r =>
    (List.range (r + 1)).all fun a =>
      !(decide (1 ≤ r ∧ 1 ≤ a ∧ 3 ^ a < 2 ^ r ∧ 2 ^ r * 1024 ^ a ≤ 3073 ^ a))

set_option maxRecDepth 200000

/-- Kernel-certified verification that the Eliahou cycle window for `N₀ = 1024`
    is completely empty across all periods `1 ≤ r ≤ 64`. -/
theorem checkEliahouWindow1024_64 :
    checkEliahouWindow1024 64 = true := by
  decide

/-- Tail-recursive bounded descent finder: checks if `m` reaches `< m₀` within `fuel` steps. -/
def reachesBelowWithin : Nat → Nat → Nat → Bool
  | 0, _, _ => false
  | fuel + 1, m₀, curr =>
    let next := acceleratedCollatz curr
    if next < m₀ then true else reachesBelowWithin fuel m₀ next

theorem reachesBelowWithin_sound (fuel m₀ curr : Nat)
    (h : reachesBelowWithin fuel m₀ curr = true) :
    ∃ k : Nat, 1 ≤ k ∧ k ≤ fuel ∧ iterateAccelerated curr k < m₀ := by
  induction fuel generalizing curr with
  | zero => contradiction
  | succ fuel ih =>
    unfold reachesBelowWithin at h
    dsimp at h
    by_cases hlt : acceleratedCollatz curr < m₀
    · rw [if_pos hlt] at h
      exact ⟨1, by omega, by omega, hlt⟩
    · rw [if_neg hlt] at h
      rcases ih (acceleratedCollatz curr) h with ⟨k, hk1, hkf, hk_lt⟩
      refine ⟨k + 1, by omega, by omega, ?_⟩
      dsimp [iterateAccelerated]
      exact hk_lt

/-- Kernel-certified verification that every integer `2 ≤ n < 1024` strictly descends
    below `n` within `85` accelerated steps. -/
theorem all_lt_1024_descend_within_85 :
    ((List.range 1024).all fun n =>
      decide (n < 2) || reachesBelowWithin 85 n n) = true := by
  decide

/-- Every integer `2 ≤ n < 1024` strictly descends below `n` within `85` steps. -/
theorem descent_of_lt_1024 (n : Nat) (hn1 : n > 1) (hlt : n < 1024) :
    ∃ k : Nat, 1 ≤ k ∧ k ≤ 85 ∧ iterateAccelerated n k < n := by
  have hmem : n ∈ List.range 1024 := List.mem_range.mpr hlt
  have hall := (List.all_eq_true.mp all_lt_1024_descend_within_85) n hmem
  have hnot2 : decide (n < 2) = false := decide_eq_false (by omega)
  rw [hnot2, Bool.false_or] at hall
  exact reachesBelowWithin_sound 85 n n hall

/-- Unconditional Length-64 Universal Cycle Exclusion Theorem (`no_nontrivial_cycle_length_le_64`):
    No integer `n > 1` that is minimal along its trajectory (`∀ i, iterateAccelerated n i ≥ n`)
    can form a cycle of any period `1 ≤ r ≤ 64`. -/
theorem no_nontrivial_cycle_length_le_64 (n r : Nat)
    (hn1 : n > 1) (hr1 : 1 ≤ r) (hr64 : r ≤ 64)
    (hmin : ∀ i : Nat, iterateAccelerated n i ≥ n) :
    iterateAccelerated n r ≠ n := by
  intro hcycle
  by_cases hlt1024 : n < 1024
  · rcases descent_of_lt_1024 n hn1 hlt1024 with ⟨k, _, _, hk_lt⟩
    have hge_k := hmin k
    omega
  · have hge1024 : n ≥ 1024 := by omega
    have hel := universal_cycle_minimum_element_bound n r 1024
      hn1 hr1 (by decide) hge1024 (fun i _ => hmin i) hcycle
    let a := wordOnes (parityWordOf r n)
    have ha_le : a ≤ r := by
      have hlen : (parityWordOf r n).length = r := parityWordOf_length r n
      have hle := wordOnes_le_length (parityWordOf r n)
      omega
    have hr_mem : r ∈ List.range 65 := List.mem_range.mpr (by omega)
    have ha_mem : a ∈ List.range (r + 1) := List.mem_range.mpr (by omega)
    have hall_r := (List.all_eq_true.mp checkEliahouWindow1024_64) r hr_mem
    have hall_a := (List.all_eq_true.mp hall_r) a ha_mem
    have htrue : decide (1 ≤ r ∧ 1 ≤ a ∧ 3 ^ a < 2 ^ r ∧ 2 ^ r * 1024 ^ a ≤ 3073 ^ a) = true :=
      decide_eq_true ⟨hr1, hel.1, hel.2.1, hel.2.2.2⟩
    rw [htrue] at hall_a
    contradiction

end CollatzProofClosure
end BBB17
