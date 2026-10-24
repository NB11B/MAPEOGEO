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

/-- **Track A (`EXACT`) — Permanent Whiteness of Left Diagonal `D 2` (`left_diag_D2_eq_false`)**:
    For every `t : Nat`, `D 2 (t + 2) = false` follows directly from `D_step 0`, `D_zero`, and `D_one`. -/
theorem left_diag_D2_eq_false (t : Nat) : D 2 (t + 2) = false := by
  rw [show t + 2 = (t + 1) + 1 by omega, D_step 0 (t + 1), D_zero (t + 1), D_one t]
  rfl

/-- **Track A (`EXACT`, New in `R30-CERT-001`) — Permanent Blackness of Left Diagonal `D 4`
    (`left_diag_D4_eq_true`)**:
    For every `t : Nat`, the 5th left diagonal `D 4 (t + 3) = cell (t + 3) (- (t : Int) + 1)`
    is permanently black (`true`), screening out `D 5` in the subsequent diagonal recurrence. -/
theorem left_diag_D4_eq_true : ∀ t : Nat, D 4 (t + 3) = true
  | 0 => rfl
  | t + 1 => by
    have ih := left_diag_D4_eq_true t
    have hstep : D 4 (t + 1 + 3) = xor (D 2 (t + 3)) (D 3 (t + 3) || D 4 (t + 3)) := by
      rw [show t + 1 + 3 = (t + 3) + 1 by omega]
      exact D_step 2 (t + 3)
    have hd2 : D 2 (t + 3) = false := by
      rw [show t + 3 = (t + 1) + 2 by omega]
      exact left_diag_D2_eq_false (t + 1)
    rw [hstep, hd2, ih]
    cases D 3 (t + 3) <;> rfl

/-- **Track A (`EXACT`, New in `R30-CERT-001`) — Diagonal Screening Law for `D 5`
    (`left_diag_D5_eq_not_D3`)**:
    Because `D 4 (t + 3) = true` permanently screens `D 5 (t + 3)` inside `D 4 || D 5 = true`,
    the 6th left diagonal `D 5 (t + 4)` is identically `!D 3 (t + 3)` (preventing period doubling
    from period 2 to period 4). -/
theorem left_diag_D5_eq_not_D3 (t : Nat) :
    D 5 (t + 4) = !D 3 (t + 3) := by
  have hstep : D 5 (t + 4) = xor (D 3 (t + 3)) (D 4 (t + 3) || D 5 (t + 3)) := by
    rw [show t + 4 = (t + 3) + 1 by omega]
    exact D_step 3 (t + 3)
  rw [hstep, left_diag_D4_eq_true t]
  cases D 3 (t + 3) <;> cases D 5 (t + 3) <;> rfl

/-- **Track A (`EXACT`, New in `R30-CERT-001`) — Law L2: Double-Black Center Screening to Depth `-2`
    (`double_black_step_depth2_forcing`)**:
    Whenever `center t = true` and `center (t + 1) = true` (a local `11` center pattern),
    PSMSL screening eliminates the right half down to column `p = -2`, forcing
    `cell t (-1) = false`, `cell (t + 1) (-1) = !center (t + 2)`, and `cell t (-2) = center (t + 2)`. -/
theorem double_black_step_depth2_forcing (t : Nat)
    (hb0 : Rule30Prize.center t = true)
    (hb1 : Rule30Prize.center (t + 1) = true) :
    cell t (-1) = false ∧
    cell (t + 1) (-1) = !Rule30Prize.center (t + 2) ∧
    cell t (-2) = Rule30Prize.center (t + 2) := by
  have hm1_t : cell t (-1) = false := by
    have h := (left_black_step_screened_forcing t hb0).1
    rw [hb1] at h
    exact h
  have hm1_t1 : cell (t + 1) (-1) = !Rule30Prize.center (t + 2) :=
    (left_black_step_screened_forcing (t + 1) hb1).1
  have hstep : cell (t + 1) (-1) = rule (cell t (-2)) (cell t (-1)) (cell t 0) := rfl
  have hc0 : cell t 0 = true := hb0
  rw [hm1_t, hc0, hm1_t1] at hstep
  unfold rule at hstep
  refine ⟨hm1_t, hm1_t1, ?_⟩
  revert hstep
  cases cell t (-2) <;> cases Rule30Prize.center (t + 2) <;> decide

/-- **Track A (`EXACT`, New in `R30-CERT-001`) — Law L3: `101` Pattern Right-Half Variable Cancellation
    (`local_101_pattern_conserved_left_xor`)**:
    Whenever `(center t, center (t + 1), center (t + 2)) = (true, false, true)` (a local `101` pattern):
    1. `cell t (-1) = true`,
    2. `cell t (-2) = !cell (t + 1) (-1)`,
    3. `cell t (-3) = xor (cell (t + 1) (-1)) (center (t + 3))`, and
    4. The unscreened right-boundary variable `cell (t + 1) (-1)` cancels identically out of
       `xor (cell t (-2)) (cell t (-3)) = !center (t + 3)`. -/
theorem local_101_pattern_conserved_left_xor (t : Nat)
    (hc0 : Rule30Prize.center t = true)
    (hc1 : Rule30Prize.center (t + 1) = false)
    (hc2 : Rule30Prize.center (t + 2) = true) :
    cell t (-1) = true ∧
    cell t (-2) = !cell (t + 1) (-1) ∧
    cell t (-3) = xor (cell (t + 1) (-1)) (Rule30Prize.center (t + 3)) ∧
    xor (cell t (-2)) (cell t (-3)) = !Rule30Prize.center (t + 3) := by
  have hm1_t : cell t (-1) = true := by
    have h := (left_black_step_screened_forcing t hc0).1
    rw [hc1] at h
    exact h
  have hm1_t2 : cell (t + 2) (-1) = !Rule30Prize.center (t + 3) :=
    (left_black_step_screened_forcing (t + 2) hc2).1
  have hstep_m1_t : cell (t + 1) (-1) = rule (cell t (-2)) (cell t (-1)) (cell t 0) := rfl
  have hc0' : cell t 0 = true := hc0
  rw [hm1_t, hc0'] at hstep_m1_t
  unfold rule at hstep_m1_t
  have hm2_t : cell t (-2) = !cell (t + 1) (-1) := by
    revert hstep_m1_t
    cases cell t (-2) <;> cases cell (t + 1) (-1) <;> decide
  have hstep_m1_t1 : cell (t + 2) (-1) =
      rule (cell (t + 1) (-2)) (cell (t + 1) (-1)) (cell (t + 1) 0) := rfl
  have hc1' : cell (t + 1) 0 = false := hc1
  rw [hc1', hm1_t2] at hstep_m1_t1
  unfold rule at hstep_m1_t1
  have hstep_m2_t : cell (t + 1) (-2) = rule (cell t (-3)) (cell t (-2)) (cell t (-1)) := rfl
  rw [hm1_t] at hstep_m2_t
  unfold rule at hstep_m2_t
  have hm3_t : cell t (-3) = xor (cell (t + 1) (-1)) (Rule30Prize.center (t + 3)) := by
    revert hstep_m1_t1 hstep_m2_t
    cases cell t (-3) <;> cases cell t (-2) <;> cases cell (t + 1) (-2) <;>
      cases cell (t + 1) (-1) <;> cases Rule30Prize.center (t + 3) <;> decide
  have hxor : xor (cell t (-2)) (cell t (-3)) = !Rule30Prize.center (t + 3) := by
    rw [hm2_t, hm3_t]
    cases cell (t + 1) (-1) <;> cases Rule30Prize.center (t + 3) <;> rfl
  exact ⟨hm1_t, hm2_t, hm3_t, hxor⟩

/-- **Track A (`EXACT`, New in `R30-CERT-001`) — Law L3b: `1010` Complement Cancellation at Depth `-4`
    (`local_1010_complement_cancellation_depth4`)**:
    Whenever `(center t, center (t + 1), center (t + 2), center (t + 3)) = (true, false, true, false)`,
    columns `-3` and `-2` at step `t` are exact Boolean complements (`cell t (-3) = !cell t (-2)`),
    collapsing the nonlinear disjunction `cell t (-3) || cell t (-2) = true` to a constant and
    linearizing depth `-4`: `cell t (-4) = !cell (t + 1) (-3)`. -/
theorem local_1010_complement_cancellation_depth4 (t : Nat)
    (hc0 : Rule30Prize.center t = true)
    (hc1 : Rule30Prize.center (t + 1) = false)
    (hc2 : Rule30Prize.center (t + 2) = true)
    (hc3 : Rule30Prize.center (t + 3) = false) :
    cell t (-3) = !cell t (-2) ∧
    (cell t (-3) || cell t (-2)) = true ∧
    cell t (-4) = !cell (t + 1) (-3) := by
  rcases local_101_pattern_conserved_left_xor t hc0 hc1 hc2 with ⟨_, hm2, hm3, _⟩
  rw [hc3] at hm3
  have hcomp : cell t (-3) = !cell t (-2) := by
    rw [hm2, hm3]
    cases cell (t + 1) (-1) <;> rfl
  have hor : (cell t (-3) || cell t (-2)) = true := by
    rw [hcomp]
    cases cell t (-2) <;> rfl
  have hstep_m3 : cell (t + 1) (-3) = rule (cell t (-4)) (cell t (-3)) (cell t (-2)) := rfl
  unfold rule at hstep_m3
  rw [hor] at hstep_m3
  have hm4 : cell t (-4) = !cell (t + 1) (-3) := by
    revert hstep_m3
    cases cell t (-4) <;> cases cell (t + 1) (-3) <;> decide
  exact ⟨hcomp, hor, hm4⟩

end Rule30ProofClosure
