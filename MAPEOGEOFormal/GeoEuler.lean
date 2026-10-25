import Mathlib

/-!
GEO-EULER-LEAN-001: semantics of successor-derived arithmetic.
This verifies the reference grammar; it does not prove the data-driven
discovery algorithm learned it, nor does it prove Euler's infinite product.
-/
namespace MAPEOGEOFormal.GeoEuler

def addR (a : Nat) : Nat → Nat
  | 0 => a
  | b + 1 => Nat.succ (addR a b)

def mulR (a : Nat) : Nat → Nat
  | 0 => 0
  | b + 1 => addR (mulR a b) a

theorem addR_eq_add (a b : Nat) : addR a b = a + b := by
  induction b with
  | zero => rfl
  | succ b ih =>
      simp [addR, ih, Nat.add_succ]

theorem mulR_eq_mul (a b : Nat) : mulR a b = a * b := by
  induction b with
  | zero => rfl
  | succ b ih =>
      simp [mulR, addR_eq_add, ih, Nat.mul_succ, Nat.add_comm]

theorem addR_swap (a b : Nat) : addR a b = addR b a := by
  simp [addR_eq_add, Nat.add_comm]

theorem mulR_swap (a b : Nat) : mulR a b = mulR b a := by
  simp [mulR_eq_mul, Nat.mul_comm]

theorem square_mul_distributes (a b : Nat) :
    (a*b)^2 = a^2*b^2 := by ring

theorem square_add_interaction (a b : Nat) :
    (a+b)^2 = a^2 + 2*a*b + b^2 := by ring

theorem cube_add_interaction (a b : Nat) :
    (a+b)^3 = a^3 + b^3 + 3*a*b*(a+b) := by ring

def HasCompositeWitness (n : Nat) : Prop :=
  ∃ a b : Nat, 1 < a ∧ 1 < b ∧ mulR a b = n

def RelationallyIrreducible (n : Nat) : Prop :=
  2 ≤ n ∧ ¬ HasCompositeWitness n

theorem witness_equiv (n : Nat) :
    HasCompositeWitness n ↔
      ∃ a b : Nat, 1 < a ∧ 1 < b ∧ a*b = n := by
  simp [HasCompositeWitness, mulR_eq_mul]

theorem irreducible_equiv (n : Nat) :
    RelationallyIrreducible n ↔
      2 ≤ n ∧ ¬ ∃ a b : Nat, 1 < a ∧ 1 < b ∧ a*b = n := by
  simp [RelationallyIrreducible, witness_equiv]

theorem composites_have_witness (a b : Nat)
    (ha : 1 < a) (hb : 1 < b) :
    HasCompositeWitness (a*b) := by
  exact ⟨a,b,ha,hb,by simp [mulR_eq_mul]⟩

end MAPEOGEOFormal.GeoEuler

#print axioms MAPEOGEOFormal.GeoEuler.addR_eq_add
#print axioms MAPEOGEOFormal.GeoEuler.mulR_eq_mul
#print axioms MAPEOGEOFormal.GeoEuler.irreducible_equiv
