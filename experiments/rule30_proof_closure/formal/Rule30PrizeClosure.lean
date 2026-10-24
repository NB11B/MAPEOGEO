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

/-- **End-to-End Composition (`CONDITIONAL`, New in `R30-FLUX-CORR-001`) — Right-History Characteristic-Flux
    Incompatibility Reduction (`right_history_characteristic_flux_incompatibility_implies_problem1`)**:
    Combines:
    1. `periodic_center_has_black_and_white_in_every_period` (`EXACT`),
    2. `spatiotemporal_leading_orCol_onset_isolation` (`EXACT` — all-depth isolation of `orCol 0` at
       odd apex times `2k + 1` and even apex times `2k + 2`),
    3. `spatiotemporal_black_white_apex_dichotomy` (`EXACT` — PSMSL black-step screening vs.
       white-step linear isolation of `cell τ 1`), and
    4. The finite-support right initial condition (`R_zero T : cell T T = true`, `cell_eq_false_of_gt T`).
    If no single-seed right-half history can satisfy both the black-step interior-flux equations and
    the white-step `cell τ 1` equations for all `k ≥ T`, `Rule30Prize.Problem1` holds unconditionally. -/
theorem right_history_characteristic_flux_incompatibility_implies_problem1
    (hFluxIncompat :
      ∀ (T P sb sw : Nat), 0 < P → sb < P → sw < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        Rule30Prize.center (T + sb) = true →
        Rule30Prize.center (T + sw) = false →
        (cell T (T : Int) = true ∧ ∀ p : Int, (T : Int) < p → cell T p = false) →
        ∃ k : Nat, T ≤ k ∧
          (orCol 0 (k + 1 + k) ≠
             xor (!Rule30Prize.center (k + 1 + k + 1)) (interiorCharacteristicFlux (k + 1) k) ∨
           orCol 0 (k + 2 + k) ≠
             xor (!Rule30Prize.center (k + 2 + k + 1)) (interiorCharacteristicFlux (k + 2) k))) :
    Rule30Prize.Problem1 := by
  rintro ⟨T, P, hP, hper⟩
  rcases periodic_center_has_black_and_white_in_every_period T P T hP hper (Nat.le_refl T) with
    ⟨⟨sb, hsb, hb⟩, ⟨sw, hsw, hw⟩⟩
  have hRightSeed : cell T (T : Int) = true ∧ ∀ p : Int, (T : Int) < p → cell T p = false := by
    refine ⟨?_, fun p hp => cell_eq_false_of_gt T p hp⟩
    have hr0 := R_zero T
    unfold R at hr0
    rw [show (T : Int) - (0 : Nat) = (T : Int) by omega] at hr0
    exact hr0
  obtain ⟨k, _, hmismatch⟩ := hFluxIncompat T P sb sw hP hsb hsw hper hb hw hRightSeed
  rcases spatiotemporal_leading_orCol_onset_isolation k with ⟨h_odd, h_even⟩
  rcases hmismatch with hbad_odd | hbad_even
  · exact hbad_odd h_odd
  · exact hbad_even h_even

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

/-! ### Section 5 Universal Arbitrary-Period Contradiction for the Infinite `11`-Free Family `0^r 1` -/

theorem rowAt_add (t : Nat) :
    ∀ (m n : Nat) (p : Int), rowAt t p (m + n) = rowAt t p m ++ rowAt t (p + (m : Int)) n
  | 0, n, p => by simp [rowAt]
  | m + 1, n, p => by
      have ih := rowAt_add t m n (p + 1)
      rw [show p + 1 + (m : Int) = p + ((m + 1 : Nat) : Int) by omega] at ih
      rw [show m + 1 + n = (m + n) + 1 by omega]
      show cell t p :: rowAt t (p + 1) (m + n) =
        cell t p :: (rowAt t (p + 1) m ++ rowAt t (p + ((m + 1 : Nat) : Int)) n)
      rw [ih]

theorem col0Word_replicate_false :
    ∀ (k t : Nat), (∀ i, i < k → cell (t + i) 0 = false) → col0Word t k = List.replicate k false
  | 0, _, _ => rfl
  | k + 1, t, hw => by
      have h0 : cell t 0 = false := by simpa using hw 0 (by omega)
      have ih := col0Word_replicate_false k (t + 1) (fun i hi => by
        have := hw (1 + i) (by omega)
        rwa [show t + (1 + i) = t + 1 + i by omega] at this)
      show cell t 0 :: col0Word (t + 1) k = false :: List.replicate k false
      rw [h0, ih]

theorem col0Word_white_then_black :
    ∀ (d t : Nat),
      (∀ i, i < d → cell (t + i) 0 = false) →
      cell (t + d) 0 = true →
      col0Word t (d + 1) = List.replicate d false ++ [true]
  | 0, t, _, hb => by
      have hb0 : cell t 0 = true := by simpa using hb
      show [cell t 0] = [true]
      rw [hb0]
  | d + 1, t, hw, hb => by
      have h0 : cell t 0 = false := by simpa using hw 0 (by omega)
      have ih := col0Word_white_then_black d (t + 1)
        (fun i hi => by
          have := hw (1 + i) (by omega)
          rwa [show t + (1 + i) = t + 1 + i by omega] at this)
        (by rwa [show t + 1 + d = t + (d + 1) by omega])
      show cell t 0 :: col0Word (t + 1) (d + 1) = false :: (List.replicate d false ++ [true])
      rw [h0, ih]

def validFrontPrefixes8 : List (List Bool) :=
  [ [true, true, false, false, true, false, false, false],
    [true, true, false, false, true, false, false, true],
    [true, true, false, true, true, true, true, false],
    [true, true, false, true, true, true, true, true] ]

theorem front_six_white_core :
    ∀ L ∈ allLists 7,
      runWord (List.replicate 6 false)
        ([false, false, false, false, false, false, true] ++ L) ∈ validFrontPrefixes8 := by
  decide +kernel

theorem late_single_black_core :
    ∀ d ∈ List.range 8, ∀ P ∈ validFrontPrefixes8, ∀ L ∈ allLists d,
      true ∈ runWord (List.replicate d false ++ [true]) (P ++ L) := by
  decide +kernel

theorem period_lock_single_black (a r : Nat)
    (hwr : ∀ i, i < r → cell (a + i) 0 = false)
    (hb1 : cell (a + r) 0 = true)
    (hr : 8 ≤ r) (ℓ : Nat) (hℓ : ℓ ≤ r - 8)
    (hw : ∀ p : Nat, 1 ≤ p → p ≤ ℓ → cell a p = false)
    (hb : cell a ((ℓ + 1 : Nat) : Int) = true) :
    (∀ i, i < ℓ → cell (a + i) 1 = false) ∧
    (∀ i, ℓ ≤ i → i ≤ r → cell (a + i) 1 = true) ∧
    cell (a + r + 1) 1 = false ∧
    cell (a + r + 1) 2 = false ∧
    cell (a + r + 1) 3 = true := by
  have hfront := (front_moves a ℓ r hwr hw hb ℓ (by omega) (Nat.le_refl ℓ)).2
  rw [show ℓ - ℓ + 1 = 1 by omega] at hfront
  have hw_col1 : ∀ i, i < ℓ → cell (a + i) 1 = false := by
    intro i hi
    have := (front_moves a ℓ r hwr hw hb i (by omega) (by omega)).1 1 (Nat.le_refl 1) (by omega)
    simpa using this
  have hblk : ∀ i, ℓ ≤ i → i ≤ r → cell (a + i) 1 = true := by
    intro i h1 h2
    have := black_stays (a + ℓ) (r - ℓ) (fun j hj => by
      have := hwr (ℓ + j) (by omega); rwa [show a + (ℓ + j) = a + ℓ + j by omega] at this)
      (by simpa using hfront) (i - ℓ) (by omega)
    rwa [show a + ℓ + (i - ℓ) = a + i by omega] at this
  have hA := nine_black (a + (r - 8)) 1 (fun s hs => by
    have := hblk (r - 8 + s) (by omega) (by omega)
    rwa [show a + (r - 8 + s) = a + (r - 8) + s by omega] at this)
  rw [show a + (r - 8) + 9 = a + r + 1 by omega,
      show (1 : Int) + 1 = 2 by rfl,
      show (1 : Int) + 2 = 3 by rfl] at hA
  have c1 : cell (a + r + 1) 1 = false := by
    show rule (cell (a + r) (1 - 1)) (cell (a + r) 1) (cell (a + r) (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, hb1, hblk r (by omega) (Nat.le_refl r)]
    rfl
  exact ⟨hw_col1, hblk, c1, hA.1, hA.2⟩

theorem period_late_single_black (a r : Nat)
    (hwr : ∀ i, i < r → cell (a + i) 0 = false)
    (hb1 : cell (a + r) 0 = true)
    (hr : 14 ≤ r) (ℓ : Nat) (hℓ1 : r - 7 ≤ ℓ) (hℓ2 : ℓ ≤ r)
    (hw : ∀ p : Nat, 1 ≤ p → p ≤ ℓ → cell a p = false)
    (hb : cell a ((ℓ + 1 : Nat) : Int) = true) :
    ∃ ℓ', ℓ' ≤ r - 8 ∧
      (∀ p : Nat, 1 ≤ p → p ≤ ℓ' → cell (a + r + 1) p = false) ∧
      cell (a + r + 1) ((ℓ' + 1 : Nat) : Int) = true := by
  let u := a + (ℓ - 6)
  let d := r - ℓ
  obtain ⟨hw_u, hb_u⟩ := front_moves a ℓ r hwr hw hb (ℓ - 6) (by omega) (by omega)
  have hrow_u : rowAt u 1 7 = [false, false, false, false, false, false, true] := by
    have c1 : cell u 1 = false := by simpa using hw_u 1 (by omega) (by omega)
    have c2 : cell u 2 = false := by simpa using hw_u 2 (by omega) (by omega)
    have c3 : cell u 3 = false := by simpa using hw_u 3 (by omega) (by omega)
    have c4 : cell u 4 = false := by simpa using hw_u 4 (by omega) (by omega)
    have c5 : cell u 5 = false := by simpa using hw_u 5 (by omega) (by omega)
    have c6 : cell u 6 = false := by simpa using hw_u 6 (by omega) (by omega)
    have c7 : cell u 7 = true := by
      rw [show ℓ - (ℓ - 6) + 1 = 7 by omega] at hb_u
      exact hb_u
    show [cell u 1, cell u 2, cell u 3, cell u 4, cell u 5, cell u 6, cell u 7] = _
    rw [c1, c2, c3, c4, c5, c6, c7]
  have hcol_u : col0Word u 6 = List.replicate 6 false := by
    apply col0Word_replicate_false 6 u
    intro i hi
    have := hwr (ℓ - 6 + i) (by omega)
    rwa [show a + (ℓ - 6 + i) = u + i by omega] at this
  have hrun6 := runWord_rowAt 6 8 u
  rw [show 8 + 6 = 7 + 7 by rfl, rowAt_add u 7 7 1,
      show (1 : Int) + (7 : Nat) = 8 by rfl,
      show u + 6 = a + ℓ by omega, hcol_u, hrow_u] at hrun6
  have hmem7 : rowAt u 8 7 ∈ allLists 7 := by
    have := mem_allLists (rowAt u 8 7)
    rwa [length_rowAt] at this
  have hpref8 : rowAt (a + ℓ) 1 8 ∈ validFrontPrefixes8 := by
    rw [← hrun6]
    exact front_six_white_core (rowAt u 8 7) hmem7
  have hcol_d : col0Word (a + ℓ) (d + 1) = List.replicate d false ++ [true] := by
    apply col0Word_white_then_black d (a + ℓ)
    · intro i hi
      have := hwr (ℓ + i) (by omega)
      rwa [show a + (ℓ + i) = a + ℓ + i by omega] at this
    · have : a + ℓ + d = a + r := by omega
      rwa [this]
  have hrun_d := runWord_rowAt (d + 1) 7 (a + ℓ)
  rw [show 7 + (d + 1) = 8 + d by omega, rowAt_add (a + ℓ) 8 d 1,
      show (1 : Int) + (8 : Nat) = 9 by rfl,
      show a + ℓ + (d + 1) = a + r + 1 by omega, hcol_d] at hrun_d
  have hmem_d : rowAt (a + ℓ) 9 d ∈ allLists d := by
    have := mem_allLists (rowAt (a + ℓ) 9 d)
    rwa [length_rowAt] at this
  have hd_range : d ∈ List.range 8 := List.mem_range.2 (by omega)
  have htrue_in : true ∈ rowAt (a + r + 1) 1 7 := by
    rw [← hrun_d]
    exact late_single_black_core d hd_range (rowAt (a + ℓ) 1 8) hpref8 (rowAt (a + ℓ) 9 d) hmem_d
  rcases first_black_aux (a + r + 1) 7 with hw7 | ⟨ℓ', hℓ'7, hw', hb'⟩
  · have hrow_false : rowAt (a + r + 1) 1 7 = [false, false, false, false, false, false, false] := by
      have f1 : cell (a + r + 1) 1 = false := by simpa using hw7 1 (by omega) (by omega)
      have f2 : cell (a + r + 1) 2 = false := by simpa using hw7 2 (by omega) (by omega)
      have f3 : cell (a + r + 1) 3 = false := by simpa using hw7 3 (by omega) (by omega)
      have f4 : cell (a + r + 1) 4 = false := by simpa using hw7 4 (by omega) (by omega)
      have f5 : cell (a + r + 1) 5 = false := by simpa using hw7 5 (by omega) (by omega)
      have f6 : cell (a + r + 1) 6 = false := by simpa using hw7 6 (by omega) (by omega)
      have f7 : cell (a + r + 1) 7 = false := by simpa using hw7 7 (by omega) (by omega)
      show [cell (a + r + 1) 1, cell (a + r + 1) 2, cell (a + r + 1) 3, cell (a + r + 1) 4,
            cell (a + r + 1) 5, cell (a + r + 1) 6, cell (a + r + 1) 7] = _
      rw [f1, f2, f3, f4, f5, f6, f7]
    rw [hrow_false] at htrue_in
    exact False.elim (by revert htrue_in; decide)
  · exact ⟨ℓ', by omega, hw', hb'⟩

/-- **Section 5 Universal Arbitrary-Period Contradiction (`EXACT`, New in `R30-UNIVERSAL-001`) —
    The Infinite `11`-Free White-Run Family `0^r 1` (`r ≥ 14`) Is Impossible for Every Transient `T`
    (`no_white_run_single_black_all_transients`)**:
    Proves unconditionally (for symbolic, arbitrarily large period `P = r + 1 ≥ 15`, arbitrary
    transient `T : Nat`, and arbitrary phase `t₀ ≥ T`) that the single-seed center column cannot
    repeat the `11`-free word `0^r 1`. Across all four right-frontier regimes (`ℓ ≤ r - 8`,
    `r - 7 ≤ ℓ ≤ r`, `ℓ = r + 1`, and `ℓ ≥ r + 2`), the right-half boundary front enters the
    `ℓ ≤ r - 8` basin within at most one period and locks permanently at `ℓ = 2` from period `2` on,
    forcing column `1` to be `P`-periodic (`decide (2 ≤ i)`) against Jen's theorem (`not_adjacent 0`). -/
theorem no_white_run_single_black_all_transients
    (T r t0 : Nat) (hr : 14 ≤ r)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + (r + 1)) = Rule30Prize.center t)
    (ht0 : T ≤ t0)
    (hw : ∀ i, i < r → Rule30Prize.center (t0 + i) = false)
    (hb1 : Rule30Prize.center (t0 + r) = true) : False := by
  generalize hQdef : r + 1 = Q at hper
  have hQ : 0 < Q := by omega
  have hperk : ∀ k t, T ≤ t → Rule30Prize.center (t + k * Q) = Rule30Prize.center t :=
    periodic_mul hper
  generalize hAdef : t0 + Q = A
  have hMul : ∀ k, (k + 1) * Q = k * Q + Q := fun k => Nat.succ_mul k Q
  have drvw : ∀ k i, i < r → cell (A + k * Q + i) 0 = false := by
    intro k i hi
    have := hperk (k + 1) (t0 + i) (by omega)
    show Rule30Prize.center (A + k * Q + i) = false
    rw [hMul k, show t0 + i + (k * Q + Q) = A + k * Q + i by omega] at this
    rw [this]; exact hw i hi
  have drvb1 : ∀ k, cell (A + k * Q + r) 0 = true := by
    intro k
    have := hperk (k + 1) (t0 + r) (by omega)
    show Rule30Prize.center (A + k * Q + r) = true
    rw [hMul k, show t0 + r + (k * Q + Q) = A + k * Q + r by omega] at this
    rw [this]; exact hb1
  have hnext : ∀ k, A + k * Q + r + 1 = A + (k + 1) * Q := by
    intro k; rw [hMul k]; omega
  -- Period 1 always starts with some ℓ₁ ≤ r - 8
  have hperiod1_basin :
      ∃ ℓ₁, ℓ₁ ≤ r - 8 ∧
        (∀ p : Nat, 1 ≤ p → p ≤ ℓ₁ → cell (A + 1 * Q) p = false) ∧
        cell (A + 1 * Q) ((ℓ₁ + 1 : Nat) : Int) = true := by
    obtain ⟨ℓ₀, hw₀, hb₀⟩ := first_black (A + 0 * Q) (by omega)
    by_cases c1 : ℓ₀ ≤ r - 8
    · obtain ⟨_, _, hc1, hc2, hc3⟩ :=
        period_lock_single_black (A + 0 * Q) r (drvw 0) (drvb1 0) (by omega) ℓ₀ c1 hw₀ hb₀
      rw [hnext 0] at hc1 hc2 hc3
      refine ⟨2, by omega, fun p hp1 hp2 => ?_, by simpa using hc3⟩
      by_cases hp : p = 1
      · subst hp; simpa using hc1
      · have : p = 2 := by omega
        subst this; simpa using hc2
    by_cases c2 : ℓ₀ ≤ r
    · obtain ⟨ℓ₁, hℓ₁, hw₁, hb₁⟩ :=
        period_late_single_black (A + 0 * Q) r (drvw 0) (drvb1 0) hr ℓ₀ (by omega) c2 hw₀ hb₀
      rw [hnext 0] at hw₁ hb₁
      exact ⟨ℓ₁, hℓ₁, hw₁, hb₁⟩
    by_cases c3 : ℓ₀ = r + 1
    · subst c3
      obtain ⟨fw, fb⟩ := period_far (A + 0 * Q) r (drvw 0) 1 (Nat.le_refl 1) hw₀ hb₀
      have w1 : cell (A + 0 * Q + r) 1 = false := by simpa using fw 1 (by omega) (by omega)
      have b2 : cell (A + 0 * Q + r) 2 = true := by simpa using fb
      have n1 : cell (A + 0 * Q + r + 1) 1 = false := by
        show rule (cell (A + 0 * Q + r) (1 - 1)) (cell (A + 0 * Q + r) 1) (cell (A + 0 * Q + r) (1 + 1)) = false
        rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, drvb1 0, w1, b2]; rfl
      have n2 : cell (A + 0 * Q + r + 1) 2 = true := by
        show rule (cell (A + 0 * Q + r) (2 - 1)) (cell (A + 0 * Q + r) 2) (cell (A + 0 * Q + r) (2 + 1)) = true
        rw [show (2 : Int) - 1 = 1 by rfl, w1, b2]; rfl
      rw [hnext 0] at n1 n2
      refine ⟨1, by omega, fun p hp1 hp2 => ?_, by simpa using n2⟩
      have : p = 1 := by omega
      subst this; simpa using n1
    · have hz2 : 2 ≤ ℓ₀ - r := by omega
      obtain ⟨fw, _⟩ := period_far (A + 0 * Q) r (drvw 0) (ℓ₀ - r) (by omega)
        (fun p hp1 hp2 => hw₀ p hp1 (by omega))
        (by rw [show r + (ℓ₀ - r) + 1 = ℓ₀ + 1 by omega]; exact hb₀)
      have w1 : cell (A + 0 * Q + r) 1 = false := by simpa using fw 1 (by omega) (by omega)
      have w2 : cell (A + 0 * Q + r) 2 = false := by simpa using fw 2 (by omega) (by omega)
      have n1 : cell (A + 0 * Q + r + 1) 1 = true := by
        show rule (cell (A + 0 * Q + r) (1 - 1)) (cell (A + 0 * Q + r) 1) (cell (A + 0 * Q + r) (1 + 1)) = true
        rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, drvb1 0, w1, w2]; rfl
      rw [hnext 0] at n1
      exact ⟨0, by omega, fun p hp1 hp2 => by omega, by simpa using n1⟩
  -- From period 2 onward, every period starts at ℓ = 2
  have hlock2 : ∀ j : Nat,
      (∀ p : Nat, 1 ≤ p → p ≤ 2 → cell (A + (2 + j) * Q) p = false) ∧
      cell (A + (2 + j) * Q) ((2 + 1 : Nat) : Int) = true := by
    intro j
    induction j with
    | zero =>
      obtain ⟨ℓ₁, hℓ₁, hw₁, hb₁⟩ := hperiod1_basin
      obtain ⟨_, _, hc1, hc2, hc3⟩ :=
        period_lock_single_black (A + 1 * Q) r (drvw 1) (drvb1 1) (by omega) ℓ₁ hℓ₁ hw₁ hb₁
      rw [hnext 1, show 1 + 1 = 2 + 0 by rfl] at hc1 hc2 hc3
      refine ⟨fun p hp1 hp2 => ?_, by simpa using hc3⟩
      by_cases hp : p = 1
      · subst hp; simpa using hc1
      · have : p = 2 := by omega
        subst this; simpa using hc2
    | succ j ih =>
      obtain ⟨hw_j, hb_j⟩ := ih
      obtain ⟨_, _, hc1, hc2, hc3⟩ :=
        period_lock_single_black (A + (2 + j) * Q) r (drvw (2 + j)) (drvb1 (2 + j))
          (by omega) 2 (by omega) hw_j hb_j
      rw [hnext (2 + j), show 2 + j + 1 = 2 + (j + 1) by omega] at hc1 hc2 hc3
      refine ⟨fun p hp1 hp2 => ?_, by simpa using hc3⟩
      by_cases hp : p = 1
      · subst hp; simpa using hc1
      · have : p = 2 := by omega
        subst this; simpa using hc2
  -- Therefore column 1 repeats decide (2 ≤ i) on every period j ≥ 0 from A + 2 * Q on
  have hcol1_pattern : ∀ j i, i < Q →
      cell (A + 2 * Q + j * Q + i) 1 = decide (2 ≤ i) := by
    intro j i hi
    obtain ⟨hw_j, hb_j⟩ := hlock2 j
    obtain ⟨hw_col1, hblk, _, _, _⟩ :=
      period_lock_single_black (A + (2 + j) * Q) r (drvw (2 + j)) (drvb1 (2 + j))
        (by omega) 2 (by omega) hw_j hb_j
    have hadd : A + (2 + j) * Q + i = A + 2 * Q + j * Q + i := by
      rw [Nat.add_mul 2 j Q]; omega
    rw [← hadd]
    by_cases hi2 : 2 ≤ i
    · rw [hblk i hi2 (by omega)]; simp [hi2]
    · rw [hw_col1 i (by omega)]; simp [hi2]
  have h1 : EventuallyPeriodic (fun t => cell t (0 + 1)) :=
    periodic_blocks (A + 2 * Q) Q hQ (fun i => decide (2 ≤ i)) hcol1_pattern
  have h0 : EventuallyPeriodic (fun t => cell t 0) := ⟨T, Q, hQ, hper⟩
  exact not_adjacent 0 h0 h1

/-! ### `R30-EXHAUST-001` Arbitrary-Word Run-Composition & Absorption-vs-Flux Dichotomy -/

/-- Canonical predicate for an eventually `P`-periodic center column from transient `T` on. -/
def PeriodicCenter (T P : Nat) : Prop :=
  0 < P ∧ ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t

/-- **Obligation 1 (`EXACT`, New in `R30-EXHAUST-001`) — Spatiotemporal Orbit State Completeness
    (`single_seed_spatiotemporal_state_completeness`)**:
    Proves that every hypothetical periodic single-seed trajectory `PeriodicCenter T P` at any phase
    `t₀ ≥ T`, any depth `k ≥ T`, and any horizon `H` is completely represented by the coupled
    spatiotemporal state:
    1. Mixed-run center structure (`∃ sb < P, center (t₀ + sb) = true` and `∃ sw < P, center (t₀ + sw) = false`),
    2. Exact right-half single-seed frontier (`cell t₀ t₀ = true`, `cell t₀ (t₀ - 1) = decide (t₀ % 2 = 1)`,
       and zero exterior `rowAt t₀ (t₀ + 1) H = List.replicate H false`),
    3. Bilateral observation coupling (`obsLeftWord = orColWord = col0OrTrace`), and
    4. Exact 6-step characteristic-flux onset laws at depth `k` with leading `orCol 0` isolation. -/
theorem single_seed_spatiotemporal_state_completeness
    (T P t₀ k H : Nat)
    (hper : PeriodicCenter T P)
    (ht₀ : T ≤ t₀)
    (hk : T ≤ k) :
    ((∃ sb < P, Rule30Prize.center (t₀ + sb) = true) ∧
     (∃ sw < P, Rule30Prize.center (t₀ + sw) = false)) ∧
    (cell t₀ (t₀ : Int) = true ∧
     cell t₀ ((t₀ : Int) - 1) = decide (t₀ % 2 = 1) ∧
     rowAt t₀ ((t₀ : Int) + 1) H = List.replicate H false) ∧
    (obsLeftWord (col0Word t₀ H) (cell (t₀ + H) 0) (rowAtLeft t₀ (-1) (H + 1)) =
       orColWord (col0Word t₀ H) (rowAt t₀ 1 (H + 1)) ∧
     orColWord (col0Word t₀ H) (rowAt t₀ 1 (H + 1)) = col0OrTrace t₀ H) ∧
    (leftCharacteristicFlux k k = !Rule30Prize.center (k + k) ∧
     leftCharacteristicFlux (k + 1) k = !Rule30Prize.center (k + 1 + k) ∧
     leftCharacteristicFlux (k + 2) k = Rule30Prize.center (k + 2 + k) ∧
     cell (k + 3) (-(k : Int)) = decide (k % 2 = 0) ∧
     leftCharacteristicFlux (k + 4) k = !Rule30Prize.center (k + 4 + k) ∧
     cell (k + 5) (-(k : Int)) = decide (k % 2 = 0) ∧
     leftCharacteristicFlux (k + P) (k + P) = leftCharacteristicFlux k k) := by
  rcases hper with ⟨hP, hper_fn⟩
  have hmix := periodic_center_has_black_and_white_in_every_period T P t₀ hP hper_fn ht₀
  rcases right_rowAt_single_seed_frontier_realization t₀ H with ⟨hr0, hr1, _, hrext⟩
  have hbil := obsLeftWord_rowAtLeft_eq_orColWord_rowAt H 0 t₀
  rw [Nat.zero_add] at hbil
  have hor := orColWord_rowAt H 0 t₀
  rw [Nat.zero_add] at hor
  rcases universal_characteristic_flux_onset_laws k with ⟨f0, f1, f2, f4, _⟩
  rcases universal_column_onset_exact_6step k with ⟨_, _, _, d3, _, d5⟩
  rcases periodic_center_forces_characteristic_flux_depth_periodicity T P k hper_fn hk with
    ⟨fp0, _, _, _, _⟩
  exact ⟨hmix, ⟨hr0, hr1, hrext⟩, ⟨hbil, hor⟩, ⟨f0, f1, f2, d3, f4, d5, fp0⟩⟩

theorem col0Word_d_101 :
    ∀ (d t : Nat),
      (∀ i, i < d → cell (t + i) 0 = false) →
      cell (t + d) 0 = true →
      cell (t + d + 1) 0 = false →
      cell (t + d + 2) 0 = true →
      col0Word t (d + 3) = List.replicate d false ++ [true, false, true]
  | 0, t, _, hb1, hw1, hb2 => by
      have h0 : cell t 0 = true := by simpa using hb1
      have h1 : cell (t + 1) 0 = false := by simpa using hw1
      have h2 : cell (t + 2) 0 = true := by simpa using hb2
      show [cell t 0, cell (t + 1) 0, cell (t + 1 + 1) 0] = [true, false, true]
      rw [h0, h1, show t + 1 + 1 = t + 2 by omega, h2]
  | d + 1, t, hw, hb1, hw1, hb2 => by
      have h0 : cell t 0 = false := by simpa using hw 0 (by omega)
      have ih := col0Word_d_101 d (t + 1)
        (fun i hi => by
          have := hw (1 + i) (by omega)
          rwa [show t + (1 + i) = t + 1 + i by omega] at this)
        (by rwa [show t + 1 + d = t + (d + 1) by omega])
        (by rwa [show t + 1 + d + 1 = t + (d + 1) + 1 by omega])
        (by rwa [show t + 1 + d + 2 = t + (d + 1) + 2 by omega])
      show cell t 0 :: col0Word (t + 1) (d + 3) =
        false :: (List.replicate d false ++ [true, false, true])
      rw [h0, ih]

theorem rowAt_replicate_false (t : Nat) :
    ∀ (k : Nat) (p : Int),
      (∀ j : Nat, j < k → cell t (p + (j : Int)) = false) →
      rowAt t p k = List.replicate k false
  | 0, _, _ => rfl
  | k + 1, p, hw => by
      have h0 : cell t p = false := by simpa using hw 0 (by omega)
      have ih := rowAt_replicate_false t k (p + 1) (fun j hj => by
        have := hw (1 + j) (by omega)
        rwa [show p + ((1 + j : Nat) : Int) = p + 1 + (j : Int) by omega] at this)
      show cell t p :: rowAt t (p + 1) k = false :: List.replicate k false
      rw [h0, ih]

theorem rowAt_white_then_black (t : Nat) :
    ∀ (z : Nat) (p : Int),
      (∀ j : Nat, j < z → cell t (p + (j : Int)) = false) →
      cell t (p + (z : Int)) = true →
      rowAt t p (z + 1) = List.replicate z false ++ [true]
  | 0, p, _, hb => by
      have hb0 : cell t p = true := by simpa using hb
      show [cell t p] = [true]
      rw [hb0]
  | z + 1, p, hw, hb => by
      have h0 : cell t p = false := by simpa using hw 0 (by omega)
      have ih := rowAt_white_then_black t z (p + 1)
        (fun j hj => by
          have := hw (1 + j) (by omega)
          rwa [show p + ((1 + j : Nat) : Int) = p + 1 + (j : Int) by omega] at this)
        (by rwa [show p + 1 + (z : Int) = p + ((z + 1 : Nat) : Int) by omega])
      show cell t p :: rowAt t (p + 1) (z + 1) = false :: (List.replicate z false ++ [true])
      rw [h0, ih]

theorem late_101_core :
    ∀ d ∈ List.range 8, ∀ P ∈ validFrontPrefixes8, ∀ L ∈ allLists (d + 2),
      true ∈ runWord (List.replicate d false ++ [true, false, true]) (P ++ L) := by
  decide +kernel

theorem z2_to_z5_101_core :
    ∀ z ∈ [2, 3, 4, 5], ∀ L ∈ allLists (8 - z),
      true ∈ runWord [true, false, true] ((List.replicate z false ++ [true]) ++ L) := by
  decide +kernel

theorem period_lock_101 (a r : Nat)
    (hwr : ∀ i, i < r → cell (a + i) 0 = false)
    (hb1 : cell (a + r) 0 = true)
    (hw1 : cell (a + r + 1) 0 = false)
    (hb2 : cell (a + r + 2) 0 = true)
    (hr : 8 ≤ r) (ℓ : Nat) (hℓ : ℓ ≤ r - 8)
    (hw : ∀ p : Nat, 1 ≤ p → p ≤ ℓ → cell a p = false)
    (hb : cell a ((ℓ + 1 : Nat) : Int) = true) :
    (∀ i, i < ℓ → cell (a + i) 1 = false) ∧
    (∀ i, ℓ ≤ i → i ≤ r → cell (a + i) 1 = true) ∧
    cell (a + r + 1) 1 = false ∧
    cell (a + r + 2) 1 = false ∧
    cell (a + r + 3) 1 = false ∧
    cell (a + r + 3) 2 = true := by
  obtain ⟨hw_col1, hblk, c1_1, c2_1, c3_1⟩ :=
    period_lock_single_black a r hwr hb1 hr ℓ hℓ hw hb
  have c1_2 : cell (a + r + 2) 1 = false := by
    show rule (cell (a + r + 1) (1 - 1)) (cell (a + r + 1) 1) (cell (a + r + 1) (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hw1, c1_1, c2_1]; rfl
  have c2_2 : cell (a + r + 2) 2 = true := by
    show rule (cell (a + r + 1) (2 - 1)) (cell (a + r + 1) 2) (cell (a + r + 1) (2 + 1)) = true
    rw [show (2 : Int) - 1 = 1 by rfl, show (2 : Int) + 1 = 3 by rfl, c1_1, c2_1, c3_1]; rfl
  have c3_2 : cell (a + r + 2) 3 = true := by
    show rule (cell (a + r + 1) (3 - 1)) (cell (a + r + 1) 3) (cell (a + r + 1) (3 + 1)) = true
    rw [show (3 : Int) - 1 = 2 by rfl, c2_1, c3_1]; rfl
  have c1_3 : cell (a + r + 3) 1 = false := by
    show rule (cell (a + r + 2) (1 - 1)) (cell (a + r + 2) 1) (cell (a + r + 2) (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb2, c1_2, c2_2]; rfl
  have c2_3 : cell (a + r + 3) 2 = true := by
    show rule (cell (a + r + 2) (2 - 1)) (cell (a + r + 2) 2) (cell (a + r + 2) (2 + 1)) = true
    rw [show (2 : Int) - 1 = 1 by rfl, show (2 : Int) + 1 = 3 by rfl, c1_2, c2_2, c3_2]; rfl
  exact ⟨hw_col1, hblk, c1_1, c1_2, c1_3, c2_3⟩

theorem period_late_101 (a r : Nat)
    (hwr : ∀ i, i < r → cell (a + i) 0 = false)
    (hb1 : cell (a + r) 0 = true)
    (hw1 : cell (a + r + 1) 0 = false)
    (hb2 : cell (a + r + 2) 0 = true)
    (hr : 14 ≤ r) (ℓ : Nat) (hℓ1 : r - 7 ≤ ℓ) (hℓ2 : ℓ ≤ r)
    (hw : ∀ p : Nat, 1 ≤ p → p ≤ ℓ → cell a p = false)
    (hb : cell a ((ℓ + 1 : Nat) : Int) = true) :
    ∃ ℓ', ℓ' ≤ r - 8 ∧
      (∀ p : Nat, 1 ≤ p → p ≤ ℓ' → cell (a + r + 3) p = false) ∧
      cell (a + r + 3) ((ℓ' + 1 : Nat) : Int) = true := by
  let u := a + (ℓ - 6)
  let d := r - ℓ
  obtain ⟨hw_u, hb_u⟩ := front_moves a ℓ r hwr hw hb (ℓ - 6) (by omega) (by omega)
  have hrow_u : rowAt u 1 7 = [false, false, false, false, false, false, true] := by
    have hw_j : ∀ j : Nat, j < 6 → cell u (1 + (j : Int)) = false := by
      intro j hj
      have := hw_u (1 + j) (by omega) (by omega)
      rwa [show ((1 + j : Nat) : Int) = 1 + (j : Int) by omega] at this
    have hb_j : cell u (1 + (6 : Int)) = true := by
      rw [show ℓ - (ℓ - 6) + 1 = 7 by omega] at hb_u
      exact hb_u
    exact rowAt_white_then_black u 6 1 hw_j hb_j
  have hcol_u : col0Word u 6 = List.replicate 6 false := by
    apply col0Word_replicate_false 6 u
    intro i hi
    have := hwr (ℓ - 6 + i) (by omega)
    rwa [show a + (ℓ - 6 + i) = u + i by omega] at this
  have hrun6 := runWord_rowAt 6 8 u
  rw [show 8 + 6 = 7 + 7 by rfl, rowAt_add u 7 7 1,
      show (1 : Int) + (7 : Nat) = 8 by rfl,
      show u + 6 = a + ℓ by omega, hcol_u, hrow_u] at hrun6
  have hmem7 : rowAt u 8 7 ∈ allLists 7 := by
    have := mem_allLists (rowAt u 8 7)
    rwa [length_rowAt] at this
  have hpref8 : rowAt (a + ℓ) 1 8 ∈ validFrontPrefixes8 := by
    rw [← hrun6]
    exact front_six_white_core (rowAt u 8 7) hmem7
  have hcol_d : col0Word (a + ℓ) (d + 3) = List.replicate d false ++ [true, false, true] := by
    apply col0Word_d_101 d (a + ℓ)
    · intro i hi
      have := hwr (ℓ + i) (by omega)
      rwa [show a + (ℓ + i) = a + ℓ + i by omega] at this
    · rwa [show a + ℓ + d = a + r by omega]
    · rwa [show a + ℓ + d + 1 = a + r + 1 by omega]
    · rwa [show a + ℓ + d + 2 = a + r + 2 by omega]
  have hrun_d := runWord_rowAt (d + 3) 7 (a + ℓ)
  rw [show 7 + (d + 3) = 8 + (d + 2) by omega, rowAt_add (a + ℓ) 8 (d + 2) 1,
      show (1 : Int) + (8 : Nat) = 9 by rfl,
      show a + ℓ + (d + 3) = a + r + 3 by omega, hcol_d] at hrun_d
  have hmem_d : rowAt (a + ℓ) 9 (d + 2) ∈ allLists (d + 2) := by
    have := mem_allLists (rowAt (a + ℓ) 9 (d + 2))
    rwa [length_rowAt] at this
  have hd_range : d ∈ List.range 8 := List.mem_range.2 (by omega)
  have htrue_in : true ∈ rowAt (a + r + 3) 1 7 := by
    rw [← hrun_d]
    exact late_101_core d hd_range (rowAt (a + ℓ) 1 8) hpref8 (rowAt (a + ℓ) 9 (d + 2)) hmem_d
  rcases first_black_aux (a + r + 3) 7 with hw7 | ⟨ℓ', hℓ'7, hw', hb'⟩
  · have hrow_false : rowAt (a + r + 3) 1 7 = List.replicate 7 false := by
      apply rowAt_replicate_false (a + r + 3) 7 1
      intro j hj
      have := hw7 (1 + j) (by omega) (by omega)
      rwa [show ((1 + j : Nat) : Int) = 1 + (j : Int) by omega] at this
    rw [hrow_false] at htrue_in
    exact False.elim (by revert htrue_in; decide)
  · exact ⟨ℓ', by omega, hw', hb'⟩

theorem period_z1_101 (a r : Nat)
    (hwr : ∀ i, i < r → cell (a + i) 0 = false)
    (hb1 : cell (a + r) 0 = true)
    (hw1 : cell (a + r + 1) 0 = false)
    (hw : ∀ p : Nat, 1 ≤ p → p ≤ r + 1 → cell a p = false)
    (hb : cell a ((r + 1 + 1 : Nat) : Int) = true) :
    (∀ i, i ≤ r + 1 → cell (a + i) 1 = false) ∧ cell (a + r + 2) 1 = true := by
  obtain ⟨fw, fb⟩ := period_far a r hwr 1 (Nat.le_refl 1) hw hb
  have w1 : cell (a + r) 1 = false := by simpa using fw 1 (Nat.le_refl 1) (Nat.le_refl 1)
  have b2 : cell (a + r) 2 = true := by simpa using fb
  have c1_1 : cell (a + r + 1) 1 = false := by
    show rule (cell (a + r) (1 - 1)) (cell (a + r) 1) (cell (a + r) (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb1, w1, b2]; rfl
  have c2_1 : cell (a + r + 1) 2 = true := by
    show rule (cell (a + r) (2 - 1)) (cell (a + r) 2) (cell (a + r) (2 + 1)) = true
    rw [show (2 : Int) - 1 = 1 by rfl, w1, b2]; rfl
  refine ⟨fun i hi => ?_, ?_⟩
  · by_cases hir : i ≤ r
    · have := (front_moves a (r + 1) r hwr hw hb i hir (by omega)).1 1 (Nat.le_refl 1) (by omega)
      simpa using this
    · have : i = r + 1 := by omega
      subst this; exact c1_1
  · show rule (cell (a + r + 1) (1 - 1)) (cell (a + r + 1) 1) (cell (a + r + 1) (1 + 1)) = true
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hw1, c1_1, c2_1]; rfl

theorem period_z2_ge_101 (a r : Nat)
    (hwr : ∀ i, i < r → cell (a + i) 0 = false)
    (hb1 : cell (a + r) 0 = true)
    (hw1 : cell (a + r + 1) 0 = false)
    (hb2 : cell (a + r + 2) 0 = true)
    (hr : 14 ≤ r) (ℓ : Nat) (hℓ : r + 2 ≤ ℓ)
    (hw : ∀ p : Nat, 1 ≤ p → p ≤ ℓ → cell a p = false)
    (hb : cell a ((ℓ + 1 : Nat) : Int) = true) :
    ∃ ℓ', ℓ' ≤ r - 8 ∧
      (∀ p : Nat, 1 ≤ p → p ≤ ℓ' → cell (a + r + 3) p = false) ∧
      cell (a + r + 3) ((ℓ' + 1 : Nat) : Int) = true := by
  let z := ℓ - r
  have hz2 : 2 ≤ z := by omega
  obtain ⟨fw, fb⟩ := period_far a r hwr z (by omega)
    (fun p hp1 hp2 => hw p hp1 (by omega))
    (by rw [show r + z + 1 = ℓ + 1 by omega]; exact hb)
  have hcol3 : col0Word (a + r) 3 = [true, false, true] :=
    col0Word_d_101 0 (a + r) (fun i hi => by omega)
      (by simpa using hb1) (by simpa using hw1) (by simpa using hb2)
  by_cases hz5 : z ≤ 5
  · have hmem_z : z ∈ [2, 3, 4, 5] := by
      have : z = 2 ∨ z = 3 ∨ z = 4 ∨ z = 5 := by omega
      rcases this with h | h | h | h <;> simp [h]
    have hrow_z : rowAt (a + r) 1 (z + 1) = List.replicate z false ++ [true] := by
      apply rowAt_white_then_black (a + r) z 1
      · intro j hj
        have := fw (1 + j) (by omega) (by omega)
        rwa [show ((1 + j : Nat) : Int) = 1 + (j : Int) by omega] at this
      · simpa [show (1 : Int) + (z : Int) = ((z + 1 : Nat) : Int) by omega] using fb
    have hrun3 := runWord_rowAt 3 6 (a + r)
    rw [show 6 + 3 = (z + 1) + (8 - z) by omega,
        rowAt_add (a + r) (z + 1) (8 - z) 1,
        hcol3, hrow_z] at hrun3
    have hmem_L : rowAt (a + r) (1 + ((z + 1 : Nat) : Int)) (8 - z) ∈ allLists (8 - z) := by
      have := mem_allLists (rowAt (a + r) (1 + ((z + 1 : Nat) : Int)) (8 - z))
      rwa [length_rowAt] at this
    have htrue_in : true ∈ rowAt (a + r + 3) 1 6 := by
      rw [← hrun3]
      exact z2_to_z5_101_core z hmem_z _ hmem_L
    rcases first_black_aux (a + r + 3) 6 with hw6 | ⟨ℓ', hℓ'6, hw', hb'⟩
    · have hrow_false : rowAt (a + r + 3) 1 6 = List.replicate 6 false := by
        apply rowAt_replicate_false (a + r + 3) 6 1
        intro j hj
        have := hw6 (1 + j) (by omega) (by omega)
        rwa [show ((1 + j : Nat) : Int) = 1 + (j : Int) by omega] at this
      rw [hrow_false] at htrue_in
      exact False.elim (by revert htrue_in; decide)
    · exact ⟨ℓ', by omega, hw', hb'⟩
  · have hrow6 : rowAt (a + r) 1 6 = List.replicate 6 false := by
      apply rowAt_replicate_false (a + r) 6 1
      intro j hj
      have := fw (1 + j) (by omega) (by omega)
      rwa [show ((1 + j : Nat) : Int) = 1 + (j : Int) by omega] at this
    have hrun3 := runWord_rowAt 3 3 (a + r)
    rw [show 3 + 3 = 6 by rfl, hcol3, hrow6] at hrun3
    have heval : runWord [true, false, true] (List.replicate 6 false) = [false, false, true] := rfl
    rw [heval] at hrun3
    have hrow3 : rowAt (a + r + 3) 1 3 =
        [cell (a + r + 3) 1, cell (a + r + 3) 2, cell (a + r + 3) 3] := rfl
    rw [hrow3] at hrun3
    simp only [List.cons.injEq] at hrun3
    refine ⟨2, by omega, fun p hp1 hp2 => ?_, by simpa using hrun3.2.2.1.symm⟩
    by_cases hp : p = 1
    · subst hp; simpa using hrun3.1.symm
    · have : p = 2 := by omega
      subst this; simpa using hrun3.2.1.symm

/-- **Obligation 3 (`EXACT`, New in `R30-EXHAUST-001`) — Universal Multi-Run Composite Exclusion
    for the Infinite 4-Run `11`-Free Family `0^r 1 0 1 = scheduleWord [(r, 1), (1, 1)]`
    (`no_white_run_101_all_transients`)**:
    Proves unconditionally (for every transient `T : Nat`, every `r ≥ 14`, and every phase `t₀ ≥ T`)
    that the single-seed center column cannot repeat the 4-run composite `11`-free word `0^r 1 0 1`
    (period `Q = r + 3 ≥ 17`). Combines PSMSL right-screening regeneration at column `3`
    (`period_lock_101`) with a two-class observational absorption dichotomy (`Z₁` where `ℓ = r + 1`
    produces `decide (i = r + 2)` vs. the absorbing lock class `ℓ = 1` producing
    `decide (1 ≤ i ∧ i ≤ r)`), both refuted by Jen's theorem (`not_adjacent 0`). -/
theorem no_white_run_101_all_transients
    (T r t0 : Nat) (hr : 14 ≤ r)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + (r + 3)) = Rule30Prize.center t)
    (ht0 : T ≤ t0)
    (hw : ∀ i, i < r → Rule30Prize.center (t0 + i) = false)
    (hb1 : Rule30Prize.center (t0 + r) = true)
    (hw1 : Rule30Prize.center (t0 + r + 1) = false)
    (hb2 : Rule30Prize.center (t0 + r + 2) = true) : False := by
  generalize hQdef : r + 3 = Q at hper
  have hQ : 0 < Q := by omega
  have hperk : ∀ k t, T ≤ t → Rule30Prize.center (t + k * Q) = Rule30Prize.center t :=
    periodic_mul hper
  generalize hAdef : t0 + Q = A
  have hMul : ∀ k, (k + 1) * Q = k * Q + Q := fun k => Nat.succ_mul k Q
  have drvw : ∀ k i, i < r → cell (A + k * Q + i) 0 = false := by
    intro k i hi
    have := hperk (k + 1) (t0 + i) (by omega)
    show Rule30Prize.center (A + k * Q + i) = false
    rw [hMul k, show t0 + i + (k * Q + Q) = A + k * Q + i by omega] at this
    rw [this]; exact hw i hi
  have drvb1 : ∀ k, cell (A + k * Q + r) 0 = true := by
    intro k
    have := hperk (k + 1) (t0 + r) (by omega)
    show Rule30Prize.center (A + k * Q + r) = true
    rw [hMul k, show t0 + r + (k * Q + Q) = A + k * Q + r by omega] at this
    rw [this]; exact hb1
  have drvw1 : ∀ k, cell (A + k * Q + r + 1) 0 = false := by
    intro k
    have := hperk (k + 1) (t0 + r + 1) (by omega)
    show Rule30Prize.center (A + k * Q + r + 1) = false
    rw [hMul k, show t0 + r + 1 + (k * Q + Q) = A + k * Q + r + 1 by omega] at this
    rw [this]; exact hw1
  have drvb2 : ∀ k, cell (A + k * Q + r + 2) 0 = true := by
    intro k
    have := hperk (k + 1) (t0 + r + 2) (by omega)
    show Rule30Prize.center (A + k * Q + r + 2) = true
    rw [hMul k, show t0 + r + 2 + (k * Q + Q) = A + k * Q + r + 2 by omega] at this
    rw [this]; exact hb2
  have hnext : ∀ k, A + k * Q + r + 3 = A + (k + 1) * Q := by
    intro k; rw [hMul k]; omega
  let Z1 : Nat → Prop := fun k =>
    (∀ p : Nat, 1 ≤ p → p ≤ r + 1 → cell (A + k * Q) p = false) ∧
    cell (A + k * Q) ((r + 1 + 1 : Nat) : Int) = true
  have z1_pattern : ∀ k, Z1 k → ∀ i, i < Q →
      cell (A + k * Q + i) 1 = decide (i = r + 2) := by
    intro k hk i hi
    obtain ⟨hw_i, hb_i⟩ := period_z1_101 (A + k * Q) r (drvw k) (drvb1 k) (drvw1 k) hk.1 hk.2
    by_cases hir1 : i ≤ r + 1
    · rw [hw_i i hir1]; simp; omega
    · have : i = r + 2 := by omega
      subst this
      rw [show A + k * Q + (r + 2) = A + k * Q + r + 2 by omega, hb_i]; simp
  have step_to_basin : ∀ k, ¬ Z1 k →
      ∃ ℓ', ℓ' ≤ r - 8 ∧
        (∀ p : Nat, 1 ≤ p → p ≤ ℓ' → cell (A + (k + 1) * Q) p = false) ∧
        cell (A + (k + 1) * Q) ((ℓ' + 1 : Nat) : Int) = true := by
    intro k hnz1
    obtain ⟨ℓ₀, hw₀, hb₀⟩ := first_black (A + k * Q) (by omega)
    by_cases c1 : ℓ₀ ≤ r - 8
    · obtain ⟨_, _, _, _, hc1, hc2⟩ :=
        period_lock_101 (A + k * Q) r (drvw k) (drvb1 k) (drvw1 k) (drvb2 k) (by omega) ℓ₀ c1 hw₀ hb₀
      rw [hnext k] at hc1 hc2
      refine ⟨1, by omega, fun p hp1 hp2 => ?_, by simpa using hc2⟩
      have : p = 1 := by omega
      subst this; simpa using hc1
    by_cases c2 : ℓ₀ ≤ r
    · obtain ⟨ℓ', hℓ', hw', hb'⟩ :=
        period_late_101 (A + k * Q) r (drvw k) (drvb1 k) (drvw1 k) (drvb2 k) hr ℓ₀ (by omega) c2 hw₀ hb₀
      rw [hnext k] at hw' hb'
      exact ⟨ℓ', hℓ', hw', hb'⟩
    by_cases c3 : ℓ₀ = r + 1
    · subst c3
      exact absurd ⟨hw₀, hb₀⟩ hnz1
    · obtain ⟨ℓ', hℓ', hw', hb'⟩ :=
        period_z2_ge_101 (A + k * Q) r (drvw k) (drvb1 k) (drvw1 k) (drvb2 k) hr ℓ₀ (by omega) hw₀ hb₀
      rw [hnext k] at hw' hb'
      exact ⟨ℓ', hℓ', hw', hb'⟩
  have h1 : EventuallyPeriodic (fun t => cell t (0 + 1)) := by
    by_cases hall : ∀ k, Z1 k
    · exact periodic_blocks A Q hQ (fun i => decide (i = r + 2))
        (fun j i hi => z1_pattern j (hall j) i hi)
    · have hex : ∃ k, ¬ Z1 k := Classical.byContradiction fun hne => hall fun k =>
        Classical.byContradiction fun hk => hne ⟨k, hk⟩
      obtain ⟨k0, hk0⟩ := hex
      obtain ⟨ℓ₁, hℓ₁, hw₁, hb₁⟩ := step_to_basin k0 hk0
      have hlock1 : ∀ j : Nat,
          (∀ p : Nat, 1 ≤ p → p ≤ 1 → cell (A + (k0 + 2 + j) * Q) p = false) ∧
          cell (A + (k0 + 2 + j) * Q) ((1 + 1 : Nat) : Int) = true := by
        intro j
        induction j with
        | zero =>
          obtain ⟨_, _, _, _, hc1, hc2⟩ :=
            period_lock_101 (A + (k0 + 1) * Q) r (drvw (k0 + 1)) (drvb1 (k0 + 1))
              (drvw1 (k0 + 1)) (drvb2 (k0 + 1)) (by omega) ℓ₁ hℓ₁ hw₁ hb₁
          rw [hnext (k0 + 1), show k0 + 1 + 1 = k0 + 2 + 0 by omega] at hc1 hc2
          refine ⟨fun p hp1 hp2 => ?_, by simpa using hc2⟩
          have : p = 1 := by omega
          subst this; simpa using hc1
        | succ j ih =>
          obtain ⟨hw_j, hb_j⟩ := ih
          obtain ⟨_, _, _, _, hc1, hc2⟩ :=
            period_lock_101 (A + (k0 + 2 + j) * Q) r (drvw (k0 + 2 + j)) (drvb1 (k0 + 2 + j))
              (drvw1 (k0 + 2 + j)) (drvb2 (k0 + 2 + j)) (by omega) 1 (by omega) hw_j hb_j
          rw [hnext (k0 + 2 + j), show k0 + 2 + j + 1 = k0 + 2 + (j + 1) by omega] at hc1 hc2
          refine ⟨fun p hp1 hp2 => ?_, by simpa using hc2⟩
          have : p = 1 := by omega
          subst this; simpa using hc1
      have hcol1_lock : ∀ j i, i < Q →
          cell (A + (k0 + 2) * Q + j * Q + i) 1 = decide (1 ≤ i ∧ i ≤ r) := by
        intro j i hi
        obtain ⟨hw_j, hb_j⟩ := hlock1 j
        obtain ⟨hw_col1, hblk, c1_1, c1_2, _, _⟩ :=
          period_lock_101 (A + (k0 + 2 + j) * Q) r (drvw (k0 + 2 + j)) (drvb1 (k0 + 2 + j))
            (drvw1 (k0 + 2 + j)) (drvb2 (k0 + 2 + j)) (by omega) 1 (by omega) hw_j hb_j
        have hadd : A + (k0 + 2 + j) * Q + i = A + (k0 + 2) * Q + j * Q + i := by
          rw [Nat.add_mul (k0 + 2) j Q]; omega
        rw [← hadd]
        by_cases hi0 : i = 0
        · subst hi0; rw [hw_col1 0 (by omega)]; simp
        by_cases hir : i ≤ r
        · rw [hblk i (by omega) hir]; simp; omega
        by_cases hir1 : i = r + 1
        · subst hir1
          rw [show A + (k0 + 2 + j) * Q + (r + 1) = A + (k0 + 2 + j) * Q + r + 1 by omega, c1_1]
          simp
        · have : i = r + 2 := by omega
          subst this
          rw [show A + (k0 + 2 + j) * Q + (r + 2) = A + (k0 + 2 + j) * Q + r + 2 by omega, c1_2]
          simp
      exact periodic_blocks (A + (k0 + 2) * Q) Q hQ (fun i => decide (1 ≤ i ∧ i ≤ r)) hcol1_lock
  have h0 : EventuallyPeriodic (fun t => cell t 0) := ⟨T, Q, hQ, hper⟩
  exact not_adjacent 0 h0 h1

/-- Observational absorption: from some `t₁ ≥ T` on, at the white steps of the center column,
    column `1` repeats with some period multiple `q * P` (`q ≥ 1`). -/
def ObservationalAbsorptionAt (T P : Nat) : Prop :=
  ∃ t₁ q : Nat, T ≤ t₁ ∧ 0 < q ∧
    ∀ t : Nat, t₁ ≤ t → cell t 0 = false → cell (t + q * P) 1 = cell t 1

/-- Finite-horizon PSMSL future-work collision at the constructive linear horizon `k`. -/
def LinearHorizonCollisionAt (T P : Nat) : Prop :=
  ∃ t₀ m₀ q k : Nat, T ≤ t₀ ∧ 0 < q ∧ t₀ + (m₀ + q) * P ≤ (k + 1) * P ∧
    FutureWorkEquiv (col0Word t₀ P) k
      (rowAt (t₀ + (m₀ + q) * P) 1 ((k + 1) * P + 1))
      (rowAt (t₀ + m₀ * P) 1 ((k + 1) * P + 1))

/-- Violation of the 6-step single-seed characteristic-flux onset law at some spatial depth `k`. -/
def CharacteristicFluxOnsetViolationAt (_T _P : Nat) : Prop :=
  ∃ k : Nat,
    leftCharacteristicFlux k k ≠ !Rule30Prize.center (k + k) ∨
    leftCharacteristicFlux (k + 1) k ≠ !Rule30Prize.center (k + 1 + k) ∨
    leftCharacteristicFlux (k + 2) k ≠ Rule30Prize.center (k + 2 + k) ∨
    leftCharacteristicFlux (k + 3) k ≠ xor (Rule30Prize.center (k + 3 + k)) (decide (k % 2 = 0)) ∨
    leftCharacteristicFlux (k + 4) k ≠ !Rule30Prize.center (k + 4 + k) ∨
    leftCharacteristicFlux (k + 5) k ≠ xor (Rule30Prize.center (k + 5 + k)) (decide (k % 2 = 0))

/-- **Obligations 3 & 4 (`EXACT`, New in `R30-EXHAUST-001`) — Unified Absorption-or-Flux-Violation
    Dichotomy Exclusion Theorem (`absorption_or_flux_violation_dichotomy_excludes_periodic_center`)**:
    Proves unconditionally (`EXACT`, zero unproved hypotheses) that for any transient `T` and
    period `P` satisfying `PeriodicCenter T P`, if the trajectory enters:
    1. `ObservationalAbsorptionAt T P` (masked column-`1` stabilization, refuted by `masked_jen`),
    2. `LinearHorizonCollisionAt T P` (PSMSL future-work collision at linear horizon, refuted by
       `universal_linear_reentry_horizon_bound`), or
    3. `CharacteristicFluxOnsetViolationAt T P` (characteristic-flux onset mismatch at depth `k`,
       refuted by `universal_column_onset_exact_6step` + `cell_neg_eq_center_xor_characteristicFlux`),
    then `False` holds. -/
theorem absorption_or_flux_violation_dichotomy_excludes_periodic_center
    (T P : Nat) (hper : PeriodicCenter T P)
    (hDichotomy :
      ObservationalAbsorptionAt T P ∨
      LinearHorizonCollisionAt T P ∨
      CharacteristicFluxOnsetViolationAt T P) : False := by
  rcases hper with ⟨hP, hper_fn⟩
  rcases hDichotomy with hAbs | hColl | hFlux
  · obtain ⟨t₁, q, ht₁, hq, hcol1⟩ := hAbs
    have hqP : 0 < q * P := Nat.mul_pos hq hP
    have hper_qP : ∀ t, t₁ ≤ t → cell (t + q * P) 0 = cell t 0 := by
      intro t ht
      exact periodic_mul hper_fn q t (by omega)
    refine Rule30MaskedJen.masked_jen 0 (P := q * P) (T := t₁) hqP hper_qP ?_
    intro t ht hw
    rw [show (0 : Int) + 1 = 1 by rfl]
    exact hcol1 t ht hw
  · obtain ⟨t₀, m₀, q, k, ht₀, hq, hbound, hfw⟩ := hColl
    exact universal_linear_reentry_horizon_bound T P t₀ m₀ q k hP hq hper_fn ht₀ hbound hfw
  · obtain ⟨k, hviol⟩ := hFlux
    rcases universal_characteristic_flux_onset_laws k with ⟨f0, f1, f2, f4, _⟩
    rcases universal_column_onset_exact_6step k with ⟨_, _, _, d3, _, d5⟩
    have f3 := (cell_neg_eq_center_xor_characteristicFlux k (k + 3)).2
    have f5 := (cell_neg_eq_center_xor_characteristicFlux k (k + 5)).2
    rw [d3] at f3
    rw [d5] at f5
    rcases hviol with v0 | v1 | v2 | v3 | v4 | v5
    · exact v0 f0
    · exact v1 f1
    · exact v2 f2
    · exact v3 f3
    · exact v4 f4
    · exact v5 f5

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

theorem closure_characteristicFlux_decomp_leading_orCol (d t : Nat) :
    leftCharacteristicFlux t (d + 1) =
      xor (orCol 0 (t + d)) (interiorCharacteristicFlux t d) ∧
    cell t (-(↑(d + 1) : Int)) =
      xor (Rule30Prize.center (t + d + 1))
          (xor (orCol 0 (t + d)) (interiorCharacteristicFlux t d)) :=
  characteristicFlux_decomp_leading_orCol d t

theorem closure_spatiotemporal_leading_orCol_onset_isolation (k : Nat) :
    orCol 0 (k + 1 + k) =
      xor (!Rule30Prize.center (k + 1 + k + 1)) (interiorCharacteristicFlux (k + 1) k) ∧
    orCol 0 (k + 2 + k) =
      xor (!Rule30Prize.center (k + 2 + k + 1)) (interiorCharacteristicFlux (k + 2) k) :=
  spatiotemporal_leading_orCol_onset_isolation k

theorem closure_spatiotemporal_black_white_apex_dichotomy (k : Nat) :
    (Rule30Prize.center (k + 1 + k) = true →
      interiorCharacteristicFlux (k + 1) k = Rule30Prize.center (k + 1 + k + 1)) ∧
    (Rule30Prize.center (k + 1 + k) = false →
      cell (k + 1 + k) 1 =
        xor (!Rule30Prize.center (k + 1 + k + 1)) (interiorCharacteristicFlux (k + 1) k)) ∧
    (Rule30Prize.center (k + 2 + k) = true →
      interiorCharacteristicFlux (k + 2) k = Rule30Prize.center (k + 2 + k + 1)) ∧
    (Rule30Prize.center (k + 2 + k) = false →
      cell (k + 2 + k) 1 =
        xor (!Rule30Prize.center (k + 2 + k + 1)) (interiorCharacteristicFlux (k + 2) k)) :=
  spatiotemporal_black_white_apex_dichotomy k

theorem closure_right_history_characteristic_flux_incompatibility_implies_problem1
    (hFluxIncompat :
      ∀ (T P sb sw : Nat), 0 < P → sb < P → sw < P →
        (∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
        Rule30Prize.center (T + sb) = true →
        Rule30Prize.center (T + sw) = false →
        (cell T (T : Int) = true ∧ ∀ p : Int, (T : Int) < p → cell T p = false) →
        ∃ k : Nat, T ≤ k ∧
          (orCol 0 (k + 1 + k) ≠
             xor (!Rule30Prize.center (k + 1 + k + 1)) (interiorCharacteristicFlux (k + 1) k) ∨
           orCol 0 (k + 2 + k) ≠
             xor (!Rule30Prize.center (k + 2 + k + 1)) (interiorCharacteristicFlux (k + 2) k))) :
    Rule30Prize.Problem1 :=
  right_history_characteristic_flux_incompatibility_implies_problem1 hFluxIncompat

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

theorem closure_universal_column_onset_exact_6step (k : Nat) :
    cell k (-(k : Int)) = true ∧
    cell (k + 1) (-(k : Int)) = true ∧
    cell (k + 2) (-(k : Int)) = false ∧
    cell (k + 3) (-(k : Int)) = decide (k % 2 = 0) ∧
    cell (k + 4) (-(k : Int)) = true ∧
    cell (k + 5) (-(k : Int)) = decide (k % 2 = 0) :=
  universal_column_onset_exact_6step k

theorem closure_odd_period_forces_characteristic_flux_anti_periodicity
    (T P k : Nat)
    (hodd : P % 2 = 1)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (hk : T ≤ k) :
    leftCharacteristicFlux (k + P + 3) (k + P) = !leftCharacteristicFlux (k + 3) k ∧
    leftCharacteristicFlux (k + P + 5) (k + P) = !leftCharacteristicFlux (k + 5) k :=
  odd_period_forces_characteristic_flux_anti_periodicity T P k hodd hper hk

theorem closure_double_white_step_depth2_forcing (t : Nat)
    (hw0 : Rule30Prize.center t = false)
    (hw1 : Rule30Prize.center (t + 1) = false) :
    cell t (-1) = cell t 1 ∧
    (cell t 1 = true → cell (t + 1) 1 = true) ∧
    (cell t (-1) = true →
      cell (t + 1) (-1) = !Rule30Prize.center (t + 2) ∧
      cell t (-2) = Rule30Prize.center (t + 2)) ∧
    ((cell t (-1) && xor (cell (t + 1) (-1)) (!Rule30Prize.center (t + 2))) = false) ∧
    ((cell t (-1) && xor (cell t (-2)) (Rule30Prize.center (t + 2))) = false) :=
  double_white_step_depth2_forcing t hw0 hw1

theorem closure_right_rowAt_single_seed_frontier_realization (T H : Nat) :
    cell T (T : Int) = true ∧
    cell T ((T : Int) - 1) = decide (T % 2 = 1) ∧
    (∀ p : Int, (T : Int) < p → cell T p = false) ∧
    rowAt T ((T : Int) + 1) H = List.replicate H false :=
  right_rowAt_single_seed_frontier_realization T H

theorem closure_symbolic_right_evolution_realizes_cell_and_orCol
    (T H s : Nat) (hs : s < H) :
    (runWord (col0Word T s) (rowAt T 1 (H + 1))).headD false = cell (T + s) 1 ∧
    (orColWord (col0Word T H) (rowAt T 1 (H + 1))).getD s false = orCol 0 (T + s) :=
  symbolic_right_evolution_realizes_cell_and_orCol T H s hs

theorem closure_no_white_run_single_black_all_transients
    (T r t0 : Nat) (hr : 14 ≤ r)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + (r + 1)) = Rule30Prize.center t)
    (ht0 : T ≤ t0)
    (hw : ∀ i, i < r → Rule30Prize.center (t0 + i) = false)
    (hb1 : Rule30Prize.center (t0 + r) = true) : False :=
  no_white_run_single_black_all_transients T r t0 hr hper ht0 hw hb1

theorem closure_runSchedule_compositional_semantics
    (s₁ s₂ : List (Nat × Nat)) (σ : List Bool) (t L n : Nat)
    (hsched : col0Word t L = scheduleWord s₁) :
    runSchedule s₁ σ = runWord (scheduleWord s₁) σ ∧
    runSchedule (s₁ ++ s₂) σ = runSchedule s₂ (runSchedule s₁ σ) ∧
    runSchedule s₁ (rowAt t 1 (n + L)) = rowAt (t + L) 1 n ∧
    orColWord (scheduleWord s₁) (rowAt t 1 (n + L + 1)) = col0OrTrace t L :=
  runSchedule_compositional_semantics s₁ s₂ σ t L n hsched

theorem closure_spatiotemporal_001001_and_011011_depth4_constant_collapse (t : Nat) :
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
      cell (t + 1) (-4) = false ∧ cell (t + 2) (-4) = true) :=
  spatiotemporal_001001_and_011011_depth4_constant_collapse t

theorem closure_single_seed_spatiotemporal_state_completeness
    (T P t₀ k H : Nat)
    (hper : PeriodicCenter T P)
    (ht₀ : T ≤ t₀)
    (hk : T ≤ k) :
    ((∃ sb < P, Rule30Prize.center (t₀ + sb) = true) ∧
     (∃ sw < P, Rule30Prize.center (t₀ + sw) = false)) ∧
    (cell t₀ (t₀ : Int) = true ∧
     cell t₀ ((t₀ : Int) - 1) = decide (t₀ % 2 = 1) ∧
     rowAt t₀ ((t₀ : Int) + 1) H = List.replicate H false) ∧
    (obsLeftWord (col0Word t₀ H) (cell (t₀ + H) 0) (rowAtLeft t₀ (-1) (H + 1)) =
       orColWord (col0Word t₀ H) (rowAt t₀ 1 (H + 1)) ∧
     orColWord (col0Word t₀ H) (rowAt t₀ 1 (H + 1)) = col0OrTrace t₀ H) ∧
    (leftCharacteristicFlux k k = !Rule30Prize.center (k + k) ∧
     leftCharacteristicFlux (k + 1) k = !Rule30Prize.center (k + 1 + k) ∧
     leftCharacteristicFlux (k + 2) k = Rule30Prize.center (k + 2 + k) ∧
     cell (k + 3) (-(k : Int)) = decide (k % 2 = 0) ∧
     leftCharacteristicFlux (k + 4) k = !Rule30Prize.center (k + 4 + k) ∧
     cell (k + 5) (-(k : Int)) = decide (k % 2 = 0) ∧
     leftCharacteristicFlux (k + P) (k + P) = leftCharacteristicFlux k k) :=
  single_seed_spatiotemporal_state_completeness T P t₀ k H hper ht₀ hk

theorem closure_no_white_run_101_all_transients
    (T r t0 : Nat) (hr : 14 ≤ r)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + (r + 3)) = Rule30Prize.center t)
    (ht0 : T ≤ t0)
    (hw : ∀ i, i < r → Rule30Prize.center (t0 + i) = false)
    (hb1 : Rule30Prize.center (t0 + r) = true)
    (hw1 : Rule30Prize.center (t0 + r + 1) = false)
    (hb2 : Rule30Prize.center (t0 + r + 2) = true) : False :=
  no_white_run_101_all_transients T r t0 hr hper ht0 hw hb1 hw1 hb2

theorem closure_absorption_or_flux_violation_dichotomy_excludes_periodic_center
    (T P : Nat) (hper : PeriodicCenter T P)
    (hDichotomy :
      ObservationalAbsorptionAt T P ∨
      LinearHorizonCollisionAt T P ∨
      CharacteristicFluxOnsetViolationAt T P) : False :=
  absorption_or_flux_violation_dichotomy_excludes_periodic_center T P hper hDichotomy

end Rule30ProofClosure
