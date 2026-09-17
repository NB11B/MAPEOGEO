import Mathlib

namespace MAPEOGEOFormal

/--
Scoped source-bound formalization for Gallier–Quaintance Proposition 3.14 (v0.11):
Unique linear coordinate representation with respect to a basis.
For any basis `b` of module `M` over ring `R`, every vector `x : M`
has a unique representation as a linear combination of basis vectors via coordinates.
-/
theorem proposition_3_14_v011
    {R M ι : Type*} [CommRing R] [AddCommGroup M] [Module R M]
    (b : Module.Basis ι R M) (x : M) :
    ∃! (c : ι →₀ R), b.repr.symm c = x := by
  refine ⟨b.repr x, ?_, ?_⟩
  · exact b.repr.symm_apply_apply x
  · intro c hc
    rw [← hc]
    exact (b.repr.apply_symm_apply c).symm

/--
Scoped source-bound formalization for Gallier–Quaintance Proposition 3.13 (v0.11):
Linear independence characterization for indexed vector families.
A family of vectors `v : Fin (n + 1) → V` over a division ring `K` is linearly independent
if and only if the tail family `Fin.tail v` is linearly independent and the first vector
`v 0` is not in the span of the tail family.
-/
theorem proposition_3_13_v011
    {K V : Type*} [DivisionRing K] [AddCommGroup V] [Module K V]
    {n : ℕ} (v : Fin (n + 1) → V) :
    LinearIndependent K v ↔
      LinearIndependent K (Fin.tail v) ∧ v 0 ∉ Submodule.span K (Set.range (Fin.tail v)) :=
  linearIndependent_finSucc

/--
Narrowed scoped source-bound formalization for Gallier–Quaintance Theorem 27.10 (v0.11):
Affine map split along a fixed invariant direction.
An affine map with linear part `A` and translation `b` decomposes into a translation
along an invariant vector `tau` and an affine map `g` possessing a fixed point.
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

/--
Scoped source-bound formalization for Gallier–Quaintance Proposition 4.4 (v0.11):
Internal direct sum disjoint kernel criterion.
Two submodules `p, q` of module `M` have trivial intersection (are disjoint)
if and only if the coproduct addition map `p × q → M` has trivial kernel.
-/
theorem proposition_4_4_v011
    {R M : Type*} [Ring R] [AddCommGroup M] [Module R M]
    (p q : Submodule R M) :
    Disjoint p q ↔ LinearMap.ker (p.subtype.coprod q.subtype) = ⊥ := by
  constructor
  · intro hdisj
    rw [Submodule.disjoint_def] at hdisj
    rw [LinearMap.ker_eq_bot]
    intro ⟨x1, y1⟩ ⟨x2, y2⟩ heq
    simp only [LinearMap.coprod_apply, Submodule.subtype_apply] at heq
    have heq2 : (x1 : M) + (y1 : M) = (x2 : M) + (y2 : M) := heq
    have hdiff : (x1 : M) - (x2 : M) = (y2 : M) - (y1 : M) := by
      calc (x1 : M) - (x2 : M) = (x1 : M) + (y1 : M) - (x2 : M) - (y1 : M) := by abel
      _ = (x2 : M) + (y2 : M) - (x2 : M) - (y1 : M) := by rw [heq2]
      _ = (y2 : M) - (y1 : M) := by abel
    have hx_mem : (x1 : M) - (x2 : M) ∈ p := Submodule.sub_mem p x1.property x2.property
    have hy_mem : (y2 : M) - (y1 : M) ∈ q := Submodule.sub_mem q y2.property y1.property
    have hx_in_q : (x1 : M) - (x2 : M) ∈ q := by rw [hdiff]; exact hy_mem
    have hzero : (x1 : M) - (x2 : M) = 0 := hdisj ((x1 : M) - (x2 : M)) hx_mem hx_in_q
    have hx_eq : x1 = x2 := Subtype.ext (sub_eq_zero.mp hzero)
    have hy_zero : (y2 : M) - (y1 : M) = 0 := by rw [← hdiff, hzero]
    have hy_eq : y1 = y2 := Subtype.ext (by
      have hneg : (y1 : M) - (y2 : M) = 0 := by
        calc (y1 : M) - (y2 : M) = -((y2 : M) - (y1 : M)) := by abel
        _ = -0 := by rw [hy_zero]
        _ = 0 := neg_zero
      exact sub_eq_zero.mp hneg)
    exact Prod.ext hx_eq hy_eq
  · intro hker
    rw [Submodule.disjoint_def]
    intro x hxp hxq
    let z : p × q := (⟨x, hxp⟩, ⟨-x, Submodule.neg_mem q hxq⟩)
    have heq : (p.subtype.coprod q.subtype) z = 0 := by
      change (⟨x, hxp⟩ : p).1 + (⟨-x, Submodule.neg_mem q hxq⟩ : q).1 = 0
      simp only [add_neg_cancel]
    have hmem : z ∈ LinearMap.ker (p.subtype.coprod q.subtype) := by
      rw [LinearMap.mem_ker]
      exact heq
    rw [hker, Submodule.mem_bot] at hmem
    have hx0 : (⟨x, hxp⟩ : p) = 0 := Prod.ext_iff.mp hmem |>.1
    exact Subtype.ext_iff.mp hx0

#print axioms proposition_3_14_v011
#print axioms proposition_3_13_v011
#print axioms affine_map_split_along_fixed_direction
#print axioms proposition_4_4_v011

end MAPEOGEOFormal
