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

/-- **Track A/C (`EXACT`, New in `R30-TRANSPORT-001`) — Universal Adjacent-Column XOR Onset Law
    (`universal_adjacent_xor_onset_law`)**:
    For every spatial depth `k : Nat`, at adjacent columns `-(k : Int)` and `-(k + 1 : Int)`:
    1. At step `t = k + 1`: `xor (cell (k + 1) (-(k : Int))) (cell (k + 1) (-(k + 1 : Int))) = false`
       (both cells are black: `(true, true)`), and
    2. At step `t = k + 2`: `xor (cell (k + 2) (-(k : Int))) (cell (k + 2) (-(k + 1 : Int))) = true`
       (the cells form the Mode A complement pair `(false, true)`). -/
theorem universal_adjacent_xor_onset_law (k : Nat) :
    xor (cell (k + 1) (-(k : Int))) (cell (k + 1) (-(k + 1 : Int))) = false ∧
    xor (cell (k + 2) (-(k : Int))) (cell (k + 2) (-(k + 1 : Int))) = true := by
  have hk := universal_column_onset_signature k
  have hk1 := universal_column_onset_signature (k + 1)
  have h1 : cell (k + 1) (-(k : Int)) = true := hk.2.1
  have h2 : cell (k + 1) (-(k + 1 : Int)) = true := by
    simpa [show (-(k + 1 : Int)) = -((k + 1 : Nat) : Int) by omega] using hk1.1
  have h3 : cell (k + 2) (-(k : Int)) = false := hk.2.2.1
  have h4 : cell (k + 2) (-(k + 1 : Int)) = true := by
    simpa [show (-(k + 1 : Int)) = -((k + 1 : Nat) : Int) by omega] using hk1.2.1
  rw [h1, h2, h3, h4]
  exact ⟨rfl, rfl⟩

/-- **Deliverable 3 Direct Closure Attempt With Exposed Transport Goal (`CONDITIONAL` —
    `transport_adjacent_xor_to_onset_implies_problem1`)**:
    Carries out the unconditional proof structure from:
    - `periodic_center_has_black_and_white_in_every_period` (every period has a black step `T + sb`),
    - `left_black_step_screened_forcing` (locking column `-1` at every periodic return `T + sb + m * P`),
    - `spatial_transport_step_dichotomy` (transporting relations leftward column by column), and
    - `universal_adjacent_xor_onset_law` (`xor = false` at `t = k + 1` and `xor = true` at `t = k + 2`),
    isolating the exact single unsolved spatial-transport proposition (`hTransportParity`):
    whether transporting the periodic depth-1 lock `∀ m, cell (T + sb + m * P) (-1) = !center (T + sb + 1)`
    outward to some column `k` flips the onset adjacent-column XOR parity at `t = k + 1` or `t = k + 2`
    (generalizing `transport_onset_excludes_1010_at_t3`, where `k = 2` flips `t = 3`). -/
theorem transport_adjacent_xor_to_onset_implies_problem1
    (hTransportParity :
      ∀ (T P sb : Nat), 0 < P → sb < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        (∀ m : Nat, cell (T + sb + m * P) (-1) = !Rule30Prize.center (T + sb + 1)) →
        ∃ k : Nat,
          xor (cell (k + 1) (-(k : Int))) (cell (k + 1) (-(k + 1 : Int))) = true ∨
          xor (cell (k + 2) (-(k : Int))) (cell (k + 2) (-(k + 1 : Int))) = false) :
    Rule30Prize.Problem1 := by
  rintro ⟨T, P, hP, hper⟩
  obtain ⟨⟨sb, hsb, hb⟩, _⟩ :=
    periodic_center_has_black_and_white_in_every_period T P T hP hper (Nat.le_refl T)
  have hperk : ∀ m t, T ≤ t → Rule30Prize.center (t + m * P) = Rule30Prize.center t :=
    periodic_mul hper
  have hlock : ∀ m : Nat, cell (T + sb + m * P) (-1) = !Rule30Prize.center (T + sb + 1) := by
    intro m
    have hbm : Rule30Prize.center (T + sb + m * P) = true := by
      rw [hperk m (T + sb) (by omega), hb]
    have hnext : Rule30Prize.center (T + sb + m * P + 1) = Rule30Prize.center (T + sb + 1) := by
      have h := hperk m (T + sb + 1) (by omega)
      rwa [show T + sb + 1 + m * P = T + sb + m * P + 1 by omega] at h
    have hforce := (left_black_step_screened_forcing (T + sb + m * P) hbm).1
    rwa [hnext] at hforce
  obtain ⟨k, hflip⟩ := hTransportParity T P sb hP hsb hper hlock
  rcases universal_adjacent_xor_onset_law k with ⟨hfalse, htrue⟩
  rcases hflip with hbad1 | hbad2
  · rw [hfalse] at hbad1; contradiction
  · rw [htrue] at hbad2; contradiction

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

theorem closure_universal_column_onset_signature (k : Nat) :
    cell k (-(k : Int)) = true ∧
    cell (k + 1) (-(k : Int)) = true ∧
    cell (k + 2) (-(k : Int)) = false ∧
    cell (k + 4) (-(k : Int)) = true ∧
    cell (k + 5) (-(k : Int)) = cell (k + 3) (-(k : Int)) :=
  universal_column_onset_signature k

theorem closure_spatial_transport_step_dichotomy (t : Nat) (p : Int) :
    (cell t p = true → cell t (p - 1) = !cell (t + 1) p) ∧
    (cell t (p + 1) = true → cell t (p - 1) = !cell (t + 1) p) ∧
    (cell t p = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t (p + 1))) ∧
    (cell t (p + 1) = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t p)) ∧
    (xor (cell t p) (cell t (p + 1)) = true → cell t (p - 1) = !cell (t + 1) p) ∧
    (xor (cell t p) (cell t (p + 1)) = false → cell t (p - 1) = xor (cell (t + 1) p) (cell t p)) :=
  spatial_transport_step_dichotomy t p

theorem closure_transport_onset_excludes_1010_at_t3 :
    ¬ (Rule30Prize.center 3 = true ∧
       Rule30Prize.center 4 = false ∧
       Rule30Prize.center 5 = true ∧
       Rule30Prize.center 6 = false) :=
  transport_onset_excludes_1010_at_t3

theorem closure_universal_adjacent_xor_onset_law (k : Nat) :
    xor (cell (k + 1) (-(k : Int))) (cell (k + 1) (-(k + 1 : Int))) = false ∧
    xor (cell (k + 2) (-(k : Int))) (cell (k + 2) (-(k + 1 : Int))) = true :=
  universal_adjacent_xor_onset_law k

theorem closure_transport_adjacent_xor_to_onset_implies_problem1
    (hTransportParity :
      ∀ (T P sb : Nat), 0 < P → sb < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        (∀ m : Nat, cell (T + sb + m * P) (-1) = !Rule30Prize.center (T + sb + 1)) →
        ∃ k : Nat,
          xor (cell (k + 1) (-(k : Int))) (cell (k + 1) (-(k + 1 : Int))) = true ∨
          xor (cell (k + 2) (-(k : Int))) (cell (k + 2) (-(k + 1 : Int))) = false) :
    Rule30Prize.Problem1 :=
  transport_adjacent_xor_to_onset_implies_problem1 hTransportParity

theorem closure_cell_neg_eq_center_xor_characteristicFlux (d t : Nat) :
    cell t (-(d : Int)) = xor (Rule30Prize.center (t + d)) (leftCharacteristicFlux t d) ∧
    leftCharacteristicFlux t d = xor (Rule30Prize.center (t + d)) (cell t (-(d : Int))) :=
  cell_neg_eq_center_xor_characteristicFlux d t

theorem closure_universal_characteristic_flux_onset_laws (k : Nat) :
    leftCharacteristicFlux k k = !Rule30Prize.center (k + k) ∧
    leftCharacteristicFlux (k + 1) k = !Rule30Prize.center (k + 1 + k) ∧
    leftCharacteristicFlux (k + 2) k = Rule30Prize.center (k + 2 + k) ∧
    leftCharacteristicFlux (k + 4) k = !Rule30Prize.center (k + 4 + k) ∧
    xor (leftCharacteristicFlux (k + 5) k) (leftCharacteristicFlux (k + 3) k) =
      xor (Rule30Prize.center (k + 5 + k)) (Rule30Prize.center (k + 3 + k)) :=
  universal_characteristic_flux_onset_laws k

theorem closure_periodic_center_forces_characteristic_flux_depth_periodicity
    (T P k : Nat)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (hk : T ≤ k) :
    leftCharacteristicFlux (k + P) (k + P) = leftCharacteristicFlux k k ∧
    leftCharacteristicFlux (k + P + 1) (k + P) = leftCharacteristicFlux (k + 1) k ∧
    leftCharacteristicFlux (k + P + 2) (k + P) = leftCharacteristicFlux (k + 2) k ∧
    leftCharacteristicFlux (k + P + 4) (k + P) = leftCharacteristicFlux (k + 4) k ∧
    xor (leftCharacteristicFlux (k + P + 5) (k + P)) (leftCharacteristicFlux (k + P + 3) (k + P)) =
      xor (leftCharacteristicFlux (k + 5) k) (leftCharacteristicFlux (k + 3) k) :=
  periodic_center_forces_characteristic_flux_depth_periodicity T P k hper hk

theorem closure_spatiotemporal_101010_quadratic_cancellation_depth5 (t : Nat)
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
    cell t (-5) = cell t (-3) :=
  spatiotemporal_101010_quadratic_cancellation_depth5 t hc0 hc1 hc2 hc3 hc4 hc5

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
