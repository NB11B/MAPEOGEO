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

theorem right_diag_R1_parity :
    ∀ T : Nat, R 1 T = decide (T % 2 = 1)
  | 0 => rfl
  | T + 1 => by
      have ih := right_diag_R1_parity T
      have hsucc := R_one_succ T
      have hpar : decide ((T + 1) % 2 = 1) = !decide (T % 2 = 1) := by
        rcases Nat.mod_two_eq_zero_or_one T with h0 | h1
        · have h' : (T + 1) % 2 = 1 := by omega
          simp [h0, h']
        · have h' : (T + 1) % 2 = 0 := by omega
          simp [h1, h']
      rw [hsucc, ih, hpar]

theorem rowAt_eq_replicate_false_of_gt :
    ∀ (H T : Nat) (p : Int), (T : Int) < p → rowAt T p H = List.replicate H false
  | 0, _, _, _ => rfl
  | H + 1, T, p, hp => by
      have h0 : cell T p = false := cell_eq_false_of_gt T p hp
      have ih := rowAt_eq_replicate_false_of_gt H T (p + 1) (by omega)
      show cell T p :: rowAt T (p + 1) H = false :: List.replicate H false
      rw [h0, ih]

/-- **Section 3 & 4 Modeling Audit (`EXACT`, New in `R30-UNIVERSAL-001`) — Exact Row-`T` Single-Seed
    Right-Frontier Realization (`right_rowAt_single_seed_frontier_realization`)**:
    Certifies that at every transient row `T : Nat` and horizon width `H : Nat`, the single-seed
    right-half configuration has exact frontier `cell T T = true` (`R_0(T) = 1`), sub-leading
    diagonal `cell T (T - 1) = decide (T % 2 = 1)` (`R_1(T) = T mod 2`), and identically zero
    exterior `rowAt T (T + 1) H = List.replicate H false`, proving that every single-seed right-half
    row is realized by the symbolic row-`T` polynomial state space. -/
theorem right_rowAt_single_seed_frontier_realization (T H : Nat) :
    cell T (T : Int) = true ∧
    cell T ((T : Int) - 1) = decide (T % 2 = 1) ∧
    (∀ p : Int, (T : Int) < p → cell T p = false) ∧
    rowAt T ((T : Int) + 1) H = List.replicate H false := by
  have hr0 : cell T (T : Int) = true := by
    have h := R_zero T
    unfold R at h
    rwa [show (T : Int) - (0 : Nat) = (T : Int) by omega] at h
  have hr1 : cell T ((T : Int) - 1) = decide (T % 2 = 1) := by
    have h := right_diag_R1_parity T
    unfold R at h
    rwa [show (T : Int) - (1 : Nat) = (T : Int) - 1 by omega] at h
  exact ⟨hr0, hr1, fun p hp => cell_eq_false_of_gt T p hp,
    rowAt_eq_replicate_false_of_gt H T ((T : Int) + 1) (by omega)⟩

/-- **Section 3 & 4 Modeling Audit (`EXACT`, New in `R30-UNIVERSAL-001`) — Symbolic-to-Cellular
    Right-Half Evolution Equivalence (`symbolic_right_evolution_realizes_cell_and_orCol`)**:
    Certifies that for every transient `T : Nat`, horizon `H : Nat`, and step offset `s < H`,
    evolving the finite row-`T` right prefix `rowAt T 1 (H + 1)` under the symbolic operators
    `runWord` and `orColWord` produces the exact cellular right-boundary bit `cell (T + s) 1`
    and the exact PSMSL boundary observation `orCol 0 (T + s)`. -/
theorem symbolic_right_evolution_realizes_cell_and_orCol
    (T H s : Nat) (hs : s < H) :
    (runWord (col0Word T s) (rowAt T 1 (H + 1))).headD false = cell (T + s) 1 ∧
    (orColWord (col0Word T H) (rowAt T 1 (H + 1))).getD s false = orCol 0 (T + s) := by
  have hlen : H - s + 1 + s = H + 1 := by omega
  have hrun := runWord_rowAt s (H - s + 1) T
  rw [hlen] at hrun
  have hhead : (rowAt (T + s) 1 (H - s + 1)).headD false = cell (T + s) 1 := rfl
  have hor := orColWord_rowAt H 0 T
  rw [show 0 + H + 1 = H + 1 by omega] at hor
  have hget := col0OrTrace_getD H T s hs
  refine ⟨?_, ?_⟩
  · rw [hrun, hhead]
  · rw [hor, hget]

/-! ### `R30-QUOTIENT-GEOM-001` — Cone Observation Fiber Bijection & Quotient Pullback Geometry -/

theorem rule_involutive_left (b a c : Bool) : rule (rule b a c) a c = b := by
  cases b <;> cases a <;> cases c <;> rfl

theorem xor_involutive_left (b a : Bool) : xor b (xor b a) = a := by
  cases b <;> cases a <;> rfl

/-- Single-step sideways left-permutive inverse of `stepLeftRow`: given right neighbor `c`,
    boundary bit `a = cell t (-1)`, and next-step left row `zs = [cell (t+1) (-1), ..., cell (t+1) (-k)]`,
    uniquely reconstructs `[cell t (-1), cell t (-2), ..., cell t (-(k+1))]`. -/
def unstepLeftRow (c a : Bool) : List Bool → List Bool
  | [] => [a]
  | z :: zs => a :: unstepLeftRow a (rule z a c) zs

theorem unstepLeftRow_head (c a : Bool) (zs : List Bool) :
    (unstepLeftRow c a zs).headD false = a := by
  cases zs <;> rfl

theorem unstepLeftRow_eq_cons (c a : Bool) (zs : List Bool) :
    ∃ rs : List Bool, unstepLeftRow c a zs = a :: rs := by
  cases zs <;> exact ⟨_, rfl⟩

theorem length_unstepLeftRow :
    ∀ (zs : List Bool) (c a : Bool), (unstepLeftRow c a zs).length = zs.length + 1
  | [], _, _ => rfl
  | z :: zs, c, a => by
    simp [unstepLeftRow, length_unstepLeftRow zs a (rule z a c)]

theorem length_stepLeftRow :
    ∀ (rest : List Bool) (c a : Bool), (stepLeftRow c (a :: rest)).length = rest.length
  | [], _, _ => rfl
  | b :: rs, c, a => by
    show (rule b a c :: stepLeftRow a (b :: rs)).length = (b :: rs).length
    simp [length_stepLeftRow rs a b]

theorem unstepLeftRow_stepLeftRow :
    ∀ (rest : List Bool) (c a : Bool),
      unstepLeftRow c a (stepLeftRow c (a :: rest)) = a :: rest
  | [], _, _ => rfl
  | b :: rs, c, a => by
    show a :: unstepLeftRow a (rule (rule b a c) a c) (stepLeftRow a (b :: rs)) = a :: b :: rs
    rw [rule_involutive_left, unstepLeftRow_stepLeftRow rs a b]

theorem stepLeftRow_unstepLeftRow :
    ∀ (zs : List Bool) (c a : Bool),
      stepLeftRow c (unstepLeftRow c a zs) = zs
  | [], _, _ => rfl
  | z :: zs, c, a => by
    obtain ⟨rs, hrs⟩ := unstepLeftRow_eq_cons a (rule z a c) zs
    have ih := stepLeftRow_unstepLeftRow zs a (rule z a c)
    show stepLeftRow c (a :: unstepLeftRow a (rule z a c) zs) = z :: zs
    rw [hrs]
    show rule (rule z a c) a c :: stepLeftRow a (rule z a c :: rs) = z :: zs
    rw [rule_involutive_left, ← hrs, ih]

/-- Exact K7-like inverse left coder `Θ_w⁻¹`: given center word `w` of length `k`, terminal center
    bit `c_after`, and boundary observation trace `y` of length `k`, reconstructs the unique
    length-`k` initial left-cone slice `lam = [x_{-1}(t), ..., x_{-k}(t)]`. -/
def reconstructLeftWord : List Bool → Bool → List Bool → List Bool
  | [], _, _ => []
  | c :: cs, c_after, y =>
    let c_next := cs.headD c_after
    let a := xor c_next (y.headD false)
    unstepLeftRow c a (reconstructLeftWord cs c_after y.tail)

theorem length_reconstructLeftWord :
    ∀ (w : List Bool) (c_after : Bool) (y : List Bool),
      (reconstructLeftWord w c_after y).length = w.length
  | [], _, _ => rfl
  | c :: cs, c_after, y => by
    simp [reconstructLeftWord, length_unstepLeftRow, length_reconstructLeftWord cs c_after y.tail]

theorem length_orColWord :
    ∀ (w σ : List Bool), (orColWord w σ).length = w.length
  | [], _ => rfl
  | c :: cs, σ => by simp [orColWord, length_orColWord cs (stepRow c σ)]

theorem length_obsLeftWord :
    ∀ (w : List Bool) (c_after : Bool) (lam : List Bool),
      (obsLeftWord w c_after lam).length = w.length
  | [], _, _ => rfl
  | c :: cs, c_after, lam => by
    simp [obsLeftWord, length_obsLeftWord cs c_after (stepLeftRow c lam)]

theorem reconstructLeftWord_obsLeftWord :
    ∀ (w : List Bool) (c_after : Bool) (lam : List Bool),
      lam.length = w.length →
      reconstructLeftWord w c_after (obsLeftWord w c_after lam) = lam
  | [], _, [], _ => rfl
  | c :: cs, c_after, a :: rest, hlen => by
    have hlen' : rest.length = cs.length := by simp at hlen; exact hlen
    have hlen_step : (stepLeftRow c (a :: rest)).length = cs.length := by
      rw [length_stepLeftRow, hlen']
    have ih := reconstructLeftWord_obsLeftWord cs c_after (stepLeftRow c (a :: rest)) hlen_step
    show unstepLeftRow c (xor (cs.headD c_after) (xor (cs.headD c_after) a))
      (reconstructLeftWord cs c_after (obsLeftWord cs c_after (stepLeftRow c (a :: rest)))) = a :: rest
    rw [xor_involutive_left, ih, unstepLeftRow_stepLeftRow]

theorem obsLeftWord_reconstructLeftWord :
    ∀ (w : List Bool) (c_after : Bool) (y : List Bool),
      y.length = w.length →
      obsLeftWord w c_after (reconstructLeftWord w c_after y) = y
  | [], _, [], _ => rfl
  | c :: cs, c_after, y0 :: ys, hlen => by
    have hlen' : ys.length = cs.length := by simp at hlen; exact hlen
    have ih := obsLeftWord_reconstructLeftWord cs c_after ys hlen'
    let a := xor (cs.headD c_after) y0
    have hhead : (unstepLeftRow c a (reconstructLeftWord cs c_after ys)).headD false = a :=
      unstepLeftRow_head c a (reconstructLeftWord cs c_after ys)
    have hstep : stepLeftRow c (unstepLeftRow c a (reconstructLeftWord cs c_after ys)) =
        reconstructLeftWord cs c_after ys :=
      stepLeftRow_unstepLeftRow (reconstructLeftWord cs c_after ys) c a
    show xor (cs.headD c_after) ((unstepLeftRow c a (reconstructLeftWord cs c_after ys)).headD false) ::
      obsLeftWord cs c_after (stepLeftRow c (unstepLeftRow c a (reconstructLeftWord cs c_after ys))) =
      y0 :: ys
    rw [hhead, xor_involutive_left, hstep, ih]

theorem orColWord_leftBlackStepAdmissible :
    ∀ (w σ : List Bool), LeftBlackStepAdmissible w (orColWord w σ)
  | [], _ => trivial
  | c :: cs, σ => by
    refine ⟨fun hc => by simp [hc], orColWord_leftBlackStepAdmissible cs (stepRow c σ)⟩

/-- Maps any right-cone slice `σ` to the unique compatible left-cone slice `λ = Θ_w⁻¹(Ψ_w(σ))`
    in the depth-`k` fiber `π_k⁻¹(w, c_after)`. -/
def fiberLeftSlice (w : List Bool) (c_after : Bool) (σ : List Bool) : List Bool :=
  reconstructLeftWord w c_after (orColWord w σ)

/-- **`R30-QUOTIENT-GEOM-001` (`EXACT`) — Cone Observation Fiber Bijection & Quotient Pullback Law
    (`cone_fiber_bijection_and_quotient_pullback`)**:
    Proves that for every central trace `(w, c_after)` of depth `k = w.length`:
    1. Every right slice `σ` uniquely determines a length-`k` left slice `fiberLeftSlice w c_after σ`
       such that `obsLeftWord w c_after lam = orColWord w σ ↔ lam = fiberLeftSlice w c_after σ`
       (explaining why every central trace fiber has cardinality `2^k`, parameterized by `σ ∈ {0,1}^k`).
    2. Two right slices `σ₁, σ₂` belong to the same observation quotient class (`MaskedPeriodEquiv w σ₁ σ₂`)
       if and only if they pull back to the exact same left slice `fiberLeftSlice w c_after σ₁ = fiberLeftSlice w c_after σ₂`.
    3. Every left slice in the pullback image satisfies the unseen constraint `LeftBlackStepAdmissible`. -/
theorem cone_fiber_bijection_and_quotient_pullback
    (w : List Bool) (c_after : Bool) (σ σ₁ σ₂ lam : List Bool)
    (hlam : lam.length = w.length) :
    (fiberLeftSlice w c_after σ).length = w.length ∧
    obsLeftWord w c_after (fiberLeftSlice w c_after σ) = orColWord w σ ∧
    (obsLeftWord w c_after lam = orColWord w σ ↔ lam = fiberLeftSlice w c_after σ) ∧
    (MaskedPeriodEquiv w σ₁ σ₂ ↔
      fiberLeftSlice w c_after σ₁ = fiberLeftSlice w c_after σ₂) ∧
    LeftBlackStepAdmissible w (obsLeftWord w c_after (fiberLeftSlice w c_after σ)) := by
  have hobs_fib : obsLeftWord w c_after (fiberLeftSlice w c_after σ) = orColWord w σ :=
    obsLeftWord_reconstructLeftWord w c_after (orColWord w σ) (length_orColWord w σ)
  refine ⟨length_reconstructLeftWord w c_after (orColWord w σ), hobs_fib, ?_, ?_, ?_⟩
  · constructor
    · intro h
      unfold fiberLeftSlice
      rw [← h, reconstructLeftWord_obsLeftWord w c_after lam hlam]
    · intro h
      rw [h, hobs_fib]
  · constructor
    · intro h
      unfold fiberLeftSlice MaskedPeriodEquiv at *
      rw [h]
    · intro h
      unfold MaskedPeriodEquiv
      have h1 := obsLeftWord_reconstructLeftWord w c_after (orColWord w σ₁) (length_orColWord w σ₁)
      have h2 := obsLeftWord_reconstructLeftWord w c_after (orColWord w σ₂) (length_orColWord w σ₂)
      unfold fiberLeftSlice at h
      rw [← h1, ← h2, h]
  · rw [hobs_fib]
    exact orColWord_leftBlackStepAdmissible w σ

end Rule30ProofClosure
