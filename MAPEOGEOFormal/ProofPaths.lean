import Mathlib
import MAPEOGEOFormal.SourceBound

namespace MAPEOGEOFormal

/--
Scoped source-bound contract for Gallier–Quaintance Lemma 3.6:
adjoining a vector outside the span of an independent set preserves linear independence.
-/
theorem lemma_3_6_insert_linear_independent
    {K E : Type*}
    [DivisionRing K] [AddCommGroup E] [Module K E]
    (S : Set E) (v : E)
    (hS : LinearIndepOn K id S)
    (hv : v ∉ Submodule.span K S) :
    LinearIndepOn K id (Set.insert v S) := by
  exact hS.id_insert hv

/--
Scoped source-bound contract for Gallier–Quaintance Theorem 3.7.
The set formulation is the basis-extension content needed by the S5 path.
-/
theorem theorem_3_7_basis_extension
    {K E : Type*}
    [DivisionRing K] [AddCommGroup E] [Module K E]
    (S L : Set E)
    (hL : LinearIndepOn K id L)
    (hLS : L ⊆ S)
    (hS : Submodule.span K S = ⊤) :
    ∃ B : Set E,
      L ⊆ B ∧ B ⊆ S ∧ LinearIndepOn K id B ∧ Submodule.span K B = ⊤ := by
  let B := hL.extend hLS
  refine ⟨B, hL.subset_extend hLS, hL.extend_subset hLS,
    hL.linearIndepOn_extend hLS, ?_⟩
  simpa [B, hS] using hL.span_extend_eq_span hLS

/--
Scoped source-bound contract for Gallier–Quaintance Proposition 3.15:
a basis determines a unique linear map from its values on basis vectors.
-/
theorem proposition_3_15_basis_determines_linear_map
    {K E F ι : Type*}
    [DivisionRing K]
    [AddCommGroup E] [Module K E]
    [AddCommGroup F] [Module K F]
    (b : Module.Basis ι K E) (v : ι → F) :
    ∃! f : E →ₗ[K] F, ∀ i, f (b i) = v i := by
  refine ⟨b.constr K v, ?_, ?_⟩
  · intro i
    exact b.constr_basis K v i
  · intro g hg
    apply b.ext
    intro i
    simpa using hg i

/--
Source-bound contract for Gallier–Quaintance Proposition 6.11:
an injective linear map admits a linear retraction and a surjective linear map admits a
linear section.
-/
theorem proposition_6_11_retraction_section
    {K E F : Type*}
    [DivisionRing K]
    [AddCommGroup E] [Module K E]
    [AddCommGroup F] [Module K F]
    (f : E →ₗ[K] F) :
    (Function.Injective f →
      ∃ r : F →ₗ[K] E, r.comp f = LinearMap.id) ∧
    (Function.Surjective f →
      ∃ s : F →ₗ[K] E, f.comp s = LinearMap.id) := by
  constructor
  · intro hf
    exact f.exists_leftInverse_of_injective (LinearMap.ker_eq_bot.mpr hf)
  · intro hf
    exact f.exists_rightInverse_of_surjective (LinearMap.range_eq_top.mpr hf)

/--
Scoped source-bound contract for Gallier–Quaintance Proposition 6.7.
A finite external direct sum, represented canonically as a finite product of module
components, has finrank equal to the sum of component finranks.
-/
theorem proposition_6_7_finite_direct_sum_finrank
    {K ι : Type*} [DivisionRing K] [Fintype ι]
    (M : ι → Type*)
    [∀ i, AddCommGroup (M i)] [∀ i, Module K (M i)]
    [∀ i, FiniteDimensional K (M i)] :
    Module.finrank K (∀ i, M i) = ∑ i, Module.finrank K (M i) := by
  exact Module.finrank_pi_fintype K

/--
Scoped source-bound contract for Gallier–Quaintance Proposition 6.15(a):
a linear section of a surjection splits the middle space as kernel plus section range.
-/
theorem proposition_6_15_section_split
    {K F G : Type*}
    [DivisionRing K]
    [AddCommGroup F] [Module K F]
    [AddCommGroup G] [Module K G]
    (g : F →ₗ[K] G) (s : G →ₗ[K] F)
    (hgs : g.comp s = LinearMap.id) :
    IsCompl (LinearMap.ker g) (LinearMap.range s) := by
  constructor
  · apply Submodule.disjoint_def.mpr
    intro x hxker hxrange
    rcases hxrange with ⟨y, rfl⟩
    have hzero : g (s y) = 0 := by
      simpa only [LinearMap.mem_ker] using hxker
    have hright : g (s y) = y := by
      simpa using LinearMap.congr_fun hgs y
    have hy : y = 0 := by
      calc
        y = g (s y) := hright.symm
        _ = 0 := hzero
    simp [hy]
  · rw [codisjoint_iff_le_sup]
    intro x _
    have hright : g (s (g x)) = g x := by
      simpa using LinearMap.congr_fun hgs (g x)
    have hk : x - s (g x) ∈ LinearMap.ker g := by
      rw [LinearMap.mem_ker]
      simp [hright]
    have hr : s (g x) ∈ LinearMap.range s := ⟨g x, rfl⟩
    have hks : x - s (g x) ∈ LinearMap.ker g ⊔ LinearMap.range s :=
      Submodule.mem_sup_left hk
    have hrs : s (g x) ∈ LinearMap.ker g ⊔ LinearMap.range s :=
      Submodule.mem_sup_right hr
    have hadd := Submodule.add_mem (LinearMap.ker g ⊔ LinearMap.range s) hks hrs
    simpa using hadd

#print axioms lemma_3_6_insert_linear_independent
#print axioms theorem_3_7_basis_extension
#print axioms proposition_3_15_basis_determines_linear_map
#print axioms proposition_6_11_retraction_section
#print axioms proposition_6_7_finite_direct_sum_finrank
#print axioms proposition_6_15_section_split

end MAPEOGEOFormal
