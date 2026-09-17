import Mathlib

/-!
# Wave F4: Quantified Real Analysis Formal Theorems (Jiří Lebl v6.3 & ReasBook Alignment)

Formalizes the source-bound real analysis theorems aligned with Jiří Lebl, *Basic Analysis I*,
Volume I, v6.3 (2026), documenting explicit alignment with the ReasBook Lean project (v6.2).
-/

namespace MAPEOGEOFormal.WaveF4

open Set Filter Topology

-- 1. Ordered Field Structure (Lebl §1.1 / ReasBook §1.1)
theorem OrderedField (x y z : ℝ) (h : x < y) (hx : 0 < x) (hy : 0 < y) :
    x + z < y + z ∧ 0 < x * y := by
  constructor
  · linarith
  · exact mul_pos hx hy

-- 2. Absolute Value Inequalities & Triangle Inequality (Lebl §1.1 Prop 1.1.13)
theorem AbsValTriangleIneq (x y : ℝ) :
    |x + y| ≤ |x| + |y| ∧ |abs x - abs y| ≤ |x - y| := by
  constructor
  · exact abs_add_le x y
  · exact abs_abs_sub_abs_le_abs_sub x y

-- 3. Supremum and Infimum Epsilon Characterization (Lebl §1.2 Def 1.2.1)
theorem SupInfDef (s : Set ℝ) (hnonempty : s.Nonempty) (_hbd : BddAbove s) (eps : ℝ) (heps : 0 < eps) :
    ∃ x ∈ s, sSup s - eps < x := by
  exact exists_lt_of_lt_csSup hnonempty (sub_lt_self (sSup s) heps)

-- 4. Least Upper Bound Axiom / Property (Lebl §1.2 Axiom 1.2.3)
theorem LeastUpperBoundAxiom (s : Set ℝ) (_hnonempty : s.Nonempty) (hbd : BddAbove s) :
    ∀ x ∈ s, x ≤ sSup s := by
  intro x hx
  exact le_csSup hbd hx

-- 5. Archimedean Property of Reals (Lebl §1.2 Thm 1.2.5)
theorem ArchimedeanProperty (x : ℝ) (eps : ℝ) (heps : 0 < eps) :
    (∃ n : ℕ, x < (n : ℝ)) ∧ (∃ n : ℕ, 0 < n ∧ (1 : ℝ) / (n : ℝ) < eps) := by
  constructor
  · exact exists_nat_gt x
  · obtain ⟨n, hn⟩ := exists_nat_gt (1 / eps)
    have hn_pos : 0 < n := by
      by_contra hc
      have : n = 0 := by linarith
      subst this
      have : (0 : ℝ) < 1 / eps := one_div_pos.2 heps
      linarith
    refine ⟨n, hn_pos, ?_⟩
    have hinv : 1 / (n : ℝ) < 1 / (1 / eps) := by
      apply one_div_lt_one_div_of_lt
      · exact one_div_pos.2 heps
      · exact hn
    rwa [one_div_one_div] at hinv

-- 6. Density of Rationals in Reals (Lebl §1.2 Thm 1.2.6)
theorem DensityOfRationals (x y : ℝ) (h : x < y) :
    ∃ q : ℚ, x < (q : ℝ) ∧ (q : ℝ) < y := by
  exact exists_rat_btwn h

-- 7. Nested Interval Property (Lebl §1.5 Thm 1.5.1)
theorem NestedIntervalProperty (a b : ℕ → ℝ) (h_nested : ∀ n, a n ≤ a (n + 1) ∧ b (n + 1) ≤ b n)
    (h_le : ∀ n, a n ≤ b n) :
    ∃ x : ℝ, ∀ n, a n ≤ x ∧ x ≤ b n := by
  have h_mono_a : Monotone a := monotone_nat_of_le_succ (fun n => (h_nested n).1)
  have h_anti_b : Antitone b := antitone_nat_of_succ_le (fun n => (h_nested n).2)
  have h_bdd_a : BddAbove (range a) := by
    use b 0
    rintro _ ⟨n, rfl⟩
    exact le_trans (h_le n) (h_anti_b (Nat.zero_le n))
  use sSup (range a)
  intro n
  constructor
  · exact le_csSup h_bdd_a (mem_range_self n)
  · apply csSup_le ⟨a 0, mem_range_self 0⟩
    rintro _ ⟨m, rfl⟩
    rcases le_total n m with hnm | hmn
    · exact le_trans (h_le m) (h_anti_b hnm)
    · exact le_trans (h_mono_a hmn) (h_le n)

-- 8. Cauchy Completeness (Lebl §2.2 Thm 2.2.12)
theorem CauchyCompleteness (u : ℕ → ℝ) :
    CauchySeq u ↔ ∃ L : ℝ, Tendsto u atTop (𝓝 L) := by
  constructor
  · intro h
    exact cauchySeq_tendsto_of_complete h
  · rintro ⟨L, hL⟩
    exact hL.cauchySeq

-- 9. Sequence Limit Sum and Product (Lebl §2.1 Prop 2.1.17)
theorem LimitAlgebraAndOrder (u v : ℕ → ℝ) (L M : ℝ)
    (hu : Tendsto u atTop (𝓝 L)) (hv : Tendsto v atTop (𝓝 M)) :
    Tendsto (fun n => u n + v n) atTop (𝓝 (L + M)) ∧
    Tendsto (fun n => u n * v n) atTop (𝓝 (L * M)) := by
  constructor
  · exact Tendsto.add hu hv
  · exact Tendsto.mul hu hv

-- 10. Monotone Convergence Theorem (Lebl §2.1 Thm 2.1.14)
theorem MonotoneConvergence (u : ℕ → ℝ) (hmono : Monotone u) (hbd : BddAbove (range u)) :
    Tendsto u atTop (𝓝 (sSup (range u))) := by
  exact tendsto_atTop_ciSup hmono hbd

-- 11. Bolzano-Weierstrass Theorem (Lebl §2.2 Thm 2.2.5)
theorem BolzanoWeierstrass (u : ℕ → ℝ) (hbd : BddAbove (range u)) (hbd_below : BddBelow (range u)) :
    ∃ φ : ℕ → ℕ, StrictMono φ ∧ ∃ L : ℝ, Tendsto (u ∘ φ) atTop (𝓝 L) := by
  have h_comp : IsCompact (Icc (sInf (range u)) (sSup (range u))) := isCompact_Icc
  have h_in : ∀ n, u n ∈ Icc (sInf (range u)) (sSup (range u)) := fun n =>
    ⟨csInf_le hbd_below (mem_range_self n), le_csSup hbd (mem_range_self n)⟩
  obtain ⟨L, -, φ, hφ, hconv⟩ := h_comp.tendsto_subseq h_in
  exact ⟨φ, hφ, L, hconv⟩

-- 12. Open and Closed Sets (Lebl §3.1 Def 3.1.6)
theorem OpenClosedSets (s : Set ℝ) :
    IsOpen s ↔ ∀ x ∈ s, ∃ eps > 0, Metric.ball x eps ⊆ s := by
  exact Metric.isOpen_iff

-- 13. Heine-Borel Theorem (Lebl §3.1 Thm 3.1.20)
theorem HeineBorel (s : Set ℝ) :
    IsCompact s ↔ IsClosed s ∧ Bornology.IsBounded s := by
  constructor
  · intro h
    exact ⟨h.isClosed, h.isBounded⟩
  · rintro ⟨hclosed, hbdd⟩
    obtain ⟨R, hR⟩ := (Metric.isBounded_iff_subset_ball (c := (0 : ℝ))).1 hbdd
    exact IsCompact.of_isClosed_subset (isCompact_closedBall 0 R) hclosed (hR.trans Metric.ball_subset_closedBall)

-- 14. Sequential Continuity Equivalence (Lebl §3.3 Prop 3.3.2)
theorem SequentialContinuity (f : ℝ → ℝ) (x0 : ℝ) (u : ℕ → ℝ)
    (hf : ContinuousAt f x0) (hu : Tendsto u atTop (𝓝 x0)) :
    Tendsto (f ∘ u) atTop (𝓝 (f x0)) := by
  exact hf.tendsto.comp hu

-- 15. Extreme Value Theorem on Compact Sets (Lebl §3.3 Thm 3.3.10)
theorem ExtremeValueTheorem (s : Set ℝ) (h_comp : IsCompact s) (h_nonempty : s.Nonempty)
    (f : ℝ → ℝ) (h_cont : ContinuousOn f s) :
    ∃ x_min ∈ s, ∃ x_max ∈ s, ∀ x ∈ s, f x_min ≤ f x ∧ f x ≤ f x_max := by
  have h_min := IsCompact.exists_isMinOn h_comp h_nonempty h_cont
  have h_max := IsCompact.exists_isMaxOn h_comp h_nonempty h_cont
  obtain ⟨x_min, hmin_s, hmin⟩ := h_min
  obtain ⟨x_max, hmax_s, hmax⟩ := h_max
  exact ⟨x_min, hmin_s, x_max, hmax_s, fun x hx => ⟨hmin hx, hmax hx⟩⟩

-- 16. Uniform Continuity & Heine-Cantor (Lebl §3.4 Thm 3.4.4)
theorem UniformContinuityHeineCantor (s : Set ℝ) (h_comp : IsCompact s)
    (f : ℝ → ℝ) (h_cont : ContinuousOn f s) :
    UniformContinuousOn f s := by
  exact IsCompact.uniformContinuousOn_of_continuous h_comp h_cont

-- 17. Rolle's Theorem (Lebl §4.2 Thm 4.2.2)
theorem RollesTheorem (a b : ℝ) (hab : a < b) (f : ℝ → ℝ)
    (h_cont : ContinuousOn f (Icc a b)) (_h_diff : DifferentiableOn ℝ f (Ioo a b))
    (h_eq : f a = f b) :
    ∃ c ∈ Ioo a b, deriv f c = 0 := by
  exact exists_deriv_eq_zero hab h_cont h_eq

-- 18. Mean Value Theorem (Lebl §4.2 Thm 4.2.4)
theorem MeanValueTheorem (a b : ℝ) (hab : a < b) (f : ℝ → ℝ)
    (h_cont : ContinuousOn f (Icc a b)) (h_diff : DifferentiableOn ℝ f (Ioo a b)) :
    ∃ c ∈ Ioo a b, deriv f c = (f b - f a) / (b - a) := by
  obtain ⟨c, hc, hderiv⟩ := exists_deriv_eq_slope f hab h_cont h_diff
  exact ⟨c, hc, hderiv⟩

-- 19. Fundamental Theorem of Calculus Part 1 (Lebl §5.3 Thm 5.3.1)
theorem FundamentalTheoremCalculus (a b : ℝ) (_hab : a < b) (f : ℝ → ℝ) (hf : ContinuousOn f (Icc a b))
    (x : ℝ) (hx : x ∈ Ioo a b) :
    HasDerivAt (fun y => ∫ t in a..y, f t) (f x) x := by
  have hcont : ContinuousAt f x := hf.continuousAt (Icc_mem_nhds hx.1 hx.2)
  have huIcc : uIcc a x = Icc a x := uIcc_of_le (le_of_lt hx.1)
  have hsubset : Icc a x ⊆ Icc a b := Icc_subset_Icc_right (le_of_lt hx.2)
  have hcont_ax : ContinuousOn f (uIcc a x) := by
    rw [huIcc]
    exact hf.mono hsubset
  have hint : IntervalIntegrable f MeasureTheory.volume a x := hcont_ax.intervalIntegrable
  apply intervalIntegral.integral_hasDerivAt_right hint _ hcont
  exact ContinuousOn.stronglyMeasurableAtFilter isOpen_Ioo (hf.mono Ioo_subset_Icc_self) x hx

end MAPEOGEOFormal.WaveF4
