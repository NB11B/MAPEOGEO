import MAPEOGEOFormal.GeoPrimeOrbitCoprime
import MAPEOGEOFormal.GeoPrimeCycle

/-! Universal operational prime criterion: actual ZMod step traversal. -/
namespace MAPEOGEOFormal.GeoPrimeOrbit

def OperationallyPrime (n : Nat) : Prop :=
  2 ≤ n ∧ ∀ k, 0 < k → k < n →
    OrbitSurjective n (k : ZMod n)

theorem operationallyPrime_iff_prime (n : Nat) :
    OperationallyPrime n ↔ Nat.Prime n := by
  by_cases hn : n = 0
  · subst n
    simp [OperationallyPrime, Nat.Prime]
  haveI : NeZero n := ⟨hn⟩
  have hbridge : OperationallyPrime n ↔
      GeoPrimeCycle.GeometricPrime n := by
    simp only [OperationallyPrime, GeoPrimeCycle.GeometricPrime,
      GeoPrimeCycle.FullStep]
    constructor
    · rintro ⟨hbound,h⟩
      exact ⟨hbound, fun k hk hklt =>
        (orbitSurjective_iff_coprime n k).mp (h k hk hklt)⟩
    · rintro ⟨hbound,h⟩
      exact ⟨hbound, fun k hk hklt =>
        (orbitSurjective_iff_coprime n k).mpr (h k hk hklt)⟩
  exact hbridge.trans (GeoPrimeCycle.geometricPrime_iff_prime n)

end MAPEOGEOFormal.GeoPrimeOrbit

#print axioms MAPEOGEOFormal.GeoPrimeOrbit.operationallyPrime_iff_prime
