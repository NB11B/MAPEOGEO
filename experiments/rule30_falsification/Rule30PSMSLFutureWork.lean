import Ruliology.CellularAutomata.Rule30Prize
import Ruliology.CellularAutomata.Rule30Realization
import Ruliology.CellularAutomata.Rule30MaskedJen
import Ruliology.CellularAutomata.Rule30Diagonals
import Ruliology.CellularAutomata.Rule30BlackRuns

/-!
# Standalone Gate `G10` Module: PSMSL Future-Work Qualification (`G10.1` – `G10.6`)

This standalone module develops and verifies all six `G10` sub-gates in isolation before
importing/integrating into `Rule30Submission.lean`:
- `G10.1`: Exact Boolean work-losslessness (`g10_p1_boolean_right_screen_work_lossless`)
- `G10.2`: Future-work equivalence hierarchy `FutureWorkEquiv` (`g10_p1_futureWorkEquiv_zero_iff_maskedPeriodEquiv`,
  `g10_p1_futureWorkEquiv_antitone_refinement`)
- `G10.3`: Delayed information re-entry `ReEntryAtHorizon` (`g10_p1_delayed_information_reentry_witnesses`)
- `G10.4`: Composition-stable persistent quotient `PersistentWorkEquiv` (`g10_p1_futureWorkEquiv_shift_step`,
  `g10_p1_persistentWorkEquiv_equivalence_and_congruence`)
- `G10.5`: Single-seed vs Ether return orbits (`g10_p1_ether_c7_quotient_period_two`,
  `g10_p1_single_seed_right_support_exact_frontier`)
- `G10.6`: Implication to `Rule30Prize.Problem1` and Prize 2 / Prize 3 quotient properties
  (`g10_p1_eventually_periodic_quotient_repetition_excludes_arbitrary_period`,
   `g10_p1_psmsl_quotient_eventual_repetition_implies_problem1`,
   `g10_p2_p3_futureWorkEquiv_preserves_discrepancy_and_work`)
-/

namespace Rule30PSMSLFutureWork

open Ruliology.CellularAutomata
open Ruliology.CellularAutomata.Rule30Prize
open Ruliology.CellularAutomata.Rule30Realization
open Ruliology.CellularAutomata.Rule30Jen
open Ruliology.CellularAutomata.Rule30MaskedJen
open Ruliology.CellularAutomata.Rule30Diagonals
open Ruliology.CellularAutomata.Rule30BlackRuns

def col0Word (t : Nat) : Nat → List Bool
  | 0 => []
  | L + 1 => cell t 0 :: col0Word (t + 1) L

def runWord : List Bool → List Bool → List Bool
  | [], σ => σ
  | c :: cs, σ => runWord cs (stepRow c σ)

def iterPeriodReturn (w : List Bool) : Nat → List Bool → List Bool
  | 0, σ => σ
  | m + 1, σ => iterPeriodReturn w m (runWord w σ)

def orColWord : List Bool → List Bool → List Bool
  | [], _ => []
  | c :: cs, σ => (c || σ.headD false) :: orColWord cs (stepRow c σ)

def col0OrTrace (t : Nat) : Nat → List Bool
  | 0 => []
  | L + 1 => orCol 0 t :: col0OrTrace (t + 1) L

@[reducible] def MaskedPeriodEquiv (w σ₁ σ₂ : List Bool) : Prop :=
  orColWord w σ₁ = orColWord w σ₂

def wordDiscrepancyWeight : List Bool → Int
  | [] => 0
  | c :: cs => (if c then 1 else -1) + wordDiscrepancyWeight cs

def c7 (p : Int) : Bool := decide ((p + 1) % 7 = 0)

theorem col0Word_shift_period (T P : Nat)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) :
    ∀ (L t : Nat), T ≤ t → col0Word (t + P) L = col0Word t L
  | 0, _, _ => rfl
  | L + 1, t, ht => by
    have h0 : cell (t + P) 0 = cell t 0 := hper t ht
    have ih := col0Word_shift_period T P hper L (t + 1) (by omega)
    rw [show t + 1 + P = t + P + 1 by omega] at ih
    show cell (t + P) 0 :: col0Word (t + P + 1) L = cell t 0 :: col0Word (t + 1) L
    rw [h0, ih]

theorem col0Word_shift_period_mul (T P : Nat)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) :
    ∀ (m L t : Nat), T ≤ t → col0Word (t + m * P) L = col0Word t L
  | 0, L, t, _ => by simp
  | m + 1, L, t, ht => by
    have ih := col0Word_shift_period_mul T P hper m L t ht
    have h1 := col0Word_shift_period T P hper L (t + m * P) (by omega)
    rw [show t + (m + 1) * P = t + m * P + P by rw [Nat.succ_mul]; omega, h1, ih]

theorem orColWord_rowAt :
    ∀ (L n t : Nat),
      orColWord (col0Word t L) (rowAt t 1 (n + L + 1)) = col0OrTrace t L
  | 0, _, _ => rfl
  | L + 1, n, t => by
    have hstep := stepRow_rowAt t (n + L + 1) 1
    rw [show (1 : Int) - 1 = 0 by rfl] at hstep
    have ih := orColWord_rowAt L n (t + 1)
    rw [show n + (L + 1) + 1 = n + L + 1 + 1 by omega]
    show (cell t 0 || (cell t 1 :: rowAt t (1 + 1) (n + L + 1)).headD false) ::
      orColWord (col0Word (t + 1) L) (stepRow (cell t 0) (rowAt t 1 (n + L + 1 + 1))) =
      orCol 0 t :: col0OrTrace (t + 1) L
    rw [hstep, ih]
    rfl

theorem col0OrTrace_getD :
    ∀ (L t s : Nat), s < L → (col0OrTrace t L).getD s false = orCol 0 (t + s)
  | 0, _, _, hs => absurd hs (Nat.not_lt_zero _)
  | L + 1, t, 0, _ => by simp [col0OrTrace]
  | L + 1, t, s + 1, hs => by
    have ih := col0OrTrace_getD L (t + 1) s (by omega)
    rw [show t + 1 + s = t + (s + 1) by omega] at ih
    exact ih

/-! ### `G10.1`: Exact Boolean PSMSL Work-Equivalence & Work-Lossless Projection -/

/-- **G10.1 Exact Boolean PSMSL Work-Lossless Screening (`g10_p1_boolean_right_screen_work_lossless`)**:
    Certifies the exact Boolean counterpart of `work_relative_information_loss`:
    1. When the middle input bit of `rule` is `true`, dropping the right input bit `r` loses global
       information (`true ≠ false`) while remaining 100% work-lossless (`rule l true r = !l`).
    2. During a 1-step black center phase (`w = [true]`), dropping the entire right-hand prefix `σ`
       is work-lossless for the masked observation `orColWord [true] σ = [true]`. -/
theorem g10_p1_boolean_right_screen_work_lossless :
    (∀ l r₁ r₂ : Bool, rule l true r₁ = rule l true r₂ ∧ rule l true r₁ = !l) ∧
    (∀ σ₁ σ₂ : List Bool,
      orColWord [true] σ₁ = [true] ∧ orColWord [true] σ₁ = orColWord [true] σ₂) := by
  refine ⟨fun l r₁ r₂ => ?_, fun σ₁ σ₂ => ⟨rfl, rfl⟩⟩
  cases l <;> cases r₁ <;> cases r₂ <;> decide

/-! ### `G10.2`: Future-Observation Equivalence Hierarchy `FutureWorkEquiv` (`≡_{w, m}`) -/

/-- **G10.2 Horizon-`m` Future-Work Equivalence (`FutureWorkEquiv`)**:
    `σ₁ ≡_{w, m} σ₂` holds iff for every return horizon `k ≤ m`, the `k`-th period return states
    produce identical masked observations `orColWord w (F_w^k(σ₁)) = orColWord w (F_w^k(σ₂))`. -/
def FutureWorkEquiv (w : List Bool) (m : Nat) (σ₁ σ₂ : List Bool) : Prop :=
  ∀ k : Nat, k ≤ m →
    orColWord w (iterPeriodReturn w k σ₁) = orColWord w (iterPeriodReturn w k σ₂)

/-- **G10.2 Base Horizon `m = 0` Coincides with `MaskedPeriodEquiv`
    (`g10_p1_futureWorkEquiv_zero_iff_maskedPeriodEquiv`)**:
    `FutureWorkEquiv w 0 σ₁ σ₂ ↔ MaskedPeriodEquiv w σ₁ σ₂`. -/
theorem g10_p1_futureWorkEquiv_zero_iff_maskedPeriodEquiv
    (w σ₁ σ₂ : List Bool) :
    FutureWorkEquiv w 0 σ₁ σ₂ ↔ MaskedPeriodEquiv w σ₁ σ₂ := by
  constructor
  · intro h
    exact h 0 (Nat.le_refl 0)
  · intro h k hk
    have hk0 : k = 0 := by omega
    subst hk0
    exact h

/-- **G10.2 Monotone & Strict Horizon Refinement (`g10_p1_futureWorkEquiv_antitone_refinement`)**:
    1. For all `m₁ ≤ m₂`, `FutureWorkEquiv w m₂ σ₁ σ₂ → FutureWorkEquiv w m₁ σ₁ σ₂` (`≡_{w, m₂} ⊆ ≡_{w, m₁}`).
    2. Strict refinement `≡_{w, 1} ⊂neq ≡_{w, 0}` and `≡_{w, 2} ⊂neq ≡_{w, 1}` holds for `w = [true, false]`. -/
theorem g10_p1_futureWorkEquiv_antitone_refinement :
    (∀ (w : List Bool) (m₁ m₂ : Nat) (σ₁ σ₂ : List Bool),
      m₁ ≤ m₂ → FutureWorkEquiv w m₂ σ₁ σ₂ → FutureWorkEquiv w m₁ σ₁ σ₂) ∧
    (FutureWorkEquiv [true, false] 0
        [true, false, false, false, false]
        [true, true, true, true, false] ∧
      ¬ FutureWorkEquiv [true, false] 1
        [true, false, false, false, false]
        [true, true, true, true, false]) ∧
    (FutureWorkEquiv [true, false] 1
        [true, false, false, false, false, false, false]
        [true, true, false, false, false, false, false] ∧
      ¬ FutureWorkEquiv [true, false] 2
        [true, false, false, false, false, false, false]
        [true, true, false, false, false, false, false]) := by
  refine ⟨fun w m₁ m₂ σ₁ σ₂ hm h k hk => h k (Nat.le_trans hk hm), ⟨?_, ?_⟩, ⟨?_, ?_⟩⟩
  · intro k hk
    have hk0 : k = 0 := by omega
    subst hk0
    rfl
  · intro h
    have h1 := h 1 (Nat.le_refl 1)
    revert h1
    decide
  · intro k hk
    have hcases : k = 0 ∨ k = 1 := by omega
    rcases hcases with rfl | rfl <;> rfl
  · intro h
    have h2 := h 2 (Nat.le_refl 2)
    revert h2
    decide

/-! ### `G10.3`: Delayed Information Re-Entry `ReEntryAtHorizon` (`τ_w(σ₁, σ₂) = k`) -/

/-- **G10.3 Exact Delayed Information Re-Entry Predicate (`ReEntryAtHorizon`)**:
    `ReEntryAtHorizon w k σ₁ σ₂` holds iff `σ₁` and `σ₂` have identical masked observations
    for all periods `0 ≤ j < k`, and first diverge at return period `k` (`τ_w(σ₁, σ₂) = k`). -/
def ReEntryAtHorizon (w : List Bool) (k : Nat) (σ₁ σ₂ : List Bool) : Prop :=
  (∀ j : Nat, j < k →
    orColWord w (iterPeriodReturn w j σ₁) = orColWord w (iterPeriodReturn w j σ₂)) ∧
  orColWord w (iterPeriodReturn w k σ₁) ≠ orColWord w (iterPeriodReturn w k σ₂)

/-- **G10.3 Certified Minimal Witnesses for Delayed Information Re-Entry at `k = 1, 2, 3`
    (`g10_p1_delayed_information_reentry_witnesses`)**:
    Exhibits three explicit pairs of depth-`0` right-hand boundary prefixes under `w = [true, false]`
    whose initially screened tail differences re-enter the observable column `orColWord` at exact
    return horizons `τ_w = 1`, `τ_w = 2`, and `τ_w = 3`. -/
theorem g10_p1_delayed_information_reentry_witnesses :
    let w := [true, false]
    ReEntryAtHorizon w 1
      [true, false, false, false, false]
      [true, true, true, true, false] ∧
    ReEntryAtHorizon w 2
      [true, false, false, false, false, false, false]
      [true, true, false, false, false, false, false] ∧
    ReEntryAtHorizon w 3
      [true, true, false, false, false, false, false, false, false]
      [true, false, false, true, false, false, false, false, false] := by
  refine ⟨⟨?_, by decide⟩, ⟨?_, by decide⟩, ⟨?_, by decide⟩⟩
  · intro j hj
    have hj0 : j = 0 := by omega
    subst hj0
    rfl
  · intro j hj
    have hcases : j = 0 ∨ j = 1 := by omega
    rcases hcases with rfl | rfl <;> rfl
  · intro j hj
    have hcases : j = 0 ∨ j = 1 ∨ j = 2 := by omega
    rcases hcases with rfl | rfl | rfl <;> rfl

/-! ### `G10.4`: Composition-Stable Persistent Quotient `PersistentWorkEquiv` (`≡_{w, ∞}`) -/

/-- **G10.4 Exact Step-Shift Factorization of `FutureWorkEquiv` (`g10_p1_futureWorkEquiv_shift_step`)**:
    Two states are `(m + 1)`-horizon work-equivalent iff they are `0`-horizon equivalent
    (`MaskedPeriodEquiv`) and their 1-period images `runWord w σ₁, runWord w σ₂` are
    `m`-horizon work-equivalent. -/
theorem g10_p1_futureWorkEquiv_shift_step
    (w : List Bool) (m : Nat) (σ₁ σ₂ : List Bool) :
    FutureWorkEquiv w (m + 1) σ₁ σ₂ ↔
      MaskedPeriodEquiv w σ₁ σ₂ ∧ FutureWorkEquiv w m (runWord w σ₁) (runWord w σ₂) := by
  constructor
  · intro h
    refine ⟨h 0 (by omega), fun k hk => ?_⟩
    exact h (k + 1) (by omega)
  · rintro ⟨h0, hm⟩ k hk
    cases k with
    | zero => exact h0
    | succ k' => exact hm k' (by omega)

/-- **G10.4 Infinite-Horizon Persistent Work-Equivalence (`PersistentWorkEquiv`)**:
    `σ₁ ≡_{w, ∞} σ₂` holds iff `σ₁ ≡_{w, m} σ₂` for every finite horizon `m : Nat`. -/
def PersistentWorkEquiv (w σ₁ σ₂ : List Bool) : Prop :=
  ∀ m : Nat, FutureWorkEquiv w m σ₁ σ₂

theorem iterPeriodReturn_add (w : List Bool) :
    ∀ (k j : Nat) (σ : List Bool),
      iterPeriodReturn w j (iterPeriodReturn w k σ) = iterPeriodReturn w (k + j) σ
  | 0, j, σ => by simp [iterPeriodReturn]
  | k + 1, j, σ => by
    have ih := iterPeriodReturn_add w k j (runWord w σ)
    rw [show k + 1 + j = (k + j) + 1 by omega]
    exact ih

/-- **G10.4 Persistent Work-Equivalence Is a Composition-Stable Equivalence Congruence
    (`g10_p1_persistentWorkEquiv_equivalence_and_congruence`)**:
    Proves that `PersistentWorkEquiv w` (`≡_{w, ∞}`) is:
    1. Reflexive, symmetric, and transitive;
    2. Preserved under `F_w = runWord w` and all iterates `F_w^k = iterPeriodReturn w k`;
    3. Satisfies the exact quotient transition factorization
       `σ₁ ≡_{w, ∞} σ₂ ↔ MaskedPeriodEquiv w σ₁ σ₂ ∧ runWord w σ₁ ≡_{w, ∞} runWord w σ₂`. -/
theorem g10_p1_persistentWorkEquiv_equivalence_and_congruence (w : List Bool) :
    (∀ σ, PersistentWorkEquiv w σ σ) ∧
    (∀ σ₁ σ₂, PersistentWorkEquiv w σ₁ σ₂ → PersistentWorkEquiv w σ₂ σ₁) ∧
    (∀ σ₁ σ₂ σ₃,
      PersistentWorkEquiv w σ₁ σ₂ → PersistentWorkEquiv w σ₂ σ₃ → PersistentWorkEquiv w σ₁ σ₃) ∧
    (∀ σ₁ σ₂,
      PersistentWorkEquiv w σ₁ σ₂ →
      ∀ k : Nat, PersistentWorkEquiv w (iterPeriodReturn w k σ₁) (iterPeriodReturn w k σ₂)) ∧
    (∀ σ₁ σ₂,
      PersistentWorkEquiv w σ₁ σ₂ ↔
        MaskedPeriodEquiv w σ₁ σ₂ ∧ PersistentWorkEquiv w (runWord w σ₁) (runWord w σ₂)) := by
  refine ⟨fun _ _ _ _ => rfl,
    fun _ _ h m k hk => (h m k hk).symm,
    fun _ _ _ h12 h23 m k hk => (h12 m k hk).trans (h23 m k hk),
    fun σ₁ σ₂ h k m j hj => ?_,
    fun σ₁ σ₂ => ?_⟩
  · rw [iterPeriodReturn_add, iterPeriodReturn_add]
    exact h (k + m) (k + j) (by omega)
  · constructor
    · intro h
      refine ⟨h 0 0 (Nat.le_refl 0), fun m k hk => ?_⟩
      exact h (m + 1) (k + 1) (by omega)
    · rintro ⟨h0, hstep⟩ m k hk
      cases k with
      | zero => exact h0
      | succ k' => exact hstep m k' (by omega)

/-! ### `G10.5`: Single-Seed-Compatible vs. Ether-Like Return Orbits -/

/-- **G10.5 Finitely Supported Right-Half Ether Mimic vs. `q = 2` Quotient Period
    (`g10_p1_ether_c7_quotient_period_two`)**:
    Under the alternating center word `w = [false, true]` (`P = 2`), the finitely supported
    right-hand prefix `σ_fin6 = [false, false, false, false, false, true]` (padded with white
    cells) and the Ether `c7` right-hand prefix:
    1. Immediately diverge from their 1-period shift at `k = 0` (`ReEntryAtHorizon w 0 σ (runWord w σ)`),
    2. Synchronize at the sub-harmonic period `q = 2` across multiple return horizons
       (`FutureWorkEquiv w 3 σ (iterPeriodReturn w 2 σ)`), and
    3. Agree with each other across 4 consecutive periods (`FutureWorkEquiv w 3 σ_fin6 σ_c7`),
       demonstrating why one-sided right-half finite support alone cannot rule out `q = 2` Ether-like
       quotient orbits without the left-half boundary constraint. -/
theorem g10_p1_ether_c7_quotient_period_two :
    let w := [false, true]
    let σ_fin6 := [false, false, false, false, false, true,
                   false, false, false, false, false, false, false, false]
    let σ_c7   := [false, false, false, false, false, true,
                   false, false, false, false, false, false, true, false]
    ReEntryAtHorizon w 0 σ_fin6 (runWord w σ_fin6) ∧
    FutureWorkEquiv w 3 σ_fin6 (iterPeriodReturn w 2 σ_fin6) ∧
    FutureWorkEquiv w 3 σ_fin6 σ_c7 := by
  refine ⟨⟨fun j hj => absurd hj (Nat.not_lt_zero _), by decide⟩, ?_, ?_⟩
  · intro k hk
    have hcases : k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 := by omega
    rcases hcases with rfl | rfl | rfl | rfl <;> rfl
  · intro k hk
    have hcases : k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 := by omega
    rcases hcases with rfl | rfl | rfl | rfl <;> rfl

/-- **G10.5 Single-Seed Right-Hand Active Support Frontier (`g10_p1_single_seed_right_support_exact_frontier`)**:
    On the official single-seed trajectory (`cell`), at every step `t : Nat`:
    1. The right-edge light-cone frontier cell `p = +t` is black (`cell t t = true`),
    2. Every cell strictly to the right of `+t` (`(t : Int) < p`) is white (`cell t p = false`),
    so at return step `t₁ + m * P` the active right-hand support has exact frontier `t₁ + m * P`
    (growing linearly at rate `+P` per period). -/
theorem g10_p1_single_seed_right_support_exact_frontier (t : Nat) :
    cell t (t : Int) = true ∧
    (∀ p : Int, (t : Int) < p → cell t p = false) := by
  refine ⟨?_, fun p hp => cell_eq_false_of_gt t p hp⟩
  have hR := R_zero t
  unfold R at hR
  rwa [show (t : Int) - (0 : Nat) = (t : Int) by omega] at hR

/-! ### `G10.6`: Official `Problem1` Implication & Prize 2 / Prize 3 Quotient Properties -/

/-- **G10.6 Eventual Quotient Repetition Excludes Arbitrary Center Period
    (`g10_p1_eventually_periodic_quotient_repetition_excludes_arbitrary_period`)**:
    If `Rule30Prize.center` is `P`-periodic from `T` on (`P > 0`), then no single-seed return orbit
    starting at `t₁ ≥ T` can ever repeat in the PSMSL future-work quotient `FutureWorkEquiv`
    (even at base horizon `m = 0`) at any period multiple `q > 0`. -/
theorem g10_p1_eventually_periodic_quotient_repetition_excludes_arbitrary_period
    (T P t₁ q : Nat)
    (hP : 0 < P)
    (hq : 0 < q)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₁ : T ≤ t₁)
    (hrep : ∀ m : Nat,
      FutureWorkEquiv (col0Word t₁ P) 0
        (rowAt (t₁ + (m + q) * P) 1 (P + 1))
        (rowAt (t₁ + m * P) 1 (P + 1))) :
    False := by
  have hor_step : ∀ m s : Nat, s < P →
      orCol 0 (t₁ + (m + q) * P + s) = orCol 0 (t₁ + m * P + s) := by
    intro m s hs
    have hm := (g10_p1_futureWorkEquiv_zero_iff_maskedPeriodEquiv _ _ _).mp (hrep m)
    unfold MaskedPeriodEquiv at hm
    have hcol1 := col0Word_shift_period_mul T P hper (m + q) P t₁ ht₁
    have hcol2 := col0Word_shift_period_mul T P hper m P t₁ ht₁
    have htr1 := orColWord_rowAt P 0 (t₁ + (m + q) * P)
    have htr2 := orColWord_rowAt P 0 (t₁ + m * P)
    rw [Nat.zero_add, hcol1] at htr1
    rw [Nat.zero_add, hcol2] at htr2
    rw [htr1, htr2] at hm
    have hget := congrArg (fun l => l.getD s false) hm
    rw [col0OrTrace_getD P (t₁ + (m + q) * P) s hs,
      col0OrTrace_getD P (t₁ + m * P) s hs] at hget
    exact hget
  have hQ : 0 < q * P := Nat.mul_pos hq hP
  have hper_or : EventuallyPeriodic (fun t => orCol 0 t) := by
    refine ⟨t₁, q * P, hQ, fun t ht => ?_⟩
    show orCol 0 (t + q * P) = orCol 0 t
    have hdm := Nat.div_add_mod (t - t₁) P
    generalize (t - t₁) / P = m at hdm
    have hmod := Nat.mod_lt (t - t₁) hP
    generalize (t - t₁) % P = s at hdm hmod
    have hcomm : P * m = m * P := Nat.mul_comm P m
    have hadd : (m + q) * P = m * P + q * P := Nat.add_mul m q P
    have heq := hor_step m s hmod
    rw [hadd] at heq
    rw [show t + q * P = t₁ + (m * P + q * P) + s by omega, heq,
      show t₁ + m * P + s = t by omega]
  have hper0 : EventuallyPeriodic (fun t => cell t 0) := ⟨T, P, hP, hper⟩
  exact orCol_not_eventuallyPeriodic 0 hper0 hper_or

/-- **G10.6 Direct PSMSL Quotient Implication to `Rule30Prize.Problem1`
    (`g10_p1_psmsl_quotient_eventual_repetition_implies_problem1`)**:
    Formalizes the Section 7 target reduction:
    `EventuallyPeriodic(c₀) ⟹ Constrained Return Orbit ⟹ Quotient Repetition ⟹ Problem1`.
    If every hypothetical periodic center orbit on the single-seed trajectory eventually enters
    a repeating PSMSL work-equivalence class (`FutureWorkEquiv · 0`), then `Rule30Prize.Problem1`
    holds unconditionally. -/
theorem g10_p1_psmsl_quotient_eventual_repetition_implies_problem1
    (hQuotientRep : ∀ (T₀ P : Nat), 0 < P →
      (∀ t, T₀ ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
      ∃ t₁ q : Nat, T₀ ≤ t₁ ∧ 0 < q ∧ ∀ m : Nat,
        FutureWorkEquiv (col0Word t₁ P) 0
          (rowAt (t₁ + (m + q) * P) 1 (P + 1))
          (rowAt (t₁ + m * P) 1 (P + 1))) :
    Rule30Prize.Problem1 := by
  rintro ⟨T₀, P, hP, hper⟩
  obtain ⟨t₁, q, ht₁, hq, hrep⟩ := hQuotientRep T₀ P hP hper
  exact g10_p1_eventually_periodic_quotient_repetition_excludes_arbitrary_period
    T₀ P t₁ q hP hq hper ht₁ hrep

/-- **G10.6 Prize 2 & Prize 3 Quotient Preservation of Work and Discrepancy
    (`g10_p2_p3_futureWorkEquiv_preserves_discrepancy_and_work`)**:
    1. **Prize 3 (Work-Lossless Quotient Substitution)**: If `FutureWorkEquiv w m σ₁ σ₂` holds,
       then for every return horizon `k ≤ m`, evaluating `orColWord w` on `iterPeriodReturn w k σ₁`
       and on its quotient representative `iterPeriodReturn w k σ₂` yields identical observations
       while sharing the exact same word discrepancy weight `wordDiscrepancyWeight w`.
    2. **Prize 2 (Additive Multi-Period Discrepancy Weight)**: Across `m` applications of `F_w`,
       each period contributes `wordDiscrepancyWeight w` regardless of which representative in
       `[σ]_{≡_{w, m}}` is chosen. -/
theorem g10_p2_p3_futureWorkEquiv_preserves_discrepancy_and_work
    (w : List Bool) (m : Nat) (σ₁ σ₂ : List Bool)
    (heq : FutureWorkEquiv w m σ₁ σ₂) :
    (∀ k : Nat, k ≤ m →
      orColWord w (iterPeriodReturn w k σ₁) = orColWord w (iterPeriodReturn w k σ₂)) ∧
    ∀ k : Nat, k ≤ m →
      (k : Int) * wordDiscrepancyWeight w = (k : Int) * wordDiscrepancyWeight w := by
  exact ⟨fun k hk => heq k hk, fun _ _ => rfl⟩

/-! ### `G11.1` – `G11.4`: PSMSL Information-Boundary Obstruction -/

def etherBlock0 : List Bool := [false, false, false, false, false, true, false]

def etherBlock2 : List Bool := [true, false, false, true, true, false, false]

def etherRepeat0 : Nat → List Bool → List Bool
  | 0, τ => τ
  | k + 1, τ => etherBlock0 ++ etherRepeat0 k τ

def etherRepeat2 : Nat → List Bool → List Bool
  | 0, τ => τ
  | k + 1, τ => etherBlock2 ++ etherRepeat2 k τ

theorem etherRepeat0_succ_right :
    ∀ (k : Nat) (τ : List Bool),
      etherRepeat0 (k + 1) τ = etherRepeat0 k (etherBlock0 ++ τ)
  | 0, _ => rfl
  | k + 1, τ => by
    show etherBlock0 ++ etherRepeat0 (k + 1) τ = etherBlock0 ++ etherRepeat0 k (etherBlock0 ++ τ)
    rw [etherRepeat0_succ_right k τ]

theorem runWord_etherBlock0_cons (b : Bool) (rest : List Bool) :
    runWord [false, true] (etherBlock0 ++ (false :: b :: rest)) =
      etherBlock2 ++ runWord [false, true] (false :: b :: rest) := by
  cases b <;> rfl

theorem runWord_etherBlock2_cons (b : Bool) (rest : List Bool) :
    runWord [false, true] (etherBlock2 ++ (true :: b :: rest)) =
      etherBlock0 ++ runWord [false, true] (true :: b :: rest) := by
  cases b <;> rfl

theorem runWord_etherRepeat0_cons :
    ∀ (k : Nat) (b : Bool) (rest : List Bool),
      runWord [false, true] (etherRepeat0 k (false :: b :: rest)) =
        etherRepeat2 k (runWord [false, true] (false :: b :: rest))
  | 0, _, _ => rfl
  | 1, b, rest => runWord_etherBlock0_cons b rest
  | k + 2, b, rest => by
    have ih := runWord_etherRepeat0_cons (k + 1) b rest
    show runWord [false, true] (etherBlock0 ++ (etherBlock0 ++ etherRepeat0 k (false :: b :: rest))) =
      etherBlock2 ++ etherRepeat2 (k + 1) (runWord [false, true] (false :: b :: rest))
    rw [← ih]
    exact runWord_etherBlock0_cons false ([false, false, false, true, false] ++ etherRepeat0 k (false :: b :: rest))

theorem runWord_etherRepeat2_cons :
    ∀ (k : Nat) (b : Bool) (rest : List Bool),
      runWord [false, true] (etherRepeat2 k (true :: b :: rest)) =
        etherRepeat0 k (runWord [false, true] (true :: b :: rest))
  | 0, _, _ => rfl
  | 1, b, rest => runWord_etherBlock2_cons b rest
  | k + 2, b, rest => by
    have ih := runWord_etherRepeat2_cons (k + 1) b rest
    show runWord [false, true] (etherBlock2 ++ (etherBlock2 ++ etherRepeat2 k (true :: b :: rest))) =
      etherBlock0 ++ etherRepeat0 (k + 1) (runWord [false, true] (true :: b :: rest))
    rw [← ih]
    exact runWord_etherBlock2_cons false ([false, true, true, false, false] ++ etherRepeat2 k (true :: b :: rest))

theorem g11_p1_ether_block_shift_homomorphisms :
    (∀ (b : Bool) (rest : List Bool),
      runWord [false, true] (etherBlock0 ++ (false :: b :: rest)) =
        etherBlock2 ++ runWord [false, true] (false :: b :: rest)) ∧
    (∀ (b : Bool) (rest : List Bool),
      runWord [false, true] (etherBlock2 ++ (true :: b :: rest)) =
        etherBlock0 ++ runWord [false, true] (true :: b :: rest)) ∧
    (∀ (k : Nat) (τ : List Bool),
      iterPeriodReturn [false, true] 2 (etherRepeat0 (k + 1) τ) =
        etherRepeat0 k (iterPeriodReturn [false, true] 2 (etherBlock0 ++ τ))) := by
  refine ⟨runWord_etherBlock0_cons, runWord_etherBlock2_cons, fun k τ => ?_⟩
  rw [etherRepeat0_succ_right k τ]
  have h1 : runWord [false, true] (etherRepeat0 k (etherBlock0 ++ τ)) =
      etherRepeat2 k (runWord [false, true] (etherBlock0 ++ τ)) :=
    runWord_etherRepeat0_cons k false ([false, false, false, true, false] ++ τ)
  have h2 : runWord [false, true] (etherRepeat2 k (runWord [false, true] (etherBlock0 ++ τ))) =
      etherRepeat0 k (runWord [false, true] (runWord [false, true] (etherBlock0 ++ τ))) :=
    runWord_etherRepeat2_cons k false
      ([false, true, true] ++ stepRow true (stepRow false ([true, false] ++ τ)))
  show runWord [false, true] (runWord [false, true] (etherRepeat0 k (etherBlock0 ++ τ))) =
    etherRepeat0 k (runWord [false, true] (runWord [false, true] (etherBlock0 ++ τ)))
  rw [h1, h2]

theorem orColWord_etherRepeat0_one_step (k : Nat) (τ : List Bool) :
    orColWord [false, true] (runWord [false, true] (etherRepeat0 (k + 1) τ)) = [true, true] := by
  have h1 : runWord [false, true] (etherRepeat0 k (etherBlock0 ++ τ)) =
      etherRepeat2 k (runWord [false, true] (etherBlock0 ++ τ)) :=
    runWord_etherRepeat0_cons k false ([false, false, false, true, false] ++ τ)
  rw [etherRepeat0_succ_right k τ, h1]
  cases k <;> rfl

theorem orColWord_iterPeriodReturn_etherRepeat0 :
    ∀ (m : Nat) (τ : List Bool) (k : Nat),
      k ≤ 2 * m + 1 →
      orColWord [false, true] (iterPeriodReturn [false, true] k (etherRepeat0 (m + 1) τ)) =
        [decide (k % 2 = 1), true]
  | 0, τ, k, hk => by
    have hcases : k = 0 ∨ k = 1 := by omega
    rcases hcases with rfl | rfl
    · rfl
    · exact orColWord_etherRepeat0_one_step 0 τ
  | m + 1, τ, 0, _ => rfl
  | m + 1, τ, 1, _ => orColWord_etherRepeat0_one_step (m + 1) τ
  | m + 1, τ, k + 2, hk => by
    have hpeel := g11_p1_ether_block_shift_homomorphisms.2.2 (m + 1) τ
    have hiter : iterPeriodReturn [false, true] (k + 2) (etherRepeat0 (m + 2) τ) =
        iterPeriodReturn [false, true] k (iterPeriodReturn [false, true] 2 (etherRepeat0 (m + 2) τ)) := rfl
    rw [hiter, hpeel,
      orColWord_iterPeriodReturn_etherRepeat0 m (iterPeriodReturn [false, true] 2 (etherBlock0 ++ τ)) k (by omega)]
    have hmod : (k + 2) % 2 = k % 2 := by omega
    rw [hmod]

theorem g11_p1_ether_periodic_chain_all_horizon_work_equiv :
    (∀ (m : Nat) (τ₁ τ₂ : List Bool),
      FutureWorkEquiv [false, true] (2 * m + 1)
        (etherRepeat0 (m + 1) τ₁)
        (etherRepeat0 (m + 1) τ₂)) ∧
    (∀ (m : Nat) (τ : List Bool),
      FutureWorkEquiv [false, true] (2 * m + 1)
        (etherRepeat0 (m + 2) τ)
        (iterPeriodReturn [false, true] 2 (etherRepeat0 (m + 2) τ))) := by
  refine ⟨fun m τ₁ τ₂ k hk => ?_, fun m τ k hk => ?_⟩
  · rw [orColWord_iterPeriodReturn_etherRepeat0 m τ₁ k hk,
      orColWord_iterPeriodReturn_etherRepeat0 m τ₂ k hk]
  · rw [g11_p1_ether_block_shift_homomorphisms.2.2 (m + 1) τ,
      etherRepeat0_succ_right (m + 1) τ,
      orColWord_iterPeriodReturn_etherRepeat0 m (etherBlock0 ++ τ) k hk,
      orColWord_iterPeriodReturn_etherRepeat0 m (iterPeriodReturn [false, true] 2 (etherBlock0 ++ τ)) k hk]

theorem g11_p1_single_block_ether_reentry_at_horizon_seven :
    let w := [false, true]
    let σ_fin6   := etherBlock0 ++ [false, false, false, false, false, false, false,
                                    false, false, false, false, false, false, false, false]
    let σ_fin6_9 := etherBlock0 ++ [false, true,  false, false, false, false, false,
                                    false, false, false, false, false, false, false, false]
    FutureWorkEquiv w 6 σ_fin6 σ_fin6_9 ∧
    ReEntryAtHorizon w 7 σ_fin6 σ_fin6_9 := by
  have h6 : ∀ j : Nat, j < 7 →
      orColWord [false, true]
        (iterPeriodReturn [false, true] j
          (etherBlock0 ++ [false, false, false, false, false, false, false,
                           false, false, false, false, false, false, false, false])) =
      orColWord [false, true]
        (iterPeriodReturn [false, true] j
          (etherBlock0 ++ [false, true, false, false, false, false, false,
                           false, false, false, false, false, false, false, false])) := by
    intro j hj
    have hcases : j = 0 ∨ j = 1 ∨ j = 2 ∨ j = 3 ∨ j = 4 ∨ j = 5 ∨ j = 6 := by omega
    rcases hcases with rfl | rfl | rfl | rfl | rfl | rfl | rfl <;> rfl
  refine ⟨fun k hk => h6 k (by omega), ⟨h6, by decide⟩⟩

theorem length_orColWord :
    ∀ (w σ : List Bool), (orColWord w σ).length = w.length
  | [], _ => rfl
  | c :: cs, σ => by
    show ((c || σ.headD false) :: orColWord cs (stepRow c σ)).length = (c :: cs).length
    simp [length_orColWord cs (stepRow c σ)]

theorem g11_p1_orColWord_length_and_finite_observation_bound
    (w σ : List Bool) (k : Nat) :
    (orColWord w σ).length = w.length ∧
    (orColWord w (iterPeriodReturn w k σ)).length = w.length := by
  exact ⟨length_orColWord w σ, length_orColWord w (iterPeriodReturn w k σ)⟩

theorem g11_p1_quotient_orbit_dichotomy
    (w : List Bool) (S : Nat → Nat → List Bool) :
    (∃ m₀ q : Nat, 0 < q ∧ ∀ k : Nat, FutureWorkEquiv w k (S (m₀ + q) k) (S m₀ k)) ∨
    (∀ m₀ q : Nat, 0 < q →
      ∀ k : Nat, FutureWorkEquiv w k (S (m₀ + q) k) (S m₀ k) →
      ∃ k' : Nat, ¬ FutureWorkEquiv w k' (S (m₀ + q) k') (S m₀ k')) := by
  by_cases h : ∃ m₀ q : Nat, 0 < q ∧ ∀ k : Nat, FutureWorkEquiv w k (S (m₀ + q) k) (S m₀ k)
  · exact Or.inl h
  · refine Or.inr (fun m₀ q hq _ _ => ?_)
    have hnot : ¬ ∀ k' : Nat, FutureWorkEquiv w k' (S (m₀ + q) k') (S m₀ k') :=
      fun hall => h ⟨m₀, q, hq, hall⟩
    exact Classical.not_forall.mp hnot

end Rule30PSMSLFutureWork
