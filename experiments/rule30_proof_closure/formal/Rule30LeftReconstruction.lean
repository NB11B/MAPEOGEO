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

/-- **Track A (`EXACT`, `R30-TRANSPORT-001`) — Alternating Step Law for `D 3`
    (`left_diag_D3_succ`)**:
    For every `t : Nat`, `D 3 (t + 3) = !D 3 (t + 2)` follows from `D_step 1`, `D_one`, and
    `left_diag_D2_eq_false`. -/
theorem left_diag_D3_succ (t : Nat) : D 3 (t + 3) = !D 3 (t + 2) := by
  rw [show t + 3 = (t + 2) + 1 by omega, D_step 1 (t + 2), D_one (t + 1), left_diag_D2_eq_false t]
  cases D 3 (t + 2) <;> rfl

/-- **Track A (`EXACT`, New in `R30-TRANSPORT-001`) — Universal 6-Step Column-Onset Signature
    (`universal_column_onset_signature`)**:
    For every spatial depth `k : Nat`, the vertical time trace of column `p = -k` across its first
    6 steps inside the light cone (`t = k .. k + 5`) satisfies the universal invariant:
    1. `cell k (-k) = true`,
    2. `cell (k + 1) (-k) = true`,
    3. `cell (k + 2) (-k) = false`,
    4. `cell (k + 4) (-k) = true`, and
    5. `cell (k + 5) (-k) = cell (k + 3) (-k)`. -/
theorem universal_column_onset_signature (k : Nat) :
    cell k (-(k : Int)) = true ∧
    cell (k + 1) (-(k : Int)) = true ∧
    cell (k + 2) (-(k : Int)) = false ∧
    cell (k + 4) (-(k : Int)) = true ∧
    cell (k + 5) (-(k : Int)) = cell (k + 3) (-(k : Int)) := by
  have h0 : cell k (-(k : Int)) = D 0 k := by unfold D; exact cell_congr (by omega)
  have h1 : cell (k + 1) (-(k : Int)) = D 1 (k + 1) := by unfold D; exact cell_congr (by omega)
  have h2 : cell (k + 2) (-(k : Int)) = D 2 (k + 2) := by unfold D; exact cell_congr (by omega)
  have h3 : cell (k + 3) (-(k : Int)) = D 3 (k + 3) := by unfold D; exact cell_congr (by omega)
  have h4 : cell (k + 4) (-(k : Int)) = D 4 (k + 4) := by unfold D; exact cell_congr (by omega)
  have h5 : cell (k + 5) (-(k : Int)) = D 5 (k + 5) := by unfold D; exact cell_congr (by omega)
  have hd4 : D 4 (k + 4) = true := by
    rw [show k + 4 = (k + 1) + 3 by omega]
    exact left_diag_D4_eq_true (k + 1)
  have hd5 : D 5 (k + 5) = D 3 (k + 3) := by
    have hs5 : D 5 (k + 5) = !D 3 (k + 4) := by
      rw [show k + 5 = (k + 1) + 4 by omega, show k + 4 = (k + 1) + 3 by omega]
      exact left_diag_D5_eq_not_D3 (k + 1)
    have hs3 : D 3 (k + 4) = !D 3 (k + 3) := by
      rw [show k + 4 = (k + 1) + 3 by omega, show k + 3 = (k + 1) + 2 by omega]
      exact left_diag_D3_succ (k + 1)
    rw [hs5, hs3, Bool.not_not]
  rw [h0, h1, h2, h3, h4, h5, D_zero k, D_one k, left_diag_D2_eq_false k, hd4, hd5]
  exact ⟨rfl, rfl, rfl, rfl, rfl⟩

/-- **Track A (`EXACT`, New in `R30-TRANSPORT-001`) — 6-Case Spatial Relation Transport Theorem
    (`spatial_transport_step_dichotomy`)**:
    Certifies the 6 exact algebraic cases by which a relation at spatial depth `(p, p + 1)`
    transports one column outward to `p - 1` without increasing polynomial degree:
    1. `T_black_left`: `cell t p = true → cell t (p - 1) = !cell (t + 1) p`
    2. `T_black_right`: `cell t (p + 1) = true → cell t (p - 1) = !cell (t + 1) p`
    3. `T_white_left`: `cell t p = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t (p + 1))`
    4. `T_white_right`: `cell t (p + 1) = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t p)`
    5. `T_comp` (`xor = true`): `xor (cell t p) (cell t (p + 1)) = true → cell t (p - 1) = !cell (t + 1) p`
    6. `T_idemp` (`xor = false`): `xor (cell t p) (cell t (p + 1)) = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t p)` -/
theorem spatial_transport_step_dichotomy (t : Nat) (p : Int) :
    (cell t p = true → cell t (p - 1) = !cell (t + 1) p) ∧
    (cell t (p + 1) = true → cell t (p - 1) = !cell (t + 1) p) ∧
    (cell t p = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t (p + 1))) ∧
    (cell t (p + 1) = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t p)) ∧
    (xor (cell t p) (cell t (p + 1)) = true → cell t (p - 1) = !cell (t + 1) p) ∧
    (xor (cell t p) (cell t (p + 1)) = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t p)) := by
  have hstep : cell (t + 1) p = rule (cell t (p - 1)) (cell t p) (cell t (p + 1)) := rfl
  unfold rule at hstep
  revert hstep
  cases cell (t + 1) p <;> cases cell t (p - 1) <;> cases cell t p <;> cases cell t (p + 1) <;> decide

/-- **Track A (`EXACT`, New in `R30-TRANSPORT-001`) — Pure Structural Exclusion of `1010` at `t = 3`
    via Spatial Transport + Column-Onset Signature (`transport_onset_excludes_1010_at_t3`)**:
    Demonstrates with zero brute-force trajectory evaluation how composing Law L3
    (`local_101_pattern_conserved_left_xor`) with `universal_column_onset_signature` at depths
    `k = 2` and `k = 3` directly refutes `(center 3, center 4, center 5, center 6) = (true, false, true, false)`:
    - Law L3 transports `(center 3..6) = (1, 0, 1, 0)` to `xor (cell 3 (-2)) (cell 3 (-3)) = true`,
    - Whereas `universal_column_onset_signature 2` gives `cell 3 (-2) = true` and
      `universal_column_onset_signature 3` gives `cell 3 (-3) = true`, so `xor true true = false`. -/
theorem transport_onset_excludes_1010_at_t3 :
    ¬ (Rule30Prize.center 3 = true ∧
       Rule30Prize.center 4 = false ∧
       Rule30Prize.center 5 = true ∧
       Rule30Prize.center 6 = false) := by
  rintro ⟨hc3, hc4, hc5, hc6⟩
  have hxor := (local_101_pattern_conserved_left_xor 3 hc3 hc4 hc5).2.2.2
  rw [hc6] at hxor
  have hm2 : cell 3 (-2) = true := (universal_column_onset_signature 2).2.1
  have hm3 : cell 3 (-3) = true := (universal_column_onset_signature 3).1
  rw [hm2, hm3] at hxor
  contradiction

/-- **Track A (`EXACT`, New in `R30-SPATIOTEMPORAL-001`) — Cumulative Spatiotemporal Characteristic OR-Flux
    (`leftCharacteristicFlux`)**:
    Accumulates the sideways disjunctions `cell (t + j) (-d + 1 + j) || cell (t + j) (-d + 2 + j)`
    along the characteristic ray from the center column `(t + d, 0)` outward to `(t, -d)`. -/
def leftCharacteristicFlux : Nat → Nat → Bool
  | _, 0 => false
  | t, d + 1 =>
      xor (leftCharacteristicFlux (t + 1) d)
          (cell t (-(d : Int)) || cell t (-(d : Int) + 1))

/-- **Track A (`EXACT`, New in `R30-SPATIOTEMPORAL-001`) — Universal Arbitrary-Depth Spatiotemporal
    Transport Law (`cell_neg_eq_center_xor_characteristicFlux`)**:
    Proves by induction on spatial depth `d : Nat` that for every time `t : Nat` and depth `d : Nat`,
    `cell t (-d) = xor (center (t + d)) (leftCharacteristicFlux t d)` and dual
    `leftCharacteristicFlux t d = xor (center (t + d)) (cell t (-d))`. -/
theorem cell_neg_eq_center_xor_characteristicFlux :
    ∀ (d t : Nat),
      cell t (-(d : Int)) = xor (Rule30Prize.center (t + d)) (leftCharacteristicFlux t d) ∧
      leftCharacteristicFlux t d = xor (Rule30Prize.center (t + d)) (cell t (-(d : Int)))
  | 0, t => by
      have h0 : cell t (-(↑(0 : Nat) : Int)) = Rule30Prize.center t := rfl
      rw [h0, Nat.add_zero]
      unfold leftCharacteristicFlux
      cases Rule30Prize.center t <;> decide
  | d + 1, t => by
      have ih := (cell_neg_eq_center_xor_characteristicFlux d (t + 1)).1
      have hcongr : cell t (-(↑(d + 1) : Int)) = cell t (-(d : Int) - 1) :=
        cell_congr (by omega)
      have hleft := cell_left' t (-(d : Int))
      unfold orCol at hleft
      have hcenter : Rule30Prize.center (t + 1 + d) = Rule30Prize.center (t + (d + 1)) := by
        rw [show t + 1 + d = t + (d + 1) by omega]
      have hflux : leftCharacteristicFlux t (d + 1) =
          xor (leftCharacteristicFlux (t + 1) d) (cell t (-(d : Int)) || cell t (-(d : Int) + 1)) := rfl
      rw [hcongr, hleft, ih, hcenter, hflux]
      cases Rule30Prize.center (t + (d + 1)) <;>
        cases leftCharacteristicFlux (t + 1) d <;>
        cases (cell t (-(d : Int)) || cell t (-(d : Int) + 1)) <;> decide

/-- **Track A (`EXACT`, New in `R30-SPATIOTEMPORAL-001`) — Universal Spatiotemporal Characteristic-Flux
    Boundary Signature (`universal_characteristic_flux_onset_laws`)**:
    Combining `cell_neg_eq_center_xor_characteristicFlux` with `universal_column_onset_signature`
    fixes the cumulative `k`-step characteristic OR-flux at the single-seed column onset `t = k .. k + 5`
    in terms of the shifted center bits `center (2k + m)` for every spatial depth `k : Nat`:
    1. `leftCharacteristicFlux k k = !center (k + k)`,
    2. `leftCharacteristicFlux (k + 1) k = !center (k + 1 + k)`,
    3. `leftCharacteristicFlux (k + 2) k = center (k + 2 + k)`,
    4. `leftCharacteristicFlux (k + 4) k = !center (k + 4 + k)`, and
    5. `xor (leftCharacteristicFlux (k + 5) k) (leftCharacteristicFlux (k + 3) k) =
        xor (center (k + 5 + k)) (center (k + 3 + k))`. -/
theorem universal_characteristic_flux_onset_laws (k : Nat) :
    leftCharacteristicFlux k k = !Rule30Prize.center (k + k) ∧
    leftCharacteristicFlux (k + 1) k = !Rule30Prize.center (k + 1 + k) ∧
    leftCharacteristicFlux (k + 2) k = Rule30Prize.center (k + 2 + k) ∧
    leftCharacteristicFlux (k + 4) k = !Rule30Prize.center (k + 4 + k) ∧
    xor (leftCharacteristicFlux (k + 5) k) (leftCharacteristicFlux (k + 3) k) =
      xor (Rule30Prize.center (k + 5 + k)) (Rule30Prize.center (k + 3 + k)) := by
  rcases universal_column_onset_signature k with ⟨h0, h1, h2, h4, h53⟩
  have f0 := (cell_neg_eq_center_xor_characteristicFlux k k).2
  have f1 := (cell_neg_eq_center_xor_characteristicFlux k (k + 1)).2
  have f2 := (cell_neg_eq_center_xor_characteristicFlux k (k + 2)).2
  have f3 := (cell_neg_eq_center_xor_characteristicFlux k (k + 3)).2
  have f4 := (cell_neg_eq_center_xor_characteristicFlux k (k + 4)).2
  have f5 := (cell_neg_eq_center_xor_characteristicFlux k (k + 5)).2
  rw [h0] at f0
  rw [h1] at f1
  rw [h2] at f2
  rw [h4] at f4
  rw [h53] at f5
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [f0]; cases Rule30Prize.center (k + k) <;> rfl
  · rw [f1]; cases Rule30Prize.center (k + 1 + k) <;> rfl
  · rw [f2]; cases Rule30Prize.center (k + 2 + k) <;> rfl
  · rw [f4]; cases Rule30Prize.center (k + 4 + k) <;> rfl
  · rw [f5, f3]
    cases Rule30Prize.center (k + 5 + k) <;>
      cases Rule30Prize.center (k + 3 + k) <;>
      cases cell (k + 3) (-(k : Int)) <;> rfl

/-- **Track A/C (`EXACT`, New in `R30-SPATIOTEMPORAL-001`) — Periodic Center Forces Spatial Depth-Periodicity
    of Cumulative Characteristic OR-Flux at Column Onset
    (`periodic_center_forces_characteristic_flux_depth_periodicity`)**:
    Formalizes the spatiotemporal transport invariant independently of any contradiction premise:
    if `center` is periodic with period `P` for `t ≥ T`, then for every spatial depth `k ≥ T`,
    advancing the spatial depth from `k` to `k + P` shifts the characteristic apex time by `2P`
    and forces the cumulative `k`-column nonlinear OR-flux `leftCharacteristicFlux (k + m) k` to be
    strictly invariant under `k ↦ k + P` across all onset offsets `m ∈ {0, 1, 2, 4}` and the `(3, 5)` pair. -/
theorem periodic_center_forces_characteristic_flux_depth_periodicity
    (T P k : Nat)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (hk : T ≤ k) :
    leftCharacteristicFlux (k + P) (k + P) = leftCharacteristicFlux k k ∧
    leftCharacteristicFlux (k + P + 1) (k + P) = leftCharacteristicFlux (k + 1) k ∧
    leftCharacteristicFlux (k + P + 2) (k + P) = leftCharacteristicFlux (k + 2) k ∧
    leftCharacteristicFlux (k + P + 4) (k + P) = leftCharacteristicFlux (k + 4) k ∧
    xor (leftCharacteristicFlux (k + P + 5) (k + P)) (leftCharacteristicFlux (k + P + 3) (k + P)) =
      xor (leftCharacteristicFlux (k + 5) k) (leftCharacteristicFlux (k + 3) k) := by
  have shift2P : ∀ m : Nat, Rule30Prize.center (k + P + m + (k + P)) = Rule30Prize.center (k + m + k) := by
    intro m
    have heq1 : k + P + m + (k + P) = (k + m + k + P) + P := by omega
    have heq2 : k + m + k + P = (k + m + k) + P := by omega
    rw [heq1, hper (k + m + k + P) (by omega), heq2, hper (k + m + k) (by omega)]
  rcases universal_characteristic_flux_onset_laws (k + P) with ⟨u0, u1, u2, u4, u53⟩
  rcases universal_characteristic_flux_onset_laws k with ⟨v0, v1, v2, v4, v53⟩
  have s0 : Rule30Prize.center (k + P + (k + P)) = Rule30Prize.center (k + k) := by
    have h := shift2P 0
    rw [show k + P + 0 + (k + P) = k + P + (k + P) by omega,
        show k + 0 + k = k + k by omega] at h
    exact h
  rw [u0, v0, s0, u1, v1, shift2P 1, u2, v2, shift2P 2, u4, v4, shift2P 4, u53, v53, shift2P 5, shift2P 3]
  exact ⟨rfl, rfl, rfl, rfl, rfl⟩

/-- **Track A/B (`EXACT`, New in `R30-SPATIOTEMPORAL-001`) — Spatiotemporal Quadratic Cross-Term
    Cancellation at Depth `-5` (`spatiotemporal_101010_quadratic_cancellation_depth5`)**:
    Proves that while a single-time relation grammar breaks at depth `-4` on odd steps because
    `cell (t + 1) (-4) = (!cell (t + 1) (-1)) && (!cell (t + 3) (-1))` is a degree-2 quadratic product
    of two distinct temporal offsets `t + 1` and `t + 3`, in the spatiotemporal relation algebra
    that quadratic cross-term cancels identically against `cell t (-4) || cell t (-3)` at depth `-5`,
    restoring pure degree-1 linearity: `cell t (-5) = cell (t + 1) (-1) = cell t (-3)`. -/
theorem spatiotemporal_101010_quadratic_cancellation_depth5 (t : Nat)
    (hc0 : Rule30Prize.center t = true)
    (hc1 : Rule30Prize.center (t + 1) = false)
    (hc2 : Rule30Prize.center (t + 2) = true)
    (hc3 : Rule30Prize.center (t + 3) = false)
    (hc4 : Rule30Prize.center (t + 4) = true)
    (hc5 : Rule30Prize.center (t + 5) = false) :
    cell t (-3) = cell (t + 1) (-1) ∧
    cell t (-4) = !cell (t + 3) (-1) ∧
    cell (t + 1) (-4) = ((!cell (t + 1) (-1)) && (!cell (t + 3) (-1))) ∧
    cell t (-5) = cell (t + 1) (-1) ∧
    cell t (-5) = cell t (-3) := by
  rcases local_101_pattern_conserved_left_xor t hc0 hc1 hc2 with ⟨_, hm2_t, hm3_t, _⟩
  rw [hc3] at hm3_t
  have hm3_t' : cell t (-3) = cell (t + 1) (-1) := by
    rw [hm3_t]; cases cell (t + 1) (-1) <;> rfl
  have hc2_shift : Rule30Prize.center (t + 2) = true := hc2
  have hc3_shift : Rule30Prize.center (t + 2 + 1) = false := by
    rw [show t + 2 + 1 = t + 3 by omega]; exact hc3
  have hc4_shift : Rule30Prize.center (t + 2 + 2) = true := by
    rw [show t + 2 + 2 = t + 4 by omega]; exact hc4
  rcases local_101_pattern_conserved_left_xor (t + 2) hc2_shift hc3_shift hc4_shift with
    ⟨_, hm2_t2, hm3_t2, _⟩
  have hc5_shift : Rule30Prize.center (t + 2 + 3) = false := by
    rw [show t + 2 + 3 = t + 5 by omega]; exact hc5
  rw [hc5_shift] at hm3_t2
  have hm1_t2 : cell (t + 2) (-1) = true := by
    have h := (left_black_step_screened_forcing (t + 2) hc2).1
    rw [show t + 2 + 1 = t + 3 by omega, hc3] at h
    exact h
  have hstep_m1_t1 : cell (t + 2) (-1) =
      rule (cell (t + 1) (-2)) (cell (t + 1) (-1)) (cell (t + 1) 0) := rfl
  have hc1' : cell (t + 1) 0 = false := hc1
  rw [hm1_t2, hc1'] at hstep_m1_t1
  unfold rule at hstep_m1_t1
  have hm2_t1 : cell (t + 1) (-2) = !cell (t + 1) (-1) := by
    revert hstep_m1_t1
    cases cell (t + 1) (-2) <;> cases cell (t + 1) (-1) <;> decide
  have hstep_m2_t1 : cell (t + 2) (-2) =
      rule (cell (t + 1) (-3)) (cell (t + 1) (-2)) (cell (t + 1) (-1)) := rfl
  rw [hm2_t2, hm2_t1] at hstep_m2_t1
  unfold rule at hstep_m2_t1
  have hm3_t1 : cell (t + 1) (-3) = cell (t + 2 + 1) (-1) := by
    revert hstep_m2_t1
    cases cell (t + 1) (-3) <;> cases cell (t + 1) (-1) <;> cases cell (t + 2 + 1) (-1) <;> decide
  have hm3_t1' : cell (t + 1) (-3) = cell (t + 3) (-1) := by
    rw [show t + 2 + 1 = t + 3 by omega] at hm3_t1; exact hm3_t1
  have hm4_t : cell t (-4) = !cell (t + 3) (-1) := by
    have h4 := (local_1010_complement_cancellation_depth4 t hc0 hc1 hc2 hc3).2.2
    rw [hm3_t1'] at h4; exact h4
  have hstep_m3_t1 : cell (t + 2) (-3) =
      rule (cell (t + 1) (-4)) (cell (t + 1) (-3)) (cell (t + 1) (-2)) := rfl
  rw [show t + 2 + 1 = t + 3 by omega] at hm3_t2
  rw [hm3_t2, hm3_t1', hm2_t1] at hstep_m3_t1
  unfold rule at hstep_m3_t1
  have hm4_t1 : cell (t + 1) (-4) = ((!cell (t + 1) (-1)) && (!cell (t + 3) (-1))) := by
    revert hstep_m3_t1
    cases cell (t + 1) (-4) <;> cases cell (t + 1) (-1) <;> cases cell (t + 3) (-1) <;> decide
  have hstep_m4_t : cell (t + 1) (-4) =
      rule (cell t (-5)) (cell t (-4)) (cell t (-3)) := rfl
  rw [hm4_t1, hm4_t, hm3_t'] at hstep_m4_t
  unfold rule at hstep_m4_t
  have hm5_t : cell t (-5) = cell (t + 1) (-1) := by
    revert hstep_m4_t
    cases cell t (-5) <;> cases cell (t + 1) (-1) <;> cases cell (t + 3) (-1) <;> decide
  exact ⟨hm3_t', hm4_t, hm4_t1, hm5_t, hm5_t.trans hm3_t'.symm⟩

/-- **Track A (`EXACT`, New in `R30-FLUX-CORR-001`) — Strictly Interior Characteristic OR-Flux
    (`interiorCharacteristicFlux`)**:
    Accumulates the strictly left-half disjunctions `cell (t + j) (-(d + 1) + 1 + j) || cell (t + j) (-(d + 1) + 2 + j)`
    for `j = 0 .. d - 1` along the characteristic ray `t + (d + 1) = N`, excluding the leading
    center-right boundary step `orCol 0 (t + d)` at `(t + d, 0)`. -/
def interiorCharacteristicFlux : Nat → Nat → Bool
  | _, 0 => false
  | t, d + 1 =>
      xor (interiorCharacteristicFlux (t + 1) d)
          (cell t (-(↑(d + 1) : Int)) || cell t (-(↑(d + 1) : Int) + 1))

/-- **Track A/B (`EXACT`, New in `R30-FLUX-CORR-001`) — All-Depth Spatiotemporal Isolation of the
    Leading PSMSL Right-Boundary Observation (`characteristicFlux_decomp_leading_orCol`)**:
    Proves by induction on `d : Nat` that for every `t, d : Nat`, `leftCharacteristicFlux t (d + 1)`
    splits into the leading PSMSL right-boundary work `orCol 0 (t + d)` at apex time `t + d` XORed
    with the strictly lower-offset interior flux `interiorCharacteristicFlux t d`:
    1. `leftCharacteristicFlux t (d + 1) = xor (orCol 0 (t + d)) (interiorCharacteristicFlux t d)`
    2. `cell t (-(d + 1)) = xor (center (t + d + 1)) (xor (orCol 0 (t + d)) (interiorCharacteristicFlux t d))` -/
theorem characteristicFlux_decomp_leading_orCol :
    ∀ (d t : Nat),
      leftCharacteristicFlux t (d + 1) =
        xor (orCol 0 (t + d)) (interiorCharacteristicFlux t d) ∧
      cell t (-(↑(d + 1) : Int)) =
        xor (Rule30Prize.center (t + d + 1))
            (xor (orCol 0 (t + d)) (interiorCharacteristicFlux t d))
  | 0, t => by
      have hf1 : leftCharacteristicFlux t 1 =
          xor (leftCharacteristicFlux (t + 1) 0)
              (cell t (-(↑(0 : Nat) : Int)) || cell t (-(↑(0 : Nat) : Int) + 1)) := rfl
      have hf0 : leftCharacteristicFlux (t + 1) 0 = false := rfl
      have hi0 : interiorCharacteristicFlux t 0 = false := rfl
      have hor : (cell t (-(↑(0 : Nat) : Int)) || cell t (-(↑(0 : Nat) : Int) + 1)) =
          orCol 0 (t + 0) := by
        rw [Nat.add_zero]; rfl
      have hdecomp : leftCharacteristicFlux t 1 =
          xor (orCol 0 (t + 0)) (interiorCharacteristicFlux t 0) := by
        rw [hf1, hf0, hi0, hor]
        cases orCol 0 (t + 0) <;> rfl
      have hcell := (cell_neg_eq_center_xor_characteristicFlux 1 t).1
      have hcenter : Rule30Prize.center (t + 1) = Rule30Prize.center (t + 0 + 1) := by
        rw [Nat.add_zero]
      rw [hdecomp, hcenter] at hcell
      exact ⟨hdecomp, hcell⟩
  | d + 1, t => by
      have ih := (characteristicFlux_decomp_leading_orCol d (t + 1)).1
      have hf : leftCharacteristicFlux t (d + 2) =
          xor (leftCharacteristicFlux (t + 1) (d + 1))
              (cell t (-(↑(d + 1) : Int)) || cell t (-(↑(d + 1) : Int) + 1)) := rfl
      have hi : interiorCharacteristicFlux t (d + 1) =
          xor (interiorCharacteristicFlux (t + 1) d)
              (cell t (-(↑(d + 1) : Int)) || cell t (-(↑(d + 1) : Int) + 1)) := rfl
      have hor_shift : orCol 0 (t + 1 + d) = orCol 0 (t + (d + 1)) := by
        rw [show t + 1 + d = t + (d + 1) by omega]
      have hdecomp : leftCharacteristicFlux t (d + 2) =
          xor (orCol 0 (t + (d + 1))) (interiorCharacteristicFlux t (d + 1)) := by
        rw [hf, ih, hor_shift, hi]
        cases orCol 0 (t + (d + 1)) <;>
          cases interiorCharacteristicFlux (t + 1) d <;>
          cases (cell t (-(↑(d + 1) : Int)) || cell t (-(↑(d + 1) : Int) + 1)) <;> rfl
      have hcell := (cell_neg_eq_center_xor_characteristicFlux (d + 2) t).1
      have hcenter : Rule30Prize.center (t + (d + 2)) = Rule30Prize.center (t + (d + 1) + 1) := by
        rw [show t + (d + 2) = t + (d + 1) + 1 by omega]
      rw [hdecomp, hcenter] at hcell
      exact ⟨hdecomp, hcell⟩

/-- **Track A/B (`EXACT`, New in `R30-FLUX-CORR-001`) — All-Depth Isolation of `orCol 0` at the
    Single-Seed Wavefront Onset (`spatiotemporal_leading_orCol_onset_isolation`)**:
    Evaluates `characteristicFlux_decomp_leading_orCol` at `(t = k + 1, d = k)` (where
    `cell (k + 1) (-(k + 1)) = true`) and `(t = k + 2, d = k)` (where `cell (k + 2) (-(k + 1)) = true`),
    proving that for every `k : Nat`, the PSMSL right-boundary work `orCol 0` at both odd (`2k + 1`)
    and even (`2k + 2`) apex times equals `!center (τ + 1) xor interiorCharacteristicFlux`:
    1. `orCol 0 (k + 1 + k) = xor (!center (k + 1 + k + 1)) (interiorCharacteristicFlux (k + 1) k)`
    2. `orCol 0 (k + 2 + k) = xor (!center (k + 2 + k + 1)) (interiorCharacteristicFlux (k + 2) k)` -/
theorem spatiotemporal_leading_orCol_onset_isolation (k : Nat) :
    orCol 0 (k + 1 + k) =
      xor (!Rule30Prize.center (k + 1 + k + 1)) (interiorCharacteristicFlux (k + 1) k) ∧
    orCol 0 (k + 2 + k) =
      xor (!Rule30Prize.center (k + 2 + k + 1)) (interiorCharacteristicFlux (k + 2) k) := by
  have h_odd := (characteristicFlux_decomp_leading_orCol k (k + 1)).2
  have h_even := (characteristicFlux_decomp_leading_orCol k (k + 2)).2
  have hc_odd : cell (k + 1) (-(↑(k + 1) : Int)) = true :=
    (universal_column_onset_signature (k + 1)).1
  have hc_even : cell (k + 2) (-(↑(k + 1) : Int)) = true := by
    have h := (universal_column_onset_signature (k + 1)).2.1
    rw [show k + 1 + 1 = k + 2 by omega] at h
    exact h
  rw [hc_odd] at h_odd
  rw [hc_even] at h_even
  refine ⟨?_, ?_⟩
  · revert h_odd
    cases orCol 0 (k + 1 + k) <;>
      cases Rule30Prize.center (k + 1 + k + 1) <;>
      cases interiorCharacteristicFlux (k + 1) k <;> decide
  · revert h_even
    cases orCol 0 (k + 2 + k) <;>
      cases Rule30Prize.center (k + 2 + k + 1) <;>
      cases interiorCharacteristicFlux (k + 2) k <;> decide

/-- **Track A/B/C (`EXACT`, New in `R30-FLUX-CORR-001`) — PSMSL Screening vs. Leading-Variable
    Isolation Dichotomy at Every Characteristic Ray Apex (`spatiotemporal_black_white_apex_dichotomy`)**:
    Combines PSMSL right-boundary screening (`orCol 0 τ = center τ || cell τ 1`) with
    `spatiotemporal_leading_orCol_onset_isolation` to establish the two exact regimes at every depth `k`:
    - **Black apex step (`center τ = true`):** `orCol 0 τ = true` screens out the leading right-half
      variable `cell τ 1`, forcing the lower-offset interior flux to match `center (τ + 1)` directly:
      `interiorCharacteristicFlux = center (τ + 1)`.
    - **White apex step (`center τ = false`):** `orCol 0 τ = cell τ 1` isolates the leading right-half
      variable linearly with coefficient `1`:
      `cell τ 1 = xor (!center (τ + 1)) interiorCharacteristicFlux`. -/
theorem spatiotemporal_black_white_apex_dichotomy (k : Nat) :
    (Rule30Prize.center (k + 1 + k) = true →
      interiorCharacteristicFlux (k + 1) k = Rule30Prize.center (k + 1 + k + 1)) ∧
    (Rule30Prize.center (k + 1 + k) = false →
      cell (k + 1 + k) 1 =
        xor (!Rule30Prize.center (k + 1 + k + 1)) (interiorCharacteristicFlux (k + 1) k)) ∧
    (Rule30Prize.center (k + 2 + k) = true →
      interiorCharacteristicFlux (k + 2) k = Rule30Prize.center (k + 2 + k + 1)) ∧
    (Rule30Prize.center (k + 2 + k) = false →
      cell (k + 2 + k) 1 =
        xor (!Rule30Prize.center (k + 2 + k + 1)) (interiorCharacteristicFlux (k + 2) k)) := by
  rcases spatiotemporal_leading_orCol_onset_isolation k with ⟨h_odd, h_even⟩
  have hor_odd : orCol 0 (k + 1 + k) =
      (Rule30Prize.center (k + 1 + k) || cell (k + 1 + k) 1) := rfl
  have hor_even : orCol 0 (k + 2 + k) =
      (Rule30Prize.center (k + 2 + k) || cell (k + 2 + k) 1) := rfl
  rw [hor_odd] at h_odd
  rw [hor_even] at h_even
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro hb
    rw [hb] at h_odd
    revert h_odd
    cases cell (k + 1 + k) 1 <;>
      cases Rule30Prize.center (k + 1 + k + 1) <;>
      cases interiorCharacteristicFlux (k + 1) k <;> decide
  · intro hw
    rw [hw] at h_odd
    revert h_odd
    cases cell (k + 1 + k) 1 <;>
      cases Rule30Prize.center (k + 1 + k + 1) <;>
      cases interiorCharacteristicFlux (k + 1) k <;> decide
  · intro hb
    rw [hb] at h_even
    revert h_even
    cases cell (k + 2 + k) 1 <;>
      cases Rule30Prize.center (k + 2 + k + 1) <;>
      cases interiorCharacteristicFlux (k + 2) k <;> decide
  · intro hw
    rw [hw] at h_even
    revert h_even
    cases cell (k + 2 + k) 1 <;>
      cases Rule30Prize.center (k + 2 + k + 1) <;>
      cases interiorCharacteristicFlux (k + 2) k <;> decide

theorem left_diag_D3_parity :
    ∀ k : Nat,
      D 3 (k + 2) = decide (k % 2 = 1) ∧
      D 3 (k + 3) = decide (k % 2 = 0)
  | 0 => ⟨rfl, rfl⟩
  | k + 1 => by
      rcases left_diag_D3_parity k with ⟨_, hk3⟩
      have h1 : D 3 (k + 1 + 2) = D 3 (k + 3) := by
        rw [show k + 1 + 2 = k + 3 by omega]
      have h2 : D 3 (k + 1 + 3) = !D 3 (k + 1 + 2) := by
        rw [show k + 1 + 3 = (k + 1) + 3 by omega, show k + 1 + 2 = (k + 1) + 2 by omega]
        exact left_diag_D3_succ (k + 1)
      have hp1 : decide ((k + 1) % 2 = 1) = decide (k % 2 = 0) := by
        rcases Nat.mod_two_eq_zero_or_one k with h | h
        · have h' : (k + 1) % 2 = 1 := by omega
          simp [h, h']
        · have h' : (k + 1) % 2 = 0 := by omega
          simp [h, h']
      have hp0 : decide ((k + 1) % 2 = 0) = !decide (k % 2 = 0) := by
        rcases Nat.mod_two_eq_zero_or_one k with h | h
        · have h' : (k + 1) % 2 = 1 := by omega
          simp [h, h']
        · have h' : (k + 1) % 2 = 0 := by omega
          simp [h, h']
      rw [h1, hk3, hp1, h2, h1, hk3, hp0]
      exact ⟨rfl, rfl⟩

/-- **Track A (`EXACT`, New in `R30-UNIVERSAL-001`) — Exact Closed-Form 6-Step Column-Onset Signature
    (`universal_column_onset_exact_6step`)**:
    Upgrades `universal_column_onset_signature` by proving the exact closed-form parity values
    `cell (k + 3) (-k) = decide (k % 2 = 0)` (`D 3 (k + 3)`) and
    `cell (k + 5) (-k) = decide (k % 2 = 0)` (`D 5 (k + 5)`) for every spatial depth `k : Nat`. -/
theorem universal_column_onset_exact_6step (k : Nat) :
    cell k (-(k : Int)) = true ∧
    cell (k + 1) (-(k : Int)) = true ∧
    cell (k + 2) (-(k : Int)) = false ∧
    cell (k + 3) (-(k : Int)) = decide (k % 2 = 0) ∧
    cell (k + 4) (-(k : Int)) = true ∧
    cell (k + 5) (-(k : Int)) = decide (k % 2 = 0) := by
  rcases universal_column_onset_signature k with ⟨h0, h1, h2, h4, h53⟩
  have h3_eq : cell (k + 3) (-(k : Int)) = D 3 (k + 3) := by
    unfold D; exact cell_congr (by omega)
  have hd3 : D 3 (k + 3) = decide (k % 2 = 0) := (left_diag_D3_parity k).2
  have h3 : cell (k + 3) (-(k : Int)) = decide (k % 2 = 0) := h3_eq.trans hd3
  have h5 : cell (k + 5) (-(k : Int)) = decide (k % 2 = 0) := h53.trans h3
  exact ⟨h0, h1, h2, h3, h4, h5⟩

/-- **Track A/C (`EXACT`, New in `R30-UNIVERSAL-001`) — Odd Period Forces Spatial Depth Anti-Periodicity
    of Characteristic OR-Flux at Onset Offsets `3` and `5`
    (`odd_period_forces_characteristic_flux_anti_periodicity`)**:
    For every transient `T : Nat`, every odd period `P : Nat` (`P % 2 = 1`), and every depth `k ≥ T`,
    advancing the spatial depth `k ↦ k + P` shifts the center apex time by `2P` (preserving `center`)
    while flipping the onset diagonal parity `(k + P) % 2 ≠ k % 2`, forcing `leftCharacteristicFlux`
    at onset offsets `m = 3` and `m = 5` to negate under `k ↦ k + P`. -/
theorem odd_period_forces_characteristic_flux_anti_periodicity
    (T P k : Nat)
    (hodd : P % 2 = 1)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (hk : T ≤ k) :
    leftCharacteristicFlux (k + P + 3) (k + P) = !leftCharacteristicFlux (k + 3) k ∧
    leftCharacteristicFlux (k + P + 5) (k + P) = !leftCharacteristicFlux (k + 5) k := by
  have shift2P : ∀ m : Nat, Rule30Prize.center (k + P + m + (k + P)) = Rule30Prize.center (k + m + k) := by
    intro m
    have heq1 : k + P + m + (k + P) = (k + m + k + P) + P := by omega
    have heq2 : k + m + k + P = (k + m + k) + P := by omega
    rw [heq1, hper (k + m + k + P) (by omega), heq2, hper (k + m + k) (by omega)]
  have hpar_flip : decide ((k + P) % 2 = 0) = !decide (k % 2 = 0) := by
    rcases Nat.mod_two_eq_zero_or_one k with hk0 | hk1
    · have hkp : (k + P) % 2 = 1 := by omega
      simp [hk0, hkp]
    · have hkp : (k + P) % 2 = 0 := by omega
      simp [hk1, hkp]
  have f3_kp := (cell_neg_eq_center_xor_characteristicFlux (k + P) (k + P + 3)).2
  have f3_k := (cell_neg_eq_center_xor_characteristicFlux k (k + 3)).2
  have f5_kp := (cell_neg_eq_center_xor_characteristicFlux (k + P) (k + P + 5)).2
  have f5_k := (cell_neg_eq_center_xor_characteristicFlux k (k + 5)).2
  have c3_kp := (universal_column_onset_exact_6step (k + P)).2.2.2.1
  have c3_k := (universal_column_onset_exact_6step k).2.2.2.1
  have c5_kp := (universal_column_onset_exact_6step (k + P)).2.2.2.2.2
  have c5_k := (universal_column_onset_exact_6step k).2.2.2.2.2
  rw [c3_kp, hpar_flip, shift2P 3] at f3_kp
  rw [c3_k] at f3_k
  rw [c5_kp, hpar_flip, shift2P 5] at f5_kp
  rw [c5_k] at f5_k
  rw [f3_kp, f3_k, f5_kp, f5_k]
  refine ⟨?_, ?_⟩
  · cases Rule30Prize.center (k + 3 + k) <;> cases decide (k % 2 = 0) <;> rfl
  · cases Rule30Prize.center (k + 5 + k) <;> cases decide (k % 2 = 0) <;> rfl

/-- **Track A/B (`EXACT`, New in `R30-UNIVERSAL-001`) — Law L4: Double-White Center Screening via
    Column-`1` Persistence (`double_white_step_depth2_forcing`)**:
    Whenever `center t = false` and `center (t + 1) = false` (a local `00` center pattern):
    1. `cell t (-1) = cell t 1`,
    2. PSMSL screening at column `1` (`true || cell t 2 = true`) forces `cell t 1 = true → cell (t + 1) 1 = true`,
    3. Consequently, `cell t (-1) = true` forces `cell (t + 1) (-1) = !center (t + 2)` and
       `cell t (-2) = center (t + 2)`, and
    4. Unconditionally over `𝔽₂`, `(cell t (-1) && xor (cell (t + 1) (-1)) (!center (t + 2))) = false`
       and `(cell t (-1) && xor (cell t (-2)) (center (t + 2))) = false`. -/
theorem double_white_step_depth2_forcing (t : Nat)
    (hw0 : Rule30Prize.center t = false)
    (hw1 : Rule30Prize.center (t + 1) = false) :
    cell t (-1) = cell t 1 ∧
    (cell t 1 = true → cell (t + 1) 1 = true) ∧
    (cell t (-1) = true →
      cell (t + 1) (-1) = !Rule30Prize.center (t + 2) ∧
      cell t (-2) = Rule30Prize.center (t + 2)) ∧
    ((cell t (-1) && xor (cell (t + 1) (-1)) (!Rule30Prize.center (t + 2))) = false) ∧
    ((cell t (-1) && xor (cell t (-2)) (Rule30Prize.center (t + 2))) = false) := by
  have hm1_t : cell t (-1) = xor (cell (t + 1) 0) (cell t 0 || cell t 1) := by
    have h := cell_left t 0
    rwa [show (0 : Int) - 1 = -1 by rfl, show (0 : Int) + 1 = 1 by rfl] at h
  have hm1_t1 : cell (t + 1) (-1) = xor (cell (t + 2) 0) (cell (t + 1) 0 || cell (t + 1) 1) := by
    have h := cell_left (t + 1) 0
    rwa [show (0 : Int) - 1 = -1 by rfl, show (0 : Int) + 1 = 1 by rfl] at h
  have hr1_t1 : cell (t + 1) 1 = rule (cell t 0) (cell t 1) (cell t 2) := rfl
  have hstep_m1 : cell (t + 1) (-1) = rule (cell t (-2)) (cell t (-1)) (cell t 0) := rfl
  unfold Rule30Prize.center at hw0 hw1
  unfold Rule30Prize.center
  rw [hw0, hw1] at hm1_t
  rw [hw1] at hm1_t1
  rw [hw0] at hr1_t1
  rw [hw0] at hstep_m1
  unfold rule at hr1_t1 hstep_m1
  revert hm1_t hm1_t1 hr1_t1 hstep_m1
  cases cell t (-1) <;>
    cases cell (t + 1) (-1) <;>
    cases cell t (-2) <;>
    cases cell t 1 <;>
    cases cell (t + 1) 1 <;>
    cases cell t 2 <;>
    cases cell (t + 2) 0 <;> decide

/-- **Track A/B (`EXACT`, New in `R30-EXHAUST-001`) — Depth-`-4` Degree-`0` Constant Collapse for
    the Short-Run Period-`3` Blocks `0010010` and `0110110`
    (`spatiotemporal_001001_and_011011_depth4_constant_collapse`)**:
    Proves that for both fundamental period-`3` short-run center patterns:
    1. Under `0010010` (`(center t, ..., center (t + 6)) = (0, 0, 1, 0, 0, 1, 0)`), the quadratic
       cross-term `cell (t + 3) (-3) = !(cell (t + 3) (-1) && !cell (t + 4) (-1))` cancels
       identically against `cell (t + 2) (-3) || cell (t + 2) (-2)` at depth `-4`, forcing the
       degree-`0` constant `cell (t + 2) (-4) = false` (independent of all right-boundary bits `y_s`), and
    2. Under `0110110` (`(center t, ..., center (t + 6)) = (0, 1, 1, 0, 1, 1, 0)`), all boundary
       variables cancel at depth `-4`, forcing `cell (t + 1) (-4) = false` and `cell (t + 2) (-4) = true`. -/
theorem spatiotemporal_001001_and_011011_depth4_constant_collapse (t : Nat) :
    ((Rule30Prize.center t = false ∧
      Rule30Prize.center (t + 1) = false ∧
      Rule30Prize.center (t + 2) = true ∧
      Rule30Prize.center (t + 3) = false ∧
      Rule30Prize.center (t + 4) = false ∧
      Rule30Prize.center (t + 5) = true ∧
      Rule30Prize.center (t + 6) = false) →
      cell (t + 2) (-4) = false) ∧
    ((Rule30Prize.center t = false ∧
      Rule30Prize.center (t + 1) = true ∧
      Rule30Prize.center (t + 2) = true ∧
      Rule30Prize.center (t + 3) = false ∧
      Rule30Prize.center (t + 4) = true ∧
      Rule30Prize.center (t + 5) = true ∧
      Rule30Prize.center (t + 6) = false) →
      cell (t + 1) (-4) = false ∧ cell (t + 2) (-4) = true) := by
  refine ⟨?_, ?_⟩
  · rintro ⟨_, _, hc2, hc3, hc4, hc5, hc6⟩
    have hm1_t2 : cell (t + 2) (-1) = true := by
      have h := (left_black_step_screened_forcing (t + 2) hc2).1
      rw [show t + 2 + 1 = t + 3 by omega, hc3] at h
      exact h
    have hm1_t5 : cell (t + 5) (-1) = true := by
      have h := (left_black_step_screened_forcing (t + 5) hc5).1
      rw [show t + 5 + 1 = t + 6 by omega, hc6] at h
      exact h
    have s_m1_t2 : cell (t + 3) (-1) = rule (cell (t + 2) (-2)) (cell (t + 2) (-1)) (cell (t + 2) 0) := rfl
    have s_m1_t3 : cell (t + 4) (-1) = rule (cell (t + 3) (-2)) (cell (t + 3) (-1)) (cell (t + 3) 0) := rfl
    have s_m1_t4 : cell (t + 5) (-1) = rule (cell (t + 4) (-2)) (cell (t + 4) (-1)) (cell (t + 4) 0) := rfl
    have s_m2_t2 : cell (t + 3) (-2) = rule (cell (t + 2) (-3)) (cell (t + 2) (-2)) (cell (t + 2) (-1)) := rfl
    have s_m2_t3 : cell (t + 4) (-2) = rule (cell (t + 3) (-3)) (cell (t + 3) (-2)) (cell (t + 3) (-1)) := rfl
    have s_m3_t2 : cell (t + 3) (-3) = rule (cell (t + 2) (-4)) (cell (t + 2) (-3)) (cell (t + 2) (-2)) := rfl
    unfold Rule30Prize.center at hc2 hc3 hc4
    rw [hm1_t2, hc2] at s_m1_t2
    rw [hc3] at s_m1_t3
    rw [hm1_t5, hc4] at s_m1_t4
    rw [hm1_t2] at s_m2_t2
    unfold rule at s_m1_t2 s_m1_t3 s_m1_t4 s_m2_t2 s_m2_t3 s_m3_t2
    revert s_m1_t2 s_m1_t3 s_m1_t4 s_m2_t2 s_m2_t3 s_m3_t2
    cases cell (t + 3) (-1) <;>
      cases cell (t + 4) (-1) <;>
      cases cell (t + 2) (-2) <;>
      cases cell (t + 3) (-2) <;>
      cases cell (t + 4) (-2) <;>
      cases cell (t + 2) (-3) <;>
      cases cell (t + 3) (-3) <;>
      cases cell (t + 2) (-4) <;> decide
  · rintro ⟨_, hd1, hd2, hd3, hd4, hd5, hd6⟩
    have hdb1 := double_black_step_depth2_forcing (t + 1) hd1 (by rwa [show t + 1 + 1 = t + 2 by omega])
    rw [show t + 1 + 1 = t + 2 by omega, show t + 1 + 2 = t + 3 by omega, hd3] at hdb1
    rcases hdb1 with ⟨hm1_t1, hm1_t2, hm2_t1⟩
    have hdb4 := double_black_step_depth2_forcing (t + 4) hd4 (by rwa [show t + 4 + 1 = t + 5 by omega])
    rw [show t + 4 + 1 = t + 5 by omega, show t + 4 + 2 = t + 6 by omega, hd6] at hdb4
    rcases hdb4 with ⟨hm1_t4, _, hm2_t4⟩
    have s_m1_t2 : cell (t + 3) (-1) = rule (cell (t + 2) (-2)) (cell (t + 2) (-1)) (cell (t + 2) 0) := rfl
    have s_m1_t3 : cell (t + 4) (-1) = rule (cell (t + 3) (-2)) (cell (t + 3) (-1)) (cell (t + 3) 0) := rfl
    have s_m2_t1 : cell (t + 2) (-2) = rule (cell (t + 1) (-3)) (cell (t + 1) (-2)) (cell (t + 1) (-1)) := rfl
    have s_m2_t2 : cell (t + 3) (-2) = rule (cell (t + 2) (-3)) (cell (t + 2) (-2)) (cell (t + 2) (-1)) := rfl
    have s_m2_t3 : cell (t + 4) (-2) = rule (cell (t + 3) (-3)) (cell (t + 3) (-2)) (cell (t + 3) (-1)) := rfl
    have s_m3_t1 : cell (t + 2) (-3) = rule (cell (t + 1) (-4)) (cell (t + 1) (-3)) (cell (t + 1) (-2)) := rfl
    have s_m3_t2 : cell (t + 3) (-3) = rule (cell (t + 2) (-4)) (cell (t + 2) (-3)) (cell (t + 2) (-2)) := rfl
    unfold Rule30Prize.center at hd2 hd3
    rw [hm1_t2, hd2] at s_m1_t2
    rw [hm1_t4, hd3] at s_m1_t3
    rw [hm2_t1, hm1_t1] at s_m2_t1
    rw [hm1_t2] at s_m2_t2
    rw [hm2_t4] at s_m2_t3
    rw [hm2_t1] at s_m3_t1
    unfold rule at s_m1_t2 s_m1_t3 s_m2_t1 s_m2_t2 s_m2_t3 s_m3_t1 s_m3_t2
    revert s_m1_t2 s_m1_t3 s_m2_t1 s_m2_t2 s_m2_t3 s_m3_t1 s_m3_t2
    cases cell (t + 3) (-1) <;>
      cases cell (t + 2) (-2) <;>
      cases cell (t + 3) (-2) <;>
      cases cell (t + 1) (-3) <;>
      cases cell (t + 2) (-3) <;>
      cases cell (t + 3) (-3) <;>
      cases cell (t + 1) (-4) <;>
      cases cell (t + 2) (-4) <;> decide

/-- **`R30-REDUCTION-SOUNDNESS-001` (`EXACT`) — Family `1010` Depth-`-2` Vertical Pair Lock and
    Both-Phase Onset Exclusion (`orbit_1010_depth2_vertical_lock_and_onset_exclusion`)**:
    Proves that whenever `(center t, center (t+1), center (t+2), center (t+3)) = (true, false, true, false)`:
    1. Both `cell t (-2)` and `cell (t + 1) (-2)` equal `!cell (t + 1) (-1)`, forcing the exact
       tail-independent vertical equality `cell t (-2) = cell (t + 1) (-2)` at column `-2`, and
    2. Colliding this vertical equality with `universal_column_onset_exact_6step 2`
       (`cell 3 (-2) = true`, `cell 4 (-2) = false`, `cell 5 (-2) = true`) refutes `1010` at BOTH
       onset phases `t = 3` and `t = 4` with zero trajectory evaluation. -/
theorem orbit_1010_depth2_vertical_lock_and_onset_exclusion (t : Nat) :
    ((Rule30Prize.center t = true ∧
      Rule30Prize.center (t + 1) = false ∧
      Rule30Prize.center (t + 2) = true ∧
      Rule30Prize.center (t + 3) = false) →
      cell t (-2) = !cell (t + 1) (-1) ∧
      cell (t + 1) (-2) = !cell (t + 1) (-1) ∧
      cell t (-2) = cell (t + 1) (-2)) ∧
    ¬ (Rule30Prize.center 3 = true ∧
       Rule30Prize.center 4 = false ∧
       Rule30Prize.center 5 = true ∧
       Rule30Prize.center 6 = false) ∧
    ¬ (Rule30Prize.center 4 = true ∧
       Rule30Prize.center 5 = false ∧
       Rule30Prize.center 6 = true ∧
       Rule30Prize.center 7 = false) := by
  have hlock : ∀ τ : Nat,
      Rule30Prize.center τ = true →
      Rule30Prize.center (τ + 1) = false →
      Rule30Prize.center (τ + 2) = true →
      Rule30Prize.center (τ + 3) = false →
      cell τ (-2) = !cell (τ + 1) (-1) ∧
      cell (τ + 1) (-2) = !cell (τ + 1) (-1) ∧
      cell τ (-2) = cell (τ + 1) (-2) := by
    intro τ hc0 hc1 hc2 hc3
    have hm2_0 : cell τ (-2) = !cell (τ + 1) (-1) :=
      (local_101_pattern_conserved_left_xor τ hc0 hc1 hc2).2.1
    have hm1_2 : cell (τ + 2) (-1) = true := by
      have h := (left_black_step_screened_forcing (τ + 2) hc2).1
      rw [show τ + 2 + 1 = τ + 3 by omega, hc3] at h
      exact h
    have hstep : cell (τ + 2) (-1) = rule (cell (τ + 1) (-2)) (cell (τ + 1) (-1)) (cell (τ + 1) 0) := rfl
    have hc1' : cell (τ + 1) 0 = false := hc1
    rw [hm1_2, hc1'] at hstep
    unfold rule at hstep
    have hm2_1 : cell (τ + 1) (-2) = !cell (τ + 1) (-1) := by
      revert hstep
      cases cell (τ + 1) (-2) <;> cases cell (τ + 1) (-1) <;> decide
    exact ⟨hm2_0, hm2_1, hm2_0.trans hm2_1.symm⟩
  have c3 : cell 3 (-2) = true := (universal_column_onset_exact_6step 2).2.1
  have c4 : cell 4 (-2) = false := (universal_column_onset_exact_6step 2).2.2.1
  have c5 : cell 5 (-2) = true := (universal_column_onset_exact_6step 2).2.2.2.1
  refine ⟨fun ⟨hc0, hc1, hc2, hc3⟩ => hlock t hc0 hc1 hc2 hc3, ?_, ?_⟩
  · rintro ⟨hc3, hc4, hc5, hc6⟩
    have heq : cell 3 (-2) = cell 4 (-2) := (hlock 3 hc3 hc4 hc5 hc6).2.2
    rw [c3, c4] at heq
    exact Bool.noConfusion heq
  · rintro ⟨hc4, hc5, hc6, hc7⟩
    have heq : cell 4 (-2) = cell 5 (-2) := (hlock 4 hc4 hc5 hc6 hc7).2.2
    rw [c4, c5] at heq
    exact Bool.noConfusion heq

/-- **`R30-REDUCTION-SOUNDNESS-001` (`EXACT`) — Families `11` (`0110110`) and `100` (`0010010`)
    All-Phase Depth-`-4` Onset Exclusion (`orbit_110_and_100_depth4_onset_exclusion`)**:
    Combines `spatiotemporal_001001_and_011011_depth4_constant_collapse` with
    `universal_column_onset_exact_6step 4` (`cell 7 (-4) = true ∧ cell 8 (-4) = true ∧ cell 9 (-4) = true`)
    to refute all three cyclic phases of `0010010` at `t ∈ {5, 6, 7}` and all three cyclic phases
    of `0110110` at `t ∈ {6, 7, 8}` without brute-force trajectory evaluation. -/
theorem orbit_110_and_100_depth4_onset_exclusion :
    (cell 7 (-4) = true ∧ cell 8 (-4) = true ∧ cell 9 (-4) = true) ∧
    (∀ t : Nat, (t = 5 ∨ t = 6 ∨ t = 7) →
      ¬ (Rule30Prize.center t = false ∧
         Rule30Prize.center (t + 1) = false ∧
         Rule30Prize.center (t + 2) = true ∧
         Rule30Prize.center (t + 3) = false ∧
         Rule30Prize.center (t + 4) = false ∧
         Rule30Prize.center (t + 5) = true ∧
         Rule30Prize.center (t + 6) = false)) ∧
    (∀ t : Nat, (t = 6 ∨ t = 7 ∨ t = 8) →
      ¬ (Rule30Prize.center t = false ∧
         Rule30Prize.center (t + 1) = true ∧
         Rule30Prize.center (t + 2) = true ∧
         Rule30Prize.center (t + 3) = false ∧
         Rule30Prize.center (t + 4) = true ∧
         Rule30Prize.center (t + 5) = true ∧
         Rule30Prize.center (t + 6) = false)) := by
  have c7 : cell 7 (-4) = true := (universal_column_onset_exact_6step 4).2.2.2.1
  have c8 : cell 8 (-4) = true := (universal_column_onset_exact_6step 4).2.2.2.2.1
  have c9 : cell 9 (-4) = true := (universal_column_onset_exact_6step 4).2.2.2.2.2
  refine ⟨⟨c7, c8, c9⟩, ?_, ?_⟩
  · intro t ht hpat
    have hfalse := (spatiotemporal_001001_and_011011_depth4_constant_collapse t).1 hpat
    rcases ht with rfl | rfl | rfl
    · change cell 7 (-4) = false at hfalse; rw [c7] at hfalse; exact Bool.noConfusion hfalse
    · change cell 8 (-4) = false at hfalse; rw [c8] at hfalse; exact Bool.noConfusion hfalse
    · change cell 9 (-4) = false at hfalse; rw [c9] at hfalse; exact Bool.noConfusion hfalse
  · intro t ht hpat
    have hfalse := ((spatiotemporal_001001_and_011011_depth4_constant_collapse t).2 hpat).1
    rcases ht with rfl | rfl | rfl
    · change cell 7 (-4) = false at hfalse; rw [c7] at hfalse; exact Bool.noConfusion hfalse
    · change cell 8 (-4) = false at hfalse; rw [c8] at hfalse; exact Bool.noConfusion hfalse
    · change cell 9 (-4) = false at hfalse; rw [c9] at hfalse; exact Bool.noConfusion hfalse

end Rule30ProofClosure
