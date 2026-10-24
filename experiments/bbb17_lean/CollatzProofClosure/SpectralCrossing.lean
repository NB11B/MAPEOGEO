import CollatzProofClosure.Definitions

namespace BBB17
namespace CollatzProofClosure

/-! # COLLATZ-C10 Workstream 2 (Gate G3): Spectral Crossing & Infinite-Path Analysis

    Investigates trajectories satisfying `3^{a_r} ≥ 2^r` for every prefix length `r`,
    establishes that `EveryNatCrossesSpectrally` (Obligation A) is a **necessary**
    condition for `CollatzConjecture` (`collatz_implies_everyNatCrossesSpectrally`),
    proves that any descent step `r` is preceded by a first spectral crossing `t ≤ r`
    (`descent_forces_prior_firstCrossing`), and characterizes return-map spectral
    expansion (`returnMap_expanding_strict_inequality`).
-/

/-- Exact concatenation law for `parityWordOf`:
    `parityWordOf (r₁ + r₂) m = parityWordOf r₁ m ++ parityWordOf r₂ (iterateAccelerated m r₁)`. -/
theorem parityWordOf_add (r₁ r₂ m : Nat) :
    parityWordOf (r₁ + r₂) m =
      parityWordOf r₁ m ++ parityWordOf r₂ (iterateAccelerated m r₁) := by
  let w := parityWordOf r₁ m ++ parityWordOf r₂ (iterateAccelerated m r₁)
  have hlen : w.length = r₁ + r₂ := by
    dsimp [w]
    rw [List.length_append, parityWordOf_length, parityWordOf_length]
  have hv : validParityWord m w := by
    dsimp [w]
    rw [validParityWord_append, applyParityWord_parityWordOf]
    exact ⟨parityWordOf_valid r₁ m, parityWordOf_valid r₂ (iterateAccelerated m r₁)⟩
  have heq := (validParityWord_iff_eq_parityWordOf w m).mp hv
  rw [hlen] at heq
  exact heq

/-- Single-step right-extension law for `parityWordOf`:
    `parityWordOf (r + 1) m = parityWordOf r m ++ [iterateAccelerated m r % 2 == 1]`. -/
theorem parityWordOf_succ_eq_append (r m : Nat) :
    parityWordOf (r + 1) m =
      parityWordOf r m ++ [iterateAccelerated m r % 2 == 1] := by
  exact parityWordOf_add r 1 m

/-- Prefix Expansion Persistence Theorem:
    If an integer `n` encounters no first spectral crossing at any step `1 ≤ t ≤ r`,
    then `parityWordOf r n` is prefix-expanding (`IsPrefixExpanding`) and spectrally
    non-contracting (`wordD (parityWordOf r n) ≤ wordA (parityWordOf r n)`). -/
theorem noncrossing_prefix_stays_expanding (n r : Nat)
    (hno : ∀ t : Nat, 1 ≤ t → t ≤ r → ¬IsFirstCrossing (parityWordOf t n)) :
    IsPrefixExpanding (parityWordOf r n) ∧
    wordD (parityWordOf r n) ≤ wordA (parityWordOf r n) := by
  induction r with
  | zero =>
    dsimp [parityWordOf, wordD, wordA]
    exact ⟨IsPrefixExpanding.nil, by omega⟩
  | succ r ih =>
    have hno_r : ∀ t : Nat, 1 ≤ t → t ≤ r → ¬IsFirstCrossing (parityWordOf t n) := by
      intro t ht1 htr
      exact hno t ht1 (by omega)
    rcases ih hno_r with ⟨hpe_r, hle_r⟩
    have hsucc := parityWordOf_succ_eq_append r n
    generalize hb : (iterateAccelerated n r % 2 == 1) = b at hsucc
    cases b with
    | true =>
      have hpe_succ : IsPrefixExpanding (parityWordOf (r + 1) n) := by
        rw [hsucc]
        exact IsPrefixExpanding.snoc_true (parityWordOf r n) hpe_r hle_r
      have hle_succ : wordD (parityWordOf (r + 1) n) ≤ wordA (parityWordOf (r + 1) n) := by
        rw [hsucc, wordD_append, wordA_append]
        dsimp [wordD, wordA]
        omega
      exact ⟨hpe_succ, hle_succ⟩
    | false =>
      have hpe_succ : IsPrefixExpanding (parityWordOf (r + 1) n) := by
        rw [hsucc]
        exact IsPrefixExpanding.snoc_false (parityWordOf r n) hpe_r
      have hle_succ : wordD (parityWordOf (r + 1) n) ≤ wordA (parityWordOf (r + 1) n) := by
        by_cases hle' : wordD (parityWordOf (r + 1) n) ≤ wordA (parityWordOf (r + 1) n)
        · exact hle'
        · have hfc : IsFirstCrossing (parityWordOf (r + 1) n) :=
            ⟨parityWordOf r n, hsucc, hpe_r, hle_r, by omega⟩
          exact False.elim (hno (r + 1) (by omega) (by omega) hfc)
      exact ⟨hpe_succ, hle_succ⟩

/-- Non-Crossing Strict Trajectory Growth Theorem:
    For any `n > 0` and `r ≥ 1`, if `n` has not encountered a first spectral crossing
    by step `r`, then `iterateAccelerated n r > n`. -/
theorem noncrossing_prefix_strict_growth (n r : Nat) (_hn : n > 0) (hr : r ≥ 1)
    (hno : ∀ t : Nat, 1 ≤ t → t ≤ r → ¬IsFirstCrossing (parityWordOf t n)) :
    iterateAccelerated n r > n := by
  have hpe_r := (noncrossing_prefix_stays_expanding n r hno).2
  have hpe_1 := (noncrossing_prefix_stays_expanding n 1 (fun t ht1 htr => hno t ht1 (by omega))).2
  have hD1 : wordD (parityWordOf 1 n) = 2 := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hA1_ge2 : wordA (parityWordOf 1 n) ≥ 2 := by omega
  have hA_r_ge : wordA (parityWordOf r n) ≥ wordA (parityWordOf 1 n) := by
    obtain ⟨k, rfl⟩ : ∃ k, r = 1 + k := ⟨r - 1, by omega⟩
    rw [parityWordOf_add 1 k n, wordA_append]
    have hpos : wordA (parityWordOf k (iterateAccelerated n 1)) ≥ 1 :=
      wordA_pos _
    have hmul := Nat.mul_le_mul_left (wordA (parityWordOf 1 n)) hpos
    omega
  have hA_ne1 : wordA (parityWordOf r n) ≠ 1 := by omega
  have hB_pos : wordB (parityWordOf r n) > 0 := by
    by_cases hB0 : wordB (parityWordOf r n) = 0
    · have hA1 := (wordB_eq_zero_iff_wordA_eq_one (parityWordOf r n)).mp hB0
      exact False.elim (hA_ne1 hA1)
    · omega
  have hgrow := expanding_word_strict_growth (parityWordOf r n) n
    (parityWordOf_valid r n) hpe_r hB_pos
  rw [applyParityWord_parityWordOf] at hgrow
  exact hgrow

/-- First-Crossing Precedes Descent Theorem (`descent_forces_prior_firstCrossing`):
    For every positive integer `n > 0` and step `r ≥ 1`, if `iterateAccelerated n r ≤ n`,
    then `n` must have encountered a first spectral crossing `IsFirstCrossing (parityWordOf t n)`
    at some step `1 ≤ t ≤ r`. -/
theorem descent_forces_prior_firstCrossing (n r : Nat) (hn : n > 0) (hr : r ≥ 1)
    (hdesc : iterateAccelerated n r ≤ n) :
    ∃ t : Nat, 1 ≤ t ∧ t ≤ r ∧ IsFirstCrossing (parityWordOf t n) := by
  exact Classical.byContradiction fun hnot => by
    have hno : ∀ t : Nat, 1 ≤ t → t ≤ r → ¬IsFirstCrossing (parityWordOf t n) := by
      intro t ht1 htr hfc
      exact hnot ⟨t, ht1, htr, hfc⟩
    have hgt := noncrossing_prefix_strict_growth n r hn hr hno
    omega

/-- Necessity of Obligation A (`collatz_implies_everyNatCrossesSpectrally`):
    `CollatzConjecture` implies `EveryNatCrossesSpectrally` (every integer `n > 1`
    encounters a first spectral crossing). -/
theorem collatz_implies_everyNatCrossesSpectrally :
    CollatzConjecture → EveryNatCrossesSpectrally := by
  intro hcol n hn1
  have hacc := universalAcceleratedDescent_iff_collatz.mpr hcol
  rcases hacc n hn1 with ⟨r, hr_pos, hlt⟩
  rcases descent_forces_prior_firstCrossing n r (by omega) (by omega) (by omega)
    with ⟨t, ht1, _, hfc⟩
  exact ⟨t, by omega, hfc⟩

/-- Exact Characterization of `NeverCrossesSpectrally`:
    An integer `n > 1` never crosses the spectral boundary if and only if for every `r ≥ 1`,
    `wordD (parityWordOf r n) ≤ wordA (parityWordOf r n)` (which forces `iterateAccelerated n r > n`
    for all `r ≥ 1`). -/
theorem neverCrossesSpectrally_iff_all_prefixes_expanding (n : Nat) (hn1 : n > 1) :
    NeverCrossesSpectrally n ↔
      (∀ r : Nat, r ≥ 1 →
        wordD (parityWordOf r n) ≤ wordA (parityWordOf r n) ∧
        iterateAccelerated n r > n) := by
  constructor
  · intro hnever r hr
    have hno : ∀ t : Nat, 1 ≤ t → t ≤ r → ¬IsFirstCrossing (parityWordOf t n) := by
      intro t ht1 _
      exact hnever t (by omega)
    exact ⟨(noncrossing_prefix_stays_expanding n r hno).2,
           noncrossing_prefix_strict_growth n r (by omega) hr hno⟩
  · intro hall r hr hfc
    have hband := firstCrossing_spectral_band (parityWordOf r n) hfc
    have hle := (hall r (by omega)).1
    omega

/-- Helper lemma: `2 ^ K % 3 ≠ 0` for all `K : Nat`. -/
theorem pow_two_mod_three_ne_zero (K : Nat) : (2 ^ K) % 3 ≠ 0 := by
  induction K with
  | zero => decide
  | succ K ih =>
    rw [Nat.pow_succ]
    omega

/-- Strict Spectral Inequality on Return-Map Words (`2^{K_s} ≤ 3^s ↔ 2^{K_s} < 3^s`):
    For any non-empty valuation sequence `ks` (`s = ks.length ≥ 1`), `2^{totalValuation ks} ≠ 3^s`,
    and whenever `2^{totalValuation ks} ≤ 3^s`, every admissible `n > 0` satisfies
    `applyParityWord n (returnMapWord ks) > n`. -/
theorem returnMap_expanding_strict_inequality (ks : List Nat) (n : Nat)
    (hne : ks ≠ []) (_hn : n > 0)
    (hv : validParityWord n (returnMapWord ks))
    (hle : 2 ^ totalValuation ks ≤ 3 ^ ks.length) :
    2 ^ totalValuation ks < 3 ^ ks.length ∧
    applyParityWord n (returnMapWord ks) > n := by
  have hs_ge1 : ks.length ≥ 1 := by
    cases ks with
    | nil => contradiction
    | cons _ _ => simp
  have hmod2 := pow_two_mod_three_ne_zero (totalValuation ks)
  have hmod3 := pow_three_mod_three_eq_zero ks.length hs_ge1
  have hne_pow : 2 ^ totalValuation ks ≠ 3 ^ ks.length := by
    intro heq
    rw [heq] at hmod2
    exact hmod2 hmod3
  refine ⟨by omega, ?_⟩
  have hD := wordD_returnMapWord ks
  have hA := wordA_returnMapWord ks
  have hA_ge3 : wordA (returnMapWord ks) ≥ 3 := by
    rw [hA]
    obtain ⟨m, hm⟩ : ∃ m, ks.length = m + 1 := ⟨ks.length - 1, by omega⟩
    rw [hm, Nat.pow_succ]
    have hp : 3 ^ m ≥ 1 := Nat.one_le_pow m 3 (by decide)
    omega
  have hB_pos : wordB (returnMapWord ks) > 0 := by
    by_cases hB0 : wordB (returnMapWord ks) = 0
    · have hA1 := (wordB_eq_zero_iff_wordA_eq_one (returnMapWord ks)).mp hB0
      omega
    · omega
  exact expanding_word_strict_growth (returnMapWord ks) n hv (by omega) hB_pos

/-- Explicit Spectral Crossing Theorem for `n ≡ 1 (mod 4)`:
    Every integer `n > 1` with `n % 4 = 1` encounters its first spectral crossing at depth `r = 2`
    (`parityWordOf 2 n = [true, false]`, `D = 4 > 3 = A`). -/
theorem mod4_eq_one_crosses_at_depth2 (n : Nat) (hmod : n % 4 = 1) :
    IsFirstCrossing (parityWordOf 2 n) := by
  have h1 : (n % 2 == 1) = true := by
    rw [beq_iff_eq]; omega
  have hc1 : acceleratedCollatz n = 3 * (n / 4) * 2 + 2 := by
    unfold acceleratedCollatz
    have hnot0 : ¬(n % 2 = 0) := by omega
    rw [if_neg hnot0]
    omega
  have h2 : (acceleratedCollatz n % 2 == 1) = false := by
    rw [beq_eq_false_iff_ne]; omega
  have hw2 : parityWordOf 2 n = [true] ++ [false] := by
    dsimp [parityWordOf]
    rw [h1, h2]
  refine ⟨[true], hw2, ?_, ?_, ?_⟩
  · exact IsPrefixExpanding.snoc_true [] IsPrefixExpanding.nil (by decide)
  · decide
  · rw [hw2]; decide

end CollatzProofClosure
end BBB17
