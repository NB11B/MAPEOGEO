import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith

/-!
# G4-PROFINITE-ZHAT-001 — Finite-to-Infinite Proof Transfer on $\widehat{\mathbb Z} = \varprojlim_{n > 0} \mathbb Z/n\mathbb Z$

Formalizes the inverse system of finite cyclic quotients $\mathbb Z/n\mathbb Z$ ordered by divisibility
$m \mid n$ (`m ∣ n`) for positive moduli $n > 0$, the profinite completion $\widehat{\mathbb Z}$ (`ZHat`),
the canonical ring structure, the faithful integer embedding $\iota : \mathbb Z \hookrightarrow \widehat{\mathbb Z}$,
automatic coherence of local multiplicative inverses across transition maps, the full finite-to-infinite
unit transfer characterization, the universal property of the inverse limit, and three formal negative
controls (`F1`, `F2`, `F3`) demonstrating why naive finite-to-infinite transfer fails without exact
poset and transition compatibility.
-/

namespace MAPEOGEOFormal.G4ProfiniteZHat

/-- Transition homomorphism $\pi_{n,m} : \mathbb Z/n\mathbb Z \to+* \mathbb Z/m\mathbb Z$ for $m \mid n$. -/
def transitionMap {m n : ℕ} (h : m ∣ n) : ZMod n →+* ZMod m :=
  ZMod.castHom h (ZMod m)

/-- **T1 (`T1_proj_refl`)**: Reflexivity of finite quotient transition maps $\pi_{n,n} = \mathrm{id}$. -/
theorem T1_proj_refl (n : ℕ) (x : ZMod n) :
    transitionMap (dvd_refl n) x = x := by
  unfold transitionMap
  have h_id : ZMod.castHom (dvd_refl n) (ZMod n) = RingHom.id (ZMod n) :=
    Subsingleton.elim _ _
  exact DFunLike.congr_fun h_id x

/-- **T2 (`T2_proj_trans`)**: Functoriality / transitivity of finite quotient transition maps:
for $k \mid m$ and $m \mid n$, $\pi_{m,k}(\pi_{n,m}(x)) = \pi_{n,k}(x)$. -/
theorem T2_proj_trans {k m n : ℕ} (hkm : k ∣ m) (hmn : m ∣ n) (x : ZMod n) :
    transitionMap hkm (transitionMap hmn x) = transitionMap (dvd_trans hkm hmn) x := by
  unfold transitionMap
  have h_comp :
      (ZMod.castHom hkm (ZMod k)).comp (ZMod.castHom hmn (ZMod m)) =
        ZMod.castHom (dvd_trans hkm hmn) (ZMod k) :=
    Subsingleton.elim _ _
  exact DFunLike.congr_fun h_comp x

/-- Compatibility predicate for a family of elements across positive finite quotients $\mathbb Z/n\mathbb Z$. -/
def IsCoherent (x : ∀ n : ℕ, ZMod n) : Prop :=
  ∀ ⦃m n : ℕ⦄, 0 < m → 0 < n → (h : m ∣ n) → transitionMap h (x n) = x m

/-- The profinite integers $\widehat{\mathbb Z} = \varprojlim_{n > 0} \mathbb Z/n\mathbb Z$,
bundled with the canonical anchor $x_0 = 0$ outside positive indices for extensionality. -/
structure ZHat where
  val : ∀ n : ℕ, ZMod n
  zero_anchor : val 0 = 0
  coherent : IsCoherent val

@[ext]
theorem ZHat.ext {x y : ZHat} (h : ∀ n : ℕ, 0 < n → x.val n = y.val n) : x = y := by
  cases x with
  | mk xv xz xc =>
    cases y with
    | mk yv yz yc =>
      simp only [mk.injEq]
      funext n
      cases n with
      | zero => exact xz.trans yz.symm
      | succ k => exact h (k + 1) (Nat.succ_pos k)

/-- **T3a (`T3_coherent_add`)**: Pointwise addition preserves inverse-system coherence. -/
theorem T3_coherent_add {x y : ∀ n : ℕ, ZMod n} (hx : IsCoherent x) (hy : IsCoherent y) :
    IsCoherent (fun n => x n + y n) := by
  intro m n hm hn hmn
  rw [map_add, hx hm hn hmn, hy hm hn hmn]

/-- **T3b (`T3_coherent_mul`)**: Pointwise multiplication preserves inverse-system coherence. -/
theorem T3_coherent_mul {x y : ∀ n : ℕ, ZMod n} (hx : IsCoherent x) (hy : IsCoherent y) :
    IsCoherent (fun n => x n * y n) := by
  intro m n hm hn hmn
  rw [map_mul, hx hm hn hmn, hy hm hn hmn]

/-- **T3c (`T3_coherent_neg`)**: Pointwise negation preserves inverse-system coherence. -/
theorem T3_coherent_neg {x : ∀ n : ℕ, ZMod n} (hx : IsCoherent x) :
    IsCoherent (fun n => -x n) := by
  intro m n hm hn hmn
  rw [map_neg, hx hm hn hmn]

/-- Pointwise addition on $\widehat{\mathbb Z}$. -/
def ZHat.add (x y : ZHat) : ZHat where
  val := fun n => if n = 0 then 0 else x.val n + y.val n
  zero_anchor := rfl
  coherent := by
    intro m n hm hn hmn
    have hm0 : m ≠ 0 := Nat.ne_of_gt hm
    have hn0 : n ≠ 0 := Nat.ne_of_gt hn
    simp only [hm0, hn0, ↓reduceIte, map_add]
    rw [x.coherent hm hn hmn, y.coherent hm hn hmn]

/-- Pointwise multiplication on $\widehat{\mathbb Z}$. -/
def ZHat.mul (x y : ZHat) : ZHat where
  val := fun n => if n = 0 then 0 else x.val n * y.val n
  zero_anchor := rfl
  coherent := by
    intro m n hm hn hmn
    have hm0 : m ≠ 0 := Nat.ne_of_gt hm
    have hn0 : n ≠ 0 := Nat.ne_of_gt hn
    simp only [hm0, hn0, ↓reduceIte, map_mul]
    rw [x.coherent hm hn hmn, y.coherent hm hn hmn]

/-- Multiplicative identity $1 \in \widehat{\mathbb Z}$. -/
def ZHat.one : ZHat where
  val := fun n => if n = 0 then 0 else 1
  zero_anchor := rfl
  coherent := by
    intro m n hm hn hmn
    have hm0 : m ≠ 0 := Nat.ne_of_gt hm
    have hn0 : n ≠ 0 := Nat.ne_of_gt hn
    simp only [hm0, hn0, ↓reduceIte, map_one]

/-- Additive identity $0 \in \widehat{\mathbb Z}$. -/
def ZHat.zero : ZHat where
  val := fun _ => 0
  zero_anchor := rfl
  coherent := by
    intro m n _ _ _
    exact map_zero _

/-- **T4 (`T4_int_embed_coherent`)**: Canonical integer embedding $\iota : \mathbb Z \to \widehat{\mathbb Z}$
is coherent across all divisibility transitions $m \mid n$. -/
theorem T4_int_embed_coherent (z : ℤ) :
    IsCoherent (fun n => if n = 0 then 0 else (z : ZMod n)) := by
  intro m n hm hn hmn
  have hm0 : m ≠ 0 := Nat.ne_of_gt hm
  have hn0 : n ≠ 0 := Nat.ne_of_gt hn
  simp only [hm0, hn0, ↓reduceIte, map_intCast]

/-- Canonical embedding $\iota : \mathbb Z \to \widehat{\mathbb Z}$. -/
def intToZHat (z : ℤ) : ZHat where
  val := fun n => if n = 0 then 0 else (z : ZMod n)
  zero_anchor := rfl
  coherent := T4_int_embed_coherent z

/-- **T5 (`T5_int_embed_injective`)**: Faithfulness of the finite-to-infinite embedding $\iota : \mathbb Z \hookrightarrow \widehat{\mathbb Z}$.
If $z$ and $w$ have identical projections in every finite quotient $\mathbb Z/n\mathbb Z$ ($n > 0$), then $z = w$ in $\mathbb Z$. -/
theorem T5_int_embed_injective {z w : ℤ} (h : intToZHat z = intToZHat w) : z = w := by
  -- Choose the adaptive finite witness modulus n = (z - w).natAbs + 1 > |z - w|
  let n : ℕ := (z - w).natAbs + 1
  have hn_pos : 0 < n := Nat.succ_pos (z - w).natAbs
  have hn_ne : n ≠ 0 := Nat.ne_of_gt hn_pos
  have h_proj : (intToZHat z).val n = (intToZHat w).val n := by rw [h]
  simp only [intToZHat, hn_ne, ↓reduceIte] at h_proj
  have h_sub : ((z - w : ℤ) : ZMod n) = 0 := by
    rw [Int.cast_sub, h_proj, sub_self]
  have h_dvd : (n : ℤ) ∣ (z - w) :=
    (ZMod.intCast_zmod_eq_zero_iff_dvd (z - w) n).mp h_sub
  have h_dvd_nat : n ∣ (z - w).natAbs := Int.natCast_dvd.mp h_dvd
  by_contra h_ne
  have h_abs_pos : 0 < (z - w).natAbs := Int.natAbs_pos.mpr (sub_ne_zero.mpr h_ne)
  have h_le : n ≤ (z - w).natAbs := Nat.le_of_dvd h_abs_pos h_dvd_nat
  omega

/-- **T6 (`T6_unit_projection_compat`)**: Any global inverse $v \in \widehat{\mathbb Z}$ of $u \in \widehat{\mathbb Z}$
yields a local inverse at every finite stage $n > 0$. -/
theorem T6_unit_projection_compat (u v : ZHat) (huv : ZHat.mul u v = ZHat.one)
    {n : ℕ} (hn : 0 < n) : u.val n * v.val n = 1 := by
  have h_at_n : (ZHat.mul u v).val n = ZHat.one.val n := by rw [huv]
  have hn0 : n ≠ 0 := Nat.ne_of_gt hn
  simp only [ZHat.mul, ZHat.one, hn0, ↓reduceIte] at h_at_n
  exact h_at_n

/-- **T7 (`T7_compatible_inverse_uniqueness`)**: Automatic Coherence of Pointwise Finite Inverses.
If $u \in \widehat{\mathbb Z}$ is coherent and $v : \forall n, \mathrm{ZMod}\, n$ satisfies $u_n \cdot v_n = 1$
at every finite stage $n > 0$ (without assuming $v$ is coherent a priori), then $v$ is automatically
coherent across all divisibility transitions $m \mid n$. -/
theorem T7_compatible_inverse_uniqueness (u : ZHat) (v : ∀ n : ℕ, ZMod n)
    (h_inv : ∀ n : ℕ, 0 < n → u.val n * v n = 1) :
    IsCoherent v := by
  intro m n hm hn hmn
  have h_un : u.val n * v n = 1 := h_inv n hn
  have h_um : u.val m * v m = 1 := h_inv m hm
  have h_mapped : transitionMap hmn (u.val n * v n) = transitionMap hmn 1 :=
    congrArg (transitionMap hmn) h_un
  rw [map_mul, map_one, u.coherent hm hn hmn] at h_mapped
  calc
    transitionMap hmn (v n)
      = transitionMap hmn (v n) * 1 := (mul_one _).symm
    _ = transitionMap hmn (v n) * (u.val m * v m) := by rw [h_um]
    _ = (u.val m * transitionMap hmn (v n)) * v m := by ring
    _ = 1 * v m := by rw [h_mapped]
    _ = v m := one_mul _

/-- **T8 (`T8_profinite_unit_characterization`)**: Full Finite-to-Infinite Unit Transfer Theorem.
An element $u \in \widehat{\mathbb Z}$ has a multiplicative inverse $v \in \widehat{\mathbb Z}$ ($u \cdot v = 1$)
if and only if every finite quotient projection $u_n \in \mathbb Z/n\mathbb Z$ ($n > 0$) has a local inverse. -/
theorem T8_profinite_unit_characterization (u : ZHat) :
    (∃ v : ZHat, ZHat.mul u v = ZHat.one) ↔
      (∀ n : ℕ, 0 < n → ∃ y : ZMod n, u.val n * y = 1) := by
  constructor
  · rintro ⟨v, huv⟩ n hn
    exact ⟨v.val n, T6_unit_projection_compat u v huv hn⟩
  · intro h_loc
    classical
    let raw_v : ∀ n : ℕ, ZMod n := fun n =>
      if hn : 0 < n then Classical.choose (h_loc n hn) else 0
    have h_raw_inv : ∀ n : ℕ, 0 < n → u.val n * raw_v n = 1 := by
      intro n hn
      dsimp [raw_v]
      rw [dif_pos hn]
      exact Classical.choose_spec (h_loc n hn)
    have h_coh : IsCoherent raw_v :=
      T7_compatible_inverse_uniqueness u raw_v h_raw_inv
    refine ⟨⟨raw_v, rfl, h_coh⟩, ?_⟩
    ext n hn
    have hn0 : n ≠ 0 := Nat.ne_of_gt hn
    simp only [ZHat.mul, ZHat.one, hn0, ↓reduceIte]
    exact h_raw_inv n hn

/-- **T9 (`T9_universal_compatible_lift`)**: Universal Property of $\widehat{\mathbb Z} = \varprojlim_{n > 0} \mathbb Z/n\mathbb Z$.
Every family of maps $f : (n : \mathbb N) \to \mathrm{ZMod}\, n$ that is coherent on positive moduli
lifts to a unique element $x \in \widehat{\mathbb Z}$ agreeing with $f$ at every finite stage $n > 0$. -/
theorem T9_universal_compatible_lift (f : ∀ n : ℕ, ZMod n) (hf : IsCoherent f) :
    ∃! x : ZHat, ∀ n : ℕ, 0 < n → x.val n = f n := by
  refine ⟨⟨fun n => if n = 0 then 0 else f n, rfl, ?_⟩, ?_, ?_⟩
  · intro m n hm hn hmn
    have hm0 : m ≠ 0 := Nat.ne_of_gt hm
    have hn0 : n ≠ 0 := Nat.ne_of_gt hn
    simp only [hm0, hn0, ↓reduceIte]
    exact hf hm hn hmn
  · intro n hn
    have hn0 : n ≠ 0 := Nat.ne_of_gt hn
    simp only [hn0, ↓reduceIte]
  · intro y hy
    ext n hn
    have hn0 : n ≠ 0 := Nat.ne_of_gt hn
    simp only [hn0, ↓reduceIte]
    exact hy n hn

/-- **Negative Control F1 (`F1_unrestricted_zero_modulus_collapse`)**:
If compatibility is imposed over *all* $n \in \mathbb N$ without the positive-modulus guard $n > 0$,
then because $m \mid 0$ for every $m \in \mathbb N$, every thread is uniquely determined by its $n = 0$
coordinate in $\mathrm{ZMod}\, 0 = \mathbb Z$. -/
theorem F1_unrestricted_zero_modulus_collapse (x : ∀ n : ℕ, ZMod n)
    (h_unrestricted : ∀ m n : ℕ, (h : m ∣ n) → transitionMap h (x n) = x m) (m : ℕ) :
    x m = transitionMap (dvd_zero m) (x 0) :=
  (h_unrestricted m 0 (dvd_zero m)).symm

/-- **Negative Control F2 (`F2_incoherent_pointwise_idempotent`)**:
A pointwise idempotent family in $\prod_{n > 0} \mathbb Z/n\mathbb Z$ ($e_2 = 1$, $e_4 = 0$) satisfies
$e_n * e_n = e_n$ at both $n = 2$ and $n = 4$ but violates inverse-limit compatibility along $2 \mid 4$. -/
theorem F2_incoherent_pointwise_idempotent :
    let e : ∀ n : ℕ, ZMod n := fun n => if n = 2 then 1 else 0
    (e 2 * e 2 = e 2) ∧ (e 4 * e 4 = e 4) ∧ ¬ IsCoherent e := by
  refine ⟨by decide, by decide, ?_⟩
  intro h_coh
  have h24 : (2 : ℕ) ∣ 4 := ⟨2, rfl⟩
  have h_eq := h_coh (by decide : 0 < 2) (by decide : 0 < 4) h24
  change transitionMap h24 0 = 1 at h_eq
  rw [map_zero] at h_eq
  exact zero_ne_one h_eq

/-- **Negative Control F3 (`F3_composite_idempotent_counterexample`)**:
Naive transfer of "only trivial idempotents ($e^2 = e \implies e = 0 \lor e = 1$)" from prime moduli
to composite moduli fails at $n = 6$ ($3^2 \equiv 3 \pmod 6$, $3 \not\equiv 0, 1 \pmod 6$). -/
theorem F3_composite_idempotent_counterexample :
    ∃ e : ZMod 6, e * e = e ∧ e ≠ 0 ∧ e ≠ 1 := by
  refine ⟨3, ?_, ?_, ?_⟩ <;> decide

#print axioms T1_proj_refl
#print axioms T2_proj_trans
#print axioms T3_coherent_add
#print axioms T3_coherent_mul
#print axioms T3_coherent_neg
#print axioms T4_int_embed_coherent
#print axioms T5_int_embed_injective
#print axioms T6_unit_projection_compat
#print axioms T7_compatible_inverse_uniqueness
#print axioms T8_profinite_unit_characterization
#print axioms T9_universal_compatible_lift
#print axioms F1_unrestricted_zero_modulus_collapse
#print axioms F2_incoherent_pointwise_idempotent
#print axioms F3_composite_idempotent_counterexample

end MAPEOGEOFormal.G4ProfiniteZHat
