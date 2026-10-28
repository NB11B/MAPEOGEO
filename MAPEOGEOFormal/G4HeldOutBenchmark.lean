import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith

/-!
# G4-HELDOUT-TRANSFER-001 — Held-Out Multi-Domain Mathematical Benchmark for G4 v3

A genuinely held-out 16-obligation Lean 4 mathematical benchmark (`T1`–`T12` positive theorems
and `F1`–`F4` negative controls) spanning four domains outside the profinite `ZHat` development
corpus (`G4ProfiniteZHat.lean`):

1. **Family A (`T1`–`T4`) — Quotient Ring Morphisms & Equivariant Algebra**:
   - `T1_quotient_ringhom_subsingleton_unique`: Universal uniqueness of ring homomorphisms out of `ZMod m`.
   - `T2_ringhom_difference_of_squares_equivariance`: Equivariant transport of difference-of-squares factorization.
   - `T3_ringhom_local_inverse_transfer`: Equivariant uniqueness of multiplicative inverses across ring homomorphisms.
   - `T4_ringhom_idempotent_image_preserved`: Preservation of idempotent elements under semiring homomorphisms.

2. **Family B (`T5`–`T8`) — Divisibility Poset & Archimedean Intersection Principles**:
   - `T5_poset_dvd_antisymm_eq`: Antisymmetry of the divisibility poset on `ℕ`.
   - `T6_poset_dvd_scale_trans`: Coherent multiplicative scaling along the divisibility poset.
   - `T7_archimedean_dvd_upper_bound`: Archimedean upper bound `d ≤ n` for divisors of `n > 0`.
   - `T8_archimedean_universal_dvd_zero`: Intersection of all positive principal ideals in `ℕ` is `{0}`.

3. **Family C (`T9`–`T12`) — Integer-to-Modular Separation, Guarded Fibers & Convex Bounds**:
   - `T9_archimedean_zmod_cast_injective`: Separation of integers by finite modular projections `ZMod n` (`n > 0`).
   - `T10_guarded_positive_fiber_cast`: Compatibility of zero-guarded piecewise integer casts across `ZMod.castHom`.
   - `T11_barycentric_convex_interval_bound`: Homogeneous barycentric convex interval containment in `ℤ`.
   - `T12_crt_coprime_mod6_reconstruction`: Chinese Remainder fiber injectivity for coprime moduli `2 ∣ 6` and `3 ∣ 6`.

4. **Family D (`F1`–`F4`) — Held-Out Negative Controls & Obstructions**:
   - `F1_noncoprime_crt_fiber_collision`: Failure of CRT fiber injectivity for non-coprime moduli `2 ∣ 8` and `4 ∣ 8`.
   - `F2_sub_archimedean_divisor_collapse`: Collapse to zero for divisibility below the Archimedean threshold (`n < m`).
   - `F3_composite_zero_divisor_non_domain`: Explicit `let`-bound zero-divisor obstruction in `ZMod 12`.
   - `F4_non_barycentric_extrapolation_counterexample`: Failure of convex upper bound when weight exceeds cap (`s < w`).
-/

namespace MAPEOGEOFormal.G4HeldOutBenchmark

/-- **T1 (`T1_quotient_ringhom_subsingleton_unique`)**:
Any two ring homomorphisms `ZMod m →+* ZMod k` agree pointwise by quotient universality. -/
theorem T1_quotient_ringhom_subsingleton_unique {k m : ℕ} (phi psi : ZMod m →+* ZMod k) (x : ZMod m) :
    phi x = psi x := by
  exact DFunLike.congr_fun (Subsingleton.elim _ _) _

/-- **T2 (`T2_ringhom_difference_of_squares_equivariance`)**:
Difference-of-squares factorization is preserved equivariantly by any commutative ring homomorphism. -/
theorem T2_ringhom_difference_of_squares_equivariance {R S : Type*} [CommRing R] [CommRing S]
    (phi : R →+* S) (a b : R) :
    phi (a * a - b * b) = (phi a - phi b) * (phi a + phi b) := by
  simp only [map_sub, map_mul]; ring

/-- **T3 (`T3_ringhom_local_inverse_transfer`)**:
If `u * v = 1` in `R` and `phi u * w = 1` in `S`, then `phi v = w`. -/
theorem T3_ringhom_local_inverse_transfer {R S : Type*} [CommRing R] [CommRing S]
    (phi : R →+* S) (u v : R) (w : S) (h_uv : u * v = 1) (h_fw : phi u * w = 1) :
    phi v = w := by
  have H_lem : ∀ {A B : Type _} [CommRing A] [CommRing B] {f : A →+* B} {x y : A} {z : B},
      f x * z = 1 → x * y = 1 → f y = z := by
    intro A B _ _ f x y z hw hu
    have hm : f x * f y = 1 := by rw [← map_mul, hu, map_one]
    calc f y = f y * 1 := (mul_one _).symm
      _ = f y * (f x * z) := by rw [hw]
      _ = (f x * f y) * z := by ring
      _ = 1 * z := by rw [hm]
      _ = z := one_mul _
  apply H_lem <;> assumption

/-- **T4 (`T4_ringhom_idempotent_image_preserved`)**:
Every semiring homomorphism preserves idempotent elements (`e * e = e → phi e * phi e = phi e`). -/
theorem T4_ringhom_idempotent_image_preserved {R S : Type*} [Semiring R] [Semiring S]
    (phi : R →+* S) (e : R) (h_idem : e * e = e) :
    phi e * phi e = phi e := by
  rw [← map_mul, ‹_ * _ = _›]

/-- **T5 (`T5_poset_dvd_antisymm_eq`)**:
Antisymmetry of the divisibility relation on natural numbers. -/
theorem T5_poset_dvd_antisymm_eq (a b : ℕ) (hab : a ∣ b) (hba : b ∣ a) :
    a = b := by
  apply Nat.dvd_antisymm <;> assumption

/-- **T6 (`T6_poset_dvd_scale_trans`)**:
Divisibility is preserved under right multiplication along the poset (`d ∣ m → d ∣ m * k`). -/
theorem T6_poset_dvd_scale_trans (d m k : ℕ) (hdm : d ∣ m) :
    d ∣ m * k := by
  exact dvd_trans ‹_ ∣ _› (dvd_mul_right _ _)

/-- **T7 (`T7_archimedean_dvd_upper_bound`)**:
Every divisor `d` of a positive natural number `n > 0` satisfies the Archimedean bound `d ≤ n`. -/
theorem T7_archimedean_dvd_upper_bound (d n : ℕ) (hn : 0 < n) (hdn : d ∣ n) :
    d ≤ n := by
  by_contra; have := flip Nat.le_of_dvd ‹_ ∣ _› (by omega); omega

/-- **T8 (`T8_archimedean_universal_dvd_zero`)**:
A natural number divisible by every positive modulus `n > 0` is zero. -/
theorem T8_archimedean_universal_dvd_zero (k : ℕ) (h_all : ∀ n : ℕ, 0 < n → n ∣ k) :
    k = 0 := by
  by_contra
  have := (fun {m : ℕ} (H : ∀ n : ℕ, 0 < n → n ∣ m) => H (m + 1) (Nat.succ_pos m)) ‹_›
  have := flip Nat.le_of_dvd ‹_ ∣ _› (by omega)
  omega

/-- **T9 (`T9_archimedean_zmod_cast_injective`)**:
Two integers whose canonical projections agree in `ZMod n` for every `n > 0` are equal. -/
theorem T9_archimedean_zmod_cast_injective (a b : ℤ)
    (h_congr : ∀ n : ℕ, 0 < n → (a : ZMod n) = (b : ZMod n)) :
    a = b := by
  have H_lem : ∀ {x y : ℤ}, (∀ n : ℕ, 0 < n → (x : ZMod n) = (y : ZMod n)) → x = y := by
    intro x y H
    by_contra h_ne
    let n : ℕ := (x - y).natAbs + 1
    have hn : 0 < n := Nat.succ_pos _
    have h_sub : ((x - y : ℤ) : ZMod n) = 0 := by rw [Int.cast_sub, H n hn, sub_self]
    have h_dvd : n ∣ (x - y).natAbs :=
      Int.natCast_dvd.mp ((ZMod.intCast_zmod_eq_zero_iff_dvd (x - y) n).mp h_sub)
    have h_pos : 0 < (x - y).natAbs := Int.natAbs_pos.mpr (sub_ne_zero.mpr h_ne)
    have := Nat.le_of_dvd h_pos h_dvd
    omega
  exact H_lem ‹_›

/-- **T10 (`T10_guarded_positive_fiber_cast`)**:
Zero-guarded modular integer casts commute with `ZMod.castHom` on positive moduli `0 < m, 0 < n`. -/
theorem T10_guarded_positive_fiber_cast {m n : ℕ} (hm : 0 < m) (hn : 0 < n) (hmn : m ∣ n) (z : ℤ) :
    ZMod.castHom hmn (ZMod m) (if n = 0 then (0 : ZMod n) else (z : ZMod n)) =
      (if m = 0 then (0 : ZMod m) else (z : ZMod m)) := by
  simp_all [Nat.ne_of_gt, map_intCast]

/-- **T11 (`T11_barycentric_convex_interval_bound`)**:
Homogeneous barycentric combination `(s - w) * x + w * y` lies between `s * x` and `s * y`
whenever `x ≤ y` and `0 ≤ w ≤ s`. -/
theorem T11_barycentric_convex_interval_bound (x y w s : ℤ)
    (hxy : x ≤ y) (hw0 : 0 ≤ w) (hws : w ≤ s) :
    s * x ≤ (s - w) * x + w * y ∧ (s - w) * x + w * y ≤ s * y := by
  constructor <;> nlinarith

/-- **T12 (`T12_crt_coprime_mod6_reconstruction`)**:
Agreement of `ZMod 2` and `ZMod 3` quotient projections uniquely determines elements of `ZMod 6`. -/
theorem T12_crt_coprime_mod6_reconstruction :
    ∀ x y : ZMod 6,
      ZMod.castHom (show 2 ∣ 6 by decide) (ZMod 2) x = ZMod.castHom (show 2 ∣ 6 by decide) (ZMod 2) y →
      ZMod.castHom (show 3 ∣ 6 by decide) (ZMod 3) x = ZMod.castHom (show 3 ∣ 6 by decide) (ZMod 3) y →
      x = y := by
  decide

/-- **Negative Control F1 (`F1_noncoprime_crt_fiber_collision`)**:
Non-coprime quotient projections (`ZMod 2` and `ZMod 4`) fail to separate distinct elements of `ZMod 8`. -/
theorem F1_noncoprime_crt_fiber_collision :
    ¬ (∀ x y : ZMod 8,
      ZMod.castHom (show 2 ∣ 8 by decide) (ZMod 2) x = ZMod.castHom (show 2 ∣ 8 by decide) (ZMod 2) y →
      ZMod.castHom (show 4 ∣ 8 by decide) (ZMod 4) x = ZMod.castHom (show 4 ∣ 8 by decide) (ZMod 4) y →
      x = y) := by
  decide

/-- **Negative Control F2 (`F2_sub_archimedean_divisor_collapse`)**:
No positive integer can be divisible by a strictly larger modulus (`m ∣ n ∧ n < m → n = 0`). -/
theorem F2_sub_archimedean_divisor_collapse (m n : ℕ) (hmn : m ∣ n) (hlt : n < m) :
    n = 0 := by
  by_contra; have := flip Nat.le_of_dvd ‹_ ∣ _› (by omega); omega

/-- **Negative Control F3 (`F3_composite_zero_divisor_non_domain`)**:
Explicit `let`-bound zero-divisor witness in composite modulus `ZMod 12` (`3 * 4 = 0`). -/
theorem F3_composite_zero_divisor_non_domain :
    let a : ZMod 12 := 3
    let b : ZMod 12 := 4
    a ≠ 0 ∧ b ≠ 0 ∧ a * b = 0 := by
  decide

/-- **Negative Control F4 (`F4_non_barycentric_extrapolation_counterexample`)**:
When weight `w` exceeds cap `s` (`s < w`), the upper convex interval bound fails. -/
theorem F4_non_barycentric_extrapolation_counterexample :
    ∃ x y w s : ℤ, x ≤ y ∧ 0 ≤ s ∧ s < w ∧ ¬ ((s - w) * x + w * y ≤ s * y) := by
  refine ⟨0, 1, 2, 1, ?_⟩; omega

#print axioms T1_quotient_ringhom_subsingleton_unique
#print axioms T2_ringhom_difference_of_squares_equivariance
#print axioms T3_ringhom_local_inverse_transfer
#print axioms T4_ringhom_idempotent_image_preserved
#print axioms T5_poset_dvd_antisymm_eq
#print axioms T6_poset_dvd_scale_trans
#print axioms T7_archimedean_dvd_upper_bound
#print axioms T8_archimedean_universal_dvd_zero
#print axioms T9_archimedean_zmod_cast_injective
#print axioms T10_guarded_positive_fiber_cast
#print axioms T11_barycentric_convex_interval_bound
#print axioms T12_crt_coprime_mod6_reconstruction
#print axioms F1_noncoprime_crt_fiber_collision
#print axioms F2_sub_archimedean_divisor_collapse
#print axioms F3_composite_zero_divisor_non_domain
#print axioms F4_non_barycentric_extrapolation_counterexample

end MAPEOGEOFormal.G4HeldOutBenchmark
