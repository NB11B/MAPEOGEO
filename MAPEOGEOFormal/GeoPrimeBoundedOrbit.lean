import Mathlib
import MAPEOGEOFormal.GeoPrimeOrbit

namespace MAPEOGEOFormal.GeoPrimeOrbit

/-- A finite operational test: every vertex is among the first n iterates. -/
def BoundedCoverage (n : Nat) (k : ZMod n) : Prop :=
  ∀ x : ZMod n, ∃ t : Fin n, iterateStep n k t.val = x

theorem boundedCoverage_iff_orbitSurjective (n : Nat) [NeZero n]
    (k : ZMod n) : BoundedCoverage n k ↔ OrbitSurjective n k := by
  constructor
  · intro h x
    rcases h x with ⟨t, ht⟩
    exact ⟨t.val, ht⟩
  · intro h x
    rcases h x with ⟨t, ht⟩
    have hperiod : iterateStep n k (t % n) = iterateStep n k t := by
      rw [iterateStep_eq, iterateStep_eq]
      simp only [Nat.cast_mod, ZMod.natCast_self, mod_zero]
    exact ⟨⟨t % n, Nat.mod_lt t (NeZero.pos n)⟩, hperiod.trans ht⟩

end MAPEOGEOFormal.GeoPrimeOrbit
#print axioms MAPEOGEOFormal.GeoPrimeOrbit.boundedCoverage_iff_orbitSurjective
