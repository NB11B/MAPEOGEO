import MAPEOGEOFormal.GeoPrimeOrbit
import Mathlib

namespace MAPEOGEOFormal.GeoPrimeOrbit

/-- A traversing step generates the entire finite cyclic additive group. -/
theorem orbitSurjective_iff_coprime (n k : Nat) [NeZero n] :
    OrbitSurjective n (k : ZMod n) ↔ Nat.Coprime n k := by
  rw [orbitSurjective_iff_mul_surjective]
  constructor
  · intro hs
    obtain ⟨u,hu⟩ := hs 1
    have hunit : IsUnit (k : ZMod n) := by
      exact isUnit_iff_exists_inv.mpr ⟨u, by simpa [mul_comm] using hu⟩
    exact (ZMod.isUnit_iff_coprime k n).mp hunit
  · intro hc
    have hunit : IsUnit (k : ZMod n) :=
      (ZMod.isUnit_iff_coprime k n).mpr (by simpa [Nat.coprime_comm] using hc)
    obtain ⟨u,hu⟩ := isUnit_iff_exists_inv.mp hunit
    intro x
    refine ⟨x*u, ?_⟩
    simpa [mul_assoc, mul_comm, mul_left_comm] using congrArg (fun y : ZMod n => x*y) hu

end MAPEOGEOFormal.GeoPrimeOrbit
#print axioms MAPEOGEOFormal.GeoPrimeOrbit.orbitSurjective_iff_coprime
