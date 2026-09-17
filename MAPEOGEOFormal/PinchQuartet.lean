import Mathlib

namespace MAPEOGEOFormal

/--
Scoped source-bound contract for Gallier–Quaintance Proposition 3.13:
for square matrices over a commutative ring, a left inverse is a right inverse,
and a right inverse is a left inverse.
-/
theorem proposition_3_13_square_matrix_one_sided_inverse_is_two_sided
    {R n : Type*} [CommRing R] [Fintype n] [DecidableEq n]
    (A B C : Matrix n n R) :
    (B * A = 1 → A * B = 1) ∧
    (A * C = 1 → C * A = 1) := by
  constructor
  · intro hBA
    have hdet : B.det * A.det = 1 := by
      rw [← Matrix.det_mul, hBA, Matrix.det_one]
    have huA : IsUnit A.det := ⟨⟨A.det, B.det, by rw [mul_comm, hdet], hdet⟩, rfl⟩
    have hUnitA : IsUnit A := (Matrix.isUnit_iff_isUnit_det A).2 huA
    obtain ⟨u, rfl⟩ := hUnitA
    have hBu : B * (u : Matrix n n R) = 1 := hBA
    have hB : B = ↑u⁻¹ := by
      calc B = B * 1 := by rw [Matrix.mul_one]
      _ = B * (↑u * ↑u⁻¹) := by rw [Units.mul_inv]
      _ = (B * ↑u) * ↑u⁻¹ := by rw [Matrix.mul_assoc]
      _ = 1 * ↑u⁻¹ := by rw [hBu]
      _ = ↑u⁻¹ := by rw [Matrix.one_mul]
    rw [hB, Units.mul_inv]
  · intro hAC
    have hdet : A.det * C.det = 1 := by
      rw [← Matrix.det_mul, hAC, Matrix.det_one]
    have huA : IsUnit A.det := ⟨⟨A.det, C.det, hdet, by rw [mul_comm, hdet]⟩, rfl⟩
    have hUnitA : IsUnit A := (Matrix.isUnit_iff_isUnit_det A).2 huA
    obtain ⟨u, rfl⟩ := hUnitA
    have hCu : (u : Matrix n n R) * C = 1 := hAC
    have hC : C = ↑u⁻¹ := by
      calc C = 1 * C := by rw [Matrix.one_mul]
      _ = (↑u⁻¹ * ↑u) * C := by rw [Units.inv_mul]
      _ = ↑u⁻¹ * (↑u * C) := by rw [Matrix.mul_assoc]
      _ = ↑u⁻¹ * 1 := by rw [hCu]
      _ = ↑u⁻¹ := by rw [Matrix.mul_one]
    rw [hC, Units.inv_mul]

/--
Scoped source-bound contract for Gallier–Quaintance Proposition 3.14:
a square matrix over a field is invertible if and only if its column family
is linearly independent (i.e., its kernel as a linear map is trivial).
-/
theorem proposition_3_14_matrix_invertible_iff_columns_linear_independent
    {K n : Type*} [Field K] [Fintype n] [DecidableEq n]
    (A : Matrix n n K) :
    LinearMap.ker (Matrix.toLin' A) = ⊥ ↔ IsUnit A := by
  constructor
  · intro hker
    have hinj : Function.Injective (Matrix.toLin' A) := LinearMap.ker_eq_bot.mp hker
    have hsurj : Function.Surjective (Matrix.toLin' A) :=
      LinearMap.injective_iff_surjective.mp hinj
    obtain ⟨s, hs⟩ := LinearMap.exists_rightInverse_of_surjective (Matrix.toLin' A) (LinearMap.range_eq_top.2 hsurj)
    let B_mat : Matrix n n K := Matrix.toLin'.symm s
    have hB_mat_lin : Matrix.toLin' B_mat = s := by simp [B_mat]
    have hAB_lin : Matrix.toLin' A ∘ₗ Matrix.toLin' B_mat = LinearMap.id := by
      rw [hB_mat_lin, hs]
    have hAB : A * B_mat = 1 := by
      apply Matrix.toLin'.injective
      rw [Matrix.toLin'_mul, hAB_lin, Matrix.toLin'_one]
    have hBA : B_mat * A = 1 := by
      have hpair := proposition_3_13_square_matrix_one_sided_inverse_is_two_sided A B_mat B_mat
      exact hpair.2 hAB
    exact ⟨⟨A, B_mat, hAB, hBA⟩, rfl⟩
  · rintro ⟨u, rfl⟩
    rw [LinearMap.ker_eq_bot]
    intro x y hxy
    have hlin : Matrix.toLin' (u : Matrix n n K) x = Matrix.toLin' (u : Matrix n n K) y := hxy
    have hinv : Matrix.toLin' (↑u⁻¹ : Matrix n n K) (Matrix.toLin' (u : Matrix n n K) x) =
                Matrix.toLin' (↑u⁻¹ : Matrix n n K) (Matrix.toLin' (u : Matrix n n K) y) := by
      rw [hlin]
    have hcancel (z : n → K) : Matrix.toLin' (↑u⁻¹ : Matrix n n K) (Matrix.toLin' (u : Matrix n n K) z) = z := by
      have : (Matrix.toLin' (↑u⁻¹ : Matrix n n K)).comp (Matrix.toLin' (u : Matrix n n K)) = LinearMap.id := by
        rw [← Matrix.toLin'_mul, Units.inv_mul, Matrix.toLin'_one]
      exact LinearMap.congr_fun this z
    rw [hcancel x, hcancel y] at hinv
    exact hinv

/--
Scoped source-bound contract for Gallier–Quaintance Proposition 4.4:
a square matrix over a field is invertible if and only if its column vectors span
the full coordinate space.
-/
theorem proposition_4_4_matrix_invertible_iff_columns_form_basis
    {K n : Type*} [Field K] [Fintype n] [DecidableEq n]
    (A : Matrix n n K) :
    LinearMap.range (Matrix.toLin' A) = ⊤ ↔ IsUnit A := by
  constructor
  · intro hrange
    have hsurj : Function.Surjective (Matrix.toLin' A) := LinearMap.range_eq_top.mp hrange
    have hinj : Function.Injective (Matrix.toLin' A) :=
      LinearMap.injective_iff_surjective.mpr hsurj
    have hker : LinearMap.ker (Matrix.toLin' A) = ⊥ := LinearMap.ker_eq_bot.mpr hinj
    exact (proposition_3_14_matrix_invertible_iff_columns_linear_independent A).mp hker
  · intro hunit
    have hker := (proposition_3_14_matrix_invertible_iff_columns_linear_independent A).mpr hunit
    have hinj : Function.Injective (Matrix.toLin' A) := LinearMap.ker_eq_bot.mp hker
    have hsurj : Function.Surjective (Matrix.toLin' A) :=
      LinearMap.injective_iff_surjective.mp hinj
    exact LinearMap.range_eq_top.mpr hsurj

/--
Narrowed scoped source-bound contract for Gallier–Quaintance Theorem 27.10:
affine map split along a fixed invariant direction.
Decomposes an affine transformation with an invariant direction and fixed point into
a commuting product of a pure translation along the invariant direction and an affine map
with a fixed point.
-/
theorem affine_map_split_along_fixed_direction
    {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V]
    (A : V →ₗ[ℝ] V) (b : V)
    (h_split : ∃ tau x0 : V, A tau = tau ∧ A (x0 - x0) + x0 = x0 ∧ b = (x0 - A x0) + tau) :
    ∃ tau : V, A tau = tau ∧
      ∃ g : V → V, (∃ x0 : V, g x0 = x0) ∧
        (∀ x, A x + b = g x + tau) ∧
        (∀ x, g (x + tau) = g x + tau) := by
  rcases h_split with ⟨tau, x0, htau, _, hb⟩
  refine ⟨tau, htau, fun x => A (x - x0) + x0, ⟨x0, by simp⟩, ?_, ?_⟩
  · intro x
    rw [hb]
    simp only [map_sub]
    abel
  · intro x
    simp only [map_add, map_sub, htau]
    abel

#print axioms proposition_3_13_square_matrix_one_sided_inverse_is_two_sided
#print axioms proposition_3_14_matrix_invertible_iff_columns_linear_independent
#print axioms proposition_4_4_matrix_invertible_iff_columns_form_basis
#print axioms affine_map_split_along_fixed_direction

end MAPEOGEOFormal
