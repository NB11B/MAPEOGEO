import CollatzProofClosure.Definitions
import CollatzProofClosure.DeficitLifting
import CollatzProofClosure.SpectralCrossing
import CollatzProofClosure.GlobalDescent
import CollatzProofClosure.CycleObstructions

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

end CollatzProofClosure
end BBB17
