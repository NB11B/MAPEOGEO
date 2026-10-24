import SweepMacros
import CollatzBridge

/-!
Canonical three-block tape, arithmetic identities, and complete certified machine
simulations for all three macro-phases of BBB17:
1. Even-Collatz branch (`u = 2k + 1` → `(j, k, v + k + 1)`)
2. Accelerated odd-Collatz branch (`u = 2k, k > 0` → `(j, 3k + 1, v - (k + 1))`)
3. Completed-orbit reset & beep branch (`u = 0` → `(j + 1, j + 1, v - (j + 1))`)
4. Exhaustive unified theorem `allCanonicalPhasesSimulated` covering every
   canonical configuration `canonConfig j u v`.

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

/-! ### Propositional characterization lemmas for `canonTape`, `updateTape`, and `jfTape` -/

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

@[simp] theorem jfTape_true_iff (p : Int) (t : Int → Bool) (i : Int) :
    jfTape p t i = true ↔ (i ≠ p + 1 ∧ (i = p ∨ t i = true)) := by
  by_cases h1 : i = p + 1
  · simp [jfTape, h1]
  · by_cases h2 : i = p <;> simp [jfTape, h1, h2]

@[simp] theorem canonTape_true_iff (j u v : Nat) (i : Int) :
    canonTape j u v i = true ↔
      ((-1 - (j : Int) ≤ i ∧ i ≤ -2) ∨
       (0 ≤ i ∧ i < (u : Int)) ∨
       ((u : Int) + 1 ≤ i ∧ i ≤ (u : Int) + (v : Int))) := by
  unfold canonTape
  exact decide_eq_true_iff

/-! ### 1. Certified Machine Simulation of the Even-Collatz Phase (`u = 2k + 1`) -/

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

/-! ### 2. Certified Machine Simulation of the Accelerated Odd-Collatz Phase (`u = 2k, k > 0`) -/

/-- Intermediate tape during the first stage (`B–C–D–E` parity scan) of the odd-Collatz
    phase `u = 2 * (m + 1)`: `canonTape j (s + 2*m + 2) v` with cell `s` cleared. -/
def oddHalvingTape (j s m v : Nat) : Int → Bool :=
  updateTape (canonTape j (s + 2 * m + 2) v) (s : Int) false

@[simp] theorem oddHalvingTape_true_iff (j s m v : Nat) (i : Int) :
    oddHalvingTape j s m v i = true ↔
      (i ≠ (s : Int) ∧
       ((-1 - (j : Int) ≤ i ∧ i ≤ -2) ∨
        (0 ≤ i ∧ i < ((s + 2 * m + 2 : Nat) : Int)) ∨
        (((s + 2 * m + 2 : Nat) : Int) + 1 ≤ i ∧
         i ≤ ((s + 2 * m + 2 : Nat) : Int) + (v : Int)))) := by
  simp [oddHalvingTape]

/-- Intermediate tape during the second stage (`G–H–I–J–F` tripling loop) of the odd-Collatz
    phase, with `a` ones in `[0, a-1]`, `3*b` ones in `[a+1, a+3*b]`, and right reservoir
    bounded by fixed upper index `R`. -/
def triplingTape (j a b R : Nat) : Int → Bool := fun i =>
  decide ((-1 - (j : Int) ≤ i ∧ i ≤ -2) ∨
          (0 ≤ i ∧ i < (a : Int)) ∨
          ((a : Int) + 1 ≤ i ∧ i ≤ (a : Int) + 3 * (b : Int)) ∨
          ((a : Int) + 3 * (b : Int) + 2 ≤ i ∧ i ≤ (R : Int)))

@[simp] theorem triplingTape_true_iff (j a b R : Nat) (i : Int) :
    triplingTape j a b R i = true ↔
      ((-1 - (j : Int) ≤ i ∧ i ≤ -2) ∨
       (0 ≤ i ∧ i < (a : Int)) ∨
       ((a : Int) + 1 ≤ i ∧ i ≤ (a : Int) + 3 * (b : Int)) ∨
       ((a : Int) + 3 * (b : Int) + 2 ≤ i ∧ i ≤ (R : Int))) := by
  unfold triplingTape
  exact decide_eq_true_iff

/-- First step of the odd-Collatz phase (`u = 2 * (m + 1)`): state `A` clears cell `0`
    and enters state `B` at head `1`. -/
theorem oddPhase_init_step (j m v : Nat) :
    step (canonConfig j (2 * (m + 1)) v) =
      ⟨(1 : State), ((0 : Nat) : Int) + 1, oddHalvingTape j 0 m v⟩ := by
  have h0 : canonTape j (2 * (m + 1)) v 0 = true := by
    rw [canonTape_true_iff]
    omega
  have hact : action (0 : State) true = ⟨false, true, (1 : State)⟩ := by decide
  simp [canonConfig, step, h0, hact]
  funext i
  rw [Bool_eq_iff]
  simp [oddHalvingTape_true_iff, canonTape_true_iff]
  omega

/-- Single pass (`m + 1 → m`) of the odd-Collatz `B–C–D–E` parity scan: in `4 * m + 9` steps,
    state `B` at head `s + 1` on `oddHalvingTape j s (m + 1) v` advances to state `B`
    at head `(s + 1) + 1` on `oddHalvingTape j (s + 1) m (v + 1)`. -/
theorem oddHalving_loop_pass (j s m v : Nat) :
    iterateStep (4 * m + 9) ⟨(1 : State), (s : Int) + 1, oddHalvingTape j s (m + 1) v⟩ =
      ⟨(1 : State), ((s + 1 : Nat) : Int) + 1, oddHalvingTape j (s + 1) m (v + 1)⟩ := by
  have hsplit : 4 * m + 9 = ((2 * m + 3) + 2) + ((2 * m + 2) + 2) := by omega
  rw [hsplit, iterateStep_add ((2 * m + 3) + 2) ((2 * m + 2) + 2)]
  have hBones : ∀ r : Nat, r < 2 * m + 3 →
      oddHalvingTape j s (m + 1) v (((s : Int) + 1) + ↑r) = true := by
    intro r hr
    rw [oddHalvingTape_true_iff]
    omega
  have hBzero : oddHalvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 3)) = false := by
    rw [Bool_eq_false_iff, oddHalvingTape_true_iff]
    omega
  have hBprev : oddHalvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 3) - 1) = true := by
    rw [oddHalvingTape_true_iff]
    omega
  have hBCD := sweep_B_then_C1_to_D (2 * m + 3) ((s : Int) + 1)
    (oddHalvingTape j s (m + 1) v) hBones hBzero hBprev
  let midTape : Int → Bool := updateTape (canonTape j (s + 2 * m + 3) (v + 1)) (s : Int) false
  have hheadD : (s : Int) + 1 + ↑(2 * m + 3) - 2 = (s : Int) + 2 * ↑m + 2 := by omega
  have htapeD : updateTape (updateTape (oddHalvingTape j s (m + 1) v)
      (((s : Int) + 1) + ↑(2 * m + 3)) true) (((s : Int) + 1) + ↑(2 * m + 3) - 1) false = midTape := by
    funext i
    rw [Bool_eq_iff]
    simp only [midTape, updateTape_false_iff, updateTape_true_iff, oddHalvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadD, htapeD] at hBCD
  rw [hBCD]
  have hDones : ∀ r : Nat, r < 2 * m + 2 →
      midTape (((s : Int) + 2 * ↑m + 2) - ↑r) = true := by
    intro r hr
    simp only [midTape, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDzero : midTape (((s : Int) + 2 * ↑m + 2) - ↑(2 * m + 2)) = false := by
    rw [Bool_eq_false_iff]
    simp only [midTape, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDnext : midTape (((s : Int) + 2 * ↑m + 2) - ↑(2 * m + 2) + 1) = true := by
    simp only [midTape, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDEB := sweep_D_then_E1_to_B (2 * m + 2) ((s : Int) + 2 * ↑m + 2)
    midTape hDones hDzero hDnext
  have hheadB : (s : Int) + 2 * ↑m + 2 - ↑(2 * m + 2) + 2 = ((s + 1 : Nat) : Int) + 1 := by omega
  have htapeB : updateTape (updateTape midTape (((s : Int) + 2 * ↑m + 2) - ↑(2 * m + 2)) true)
      (((s : Int) + 2 * ↑m + 2) - ↑(2 * m + 2) + 1) false =
      oddHalvingTape j (s + 1) m (v + 1) := by
    funext i
    rw [Bool_eq_iff]
    simp only [midTape, updateTape_false_iff, updateTape_true_iff, oddHalvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadB, htapeB] at hDEB
  exact hDEB

/-- Base case (`m = 0`) of the odd-Collatz `B–C–D–E` parity scan: in `6` steps
    (`B(1) → B(0) → C(1) → D(0) → E(0) → F → G`), the machine transitions from state `B`
    at head `s + 1` on `oddHalvingTape j s 0 v` to state `G` at head `(s + 1) + 3 * 0`
    on `triplingTape j (s + 1) 0 (s + 2 + v)`. -/
theorem oddHalving_loop_base (j s v : Nat) :
    iterateStep 6 ⟨(1 : State), (s : Int) + 1, oddHalvingTape j s 0 v⟩ =
      ⟨(6 : State), ((s + 1 : Nat) : Int) + 3 * ↑(0 : Nat), triplingTape j (s + 1) 0 (s + 2 + v)⟩ := by
  have hsplit : (6 : Nat) = (1 + 2) + (0 + 3) := by omega
  rw [hsplit, iterateStep_add (1 + 2) (0 + 3)]
  have hBones : ∀ r : Nat, r < 1 → oddHalvingTape j s 0 v (((s : Int) + 1) + ↑r) = true := by
    intro r hr
    rw [oddHalvingTape_true_iff]
    omega
  have hBzero : oddHalvingTape j s 0 v (((s : Int) + 1) + ↑(1 : Nat)) = false := by
    rw [Bool_eq_false_iff, oddHalvingTape_true_iff]
    omega
  have hBprev : oddHalvingTape j s 0 v (((s : Int) + 1) + ↑(1 : Nat) - 1) = true := by
    rw [oddHalvingTape_true_iff]
    omega
  have hBCD := sweep_B_then_C1_to_D 1 ((s : Int) + 1) (oddHalvingTape j s 0 v) hBones hBzero hBprev
  let midTape0 : Int → Bool := updateTape (canonTape j (s + 1) (v + 1)) (s : Int) false
  have hheadD : (s : Int) + 1 + ↑(1 : Nat) - 2 = (s : Int) := by omega
  have htapeD : updateTape (updateTape (oddHalvingTape j s 0 v)
      (((s : Int) + 1) + ↑(1 : Nat)) true) (((s : Int) + 1) + ↑(1 : Nat) - 1) false = midTape0 := by
    funext i
    rw [Bool_eq_iff]
    simp only [midTape0, updateTape_false_iff, updateTape_true_iff, oddHalvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadD, htapeD] at hBCD
  rw [hBCD]
  have hDones : ∀ r : Nat, r < 0 → midTape0 ((s : Int) - ↑r) = true := by
    intro r hr
    omega
  have hDzero : midTape0 ((s : Int) - ↑(0 : Nat)) = false := by
    rw [Bool_eq_false_iff]
    simp only [midTape0, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDnext : midTape0 ((s : Int) - ↑(0 : Nat) + 1) = false := by
    rw [Bool_eq_false_iff]
    simp only [midTape0, updateTape_false_iff, canonTape_true_iff]
    omega
  have hDEFG := sweep_D_then_E0_F_to_G 0 (s : Int) midTape0 hDones hDzero hDnext
  have hheadG : (s : Int) - ↑(0 : Nat) + 1 = ((s + 1 : Nat) : Int) + 3 * ↑(0 : Nat) := by omega
  have htapeG : updateTape (updateTape midTape0 ((s : Int) - ↑(0 : Nat)) true)
      ((s : Int) - ↑(0 : Nat) + 2) false = triplingTape j (s + 1) 0 (s + 2 + v) := by
    funext i
    rw [Bool_eq_iff]
    simp only [midTape0, updateTape_false_iff, updateTape_true_iff, triplingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadG, htapeG] at hDEFG
  exact hDEFG

/-- Inductive `m`-pass execution of the odd-Collatz `B–C–D–E` scan reaching state `G`. -/
theorem oddHalving_loop_run (m j s v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      iterateStep steps ⟨(1 : State), (s : Int) + 1, oddHalvingTape j s m v⟩ =
        ⟨(6 : State), ((s + m + 1 : Nat) : Int) + 3 * ↑(0 : Nat),
          triplingTape j (s + m + 1) 0 (s + 2 * m + 2 + v)⟩ := by
  induction m generalizing s v with
  | zero =>
    refine ⟨6, by omega, ?_⟩
    simpa using oddHalving_loop_base j s v
  | succ m ih =>
    rcases ih (s + 1) (v + 1) with ⟨steps, hpos, hrun⟩
    refine ⟨(4 * m + 9) + steps, by omega, ?_⟩
    rw [iterateStep_add (4 * m + 9) steps, oddHalving_loop_pass j s m v, hrun]
    have hs : s + 1 + m + 1 = s + (m + 1) + 1 := by omega
    have hR : s + 1 + 2 * m + 2 + (v + 1) = s + 2 * (m + 1) + 2 + v := by omega
    rw [hs, hR]

/-- Single pass (`a + 1 → a`, `b → b + 1`) of the `G–H–I–J–F` tripling loop:
    in `6 * b + 6` steps, state `G` at head `(a + 1) + 3 * b` on `triplingTape j (a + 1) b R`
    advances to state `G` at head `a + 3 * (b + 1)` on `triplingTape j a (b + 1) R`. -/
theorem tripling_loop_pass (j a b R : Nat) :
    iterateStep (6 * b + 6)
      ⟨(6 : State), ((a + 1 : Nat) : Int) + 3 * (b : Int), triplingTape j (a + 1) b R⟩ =
      ⟨(6 : State), (a : Int) + 3 * ((b + 1 : Nat) : Int), triplingTape j a (b + 1) R⟩ := by
  have hsplit : 6 * b + 6 = (3 * b + 2) + ((3 * b + 1) + 3) := by omega
  rw [hsplit, iterateStep_add (3 * b + 2) ((3 * b + 1) + 3)]
  have hGones : ∀ r : Nat, r < 3 * b →
      triplingTape j (a + 1) b R ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑r) = true := by
    intro r hr
    rw [triplingTape_true_iff]
    omega
  have hGzero : triplingTape j (a + 1) b R
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b)) = false := by
    rw [Bool_eq_false_iff, triplingTape_true_iff]
    omega
  have hGprev : triplingTape j (a + 1) b R
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b) - 1) = true := by
    rw [triplingTape_true_iff]
    omega
  have hGHI := sweep_G_then_H1_to_I (3 * b) (((a + 1 : Nat) : Int) + 3 * (b : Int))
    (triplingTape j (a + 1) b R) hGones hGzero hGprev
  let midITape : Int → Bool :=
    updateTape (updateTape (triplingTape j (a + 1) b R) ((a : Int) + 1) true) (a : Int) false
  have hheadI : ((a + 1 : Nat) : Int) + 3 * (b : Int) - ↑(3 * b) = (a : Int) + 1 := by omega
  have htapeI : updateTape (updateTape (triplingTape j (a + 1) b R)
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b)) true)
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b) - 1) false = midITape := by
    funext i
    rw [Bool_eq_iff]
    simp only [midITape, updateTape_false_iff, updateTape_true_iff, triplingTape_true_iff]
    omega
  rw [htapeI, hheadI] at hGHI
  rw [hGHI]
  have hIones : ∀ r : Nat, r < 3 * b + 1 →
      midITape (((a : Int) + 1) + ↑r) = true := by
    intro r hr
    simp only [midITape, updateTape_false_iff, updateTape_true_iff, triplingTape_true_iff]
    omega
  have hIzero : midITape (((a : Int) + 1) + ↑(3 * b + 1)) = false := by
    rw [Bool_eq_false_iff]
    simp only [midITape, updateTape_false_iff, updateTape_true_iff, triplingTape_true_iff]
    omega
  have hIJFG := sweep_I_then_JF_to_G (3 * b + 1) ((a : Int) + 1) midITape hIones hIzero
  have hheadG : (a : Int) + 1 + ↑(3 * b + 1) + 1 = (a : Int) + 3 * ((b + 1 : Nat) : Int) := by omega
  have htapeG : jfTape ((a : Int) + 1 + ↑(3 * b + 1) + 1)
      (updateTape midITape ((a : Int) + 1 + ↑(3 * b + 1)) true) =
      triplingTape j a (b + 1) R := by
    funext i
    rw [Bool_eq_iff]
    simp only [midITape, jfTape_true_iff, updateTape_false_iff, updateTape_true_iff, triplingTape_true_iff]
    omega
  rw [htapeG, hheadG] at hIJFG
  exact hIJFG

/-- Base case (`a = 0`) of the `G–H–I–J–F` tripling loop: in `3 * b + 2` steps,
    state `G` sweeps left across `3 * b` ones, writes `1` at `0`, `H` reads `0` at `-1`,
    and the machine returns to `A` at head `0`. -/
theorem tripling_loop_base (j b R : Nat) :
    iterateStep (3 * b + 2)
      ⟨(6 : State), ((0 : Nat) : Int) + 3 * (b : Int), triplingTape j 0 b R⟩ =
      ⟨(0 : State), 0, updateTape (triplingTape j 0 b R) 0 true⟩ := by
  have hGones : ∀ r : Nat, r < 3 * b →
      triplingTape j 0 b R ((((0 : Nat) : Int) + 3 * (b : Int)) - ↑r) = true := by
    intro r hr
    rw [triplingTape_true_iff]
    omega
  have hGzero : triplingTape j 0 b R ((((0 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b)) = false := by
    rw [Bool_eq_false_iff, triplingTape_true_iff]
    omega
  have hGprev : triplingTape j 0 b R ((((0 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b) - 1) = false := by
    rw [Bool_eq_false_iff, triplingTape_true_iff]
    omega
  have hGHA := sweep_G_then_H0_to_A (3 * b) (((0 : Nat) : Int) + 3 * (b : Int))
    (triplingTape j 0 b R) hGones hGzero hGprev
  have hheadA : ((0 : Nat) : Int) + 3 * (b : Int) - ↑(3 * b) = 0 := by omega
  rw [hheadA] at hGHA
  exact hGHA

/-- Inductive `a`-pass execution of the `G–H–I–J–F` tripling loop followed by exit to `A`. -/
theorem tripling_loop_run (a j b R : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      iterateStep steps ⟨(6 : State), (a : Int) + 3 * (b : Int), triplingTape j a b R⟩ =
        ⟨(0 : State), 0, updateTape (triplingTape j 0 (a + b) R) 0 true⟩ := by
  induction a generalizing b with
  | zero =>
    refine ⟨3 * b + 2, by omega, ?_⟩
    simpa using tripling_loop_base j b R
  | succ a ih =>
    rcases ih (b + 1) with ⟨steps, hpos, hrun⟩
    refine ⟨(6 * b + 6) + steps, by omega, ?_⟩
    rw [iterateStep_add (6 * b + 6) steps, tripling_loop_pass j a b R, hrun]
    have hab : a + (b + 1) = a + 1 + b := by omega
    rw [hab]

/-- Target proposition for the accelerated odd-Collatz canonical machine phase (`u = 2k, k > 0`). -/
def OddCanonicalPhaseSimulation : Prop :=
  ∀ j k v : Nat, k > 0 → ∃ steps : Nat, steps > 0 ∧
    iterateStep steps (canonConfig j (2 * k) v) =
      canonConfig (oddPhase j k v).1 (oddPhase j k v).2.1 (oddPhase j k v).2.2

/-- Certified theorem: for every `k > 0`, the actual BBB17 machine executes `oddPhase`
    from `canonConfig j (2 * k) v` in finitely many positive steps, across both
    reservoir regimes (`v ≥ k + 1` and `v ≤ k + 1`). -/
theorem oddCanonicalPhaseSimulation_holds : OddCanonicalPhaseSimulation := by
  intro j k v hk
  obtain ⟨m, rfl⟩ : ∃ m : Nat, k = m + 1 := ⟨k - 1, by omega⟩
  rcases oddHalving_loop_run m j 0 v with ⟨s1, hs1, hrun1⟩
  rcases tripling_loop_run (m + 1) j 0 (2 * (m + 1) + v) with ⟨s2, hs2, hrun2⟩
  refine ⟨1 + (s1 + s2), by omega, ?_⟩
  rw [iterateStep_add 1 (s1 + s2), iterateStep_one, oddPhase_init_step j m v]
  rw [iterateStep_add s1 s2, hrun1]
  have h0m : 0 + m + 1 = m + 1 := by omega
  have h0R : 0 + 2 * m + 2 + v = 2 * (m + 1) + v := by omega
  rw [h0m, h0R, hrun2]
  simp only [canonConfig, oddPhase]
  congr 1
  funext i
  rw [Bool_eq_iff]
  simp only [updateTape_true_iff, triplingTape_true_iff, canonTape_true_iff]
  omega

/-! ### 3. Certified Machine Simulation of the Completed-Orbit Reset & Beep Phase (`u = 0`) -/

/-- Intermediate tape at state `M` (12) during the `L–M–N–O–P–Q` reset loop, with
    `a` ones remaining in `[-1-a, -2]`, `s` ones shifted to `[-2-(a+s), -3-a]`,
    `s + 1` ones built in `[0, s]`, and reservoir `[s + 2, v]`. -/
def resetTape (a s v : Nat) : Int → Bool := fun i =>
  decide ((-2 - ((a + s : Nat) : Int) ≤ i ∧ i ≤ -3 - (a : Int)) ∨
          (-1 - (a : Int) ≤ i ∧ i ≤ -2) ∨
          (0 ≤ i ∧ i ≤ (s : Int)) ∨
          ((s : Int) + 2 ≤ i ∧ i ≤ (v : Int)))

@[simp] theorem resetTape_true_iff (a s v : Nat) (i : Int) :
    resetTape a s v i = true ↔
      ((-2 - ((a + s : Nat) : Int) ≤ i ∧ i ≤ -3 - (a : Int)) ∨
       (-1 - (a : Int) ≤ i ∧ i ≤ -2) ∨
       (0 ≤ i ∧ i ≤ (s : Int)) ∨
       ((s : Int) + 2 ≤ i ∧ i ≤ (v : Int))) := by
  unfold resetTape
  exact decide_eq_true_iff

/-- Initial two steps of the reset phase (`A(0) → L → M`): from `canonConfig j 0 v`,
    the machine enters state `M` (12) at head `0` on `resetTape j 0 v`. -/
theorem resetPhase_init_two_steps (j v : Nat) :
    iterateStep 2 (canonConfig j 0 v) =
      ⟨(12 : State), ((0 : Nat) : Int), resetTape j 0 v⟩ := by
  have h0 : canonTape j 0 v 0 = false := by
    rw [Bool_eq_false_iff, canonTape_true_iff]
    omega
  have hactA : action (0 : State) false = ⟨true, true, (11 : State)⟩ := by decide
  have hstep1 : step (canonConfig j 0 v) = ⟨(11 : State), 1, updateTape (canonTape j 0 v) 0 true⟩ := by
    simp [canonConfig, step, h0, hactA]
    funext i
    by_cases hi : i = 0 <;> simp [updateTape, hi]
  rw [iterateStep_two, hstep1, L_one_step_config]
  have hhead : (1 : Int) - 1 = ((0 : Nat) : Int) := by omega
  rw [hhead]
  congr 1
  funext i
  rw [Bool_eq_iff]
  simp only [updateTape_false_iff, updateTape_true_iff, resetTape_true_iff, canonTape_true_iff]
  omega

/-- Single pass (`a + 1 → a`, `s → s + 1`) of the `M–N–O–P–Q–L` reset loop:
    in `2 * a + 2 * s + 9` steps, state `M` at head `s` on `resetTape (a + 1) s v`
    advances to state `M` at head `s + 1` on `resetTape a (s + 1) v`. -/
theorem reset_loop_pass (a s v : Nat) :
    iterateStep (2 * a + 2 * s + 9) ⟨(12 : State), (s : Int), resetTape (a + 1) s v⟩ =
      ⟨(12 : State), ((s + 1 : Nat) : Int), resetTape a (s + 1) v⟩ := by
  have hsplit : 2 * a + 2 * s + 9 =
      ((s + 1) + 1) + (((a + 1) + 1) + (1 + ((a + 1) + ((s + 1) + 2)))) := by omega
  rw [hsplit, iterateStep_add ((s + 1) + 1)]
  -- 1. M sweeps left over s + 1 ones [0, s] and reads 0 at -1 -> N at -2
  have hMones : ∀ r : Nat, r < s + 1 → resetTape (a + 1) s v ((s : Int) - ↑r) = true := by
    intro r hr
    rw [resetTape_true_iff]
    omega
  have hMzero : resetTape (a + 1) s v ((s : Int) - ↑(s + 1)) = false := by
    rw [Bool_eq_false_iff, resetTape_true_iff]
    omega
  have hMN := sweep_M_to_N (s + 1) (s : Int) (resetTape (a + 1) s v) hMones hMzero
  have hheadN : (s : Int) - ↑(s + 1) - 1 = -2 := by omega
  rw [hheadN] at hMN
  rw [hMN]
  -- 2. N sweeps left over a + 1 ones [-2 - a, -2] and reads 0 at -3 - a -> O at -2 - a
  rw [iterateStep_add ((a + 1) + 1)]
  have hNones : ∀ r : Nat, r < a + 1 → resetTape (a + 1) s v ((-2 : Int) - ↑r) = true := by
    intro r hr
    rw [resetTape_true_iff]
    omega
  have hNzero : resetTape (a + 1) s v ((-2 : Int) - ↑(a + 1)) = false := by
    rw [Bool_eq_false_iff, resetTape_true_iff]
    omega
  have hNO := sweep_N_to_beep_O (a + 1) (-2 : Int) (resetTape (a + 1) s v) hNones hNzero
  let tapeO : Int → Bool := updateTape (resetTape (a + 1) s v) (-3 - (a : Int)) true
  have hheadO : (-2 : Int) - ↑(a + 1) + 1 = -2 - (a : Int) := by omega
  have htapeO : updateTape (resetTape (a + 1) s v) ((-2 : Int) - ↑(a + 1)) true = tapeO := by
    have heq : (-2 : Int) - ↑(a + 1) = -3 - (a : Int) := by omega
    rw [heq]
  rw [hheadO, htapeO] at hNO
  rw [hNO]
  -- 3. O reads 1 at -2 - a, writes 0, moves right to -1 - a in state P (15)
  rw [iterateStep_add 1, iterateStep_one]
  have hOone : tapeO (-2 - (a : Int)) = true := by
    simp only [tapeO, updateTape_true_iff, resetTape_true_iff]
    omega
  let tapeP : Int → Bool := updateTape tapeO (-2 - (a : Int)) false
  have hOP : step ⟨(14 : State), -2 - (a : Int), tapeO⟩ =
      ⟨(15 : State), -1 - (a : Int), tapeP⟩ := by
    simp [step, hOone, action_O_on_one]
    constructor
    · omega
    · funext i
      by_cases hi : i = -2 - (a : Int) <;> simp [tapeP, updateTape, hi]
  rw [hOP]
  -- 4. P sweeps right over a ones [-1 - a, -2] and reads 0 at -1 -> Q at 0
  rw [iterateStep_add (a + 1)]
  have hPones : ∀ r : Nat, r < a → tapeP ((-1 - (a : Int)) + ↑r) = true := by
    intro r hr
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]
    omega
  have hPzero : tapeP ((-1 - (a : Int)) + ↑a) = false := by
    rw [Bool_eq_false_iff]
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]
    omega
  have hPQ := sweep_P_to_Q a (-1 - (a : Int)) tapeP hPones hPzero
  have hheadQ : -1 - (a : Int) + ↑a + 1 = 0 := by omega
  rw [hheadQ] at hPQ
  rw [hPQ]
  -- 5. Q sweeps right over s + 1 ones [0, s], reads 0 at s + 1, L -> M at s + 1
  have hQones : ∀ r : Nat, r < s + 1 → tapeP ((0 : Int) + ↑r) = true := by
    intro r hr
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]
    omega
  have hQzero : tapeP ((0 : Int) + ↑(s + 1)) = false := by
    rw [Bool_eq_false_iff]
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]
    omega
  have hQLM := sweep_Q_then_L_to_M (s + 1) 0 tapeP hQones hQzero
  have hheadM : (0 : Int) + ↑(s + 1) = ((s + 1 : Nat) : Int) := by omega
  have htapeM : jfTape ((0 : Int) + ↑(s + 1)) tapeP = resetTape a (s + 1) v := by
    funext i
    rw [Bool_eq_iff]
    simp only [tapeP, tapeO, jfTape_true_iff, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]
    omega
  rw [htapeM, hheadM] at hQLM
  exact hQLM

/-- Base case (`a = 0`) of the reset loop: from state `M` at head `s` on `resetTape 0 s v`,
    in `s + 3` steps (`M` sweeps `s + 1` ones to `N` at `-2`, `N` reads `0` at `-2` -> beep state `O` at `-1`),
    the machine reaches beep state `O` (14) at head `-1`, and 1 step later enters `A` at head `0`. -/
theorem reset_loop_base_to_beep (s v : Nat) :
    iterateStep (s + 3) ⟨(12 : State), (s : Int), resetTape 0 s v⟩ =
      ⟨(14 : State), -1, updateTape (resetTape 0 s v) (-2 : Int) true⟩ := by
  have hsplit : s + 3 = ((s + 1) + 1) + (0 + 1) := by omega
  rw [hsplit, iterateStep_add ((s + 1) + 1) (0 + 1)]
  have hMones : ∀ r : Nat, r < s + 1 → resetTape 0 s v ((s : Int) - ↑r) = true := by
    intro r hr
    rw [resetTape_true_iff]
    omega
  have hMzero : resetTape 0 s v ((s : Int) - ↑(s + 1)) = false := by
    rw [Bool_eq_false_iff, resetTape_true_iff]
    omega
  have hMN := sweep_M_to_N (s + 1) (s : Int) (resetTape 0 s v) hMones hMzero
  have hheadN : (s : Int) - ↑(s + 1) - 1 = -2 := by omega
  rw [hheadN] at hMN
  rw [hMN]
  have hNones : ∀ r : Nat, r < 0 → resetTape 0 s v ((-2 : Int) - ↑r) = true := by
    intro r hr
    omega
  have hNzero : resetTape 0 s v ((-2 : Int) - ↑(0 : Nat)) = false := by
    rw [Bool_eq_false_iff, resetTape_true_iff]
    omega
  have hNO := sweep_N_to_beep_O 0 (-2 : Int) (resetTape 0 s v) hNones hNzero
  have hheadO : (-2 : Int) - ↑(0 : Nat) + 1 = -1 := by omega
  have htapeO : updateTape (resetTape 0 s v) ((-2 : Int) - ↑(0 : Nat)) true =
      updateTape (resetTape 0 s v) (-2 : Int) true := rfl
  rw [hheadO, htapeO] at hNO
  exact hNO

/-- Final step from the terminal beep state `O` at `-1` into `A` at `0`. -/
theorem reset_loop_beep_to_A (s v : Nat) :
    step ⟨(14 : State), -1, updateTape (resetTape 0 s v) (-2 : Int) true⟩ =
      ⟨(0 : State), 0, updateTape (resetTape 0 s v) (-2 : Int) true⟩ := by
  have hzero : updateTape (resetTape 0 s v) (-2 : Int) true (-1 : Int) = false := by
    rw [Bool_eq_false_iff, updateTape_true_iff, resetTape_true_iff]
    omega
  simp [step, hzero, action_O_on_zero]
  funext i
  by_cases hi : i = -1
  · subst hi
    exact hzero.symm
  · simp [hi]

/-- Inductive `a`-pass execution of the reset loop reaching the terminal beep state `O` at `-1`
    and then returning to `A` at `0` on the next step. -/
theorem reset_loop_run (a s v : Nat) :
    ∃ bSteps : Nat, bSteps > 0 ∧
      exitBeep (iterateStep bSteps ⟨(12 : State), (s : Int), resetTape a s v⟩) ∧
      iterateStep (bSteps + 1) ⟨(12 : State), (s : Int), resetTape a s v⟩ =
        ⟨(0 : State), 0, updateTape (resetTape 0 (a + s) v) (-2 : Int) true⟩ := by
  induction a generalizing s with
  | zero =>
    refine ⟨s + 3, by omega, ?_, ?_⟩
    · rw [reset_loop_base_to_beep s v]
      rfl
    · rw [iterateStep_add (s + 3) 1, reset_loop_base_to_beep s v, iterateStep_one]
      simpa using reset_loop_beep_to_A s v
  | succ a ih =>
    rcases ih (s + 1) with ⟨bSteps, hpos, hbeep, hrun⟩
    refine ⟨(2 * a + 2 * s + 9) + bSteps, by omega, ?_, ?_⟩
    · rw [iterateStep_add (2 * a + 2 * s + 9) bSteps, reset_loop_pass a s v]
      exact hbeep
    · have hadd : (2 * a + 2 * s + 9) + bSteps + 1 = (2 * a + 2 * s + 9) + (bSteps + 1) := by omega
      rw [hadd, iterateStep_add (2 * a + 2 * s + 9) (bSteps + 1), reset_loop_pass a s v, hrun]
      have has : a + (s + 1) = a + 1 + s := by omega
      rw [has]

/-- Target proposition for the completed-orbit reset & beep phase (`u = 0`). -/
def ResetCanonicalPhaseSimulation : Prop :=
  ∀ j v : Nat, ∃ bSteps : Nat, bSteps > 0 ∧
    exitBeep (iterateStep bSteps (canonConfig j 0 v)) ∧
    iterateStep (bSteps + 1) (canonConfig j 0 v) =
      canonConfig (resetPhase j v).1 (resetPhase j v).2.1 (resetPhase j v).2.2

/-- Certified theorem: from every completed-orbit configuration `canonConfig j 0 v`,
    the actual BBB17 machine emits a beep in state `O` and transitions to
    `canonConfig (j + 1) (j + 1) (v - (j + 1))`. -/
theorem resetCanonicalPhaseSimulation_holds : ResetCanonicalPhaseSimulation := by
  intro j v
  rcases reset_loop_run j 0 v with ⟨bSteps, hpos, hbeep, hrun⟩
  refine ⟨2 + bSteps, by omega, ?_, ?_⟩
  · rw [iterateStep_add 2 bSteps, resetPhase_init_two_steps j v]
    exact hbeep
  · have hadd : 2 + bSteps + 1 = 2 + (bSteps + 1) := by omega
    rw [hadd, iterateStep_add 2 (bSteps + 1), resetPhase_init_two_steps j v, hrun]
    have hj0 : j + 0 = j := by omega
    rw [hj0]
    simp only [canonConfig, resetPhase]
    congr 1
    funext i
    rw [Bool_eq_iff]
    simp only [updateTape_true_iff, resetTape_true_iff, canonTape_true_iff]
    omega

/-! ### 4. Unified MachinePhase = ArithmeticPhase Theorem for All Canonical Configurations -/

/-- Next canonical `(j', u', v')` triple determined by the arithmetic phase map on `(j, u, v)`. -/
def nextCanonicalTriple (j u v : Nat) : Nat × Nat × Nat :=
  if u = 0 then
    resetPhase j v
  else if u % 2 = 1 then
    evenPhase j (u / 2) v
  else
    oddPhase j (u / 2) v

/-- Unified theorem (`MachinePhase(j, u, v) = ArithmeticPhase(j, u, v)`):
    Every canonical configuration `canonConfig j u v` reaches the exact canonical
    configuration predicted by `nextCanonicalTriple j u v` in finitely many positive
    machine steps. -/
theorem machinePhase_eq_arithmeticPhase (j u v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      iterateStep steps (canonConfig j u v) =
        canonConfig (nextCanonicalTriple j u v).1
          (nextCanonicalTriple j u v).2.1
          (nextCanonicalTriple j u v).2.2 := by
  rcases canon_register_trichotomy u with rfl | ⟨k, rfl⟩ | ⟨k, hk, rfl⟩
  · rcases resetCanonicalPhaseSimulation_holds j v with ⟨bSteps, hpos, _, hrun⟩
    refine ⟨bSteps + 1, by omega, ?_⟩
    simpa [nextCanonicalTriple] using hrun
  · rcases canonicalPhaseSimulation_holds j k v with ⟨steps, hpos, hrun⟩
    have hne0 : 2 * k + 1 ≠ 0 := by omega
    have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    refine ⟨steps, hpos, ?_⟩
    simpa [nextCanonicalTriple, hne0, hmod, hdiv] using hrun
  · rcases oddCanonicalPhaseSimulation_holds j k v hk with ⟨steps, hpos, hrun⟩
    have hne0 : 2 * k ≠ 0 := by omega
    have hmod : ¬((2 * k) % 2 = 1) := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    refine ⟨steps, hpos, ?_⟩
    simpa [nextCanonicalTriple, hne0, hmod, hdiv] using hrun

/-- Explicit odd-branch corollary when `v ≥ k + 1` (reservoir exceeds expansion):
    the machine reaches `canonConfig j (3*k + 1) (v - (k + 1))` while conserving total right-hand ones. -/
theorem oddPhase_machine_sim_conserved (j k v : Nat) (hk : k > 0) (hv : v ≥ k + 1) :
    ∃ steps : Nat, steps > 0 ∧
      iterateStep steps (canonConfig j (2 * k) v) =
        canonConfig j (3 * k + 1) (v - (k + 1)) ∧
      (3 * k + 1) + (v - (k + 1)) = 2 * k + v := by
  rcases oddCanonicalPhaseSimulation_holds j k v hk with ⟨steps, hpos, hrun⟩
  exact ⟨steps, hpos, hrun, by omega⟩

/-- Explicit odd-branch corollary when `v ≤ k + 1` (expansion exceeds reservoir):
    `v ≥ k + 1` is NOT required—the machine writes into fresh `false` cells on the right
    and reaches `canonConfig j (3*k + 1) 0` with an empty reservoir. -/
theorem oddPhase_machine_sim_fresh_tape (j k v : Nat) (hk : k > 0) (hv : v ≤ k + 1) :
    ∃ steps : Nat, steps > 0 ∧
      iterateStep steps (canonConfig j (2 * k) v) =
        canonConfig j (3 * k + 1) 0 := by
  rcases oddCanonicalPhaseSimulation_holds j k v hk with ⟨steps, hpos, hrun⟩
  have hv0 : v - (k + 1) = 0 := by omega
  rw [oddPhase, hv0] at hrun
  exact ⟨steps, hpos, hrun⟩

/-! ### 5. Global Canonical Invariant: Initial Blank Tape & Closure Under Phase Execution -/

/-- Predicate asserting that a machine configuration is in canonical 3-block form. -/
def IsCanonical (c : Config) : Prop :=
  ∃ j u v : Nat, c = canonConfig j u v

/-- The initial blank-tape configuration `initial = ⟨0, 0, fun _ => false⟩` is
    literally `canonConfig 0 0 0`. -/
theorem initial_eq_canonConfig : initial = canonConfig 0 0 0 := by
  unfold initial canonConfig
  congr 1
  funext i
  symm
  rw [Bool_eq_false_iff, canonTape_true_iff]
  omega

/-- The initial configuration satisfies `IsCanonical`. -/
theorem initial_isCanonical : IsCanonical initial :=
  ⟨0, 0, 0, initial_eq_canonConfig⟩

/-- Global phase-closure and termination theorem: every canonical configuration terminates
    its current macro-phase in finitely many positive steps at a canonical configuration. -/
theorem canonical_phase_terminates_and_preserves (c : Config) (hc : IsCanonical c) :
    ∃ steps : Nat, steps > 0 ∧ IsCanonical (iterateStep steps c) := by
  rcases hc with ⟨j, u, v, rfl⟩
  rcases machinePhase_eq_arithmeticPhase j u v with ⟨steps, hpos, hrun⟩
  refine ⟨steps, hpos, (nextCanonicalTriple j u v).1, (nextCanonicalTriple j u v).2.1,
    (nextCanonicalTriple j u v).2.2, hrun⟩

end BBB17
