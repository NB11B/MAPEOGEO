import Mathlib

/-! GEO-PRIME-GEOM-001: geometric admissibility does not imply primality. -/
namespace MAPEOGEOFormal.GeoPrimeGeometry

theorem consecutive_square_identity (n : Nat) :
    n^2 + (n+1)^2 = 2*n^2 + 2*n + 1 := by ring

theorem primitive_composite_counterexample :
    119^2 + 120^2 = (169:Nat)^2 ∧
    Nat.Coprime 119 120 ∧
    ¬ Nat.Prime 169 := by
  norm_num [Nat.Coprime]

end MAPEOGEOFormal.GeoPrimeGeometry
#print axioms MAPEOGEOFormal.GeoPrimeGeometry.primitive_composite_counterexample
