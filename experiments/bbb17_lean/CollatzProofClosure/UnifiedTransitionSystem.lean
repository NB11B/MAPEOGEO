import CollatzProofClosure.Definitions
import CollatzProofClosure.SpectralCrossing
import CollatzProofClosure.GlobalDescent
import CollatzProofClosure.CycleObstructions

namespace BBB17
namespace CollatzProofClosure

/-! # Unified PSMSL + MAPEOGEO + Symbolic-Dynamics Collatz Transition System

    Integrates our parallel mathematical programs into a single formal proof-discovery object:

    1. **PSMSL Upper-Triangular Projective Operator Algebra (`OperatorMatrix`, `wordMatrix`)**:
       Every parity word `w` defines an exact upper-triangular operator matrix
       `M_w = [[A_w, B_w], [0, D_w]]` satisfying the exact composition law
       `wordMatrix (w₁ ++ w₂) = mulOpMatrix (wordMatrix w₂) (wordMatrix w₁)`
       and the projective fixed-point eigenvector identity on `(B_w, D_w - A_w)`.
    2. **MAPEOGEO Unified Transition State (`CollatzTransitionState`, `orbitSurplus`, `deficitReservoir`)**:
       Combines the trajectory value `n_r`, affine operator `(A_r, B_r, D_r)`, odd-step count `a_r`,
       2-adic affine surplus `Ω_r(n) = 2^r * (n_r - n)`, and cumulative Diophantine deficit
       reservoir `P_r(n)` into one state space with exact step-to-step transition equations:
       - Even step (`b_r = 0`): `P_{r+1} = P_r` and `Ω_{r+1} + 2^r * n = Ω_r` (forcing `n_r ≥ 2n`).
       - Odd step (`b_r = 1`): `P_{r+1} = (3n + 1) * P_r + n^{a_r} * Ω_r` and `Ω_{r+1} = 3 * Ω_r + 2^r * (n + 1)`.
    3. **Exact Reservoir-Surplus Conservation Law (`reservoir_surplus_conservation_law`)**:
       Upgrades the C10 multiplicative inequality `2^r * n^{a_r} * n_r ≤ n * (3n + 1)^{a_r}` into
       an **exact conservation identity** valid across all non-descending prefixes of any length `r`:
       `deficitReservoir n r + 2^r * n^{a_r} * F^r(n) = n * (3n + 1)^{a_r}`,
       or equivalently:
       `deficitReservoir n r + n^{a_r} * orbitSurplus n r + 2^r * n^{a_r + 1} = n * (3n + 1)^{a_r}`.
    4. **Symbolic-Dynamics Prefix Admissibility & Sharpened Power Bound (`sharpened_nondescent_power_bound`)**:
       Every non-descending orbit of `n > 1` must begin with `true :: true` (`n ≡ 3 (mod 4)`),
       injecting `P_2(n) = n * (n + 1) > 0` at step 2 and forcing for all `r ≥ 2`:
       `deficitReservoir n r ≥ n * (n + 1) * (3n + 1)^{a_r - 2}`
       and the strictly sharpened power bound:
       `2^r * n^{a_r - 1} ≤ (9n + 5) * (3n + 1)^{a_r - 2}`.
-/

/-! ## 1. PSMSL Upper-Triangular Projective Operator Algebra -/

/-- Exact 2×2 upper-triangular integer matrix `[[A, B], [0, D]]` representing the
    affine operator `x ↦ (A * x + B) / D` in projective coordinates `[x : 1]`. -/
structure OperatorMatrix where
  A : Nat
  B : Nat
  D : Nat
  deriving DecidableEq, Repr

/-- Exact matrix multiplication `M₂ * M₁` of upper-triangular operator matrices:
    `[[A₂, B₂], [0, D₂]] * [[A₁, B₁], [0, D₁]] = [[A₂*A₁, A₂*B₁ + B₂*D₁], [0, D₂*D₁]]`. -/
def mulOpMatrix (M₂ M₁ : OperatorMatrix) : OperatorMatrix :=
  { A := M₂.A * M₁.A
  , B := M₂.A * M₁.B + M₂.B * M₁.D
  , D := M₂.D * M₁.D }

/-- Elementary even-step (`false`) and odd-step (`true`) operator matrices:
    `M_false = [[1, 0], [0, 2]]` and `M_true = [[3, 1], [0, 2]]`. -/
def stepOpMatrix (b : Bool) : OperatorMatrix :=
  if b then { A := 3, B := 1, D := 2 } else { A := 1, B := 0, D := 2 }

/-- The operator matrix associated to a parity word `w`. -/
def wordMatrix (w : List Bool) : OperatorMatrix :=
  { A := wordA w, B := wordB w, D := wordD w }

/-- PSMSL Matrix Composition Theorem (`wordMatrix_append`):
    Composition of parity words `w₁ ++ w₂` corresponds to exact matrix multiplication
    `mulOpMatrix (wordMatrix w₂) (wordMatrix w₁)`. -/
theorem wordMatrix_append (w₁ w₂ : List Bool) :
    wordMatrix (w₁ ++ w₂) = mulOpMatrix (wordMatrix w₂) (wordMatrix w₁) := by
  unfold wordMatrix mulOpMatrix
  rw [wordA_append, wordB_append, wordD_append]
  have hA : wordA w₁ * wordA w₂ = wordA w₂ * wordA w₁ := Nat.mul_comm _ _
  have hD : wordD w₁ * wordD w₂ = wordD w₂ * wordD w₁ := Nat.mul_comm _ _
  have hB : wordD w₁ * wordB w₂ = wordB w₂ * wordD w₁ := Nat.mul_comm _ _
  rw [hA, hD, hB]

/-- Associativity of `mulOpMatrix`. -/
theorem mulOpMatrix_assoc (M₃ M₂ M₁ : OperatorMatrix) :
    mulOpMatrix M₃ (mulOpMatrix M₂ M₁) = mulOpMatrix (mulOpMatrix M₃ M₂) M₁ := by
  unfold mulOpMatrix
  dsimp
  have hA : M₃.A * (M₂.A * M₁.A) = M₃.A * M₂.A * M₁.A := (Nat.mul_assoc _ _ _).symm
  have hD : M₃.D * (M₂.D * M₁.D) = M₃.D * M₂.D * M₁.D := (Nat.mul_assoc _ _ _).symm
  have hB : M₃.A * (M₂.A * M₁.B + M₂.B * M₁.D) + M₃.B * (M₂.D * M₁.D) =
      (M₃.A * M₂.A) * M₁.B + (M₃.A * M₂.B + M₃.B * M₂.D) * M₁.D := by
    rw [Nat.mul_add, Nat.add_mul, ← Nat.mul_assoc, ← Nat.mul_assoc, ← Nat.mul_assoc, Nat.add_assoc]
  rw [hA, hB, hD]

/-- Projective Fixed-Ray Eigenvector Identity (`wordMatrix_projective_eigenvector`):
    In the contracting regime `wordD w ≥ wordA w`, the projective vector
    `(wordB w, wordD w - wordA w)` is an exact integer eigenvector of `wordMatrix w`
    with eigenvalue `wordD w = 2^{|w|}`. -/
theorem wordMatrix_projective_eigenvector (w : List Bool) (hcont : wordD w ≥ wordA w) :
    let M := wordMatrix w
    M.A * M.B + M.B * (M.D - M.A) = M.D * M.B ∧
    M.D * (M.D - M.A) = M.D * (M.D - M.A) := by
  dsimp [wordMatrix]
  constructor
  · rw [Nat.mul_comm (wordA w) (wordB w), ← Nat.left_distrib,
        Nat.add_sub_of_le hcont, Nat.mul_comm]
  · rfl

/-! ## 2. MAPEOGEO Unified State Space & Exact Reservoir-Surplus Conservation Law -/

/-- The 2-adically scaled non-descent surplus `Ω_r(n) = 2^r * (F^r(n) - n)`. -/
def orbitSurplus (n r : Nat) : Nat :=
  2 ^ r * (iterateAccelerated n r - n)

/-- The cumulative Diophantine deficit reservoir `P_r(n)` along a trajectory:
    - Invariant across even steps (`b_r = 0`),
    - Amplified by `(3n + 1)` and fed by `n^{a_r} * Ω_r(n)` on odd steps (`b_r = 1`). -/
def deficitReservoir (n : Nat) : Nat → Nat
  | 0 => 0
  | r + 1 =>
    if iterateAccelerated n r % 2 = 1 then
      (3 * n + 1) * deficitReservoir n r +
        n ^ wordOnes (parityWordOf r n) * orbitSurplus n r
    else
      deficitReservoir n r

/-- Unified MAPEOGEO state vector `X_r` combining trajectory, operator, spectral, residue,
    surplus, and reservoir coordinates at depth `r`. -/
structure CollatzTransitionState where
  n₀ : Nat
  r : Nat
  nr : Nat
  Ar : Nat
  Br : Nat
  Dr : Nat
  ar : Nat
  rho_r : Nat
  surplus : Nat
  reservoir : Nat
  deriving DecidableEq, Repr

/-- Construct the canonical state `X_r(n)` at depth `r`. -/
def stateAtDepth (n r : Nat) : CollatzTransitionState :=
  let w := parityWordOf r n
  { n₀ := n
  , r := r
  , nr := iterateAccelerated n r
  , Ar := wordA w
  , Br := wordB w
  , Dr := wordD w
  , ar := wordOnes w
  , rho_r := wordResidue w
  , surplus := orbitSurplus n r
  , reservoir := deficitReservoir n r }

/-- Exact connection between `orbitSurplus n r` and the affine operator `(A_r, B_r, D_r)`:
    Whenever `F^r(n) ≥ n`, `orbitSurplus n r + 2^r * n = 3^{a_r} * n + B_r`. -/
theorem orbitSurplus_affine_identity (n r : Nat) (hge : iterateAccelerated n r ≥ n) :
    let w := parityWordOf r n
    orbitSurplus n r + 2 ^ r * n = 3 ^ wordOnes w * n + wordB w := by
  dsimp [orbitSurplus]
  have hv := parityWordOf_valid r n
  have hid := parityWord_affine_identity (parityWordOf r n) n hv
  rw [applyParityWord_parityWordOf, wordD_eq_pow_two_length, parityWordOf_length,
      wordA_eq_pow_three_wordOnes] at hid
  rw [Nat.mul_sub_left_distrib, Nat.sub_add_cancel (Nat.mul_le_mul_left (2 ^ r) hge)]
  exact hid

/-- Even-Step Surplus Transition Law (`orbitSurplus_even_step`):
    If step `r` is even (`F^r(n) % 2 = 0`) and `F^{r+1}(n) ≥ n`, then
    `orbitSurplus n (r + 1) + 2^r * n = orbitSurplus n r`,
    and in particular `F^r(n) ≥ 2 * n`. -/
theorem orbitSurplus_even_step (n r : Nat)
    (hev : iterateAccelerated n r % 2 = 0)
    (hge_next : iterateAccelerated n (r + 1) ≥ n) :
    orbitSurplus n (r + 1) + 2 ^ r * n = orbitSurplus n r ∧
    iterateAccelerated n r ≥ 2 * n := by
  have hsucc : iterateAccelerated n (r + 1) = acceleratedCollatz (iterateAccelerated n r) :=
    iterateAccelerated_succ_right n r
  have hm : stepParityMatches (iterateAccelerated n r) false := by
    dsimp [stepParityMatches]; exact hev
  have hstep : 2 * acceleratedCollatz (iterateAccelerated n r) = iterateAccelerated n r := by
    have hs := acceleratedCollatz_step_eq (iterateAccelerated n r) false hm
    simpa using hs
  rw [← hsucc] at hstep
  have hge_2n : iterateAccelerated n r ≥ 2 * n := by omega
  refine ⟨?_, hge_2n⟩
  unfold orbitSurplus
  rw [Nat.pow_succ, Nat.mul_assoc (2 ^ r) 2 _, ← Nat.left_distrib]
  exact congrArg (2 ^ r * ·) (by omega)

/-- Odd-Step Surplus Transition Law (`orbitSurplus_odd_step`):
    If step `r` is odd (`F^r(n) % 2 = 1`) and `F^r(n) ≥ n`, then
    `orbitSurplus n (r + 1) = 3 * orbitSurplus n r + 2^r * (n + 1)`
    and `F^{r+1}(n) > n`. -/
theorem orbitSurplus_odd_step (n r : Nat)
    (hodd : iterateAccelerated n r % 2 = 1)
    (hge : iterateAccelerated n r ≥ n) :
    orbitSurplus n (r + 1) = 3 * orbitSurplus n r + 2 ^ r * (n + 1) ∧
    iterateAccelerated n (r + 1) > n := by
  have hsucc : iterateAccelerated n (r + 1) = acceleratedCollatz (iterateAccelerated n r) :=
    iterateAccelerated_succ_right n r
  have hm : stepParityMatches (iterateAccelerated n r) true := by
    dsimp [stepParityMatches]; exact hodd
  have hstep : 2 * acceleratedCollatz (iterateAccelerated n r) = 3 * iterateAccelerated n r + 1 := by
    have hs := acceleratedCollatz_step_eq (iterateAccelerated n r) true hm
    simpa using hs
  rw [← hsucc] at hstep
  have hgt_n : iterateAccelerated n (r + 1) > n := by omega
  refine ⟨?_, hgt_n⟩
  unfold orbitSurplus
  rw [Nat.pow_succ, Nat.mul_assoc (2 ^ r) 2 _,
      ← Nat.mul_assoc 3 (2 ^ r) _, Nat.mul_comm 3 (2 ^ r), Nat.mul_assoc (2 ^ r) 3 _,
      ← Nat.left_distrib]
  exact congrArg (2 ^ r * ·) (by omega)

/-- Exact Reservoir-Surplus Conservation Law (`reservoir_surplus_conservation_law`):
    For EVERY `n : Nat` and EVERY depth `r : Nat` along a non-descending prefix
    (`∀ i < r, iterateAccelerated n i ≥ n`), the Diophantine deficit reservoir `deficitReservoir n r`
    and the trajectory output `iterateAccelerated n r` satisfy the **exact identity**:
    `deficitReservoir n r + 2^r * n^{a_r} * iterateAccelerated n r = n * (3 * n + 1)^{a_r}`. -/
theorem reservoir_surplus_conservation_law (n r : Nat)
    (hge : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n) :
    let a := wordOnes (parityWordOf r n)
    deficitReservoir n r + 2 ^ r * n ^ a * iterateAccelerated n r =
      n * (3 * n + 1) ^ a := by
  dsimp
  induction r with
  | zero =>
    dsimp [deficitReservoir, parityWordOf, wordOnes, iterateAccelerated]
    omega
  | succ r ih =>
    have hge_r : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n :=
      fun i hi => hge i (by omega)
    have h_ih := ih hge_r
    have hn_r : iterateAccelerated n r ≥ n := hge r (by omega)
    have hsucc_w : parityWordOf (r + 1) n =
        parityWordOf r n ++ [iterateAccelerated n r % 2 == 1] :=
      parityWordOf_succ_eq_append r n
    have hsucc_it : iterateAccelerated n (r + 1) =
        acceleratedCollatz (iterateAccelerated n r) :=
      iterateAccelerated_succ_right n r
    by_cases hev : iterateAccelerated n r % 2 = 0
    · have hnot1 : ¬(iterateAccelerated n r % 2 = 1) := by omega
      have hb_false : (iterateAccelerated n r % 2 == 1) = false := by
        rw [beq_eq_false_iff_ne]; exact hnot1
      have hres_eq : deficitReservoir n (r + 1) = deficitReservoir n r := by
        change (if iterateAccelerated n r % 2 = 1 then
          (3 * n + 1) * deficitReservoir n r +
            n ^ wordOnes (parityWordOf r n) * orbitSurplus n r
        else deficitReservoir n r) = deficitReservoir n r
        rw [if_neg hnot1]
      have hones_eq : wordOnes (parityWordOf (r + 1) n) = wordOnes (parityWordOf r n) := by
        rw [hsucc_w, hb_false, wordOnes_append]
        dsimp [wordOnes]
      have hm : stepParityMatches (iterateAccelerated n r) false := by
        dsimp [stepParityMatches]; exact hev
      have hstep : 2 * acceleratedCollatz (iterateAccelerated n r) = iterateAccelerated n r := by
        have hs := acceleratedCollatz_step_eq (iterateAccelerated n r) false hm
        simpa using hs
      rw [hres_eq, hones_eq, hsucc_it]
      have hpow_mul : 2 ^ (r + 1) * n ^ wordOnes (parityWordOf r n) *
          acceleratedCollatz (iterateAccelerated n r) =
          2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r := by
        rw [Nat.pow_succ, Nat.mul_assoc (2 ^ r) 2 _,
            Nat.mul_comm 2 (n ^ wordOnes (parityWordOf r n)),
            ← Nat.mul_assoc (2 ^ r) (n ^ wordOnes (parityWordOf r n)) 2,
            Nat.mul_assoc (2 ^ r * n ^ wordOnes (parityWordOf r n)) 2 _,
            hstep]
      rw [hpow_mul]
      exact h_ih
    · have hodd : iterateAccelerated n r % 2 = 1 := by omega
      have hb_true : (iterateAccelerated n r % 2 == 1) = true := by
        rw [beq_iff_eq]; exact hodd
      have hres_eq : deficitReservoir n (r + 1) =
          (3 * n + 1) * deficitReservoir n r +
            n ^ wordOnes (parityWordOf r n) * orbitSurplus n r := by
        change (if iterateAccelerated n r % 2 = 1 then
          (3 * n + 1) * deficitReservoir n r +
            n ^ wordOnes (parityWordOf r n) * orbitSurplus n r
        else deficitReservoir n r) = _
        rw [if_pos hodd]
      have hones_eq : wordOnes (parityWordOf (r + 1) n) = wordOnes (parityWordOf r n) + 1 := by
        rw [hsucc_w, hb_true, wordOnes_append]
        dsimp [wordOnes]
      have hm : stepParityMatches (iterateAccelerated n r) true := by
        dsimp [stepParityMatches]; exact hodd
      have hstep : 2 * acceleratedCollatz (iterateAccelerated n r) =
          3 * iterateAccelerated n r + 1 := by
        have hs := acceleratedCollatz_step_eq (iterateAccelerated n r) true hm
        simpa using hs
      rw [hres_eq, hones_eq, hsucc_it]
      unfold orbitSurplus
      have hterm1 : n ^ wordOnes (parityWordOf r n) *
          (2 ^ r * (iterateAccelerated n r - n)) =
          (2 ^ r * n ^ wordOnes (parityWordOf r n)) *
            (iterateAccelerated n r - n) := by
        rw [← Nat.mul_assoc, Nat.mul_comm (n ^ wordOnes (parityWordOf r n)) (2 ^ r)]
      have hterm2 : 2 ^ (r + 1) * n ^ (wordOnes (parityWordOf r n) + 1) *
          acceleratedCollatz (iterateAccelerated n r) =
          (2 ^ r * n ^ wordOnes (parityWordOf r n)) *
            (n * (3 * iterateAccelerated n r + 1)) := by
        rw [Nat.pow_succ 2 r, Nat.pow_succ n (wordOnes (parityWordOf r n))]
        have h1 : 2 ^ r * 2 * (n ^ wordOnes (parityWordOf r n) * n) *
            acceleratedCollatz (iterateAccelerated n r) =
            (2 ^ r * n ^ wordOnes (parityWordOf r n)) *
              (n * (2 * acceleratedCollatz (iterateAccelerated n r))) := by
          rw [Nat.mul_assoc (2 ^ r) 2 _,
              Nat.mul_comm 2 (n ^ wordOnes (parityWordOf r n) * n),
              ← Nat.mul_assoc (2 ^ r) (n ^ wordOnes (parityWordOf r n) * n) 2,
              ← Nat.mul_assoc (2 ^ r) (n ^ wordOnes (parityWordOf r n)) n,
              Nat.mul_assoc (2 ^ r * n ^ wordOnes (parityWordOf r n) * n) 2 _,
              Nat.mul_assoc (2 ^ r * n ^ wordOnes (parityWordOf r n)) n _]
        rw [h1, hstep]
      have hsum_terms : (n ^ wordOnes (parityWordOf r n) *
          (2 ^ r * (iterateAccelerated n r - n))) +
          2 ^ (r + 1) * n ^ (wordOnes (parityWordOf r n) + 1) *
            acceleratedCollatz (iterateAccelerated n r) =
          (3 * n + 1) * (2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r) := by
        rw [hterm1, hterm2, ← Nat.left_distrib]
        have h_inner : (iterateAccelerated n r - n) + n * (3 * iterateAccelerated n r + 1) =
            (3 * n + 1) * iterateAccelerated n r := by
          rw [Nat.mul_add, Nat.mul_one, Nat.add_mul, Nat.one_mul]
          have hc : n * (3 * iterateAccelerated n r) = 3 * n * iterateAccelerated n r := by
            rw [← Nat.mul_assoc, Nat.mul_comm n 3, Nat.mul_assoc]
          omega
        rw [h_inner, ← Nat.mul_assoc (2 ^ r * n ^ wordOnes (parityWordOf r n)) (3 * n + 1) _,
            Nat.mul_comm (2 ^ r * n ^ wordOnes (parityWordOf r n)) (3 * n + 1),
            Nat.mul_assoc]
      rw [Nat.add_assoc, hsum_terms, ← Nat.mul_add, h_ih,
          Nat.pow_succ (3 * n + 1) (wordOnes (parityWordOf r n)),
          ← Nat.mul_assoc, Nat.mul_comm (3 * n + 1) n, Nat.mul_assoc,
          Nat.mul_comm (3 * n + 1) ((3 * n + 1) ^ wordOnes (parityWordOf r n))]

/-- Corollary (`reservoir_plus_surplus_eq_power_gap`):
    Whenever `∀ i ≤ r, iterateAccelerated n i ≥ n`, the reservoir `deficitReservoir n r`
    and the scaled surplus `n^{a_r} * orbitSurplus n r` partition the exact C10 power gap:
    `deficitReservoir n r + n^{a_r} * orbitSurplus n r + 2^r * n^{a_r + 1} = n * (3 * n + 1)^{a_r}`. -/
theorem reservoir_plus_surplus_eq_power_gap (n r : Nat)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let a := wordOnes (parityWordOf r n)
    deficitReservoir n r + n ^ a * orbitSurplus n r + 2 ^ r * n ^ (a + 1) =
      n * (3 * n + 1) ^ a := by
  dsimp
  have hcons := reservoir_surplus_conservation_law n r (fun i hi => hge i (by omega))
  have hn_r : iterateAccelerated n r ≥ n := hge r (by omega)
  unfold orbitSurplus
  let a := wordOnes (parityWordOf r n)
  have hexp : n ^ a * (2 ^ r * (iterateAccelerated n r - n)) + 2 ^ r * n ^ (a + 1) =
      2 ^ r * n ^ a * iterateAccelerated n r := by
    rw [Nat.pow_succ n a, ← Nat.mul_assoc (2 ^ r) (n ^ a) n,
        ← Nat.mul_assoc (n ^ a) (2 ^ r) (iterateAccelerated n r - n),
        Nat.mul_comm (n ^ a) (2 ^ r),
        ← Nat.left_distrib (2 ^ r * n ^ a) (iterateAccelerated n r - n) n,
        Nat.sub_add_cancel hn_r]
  rw [Nat.add_assoc, hexp]
  exact hcons

/-! ## 3. Symbolic-Dynamics Prefix Admissibility & Sharpened Power Bound -/

/-- Any integer `n > 1` that does not descend in its first 2 accelerated steps
    (`iterateAccelerated n 1 ≥ n` and `iterateAccelerated n 2 ≥ n`) must satisfy `n % 4 = 3`,
    have `wordOnes (parityWordOf 2 n) = 2`, and inject `deficitReservoir n 2 = n * (n + 1)`
    at depth 2. -/
theorem nondescent_depth2_forces_mod4_eq_3_and_reservoir (n : Nat)
    (hn1 : n > 1)
    (h1 : iterateAccelerated n 1 ≥ n)
    (h2 : iterateAccelerated n 2 ≥ n) :
    n % 4 = 3 ∧
    wordOnes (parityWordOf 2 n) = 2 ∧
    deficitReservoir n 2 = n * (n + 1) := by
  dsimp [iterateAccelerated] at h1 h2
  have hodd0 : n % 2 = 1 := by
    by_cases hev : n % 2 = 0
    · unfold acceleratedCollatz at h1
      rw [if_pos hev] at h1
      omega
    · omega
  have hacc1 : acceleratedCollatz n = (3 * n + 1) / 2 := by
    unfold acceleratedCollatz
    have hnot0 : ¬(n % 2 = 0) := by omega
    rw [if_neg hnot0]
  have hodd1 : (acceleratedCollatz n) % 2 = 1 := by
    by_cases hev1 : (acceleratedCollatz n) % 2 = 0
    · have hm1 : stepParityMatches (acceleratedCollatz n) false := by
        dsimp [stepParityMatches]; exact hev1
      have hs1 : 2 * acceleratedCollatz (acceleratedCollatz n) = acceleratedCollatz n := by
        have hs := acceleratedCollatz_step_eq (acceleratedCollatz n) false hm1
        simpa using hs
      omega
    · omega
  have hm4 : n % 4 = 3 := by
    rw [hacc1] at hodd1
    omega
  have hb0 : (n % 2 == 1) = true := by rw [beq_iff_eq]; exact hodd0
  have hb1 : (acceleratedCollatz n % 2 == 1) = true := by rw [beq_iff_eq]; exact hodd1
  have hones1 : wordOnes (parityWordOf 1 n) = 1 := by
    dsimp [parityWordOf, wordOnes]
    rw [hb0]
    rfl
  have hones2 : wordOnes (parityWordOf 2 n) = 2 := by
    dsimp [parityWordOf, wordOnes]
    rw [hb0, hb1]
    rfl
  have hres1 : deficitReservoir n 1 = 0 := by
    change (if iterateAccelerated n 0 % 2 = 1 then
      (3 * n + 1) * deficitReservoir n 0 +
        n ^ wordOnes (parityWordOf 0 n) * orbitSurplus n 0
    else deficitReservoir n 0) = 0
    have hodd0' : iterateAccelerated n 0 % 2 = 1 := hodd0
    rw [if_pos hodd0']
    dsimp [deficitReservoir, orbitSurplus, iterateAccelerated, parityWordOf, wordOnes]
    rw [Nat.sub_self, Nat.mul_zero]
  have hres2 : deficitReservoir n 2 = n * (n + 1) := by
    change (if iterateAccelerated n 1 % 2 = 1 then
      (3 * n + 1) * deficitReservoir n 1 +
        n ^ wordOnes (parityWordOf 1 n) * orbitSurplus n 1
    else deficitReservoir n 1) = n * (n + 1)
    have hodd1' : iterateAccelerated n 1 % 2 = 1 := hodd1
    rw [if_pos hodd1', hres1, hones1]
    dsimp [orbitSurplus, iterateAccelerated]
    rw [hacc1]
    have hsub : 2 * ((3 * n + 1) / 2 - n) = n + 1 := by omega
    rw [Nat.zero_add, Nat.pow_one, hsub]
  exact ⟨hm4, hones2, hres2⟩

/-- Reservoir Growth Lower Bound (`deficitReservoir_lower_bound_ge_two`):
    For any `n > 1` and any depth `r ≥ 2` such that `∀ i ≤ r, iterateAccelerated n i ≥ n`,
    `wordOnes (parityWordOf r n) ≥ 2` and
    `deficitReservoir n r ≥ n * (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2)`. -/
theorem deficitReservoir_lower_bound_ge_two (n r : Nat)
    (hn1 : n > 1) (hr2 : r ≥ 2)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let a := wordOnes (parityWordOf r n)
    a ≥ 2 ∧
    deficitReservoir n r ≥ n * (n + 1) * (3 * n + 1) ^ (a - 2) := by
  dsimp
  obtain ⟨k, rfl⟩ : ∃ k : Nat, r = 2 + k := ⟨r - 2, by omega⟩
  clear hr2
  induction k with
  | zero =>
    have h1 : iterateAccelerated n 1 ≥ n := hge 1 (by omega)
    have h2 : iterateAccelerated n 2 ≥ n := hge 2 (by omega)
    rcases nondescent_depth2_forces_mod4_eq_3_and_reservoir n hn1 h1 h2 with ⟨_, hones2, hres2⟩
    change wordOnes (parityWordOf 2 n) ≥ 2 ∧
      deficitReservoir n 2 ≥ n * (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf 2 n) - 2)
    rw [hones2, hres2]
    exact ⟨by omega, by simp⟩
  | succ k ih =>
    have hge_prev : ∀ i : Nat, i ≤ 2 + k → iterateAccelerated n i ≥ n :=
      fun i hi => hge i (by omega)
    rcases ih hge_prev with ⟨ha_ge2, hres_ih⟩
    have h2k_eq : 2 + (k + 1) = (2 + k) + 1 := by omega
    rw [h2k_eq]
    have hsucc_w : parityWordOf ((2 + k) + 1) n =
        parityWordOf (2 + k) n ++ [iterateAccelerated n (2 + k) % 2 == 1] :=
      parityWordOf_succ_eq_append (2 + k) n
    by_cases hev : iterateAccelerated n (2 + k) % 2 = 0
    · have hnot1 : ¬(iterateAccelerated n (2 + k) % 2 = 1) := by omega
      have hb_false : (iterateAccelerated n (2 + k) % 2 == 1) = false := by
        rw [beq_eq_false_iff_ne]; exact hnot1
      have hones_eq : wordOnes (parityWordOf ((2 + k) + 1) n) =
          wordOnes (parityWordOf (2 + k) n) := by
        rw [hsucc_w, hb_false, wordOnes_append]
        dsimp [wordOnes]
      have hres_eq : deficitReservoir n ((2 + k) + 1) = deficitReservoir n (2 + k) := by
        change (if iterateAccelerated n (2 + k) % 2 = 1 then
          (3 * n + 1) * deficitReservoir n (2 + k) +
            n ^ wordOnes (parityWordOf (2 + k) n) * orbitSurplus n (2 + k)
        else deficitReservoir n (2 + k)) = _
        rw [if_neg hnot1]
      rw [hones_eq, hres_eq]
      exact ⟨ha_ge2, hres_ih⟩
    · have hodd : iterateAccelerated n (2 + k) % 2 = 1 := by omega
      have hb_true : (iterateAccelerated n (2 + k) % 2 == 1) = true := by
        rw [beq_iff_eq]; exact hodd
      have hones_eq : wordOnes (parityWordOf ((2 + k) + 1) n) =
          wordOnes (parityWordOf (2 + k) n) + 1 := by
        rw [hsucc_w, hb_true, wordOnes_append]
        dsimp [wordOnes]
      have hres_eq : deficitReservoir n ((2 + k) + 1) =
          (3 * n + 1) * deficitReservoir n (2 + k) +
            n ^ wordOnes (parityWordOf (2 + k) n) * orbitSurplus n (2 + k) := by
        change (if iterateAccelerated n (2 + k) % 2 = 1 then
          (3 * n + 1) * deficitReservoir n (2 + k) +
            n ^ wordOnes (parityWordOf (2 + k) n) * orbitSurplus n (2 + k)
        else deficitReservoir n (2 + k)) = _
        rw [if_pos hodd]
      rw [hones_eq, hres_eq]
      refine ⟨by omega, ?_⟩
      have hsub_eq : wordOnes (parityWordOf (2 + k) n) + 1 - 2 =
          (wordOnes (parityWordOf (2 + k) n) - 2) + 1 := by omega
      rw [hsub_eq, Nat.pow_succ]
      have hmul_le : (3 * n + 1) * (n * (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf (2 + k) n) - 2)) ≤
          (3 * n + 1) * deficitReservoir n (2 + k) :=
        Nat.mul_le_mul_left (3 * n + 1) hres_ih
      have hcomm : n * (n + 1) * ((3 * n + 1) ^ (wordOnes (parityWordOf (2 + k) n) - 2) * (3 * n + 1)) =
          (3 * n + 1) * (n * (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf (2 + k) n) - 2)) := by
        rw [← Nat.mul_assoc (n * (n + 1)) _ (3 * n + 1),
            Nat.mul_comm _ (3 * n + 1)]
      rw [hcomm]
      omega

/-- Sharpened Non-Descent Power Bound (`sharpened_nondescent_power_bound`):
    For ANY `n > 1` and ANY depth `r ≥ 2` such that `∀ i ≤ r, iterateAccelerated n i ≥ n`,
    letting `a = wordOnes (parityWordOf r n)` (`a ≥ 2`), the reservoir conservation law forces:
    `2^r * n^a + (n + 1) * (3 * n + 1)^{a - 2} ≤ (3 * n + 1)^a`,
    or equivalently:
    `2^r * n^{a - 1} ≤ (9 * n + 5) * (3 * n + 1)^{a - 2}`. -/
theorem sharpened_nondescent_power_bound (n r : Nat)
    (hn1 : n > 1) (hr2 : r ≥ 2)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let a := wordOnes (parityWordOf r n)
    a ≥ 2 ∧
    2 ^ r * n ^ a + (n + 1) * (3 * n + 1) ^ (a - 2) ≤ (3 * n + 1) ^ a ∧
    2 ^ r * n ^ (a - 1) ≤ (9 * n + 5) * (3 * n + 1) ^ (a - 2) := by
  dsimp
  rcases deficitReservoir_lower_bound_ge_two n r hn1 hr2 hge with ⟨ha_ge2, hres_ge⟩
  have hgap := reservoir_plus_surplus_eq_power_gap n r hge
  dsimp at hgap
  have hle_sum : n * (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) +
      2 ^ r * n ^ (wordOnes (parityWordOf r n) + 1) ≤
      n * (3 * n + 1) ^ wordOnes (parityWordOf r n) := by omega
  have hlhs_factor : n * (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) +
      2 ^ r * n ^ (wordOnes (parityWordOf r n) + 1) =
      (2 ^ r * n ^ wordOnes (parityWordOf r n) +
        (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2)) * n := by
    rw [Nat.add_mul, Nat.pow_succ n (wordOnes (parityWordOf r n)),
        ← Nat.mul_assoc (2 ^ r) (n ^ wordOnes (parityWordOf r n)) n]
    have hc : n * (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) =
        (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) * n := by
      rw [Nat.mul_comm n (n + 1), Nat.mul_assoc (n + 1) n _,
          Nat.mul_comm n ((3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2)), ← Nat.mul_assoc]
    rw [hc]
    omega
  have hrhs_comm : n * (3 * n + 1) ^ wordOnes (parityWordOf r n) =
      (3 * n + 1) ^ wordOnes (parityWordOf r n) * n := Nat.mul_comm _ _
  rw [hlhs_factor, hrhs_comm] at hle_sum
  have hineq1 : 2 ^ r * n ^ wordOnes (parityWordOf r n) +
      (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) ≤
      (3 * n + 1) ^ wordOnes (parityWordOf r n) :=
    Nat.le_of_mul_le_mul_right hle_sum (by omega)
  have ha_split : wordOnes (parityWordOf r n) =
      (wordOnes (parityWordOf r n) - 2) + 2 := by omega
  have hpow3_split : (3 * n + 1) ^ wordOnes (parityWordOf r n) =
      ((3 * n + 1) ^ 2) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) := by
    conv => lhs; rw [ha_split]
    rw [Nat.pow_add, Nat.mul_comm]
  have hsq : (3 * n + 1) ^ 2 = n * (9 * n + 5) + (n + 1) := by
    rw [Nat.pow_succ, Nat.pow_succ, Nat.pow_zero, Nat.one_mul,
        Nat.mul_add, Nat.add_mul, Nat.mul_add]
    have h9 : 3 * n * (3 * n) = n * (9 * n) := by
      rw [← Nat.mul_assoc (3 * n) 3 n, Nat.mul_comm 3 n,
          Nat.mul_assoc n 3 3, Nat.mul_assoc n (3 * 3) n]
    omega
  have hrhs_expand : (3 * n + 1) ^ wordOnes (parityWordOf r n) =
      (n * (9 * n + 5)) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) +
        (n + 1) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) := by
    rw [hpow3_split, hsq, Nat.add_mul]
  have hineq2_mul_n : 2 ^ r * n ^ wordOnes (parityWordOf r n) ≤
      (n * (9 * n + 5)) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) := by
    omega
  have ha_split1 : wordOnes (parityWordOf r n) =
      (wordOnes (parityWordOf r n) - 1) + 1 := by omega
  have hna_split : 2 ^ r * n ^ wordOnes (parityWordOf r n) =
      (2 ^ r * n ^ (wordOnes (parityWordOf r n) - 1)) * n := by
    conv => lhs; rw [ha_split1, Nat.pow_succ]
    rw [← Nat.mul_assoc]
  have hrhs_n : (n * (9 * n + 5)) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) =
      ((9 * n + 5) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2)) * n := by
    rw [Nat.mul_comm n (9 * n + 5), Nat.mul_assoc (9 * n + 5) n _,
        Nat.mul_comm n ((3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2)), ← Nat.mul_assoc]
  rw [hna_split, hrhs_n] at hineq2_mul_n
  have hineq2 : 2 ^ r * n ^ (wordOnes (parityWordOf r n) - 1) ≤
      (9 * n + 5) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 2) :=
    Nat.le_of_mul_le_mul_right hineq2_mul_n (by omega)
  exact ⟨ha_ge2, hineq1, hineq2⟩

end CollatzProofClosure
end BBB17
