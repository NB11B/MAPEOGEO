import MAPEOGEOFormal.GeoEuler
import Mathlib

/-!
GEO-EULER-LEAN-002: bridge relational irreducibility to Nat.Prime.
Separate module keeps any failure independent from the basic arithmetic proofs.
-/
namespace MAPEOGEOFormal.GeoEuler

theorem relationallyIrreducible_iff_prime (n : Nat) :
    RelationallyIrreducible n ↔ Nat.Prime n := by
  rw [irreducible_equiv, Nat.prime_iff_not_exists_mul_eq]
  constructor
  · rintro ⟨hn, hnone⟩
    refine ⟨hn, ?_⟩
    rintro ⟨a,b,ha,hb,hab⟩
    apply hnone
    have ha1 : 1 < a := by
      by_contra h
      have hle : a ≤ 1 := by omega
      interval_cases a <;> simp_all
    have hb1 : 1 < b := by
      by_contra h
      have hle : b ≤ 1 := by omega
      interval_cases b <;> simp_all
    exact ⟨a,b,ha1,hb1,hab⟩
  · rintro ⟨hn, hnone⟩
    refine ⟨hn, ?_⟩
    rintro ⟨a,b,ha,hb,hab⟩
    apply hnone
    have ha' : a < n := by
      have hle : a * 2 ≤ a * b :=
        Nat.mul_le_mul_left a (by omega : 2 ≤ b)
      omega
    have hb' : b < n := by
      have hle : 2 * b ≤ a * b :=
        Nat.mul_le_mul_right b (by omega : 2 ≤ a)
      omega
    exact ⟨a,b,ha',hb',hab⟩

end MAPEOGEOFormal.GeoEuler

#print axioms MAPEOGEOFormal.GeoEuler.relationallyIrreducible_iff_prime
