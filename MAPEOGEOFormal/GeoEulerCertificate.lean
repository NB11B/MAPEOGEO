import Mathlib
import MAPEOGEOFormal.GeoEuler

/-!
  A certificate checks the *recurrence laws* of an externally selected
  binary operation, rather than trusting its name or finite sample fit.
  Any implementation proving these laws has unique arithmetic semantics.
-/
namespace MAPEOGEOFormal.GeoEuler

structure RecurrenceCertificate (A M : Nat → Nat → Nat) : Prop where
  add_zero : ∀ a, A a 0 = a
  add_succ : ∀ a b, A a (b+1) = Nat.succ (A a b)
  mul_zero : ∀ a, M a 0 = 0
  mul_succ : ∀ a b, M a (b+1) = A (M a b) a

theorem certified_add_eq (A M : Nat → Nat → Nat)
    (h : RecurrenceCertificate A M) (a b : Nat) : A a b = a+b := by
  induction b with
  | zero => simpa using h.add_zero a
  | succ b ih =>
      rw [h.add_succ, ih]
      exact (Nat.add_succ a b).symm

theorem certified_mul_eq (A M : Nat → Nat → Nat)
    (h : RecurrenceCertificate A M) (a b : Nat) : M a b = a*b := by
  induction b with
  | zero => simpa using h.mul_zero a
  | succ b ih =>
      rw [h.mul_succ, certified_add_eq A M h, ih, Nat.mul_succ]

theorem reference_certificate : RecurrenceCertificate addR mulR := by
  constructor
  · intro a; rfl
  · intro a b; rfl
  · intro a; rfl
  · intro a b; rfl

theorem certified_irreducibility (A M : Nat → Nat → Nat)
    (h : RecurrenceCertificate A M) (n : Nat) :
    (2 ≤ n ∧ ¬ ∃ a b, 1 < a ∧ 1 < b ∧ M a b = n) ↔
    RelationallyIrreducible n := by
  simp only [certified_mul_eq A M h, irreducible_equiv]

end MAPEOGEOFormal.GeoEuler

#print axioms MAPEOGEOFormal.GeoEuler.certified_add_eq
#print axioms MAPEOGEOFormal.GeoEuler.certified_mul_eq
#print axioms MAPEOGEOFormal.GeoEuler.certified_irreducibility
