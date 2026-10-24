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

/-! ## 4. Normalized Cumulative Reservoir `Q_r`, Telescoping Increments, and Exponential Gap Decay

    In normalized coordinates `Q_r = qNum n r / qDen n r`, where:
    - `qNum n r = deficitReservoir n r = P_r(n)`,
    - `qDen n r = n * (3 * n + 1)^{a_r}`,
    the conservation law becomes:
    `Q_r + (2^r * n^{a_r - 1} * n_r) / (3 * n + 1)^{a_r} = 1`.
-/

/-- Numerator `P_r(n)` of the normalized cumulative reservoir `Q_r(n)`. -/
def qNum (n r : Nat) : Nat :=
  deficitReservoir n r

/-- Denominator `n * (3 * n + 1)^{a_r}` of the normalized cumulative reservoir `Q_r(n)`. -/
def qDen (n r : Nat) : Nat :=
  n * (3 * n + 1) ^ wordOnes (parityWordOf r n)

/-- Exact Even/Odd Update Equations for `Q_r` (`normalized_reservoir_exact_increment`):
    1. On an even step (`F^r(n) % 2 = 0`), `qNum n (r + 1) = qNum n r` and `qDen n (r + 1) = qDen n r`,
       so `qNum n (r + 1) * qDen n r = qNum n r * qDen n (r + 1)` (`Q_{r+1} = Q_r`).
    2. On an odd step (`F^r(n) % 2 = 1`), `qDen n (r + 1) = (3 * n + 1) * qDen n r`,
       `qNum n (r + 1) = (3 * n + 1) * qNum n r + n^{a_r} * orbitSurplus n r`, and cross-multiplying gives:
       `qNum n (r + 1) * qDen n r = qNum n r * qDen n (r + 1) + (n^{a_r} * orbitSurplus n r) * qDen n r`
       (`Q_{r+1} - Q_r = (n^{a_r} * Ω_r) / (n * (3n + 1)^{a_r + 1})`). -/
theorem normalized_reservoir_exact_increment (n r : Nat) :
    (iterateAccelerated n r % 2 = 0 →
      qNum n (r + 1) = qNum n r ∧
      qDen n (r + 1) = qDen n r ∧
      qNum n (r + 1) * qDen n r = qNum n r * qDen n (r + 1)) ∧
    (iterateAccelerated n r % 2 = 1 →
      qDen n (r + 1) = (3 * n + 1) * qDen n r ∧
      qNum n (r + 1) = (3 * n + 1) * qNum n r +
        n ^ wordOnes (parityWordOf r n) * orbitSurplus n r ∧
      qNum n (r + 1) * qDen n r =
        qNum n r * qDen n (r + 1) +
          (n ^ wordOnes (parityWordOf r n) * orbitSurplus n r) * qDen n r) := by
  have hsucc_w : parityWordOf (r + 1) n =
      parityWordOf r n ++ [iterateAccelerated n r % 2 == 1] :=
    parityWordOf_succ_eq_append r n
  constructor
  · intro hev
    have hnot1 : ¬(iterateAccelerated n r % 2 = 1) := by omega
    have hb_false : (iterateAccelerated n r % 2 == 1) = false := by
      rw [beq_eq_false_iff_ne]; exact hnot1
    have hnum : qNum n (r + 1) = qNum n r := by
      unfold qNum
      change (if iterateAccelerated n r % 2 = 1 then
        (3 * n + 1) * deficitReservoir n r +
          n ^ wordOnes (parityWordOf r n) * orbitSurplus n r
      else deficitReservoir n r) = deficitReservoir n r
      rw [if_neg hnot1]
    have hones : wordOnes (parityWordOf (r + 1) n) = wordOnes (parityWordOf r n) := by
      rw [hsucc_w, hb_false, wordOnes_append]; dsimp [wordOnes]
    have hden : qDen n (r + 1) = qDen n r := by
      unfold qDen; rw [hones]
    refine ⟨hnum, hden, ?_⟩
    rw [hnum, hden]
  · intro hodd
    have hb_true : (iterateAccelerated n r % 2 == 1) = true := by
      rw [beq_iff_eq]; exact hodd
    have hones : wordOnes (parityWordOf (r + 1) n) = wordOnes (parityWordOf r n) + 1 := by
      rw [hsucc_w, hb_true, wordOnes_append]; dsimp [wordOnes]
    have hden : qDen n (r + 1) = (3 * n + 1) * qDen n r := by
      unfold qDen
      rw [hones, Nat.pow_succ, ← Nat.mul_assoc,
          Nat.mul_comm (n * (3 * n + 1) ^ wordOnes (parityWordOf r n)) (3 * n + 1)]
    have hnum : qNum n (r + 1) = (3 * n + 1) * qNum n r +
        n ^ wordOnes (parityWordOf r n) * orbitSurplus n r := by
      unfold qNum
      change (if iterateAccelerated n r % 2 = 1 then
        (3 * n + 1) * deficitReservoir n r +
          n ^ wordOnes (parityWordOf r n) * orbitSurplus n r
      else deficitReservoir n r) = _
      rw [if_pos hodd]
    refine ⟨hden, hnum, ?_⟩
    rw [hnum, hden, Nat.add_mul]
    have hc : (3 * n + 1) * qNum n r * qDen n r =
        qNum n r * ((3 * n + 1) * qDen n r) := by
      rw [Nat.mul_comm (3 * n + 1) (qNum n r), Nat.mul_assoc]
    rw [hc]

/-- Monotonicity and Strict Upper Bound `0 ≤ Q_r < 1` (`normalized_reservoir_monotone_bounded`):
    For every `n > 0` and every depth `r` along a non-descending prefix
    (`∀ i ≤ r, iterateAccelerated n i ≥ n`):
    1. `qNum n r < qDen n r` (`Q_r < 1`),
    2. `qDen n r - qNum n r = 2^r * n^{a_r} * iterateAccelerated n r`
       (`1 - Q_r = (2^r * n^{a_r - 1} * n_r) / (3n + 1)^{a_r}`),
    3. `qNum n r * qDen n (r + 1) ≤ qNum n (r + 1) * qDen n r` (`Q_r ≤ Q_{r+1}`). -/
theorem normalized_reservoir_monotone_bounded (n r : Nat)
    (hn : n > 0)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let a := wordOnes (parityWordOf r n)
    qNum n r < qDen n r ∧
    qDen n r - qNum n r = 2 ^ r * n ^ a * iterateAccelerated n r ∧
    qNum n r * qDen n (r + 1) ≤ qNum n (r + 1) * qDen n r := by
  dsimp
  have hcons := reservoir_surplus_conservation_law n r (fun i hi => hge i (by omega))
  dsimp at hcons
  unfold qNum qDen
  have hn_r : iterateAccelerated n r ≥ n := hge r (by omega)
  have hpos_pow2 : 2 ^ r > 0 := pow_pos_of_pos 2 r (by decide)
  have hpos_pown : n ^ wordOnes (parityWordOf r n) > 0 :=
    pow_pos_of_pos n (wordOnes (parityWordOf r n)) hn
  have hpos_nr : iterateAccelerated n r > 0 := by omega
  have hpos_rem : 2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r > 0 :=
    Nat.mul_pos (Nat.mul_pos hpos_pow2 hpos_pown) hpos_nr
  have hlt : deficitReservoir n r < n * (3 * n + 1) ^ wordOnes (parityWordOf r n) := by omega
  have hsub : n * (3 * n + 1) ^ wordOnes (parityWordOf r n) - deficitReservoir n r =
      2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r := by omega
  refine ⟨hlt, hsub, ?_⟩
  rcases normalized_reservoir_exact_increment n r with ⟨hev_case, hodd_case⟩
  by_cases hev : iterateAccelerated n r % 2 = 0
  · rcases hev_case hev with ⟨_, _, heq⟩
    unfold qNum qDen at heq
    omega
  · have hodd : iterateAccelerated n r % 2 = 1 := by omega
    rcases hodd_case hodd with ⟨_, _, heq⟩
    unfold qNum qDen at heq
    omega

/-- Cross-multiplied one-step increment numerator at step `i`:
    `qNum n (i + 1) * qDen n i - qNum n i * qDen n (i + 1)`. -/
def crossStepIncrement (n i : Nat) : Nat :=
  if iterateAccelerated n i % 2 = 1 then
    (n ^ wordOnes (parityWordOf i n) * orbitSurplus n i) * qDen n i
  else
    0

/-- Exact Telescoping Step Identity (`normalized_reservoir_telescoping`):
    1. `qNum n 0 = 0`,
    2. At every step `i`, `qNum n (i + 1) * qDen n i = qNum n i * qDen n (i + 1) + crossStepIncrement n i`,
    3. Across any depth `r`, `qNum n r` is generated from `0` by the exact finite folding
       of the odd-step increments `n^{a_i} * orbitSurplus n i`. -/
theorem normalized_reservoir_telescoping (n i : Nat) :
    qNum n 0 = 0 ∧
    qNum n (i + 1) * qDen n i =
      qNum n i * qDen n (i + 1) + crossStepIncrement n i := by
  refine ⟨rfl, ?_⟩
  rcases normalized_reservoir_exact_increment n i with ⟨hev_case, hodd_case⟩
  unfold crossStepIncrement
  by_cases hev : iterateAccelerated n i % 2 = 0
  · have hnot1 : ¬(iterateAccelerated n i % 2 = 1) := by omega
    rw [if_neg hnot1, Nat.add_zero]
    exact (hev_case hev).2.2
  · have hodd : iterateAccelerated n i % 2 = 1 := by omega
    rw [if_pos hodd]
    exact (hodd_case hodd).2.2

/-- Exact Reservoir Threshold Descent Criterion (`reservoir_threshold_iff_descent`):
    Along any trajectory of `n > 0` where all prior steps `i < r` satisfy `F^i(n) ≥ n`,
    strict descent `F^r(n) < n` occurs at depth `r` IF AND ONLY IF the normalized
    reservoir `Q_r` plus the power ratio `(2^r * n^{a_r}) / (3n + 1)^{a_r}` strictly exceeds `1`:
    `qNum n r + 2^r * n^{a_r + 1} > qDen n r`. -/
theorem reservoir_threshold_iff_descent (n r : Nat)
    (hn : n > 0)
    (hge : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n) :
    let a := wordOnes (parityWordOf r n)
    iterateAccelerated n r < n ↔
      qNum n r + 2 ^ r * n ^ (a + 1) > qDen n r := by
  dsimp
  have hcons := reservoir_surplus_conservation_law n r hge
  dsimp at hcons
  unfold qNum qDen
  have hpow_pos : 2 ^ r * n ^ wordOnes (parityWordOf r n) > 0 :=
    Nat.mul_pos (pow_pos_of_pos 2 r (by decide))
      (pow_pos_of_pos n (wordOnes (parityWordOf r n)) hn)
  have hna1 : 2 ^ r * n ^ (wordOnes (parityWordOf r n) + 1) =
      (2 ^ r * n ^ wordOnes (parityWordOf r n)) * n := by
    rw [Nat.pow_succ n (wordOnes (parityWordOf r n)), ← Nat.mul_assoc]
  rw [hna1, ← hcons]
  constructor
  · intro hlt
    have hmul_lt : (2 ^ r * n ^ wordOnes (parityWordOf r n)) * iterateAccelerated n r <
        (2 ^ r * n ^ wordOnes (parityWordOf r n)) * n :=
      Nat.mul_lt_mul_of_pos_left hlt hpow_pos
    omega
  · intro hgt
    have hmul_lt : (2 ^ r * n ^ wordOnes (parityWordOf r n)) * iterateAccelerated n r <
        (2 ^ r * n ^ wordOnes (parityWordOf r n)) * n := by
      omega
    by_cases hge_n : iterateAccelerated n r ≥ n
    · have hmul_ge : (2 ^ r * n ^ wordOnes (parityWordOf r n)) * n ≤
          (2 ^ r * n ^ wordOnes (parityWordOf r n)) * iterateAccelerated n r :=
        Nat.mul_le_mul_left (2 ^ r * n ^ wordOnes (parityWordOf r n)) hge_n
      omega
    · omega

/-- Exact Strict Odd-Step Contraction Identity (`strict_odd_excursion_step_bound`):
    For any odd `n` (`n % 2 = 1`) and any odd step `i` (`F^i(n) % 2 = 1`) where `F^i(n) > n`:
    1. `F^i(n) ≥ n + 2` (since both `n` and `F^i(n)` are odd),
    2. `(n + 2) * (3 * F^i(n) + 1) + (F^i(n) - (n + 2)) = (3 * n + 7) * F^i(n)`, and
    3. `(n + 2) * (2 * F^{i+1}(n)) ≤ (3 * n + 7) * F^i(n)`. -/
theorem strict_odd_excursion_step_bound (n i : Nat)
    (hn_odd : n % 2 = 1)
    (hi_odd : iterateAccelerated n i % 2 = 1)
    (hgt : iterateAccelerated n i > n) :
    iterateAccelerated n i ≥ n + 2 ∧
    (n + 2) * (3 * iterateAccelerated n i + 1) +
      (iterateAccelerated n i - (n + 2)) =
      (3 * n + 7) * iterateAccelerated n i ∧
    (n + 2) * (2 * iterateAccelerated n (i + 1)) ≤
      (3 * n + 7) * iterateAccelerated n i := by
  have hge2 : iterateAccelerated n i ≥ n + 2 := by omega
  have hid : (n + 2) * (3 * iterateAccelerated n i + 1) +
      (iterateAccelerated n i - (n + 2)) =
      (3 * n + 7) * iterateAccelerated n i := by
    rw [Nat.add_mul, Nat.mul_add, Nat.mul_one, Nat.add_mul]
    have hc : n * (3 * iterateAccelerated n i) = 3 * n * iterateAccelerated n i := by
      rw [← Nat.mul_assoc, Nat.mul_comm n 3, Nat.mul_assoc]
    omega
  have hsucc : iterateAccelerated n (i + 1) = acceleratedCollatz (iterateAccelerated n i) :=
    iterateAccelerated_succ_right n i
  have hm : stepParityMatches (iterateAccelerated n i) true := by
    dsimp [stepParityMatches]; exact hi_odd
  have hstep : 2 * acceleratedCollatz (iterateAccelerated n i) =
      3 * iterateAccelerated n i + 1 := by
    have hs := acceleratedCollatz_step_eq (iterateAccelerated n i) true hm
    simpa using hs
  rw [← hsucc] at hstep
  refine ⟨hge2, hid, ?_⟩
  rw [hstep]
  omega

/-- Strict Excursion Power Law & Exponential Reservoir Gap Decay (`infinite_nondescent_reservoir_obstruction`):
    For any `n > 1` with `n % 2 = 1` and any depth `r ≥ 1` along a strictly non-returning
    non-descending prefix (`∀ i, 1 ≤ i → i < r → iterateAccelerated n i > n`):
    1. `wordOnes (parityWordOf r n) ≥ 1`,
    2. `2^r * (n + 2)^{a_r - 1} * iterateAccelerated n r ≤ (3 * n + 1) * (3 * n + 7)^{a_r - 1}`,
    3. `(n + 2)^{a_r - 1} * (qDen n r - qNum n r) ≤ n^{a_r} * (3 * n + 1) * (3 * n + 7)^{a_r - 1}`
       (i.e. `1 - Q_r ≤ (1 - 2 / ((n + 2)(3n + 1)))^{a_r - 1}`, proving that `1 - Q_r` decays
       exponentially toward `0` as `a_r → ∞` along any non-periodic non-descending orbit!). -/
theorem infinite_nondescent_reservoir_obstruction (n r : Nat)
    (_hn1 : n > 1) (hr1 : r ≥ 1) (hn_odd : n % 2 = 1)
    (hstrict : ∀ i : Nat, 1 ≤ i → i < r → iterateAccelerated n i > n) :
    let a := wordOnes (parityWordOf r n)
    a ≥ 1 ∧
    2 ^ r * (n + 2) ^ (a - 1) * iterateAccelerated n r ≤
      (3 * n + 1) * (3 * n + 7) ^ (a - 1) ∧
    (n + 2) ^ (a - 1) * (qDen n r - qNum n r) ≤
      n ^ a * ((3 * n + 1) * (3 * n + 7) ^ (a - 1)) := by
  dsimp
  obtain ⟨k, rfl⟩ : ∃ k : Nat, r = 1 + k := ⟨r - 1, by omega⟩
  clear hr1
  have hpow_ineq : ∀ k : Nat,
      (∀ i : Nat, 1 ≤ i → i < 1 + k → iterateAccelerated n i > n) →
      let a := wordOnes (parityWordOf (1 + k) n)
      a ≥ 1 ∧
      2 ^ (1 + k) * (n + 2) ^ (a - 1) * iterateAccelerated n (1 + k) ≤
        (3 * n + 1) * (3 * n + 7) ^ (a - 1) := by
    intro k
    induction k with
    | zero =>
      intro _
      dsimp [parityWordOf, wordOnes, iterateAccelerated]
      have hb0 : (n % 2 == 1) = true := by rw [beq_iff_eq]; exact hn_odd
      rw [hb0]
      dsimp [wordOnes]
      have hm0 : stepParityMatches n true := by dsimp [stepParityMatches]; exact hn_odd
      have hs0 : 2 * acceleratedCollatz n = 3 * n + 1 := by
        have hs := acceleratedCollatz_step_eq n true hm0
        simpa using hs
      exact ⟨by omega, by omega⟩
    | succ k ih =>
      intro hstr_succ
      have hstr_k : ∀ i : Nat, 1 ≤ i → i < 1 + k → iterateAccelerated n i > n :=
        fun i hi1 hik => hstr_succ i hi1 (by omega)
      rcases ih hstr_k with ⟨ha_ge1, h_ih⟩
      have h1k_eq : 1 + (k + 1) = (1 + k) + 1 := by omega
      rw [h1k_eq]
      have hsucc_w : parityWordOf ((1 + k) + 1) n =
          parityWordOf (1 + k) n ++ [iterateAccelerated n (1 + k) % 2 == 1] :=
        parityWordOf_succ_eq_append (1 + k) n
      have hsucc_it : iterateAccelerated n ((1 + k) + 1) =
          acceleratedCollatz (iterateAccelerated n (1 + k)) :=
        iterateAccelerated_succ_right n (1 + k)
      by_cases hev : iterateAccelerated n (1 + k) % 2 = 0
      · have hnot1 : ¬(iterateAccelerated n (1 + k) % 2 = 1) := by omega
        have hb_false : (iterateAccelerated n (1 + k) % 2 == 1) = false := by
          rw [beq_eq_false_iff_ne]; exact hnot1
        have hones_eq : wordOnes (parityWordOf ((1 + k) + 1) n) =
            wordOnes (parityWordOf (1 + k) n) := by
          rw [hsucc_w, hb_false, wordOnes_append]; dsimp [wordOnes]
        have hm : stepParityMatches (iterateAccelerated n (1 + k)) false := by
          dsimp [stepParityMatches]; exact hev
        have hstep : 2 * acceleratedCollatz (iterateAccelerated n (1 + k)) =
            iterateAccelerated n (1 + k) := by
          have hs := acceleratedCollatz_step_eq (iterateAccelerated n (1 + k)) false hm
          simpa using hs
        rw [hones_eq, hsucc_it]
        refine ⟨ha_ge1, ?_⟩
        have hlhs : 2 ^ ((1 + k) + 1) *
            (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) *
            acceleratedCollatz (iterateAccelerated n (1 + k)) =
            2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) *
              iterateAccelerated n (1 + k) := by
          rw [Nat.pow_succ, Nat.mul_assoc (2 ^ (1 + k)) 2 _,
              Nat.mul_comm 2 ((n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1)),
              ← Nat.mul_assoc (2 ^ (1 + k)) _ 2,
              Nat.mul_assoc (2 ^ (1 + k) * _) 2 _, hstep]
        rw [hlhs]
        exact h_ih
      · have hodd : iterateAccelerated n (1 + k) % 2 = 1 := by omega
        have hb_true : (iterateAccelerated n (1 + k) % 2 == 1) = true := by
          rw [beq_iff_eq]; exact hodd
        have hones_eq : wordOnes (parityWordOf ((1 + k) + 1) n) =
            wordOnes (parityWordOf (1 + k) n) + 1 := by
          rw [hsucc_w, hb_true, wordOnes_append]; dsimp [wordOnes]
        have hgt_1k : iterateAccelerated n (1 + k) > n :=
          hstr_succ (1 + k) (by omega) (by omega)
        have hstep_bound := (strict_odd_excursion_step_bound n (1 + k) hn_odd hodd hgt_1k).2.2
        have hsucc_it' : iterateAccelerated n (1 + k + 1) =
            acceleratedCollatz (iterateAccelerated n (1 + k)) := hsucc_it
        rw [hsucc_it'] at hstep_bound
        rw [hones_eq, hsucc_it]
        refine ⟨by omega, ?_⟩
        have hsub_eq : wordOnes (parityWordOf (1 + k) n) + 1 - 1 =
            (wordOnes (parityWordOf (1 + k) n) - 1) + 1 := by omega
        rw [hsub_eq, Nat.pow_succ (n + 2) _, Nat.pow_succ (3 * n + 7) _]
        have hlhs_eq : 2 ^ (1 + k + 1) *
            ((n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) * (n + 2)) *
            acceleratedCollatz (iterateAccelerated n (1 + k)) =
            (2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1)) *
              ((n + 2) * (2 * acceleratedCollatz (iterateAccelerated n (1 + k)))) := by
          rw [Nat.pow_succ 2 (1 + k),
              Nat.mul_assoc (2 ^ (1 + k)) 2 _,
              Nat.mul_comm 2 ((n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) * (n + 2)),
              ← Nat.mul_assoc (2 ^ (1 + k)) _ 2,
              ← Nat.mul_assoc (2 ^ (1 + k)) _ (n + 2),
              Nat.mul_assoc (2 ^ (1 + k) * _ * (n + 2)) 2 _,
              Nat.mul_assoc (2 ^ (1 + k) * _) (n + 2) _]
        have hle1 : (2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1)) *
            ((n + 2) * (2 * acceleratedCollatz (iterateAccelerated n (1 + k)))) ≤
            (2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1)) *
              ((3 * n + 7) * iterateAccelerated n (1 + k)) :=
          Nat.mul_le_mul_left _ hstep_bound
        have hmid_eq : (2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1)) *
            ((3 * n + 7) * iterateAccelerated n (1 + k)) =
            (2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) *
              iterateAccelerated n (1 + k)) * (3 * n + 7) := by
          rw [← Nat.mul_assoc, Nat.mul_comm _ (3 * n + 7),
              Nat.mul_assoc (3 * n + 7) _ _, Nat.mul_comm (3 * n + 7) _]
        have hle2 : (2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) *
            iterateAccelerated n (1 + k)) * (3 * n + 7) ≤
            ((3 * n + 1) * (3 * n + 7) ^ (wordOnes (parityWordOf (1 + k) n) - 1)) *
              (3 * n + 7) :=
          Nat.mul_le_mul_right (3 * n + 7) h_ih
        rw [hlhs_eq, ← Nat.mul_assoc (3 * n + 1) _ (3 * n + 7)]
        exact Nat.le_trans hle1 (by rw [hmid_eq]; exact hle2)
  rcases hpow_ineq k hstrict with ⟨ha_ge1, hbound⟩
  have hge_all : ∀ i : Nat, i < 1 + k → iterateAccelerated n i ≥ n := by
    intro i hi
    cases i with
    | zero => dsimp [iterateAccelerated]; omega
    | succ i' =>
      have hgt := hstrict (i' + 1) (by omega) hi
      omega
  have hcons := reservoir_surplus_conservation_law n (1 + k) hge_all
  dsimp at hcons
  have hsub : qDen n (1 + k) - qNum n (1 + k) =
      2 ^ (1 + k) * n ^ wordOnes (parityWordOf (1 + k) n) * iterateAccelerated n (1 + k) := by
    unfold qDen qNum
    omega
  refine ⟨ha_ge1, hbound, ?_⟩
  rw [hsub]
  have hlhs_comm : (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) *
      (2 ^ (1 + k) * n ^ wordOnes (parityWordOf (1 + k) n) * iterateAccelerated n (1 + k)) =
      n ^ wordOnes (parityWordOf (1 + k) n) *
        (2 ^ (1 + k) * (n + 2) ^ (wordOnes (parityWordOf (1 + k) n) - 1) *
          iterateAccelerated n (1 + k)) := by
    rw [← Nat.mul_assoc ((n + 2) ^ _) (2 ^ (1 + k) * n ^ _) _,
        ← Nat.mul_assoc ((n + 2) ^ _) (2 ^ (1 + k)) (n ^ _),
        Nat.mul_comm ((n + 2) ^ _) (2 ^ (1 + k)),
        Nat.mul_comm (2 ^ (1 + k) * (n + 2) ^ _) (n ^ _),
        Nat.mul_assoc (n ^ _) (2 ^ (1 + k) * (n + 2) ^ _) _]
  rw [hlhs_comm]
  exact Nat.mul_le_mul_left (n ^ wordOnes (parityWordOf (1 + k) n)) hbound

/-! ## 5. Unbounded Odd Operations (`a_r → ∞`), Reservoir-Offset Duality, and Arithmetic Compatibility

    Addresses the three unified proof targets:
    1. **Infinite-Path Exclusion & Unbounded Odd Operations (`unbounded_odd_steps_of_never_descending`)**:
       A never-descending trajectory of `n > 0` cannot have only finitely many odd steps:
       from any depth `r`, at most `F^r(n)` consecutive even steps can occur before the next
       odd step, forcing `∀ M : Nat, ∃ R : Nat, wordOnes (parityWordOf R n) ≥ M`.
    2. **Reservoir-Offset Duality & 2-Adic Divisibility Lower Bounds
       (`reservoir_offset_duality_identity`, `reservoir_complement_divisibility_and_lower_bound`,
        `arithmetic_compatibility_obstruction`)**:
       Proves the exact duality identity
       `deficitReservoir n r + n^{a_r} * B_r + n * (3n)^{a_r} = n * (3n + 1)^{a_r}`,
       the exact 2-adic congruence `qNum n r % 2^r = qDen n r % 2^r`,
       the exact divisibility `(qDen n r - qNum n r) % (2^r * n^{a_r}) = 0`,
       and the resulting Arithmetic Compatibility Obstruction on `1 - Q_r`.
    3. **Sharpened Cycle Exclusion (`periodic_orbit_strict_interior_excursion_bound`)**:
       Any cycle of period `r ≥ 1` with strict minimum element `n > 1`
       (`∀ 1 ≤ i < r, F^i(n) > n` and `F^r(n) = n`) must satisfy both `3^{a_r} < 2^r`
       and `2^r * n * (n + 2)^{a_r - 1} ≤ (3n + 1) * (3n + 7)^{a_r - 1}`.
-/

/-- If `k` consecutive steps starting from `m` are even, then `2^k * F^k(m) = m`. -/
theorem even_run_pow_two_mul_eq (k : Nat) :
    ∀ m : Nat, (∀ j : Nat, j < k → iterateAccelerated m j % 2 = 0) →
      2 ^ k * iterateAccelerated m k = m := by
  induction k with
  | zero =>
    intro m _
    dsimp [iterateAccelerated]
    omega
  | succ k ih =>
    intro m hev_all
    have hev_k : ∀ j : Nat, j < k → iterateAccelerated m j % 2 = 0 :=
      fun j hj => hev_all j (by omega)
    have h_ih := ih m hev_k
    have hev_last : iterateAccelerated m k % 2 = 0 := hev_all k (by omega)
    have hsucc : iterateAccelerated m (k + 1) = acceleratedCollatz (iterateAccelerated m k) :=
      iterateAccelerated_succ_right m k
    have hm : stepParityMatches (iterateAccelerated m k) false := by
      dsimp [stepParityMatches]; exact hev_last
    have hstep : 2 * acceleratedCollatz (iterateAccelerated m k) = iterateAccelerated m k := by
      have hs := acceleratedCollatz_step_eq (iterateAccelerated m k) false hm
      simpa using hs
    rw [hsucc, Nat.pow_succ, Nat.mul_assoc (2 ^ k) 2 _, hstep, h_ih]

/-- Elementary exponential growth `2^k > k` for all `k : Nat`. -/
theorem two_pow_gt_self (k : Nat) : 2 ^ k > k := by
  induction k with
  | zero => decide
  | succ k ih =>
    rw [Nat.pow_succ]
    omega

/-- Semigroup property of `iterateAccelerated`: `F^{r + j}(n) = F^j(F^r(n))`. -/
theorem iterateAccelerated_add (n r j : Nat) :
    iterateAccelerated n (r + j) = iterateAccelerated (iterateAccelerated n r) j := by
  induction r generalizing n with
  | zero =>
    rw [Nat.zero_add]
    rfl
  | succ r ih =>
    rw [Nat.succ_add]
    dsimp [iterateAccelerated]
    exact ih (acceleratedCollatz n)

/-- Along any never-descending trajectory of `n > 0` (`∀ i, F^i(n) ≥ n`), starting from any
    depth `r`, there cannot be `F^r(n)` consecutive even steps; hence there exists `j < F^r(n)`
    such that `F^{r + j}(n)` is odd (`iterateAccelerated n (r + j) % 2 = 1`). -/
theorem never_descending_always_has_next_odd_step (n r : Nat)
    (hn : n > 0)
    (hnever_desc : ∀ i : Nat, iterateAccelerated n i ≥ n) :
    ∃ j : Nat, j < iterateAccelerated n r ∧
      iterateAccelerated n (r + j) % 2 = 1 := by
  apply Classical.byContradiction
  intro hno
  have hall_even : ∀ j : Nat, j < iterateAccelerated n r →
      iterateAccelerated (iterateAccelerated n r) j % 2 = 0 := by
    intro j hj
    have hadd : iterateAccelerated (iterateAccelerated n r) j =
        iterateAccelerated n (r + j) :=
      (iterateAccelerated_add n r j).symm
    rw [hadd]
    by_cases hev : iterateAccelerated n (r + j) % 2 = 0
    · exact hev
    · exfalso
      exact hno ⟨j, hj, by omega⟩
  let m := iterateAccelerated n r
  have heq := even_run_pow_two_mul_eq m m hall_even
  have hadd_m : iterateAccelerated m m = iterateAccelerated n (r + m) :=
    (iterateAccelerated_add n r m).symm
  rw [hadd_m] at heq
  have hge_n : iterateAccelerated n (r + m) ≥ n := hnever_desc (r + m)
  have hge_1 : iterateAccelerated n (r + m) ≥ 1 := by omega
  have hpow_gt : 2 ^ m > m := two_pow_gt_self m
  have hmul_ge : 2 ^ m * 1 ≤ 2 ^ m * iterateAccelerated n (r + m) :=
    Nat.mul_le_mul_left (2 ^ m) hge_1
  omega

/-- Monotonicity of `wordOnes (parityWordOf r n)` with respect to `r`. -/
theorem wordOnes_parityWordOf_mono (n r k : Nat) :
    wordOnes (parityWordOf r n) ≤ wordOnes (parityWordOf (r + k) n) := by
  rw [parityWordOf_add, wordOnes_append]
  omega

/-- Strict increase of `wordOnes (parityWordOf r n)` across an odd step at `r + j`. -/
theorem wordOnes_parityWordOf_strict_step (n r j : Nat)
    (hodd : iterateAccelerated n (r + j) % 2 = 1) :
    wordOnes (parityWordOf (r + j + 1) n) ≥ wordOnes (parityWordOf r n) + 1 := by
  have hmono := wordOnes_parityWordOf_mono n r j
  have hsucc := parityWordOf_succ_eq_append (r + j) n
  have hb : (iterateAccelerated n (r + j) % 2 == 1) = true := by
    rw [beq_iff_eq]; exact hodd
  rw [hsucc, hb, wordOnes_append]
  dsimp [wordOnes]
  omega

/-- Unbounded Odd Operations Theorem (`unbounded_odd_steps_of_never_descending`):
    For any hypothetical never-descending positive integer `n > 0`
    (`∀ i, iterateAccelerated n i ≥ n`), the odd-step count `a_r = wordOnes (parityWordOf r n)`
    grows without bound (`∀ M : Nat, ∃ r : Nat, wordOnes (parityWordOf r n) ≥ M`). -/
theorem unbounded_odd_steps_of_never_descending (n : Nat)
    (hn : n > 0)
    (hnever_desc : ∀ i : Nat, iterateAccelerated n i ≥ n) :
    ∀ M : Nat, ∃ r : Nat, wordOnes (parityWordOf r n) ≥ M := by
  intro M
  induction M with
  | zero => exact ⟨0, by omega⟩
  | succ M ih =>
    rcases ih with ⟨r, hr⟩
    rcases never_descending_always_has_next_odd_step n r hn hnever_desc with ⟨j, _, hodd⟩
    refine ⟨r + j + 1, ?_⟩
    have hinc := wordOnes_parityWordOf_strict_step n r j hodd
    omega

/-- Exact Reservoir-Offset Duality Identity (`reservoir_offset_duality_identity`):
    Along any non-descending prefix (`∀ i < r, iterateAccelerated n i ≥ n`),
    letting `w = parityWordOf r n` and `a = wordOnes w`:
    1. `qDen n r - qNum n r = n * (3 * n)^a + n^a * wordB w`, and
    2. `deficitReservoir n r + n^a * wordB w + n * (3 * n)^a = n * (3 * n + 1)^a`. -/
theorem reservoir_offset_duality_identity (n r : Nat)
    (hge : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n) :
    let w := parityWordOf r n
    let a := wordOnes w
    qDen n r - qNum n r = n * (3 * n) ^ a + n ^ a * wordB w ∧
    deficitReservoir n r + n ^ a * wordB w + n * (3 * n) ^ a =
      n * (3 * n + 1) ^ a := by
  dsimp
  have hcons := reservoir_surplus_conservation_law n r hge
  dsimp at hcons
  have hv := parityWordOf_valid r n
  have hid := parityWord_affine_identity (parityWordOf r n) n hv
  rw [applyParityWord_parityWordOf, wordD_eq_pow_two_length, parityWordOf_length,
      wordA_eq_pow_three_wordOnes] at hid
  have hmul_na : 2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r =
      n ^ wordOnes (parityWordOf r n) * (2 ^ r * iterateAccelerated n r) := by
    rw [Nat.mul_comm (2 ^ r) (n ^ _), Nat.mul_assoc]
  have hrhs_aff : n ^ wordOnes (parityWordOf r n) *
      (3 ^ wordOnes (parityWordOf r n) * n + wordB (parityWordOf r n)) =
      n * (3 * n) ^ wordOnes (parityWordOf r n) +
        n ^ wordOnes (parityWordOf r n) * wordB (parityWordOf r n) := by
    rw [Nat.mul_add, ← Nat.mul_assoc (n ^ _) (3 ^ _) n,
        Nat.mul_comm (n ^ _) (3 ^ _),
        ← mul_pow_eq 3 n (wordOnes (parityWordOf r n)),
        Nat.mul_comm ((3 * n) ^ _) n]
  have hgap_eq : 2 ^ r * n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r =
      n * (3 * n) ^ wordOnes (parityWordOf r n) +
        n ^ wordOnes (parityWordOf r n) * wordB (parityWordOf r n) := by
    rw [hmul_na, hid, hrhs_aff]
  unfold qDen qNum
  constructor
  · omega
  · omega

/-- Exact 2-Adic Congruence and Divisibility Lower Bound on `1 - Q_r`
    (`reservoir_complement_divisibility_and_lower_bound`):
    Along any non-descending prefix (`∀ i ≤ r, iterateAccelerated n i ≥ n`):
    1. `(qDen n r - qNum n r) % (2^r * n^{a_r}) = 0`,
    2. `(qDen n r - qNum n r) % 2^r = 0`,
    3. `qDen n r - qNum n r ≥ 2^r * n^{a_r + 1}`, and
    4. `qDen n r - qNum n r ≥ n * (3 * n)^{a_r} + n^{a_r} * wordB (parityWordOf r n)`. -/
theorem reservoir_complement_divisibility_and_lower_bound (n r : Nat)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let w := parityWordOf r n
    let a := wordOnes w
    (qDen n r - qNum n r) % (2 ^ r * n ^ a) = 0 ∧
    (qDen n r - qNum n r) % (2 ^ r) = 0 ∧
    qDen n r - qNum n r ≥ 2 ^ r * n ^ (a + 1) ∧
    qDen n r - qNum n r = n * (3 * n) ^ a + n ^ a * wordB w := by
  dsimp
  have hge_lt : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n :=
    fun i hi => hge i (by omega)
  have hcons := reservoir_surplus_conservation_law n r hge_lt
  dsimp at hcons
  have hdual := (reservoir_offset_duality_identity n r hge_lt).1
  have hn_r : iterateAccelerated n r ≥ n := hge r (by omega)
  have hsub : qDen n r - qNum n r =
      (2 ^ r * n ^ wordOnes (parityWordOf r n)) * iterateAccelerated n r := by
    unfold qDen qNum
    omega
  refine ⟨?_, ?_, ?_, hdual⟩
  · rw [hsub, Nat.mul_mod_right]
  · have hsub2 : qDen n r - qNum n r =
        2 ^ r * (n ^ wordOnes (parityWordOf r n) * iterateAccelerated n r) := by
      rw [hsub, Nat.mul_assoc]
    rw [hsub2, Nat.mul_mod_right]
  · rw [hsub, Nat.pow_succ, ← Nat.mul_assoc]
    exact Nat.mul_le_mul_left _ hn_r

/-- Arithmetic Compatibility Obstruction Theorem (`arithmetic_compatibility_obstruction`):
    For any odd `n > 1` (`n % 2 = 1`) and any depth `r ≥ 1` along a non-returning
    non-descending prefix (`∀ i, 1 ≤ i → i ≤ r → iterateAccelerated n i > n`),
    combining the divisibility lower bound `qDen n r - qNum n r ≥ 2^r * n^{a_r} * F^r(n)`
    with the exponential upper bound `infinite_nondescent_reservoir_obstruction` forces:
    1. `2^r * n * (n + 2)^{a_r - 1} < (3 * n + 1) * (3 * n + 7)^{a_r - 1}`, and
    2. Whenever `F^r(n)` is odd (`F^r(n) % 2 = 1`), `F^r(n) ≥ n + 2` and
       `2^r * (n + 2)^{a_r} ≤ (3 * n + 1) * (3 * n + 7)^{a_r - 1} < (3 * n + 7)^{a_r}`. -/
theorem arithmetic_compatibility_obstruction (n r : Nat)
    (hn1 : n > 1) (hr1 : r ≥ 1) (hn_odd : n % 2 = 1)
    (hstrict : ∀ i : Nat, 1 ≤ i → i ≤ r → iterateAccelerated n i > n) :
    let a := wordOnes (parityWordOf r n)
    2 ^ r * n * (n + 2) ^ (a - 1) <
      (3 * n + 1) * (3 * n + 7) ^ (a - 1) ∧
    (iterateAccelerated n r % 2 = 1 →
      2 ^ r * (n + 2) ^ a ≤ (3 * n + 1) * (3 * n + 7) ^ (a - 1) ∧
      2 ^ r * (n + 2) ^ a < (3 * n + 7) ^ a) := by
  dsimp
  rcases infinite_nondescent_reservoir_obstruction n r hn1 hr1 hn_odd
    (fun i hi1 hik => hstrict i hi1 (by omega)) with ⟨ha_ge1, hbound, _⟩
  have hgt_r : iterateAccelerated n r > n := hstrict r hr1 (by omega)
  have hpos_pow : 2 ^ r * (n + 2) ^ (wordOnes (parityWordOf r n) - 1) > 0 :=
    Nat.mul_pos (pow_pos_of_pos 2 r (by decide))
      (pow_pos_of_pos (n + 2) (wordOnes (parityWordOf r n) - 1) (by omega))
  have hlt_lhs : (2 ^ r * (n + 2) ^ (wordOnes (parityWordOf r n) - 1)) * n <
      (2 ^ r * (n + 2) ^ (wordOnes (parityWordOf r n) - 1)) * iterateAccelerated n r :=
    Nat.mul_lt_mul_of_pos_left hgt_r hpos_pow
  have hcomm_n : 2 ^ r * n * (n + 2) ^ (wordOnes (parityWordOf r n) - 1) =
      (2 ^ r * (n + 2) ^ (wordOnes (parityWordOf r n) - 1)) * n := by
    rw [Nat.mul_assoc (2 ^ r) n _, Nat.mul_comm n ((n + 2) ^ _), ← Nat.mul_assoc]
  refine ⟨by omega, ?_⟩
  intro hodd_r
  have hge_n2 : iterateAccelerated n r ≥ n + 2 := by omega
  have hle_n2 : (2 ^ r * (n + 2) ^ (wordOnes (parityWordOf r n) - 1)) * (n + 2) ≤
      (2 ^ r * (n + 2) ^ (wordOnes (parityWordOf r n) - 1)) * iterateAccelerated n r :=
    Nat.mul_le_mul_left _ hge_n2
  have ha_split : wordOnes (parityWordOf r n) =
      (wordOnes (parityWordOf r n) - 1) + 1 := by omega
  have hpow_n2 : 2 ^ r * (n + 2) ^ wordOnes (parityWordOf r n) =
      (2 ^ r * (n + 2) ^ (wordOnes (parityWordOf r n) - 1)) * (n + 2) := by
    conv => lhs; rw [ha_split, Nat.pow_succ]
    rw [← Nat.mul_assoc]
  have hle_odd : 2 ^ r * (n + 2) ^ wordOnes (parityWordOf r n) ≤
      (3 * n + 1) * (3 * n + 7) ^ (wordOnes (parityWordOf r n) - 1) := by
    rw [hpow_n2]
    exact Nat.le_trans hle_n2 hbound
  have hpos_3n7 : (3 * n + 7) ^ (wordOnes (parityWordOf r n) - 1) > 0 :=
    pow_pos_of_pos (3 * n + 7) (wordOnes (parityWordOf r n) - 1) (by omega)
  have hlt_3n7 : (3 * n + 1) * (3 * n + 7) ^ (wordOnes (parityWordOf r n) - 1) <
      (3 * n + 7) * (3 * n + 7) ^ (wordOnes (parityWordOf r n) - 1) :=
    Nat.mul_lt_mul_of_pos_right (by omega) hpos_3n7
  have hpow_3n7 : (3 * n + 7) ^ wordOnes (parityWordOf r n) =
      (3 * n + 7) * (3 * n + 7) ^ (wordOnes (parityWordOf r n) - 1) := by
    conv => lhs; rw [ha_split, Nat.pow_succ]
    rw [Nat.mul_comm]
  exact ⟨hle_odd, by omega⟩

/-- Sharpened Cycle Exclusion via Strict Interior Excursion (`periodic_orbit_strict_interior_excursion_bound`):
    Suppose `n > 1` is the strict minimum element of a cycle of minimal period `r ≥ 1`
    (`∀ i, 1 ≤ i → i < r → iterateAccelerated n i > n` and `iterateAccelerated n r = n`).
    Then `a = wordOnes (parityWordOf r n) ≥ 1`, `3^a < 2^r`, and simultaneously:
    `2^r * n * (n + 2)^{a - 1} ≤ (3 * n + 1) * (3 * n + 7)^{a - 1}`
    (strictly sharpening Eliahou's `2^r * n^a ≤ (3 * n + 1)^a` at every odd step `i ≥ 1`!). -/
theorem periodic_orbit_strict_interior_excursion_bound (n r : Nat)
    (hn1 : n > 1) (hr1 : r ≥ 1)
    (hstrict : ∀ i : Nat, 1 ≤ i → i < r → iterateAccelerated n i > n)
    (hcycle : iterateAccelerated n r = n) :
    let a := wordOnes (parityWordOf r n)
    1 ≤ a ∧
    3 ^ a < 2 ^ r ∧
    2 ^ r * (n + 2) ^ (a - 1) * n ≤
      (3 * n + 1) * (3 * n + 7) ^ (a - 1) := by
  dsimp
  have hmin : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n := by
    intro i hi
    cases i with
    | zero => dsimp [iterateAccelerated]; omega
    | succ i' =>
      by_cases hlt : i' + 1 < r
      · have hgt := hstrict (i' + 1) (by omega) hlt
        omega
      · have heq_r : i' + 1 = r := by omega
        rw [heq_r, hcycle]
        omega
  rcases universal_cycle_minimum_element_bound n r n hn1 hr1 (by omega) (by omega) hmin hcycle with
    ⟨ha1, hcont, _, _⟩
  have hn_odd : n % 2 = 1 := by
    have h1 := hmin 1 (by omega)
    dsimp [iterateAccelerated] at h1
    by_cases hev : n % 2 = 0
    · unfold acceleratedCollatz at h1
      rw [if_pos hev] at h1
      omega
    · omega
  rcases infinite_nondescent_reservoir_obstruction n r hn1 hr1 hn_odd hstrict with
    ⟨_, hbound, _⟩
  rw [hcycle] at hbound
  exact ⟨ha1, hcont, hbound⟩

end CollatzProofClosure
end BBB17
