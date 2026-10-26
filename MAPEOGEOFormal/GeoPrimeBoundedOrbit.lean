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
    let j : ZMod n := t
    have hcast : (j.val : ZMod n) = j := ZMod.natCast_zmod_val j
    refine ⟨⟨j.val, ZMod.val_lt j⟩, ?_⟩
    rw [iterateStep_eq, hcast]
    simpa [j, iterateStep_eq] using ht

end MAPEOGEOFormal.GeoPrimeOrbit
#print axioms MAPEOGEOFormal.GeoPrimeOrbit.boundedCoverage_iff_orbitSurjective
