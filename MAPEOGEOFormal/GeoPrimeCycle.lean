import Mathlib
import MAPEOGEOFormal.GeoEulerPrime

namespace MAPEOGEOFormal.GeoPrimeCycle

def FullStep (n k : Nat) : Prop := Nat.Coprime n k

def GeometricPrime (n : Nat) : Prop :=
  2 ≤ n ∧ ∀ k, 0 < k → k < n → FullStep n k

theorem geometricPrime_iff_prime (n : Nat) :
    GeometricPrime n ↔ Nat.Prime n := by
  constructor
  · rintro ⟨hn, hsteps⟩
    apply Nat.prime_of_coprime n (by omega)
    intro k hk hk0
    exact hsteps k (Nat.pos_of_ne_zero hk0) hk
  · intro hp
    refine ⟨hp.two_le, ?_⟩
    intro k hk hklt
    apply (hp.coprime_iff_not_dvd).2
    intro hd
    have hle : n ≤ k := Nat.le_of_dvd hk hd
    omega

end MAPEOGEOFormal.GeoPrimeCycle

#print axioms MAPEOGEOFormal.GeoPrimeCycle.geometricPrime_iff_prime
