import MAPEOGEOFormal.GeoEulerPrime
import MAPEOGEOFormal.GeoPrimePell
import Mathlib

/-! GEO-PRIME-GEOM-003: geometry is a candidate relation, and primality is
the previously verified independent multiplicative-irreducibility property. -/
namespace MAPEOGEOFormal.GeoPrimeGeometry

def GeometricCandidate (n c : Nat) : Prop :=
  n^2 + (n+1)^2 = c^2

theorem candidate_prime_iff_irreducible (n c : Nat)
    (_h : GeometricCandidate n c) :
    Nat.Prime c ↔ GeoEuler.RelationallyIrreducible c := by
  exact (GeoEuler.relationallyIrreducible_iff_prime c).symm

theorem prime_geometric_examples :
    Nat.Prime 5 ∧ Nat.Prime 29 := by
  norm_num

theorem primitive_composite_not_prime :
    GeometricCandidate 119 169 ∧
    ¬ GeoEuler.RelationallyIrreducible 169 := by
  constructor
  · norm_num [GeometricCandidate]
  · intro h
    have hp : Nat.Prime 169 :=
      (GeoEuler.relationallyIrreducible_iff_prime 169).mp h
    norm_num at hp

theorem nonsquare_composite_not_prime :
    GeometricCandidate 696 985 ∧
    ¬ GeoEuler.RelationallyIrreducible 985 := by
  constructor
  · norm_num [GeometricCandidate]
  · intro h
    have hp : Nat.Prime 985 :=
      (GeoEuler.relationallyIrreducible_iff_prime 985).mp h
    norm_num at hp

end MAPEOGEOFormal.GeoPrimeGeometry

#print axioms MAPEOGEOFormal.GeoPrimeGeometry.candidate_prime_iff_irreducible
#print axioms MAPEOGEOFormal.GeoPrimeGeometry.primitive_composite_not_prime
