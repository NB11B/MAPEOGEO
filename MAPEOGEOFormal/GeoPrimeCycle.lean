import Mathlib
import MAPEOGEOFormal.GeoEulerPrime

namespace MAPEOGEOFormal.GeoPrimeCycle

/-- The orbit of repeated step k in a cycle of n vertices visits every
vertex exactly when k and n are coprime. -/
def FullStep (n k : Nat) : Prop := Nat.Coprime n k

def GeometricPrime (n : Nat) : Prop :=
  2 ≤ n ∧ ∀ k, 0 < k → k < n → FullStep n k

theorem geometricPrime_iff_prime (n : Nat) :
    GeometricPrime n ↔ Nat.Prime n := by
  constructor
  · rintro ⟨hn, hsteps⟩
    by_contra hprime
    obtain ⟨d, hdvd, hd2, hdlt⟩ :=
      (Nat.not_prime_iff_exists_dvd_lt hn).mp hprime
    have hg : Nat.gcd n d = d := Nat.gcd_eq_right hdvd
    have hc := hsteps d (by omega) hdlt
    simp only [FullStep, Nat.Coprime] at hc
    omega
  · intro hp
    refine ⟨hp.two_le, ?_⟩
    intro k hk hklt
    by_contra hc
    have ⟨p, hpp, hpn, hpk⟩ :=
      (Nat.Prime.not_coprime_iff_dvd).mp (by
        simpa [FullStep, Nat.coprime_comm] using hc)
    have heq : n = p :=
      (Nat.Prime.dvd_iff_eq hpp (by have := hpp.two_le; omega)).mp hpn
    subst p
    have hle := Nat.le_of_dvd hk hpk
    omega

end MAPEOGEOFormal.GeoPrimeCycle

#print axioms MAPEOGEOFormal.GeoPrimeCycle.geometricPrime_iff_prime
