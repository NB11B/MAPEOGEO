import CollatzReduction

/-!
Formal Lean 4 certification for the three Collatz research tracks on top of `fbf5d2b`:
- **Track B (Canonical High-Water Geometry)**:
  - `highWater u v = u + v`
  - Exact conservation on even-Collatz phases: `S' = S`
  - Exact running-maximum law on odd-Collatz phases: `S' = max S (3k + 1)`
  - Exact characterization of the strict-growth regime (`S' > S ↔ v < k + 1`),
    formally falsifying `S` as a descending Lyapunov potential
  - Universal monotonicity `S' ≥ S` across all positive-register phases
- **Track C (Affine Parity-Word Operator Composition & Residue Classes)**:
  - Exact rational/integer affine identity `wordD w * applyParityWord m w = wordA w * m + wordB w`
    for every valid parity word `w : List Bool`
  - Exact residue-class periodicity modulo `wordD w = 2^|w|`: validity is periodic mod `2^|w|`
    and `applyParityWord (m + q * 2^|w|) w = applyParityWord m w + q * 3^(ones w)`
- **Track A (Cycle Rejection & Conditional Well-Founded Potential Gate)**:
  - Cycle equation `wordD w * m = wordA w * m + wordB w` and impossibility of cycles
    whenever `wordA w ≥ wordD w` and `wordB w > 0`
  - Conditional well-founded descent gate: any potential `V : Nat → Nat` that strictly
    decreases along positive-register trajectories forces `RegReachesZero u` for all `u`
    and hence `¬ Quasihalts`.

No axioms, `sorry`, or unproved Collatz claim are introduced.
-/
namespace BBB17

/-! ### Track B: Canonical High-Water Resource Geometry (`S = u + v`) -/

/-- Total right-hand marked cells `S = u + v` (active register plus reservoir). -/
def highWater (u v : Nat) : Nat := u + v

/-- On the even-Collatz branch (`u = 2k + 1`), `S = u + v` is strictly conserved: `S' = S`. -/
theorem evenPhase_highWater_eq (j k v : Nat) :
    highWater (evenPhase j k v).2.1 (evenPhase j k v).2.2 = highWater (2 * k + 1) v := by
  dsimp [highWater, evenPhase]
  omega

/-- On the accelerated odd-Collatz branch (`u = 2k`), `S = u + v` satisfies the exact
    high-water law `S' = max S (3k + 1)`. -/
theorem oddPhase_highWater_eq_max (j k v : Nat) :
    highWater (oddPhase j k v).2.1 (oddPhase j k v).2.2 =
      max (highWater (2 * k) v) (3 * k + 1) := by
  dsimp [highWater, oddPhase]
  omega

/-- Exact characterization of the strict-growth regime for `S = u + v` on the odd-Collatz
    branch: `S' > S` if and only if the reservoir is exhausted (`v < k + 1`).
    (In the bounded sweep `1 ≤ u < 128, 0 ≤ v < 128`, this accounts for all
    `∑_{k=1}^{63} (k + 1) = 2079` strict-growth cases and falsifies `S` as a descending potential.) -/
theorem oddPhase_highWater_strict_growth_iff (j k v : Nat) :
    highWater (oddPhase j k v).2.1 (oddPhase j k v).2.2 > highWater (2 * k) v ↔
      v < k + 1 := by
  dsimp [highWater, oddPhase]
  omega

/-- Across every positive-register phase (`u > 0`), `S = u + v` is nondecreasing (`S' ≥ S`). -/
theorem posReg_highWater_nondecreasing (j u v : Nat) (hu : u > 0) :
    highWater (nextCanonicalTriple j u v).2.1 (nextCanonicalTriple j u v).2.2 ≥
      highWater u v := by
  rcases canon_register_trichotomy u with rfl | ⟨k, rfl⟩ | ⟨k, hk, rfl⟩
  · omega
  · have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    simp [nextCanonicalTriple, hmod, hdiv, highWater, evenPhase]
    omega
  · have hne0 : 2 * k ≠ 0 := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    simp [nextCanonicalTriple, hne0, hdiv, highWater, oddPhase]
    omega

/-- On the reset branch (`u = 0`), the new high-water mark is `max v (j + 1)`. -/
theorem resetPhase_highWater_eq_max (j v : Nat) :
    highWater (resetPhase j v).2.1 (resetPhase j v).2.2 = max v (j + 1) := by
  dsimp [highWater, resetPhase]
  omega

/-! ### Track C: Affine Parity-Word Operator Composition & Residue Classes -/

/-- Parity bit (`false` = even step `m / 2`, `true` = odd step `(3m + 1) / 2`) matches `m`. -/
def stepParityMatches (m : Nat) (b : Bool) : Prop :=
  if b then m % 2 = 1 else m % 2 = 0

/-- A parity word `w : List Bool` is valid for starting integer `m` if each successive
    accelerated Collatz iterate has the parity prescribed by `w`. -/
def validParityWord : Nat → List Bool → Prop
  | _, [] => True
  | m, b :: bs => stepParityMatches m b ∧ validParityWord (acceleratedCollatz m) bs

/-- Result of applying the accelerated Collatz map along a parity word `w`. -/
def applyParityWord : Nat → List Bool → Nat
  | m, [] => m
  | m, _ :: bs => applyParityWord (acceleratedCollatz m) bs

/-- Multiplicative numerator coefficient `A(w) = 3^(ones w)`. -/
def wordA : List Bool → Nat
  | [] => 1
  | false :: bs => wordA bs
  | true :: bs => 3 * wordA bs

/-- Denominator coefficient `D(w) = 2^(length w)`. -/
def wordD : List Bool → Nat
  | [] => 1
  | _ :: bs => 2 * wordD bs

/-- Additive offset coefficient `B(w)` satisfying `D(w) * applyParityWord m w = A(w) * m + B(w)`. -/
def wordB : List Bool → Nat
  | [] => 0
  | false :: bs => 2 * wordB bs
  | true :: bs => wordA bs + 2 * wordB bs

theorem wordD_pos (w : List Bool) : wordD w > 0 := by
  induction w with
  | nil => decide
  | cons b bs ih =>
    unfold wordD
    omega

theorem wordA_pos (w : List Bool) : wordA w > 0 := by
  induction w with
  | nil => decide
  | cons b bs ih =>
    cases b <;> unfold wordA <;> omega

/-- Single-step affine identity for `acceleratedCollatz`. -/
theorem acceleratedCollatz_step_eq (m : Nat) (b : Bool) (h : stepParityMatches m b) :
    2 * acceleratedCollatz m = (if b then 3 * m + 1 else m) := by
  cases b with
  | false =>
    unfold stepParityMatches at h
    dsimp at h
    unfold acceleratedCollatz
    rw [if_pos h]
    dsimp
    omega
  | true =>
    unfold stepParityMatches at h
    dsimp at h
    have hne0 : ¬(m % 2 = 0) := by omega
    unfold acceleratedCollatz
    rw [if_neg hne0]
    dsimp
    omega

/-- Helper ring lemma: `2 * (A * X + B) = A * (2 * X) + 2 * B`. -/
theorem double_linear_comb (A X B : Nat) :
    2 * (A * X + B) = A * (2 * X) + 2 * B := by
  rw [Nat.mul_add, ← Nat.mul_assoc 2 A X, Nat.mul_comm 2 A, Nat.mul_assoc A 2 X]

/-- Helper ring lemma: `A * (3 * m + 1) + 2 * B = (3 * A) * m + (A + 2 * B)`. -/
theorem triple_linear_comb (A m B : Nat) :
    A * (3 * m + 1) + 2 * B = (3 * A) * m + (A + 2 * B) := by
  rw [Nat.mul_add, Nat.mul_one, ← Nat.mul_assoc A 3 m, Nat.mul_comm A 3, Nat.add_assoc]

/-- Exact Affine Parity-Word Identity:
    For every parity word `w : List Bool` and every `m : Nat` satisfying `validParityWord m w`,
    `wordD w * applyParityWord m w = wordA w * m + wordB w`. -/
theorem parityWord_affine_identity (w : List Bool) :
    ∀ m : Nat, validParityWord m w →
      wordD w * applyParityWord m w = wordA w * m + wordB w := by
  induction w with
  | nil =>
    intro m _
    simp [wordD, applyParityWord, wordA, wordB]
  | cons b bs ih =>
    intro m hvalid
    rcases hvalid with ⟨hhead, htail⟩
    have hrec := ih (acceleratedCollatz m) htail
    have hstep := acceleratedCollatz_step_eq m b hhead
    cases b with
    | false =>
      dsimp at hstep
      dsimp [wordD, applyParityWord, wordA, wordB]
      rw [Nat.mul_assoc 2 (wordD bs), hrec, double_linear_comb, hstep]
    | true =>
      dsimp at hstep
      dsimp [wordD, applyParityWord, wordA, wordB]
      rw [Nat.mul_assoc 2 (wordD bs), hrec, double_linear_comb, hstep, triple_linear_comb]

/-- Necessary congruence condition on the residue class of `m` modulo `wordD w = 2^|w|`. -/
theorem parityWord_divisibility (w : List Bool) (m : Nat) (hvalid : validParityWord m w) :
    (wordA w * m + wordB w) % wordD w = 0 := by
  have hid := parityWord_affine_identity w m hvalid
  have hcomm : wordD w * applyParityWord m w = applyParityWord m w * wordD w := Nat.mul_comm _ _
  rw [← hid, hcomm, Nat.mul_mod_left]

/-- Single-step shift by `2 * q` under `acceleratedCollatz`. -/
theorem acceleratedCollatz_add_two_mul (m q : Nat) (b : Bool) (h : stepParityMatches m b) :
    stepParityMatches (m + 2 * q) b ∧
    acceleratedCollatz (m + 2 * q) = acceleratedCollatz m + (if b then 3 * q else q) := by
  cases b with
  | false =>
    unfold stepParityMatches at *
    dsimp at *
    have h2 : (m + 2 * q) % 2 = 0 := by omega
    refine ⟨h2, ?_⟩
    unfold acceleratedCollatz
    rw [if_pos h2, if_pos h]
    omega
  | true =>
    unfold stepParityMatches at *
    dsimp at *
    have h2 : (m + 2 * q) % 2 = 1 := by omega
    have hne1 : ¬(m % 2 = 0) := by omega
    have hne2 : ¬((m + 2 * q) % 2 = 0) := by omega
    refine ⟨h2, ?_⟩
    unfold acceleratedCollatz
    rw [if_neg hne2, if_neg hne1]
    omega

/-- Residue-Class Shift Theorem for Parity Words:
    Adding `q * wordD w = q * 2^|w|` preserves `validParityWord` and shifts the output
    by `q * wordA w = q * 3^(ones w)`. -/
theorem parityWord_residue_shift (w : List Bool) :
    ∀ m q : Nat, validParityWord m w →
      validParityWord (m + q * wordD w) w ∧
      applyParityWord (m + q * wordD w) w = applyParityWord m w + q * wordA w := by
  induction w with
  | nil =>
    intro m q _
    simp [validParityWord, applyParityWord, wordD, wordA]
  | cons b bs ih =>
    intro m q hvalid
    rcases hvalid with ⟨hhead, htail⟩
    have hD : q * wordD (b :: bs) = 2 * (q * wordD bs) := by
      dsimp [wordD]
      rw [← Nat.mul_assoc q 2 (wordD bs), Nat.mul_comm q 2, Nat.mul_assoc 2 q (wordD bs)]
    rw [hD]
    have hstep := acceleratedCollatz_add_two_mul m (q * wordD bs) b hhead
    cases b with
    | false =>
      dsimp at hstep
      rcases ih (acceleratedCollatz m) q htail with ⟨hvalid', hout'⟩
      refine ⟨⟨hstep.1, ?_⟩, ?_⟩
      · rw [hstep.2]
        exact hvalid'
      · dsimp [applyParityWord, wordA]
        rw [hstep.2, hout']
    | true =>
      dsimp at hstep
      have h3 : 3 * (q * wordD bs) = (3 * q) * wordD bs := (Nat.mul_assoc 3 q (wordD bs)).symm
      rcases ih (acceleratedCollatz m) (3 * q) htail with ⟨hvalid', hout'⟩
      refine ⟨⟨hstep.1, ?_⟩, ?_⟩
      · rw [hstep.2, h3]
        exact hvalid'
      · dsimp [applyParityWord, wordA]
        have h3A : (3 * q) * wordA bs = q * (3 * wordA bs) := by
          rw [Nat.mul_comm 3 q, Nat.mul_assoc q 3 (wordA bs)]
        rw [hstep.2, h3, hout', h3A]

/-! ### Track A: Cycle Algebra & Conditional Well-Founded Potential Gate -/

/-- Any fixed point (cycle) of a valid parity word `w` satisfies the linear Diophantine
    equation `wordD w * m = wordA w * m + wordB w`. -/
theorem parityWord_cycle_equation (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hcycle : applyParityWord m w = m) :
    wordD w * m = wordA w * m + wordB w := by
  have hid := parityWord_affine_identity w m hvalid
  rw [hcycle] at hid
  exact hid

/-- Cycle Rejection Theorem: no positive integer `m` can form a cycle along any valid
    parity word `w` with `wordA w ≥ wordD w` (`3^a ≥ 2^r`) and `wordB w > 0`. -/
theorem no_cycle_when_wordA_ge_wordD (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hge : wordA w ≥ wordD w) (hB : wordB w > 0) :
    applyParityWord m w ≠ m := by
  intro hcycle
  have heq := parityWord_cycle_equation w m hvalid hcycle
  have hle : wordD w * m ≤ wordA w * m := Nat.mul_le_mul_right m hge
  omega

/-- Multi-step composition law for `iterateRegStep`. -/
theorem iterateRegStep_add (u a b : Nat) :
    iterateRegStep u (a + b) = iterateRegStep (iterateRegStep u a) b := by
  induction a generalizing u with
  | zero => simp
  | succ a ih =>
    rw [Nat.succ_add, iterateRegStep_succ, ih (collatzRegStep u), ← iterateRegStep_succ]

/-- Helper by bounded induction on the potential value `B`: if `V : Nat → Nat` strictly
    decreases after some number of register steps from every positive register `u > 0`,
    then every `u` with `V u ≤ B` reaches `0`. -/
theorem wellFounded_potential_bounded (V : Nat → Nat)
    (hdesc : ∀ u : Nat, u > 0 → ∃ d : Nat, V (iterateRegStep u d) < V u)
    (B : Nat) :
    ∀ u : Nat, V u ≤ B → RegReachesZero u := by
  induction B with
  | zero =>
    intro u hV
    by_cases hu0 : u = 0
    · subst hu0
      exact ⟨0, rfl⟩
    · rcases hdesc u (by omega) with ⟨d, hd⟩
      omega
  | succ B ih =>
    intro u hV
    by_cases hu0 : u = 0
    · subst hu0
      exact ⟨0, rfl⟩
    · rcases hdesc u (by omega) with ⟨d, hd⟩
      rcases ih (iterateRegStep u d) (by omega) with ⟨n, hn⟩
      refine ⟨d + n, ?_⟩
      rw [iterateRegStep_add u d n, hn]

/-- Conditional Well-Founded Descent Gate:
    Any potential function `V : Nat → Nat` that strictly decreases along positive-register
    trajectories forces every register `u` to reach `0`, which by our certified BBB17
    equivalence guarantees `CollatzConjecture` and `¬ Quasihalts`. -/
theorem wellFounded_potential_forces_reset (V : Nat → Nat)
    (hdesc : ∀ u : Nat, u > 0 → ∃ d : Nat, V (iterateRegStep u d) < V u) :
    (∀ u : Nat, RegReachesZero u) ∧ CollatzConjecture ∧ ¬ Quasihalts := by
  have hall : ∀ u : Nat, RegReachesZero u :=
    fun u => wellFounded_potential_bounded V hdesc (V u) u (Nat.le_refl _)
  have hcollatz : CollatzConjecture := by
    intro m hm
    obtain ⟨u, rfl⟩ : ∃ u : Nat, m = u + 1 := ⟨m - 1, by omega⟩
    exact (regReachesZero_iff_reachesOne u).mp (hall u)
  exact ⟨hall, hcollatz, fun hqh => quasihalts_implies_not_collatz hqh hcollatz⟩

end BBB17
