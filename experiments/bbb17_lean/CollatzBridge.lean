/-! Logical reduction obligations for BBB17, distinct from machine correctness. -/
import BBB17
namespace BBB17
def collatz (n : Nat) : Nat :=
  if n % 2 = 0 then n / 2 else 3 * n + 1

def ReachesOne (n : Nat) : Prop :=
  ∃ k : Nat, (Function.iterate collatz k) n = 1

def CollatzConjecture : Prop := ∀ n : Nat, n > 0 → ReachesOne n

def GoodPrefix (bound : Nat) : Prop :=
  ∀ n : Nat, 0 < n → n ≤ bound → ReachesOne n

theorem goodPrefix_of_collatz (h : CollatzConjecture) (N : Nat) :
    GoodPrefix N := by
  intro n hn _
  exact h n hn

theorem bad_input_blocks_larger_prefixes
    (m : Nat) (hm : 0 < m ∧ ¬ ReachesOne m)
    (N : Nat) (hMN : m ≤ N) : ¬ GoodPrefix N := by
  intro h
  exact hm.2 (h m hm.1 hMN)

-- A proof of each implication below requires a certified simulation relation,
-- not merely bounded execution. No axiom or sorry is used to fill these gaps.
def MachineEquivalentToCollatz : Prop :=
  Quasihalts ↔ ¬ CollatzConjecture
end BBB17
