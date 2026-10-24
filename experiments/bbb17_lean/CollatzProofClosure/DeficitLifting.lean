import CollatzProofClosure.Definitions

namespace BBB17
namespace CollatzProofClosure

/-! # COLLATZ-C10 Workstream 1 (Gates G1 & G2): Exact Deficit & Residue Lifting

    Formalizes the exact endpoint and deficit lifting recurrences for both even and
    odd extensions `w ++ [b]`, boundary laws for `minWordRep w`, and the exact
    pre-crossing characterization of `MinimalCrossingDeficitPositive`.
-/

/-- Exact Even-Step Lift Endpoint Identity (`2 * y' = y + ℓ * A(w)`):
    For any admissible `m` on `w` and lift `m' = m + ℓ * D(w)` admissible on `w ++ [false]`,
    `2 * applyParityWord m' (w ++ [false]) = applyParityWord m w + ℓ * wordA w`. -/
theorem even_step_lift_endpoint_eq (w : List Bool) (m ℓ : Nat)
    (hv : validParityWord m w)
    (hv_ext : validParityWord (m + ℓ * wordD w) (w ++ [false])) :
    2 * applyParityWord (m + ℓ * wordD w) (w ++ [false]) =
      applyParityWord m w + ℓ * wordA w := by
  have hshift := (parityWord_residue_shift w m ℓ hv).2
  have happ := applyParityWord_append w [false] (m + ℓ * wordD w)
  have hpost := ((validParityWord_append w [false] (m + ℓ * wordD w)).mp hv_ext).2
  dsimp [validParityWord, applyParityWord] at hpost happ
  have hstep := acceleratedCollatz_step_eq
    (applyParityWord (m + ℓ * wordD w) w) false hpost.1
  dsimp at hstep
  rw [happ, hstep, hshift]

/-- Exact Even-Step Lift Deficit Recurrence (`2 * (m' - y') = (2 * m - y) + ℓ * (2 * D(w) - A(w))`):
    Avoids fractional intermediate terms and holds across all compatible even-step lifts. -/
theorem even_step_lift_deficit_recurrence (w : List Bool) (m ℓ : Nat)
    (hv : validParityWord m w)
    (hv_ext : validParityWord (m + ℓ * wordD w) (w ++ [false]))
    (hy_le : applyParityWord m w ≤ 2 * m)
    (hA_le : wordA w ≤ 2 * wordD w) :
    let m' := m + ℓ * wordD w
    let y  := applyParityWord m w
    let y' := applyParityWord m' (w ++ [false])
    y' ≤ m' ∧
    2 * (m' - y') = (2 * m - y) + ℓ * (2 * wordD w - wordA w) := by
  dsimp
  have hend := even_step_lift_endpoint_eq w m ℓ hv hv_ext
  have hℓ_le : ℓ * wordA w ≤ ℓ * (2 * wordD w) :=
    Nat.mul_le_mul_left ℓ hA_le
  have hℓ_sub : ℓ * (2 * wordD w - wordA w) + ℓ * wordA w = ℓ * (2 * wordD w) := by
    rw [← Nat.mul_add, Nat.sub_add_cancel hA_le]
  have hℓ_assoc : ℓ * (2 * wordD w) = 2 * (ℓ * wordD w) := by
    rw [← Nat.mul_assoc, Nat.mul_comm ℓ 2, Nat.mul_assoc]
  omega

/-- Exact Odd-Step Lift Endpoint Identity (`2 * y' = 3 * (y + ℓ * A(w)) + 1`):
    For any admissible `m` on `w` and lift `m' = m + ℓ * D(w)` admissible on `w ++ [true]`,
    `2 * applyParityWord m' (w ++ [true]) = 3 * (applyParityWord m w + ℓ * wordA w) + 1`. -/
theorem odd_step_lift_endpoint_eq (w : List Bool) (m ℓ : Nat)
    (hv : validParityWord m w)
    (hv_ext : validParityWord (m + ℓ * wordD w) (w ++ [true])) :
    2 * applyParityWord (m + ℓ * wordD w) (w ++ [true]) =
      3 * (applyParityWord m w + ℓ * wordA w) + 1 := by
  have hshift := (parityWord_residue_shift w m ℓ hv).2
  have happ := applyParityWord_append w [true] (m + ℓ * wordD w)
  have hpost := ((validParityWord_append w [true] (m + ℓ * wordD w)).mp hv_ext).2
  dsimp [validParityWord, applyParityWord] at hpost happ
  have hstep := acceleratedCollatz_step_eq
    (applyParityWord (m + ℓ * wordD w) w) true hpost.1
  dsimp at hstep
  rw [happ, hstep, hshift]

/-- Exact Odd-Step Lift Deficit Recurrence in the Contracting Regime
    (`2 * (m' - y') = (2 * m - 3 * y - 1) + ℓ * (2 * D(w) - 3 * A(w))`). -/
theorem odd_step_lift_deficit_recurrence (w : List Bool) (m ℓ : Nat)
    (hv : validParityWord m w)
    (hv_ext : validParityWord (m + ℓ * wordD w) (w ++ [true]))
    (hy_le : 3 * applyParityWord m w + 1 ≤ 2 * m)
    (hA_le : 3 * wordA w ≤ 2 * wordD w) :
    let m' := m + ℓ * wordD w
    let y  := applyParityWord m w
    let y' := applyParityWord m' (w ++ [true])
    y' ≤ m' ∧
    2 * (m' - y') = (2 * m - 3 * y - 1) + ℓ * (2 * wordD w - 3 * wordA w) := by
  dsimp
  have hend := odd_step_lift_endpoint_eq w m ℓ hv hv_ext
  have hℓ_sub : ℓ * (2 * wordD w - 3 * wordA w) + ℓ * (3 * wordA w) = ℓ * (2 * wordD w) := by
    rw [← Nat.mul_add, Nat.sub_add_cancel hA_le]
  have hℓ_A : 3 * (ℓ * wordA w) = ℓ * (3 * wordA w) := by
    rw [← Nat.mul_assoc, Nat.mul_comm 3 ℓ, Nat.mul_assoc]
  have hℓ_D : ℓ * (2 * wordD w) = 2 * (ℓ * wordD w) := by
    rw [← Nat.mul_assoc, Nat.mul_comm ℓ 2, Nat.mul_assoc]
  omega

/-- Dual Odd-Step Lift Expansion Recurrence in the Prefix-Expanding Regime
    (`2 * (y' - m') = (3 * y + 1 - 2 * m) + ℓ * (3 * A(w) - 2 * D(w))`). -/
theorem odd_step_lift_expansion_recurrence (w : List Bool) (m ℓ : Nat)
    (hv : validParityWord m w)
    (hv_ext : validParityWord (m + ℓ * wordD w) (w ++ [true]))
    (hy_ge : 2 * m ≤ 3 * applyParityWord m w + 1)
    (hA_ge : 2 * wordD w ≤ 3 * wordA w) :
    let m' := m + ℓ * wordD w
    let y  := applyParityWord m w
    let y' := applyParityWord m' (w ++ [true])
    m' ≤ y' ∧
    2 * (y' - m') = (3 * y + 1 - 2 * m) + ℓ * (3 * wordA w - 2 * wordD w) := by
  dsimp
  have hend := odd_step_lift_endpoint_eq w m ℓ hv hv_ext
  have hℓ_sub : ℓ * (3 * wordA w - 2 * wordD w) + ℓ * (2 * wordD w) = ℓ * (3 * wordA w) := by
    rw [← Nat.mul_add, Nat.sub_add_cancel hA_ge]
  have hℓ_A : 3 * (ℓ * wordA w) = ℓ * (3 * wordA w) := by
    rw [← Nat.mul_assoc, Nat.mul_comm 3 ℓ, Nat.mul_assoc]
  have hℓ_D : ℓ * (2 * wordD w) = 2 * (ℓ * wordD w) := by
    rw [← Nat.mul_assoc, Nat.mul_comm ℓ 2, Nat.mul_assoc]
  omega

/-- Exact Canonical Residue Lifting Formula (`wordResidue (w ++ [b]) = wordResidue w + liftBit w b * wordD w`):
    Unifies both branches of `wordResidue_append_singleton_dichotomy` via `liftBit w b ∈ {0, 1}`. -/
theorem wordResidue_append_eq_add_liftBit (w : List Bool) (b : Bool) :
    (liftBit w b = 0 ∨ liftBit w b = 1) ∧
    wordResidue (w ++ [b]) = wordResidue w + liftBit w b * wordD w := by
  have hdich := wordResidue_append_singleton_dichotomy w b
  unfold liftBit canonicalOutput
  by_cases hpar : decide (applyParityWord (wordResidue w) w % 2 = 1) = b
  · rw [if_pos hpar]
    refine ⟨Or.inl rfl, ?_⟩
    rw [Nat.zero_mul, Nat.add_zero]
    have hmatch : stepParityMatches (applyParityWord (wordResidue w) w) b := by
      cases b with
      | false =>
        dsimp [stepParityMatches]
        have hf : decide (applyParityWord (wordResidue w) w % 2 = 1) = false := hpar
        have hnot1 : ¬(applyParityWord (wordResidue w) w % 2 = 1) := of_decide_eq_false hf
        omega
      | true =>
        dsimp [stepParityMatches]
        exact of_decide_eq_true hpar
    have hv_r0 : validParityWord (wordResidue w) (w ++ [b]) := by
      rw [validParityWord_append]
      refine ⟨wordResidue_valid w, ?_⟩
      dsimp [validParityWord]
      exact ⟨hmatch, trivial⟩
    have hmod := (validParityWord_iff_mod_eq_wordResidue (w ++ [b]) (wordResidue w)).mp hv_r0
    have hlt_w : wordResidue w < wordD w := wordResidue_lt_wordD w
    have hlt_wb : wordResidue w < wordD (w ++ [b]) := by
      rw [wordD_append]; dsimp [wordD]; omega
    rw [Nat.mod_eq_of_lt hlt_wb] at hmod
    exact hmod.symm
  · rw [if_neg hpar]
    refine ⟨Or.inr rfl, ?_⟩
    rw [Nat.one_mul]
    have hnot_match : ¬stepParityMatches (applyParityWord (wordResidue w) w) b := by
      intro hm
      apply hpar
      cases b with
      | false =>
        dsimp [stepParityMatches] at hm
        exact decide_eq_false (by omega)
      | true =>
        dsimp [stepParityMatches] at hm
        exact decide_eq_true hm
    exact (hdich.2 hnot_match).1

/-- Boundary Law for `minWordRep`: whenever `wordResidue w ≥ 2`, `minWordRep w = wordResidue w`. -/
theorem minWordRep_eq_wordResidue_of_ge_two (w : List Bool) (hge2 : wordResidue w ≥ 2) :
    minWordRep w = wordResidue w ∧ minRepOutput w = canonicalOutput w := by
  have h1 : minWordRep w = wordResidue w := by
    unfold minWordRep minClassRep
    have hnot1 : ¬(wordResidue w ≤ 1) := by omega
    rw [if_neg hnot1]
  refine ⟨h1, ?_⟩
  unfold minRepOutput canonicalOutput
  rw [h1]

/-- Boundary Law for `wordResidue w ≤ 1`: `minWordRep w = wordResidue w + wordD w`
    and `minRepOutput w = canonicalOutput w + wordA w`. -/
theorem minWordRep_eq_add_wordD_of_le_one (w : List Bool) (hle1 : wordResidue w ≤ 1) :
    minWordRep w = wordResidue w + wordD w ∧
    minRepOutput w = canonicalOutput w + wordA w := by
  have h1 : minWordRep w = wordResidue w + wordD w := by
    unfold minWordRep minClassRep
    rw [if_pos hle1]
  refine ⟨h1, ?_⟩
  unfold minRepOutput canonicalOutput
  rw [h1]
  have hshift := (parityWord_residue_shift w (wordResidue w) 1 (wordResidue_valid w)).2
  simpa using hshift

/-- Exact Pre-Crossing Characterization Theorem (Gate G2):
    For any first-crossing word `w = w₁ ++ [false] ∈ 𝓜`, let `m₁` be admissible for `w₁`
    and `m' = m₁ + ℓ * wordD w₁` be admissible for `w`. Then:
    1. `2 * applyParityWord m' w = applyParityWord m₁ w₁ + ℓ * wordA w`,
    2. `wordDelta w = 2 * wordD w₁ - wordA w₁`, and
    3. Strict descent `applyParityWord m' w < m'` holds IF AND ONLY IF the pre-crossing
       output `y₁ = applyParityWord m₁ w₁` satisfies the strict upper bound
       `applyParityWord m₁ w₁ + ℓ * wordA w < 2 * m₁ + 2 * ℓ * wordD w₁`
       (which when `ℓ ≤ 1` and `2 * wordD w₁ > wordA w` simplifies to `y₁ < 2 * m₁ + ℓ * wordDelta w`). -/
theorem firstCrossing_descent_iff_preCrossing_bound (w₁ : List Bool) (m₁ ℓ : Nat)
    (hw : IsFirstCrossing (w₁ ++ [false]))
    (hv₁ : validParityWord m₁ w₁)
    (hv_ext : validParityWord (m₁ + ℓ * wordD w₁) (w₁ ++ [false])) :
    let w  := w₁ ++ [false]
    let m' := m₁ + ℓ * wordD w₁
    let y₁ := applyParityWord m₁ w₁
    let y' := applyParityWord m' w
    2 * y' = y₁ + ℓ * wordA w ∧
    wordDelta w = 2 * wordD w₁ - wordA w₁ ∧
    (y' < m' ↔ y₁ < 2 * m₁ + ℓ * wordDelta w) := by
  dsimp
  have hend := even_step_lift_endpoint_eq w₁ m₁ ℓ hv₁ hv_ext
  have hband := firstCrossing_spectral_band (w₁ ++ [false]) hw
  have hD_eq : wordD (w₁ ++ [false]) = 2 * wordD w₁ := by
    rw [wordD_append]; dsimp [wordD]; omega
  have hA_eq : wordA (w₁ ++ [false]) = wordA w₁ := by
    rw [wordA_append]; dsimp [wordA]; omega
  have hDelta_eq : wordDelta (w₁ ++ [false]) = 2 * wordD w₁ - wordA w₁ := by
    unfold wordDelta; omega
  have hℓ_sub : ℓ * wordDelta (w₁ ++ [false]) + ℓ * wordA w₁ =
      2 * (ℓ * wordD w₁) := by
    rw [hDelta_eq, ← Nat.mul_add, Nat.sub_add_cancel (by omega)]
    rw [← Nat.mul_assoc, Nat.mul_comm ℓ 2, Nat.mul_assoc]
  refine ⟨?_, hDelta_eq, ?_⟩
  · rw [hA_eq]; exact hend
  · constructor <;> intro h <;> omega

end CollatzProofClosure
end BBB17
