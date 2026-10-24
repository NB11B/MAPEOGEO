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

end BBB17
