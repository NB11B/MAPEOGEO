import MAPEOGEOFormal.GeoEulerPrime
import Mathlib

/-! GEO-PRIME-LEAN-002: an independently constructed multiplication
from the additive square-interaction residual, connected to the
existing successor-derived prime correspondence. -/
namespace MAPEOGEOFormal.GeoEuler

def squareInteraction (a b : Nat) : Nat :=
  (a + b)^2 - a^2 - b^2

def interactionMul (a b : Nat) : Nat :=
  squareInteraction a b / 2

theorem squareInteraction_eq (a b : Nat) :
    squareInteraction a b = 2 * (a*b) := by
  unfold squareInteraction
  have h : a^2 + b^2 + 2 * (a*b) = (a+b)^2 := by ring
  omega

theorem interactionMul_eq_mul (a b : Nat) :
    interactionMul a b = a*b := by
  simp [interactionMul, squareInteraction_eq]

theorem interactionMul_eq_recursive (a b : Nat) :
    interactionMul a b = mulR a b := by
  rw [interactionMul_eq_mul, mulR_eq_mul]

def InteractionIrreducible (n : Nat) : Prop :=
  2 ≤ n ∧ ¬ ∃ a b : Nat, 1 < a ∧ 1 < b ∧ interactionMul a b = n

theorem interactionIrreducible_iff_prime (n : Nat) :
    InteractionIrreducible n ↔ Nat.Prime n := by
  have h : InteractionIrreducible n ↔ RelationallyIrreducible n := by
    simp only [InteractionIrreducible, RelationallyIrreducible,
      HasCompositeWitness, interactionMul_eq_mul, mulR_eq_mul]
  exact h.trans (relationallyIrreducible_iff_prime n)

end MAPEOGEOFormal.GeoEuler

#print axioms MAPEOGEOFormal.GeoEuler.interactionIrreducible_iff_prime
