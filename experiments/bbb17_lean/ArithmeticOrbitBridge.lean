import PhaseArithmetic

/-!
Target 4: Arithmetic orbit bridge, with strict separation between certified
canonical phase transitions and the as-yet-unproved infinite-execution theorem.
No hypothesis that every Collatz orbit terminates is introduced.
-/
namespace BBB17

/-- The accelerated map whose odd step includes the immediately following divide by 2. -/
def acceleratedCollatz (m : Nat) : Nat :=
  if m % 2 = 0 then m / 2 else (3 * m + 1) / 2

/-- The arithmetic projection of a canonical phase state. -/
def canonicalValue (u : Nat) : Nat := u + 1

theorem next_even_register (j k v : Nat) :
    (nextCanonicalTriple j (2 * k + 1) v).2.1 = k := by
  have hpos : 2 * k + 1 ≠ 0 := by omega
  have hmod : (2 * k + 1) % 2 = 1 := by omega
  have hdiv : (2 * k + 1) / 2 = k := by omega
  simp [nextCanonicalTriple, hpos, hmod, hdiv, evenPhase]

theorem next_odd_register (j k v : Nat) (hk : k > 0) :
    (nextCanonicalTriple j (2 * k) v).2.1 = 3 * k + 1 := by
  have hpos : 2 * k ≠ 0 := by omega
  have hmod : (2 * k) % 2 ≠ 1 := by omega
  have hdiv : (2 * k) / 2 = k := by omega
  simp [nextCanonicalTriple, hpos, hmod, hdiv, oddPhase]

theorem next_reset_register (j v : Nat) :
    (nextCanonicalTriple j 0 v).2.1 = j + 1 := by
  simp [nextCanonicalTriple, resetPhase]

/-- Arithmetic soundness of the *defined phase map*.
This does not claim that a complete unbounded execution follows Collatz. -/
theorem next_canonical_value_matches_accelerated
    (j u v : Nat) (hu : 0 < u) :
    canonicalValue (nextCanonicalTriple j u v).2.1 =
      acceleratedCollatz (canonicalValue u) := by
  rcases canon_register_trichotomy u with hzero | ⟨k, hk⟩ | ⟨k, hk, heq⟩
  · omega
  · rw [hk, next_even_register]
    have hmod : (2 * k + 2) % 2 = 0 := by omega
    simp [canonicalValue, acceleratedCollatz, hmod]
    omega
  · rw [heq, next_odd_register j k v hk]
    have hmod : (2 * k + 1) % 2 ≠ 0 := by omega
    simp [canonicalValue, acceleratedCollatz, hmod]
    omega

/-- The reset operation initializes the next starting integer. -/
theorem reset_starts_successor (j v : Nat) :
    canonicalValue (nextCanonicalTriple j 0 v).2.1 = j + 2 := by
  rw [next_reset_register]
  unfold canonicalValue
  omega

/-- Target theorem only: the remaining global statement must connect
all phase boundaries and all beeps of the literal infinite machine run. -/
def GlobalOrbitBridge : Prop :=
  Quasihalts ↔ ¬ CollatzConjecture

end BBB17
