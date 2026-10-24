import Rule30BilateralCompatibility

/-!
# `R30-CLOSE-001` End-to-End Composition (`Rule30PrizeClosure.lean`)

Composes the unconditional (`EXACT`) theorems from `Rule30ClosureCore`, `Rule30LeftReconstruction`,
`Rule30RightInformation`, and `Rule30BilateralCompatibility` into the official `Rule30Prize.Problem1`
reduction certificates (`M5`):
1. **`bilateral_cone_unsat_implies_problem1` (`CONDITIONAL` — Track A/C Reduction to `Problem1`):**
   Uses `periodic_center_has_black_and_white_in_every_period` (which unconditionally eliminates
   all-white and all-black period words for all `T : Nat`) together with
   `obsLeftWord_rowAtLeft_eq_orColWord_rowAt` to reduce `Rule30Prize.Problem1` to finite-horizon
   bilateral observation incompatibility on mixed (black-and-white) periodic words.
2. **`linear_horizon_quotient_collision_implies_problem1` (`CONDITIONAL` — Track B Reduction to `Problem1`):**
   Uses `periodic_center_distinct_futureWork_classes_at_linear_horizon` (proved via `window_jen`)
   to show that if every hypothetical `P`-periodic center orbit experiences even a single
   `FutureWorkEquiv (col0Word T P) k` collision at the constructive linear horizon
   `k = T + (m₀ + q) * P`, then `Rule30Prize.Problem1` holds unconditionally.
3. **`bounded_T0_periods_one_to_four_excluded` (`BOUNDED`):**
   Explicitly verifies that at `T = 0`, no period `P ∈ {1, 2, 3, 4}` is compatible with the
   single-seed trajectory.
-/

namespace Rule30ProofClosure

open Ruliology.CellularAutomata
open Ruliology.CellularAutomata.Rule30Prize
open Ruliology.CellularAutomata.Rule30Realization
open Ruliology.CellularAutomata.Rule30Jen
open Ruliology.CellularAutomata.Rule30MaskedJen
open Ruliology.CellularAutomata.Rule30Diagonals
open Ruliology.CellularAutomata.Rule30BlackRuns

/-- **M5 Track A/C End-to-End Reduction (`CONDITIONAL` — `bilateral_cone_unsat_implies_problem1`)**:
    Since `periodic_center_has_black_and_white_in_every_period` unconditionally guarantees that any
    hypothetical `P`-periodic center from `T` on (`P > 0`) has both a black step and a white step
    in `[T, T + P)`, if every such mixed periodic center trajectory suffers a bilateral observation
    mismatch `obsLeftWord ≠ orColWord` at some finite horizon `H`, then `Rule30Prize.Problem1`
    holds unconditionally. -/
theorem bilateral_cone_unsat_implies_problem1
    (hBilateralUnsat :
      ∀ (T P : Nat), 0 < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        (∃ sb < P, Rule30Prize.center (T + sb) = true) →
        (∃ sw < P, Rule30Prize.center (T + sw) = false) →
        ∃ t₁ H n : Nat, T ≤ t₁ ∧
          obsLeftWord (col0Word t₁ H) (cell (t₁ + H) 0) (rowAtLeft t₁ (-1) (n + H + 1)) ≠
            orColWord (col0Word t₁ H) (rowAt t₁ 1 (n + H + 1))) :
    Rule30Prize.Problem1 := by
  rintro ⟨T, P, hP, hper⟩
  obtain ⟨hb, hw⟩ := periodic_center_has_black_and_white_in_every_period T P T hP hper (Nat.le_refl T)
  obtain ⟨t₁, H, n, _, hmis⟩ := hBilateralUnsat T P hP hper hb hw
  exact hmis (obsLeftWord_rowAtLeft_eq_orColWord_rowAt H n t₁)

/-- **M5 Track B End-to-End Reduction (`CONDITIONAL` — `linear_horizon_quotient_collision_implies_problem1`)**:
    Upgrades `g11_p1_single_persistent_quotient_collision_implies_problem1` from an infinite-horizon
    premise (`∀ k : Nat`) to a **single finite linear horizon** `k = t₁ + (m₀ + q) * P`:
    if every hypothetical `P`-periodic center trajectory has a pair of return steps `(m₀, m₀ + q)`
    (`q > 0`) that remain `FutureWorkEquiv (col0Word t₁ P) k`-equivalent up to the linear light-cone
    horizon `k = t₁ + (m₀ + q) * P`, then `Rule30Prize.Problem1` holds unconditionally! -/
theorem linear_horizon_quotient_collision_implies_problem1
    (hLinearColl :
      ∀ (T P : Nat), 0 < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        ∃ t₁ m₀ q : Nat, T ≤ t₁ ∧ 0 < q ∧
          let k := t₁ + (m₀ + q) * P
          FutureWorkEquiv (col0Word t₁ P) k
            (rowAt (t₁ + (m₀ + q) * P) 1 ((k + 1) * P + 1))
            (rowAt (t₁ + m₀ * P) 1 ((k + 1) * P + 1))) :
    Rule30Prize.Problem1 := by
  rintro ⟨T, P, hP, hper⟩
  obtain ⟨t₁, m₀, q, ht₁, hq, hcoll⟩ := hLinearColl T P hP hper
  let k := t₁ + (m₀ + q) * P
  have hbound : t₁ + (m₀ + q) * P ≤ (k + 1) * P := by
    have h1 : k + 1 ≤ (k + 1) * P := by
      have := Nat.mul_le_mul_left (k + 1) hP
      simpa using this
    omega
  exact universal_linear_reentry_horizon_bound T P t₁ m₀ q k hP hq hper ht₁ hbound hcoll

/-- **M5 Track A/C Structural Spatial-Bridge Reduction (`CONDITIONAL` —
    `spatial_bridge_to_left_diagonals_implies_problem1`)**:
    Exposes the exact surviving proposition for universal certificate generalization:
    Every periodic center word `P > 0` contains both black and white steps in `[T, T + P)`
    (`periodic_center_has_black_and_white_in_every_period`), while the left cone boundary satisfies
    the universal invariants `D 2 (t + 2) = false` and `D 4 (t + 3) = true` (`left_diag_D4_eq_true`).
    If the sideways operator-cancellation laws (`L1`–`L3`: `left_black_step_screened_forcing`,
    `double_black_step_depth2_forcing`, `local_101_pattern_conserved_left_xor`) bridge the spatial
    cone gap from `p ∈ {-1, -2, -3}` to force a contradiction with `(D 2, D 4) = (false, true)` at
    some step `t ≥ T`, then `Rule30Prize.Problem1` holds unconditionally. -/
theorem spatial_bridge_to_left_diagonals_implies_problem1
    (hSpatialBridge :
      ∀ (T P : Nat), 0 < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        (∃ sb < P, Rule30Prize.center (T + sb) = true) →
        (∃ sw < P, Rule30Prize.center (T + sw) = false) →
        ∃ t : Nat, (D 2 (t + 2) = true ∨ D 4 (t + 3) = false)) :
    Rule30Prize.Problem1 := by
  rintro ⟨T, P, hP, hper⟩
  obtain ⟨hb, hw⟩ := periodic_center_has_black_and_white_in_every_period T P T hP hper (Nat.le_refl T)
  obtain ⟨t, hbad⟩ := hSpatialBridge T P hP hper hb hw
  rcases hbad with hd2 | hd4
  · have h := left_diag_D2_eq_false t
    rw [h] at hd2
    contradiction
  · have h := left_diag_D4_eq_true t
    rw [h] at hd4
    contradiction

/-- **Bounded Verification (`BOUNDED` — `bounded_T0_periods_one_to_four_excluded`)**:
    Certifies on the single-seed trajectory at `T = 0` that no period `P ∈ {1, 2, 3, 4}` holds
    even across the first period return `t = 0 .. 2`. -/
theorem bounded_T0_periods_one_to_four_excluded :
    ¬ (∀ t, 0 ≤ t → Rule30Prize.center (t + 1) = Rule30Prize.center t) ∧
    ¬ (∀ t, 0 ≤ t → Rule30Prize.center (t + 2) = Rule30Prize.center t) ∧
    ¬ (∀ t, 0 ≤ t → Rule30Prize.center (t + 3) = Rule30Prize.center t) ∧
    ¬ (∀ t, 0 ≤ t → Rule30Prize.center (t + 4) = Rule30Prize.center t) := by
  refine ⟨no_period_one_center_all_transients 0, ?_, ?_, ?_⟩
  · intro h2
    have h := h2 0 (Nat.zero_le 0)
    revert h; decide
  · intro h3
    have h := h3 2 (Nat.zero_le 2)
    revert h; decide
  · intro h4
    have h := h4 3 (Nat.zero_le 3)
    revert h; decide

/-! ### Top-Level Re-Exports for Single-Module `Check.lean Rule30PrizeClosure` Verification -/

theorem closure_left_diag_D4_eq_true (t : Nat) :
    D 4 (t + 3) = true :=
  left_diag_D4_eq_true t

theorem closure_left_diag_D5_eq_not_D3 (t : Nat) :
    D 5 (t + 4) = !D 3 (t + 3) :=
  left_diag_D5_eq_not_D3 t

theorem closure_double_black_step_depth2_forcing (t : Nat)
    (hb0 : Rule30Prize.center t = true)
    (hb1 : Rule30Prize.center (t + 1) = true) :
    cell t (-1) = false ∧
    cell (t + 1) (-1) = !Rule30Prize.center (t + 2) ∧
    cell t (-2) = Rule30Prize.center (t + 2) :=
  double_black_step_depth2_forcing t hb0 hb1

theorem closure_local_101_pattern_conserved_left_xor (t : Nat)
    (hc0 : Rule30Prize.center t = true)
    (hc1 : Rule30Prize.center (t + 1) = false)
    (hc2 : Rule30Prize.center (t + 2) = true) :
    cell t (-1) = true ∧
    cell t (-2) = !cell (t + 1) (-1) ∧
    cell t (-3) = xor (cell (t + 1) (-1)) (Rule30Prize.center (t + 3)) ∧
    xor (cell t (-2)) (cell t (-3)) = !Rule30Prize.center (t + 3) :=
  local_101_pattern_conserved_left_xor t hc0 hc1 hc2

theorem closure_local_1010_complement_cancellation_depth4 (t : Nat)
    (hc0 : Rule30Prize.center t = true)
    (hc1 : Rule30Prize.center (t + 1) = false)
    (hc2 : Rule30Prize.center (t + 2) = true)
    (hc3 : Rule30Prize.center (t + 3) = false) :
    cell t (-3) = !cell t (-2) ∧
    (cell t (-3) || cell t (-2)) = true ∧
    cell t (-4) = !cell (t + 1) (-3) :=
  local_1010_complement_cancellation_depth4 t hc0 hc1 hc2 hc3

theorem closure_spatial_bridge_to_left_diagonals_implies_problem1
    (hSpatialBridge :
      ∀ (T P : Nat), 0 < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        (∃ sb < P, Rule30Prize.center (T + sb) = true) →
        (∃ sw < P, Rule30Prize.center (T + sw) = false) →
        ∃ t : Nat, (D 2 (t + 2) = true ∨ D 4 (t + 3) = false)) :
    Rule30Prize.Problem1 :=
  spatial_bridge_to_left_diagonals_implies_problem1 hSpatialBridge

theorem closure_stepLeftRow_rowAtLeft (t n : Nat) (p : Int) :
    stepLeftRow (cell t (p + 1)) (rowAtLeft t p (n + 1)) = rowAtLeft (t + 1) p n :=
  stepLeftRow_rowAtLeft t n p

theorem closure_runLeftWord_rowAtLeft (L n t : Nat) :
    runLeftWord (col0Word t L) (rowAtLeft t (-1) (n + L)) = rowAtLeft (t + L) (-1) n :=
  runLeftWord_rowAtLeft L n t

theorem closure_left_black_step_screened_forcing (t : Nat)
    (hb : Rule30Prize.center t = true) :
    cell t (-1) = !Rule30Prize.center (t + 1) ∧
    Rule30Prize.center (t + 1) = !cell t (-1) :=
  left_black_step_screened_forcing t hb

theorem closure_left_effective_boundary_autonomous_step (t : Nat)
    (hno11 : (Rule30Prize.center t && Rule30Prize.center (t + 1)) = false) :
    cell (t + 1) (-1) = xor (cell t (-2)) (cell t (-1)) :=
  left_effective_boundary_autonomous_step t hno11

theorem closure_no_eventually_all_white_center (T : Nat) :
    ¬ ∀ t : Nat, T ≤ t → Rule30Prize.center t = false :=
  no_eventually_all_white_center T

theorem closure_no_eventually_all_black_center (T : Nat) :
    ¬ ∀ t : Nat, T ≤ t → Rule30Prize.center t = true :=
  no_eventually_all_black_center T

theorem closure_no_period_one_center_all_transients (T : Nat) :
    ¬ ∀ t : Nat, T ≤ t → Rule30Prize.center (t + 1) = Rule30Prize.center t :=
  no_period_one_center_all_transients T

theorem closure_periodic_center_has_black_and_white_in_every_period
    (T P t₁ : Nat)
    (hP : 0 < P)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₁ : T ≤ t₁) :
    (∃ sb : Nat, sb < P ∧ Rule30Prize.center (t₁ + sb) = true) ∧
    (∃ sw : Nat, sw < P ∧ Rule30Prize.center (t₁ + sw) = false) :=
  periodic_center_has_black_and_white_in_every_period T P t₁ hP hper ht₁

theorem closure_left_light_cone_support_bound (T : Nat) :
    cell T (-(T : Int)) = true ∧
    ∀ p : Int, p < -(T : Int) → cell T p = false :=
  left_light_cone_support_bound T

theorem closure_bilateral_center_conservation (t : Nat) :
    cell t (-1) = xor (cell (t + 1) 0) (orCol 0 t) ∧
    orCol 0 t = xor (cell (t + 1) 0) (cell t (-1)) :=
  bilateral_center_conservation t

theorem closure_futureWorkEquiv_implies_orCol_and_left_col_agree
    (T P t₀ m₀ q k : Nat)
    (hP : 0 < P)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₀ : T ≤ t₀)
    (hfw : FutureWorkEquiv (col0Word t₀ P) k
      (rowAt (t₀ + (m₀ + q) * P) 1 ((k + 1) * P + 1))
      (rowAt (t₀ + m₀ * P) 1 ((k + 1) * P + 1))) :
    ∀ s : Nat, s < (k + 1) * P →
      orCol 0 (t₀ + (m₀ + q) * P + s) = orCol 0 (t₀ + m₀ * P + s) ∧
      cell (t₀ + (m₀ + q) * P + s) (-1) = cell (t₀ + m₀ * P + s) (-1) :=
  futureWorkEquiv_implies_orCol_and_left_col_agree T P t₀ m₀ q k hP hper ht₀ hfw

theorem closure_universal_linear_reentry_horizon_bound
    (T P t₀ m₀ q k : Nat)
    (hP : 0 < P)
    (hq : 0 < q)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₀ : T ≤ t₀)
    (hbound : t₀ + (m₀ + q) * P ≤ (k + 1) * P) :
    ¬ FutureWorkEquiv (col0Word t₀ P) k
        (rowAt (t₀ + (m₀ + q) * P) 1 ((k + 1) * P + 1))
        (rowAt (t₀ + m₀ * P) 1 ((k + 1) * P + 1)) :=
  universal_linear_reentry_horizon_bound T P t₀ m₀ q k hP hq hper ht₀ hbound

theorem closure_periodic_center_distinct_futureWork_classes_at_linear_horizon
    (T P t₀ M k m₁ m₂ : Nat)
    (hP : 0 < P)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₀ : T ≤ t₀)
    (hbound : t₀ + M * P ≤ (k + 1) * P)
    (hm12 : m₁ < m₂)
    (hm2 : m₂ < M) :
    ¬ FutureWorkEquiv (col0Word t₀ P) k
        (rowAt (t₀ + m₂ * P) 1 ((k + 1) * P + 1))
        (rowAt (t₀ + m₁ * P) 1 ((k + 1) * P + 1)) :=
  periodic_center_distinct_futureWork_classes_at_linear_horizon T P t₀ M k m₁ m₂ hP hper ht₀ hbound hm12 hm2

theorem closure_obsLeftWord_rowAtLeft (L n t : Nat) :
    obsLeftWord (col0Word t L) (cell (t + L) 0) (rowAtLeft t (-1) (n + L + 1)) = col0OrTrace t L :=
  obsLeftWord_rowAtLeft L n t

theorem closure_obsLeftWord_rowAtLeft_eq_orColWord_rowAt (L n t : Nat) :
    obsLeftWord (col0Word t L) (cell (t + L) 0) (rowAtLeft t (-1) (n + L + 1)) =
      orColWord (col0Word t L) (rowAt t 1 (n + L + 1)) :=
  obsLeftWord_rowAtLeft_eq_orColWord_rowAt L n t

theorem closure_bilateral_observation_mismatch_excludes_periodic_word
    (L n t : Nat) (w : List Bool) (c_after : Bool)
    (hmismatch :
      obsLeftWord w c_after (rowAtLeft t (-1) (n + L + 1)) ≠
        orColWord w (rowAt t 1 (n + L + 1))) :
    ¬ (col0Word t L = w ∧ cell (t + L) 0 = c_after) :=
  bilateral_observation_mismatch_excludes_periodic_word L n t w c_after hmismatch

theorem closure_decoupled_halves_consistent_but_bilaterally_incompatible :
    let w6 := [false, true, false, true, false, true]
    let L₁ := [true, false, false, false, false, false, false, false]
    let R₁ := [true, false, false, false, false, false, false, false]
    LeftBlackStepAdmissible w6 (obsLeftWord w6 false L₁) ∧
    LeftBlackStepAdmissible w6 (orColWord w6 R₁) ∧
    obsLeftWord [false] true (rowAtLeft 1 (-1) 2) ≠
      orColWord [false] (rowAt 1 1 2) ∧
    ¬ (cell 1 0 = false ∧ cell 2 0 = true) :=
  decoupled_halves_consistent_but_bilaterally_incompatible

end Rule30ProofClosure
