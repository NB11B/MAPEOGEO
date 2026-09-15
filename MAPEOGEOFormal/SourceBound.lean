import Mathlib

namespace MAPEOGEOFormal

/-- Source-bound formal contract for Gallier–Quaintance Theorem 6.16. -/
theorem theorem_6_16_rank_nullity
    {K V W : Type*}
    [DivisionRing K]
    [AddCommGroup V] [Module K V]
    [AddCommGroup W] [Module K W]
    [FiniteDimensional K V]
    (f : V →ₗ[K] W) :
    Module.finrank K (LinearMap.range f) +
        Module.finrank K (LinearMap.ker f) = Module.finrank K V := by
  exact LinearMap.finrank_range_add_finrank_ker f

/-- Source-bound formal scope for Gallier–Quaintance Definition 44.6. -/
theorem definition_44_6_two_point_convex_interval
    (x y t : ℝ) (ht0 : 0 ≤ t) (ht1 : t ≤ 1) :
    min x y ≤ t * x + (1 - t) * y ∧
      t * x + (1 - t) * y ≤ max x y := by
  rcases le_total x y with hxy | hyx
  · rw [min_eq_left hxy, max_eq_right hxy]
    constructor <;> nlinarith
  · rw [min_eq_right hyx, max_eq_left hyx]
    constructor <;> nlinarith

/-- Source-bound scoped formal contract for Gallier–Quaintance Theorem 47.9. -/
theorem theorem_47_9_one_dim_positive_lp
    (a b c : ℝ) (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    ∃ xstar : ℝ,
      0 ≤ xstar ∧ a * xstar ≤ b ∧
        ∀ x : ℝ, 0 ≤ x → a * x ≤ b → c * x ≤ c * xstar := by
  refine ⟨b / a, div_nonneg hb (le_of_lt ha), ?_, ?_⟩
  · have hane : a ≠ 0 := ne_of_gt ha
    have hEq : a * (b / a) = b := by
      field_simp [hane]
    exact le_of_eq hEq
  · intro x hx hfeas
    have hxle : x ≤ b / a := by
      apply (le_div_iff₀ ha).2
      simpa [mul_comm] using hfeas
    exact mul_le_mul_of_nonneg_left hxle hc

/-- Source-bound formal identity for Gallier–Quaintance Definition 53.4. -/
theorem definition_53_4_gaussian_exponent_identity
    (x y σ : ℝ) (hσ : σ ≠ 0) :
    -((x - y) ^ 2) / (2 * σ ^ 2) =
      (x * y) / (σ ^ 2) - x ^ 2 / (2 * σ ^ 2) - y ^ 2 / (2 * σ ^ 2) := by
  field_simp [hσ]
  ring

#print axioms theorem_6_16_rank_nullity
#print axioms definition_44_6_two_point_convex_interval
#print axioms theorem_47_9_one_dim_positive_lp
#print axioms definition_53_4_gaussian_exponent_identity

end MAPEOGEOFormal
