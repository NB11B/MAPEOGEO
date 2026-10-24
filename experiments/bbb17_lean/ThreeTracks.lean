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
  · have hne0 : 2 * k + 1 ≠ 0 := by omega
    have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    unfold nextCanonicalTriple
    rw [if_neg hne0, if_pos hmod, hdiv]
    dsimp [highWater, evenPhase]
    omega
  · have hne0 : 2 * k ≠ 0 := by omega
    have hmod : ¬((2 * k) % 2 = 1) := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    unfold nextCanonicalTriple
    rw [if_neg hne0, if_neg hmod, hdiv]
    dsimp [highWater, oddPhase]
    omega

/-- On every positive-register phase (`u > 0`), the active register of `nextCanonicalTriple`
    evolves by `collatzRegStep u`. -/
theorem nextCanonicalTriple_u_eq_collatzRegStep (j u v : Nat) (hu : u > 0) :
    (nextCanonicalTriple j u v).2.1 = collatzRegStep u := by
  rcases canon_register_trichotomy u with rfl | ⟨k, rfl⟩ | ⟨k, hk, rfl⟩
  · omega
  · have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    simp [nextCanonicalTriple, collatzRegStep, hmod, hdiv, evenPhase]
  · have hne0 : 2 * k ≠ 0 := by omega
    have hmod : (2 * k) % 2 = 0 := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    simp [nextCanonicalTriple, collatzRegStep, hne0, hmod, hdiv, oddPhase]

/-- Unified High-Water Envelope Law:
    Across EVERY positive-register phase (`u > 0`, both even and odd branches),
    the new high-water mark is the running maximum of the previous high-water mark
    `S = u + v` and the next arithmetic register `u' = collatzRegStep u`:
    `S' = max S (collatzRegStep u)`. -/
theorem posReg_highWater_eq_max_next_u (j u v : Nat) (hu : u > 0) :
    highWater (nextCanonicalTriple j u v).2.1 (nextCanonicalTriple j u v).2.2 =
      max (highWater u v) (collatzRegStep u) := by
  rcases canon_register_trichotomy u with rfl | ⟨k, rfl⟩ | ⟨k, hk, rfl⟩
  · omega
  · have hne0 : 2 * k + 1 ≠ 0 := by omega
    have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    simp only [nextCanonicalTriple, collatzRegStep, hne0, hmod, hdiv, ite_false, ite_true,
      evenPhase, highWater]
    omega
  · have hne0 : 2 * k ≠ 0 := by omega
    have hmod : ¬((2 * k) % 2 = 1) := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    simp only [nextCanonicalTriple, collatzRegStep, hne0, hmod, hdiv, ite_false,
      oddPhase, highWater]
    omega

/-- Exact Drawdown Formula for the Reservoir (`v'`):
    After any positive-register phase (`u > 0`), the reservoir `v'` equals the
    drawdown of the arithmetic register below the computational high-water mark:
    `v' = max (u + v) (collatzRegStep u) - collatzRegStep u`. -/
theorem posReg_reservoir_eq_drawdown (j u v : Nat) (hu : u > 0) :
    (nextCanonicalTriple j u v).2.2 =
      max (highWater u v) (collatzRegStep u) - collatzRegStep u := by
  have hS := posReg_highWater_eq_max_next_u j u v hu
  have hu' := nextCanonicalTriple_u_eq_collatzRegStep j u v hu
  dsimp [highWater] at hS ⊢
  omega

/-- Strict High-Water Growth Characterization:
    Across any positive-register phase (`u > 0`), `S' > S` (reservoir exhaustion)
    occurs if and only if the new arithmetic register `collatzRegStep u` strictly
    exceeds the prior high-water mark `S = u + v`. -/
theorem posReg_highWater_strict_growth_iff_record (j u v : Nat) (hu : u > 0) :
    highWater (nextCanonicalTriple j u v).2.1 (nextCanonicalTriple j u v).2.2 >
      highWater u v ↔ collatzRegStep u > highWater u v := by
  rw [posReg_highWater_eq_max_next_u j u v hu]
  omega

/-- High-Water Stability Under Bounded Register Steps:
    Whenever `collatzRegStep u ≤ highWater u v` (in particular, once `S` reaches the
    maximum register value of any bounded trajectory or cycle), `S` is strictly conserved (`S' = S`). -/
theorem posReg_highWater_conserved_when_bounded (j u v : Nat) (hu : u > 0)
    (hbound : collatzRegStep u ≤ highWater u v) :
    highWater (nextCanonicalTriple j u v).2.1 (nextCanonicalTriple j u v).2.2 =
      highWater u v := by
  rw [posReg_highWater_eq_max_next_u j u v hu]
  omega

/-- On the reset branch (`u = 0`), the new high-water mark is `max v (j + 1)`. -/
theorem resetPhase_highWater_eq_max (j v : Nat) :
    highWater (resetPhase j v).2.1 (resetPhase j v).2.2 = max v (j + 1) := by
  dsimp [highWater, resetPhase]
  omega

/-- Universal Three-Phase Max-Plus High-Water Law (`S' = max(S, u')`):
    Across ALL three canonical phases (`u = 0` reset, `u = 2k + 1` even, `u = 2k > 0` odd),
    the updated high-water state `S' = u' + v'` equals `max S u'`. -/
theorem nextCanonicalTriple_highWater_eq_max (j u v : Nat) :
    highWater (nextCanonicalTriple j u v).2.1 (nextCanonicalTriple j u v).2.2 =
      max (highWater u v) (nextCanonicalTriple j u v).2.1 := by
  rcases canon_register_trichotomy u with rfl | ⟨k, rfl⟩ | ⟨k, hk, rfl⟩
  · simp only [nextCanonicalTriple, ite_true, resetPhase, highWater]
    omega
  · have hne0 : 2 * k + 1 ≠ 0 := by omega
    have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    simp only [nextCanonicalTriple, hne0, hmod, hdiv, ite_false, ite_true, evenPhase, highWater]
    omega
  · have hne0 : 2 * k ≠ 0 := by omega
    have hmod : ¬((2 * k) % 2 = 1) := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    simp only [nextCanonicalTriple, hne0, hmod, hdiv, ite_false, oddPhase, highWater]
    omega

/-- Global High-Water Monotonicity (`S' ≥ S`):
    Across ALL three canonical phases (including reset `u = 0`), `S = u + v` is nondecreasing. -/
theorem nextCanonicalTriple_highWater_nondecreasing (j u v : Nat) :
    highWater (nextCanonicalTriple j u v).2.1 (nextCanonicalTriple j u v).2.2 ≥
      highWater u v := by
  rw [nextCanonicalTriple_highWater_eq_max]
  omega

/-- Coordinate map from canonical `(j, u, v)` to high-water coordinates `(j, u, S)` with `S = u + v`. -/
def toHighWaterTriple (t : Nat × Nat × Nat) : Nat × Nat × Nat :=
  (t.1, t.2.1, highWater t.2.1 t.2.2)

/-- Inverse coordinate map from high-water `(j, u, S)` (`S ≥ u`) to `(j, u, v = S - u)`. -/
def fromHighWaterTriple (t : Nat × Nat × Nat) : Nat × Nat × Nat :=
  (t.1, t.2.1, t.2.2 - t.2.1)

theorem fromHighWaterTriple_toHighWaterTriple (j u v : Nat) :
    fromHighWaterTriple (toHighWaterTriple (j, u, v)) = (j, u, v) := by
  simp only [fromHighWaterTriple, toHighWaterTriple, highWater]
  ext <;> dsimp <;> omega

theorem toHighWaterTriple_fromHighWaterTriple (j u S : Nat) (hSu : S ≥ u) :
    toHighWaterTriple (fromHighWaterTriple (j, u, S)) = (j, u, S) := by
  simp only [toHighWaterTriple, fromHighWaterTriple, highWater]
  ext <;> dsimp <;> omega

/-- Canonical phase operator directly in high-water coordinates `(j, u, S)`:
    - `u = 0 ↦ (j + 1, j + 1, max S (j + 1))`
    - `u = 2k + 1 ↦ (j, k, S)`
    - `u = 2k > 0 ↦ (j, 3k + 1, max S (3k + 1))` -/
def nextHighWaterTriple (j u S : Nat) : Nat × Nat × Nat :=
  if u = 0 then
    (j + 1, j + 1, max S (j + 1))
  else if u % 2 = 1 then
    (j, u / 2, S)
  else
    (j, 3 * (u / 2) + 1, max S (3 * (u / 2) + 1))

/-- Exact Conjugacy Theorem (`toHighWaterTriple ∘ nextCanonicalTriple = nextHighWaterTriple`):
    The `(j, u, S)` operator `nextHighWaterTriple` is an exact representation of the
    canonical `(j, u, v)` phase dynamics across all three branches. -/
theorem toHighWaterTriple_nextCanonicalTriple (j u v : Nat) :
    toHighWaterTriple (nextCanonicalTriple j u v) =
      nextHighWaterTriple j u (highWater u v) := by
  rcases canon_register_trichotomy u with rfl | ⟨k, rfl⟩ | ⟨k, hk, rfl⟩
  · simp only [nextCanonicalTriple, nextHighWaterTriple, toHighWaterTriple,
      ite_true, resetPhase, highWater]
    ext <;> dsimp <;> omega
  · have hne0 : 2 * k + 1 ≠ 0 := by omega
    have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    simp only [nextCanonicalTriple, nextHighWaterTriple, toHighWaterTriple,
      hne0, hmod, hdiv, ite_false, ite_true, evenPhase, highWater]
    ext <;> dsimp <;> omega
  · have hne0 : 2 * k ≠ 0 := by omega
    have hmod : ¬((2 * k) % 2 = 1) := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    simp only [nextCanonicalTriple, nextHighWaterTriple, toHighWaterTriple,
      hne0, hmod, hdiv, ite_false, oddPhase, highWater]
    ext <;> dsimp <;> omega

/-- High-water state update operator `H_a(S) = max(S, a)` (Track R7-F). -/
def highWaterOp (a S : Nat) : Nat := max S a

/-- Exact max-plus operator composition law `H_b(H_a(S)) = H_{max(a,b)}(S)`. -/
theorem highWaterOp_comp (a b S : Nat) :
    highWaterOp b (highWaterOp a S) = highWaterOp (max a b) S := by
  dsimp [highWaterOp]
  omega

/-- Commutativity of high-water updates: `H_b(H_a(S)) = H_a(H_b(S))`. -/
theorem highWaterOp_comm (a b S : Nat) :
    highWaterOp b (highWaterOp a S) = highWaterOp a (highWaterOp b S) := by
  dsimp [highWaterOp]
  omega

/-- Idempotence of high-water updates: `H_a(H_a(S)) = H_a(S)`. -/
theorem highWaterOp_idem (a S : Nat) :
    highWaterOp a (highWaterOp a S) = highWaterOp a S := by
  dsimp [highWaterOp]
  omega

/-- `r`-step canonical trajectory iteration on `(j, u, v)`. -/
def iterateCanonicalTriple : Nat → Nat × Nat × Nat → Nat × Nat × Nat
  | 0, t => t
  | r + 1, t => iterateCanonicalTriple r (nextCanonicalTriple t.1 t.2.1 t.2.2)

/-- Sequence of active registers `u₁, …, u_r` visited along `r` canonical macro-steps. -/
def trajectoryNextRegisters : Nat → Nat × Nat × Nat → List Nat
  | 0, _ => []
  | r + 1, t =>
    let t' := nextCanonicalTriple t.1 t.2.1 t.2.2
    t'.2.1 :: trajectoryNextRegisters r t'

/-- Compositional max-fold `max(S₀, u₁, …, u_r)` over a list of active-register values. -/
def foldHighWater : Nat → List Nat → Nat
  | S, [] => S
  | S, u :: us => foldHighWater (max S u) us

/-- Multi-Step Compositional High-Water Law (`S_r = max(S₀, u₁, …, u_r)`):
    After any `r` canonical macro-steps, the high-water state equals the running maximum
    of the initial high-water state `S₀` and the active-register sequence `u₁, …, u_r`,
    without needing intermediate reservoir values `v₁, …, v_{r-1}`. -/
theorem iterateCanonicalTriple_highWater_eq_fold (r : Nat) (t : Nat × Nat × Nat) :
    highWater (iterateCanonicalTriple r t).2.1 (iterateCanonicalTriple r t).2.2 =
      foldHighWater (highWater t.2.1 t.2.2) (trajectoryNextRegisters r t) := by
  induction r generalizing t with
  | zero => rfl
  | succ r ih =>
    dsimp [iterateCanonicalTriple, trajectoryNextRegisters, foldHighWater]
    rw [ih (nextCanonicalTriple t.1 t.2.1 t.2.2),
      nextCanonicalTriple_highWater_eq_max t.1 t.2.1 t.2.2]

/-- Integer linear form `L(j, u, v) = a * j + b * u + c * v` on canonical triples. -/
def linearForm (a b c : Int) (t : Nat × Nat × Nat) : Int :=
  a * (t.1 : Int) + b * (t.2.1 : Int) + c * (t.2.2 : Int)

/-- Three-Witness Universal Linear Invariant No-Go Theorem (Track R7-D):
    Any linear form `a * j + b * u + c * v` preserved across the three witness canonical
    transitions `(0, 1, 0) → (0, 0, 1)`, `(0, 2, 0) → (0, 4, 0)`, and `(0, 0, 0) → (1, 1, 0)`
    must have `a = 0 ∧ b = 0 ∧ c = 0`. -/
theorem no_nontrivial_linear_invariant (a b c : Int)
    (hw1 : linearForm a b c (nextCanonicalTriple 0 1 0) = linearForm a b c (0, 1, 0))
    (hw2 : linearForm a b c (nextCanonicalTriple 0 2 0) = linearForm a b c (0, 2, 0))
    (hw3 : linearForm a b c (nextCanonicalTriple 0 0 0) = linearForm a b c (0, 0, 0)) :
    a = 0 ∧ b = 0 ∧ c = 0 := by
  have h1 : nextCanonicalTriple 0 1 0 = (0, 0, 1) := by decide
  have h2 : nextCanonicalTriple 0 2 0 = (0, 4, 0) := by decide
  have h3 : nextCanonicalTriple 0 0 0 = (1, 1, 0) := by decide
  rw [h1] at hw1
  rw [h2] at hw2
  rw [h3] at hw3
  dsimp [linearForm] at hw1 hw2 hw3
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

/-! ### Binary (`2^r`) vs. Base-7 (`7^k`) Comparison Baseline -/

/-- Any odd shift `s` (`s % 2 = 1`) flips the single-step parity condition `stepParityMatches`. -/
theorem odd_shift_flips_stepParity (m s : Nat) (b : Bool)
    (hs : s % 2 = 1) (h : stepParityMatches m b) :
    ¬ stepParityMatches (m + s) b := by
  cases b <;> unfold stepParityMatches at * <;> dsimp at * <;> omega

/-- Shifting `m` by `7` (or any odd multiple `7 * (2 * k + 1)`, including `7^n`) strictly breaks
    `validParityWord` at the very first step of any non-empty parity word `b :: bs`. -/
theorem base7_odd_shift_breaks_parityWord (m k : Nat) (b : Bool) (bs : List Bool)
    (hvalid : validParityWord m (b :: bs)) :
    ¬ validParityWord (m + 7 * (2 * k + 1)) (b :: bs) := by
  intro hvalid7
  have hs : (7 * (2 * k + 1)) % 2 = 1 := by omega
  exact odd_shift_flips_stepParity m (7 * (2 * k + 1)) b hs hvalid.1 hvalid7.1

/-- Special case `k = 0`: a unit Base-7 shift `m + 7` never shares a non-empty valid parity word with `m`. -/
theorem base7_unit_shift_breaks_parityWord (m : Nat) (b : Bool) (bs : List Bool)
    (hvalid : validParityWord m (b :: bs)) :
    ¬ validParityWord (m + 7) (b :: bs) := by
  have h := base7_odd_shift_breaks_parityWord m 0 b bs hvalid
  simpa using h

/-- Conversely, Base-7 shifts that are multiples of the binary period `7 * q * 2^|w|`
    preserve `validParityWord` and shift the output by `7 * q * 3^(ones w)`. -/
theorem base7_binary_compatible_shift (w : List Bool) (m q : Nat)
    (hvalid : validParityWord m w) :
    validParityWord (m + (7 * q) * wordD w) w ∧
    applyParityWord (m + (7 * q) * wordD w) w = applyParityWord m w + (7 * q) * wordA w :=
  parityWord_residue_shift w m (7 * q) hvalid

/-! ### Track A: Cycle Algebra & Conditional Well-Founded Potential Gate -/

/-- Any fixed point (cycle) of a valid parity word `w` satisfies the linear Diophantine
    equation `wordD w * m = wordA w * m + wordB w`. -/
theorem parityWord_cycle_equation (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hcycle : applyParityWord m w = m) :
    wordD w * m = wordA w * m + wordB w := by
  have hid := parityWord_affine_identity w m hvalid
  rw [hcycle] at hid
  exact hid

/-- Cycle Rejection Theorem (Expanding Regime `3^a ≥ 2^r`):
    no integer `m` can form a cycle along any valid parity word `w`
    with `wordA w ≥ wordD w` and `wordB w > 0`. -/
theorem no_cycle_when_wordA_ge_wordD (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hge : wordA w ≥ wordD w) (hB : wordB w > 0) :
    applyParityWord m w ≠ m := by
  intro hcycle
  have heq := parityWord_cycle_equation w m hvalid hcycle
  have hle : wordD w * m ≤ wordA w * m := Nat.mul_le_mul_right m hge
  omega

/-- Contracting Cycle Gap Equation (`2^r ≥ 3^a`):
    Any cycle `applyParityWord m w = m` of a valid parity word with `wordD w ≥ wordA w`
    satisfies `(wordD w - wordA w) * m = wordB w`. -/
theorem contracting_cycle_gap_eq (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hle : wordA w ≤ wordD w)
    (hcycle : applyParityWord m w = m) :
    (wordD w - wordA w) * m = wordB w := by
  have heq := parityWord_cycle_equation w m hvalid hcycle
  have hsub : (wordD w - wordA w) * m + wordA w * m = wordD w * m := by
    rw [← Nat.add_mul, Nat.sub_add_cancel hle]
  omega

/-- Uniqueness of Contracting Cycles (`2^r > 3^a`):
    At most one natural number `m` can form a cycle for a contracting parity word `w`. -/
theorem contracting_cycle_unique (w : List Bool) (m₁ m₂ : Nat)
    (hgt : wordD w > wordA w)
    (hv₁ : validParityWord m₁ w) (hc₁ : applyParityWord m₁ w = m₁)
    (hv₂ : validParityWord m₂ w) (hc₂ : applyParityWord m₂ w = m₂) :
    m₁ = m₂ := by
  have hle : wordA w ≤ wordD w := by omega
  have hg₁ := contracting_cycle_gap_eq w m₁ hv₁ hle hc₁
  have hg₂ := contracting_cycle_gap_eq w m₂ hv₂ hle hc₂
  have hcomb : (wordD w - wordA w) * m₁ = (wordD w - wordA w) * m₂ := by omega
  exact Nat.eq_of_mul_eq_mul_left (by omega) hcomb

/-- Cycle Rejection by Gap Non-Divisibility (`(2^r - 3^a) ∤ B(w)`):
    In the contracting regime `wordD w > wordA w`, if `wordB w % (wordD w - wordA w) ≠ 0`,
    no integer `m` can form a cycle along `w`. -/
theorem no_cycle_when_gap_not_dvd_B (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hgt : wordD w > wordA w)
    (hndvd : wordB w % (wordD w - wordA w) ≠ 0) :
    applyParityWord m w ≠ m := by
  intro hcycle
  have hg := contracting_cycle_gap_eq w m hvalid (by omega) hcycle
  have hmod : ((wordD w - wordA w) * m) % (wordD w - wordA w) = 0 := by
    rw [Nat.mul_comm, Nat.mul_mod_left]
  rw [hg] at hmod
  exact hndvd hmod

/-- Exact Candidate Formula for Contracting Cycles:
    If `m` forms a cycle for a contracting parity word `w` (`wordD w > wordA w`),
    then `m = wordB w / (wordD w - wordA w)`. -/
theorem contracting_cycle_eq_quotient (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hgt : wordD w > wordA w)
    (hcycle : applyParityWord m w = m) :
    m = wordB w / (wordD w - wordA w) := by
  have hg := contracting_cycle_gap_eq w m hvalid (by omega) hcycle
  have hpos : wordD w - wordA w > 0 := by omega
  rw [← hg, Nat.mul_comm, Nat.mul_div_left m hpos]

/-- Cycle Rejection by Parity-Cylinder Mismatch:
    In the contracting regime `wordD w > wordA w`, if the unique rational quotient
    `m₀ = wordB w / (wordD w - wordA w)` does not satisfy `validParityWord m₀ w`,
    then no integer `m` can form a cycle along `w`. -/
theorem no_cycle_when_quotient_invalid (w : List Bool) (m : Nat)
    (hvalid : validParityWord m w) (hgt : wordD w > wordA w)
    (hinv : ¬ validParityWord (wordB w / (wordD w - wordA w)) w) :
    applyParityWord m w ≠ m := by
  intro hcycle
  have hm := contracting_cycle_eq_quotient w m hvalid hgt hcycle
  rw [hm] at hvalid
  exact hinv hvalid

/-- Nontrivial Cycle Rejection when Quotient `≤ 1`:
    If `wordD w > wordA w` and `wordB w / (wordD w - wordA w) ≤ 1`,
    no integer `m > 1` can form a cycle along `w`. -/
theorem no_nontrivial_cycle_when_quotient_le_one (w : List Bool) (m : Nat)
    (hm : m > 1) (hvalid : validParityWord m w) (hgt : wordD w > wordA w)
    (hq : wordB w / (wordD w - wordA w) ≤ 1) :
    applyParityWord m w ≠ m := by
  intro hcycle
  have heq := contracting_cycle_eq_quotient w m hvalid hgt hcycle
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

/-! ### BBB17-R7-001 Gate 2: Corrected Reset Execution Cost Polynomial (`2j^2 + 8j + 6`) -/

/-- Exact step count of the `a`-pass reset loop starting from state `M` at head `s`:
    `2 * a * (a + s) + 8 * a + s + 4`. -/
def resetLoopSteps (a s : Nat) : Nat :=
  2 * a * (a + s) + 8 * a + s + 4

/-- Exact step count of the complete reset phase (`u = 0`) from `canonConfig j 0 v`:
    `T_reset(j) = 2 * j^2 + 8 * j + 6`. -/
def resetPhaseSteps (j : Nat) : Nat :=
  2 * j * j + 8 * j + 6

/-- Previous handoff reset polynomial `j^2 + 8j + 6` (falsified for all `j > 0`). -/
def handoffResetPoly (j : Nat) : Nat :=
  j * j + 8 * j + 6

theorem resetLoopSteps_zero (s : Nat) :
    resetLoopSteps 0 s = s + 4 := by
  dsimp [resetLoopSteps]
  omega

theorem resetLoopSteps_succ (a s : Nat) :
    (2 * a + 2 * s + 9) + resetLoopSteps a (s + 1) = resetLoopSteps (a + 1) s := by
  dsimp [resetLoopSteps]
  have h1 : 2 * a * (a + (s + 1)) = 2 * a * (a + s) + 2 * a := by
    have hs : a + (s + 1) = (a + s) + 1 := by omega
    rw [hs, Nat.mul_add, Nat.mul_one]
  have h2 : 2 * (a + 1) * (a + 1 + s) = 2 * a * (a + s) + 2 * (a + s) + 2 * (a + 1) := by
    have hs : a + 1 + s = (a + s) + 1 := by omega
    have ha : 2 * (a + 1) = 2 * a + 2 := by omega
    rw [hs, Nat.mul_add, Nat.mul_one, ha, Nat.add_mul]
  omega

theorem two_add_resetLoopSteps_zero (j : Nat) :
    2 + resetLoopSteps j 0 = resetPhaseSteps j := by
  dsimp [resetLoopSteps, resetPhaseSteps]
  omega

/-- Exact cost and beep theorem for the `a`-pass reset loop:
    In `resetLoopSteps a s = 2*a*(a+s) + 8*a + s + 4` steps, the machine visits
    beep state `O` (14) `a + 1` times, emits its terminal beep at `resetLoopSteps a s - 1`,
    and reaches state `A` at head `0` on `updateTape (resetTape 0 (a + s) v) (-2) true`. -/
theorem reset_loop_run_exact_cost_and_beeps (a s v : Nat) :
    beepsInSteps (resetLoopSteps a s) ⟨(12 : State), (s : Int), resetTape a s v⟩ = a + 1 ∧
    exitBeep (iterateStep (resetLoopSteps a s - 1) ⟨(12 : State), (s : Int), resetTape a s v⟩) ∧
    iterateStep (resetLoopSteps a s) ⟨(12 : State), (s : Int), resetTape a s v⟩ =
      ⟨(0 : State), 0, updateTape (resetTape 0 (a + s) v) (-2 : Int) true⟩ := by
  induction a generalizing s with
  | zero =>
    rw [resetLoopSteps_zero]
    refine ⟨reset_loop_base_beeps_one s v, ?_, ?_⟩
    · have hsub : (s + 4) - 1 = s + 3 := by omega
      rw [hsub, reset_loop_base_to_beep s v]
      rfl
    · have hsplit : s + 4 = (s + 3) + 1 := by omega
      rw [hsplit, iterateStep_add (s + 3) 1, reset_loop_base_to_beep s v, iterateStep_one]
      simpa using reset_loop_beep_to_A s v
  | succ a ih =>
    rcases ih (s + 1) with ⟨hbeeps, hbeep, hrun⟩
    rw [← resetLoopSteps_succ a s]
    have hpos : resetLoopSteps a (s + 1) ≥ 4 := by
      dsimp [resetLoopSteps]; omega
    refine ⟨?_, ?_, ?_⟩
    · rw [beepsInSteps_add (2 * a + 2 * s + 9) (resetLoopSteps a (s + 1)),
        reset_loop_pass_beeps_one a s v, reset_loop_pass a s v, hbeeps]
      omega
    · have hsub : (2 * a + 2 * s + 9) + resetLoopSteps a (s + 1) - 1 =
        (2 * a + 2 * s + 9) + (resetLoopSteps a (s + 1) - 1) := by omega
      rw [hsub, iterateStep_add (2 * a + 2 * s + 9) (resetLoopSteps a (s + 1) - 1),
        reset_loop_pass a s v]
      exact hbeep
    · rw [iterateStep_add (2 * a + 2 * s + 9) (resetLoopSteps a (s + 1)),
        reset_loop_pass a s v, hrun]
      have has : a + (s + 1) = a + 1 + s := by omega
      rw [has]

/-- Certified Reset Execution Cost and Beep Theorem (`T_reset(j) = 2j^2 + 8j + 6`):
    From `canonConfig j 0 v`, the BBB17 machine takes **exactly `2 * j * j + 8 * j + 6` steps**,
    emits **exactly `j + 1` beeps** (with the terminal beep at step `2 * j * j + 8 * j + 5`),
    and arrives at `canonConfig (j + 1) (j + 1) (v - (j + 1))`. -/
theorem resetPhase_exact_cost_and_beeps (j v : Nat) :
    beepsInSteps (resetPhaseSteps j) (canonConfig j 0 v) = j + 1 ∧
    exitBeep (iterateStep (resetPhaseSteps j - 1) (canonConfig j 0 v)) ∧
    iterateStep (resetPhaseSteps j) (canonConfig j 0 v) =
      canonConfig (resetPhase j v).1 (resetPhase j v).2.1 (resetPhase j v).2.2 := by
  rcases reset_loop_run_exact_cost_and_beeps j 0 v with ⟨hbeeps, hbeep, hrun⟩
  rw [← two_add_resetLoopSteps_zero j]
  have hpos : resetLoopSteps j 0 ≥ 4 := by
    dsimp [resetLoopSteps]; omega
  refine ⟨?_, ?_, ?_⟩
  · rw [beepsInSteps_add 2 (resetLoopSteps j 0), reset_init_beeps_zero j v,
      resetPhase_init_two_steps j v, hbeeps, Nat.zero_add]
  · have hsub : 2 + resetLoopSteps j 0 - 1 = 2 + (resetLoopSteps j 0 - 1) := by omega
    rw [hsub, iterateStep_add 2 (resetLoopSteps j 0 - 1), resetPhase_init_two_steps j v]
    exact hbeep
  · rw [iterateStep_add 2 (resetLoopSteps j 0), resetPhase_init_two_steps j v, hrun]
    have hj0 : j + 0 = j := by omega
    rw [hj0]
    simp only [canonConfig, resetPhase]
    congr 1
    funext i; rw [Bool_eq_iff]
    simp only [updateTape_true_iff, resetTape_true_iff, canonTape_true_iff]
    omega

/-- Exact discrepancy between the true reset cost `2j^2 + 8j + 6` and the falsified
    handoff polynomial `j^2 + 8j + 6`: the difference is `j^2`. -/
theorem resetPhaseSteps_sub_handoffResetPoly (j : Nat) :
    resetPhaseSteps j - handoffResetPoly j = j * j := by
  dsimp [resetPhaseSteps, handoffResetPoly]
  have h2 : 2 * j * j = j * j + j * j := by
    rw [Nat.succ_mul 1 j, Nat.one_mul, Nat.add_mul]
  omega

/-- Formal falsification of `handoffResetPoly`: for every `j > 0`,
    `resetPhaseSteps j ≠ j^2 + 8j + 6`. -/
theorem resetPhaseSteps_ne_handoffResetPoly (j : Nat) (hj : j > 0) :
    resetPhaseSteps j ≠ handoffResetPoly j := by
  have hpos : j * j > 0 := Nat.mul_pos hj hj
  have hsub := resetPhaseSteps_sub_handoffResetPoly j
  omega

/-! ### BBB17-R7-001 Gate 3: Parity-Word Residue Bijection Modulo `2^r` -/

/-- Deterministic extraction of the length-`r` accelerated Collatz parity word of `m`. -/
def parityWordOf : Nat → Nat → List Bool
  | 0, _ => []
  | r + 1, m => (m % 2 == 1) :: parityWordOf r (acceleratedCollatz m)

theorem parityWordOf_length (r m : Nat) : (parityWordOf r m).length = r := by
  induction r generalizing m with
  | zero => rfl
  | succ r ih =>
    dsimp [parityWordOf]
    rw [ih]

theorem stepParityMatches_of_beq (m : Nat) :
    stepParityMatches m (m % 2 == 1) := by
  by_cases h : m % 2 = 1
  · have hb : (m % 2 == 1) = true := beq_iff_eq.mpr h
    rw [hb]
    dsimp [stepParityMatches]
    exact h
  · have hb : (m % 2 == 1) = false := beq_false_of_ne h
    rw [hb]
    dsimp [stepParityMatches]
    omega

theorem parityWordOf_valid (r m : Nat) :
    validParityWord m (parityWordOf r m) := by
  induction r generalizing m with
  | zero => trivial
  | succ r ih =>
    dsimp [parityWordOf, validParityWord]
    exact ⟨stepParityMatches_of_beq m, ih (acceleratedCollatz m)⟩

theorem stepParityMatches_unique (m : Nat) (b₁ b₂ : Bool)
    (h₁ : stepParityMatches m b₁) (h₂ : stepParityMatches m b₂) :
    b₁ = b₂ := by
  cases b₁ <;> cases b₂
  · rfl
  · dsimp [stepParityMatches] at h₁ h₂; omega
  · dsimp [stepParityMatches] at h₁ h₂; omega
  · rfl

theorem validParityWord_unique (w₁ w₂ : List Bool) (m : Nat)
    (hlen : w₁.length = w₂.length)
    (hv₁ : validParityWord m w₁) (hv₂ : validParityWord m w₂) :
    w₁ = w₂ := by
  induction w₁ generalizing w₂ m with
  | nil =>
    cases w₂ with
    | nil => rfl
    | cons _ _ => contradiction
  | cons b₁ bs₁ ih =>
    cases w₂ with
    | nil => contradiction
    | cons b₂ bs₂ =>
      dsimp at hlen
      rcases hv₁ with ⟨hp₁, ht₁⟩
      rcases hv₂ with ⟨hp₂, ht₂⟩
      have hb : b₁ = b₂ := stepParityMatches_unique m b₁ b₂ hp₁ hp₂
      have hbs : bs₁ = bs₂ := ih bs₂ (acceleratedCollatz m) (by omega) ht₁ ht₂
      rw [hb, hbs]

theorem validParityWord_iff_eq_parityWordOf (w : List Bool) (m : Nat) :
    validParityWord m w ↔ parityWordOf w.length m = w := by
  constructor
  · intro hv
    exact validParityWord_unique (parityWordOf w.length m) w m
      (parityWordOf_length w.length m) (parityWordOf_valid w.length m) hv
  · intro heq
    rw [← heq]
    exact parityWordOf_valid w.length m

/-- Constructive odd-branch modular lift: given `D = 2^s` (`D % 3 ≠ 0`) and `R < D`,
    selects `q ∈ {0, 1, 2}` such that `R + q * D ≡ 2 (mod 3)` and returns
    `m = 2 * ((R + q * D - 2) / 3) + 1 < 2 * D`, satisfying `acceleratedCollatz m = R + q * D`. -/
def oddStepLift (D R : Nat) : Nat :=
  let q := if R % 3 = 2 then 0 else if (R + D) % 3 = 2 then 1 else 2
  2 * ((R + q * D - 2) / 3) + 1

/-- Canonical minimal non-negative residue representative `wordResidue w < wordD w`
    for any parity word `w : List Bool`. -/
def wordResidue : List Bool → Nat
  | [] => 0
  | false :: bs => 2 * wordResidue bs
  | true :: bs => oddStepLift (wordD bs) (wordResidue bs)

theorem wordD_mod_three (w : List Bool) : wordD w % 3 = 1 ∨ wordD w % 3 = 2 := by
  induction w with
  | nil =>
    dsimp [wordD]
    omega
  | cons b bs ih =>
    dsimp [wordD]
    omega

theorem oddStepLift_spec (D R : Nat) (hD : D % 3 = 1 ∨ D % 3 = 2) (hR : R < D) :
    oddStepLift D R < 2 * D ∧
    stepParityMatches (oddStepLift D R) true ∧
    ∃ q : Nat, acceleratedCollatz (oddStepLift D R) = R + q * D := by
  dsimp [oddStepLift]
  by_cases h0 : R % 3 = 2
  · rw [if_pos h0]
    refine ⟨by omega, ?_, 0, ?_⟩
    · dsimp [stepParityMatches]; omega
    · unfold acceleratedCollatz
      have hodd : ¬((2 * ((R + 0 * D - 2) / 3) + 1) % 2 = 0) := by omega
      rw [if_neg hodd]
      omega
  · rw [if_neg h0]
    by_cases h1 : (R + D) % 3 = 2
    · rw [if_pos h1]
      refine ⟨by omega, ?_, 1, ?_⟩
      · dsimp [stepParityMatches]; omega
      · unfold acceleratedCollatz
        have hodd : ¬((2 * ((R + 1 * D - 2) / 3) + 1) % 2 = 0) := by omega
        rw [if_neg hodd]
        omega
    · rw [if_neg h1]
      refine ⟨by omega, ?_, 2, ?_⟩
      · dsimp [stepParityMatches]; omega
      · unfold acceleratedCollatz
        have hodd : ¬((2 * ((R + 2 * D - 2) / 3) + 1) % 2 = 0) := by omega
        rw [if_neg hodd]
        omega

/-- Every parity word `w` has a canonical representative `wordResidue w < wordD w = 2^|w|`
    satisfying `validParityWord (wordResidue w) w`. -/
theorem wordResidue_spec (w : List Bool) :
    wordResidue w < wordD w ∧ validParityWord (wordResidue w) w := by
  induction w with
  | nil =>
    dsimp [wordResidue, wordD, validParityWord]
    exact ⟨by omega, trivial⟩
  | cons b bs ih =>
    rcases ih with ⟨hlt, hvalid⟩
    cases b with
    | false =>
      dsimp [wordResidue, wordD, validParityWord]
      refine ⟨by omega, ?_, ?_⟩
      · dsimp [stepParityMatches]; omega
      · have hc : acceleratedCollatz (2 * wordResidue bs) = wordResidue bs := by
          unfold acceleratedCollatz
          have hev : (2 * wordResidue bs) % 2 = 0 := by omega
          rw [if_pos hev]
          omega
        rw [hc]
        exact hvalid
    | true =>
      dsimp [wordResidue, wordD, validParityWord]
      rcases oddStepLift_spec (wordD bs) (wordResidue bs) (wordD_mod_three bs) hlt
        with ⟨hlt', hp', q, hq⟩
      refine ⟨hlt', hp', ?_⟩
      rw [hq]
      exact (parityWord_residue_shift bs (wordResidue bs) q hvalid).1

theorem wordResidue_lt_wordD (w : List Bool) : wordResidue w < wordD w :=
  (wordResidue_spec w).1

theorem wordResidue_valid (w : List Bool) : validParityWord (wordResidue w) w :=
  (wordResidue_spec w).2

/-- Coprimality of `3` and `2^|w|`: if `2^|w|` divides `3 * d`, then `2^|w|` divides `d`. -/
theorem three_mul_mod_wordD_eq_zero (w : List Bool) (d : Nat)
    (h : (3 * d) % wordD w = 0) : d % wordD w = 0 := by
  induction w generalizing d with
  | nil =>
    dsimp [wordD]
    omega
  | cons b bs ih =>
    dsimp [wordD] at h ⊢
    have hmod2 : (2 * wordD bs) % 2 = 0 := by omega
    have h3even : (3 * d) % 2 = 0 := by
      have hdvd : wordD bs * 2 ∣ 3 * d := by
        rw [Nat.mul_comm]
        exact Nat.dvd_of_mod_eq_zero h
      have h2dvd : 2 ∣ 3 * d := Nat.dvd_trans (Nat.dvd_mul_left 2 (wordD bs)) hdvd
      exact Nat.mod_eq_zero_of_dvd h2dvd
    have hd_eq : d = 2 * (d / 2) := by omega
    have h3 : (3 * (d / 2)) % wordD bs = 0 := by
      have hmul : 3 * d = 2 * (3 * (d / 2)) := by omega
      rw [hmul, Nat.mul_mod_mul_left] at h
      omega
    have ih_d := ih (d / 2) h3
    rw [hd_eq, Nat.mul_mod_mul_left, ih_d]

/-- Any two natural numbers `m₁ ≤ m₂` sharing a valid parity word `w` are congruent mod `wordD w`. -/
theorem validParityWord_sub_mod_wordD_eq_zero (w : List Bool) :
    ∀ m₁ m₂ : Nat, validParityWord m₁ w → validParityWord m₂ w → m₁ ≤ m₂ →
      (m₂ - m₁) % wordD w = 0 := by
  induction w with
  | nil =>
    intro m₁ m₂ _ _ _
    dsimp [wordD]
    omega
  | cons b bs ih =>
    intro m₁ m₂ hv₁ hv₂ hle
    rcases hv₁ with ⟨hp₁, ht₁⟩
    rcases hv₂ with ⟨hp₂, ht₂⟩
    dsimp [wordD]
    cases b with
    | false =>
      dsimp [stepParityMatches] at hp₁ hp₂
      have hc₁ : acceleratedCollatz m₁ = m₁ / 2 := by
        unfold acceleratedCollatz; rw [if_pos hp₁]
      have hc₂ : acceleratedCollatz m₂ = m₂ / 2 := by
        unfold acceleratedCollatz; rw [if_pos hp₂]
      rw [hc₁] at ht₁
      rw [hc₂] at ht₂
      have hih := ih (m₁ / 2) (m₂ / 2) ht₁ ht₂ (by omega)
      have hsub : m₂ - m₁ = 2 * (m₂ / 2 - m₁ / 2) := by omega
      rw [hsub, Nat.mul_mod_mul_left, hih]
    | true =>
      dsimp [stepParityMatches] at hp₁ hp₂
      have hne₁ : ¬(m₁ % 2 = 0) := by omega
      have hne₂ : ¬(m₂ % 2 = 0) := by omega
      have hc₁ : acceleratedCollatz m₁ = 3 * (m₁ / 2) + 2 := by
        unfold acceleratedCollatz; rw [if_neg hne₁]; omega
      have hc₂ : acceleratedCollatz m₂ = 3 * (m₂ / 2) + 2 := by
        unfold acceleratedCollatz; rw [if_neg hne₂]; omega
      rw [hc₁] at ht₁
      rw [hc₂] at ht₂
      have hih := ih (3 * (m₁ / 2) + 2) (3 * (m₂ / 2) + 2) ht₁ ht₂ (by omega)
      have h3 : (3 * (m₂ / 2 - m₁ / 2)) % wordD bs = 0 := by
        have heq : (3 * (m₂ / 2) + 2) - (3 * (m₁ / 2) + 2) = 3 * (m₂ / 2 - m₁ / 2) := by omega
        rw [← heq]
        exact hih
      have hd := three_mul_mod_wordD_eq_zero bs (m₂ / 2 - m₁ / 2) h3
      have hsub : m₂ - m₁ = 2 * (m₂ / 2 - m₁ / 2) := by omega
      rw [hsub, Nat.mul_mod_mul_left, hd]

/-- Uniqueness of the residue representative `< wordD w` for any parity word `w`. -/
theorem validParityWord_eq_of_lt_wordD (w : List Bool) (r₁ r₂ : Nat)
    (hr₁ : r₁ < wordD w) (hr₂ : r₂ < wordD w)
    (hv₁ : validParityWord r₁ w) (hv₂ : validParityWord r₂ w) :
    r₁ = r₂ := by
  by_cases hle : r₁ ≤ r₂
  · have hmod := validParityWord_sub_mod_wordD_eq_zero w r₁ r₂ hv₁ hv₂ hle
    have hlt : r₂ - r₁ < wordD w := by omega
    have hzero : r₂ - r₁ = 0 := by
      rw [← Nat.mod_eq_of_lt hlt]
      exact hmod
    omega
  · have hle' : r₂ ≤ r₁ := by omega
    have hmod := validParityWord_sub_mod_wordD_eq_zero w r₂ r₁ hv₂ hv₁ hle'
    have hlt : r₁ - r₂ < wordD w := by omega
    have hzero : r₁ - r₂ = 0 := by
      rw [← Nat.mod_eq_of_lt hlt]
      exact hmod
    omega

theorem wordD_eq_pow_two_length (w : List Bool) :
    wordD w = 2 ^ w.length := by
  induction w with
  | nil => rfl
  | cons _ bs ih =>
    dsimp [wordD]
    rw [ih, Nat.pow_succ, Nat.mul_comm]

theorem wordD_eq_of_length_eq (w₁ w₂ : List Bool) (h : w₁.length = w₂.length) :
    wordD w₁ = wordD w₂ := by
  rw [wordD_eq_pow_two_length w₁, wordD_eq_pow_two_length w₂, h]

/-- Exact Parity-Word Residue Bijection Theorem (`validParityWord m w ↔ m % 2^|w| = wordResidue w`):
    For every parity word `w : List Bool` and every natural number `m : Nat`,
    `m` has parity word `w` if and only if `m` belongs to the unique residue class
    `wordResidue w` modulo `wordD w = 2^|w|`. -/
theorem validParityWord_iff_mod_eq_wordResidue (w : List Bool) (m : Nat) :
    validParityWord m w ↔ m % wordD w = wordResidue w := by
  constructor
  · intro hv
    let r := m % wordD w
    let q := m / wordD w
    let w' := parityWordOf w.length r
    have hlen' : w'.length = w.length := parityWordOf_length w.length r
    have hD' : wordD w' = wordD w := wordD_eq_of_length_eq w' w hlen'
    have hvr : validParityWord r w' := parityWordOf_valid w.length r
    have hvm' : validParityWord (r + q * wordD w') w' :=
      (parityWord_residue_shift w' r q hvr).1
    have hdecomp : r + q * wordD w' = m := by
      rw [hD', Nat.mul_comm q (wordD w)]
      exact (Nat.mod_add_div m (wordD w))
    rw [hdecomp] at hvm'
    have hw_eq : w' = w := validParityWord_unique w' w m hlen' hvm' hv
    rw [hw_eq] at hvr
    have hr_lt : r < wordD w := Nat.mod_lt m (wordD_pos w)
    exact validParityWord_eq_of_lt_wordD w r (wordResidue w) hr_lt
      (wordResidue_lt_wordD w) hvr (wordResidue_valid w)
  · intro hmod
    have hdecomp : wordResidue w + (m / wordD w) * wordD w = m := by
      rw [← hmod, Nat.mul_comm (m / wordD w) (wordD w)]
      exact Nat.mod_add_div m (wordD w)
    rw [← hdecomp]
    exact (parityWord_residue_shift w (wordResidue w) (m / wordD w) (wordResidue_valid w)).1

/-- Left inverse of the bijection between length-`r` parity words and residues `< 2^r`. -/
theorem parityWordOf_wordResidue (w : List Bool) :
    parityWordOf w.length (wordResidue w) = w :=
  (validParityWord_iff_eq_parityWordOf w (wordResidue w)).mp (wordResidue_valid w)

/-- Right inverse of the bijection between residues `m < 2^r` and length-`r` parity words. -/
theorem wordResidue_parityWordOf (r m : Nat) (hm : m < 2 ^ r) :
    wordResidue (parityWordOf r m) = m := by
  let w := parityWordOf r m
  have hD : wordD w = 2 ^ r := by
    rw [wordD_eq_pow_two_length w, parityWordOf_length r m]
  have hm_lt : m < wordD w := by omega
  exact validParityWord_eq_of_lt_wordD w (wordResidue w) m
    (wordResidue_lt_wordD w) hm_lt (wordResidue_valid w) (parityWordOf_valid r m)

/-! ### BBB17-R7-001 Gate 4: Mechanized Length-7 Operator Catalog Check -/

/-- Decidable boolean version of `stepParityMatches`. -/
def stepParityMatchesBool (m : Nat) (b : Bool) : Bool :=
  if b then m % 2 == 1 else m % 2 == 0

/-- Decidable boolean version of `validParityWord`. -/
def validParityWordBool : Nat → List Bool → Bool
  | _, [] => true
  | m, b :: bs => stepParityMatchesBool m b && validParityWordBool (acceleratedCollatz m) bs

theorem stepParityMatchesBool_eq_true_iff (m : Nat) (b : Bool) :
    stepParityMatchesBool m b = true ↔ stepParityMatches m b := by
  cases b <;> dsimp [stepParityMatchesBool, stepParityMatches] <;> exact beq_iff_eq

theorem validParityWordBool_eq_true_iff (w : List Bool) :
    ∀ m : Nat, validParityWordBool m w = true ↔ validParityWord m w := by
  induction w with
  | nil =>
    intro m
    simp [validParityWordBool, validParityWord]
  | cons b bs ih =>
    intro m
    dsimp [validParityWordBool, validParityWord]
    rw [Bool.and_eq_true, stepParityMatchesBool_eq_true_iff, ih (acceleratedCollatz m)]

/-- Complete enumeration of all `2^r` parity words of length `r`. -/
def allParityWords : Nat → List (List Bool)
  | 0 => [[]]
  | r + 1 => (allParityWords r).map (false :: ·) ++ (allParityWords r).map (true :: ·)

/-- Decidable positive fixed-point rejection certificate for a parity word `w`:
    returns `true` if either `w` is expanding (`wordA w ≥ wordD w` with `wordB w > 0`)
    or `w` is contracting (`wordD w > wordA w`) and the unique rational candidate
    `q = wordB w / (wordD w - wordA w)` fails divisibility, positivity, or parity validity. -/
def wordRejectsPosCycle (w : List Bool) : Bool :=
  if wordA w ≥ wordD w then
    decide (wordB w > 0)
  else
    let gap := wordD w - wordA w
    let q := wordB w / gap
    decide (wordB w % gap ≠ 0) || decide (q = 0) || !validParityWordBool q w

/-- Soundness of `wordRejectsPosCycle`: if `wordRejectsPosCycle w = true`, then
    no positive integer `m > 0` can be a valid fixed point of `w`. -/
theorem wordRejectsPosCycle_sound (w : List Bool)
    (hcert : wordRejectsPosCycle w = true) (m : Nat) (hm : m > 0)
    (hvalid : validParityWord m w) :
    applyParityWord m w ≠ m := by
  unfold wordRejectsPosCycle at hcert
  by_cases hge : wordA w ≥ wordD w
  · rw [if_pos hge] at hcert
    have hB : wordB w > 0 := of_decide_eq_true hcert
    exact no_cycle_when_wordA_ge_wordD w m hvalid hge hB
  · rw [if_neg hge] at hcert
    have hgt : wordD w > wordA w := by omega
    intro hcycle
    have hq_eq : m = wordB w / (wordD w - wordA w) :=
      contracting_cycle_eq_quotient w m hvalid hgt hcycle
    by_cases hdvd : wordB w % (wordD w - wordA w) = 0
    · have hvb : validParityWordBool (wordB w / (wordD w - wordA w)) w = true := by
        rw [validParityWordBool_eq_true_iff, ← hq_eq]
        exact hvalid
      have hq_ne0 : wordB w / (wordD w - wordA w) ≠ 0 := by omega
      have h1 : decide (wordB w % (wordD w - wordA w) ≠ 0) = false :=
        decide_eq_false (by omega)
      have h2 : decide (wordB w / (wordD w - wordA w) = 0) = false :=
        decide_eq_false hq_ne0
      dsimp at hcert
      rw [h1, h2, hvb] at hcert
      contradiction
    · exact no_cycle_when_gap_not_dvd_B w m hvalid hgt hdvd hcycle

set_option maxRecDepth 20000

/-- Exact catalog size check: there are `128` parity words of length `7`. -/
theorem length7_catalog_size : (allParityWords 7).length = 128 := by decide

/-- Kernel-checked finite verification across all 128 parity words of length 7:
    every word in `allParityWords 7` satisfies `wordRejectsPosCycle`. -/
theorem length7_all_reject_pos_cycle :
    ((allParityWords 7).all wordRejectsPosCycle) = true := by decide

/-- Universal Length-7 Fixed-Point Falsification Theorem (Track R7-C):
    For every length-7 parity word `w ∈ allParityWords 7` and every positive integer `m > 0`,
    if `validParityWord m w` holds, then `applyParityWord m w ≠ m`. -/
theorem length7_no_positive_fixed_point (w : List Bool)
    (hw : w ∈ allParityWords 7) (m : Nat) (hm : m > 0)
    (hvalid : validParityWord m w) :
    applyParityWord m w ≠ m := by
  have hcert : wordRejectsPosCycle w = true :=
    (List.all_eq_true.mp length7_all_reject_pos_cycle) w hw
  exact wordRejectsPosCycle_sound w hcert m hm hvalid

/-! ### BBB17-R7-001 Gate 5: Control-Cycle Falsification (R7-A) & Odd-Modulus Generalization (R7-B) -/

/-- Membership in the 7-state reset subsystem `{A=0, L=11, M=12, N=13, O=14, P=15, Q=16}`. -/
def isResetSubstate (q : State) : Bool :=
  q == (0 : State) || decide (q.val ≥ 11)

/-- Directed control-graph edge inside the 7-state reset subsystem `{A, L, M, N, O, P, Q}`. -/
def resetSubEdge (q₁ q₂ : State) : Bool :=
  isResetSubstate q₁ && isResetSubstate q₂ &&
    ((action q₁ false).next == q₂ || (action q₁ true).next == q₂)

/-- The 7 states of the reset subsystem. -/
def resetSubStates : List State :=
  [(0 : State), (11 : State), (12 : State), (13 : State), (14 : State), (15 : State), (16 : State)]

/-- Exact 6-state repeating control cycle `L(11) → M(12) → N(13) → O(14) → P(15) → Q(16) → L(11)`
    inside the reset subsystem (Track R7-A). -/
theorem reset_six_state_cycle_certified :
    resetSubEdge (11 : State) (12 : State) = true ∧
    resetSubEdge (12 : State) (13 : State) = true ∧
    resetSubEdge (13 : State) (14 : State) = true ∧
    resetSubEdge (14 : State) (15 : State) = true ∧
    resetSubEdge (15 : State) (16 : State) = true ∧
    resetSubEdge (16 : State) (11 : State) = true := by decide

/-- Exact 5-state entry/exit control cycle `A(0) → L(11) → M(12) → N(13) → O(14) → A(0)`
    inside the reset subsystem (Track R7-A). -/
theorem reset_five_state_cycle_certified :
    resetSubEdge (0 : State) (11 : State) = true ∧
    resetSubEdge (11 : State) (12 : State) = true ∧
    resetSubEdge (12 : State) (13 : State) = true ∧
    resetSubEdge (13 : State) (14 : State) = true ∧
    resetSubEdge (14 : State) (0 : State) = true := by decide

/-- Recursive search for any simple cycle of length `len` starting at `start`
    inside the 7-state reset subsystem `{A, L, M, N, O, P, Q}`. -/
def hasSimpleResetWalkToStart (start curr : State) (visited : List State) : Nat → Bool
  | 0 => false
  | 1 => resetSubEdge curr start
  | k + 2 =>
    resetSubStates.any (fun nxt =>
      resetSubEdge curr nxt && !(visited.elem nxt) &&
        hasSimpleResetWalkToStart start nxt (nxt :: visited) (k + 1))

/-- Check whether ANY state in `resetSubStates` initiates a simple cycle of length `len`
    in the reset subsystem `{A, L, M, N, O, P, Q}`. -/
def hasSimpleResetCycleOfLength (len : Nat) : Bool :=
  resetSubStates.any (fun s => hasSimpleResetWalkToStart s s [s] len)

/-- Track R7-A Formal Qualification:
    The 7-state reset subsystem `{A, L, M, N, O, P, Q}` has primitive cycles of lengths
    `1`, `5`, and `6`, and **no simple 7-state cycle** (`hasSimpleResetCycleOfLength 7 = false`). -/
theorem reset_subsystem_cycle_spectrum :
    hasSimpleResetCycleOfLength 1 = true ∧
    hasSimpleResetCycleOfLength 5 = true ∧
    hasSimpleResetCycleOfLength 6 = true ∧
    hasSimpleResetCycleOfLength 7 = false := by decide

/-- Track R7-B General Odd-Modulus Singleton Theorem:
    For EVERY odd modulus `q = 2 * k + 1` and residue `r < 2 * k + 1`, the doubled
    even-branch value `r` (`2 * C(m) = m ≡ r`) and doubled odd-branch value `3 * r + 1`
    (`2 * C(m) = 3m + 1 ≡ 3r + 1`) coincide modulo `2 * k + 1` if and only if
    `r = k = (q - 1) / 2` (equivalently `2 * r + 1 ≡ 0 (mod 2 * k + 1)`).
    In particular, `q = 7` (`k = 3`, singleton `r = 3`) is an instance of `r = k`
    alongside `q = 3` (`r = 1`), `q = 5` (`r = 2`), `q = 21` (`r = 10`), and `q = 49` (`r = 24`). -/
theorem oddModulus_singleton_iff (k r : Nat) (hr : r < 2 * k + 1) :
    (3 * r + 1) % (2 * k + 1) = r % (2 * k + 1) ↔ r = k := by
  have hr_mod : r % (2 * k + 1) = r := Nat.mod_eq_of_lt hr
  by_cases h1 : 3 * r + 1 < 2 * k + 1
  · have hm1 : (3 * r + 1) % (2 * k + 1) = 3 * r + 1 := Nat.mod_eq_of_lt h1
    rw [hm1, hr_mod]
    omega
  · by_cases h2 : 3 * r + 1 < 2 * (2 * k + 1)
    · have hsub_lt : (3 * r + 1) - (2 * k + 1) < 2 * k + 1 := by omega
      have hdecomp : ((3 * r + 1) - (2 * k + 1)) + (2 * k + 1) = 3 * r + 1 := by omega
      have hm2 : (((3 * r + 1) - (2 * k + 1)) + (2 * k + 1)) % (2 * k + 1) =
          (3 * r + 1) - (2 * k + 1) := by
        rw [Nat.add_mod_right, Nat.mod_eq_of_lt hsub_lt]
      rw [hdecomp] at hm2
      rw [hm2, hr_mod]
      omega
    · have hsub_lt : (3 * r + 1) - 2 * (2 * k + 1) < 2 * k + 1 := by omega
      have hdecomp : (((3 * r + 1) - 2 * (2 * k + 1)) + (2 * k + 1)) + (2 * k + 1) =
          3 * r + 1 := by omega
      have hm3 : ((((3 * r + 1) - 2 * (2 * k + 1)) + (2 * k + 1)) + (2 * k + 1)) % (2 * k + 1) =
          (3 * r + 1) - 2 * (2 * k + 1) := by
        rw [Nat.add_mod_right, Nat.add_mod_right, Nat.mod_eq_of_lt hsub_lt]
      rw [hdecomp] at hm3
      rw [hm3, hr_mod]
      omega

/-! ### Collatz Convergence Program: Gates C1–C5
    - **Gate C1**: Symbolic parity words, exact trajectory-to-word correspondence, and residue-class affine operators.
    - **Gate C2**: Unconditional spectral contraction (`2^r > 3^a`) for all positive cycles and arbitrary-period 1-circuit cycle exclusion.
    - **Gate C3**: Exact parity-cylinder descent threshold `(2^r - 3^a) * m > B(w)` and universal asymptotic descent on every contracting cylinder.
    - **Gate C4 & C5**: Equivalence `UniversalCollatzDescent ↔ UniversalAcceleratedDescent ↔ CollatzConjecture`, unconditional descent on infinite residue classes (`0 mod 2`, `1 mod 4`, `3 mod 16`, `11 mod 32`, `23 mod 32`), and exact reduction of `CollatzConjecture` to the surviving residue frontier (`{7, 15, 19, 27, 31} mod 32`).
-/

/-- `r`-step iteration of `acceleratedCollatz`. -/
def iterateAccelerated : Nat → Nat → Nat
  | m, 0 => m
  | m, r + 1 => iterateAccelerated (acceleratedCollatz m) r

/-- Gate C1: Applying `parityWordOf r m` to `m` computes `iterateAccelerated m r`. -/
theorem applyParityWord_parityWordOf (r m : Nat) :
    applyParityWord m (parityWordOf r m) = iterateAccelerated m r := by
  induction r generalizing m with
  | zero => rfl
  | succ r ih =>
    dsimp [parityWordOf, applyParityWord, iterateAccelerated]
    exact ih (acceleratedCollatz m)

/-- Gate C1: Universal exact affine trajectory identity for `iterateAccelerated m r`. -/
theorem iterateAccelerated_exact_affine (r m : Nat) :
    wordD (parityWordOf r m) * iterateAccelerated m r =
      wordA (parityWordOf r m) * m + wordB (parityWordOf r m) := by
  rw [← applyParityWord_parityWordOf r m]
  exact parityWord_affine_identity (parityWordOf r m) m (parityWordOf_valid r m)

/-- Gate C1: Exact linear representation on the residue class `wordResidue w + q * 2^|w|`. -/
theorem applyParityWord_on_residue_class (w : List Bool) (q : Nat) :
    applyParityWord (wordResidue w + q * wordD w) w =
      applyParityWord (wordResidue w) w + q * wordA w :=
  (parityWord_residue_shift w (wordResidue w) q (wordResidue_valid w)).2

/-! #### Gate C2: Arbitrary-Period Cycle Obstructions -/

/-- A parity word `w` has `wordB w = 0` if and only if `wordA w = 1` (all steps even). -/
theorem wordB_eq_zero_iff_wordA_eq_one (w : List Bool) :
    wordB w = 0 ↔ wordA w = 1 := by
  induction w with
  | nil =>
    dsimp [wordB, wordA]
    omega
  | cons b bs ih =>
    cases b with
    | false =>
      dsimp [wordB, wordA]
      omega
    | true =>
      dsimp [wordB, wordA]
      have hA := wordA_pos bs
      omega

/-- Every non-empty parity word `w ≠ []` has `wordD w ≥ 2`. -/
theorem wordD_ge_two_of_ne_nil (w : List Bool) (hw : w ≠ []) :
    wordD w ≥ 2 := by
  cases w with
  | nil => contradiction
  | cons b bs =>
    dsimp [wordD]
    have hD := wordD_pos bs
    omega

/-- Gate C2: Any positive integer `m > 0` forming a cycle along a non-empty valid parity word `w`
    must have `wordB w > 0` (at least one odd step). -/
theorem cycle_pos_forces_wordB_pos (w : List Bool) (m : Nat)
    (hw : w ≠ []) (hm : m > 0) (hv : validParityWord m w) (hc : applyParityWord m w = m) :
    wordB w > 0 := by
  have heq := parityWord_cycle_equation w m hv hc
  have hD2 := wordD_ge_two_of_ne_nil w hw
  by_cases hB : wordB w = 0
  · have hA1 : wordA w = 1 := (wordB_eq_zero_iff_wordA_eq_one w).mp hB
    rw [hB, hA1] at heq
    have hge : wordD w * m ≥ 2 * m := Nat.mul_le_mul_right m hD2
    omega
  · omega

/-- Gate C2 (Unconditional Spectral Contraction for Cycles):
    Every cycle of a positive integer `m > 0` along ANY non-empty parity word `w`
    strictly contracts: `wordD w > wordA w` (`2^|w| > 3^(ones w)`). -/
theorem cycle_pos_forces_contracting (w : List Bool) (m : Nat)
    (hw : w ≠ []) (hm : m > 0) (hv : validParityWord m w) (hc : applyParityWord m w = m) :
    wordD w > wordA w := by
  have hB : wordB w > 0 := cycle_pos_forces_wordB_pos w m hw hm hv hc
  by_cases hge : wordA w ≥ wordD w
  · exfalso
    exact no_cycle_when_wordA_ge_wordD w m hv hge hB hc
  · omega

/-- All-even parity word `replicate k false` has `wordA = 1` and `wordB = 0`. -/
theorem wordA_replicate_false (k : Nat) :
    wordA (List.replicate k false) = 1 := by
  induction k with
  | zero => rfl
  | succ k ih =>
    dsimp [List.replicate, wordA]
    exact ih

theorem wordB_replicate_false (k : Nat) :
    wordB (List.replicate k false) = 0 := by
  induction k with
  | zero => rfl
  | succ k ih =>
    dsimp [List.replicate, wordB]
    omega

/-- 1-circuit parity word of arbitrary period `k + 1`: one odd step followed by `k` even steps. -/
def singleOddWord (k : Nat) : List Bool :=
  true :: List.replicate k false

theorem wordA_singleOddWord (k : Nat) :
    wordA (singleOddWord k) = 3 := by
  dsimp [singleOddWord, wordA]
  rw [wordA_replicate_false]

theorem wordB_singleOddWord (k : Nat) :
    wordB (singleOddWord k) = 1 := by
  dsimp [singleOddWord, wordB]
  rw [wordA_replicate_false, wordB_replicate_false]

/-- Gate C2 (Arbitrary-Period 1-Circuit Cycle Exclusion):
    For EVERY `k : Nat` (period `r = k + 1`) and EVERY `m > 1`,
    no integer `m > 1` can form a cycle along `singleOddWord k = true :: replicate k false`. -/
theorem no_single_odd_cycle_above_one (k m : Nat)
    (hm : m > 1) (hv : validParityWord m (singleOddWord k)) :
    applyParityWord m (singleOddWord k) ≠ m := by
  intro hc
  have heq := parityWord_cycle_equation (singleOddWord k) m hv hc
  rw [wordA_singleOddWord, wordB_singleOddWord] at heq
  by_cases hle : wordD (singleOddWord k) ≤ 3
  · have hmul : wordD (singleOddWord k) * m ≤ 3 * m := Nat.mul_le_mul_right m hle
    omega
  · have hge : wordD (singleOddWord k) ≥ 4 := by omega
    have hmul : wordD (singleOddWord k) * m ≥ 4 * m := Nat.mul_le_mul_right m hge
    omega

/-! #### Gate C3: Parity-Cylinder Descent Threshold & Asymptotic Contraction -/

/-- Gate C3: For any contracting parity word `w` (`wordD w > wordA w`) and any valid input `m`,
    `applyParityWord m w < m` holds if and only if `(wordD w - wordA w) * m > wordB w`. -/
theorem contracting_word_descent_iff (w : List Bool) (m : Nat)
    (hv : validParityWord m w) (hgt : wordD w > wordA w) :
    applyParityWord m w < m ↔ (wordD w - wordA w) * m > wordB w := by
  have hid := parityWord_affine_identity w m hv
  have hD : wordD w > 0 := wordD_pos w
  have hsub : (wordD w - wordA w) * m + wordA w * m = wordD w * m := by
    rw [← Nat.add_mul, Nat.sub_add_cancel (by omega)]
  constructor
  · intro hlt
    have hmul : wordD w * applyParityWord m w + wordD w ≤ wordD w * m := by
      have h1 : applyParityWord m w + 1 ≤ m := by omega
      have h2 := Nat.mul_le_mul_left (wordD w) h1
      rw [Nat.mul_add, Nat.mul_one] at h2
      exact h2
    omega
  · intro hgap
    by_cases hge : m ≤ applyParityWord m w
    · have hmul : wordD w * m ≤ wordD w * applyParityWord m w :=
        Nat.mul_le_mul_left (wordD w) hge
      omega
    · omega

/-- Gate C3 (Universal Asymptotic Descent on Contracting Cylinders):
    For every contracting parity word `w` (`2^|w| > 3^(ones w)`), every integer
    `m = wordResidue w + q * 2^|w|` with `q > wordB w` strictly descends under `w`. -/
theorem contracting_word_asymptotic_descent (w : List Bool)
    (hgt : wordD w > wordA w) (q : Nat) (hq : q > wordB w) :
    applyParityWord (wordResidue w + q * wordD w) w < wordResidue w + q * wordD w := by
  let m := wordResidue w + q * wordD w
  have hv : validParityWord m w :=
    (parityWord_residue_shift w (wordResidue w) q (wordResidue_valid w)).1
  rw [contracting_word_descent_iff w m hv hgt]
  have hD : wordD w ≥ 1 := wordD_pos w
  have hgap : wordD w - wordA w ≥ 1 := by omega
  have hqm : m ≥ q := by
    have hqD : q * wordD w ≥ q * 1 := Nat.mul_le_mul_left q hD
    omega
  have hmul : (wordD w - wordA w) * m ≥ 1 * m := Nat.mul_le_mul_right m hgap
  omega

/-! #### Gates C4 & C5: Universal Descent Reduction & Certified Residue Classes -/

/-- `collatz` preserves positivity (`n > 0 → collatz n > 0`). -/
theorem collatz_pos (n : Nat) (hn : n > 0) : collatz n > 0 := by
  unfold collatz
  by_cases h : n % 2 = 0
  · rw [if_pos h]; omega
  · rw [if_neg h]; omega

/-- `iterateCollatz` preserves positivity (`n > 0 → iterateCollatz n k > 0`). -/
theorem iterateCollatz_pos (n k : Nat) (hn : n > 0) : iterateCollatz n k > 0 := by
  induction k generalizing n with
  | zero => exact hn
  | succ k ih =>
    rw [iterateCollatz_succ_left]
    exact ih (collatz n) (collatz_pos n hn)

/-- Composition law for `iterateCollatz`: `iterateCollatz n (a + b) = iterateCollatz (iterateCollatz n a) b`. -/
theorem iterateCollatz_add (n a b : Nat) :
    iterateCollatz n (a + b) = iterateCollatz (iterateCollatz n a) b := by
  induction a generalizing n with
  | zero =>
    simp [iterateCollatz]
  | succ a ih =>
    rw [Nat.succ_add, iterateCollatz_succ_left, ih (collatz n), ← iterateCollatz_succ_left]

/-- Primary theorem target (Gate C4): every integer `n > 1` eventually reaches
    a strictly smaller positive integer under `collatz`. -/
def UniversalCollatzDescent : Prop :=
  ∀ n : Nat, n > 1 → ∃ k : Nat, k > 0 ∧ iterateCollatz n k < n

/-- Bounded strong induction: if every `1 < m ≤ B` reaches a strictly smaller value
    under `iterateCollatz`, then every `0 < n ≤ B` reaches `1`. -/
theorem reachesOne_of_descent_bounded (B : Nat)
    (hdesc : ∀ m : Nat, 1 < m → m ≤ B → ∃ k : Nat, k > 0 ∧ iterateCollatz m k < m) :
    ∀ n : Nat, 0 < n → n ≤ B → ReachesOne n := by
  induction B with
  | zero =>
    intro n hn hle
    omega
  | succ B ih =>
    intro n hn hle
    by_cases hn1 : n = 1
    · subst hn1
      exact ⟨0, rfl⟩
    · rcases hdesc n (by omega) hle with ⟨k, _, hlt⟩
      have hpos' : 0 < iterateCollatz n k := iterateCollatz_pos n k hn
      rcases ih (fun m hm1 hmB => hdesc m hm1 (by omega)) (iterateCollatz n k) hpos' (by omega)
        with ⟨m, hm⟩
      refine ⟨k + m, ?_⟩
      rw [iterateCollatz_add n k m, hm]

/-- Gate C4 → Gate C5: `UniversalCollatzDescent` implies `CollatzConjecture`. -/
theorem universalCollatzDescent_implies_collatz (h : UniversalCollatzDescent) :
    CollatzConjecture := by
  intro n hn
  exact reachesOne_of_descent_bounded n (fun m hm1 _ => h m hm1) n hn (Nat.le_refl n)

/-- Gate C5 → Gate C4: `CollatzConjecture` implies `UniversalCollatzDescent`. -/
theorem collatz_implies_universalCollatzDescent (h : CollatzConjecture) :
    UniversalCollatzDescent := by
  intro n hn1
  rcases h n (by omega) with ⟨k, hk⟩
  cases k with
  | zero =>
    unfold iterateCollatz at hk
    omega
  | succ k =>
    refine ⟨k + 1, by omega, ?_⟩
    omega

/-- Exact logical equivalence between Gate C4 (`UniversalCollatzDescent`) and Gate C5 (`CollatzConjecture`). -/
theorem universalCollatzDescent_iff_collatz :
    UniversalCollatzDescent ↔ CollatzConjecture :=
  ⟨universalCollatzDescent_implies_collatz, collatz_implies_universalCollatzDescent⟩

/-- Every step of `acceleratedCollatz` equals 1 or 2 steps of `collatz`. -/
theorem acceleratedCollatz_eq_collatz_steps (n : Nat) :
    ∃ s : Nat, s ≥ 1 ∧ iterateCollatz n s = acceleratedCollatz n := by
  by_cases hev : n % 2 = 0
  · refine ⟨1, by omega, ?_⟩
    change collatz n = acceleratedCollatz n
    unfold collatz acceleratedCollatz
    rw [if_pos hev, if_pos hev]
  · refine ⟨2, by omega, ?_⟩
    change collatz (collatz n) = acceleratedCollatz n
    have hev2 : (3 * n + 1) % 2 = 0 := by omega
    unfold collatz acceleratedCollatz
    rw [if_neg hev, if_pos hev2, if_neg hev]

/-- Every `r` steps of `iterateAccelerated` correspond to `k ≥ r` steps of `iterateCollatz`. -/
theorem iterateAccelerated_to_iterateCollatz (n r : Nat) :
    ∃ k : Nat, k ≥ r ∧ iterateCollatz n k = iterateAccelerated n r := by
  induction r generalizing n with
  | zero =>
    exact ⟨0, Nat.le_refl 0, rfl⟩
  | succ r ih =>
    rcases acceleratedCollatz_eq_collatz_steps n with ⟨s, hs, hstep⟩
    rcases ih (acceleratedCollatz n) with ⟨k, hk, hrest⟩
    refine ⟨s + k, by omega, ?_⟩
    rw [iterateCollatz_add n s k, hstep, hrest]
    rfl

/-- Accelerated Universal Descent (Gate C4 in accelerated form). -/
def UniversalAcceleratedDescent : Prop :=
  ∀ n : Nat, n > 1 → ∃ r : Nat, r > 0 ∧ iterateAccelerated n r < n

/-- `UniversalAcceleratedDescent` is also logically equivalent to `CollatzConjecture`. -/
theorem universalAcceleratedDescent_iff_collatz :
    UniversalAcceleratedDescent ↔ CollatzConjecture := by
  rw [← universalCollatzDescent_iff_collatz]
  constructor
  · intro hacc n hn1
    rcases hacc n hn1 with ⟨r, hr, hlt⟩
    rcases iterateAccelerated_to_iterateCollatz n r with ⟨k, hk, heq⟩
    refine ⟨k, by omega, ?_⟩
    omega
  · intro hcol
    have hconj : CollatzConjecture := universalCollatzDescent_implies_collatz hcol
    intro n hn1
    obtain ⟨u, rfl⟩ : ∃ u : Nat, n = u + 1 := ⟨n - 1, by omega⟩
    rcases (regReachesZero_iff_reachesOne u).mpr (hconj (u + 1) (by omega)) with ⟨r, hr0⟩
    have hr_pos : r > 0 := by
      cases r with
      | zero =>
        unfold iterateRegStep at hr0
        omega
      | succ r' => omega
    have hrel : ∀ t u : Nat, iterateAccelerated (u + 1) t = iterateRegStep u t + 1 := by
      intro t
      induction t with
      | zero => intro u; rfl
      | succ t ih =>
        intro u
        dsimp [iterateAccelerated, iterateRegStep]
        have hstep : acceleratedCollatz (u + 1) = collatzRegStep u + 1 := by
          by_cases hodd : u % 2 = 1
          · have hev : (u + 1) % 2 = 0 := by omega
            unfold acceleratedCollatz collatzRegStep
            rw [if_pos hev, if_pos hodd]
            omega
          · have hnev : ¬((u + 1) % 2 = 0) := by omega
            unfold acceleratedCollatz collatzRegStep
            rw [if_neg hnev, if_neg hodd]
            omega
        rw [hstep, ih (collatzRegStep u)]
    refine ⟨r, hr_pos, ?_⟩
    rw [hrel r u, hr0]
    omega

/-! #### Unconditional Descent Theorems on Infinite Residue Families & Exact Frontier Reduction -/

/-- Unconditional 1-step descent for all even integers `n > 1` (`n ≡ 0 (mod 2)`). -/
theorem collatz_descent_even (n : Nat) (hn : n > 1) (heven : n % 2 = 0) :
    iterateCollatz n 1 < n := by
  change collatz n < n
  unfold collatz
  rw [if_pos heven]
  omega

/-- Unconditional 3-step descent for all integers `n > 1` with `n ≡ 1 (mod 4)`:
    `4k + 1 → 12k + 4 → 6k + 2 → 3k + 1 < 4k + 1`. -/
theorem collatz_descent_mod4_eq1 (n : Nat) (hn : n > 1) (hmod : n % 4 = 1) :
    iterateCollatz n 3 < n := by
  change collatz (collatz (collatz n)) < n
  have h1 : ¬(n % 2 = 0) := by omega
  have h2 : (3 * n + 1) % 2 = 0 := by omega
  have h3 : ((3 * n + 1) / 2) % 2 = 0 := by omega
  unfold collatz
  rw [if_neg h1, if_pos h2, if_pos h3]
  omega

/-- Unconditional 6-step descent for all integers `n` with `n ≡ 3 (mod 16)`:
    `16k + 3 → 48k + 10 → 24k + 5 → 72k + 16 → 36k + 8 → 18k + 4 → 9k + 2 < 16k + 3`. -/
theorem collatz_descent_mod16_eq3 (n : Nat) (hmod : n % 16 = 3) :
    iterateCollatz n 6 < n := by
  change collatz (collatz (collatz (collatz (collatz (collatz n))))) < n
  have h1 : ¬(n % 2 = 0) := by omega
  have h2 : (3 * n + 1) % 2 = 0 := by omega
  have h3 : ¬(((3 * n + 1) / 2) % 2 = 0) := by omega
  have h4 : (3 * ((3 * n + 1) / 2) + 1) % 2 = 0 := by omega
  have h5 : ((3 * ((3 * n + 1) / 2) + 1) / 2) % 2 = 0 := by omega
  have h6 : (((3 * ((3 * n + 1) / 2) + 1) / 2) / 2) % 2 = 0 := by omega
  unfold collatz
  rw [if_neg h1, if_pos h2, if_neg h3, if_pos h4, if_pos h5, if_pos h6]
  omega

/-- Unconditional 8-step descent for all integers `n` with `n ≡ 11 (mod 32)`. -/
theorem collatz_descent_mod32_eq11 (n : Nat) (hmod : n % 32 = 11) :
    iterateCollatz n 8 < n := by
  change collatz (collatz (collatz (collatz (collatz (collatz (collatz (collatz n))))))) < n
  have h1 : ¬(n % 2 = 0) := by omega
  have h2 : (3 * n + 1) % 2 = 0 := by omega
  have h3 : ¬(((3 * n + 1) / 2) % 2 = 0) := by omega
  have h4 : (3 * ((3 * n + 1) / 2) + 1) % 2 = 0 := by omega
  have h5 : (((3 * ((3 * n + 1) / 2) + 1) / 2)) % 2 = 0 := by omega
  have h6 : ¬((((3 * ((3 * n + 1) / 2) + 1) / 2) / 2) % 2 = 0) := by omega
  have h7 : (3 * (((3 * ((3 * n + 1) / 2) + 1) / 2) / 2) + 1) % 2 = 0 := by omega
  have h8 : ((3 * (((3 * ((3 * n + 1) / 2) + 1) / 2) / 2) + 1) / 2) % 2 = 0 := by omega
  unfold collatz
  rw [if_neg h1, if_pos h2, if_neg h3, if_pos h4, if_pos h5, if_neg h6, if_pos h7, if_pos h8]
  omega

/-- Unconditional 8-step descent for all integers `n` with `n ≡ 23 (mod 32)`. -/
theorem collatz_descent_mod32_eq23 (n : Nat) (hmod : n % 32 = 23) :
    iterateCollatz n 8 < n := by
  change collatz (collatz (collatz (collatz (collatz (collatz (collatz (collatz n))))))) < n
  have h1 : ¬(n % 2 = 0) := by omega
  have h2 : (3 * n + 1) % 2 = 0 := by omega
  have h3 : ¬(((3 * n + 1) / 2) % 2 = 0) := by omega
  have h4 : (3 * ((3 * n + 1) / 2) + 1) % 2 = 0 := by omega
  have h5 : ¬(((3 * ((3 * n + 1) / 2) + 1) / 2) % 2 = 0) := by omega
  have h6 : (3 * ((3 * ((3 * n + 1) / 2) + 1) / 2) + 1) % 2 = 0 := by omega
  have h7 : (((3 * ((3 * ((3 * n + 1) / 2) + 1) / 2) + 1) / 2)) % 2 = 0 := by omega
  have h8 : ((((3 * ((3 * ((3 * n + 1) / 2) + 1) / 2) + 1) / 2) / 2)) % 2 = 0 := by omega
  unfold collatz
  rw [if_neg h1, if_pos h2, if_neg h3, if_pos h4, if_neg h5, if_pos h6, if_pos h7, if_pos h8]
  omega

/-- Exact Modulo-32 Frontier Reduction Theorem:
    `CollatzConjecture` holds if and only if every `n > 1` in the five unresolved
    residue classes `n % 32 ∈ {7, 15, 19, 27, 31}` eventually reaches a smaller integer.
    (All 27 other residue classes modulo 32 are unconditionally proved to descend in `≤ 8` steps.) -/
theorem collatz_iff_mod32_frontier_descent :
    CollatzConjecture ↔
      (∀ n : Nat, n > 1 →
        (n % 32 = 7 ∨ n % 32 = 15 ∨ n % 32 = 19 ∨ n % 32 = 27 ∨ n % 32 = 31) →
        ∃ k : Nat, k > 0 ∧ iterateCollatz n k < n) := by
  rw [← universalCollatzDescent_iff_collatz]
  constructor
  · intro h n hn1 _
    exact h n hn1
  · intro hfront n hn1
    by_cases hev : n % 2 = 0
    · exact ⟨1, by omega, collatz_descent_even n hn1 hev⟩
    · by_cases hm4 : n % 4 = 1
      · exact ⟨3, by omega, collatz_descent_mod4_eq1 n hn1 hm4⟩
      · by_cases hm16 : n % 16 = 3
        · exact ⟨6, by omega, collatz_descent_mod16_eq3 n hm16⟩
        · by_cases hm11 : n % 32 = 11
          · exact ⟨8, by omega, collatz_descent_mod32_eq11 n hm11⟩
          · by_cases hm23 : n % 32 = 23
            · exact ⟨8, by omega, collatz_descent_mod32_eq23 n hm23⟩
            · have hrem : n % 32 = 7 ∨ n % 32 = 15 ∨ n % 32 = 19 ∨ n % 32 = 27 ∨ n % 32 = 31 := by
                omega
              exact hfront n hn1 hrem

/-! #### Gate C5 Obstruction Analysis: Why Finite 2-Adic Sieves Cannot Close C5 Alone -/

/-- Expanding-Word Strict Growth Theorem:
    For EVERY parity word `w` in the expanding regime (`wordA w ≥ wordD w` with `wordB w > 0`)
    and EVERY admissible integer `m` (`validParityWord m w`), the `|w|`-step output is
    strictly larger than `m` (`applyParityWord m w > m`). -/
theorem expanding_word_strict_growth (w : List Bool) (m : Nat)
    (hv : validParityWord m w) (hge : wordA w ≥ wordD w) (hB : wordB w > 0) :
    applyParityWord m w > m := by
  have hid := parityWord_affine_identity w m hv
  have hmul : wordD w * m ≤ wordA w * m := Nat.mul_le_mul_right m hge
  by_cases hle : applyParityWord m w ≤ m
  · have hout : wordD w * applyParityWord m w ≤ wordD w * m :=
      Nat.mul_le_mul_left (wordD w) hle
    omega
  · omega

/-- The all-odd parity word `replicate r true` of arbitrary length `r`. -/
def allTrueWord (r : Nat) : List Bool :=
  List.replicate r true

theorem wordA_ge_wordD_allTrueWord (r : Nat) :
    wordA (allTrueWord r) ≥ wordD (allTrueWord r) := by
  induction r with
  | zero =>
    dsimp [allTrueWord, List.replicate, wordA, wordD]
    omega
  | succ r ih =>
    dsimp [allTrueWord, List.replicate, wordA, wordD] at ih ⊢
    omega

theorem wordB_pos_allTrueWord (r : Nat) (hr : r > 0) :
    wordB (allTrueWord r) > 0 := by
  cases r with
  | zero => omega
  | succ r =>
    dsimp [allTrueWord, List.replicate, wordB]
    have hA := wordA_pos (List.replicate r true)
    omega

/-- Finite-Depth Sieve Obstruction Theorem:
    At EVERY finite depth `r > 0`, the residue class `m ≡ wordResidue (allTrueWord r) (mod 2^r)`
    (which equals `2^r - 1 (mod 2^r)`) is non-empty and EVERY integer `m` in this residue class
    strictly grows after `r` accelerated steps (`applyParityWord m (allTrueWord r) > m`).
    Consequently, no finite 2-adic modulus `2^r` can bound the stopping time across all residues. -/
theorem allTrueWord_never_descends_at_depth (r q : Nat) (hr : r > 0) :
    let w := allTrueWord r
    let m := wordResidue w + q * wordD w
    validParityWord m w ∧ applyParityWord m w > m := by
  intro w m
  have hv : validParityWord m w :=
    (parityWord_residue_shift w (wordResidue w) q (wordResidue_valid w)).1
  exact ⟨hv, expanding_word_strict_growth w m hv
    (wordA_ge_wordD_allTrueWord r) (wordB_pos_allTrueWord r hr)⟩

/-! ### COLLATZ-C6: Adaptive Residue Descent & Tree Well-Foundedness Analysis
    1. Discharge of `n ≡ 19 (mod 32)` and reduction of the modulo-32 frontier to the
       4 spectrally expanding classes `{7, 15, 27, 31} (mod 32)`.
    2. Universal decidable cylinder descent certificate `cylinderCert` and its soundness
       theorem `cylinderCert_sound`.
    3. Adaptive refinement across moduli `64`, `128`, and `256`, discharging `237 / 256`
       residue classes (`92.58%`) and reducing `CollatzConjecture` to the 19-class
       expanding frontier modulo `256` (`collatz_iff_mod256_frontier_descent`).
    4. Exact well-foundedness vs. 2-adic escape analysis: proving that while `allTrueWord r`
       is an infinite expanding path in the 2-adic tree over `ℤ₂`, every natural number `n ∈ ℕ`
       satisfies `2^r ∣ (n + 1)` along `allTrueWord r` and therefore exits the branch in
       at most `n` steps (`every_nat_exits_allTrue_branch`).
-/

/-- Unconditional 8-step descent for all integers `n` with `n ≡ 19 (mod 32)`:
    `32k + 19 → 96k + 58 → 48k + 29 → 144k + 88 → 72k + 44 → 36k + 22 → 18k + 11 → 54k + 34 → 27k + 17 < 32k + 19`. -/
theorem collatz_descent_mod32_eq19 (n : Nat) (hmod : n % 32 = 19) :
    iterateCollatz n 8 < n := by
  change collatz (collatz (collatz (collatz (collatz (collatz (collatz (collatz n))))))) < n
  have h1 : ¬(n % 2 = 0) := by omega
  have h2 : (3 * n + 1) % 2 = 0 := by omega
  have h3 : ¬(((3 * n + 1) / 2) % 2 = 0) := by omega
  have h4 : (3 * ((3 * n + 1) / 2) + 1) % 2 = 0 := by omega
  have h5 : (((3 * ((3 * n + 1) / 2) + 1) / 2)) % 2 = 0 := by omega
  have h6 : ((((3 * ((3 * n + 1) / 2) + 1) / 2) / 2)) % 2 = 0 := by omega
  have h7 : ¬(((((3 * ((3 * n + 1) / 2) + 1) / 2) / 2) / 2) % 2 = 0) := by omega
  have h8 : (3 * (((((3 * ((3 * n + 1) / 2) + 1) / 2) / 2) / 2)) + 1) % 2 = 0 := by omega
  unfold collatz
  rw [if_neg h1, if_pos h2, if_neg h3, if_pos h4, if_pos h5, if_pos h6, if_neg h7, if_pos h8]
  omega

/-- Refined Modulo-32 Four-Class Frontier Theorem:
    Discharging `19 (mod 32)` reduces `CollatzConjecture` to the 4 spectrally expanding
    residue classes `n % 32 ∈ {7, 15, 27, 31}`. -/
theorem collatz_iff_mod32_four_class_frontier :
    CollatzConjecture ↔
      (∀ n : Nat, n > 1 →
        (n % 32 = 7 ∨ n % 32 = 15 ∨ n % 32 = 27 ∨ n % 32 = 31) →
        ∃ k : Nat, k > 0 ∧ iterateCollatz n k < n) := by
  rw [collatz_iff_mod32_frontier_descent]
  constructor
  · intro h n hn1 h4
    rcases h4 with h7 | h15 | h27 | h31
    · exact h n hn1 (Or.inl h7)
    · exact h n hn1 (Or.inr (Or.inl h15))
    · exact h n hn1 (Or.inr (Or.inr (Or.inr (Or.inl h27))))
    · exact h n hn1 (Or.inr (Or.inr (Or.inr (Or.inr h31))))
  · intro h4 n hn1 h5
    rcases h5 with h7 | h15 | h19 | h27 | h31
    · exact h4 n hn1 (Or.inl h7)
    · exact h4 n hn1 (Or.inr (Or.inl h15))
    · exact ⟨8, by omega, collatz_descent_mod32_eq19 n h19⟩
    · exact h4 n hn1 (Or.inr (Or.inr (Or.inl h27)))
    · exact h4 n hn1 (Or.inr (Or.inr (Or.inr h31)))

/-- Minimum integer `> 1` in the residue class `r₀ (mod D)` for `r₀ < D`. -/
def minClassRep (D r₀ : Nat) : Nat :=
  if r₀ ≤ 1 then r₀ + D else r₀

/-- Decidable certificate that every integer `n > 1` in the residue class `r₀ (mod 2^r)`
    strictly descends after `r` accelerated steps. -/
def cylinderCert (r r₀ : Nat) : Bool :=
  let w := parityWordOf r r₀
  let D := wordD w
  let A := wordA w
  let B := wordB w
  let m₀ := minClassRep D r₀
  decide (r > 0) && decide (r₀ < D) && decide (D > A) && decide ((D - A) * m₀ > B)

theorem wordD_parityWordOf (r m : Nat) :
    wordD (parityWordOf r m) = 2 ^ r := by
  rw [wordD_eq_pow_two_length, parityWordOf_length]

/-- Soundness of `cylinderCert`: if `cylinderCert r r₀ = true`, then every `n > 1`
    with `n % 2^r = r₀` strictly descends in `k ≥ r > 0` standard `collatz` steps. -/
theorem cylinderCert_sound (r r₀ n : Nat)
    (hcert : cylinderCert r r₀ = true) (hn1 : n > 1) (hmod : n % (2 ^ r) = r₀) :
    ∃ k : Nat, k > 0 ∧ iterateCollatz n k < n := by
  unfold cylinderCert at hcert
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hcert
  rcases hcert with ⟨⟨⟨hr, hr₀⟩, hgt⟩, hgap₀⟩
  have hD_pow : wordD (parityWordOf r r₀) = 2 ^ r := wordD_parityWordOf r r₀
  have hmod_w : n % wordD (parityWordOf r r₀) = r₀ := by rw [hD_pow]; exact hmod
  obtain ⟨q, hq_eq⟩ : ∃ q : Nat, n = r₀ + q * wordD (parityWordOf r r₀) := by
    refine ⟨n / wordD (parityWordOf r r₀), ?_⟩
    have hdiv := Nat.mod_add_div n (wordD (parityWordOf r r₀))
    have hcomm : wordD (parityWordOf r r₀) * (n / wordD (parityWordOf r r₀)) =
        (n / wordD (parityWordOf r r₀)) * wordD (parityWordOf r r₀) := Nat.mul_comm _ _
    omega
  have hv_r₀ : validParityWord r₀ (parityWordOf r r₀) := parityWordOf_valid r r₀
  have hv_n : validParityWord n (parityWordOf r r₀) := by
    rw [hq_eq]
    exact (parityWord_residue_shift (parityWordOf r r₀) r₀ q hv_r₀).1
  have hn_ge : n ≥ minClassRep (wordD (parityWordOf r r₀)) r₀ := by
    unfold minClassRep
    by_cases hle1 : r₀ ≤ 1
    · rw [if_pos hle1]
      have hq_pos : q ≥ 1 := by
        cases q with
        | zero =>
          rw [Nat.zero_mul, Nat.add_zero] at hq_eq
          omega
        | succ q' => omega
      have hqD : q * wordD (parityWordOf r r₀) ≥ 1 * wordD (parityWordOf r r₀) :=
        Nat.mul_le_mul_right (wordD (parityWordOf r r₀)) hq_pos
      omega
    · rw [if_neg hle1]
      omega
  have hgap_n : (wordD (parityWordOf r r₀) - wordA (parityWordOf r r₀)) * n >
      wordB (parityWordOf r r₀) := by
    have hmul : (wordD (parityWordOf r r₀) - wordA (parityWordOf r r₀)) *
        minClassRep (wordD (parityWordOf r r₀)) r₀ ≤
        (wordD (parityWordOf r r₀) - wordA (parityWordOf r r₀)) * n :=
      Nat.mul_le_mul_left (wordD (parityWordOf r r₀) - wordA (parityWordOf r r₀)) hn_ge
    omega
  have hlt_w : applyParityWord n (parityWordOf r r₀) < n :=
    (contracting_word_descent_iff (parityWordOf r r₀) n hv_n hgt).mpr hgap_n
  have hw_eq : parityWordOf r n = parityWordOf r r₀ := by
    have h := (validParityWord_iff_eq_parityWordOf (parityWordOf r r₀) n).mp hv_n
    rw [parityWordOf_length r r₀] at h
    exact h
  have hacc_lt : iterateAccelerated n r < n := by
    rw [← applyParityWord_parityWordOf r n, hw_eq]
    exact hlt_w
  rcases iterateAccelerated_to_iterateCollatz n r with ⟨k, hk, heq⟩
  refine ⟨k, by omega, ?_⟩
  omega

/-- Multi-depth adaptive cylinder certificate up to depth 8 (`mod 256`). -/
def dischargedByDepth8 (r₂₅₆ : Nat) : Bool :=
  cylinderCert 1 (r₂₅₆ % 2) ||
  cylinderCert 2 (r₂₅₆ % 4) ||
  cylinderCert 3 (r₂₅₆ % 8) ||
  cylinderCert 4 (r₂₅₆ % 16) ||
  cylinderCert 5 (r₂₅₆ % 32) ||
  cylinderCert 6 (r₂₅₆ % 64) ||
  cylinderCert 7 (r₂₅₆ % 128) ||
  cylinderCert 8 (r₂₅₆ % 256)

/-- Soundness of `dischargedByDepth8`: any `n > 1` whose mod-256 residue satisfies
    `dischargedByDepth8 (n % 256) = true` reaches a strictly smaller integer under `collatz`. -/
theorem dischargedByDepth8_sound (n : Nat) (hn1 : n > 1)
    (h : dischargedByDepth8 (n % 256) = true) :
    ∃ k : Nat, k > 0 ∧ iterateCollatz n k < n := by
  unfold dischargedByDepth8 at h
  simp only [Bool.or_eq_true] at h
  rcases h with ((((((h1 | h2) | h3) | h4) | h5) | h6) | h7) | h8
  · exact cylinderCert_sound 1 ((n % 256) % 2) n h1 hn1 (by omega)
  · exact cylinderCert_sound 2 ((n % 256) % 4) n h2 hn1 (by omega)
  · exact cylinderCert_sound 3 ((n % 256) % 8) n h3 hn1 (by omega)
  · exact cylinderCert_sound 4 ((n % 256) % 16) n h4 hn1 (by omega)
  · exact cylinderCert_sound 5 ((n % 256) % 32) n h5 hn1 (by omega)
  · exact cylinderCert_sound 6 ((n % 256) % 64) n h6 hn1 (by omega)
  · exact cylinderCert_sound 7 ((n % 256) % 128) n h7 hn1 (by omega)
  · exact cylinderCert_sound 8 ((n % 256) % 256) n h8 hn1 (by omega)

/-- The 4 surviving expanding residue classes modulo 32 (depth 5). -/
def frontier32 : List Nat := [7, 15, 27, 31]

/-- The 8 surviving expanding residue classes modulo 64 (depth 6). -/
def frontier64 : List Nat := [7, 15, 27, 31, 39, 47, 59, 63]

/-- The 3 residue classes modulo 128 newly discharged at depth 7 (`2^7 = 128 > 81 = 3^4`). -/
def discharged128 : List Nat := [7, 15, 59]

/-- The 13 surviving expanding residue classes modulo 128 (depth 7). -/
def frontier128 : List Nat := [27, 31, 39, 47, 63, 71, 79, 91, 95, 103, 111, 123, 127]

/-- The 7 residue classes modulo 256 newly discharged at depth 8 (`2^8 = 256 > 243 = 3^5`). -/
def discharged256 : List Nat := [39, 79, 95, 123, 175, 199, 219]

/-- The 19 surviving expanding residue classes modulo 256 (depth 8). -/
def frontier256 : List Nat :=
  [27, 31, 47, 63, 71, 91, 103, 111, 127, 155, 159, 167, 191, 207, 223, 231, 239, 251, 255]

/-- Kernel-checked verification of the newly discharged classes at depths 7 and 8,
    and verification that all surviving frontier classes at depths 5, 6, 7, 8 are expanding. -/
theorem adaptive_refinement_catalog_certified :
    (discharged128.all (cylinderCert 7)) = true ∧
    (discharged256.all (cylinderCert 8)) = true ∧
    (frontier32.all (fun r₀ => decide (wordA (parityWordOf 5 r₀) > wordD (parityWordOf 5 r₀)))) = true ∧
    (frontier64.all (fun r₀ => decide (wordA (parityWordOf 6 r₀) > wordD (parityWordOf 6 r₀)))) = true ∧
    (frontier128.all (fun r₀ => decide (wordA (parityWordOf 7 r₀) > wordD (parityWordOf 7 r₀)))) = true ∧
    (frontier256.all (fun r₀ => decide (wordA (parityWordOf 8 r₀) > wordD (parityWordOf 8 r₀)))) = true := by
  decide

/-- Kernel-checked partition of all 256 residue classes modulo 256 into the 237 discharged
    classes (`dischargedByDepth8 r = true`) and the 19 surviving classes (`r ∈ frontier256`). -/
theorem mod256_partition_certified :
    ((List.range 256).all (fun r => dischargedByDepth8 r != frontier256.elem r)) = true ∧
    frontier256.length = 19 := by
  decide

/-- Exhaustive modulo-256 coverage lemma: every residue `r < 256` either satisfies
    `dischargedByDepth8 r = true` or belongs to `frontier256`. -/
theorem mod256_discharged_or_in_frontier256 :
    ((List.range 256).all (fun r => dischargedByDepth8 r || decide (r ∈ frontier256))) = true := by
  decide

/-- Exact Modulo-256 Frontier Reduction Theorem (COLLATZ-C6):
    `CollatzConjecture` is logically equivalent to descent on the 19 surviving
    expanding residue classes modulo 256 (`237 / 256 = 92.58%` unconditionally discharged). -/
theorem collatz_iff_mod256_frontier_descent :
    CollatzConjecture ↔
      (∀ n : Nat, n > 1 → (n % 256) ∈ frontier256 →
        ∃ k : Nat, k > 0 ∧ iterateCollatz n k < n) := by
  rw [← universalCollatzDescent_iff_collatz]
  constructor
  · intro h n hn1 _
    exact h n hn1
  · intro hfront n hn1
    have hlt : n % 256 < 256 := Nat.mod_lt n (by decide)
    have hmem : (n % 256) ∈ List.range 256 := List.mem_range.mpr hlt
    have hor : (dischargedByDepth8 (n % 256) || decide ((n % 256) ∈ frontier256)) = true :=
      (List.all_eq_true.mp mod256_discharged_or_in_frontier256) (n % 256) hmem
    rw [Bool.or_eq_true] at hor
    rcases hor with hdisc | hfelem
    · exact dischargedByDepth8_sound n hn1 hdisc
    · exact hfront n hn1 (of_decide_eq_true hfelem)

/-! #### C6 Well-Foundedness vs. 2-Adic Escape Analysis -/

/-- Staircase Depth Obstruction: if a parity word `w` has `wordA w > 2 * wordD w`,
    then even after appending an even step (`false :: w` or `w` extended by one step),
    its multiplicative factor remains strictly greater than the doubled denominator `2 * wordD w`. -/
theorem staircase_no_discharge_when_wordA_gt_two_wordD (w : List Bool)
    (h : wordA w > 2 * wordD w) (b : Bool) :
    wordA (b :: w) > wordD (b :: w) := by
  cases b <;> dsimp [wordA, wordD] <;> omega

/-- Exact 2-adic divisibility law for the infinite `allTrueWord` branch:
    For every `r : Nat` and `n : Nat`, if `validParityWord n (allTrueWord r)` holds,
    then `wordD (allTrueWord r) = 2^r` divides `n + 1` (`(n + 1) % wordD (allTrueWord r) = 0`). -/
theorem validParityWord_allTrueWord_div (r : Nat) :
    ∀ n : Nat, validParityWord n (allTrueWord r) →
      (n + 1) % wordD (allTrueWord r) = 0 := by
  induction r with
  | zero =>
    intro n _
    dsimp [allTrueWord, List.replicate, wordD]
    omega
  | succ r ih =>
    intro n hv
    dsimp [allTrueWord, List.replicate, validParityWord] at hv
    rcases hv with ⟨hp, htail⟩
    dsimp [stepParityMatches] at hp
    have hne0 : ¬(n % 2 = 0) := by omega
    have hacc : acceleratedCollatz n = 3 * (n / 2) + 2 := by
      unfold acceleratedCollatz
      rw [if_neg hne0]
      omega
    rw [hacc] at htail
    have hih := ih (3 * (n / 2) + 2) htail
    have h3 : (3 * (n / 2 + 1)) % wordD (allTrueWord r) = 0 := by
      have heq : 3 * (n / 2) + 2 + 1 = 3 * (n / 2 + 1) := by omega
      rw [← heq]
      exact hih
    have hd := three_mul_mod_wordD_eq_zero (allTrueWord r) (n / 2 + 1) h3
    dsimp [allTrueWord, List.replicate, wordD]
    have hn1 : n + 1 = 2 * (n / 2 + 1) := by omega
    rw [hn1, Nat.mul_mod_mul_left]
    change 2 * ((n / 2 + 1) % wordD (allTrueWord r)) = 0
    rw [hd]

/-- Lower bound for integers remaining on `allTrueWord r`:
    any `n : Nat` satisfying `validParityWord n (allTrueWord r)` must satisfy
    `n + 1 ≥ wordD (allTrueWord r) = 2^r`. -/
theorem validParityWord_allTrueWord_ge (r n : Nat)
    (hv : validParityWord n (allTrueWord r)) :
    n + 1 ≥ wordD (allTrueWord r) := by
  have hmod := validParityWord_allTrueWord_div r n hv
  by_cases hlt : n + 1 < wordD (allTrueWord r)
  · have heq : (n + 1) % wordD (allTrueWord r) = n + 1 := Nat.mod_eq_of_lt hlt
    omega
  · omega

/-- Exponential growth `wordD (allTrueWord r) > r` for all `r : Nat`. -/
theorem wordD_allTrueWord_gt_self (r : Nat) :
    wordD (allTrueWord r) > r := by
  induction r with
  | zero =>
    dsimp [allTrueWord, List.replicate, wordD]
    omega
  | succ r ih =>
    dsimp [allTrueWord, List.replicate, wordD] at ih ⊢
    omega

/-- Individual Escape Theorem from the Infinite 2-Adic Branch:
    While `allTrueWord r` is an infinite unresolved branch in the 2-adic residue tree,
    NO natural number `n ∈ ℕ` can remain on `allTrueWord (n + 1)`: every positive integer `n`
    must exit the all-odd branch in at most `n` accelerated steps. -/
theorem every_nat_exits_allTrue_branch (n : Nat) :
    ¬ validParityWord n (allTrueWord (n + 1)) := by
  intro hv
  have hge := validParityWord_allTrueWord_ge (n + 1) n hv
  have hgt := wordD_allTrueWord_gt_self (n + 1)
  omega

/-! ### COLLATZ-C7: Odd-to-Odd Return-Map Qualification & Cross-Branch Dynamics
    - **C7.1 (Exact Return-Map Composition)**: General parity-word concatenation laws
      (`wordA_append`, `wordD_append`, `wordB_append`, `validParityWord_append`,
      `applyParityWord_append`) and exact odd-to-odd return-map operator `returnMapWord ks`
      for arbitrary valuation sequences `ks : List Nat`.
    - **C7.2 (Arithmetic Constraints on Valuation Sequences)**: Exact modulo-`2^{K_r}` residue
      bijection for valuation sequences, odd-input preservation, and finite-prefix vs.
      infinite-path separation (`returnMapWord_replicate_zero_eq_allTrueWord`).
    - **C7.3 (Cross-Branch Compensation & Descent)**: Exact necessary and sufficient condition
      (`cross_branch_descent_iff`) for an expanding segment `w₁` followed by a contracting
      segment `w₂` to achieve net descent `F_{w₁ ++ w₂}(n) < n`.
    - **C7.4 & Section 5 (Minimal-Crossing Structure & Infinite-Path Obstruction)**:
      Proof that every minimal-crossing word ends with an even step (`minimal_crossing_last_bit_false`)
      and exact equivalence `CollatzConjecture ↔ ∀ n > 1, EventuallyHitsContractingCylinder n`
      (`eventuallyHitsContractingCylinder_iff_collatz`).
-/

/-! #### C7.1: General Operator Composition & Odd-to-Odd Return Map -/

/-- Exact validity composition across concatenated parity words `w₁ ++ w₂`. -/
theorem validParityWord_append (w₁ w₂ : List Bool) :
    ∀ m : Nat, validParityWord m (w₁ ++ w₂) ↔
      validParityWord m w₁ ∧ validParityWord (applyParityWord m w₁) w₂ := by
  induction w₁ with
  | nil =>
    intro m
    simp [validParityWord, applyParityWord]
  | cons b bs ih =>
    intro m
    dsimp [validParityWord, applyParityWord]
    rw [ih (acceleratedCollatz m), and_assoc]

/-- Exact operator composition across concatenated parity words `w₁ ++ w₂`. -/
theorem applyParityWord_append (w₁ w₂ : List Bool) :
    ∀ m : Nat, applyParityWord m (w₁ ++ w₂) =
      applyParityWord (applyParityWord m w₁) w₂ := by
  induction w₁ with
  | nil =>
    intro m
    rfl
  | cons b bs ih =>
    intro m
    dsimp [applyParityWord]
    exact ih (acceleratedCollatz m)

/-- Multiplicative numerator law for `w₁ ++ w₂`: `wordA (w₁ ++ w₂) = wordA w₁ * wordA w₂`. -/
theorem wordA_append (w₁ w₂ : List Bool) :
    wordA (w₁ ++ w₂) = wordA w₁ * wordA w₂ := by
  induction w₁ with
  | nil =>
    dsimp [wordA]
    omega
  | cons b bs ih =>
    cases b with
    | false =>
      dsimp [wordA]
      exact ih
    | true =>
      dsimp [wordA]
      rw [ih, Nat.mul_assoc]

/-- Multiplicative denominator law for `w₁ ++ w₂`: `wordD (w₁ ++ w₂) = wordD w₁ * wordD w₂`. -/
theorem wordD_append (w₁ w₂ : List Bool) :
    wordD (w₁ ++ w₂) = wordD w₁ * wordD w₂ := by
  induction w₁ with
  | nil =>
    dsimp [wordD]
    omega
  | cons b bs ih =>
    dsimp [wordD]
    rw [ih, Nat.mul_assoc]

/-- Exact affine cocycle law for `wordB (w₁ ++ w₂)`:
    `wordB (w₁ ++ w₂) = wordA w₂ * wordB w₁ + wordD w₁ * wordB w₂`. -/
theorem wordB_append (w₁ w₂ : List Bool) :
    wordB (w₁ ++ w₂) = wordA w₂ * wordB w₁ + wordD w₁ * wordB w₂ := by
  induction w₁ with
  | nil =>
    dsimp [wordB, wordD]
    omega
  | cons b bs ih =>
    cases b with
    | false =>
      dsimp [wordB, wordD]
      rw [ih]
      have h1 : 2 * (wordA w₂ * wordB bs + wordD bs * wordB w₂) =
          wordA w₂ * (2 * wordB bs) + (2 * wordD bs) * wordB w₂ := by
        rw [Nat.mul_add, ← Nat.mul_assoc 2 (wordA w₂) (wordB bs),
          Nat.mul_comm 2 (wordA w₂), Nat.mul_assoc (wordA w₂) 2 (wordB bs),
          ← Nat.mul_assoc 2 (wordD bs) (wordB w₂)]
      exact h1
    | true =>
      dsimp [wordB, wordD]
      rw [ih, wordA_append]
      have h1 : wordA bs * wordA w₂ + 2 * (wordA w₂ * wordB bs + wordD bs * wordB w₂) =
          wordA w₂ * (wordA bs + 2 * wordB bs) + (2 * wordD bs) * wordB w₂ := by
        rw [Nat.mul_add 2, Nat.mul_add (wordA w₂), Nat.mul_comm (wordA bs) (wordA w₂),
          ← Nat.mul_assoc 2 (wordA w₂) (wordB bs), Nat.mul_comm 2 (wordA w₂),
          Nat.mul_assoc (wordA w₂) 2 (wordB bs), ← Nat.mul_assoc 2 (wordD bs) (wordB w₂),
          Nat.add_assoc]
      exact h1

/-- Odd-to-odd return-map parity word for a sequence of extra-halving counts
    `ks = [k₁, ..., kᵣ]` (where the `i`-th odd-to-odd step divides `3n + 1` by `2^{kᵢ + 1}`). -/
def returnMapWord : List Nat → List Bool
  | [] => []
  | k :: ks => singleOddWord k ++ returnMapWord ks

/-- Total 2-adic exponent `K_r = ∑_{i=1}^r (kᵢ + 1)` of a valuation sequence `ks`. -/
def totalValuation (ks : List Nat) : Nat :=
  (returnMapWord ks).length

/-- C7.1: `wordA` of an `r`-step odd-to-odd return sequence `ks` is `3^r`. -/
theorem wordA_returnMapWord (ks : List Nat) :
    wordA (returnMapWord ks) = 3 ^ ks.length := by
  induction ks with
  | nil => rfl
  | cons k ks ih =>
    dsimp [returnMapWord]
    rw [wordA_append, wordA_singleOddWord, ih, Nat.pow_succ, Nat.mul_comm]

/-- C7.1: `wordD` of an `r`-step odd-to-odd return sequence `ks` is `2^(totalValuation ks)`. -/
theorem wordD_returnMapWord (ks : List Nat) :
    wordD (returnMapWord ks) = 2 ^ totalValuation ks :=
  wordD_eq_pow_two_length (returnMapWord ks)

/-- C7.1 (Exact Return-Map Composition Formula):
    For every valuation sequence `ks : List Nat` and every admissible integer `n`,
    `2^(totalValuation ks) * applyParityWord n (returnMapWord ks) = 3^(ks.length) * n + wordB (returnMapWord ks)`. -/
theorem returnMap_exact_affine (ks : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord ks)) :
    2 ^ totalValuation ks * applyParityWord n (returnMapWord ks) =
      3 ^ ks.length * n + wordB (returnMapWord ks) := by
  rw [← wordD_returnMapWord ks, ← wordA_returnMapWord ks]
  exact parityWord_affine_identity (returnMapWord ks) n hv

/-! #### C7.2: Arithmetic Constraints on Valuation Sequences -/

/-- C7.2: Every finite valuation sequence `ks` is admissible and corresponds to the unique
    residue class `wordResidue (returnMapWord ks)` modulo `2^(totalValuation ks)`. -/
theorem returnMapWord_admissible_iff (ks : List Nat) (n : Nat) :
    validParityWord n (returnMapWord ks) ↔
      n % (2 ^ totalValuation ks) = wordResidue (returnMapWord ks) := by
  rw [← wordD_returnMapWord ks]
  exact validParityWord_iff_mod_eq_wordResidue (returnMapWord ks) n

/-- C7.2: Any integer `n` realizing a non-empty odd-to-odd return sequence `k :: ks` is odd. -/
theorem returnMapWord_input_odd (k : Nat) (ks : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord (k :: ks))) :
    n % 2 = 1 := by
  dsimp [returnMapWord, singleOddWord, validParityWord, stepParityMatches] at hv
  exact hv.1

/-- C7.2: Exact algebraic identity for `allTrueWord r`:
    `wordB (allTrueWord r) + wordD (allTrueWord r) = wordA (allTrueWord r)` (`B_r = 3^r - 2^r`). -/
theorem wordB_allTrueWord_add_wordD (r : Nat) :
    wordB (allTrueWord r) + wordD (allTrueWord r) = wordA (allTrueWord r) := by
  induction r with
  | zero =>
    dsimp [allTrueWord, List.replicate, wordB, wordD, wordA]
  | succ r ih =>
    dsimp [allTrueWord, List.replicate, wordB, wordD, wordA] at ih ⊢
    omega

/-- C7.2: Exact closed-form trajectory of `allTrueWord r` on its base representative `2^r - 1`:
    `applyParityWord (wordD (allTrueWord r) - 1) (allTrueWord r) = wordA (allTrueWord r) - 1`. -/
theorem applyParityWord_allTrueWord_base (r : Nat)
    (hv : validParityWord (wordD (allTrueWord r) - 1) (allTrueWord r)) :
    applyParityWord (wordD (allTrueWord r) - 1) (allTrueWord r) =
      wordA (allTrueWord r) - 1 := by
  have hid := parityWord_affine_identity (allTrueWord r) (wordD (allTrueWord r) - 1) hv
  have hBD := wordB_allTrueWord_add_wordD r
  have hD : wordD (allTrueWord r) ≥ 1 := wordD_pos (allTrueWord r)
  have hA : wordA (allTrueWord r) ≥ 1 := wordA_pos (allTrueWord r)
  have hsub1 : wordA (allTrueWord r) * (wordD (allTrueWord r) - 1) + wordA (allTrueWord r) =
      wordA (allTrueWord r) * wordD (allTrueWord r) := by
    rw [← Nat.mul_succ]
    congr 1
    omega
  have hsub2 : wordD (allTrueWord r) * (wordA (allTrueWord r) - 1) + wordD (allTrueWord r) =
      wordD (allTrueWord r) * wordA (allTrueWord r) := by
    rw [← Nat.mul_succ]
    congr 1
    omega
  have hcomm : wordA (allTrueWord r) * wordD (allTrueWord r) =
      wordD (allTrueWord r) * wordA (allTrueWord r) := Nat.mul_comm _ _
  have hcomb : wordD (allTrueWord r) *
      applyParityWord (wordD (allTrueWord r) - 1) (allTrueWord r) =
      wordD (allTrueWord r) * (wordA (allTrueWord r) - 1) := by omega
  exact Nat.eq_of_mul_eq_mul_left hD hcomb

/-- C7.2: Exact closed-form trajectory of `allTrueWord r` on `(2^r - 1) + q * 2^r`:
    `applyParityWord ((wordD (allTrueWord r) - 1) + q * wordD (allTrueWord r)) (allTrueWord r) = (wordA (allTrueWord r) - 1) + q * wordA (allTrueWord r)`. -/
theorem applyParityWord_allTrueWord_exact (r q : Nat)
    (hv : validParityWord (wordD (allTrueWord r) - 1) (allTrueWord r)) :
    applyParityWord ((wordD (allTrueWord r) - 1) + q * wordD (allTrueWord r)) (allTrueWord r) =
      (wordA (allTrueWord r) - 1) + q * wordA (allTrueWord r) := by
  rw [(parityWord_residue_shift (allTrueWord r) (wordD (allTrueWord r) - 1) q hv).2,
    applyParityWord_allTrueWord_base r hv]

/-- C7.2: A valuation sequence of `r` minimal valuations (`kᵢ = 0`, i.e. `tᵢ = 1`)
    is identical to `allTrueWord r`. -/
theorem returnMapWord_replicate_zero (r : Nat) :
    returnMapWord (List.replicate r 0) = allTrueWord r := by
  induction r with
  | zero => rfl
  | succ r ih =>
    dsimp [List.replicate, returnMapWord, singleOddWord, allTrueWord]
    rw [ih]
    rfl

/-- C7.2 (Finite Prefix vs. Infinite Trajectory Separation for Valuation Sequences):
    While `List.replicate r 0` is admissible for every finite `r`, NO natural number `n`
    can realize the valuation sequence `List.replicate (n + 1) 0`. -/
theorem no_nat_realizes_replicate_zero_self (n : Nat) :
    ¬ validParityWord n (returnMapWord (List.replicate (n + 1) 0)) := by
  rw [returnMapWord_replicate_zero]
  exact every_nat_exits_allTrue_branch n

/-! #### C7.3: Cross-Branch Compensation & Descent -/

/-- C7.3 (Exact Cross-Branch Compensation Theorem):
    Suppose a trajectory executes segment `w₁` (e.g. an expanding segment) followed by
    segment `w₂` (a compensating contracting segment) such that the combined spectral
    condition `wordD w₁ * wordD w₂ > wordA w₁ * wordA w₂` holds.
    Then `applyParityWord (applyParityWord n w₁) w₂ < n` holds if and only if
    `(wordD w₁ * wordD w₂ - wordA w₁ * wordA w₂) * n > wordA w₂ * wordB w₁ + wordD w₁ * wordB w₂`. -/
theorem cross_branch_descent_iff (w₁ w₂ : List Bool) (n : Nat)
    (hv₁ : validParityWord n w₁)
    (hv₂ : validParityWord (applyParityWord n w₁) w₂)
    (hgt : wordD w₁ * wordD w₂ > wordA w₁ * wordA w₂) :
    applyParityWord (applyParityWord n w₁) w₂ < n ↔
      (wordD w₁ * wordD w₂ - wordA w₁ * wordA w₂) * n >
        wordA w₂ * wordB w₁ + wordD w₁ * wordB w₂ := by
  have hv : validParityWord n (w₁ ++ w₂) :=
    (validParityWord_append w₁ w₂ n).mpr ⟨hv₁, hv₂⟩
  have hgt' : wordD (w₁ ++ w₂) > wordA (w₁ ++ w₂) := by
    rw [wordD_append, wordA_append]
    exact hgt
  rw [← applyParityWord_append w₁ w₂ n,
    contracting_word_descent_iff (w₁ ++ w₂) n hv hgt',
    wordD_append, wordA_append, wordB_append]

/-! #### C7.4 & Section 5: Minimal-Crossing Structure & Infinite-Path Obstruction -/

/-- Section 5 (Minimal-Crossing Terminal Step Theorem):
    If `w₁` is spectrally expanding (`wordA w₁ > wordD w₁`) and `w₁ ++ [b]` is spectrally
    contracting (`wordD (w₁ ++ [b]) > wordA (w₁ ++ [b])`), then the crossing step `b`
    MUST be `false` (even) and `2 * wordD w₁ > wordA w₁`. -/
theorem minimal_crossing_terminal_step_even (w₁ : List Bool) (b : Bool)
    (hexp : wordA w₁ > wordD w₁)
    (hcon : wordD (w₁ ++ [b]) > wordA (w₁ ++ [b])) :
    b = false ∧ 2 * wordD w₁ > wordA w₁ := by
  rw [wordD_append, wordA_append] at hcon
  cases b with
  | false =>
    dsimp [wordD, wordA] at hcon
    exact ⟨rfl, by omega⟩
  | true =>
    dsimp [wordD, wordA] at hcon
    omega

/-- Predicate that `n` eventually reaches a parity cylinder `w = parityWordOf r n` (`r > 0`)
    satisfying spectral contraction `wordD w > wordA w` and the affine descent inequality
    `(wordD w - wordA w) * n > wordB w`. -/
def EventuallyHitsContractingCylinder (n : Nat) : Prop :=
  ∃ r : Nat, r > 0 ∧
    let w := parityWordOf r n
    wordD w > wordA w ∧ (wordD w - wordA w) * n > wordB w

/-- C7.4 (Exact Infinite-Path Obstruction Equivalence):
    `CollatzConjecture` holds if and only if every integer `n > 1` eventually reaches
    a contracting parity cylinder above its affine threshold (`EventuallyHitsContractingCylinder n`). -/
theorem eventuallyHitsContractingCylinder_iff_collatz :
    (∀ n : Nat, n > 1 → EventuallyHitsContractingCylinder n) ↔ CollatzConjecture := by
  rw [← universalAcceleratedDescent_iff_collatz]
  constructor
  · intro h n hn1
    rcases h n hn1 with ⟨r, hr, hgt, hgap⟩
    have hv : validParityWord n (parityWordOf r n) := parityWordOf_valid r n
    have hlt : applyParityWord n (parityWordOf r n) < n :=
      (contracting_word_descent_iff (parityWordOf r n) n hv hgt).mpr hgap
    rw [applyParityWord_parityWordOf r n] at hlt
    exact ⟨r, hr, hlt⟩
  · intro h n hn1
    rcases h n hn1 with ⟨r, hr, hlt⟩
    let w := parityWordOf r n
    have hv : validParityWord n w := parityWordOf_valid r n
    have hlt_w : applyParityWord n w < n := by
      rw [applyParityWord_parityWordOf r n]
      exact hlt
    have hgt : wordD w > wordA w := by
      by_cases hge : wordA w ≥ wordD w
      · by_cases hB : wordB w = 0
        · have hA1 : wordA w = 1 := (wordB_eq_zero_iff_wordA_eq_one w).mp hB
          have hlen : w.length = r := parityWordOf_length r n
          have hne : w ≠ [] := by
            intro hnil
            rw [hnil] at hlen
            dsimp at hlen
            omega
          have hD2 : wordD w ≥ 2 := wordD_ge_two_of_ne_nil w hne
          omega
        · have hgrow := expanding_word_strict_growth w n hv hge (by omega)
          omega
      · omega
    have hgap : (wordD w - wordA w) * n > wordB w :=
      (contracting_word_descent_iff w n hv hgt).mp hlt_w
    exact ⟨r, hr, hgt, hgap⟩

/-! ### COLLATZ-C8: Minimal-Crossing Inequality `(D(w) - A(w)) * m_min(w) > B(w)` & Pincer Certification
    Formalizing the priority proof obligation from the C7 qualification review:
    1. `wordOnes` and the inductive characterization `IsPrefixExpanding` & `IsFirstCrossing` (`w ∈ 𝓜`).
    2. Universal Lean proof of the analytical offset bound (`three_mul_wordB_le_wordOnes_mul_wordA`):
       `IsPrefixExpanding w → 3 * wordB w ≤ wordOnes w * wordA w` (`B(w) ≤ a(w) * 3^{a(w)-1}`).
    3. Exact equivalence (`firstCrossing_inequality_iff_trajectory_descent`): for every `w` with
       `wordD w > wordA w`, `(wordD w - wordA w) * m_min(w) > wordB w` holds if and only if
       the constructive representative `m_min(w)` itself descends at step `|w|`
       (`iterateAccelerated (m_min w) w.length < m_min w`).
    4. Two-sided Pincer Theorem (`firstCrossing_spectral_pincer_descent`): whenever
       `3 * (wordD w - wordA w) * m_min(w) > wordOnes w * wordA w`, every first-crossing word
       `w ∈ 𝓜` satisfies `(wordD w - wordA w) * m_min(w) > wordB w` and discharges its entire
       positive residue cylinder.
    5. Constructive survival lower bound (`survival_past_depth7_forces_ge_27`): every integer
       `2 ≤ n < 27` is discharged at depth `≤ 7`, so any residue class surviving depth `7`
       satisfies `m_min(w) ≥ 27`.
-/

/-- Number of odd steps (`true` bits) in a parity word `w`. -/
def wordOnes : List Bool → Nat
  | [] => 0
  | false :: bs => wordOnes bs
  | true :: bs => wordOnes bs + 1

/-- Additive law for `wordOnes` across concatenation `w₁ ++ w₂`. -/
theorem wordOnes_append (w₁ w₂ : List Bool) :
    wordOnes (w₁ ++ w₂) = wordOnes w₁ + wordOnes w₂ := by
  induction w₁ with
  | nil =>
    dsimp [wordOnes]
    omega
  | cons b bs ih =>
    cases b <;> dsimp [wordOnes] <;> omega

/-- Exact power relation `wordA w = 3 ^ (wordOnes w)`. -/
theorem wordA_eq_pow_three_wordOnes (w : List Bool) :
    wordA w = 3 ^ wordOnes w := by
  induction w with
  | nil => rfl
  | cons b bs ih =>
    cases b with
    | false =>
      dsimp [wordA, wordOnes]
      exact ih
    | true =>
      dsimp [wordA, wordOnes]
      rw [ih, Nat.pow_succ, Nat.mul_comm]

/-- Inductive family of parity words whose prefixes preceding every odd step are
    spectrally non-contracting (`wordD w₁ ≤ wordA w₁`). -/
inductive IsPrefixExpanding : List Bool → Prop where
  | nil : IsPrefixExpanding []
  | snoc_false (w : List Bool) :
      IsPrefixExpanding w → IsPrefixExpanding (w ++ [false])
  | snoc_true (w : List Bool) :
      IsPrefixExpanding w → wordD w ≤ wordA w → IsPrefixExpanding (w ++ [true])

/-- The family `𝓜` of first-crossing parity words: `w = w₁ ++ [false]` where `w₁` is
    prefix-expanding with `wordD w₁ ≤ wordA w₁`, while `w` is contracting (`wordD w > wordA w`). -/
def IsFirstCrossing (w : List Bool) : Prop :=
  ∃ w₁ : List Bool,
    w = w₁ ++ [false] ∧
    IsPrefixExpanding w₁ ∧
    wordD w₁ ≤ wordA w₁ ∧
    wordD w > wordA w

theorem isFirstCrossing_implies_isPrefixExpanding (w : List Bool)
    (hw : IsFirstCrossing w) : IsPrefixExpanding w := by
  rcases hw with ⟨w₁, rfl, hw₁, _, _⟩
  exact IsPrefixExpanding.snoc_false w₁ hw₁

/-- Universal Prefix-Expanding Offset Bound (`3 * B(w) ≤ a(w) * A(w)`):
    For EVERY parity word `w` satisfying `IsPrefixExpanding w` (and in particular for
    every first-crossing word `w ∈ 𝓜`),
    `3 * wordB w ≤ wordOnes w * wordA w` (equivalently `B(w) ≤ a(w) * 3^{a(w)-1}`). -/
theorem three_mul_wordB_le_wordOnes_mul_wordA (w : List Bool)
    (hw : IsPrefixExpanding w) :
    3 * wordB w ≤ wordOnes w * wordA w := by
  induction hw with
  | nil =>
    dsimp [wordB, wordOnes, wordA]
    omega
  | snoc_false w _ ih =>
    rw [wordB_append, wordOnes_append, wordA_append]
    dsimp [wordB, wordOnes, wordA]
    rw [Nat.mul_one]
    omega
  | snoc_true w _ hDA ih =>
    rw [wordB_append, wordOnes_append, wordA_append]
    dsimp [wordB, wordOnes, wordA]
    have h1 : 3 * wordB w + wordD w ≤ wordOnes w * wordA w + wordA w := by omega
    have h2 : (wordOnes w + 1) * wordA w = wordOnes w * wordA w + wordA w := by
      rw [Nat.add_mul, Nat.one_mul]
    have h3 : (wordOnes w + 1) * (wordA w * 3) = 3 * (wordOnes w * wordA w + wordA w) := by
      rw [← h2, ← Nat.mul_assoc, Nat.mul_comm ((wordOnes w + 1) * wordA w) 3]
    omega

/-- Constructive minimal positive representative `m_min(w) > 1` of the residue cylinder of `w`. -/
def minWordRep (w : List Bool) : Nat :=
  minClassRep (wordD w) (wordResidue w)

theorem minWordRep_gt_one (w : List Bool) (hne : w ≠ []) :
    minWordRep w > 1 := by
  unfold minWordRep minClassRep
  have hD2 : wordD w ≥ 2 := wordD_ge_two_of_ne_nil w hne
  by_cases hle1 : wordResidue w ≤ 1
  · rw [if_pos hle1]; omega
  · rw [if_neg hle1]; omega

theorem minWordRep_valid (w : List Bool) :
    validParityWord (minWordRep w) w := by
  unfold minWordRep minClassRep
  by_cases hle1 : wordResidue w ≤ 1
  · rw [if_pos hle1]
    have h := (parityWord_residue_shift w (wordResidue w) 1 (wordResidue_valid w)).1
    simpa using h
  · rw [if_neg hle1]
    exact wordResidue_valid w

theorem parityWordOf_minWordRep (w : List Bool) :
    parityWordOf w.length (minWordRep w) = w :=
  (validParityWord_iff_eq_parityWordOf w (minWordRep w)).mp (minWordRep_valid w)

/-- Exact Trajectory Equivalence for the Minimal Representative `m_min(w)`:
    For any contracting word `w` (`wordD w > wordA w`), the minimal-crossing inequality
    `(wordD w - wordA w) * minWordRep w > wordB w` holds if and only if
    `iterateAccelerated (minWordRep w) w.length < minWordRep w`. -/
theorem firstCrossing_inequality_iff_trajectory_descent (w : List Bool)
    (hgt : wordD w > wordA w) :
    (wordD w - wordA w) * minWordRep w > wordB w ↔
      iterateAccelerated (minWordRep w) w.length < minWordRep w := by
  have hv := minWordRep_valid w
  rw [← contracting_word_descent_iff w (minWordRep w) hv hgt]
  have hp := applyParityWord_parityWordOf w.length (minWordRep w)
  rw [parityWordOf_minWordRep w] at hp
  rw [hp]

/-- First-Crossing Spectral Pincer Theorem:
    For EVERY first-crossing word `w ∈ 𝓜` (`IsFirstCrossing w`), if the constructive
    minimal representative `minWordRep w` satisfies
    `3 * (wordD w - wordA w) * minWordRep w > wordOnes w * wordA w`,
    then `(wordD w - wordA w) * minWordRep w > wordB w` holds and every integer `n > 1`
    in the residue class `n % wordD w = wordResidue w` strictly descends in `|w|` accelerated steps. -/
theorem firstCrossing_spectral_pincer_descent (w : List Bool)
    (hw : IsFirstCrossing w)
    (hpincer : 3 * ((wordD w - wordA w) * minWordRep w) > wordOnes w * wordA w) :
    (wordD w - wordA w) * minWordRep w > wordB w ∧
    (∀ n : Nat, n > 1 → n % wordD w = wordResidue w →
      applyParityWord n w < n) := by
  have hpe : IsPrefixExpanding w := isFirstCrossing_implies_isPrefixExpanding w hw
  have hB : 3 * wordB w ≤ wordOnes w * wordA w :=
    three_mul_wordB_le_wordOnes_mul_wordA w hpe
  rcases hw with ⟨w₁, hw_eq, _, _, hgt⟩
  have hineq : (wordD w - wordA w) * minWordRep w > wordB w := by omega
  refine ⟨hineq, ?_⟩
  intro n hn1 hmod
  have hv_n : validParityWord n w := (validParityWord_iff_mod_eq_wordResidue w n).mpr hmod
  rw [contracting_word_descent_iff w n hv_n hgt]
  obtain ⟨q, hq_eq⟩ : ∃ q : Nat, n = wordResidue w + q * wordD w := by
    refine ⟨n / wordD w, ?_⟩
    have hdiv := Nat.mod_add_div n (wordD w)
    have hcomm : wordD w * (n / wordD w) = (n / wordD w) * wordD w := Nat.mul_comm _ _
    omega
  have hn_ge : n ≥ minWordRep w := by
    unfold minWordRep minClassRep
    by_cases hle1 : wordResidue w ≤ 1
    · rw [if_pos hle1]
      have hq_pos : q ≥ 1 := by
        cases q with
        | zero =>
          rw [Nat.zero_mul, Nat.add_zero] at hq_eq
          omega
        | succ q' => omega
      have hqD : q * wordD w ≥ 1 * wordD w := Nat.mul_le_mul_right (wordD w) hq_pos
      omega
    · rw [if_neg hle1]
      omega
  have hmul : (wordD w - wordA w) * minWordRep w ≤ (wordD w - wordA w) * n :=
    Nat.mul_le_mul_left (wordD w - wordA w) hn_ge
  omega

/-- Exact Counterexample Obstruction Theorem for `w ∈ 𝓜`:
    Any hypothetical first-crossing word `w ∈ 𝓜` that fails the minimal-crossing inequality
    `(wordD w - wordA w) * minWordRep w > wordB w` must simultaneously satisfy:
    1. `3 * ((wordD w - wordA w) * minWordRep w) ≤ wordOnes w * wordA w`, and
    2. `iterateAccelerated (minWordRep w) w.length ≥ minWordRep w`. -/
theorem firstCrossing_counterexample_obstruction (w : List Bool)
    (hw : IsFirstCrossing w)
    (hfail : ¬((wordD w - wordA w) * minWordRep w > wordB w)) :
    3 * ((wordD w - wordA w) * minWordRep w) ≤ wordOnes w * wordA w ∧
    iterateAccelerated (minWordRep w) w.length ≥ minWordRep w := by
  have hpe : IsPrefixExpanding w := isFirstCrossing_implies_isPrefixExpanding w hw
  have hB : 3 * wordB w ≤ wordOnes w * wordA w :=
    three_mul_wordB_le_wordOnes_mul_wordA w hpe
  rcases hw with ⟨w₁, _, _, _, hgt⟩
  have hiff := firstCrossing_inequality_iff_trajectory_descent w hgt
  omega

/-- Kernel-checked verification that every integer `2 ≤ n < 27` is discharged by depth 8 (`dischargedByDepth8`). -/
theorem all_lt_27_dischargedByDepth8 :
    ((List.range 27).all (fun n => decide (n < 2) || dischargedByDepth8 (n % 256))) = true := by
  decide

/-- Survival Lower Bound Theorem (`n ≥ 27`):
    Every integer `n > 1` whose modulo-256 residue lies in the surviving 19-class frontier
    (`dischargedByDepth8 (n % 256) = false`) satisfies `n ≥ 27`. -/
theorem survival_past_depth8_forces_ge_27 (n : Nat) (hn1 : n > 1)
    (hsurv : dischargedByDepth8 (n % 256) = false) :
    n ≥ 27 := by
  by_cases hlt : n < 27
  · have hmem : n ∈ List.range 27 := List.mem_range.mpr hlt
    have hall := (List.all_eq_true.mp all_lt_27_dischargedByDepth8) n hmem
    have hn2 : decide (n < 2) = false := decide_eq_false (by omega)
    rw [hn2, hsurv] at hall
    contradiction
  · omega

end BBB17
