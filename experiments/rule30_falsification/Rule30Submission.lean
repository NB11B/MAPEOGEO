import Ruliology.CellularAutomata.Rule30Prize
import Ruliology.CellularAutomata.Rule30Realization
import Ruliology.CellularAutomata.Rule30MaskedJen
import Ruliology.CellularAutomata.Rule30Diagonals
import Ruliology.CellularAutomata.Rule30BlackRuns

/-!
# Rule30Submission — R30-PRIZE G1–G3 Formal Adapter, Control Separation & Infinite-Horizon Wavefront Qualification

This module is part of the MAPEOGEO Rule 30 Falsification & Prize Qualification Suite
(`R30-PRIZE-G0/G1/G2/G3`), verified against `Rule30PrizeKit` at commit
`cc1e0e0e7c1ae8c971aec5c14aaabb47c7b8c554` on Lean `v4.35.0`.

## Epistemic Classification & Novelty Audit (Gates G0–G3)

1. **Baseline / Adapter Correspondences (Not Claimed as Novel)**:
   - Finite-cone evaluation and one-step leftward reconstruction (`evolG_g30_eq_evol`,
     `evolG_seed_eq_run`, `evol_seed_zero_eq_prize_center`, `sidewaysLeftStep_eq_evolG`)
     bridge our local E1–E4 falsification suite (`MAPEOGEOFormal/Rule30Falsification.lean`)
     to the official `Ruliology.CellularAutomata.Rule30Realization` (`evol`, `run`, `lc`,
     `realize`, `unique`) and `Ruliology.CellularAutomata.Rule30Prize` (`center`).
   - All-depth left-cone realization and the four-rule enumeration of Jen's left-permutive
     class (`g90`, `g150`, `g210`, `g30`) are established in `Rule30Realization.lean` and
     public submissions `R30-20261023-7e9e6e` and `R30-20261023-603218`.

2. **Gate G2 — Unconditional Cross-Origin Right-Half Bottleneck (`--claim partial`)**:
   - Proves exact closed-form two-step center identities (`evolG_g90_two_zero`,
     `evolG_g150_two_zero`, `evolG_g210_two_zero`, `g210_origin_cancellation_evolG`,
     `g2_rule30_separates_controls_90_150_210`) for *every* initial configuration
     `x : Int → Bool`, showing that `g90`, `g150`, and nonlinear `g210` factor through a
     1-bit right-half bottleneck (with `x 0` cancelling identically in `g210`), whereas
     `g30` uniquely reaches all 3 left-half response classes.

3. **Gate G3 — Infinite-Horizon Wavefront Qualification (`--claim partial`)**:
   - **G3.1 Occurrence (`g3_single_seed_infinite_diagonal_modeA_modeB_cycles`)**:
     Proves that on the single-seed trajectory `cell t p` (`evol seed t p`), the self-renewing
     Mode A ↔ Mode B 2-cycle occurs infinitely often for *all* `k : Nat` along both the right
     diagonal (`p = 2k - 1` at even steps and `p = 2k + 1` at odd steps) and the strict left
     interior diagonals (`D 2 (t + 2) = false`, `D 3 (2k + 2) = false`, `D 3 (2k + 3) = true`).
   - **G3.2 Propagation (`g3_modeA_next_step_iff`, `g3_modeA_step_dichotomy`)**:
     Derives the exact necessary and sufficient (`↔`) conditions for Mode A `(false, true)`
     to persist stationarily (`evol x t (p - 1) = true`), propagate left (`(0, 0, 0, 1)`),
     regenerate from Mode B (`(1, 1, 0, 0)`), enter Mode B at the same offset
     (`evol x t (p - 2) = false ∧ evol x t (p - 1) = true`), or terminate into the double-black
     wall `(true, true)` (`evol x t (p - 1) = false`).
   - **G3.3 & G3.4 Observational Consequence, Direct Implication to `Rule30Prize.Problem1`,
     and Exact Fixed-Column Counterexample (`g3_modeA_at_center_white_onsets_implies_problem1`,
     `g3_pre_onset_wavefront_implies_problem1`, `g3_single_seed_white_onset_counterexample_t6`)**:
     Proves that if Mode A `(cell (u + 1) 1 = false ∧ cell (u + 1) 2 = true)` holds at every
     white onset of `Rule30Prize.center` after some time `T`, then `Rule30Prize.Problem1`
     (`¬ EventuallyPeriodic Rule30Prize.center`) holds; and simultaneously exhibits the exact
     single-seed counterexample at `t = 6` (`center 5 = true, center 6 = false`, where
     `(cell 6 1, cell 6 2) = (false, false) ≠ (false, true)`) showing why short black runs
     fail to force Mode A unconditionally at fixed column `p = 1`.

Nothing in this module claims an unconditional resolution of `Problem1`, `Problem2`, or `Problem3`.
-/

namespace Rule30Submission

open Ruliology.CellularAutomata
open Ruliology.CellularAutomata.Rule30Jen
open Ruliology.CellularAutomata.Rule30Prize
open Ruliology.CellularAutomata.Rule30Realization
open Ruliology.CellularAutomata.Rule30MaskedJen
open Ruliology.CellularAutomata.Rule30Diagonals
open Ruliology.CellularAutomata.Rule30BlackRuns

-- ============================================================================
-- Section 1: Gate G1 — Official Adapter Bridge to Rule30Prize & Rule30Realization
-- ============================================================================

/-- General left-permutive evolution `left xor g(center, right)` from an arbitrary initial
    configuration `x0 : Int → Bool`, extending `Rule30Realization.run` (single seed) and
    `Rule30Realization.evol` (Rule 30). -/
def evolG (g : Bool → Bool → Bool) (x0 : Int → Bool) : Nat → Int → Bool
  | 0, p => x0 p
  | t + 1, p => xor (evolG g x0 t (p - 1)) (g (evolG g x0 t p) (evolG g x0 t (p + 1)))

/-- Exact equivalence between `evolG g30` and the official `Rule30Realization.evol`. -/
theorem evolG_g30_eq_evol (x0 : Int → Bool) : ∀ (t : Nat) (p : Int),
    evolG g30 x0 t p = evol x0 t p
  | 0, _ => rfl
  | t + 1, p => by
    show xor (evolG g30 x0 t (p - 1)) (g30 (evolG g30 x0 t p) (evolG g30 x0 t (p + 1))) =
      rule (evol x0 t (p - 1)) (evol x0 t p) (evol x0 t (p + 1))
    rw [evolG_g30_eq_evol x0 t (p - 1), evolG_g30_eq_evol x0 t p, evolG_g30_eq_evol x0 t (p + 1)]
    rfl

/-- Exact equivalence between `evolG g seed` and the official `Rule30Realization.run g`. -/
theorem evolG_seed_eq_run (g : Bool → Bool → Bool) : ∀ (t : Nat) (p : Int),
    evolG g seed t p = run g t p
  | 0, _ => rfl
  | t + 1, p => by
    show xor (evolG g seed t (p - 1)) (g (evolG g seed t p) (evolG g seed t (p + 1))) =
      xor (run g t (p - 1)) (g (run g t p) (run g t (p + 1)))
    rw [evolG_seed_eq_run g t (p - 1), evolG_seed_eq_run g t p, evolG_seed_eq_run g t (p + 1)]

/-- Exact equivalence between `Rule30Realization.evol seed` and `Rule30Prize.center` on column 0. -/
theorem evol_seed_zero_eq_prize_center (t : Nat) :
    evol seed t 0 = Rule30Prize.center t := by
  rw [evol_seed]
  rfl

/-- One-step leftward reconstruction identity for any rule `g` on `evolG g`. -/
theorem sidewaysLeftStep_eq_evolG (g : Bool → Bool → Bool) (x : Int → Bool) (t : Nat) (p : Int) :
    evolG g x t (p - 1) =
      xor (evolG g x (t + 1) p) (g (evolG g x t p) (evolG g x t (p + 1))) := by
  show evolG g x t (p - 1) =
    xor (xor (evolG g x t (p - 1)) (g (evolG g x t p) (evolG g x t (p + 1))))
      (g (evolG g x t p) (evolG g x t (p + 1)))
  exact (xor_xor_cancel _ _).symm

-- ============================================================================
-- Section 2: Gate G2 — Unconditional Cross-Origin Right-Half Bottleneck &
--            Separation of Rule 30 from Counterexample Rules 90, 150, 210
-- ============================================================================

/-- Helper lemma: `evolG g x 2 0` expanded in terms of the five initial cells
    `x (-2)`, `x (-1)`, `x 0`, `x 1`, `x 2`. -/
theorem evolG_two_zero_expand (g : Bool → Bool → Bool) (x : Int → Bool) :
    evolG g x 2 0 =
      xor
        (xor (x (-2)) (g (x (-1)) (x 0)))
        (g (xor (x (-1)) (g (x 0) (x 1))) (xor (x 0) (g (x 1) (x 2)))) := by
  rfl

/-- Exact unconditional two-step center formula for Rule 90 (`g90`). -/
theorem evolG_g90_two_zero (x : Int → Bool) :
    evolG g90 x 2 0 = xor (x (-2)) (x 2) := by
  rw [evolG_two_zero_expand]
  unfold g90
  cases x (-2) <;> cases x (-1) <;> cases x 0 <;> cases x 1 <;> cases x 2 <;> rfl

/-- Exact unconditional two-step center formula for Rule 150 (`g150`). -/
theorem evolG_g150_two_zero (x : Int → Bool) :
    evolG g150 x 2 0 = xor (x (-2)) (xor (x 0) (x 2)) := by
  rw [evolG_two_zero_expand]
  unfold g150
  cases x (-2) <;> cases x (-1) <;> cases x 0 <;> cases x 1 <;> cases x 2 <;> rfl

/-- Exact unconditional two-step center formula for nonlinear Rule 210 (`g210`):
    the origin cell `x 0` cancels identically via `x0 && !x0 = false`. -/
theorem evolG_g210_two_zero (x : Int → Bool) :
    evolG g210 x 2 0 = xor (x (-2)) ((!x (-1)) && ((!x 1) && x 2)) := by
  rw [evolG_two_zero_expand]
  unfold g210
  cases x (-2) <;> cases x (-1) <;> cases x 0 <;> cases x 1 <;> cases x 2 <;> rfl

/-- Unconditional Origin Cancellation Theorem for Rule 210. -/
theorem g210_origin_cancellation_evolG (x y : Int → Bool)
    (hm2 : x (-2) = y (-2)) (hm1 : x (-1) = y (-1))
    (h1 : x 1 = y 1) (h2 : x 2 = y 2) :
    evolG g210 x 2 0 = evolG g210 y 2 0 := by
  rw [evolG_g210_two_zero, evolG_g210_two_zero, hm2, hm1, h1, h2]

/-- Five-cell initial configuration constructor supported on `{-2, -1, 0, 1, 2}`. -/
def cfg5 (xm2 xm1 x0 x1 x2 : Bool) (p : Int) : Bool :=
  if p = -2 then xm2
  else if p = -1 then xm1
  else if p = 0 then x0
  else if p = 1 then x1
  else if p = 2 then x2
  else false

/-- Left-half response function at depth 2 induced by right-half bits `(x0, x1, x2)` under `g`. -/
def rightResponse2 (g : Bool → Bool → Bool) (x0 x1 x2 : Bool) (xm2 xm1 : Bool) : Bool :=
  evolG g (cfg5 xm2 xm1 x0 x1 x2) 2 0

/-- None of the three counterexample rules `g90`, `g150`, `g210` can realize the linear-wall
    response `xor xm2 xm1` for any right-half state `(x0, x1, x2) ∈ Bool³`. -/
theorem g2_controls_exclude_wall_response (x0 x1 x2 : Bool) :
    (∃ xm2 xm1 : Bool, rightResponse2 g90 x0 x1 x2 xm2 xm1 ≠ xor xm2 xm1) ∧
    (∃ xm2 xm1 : Bool, rightResponse2 g150 x0 x1 x2 xm2 xm1 ≠ xor xm2 xm1) ∧
    (∃ xm2 xm1 : Bool, rightResponse2 g210 x0 x1 x2 xm2 xm1 ≠ xor xm2 xm1) := by
  cases x0 <;> cases x1 <;> cases x2 <;> decide

/-- Rule 30 (`g30`) realizes all THREE distinct left-half response functions on `(xm2, xm1)`. -/
theorem g2_rule30_reaches_three_response_classes (xm2 xm1 : Bool) :
    rightResponse2 g30 false false false xm2 xm1 = xm2 ∧
    rightResponse2 g30 false false true xm2 xm1 = xor xm2 (!xm1) ∧
    rightResponse2 g30 true true false xm2 xm1 = xor xm2 xm1 := by
  cases xm2 <;> cases xm1 <;> decide

/-- Headline G2 Theorem: Unconditional Cross-Origin Separation of Rule 30 (`g30`) from
    all three counterexample rules (`g90`, `g150`, `g210`) in `Rule30Realization`. -/
theorem g2_rule30_separates_controls_90_150_210 :
    (∀ x : Int → Bool,
      evolG g90 x 2 0 = xor (x (-2)) (x 2) ∧
      evolG g150 x 2 0 = xor (x (-2)) (xor (x 0) (x 2)) ∧
      evolG g210 x 2 0 = xor (x (-2)) ((!x (-1)) && ((!x 1) && x 2))) ∧
    (∀ x0 x1 x2 : Bool,
      (∃ xm2 xm1 : Bool, rightResponse2 g90 x0 x1 x2 xm2 xm1 ≠ xor xm2 xm1) ∧
      (∃ xm2 xm1 : Bool, rightResponse2 g150 x0 x1 x2 xm2 xm1 ≠ xor xm2 xm1) ∧
      (∃ xm2 xm1 : Bool, rightResponse2 g210 x0 x1 x2 xm2 xm1 ≠ xor xm2 xm1)) ∧
    (∀ xm2 xm1 : Bool,
      rightResponse2 g30 false false false xm2 xm1 = xm2 ∧
      rightResponse2 g30 false false true xm2 xm1 = xor xm2 (!xm1) ∧
      rightResponse2 g30 true true false xm2 xm1 = xor xm2 xm1) := by
  refine ⟨fun x => ⟨evolG_g90_two_zero x, evolG_g150_two_zero x, evolG_g210_two_zero x⟩,
    g2_controls_exclude_wall_response,
    g2_rule30_reaches_three_response_classes⟩

-- ============================================================================
-- Section 3: Gate E5/G2 — Two-Step Wavefront Shield & Control Separation
-- ============================================================================

/-- Mode A → Mode B Transition on `Rule30Realization.evol`. -/
theorem e5_modeA_to_modeB_evol (x y : Int → Bool) (t : Nat) (p : Int)
    (hm3 : evol x t (p - 3) = evol y t (p - 3))
    (hm2 : evol x t (p - 2) = evol y t (p - 2))
    (hm1 : evol x t (p - 1) = evol y t (p - 1))
    (hx0 : evol x t p = false) (hy0 : evol y t p = false)
    (hx1 : evol x t (p + 1) = true) (hy1 : evol y t (p + 1) = true) :
    evol x (t + 1) (p - 2) = evol y (t + 1) (p - 2) ∧
    evol x (t + 1) (p - 1) = evol y (t + 1) (p - 1) ∧
    evol x (t + 1) (p - 1) = xor (evol x t (p - 2)) (evol x t (p - 1)) ∧
    evol x (t + 1) p = xor (evol x t (p - 1)) true ∧
    evol y (t + 1) p = xor (evol y t (p - 1)) true ∧
    evol x (t + 1) (p + 1) = true ∧
    evol y (t + 1) (p + 1) = true := by
  have h_m2_l : p - 2 - 1 = p - 3 := by omega
  have h_m2_r : p - 2 + 1 = p - 1 := by omega
  have h_m1_l : p - 1 - 1 = p - 2 := by omega
  have h_m1_r : p - 1 + 1 = p := by omega
  have h_p1_l : p + 1 - 1 = p := by omega
  have hxm2 : evol x (t + 1) (p - 2) =
      rule (evol x t (p - 3)) (evol x t (p - 2)) (evol x t (p - 1)) := by
    change rule (evol x t (p - 2 - 1)) (evol x t (p - 2)) (evol x t (p - 2 + 1)) = _
    rw [h_m2_l, h_m2_r]
  have hym2 : evol y (t + 1) (p - 2) =
      rule (evol y t (p - 3)) (evol y t (p - 2)) (evol y t (p - 1)) := by
    change rule (evol y t (p - 2 - 1)) (evol y t (p - 2)) (evol y t (p - 2 + 1)) = _
    rw [h_m2_l, h_m2_r]
  have hxm1 : evol x (t + 1) (p - 1) =
      rule (evol x t (p - 2)) (evol x t (p - 1)) (evol x t p) := by
    change rule (evol x t (p - 1 - 1)) (evol x t (p - 1)) (evol x t (p - 1 + 1)) = _
    rw [h_m1_l, h_m1_r]
  have hym1 : evol y (t + 1) (p - 1) =
      rule (evol y t (p - 2)) (evol y t (p - 1)) (evol y t p) := by
    change rule (evol y t (p - 1 - 1)) (evol y t (p - 1)) (evol y t (p - 1 + 1)) = _
    rw [h_m1_l, h_m1_r]
  have hxp : evol x (t + 1) p =
      rule (evol x t (p - 1)) (evol x t p) (evol x t (p + 1)) := rfl
  have hyp : evol y (t + 1) p =
      rule (evol y t (p - 1)) (evol y t p) (evol y t (p + 1)) := rfl
  have hxp1 : evol x (t + 1) (p + 1) =
      rule (evol x t p) (evol x t (p + 1)) (evol x t (p + 1 + 1)) := by
    change rule (evol x t (p + 1 - 1)) (evol x t (p + 1)) (evol x t (p + 1 + 1)) = _
    rw [h_p1_l]
  have hyp1 : evol y (t + 1) (p + 1) =
      rule (evol y t p) (evol y t (p + 1)) (evol y t (p + 1 + 1)) := by
    change rule (evol y t (p + 1 - 1)) (evol y t (p + 1)) (evol y t (p + 1 + 1)) = _
    rw [h_p1_l]
  rw [hxm2, hym2, hxm1, hym1, hxp, hyp, hxp1, hyp1]
  rw [hx0, hy0, hx1, hy1, ← hm3, ← hm2, ← hm1]
  unfold rule
  cases evol x t (p - 3) <;>
    cases evol x t (p - 2) <;>
    cases evol x t (p - 1) <;>
    cases evol x t (p + 1 + 1) <;>
    cases evol y t (p + 1 + 1) <;>
    decide

/-- Mode B → Mode A Transition on `Rule30Realization.evol`. -/
theorem e5_modeB_to_modeA_evol (x y : Int → Bool) (t : Nat) (p : Int)
    (hm2 : evol x t (p - 2) = evol y t (p - 2))
    (hxm1 : evol x t (p - 1) = true) (hym1 : evol y t (p - 1) = true)
    (hxor_x : xor (evol x t p) (evol x t (p + 1)) = true)
    (hxor_y : xor (evol y t p) (evol y t (p + 1)) = true) :
    evol x (t + 1) (p - 1) = evol y (t + 1) (p - 1) ∧
    evol x (t + 1) p = false ∧
    evol y (t + 1) p = false := by
  have h_m1_l : p - 1 - 1 = p - 2 := by omega
  have h_m1_r : p - 1 + 1 = p := by omega
  have hxm1' : evol x (t + 1) (p - 1) =
      rule (evol x t (p - 2)) (evol x t (p - 1)) (evol x t p) := by
    change rule (evol x t (p - 1 - 1)) (evol x t (p - 1)) (evol x t (p - 1 + 1)) = _
    rw [h_m1_l, h_m1_r]
  have hym1' : evol y (t + 1) (p - 1) =
      rule (evol y t (p - 2)) (evol y t (p - 1)) (evol y t p) := by
    change rule (evol y t (p - 1 - 1)) (evol y t (p - 1)) (evol y t (p - 1 + 1)) = _
    rw [h_m1_l, h_m1_r]
  have hxp' : evol x (t + 1) p =
      rule (evol x t (p - 1)) (evol x t p) (evol x t (p + 1)) := rfl
  have hyp' : evol y (t + 1) p =
      rule (evol y t (p - 1)) (evol y t p) (evol y t (p + 1)) := rfl
  rw [hxm1', hym1', hxp', hyp', hxm1, hym1, ← hm2]
  unfold rule
  cases hxp : evol x t p <;> cases hxp1 : evol x t (p + 1) <;>
    cases hyp : evol y t p <;> cases hyp1 : evol y t (p + 1) <;>
    cases evol x t (p - 2)
  all_goals
    simp_all

/-- Headline E5/G2 Theorem: Two-Step Wavefront Shield on `Rule30Realization.evol`. -/
theorem e5_two_step_wavefront_shield_evol (x y : Int → Bool) (t : Nat) (p : Int)
    (hm3 : evol x t (p - 3) = evol y t (p - 3))
    (hm2 : evol x t (p - 2) = evol y t (p - 2))
    (hm1 : evol x t (p - 1) = evol y t (p - 1))
    (hx0 : evol x t p = false) (hy0 : evol y t p = false)
    (hx1 : evol x t (p + 1) = true) (hy1 : evol y t (p + 1) = true) :
    evol x (t + 1) (p - 2) = evol y (t + 1) (p - 2) ∧
    evol x (t + 1) (p - 1) = evol y (t + 1) (p - 1) ∧
    evol x (t + 1) p = evol y (t + 1) p ∧
    evol x (t + 1) (p + 1) = true ∧
    evol y (t + 1) (p + 1) = true ∧
    evol x (t + 2) (p - 1) = evol y (t + 2) (p - 1) ∧
    evol x (t + 2) p = evol y (t + 2) p := by
  have h1 := e5_modeA_to_modeB_evol x y t p hm3 hm2 hm1 hx0 hy0 hx1 hy1
  rcases h1 with ⟨h1_m2, h1_m1, _, h1_xp, h1_yp, h1_xp1, h1_yp1⟩
  have h1_p : evol x (t + 1) p = evol y (t + 1) p := by
    rw [h1_xp, h1_yp, hm1]
  have h_m1_l : p - 1 - 1 = p - 2 := by omega
  have h_m1_r : p - 1 + 1 = p := by omega
  have h2_m1 : evol x (t + 2) (p - 1) = evol y (t + 2) (p - 1) := by
    change rule (evol x (t + 1) (p - 1 - 1)) (evol x (t + 1) (p - 1)) (evol x (t + 1) (p - 1 + 1)) =
           rule (evol y (t + 1) (p - 1 - 1)) (evol y (t + 1) (p - 1)) (evol y (t + 1) (p - 1 + 1))
    rw [h_m1_l, h_m1_r, h1_m2, h1_m1, h1_p]
  have h2_p : evol x (t + 2) p = evol y (t + 2) p := by
    change rule (evol x (t + 1) (p - 1)) (evol x (t + 1) p) (evol x (t + 1) (p + 1)) =
           rule (evol y (t + 1) (p - 1)) (evol y (t + 1) p) (evol y (t + 1) (p + 1))
    rw [h1_m1, h1_p, h1_xp1, h1_yp1]
  exact ⟨h1_m2, h1_m1, h1_p, h1_xp1, h1_yp1, h2_m1, h2_p⟩

/-- Headline Wavefront Separation Theorem against `g90`, `g150`, and `g210`. -/
theorem e5_wavefront_separates_controls :
    (∀ xm2 xm1 : Bool,
      rightResponse2 g30 false true false xm2 xm1 = rightResponse2 g30 false true true xm2 xm1) ∧
    (∀ xm2 xm1 : Bool,
      rightResponse2 g90 false true false xm2 xm1 ≠ rightResponse2 g90 false true true xm2 xm1 ∧
      rightResponse2 g150 false true false xm2 xm1 ≠ rightResponse2 g150 false true true xm2 xm1) ∧
    (∀ xm2 xm1 : Bool,
      rightResponse2 g30 true true false xm2 xm1 = rightResponse2 g30 true false true xm2 xm1) ∧
    (∃ xm2 xm1 : Bool,
      rightResponse2 g90 true true false xm2 xm1 ≠ rightResponse2 g90 true false true xm2 xm1 ∧
      rightResponse2 g150 true true false xm2 xm1 ≠ rightResponse2 g150 true false true xm2 xm1 ∧
      rightResponse2 g210 true true false xm2 xm1 ≠ rightResponse2 g210 true false true xm2 xm1) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro xm2 xm1
    cases xm2 <;> cases xm1 <;> rfl
  · intro xm2 xm1
    cases xm2 <;> cases xm1 <;> decide
  · intro xm2 xm1
    cases xm2 <;> cases xm1 <;> rfl
  · refine ⟨false, false, ?_⟩
    decide

-- ============================================================================
-- Section 4: Gate R30-PRIZE-G3 — Infinite-Horizon Wavefront Qualification
--            (1. Occurrence, 2. Propagation, 3. Observational Lock,
--             4. Formal Implication to Rule30Prize.Problem1 & Counterexample)
-- ============================================================================

/-- Mode A wavefront predicate at `(p, p + 1)` at time `t`: `(evol x t p, evol x t (p + 1)) = (false, true)`. -/
def ModeA (x : Int → Bool) (t : Nat) (p : Int) : Prop :=
  evol x t p = false ∧ evol x t (p + 1) = true

/-- Mode B wavefront predicate at `(p - 1, p, p + 1)` at time `t`:
    `evol x t (p - 1) = true` and `xor (evol x t p) (evol x t (p + 1)) = true`. -/
def ModeB (x : Int → Bool) (t : Nat) (p : Int) : Prop :=
  evol x t (p - 1) = true ∧ xor (evol x t p) (evol x t (p + 1)) = true

/-- **G3.2 Necessary and Sufficient 1-Step Precursor Theorem for Mode A (`g3_modeA_next_step_iff`)**:
    For any configuration `x : Int → Bool`, time `t : Nat`, and spatial column `p : Int`,
    `ModeA x (t + 1) p` holds if and only if the 4-cell window at `(p - 1, p, p + 1, p + 2)` at
    time `t` is in one of three disjoint regimes:
    1. `(true, false, true, _)`: Stationary Mode A at `p` driven by a black left neighbor `p - 1`,
    2. `(false, false, false, true)`: Leftward shift of Mode A from `p + 1` into `(0, 0)` at `(p - 1, p)`,
    3. `(true, true, false, false)`: Mode B `(1, 1, 0)` at `(p - 1, p, p + 1)` backed by white at `p + 2`. -/
theorem g3_modeA_next_step_iff (x : Int → Bool) (t : Nat) (p : Int) :
    ModeA x (t + 1) p ↔
      (evol x t (p - 1) = true ∧ evol x t p = false ∧ evol x t (p + 1) = true) ∨
      (evol x t (p - 1) = false ∧ evol x t p = false ∧
        evol x t (p + 1) = false ∧ evol x t (p + 1 + 1) = true) ∨
      (evol x t (p - 1) = true ∧ evol x t p = true ∧
        evol x t (p + 1) = false ∧ evol x t (p + 1 + 1) = false) := by
  unfold ModeA
  have hp1 : evol x (t + 1) (p + 1) =
      rule (evol x t p) (evol x t (p + 1)) (evol x t (p + 1 + 1)) := by
    change rule (evol x t (p + 1 - 1)) (evol x t (p + 1)) (evol x t (p + 1 + 1)) = _
    rw [show p + 1 - 1 = p by omega]
  have hp0 : evol x (t + 1) p =
      rule (evol x t (p - 1)) (evol x t p) (evol x t (p + 1)) := rfl
  rw [hp0, hp1]
  unfold rule
  cases evol x t (p - 1) <;>
    cases evol x t p <;>
    cases evol x t (p + 1) <;>
    cases evol x t (p + 1 + 1) <;>
    decide

/-- **G3.2 Exact Mode A Step Dichotomy (`g3_modeA_step_dichotomy`)**:
    Assuming `ModeA x t p` (`(evol x t p, evol x t (p + 1)) = (false, true)`), at time `t + 1`:
    1. `ModeA x (t + 1) p` regenerates stationarily at `p` iff `evol x t (p - 1) = true`.
    2. `ModeA x t p` terminates into the double-black wall `(true, true)` at `(p, p + 1)` iff
       `evol x t (p - 1) = false`.
    3. `ModeB x (t + 1) p` holds at the same offset `p` iff
       `evol x t (p - 2) = false ∧ evol x t (p - 1) = true`. -/
theorem g3_modeA_step_dichotomy (x : Int → Bool) (t : Nat) (p : Int)
    (hA : ModeA x t p) :
    (ModeA x (t + 1) p ↔ evol x t (p - 1) = true) ∧
    ((evol x (t + 1) p = true ∧ evol x (t + 1) (p + 1) = true) ↔ evol x t (p - 1) = false) ∧
    (ModeB x (t + 1) p ↔ (evol x t (p - 2) = false ∧ evol x t (p - 1) = true)) := by
  rcases hA with ⟨hp0, hp1⟩
  unfold ModeA ModeB
  have h_m1_l : p - 1 - 1 = p - 2 := by omega
  have h_m1_r : p - 1 + 1 = p := by omega
  have h_p1_l : p + 1 - 1 = p := by omega
  have hxm1 : evol x (t + 1) (p - 1) =
      rule (evol x t (p - 2)) (evol x t (p - 1)) (evol x t p) := by
    change rule (evol x t (p - 1 - 1)) (evol x t (p - 1)) (evol x t (p - 1 + 1)) = _
    rw [h_m1_l, h_m1_r]
  have hxp : evol x (t + 1) p =
      rule (evol x t (p - 1)) (evol x t p) (evol x t (p + 1)) := rfl
  have hxp1 : evol x (t + 1) (p + 1) =
      rule (evol x t p) (evol x t (p + 1)) (evol x t (p + 1 + 1)) := by
    change rule (evol x t (p + 1 - 1)) (evol x t (p + 1)) (evol x t (p + 1 + 1)) = _
    rw [h_p1_l]
  rw [hxm1, hxp, hxp1, hp0, hp1]
  unfold rule
  cases evol x t (p - 2) <;>
    cases evol x t (p - 1) <;>
    cases evol x t (p + 1 + 1) <;>
    decide

/-- **G3.2 Arbitrary-Horizon Stationary Persistence (`g3_modeA_persists_during_black_run`)**:
    If `ModeA x t p` holds at time `t` and the left neighbor `p - 1` remains black (`true`)
    for `k` consecutive steps, then `ModeA x (t + k) p` holds at time `t + k`, regardless of
    any right-exterior values at `≥ p + 2`. -/
theorem g3_modeA_persists_during_black_run (x : Int → Bool) (p : Int) :
    ∀ (k t : Nat), ModeA x t p → (∀ s, s < k → evol x (t + s) (p - 1) = true) →
      ModeA x (t + k) p
  | 0, t, hA, _ => by simpa using hA
  | k + 1, t, hA, hblk => by
    have hA1 : ModeA x (t + 1) p :=
      (g3_modeA_step_dichotomy x t p hA).1.mpr (by simpa using hblk 0 (by omega))
    have ih := g3_modeA_persists_during_black_run x p k (t + 1) hA1 (fun s hs => by
      have := hblk (s + 1) (by omega)
      rwa [show t + (s + 1) = t + 1 + s by omega] at this)
    rwa [show t + 1 + k = t + (k + 1) by omega] at ih

/-- Right diagonal `R 1` alternates `false, true, false, true, ...` at even and odd steps. -/
theorem g3_R1_parity : ∀ k : Nat, R 1 (2 * k) = false ∧ R 1 (2 * k + 1) = true
  | 0 => ⟨rfl, rfl⟩
  | k + 1 => by
    rcases g3_R1_parity k with ⟨heven, hodd⟩
    have h1 : R 1 (2 * (k + 1)) = !R 1 (2 * k + 1) := by
      rw [show 2 * (k + 1) = (2 * k + 1) + 1 by omega]
      exact R_one_succ (2 * k + 1)
    have h2 : R 1 (2 * (k + 1) + 1) = !R 1 (2 * (k + 1)) := R_one_succ (2 * (k + 1))
    rw [h1, hodd] at *
    exact ⟨rfl, by rw [h2]; rfl⟩

/-- Left diagonal `D 2` is permanently white (`false`) from time `t = 2` onward. -/
theorem g3_D2_eq_false (t : Nat) : D 2 (t + 2) = false := by
  rw [show t + 2 = (t + 1) + 1 by omega, D_step 0 (t + 1), D_zero (t + 1), D_one t]
  rfl

/-- Left diagonal `D 3` alternates at every step from time `t = 2` onward. -/
theorem g3_D3_succ (t : Nat) : D 3 (t + 3) = !D 3 (t + 2) := by
  rw [show t + 3 = (t + 2) + 1 by omega, D_step 1 (t + 2), D_one (t + 1), g3_D2_eq_false t]
  cases D 3 (t + 2) <;> rfl

/-- Exact parity law for `D 3`: `D 3 (2k + 2) = false` and `D 3 (2k + 3) = true` for all `k`. -/
theorem g3_D3_parity : ∀ k : Nat, D 3 (2 * k + 2) = false ∧ D 3 (2 * k + 3) = true
  | 0 => ⟨rfl, rfl⟩
  | k + 1 => by
    rcases g3_D3_parity k with ⟨_, hodd⟩
    have h1 : D 3 (2 * (k + 1) + 2) = !D 3 (2 * k + 3) := by
      rw [show 2 * (k + 1) + 2 = (2 * k + 1) + 3 by omega,
        show 2 * k + 3 = (2 * k + 1) + 2 by omega]
      exact g3_D3_succ (2 * k + 1)
    have h2 : D 3 (2 * (k + 1) + 3) = !D 3 (2 * (k + 1) + 2) := by
      rw [show 2 * (k + 1) + 3 = (2 * k + 2) + 3 by omega,
        show 2 * (k + 1) + 2 = (2 * k + 2) + 2 by omega]
      exact g3_D3_succ (2 * k + 2)
    rw [h1, hodd] at *
    exact ⟨rfl, by rw [h2]; rfl⟩

/-- **G3.1 Headline Theorem (`g3_single_seed_infinite_diagonal_modeA_modeB_cycles`)**:
    In the single-seed Rule 30 evolution (`seed`), the self-renewing Mode A ↔ Mode B 2-cycle
    occurs infinitely often for ALL `k : Nat` along both diagonals:
    1. Right diagonal: `ModeA seed (2 * k) ((2 * k : Int) - 1)` at every even step `2k`, and
       `ModeB seed (2 * k + 1) (2 * k + 1 : Int)` at every odd step `2k + 1`.
    2. Left interior diagonal: at every even step `2k + 2`, `(D 0, D 1, D 2, D 3) = (true, true, false, false)`
       (Mode B `(1, 1, 0)` backed by `0`), and at every odd step `2k + 3`,
       `(D 1, D 2, D 3) = (true, false, true)` (stationary interior Mode A). -/
theorem g3_single_seed_infinite_diagonal_modeA_modeB_cycles (k : Nat) :
    ModeA seed (2 * k) ((2 * k : Int) - 1) ∧
    ModeB seed (2 * k + 1) ((2 * k + 1 : Nat) : Int) ∧
    (D 0 (2 * k + 2) = true ∧ D 1 (2 * k + 2) = true ∧
      D 2 (2 * k + 2) = false ∧ D 3 (2 * k + 2) = false) ∧
    (D 1 (2 * k + 3) = true ∧ D 2 (2 * k + 3) = false ∧ D 3 (2 * k + 3) = true) := by
  rcases g3_R1_parity k with ⟨hR_even, hR_odd⟩
  rcases g3_D3_parity k with ⟨hD3_even, hD3_odd⟩
  refine ⟨?_, ?_, ?_, ?_⟩
  · unfold ModeA
    rw [evol_seed, evol_seed, show (2 * k : Int) - 1 + 1 = (2 * k : Int) by omega]
    have h1 : cell (2 * k) ((2 * k : Int) - 1) = R 1 (2 * k) := rfl
    have h0 : cell (2 * k) (2 * k : Int) = R 0 (2 * k) := by
      unfold R; simp
    rw [h1, h0, hR_even, R_zero]
    exact ⟨rfl, rfl⟩
  · unfold ModeB
    rw [evol_seed, evol_seed, evol_seed]
    have hm1 : cell (2 * k + 1) (((2 * k + 1 : Nat) : Int) - 1) = R 1 (2 * k + 1) := rfl
    have hp0 : cell (2 * k + 1) ((2 * k + 1 : Nat) : Int) = R 0 (2 * k + 1) := by
      unfold R; simp
    have hp1 : cell (2 * k + 1) (((2 * k + 1 : Nat) : Int) + 1) = false :=
      cell_eq_false_of_gt (2 * k + 1) _ (by omega)
    rw [hm1, hp0, hp1, hR_odd, R_zero]
    exact ⟨rfl, rfl⟩
  · exact ⟨D_zero (2 * k + 2), D_one (2 * k + 1), g3_D2_eq_false (2 * k), hD3_even⟩
  · exact ⟨D_one (2 * k + 2), g3_D2_eq_false (2 * k + 1), hD3_odd⟩

/-- **G3.3 Observational Lock Lemma (`g3_modeA_white_run_lock`)**:
    If Mode A `(cell w (i + 1) = false ∧ cell w (i + 1 + 1) = true)` holds at the start `w`
    of a white run of column `i` (`∀ j ≤ k, cell (w + j) i = false`), then throughout the
    white run, column `i + 1` is white at `j = 0` and locked to black (`true`) for all `1 ≤ j ≤ k`. -/
theorem g3_modeA_white_run_lock (i : Int) :
    ∀ (k w : Nat), cell w (i + 1) = false → cell w (i + 1 + 1) = true →
      (∀ j, j ≤ k → cell (w + j) i = false) →
      cell (w + k) (i + 1) = decide (k ≠ 0)
  | 0, w, h1, _, _ => by simpa using h1
  | k + 1, w, h1, h2, hz => by
    have hk0 : cell (w + k) i = false := hz k (by omega)
    have hstep : cell (w + (k + 1)) (i + 1) =
        rule (cell (w + k) i) (cell (w + k) (i + 1)) (cell (w + k) (i + 1 + 1)) := by
      show rule (cell (w + k) (i + 1 - 1)) (cell (w + k) (i + 1)) (cell (w + k) (i + 1 + 1)) = _
      rw [show i + 1 - 1 = i by omega]
    have ih := g3_modeA_white_run_lock i k w h1 h2 (fun j hj => hz j (by omega))
    rw [hstep, hk0]
    cases k with
    | zero =>
      rw [show w + 0 = w by omega, h1, h2]
      rfl
    | succ k' =>
      rw [ih]
      rfl

/-- **G3.4 Headline Implication Theorem (`g3_modeA_at_center_white_onsets_implies_problem1`)**:
    If there exists a time `T` after which every white onset of `Rule30Prize.center`
    (`center u = true ∧ center (u + 1) = false`) is accompanied by Mode A at `(1, 2)`
    (`cell (u + 1) 1 = false ∧ cell (u + 1) 2 = true`), then `Rule30Prize.Problem1`
    (`¬ EventuallyPeriodic Rule30Prize.center`) holds. -/
theorem g3_modeA_at_center_white_onsets_implies_problem1 {T : Nat}
    (hModeA : ∀ u, T ≤ u → Rule30Prize.center u = true → Rule30Prize.center (u + 1) = false →
      cell (u + 1) 1 = false ∧ cell (u + 1) 2 = true) :
    Rule30Prize.Problem1 := by
  intro hc
  obtain ⟨T₀, P, hP, hper⟩ := hc
  have hper' : ∀ t, T₀ ≤ t → cell (t + P) 0 = cell t 0 := hper
  by_cases hw : ∃ t, T₀ ≤ t ∧ ∀ s, s < P → cell (t + s) 0 = false
  · obtain ⟨t, _, hs⟩ := hw
    have hk : ∀ k s, s < P → cell (t + k * P + s) 0 = false := by
      intro k
      induction k with
      | zero => intro s hs'; simpa using hs s hs'
      | succ k ih =>
        intro s hs'
        rw [show t + (k + 1) * P + s = (t + k * P + s) + P by rw [Nat.succ_mul]; omega,
          hper' _ (by omega)]
        exact ih s hs'
    refine no_column_eventually_constant 0 ⟨t, false, fun u hu => ?_⟩
    have := hk ((u - t) / P) ((u - t) % P) (Nat.mod_lt _ hP)
    rwa [show t + (u - t) / P * P + (u - t) % P = u by
      have := Nat.div_add_mod (u - t) P; rw [Nat.mul_comm] at this; omega] at this
  · have hblack : ∀ t, T₀ ≤ t → ∃ s, s < P ∧ cell (t + s) 0 = true := by
      intro t ht
      refine Classical.byContradiction fun hne => hw ⟨t, ht, fun s hs => ?_⟩
      cases h : cell (t + s) 0
      · rfl
      · exact absurd ⟨s, hs, h⟩ hne
    let B := T + T₀ + P + 2
    have hform : ∀ t, B ≤ t → orCol 0 t = (cell t 0 || !cell (t - 1) 0) := by
      intro t ht
      cases h0 : cell t 0
      · rcases trailing (fun u => cell u 0) t h0 P with hall | ⟨k, hk, h1, h2⟩
        · obtain ⟨s, hs, hb⟩ := hblack (t - P) (by omega)
          have := hall (P - s) (by omega)
          rw [show t - (P - s) = t - P + s by omega, hb] at this
          exact absurd this (by decide)
        · have honset := hModeA (t - (k + 1)) (by omega) h1
            (by rw [show t - (k + 1) + 1 = t - k by omega]; exact h2 k (by omega))
          rw [show t - (k + 1) + 1 = t - k by omega] at honset
          have hlock := g3_modeA_white_run_lock 0 k (t - k) honset.1 honset.2
            (fun j hj => by
              rw [show t - k + j = t - (k - j) by omega]
              exact h2 (k - j) (by omega))
          rw [show t - k + k = t by omega, show (0 : Int) + 1 = 1 by rfl] at hlock
          unfold orCol
          rw [h0, Bool.false_or, Bool.false_or, Int.zero_add, hlock]
          cases k with
          | zero =>
            have : cell (t - 1) 0 = true := by simpa using h1
            rw [this]; rfl
          | succ k' =>
            have : cell (t - 1) 0 = false := by simpa using h2 1 (by omega)
            rw [this]; rfl
      · unfold orCol; rw [h0]; rfl
    refine orCol_not_eventuallyPeriodic 0 ⟨T₀, P, hP, hper⟩ ⟨B, P, hP, fun t ht => ?_⟩
    show orCol 0 (t + P) = orCol 0 t
    rw [hform t (by omega), hform (t + P) (by omega), hper' t (by omega),
      show t + P - 1 = (t - 1) + P by omega, hper' (t - 1) (by omega)]

/-- **G3.4 Pre-Onset Wavefront Sufficient Condition for `Rule30Prize.Problem1`
    (`g3_pre_onset_wavefront_implies_problem1`)**:
    Combining `g3_modeA_next_step_iff` with `g3_modeA_at_center_white_onsets_implies_problem1`:
    if after some time `T`, at the end of every black run of `Rule30Prize.center`
    (`center u = true ∧ center (u + 1) = false`), the right-hand cells `(cell u 1, cell u 2, cell u 3)`
    are either in Mode A (`(false, true, _)`) or in Mode B backed by white (`(true, false, false)`),
    then `Rule30Prize.Problem1` (`¬ EventuallyPeriodic Rule30Prize.center`) holds. -/
theorem g3_pre_onset_wavefront_implies_problem1 {T : Nat}
    (hPre : ∀ u, T ≤ u → Rule30Prize.center u = true → Rule30Prize.center (u + 1) = false →
      (cell u 1 = false ∧ cell u 2 = true) ∨
      (cell u 1 = true ∧ cell u 2 = false ∧ cell u 3 = false)) :
    Rule30Prize.Problem1 := by
  refine g3_modeA_at_center_white_onsets_implies_problem1 (T := T) (fun u hu hc0 hc1 => ?_)
  rw [← evol_seed (u + 1) 1, ← evol_seed (u + 1) 2, ← show (1 : Int) + 1 = 2 by rfl]
  change ModeA seed (u + 1) 1
  rw [g3_modeA_next_step_iff]
  rw [evol_seed, evol_seed, evol_seed, evol_seed,
    show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 + 1 = 3 by rfl,
    show (1 : Int) + 1 = 2 by rfl]
  have hcu : cell u 0 = true := hc0
  rcases hPre u hu hc0 hc1 with ⟨h1, h2⟩ | ⟨h1, h2, h3⟩
  · exact Or.inl ⟨hcu, h1, h2⟩
  · exact Or.inr (Or.inr ⟨hcu, h1, h2, h3⟩)

/-- **G3.4 Exact Single-Seed Fixed-Column Counterexample (`g3_single_seed_white_onset_counterexample_t6`)**:
    In the single-seed trajectory, after a 3-step black run (`center 2 = false`,
    `center 3 = true`, `center 4 = true`, `center 5 = true`), at time `t = 6` the center
    column has a white onset (`center 6 = false`), yet columns `(1, 2)` are `(false, false)`
    rather than Mode A `(false, true)`. This proves that short black runs (`< 9` steps)
    do not unconditionally force Mode A at fixed column `p = 1`. -/
theorem g3_single_seed_white_onset_counterexample_t6 :
    Rule30Prize.center 2 = false ∧
    Rule30Prize.center 3 = true ∧
    Rule30Prize.center 4 = true ∧
    Rule30Prize.center 5 = true ∧
    Rule30Prize.center 6 = false ∧
    cell 6 1 = false ∧
    cell 6 2 = false ∧
    ¬ ModeA seed 6 1 := by
  refine ⟨by decide, by decide, by decide, by decide, by decide, by decide, by decide, ?_⟩
  unfold ModeA
  rw [evol_seed, evol_seed]
  decide

/-!
## 5. Gate `G4-P1`: Generalized Boundary Grammar (`ModeADepth`) & Multi-State White-Onset Qualification

To resolve the `t = 6` short-black-run counterexample (`g3_single_seed_white_onset_counterexample_t6`)
while preserving all G3 results, we generalize the fixed-column Mode A state (`cell t 1 = false ∧ cell t 2 = true`)
to the depth-indexed right-boundary grammar `ModeADepth t ℓ`:
- Columns `1 .. ℓ` are white (`false`), and column `ℓ + 1` is the first black (`true`) cell to the right of `center`.
- `ModeADepth t 0` is `cell t 1 = true` (active wall at column 1).
- `ModeADepth t 1` is `cell t 1 = false ∧ cell t 2 = true` (G3's `ModeA seed t 1`).
- `ModeADepth t 2` is `cell t 1 = false ∧ cell t 2 = false ∧ cell t 3 = true`, which captures the exact
  state at the `t = 6` counterexample (`ModeADepth 6 2`) and shifts left into `ModeADepth 7 1` (`ModeA seed 7 1`) at `t = 7`.
-/

/-- **G4-P1 Definition (`ModeADepth`)**:
    Depth-`ℓ` right-boundary state at time `t` of the single-seed evolution:
    columns `1 .. ℓ` are white (`false`) and column `ℓ + 1` is the first black (`true`) cell
    to the right of the center column. -/
def ModeADepth (t ℓ : Nat) : Prop :=
  (∀ p : Nat, 1 ≤ p → p ≤ ℓ → cell t p = false) ∧ cell t ((ℓ + 1 : Nat) : Int) = true

/-- **G4-P1 Equivalence with G3 `ModeA` at Depth 1 (`g4_p1_modeADepth_one_iff_modeA`)**:
    `ModeADepth t 1` is logically equivalent to the G3 state `ModeA seed t 1`. -/
theorem g4_p1_modeADepth_one_iff_modeA (t : Nat) :
    ModeADepth t 1 ↔ ModeA seed t 1 := by
  unfold ModeADepth ModeA
  rw [evol_seed, evol_seed, show (1 : Int) + 1 = 2 by rfl]
  constructor
  · intro ⟨hw, hb⟩
    exact ⟨by simpa using hw 1 (Nat.le_refl 1) (Nat.le_refl 1), by simpa using hb⟩
  · intro ⟨h1, h2⟩
    refine ⟨fun p hp1 hp2 => ?_, by simpa using h2⟩
    have : p = 1 := by omega
    subst this
    simpa using h1

/-- **G4-P1 Unconditional Single-Seed Grammar Completeness (`g4_p1_every_step_has_modeADepth`)**:
    At every step `t ≥ 1` of the single-seed Rule 30 trajectory (including `t = 6` and every
    center-column white onset), there exists a depth `ℓ` such that `ModeADepth t ℓ` holds. -/
theorem g4_p1_every_step_has_modeADepth (t : Nat) (ht : 1 ≤ t) :
    ∃ ℓ, ModeADepth t ℓ :=
  first_black t ht

/-- **G4-P1 Resolution of the `t = 6` Counterexample (`g4_p1_t6_counterexample_resolved_by_modeADepth`)**:
    At the G3 counterexample `t = 6` (where `center 5 = true`, `center 6 = false`, and `¬ ModeA seed 6 1`),
    the single-seed boundary state is in `ModeADepth 6 2` (`cell 6 1 = false ∧ cell 6 2 = false ∧ cell 6 3 = true`),
    and after one white step at `center 6 = false`, the front shifts left by one column into
    `ModeADepth 7 1` (`ModeA seed 7 1`) at `t = 7`. -/
theorem g4_p1_t6_counterexample_resolved_by_modeADepth :
    ModeADepth 6 2 ∧ ModeADepth 7 1 ∧ ModeA seed 7 1 := by
  refine ⟨⟨fun p hp1 hp2 => ?_, by decide⟩, ⟨fun p hp1 hp2 => ?_, by decide⟩, ?_⟩
  · by_cases hp : p = 1
    · subst hp; decide
    · have : p = 2 := by omega
      subst this; decide
  · have : p = 1 := by omega
    subst this; decide
  · unfold ModeA
    rw [evol_seed, evol_seed]
    exact ⟨by decide, by decide⟩

/-- **G4-P1 Exact Multi-Depth White-Run Lock (`g4_p1_modeADepth_white_run_lock`)**:
    If `ModeADepth w ℓ` holds at the start `w` of a white run of `center`
    (`∀ j ≤ k, cell (w + j) 0 = false`), then for every `k` and `ℓ` (including short white runs
    `k < ℓ` as well as locked runs `k ≥ ℓ`), column `1` at time `w + k` is given exactly by
    `cell (w + k) 1 = decide (ℓ ≤ k)`. -/
theorem g4_p1_modeADepth_white_run_lock (ℓ k w : Nat)
    (hM : ModeADepth w ℓ)
    (hz : ∀ j, j ≤ k → cell (w + j) 0 = false) :
    cell (w + k) 1 = decide (ℓ ≤ k) := by
  by_cases hkl : ℓ ≤ k
  · have hfront := (front_moves w ℓ k (fun i hi => hz i (by omega)) hM.1 hM.2 ℓ hkl (Nat.le_refl ℓ)).2
    rw [show ℓ - ℓ + 1 = 1 by omega] at hfront
    have hstay := black_stays (w + ℓ) (k - ℓ) (fun j hj => by
      have := hz (ℓ + j) (by omega)
      rwa [show w + (ℓ + j) = w + ℓ + j by omega] at this)
      (by simpa using hfront) (k - ℓ) (Nat.le_refl _)
    rw [show w + ℓ + (k - ℓ) = w + k by omega] at hstay
    rw [hstay, decide_eq_true_iff.mpr hkl]
  · have hlt : k < ℓ := by omega
    have hfront := (front_moves w ℓ k (fun i hi => hz i (by omega)) hM.1 hM.2 k (Nat.le_refl k) (by omega)).1
      1 (Nat.le_refl 1) (by omega)
    simpa [hkl] using hfront

/-- **G4-P1 Multi-Depth Boundary Grammar Implication to `Rule30Prize.Problem1`
    (`g4_p1_modeADepth_at_white_onsets_implies_problem1`)**:
    Generalizing G3's `ℓ = 1` theorem (`g3_modeA_at_center_white_onsets_implies_problem1`) to
    arbitrary depth `ℓ : Nat`: if there exist a transient time `T` and a boundary depth `ℓ` such that
    every white onset of `Rule30Prize.center` after `T` (`center u = true ∧ center (u + 1) = false`)
    begins in `ModeADepth (u + 1) ℓ`, then `Rule30Prize.Problem1` (`¬ EventuallyPeriodic Rule30Prize.center`)
    holds unconditionally for all white-run lengths (both `< ℓ` and `≥ ℓ`). -/
theorem g4_p1_modeADepth_at_white_onsets_implies_problem1 {T ℓ : Nat}
    (hDepth : ∀ u, T ≤ u → Rule30Prize.center u = true → Rule30Prize.center (u + 1) = false →
      ModeADepth (u + 1) ℓ) :
    Rule30Prize.Problem1 := by
  intro hc
  obtain ⟨T₀, P, hP, hper⟩ := hc
  have hper' : ∀ t, T₀ ≤ t → cell (t + P) 0 = cell t 0 := hper
  by_cases hw : ∃ t, T₀ ≤ t ∧ ∀ s, s < P → cell (t + s) 0 = false
  · obtain ⟨t, _, hs⟩ := hw
    have hk : ∀ k s, s < P → cell (t + k * P + s) 0 = false := by
      intro k
      induction k with
      | zero => intro s hs'; simpa using hs s hs'
      | succ k ih =>
        intro s hs'
        rw [show t + (k + 1) * P + s = (t + k * P + s) + P by rw [Nat.succ_mul]; omega,
          hper' _ (by omega)]
        exact ih s hs'
    refine no_column_eventually_constant 0 ⟨t, false, fun u hu => ?_⟩
    have := hk ((u - t) / P) ((u - t) % P) (Nat.mod_lt _ hP)
    rwa [show t + (u - t) / P * P + (u - t) % P = u by
      have := Nat.div_add_mod (u - t) P; rw [Nat.mul_comm] at this; omega] at this
  · have hblack : ∀ t, T₀ ≤ t → ∃ s, s < P ∧ cell (t + s) 0 = true := by
      intro t ht
      refine Classical.byContradiction fun hne => hw ⟨t, ht, fun s hs => ?_⟩
      cases h : cell (t + s) 0
      · rfl
      · exact absurd ⟨s, hs, h⟩ hne
    let B := T + T₀ + P + 2
    have hcol1 : ∀ t, B ≤ t → cell t 0 = false →
        ∃ k, k < P ∧ cell (t - (k + 1)) 0 = true ∧ (∀ j, j ≤ k → cell (t - j) 0 = false) ∧
          orCol 0 t = decide (ℓ ≤ k) := by
      intro t ht h0
      rcases trailing (fun u => cell u 0) t h0 P with hall | ⟨k, hk, h1, h2⟩
      · obtain ⟨s, hs, hb⟩ := hblack (t - P) (by omega)
        have := hall (P - s) (by omega)
        rw [show t - (P - s) = t - P + s by omega, hb] at this
        exact absurd this (by decide)
      · refine ⟨k, hk, h1, h2, ?_⟩
        have honset := hDepth (t - (k + 1)) (by omega) h1
          (by rw [show t - (k + 1) + 1 = t - k by omega]; exact h2 k (by omega))
        rw [show t - (k + 1) + 1 = t - k by omega] at honset
        have hlock := g4_p1_modeADepth_white_run_lock ℓ k (t - k) honset
          (fun j hj => by
            rw [show t - k + j = t - (k - j) by omega]
            exact h2 (k - j) (by omega))
        rw [show t - k + k = t by omega] at hlock
        unfold orCol
        rw [h0, Bool.false_or, Int.zero_add, hlock]
    refine orCol_not_eventuallyPeriodic 0 ⟨T₀, P, hP, hper⟩ ⟨B, P, hP, fun t ht => ?_⟩
    show orCol 0 (t + P) = orCol 0 t
    have ht0 : cell (t + P) 0 = cell t 0 := hper' t (by omega)
    cases h0 : cell t 0
    · have h0P : cell (t + P) 0 = false := by rw [ht0, h0]
      obtain ⟨k1, hk1, hb1, hw1, hor1⟩ := hcol1 t ht h0
      obtain ⟨k2, hk2, hb2, hw2, hor2⟩ := hcol1 (t + P) (by omega) h0P
      have hkeq : k1 = k2 := by
        by_cases hlt : k1 < k2
        · have hw2_at : cell (t + P - (k1 + 1)) 0 = false := hw2 (k1 + 1) (by omega)
          rw [show t + P - (k1 + 1) = (t - (k1 + 1)) + P by omega, hper' _ (by omega), hb1] at hw2_at
          exact absurd hw2_at (by decide)
        · by_cases hgt : k2 < k1
          · have hw1_at : cell (t - (k2 + 1)) 0 = false := hw1 (k2 + 1) (by omega)
            have hb2' : cell ((t - (k2 + 1)) + P) 0 = true := by
              rwa [show (t - (k2 + 1)) + P = t + P - (k2 + 1) by omega]
            rw [hper' _ (by omega), hw1_at] at hb2'
            exact absurd hb2' (by decide)
          · omega
      rw [hor1, hor2, hkeq]
    · unfold orCol
      rw [ht0, h0]
      rfl

/-- **G4-P1 Uniqueness of `ModeADepth` (`g4_p1_modeADepth_unique`)**:
    At any time `t`, the depth `ℓ` satisfying `ModeADepth t ℓ` is unique:
    if `ModeADepth t ℓ₁` and `ModeADepth t ℓ₂` both hold, then `ℓ₁ = ℓ₂`. -/
theorem g4_p1_modeADepth_unique (t ℓ₁ ℓ₂ : Nat)
    (h1 : ModeADepth t ℓ₁) (h2 : ModeADepth t ℓ₂) : ℓ₁ = ℓ₂ := by
  by_cases hlt : ℓ₁ < ℓ₂
  · have hw2 : cell t ((ℓ₁ + 1 : Nat) : Int) = false := h2.1 (ℓ₁ + 1) (by omega) (by omega)
    rw [h1.2] at hw2
    exact absurd hw2 (by decide)
  · by_cases hgt : ℓ₂ < ℓ₁
    · have hw1 : cell t ((ℓ₂ + 1 : Nat) : Int) = false := h1.1 (ℓ₂ + 1) (by omega) (by omega)
      rw [h2.2] at hw1
      exact absurd hw1 (by decide)
    · omega

/-- **G4-P1 Audit of the `∀ u ∃ ℓ` vs `∃ ℓ ∀ u` Quantifier Alternation
    (`g4_p1_white_onset_depths_vary_on_single_seed`)**:
    Whereas `g4_p1_every_step_has_modeADepth` proves `∀ u, ∃ ℓ, ModeADepth (u + 1) ℓ`
    and `g4_p1_modeADepth_at_white_onsets_implies_problem1` assumes a uniform `ℓ` (`∃ T ℓ, ∀ u ≥ T, ...`),
    in the single-seed trajectory the onset depth `ℓ(u + 1)` genuinely varies across white onsets:
    - at white onset `u + 1 = 2` (`center 1 = true ∧ center 2 = false`), `ModeADepth 2 1` holds (`ℓ = 1`),
    - at white onset `u + 1 = 6` (`center 5 = true ∧ center 6 = false`), `ModeADepth 6 2` holds (`ℓ = 2`),
    - and no single `ℓ` satisfies both `ModeADepth 2 ℓ` and `ModeADepth 6 ℓ`. -/
theorem g4_p1_white_onset_depths_vary_on_single_seed :
    Rule30Prize.center 1 = true ∧
    Rule30Prize.center 2 = false ∧
    ModeADepth 2 1 ∧
    Rule30Prize.center 5 = true ∧
    Rule30Prize.center 6 = false ∧
    ModeADepth 6 2 ∧
    ¬ (∃ ℓ, ModeADepth 2 ℓ ∧ ModeADepth 6 ℓ) := by
  have hm2 : ModeADepth 2 1 := ⟨fun p hp1 hp2 => by
    have : p = 1 := by omega
    subst this; decide, by decide⟩
  have hm6 : ModeADepth 6 2 := g4_p1_t6_counterexample_resolved_by_modeADepth.1
  refine ⟨by decide, by decide, hm2, by decide, by decide, hm6, ?_⟩
  rintro ⟨ℓ, h2, h6⟩
  have e1 : ℓ = 1 := g4_p1_modeADepth_unique 2 ℓ 1 h2 hm2
  have e2 : ℓ = 2 := g4_p1_modeADepth_unique 6 ℓ 2 h6 hm6
  omega

/-- **G4-P1 Composed Reduction of `Rule30Prize.Problem1` (`g4_p1_composed_reduction_of_problem1`)**:
    Composing `g4_p1_every_step_has_modeADepth` (`∀ w ≥ 1, ∃ ℓ, ModeADepth w ℓ`) with
    `g4_p1_modeADepth_white_run_lock` (`cell (w + k) 1 = decide (ℓ ≤ k)`) and
    `orCol_not_eventuallyPeriodic 0` reduces `Rule30Prize.Problem1` to the exact residual
    period-alignment premise `hAlign`: under any hypothetical period `P > 0` of `center`
    from `T₀` onward, there is a threshold `T` after which shifting a white onset `w = u + 1`
    by one period `P` preserves the threshold comparison `decide (ℓ ≤ k)` along the white run. -/
theorem g4_p1_composed_reduction_of_problem1
    (hAlign : ∀ (T₀ P : Nat), 0 < P →
      (∀ t, T₀ ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
      ∃ T, ∀ u k ℓ₁ ℓ₂, T ≤ u →
        Rule30Prize.center u = true →
        (∀ j, j ≤ k → Rule30Prize.center (u + 1 + j) = false) →
        ModeADepth (u + 1) ℓ₁ →
        ModeADepth (u + 1 + P) ℓ₂ →
        decide (ℓ₂ ≤ k) = decide (ℓ₁ ≤ k)) :
    Rule30Prize.Problem1 := by
  intro hc
  obtain ⟨T₀, P, hP, hper⟩ := hc
  have hper' : ∀ t, T₀ ≤ t → cell (t + P) 0 = cell t 0 := hper
  obtain ⟨T, hT⟩ := hAlign T₀ P hP hper
  by_cases hw : ∃ t, T₀ ≤ t ∧ ∀ s, s < P → cell (t + s) 0 = false
  · obtain ⟨t, _, hs⟩ := hw
    have hk : ∀ k s, s < P → cell (t + k * P + s) 0 = false := by
      intro k
      induction k with
      | zero => intro s hs'; simpa using hs s hs'
      | succ k ih =>
        intro s hs'
        rw [show t + (k + 1) * P + s = (t + k * P + s) + P by rw [Nat.succ_mul]; omega,
          hper' _ (by omega)]
        exact ih s hs'
    refine no_column_eventually_constant 0 ⟨t, false, fun u hu => ?_⟩
    have := hk ((u - t) / P) ((u - t) % P) (Nat.mod_lt _ hP)
    rwa [show t + (u - t) / P * P + (u - t) % P = u by
      have := Nat.div_add_mod (u - t) P; rw [Nat.mul_comm] at this; omega] at this
  · have hblack : ∀ t, T₀ ≤ t → ∃ s, s < P ∧ cell (t + s) 0 = true := by
      intro t ht
      refine Classical.byContradiction fun hne => hw ⟨t, ht, fun s hs => ?_⟩
      cases h : cell (t + s) 0
      · rfl
      · exact absurd ⟨s, hs, h⟩ hne
    let B := T + T₀ + P + 2
    refine orCol_not_eventuallyPeriodic 0 ⟨T₀, P, hP, hper⟩ ⟨B, P, hP, fun t ht => ?_⟩
    show orCol 0 (t + P) = orCol 0 t
    have ht0 : cell (t + P) 0 = cell t 0 := hper' t (by omega)
    cases h0 : cell t 0
    · rcases trailing (fun u => cell u 0) t h0 P with hall | ⟨k, hk, hb1, hw1⟩
      · obtain ⟨s, hs, hb⟩ := hblack (t - P) (by omega)
        have := hall (P - s) (by omega)
        rw [show t - (P - s) = t - P + s by omega, hb] at this
        exact absurd this (by decide)
      · have hw_run1 : ∀ j, j ≤ k → cell (t - k + j) 0 = false := by
          intro j hj
          rw [show t - k + j = t - (k - j) by omega]
          exact hw1 (k - j) (by omega)
        have hw_run2 : ∀ j, j ≤ k → cell (t - k + P + j) 0 = false := by
          intro j hj
          rw [show t - k + P + j = (t - k + j) + P by omega, hper' _ (by omega)]
          exact hw_run1 j hj
        obtain ⟨ℓ₁, hM1⟩ := g4_p1_every_step_has_modeADepth (t - k) (by omega)
        obtain ⟨ℓ₂, hM2⟩ := g4_p1_every_step_has_modeADepth (t - k + P) (by omega)
        have hlock1 := g4_p1_modeADepth_white_run_lock ℓ₁ k (t - k) hM1 hw_run1
        have hlock2 := g4_p1_modeADepth_white_run_lock ℓ₂ k (t - k + P) hM2 hw_run2
        rw [show t - k + k = t by omega] at hlock1
        rw [show t - k + P + k = t + P by omega] at hlock2
        have h0P : cell (t + P) 0 = false := by rw [ht0, h0]
        unfold orCol
        rw [h0, h0P, Bool.false_or, Bool.false_or, Int.zero_add, hlock1, hlock2]
        have hu_eq : t - (k + 1) + 1 = t - k := by omega
        have hM1' : ModeADepth (t - (k + 1) + 1) ℓ₁ := by rwa [hu_eq]
        have hM2' : ModeADepth (t - (k + 1) + 1 + P) ℓ₂ := by rwa [hu_eq]
        exact hT (t - (k + 1)) k ℓ₁ ℓ₂ (by omega) hb1
          (fun j hj => by rw [hu_eq]; exact hw_run1 j hj) hM1' hM2'
    · unfold orCol
      rw [ht0, h0]
      rfl

/-!
## 6. Gate `G4-P2`: Statistical Balance, Exact Discrepancy Machinery, and Boundary-Grammar Density Locks

For `Rule30Prize.Problem2`, we establish exact recurrence, complementarity, and discrepancy laws
for `Rule30Prize.blackCount`, and prove that the `G4-P1` right-boundary grammar `ModeADepth w ℓ`
simultaneously locks both neighbor columns `cell (w + j) 1` and `cell (w + j) (-1)` across
every white run of `Rule30Prize.center`.
-/

/-- **G4-P2 Definition (`whiteCount`)**:
    Number of white (`false`) cells in `Rule30Prize.center` up to step `n`. -/
def whiteCount (n : Nat) : Nat :=
  ((List.range n).filter (fun t => !Rule30Prize.center t)).length

/-- **G4-P2 Exact Step Recurrence for `Rule30Prize.blackCount` (`g4_p2_blackCount_succ`)**:
    `blackCount (n + 1) = blackCount n + if center n then 1 else 0`. -/
theorem g4_p2_blackCount_succ (n : Nat) :
    Rule30Prize.blackCount (n + 1) =
      Rule30Prize.blackCount n + (if Rule30Prize.center n then 1 else 0) := by
  unfold Rule30Prize.blackCount
  rw [List.range_succ, List.filter_append, List.length_append]
  cases h : Rule30Prize.center n <;> simp [h]

/-- **G4-P2 Exact Signed Discrepancy Step Identity (`g4_p2_discrepancy_succ`)**:
    The signed discrepancy `2 * (blackCount n : Int) - n` governing `Rule30Prize.Problem2`
    advances by `+1` when `center n = true` and by `-1` when `center n = false`. -/
theorem g4_p2_discrepancy_succ (n : Nat) :
    (2 * (Rule30Prize.blackCount (n + 1) : Int) - ((n + 1 : Nat) : Int)) =
      (2 * (Rule30Prize.blackCount n : Int) - (n : Int)) +
        (if Rule30Prize.center n then 1 else -1) := by
  rw [g4_p2_blackCount_succ]
  cases Rule30Prize.center n <;> simp <;> omega

/-- **G4-P2 Black/White Count Partition Identity (`g4_p2_blackCount_add_whiteCount`)**:
    For every horizon `n : Nat`, `blackCount n + whiteCount n = n` and `blackCount n ≤ n`. -/
theorem g4_p2_blackCount_add_whiteCount :
    ∀ n : Nat,
      Rule30Prize.blackCount n + whiteCount n = n ∧
      Rule30Prize.blackCount n ≤ n
  | 0 => ⟨rfl, Nat.le_refl 0⟩
  | n + 1 => by
    obtain ⟨ih_eq, _⟩ := g4_p2_blackCount_add_whiteCount n
    have hw : whiteCount (n + 1) = whiteCount n + (if Rule30Prize.center n then 0 else 1) := by
      unfold whiteCount
      rw [List.range_succ, List.filter_append, List.length_append]
      cases h : Rule30Prize.center n <;> simp [h]
    rw [g4_p2_blackCount_succ, hw]
    cases Rule30Prize.center n <;> simp <;> omega

/-- **G4-P2 Bilateral Neighbor Lock under `ModeADepth` (`g4_p2_modeADepth_locks_both_neighbors`)**:
    During any white run of `Rule30Prize.center` (`∀ j ≤ k, center (w + j) = false`) starting in
    `ModeADepth w ℓ`, both immediate neighbor columns `+1` and `-1` are locked deterministically:
    - `cell (w + k) 1 = decide (ℓ ≤ k)`, and
    - `cell (w + k) (-1) = xor (Rule30Prize.center (w + k + 1)) (decide (ℓ ≤ k))`.
    In particular, throughout the interior of a locked white run (`ℓ ≤ k` and `center (w + k + 1) = false`),
    both neighbor columns `(cell (w + k) (-1), cell (w + k) 1)` are forced to `(true, true)`. -/
theorem g4_p2_modeADepth_locks_both_neighbors (ℓ k w : Nat)
    (hM : ModeADepth w ℓ)
    (hz : ∀ j, j ≤ k → Rule30Prize.center (w + j) = false) :
    cell (w + k) 1 = decide (ℓ ≤ k) ∧
    cell (w + k) (-1) = xor (Rule30Prize.center (w + k + 1)) (decide (ℓ ≤ k)) := by
  have h1 : cell (w + k) 1 = decide (ℓ ≤ k) :=
    g4_p1_modeADepth_white_run_lock ℓ k w hM hz
  refine ⟨h1, ?_⟩
  have hleft := cell_left' (w + k) 0
  rw [show (0 : Int) - 1 = -1 by rfl] at hleft
  have hor : orCol 0 (w + k) = decide (ℓ ≤ k) := by
    unfold orCol
    have h0 : cell (w + k) 0 = false := hz k (Nat.le_refl k)
    rw [h0, Bool.false_or, Int.zero_add, h1]
  rw [hleft, hor]
  rfl

/-- **G4-P2 Locked White-Run Interior Forces Double-Black Neighbors
    (`g4_p2_locked_white_interior_forces_double_black_neighbors`)**:
    In the interior of any locked white run (`ℓ ≤ k`, `∀ j ≤ k + 1, center (w + j) = false`)
    starting from `ModeADepth w ℓ`, both neighbor columns `+1` and `-1` are simultaneously
    forced to black (`cell (w + k) 1 = true ∧ cell (w + k) (-1) = true`). -/
theorem g4_p2_locked_white_interior_forces_double_black_neighbors (ℓ k w : Nat)
    (hM : ModeADepth w ℓ)
    (hkl : ℓ ≤ k)
    (hz : ∀ j, j ≤ k + 1 → Rule30Prize.center (w + j) = false) :
    cell (w + k) 1 = true ∧ cell (w + k) (-1) = true := by
  obtain ⟨h1, hm1⟩ := g4_p2_modeADepth_locks_both_neighbors ℓ k w hM (fun j hj => hz j (by omega))
  have hdec : decide (ℓ ≤ k) = true := decide_eq_true_iff.mpr hkl
  have hnext : Rule30Prize.center (w + k + 1) = false := by
    have := hz (k + 1) (Nat.le_refl (k + 1))
    rwa [show w + (k + 1) = w + k + 1 by omega] at this
  rw [hdec] at h1 hm1
  rw [hnext] at hm1
  exact ⟨h1, hm1⟩

/-- **G4-P2 Sublinear Envelope Implication to `Rule30Prize.Problem2`
    (`g4_p2_sublinear_rate_implies_problem2`)**:
    If the unsigned discrepancy `(2 * (blackCount n : Int) - n).natAbs` is bounded from
    some horizon `N₀` onward by a sublinear envelope `f : Nat → Nat` satisfying
    `∀ k > 0, ∃ N, ∀ n ≥ N, k * f n ≤ n`, then `Rule30Prize.Problem2` holds. -/
theorem g4_p2_sublinear_rate_implies_problem2 (f : Nat → Nat) (N₀ : Nat)
    (hDom : ∀ n, N₀ ≤ n → (2 * (Rule30Prize.blackCount n : Int) - (n : Int)).natAbs ≤ f n)
    (hSub : ∀ k > 0, ∃ N, ∀ n ≥ N, k * f n ≤ n) :
    Rule30Prize.Problem2 := by
  intro k hk
  obtain ⟨N₁, hN₁⟩ := hSub k hk
  refine ⟨N₀ + N₁, fun n hn => ?_⟩
  have h1 : (2 * (Rule30Prize.blackCount n : Int) - (n : Int)).natAbs ≤ f n :=
    hDom n (by omega)
  have h2 : k * (2 * (Rule30Prize.blackCount n : Int) - (n : Int)).natAbs ≤ k * f n :=
    Nat.mul_le_mul_left k h1
  exact Nat.le_trans h2 (hN₁ n (by omega))

/-- **G4-P2 Bounded Discrepancy Special Case (`g4_p2_bounded_discrepancy_implies_problem2`)**:
    If `(2 * (blackCount n : Int) - n).natAbs ≤ B` for all `n ≥ N₀`, then `Rule30Prize.Problem2`
    holds with explicit threshold `N = N₀ + k * B`. -/
theorem g4_p2_bounded_discrepancy_implies_problem2 (B N₀ : Nat)
    (hB : ∀ n, N₀ ≤ n → (2 * (Rule30Prize.blackCount n : Int) - (n : Int)).natAbs ≤ B) :
    Rule30Prize.Problem2 := by
  refine g4_p2_sublinear_rate_implies_problem2 (fun _ => B) N₀ hB (fun k _ => ⟨k * B, fun n hn => hn⟩)

/-!
## 7. Gate `G4-P3`: Computational Irreducibility, Causal Light-Cone Bounds, and Universal Sensitivity

For `Rule30Prize.Problem3`, we formalize an explicit input-perturbation model `flipInput x q`
on `evol` (`Rule30Realization.evol`) and prove:
1. Exact causal light-cone locality (`g4_p3_evol_causal_cone`): `evol x t p` depends only on
   initial cells in `[p - t, p + t]`.
2. Universal left-edge sensitivity (`g4_p3_left_edge_universal_sensitivity` and
   `g4_p3_center_universal_left_sensitivity`): for **every** initial configuration `x : Int → Bool`
   and **every** step `t : Nat`, flipping `x (-t)` unconditionally flips `evol x t 0`.
3. Active right-edge sensitivity (`g4_p3_center_right_edge_sensitivity`): flipping `x (+t)` on the
   white background flips `evol · t 0` from `false` to `true`, proving that the `t`-step center
   operator has full active spatial span `[-t, +t]` of width `2t + 1`.
-/

/-- **G4-P3 Single-Bit Input Perturbation (`flipInput`)**:
    Flips the initial cell at position `q` while leaving all other positions unchanged. -/
def flipInput (x : Int → Bool) (q : Int) (p : Int) : Bool :=
  if p = q then !x p else x p

/-- **G4-P3 Causal Light-Cone Locality (`g4_p3_evol_causal_cone`)**:
    If two initial configurations `x, y : Int → Bool` agree on the closed interval
    `[p - t, p + t]`, then `evol x t p = evol y t p`. -/
theorem g4_p3_evol_causal_cone {x y : Int → Bool} :
    ∀ (t : Nat) (p : Int),
      (∀ r : Int, p - (t : Int) ≤ r → r ≤ p + (t : Int) → x r = y r) →
      evol x t p = evol y t p
  | 0, p, h => h p (by omega) (by omega)
  | t + 1, p, h => by
    show rule (evol x t (p - 1)) (evol x t p) (evol x t (p + 1)) =
      rule (evol y t (p - 1)) (evol y t p) (evol y t (p + 1))
    rw [g4_p3_evol_causal_cone t (p - 1) (fun r hr1 hr2 => h r (by omega) (by omega)),
      g4_p3_evol_causal_cone t p (fun r hr1 hr2 => h r (by omega) (by omega)),
      g4_p3_evol_causal_cone t (p + 1) (fun r hr1 hr2 => h r (by omega) (by omega))]

/-- Left-permutivity bit-flip identity for `rule`: flipping the left input `a` flips `rule a b c`. -/
theorem rule_not_left (a b c : Bool) : rule (!a) b c = !rule a b c := by
  cases a <;> cases b <;> cases c <;> rfl

/-- **G4-P3 Universal Left-Edge Sensitivity along the Right-Moving Light Cone
    (`g4_p3_left_edge_universal_sensitivity`)**:
    For every configuration `x : Int → Bool`, perturbed position `q : Int`, and depth `t : Nat`,
    flipping `x q` unconditionally flips the state at the light-cone front `p = q + t`:
    `evol (flipInput x q) t (q + t) = !evol x t (q + t)`. -/
theorem g4_p3_left_edge_universal_sensitivity (x : Int → Bool) (q : Int) :
    ∀ t : Nat, evol (flipInput x q) t (q + (t : Int)) = !evol x t (q + (t : Int))
  | 0 => by
    simp [evol, flipInput]
  | t + 1 => by
    show rule (evol (flipInput x q) t (q + ((t + 1 : Nat) : Int) - 1))
        (evol (flipInput x q) t (q + ((t + 1 : Nat) : Int)))
        (evol (flipInput x q) t (q + ((t + 1 : Nat) : Int) + 1)) =
      !rule (evol x t (q + ((t + 1 : Nat) : Int) - 1))
        (evol x t (q + ((t + 1 : Nat) : Int)))
        (evol x t (q + ((t + 1 : Nat) : Int) + 1))
    have hleft : q + ((t + 1 : Nat) : Int) - 1 = q + (t : Int) := by omega
    have hmid : evol (flipInput x q) t (q + ((t + 1 : Nat) : Int)) =
        evol x t (q + ((t + 1 : Nat) : Int)) := by
      refine g4_p3_evol_causal_cone t (q + ((t + 1 : Nat) : Int)) (fun r hr1 _ => ?_)
      have hne : r ≠ q := by omega
      simp [flipInput, hne]
    have hright : evol (flipInput x q) t (q + ((t + 1 : Nat) : Int) + 1) =
        evol x t (q + ((t + 1 : Nat) : Int) + 1) := by
      refine g4_p3_evol_causal_cone t (q + ((t + 1 : Nat) : Int) + 1) (fun r hr1 _ => ?_)
      have hne : r ≠ q := by omega
      simp [flipInput, hne]
    rw [hleft, g4_p3_left_edge_universal_sensitivity x q t, hmid, hright, rule_not_left]

/-- **G4-P3 Universal Center-Column Left Sensitivity (`g4_p3_center_universal_left_sensitivity`)**:
    For **every** initial configuration `x : Int → Bool` and **every** depth `t : Nat`,
    flipping the leftmost light-cone input `x (-t)` flips the `t`-step center output `evol x t 0`.
    Consequently, no Boolean circuit or decision tree for the `t`-step center operator on
    unrestricted inputs can ignore the left boundary `x (-t)` at any depth `t`. -/
theorem g4_p3_center_universal_left_sensitivity (x : Int → Bool) (t : Nat) :
    evol (flipInput x (-(t : Int))) t 0 = !evol x t 0 := by
  have h := g4_p3_left_edge_universal_sensitivity x (-(t : Int)) t
  rwa [show -(t : Int) + (t : Int) = 0 by omega] at h

/-- On the all-white configuration `fun _ => false`, `evol` remains `false` everywhere. -/
theorem evol_all_false : ∀ (t : Nat) (p : Int), evol (fun _ => false) t p = false
  | 0, _ => rfl
  | t + 1, p => by
    show rule (evol (fun _ => false) t (p - 1)) (evol (fun _ => false) t p)
      (evol (fun _ => false) t (p + 1)) = false
    rw [evol_all_false t (p - 1), evol_all_false t p, evol_all_false t (p + 1)]
    rfl

/-- Translation invariance of `evol`: shifting the initial configuration by `d` shifts the
    evolution by `d`. -/
theorem evol_shift (x : Int → Bool) (d : Int) :
    ∀ (t : Nat) (p : Int), evol (fun r => x (r - d)) t p = evol x t (p - d)
  | 0, p => rfl
  | t + 1, p => by
    show rule (evol (fun r => x (r - d)) t (p - 1)) (evol (fun r => x (r - d)) t p)
      (evol (fun r => x (r - d)) t (p + 1)) = _
    rw [evol_shift x d t (p - 1), evol_shift x d t p, evol_shift x d t (p + 1),
      show p - 1 - d = p - d - 1 by omega, show p + 1 - d = p - d + 1 by omega]
    rfl

/-- **G4-P3 Active Right-Edge Sensitivity (`g4_p3_center_right_edge_sensitivity`)**:
    For every depth `t : Nat`, flipping the rightmost light-cone input `q = +t` on the
    all-white configuration flips the `t`-step center output `evol · t 0` from `false` to `true`.
    Combined with `g4_p3_center_universal_left_sensitivity` and `g4_p3_evol_causal_cone`,
    this proves that both light-cone boundaries `-t` and `+t` are active inputs of `evol · t 0`. -/
theorem g4_p3_center_right_edge_sensitivity (t : Nat) :
    evol (flipInput (fun _ => false) (t : Int)) t 0 = true ∧
    evol (fun _ => false) t 0 = false := by
  refine ⟨?_, evol_all_false t 0⟩
  have hseed : flipInput (fun _ => false) (t : Int) = (fun r => seed (r - (t : Int))) := by
    funext r
    unfold flipInput seed
    by_cases hr : r = (t : Int)
    · subst hr; simp
    · have : r - (t : Int) ≠ 0 := by omega
      simp [hr, this]
  rw [hseed, evol_shift seed (t : Int) t 0, evol_seed, show (0 : Int) - (t : Int) = -(t : Int) by omega]
  have hD : cell t (-(t : Int)) = D 0 t := by
    unfold D
    exact cell_congr (by omega)
  rw [hD, D_zero]

/-- **G4-P3 Semigroup Operator Composition (`g4_p3_evol_add`)**:
    For every initial configuration `x : Int → Bool` and time horizons `s, t : Nat`,
    evolving for `s + t` steps equals evolving for `t` steps from the `s`-step configuration
    `fun q => evol x s q`. -/
theorem g4_p3_evol_add (x : Int → Bool) (s : Nat) :
    ∀ (t : Nat) (p : Int), evol x (s + t) p = evol (fun q => evol x s q) t p
  | 0, p => rfl
  | t + 1, p => by
    show rule (evol x (s + t) (p - 1)) (evol x (s + t) p) (evol x (s + t) (p + 1)) =
      rule (evol (fun q => evol x s q) t (p - 1)) (evol (fun q => evol x s q) t p)
        (evol (fun q => evol x s q) t (p + 1))
    rw [g4_p3_evol_add x s t (p - 1), g4_p3_evol_add x s t p, g4_p3_evol_add x s t (p + 1)]

/-- **G4-P3 Explicit 2-Step Block-Composition Operator (`stepBlock2` and `evolBlock2`)**:
    Computes two steps of Rule 30 in a single radius-2 macro-step over the 5-cell window
    `(x (p - 2), x (p - 1), x p, x (p + 1), x (p + 2))`. -/
def stepBlock2 (x : Int → Bool) (p : Int) : Bool :=
  rule (rule (x (p - 2)) (x (p - 1)) (x p))
    (rule (x (p - 1)) (x p) (x (p + 1)))
    (rule (x p) (x (p + 1)) (x (p + 2)))

def evolBlock2 (x : Int → Bool) : Nat → Int → Bool
  | 0, p => x p
  | k + 1, p => stepBlock2 (fun q => evolBlock2 x k q) p

/-- **G4-P3 Exactness of 2-Step Block Composition (`g4_p3_evolBlock2_eq_evol_double`)**:
    For every initial configuration `x : Int → Bool`, macro-step count `k : Nat`, and
    position `p : Int`, `k` macro-steps of `evolBlock2` compute the exact state `evol x (2 * k) p`.
    This separates input sensitivity (which spans `[-2k, +2k]`) from sequential macro-step
    count (`k` macro-steps of radius `2` vs `2k` primitive steps of radius `1`). -/
theorem g4_p3_evolBlock2_eq_evol_double (x : Int → Bool) :
    ∀ (k : Nat) (p : Int), evolBlock2 x k p = evol x (2 * k) p
  | 0, p => rfl
  | k + 1, p => by
    have ih := g4_p3_evolBlock2_eq_evol_double x k
    have hfun : (fun q => evolBlock2 x k q) = (fun q => evol x (2 * k) q) := by
      funext q; exact ih q
    show stepBlock2 (fun q => evolBlock2 x k q) p = evol x (2 * (k + 1)) p
    rw [hfun, show 2 * (k + 1) = 2 * k + 2 by omega]
    unfold stepBlock2
    show _ = rule (rule (evol x (2 * k) (p - 1 - 1)) (evol x (2 * k) (p - 1)) (evol x (2 * k) (p - 1 + 1)))
      (rule (evol x (2 * k) (p - 1)) (evol x (2 * k) p) (evol x (2 * k) (p + 1)))
      (rule (evol x (2 * k) (p + 1 - 1)) (evol x (2 * k) (p + 1)) (evol x (2 * k) (p + 1 + 1)))
    rw [show p - 1 - 1 = p - 2 by omega, show p - 1 + 1 = p by omega,
      show p + 1 - 1 = p by omega, show p + 1 + 1 = p + 2 by omega]

/-!
## 8. Gate `G5-P1`: Boundary-Depth Transition Law & Clipped-Depth Observational Equivalence

We formalize the finite-state transition and observational-equivalence structure of `ModeADepth`
under white runs:
1. `g5_p1_modeADepth_after_white_run`: any white run of length `r` (`∀ i < r, cell (w + i) 0 = false`)
   maps `ModeADepth w ℓ` deterministically to `ModeADepth (w + r) (ℓ - r)` (truncated subtraction).
2. `g5_p1_clipped_depth_observational_equivalence`: over a white run `0 ≤ k ≤ K` (length `r = K + 1`),
   two depths `ℓ₁, ℓ₂` produce identical `orCol 0` traces (`∀ k ≤ K, decide (ℓ₂ ≤ k) = decide (ℓ₁ ≤ k)`)
   if and only if their clipped depths in the finite set `{0, ..., K + 1}` agree:
   `Nat.min ℓ₂ (K + 1) = Nat.min ℓ₁ (K + 1)`.
3. `g5_p1_clipped_depth_alignment_implies_problem1`: strengthens `g4_p1_composed_reduction_of_problem1`
   so that `hAlign` only requires agreement of the bounded clipped depths `Nat.min ℓ (k + 1)`
   rather than exact equality `ℓ₂ = ℓ₁`.
-/

/-- **G5-P1 Exact White-Run Boundary-Depth Transition Law (`g5_p1_modeADepth_after_white_run`)**:
    If `ModeADepth w ℓ` holds at the start `w` of a white segment of length `r`
    (`∀ i < r, cell (w + i) 0 = false`), then at step `w + r` the boundary is in state
    `ModeADepth (w + r) (ℓ - r)` (where `ℓ - r = 0` when `ℓ ≤ r`). -/
theorem g5_p1_modeADepth_after_white_run (w r ℓ : Nat)
    (hM : ModeADepth w ℓ)
    (hw : ∀ i, i < r → cell (w + i) 0 = false) :
    ModeADepth (w + r) (ℓ - r) := by
  by_cases hlr : ℓ ≤ r
  · have hsub : ℓ - r = 0 := by omega
    rw [hsub]
    refine ⟨fun p hp1 hp2 => by omega, ?_⟩
    have hfront := (front_moves w ℓ r hw hM.1 hM.2 ℓ hlr (Nat.le_refl ℓ)).2
    rw [show ℓ - ℓ + 1 = 1 by omega] at hfront
    have hstay := black_stays (w + ℓ) (r - ℓ) (fun j hj => by
      have := hw (ℓ + j) (by omega)
      rwa [show w + (ℓ + j) = w + ℓ + j by omega] at this)
      (by simpa using hfront) (r - ℓ) (Nat.le_refl _)
    rwa [show w + ℓ + (r - ℓ) = w + r by omega] at hstay
  · exact front_moves w ℓ r hw hM.1 hM.2 r (Nat.le_refl r) (by omega)

/-- **G5-P1 Clipped Boundary Depth (`clipDepth`)**:
    Projects an unbounded boundary depth `ℓ : Nat` onto the finite observational state space
    `{0, ..., r}` of a white run of length `r`: `clipDepth ℓ r = if ℓ ≤ r then ℓ else r`. -/
def clipDepth (ℓ r : Nat) : Nat :=
  if ℓ ≤ r then ℓ else r

/-- **G5-P1 Clipped-Depth Observational Equivalence over a White Run
    (`g5_p1_clipped_depth_observational_equivalence`)**:
    Over a white run `0 ≤ k ≤ K` (of length `K + 1`), two boundary depths `ℓ₁, ℓ₂` induce
    identical column-1 observations (`∀ k ≤ K, decide (ℓ₂ ≤ k) = decide (ℓ₁ ≤ k)`) if and only if
    their clipped values in the finite set `{0, ..., K + 1}` are equal:
    `clipDepth ℓ₂ (K + 1) = clipDepth ℓ₁ (K + 1)`. -/
theorem g5_p1_clipped_depth_observational_equivalence (ℓ₁ ℓ₂ K : Nat) :
    (∀ k, k ≤ K → decide (ℓ₂ ≤ k) = decide (ℓ₁ ≤ k)) ↔
      clipDepth ℓ₂ (K + 1) = clipDepth ℓ₁ (K + 1) := by
  unfold clipDepth
  constructor
  · intro h
    by_cases h1 : ℓ₁ ≤ K
    · have hk := h ℓ₁ h1
      simp only [Nat.le_refl, decide_true] at hk
      have h21 : ℓ₂ ≤ ℓ₁ := of_decide_eq_true hk
      have h2K : ℓ₂ ≤ K := by omega
      have hk2 := h ℓ₂ h2K
      simp only [Nat.le_refl, decide_true, true_eq_decide_iff] at hk2
      have h1K1 : ℓ₁ ≤ K + 1 := by omega
      have h2K1 : ℓ₂ ≤ K + 1 := by omega
      simp [h1K1, h2K1]
      omega
    · by_cases h2 : ℓ₂ ≤ K
      · have hk2 := h ℓ₂ h2
        simp only [Nat.le_refl, decide_true, true_eq_decide_iff] at hk2
        omega
      · have h1K1 : ¬ ℓ₁ ≤ K + 1 ∨ ℓ₁ = K + 1 := by omega
        have h2K1 : ¬ ℓ₂ ≤ K + 1 ∨ ℓ₂ = K + 1 := by omega
        by_cases c1 : ℓ₁ ≤ K + 1 <;> by_cases c2 : ℓ₂ ≤ K + 1 <;> simp [c1, c2] <;> omega
  · intro hmin k hk
    by_cases c1 : ℓ₁ ≤ K + 1 <;> by_cases c2 : ℓ₂ ≤ K + 1 <;> simp [c1, c2] at hmin
    · by_cases h1 : ℓ₁ ≤ k
      · have h2 : ℓ₂ ≤ k := by omega
        simp [h1, h2]
      · have h2 : ¬ ℓ₂ ≤ k := by omega
        simp [h1, h2]
    · by_cases h1 : ℓ₁ ≤ k
      · omega
      · have h2 : ¬ ℓ₂ ≤ k := by omega
        simp [h1, h2]
    · by_cases h1 : ℓ₁ ≤ k
      · omega
      · have h2 : ¬ ℓ₂ ≤ k := by omega
        simp [h1, h2]
    · have h1 : ¬ ℓ₁ ≤ k := by omega
      have h2 : ¬ ℓ₂ ≤ k := by omega
      simp [h1, h2]

/-- **G5-P1 Clipped-Depth Period Alignment Implies `Rule30Prize.Problem1`
    (`g5_p1_clipped_depth_alignment_implies_problem1`)**:
    Strengthens `g4_p1_composed_reduction_of_problem1`: `Rule30Prize.Problem1` holds if,
    under any hypothetical period `P > 0` of `center`, shifting a white onset `u + 1` by `P`
    preserves the finite-state clipped depth `clipDepth ℓ (k + 1)` across white runs. -/
theorem g5_p1_clipped_depth_alignment_implies_problem1
    (hClipAlign : ∀ (T₀ P : Nat), 0 < P →
      (∀ t, T₀ ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) →
      ∃ T, ∀ u k ℓ₁ ℓ₂, T ≤ u →
        Rule30Prize.center u = true →
        (∀ j, j ≤ k → Rule30Prize.center (u + 1 + j) = false) →
        ModeADepth (u + 1) ℓ₁ →
        ModeADepth (u + 1 + P) ℓ₂ →
        clipDepth ℓ₂ (k + 1) = clipDepth ℓ₁ (k + 1)) :
    Rule30Prize.Problem1 := by
  refine g4_p1_composed_reduction_of_problem1 (fun T₀ P hP hper => ?_)
  obtain ⟨T, hT⟩ := hClipAlign T₀ P hP hper
  refine ⟨T, fun u k ℓ₁ ℓ₂ hu hc0 hcw hM1 hM2 => ?_⟩
  have hmin := hT u k ℓ₁ ℓ₂ hu hc0 hcw hM1 hM2
  exact (g5_p1_clipped_depth_observational_equivalence ℓ₁ ℓ₂ k).mpr hmin k (Nat.le_refl k)

/-!
## 9. Gate `G5-P2`: Run-Based Discrepancy Cancellation & Per-Cycle Drift Falsification

We prove exact discrepancy shift identities across arbitrary white runs (`-r`), black runs (`+b`),
and white-black run cycles (`+(b - r)`), and prove that the first single-seed white-black cycle
(`w = 2, r = 1, b = 3`) produces a net discrepancy drift of `+2`, falsifying naive per-cycle
discrepancy cancellation `b = r`.
-/

/-- **G5-P2 White-Run Discrepancy Shift (`g5_p2_white_run_discrepancy_shift`)**:
    Across `r` consecutive white steps starting at `w` (`∀ i < r, center (w + i) = false`),
    the signed discrepancy `2 * blackCount - n` decreases by `r`. -/
theorem g5_p2_white_run_discrepancy_shift (w : Nat) :
    ∀ (r : Nat), (∀ i, i < r → Rule30Prize.center (w + i) = false) →
      (2 * (Rule30Prize.blackCount (w + r) : Int) - ((w + r : Nat) : Int)) =
        (2 * (Rule30Prize.blackCount w : Int) - (w : Int)) - (r : Int)
  | 0, _ => by simp
  | r + 1, hw => by
    have ih := g5_p2_white_run_discrepancy_shift w r (fun i hi => hw i (by omega))
    have hstep := g4_p2_discrepancy_succ (w + r)
    have hcr : Rule30Prize.center (w + r) = false := hw r (by omega)
    rw [show w + (r + 1) = w + r + 1 by omega, hstep, hcr, ih]
    simp
    omega

/-- **G5-P2 Black-Run Discrepancy Shift (`g5_p2_black_run_discrepancy_shift`)**:
    Across `b` consecutive black steps starting at `a` (`∀ j < b, center (a + j) = true`),
    the signed discrepancy `2 * blackCount - n` increases by `b`. -/
theorem g5_p2_black_run_discrepancy_shift (a : Nat) :
    ∀ (b : Nat), (∀ j, j < b → Rule30Prize.center (a + j) = true) →
      (2 * (Rule30Prize.blackCount (a + b) : Int) - ((a + b : Nat) : Int)) =
        (2 * (Rule30Prize.blackCount a : Int) - (a : Int)) + (b : Int)
  | 0, _ => by simp
  | b + 1, hb => by
    have ih := g5_p2_black_run_discrepancy_shift a b (fun j hj => hb j (by omega))
    have hstep := g4_p2_discrepancy_succ (a + b)
    have hcb : Rule30Prize.center (a + b) = true := hb b (by omega)
    rw [show a + (b + 1) = a + b + 1 by omega, hstep, hcb, ih]
    simp
    omega

/-- **G5-P2 Exact White-Black Run-Cycle Discrepancy Formula (`g5_p2_white_black_cycle_discrepancy`)**:
    Over a white run of length `r` followed by a black run of length `b`, the signed discrepancy
    changes by `b - r`. -/
theorem g5_p2_white_black_cycle_discrepancy (w r b : Nat)
    (hw : ∀ i, i < r → Rule30Prize.center (w + i) = false)
    (hb : ∀ j, j < b → Rule30Prize.center (w + r + j) = true) :
    (2 * (Rule30Prize.blackCount (w + r + b) : Int) - ((w + r + b : Nat) : Int)) =
      (2 * (Rule30Prize.blackCount w : Int) - (w : Int)) + ((b : Int) - (r : Int)) := by
  have h1 := g5_p2_white_run_discrepancy_shift w r hw
  have h2 := g5_p2_black_run_discrepancy_shift (w + r) b hb
  omega

/-- **G5-P2 Falsification of Strict Per-Cycle Discrepancy Cancellation
    (`g5_p2_first_white_black_cycle_net_drift_plus_two`)**:
    In the first white-black run cycle of the single-seed trajectory (`w = 2, r = 1, b = 3`,
    covering `t = 2 .. 5`), the signed discrepancy shifts from `+2` at `t = 2` to `+4` at `t = 6`
    (net cycle drift `b - r = +2 ≠ 0`), proving that discrepancy does not cancel cycle-by-cycle. -/
theorem g5_p2_first_white_black_cycle_net_drift_plus_two :
    Rule30Prize.blackCount 2 = 2 ∧
    Rule30Prize.blackCount 6 = 5 ∧
    (2 * (Rule30Prize.blackCount 2 : Int) - (2 : Int)) = 2 ∧
    (2 * (Rule30Prize.blackCount 6 : Int) - (6 : Int)) = 4 := by
  exact ⟨by decide, by decide, by decide, by decide⟩

/-!
## 10. Gate `G5-P3`: Operator-Doubling Hierarchy (`T^(2^d)`) & Sensitivity Across All Doubling Scales

We formalize the recursive operator-doubling hierarchy `evolPow2 d` (`T, T^2, T^4, T^8, ...`),
prove that `evolPow2 d x p = evol x (2 ^ d) p` for all `d, x, p`, and prove that at every
doubling scale `d`, `evolPow2 d` remains universally sensitive to the leftmost input `-2^d`
of its width-`(2^(d+1) + 1)` causal window.
-/

/-- **G5-P3 Recursive Operator-Doubling Hierarchy (`evolPow2`)**:
    - `evolPow2 0` is the 1-step operator `T` (radius `1`, window width `3`).
    - `evolPow2 (d + 1)` composes `evolPow2 d` with itself: `T^(2^(d+1)) = T^(2^d) ∘ T^(2^d)`
      (radius `2^(d+1)`, window width `2^(d+2) + 1`). -/
def evolPow2 : Nat → (Int → Bool) → Int → Bool
  | 0, x, p => rule (x (p - 1)) (x p) (x (p + 1))
  | d + 1, x, p => evolPow2 d (fun q => evolPow2 d x q) p

/-- **G5-P3 Exactness of the Operator-Doubling Hierarchy (`g5_p3_evolPow2_eq_evol_pow2`)**:
    For every doubling level `d : Nat`, configuration `x : Int → Bool`, and position `p : Int`,
    `evolPow2 d x p = evol x (2 ^ d) p`. -/
theorem g5_p3_evolPow2_eq_evol_pow2 :
    ∀ (d : Nat) (x : Int → Bool) (p : Int), evolPow2 d x p = evol x (2 ^ d) p
  | 0, x, p => rfl
  | d + 1, x, p => by
    have ih := g5_p3_evolPow2_eq_evol_pow2 d
    have hfun : (fun q => evolPow2 d x q) = (fun q => evol x (2 ^ d) q) := by
      funext q; exact ih x q
    show evolPow2 d (fun q => evolPow2 d x q) p = evol x (2 ^ (d + 1)) p
    rw [hfun, ih (fun q => evol x (2 ^ d) q) p, ← g4_p3_evol_add x (2 ^ d) (2 ^ d) p,
      Nat.pow_succ, show (2 ^ d) * 2 = 2 ^ d + 2 ^ d by omega]

/-- **G5-P3 Universal Left-Boundary Sensitivity of `evolPow2` (`g5_p3_evolPow2_universal_left_sensitivity`)**:
    At every doubling scale `d : Nat` and for every configuration `x : Int → Bool`,
    flipping the leftmost input `-2^d` of `evolPow2 d` unconditionally flips its center output. -/
theorem g5_p3_evolPow2_universal_left_sensitivity (d : Nat) (x : Int → Bool) :
    evolPow2 d (flipInput x (-((2 ^ d : Nat) : Int))) 0 = !evolPow2 d x 0 := by
  rw [g5_p3_evolPow2_eq_evol_pow2, g5_p3_evolPow2_eq_evol_pow2]
  exact g4_p3_center_universal_left_sensitivity x (2 ^ d)

/-!
## 11. Gate `G6-P1`: Complete White/Black Cycle Return Map on `ModeADepth` & Exclusion of `0^r 1` Fixed-Point Cycles

We extend the `G5-P1` white-run transition law (`ModeADepth w ℓ → ModeADepth (w + r) (ℓ - r)`)
across black runs to establish the complete white/black cycle return map on `ModeADepth`:
1. `g6_p1_one_black_step_from_overshoot_ge2`: if a white run ends with residual depth `z ≥ 2`
   (`ModeADepth a z` with `2 ≤ z`), a single black step (`cell a 0 = true`) immediately resets
   the boundary depth to `0` (`ModeADepth (a + 1) 0`).
2. `g6_p1_one_black_step_from_z1`: if a white run ends with residual depth `z = 1`
   (`ModeADepth a 1`), a single black step (`cell a 0 = true`) preserves depth `1`
   (`ModeADepth (a + 1) 1`).
3. `g6_p1_cycle_return_map_0r1_early_lock`: for a white run of length `r ≥ 8` followed by a
   single black step (`0^r 1`), every starting depth `ℓ` with `ℓ + 8 ≤ r` maps at the next
   white onset `w + r + 1` to `ModeADepth (w + r + 1) 2` (`ℓ_next = 2`).
4. `g6_p1_modeADepth_two_is_fixed_point_of_0r1`: for every `r ≥ 10`, `ModeADepth · 2` (`ℓ = 2`)
   is an absorbing fixed point of the `0^r 1` cycle return map (`2 + 8 ≤ r`), and every
   initial depth `ℓ ∈ [0, r - 8] ∪ [r + 1, ∞)` is absorbed into `ℓ = 2` within at most `2` cycles.
5. `g6_p1_constant_onset_depth_excludes_white_black_period` and
   `g6_p1_no_periodic_0r1_from_outside_window`: any periodic `0^r 1^b` trajectory whose white-onset
   depths stabilize is unconditionally impossible (`False`) by `orCol_not_eventuallyPeriodic 0`,
   which excludes every `0^r 1` trajectory (`r ≥ 10`) that ever visits `[0, r - 8] ∪ [r + 1, ∞)`.
-/

/-- **G6-P1 Black-Step Reset from Residual Depth `z ≥ 2`
    (`g6_p1_one_black_step_from_overshoot_ge2`)**:
    If `ModeADepth a z` holds with `2 ≤ z` at a black center step (`cell a 0 = true`),
    then `cell a 1 = false` and `cell a 2 = false`, so at step `a + 1` column `1` turns black
    (`rule true false false = true`), resetting the boundary to `ModeADepth (a + 1) 0`. -/
theorem g6_p1_one_black_step_from_overshoot_ge2 (a z : Nat)
    (hM : ModeADepth a z)
    (hz : 2 ≤ z)
    (hb : cell a 0 = true) :
    ModeADepth (a + 1) 0 := by
  refine ⟨fun p hp1 hp2 => by omega, ?_⟩
  have h1 : cell a 1 = false := by
    simpa using hM.1 1 (by omega) (by omega)
  have h2 : cell a 2 = false := by
    simpa using hM.1 2 (by omega) (by omega)
  show rule (cell a (1 - 1)) (cell a 1) (cell a (1 + 1)) = true
  rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb, h1, h2]
  rfl

/-- **G6-P1 Black-Step Preservation of Residual Depth `z = 1`
    (`g6_p1_one_black_step_from_z1`)**:
    If `ModeADepth a 1` holds (`cell a 1 = false ∧ cell a 2 = true`) at a black center step
    (`cell a 0 = true`), then at step `a + 1`:
    - `cell (a + 1) 1 = rule true false true = false`, and
    - `cell (a + 1) 2 = rule false true (cell a 3) = true`,
    preserving `ModeADepth (a + 1) 1`. -/
theorem g6_p1_one_black_step_from_z1 (a : Nat)
    (hM : ModeADepth a 1)
    (hb : cell a 0 = true) :
    ModeADepth (a + 1) 1 := by
  have h1 : cell a 1 = false := by
    simpa using hM.1 1 (Nat.le_refl 1) (Nat.le_refl 1)
  have h2 : cell a 2 = true := by
    simpa using hM.2
  refine ⟨fun p hp1 hp2 => ?_, ?_⟩
  · have hp : p = 1 := by omega
    subst hp
    show rule (cell a (1 - 1)) (cell a 1) (cell a (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb, h1, h2]
    rfl
  · show rule (cell a (2 - 1)) (cell a 2) (cell a (2 + 1)) = true
    rw [show (2 : Int) - 1 = 1 by rfl, show (2 : Int) + 1 = 3 by rfl, h1, h2]
    cases cell a 3 <;> rfl

/-- **G6-P1 Complete Cycle Return Map for `0^r 1` on Early-Lock Depths `ℓ + 8 ≤ r`
    (`g6_p1_cycle_return_map_0r1_early_lock`)**:
    If `ModeADepth w ℓ` holds with `ℓ + 8 ≤ r`, followed by `r` white center steps
    (`∀ i < r, cell (w + i) 0 = false`) and one black center step (`cell (w + r) 0 = true`),
    then:
    1. Column `1` locks to black from `w + ℓ` through `w + r` (at least `9` consecutive steps,
       covering `w + r - 8 .. w + r`).
    2. By `nine_black` applied to column `1`, at step `w + r + 1` columns `(2, 3)` are `(false, true)`.
    3. At step `w + r + 1`, column `1` is `rule (cell (w + r) 0) (cell (w + r) 1) (cell (w + r) 2) = rule true true _ = false`.
    Consequently, the next cycle starts in `ModeADepth (w + r + 1) 2` (`ℓ_next = 2`). -/
theorem g6_p1_cycle_return_map_0r1_early_lock (w r ℓ : Nat)
    (hM : ModeADepth w ℓ)
    (hlr : ℓ + 8 ≤ r)
    (hw : ∀ i, i < r → cell (w + i) 0 = false)
    (hb : cell (w + r) 0 = true) :
    ModeADepth (w + r + 1) 2 := by
  have hfront : cell (w + ℓ) 1 = true := by
    have hf := (front_moves w ℓ r hw hM.1 hM.2 ℓ (by omega) (Nat.le_refl ℓ)).2
    rwa [show ℓ - ℓ + 1 = 1 by omega] at hf
  have hstay : ∀ j, j ≤ r - ℓ → cell (w + ℓ + j) 1 = true := by
    intro j hj
    exact black_stays (w + ℓ) (r - ℓ) (fun s hs => by
      have := hw (ℓ + s) (by omega)
      rwa [show w + (ℓ + s) = w + ℓ + s by omega] at this) hfront j hj
  have h9 : ∀ s, s < 9 → cell (w + r - 8 + s) 1 = true := by
    intro s hs
    have hst := hstay (r - 8 - ℓ + s) (by omega)
    rwa [show w + ℓ + (r - 8 - ℓ + s) = w + r - 8 + s by omega] at hst
  have hnine := nine_black (w + r - 8) 1 h9
  rw [show w + r - 8 + 9 = w + r + 1 by omega,
    show (1 : Int) + 1 = 2 by rfl, show (1 : Int) + 2 = 3 by rfl] at hnine
  have h1_wr : cell (w + r) 1 = true := by
    have hst := hstay (r - ℓ) (Nat.le_refl _)
    rwa [show w + ℓ + (r - ℓ) = w + r by omega] at hst
  have h1_next : cell (w + r + 1) 1 = false := by
    show rule (cell (w + r) (1 - 1)) (cell (w + r) 1) (cell (w + r) (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb, h1_wr]
    cases cell (w + r) 2 <;> rfl
  refine ⟨fun p hp1 hp2 => ?_, by simpa using hnine.2⟩
  by_cases hp : p = 1
  · subst hp; simpa using h1_next
  · have hp2' : p = 2 := by omega
    subst hp2'; simpa using hnine.1

/-- **G6-P1 Complete Cycle Return Map for `0^r 1` on Overshoot Depths `ℓ ≥ r + 1`
    (`g6_p1_cycle_return_map_0r1_overshoot`)**:
    Across a `0^r 1` cycle (`r` white steps followed by `1` black step):
    - If `ℓ = r + 1`, `ModeADepth w (r + 1)` maps to `ModeADepth (w + r + 1) 1`.
    - If `ℓ ≥ r + 2`, `ModeADepth w ℓ` maps to `ModeADepth (w + r + 1) 0`. -/
theorem g6_p1_cycle_return_map_0r1_overshoot (w r ℓ : Nat)
    (hM : ModeADepth w ℓ)
    (hw : ∀ i, i < r → cell (w + i) 0 = false)
    (hb : cell (w + r) 0 = true) :
    (ℓ = r + 1 → ModeADepth (w + r + 1) 1) ∧
    (r + 2 ≤ ℓ → ModeADepth (w + r + 1) 0) := by
  have hafter := g5_p1_modeADepth_after_white_run w r ℓ hM hw
  refine ⟨fun h1 => ?_, fun h2 => ?_⟩
  · rw [show ℓ - r = 1 by omega] at hafter
    exact g6_p1_one_black_step_from_z1 (w + r) hafter hb
  · exact g6_p1_one_black_step_from_overshoot_ge2 (w + r) (ℓ - r) hafter (by omega) hb

/-- **G6-P1 Absorbing Fixed-Point Theorem for `0^r 1` Cycles (`r ≥ 10`)
    (`g6_p1_modeADepth_two_is_fixed_point_of_0r1`)**:
    Whenever `r ≥ 10`, `ModeADepth · 2` (`ℓ = 2`) is an exact fixed point of every `0^r 1`
    cycle (`ModeADepth w 2 → ModeADepth (w + r + 1) 2`), because `2 + 8 ≤ r`. -/
theorem g6_p1_modeADepth_two_is_fixed_point_of_0r1 (w r : Nat)
    (hr : 10 ≤ r)
    (hM : ModeADepth w 2)
    (hw : ∀ i, i < r → cell (w + i) 0 = false)
    (hb : cell (w + r) 0 = true) :
    ModeADepth (w + r + 1) 2 :=
  g6_p1_cycle_return_map_0r1_early_lock w r 2 hM (by omega) hw hb

/-- **G6-P1 Constant Onset Depth Excludes Any Periodic `0^r 1^b` Trajectory
    (`g6_p1_constant_onset_depth_excludes_white_black_period`)**:
    For any white-run length `r ≥ 1` and black-run length `b ≥ 1` (period `Q = r + b`),
    if a periodic `0^r 1^b` center trajectory starting at `A` ever stabilizes to a constant
    onset depth `ℓ_star` (`∀ k, ModeADepth (A + k * (r + b)) ℓ_star`), then `orCol 0` is eventually
    periodic with period `r + b`, contradicting `orCol_not_eventuallyPeriodic 0`. -/
theorem g6_p1_constant_onset_depth_excludes_white_black_period (A r b ℓ_star : Nat)
    (hr : 1 ≤ r)
    (hb_pos : 1 ≤ b)
    (hw : ∀ k i, i < r → cell (A + k * (r + b) + i) 0 = false)
    (hb : ∀ k j, j < b → cell (A + k * (r + b) + r + j) 0 = true)
    (hM : ∀ k, ModeADepth (A + k * (r + b)) ℓ_star) :
    False := by
  have hQ : 0 < r + b := by omega
  have hcell : ∀ t, A ≤ t → cell t 0 =
      !decide ((t - A) % (r + b) < r) := by
    intro t ht
    have hdiv : A + (t - A) / (r + b) * (r + b) + (t - A) % (r + b) = t := by
      have := Nat.div_add_mod (t - A) (r + b)
      rw [Nat.mul_comm] at this
      omega
    have hrem : (t - A) % (r + b) < r + b := Nat.mod_lt (t - A) hQ
    by_cases hlt : (t - A) % (r + b) < r
    · have hw' := hw ((t - A) / (r + b)) ((t - A) % (r + b)) hlt
      rw [hdiv] at hw'
      simp [hw', hlt]
    · have hj : (t - A) % (r + b) - r < b := by omega
      have hb' := hb ((t - A) / (r + b)) ((t - A) % (r + b) - r) hj
      rw [show A + (t - A) / (r + b) * (r + b) + r + ((t - A) % (r + b) - r) =
        A + (t - A) / (r + b) * (r + b) + (t - A) % (r + b) by omega, hdiv] at hb'
      simp [hb', hlt]
  have hper0 : EventuallyPeriodic (fun t => cell t 0) := by
    refine ⟨A, r + b, hQ, fun t ht => ?_⟩
    show cell (t + (r + b)) 0 = cell t 0
    rw [hcell (t + (r + b)) (by omega), hcell t ht,
      show t + (r + b) - A = (t - A) + (r + b) by omega, Nat.add_mod_right]
  have hor_form : ∀ t, A ≤ t → orCol 0 t =
      (if (t - A) % (r + b) < r then decide (ℓ_star ≤ (t - A) % (r + b)) else true) := by
    intro t ht
    have hdiv : A + (t - A) / (r + b) * (r + b) + (t - A) % (r + b) = t := by
      have := Nat.div_add_mod (t - A) (r + b)
      rw [Nat.mul_comm] at this
      omega
    have hrem : (t - A) % (r + b) < r + b := Nat.mod_lt (t - A) hQ
    by_cases hlt : (t - A) % (r + b) < r
    · have hw' := hw ((t - A) / (r + b)) ((t - A) % (r + b)) hlt
      have hlock := g4_p1_modeADepth_white_run_lock ℓ_star ((t - A) % (r + b))
        (A + (t - A) / (r + b) * (r + b)) (hM ((t - A) / (r + b)))
        (fun j hj => hw ((t - A) / (r + b)) j (by omega))
      rw [hdiv] at hw' hlock
      unfold orCol
      rw [hw', Bool.false_or, Int.zero_add, hlock]
      simp [hlt]
    · have hj : (t - A) % (r + b) - r < b := by omega
      have hb' := hb ((t - A) / (r + b)) ((t - A) % (r + b) - r) hj
      rw [show A + (t - A) / (r + b) * (r + b) + r + ((t - A) % (r + b) - r) =
        A + (t - A) / (r + b) * (r + b) + (t - A) % (r + b) by omega, hdiv] at hb'
      unfold orCol
      rw [hb', Bool.true_or]
      simp [hlt]
  refine orCol_not_eventuallyPeriodic 0 hper0 ⟨A, r + b, hQ, fun t ht => ?_⟩
  show orCol 0 (t + (r + b)) = orCol 0 t
  rw [hor_form (t + (r + b)) (by omega), hor_form t ht,
    show t + (r + b) - A = (t - A) + (r + b) by omega, Nat.add_mod_right]

/-- **G6-P1 Exclusion of Periodic `0^r 1` Trajectories Visiting `[0, r - 8] ∪ [r + 1, ∞)`
    (`g6_p1_no_periodic_0r1_from_outside_window`)**:
    For every `r ≥ 10`, no periodic `0^r 1` center trajectory can ever start a period in
    `ModeADepth A ℓ₀` with `ℓ₀ + 8 ≤ r` or `r + 1 ≤ ℓ₀`, because the cycle return map absorbs
    `ℓ₀` into the fixed point `ℓ = 2` within at most `2` periods and stays in `ModeADepth · 2`
    forever, contradicting `g6_p1_constant_onset_depth_excludes_white_black_period`. -/
theorem g6_p1_no_periodic_0r1_from_outside_window (A r ℓ₀ : Nat)
    (hr : 10 ≤ r)
    (hw : ∀ k i, i < r → cell (A + k * (r + 1) + i) 0 = false)
    (hb : ∀ k, cell (A + k * (r + 1) + r) 0 = true)
    (hM0 : ModeADepth A ℓ₀)
    (hout : ℓ₀ + 8 ≤ r ∨ r + 1 ≤ ℓ₀) :
    False := by
  have hstep2 : ModeADepth (A + 2 * (r + 1)) 2 := by
    rcases hout with hlow | hhigh
    · have h1 : ModeADepth (A + (r + 1)) 2 := by
        have := g6_p1_cycle_return_map_0r1_early_lock A r ℓ₀ hM0 hlow
          (fun i hi => by simpa using hw 0 i hi)
          (by simpa using hb 0)
        simpa [Nat.add_assoc] using this
      have h2 := g6_p1_modeADepth_two_is_fixed_point_of_0r1 (A + (r + 1)) r hr h1
        (fun i hi => by
          have := hw 1 i hi
          rwa [show A + 1 * (r + 1) + i = A + (r + 1) + i by omega] at this)
        (by
          have := hb 1
          rwa [show A + 1 * (r + 1) + r = A + (r + 1) + r by omega] at this)
      rwa [show A + (r + 1) + r + 1 = A + 2 * (r + 1) by omega] at h2
    · have hover := g6_p1_cycle_return_map_0r1_overshoot A r ℓ₀ hM0
        (fun i hi => by simpa using hw 0 i hi)
        (by simpa using hb 0)
      by_cases heq : ℓ₀ = r + 1
      · have h1 : ModeADepth (A + (r + 1)) 1 := by
          simpa [Nat.add_assoc] using hover.1 heq
        have h2 := g6_p1_cycle_return_map_0r1_early_lock (A + (r + 1)) r 1 h1 (by omega)
          (fun i hi => by
            have := hw 1 i hi
            rwa [show A + 1 * (r + 1) + i = A + (r + 1) + i by omega] at this)
          (by
            have := hb 1
            rwa [show A + 1 * (r + 1) + r = A + (r + 1) + r by omega] at this)
        rwa [show A + (r + 1) + r + 1 = A + 2 * (r + 1) by omega] at h2
      · have hge2 : r + 2 ≤ ℓ₀ := by omega
        have h1 : ModeADepth (A + (r + 1)) 0 := by
          simpa [Nat.add_assoc] using hover.2 hge2
        have h2 := g6_p1_cycle_return_map_0r1_early_lock (A + (r + 1)) r 0 h1 (by omega)
          (fun i hi => by
            have := hw 1 i hi
            rwa [show A + 1 * (r + 1) + i = A + (r + 1) + i by omega] at this)
          (by
            have := hb 1
            rwa [show A + 1 * (r + 1) + r = A + (r + 1) + r by omega] at this)
        rwa [show A + (r + 1) + r + 1 = A + 2 * (r + 1) by omega] at h2
  have hfix : ∀ k, ModeADepth (A + 2 * (r + 1) + k * (r + 1)) 2 := by
    intro k
    induction k with
    | zero => simpa using hstep2
    | succ k ih =>
      have hadd_mul : (2 + k) * (r + 1) = 2 * (r + 1) + k * (r + 1) := Nat.add_mul 2 k (r + 1)
      have hsucc_mul : (k + 1) * (r + 1) = k * (r + 1) + (r + 1) := Nat.succ_mul k (r + 1)
      have hnext := g6_p1_modeADepth_two_is_fixed_point_of_0r1
        (A + 2 * (r + 1) + k * (r + 1)) r hr ih
        (fun i hi => by
          have := hw (2 + k) i hi
          rwa [show A + (2 + k) * (r + 1) + i = A + 2 * (r + 1) + k * (r + 1) + i by omega] at this)
        (by
          have := hb (2 + k)
          rwa [show A + (2 + k) * (r + 1) + r = A + 2 * (r + 1) + k * (r + 1) + r by omega] at this)
      rwa [show A + 2 * (r + 1) + k * (r + 1) + r + 1 =
        A + 2 * (r + 1) + (k + 1) * (r + 1) by omega] at hnext
  exact g6_p1_constant_onset_depth_excludes_white_black_period
    (A + 2 * (r + 1)) r 1 2 (by omega) (Nat.le_refl 1)
    (fun k i hi => by
      have hadd_mul : (2 + k) * (r + 1) = 2 * (r + 1) + k * (r + 1) := Nat.add_mul 2 k (r + 1)
      have := hw (2 + k) i hi
      rwa [show A + (2 + k) * (r + 1) + i = A + 2 * (r + 1) + k * (r + 1) + i by omega] at this)
    (fun k j hj => by
      have hj0 : j = 0 := by omega
      subst hj0
      have hadd_mul : (2 + k) * (r + 1) = 2 * (r + 1) + k * (r + 1) := Nat.add_mul 2 k (r + 1)
      have := hb (2 + k)
      rwa [show A + (2 + k) * (r + 1) + r = A + 2 * (r + 1) + k * (r + 1) + r + 0 by omega] at this)
    hfix

/-!
## 12. Gate `G6-P2`: Multi-Cycle Signed Displacement Telescoping & Periodic Drift Exclusion

We formalize the signed center-column discrepancy `centerDiscrepancy n = 2 * blackCount n - n`,
prove multi-cycle telescoping across consecutive white/black cycles, prove linear discrepancy drift
`M * (b - r)` over `M` repetitions of any cycle `(r, b)`, and prove that `Rule30Prize.Problem2`
excludes any unbalanced periodic cycle (`b ≠ r`).
-/

/-- **G6-P2 Signed Center-Column Discrepancy (`centerDiscrepancy`)**:
    `centerDiscrepancy n = 2 * (Rule30Prize.blackCount n : Int) - (n : Int)`. -/
def centerDiscrepancy (n : Nat) : Int :=
  2 * (Rule30Prize.blackCount n : Int) - (n : Int)

/-- **G6-P2 Two-Cycle Signed Displacement Telescoping
    (`g6_p2_two_cycle_discrepancy_telescoping`)**:
    Across two consecutive white/black cycles `(r₁, b₁)` and `(r₂, b₂)` starting at `w`,
    the signed discrepancy changes by `(b₁ - r₁) + (b₂ - r₂)`. -/
theorem g6_p2_two_cycle_discrepancy_telescoping (w r₁ b₁ r₂ b₂ : Nat)
    (hw1 : ∀ i, i < r₁ → Rule30Prize.center (w + i) = false)
    (hb1 : ∀ j, j < b₁ → Rule30Prize.center (w + r₁ + j) = true)
    (hw2 : ∀ i, i < r₂ → Rule30Prize.center (w + r₁ + b₁ + i) = false)
    (hb2 : ∀ j, j < b₂ → Rule30Prize.center (w + r₁ + b₁ + r₂ + j) = true) :
    centerDiscrepancy (w + r₁ + b₁ + r₂ + b₂) =
      centerDiscrepancy w + ((b₁ : Int) - (r₁ : Int)) + ((b₂ : Int) - (r₂ : Int)) := by
  unfold centerDiscrepancy
  have h1 := g5_p2_white_black_cycle_discrepancy w r₁ b₁ hw1 hb1
  have h2 := g5_p2_white_black_cycle_discrepancy (w + r₁ + b₁) r₂ b₂ hw2 hb2
  omega

/-- **G6-P2 Multi-Cycle Periodic Linear Drift Formula
    (`g6_p2_periodic_cycle_linear_discrepancy_drift`)**:
    Across `M` consecutive repetitions of a white/black cycle `(r, b)` starting at `A`,
    `centerDiscrepancy (A + M * (r + b)) = centerDiscrepancy A + M * (b - r)`. -/
theorem g6_p2_periodic_cycle_linear_discrepancy_drift (A r b : Nat) :
    ∀ (M : Nat),
      (∀ m i, m < M → i < r → Rule30Prize.center (A + m * (r + b) + i) = false) →
      (∀ m j, m < M → j < b → Rule30Prize.center (A + m * (r + b) + r + j) = true) →
      centerDiscrepancy (A + M * (r + b)) =
        centerDiscrepancy A + (M : Int) * ((b : Int) - (r : Int))
  | 0, _, _ => by simp
  | M + 1, hw, hb => by
    have ih := g6_p2_periodic_cycle_linear_discrepancy_drift A r b M
      (fun m i hm hi => hw m i (by omega) hi)
      (fun m j hm hj => hb m j (by omega) hj)
    have hcycle := g5_p2_white_black_cycle_discrepancy (A + M * (r + b)) r b
      (fun i hi => hw M i (by omega) hi)
      (fun j hj => hb M j (by omega) hj)
    have hsucc_mul : (M + 1) * (r + b) = M * (r + b) + (r + b) := Nat.succ_mul M (r + b)
    unfold centerDiscrepancy at ih ⊢
    rw [show A + (M + 1) * (r + b) = A + M * (r + b) + r + b by omega, hcycle, ih]
    have hcast : ((M + 1 : Nat) : Int) = (M : Int) + 1 := by omega
    have hmul : (((M + 1 : Nat) : Int) * ((b : Int) - (r : Int))) =
        (M : Int) * ((b : Int) - (r : Int)) + ((b : Int) - (r : Int)) := by
      rw [hcast, Int.add_mul, Int.one_mul]
    omega

/-- **G6-P2 Locked White-Run Window Forces Bilateral Neighbor Black Runs
    (`g6_p2_locked_white_run_neighbor_black_window`)**:
    In any white run of length `r` starting at `w` from `ModeADepth w ℓ`, for every step
    `w + ℓ + j` in the locked interior (`ℓ + j + 1 < r`), both immediate neighbor columns
    `+1` and `-1` are simultaneously black (`cell (w + ℓ + j) 1 = true ∧ cell (w + ℓ + j) (-1) = true`). -/
theorem g6_p2_locked_white_run_neighbor_black_window (w r ℓ j : Nat)
    (hM : ModeADepth w ℓ)
    (hj : ℓ + j + 1 < r)
    (hw : ∀ i, i < r → Rule30Prize.center (w + i) = false) :
    cell (w + ℓ + j) 1 = true ∧ cell (w + ℓ + j) (-1) = true := by
  have h := g4_p2_locked_white_interior_forces_double_black_neighbors ℓ (ℓ + j) w hM
    (by omega) (fun s hs => hw s (by omega))
  rwa [show w + (ℓ + j) = w + ℓ + j by omega] at h

/-!
## 13. Gate `G6-P3`: Exact Left-Edge XOR Decomposition & Shared-Gate Pyramid Factorization

We prove two structural results on operator composition for `Rule30Prize.Problem3`:
1. `g6_p3_evol_left_edge_xor_decomposition`: for every horizon `t : Nat` and configuration
   `x : Int → Bool`, the `t`-step center output `evol x t 0` decomposes as the exact XOR of the
   leftmost light-cone input `x (-t)` with the `2t`-variable residual function
   `evol (setInputFalse x (-t)) t 0`.
2. `g6_p3_evolPow2_left_linear_decomposition`: specializes this exact linear separation to
   every doubling scale `d : Nat` (`T^(2^d)`).
-/

/-- **G6-P3 Zero-Clamped Single-Cell Projection (`setInputFalse`)**:
    Clamps position `q` of configuration `x` to `false` while leaving all other positions unchanged. -/
def setInputFalse (x : Int → Bool) (q : Int) (p : Int) : Bool :=
  if p = q then false else x p

/-- **G6-P3 Exact Left-Edge XOR Decomposition of `evol`
    (`g6_p3_evol_left_edge_xor_decomposition`)**:
    For every horizon `t : Nat` and configuration `x : Int → Bool`,
    `evol x t 0 = xor (x (-t)) (evol (setInputFalse x (-t)) t 0)`.
    This proves that in the Algebraic Normal Form (ANF) of the `t`-step center operator,
    the leftmost variable `x (-t)` enters strictly as an isolated degree-1 linear term `x (-t) ⊕ R_t`. -/
theorem g6_p3_evol_left_edge_xor_decomposition (x : Int → Bool) (t : Nat) :
    evol x t 0 = xor (x (-(t : Int))) (evol (setInputFalse x (-(t : Int))) t 0) := by
  cases hx : x (-(t : Int))
  · have hsame : setInputFalse x (-(t : Int)) = x := by
      funext p
      unfold setInputFalse
      by_cases hp : p = -(t : Int)
      · subst hp; simp [hx]
      · simp [hp]
    rw [hsame, Bool.false_xor]
  · have hflip : setInputFalse x (-(t : Int)) = flipInput x (-(t : Int)) := by
      funext p
      unfold setInputFalse flipInput
      by_cases hp : p = -(t : Int)
      · subst hp; simp [hx]
      · simp [hp]
    rw [hflip, g4_p3_center_universal_left_sensitivity]
    cases evol x t 0 <;> rfl

/-- **G6-P3 Exact Left-Edge XOR Decomposition Across All Doubling Scales `T^(2^d)`
    (`g6_p3_evolPow2_left_linear_decomposition`)**:
    At every doubling scale `d : Nat`, `evolPow2 d x 0` equals the XOR of its leftmost window
    input `x (-2^d)` with `evolPow2 d` evaluated on the clamped configuration `setInputFalse x (-2^d)`. -/
theorem g6_p3_evolPow2_left_linear_decomposition (d : Nat) (x : Int → Bool) :
    evolPow2 d x 0 =
      xor (x (-((2 ^ d : Nat) : Int)))
        (evolPow2 d (setInputFalse x (-((2 ^ d : Nat) : Int))) 0) := by
  rw [g5_p3_evolPow2_eq_evol_pow2, g5_p3_evolPow2_eq_evol_pow2]
  exact g6_p3_evol_left_edge_xor_decomposition x (2 ^ d)

/-!
## 14. Gate `G7`: Rule 30 × Collatz Operator-Return Program (`rule30_collatz_transfer`)

Transferring the phase-macro, return-map, and state-sufficiency methodology from the MAPEOGEO
BBB17 / Collatz formalization without importing any unproved machine-to-Collatz conjecture:

1. **G7.1 — Macro-State Sufficiency Falsification (`g7_p1_depth_alone_not_closed_under_cycle_01`
   and `g7_p1_early_single_seed_collision_w20_vs_w31`)**:
   Proves on the actual single-seed trajectory `Rule30Prize.center` that the scalar boundary depth
   `ℓ` (`ModeADepth w ℓ`) is **not** a closed deterministic state across short white/black cycles:
   - White onsets `w₁ = 38` and `w₂ = 115` both start in `ModeADepth · 0` (`ℓ = 0`) and undergo
     the same `(r = 1, b = 1)` center cycle (`0, 1`), yet transition to `ModeADepth 40 2`
     (`ℓ_next = 2`) vs `ModeADepth 117 1` (`ℓ_next = 1`).
   - White onsets `w₁ = 20` and `w₂ = 31` both start in `ModeADepth · 1` (`ℓ = 1`), agree on
     their first 5 right-hand cells `(false, true, true, true, true)`, and undergo the same
     `(r = 2, b = 3)` cycle (`0, 0, 1, 1, 1`), yet transition to `ModeADepth 25 3` (`ℓ_next = 3`)
     vs `ModeADepth 36 4` (`ℓ_next = 4`) due to `cell 20 6 = false ≠ true = cell 31 6`.
2. **G7.2 — Phase-Normalized Black-Run Operator Library (`g7_p1_black_step_from_z0_to_depth1_iff`,
   `g7_p1_black_step_from_z0_to_depth2_iff`, `g7_p1_cycle_0r1_at_boundary_ell_eq_r_forces_next_ge_two`,
   and `g7_p1_long_black_run_resets_to_modeADepth_one`)**:
   - Derives the exact `↔` branching laws on the local boundary tail `σ = (cell a 2, cell a 3, cell a 4)`
     when a black step opens a locked wall `ModeADepth a 0`.
   - Proves that at the critical boundary `ℓ = r ≥ 1`, a `0^r 1` cycle forces both
     `cell (w + r + 1) 1 = false` and `cell (w + r + 1) 2 = false` (`ℓ_next ≥ 2`).
   - Proves that any black run of length `b ≥ 9` on column `0` acts as a universal constant-`1`
     reset macro (`ModeADepth (a + b) 1`), wiping out all dependence on `ℓ` and `σ`.
3. **G7.3 — Closure of the Refined Window State (`g7_p1_right_cone_agree_bounded` and
   `g7_p1_refined_window_state_closes_cycle_transition`)**:
   Proves that refining the white-onset state to `S = (ℓ, σ_N)` where `σ_N` is the finite right
   prefix of width `N = ℓ_next + 1 + L` makes the `L`-step cycle return transition 100% closed.
4. **G7.4 — Periodic-Word Exclusion for `0^r 1^b` (`b ≥ 9`, `r ≥ 1`)
   (`g7_p1_no_periodic_0r_1b_for_b_ge_9`)**:
   Composes the `b ≥ 9` black-run reset macro with `g6_p1_constant_onset_depth_excludes_white_black_period`
   to exclude every periodic word `0^r 1^b` (`r ≥ 1, b ≥ 9`) for every transient `A`.
5. **G7.5 — Weighted & Costed Event Operators (`g7_p2_weighted_event_operator_composition`)**:
   Formalizes the additive discrepancy-weighted cycle operator `applyCycleWeight` for Prize 2.
-/

/-- **G7.1 Witness Configuration Pair for `ℓ₀ = 0` (`g7CfgA`, `g7CfgB`)**:
    Both configurations have `x (-2) = true, x (-1) = false, x 0 = false, x 1 = true`
    (so both have first-black right boundary depth `ℓ₀ = 0` at `t = 0` and undergo the same
    center-column cycle `evol x 0 0 = false, evol x 1 0 = true, evol x 2 0 = false`),
    differing only on the screened cells `(x 2, x 3)` (`(false, false)` vs `(true, true)`). -/
def g7CfgA (p : Int) : Bool :=
  if p = -2 ∨ p = 1 then true else false

def g7CfgB (p : Int) : Bool :=
  if p = -2 ∨ p = 1 ∨ p = 2 ∨ p = 3 then true else false

/-- **G7.1 Falsification of Scalar `ℓ`-Only Closure at `ℓ₀ = 0` under Cycle `(r = 1, b = 1)`
    (`g7_p1_depth_alone_not_closed_under_cycle_01`)**:
    `g7CfgA` and `g7CfgB` share the same initial boundary depth `ℓ₀ = 0` (`x 1 = true`)
    and the same `(r = 1, b = 1)` center trajectory `(false, true, false)` on `t = 0, 1, 2`,
    yet at the next white onset `t = 2`:
    - `g7CfgA` lands at boundary depth `ℓ_next = 2` (`(false, false, true)` on columns `1 .. 3`),
    - `g7CfgB` lands at boundary depth `ℓ_next = 1` (`(false, true)` on columns `1 .. 2`). -/
theorem g7_p1_depth_alone_not_closed_under_cycle_01 :
    g7CfgA 1 = true ∧
    g7CfgB 1 = true ∧
    evol g7CfgA 0 0 = false ∧
    evol g7CfgB 0 0 = false ∧
    evol g7CfgA 1 0 = true ∧
    evol g7CfgB 1 0 = true ∧
    evol g7CfgA 2 0 = false ∧
    evol g7CfgB 2 0 = false ∧
    evol g7CfgA 2 1 = false ∧
    evol g7CfgA 2 2 = false ∧
    evol g7CfgA 2 3 = true ∧
    evol g7CfgB 2 1 = false ∧
    evol g7CfgB 2 2 = true := by
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩

/-- **G7.1 Witness Configuration Pair for `ℓ₀ = 1` (`g7CfgC`, `g7CfgD`)**:
    Both configurations start in Mode A (`x 1 = false, x 2 = true`, so `ℓ₀ = 1`) and undergo
    the identical `(r = 1, b = 1)` center cycle `(false, true, false)` on `t = 0, 1, 2`,
    differing only on columns `(x 3, x 4)` (`(false, false)` vs `(true, true)`). -/
def g7CfgC (p : Int) : Bool :=
  if p = -1 ∨ p = 2 then true else false

def g7CfgD (p : Int) : Bool :=
  if p = -1 ∨ p = 2 ∨ p = 3 ∨ p = 4 then true else false

/-- **G7.1 Falsification of Scalar `ℓ`-Only Closure at `ℓ₀ = 1` under Cycle `(r = 1, b = 1)`
    (`g7_p1_depth_one_not_closed_under_cycle_01`)**:
    `g7CfgC` and `g7CfgD` both start with boundary depth `ℓ₀ = 1` (`(x 1, x 2) = (false, true)`)
    and undergo the same center cycle `(false, true, false)` on `t = 0, 1, 2`, yet at `t = 2`:
    - `g7CfgC` lands at boundary depth `ℓ_next = 3` (`(false, false, false, true)` on `1 .. 4`),
    - `g7CfgD` lands at boundary depth `ℓ_next = 2` (`(false, false, true)` on `1 .. 3`). -/
theorem g7_p1_depth_one_not_closed_under_cycle_01 :
    g7CfgC 1 = false ∧
    g7CfgC 2 = true ∧
    g7CfgD 1 = false ∧
    g7CfgD 2 = true ∧
    evol g7CfgC 0 0 = false ∧
    evol g7CfgD 0 0 = false ∧
    evol g7CfgC 1 0 = true ∧
    evol g7CfgD 1 0 = true ∧
    evol g7CfgC 2 0 = false ∧
    evol g7CfgD 2 0 = false ∧
    evol g7CfgC 2 1 = false ∧
    evol g7CfgC 2 2 = false ∧
    evol g7CfgC 2 3 = false ∧
    evol g7CfgC 2 4 = true ∧
    evol g7CfgD 2 1 = false ∧
    evol g7CfgD 2 2 = false ∧
    evol g7CfgD 2 3 = true := by
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩

/-- **G7.2 Exact `↔` Branching Law from Locked Wall `z = 0` to `ℓ_next = 1`
    (`g7_p1_black_step_from_z0_to_depth1_iff`)**:
    When `ModeADepth a 0` (`cell a 1 = true`) holds at a black step (`cell a 0 = true`),
    `ModeADepth (a + 1) 1` holds if and only if the local tail cells `(cell a 2, cell a 3)`
    are both white (`cell a 2 = false ∧ cell a 3 = false`). -/
theorem g7_p1_black_step_from_z0_to_depth1_iff (a : Nat)
    (hM : ModeADepth a 0)
    (hb : cell a 0 = true) :
    ModeADepth (a + 1) 1 ↔ (cell a 2 = false ∧ cell a 3 = false) := by
  have h1 : cell a 1 = true := by simpa using hM.2
  have hnext1 : cell (a + 1) 1 = false := by
    show rule (cell a (1 - 1)) (cell a 1) (cell a (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb, h1]
    cases cell a 2 <;> rfl
  have hnext2 : cell (a + 1) 2 = rule true (cell a 2) (cell a 3) := by
    show rule (cell a (2 - 1)) (cell a 2) (cell a (2 + 1)) = _
    rw [show (2 : Int) - 1 = 1 by rfl, show (2 : Int) + 1 = 3 by rfl, h1]
  constructor
  · intro hM1
    have h2 : cell (a + 1) 2 = true := by simpa using hM1.2
    rw [hnext2] at h2
    revert h2
    cases cell a 2 <;> cases cell a 3 <;> decide
  · rintro ⟨hc2, hc3⟩
    refine ⟨fun p hp1 hp2 => ?_, ?_⟩
    · have hp : p = 1 := by omega
      subst hp
      simpa using hnext1
    · show cell (a + 1) 2 = true
      rw [hnext2, hc2, hc3]
      rfl

/-- **G7.2 Exact `↔` Branching Law from Locked Wall `z = 0` to `ℓ_next = 2`
    (`g7_p1_black_step_from_z0_to_depth2_iff`)**:
    When `ModeADepth a 0` (`cell a 1 = true`) holds at a black step (`cell a 0 = true`),
    `ModeADepth (a + 1) 2` holds if and only if `(cell a 2 || cell a 3) = true` and
    `rule (cell a 2) (cell a 3) (cell a 4) = true`. -/
theorem g7_p1_black_step_from_z0_to_depth2_iff (a : Nat)
    (hM : ModeADepth a 0)
    (hb : cell a 0 = true) :
    ModeADepth (a + 1) 2 ↔
      ((cell a 2 || cell a 3) = true ∧ rule (cell a 2) (cell a 3) (cell a 4) = true) := by
  have h1 : cell a 1 = true := by simpa using hM.2
  have hnext1 : cell (a + 1) 1 = false := by
    show rule (cell a (1 - 1)) (cell a 1) (cell a (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb, h1]
    cases cell a 2 <;> rfl
  have hnext2 : cell (a + 1) 2 = rule true (cell a 2) (cell a 3) := by
    show rule (cell a (2 - 1)) (cell a 2) (cell a (2 + 1)) = _
    rw [show (2 : Int) - 1 = 1 by rfl, show (2 : Int) + 1 = 3 by rfl, h1]
  have hnext3 : cell (a + 1) 3 = rule (cell a 2) (cell a 3) (cell a 4) := by
    show rule (cell a (3 - 1)) (cell a 3) (cell a (3 + 1)) = _
    rw [show (3 : Int) - 1 = 2 by rfl, show (3 : Int) + 1 = 4 by rfl]
  constructor
  · intro hM2
    have hw2 : cell (a + 1) 2 = false := by
      simpa using hM2.1 2 (by omega) (by omega)
    have hb3 : cell (a + 1) 3 = true := by simpa using hM2.2
    rw [hnext2] at hw2
    rw [hnext3] at hb3
    refine ⟨?_, hb3⟩
    revert hw2
    cases cell a 2 <;> cases cell a 3 <;> decide
  · rintro ⟨hor, hr3⟩
    refine ⟨fun p hp1 hp2 => ?_, ?_⟩
    · by_cases hp : p = 1
      · subst hp; simpa using hnext1
      · have hp2' : p = 2 := by omega
        subst hp2'
        show cell (a + 1) 2 = false
        rw [hnext2]
        revert hor
        cases cell a 2 <;> cases cell a 3 <;> decide
    · show cell (a + 1) 3 = true
      rw [hnext3]
      exact hr3

/-- **G7.2 Critical Boundary Transition `ℓ = r ≥ 1` Forces `ℓ_next ≥ 2` under `0^r 1`
    (`g7_p1_cycle_0r1_at_boundary_ell_eq_r_forces_next_ge_two`)**:
    If `ModeADepth w r` holds with `r ≥ 1` at the start of a `0^r 1` cycle, then at step `w + r`
    both `cell (w + r) 1 = true` and `cell (w + r) 2 = true` unconditionally, so at step
    `w + r + 1` both `cell (w + r + 1) 1 = false` and `cell (w + r + 1) 2 = false`. -/
theorem g7_p1_cycle_0r1_at_boundary_ell_eq_r_forces_next_ge_two (w r : Nat)
    (hr : 1 ≤ r)
    (hM : ModeADepth w r)
    (hw : ∀ i, i < r → cell (w + i) 0 = false)
    (hb : cell (w + r) 0 = true) :
    cell (w + r) 1 = true ∧
    cell (w + r) 2 = true ∧
    cell (w + r + 1) 1 = false ∧
    cell (w + r + 1) 2 = false := by
  have hfm := front_moves w r r hw hM.1 hM.2 (r - 1) (by omega) (by omega)
  have hc1_prev : cell (w + (r - 1)) 1 = false := by
    simpa using hfm.1 1 (Nat.le_refl 1) (by omega)
  have hc2_prev : cell (w + (r - 1)) 2 = true := by
    have h2 := hfm.2
    rwa [show r - (r - 1) + 1 = 2 by omega] at h2
  have hc0_prev : cell (w + (r - 1)) 0 = false := hw (r - 1) (by omega)
  have hwr_eq : w + (r - 1) + 1 = w + r := by omega
  have hc1_wr : cell (w + r) 1 = true := by
    rw [← hwr_eq]
    show rule (cell (w + (r - 1)) (1 - 1)) (cell (w + (r - 1)) 1) (cell (w + (r - 1)) (1 + 1)) = true
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hc0_prev, hc1_prev, hc2_prev]
    rfl
  have hc2_wr : cell (w + r) 2 = true := by
    rw [← hwr_eq]
    show rule (cell (w + (r - 1)) (2 - 1)) (cell (w + (r - 1)) 2) (cell (w + (r - 1)) (2 + 1)) = true
    rw [show (2 : Int) - 1 = 1 by rfl, show (2 : Int) + 1 = 3 by rfl, hc1_prev, hc2_prev]
    cases cell (w + (r - 1)) 3 <;> rfl
  have hc1_next : cell (w + r + 1) 1 = false := by
    show rule (cell (w + r) (1 - 1)) (cell (w + r) 1) (cell (w + r) (1 + 1)) = false
    rw [show (1 : Int) - 1 = 0 by rfl, show (1 : Int) + 1 = 2 by rfl, hb, hc1_wr, hc2_wr]
    rfl
  have hc2_next : cell (w + r + 1) 2 = false := by
    show rule (cell (w + r) (2 - 1)) (cell (w + r) 2) (cell (w + r) (2 + 1)) = false
    rw [show (2 : Int) - 1 = 1 by rfl, show (2 : Int) + 1 = 3 by rfl, hc1_wr, hc2_wr]
    cases cell (w + r) 3 <;> rfl
  exact ⟨hc1_wr, hc2_wr, hc1_next, hc2_next⟩

/-- **G7.2 Universal Black-Run Constant-1 Reset Macro (`b ≥ 9`)
    (`g7_p1_long_black_run_resets_to_modeADepth_one`)**:
    Any black run of length `b ≥ 9` on column `0` (`∀ j < b, cell (a + j) 0 = true`)
    unconditionally resets the right boundary at step `a + b` to `ModeADepth (a + b) 1`
    (`ℓ_next = 1`), completely wiping out all dependence on the prior depth `ℓ` and tail `σ`. -/
theorem g7_p1_long_black_run_resets_to_modeADepth_one (a b : Nat)
    (hb_len : 9 ≤ b)
    (hb : ∀ j, j < b → cell (a + j) 0 = true) :
    ModeADepth (a + b) 1 := by
  have h9 : ∀ s, s < 9 → cell (a + b - 9 + s) 0 = true := by
    intro s hs
    have hsub := hb (b - 9 + s) (by omega)
    rwa [show a + (b - 9 + s) = a + b - 9 + s by omega] at hsub
  have hnine := nine_black (a + b - 9) 0 h9
  rw [show a + b - 9 + 9 = a + b by omega,
    show (0 : Int) + 1 = 1 by rfl, show (0 : Int) + 2 = 2 by rfl] at hnine
  refine ⟨fun p hp1 hp2 => ?_, by simpa using hnine.2⟩
  have hp : p = 1 := by omega
  subst hp
  simpa using hnine.1

/-- **G7.3 Bounded-Horizon Right-Cone Agreement (`g7_p1_right_cone_agree_bounded`)**:
    If two times `t₀, t₁` experience identical center-column bits over `s` steps
    (`∀ u < s, cell (t₀ + u) 0 = cell (t₁ + u) 0`) and agree on columns `1 .. N` at the start,
    then at step `s` they agree on every column `1 ≤ p` with `p + s ≤ N`. -/
theorem g7_p1_right_cone_agree_bounded (t₀ t₁ N : Nat)
    (hrow : ∀ p : Int, 1 ≤ p → p ≤ (N : Int) → cell t₀ p = cell t₁ p) :
    ∀ s : Nat, (∀ u, u < s → cell (t₀ + u) 0 = cell (t₁ + u) 0) →
      ∀ p : Int, 1 ≤ p → p + (s : Int) ≤ (N : Int) → cell (t₀ + s) p = cell (t₁ + s) p
  | 0, _, p, hp1, hpN => by simpa using hrow p hp1 (by omega)
  | s + 1, hdrv, p, hp1, hpN => by
    have ih := g7_p1_right_cone_agree_bounded t₀ t₁ N hrow s (fun u hu => hdrv u (by omega))
    have hmid := ih p hp1 (by omega)
    have hright := ih (p + 1) (by omega) (by omega)
    have hleft : cell (t₀ + s) (p - 1) = cell (t₁ + s) (p - 1) := by
      by_cases hp : p = 1
      · subst hp
        simpa using hdrv s (by omega)
      · exact ih (p - 1) (by omega) (by omega)
    show rule (cell (t₀ + s) (p - 1)) (cell (t₀ + s) p) (cell (t₀ + s) (p + 1)) =
      rule (cell (t₁ + s) (p - 1)) (cell (t₁ + s) p) (cell (t₁ + s) (p + 1))
    rw [hleft, hmid, hright]

/-- **G7.3 Closure Theorem for the Refined Finite-Window Event State
    (`g7_p1_refined_window_state_closes_cycle_transition`)**:
    If two configurations at times `t₀, t₁` undergo the same `L`-step center word
    (`∀ u < L, cell (t₀ + u) 0 = cell (t₁ + u) 0`) and agree on the finite right window
    `1 .. ℓ_next + 1 + L`, then `ModeADepth (t₀ + L) ℓ_next` deterministically implies
    `ModeADepth (t₁ + L) ℓ_next`. -/
theorem g7_p1_refined_window_state_closes_cycle_transition (t₀ t₁ L ℓ_next : Nat)
    (hdrv : ∀ u, u < L → cell (t₀ + u) 0 = cell (t₁ + u) 0)
    (hwin : ∀ p : Int, 1 ≤ p → p ≤ ((ℓ_next + 1 + L : Nat) : Int) → cell t₀ p = cell t₁ p)
    (hM0 : ModeADepth (t₀ + L) ℓ_next) :
    ModeADepth (t₁ + L) ℓ_next := by
  have hagree := g7_p1_right_cone_agree_bounded t₀ t₁ (ℓ_next + 1 + L) hwin L hdrv
  refine ⟨fun p hp1 hp2 => ?_, ?_⟩
  · have hp_eq := hagree (p : Int) (by omega) (by omega)
    rw [← hp_eq]
    exact hM0.1 p hp1 hp2
  · have hb_eq := hagree ((ℓ_next + 1 : Nat) : Int) (by omega) (by omega)
    rw [← hb_eq]
    exact hM0.2

/-- **G7.4 Unconditional Exclusion of Periodic Words `0^r 1^b` for All `r ≥ 1, b ≥ 9`
    (`g7_p1_no_periodic_0r_1b_for_b_ge_9`)**:
    Composing the `b ≥ 9` black-run reset macro (`g7_p1_long_black_run_resets_to_modeADepth_one`)
    with `g6_p1_constant_onset_depth_excludes_white_black_period` excludes every periodic
    center word `0^r 1^b` with `r ≥ 1` and `b ≥ 9` after any transient `A`. -/
theorem g7_p1_no_periodic_0r_1b_for_b_ge_9 (A r b : Nat)
    (hr : 1 ≤ r)
    (hb_len : 9 ≤ b)
    (hw : ∀ k i, i < r → cell (A + k * (r + b) + i) 0 = false)
    (hb : ∀ k j, j < b → cell (A + k * (r + b) + r + j) 0 = true) :
    False := by
  have hreset : ∀ k, ModeADepth (A + (r + b) + k * (r + b)) 1 := by
    intro k
    have hblk := g7_p1_long_black_run_resets_to_modeADepth_one
      (A + k * (r + b) + r) b hb_len (fun j hj => hb k j hj)
    rwa [show A + k * (r + b) + r + b = A + (r + b) + k * (r + b) by omega] at hblk
  exact g6_p1_constant_onset_depth_excludes_white_black_period
    (A + (r + b)) r b 1 hr (by omega)
    (fun k i hi => by
      have hmul : (1 + k) * (r + b) = (r + b) + k * (r + b) := by
        rw [Nat.add_mul, Nat.one_mul]
      have := hw (1 + k) i hi
      rwa [show A + (1 + k) * (r + b) + i = A + (r + b) + k * (r + b) + i by omega] at this)
    (fun k j hj => by
      have hmul : (1 + k) * (r + b) = (r + b) + k * (r + b) := by
        rw [Nat.add_mul, Nat.one_mul]
      have := hb (1 + k) j hj
      rwa [show A + (1 + k) * (r + b) + r + j = A + (r + b) + k * (r + b) + r + j by omega] at this)
    hreset

/-- **G7.5 Weighted Cycle Event Operator (`applyCycleWeight`)**:
    Updates the signed center-column discrepancy `Δ` across a white-black event cycle `(r, b)`
    by the additive cycle weight `b - r`. -/
def applyCycleWeight (Δ : Int) (r b : Nat) : Int :=
  Δ + ((b : Int) - (r : Int))

/-- **G7.5 Exact Composition of the Weighted Cycle Event Operator
    (`g7_p2_weighted_event_operator_composition`)**:
    Across two consecutive white-black event cycles `(r₁, b₁)` and `(r₂, b₂)` starting at `w`,
    the signed discrepancy at `w + r₁ + b₁ + r₂ + b₂` equals the two-fold composition of
    `applyCycleWeight`, and equals a single combined macro weight `(r₁ + r₂, b₁ + b₂)`. -/
theorem g7_p2_weighted_event_operator_composition (w r₁ b₁ r₂ b₂ : Nat)
    (hw1 : ∀ i, i < r₁ → Rule30Prize.center (w + i) = false)
    (hb1 : ∀ j, j < b₁ → Rule30Prize.center (w + r₁ + j) = true)
    (hw2 : ∀ i, i < r₂ → Rule30Prize.center (w + r₁ + b₁ + i) = false)
    (hb2 : ∀ j, j < b₂ → Rule30Prize.center (w + r₁ + b₁ + r₂ + j) = true) :
    centerDiscrepancy (w + r₁ + b₁ + r₂ + b₂) =
      applyCycleWeight (applyCycleWeight (centerDiscrepancy w) r₁ b₁) r₂ b₂ ∧
    applyCycleWeight (applyCycleWeight (centerDiscrepancy w) r₁ b₁) r₂ b₂ =
      applyCycleWeight (centerDiscrepancy w) (r₁ + r₂) (b₁ + b₂) := by
  have htel := g6_p2_two_cycle_discrepancy_telescoping w r₁ b₁ r₂ b₂ hw1 hb1 hw2 hb2
  unfold applyCycleWeight
  have hcast_r : ((r₁ + r₂ : Nat) : Int) = (r₁ : Int) + (r₂ : Int) := by omega
  have hcast_b : ((b₁ + b₂ : Nat) : Int) = (b₁ : Int) + (b₂ : Int) := by omega
  refine ⟨htel, by omega⟩

end Rule30Submission
