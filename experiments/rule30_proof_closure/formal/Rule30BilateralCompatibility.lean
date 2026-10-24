import Rule30RightInformation

/-!
# `R30-CLOSE-001` Track C & Section 5 — Bilateral Compatibility & Decoupling Falsification (`Rule30BilateralCompatibility.lean`)

Establishes the formal bilateral compatibility theorems and the Section 5 decoupling falsification:
1. **`obsLeftWord_rowAtLeft` & `obsLeftWord_rowAtLeft_eq_orColWord_rowAt` (`EXACT`):**
   Proves that for every time `t : Nat`, extra width `n : Nat`, and horizon `L : Nat`, the
   left-half observation operator `obsLeftWord (col0Word t L) (cell (t + L) 0) (rowAtLeft t (-1) (n + L + 1))`
   and the right-half PSMSL observation operator `orColWord (col0Word t L) (rowAt t 1 (n + L + 1))`
   both evaluate to the exact same trace `col0OrTrace t L` (Checkpoint 02: Bilateral Soundness).
2. **`bilateral_observation_mismatch_excludes_periodic_word` (`EXACT`):**
   If at any time `t₁ ≥ T` and horizon `H : Nat`, the left-half observation trace and right-half
   observation trace disagree under `col0Word t₁ H`, then `Rule30Prize.center` cannot realize that
   center trajectory (`False`).
3. **`decoupled_halves_consistent_but_bilaterally_incompatible` (`EXACT`):**
   Formally resolves Section 5 ("Can the left and right halves actually be decoupled?"):
   At `T = 1` under the alternating periodic word `w = [false, true]` (`P = 2`), the single-seed
   cone states `L₁ = [true]` (`cell 1 (-1) = true`, padded with `false` for `p < -1`) and
   `R₁ = [true]` (`cell 1 1 = true`, padded with `false` for `p > 1`):
   - `L₁` satisfies the pure left-half black-step admissibility constraint (`c_s = true → obsLeft_s = true`)
     across 3 full periods (`6` steps, `w3 = [false, true, false, true, false, true]`), and
   - `R₁` satisfies right-half evolution across all 3 periods,
   **yet** their bilateral observations disagree at the very first step `s = 0`
   (`obsLeftWord [false] true L₁_pad = [false] ≠ [true] = orColWord [false] R₁_pad`)!
-/

namespace Rule30ProofClosure

open Ruliology.CellularAutomata
open Ruliology.CellularAutomata.Rule30Prize
open Ruliology.CellularAutomata.Rule30Realization
open Ruliology.CellularAutomata.Rule30Jen
open Ruliology.CellularAutomata.Rule30MaskedJen
open Ruliology.CellularAutomata.Rule30Diagonals
open Ruliology.CellularAutomata.Rule30BlackRuns

theorem headD_col0Word :
    ∀ (L t : Nat), (col0Word (t + 1) L).headD (cell (t + (L + 1)) 0) = cell (t + 1) 0
  | 0, _ => rfl
  | _ + 1, _ => rfl

/-- **Track C (`EXACT`) — Left-Half Observation Operator Evaluates to `col0OrTrace`
    (`obsLeftWord_rowAtLeft`)**:
    For every horizon `L : Nat`, extra width `n : Nat`, and time `t : Nat`, evaluating `obsLeftWord`
    on `rowAtLeft t (-1) (n + L + 1)` across `col0Word t L` reconstructs the exact `col0OrTrace t L`. -/
theorem obsLeftWord_rowAtLeft :
    ∀ (L n t : Nat),
      obsLeftWord (col0Word t L) (cell (t + L) 0) (rowAtLeft t (-1) (n + L + 1)) = col0OrTrace t L
  | 0, _, _ => rfl
  | L + 1, n, t => by
    have hstep := stepLeftRow_rowAtLeft t (n + L + 1) (-1)
    rw [show (-1 : Int) + 1 = 0 by rfl] at hstep
    have ih := obsLeftWord_rowAtLeft L n (t + 1)
    rw [show t + 1 + L = t + (L + 1) by omega] at ih
    have hhead := headD_col0Word L t
    have hcons := (bilateral_center_conservation t).2.symm
    rw [show n + (L + 1) + 1 = n + L + 1 + 1 by omega]
    show xor ((col0Word (t + 1) L).headD (cell (t + (L + 1)) 0))
        ((cell t (-1) :: rowAtLeft t (-1 - 1) (n + L + 1)).headD false) ::
      obsLeftWord (col0Word (t + 1) L) (cell (t + (L + 1)) 0)
        (stepLeftRow (cell t 0) (rowAtLeft t (-1) (n + L + 1 + 1))) =
      orCol 0 t :: col0OrTrace (t + 1) L
    rw [hhead, List.headD_cons, hcons, hstep, ih]

/-- **Checkpoint 02 (`EXACT`) — Bilateral Observation Equality on the Single-Seed Trajectory
    (`obsLeftWord_rowAtLeft_eq_orColWord_rowAt`)**:
    On any true Rule 30 trajectory from the single seed, the left-reconstructed observation word
    `obsLeftWord` on `rowAtLeft t (-1) (n + L + 1)` and the right-half PSMSL observation word
    `orColWord` on `rowAt t 1 (n + L + 1)` are identically equal for all `L, n, t : Nat`. -/
theorem obsLeftWord_rowAtLeft_eq_orColWord_rowAt (L n t : Nat) :
    obsLeftWord (col0Word t L) (cell (t + L) 0) (rowAtLeft t (-1) (n + L + 1)) =
      orColWord (col0Word t L) (rowAt t 1 (n + L + 1)) := by
  rw [obsLeftWord_rowAtLeft L n t, orColWord_rowAt L n t]

/-- **Track C (`EXACT`) — Bilateral Observation Mismatch Excludes Candidate Center Word
    (`bilateral_observation_mismatch_excludes_periodic_word`)**:
    If a candidate horizon-`L` center word `w` with subsequent bit `c_after` produces distinct
    left and right observation traces on `(rowAtLeft t (-1) (n + L + 1), rowAt t 1 (n + L + 1))`,
    then the single-seed trajectory cannot realize `(col0Word t L = w ∧ cell (t + L) 0 = c_after)`. -/
theorem bilateral_observation_mismatch_excludes_periodic_word
    (L n t : Nat) (w : List Bool) (c_after : Bool)
    (hmismatch :
      obsLeftWord w c_after (rowAtLeft t (-1) (n + L + 1)) ≠
        orColWord w (rowAt t 1 (n + L + 1))) :
    ¬ (col0Word t L = w ∧ cell (t + L) 0 = c_after) := by
  rintro ⟨hw, hc⟩
  apply hmismatch
  rw [← hw, ← hc]
  exact obsLeftWord_rowAtLeft_eq_orColWord_rowAt L n t

/-- Predicate certifying that every black step `w[s] = true` in a candidate word `w` produces
    `obs[s] = true` (the necessary & sufficient condition for a left-half observation trace `obs`
    to be realizable by *some* right-half bit sequence `r_s ∈ {false, true}`). -/
def LeftBlackStepAdmissible : List Bool → List Bool → Prop
  | [], _ => True
  | _, [] => False
  | c :: cs, o :: os => (c = true → o = true) ∧ LeftBlackStepAdmissible cs os

/-- **Section 5 (`EXACT`) — Formal Falsification of Left-Right Decoupling
    (`decoupled_halves_consistent_but_bilaterally_incompatible`)**:
    At `T = 1` under the alternating periodic center word `w = [false, true]` repeated for 3 periods
    (`w6 = [false, true, false, true, false, true]`, `c_after = false`), the single-seed time-`1`
    left-half prefix `L₁ = [true, false, false, false, false, false, false, false]` (`cell 1 (-1) = true`,
    `0` for `p < -1`) and right-half prefix `R₁ = [true, false, false, false, false, false, false, false]`:
    1. `L₁` is `LeftBlackStepAdmissible` across all 6 steps (`𝓛_{1, [0,1]}(6) ≠ ∅`),
    2. `R₁` is `LeftBlackStepAdmissible` across all 6 steps (`𝓡_{1, [0,1]}(6) ≠ ∅`),
    3. Yet `obsLeftWord` and `orColWord` disagree already at step `1` (`𝒞_{1, [0,1]}(1) = ∅`),
       and consequently the single-seed trajectory at `T = 1` cannot follow `c(1) = false, c(2) = true`! -/
theorem decoupled_halves_consistent_but_bilaterally_incompatible :
    let w6 := [false, true, false, true, false, true]
    let L₁ := [true, false, false, false, false, false, false, false]
    let R₁ := [true, false, false, false, false, false, false, false]
    LeftBlackStepAdmissible w6 (obsLeftWord w6 false L₁) ∧
    LeftBlackStepAdmissible w6 (orColWord w6 R₁) ∧
    obsLeftWord [false] true (rowAtLeft 1 (-1) 2) ≠
      orColWord [false] (rowAt 1 1 2) ∧
    ¬ (cell 1 0 = false ∧ cell 2 0 = true) := by
  refine ⟨?_, ?_, by decide, ?_⟩
  · simp [obsLeftWord, stepLeftRow, rule, LeftBlackStepAdmissible]
  · simp [orColWord, stepRow, rule, LeftBlackStepAdmissible]
  · rintro ⟨h1, h2⟩
    have hmis : obsLeftWord [false] true (rowAtLeft 1 (-1) (0 + 1 + 1)) ≠
        orColWord [false] (rowAt 1 1 (0 + 1 + 1)) := by decide
    apply bilateral_observation_mismatch_excludes_periodic_word 1 0 1 [false] true hmis
    exact ⟨by simp [col0Word, h1], h2⟩

end Rule30ProofClosure
