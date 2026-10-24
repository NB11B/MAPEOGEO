import Rule30ClosureCore

/-!
# `R30-CLOSE-001` Track A — Left-Side Reconstruction & Phase Constraints (`Rule30LeftReconstruction.lean`)

Establishes the formal Track A left-reconstruction theorems:
1. **`stepLeftRow_rowAtLeft` & `runLeftWord_rowAtLeft` (`EXACT`):**
   Proves that the forward left-half word operator `runLeftWord (col0Word t L)` acting on the
   finite left-boundary prefix `rowAtLeft t (-1) (n + L)` computes the exact left-half state
   `rowAtLeft (t + L) (-1) n` with zero dependency on the right half (`p ≥ 1`).
2. **`left_black_step_screened_forcing` (`EXACT`):**
   At every step `t` where `Rule30Prize.center t = true`, right-neighbor screening (`true || r = true`)
   eliminates column `1` from the center update and forces `cell t (-1) = !Rule30Prize.center (t + 1)`.
3. **`left_effective_boundary_autonomous_step` (`EXACT`):**
   Whenever `center t && center (t + 1) = false` (no two consecutive black center cells), column `-1`
   steps as an autonomous zero-boundary left half: `cell (t + 1) (-1) = xor (cell t (-2)) (cell t (-1))`.
4. **`no_eventually_all_white_center`, `no_eventually_all_black_center`, and
   `no_period_one_center_all_transients` (`EXACT`):**
   Unconditionally rules out all-white center tails, all-black center tails, and period `P = 1`
   for **every** transient `T : Nat`.
5. **`left_light_cone_support_bound` (`EXACT`):**
   Certifies that at any time `T : Nat`, the single-seed left half has exact frontier `cell T (-T) = true`
   and zero exterior `∀ p < -T, cell T p = false`.
-/

namespace Rule30ProofClosure

open Ruliology.CellularAutomata
open Ruliology.CellularAutomata.Rule30Prize
open Ruliology.CellularAutomata.Rule30Realization
open Ruliology.CellularAutomata.Rule30Jen
open Ruliology.CellularAutomata.Rule30MaskedJen
open Ruliology.CellularAutomata.Rule30Diagonals
open Ruliology.CellularAutomata.Rule30BlackRuns

/-- **Track A (`EXACT`) — One-Step Left-Half Evolution Soundness (`stepLeftRow_rowAtLeft`)**:
    For every time `t : Nat`, width `n : Nat`, and column `p : Int`, stepping `rowAtLeft t p (n + 1)`
    with right-neighbor `cell t (p + 1)` produces `rowAtLeft (t + 1) p n`. -/
theorem stepLeftRow_rowAtLeft (t : Nat) :
    ∀ (n : Nat) (p : Int),
      stepLeftRow (cell t (p + 1)) (rowAtLeft t p (n + 1)) = rowAtLeft (t + 1) p n
  | 0, _ => rfl
  | n + 1, p => by
    have ih := stepLeftRow_rowAtLeft t n (p - 1)
    rw [show p - 1 + 1 = p by omega] at ih
    show rule (cell t (p - 1)) (cell t p) (cell t (p + 1)) ::
        stepLeftRow (cell t p) (rowAtLeft t (p - 1) (n + 1)) =
      cell (t + 1) p :: rowAtLeft (t + 1) (p - 1) n
    rw [ih]
    rfl

/-- **Track A (`EXACT`) — Multi-Step Left-Half Word Operator Soundness (`runLeftWord_rowAtLeft`)**:
    Driving the finite left-half prefix `rowAtLeft t (-1) (n + L)` at `p = 0` by `col0Word t L`
    produces the exact left-half prefix `rowAtLeft (t + L) (-1) n`, proving that forward evolution
    of the negative half-line `p ≤ -1` is 100% determined by `rowAtLeft t (-1)` and the center
    column `col0Word t L`. -/
theorem runLeftWord_rowAtLeft :
    ∀ (L n t : Nat),
      runLeftWord (col0Word t L) (rowAtLeft t (-1) (n + L)) = rowAtLeft (t + L) (-1) n
  | 0, n, t => by simp [col0Word, runLeftWord]
  | L + 1, n, t => by
    have hstep : stepLeftRow (cell t 0) (rowAtLeft t (-1) (n + L + 1)) = rowAtLeft (t + 1) (-1) (n + L) := by
      have h := stepLeftRow_rowAtLeft t (n + L) (-1)
      rwa [show (-1 : Int) + 1 = 0 by rfl] at h
    have ih := runLeftWord_rowAtLeft L n (t + 1)
    show runLeftWord (col0Word (t + 1) L) (stepLeftRow (cell t 0) (rowAtLeft t (-1) (n + (L + 1)))) =
      rowAtLeft (t + (L + 1)) (-1) n
    rw [show n + (L + 1) = n + L + 1 by omega, hstep, ih,
      show t + 1 + L = t + (L + 1) by omega]

/-- **Track A (`EXACT`) — Pure Left-Half Black-Step Screened Forcing (`left_black_step_screened_forcing`)**:
    Whenever the center cell `Rule30Prize.center t` is black (`true`), PSMSL right-neighbor
    screening (`true || cell t 1 = true`) eliminates the right half from the center update and
    forces `cell t (-1) = !Rule30Prize.center (t + 1)`. -/
theorem left_black_step_screened_forcing (t : Nat)
    (hb : Rule30Prize.center t = true) :
    cell t (-1) = !Rule30Prize.center (t + 1) ∧
    Rule30Prize.center (t + 1) = !cell t (-1) := by
  have hl := left_of_black t 0 hb
  rw [show (0 : Int) - 1 = -1 by rfl] at hl
  unfold Rule30Prize.center at *
  refine ⟨hl, ?_⟩
  rw [hl, Bool.not_not]

/-- **Track A (`EXACT`) — Autonomous Zero-Boundary Step Under `11`-Free Center
    (`left_effective_boundary_autonomous_step`)**:
    Whenever `Rule30Prize.center t && Rule30Prize.center (t + 1) = false`, column `-1` evolves
    with an effective white right boundary `false` at column `0`:
    `cell (t + 1) (-1) = xor (cell t (-2)) (cell t (-1))`. -/
theorem left_effective_boundary_autonomous_step (t : Nat)
    (hno11 : (Rule30Prize.center t && Rule30Prize.center (t + 1)) = false) :
    cell (t + 1) (-1) = xor (cell t (-2)) (cell t (-1)) := by
  have heff := effective_step t
  rw [hno11] at heff
  unfold rule at heff
  simpa using heff

/-- **Track A (`EXACT`) — Unconditional Exclusion of Eventually All-White Center
    (`no_eventually_all_white_center`)**:
    For every transient `T : Nat`, the center column cannot remain white (`false`) for all `t ≥ T`. -/
theorem no_eventually_all_white_center (T : Nat) :
    ¬ ∀ t : Nat, T ≤ t → Rule30Prize.center t = false := by
  intro hw
  exact center_not_eventually_constant ⟨T, false, hw⟩

/-- **Track A (`EXACT`) — Unconditional Exclusion of Eventually All-Black Center
    (`no_eventually_all_black_center`)**:
    For every transient `T : Nat`, the center column cannot remain black (`true`) for all `t ≥ T`. -/
theorem no_eventually_all_black_center (T : Nat) :
    ¬ ∀ t : Nat, T ≤ t → Rule30Prize.center t = true := by
  intro hb
  exact center_not_eventually_constant ⟨T, true, hb⟩

/-- **Track A (`EXACT`) — Unconditional Exclusion of Period `P = 1` for All Transients
    (`no_period_one_center_all_transients`)**:
    For every transient `T : Nat`, the center column cannot be periodic with period `P = 1` from `T` on. -/
theorem no_period_one_center_all_transients (T : Nat) :
    ¬ ∀ t : Nat, T ≤ t → Rule30Prize.center (t + 1) = Rule30Prize.center t := by
  intro h1
  exact center_not_eventually_period_one ⟨T, h1⟩

/-- **Track A (`EXACT`) — Every Periodic Center Window Contains Both Black and White Cells
    (`periodic_center_has_black_and_white_in_every_period`)**:
    If `Rule30Prize.center` is `P`-periodic from `T` on (`P > 0`), then every period window
    `[t₁, t₁ + P)` (`t₁ ≥ T`) contains at least one black step (`center (t₁ + s_b) = true`) and
    at least one white step (`center (t₁ + s_w) = false`). -/
theorem periodic_center_has_black_and_white_in_every_period
    (T P t₁ : Nat)
    (hP : 0 < P)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₁ : T ≤ t₁) :
    (∃ sb : Nat, sb < P ∧ Rule30Prize.center (t₁ + sb) = true) ∧
    (∃ sw : Nat, sw < P ∧ Rule30Prize.center (t₁ + sw) = false) := by
  have hperk : ∀ k t, T ≤ t → Rule30Prize.center (t + k * P) = Rule30Prize.center t :=
    periodic_mul hper
  constructor
  · apply Classical.byContradiction
    intro hnob
    have hallw : ∀ s, s < P → Rule30Prize.center (t₁ + s) = false := by
      intro s hs
      cases hc : Rule30Prize.center (t₁ + s)
      · rfl
      · exact absurd ⟨s, hs, hc⟩ hnob
    apply no_eventually_all_white_center t₁
    intro t ht
    have hdm := Nat.div_add_mod (t - t₁) P
    have hmod := Nat.mod_lt (t - t₁) hP
    have h1 := hperk ((t - t₁) / P) (t₁ + (t - t₁) % P) (by omega)
    have h2 := hallw ((t - t₁) % P) hmod
    have hcomm : P * ((t - t₁) / P) = (t - t₁) / P * P := Nat.mul_comm _ _
    rw [show t₁ + (t - t₁) % P + (t - t₁) / P * P = t by omega] at h1
    rw [h1, h2]
  · apply Classical.byContradiction
    intro hnow
    have hallb : ∀ s, s < P → Rule30Prize.center (t₁ + s) = true := by
      intro s hs
      cases hc : Rule30Prize.center (t₁ + s)
      · exact absurd ⟨s, hs, hc⟩ hnow
      · rfl
    apply no_eventually_all_black_center t₁
    intro t ht
    have hdm := Nat.div_add_mod (t - t₁) P
    have hmod := Nat.mod_lt (t - t₁) hP
    have h1 := hperk ((t - t₁) / P) (t₁ + (t - t₁) % P) (by omega)
    have h2 := hallb ((t - t₁) % P) hmod
    have hcomm : P * ((t - t₁) / P) = (t - t₁) / P * P := Nat.mul_comm _ _
    rw [show t₁ + (t - t₁) % P + (t - t₁) / P * P = t by omega] at h1
    rw [h1, h2]

/-- **Track A (`EXACT`) — Single-Seed Left Light-Cone Support Bound (`left_light_cone_support_bound`)**:
    At every step `T : Nat` on the single-seed trajectory:
    1. The left light-cone frontier cell `p = -T` is black (`cell T (-T) = true`), and
    2. Every cell strictly to the left of `-T` (`p < -T`) is white (`cell T p = false`). -/
theorem left_light_cone_support_bound (T : Nat) :
    cell T (-(T : Int)) = true ∧
    ∀ p : Int, p < -(T : Int) → cell T p = false :=
  ⟨cell_left_edge T, fun p hp => cell_eq_false_of_lt T p hp⟩

end Rule30ProofClosure
