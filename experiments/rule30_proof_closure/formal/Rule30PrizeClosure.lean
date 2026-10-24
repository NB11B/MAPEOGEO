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

end Rule30ProofClosure
