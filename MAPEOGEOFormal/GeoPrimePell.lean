import Mathlib

/-! GEO-PRIME-GEOM-002: exact algebraic norm preservation for the proposed generator. -/
namespace MAPEOGEOFormal.GeoPrimeGeometry

theorem pell_transform_preserves (x c : ℤ) :
    (3*x+4*c)^2 - 2*(2*x+3*c)^2 = x^2 - 2*c^2 := by
  ring

theorem consecutive_triangle_identity (n : ℕ) :
    n^2 + (n+1)^2 = 2*n^2 + 2*n + 1 := by
  ring

theorem primitive_composite_hypotenuse :
    (119:ℕ)^2 + 120^2 = 169^2 ∧
    Nat.Coprime 119 120 ∧ ¬ Nat.Prime 169 := by
  norm_num [Nat.Coprime]

end MAPEOGEOFormal.GeoPrimeGeometry

#print axioms MAPEOGEOFormal.GeoPrimeGeometry.pell_transform_preserves
#print axioms MAPEOGEOFormal.GeoPrimeGeometry.primitive_composite_hypotenuse
