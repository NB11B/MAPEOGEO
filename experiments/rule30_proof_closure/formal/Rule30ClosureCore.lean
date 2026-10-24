import Ruliology.CellularAutomata.Rule30Prize
import Ruliology.CellularAutomata.Rule30Realization
import Ruliology.CellularAutomata.Rule30MaskedJen
import Ruliology.CellularAutomata.Rule30Diagonals
import Ruliology.CellularAutomata.Rule30BlackRuns

/-!
# `R30-CLOSE-001` Formal Layer — Core Semantics (`Rule30ClosureCore.lean`)

Provides the shared, kernel-verified reference definitions for the three proof-closure tracks:
- Right-half word-driven symbolic evolution (`runWord`, `iterPeriodReturn`, `orColWord`, `FutureWorkEquiv`, `ReEntryAtHorizon`)
- Left-half word-driven symbolic evolution (`rowAtLeft`, `stepLeftRow`, `runLeftWord`, `obsLeftWord`)
- Center-column window extraction (`col0Word`, `col0OrTrace`) and exact soundness bridges to `Rule30Jen.cell`.
-/

namespace Rule30ProofClosure

open Ruliology.CellularAutomata
open Ruliology.CellularAutomata.Rule30Prize
open Ruliology.CellularAutomata.Rule30Realization
open Ruliology.CellularAutomata.Rule30Jen
open Ruliology.CellularAutomata.Rule30MaskedJen
open Ruliology.CellularAutomata.Rule30Diagonals
open Ruliology.CellularAutomata.Rule30BlackRuns

/-- Extracts the length-`L` center driving word `[cell t 0, ..., cell (t + L - 1) 0]`. -/
def col0Word (t : Nat) : Nat → List Bool
  | 0 => []
  | L + 1 => cell t 0 :: col0Word (t + 1) L

/-- Advances a finite right-half prefix `[cell t 1, cell t 2, ...]` through center word `w`. -/
def runWord : List Bool → List Bool → List Bool
  | [], σ => σ
  | c :: cs, σ => runWord cs (stepRow c σ)

/-- Iterates the 1-period return operator `runWord w` `m` times. -/
def iterPeriodReturn (w : List Bool) : Nat → List Bool → List Bool
  | 0, σ => σ
  | m + 1, σ => iterPeriodReturn w m (runWord w σ)

/-- Extracts the masked right-half observation trace `c_s || cell (t + s) 1` across word `w`. -/
def orColWord : List Bool → List Bool → List Bool
  | [], _ => []
  | c :: cs, σ => (c || σ.headD false) :: orColWord cs (stepRow c σ)

/-- Direct `orCol 0` trace over `[t, t + L)`. -/
def col0OrTrace (t : Nat) : Nat → List Bool
  | 0 => []
  | L + 1 => orCol 0 t :: col0OrTrace (t + 1) L

/-- 1-period masked observational equivalence. -/
@[reducible] def MaskedPeriodEquiv (w σ₁ σ₂ : List Bool) : Prop :=
  orColWord w σ₁ = orColWord w σ₂

/-- Horizon-`m` PSMSL future-work equivalence (`≡_{w, m}`). -/
def FutureWorkEquiv (w : List Bool) (m : Nat) (σ₁ σ₂ : List Bool) : Prop :=
  ∀ k : Nat, k ≤ m →
    orColWord w (iterPeriodReturn w k σ₁) = orColWord w (iterPeriodReturn w k σ₂)

/-- Exact delayed information re-entry at horizon `k` (`τ_w(σ₁, σ₂) = k`). -/
def ReEntryAtHorizon (w : List Bool) (k : Nat) (σ₁ σ₂ : List Bool) : Prop :=
  (∀ j : Nat, j < k →
    orColWord w (iterPeriodReturn w j σ₁) = orColWord w (iterPeriodReturn w j σ₂)) ∧
  orColWord w (iterPeriodReturn w k σ₁) ≠ orColWord w (iterPeriodReturn w k σ₂)

/-- Infinite-horizon persistent work-equivalence (`≡_{w, ∞}`). -/
def PersistentWorkEquiv (w σ₁ σ₂ : List Bool) : Prop :=
  ∀ m : Nat, FutureWorkEquiv w m σ₁ σ₂

/-- Extracts the finite left-half row `[cell t p, cell t (p - 1), ..., cell t (p - (n - 1))]`
    ordered from right to left (from boundary `p` outward toward `-t`). -/
def rowAtLeft (t : Nat) (p : Int) : Nat → List Bool
  | 0 => []
  | n + 1 => cell t p :: rowAtLeft t (p - 1) n

theorem length_rowAtLeft (t : Nat) : ∀ (n : Nat) (p : Int), (rowAtLeft t p n).length = n
  | 0, _ => rfl
  | n + 1, p => by simp [rowAtLeft, length_rowAtLeft t n (p - 1)]

/-- One Rule 30 step on a finite left-half row `[x_p, x_{p-1}, ...]` with right neighbor `r`
    at `p + 1`; the result has length one less than the input. -/
def stepLeftRow (r : Bool) : List Bool → List Bool
  | a :: b :: rest => rule b a r :: stepLeftRow a (b :: rest)
  | _ => []

/-- Advances a finite left-half prefix `[cell t (-1), cell t (-2), ...]` through center word `w`. -/
def runLeftWord : List Bool → List Bool → List Bool
  | [], lam => lam
  | c :: cs, lam => runLeftWord cs (stepLeftRow c lam)

/-- Given center word `w = [c_0, ..., c_{L-1}]`, the subsequent center bit `c_after = c_L`,
    and a left-half prefix `lam = [x_{-1}(t), x_{-2}(t), ...]`, computes at each step `s < L`
    the left-reconstructed observation `xor c_{s+1} x_{-1}(t + s)`. -/
def obsLeftWord : List Bool → Bool → List Bool → List Bool
  | [], _, _ => []
  | c :: cs, c_after, lam =>
    let c_next := cs.headD c_after
    xor c_next (lam.headD false) :: obsLeftWord cs c_after (stepLeftRow c lam)

theorem col0Word_shift_period (T P : Nat)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) :
    ∀ (L t : Nat), T ≤ t → col0Word (t + P) L = col0Word t L
  | 0, _, _ => rfl
  | L + 1, t, ht => by
    have h0 : cell (t + P) 0 = cell t 0 := hper t ht
    have ih := col0Word_shift_period T P hper L (t + 1) (by omega)
    rw [show t + 1 + P = t + P + 1 by omega] at ih
    show cell (t + P) 0 :: col0Word (t + P + 1) L = cell t 0 :: col0Word (t + 1) L
    rw [h0, ih]

theorem col0Word_shift_period_mul (T P : Nat)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) :
    ∀ (m L t : Nat), T ≤ t → col0Word (t + m * P) L = col0Word t L
  | 0, L, t, _ => by simp
  | m + 1, L, t, ht => by
    have ih := col0Word_shift_period_mul T P hper m L t ht
    have h1 := col0Word_shift_period T P hper L (t + m * P) (by omega)
    rw [show t + (m + 1) * P = t + m * P + P by rw [Nat.succ_mul]; omega, h1, ih]

theorem runWord_rowAt :
    ∀ (L n t : Nat),
      runWord (col0Word t L) (rowAt t 1 (n + L)) = rowAt (t + L) 1 n
  | 0, n, t => by simp [col0Word, runWord]
  | L + 1, n, t => by
    have hstep : stepRow (cell t 0) (rowAt t 1 (n + L + 1)) = rowAt (t + 1) 1 (n + L) := by
      have h := stepRow_rowAt t (n + L) 1
      rwa [show (1 : Int) - 1 = 0 by rfl] at h
    have ih := runWord_rowAt L n (t + 1)
    show runWord (col0Word (t + 1) L) (stepRow (cell t 0) (rowAt t 1 (n + (L + 1)))) =
      rowAt (t + (L + 1)) 1 n
    rw [show n + (L + 1) = n + L + 1 by omega, hstep, ih,
      show t + 1 + L = t + (L + 1) by omega]

theorem iterPeriodReturn_rowAt (T P : Nat)
    (hper : ∀ t, T ≤ t → Rule30Prize.center (t + P) = Rule30Prize.center t) :
    ∀ (m n t₁ : Nat), T ≤ t₁ →
      iterPeriodReturn (col0Word t₁ P) m (rowAt t₁ 1 (n + m * P)) =
        rowAt (t₁ + m * P) 1 n
  | 0, n, t₁, _ => by simp [iterPeriodReturn]
  | m + 1, n, t₁, ht₁ => by
    have hstep := runWord_rowAt P (n + m * P) t₁
    have hcol : col0Word (t₁ + P) P = col0Word t₁ P :=
      col0Word_shift_period T P hper P t₁ ht₁
    have ih := iterPeriodReturn_rowAt T P hper m n (t₁ + P) (by omega)
    rw [hcol, show t₁ + P + m * P = t₁ + (m + 1) * P by rw [Nat.succ_mul]; omega] at ih
    show iterPeriodReturn (col0Word t₁ P) m
      (runWord (col0Word t₁ P) (rowAt t₁ 1 (n + (m + 1) * P))) =
      rowAt (t₁ + (m + 1) * P) 1 n
    rw [show n + (m + 1) * P = n + m * P + P by rw [Nat.succ_mul]; omega, hstep, ih]

theorem orColWord_rowAt :
    ∀ (L n t : Nat),
      orColWord (col0Word t L) (rowAt t 1 (n + L + 1)) = col0OrTrace t L
  | 0, _, _ => rfl
  | L + 1, n, t => by
    have hstep := stepRow_rowAt t (n + L + 1) 1
    rw [show (1 : Int) - 1 = 0 by rfl] at hstep
    have ih := orColWord_rowAt L n (t + 1)
    rw [show n + (L + 1) + 1 = n + L + 1 + 1 by omega]
    show (cell t 0 || (cell t 1 :: rowAt t (1 + 1) (n + L + 1)).headD false) ::
      orColWord (col0Word (t + 1) L) (stepRow (cell t 0) (rowAt t 1 (n + L + 1 + 1))) =
      orCol 0 t :: col0OrTrace (t + 1) L
    rw [hstep, ih]
    rfl

theorem col0OrTrace_getD :
    ∀ (L t s : Nat), s < L → (col0OrTrace t L).getD s false = orCol 0 (t + s)
  | 0, _, _, hs => absurd hs (Nat.not_lt_zero _)
  | L + 1, t, 0, _ => by simp [col0OrTrace]
  | L + 1, t, s + 1, hs => by
    have ih := col0OrTrace_getD L (t + 1) s (by omega)
    rw [show t + 1 + s = t + (s + 1) by omega] at ih
    exact ih

theorem col0Word_getD :
    ∀ (L t s : Nat), s < L → (col0Word t L).getD s false = cell (t + s) 0
  | 0, _, _, hs => absurd hs (Nat.not_lt_zero _)
  | L + 1, t, 0, _ => by simp [col0Word]
  | L + 1, t, s + 1, hs => by
    have ih := col0Word_getD L (t + 1) s (by omega)
    rw [show t + 1 + s = t + (s + 1) by omega] at ih
    exact ih

end Rule30ProofClosure
