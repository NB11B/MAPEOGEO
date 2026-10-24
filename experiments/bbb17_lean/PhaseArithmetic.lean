import SweepMacros
import CollatzBridge

/-!
Canonical three-block tape and arithmetic identities for the proposed BBB17
Collatz simulation. The 242 measured phase matches are observations, NOT
a proof that every canonical configuration follows these phase laws.
No axioms, sorry, or claimed machine/arithmetic simulation theorem.
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

/-- Observed closed-form output of the even-integer arithmetic branch. -/
def evenPhase (j k v : Nat) : Nat × Nat × Nat :=
  (j, k, v + k + 1)

/-- Observed closed-form output of the odd-integer arithmetic branch.
The reservoir uses truncated natural subtraction. -/
def oddPhase (j k v : Nat) : Nat × Nat × Nat :=
  (j, 3 * k + 1, v - (k + 1))

/-- Observed closed-form reset branch. -/
def resetPhase (j v : Nat) : Nat × Nat × Nat :=
  (j + 1, j + 1, v - (j + 1))

theorem decode_evenPhase (j k v : Nat) :
    decodeActive (evenPhase j k v).2.1 = (2 * k + 2) / 2 := by
  simp [decodeActive, evenPhase]
  omega

theorem decode_oddPhase (j k v : Nat) :
    decodeActive (oddPhase j k v).2.1 = (3 * (2 * k + 1) + 1) / 2 := by
  simp [decodeActive, oddPhase]
  omega

theorem evenPhase_matches_collatz (k : Nat) :
    decodeActive k = collatz (2 * k + 2) := by
  have hmod : (2 * k + 2) % 2 = 0 := by omega
  simp [collatz, decodeActive, hmod]
  omega

theorem oddPhase_matches_accelerated_collatz (k : Nat) :
    decodeActive (3 * k + 1) = (3 * (2 * k + 1) + 1) / 2 := by
  simp [decodeActive]
  omega

/-- This is a *target proposition*, not a proved theorem.
One must prove a positive number of real machine steps for each branch,
including tape, head, state and exact beep behavior. -/
def CanonicalPhaseSimulation : Prop :=
  ∀ j k v : Nat, ∃ steps : Nat, steps > 0 ∧
    iterateStep steps (canonConfig j (2 * k + 1) v) =
       canonConfig (evenPhase j k v).1 (evenPhase j k v).2.1
         (evenPhase j k v).2.2

end BBB17
