import Rule30LeftReconstruction

/-!
# `R30-CLOSE-001` Track B — PSMSL Persistent-Information & Linear Re-Entry Bounds (`Rule30RightInformation.lean`)

Establishes the formal Track B theorems connecting PSMSL right-half future-work equivalence to
left-permutive reconstruction and the single-seed light-cone boundary:
1. **`bilateral_center_conservation` (`EXACT`):**
   Proves the exact step-by-step affine conservation law across column `0`:
   `cell t (-1) = xor (cell (t + 1) 0) (orCol 0 t)` and
   `orCol 0 t = xor (cell (t + 1) 0) (cell t (-1))`.
2. **`futureWorkEquiv_implies_orCol_and_left_col_agree` (`EXACT`):**
   Under any `P`-periodic center from `T` on (`P > 0`, `t₀ ≥ T`), if the return states at
   `t₁ = t₀ + m₀ * P` and `t₂ = t₀ + (m₀ + q) * P` are `FutureWorkEquiv (col0Word t₀ P) k`-equivalent,
   then both `orCol 0` and the left-half column `cell · (-1)` agree at every step `s < (k + 1) * P`.
3. **`universal_linear_reentry_horizon_bound` (`EXACT`):**
   Upgrades `G11.4`'s existential re-entry theorem (`∃ k' > k`) to an **explicit, universal,
   constructive linear upper bound** via `window_jen`: for every `T, P, t₀, m₀, q, k : Nat` with
   `P > 0`, `q > 0`, `T ≤ t₀`, and `t₀ + (m₀ + q) * P ≤ (k + 1) * P`, the return states at
   `m₀ + q` and `m₀` **cannot** be `FutureWorkEquiv (col0Word t₀ P) k`-equivalent!
4. **`periodic_center_distinct_futureWork_classes_at_linear_horizon` (`EXACT`):**
   Consequently, for any `M : Nat` return steps `0 ≤ m₁ < m₂ < M`, at any linear horizon `k`
   satisfying `t₀ + m₂ * P ≤ (k + 1) * P`, their `FutureWorkEquiv` classes are strictly distinct.
-/

namespace Rule30ProofClosure

open Ruliology.CellularAutomata
open Ruliology.CellularAutomata.Rule30Prize
open Ruliology.CellularAutomata.Rule30Realization
open Ruliology.CellularAutomata.Rule30Jen
open Ruliology.CellularAutomata.Rule30MaskedJen
open Ruliology.CellularAutomata.Rule30Diagonals
open Ruliology.CellularAutomata.Rule30BlackRuns

/-- **Track B (`EXACT`) — Bilateral Center Conservation Law (`bilateral_center_conservation`)**:
    At every step `t : Nat`, the first left-half column `cell t (-1)` and the first right-half
    PSMSL masked observation `orCol 0 t = cell t 0 || cell t 1` are in exact 1-to-1 affine
    bijection over `𝔽₂` via `cell (t + 1) 0`. -/
theorem bilateral_center_conservation (t : Nat) :
    cell t (-1) = xor (cell (t + 1) 0) (orCol 0 t) ∧
    orCol 0 t = xor (cell (t + 1) 0) (cell t (-1)) := by
  have hl := cell_left' t 0
  rw [show (0 : Int) - 1 = -1 by rfl] at hl
  refine ⟨hl, ?_⟩
  rw [hl]
  cases cell (t + 1) 0 <;> cases orCol 0 t <;> rfl

/-- **Track B (`EXACT`) — `FutureWorkEquiv` Forces Both `orCol 0` and `cell · (-1)` Window Agreement
    (`futureWorkEquiv_implies_orCol_and_left_col_agree`)**:
    If `Rule30Prize.center` is `P`-periodic from `T` on (`P > 0`, `t₀ ≥ T`) and the right-half
    return prefixes at `t₁ = t₀ + m₀ * P` and `t₂ = t₀ + (m₀ + q) * P` are
    `FutureWorkEquiv (col0Word t₀ P) k`-equivalent, then for every `s < (k + 1) * P`:
    1. `orCol 0 (t₂ + s) = orCol 0 (t₁ + s)`, and
    2. `cell (t₂ + s) (-1) = cell (t₁ + s) (-1)`. -/
theorem futureWorkEquiv_implies_orCol_and_left_col_agree
    (T P t₀ m₀ q k : Nat)
    (hP : 0 < P)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₀ : T ≤ t₀)
    (hfw : FutureWorkEquiv (col0Word t₀ P) k
      (rowAt (t₀ + (m₀ + q) * P) 1 ((k + 1) * P + 1))
      (rowAt (t₀ + m₀ * P) 1 ((k + 1) * P + 1))) :
    ∀ s : Nat, s < (k + 1) * P →
      orCol 0 (t₀ + (m₀ + q) * P + s) = orCol 0 (t₀ + m₀ * P + s) ∧
      cell (t₀ + (m₀ + q) * P + s) (-1) = cell (t₀ + m₀ * P + s) (-1) := by
  have hperk : ∀ m t, T ≤ t → Rule30Prize.center (t + m * P) = Rule30Prize.center t :=
    periodic_mul hper
  intro s hs
  let j := s / P
  let r := s % P
  have hdiv : P * j + r = s := Nat.div_add_mod s P
  have hr : r < P := Nat.mod_lt s hP
  have hj : j ≤ k := by
    have hmul : P * j < P * (k + 1) := by
      rw [Nat.mul_comm P (k + 1)]
      omega
    have hlt : j < k + 1 := Nat.lt_of_mul_lt_mul_left hmul
    omega
  have hj_fw := hfw j hj
  have hcol1 := col0Word_shift_period_mul T P hper (m₀ + q) P t₀ ht₀
  have hcol2 := col0Word_shift_period_mul T P hper m₀ P t₀ ht₀
  have hlen : P + 1 + (k - j) * P + j * P = (k + 1) * P + 1 := by
    have : (k - j) * P + j * P = k * P := by rw [← Nat.add_mul, Nat.sub_add_cancel hj]
    rw [Nat.succ_mul]; omega
  have hiter1 := iterPeriodReturn_rowAt T P hper j (P + 1 + (k - j) * P) (t₀ + (m₀ + q) * P) (by omega)
  have hiter2 := iterPeriodReturn_rowAt T P hper j (P + 1 + (k - j) * P) (t₀ + m₀ * P) (by omega)
  rw [hcol1, hlen] at hiter1
  rw [hcol2, hlen] at hiter2
  rw [hiter1, hiter2] at hj_fw
  have hor1 := orColWord_rowAt P ((k - j) * P) (t₀ + (m₀ + q) * P + j * P)
  have hor2 := orColWord_rowAt P ((k - j) * P) (t₀ + m₀ * P + j * P)
  have hcol3 : col0Word (t₀ + (m₀ + q) * P + j * P) P = col0Word t₀ P := by
    rw [show t₀ + (m₀ + q) * P + j * P = t₀ + (m₀ + q + j) * P by
      rw [Nat.add_mul (m₀ + q) j P]; omega]
    exact col0Word_shift_period_mul T P hper (m₀ + q + j) P t₀ ht₀
  have hcol4 : col0Word (t₀ + m₀ * P + j * P) P = col0Word t₀ P := by
    rw [show t₀ + m₀ * P + j * P = t₀ + (m₀ + j) * P by
      rw [Nat.add_mul m₀ j P]; omega]
    exact col0Word_shift_period_mul T P hper (m₀ + j) P t₀ ht₀
  rw [hcol3, show (k - j) * P + P + 1 = P + 1 + (k - j) * P by omega] at hor1
  rw [hcol4, show (k - j) * P + P + 1 = P + 1 + (k - j) * P by omega] at hor2
  rw [hor1, hor2] at hj_fw
  have hget := congrArg (fun l => l.getD r false) hj_fw
  rw [col0OrTrace_getD P (t₀ + (m₀ + q) * P + j * P) r hr,
    col0OrTrace_getD P (t₀ + m₀ * P + j * P) r hr] at hget
  have hcomm : P * j = j * P := Nat.mul_comm P j
  have hs1 : t₀ + (m₀ + q) * P + j * P + r = t₀ + (m₀ + q) * P + s := by omega
  have hs2 : t₀ + m₀ * P + j * P + r = t₀ + m₀ * P + s := by omega
  rw [hs1, hs2] at hget
  refine ⟨hget, ?_⟩
  rw [(bilateral_center_conservation (t₀ + (m₀ + q) * P + s)).1,
    (bilateral_center_conservation (t₀ + m₀ * P + s)).1, hget]
  have hc_eq : cell (t₀ + (m₀ + q) * P + s + 1) 0 = cell (t₀ + m₀ * P + s + 1) 0 := by
    have hq := hperk q (t₀ + m₀ * P + s + 1) (by omega)
    unfold Rule30Prize.center at hq
    rwa [show t₀ + m₀ * P + s + 1 + q * P = t₀ + (m₀ + q) * P + s + 1 by
      rw [Nat.add_mul m₀ q P]; omega] at hq
  rw [hc_eq]

/-- **Track B (`EXACT`) — Universal Constructive Linear Re-Entry Horizon Bound
    (`universal_linear_reentry_horizon_bound`)**:
    Directly intersects:
    1. Left-permutive triangular reconstruction (`determine` via `window_jen`),
    2. PSMSL `FutureWorkEquiv` semantics (`futureWorkEquiv_implies_orCol_and_left_col_agree`), and
    3. Single-seed finite initial support (`cell_eq_false_of_lt` vs `cell_left_edge`),
    to prove that for **every** `T, P, t₀, m₀, q, k : Nat` with `P > 0`, `q > 0`, `T ≤ t₀`, and
    `t₀ + (m₀ + q) * P ≤ (k + 1) * P`, the return states at `m₀ + q` and `m₀` **cannot** remain
    `FutureWorkEquiv (col0Word t₀ P) k`-equivalent. -/
theorem universal_linear_reentry_horizon_bound
    (T P t₀ m₀ q k : Nat)
    (hP : 0 < P)
    (hq : 0 < q)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₀ : T ≤ t₀)
    (hbound : t₀ + (m₀ + q) * P ≤ (k + 1) * P) :
    ¬ FutureWorkEquiv (col0Word t₀ P) k
        (rowAt (t₀ + (m₀ + q) * P) 1 ((k + 1) * P + 1))
        (rowAt (t₀ + m₀ * P) 1 ((k + 1) * P + 1)) := by
  intro hfw
  have hperk : ∀ m t, T ≤ t → Rule30Prize.center (t + m * P) = Rule30Prize.center t :=
    periodic_mul hper
  have hor := futureWorkEquiv_implies_orCol_and_left_col_agree T P t₀ m₀ q k hP hper ht₀ hfw
  have hlt : t₀ + m₀ * P < t₀ + (m₀ + q) * P := by
    have hqP : 0 < q * P := Nat.mul_pos hq hP
    rw [Nat.add_mul m₀ q P]
    omega
  refine window_jen (t₁ := t₀ + m₀ * P) (t₂ := t₀ + (m₀ + q) * P) hlt (fun s _ => ?_) (fun s hs => ?_)
  · have hq_per := hperk q (t₀ + m₀ * P + s) (by omega)
    unfold Rule30Prize.center at hq_per
    rw [show t₀ + m₀ * P + s + q * P = t₀ + (m₀ + q) * P + s by
      rw [Nat.add_mul m₀ q P]; omega] at hq_per
    exact hq_per.symm
  · exact (hor s (by omega)).1.symm

/-- **Track B (`EXACT`) — Pairwise Distinctness of `FutureWorkEquiv` Classes Across Any `M`
    Return Steps at Linear Horizon (`periodic_center_distinct_futureWork_classes_at_linear_horizon`)**:
    Under any `P`-periodic center from `T` on (`P > 0`, `t₀ ≥ T`), for every `M : Nat`, every
    horizon `k : Nat` satisfying `t₀ + M * P ≤ (k + 1) * P`, and every pair of distinct return
    indices `m₁ < m₂ < M`, the return states at `m₁` and `m₂` occupy strictly distinct
    `FutureWorkEquiv (col0Word t₀ P) k` equivalence classes. -/
theorem periodic_center_distinct_futureWork_classes_at_linear_horizon
    (T P t₀ M k m₁ m₂ : Nat)
    (hP : 0 < P)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t)
    (ht₀ : T ≤ t₀)
    (hbound : t₀ + M * P ≤ (k + 1) * P)
    (hm12 : m₁ < m₂)
    (hm2 : m₂ < M) :
    ¬ FutureWorkEquiv (col0Word t₀ P) k
        (rowAt (t₀ + m₂ * P) 1 ((k + 1) * P + 1))
        (rowAt (t₀ + m₁ * P) 1 ((k + 1) * P + 1)) := by
  have hq : 0 < m₂ - m₁ := by omega
  have hm2_eq : m₁ + (m₂ - m₁) = m₂ := by omega
  have hmul_eq : (m₁ + (m₂ - m₁)) * P = m₂ * P := by rw [hm2_eq]
  have hle : m₂ * P ≤ M * P := Nat.mul_le_mul_right P (by omega)
  rw [← hm2_eq]
  exact universal_linear_reentry_horizon_bound T P t₀ m₁ (m₂ - m₁) k hP hq hper ht₀ (by omega)

end Rule30ProofClosure
