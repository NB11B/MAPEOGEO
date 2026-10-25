import Mathlib
import MAPEOGEOFormal.GeoPrimeCycle

/-!
The actual cycle traversal is defined as repeated addition in ZMod n.
This file establishes its connection to a structural additive-generation
criterion. The cardinality/equivalence theorem remains a separate gate.
-/
namespace MAPEOGEOFormal.GeoPrimeOrbit

def step (n : Nat) (k x : ZMod n) : ZMod n := x + k

def iterateStep (n : Nat) (k : ZMod n) : Nat → ZMod n
  | 0 => 0
  | t + 1 => step n k (iterateStep n k t)

theorem iterateStep_eq (n : Nat) (k : ZMod n) (t : Nat) :
    iterateStep n k t = (t : ZMod n) * k := by
  induction t with
  | zero => simp [iterateStep]
  | succ t ih =>
      simp only [iterateStep, step, ih]
      push_cast
      ring

/-- Operational full traversal: each target is an iterate of the step. -/
def OrbitSurjective (n : Nat) (k : ZMod n) : Prop :=
  ∀ x : ZMod n, ∃ t : Nat, iterateStep n k t = x

theorem orbitSurjective_iff_mul_surjective (n : Nat) (k : ZMod n) :
    OrbitSurjective n k ↔ Function.Surjective (fun x : ZMod n => x*k) := by
  constructor
  · intro h x
    rcases h x with ⟨t,ht⟩
    refine ⟨(t : ZMod n), ?_⟩
    simpa [iterateStep_eq] using ht
  · intro h x
    rcases h x with ⟨j,hj⟩
    exact ⟨j.val, by simpa [iterateStep_eq] using hj⟩

end MAPEOGEOFormal.GeoPrimeOrbit
#print axioms MAPEOGEOFormal.GeoPrimeOrbit.iterateStep_eq
#print axioms MAPEOGEOFormal.GeoPrimeOrbit.orbitSurjective_iff_mul_surjective
