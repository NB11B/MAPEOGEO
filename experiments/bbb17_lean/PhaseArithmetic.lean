import SweepMacros
import CollatzBridge

/-!
Canonical three-block tape, arithmetic identities, and certified machine
simulation for the even-Collatz (`u = 2k + 1`) macro-phase of BBB17.
No axioms or `sorry` placeholders are used.
-/
namespace BBB17

/-- The three marked blocks: left counter, active unary register,
and separated right reservoir. -/
def canonTape (j u v : Nat) : Int → Bool := fun i =>
  decide ((-1 - (j : Int) ≤ i ∧ i ≤ -2) ∨
          (0 ≤ i ∧ i < (u : Int)) ∨
          ((u : Int) + 1 ≤ i ∧ i ≤ (u : Int) + (v : Int)))

def canonConfig (j u v : Nat) : Config :=
  ⟨(0 : State), 0, canonTape j u v⟩

/-- The active Collatz integer is one larger than the unary register. -/
def decodeActive (u : Nat) : Nat := u + 1

/-- Closed-form output of the even-integer arithmetic branch (`m = 2k + 2`). -/
def evenPhase (j k v : Nat) : Nat × Nat × Nat :=
  (j, k, v + k + 1)

/-- Closed-form output of the odd-integer arithmetic branch (`m = 2k + 1`).
The reservoir uses truncated natural subtraction. -/
def oddPhase (j k v : Nat) : Nat × Nat × Nat :=
  (j, 3 * k + 1, v - (k + 1))

/-- Closed-form reset branch (`u = 0`, `m = 1`). -/
def resetPhase (j v : Nat) : Nat × Nat × Nat :=
  (j + 1, j + 1, v - (j + 1))

theorem decode_evenPhase (j k v : Nat) :
    decodeActive (evenPhase j k v).2.1 = (2 * k + 2) / 2 := by
  dsimp [decodeActive, evenPhase]
  omega

theorem decode_oddPhase (j k v : Nat) :
    decodeActive (oddPhase j k v).2.1 = (3 * (2 * k + 1) + 1) / 2 := by
  dsimp [decodeActive, oddPhase]
  omega

theorem evenPhase_matches_collatz (k : Nat) :
    decodeActive k = collatz (2 * k + 2) := by
  have hmod : (2 * k + 2) % 2 = 0 := by omega
  dsimp [collatz, decodeActive]
  rw [if_pos hmod]
  omega

theorem oddPhase_matches_accelerated_collatz (k : Nat) :
    decodeActive (3 * k + 1) = (3 * (2 * k + 1) + 1) / 2 := by
  dsimp [decodeActive]
  omega

/-- Exhaustive three-branch classification of every canonical active register `u`:
    reset (`u = 0`), even-Collatz (`u = 2 * k + 1`), or positive odd-Collatz (`u = 2 * k`, `k > 0`). -/
theorem canon_register_trichotomy (u : Nat) :
    u = 0 ∨ (∃ k : Nat, u = 2 * k + 1) ∨ (∃ k : Nat, k > 0 ∧ u = 2 * k) := by
  by_cases h0 : u = 0
  · exact Or.inl h0
  · by_cases hmod : u % 2 = 1
    · exact Or.inr (Or.inl ⟨u / 2, by omega⟩)
    · exact Or.inr (Or.inr ⟨u / 2, by omega, by omega⟩)

/-- Even-Collatz phase conserves total right-hand 1-cells (`u' + v' = (2k + 1) + v`). -/
theorem evenPhase_right_ones_conserved (j k v : Nat) :
    (evenPhase j k v).2.1 + (evenPhase j k v).2.2 = (2 * k + 1) + v := by
  dsimp [evenPhase]
  omega

/-- Odd-Collatz phase reservoir regime 1 (interior high-water mark `v ≥ k + 1`):
    total right-hand 1-cells are conserved (`u' + v' = 2k + v`). -/
theorem oddPhase_reservoir_conserved (j k v : Nat) (hv : v ≥ k + 1) :
    (oddPhase j k v).2.1 + (oddPhase j k v).2.2 = 2 * k + v := by
  dsimp [oddPhase]
  omega

/-- Odd-Collatz phase reservoir regime 2 (new high-water mark `v ≤ k + 1`):
    saturating subtraction empties the reservoir (`v' = 0`) and `u' = 3k + 1`. -/
theorem oddPhase_reservoir_saturated (j k v : Nat) (hv : v ≤ k + 1) :
    (oddPhase j k v).2.2 = 0 ∧ (oddPhase j k v).2.1 = 3 * k + 1 := by
  dsimp [oddPhase]
  omega

/-- Reset phase reservoir regime 1 (`v ≥ j + 1`): `u' + v' = v`. -/
theorem resetPhase_reservoir_conserved (j v : Nat) (hv : v ≥ j + 1) :
    (resetPhase j v).2.1 + (resetPhase j v).2.2 = v := by
  dsimp [resetPhase]
  omega

/-- Reset phase reservoir regime 2 (`v ≤ j + 1`): reservoir saturates at `0`. -/
theorem resetPhase_reservoir_saturated (j v : Nat) (hv : v ≤ j + 1) :
    (resetPhase j v).2.2 = 0 ∧ (resetPhase j v).2.1 = j + 1 := by
  dsimp [resetPhase]
  omega

/-! ### Propositional characterization lemmas for `canonTape` and `updateTape` -/

theorem Bool_eq_iff (a b : Bool) : (a = b) ↔ (a = true ↔ b = true) := by
  cases a <;> cases b <;> decide

theorem Bool_eq_false_iff (a : Bool) : (a = false) ↔ ¬(a = true) := by
  cases a <;> decide

@[simp] theorem updateTape_true_iff (t : Int → Bool) (p i : Int) :
    updateTape t p true i = true ↔ (i = p ∨ t i = true) := by
  by_cases h : i = p <;> simp [updateTape, h]

@[simp] theorem updateTape_false_iff (t : Int → Bool) (p i : Int) :
    updateTape t p false i = true ↔ (i ≠ p ∧ t i = true) := by
  by_cases h : i = p <;> simp [updateTape, h]

@[simp] theorem canonTape_true_iff (j u v : Nat) (i : Int) :
    canonTape j u v i = true ↔
      ((-1 - (j : Int) ≤ i ∧ i ≤ -2) ∨
       (0 ≤ i ∧ i < (u : Int)) ∨
       ((u : Int) + 1 ≤ i ∧ i ≤ (u : Int) + (v : Int))) := by
  unfold canonTape
  exact decide_eq_true_iff

/-! ### Certified Machine Simulation of the Even-Collatz Phase (`u = 2k + 1`) -/

/-- Intermediate tape during the `B–C–D–E` halving loop after `s` completed passes
    with `m` passes remaining: `canonTape j (s + 2*m + 1) v` with cell `s` cleared. -/
def halvingTape (j s m v : Nat) : Int → Bool :=
  updateTape (canonTape j (s + 2 * m + 1) v) (s : Int) false

@[simp] theorem halvingTape_true_iff (j s m v : Nat) (i : Int) :
    halvingTape j s m v i = true ↔
      (i ≠ (s : Int) ∧
       ((-1 - (j : Int) ≤ i ∧ i ≤ -2) ∨
        (0 ≤ i ∧ i < ((s + 2 * m + 1 : Nat) : Int)) ∨
        (((s + 2 * m + 1 : Nat) : Int) + 1 ≤ i ∧
         i ≤ ((s + 2 * m + 1 : Nat) : Int) + (v : Int)))) := by
  simp [halvingTape]

/-- First step of the even-Collatz phase: from `canonConfig j (2k + 1) v`, state `A` reads `1`
    at cell `0`, clears cell `0`, and moves right to cell `1` in state `B`. -/
theorem evenPhase_init_step (j k v : Nat) :
    step (canonConfig j (2 * k + 1) v) =
      ⟨(1 : State), ((0 : Nat) : Int) + 1, halvingTape j 0 k v⟩ := by
  have h0 : canonTape j (2 * k + 1) v 0 = true := by
    rw [canonTape_true_iff]
    omega
  have hact : action (0 : State) true = ⟨false, true, (1 : State)⟩ := by decide
  simp [canonConfig, step, h0, hact]
  funext i
  rw [Bool_eq_iff]
  simp [halvingTape_true_iff, canonTape_true_iff]

/-- Base case (`m = 0`) of the `B–C–D–E` halving loop: from state `B` at head `s + 1`
    on `halvingTape j s 0 v`, the machine executes `B(0) → C(0) → K(1^s) → K(0) → A`
    in `s + 3` steps and arrives at `canonConfig j s (v + 1)`. -/
theorem halving_loop_base (j s v : Nat) :
    iterateStep (s + 3) ⟨(1 : State), (s : Int) + 1, halvingTape j s 0 v⟩ =
      canonConfig j s (v + 1) := by
  have hsplit : s + 3 = 2 + (s + 1) := by omega
  rw [hsplit, iterateStep_add 2 (s + 1)]
  have hones0 : ∀ r : Nat, r < 0 → halvingTape j s 0 v (((s : Int) + 1) + ↑r) = true := by
    intro r hr
    omega
  have hzero : halvingTape j s 0 v (((s : Int) + 1) + ↑(0 : Nat)) = false := by
    rw [Bool_eq_false_iff, halvingTape_true_iff]
    omega
  have hprev : halvingTape j s 0 v (((s : Int) + 1) + ↑(0 : Nat) - 1) = false := by
    rw [Bool_eq_false_iff, halvingTape_true_iff]
    omega
  have hBCK := sweep_B_then_C0_to_K 0 ((s : Int) + 1) (halvingTape j s 0 v) hones0 hzero hprev
  have hheadK : (s : Int) + 1 + ↑(0 : Nat) - 2 = (s : Int) - 1 := by omega
  have htapeK : updateTape (halvingTape j s 0 v) ((s : Int) + 1 + ↑(0 : Nat)) true =
      canonTape j s (v + 1) := by
    funext i
    rw [Bool_eq_iff]
    simp only [updateTape_true_iff, halvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadK, htapeK] at hBCK
  rw [hBCK]
  have hKones : ∀ r : Nat, r < s → canonTape j s (v + 1) (((s : Int) - 1) - ↑r) = true := by
    intro r hr
    rw [canonTape_true_iff]
    omega
  have hKzero : canonTape j s (v + 1) (((s : Int) - 1) - ↑s) = false := by
    rw [Bool_eq_false_iff, canonTape_true_iff]
    omega
  have hKA := sweep_K_to_A s ((s : Int) - 1) (canonTape j s (v + 1)) hKones hKzero
  have hheadA : (s : Int) - 1 - ↑s + 1 = 0 := by omega
  rw [hheadA] at hKA
  exact hKA

/-- Single pass (`m + 1 → m`) of the `B–C–D–E` halving loop: in `4 * m + 7` steps,
    state `B` at head `s + 1` on `halvingTape j s (m + 1) v` advances to state `B`
    at head `(s + 1) + 1` on `halvingTape j (s + 1) m (v + 1)`. -/
theorem halving_loop_pass (j s m v : Nat) :
    iterateStep (4 * m + 7) ⟨(1 : State), (s : Int) + 1, halvingTape j s (m + 1) v⟩ =
      ⟨(1 : State), ((s + 1 : Nat) : Int) + 1, halvingTape j (s + 1) m (v + 1)⟩ := by
  have hsplit : 4 * m + 7 = ((2 * m + 2) + 2) + ((2 * m + 1) + 2) := by omega
  rw [hsplit, iterateStep_add ((2 * m + 2) + 2) ((2 * m + 1) + 2)]
  -- Half 1: B sweeps right over 2m + 2 ones, reads 0 at s + 2m + 3, C reads 1 at s + 2m + 2 -> D
  have hBones : ∀ r : Nat, r < 2 * m + 2 →
      halvingTape j s (m + 1) v (((s : Int) + 1) + ↑r) = true := by
    intro r hr
    rw [halvingTape_true_iff]
    omega
  have hBzero : halvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 2)) = false := by
    rw [Bool_eq_false_iff, halvingTape_true_iff]
    omega
  have hBprev : halvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 2) - 1) = true := by
    rw [halvingTape_true_iff]
    omega
  have hBCD := sweep_B_then_C1_to_D (2 * m + 2) ((s : Int) + 1)
    (halvingTape j s (m + 1) v) hBones hBzero hBprev
  let midTape : Int → Bool := updateTape (canonTape j (s + 2 * m + 2) (v + 1)) (s : Int) false
  have hheadD : (s : Int) + 1 + ↑(2 * m + 2) - 2 = (s : Int) + 2 * ↑m + 1 := by omega
  have htapeD : updateTape (updateTape (halvingTape j s (m + 1) v)
      (((s : Int) + 1) + ↑(2 * m + 2)) true) (((s : Int) + 1) + ↑(2 * m + 2) - 1) false = midTape := by
    funext i
    rw [Bool_eq_iff]
    simp only [midTape, updateTape_false_iff, updateTape_true_iff, halvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadD, htapeD] at hBCD
  rw [hBCD]
  -- Half 2: D sweeps left over 2m + 1 ones, reads 0 at s, E reads 1 at s + 1 -> B
  have hDones : ∀ r : Nat, r < 2 * m + 1 →
      midTape (((s : Int) + 2 * ↑m + 1) - ↑r) = true := by
    intro r hr
    simp only [midTape, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDzero : midTape (((s : Int) + 2 * ↑m + 1) - ↑(2 * m + 1)) = false := by
    rw [Bool_eq_false_iff]
    simp only [midTape, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDnext : midTape (((s : Int) + 2 * ↑m + 1) - ↑(2 * m + 1) + 1) = true := by
    simp only [midTape, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDEB := sweep_D_then_E1_to_B (2 * m + 1) ((s : Int) + 2 * ↑m + 1)
    midTape hDones hDzero hDnext
  have hheadB : (s : Int) + 2 * ↑m + 1 - ↑(2 * m + 1) + 2 = ((s + 1 : Nat) : Int) + 1 := by omega
  have htapeB : updateTape (updateTape midTape (((s : Int) + 2 * ↑m + 1) - ↑(2 * m + 1)) true)
      (((s : Int) + 2 * ↑m + 1) - ↑(2 * m + 1) + 1) false =
      halvingTape j (s + 1) m (v + 1) := by
    funext i
    rw [Bool_eq_iff]
    simp only [midTape, updateTape_false_iff, updateTape_true_iff, halvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadB, htapeB] at hDEB
  exact hDEB

/-- Inductive `m`-pass execution of the `B–C–D–E` halving loop followed by the `K`-sweep to `A`. -/
theorem halving_loop_run (m j s v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      iterateStep steps ⟨(1 : State), (s : Int) + 1, halvingTape j s m v⟩ =
        canonConfig j (s + m) (v + m + 1) := by
  induction m generalizing s v with
  | zero =>
    refine ⟨s + 3, by omega, ?_⟩
    simpa using halving_loop_base j s v
  | succ m ih =>
    rcases ih (s + 1) (v + 1) with ⟨steps, hpos, hrun⟩
    refine ⟨(4 * m + 7) + steps, by omega, ?_⟩
    rw [iterateStep_add (4 * m + 7) steps, halving_loop_pass j s m v, hrun]
    have hs : s + 1 + m = s + (m + 1) := by omega
    have hv : v + 1 + m + 1 = v + (m + 1) + 1 := by omega
    rw [hs, hv]

/-- Target proposition for the even-Collatz canonical machine phase. -/
def CanonicalPhaseSimulation : Prop :=
  ∀ j k v : Nat, ∃ steps : Nat, steps > 0 ∧
    iterateStep steps (canonConfig j (2 * k + 1) v) =
       canonConfig (evenPhase j k v).1 (evenPhase j k v).2.1
         (evenPhase j k v).2.2

/-- Certified theorem: the actual BBB17 machine executes `evenPhase` from every
    canonical configuration `canonConfig j (2 * k + 1) v` in finitely many positive steps. -/
theorem canonicalPhaseSimulation_holds : CanonicalPhaseSimulation := by
  intro j k v
  rcases halving_loop_run k j 0 v with ⟨steps, hpos, hrun⟩
  refine ⟨1 + steps, by omega, ?_⟩
  rw [iterateStep_add 1 steps, iterateStep_one, evenPhase_init_step j k v, hrun]
  simp [evenPhase]

end BBB17
