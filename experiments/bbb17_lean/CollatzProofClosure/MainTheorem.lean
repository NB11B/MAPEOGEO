import CollatzProofClosure.Definitions
import CollatzProofClosure.DeficitLifting
import CollatzProofClosure.SpectralCrossing
import CollatzProofClosure.GlobalDescent
import CollatzProofClosure.CycleObstructions
import CollatzProofClosure.UnifiedTransitionSystem

namespace BBB17
namespace CollatzProofClosure

/-! # COLLATZ-C10 Unified Proof-Closure Synthesis (`MainTheorem.lean`)

    Synthesizes the five C10 workstreams into two master theorems:
    1. `c10_unified_convergence_criteria`: Connects the two-obligation first-crossing
       route (`EveryNatCrossesSpectrally ∧ MinimalCrossingDeficitPositive`), the
       necessity of spectral crossing (`CollatzConjecture → EveryNatCrossesSpectrally`),
       the multi-segment composite deficit equivalence (`UniversalCompositeDeficitPositive ↔ CollatzConjecture`),
       and the offset-free power-threshold criterion (`eventual_power_threshold_implies_collatz`).
    2. `infinite_nondescent_diophantine_obstruction_system`: Proves that any hypothetical
       integer `n > 1` that never descends below its initial value (`∀ i, iterateAccelerated n i ≥ n`)
       must simultaneously satisfy:
       - `n ≥ 1024`,
       - local geometric peak drawdown within `n` steps (`∃ i ≤ n, iterateAccelerated n (i + 1) < iterateAccelerated n i`),
       - at EVERY depth `r ≥ 1`:
         `(2^r - 3^{a_r}) * n ≤ wordB w_r`,
         `n^{a_r} * (3^{a_r} * n + wordB w_r) ≤ n * (3 * n + 1)^{a_r}`,
         `2^r * n^{a_r} ≤ (3 * n + 1)^{a_r}`, and
         `2^r * 1024^{a_r} ≤ 3073^{a_r}`,
       - complete exclusion of spectral contraction (`2^r < 3^{a_r}`) and periodicity
         (`iterateAccelerated n r ≠ n`) across all depths `1 ≤ r ≤ 64`.
-/

/-- Helper lemma: for any `n ≥ N₀ > 0` satisfying `∀ i ≤ r, iterateAccelerated n i ≥ n`,
    `2 ^ r * N₀ ^ a_r ≤ (3 * N₀ + 1) ^ a_r`. -/
theorem nondescent_lower_bound_power_ratio (n r N₀ : Nat)
    (hn : n > 0) (_hN₀_pos : N₀ > 0) (hN₀_le : N₀ ≤ n)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let a := wordOnes (parityWordOf r n)
    2 ^ r * N₀ ^ a ≤ (3 * N₀ + 1) ^ a := by
  dsimp
  let a := wordOnes (parityWordOf r n)
  have hratio := (nondescent_diophantine_sandwich n r hn hge).2.2
  have hstep_N₀ : N₀ * (3 * n + 1) ≤ (3 * N₀ + 1) * n := by
    rw [Nat.mul_add, Nat.mul_one, Nat.add_mul, Nat.one_mul]
    have hcomm : N₀ * (3 * n) = 3 * N₀ * n := by
      rw [← Nat.mul_assoc, Nat.mul_comm N₀ 3, Nat.mul_assoc]
    omega
  have hpow_N₀ : N₀ ^ a * (3 * n + 1) ^ a ≤ (3 * N₀ + 1) ^ a * n ^ a := by
    rw [← mul_pow_eq N₀ (3 * n + 1) a, ← mul_pow_eq (3 * N₀ + 1) n a]
    exact pow_le_pow_of_le (N₀ * (3 * n + 1)) ((3 * N₀ + 1) * n) a hstep_N₀
  have hmul_lhs : (2 ^ r * N₀ ^ a) * n ^ a ≤ N₀ ^ a * (3 * n + 1) ^ a := by
    have hcomm : (2 ^ r * N₀ ^ a) * n ^ a = N₀ ^ a * (2 ^ r * n ^ a) := by
      rw [Nat.mul_comm (2 ^ r) (N₀ ^ a), Nat.mul_assoc]
    rw [hcomm]
    exact Nat.mul_le_mul_left (N₀ ^ a) hratio
  have hle_na : (2 ^ r * N₀ ^ a) * n ^ a ≤ (3 * N₀ + 1) ^ a * n ^ a :=
    Nat.le_trans hmul_lhs hpow_N₀
  have hna_pos : n ^ a > 0 := pow_pos_of_pos n a hn
  exact Nat.le_of_mul_le_mul_right hle_na hna_pos

/-- Master Infinite Non-Descent Diophantine Obstruction Theorem:
    Any hypothetical integer `n > 1` whose trajectory never drops below `n`
    (`∀ i, iterateAccelerated n i ≥ n`) must simultaneously satisfy:
    1. `n ≥ 1024`,
    2. `∃ i ≤ n, iterateAccelerated n (i + 1) < iterateAccelerated n i` (mandatory peak drawdown),
    3. For every `r ≥ 1` (with `w_r = parityWordOf r n` and `a_r = wordOnes w_r`):
       - `(2^r - 3^{a_r}) * n ≤ wordB w_r`,
       - `n^{a_r} * (3^{a_r} * n + wordB w_r) ≤ n * (3 * n + 1)^{a_r}`,
       - `2^r * n^{a_r} ≤ (3 * n + 1)^{a_r}`, and
       - `2^r * 1024^{a_r} ≤ 3073^{a_r}`,
    4. For every `1 ≤ r ≤ 64`, `2 ^ r < 3 ^ wordOnes (parityWordOf r n)`
       (no spectral contraction can occur at any depth `r ≤ 64`) and `iterateAccelerated n r > n`. -/
theorem infinite_nondescent_diophantine_obstruction_system (n : Nat) (hn1 : n > 1)
    (hnever_desc : ∀ i : Nat, iterateAccelerated n i ≥ n) :
    n ≥ 1024 ∧
    (∃ i : Nat, i ≤ n ∧ iterateAccelerated n (i + 1) < iterateAccelerated n i) ∧
    (∀ r : Nat, r ≥ 1 →
      let w := parityWordOf r n
      let a := wordOnes w
      (2 ^ r - 3 ^ a) * n ≤ wordB w ∧
      n ^ a * (3 ^ a * n + wordB w) ≤ n * (3 * n + 1) ^ a ∧
      2 ^ r * n ^ a ≤ (3 * n + 1) ^ a ∧
      2 ^ r * 1024 ^ a ≤ 3073 ^ a) ∧
    (∀ r : Nat, 1 ≤ r → r ≤ 64 →
      2 ^ r < 3 ^ wordOnes (parityWordOf r n) ∧
      iterateAccelerated n r > n) := by
  have hn_ge1024 : n ≥ 1024 := by
    by_cases hlt : n < 1024
    · rcases descent_of_lt_1024 n hn1 hlt with ⟨k, _, _, hk_lt⟩
      have hge_k := hnever_desc k
      omega
    · omega
  have hdrawdown := every_nat_experiences_peak_drawdown n (by omega)
  have hdioph : ∀ r : Nat, r ≥ 1 →
      let w := parityWordOf r n
      let a := wordOnes w
      (2 ^ r - 3 ^ a) * n ≤ wordB w ∧
      n ^ a * (3 ^ a * n + wordB w) ≤ n * (3 * n + 1) ^ a ∧
      2 ^ r * n ^ a ≤ (3 * n + 1) ^ a ∧
      2 ^ r * 1024 ^ a ≤ 3073 ^ a := by
    intro r _
    dsimp
    have hsand := nondescent_diophantine_sandwich n r (by omega) (fun i _ => hnever_desc i)
    have h1024 := nondescent_lower_bound_power_ratio n r 1024
      (by omega) (by decide) hn_ge1024 (fun i _ => hnever_desc i)
    exact ⟨hsand.1, hsand.2.1, hsand.2.2, h1024⟩
  refine ⟨hn_ge1024, hdrawdown, hdioph, ?_⟩
  intro r hr1 hr64
  let w := parityWordOf r n
  let a := wordOnes w
  have h1024 := (hdioph r hr1).2.2.2
  have ha_ge1 : 1 ≤ a := by
    have h1 := hnever_desc 1
    dsimp [iterateAccelerated] at h1
    have hodd : n % 2 = 1 := by
      by_cases hev : n % 2 = 0
      · unfold acceleratedCollatz at h1
        rw [if_pos hev] at h1
        omega
      · omega
    obtain ⟨k, rfl⟩ : ∃ k, r = 1 + k := ⟨r - 1, by omega⟩
    have hadd := parityWordOf_add 1 k n
    have hw1 : wordOnes (parityWordOf 1 n) = 1 := by
      dsimp [parityWordOf]
      have hb : (n % 2 == 1) = true := by rw [beq_iff_eq]; exact hodd
      rw [hb]
      rfl
    have hones_r : wordOnes (parityWordOf (1 + k) n) ≥ 1 := by
      rw [hadd, wordOnes_append, hw1]
      omega
    exact hones_r
  have ha_le : a ≤ r := by
    have hlen : w.length = r := parityWordOf_length r n
    have hle := wordOnes_le_length w
    omega
  have hnot_cont : ¬(3 ^ a < 2 ^ r) := by
    intro hcont
    have hr_mem : r ∈ List.range 65 := List.mem_range.mpr (by omega)
    have ha_mem : a ∈ List.range (r + 1) := List.mem_range.mpr (by omega)
    have hall_r := (List.all_eq_true.mp checkEliahouWindow1024_64) r hr_mem
    have hall_a := (List.all_eq_true.mp hall_r) a ha_mem
    have htrue : decide (1 ≤ r ∧ 1 ≤ a ∧ 3 ^ a < 2 ^ r ∧ 2 ^ r * 1024 ^ a ≤ 3073 ^ a) = true :=
      decide_eq_true ⟨hr1, ha_ge1, hcont, h1024⟩
    rw [htrue] at hall_a
    contradiction
  have hne_pow : 2 ^ r ≠ 3 ^ a := by
    have hmod2 := pow_two_mod_three_ne_zero r
    have hmod3 := pow_three_mod_three_eq_zero a ha_ge1
    intro heq
    rw [heq] at hmod2
    exact hmod2 hmod3
  have hlt_pow : 2 ^ r < 3 ^ a := by omega
  have hne_cyc : iterateAccelerated n r ≠ n :=
    no_nontrivial_cycle_length_le_64 n r hn1 hr1 hr64 hnever_desc
  have hge_n : iterateAccelerated n r ≥ n := hnever_desc r
  exact ⟨hlt_pow, by omega⟩

/-- Unified Multi-Route Convergence Summary Theorem (`c10_unified_convergence_criteria`):
    1. `EveryNatCrossesSpectrally ∧ MinimalCrossingDeficitPositive → CollatzConjecture`,
    2. `CollatzConjecture → EveryNatCrossesSpectrally` (Obligation A is necessary),
    3. `UniversalCompositeDeficitPositive ↔ CollatzConjecture`, and
    4. `(∀ n > 1, ∃ r ≥ 1, 2^r * n^{a_r(n)} > (3n + 1)^{a_r(n)}) → CollatzConjecture`. -/
theorem c10_unified_convergence_criteria :
    (EveryNatCrossesSpectrally ∧ MinimalCrossingDeficitPositive → CollatzConjecture) ∧
    (CollatzConjecture → EveryNatCrossesSpectrally) ∧
    (UniversalCompositeDeficitPositive ↔ CollatzConjecture) ∧
    ((∀ n : Nat, n > 1 → ∃ r : Nat, r ≥ 1 ∧
      2 ^ r * n ^ wordOnes (parityWordOf r n) >
        (3 * n + 1) ^ wordOnes (parityWordOf r n)) → CollatzConjecture) :=
  ⟨two_obligations_imply_collatz,
   collatz_implies_everyNatCrossesSpectrally,
   universalCompositeDeficitPositive_iff_collatz,
   eventual_power_threshold_implies_collatz⟩

/-- Unified PSMSL + MAPEOGEO + Symbolic-Dynamics Non-Descent Synthesis (`unified_transition_nondescent_laws`):
    For any hypothetical never-descending integer `n > 1` (`∀ i, iterateAccelerated n i ≥ n`):
    1. `n % 4 = 3` and `deficitReservoir n 2 = n * (n + 1)` (`nondescent_depth2_forces_mod4_eq_3_and_reservoir`),
    2. For every depth `r ≥ 0`, the exact Reservoir-Surplus Conservation Law holds:
       `deficitReservoir n r + n^{a_r} * orbitSurplus n r + 2^r * n^{a_r + 1} = n * (3 * n + 1)^{a_r}`,
    3. For every depth `r ≥ 2`, `a_r ≥ 2`,
       `deficitReservoir n r ≥ n * (n + 1) * (3 * n + 1)^{a_r - 2}`, and
       `2^r * n^{a_r - 1} ≤ (9 * n + 5) * (3 * n + 1)^{a_r - 2}`. -/
theorem unified_transition_nondescent_laws (n : Nat)
    (hn1 : n > 1)
    (hnever_desc : ∀ i : Nat, iterateAccelerated n i ≥ n) :
    (n % 4 = 3 ∧ deficitReservoir n 2 = n * (n + 1)) ∧
    (∀ r : Nat,
      let a := wordOnes (parityWordOf r n)
      deficitReservoir n r + n ^ a * orbitSurplus n r + 2 ^ r * n ^ (a + 1) =
        n * (3 * n + 1) ^ a) ∧
    (∀ r : Nat, r ≥ 2 →
      let a := wordOnes (parityWordOf r n)
      a ≥ 2 ∧
      deficitReservoir n r ≥ n * (n + 1) * (3 * n + 1) ^ (a - 2) ∧
      2 ^ r * n ^ (a - 1) ≤ (9 * n + 5) * (3 * n + 1) ^ (a - 2)) := by
  rcases nondescent_depth2_forces_mod4_eq_3_and_reservoir n hn1 (hnever_desc 1) (hnever_desc 2) with
    ⟨hm4, _, hres2⟩
  refine ⟨⟨hm4, hres2⟩, ?_, ?_⟩
  · intro r
    exact reservoir_plus_surplus_eq_power_gap n r (fun i _ => hnever_desc i)
  · intro r hr2
    rcases deficitReservoir_lower_bound_ge_two n r hn1 hr2 (fun i _ => hnever_desc i) with
      ⟨ha2, hres_ge⟩
    rcases sharpened_nondescent_power_bound n r hn1 hr2 (fun i _ => hnever_desc i) with
      ⟨_, _, hsharp⟩
    exact ⟨ha2, hres_ge, hsharp⟩

/-- Normalized Cumulative Reservoir Obstruction Synthesis (`infinite_nondescent_reservoir_master`):
    For any hypothetical non-returning never-descending integer `n > 1`
    (`∀ i ≥ 1, iterateAccelerated n i > n`):
    1. For every `r ≥ 0`, `qNum n r < qDen n r` (`0 ≤ Q_r < 1`) and `qNum n r * qDen n (r + 1) ≤ qNum n (r + 1) * qDen n r` (`Q_r ≤ Q_{r+1}`),
    2. For every `r ≥ 0`, `qNum n (r + 1) * qDen n r = qNum n r * qDen n (r + 1) + crossStepIncrement n r` (exact telescoping increments),
    3. For every `r ≥ 1`, let `a = wordOnes (parityWordOf r n)`. Then `a ≥ 1`,
       `2^r * (n + 2)^{a - 1} * iterateAccelerated n r ≤ (3 * n + 1) * (3 * n + 7)^{a - 1}`, and
       `(n + 2)^{a - 1} * (qDen n r - qNum n r) ≤ n^a * ((3 * n + 1) * (3 * n + 7)^{a - 1})`
       (exponential decay of `1 - Q_r ≤ (1 - 2 / ((n + 2)(3n + 1)))^{a - 1}`). -/
theorem infinite_nondescent_reservoir_master (n : Nat)
    (hn1 : n > 1)
    (hstrict : ∀ i : Nat, i ≥ 1 → iterateAccelerated n i > n) :
    (∀ M : Nat, ∃ r : Nat, wordOnes (parityWordOf r n) ≥ M) ∧
    (∀ r : Nat,
      let w := parityWordOf r n
      let a := wordOnes w
      qNum n r < qDen n r ∧
      qNum n r * qDen n (r + 1) ≤ qNum n (r + 1) * qDen n r ∧
      qNum n (r + 1) * qDen n r =
        qNum n r * qDen n (r + 1) + crossStepIncrement n r ∧
      qDen n r - qNum n r = n * (3 * n) ^ a + n ^ a * wordB w ∧
      (qDen n r - qNum n r) % (2 ^ r * n ^ a) = 0) ∧
    (∀ r : Nat, r ≥ 1 →
      let a := wordOnes (parityWordOf r n)
      a ≥ 1 ∧
      2 ^ r * (n + 2) ^ (a - 1) * iterateAccelerated n r ≤
        (3 * n + 1) * (3 * n + 7) ^ (a - 1) ∧
      (n + 2) ^ (a - 1) * (qDen n r - qNum n r) ≤
        n ^ a * ((3 * n + 1) * (3 * n + 7) ^ (a - 1))) := by
  have hge_all : ∀ i : Nat, iterateAccelerated n i ≥ n := by
    intro i
    cases i with
    | zero => dsimp [iterateAccelerated]; omega
    | succ i' =>
      have hgt := hstrict (i' + 1) (by omega)
      omega
  have hn_odd : n % 2 = 1 := by
    rcases nondescent_depth2_forces_mod4_eq_3_and_reservoir n hn1 (hge_all 1) (hge_all 2) with
      ⟨hm4, _, _⟩
    omega
  refine ⟨unbounded_odd_steps_of_never_descending n (by omega) hge_all, ?_, ?_⟩
  · intro r
    dsimp
    rcases normalized_reservoir_monotone_bounded n r (by omega) (fun i _ => hge_all i) with
      ⟨hlt, _, hmono⟩
    rcases normalized_reservoir_telescoping n r with ⟨_, htel⟩
    rcases reservoir_complement_divisibility_and_lower_bound n r (fun i _ => hge_all i) with
      ⟨hdiv, _, _, hdual⟩
    exact ⟨hlt, hmono, htel, hdual, hdiv⟩
  · intro r hr1
    exact infinite_nondescent_reservoir_obstruction n r hn1 hr1 hn_odd
      (fun i hi1 _ => hstrict i hi1)

/-- Projective Fixed-Point and Universal Non-Descent Offset Master Synthesis
    (`projective_fixedPoint_and_congruence_master`):
    For any hypothetical never-descending integer `n > 1` (`∀ i, iterateAccelerated n i ≥ n`),
    at every depth `r ≥ 1`, letting `w = parityWordOf r n` and `a = wordOnes w`:
    1. Exact Reservoir-Offset Duality:
       `deficitReservoir n r + n^a * wordB w + n * (3 * n)^a = n * (3 * n + 1)^a`,
    2. Universal Non-Descent Offset Bound (valid across all depths `r ≥ 1`, even after
       arbitrarily many spectral crossings):
       `deficitReservoir n r + n^a * wordB w ≤ n * (a * (3 * n + 1)^{a - 1})` and
       `n^{a - 1} * wordB w ≤ a * (3 * n + 1)^{a - 1}`,
    3. Universal Projective Fixed-Point Bound at Contracting Depths:
       `wordDelta w * n^a ≤ n^{a - 1} * wordB w ≤ a * (3 * n + 1)^{a - 1}` and
       `wordDelta w * n ≤ a * 4^{a - 1}`. -/
theorem projective_fixedPoint_and_congruence_master (n : Nat)
    (hn1 : n > 1)
    (hnever_desc : ∀ i : Nat, iterateAccelerated n i ≥ n) :
    ∀ r : Nat, r ≥ 1 →
      let w := parityWordOf r n
      let a := wordOnes w
      a ≥ 1 ∧
      deficitReservoir n r + n ^ a * wordB w + n * (3 * n) ^ a =
        n * (3 * n + 1) ^ a ∧
      deficitReservoir n r + n ^ a * wordB w ≤
        n * (a * (3 * n + 1) ^ (a - 1)) ∧
      n ^ (a - 1) * wordB w ≤ a * (3 * n + 1) ^ (a - 1) ∧
      wordDelta w * n ^ a ≤ n ^ (a - 1) * wordB w ∧
      wordDelta w * n ^ a ≤ a * (3 * n + 1) ^ (a - 1) ∧
      wordDelta w * n ≤ a * 4 ^ (a - 1) := by
  intro r hr1
  dsimp
  have hdual := (reservoir_offset_duality_identity n r (fun i _ => hnever_desc i)).2
  rcases universal_nondescent_offset_and_fixedPoint_bound n r hn1 hr1 (fun i _ => hnever_desc i) with
    ⟨ha1, hres_B_le, hB_le, hdelta_na_le, hdelta_na_rhs, hdelta_4⟩
  exact ⟨ha1, hdual, hres_B_le, hB_le, hdelta_na_le, hdelta_na_rhs, hdelta_4⟩

/-- Signed Projective Gap, 2-Adic Modular Branch Lock, and Surviving Lift Set Master Synthesis
    (`signedProjectiveGap_and_survivingLiftSet_master`):
    For any hypothetical never-descending integer `n > 1` (`∀ i, iterateAccelerated n i ≥ n`),
    at every depth `r : Nat`, letting `w = parityWordOf r n` and `a = wordOnes w`:
    1. Signed Projective Gap Nonpositivity and Negated Surplus Identity:
       `signedProjectiveGap w n = - (orbitSurplus n r : Int) ≤ 0`,
    2. Exact Even/Odd Step Update Laws:
       `signedProjectiveGap (w ++ [false]) n = signedProjectiveGap w n + (wordD w : Int) * (n : Int)` and
       `signedProjectiveGap (w ++ [true]) n = 3 * signedProjectiveGap w n - (wordD w : Int) * ((n : Int) + 1)`,
    3. Autonomous 2-Adic Modular Branch Lock:
       `iterateAccelerated n r % 2 = 1 ↔ signedProjectiveGap w n % (2 * (wordD w : Int)) = 0`,
    4. Even-Step Descent Band Obstruction:
       Whenever `signedProjectiveGap w n > -((2 ^ r : Nat) : Int) * (n : Int)` (`F^r(n) < 2 * n`),
       step `r` is forced to be an odd step (`iterateAccelerated n r % 2 = 1`),
    5. Global Reservoir-Gap Identity:
       `(deficitReservoir n r : Int) - ((n ^ a : Nat) : Int) * signedProjectiveGap w n =
         (n : Int) * (((3 * n + 1) ^ a : Nat) : Int) - ((2 ^ r * n ^ (a + 1) : Nat) : Int)`,
    6. Self-Membership in `𝓢_r(n)` (`InSurvivingLiftSet n r n`) and Intermediate Contracting Cap
       for all `m ∈ 𝓢_r(n)` with `m > 1`. -/
theorem signedProjectiveGap_and_survivingLiftSet_master (n : Nat)
    (hn1 : n > 1)
    (hnever_desc : ∀ i : Nat, iterateAccelerated n i ≥ n) :
    ∀ r : Nat,
      let w := parityWordOf r n
      let a := wordOnes w
      signedProjectiveGap w n = - (orbitSurplus n r : Int) ∧
      signedProjectiveGap w n ≤ 0 ∧
      signedProjectiveGap (w ++ [false]) n =
        signedProjectiveGap w n + (wordD w : Int) * (n : Int) ∧
      signedProjectiveGap (w ++ [true]) n =
        3 * signedProjectiveGap w n - (wordD w : Int) * ((n : Int) + 1) ∧
      (iterateAccelerated n r % 2 = 1 ↔
        signedProjectiveGap w n % (2 * (wordD w : Int)) = 0) ∧
      (signedProjectiveGap w n + (wordD w : Int) * (n : Int) > 0 →
        iterateAccelerated n r % 2 = 1) ∧
      (deficitReservoir n r : Int) - ((n ^ a : Nat) : Int) * signedProjectiveGap w n +
        ((2 ^ r * n ^ (a + 1) : Nat) : Int) =
        ((n * (3 * n + 1) ^ a : Nat) : Int) ∧
      InSurvivingLiftSet n r n := by
  have hn_odd : n % 2 = 1 := by
    rcases nondescent_depth2_forces_mod4_eq_3_and_reservoir n hn1 (hnever_desc 1) (hnever_desc 2) with
      ⟨hm4, _, _⟩
    omega
  intro r
  dsimp
  have hv := parityWordOf_valid r n
  rcases signedProjectiveGap_reservoir_conservation n r (fun i _ => hnever_desc i) with
    ⟨hgap_surp, hgap_le0, hres_gap⟩
  have hev_step := signedProjectiveGap_even_step (parityWordOf r n) n
  have hodd_step := signedProjectiveGap_odd_step (parityWordOf r n) n
  have hlock := (signedProjectiveGap_modular_branch_lock (parityWordOf r n) n hv).2.2.2 hn_odd
  rw [applyParityWord_parityWordOf] at hlock
  have hv_succ := parityWordOf_valid (r + 1) n
  have hge_succ : applyParityWord n (parityWordOf (r + 1) n) ≥ n := by
    rw [applyParityWord_parityWordOf]
    exact hnever_desc (r + 1)
  have hgap_succ_le0 : signedProjectiveGap (parityWordOf (r + 1) n) n ≤ 0 :=
    (signedProjectiveGap_sign_trichotomy (parityWordOf (r + 1) n) n hv_succ).2.2.2.mpr hge_succ
  have hband := (signedProjectiveGap_even_step_descent_band n r).2
  have hsurv : InSurvivingLiftSet n r n := ⟨rfl, fun i _ => hnever_desc i⟩
  exact ⟨hgap_surp, hgap_le0, hev_step, hodd_step, hlock.1,
    fun hgt => hband hgt hgap_succ_le0, hres_gap, hsurv⟩

/-- Mechanism A Master Synthesis: Delayed-Descent Surplus Elimination and Finite Quotient Collapse
    (`mechanismA_delayed_descent_and_quotient_collapse_master`):
    For any hypothetical never-descending integer `n > 1` (`∀ i, iterateAccelerated n i ≥ n`),
    at every depth `i ≥ 1` and subsequent depth `r ≥ i + 2`:
    1. Delayed-Descent Valuation Lock on `s_i = iterateAccelerated n i - n`:
       - `s_i < n → s_i % 2 = 0`,
       - `3 * s_i + 1 < n → s_i % 4 = 0`,
       - `s_i > 0 → 3 * s_i + 1 < n → s_i ≥ 4`, and
       - `IsFirstCrossing (parityWordOf i n) → s_i > 0 → wordOnes (parityWordOf i n) < n → wordOnes (parityWordOf i n) ≥ 13`.
    2. Finite Quotient Collapse and Lift-Bit Lock on `𝓢_r(n)`:
       - Every `m ∈ 𝓢_r(n)` (`m > 1`) satisfies
         `wordDelta (parityWordOf i n) * wordResidue (parityWordOf r n) + (m / 2^r) * (wordDelta (parityWordOf i n) * 2^r) ≤ wordB (parityWordOf i n)`,
       - Whenever `wordDelta (parityWordOf i n) * 2^r > wordB (parityWordOf i n)`, every `m ∈ 𝓢_r(n)` (`m > 1`)
         has `m / 2^r = 0` and `m = wordResidue (parityWordOf r n) = n` (eliminating all proper lifts `q ≥ 1`). -/
theorem mechanismA_delayed_descent_and_quotient_collapse_master (n i r : Nat)
    (hn1 : n > 1) (hi1 : i ≥ 1) (hir2 : i + 2 ≤ r)
    (hnever_desc : ∀ j : Nat, iterateAccelerated n j ≥ n) :
    let w_i := parityWordOf i n
    let w_r := parityWordOf r n
    let s_i := iterateAccelerated n i - n
    (s_i < n → s_i % 2 = 0) ∧
    (3 * s_i + 1 < n → s_i % 4 = 0) ∧
    (s_i > 0 → 3 * s_i + 1 < n → s_i ≥ 4) ∧
    (IsFirstCrossing w_i → s_i > 0 → wordOnes w_i < n → wordOnes w_i ≥ 13) ∧
    (∀ m : Nat, m > 1 → InSurvivingLiftSet n r m →
      wordDelta w_i * wordResidue w_r + (m / 2 ^ r) * (wordDelta w_i * 2 ^ r) ≤ wordB w_i) ∧
    (wordDelta w_i * 2 ^ r > wordB w_i →
      ∀ m : Nat, m > 1 → InSurvivingLiftSet n r m →
        m / 2 ^ r = 0 ∧ m = wordResidue w_r) := by
  dsimp
  have hsurv_r : InSurvivingLiftSet n r n := ⟨rfl, fun j _ => hnever_desc j⟩
  rcases small_surplus_delayed_descent_elimination n r i hn1 (by omega) (by omega) hsurv_r with
    ⟨hev_elim, hmod4_elim, hs4, hfc13⟩
  rcases survivingLiftSet_quotient_collapse_and_liftBit_lock n i r hi1 (by omega) with
    ⟨hq_bound, hq_zero, _⟩
  exact ⟨hev_elim (by omega), hmod4_elim hir2, hs4 hir2,
    fun hfc => hfc13 hfc hir2, hq_bound, hq_zero⟩

/-- Unified Contradiction Trichotomy Master Theorem (`unified_contradiction_trichotomy_master`):
    Synthesizes the Section 9 contradiction architecture for a hypothetical never-descending
    orbit (`∀ r, iterateAccelerated n r ≥ n`):
    1. **Case A → Case C Reduction**: Any bounded recurrence (`M - n + 2` visits to `[n, M]`)
       repeats an iterate and constructively extracts a pure cycle minimum `m* ≥ n > 1` with
       `iterateAccelerated m* p = m*` (`p ≥ 1`) and `∀ r, iterateAccelerated m* r ≥ m*`.
    2. **Sharpened Case C Cycle Obstructions**: Any strict cycle minimum `n > 1` of minimal period `p ≥ 1`
       satisfies `n ≥ 1024`, `p ≥ 65`, `iterateAccelerated n i ≥ n + 4` for all `1 ≤ i < p`,
       `signedProjectiveGap (parityWordOf p n) n = 0`, `wordB (parityWordOf p n) % n = 0`, and
       `deficitReservoir n p + 2^p * n^{a_p + 1} = n * (3 * n + 1)^{a_p}`.
    3. **Two-Target Equivalence**: `CollatzConjecture` holds if and only if both Pure Cycle Exclusion
       (Case C) and Injective / Escape-to-Infinity Non-Descent Exclusion (Case B) hold. -/
theorem unified_contradiction_trichotomy_master :
    (∀ (n M : Nat) (depthSeq : Nat → Nat),
      n > 1 →
      (∀ r : Nat, iterateAccelerated n r ≥ n) →
      (∀ t₁ t₂ : Nat, t₁ < t₂ → depthSeq t₁ < depthSeq t₂) →
      (∀ t : Nat, t ≤ M - n + 1 → iterateAccelerated n (depthSeq t) ≤ M) →
      ∃ m_star p : Nat,
        p ≥ 1 ∧ m_star ≥ n ∧ m_star > 1 ∧
        iterateAccelerated m_star p = m_star ∧
        ∀ r : Nat, iterateAccelerated m_star r ≥ m_star) ∧
    (∀ (n p : Nat),
      n > 1 → p ≥ 1 →
      (∀ i : Nat, 1 ≤ i → i < p → iterateAccelerated n i > n) →
      iterateAccelerated n p = n →
      let w_p := parityWordOf p n
      let a_p := wordOnes w_p
      n ≥ 1024 ∧ p ≥ 65 ∧
      (∀ i : Nat, 1 ≤ i → i < p → iterateAccelerated n i - n ≥ 4) ∧
      signedProjectiveGap w_p n = 0 ∧
      wordDelta w_p * n = wordB w_p ∧
      wordB w_p % n = 0 ∧
      deficitReservoir n p + 2 ^ p * n ^ (a_p + 1) = n * (3 * n + 1) ^ a_p) ∧
    (CollatzConjecture ↔
      (¬(∃ m p : Nat, m > 1 ∧ p ≥ 1 ∧
          iterateAccelerated m p = m ∧ ∀ r : Nat, iterateAccelerated m r ≥ m) ∧
       ¬(∃ n : Nat, n > 1 ∧
          (∀ r : Nat, iterateAccelerated n r ≥ n) ∧
          (∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j)))) := by
  refine ⟨?_, ?_, collatz_iff_no_pure_cycle_and_no_divergent_nondescent⟩
  · intro n M depthSeq hn1 hnever_desc hmono hbounded
    exact (bounded_recurrence_reduces_to_pure_cycle n M depthSeq hn1 hnever_desc hmono hbounded).2
  · intro n p hn1 hp1 hstrict hcycle
    dsimp
    rcases cycle_interior_gap_ge_four_and_reservoir_identity n p hn1 hp1 hstrict hcycle with
      ⟨hn1024, hp65, hint, hgap0, hnd, hBmod, hcons⟩
    exact ⟨hn1024, hp65, fun i hi1 hip => (hint i hi1 hip).1, hgap0, hnd, hBmod, hcons⟩

/-- Section 10 Master Theorem: Exact Two-Target Reduction (`NoNontrivialCycle ∧ NoDivergentOrbit`),
    Divergence-Injectivity Equivalence, and Valuation-Block Asymptotics
    (`section10_divergent_orbit_and_valuation_master`):
    1. `CollatzConjecture ↔ (NoNontrivialCycle ∧ NoDivergentOrbit)`,
    2. For every `n : Nat`, `DivergentOrbit n ↔ (∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j)`,
    3. Every divergent orbit of `n > 1` attains a global never-descending minimum `n* = iterateAccelerated n r* > 1`
       with `DivergentOrbit n*`,
    4. Every never-descending divergent orbit satisfies the asymptotic power-deficit and negative-gap laws
       `2^{r + m} * n^{a_r} < (3 * n + 1)^{a_r}` and `signedProjectiveGap w_r n < -(2^r * (M - n))` for all `r ≥ R`, and
    5. Every odd-to-odd return block `singleOddWord k` on `u > 1` strictly grows for `k = 0` and strictly descends
       for `k ≥ 1`, while any non-descending valuation sequence `ks` of cumulative valuation `K = totalValuation ks`
       and odd-step count `s = ks.length` satisfies `deficitReservoir n K + 2^K * n^s * F^K(n) = n * (3 * n + 1)^s`
       and `2^K * n^s ≤ (3 * n + 1)^s`. -/
theorem section10_divergent_orbit_and_valuation_master :
    (CollatzConjecture ↔ (NoNontrivialCycle ∧ NoDivergentOrbit)) ∧
    (∀ n : Nat,
      DivergentOrbit n ↔
        (∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j)) ∧
    (∀ n : Nat, n > 1 → DivergentOrbit n →
      ∃ r_star : Nat,
        let n_star := iterateAccelerated n r_star
        n_star > 1 ∧ n_star ≤ n ∧
        (∀ r : Nat, iterateAccelerated n_star r ≥ n_star) ∧
        DivergentOrbit n_star) ∧
    (∀ (n M m : Nat),
      n > 1 → M ≥ n →
      (∀ r : Nat, iterateAccelerated n r ≥ n) →
      DivergentOrbit n →
      ∃ R : Nat, ∀ r : Nat, r ≥ R →
        let w_r := parityWordOf r n
        let a_r := wordOnes w_r
        iterateAccelerated n r > M ∧
        signedProjectiveGap w_r n < ((2 ^ r : Nat) : Int) * ((n : Int) - (M : Int)) ∧
        2 ^ (r + m) * n ^ a_r < (3 * n + 1) ^ a_r) ∧
    (∀ (k u : Nat),
      u > 1 → validParityWord u (singleOddWord k) →
      2 ^ (k + 1) * applyParityWord u (singleOddWord k) = 3 * u + 1 ∧
      (k = 0 → applyParityWord u (singleOddWord k) > u) ∧
      (k ≥ 1 → applyParityWord u (singleOddWord k) < u)) := by
  refine ⟨collatz_iff_noNontrivialCycle_and_noDivergentOrbit,
    divergentOrbit_iff_injective,
    divergentOrbit_attains_global_nondescent_minimum,
    ?_,
    singleOddWord_step_dichotomy⟩
  intro n M m hn1 hM hnever_desc hdiv
  rcases divergentOrbit_asymptotic_power_and_gap_laws n M m hn1 hM hnever_desc hdiv with
    ⟨R, hR⟩
  refine ⟨R, fun r hr => ?_⟩
  rcases hR r hr with ⟨hitM, _, hgap, _, hpow⟩
  exact ⟨hitM, hgap, hpow⟩

/-- Section 11 Master Theorem: Ordered Valuation-Block Dynamics, Goodstein Rank Decay,
    Four-Color 1-Circuit Reducibility, Diophantine Cycle Equivalence, and Falsification Witnesses
    (`section11_ordered_valuation_goodstein_fourColor_master`):
    1. **Exact Affine-Parity Equivalence**:
       `∀ w n y, wordD w * y = wordA w * n + wordB w ↔ (validParityWord n w ∧ applyParityWord n w = y)`.
    2. **Pure Diophantine Non-Divisibility Equivalence for `NoNontrivialCycle`**:
       `NoNontrivialCycle ↔ ∀ w, wordD w > wordA w → wordB w > 2 * wordDelta w → wordB w % wordDelta w ≠ 0`.
    3. **Ordered Valuation-Block Recurrence & Two-Sided Extremal Sandwich**:
       `B_{s+1} = 3 * B_s + 2^{K_s}` and `3^s - 2^s ≤ B_s ≤ 2^{K_s - s} * (3^s - 2^s)`.
    4. **Goodstein 2-Adic Tail Rank Decay & Four-Color 1-Circuit Reducibility**:
       `2^a * (F(n, allTrueWord a) + 1) = 3^a * (n + 1)` and every contracting `oneCircuitWord a k`
       with `a = 1 ∨ (2^{a+k} - 3^a) * (2^a - 1) > 3^a - 2^a` forces `F(n, oneCircuitWord a k) < n` for all `n > 1`.
    5. **Formal Falsifications of Naive Strengthening Hypotheses**:
       `trivial_cycle_repeat_divides_offset_witness` and `contracting_odd_block_survives_above_initial_at_27`. -/
theorem section11_ordered_valuation_goodstein_fourColor_master :
    (∀ (w : List Bool) (n y : Nat),
      wordD w * y = wordA w * n + wordB w ↔
        (validParityWord n w ∧ applyParityWord n w = y)) ∧
    (NoNontrivialCycle ↔
      (∀ w : List Bool,
        wordD w > wordA w →
        wordB w > 2 * wordDelta w →
        wordB w % wordDelta w ≠ 0)) ∧
    (∀ (ks : List Nat) (k : Nat),
      wordB (returnMapWord (ks ++ [k])) =
        3 * wordB (returnMapWord ks) + 2 ^ totalValuation ks) ∧
    (∀ ks : List Nat,
      let s := ks.length
      let K := totalValuation ks
      K ≥ s ∧
      wordB (returnMapWord ks) + 2 ^ s ≥ 3 ^ s ∧
      2 ^ s * wordB (returnMapWord ks) + 2 ^ K * 2 ^ s ≤ 2 ^ K * 3 ^ s) ∧
    (∀ (a n : Nat),
      validParityWord n (allTrueWord a) →
      2 ^ a * (applyParityWord n (allTrueWord a) + 1) = 3 ^ a * (n + 1) ∧
      n + 1 ≥ 2 ^ a) ∧
    (∀ (a k n : Nat),
      a ≥ 1 → n > 1 →
      validParityWord n (oneCircuitWord a k) →
      2 ^ (a + k) > 3 ^ a →
      (a = 1 ∨ (2 ^ (a + k) - 3 ^ a) * (2 ^ a - 1) > 3 ^ a - 2 ^ a) →
      applyParityWord n (oneCircuitWord a k) < n) ∧
    (validOddReturnSeq 27 [0] ∧
     applyParityWord 27 (returnMapWord [0]) = 41 ∧
     validOddReturnSeq 27 [0, 1] ∧
     applyParityWord 27 (returnMapWord [0, 1]) = 31 ∧
     31 < 41 ∧ 31 > 27) :=
  ⟨affine_identity_iff_validParityWord_and_output,
   noNontrivialCycle_iff_offset_nondivisibility,
   wordB_returnMapWord_snoc,
   returnMap_offset_extremal_sandwich,
   allTrueWord_goodstein_plus_one_law,
   oneCircuitWord_reducible_descent,
   contracting_odd_block_survives_above_initial_at_27⟩

end CollatzProofClosure
end BBB17
