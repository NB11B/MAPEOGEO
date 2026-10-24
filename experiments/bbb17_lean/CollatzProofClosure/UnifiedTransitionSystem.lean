import CollatzProofClosure.Definitions
import CollatzProofClosure.DeficitLifting
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

/-! ## Section 6: Projective Fixed-Point Dynamics, 2-Adic Lifting Coupling, and Universal Non-Descent Offset Bound

    In Section 5 we proved the exact Reservoir-Offset Duality Identity:
    `deficitReservoir n r + n^{a_r} * wordB w_r + n * (3 * n)^{a_r} = n * (3 * n + 1)^{a_r}`.
    Alone, the pure exponential bounds `(3n / (3n+1))^{a_r} < 1 - Q_r ≤ U^{a_r - 1}` with
    `U = n(3n+7)/((n+2)(3n+1))` are algebraically compatible because `U / L = (3n+7)/(3n+6) > 1`.
    Therefore, extracting a contradiction requires coupling the reservoir-offset duality identity with:
    1. **2-adic canonical residue lifting (`minWordRep w + q * wordD w`)** and the projective
       fixed point `x_w = wordB w / wordDelta w` of contracting operators (`wordD w > wordA w`),
    2. **Exact step evolution of the projective fixed-point coordinates `(wordB w, wordDelta w)`**
       under even and odd extensions, and
    3. **Universal Non-Descent Offset and Fixed-Point Bound**:
       Using `(Y + 1)^a ≤ Y^a + a * (Y + 1)^{a - 1}` with `Y = 3 * n`, the Reservoir-Offset
       Duality Identity implies that along **every** non-descending prefix of **any** length `r ≥ 1`
       (even after arbitrarily many spectral crossings, where `IsPrefixExpanding` no longer holds!):
       `deficitReservoir n r + n^{a_r} * wordB w_r ≤ n * a_r * (3 * n + 1)^{a_r - 1}`,
       so `n^{a_r - 1} * wordB w_r ≤ a_r * (3 * n + 1)^{a_r - 1}`, and at every contracting
       depth (`wordDelta w_r ≥ 1`):
       `wordDelta w_r * n^{a_r} ≤ n^{a_r - 1} * wordB w_r ≤ a_r * (3 * n + 1)^{a_r - 1}`
       and `wordDelta w_r * n ≤ a_r * 4^{a_r - 1}`.
-/

/-- Projective Fixed-Point Dichotomy (`contracting_nondescent_iff_le_fixedPoint`):
    For any contracting parity word `w` (`wordD w > wordA w`, so `wordDelta w > 0`) and
    any admissible integer `m` (`validParityWord m w`), non-descent `applyParityWord m w ≥ m`
    holds if and only if `m` lies at or below the projective fixed point `x_w = wordB w / wordDelta w`
    (`wordDelta w * m ≤ wordB w`), and strict descent `applyParityWord m w < m` holds if and only if
    `m` lies strictly above `x_w` (`wordDelta w * m > wordB w`, quantized as `wordDelta w * m ≥ wordB w + wordD w`). -/
theorem contracting_nondescent_iff_le_fixedPoint (w : List Bool) (m : Nat)
    (hv : validParityWord m w) (hgt : wordD w > wordA w) :
    (applyParityWord m w ≥ m ↔ wordDelta w * m ≤ wordB w) ∧
    (applyParityWord m w < m ↔ wordDelta w * m > wordB w) ∧
    (applyParityWord m w < m ↔ wordDelta w * m ≥ wordB w + wordD w) := by
  have hdesc_iff := contracting_word_descent_iff w m hv hgt
  have hquant := discrete_deficit_quantization_iff w m hv hgt
  unfold wordDelta at *
  refine ⟨?_, hdesc_iff, hquant.2.1.symm⟩
  constructor <;> intro h <;> omega

/-- Coupling of the Projective Fixed Point `x_w = B_w / Δ_w` with 2-Adic Residue Lifts
    (`fixedPoint_residue_lift_coupling`):
    For any contracting parity word `w` (`wordD w ≥ wordA w`) and any lift quotient `q : Nat`,
    let `m = minWordRep w + q * wordD w` and `y = applyParityWord m w`. Then:
    1. `validParityWord m w` and `y = minRepOutput w + q * wordA w`,
    2. Whenever the canonical representative descends or stays equal (`minRepOutput w ≤ minWordRep w`),
       every lift `q ≥ 0` satisfies `y ≤ m` and lies above the projective fixed point:
       `wordDelta w * m = wordB w + wordD w * ((minWordRep w - minRepOutput w) + q * wordDelta w)`,
    3. Conversely, if `m` avoids descent (`y ≥ m`), then `q * wordDelta w ≤ minRepOutput w - minWordRep w`
       and `wordB w = wordDelta w * m + wordD w * ((minRepOutput w - minWordRep w) - q * wordDelta w)`
       (so at most finitely many 2-adic lifts `q` can remain below the projective fixed point `x_w`). -/
theorem fixedPoint_residue_lift_coupling (w : List Bool) (q : Nat)
    (hge : wordD w ≥ wordA w) :
    let m := minWordRep w + q * wordD w
    let y := applyParityWord m w
    validParityWord m w ∧
    y = minRepOutput w + q * wordA w ∧
    (minRepOutput w ≤ minWordRep w →
      y ≤ m ∧
      wordDelta w * m =
        wordB w + wordD w * ((minWordRep w - minRepOutput w) + q * wordDelta w)) ∧
    (y ≥ m →
      minRepOutput w ≥ minWordRep w + q * wordDelta w ∧
      wordB w =
        wordDelta w * m + wordD w * ((minRepOutput w - minWordRep w) - q * wordDelta w)) := by
  dsimp
  have hv_min := minWordRep_valid w
  rcases parityWord_residue_shift w (minWordRep w) q hv_min with ⟨hv_m, hy_eq⟩
  have hy_min : applyParityWord (minWordRep w) w = minRepOutput w := rfl
  rw [hy_min] at hy_eq
  have hbal := discrete_deficit_balance w (minWordRep w + q * wordD w) hv_m hge
  have hq_delta : q * wordDelta w + q * wordA w = q * wordD w := by
    unfold wordDelta
    rw [← Nat.mul_add, Nat.sub_add_cancel hge]
  refine ⟨hv_m, hy_eq, ?_, ?_⟩
  · intro hmin_le
    have hy_le_m : applyParityWord (minWordRep w + q * wordD w) w ≤
        minWordRep w + q * wordD w := by omega
    have hdiff : minWordRep w + q * wordD w -
        applyParityWord (minWordRep w + q * wordD w) w =
        (minWordRep w - minRepOutput w) + q * wordDelta w := by omega
    have hdesc := (discrete_deficit_descent_identity w (minWordRep w + q * wordD w) hv_m hge hy_le_m).1
    rw [hdiff] at hdesc
    exact ⟨hy_le_m, hdesc⟩
  · intro hy_ge_m
    have hmin_ge : minRepOutput w ≥ minWordRep w + q * wordDelta w := by omega
    have hdiff : applyParityWord (minWordRep w + q * wordD w) w -
        (minWordRep w + q * wordD w) =
        (minRepOutput w - minWordRep w) - q * wordDelta w := by omega
    have hnondesc := (discrete_deficit_nondescent_identity w (minWordRep w + q * wordD w) hv_m hge hy_ge_m).1
    rw [hdiff] at hnondesc
    exact ⟨hmin_ge, hnondesc⟩

/-- Projective Fixed-Point Even-Step Evolution Law (`fixedPoint_even_extension_law`):
    Under an even step `w ↦ w ++ [false]` in the contracting regime (`wordD w ≥ wordA w`):
    1. `wordB (w ++ [false]) = wordB w` (numerator is unchanged),
    2. `wordDelta (w ++ [false]) = wordDelta w + wordD w` (denominator increases by `D_w = 2^|w|`),
    3. Cross-ratio identity:
       `wordB w * wordDelta (w ++ [false]) = wordB (w ++ [false]) * wordDelta w + wordB w * wordD w`
       (so the projective fixed point strictly contracts toward `0`), and
    4. For every integer `m`, `wordDelta (w ++ [false]) * m = wordDelta w * m + wordD w * m`. -/
theorem fixedPoint_even_extension_law (w : List Bool) (m : Nat)
    (hge : wordD w ≥ wordA w) :
    wordB (w ++ [false]) = wordB w ∧
    wordDelta (w ++ [false]) = wordDelta w + wordD w ∧
    wordB w * wordDelta (w ++ [false]) =
      wordB (w ++ [false]) * wordDelta w + wordB w * wordD w ∧
    wordDelta (w ++ [false]) * m = wordDelta w * m + wordD w * m := by
  have hB : wordB (w ++ [false]) = wordB w := by
    rw [wordB_append]; dsimp [wordB, wordA]; omega
  have hD : wordD (w ++ [false]) = 2 * wordD w := by
    rw [wordD_append]; dsimp [wordD]; omega
  have hA : wordA (w ++ [false]) = wordA w := by
    rw [wordA_append]; dsimp [wordA]; omega
  have hDelta : wordDelta (w ++ [false]) = wordDelta w + wordD w := by
    unfold wordDelta
    omega
  refine ⟨hB, hDelta, ?_, ?_⟩
  · rw [hB, hDelta, Nat.mul_add]
  · rw [hDelta, Nat.add_mul]

/-- Projective Fixed-Point Odd-Step Evolution Law (`fixedPoint_odd_extension_law`):
    Under an odd step `w ↦ w ++ [true]`:
    1. `wordB (w ++ [true]) = 3 * wordB w + wordD w`,
    2. `wordD (w ++ [true]) = 2 * wordD w` and `wordA (w ++ [true]) = 3 * wordA w`, and
    3. Whenever `w ++ [true]` remains contracting (`2 * wordD w ≥ 3 * wordA w`),
       `wordDelta (w ++ [true]) + wordA w = 2 * wordDelta w` and
       `wordB (w ++ [true]) * wordDelta w =
          wordB w * wordDelta (w ++ [true]) + wordB w * (wordDelta w + wordA w) + wordD w * wordDelta w`. -/
theorem fixedPoint_odd_extension_law (w : List Bool) :
    wordB (w ++ [true]) = 3 * wordB w + wordD w ∧
    wordD (w ++ [true]) = 2 * wordD w ∧
    wordA (w ++ [true]) = 3 * wordA w ∧
    (2 * wordD w ≥ 3 * wordA w →
      wordDelta (w ++ [true]) + wordA w = 2 * wordDelta w ∧
      wordB (w ++ [true]) * wordDelta w =
        wordB w * wordDelta (w ++ [true]) +
          wordB w * (wordDelta w + wordA w) + wordD w * wordDelta w) := by
  have hB : wordB (w ++ [true]) = 3 * wordB w + wordD w := by
    rw [wordB_append]; dsimp [wordB, wordA]; omega
  have hD : wordD (w ++ [true]) = 2 * wordD w := by
    rw [wordD_append]; dsimp [wordD]; omega
  have hA : wordA (w ++ [true]) = 3 * wordA w := by
    rw [wordA_append]; dsimp [wordA]; omega
  refine ⟨hB, hD, hA, ?_⟩
  intro hge
  have hDelta : wordDelta (w ++ [true]) + wordA w = 2 * wordDelta w := by
    unfold wordDelta
    omega
  refine ⟨hDelta, ?_⟩
  have h1 : wordB w * wordDelta (w ++ [true]) + wordB w * (wordDelta w + wordA w) =
      wordB w * (wordDelta (w ++ [true]) + wordA w + wordDelta w) := by
    rw [← Nat.mul_add]
    congr 1
    omega
  have h2 : wordDelta (w ++ [true]) + wordA w + wordDelta w = 3 * wordDelta w := by omega
  rw [hB, Nat.add_mul, h1, h2, Nat.mul_comm 3 (wordB w), Nat.mul_assoc]

/-- Elementary Power-Gap Upper Bound (`pow_succ_sub_pow_le_mul_pow_pred`):
    For all `Y a : Nat`, `(Y + 1)^a ≤ Y^a + a * (Y + 1)^{a - 1}`.
    (Follows by telescoping `(Y + 1)^a - Y^a = ∑_{k=0}^{a-1} Y^k (Y + 1)^{a - 1 - k} ≤ a * (Y + 1)^{a - 1}`.) -/
theorem pow_succ_sub_pow_le_mul_pow_pred (Y a : Nat) :
    (Y + 1) ^ a ≤ Y ^ a + a * (Y + 1) ^ (a - 1) := by
  induction a with
  | zero =>
    simp
  | succ a ih =>
    cases a with
    | zero =>
      simp
    | succ b =>
      have hsub1 : b + 1 - 1 = b := by omega
      have hsub2 : b + 1 + 1 - 1 = b + 1 := by omega
      rw [hsub1] at ih
      rw [hsub2]
      calc (Y + 1) ^ (b + 1 + 1)
        _ = (Y + 1) ^ (b + 1) * Y + (Y + 1) ^ (b + 1) := by
          rw [Nat.pow_succ (Y + 1) (b + 1), Nat.mul_add, Nat.mul_one]
        _ ≤ (Y ^ (b + 1) + (b + 1) * (Y + 1) ^ b) * Y + (Y + 1) ^ (b + 1) := by
          have hmul := Nat.mul_le_mul_right Y ih
          omega
        _ = Y ^ (b + 1 + 1) + (b + 1) * ((Y + 1) ^ b * Y) + (Y + 1) ^ (b + 1) := by
          rw [Nat.add_mul, ← Nat.pow_succ Y (b + 1), Nat.mul_assoc]
        _ ≤ Y ^ (b + 1 + 1) + (b + 1) * ((Y + 1) ^ b * (Y + 1)) + (Y + 1) ^ (b + 1) := by
          have hY : (Y + 1) ^ b * Y ≤ (Y + 1) ^ b * (Y + 1) :=
            Nat.mul_le_mul_left ((Y + 1) ^ b) (by omega)
          have hmul := Nat.mul_le_mul_left (b + 1) hY
          omega
        _ = Y ^ (b + 1 + 1) + (b + 1 + 1) * (Y + 1) ^ (b + 1) := by
          have hpow : (Y + 1) ^ b * (Y + 1) = (Y + 1) ^ (b + 1) :=
            (Nat.pow_succ (Y + 1) b).symm
          rw [hpow, Nat.add_mul (b + 1) 1, Nat.one_mul, Nat.add_assoc]

/-- Universal Non-Descent Offset and Projective Fixed-Point Bound
    (`universal_nondescent_offset_and_fixedPoint_bound`):
    For ANY `n > 1` and ANY depth `r ≥ 1` along a non-descending trajectory prefix
    (`∀ i ≤ r, iterateAccelerated n i ≥ n`), let `w = parityWordOf r n` and `a = wordOnes w`.
    Even after arbitrarily many spectral crossings (where `IsPrefixExpanding w` no longer holds!),
    combining the Reservoir-Offset Duality Identity with `pow_succ_sub_pow_le_mul_pow_pred` forces:
    1. `a ≥ 1`,
    2. `deficitReservoir n r + n^a * wordB w ≤ n * (a * (3 * n + 1)^{a - 1})`,
    3. `n^{a - 1} * wordB w ≤ a * (3 * n + 1)^{a - 1}`,
    4. `wordDelta w * n^a ≤ n^{a - 1} * wordB w ≤ a * (3 * n + 1)^{a - 1}`, and
    5. `wordDelta w * n ≤ a * 4^{a - 1}`. -/
theorem universal_nondescent_offset_and_fixedPoint_bound (n r : Nat)
    (hn1 : n > 1) (hr1 : r ≥ 1)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let w := parityWordOf r n
    let a := wordOnes w
    a ≥ 1 ∧
    deficitReservoir n r + n ^ a * wordB w ≤
      n * (a * (3 * n + 1) ^ (a - 1)) ∧
    n ^ (a - 1) * wordB w ≤ a * (3 * n + 1) ^ (a - 1) ∧
    wordDelta w * n ^ a ≤ n ^ (a - 1) * wordB w ∧
    wordDelta w * n ^ a ≤ a * (3 * n + 1) ^ (a - 1) ∧
    wordDelta w * n ≤ a * 4 ^ (a - 1) := by
  dsimp
  have ha1 : wordOnes (parityWordOf r n) ≥ 1 := by
    have h1 := hge 1 hr1
    dsimp [iterateAccelerated] at h1
    have hodd0 : n % 2 = 1 := by
      by_cases hev : n % 2 = 0
      · unfold acceleratedCollatz at h1
        rw [if_pos hev] at h1
        omega
      · omega
    have hb0 : (n % 2 == 1) = true := by rw [beq_iff_eq]; exact hodd0
    have hones1 : wordOnes (parityWordOf 1 n) = 1 := by
      dsimp [parityWordOf]; rw [hb0]; dsimp [wordOnes]
    have hmono := wordOnes_parityWordOf_mono n 1 (r - 1)
    have hr_eq : 1 + (r - 1) = r := by omega
    rw [hr_eq, hones1] at hmono
    exact hmono
  have hge_lt : ∀ i : Nat, i < r → iterateAccelerated n i ≥ n :=
    fun i hi => hge i (by omega)
  have hdual := (reservoir_offset_duality_identity n r hge_lt).2
  have hpow_gap := pow_succ_sub_pow_le_mul_pow_pred (3 * n) (wordOnes (parityWordOf r n))
  have hmul_gap : n * (3 * n + 1) ^ wordOnes (parityWordOf r n) ≤
      n * (3 * n) ^ wordOnes (parityWordOf r n) +
        n * (wordOnes (parityWordOf r n) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 1)) := by
    rw [← Nat.mul_add]
    exact Nat.mul_le_mul_left n hpow_gap
  have hres_B_le : deficitReservoir n r +
      n ^ wordOnes (parityWordOf r n) * wordB (parityWordOf r n) ≤
      n * (wordOnes (parityWordOf r n) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 1)) := by
    omega
  have ha_split : wordOnes (parityWordOf r n) =
      (wordOnes (parityWordOf r n) - 1) + 1 := by omega
  have hna_eq : n ^ wordOnes (parityWordOf r n) * wordB (parityWordOf r n) =
      n * (n ^ (wordOnes (parityWordOf r n) - 1) * wordB (parityWordOf r n)) := by
    conv => lhs; rw [ha_split, Nat.pow_succ]
    rw [Nat.mul_comm (n ^ _) n, Nat.mul_assoc]
  have hmul_B_le : n * (n ^ (wordOnes (parityWordOf r n) - 1) * wordB (parityWordOf r n)) ≤
      n * (wordOnes (parityWordOf r n) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 1)) := by
    omega
  have hB_le : n ^ (wordOnes (parityWordOf r n) - 1) * wordB (parityWordOf r n) ≤
      wordOnes (parityWordOf r n) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 1) :=
    Nat.le_of_mul_le_mul_left hmul_B_le (by omega)
  have hdelta_n_le_B : wordDelta (parityWordOf r n) * n ≤ wordB (parityWordOf r n) := by
    by_cases hDA : wordD (parityWordOf r n) ≥ wordA (parityWordOf r n)
    · have hv := parityWordOf_valid r n
      have hge_r : applyParityWord n (parityWordOf r n) ≥ n := by
        rw [applyParityWord_parityWordOf]
        exact hge r (by omega)
      have hnd := (discrete_deficit_nondescent_identity (parityWordOf r n) n hv hDA hge_r).1
      omega
    · unfold wordDelta
      have h0 : wordD (parityWordOf r n) - wordA (parityWordOf r n) = 0 := by omega
      rw [h0, Nat.zero_mul]
      omega
  have h1 : wordDelta (parityWordOf r n) * n ^ wordOnes (parityWordOf r n) =
      n ^ (wordOnes (parityWordOf r n) - 1) * (wordDelta (parityWordOf r n) * n) := by
    conv => lhs; rw [ha_split, Nat.pow_succ]
    rw [← Nat.mul_assoc, Nat.mul_comm (wordDelta _) (n ^ _), Nat.mul_assoc]
  have hdelta_na_le : wordDelta (parityWordOf r n) * n ^ wordOnes (parityWordOf r n) ≤
      n ^ (wordOnes (parityWordOf r n) - 1) * wordB (parityWordOf r n) := by
    rw [h1]
    exact Nat.mul_le_mul_left _ hdelta_n_le_B
  have hdelta_na_le_rhs : wordDelta (parityWordOf r n) * n ^ wordOnes (parityWordOf r n) ≤
      wordOnes (parityWordOf r n) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 1) :=
    Nat.le_trans hdelta_na_le hB_le
  have h3n1_le_4n : 3 * n + 1 ≤ 4 * n := by omega
  have hpow_le : (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 1) ≤
      (4 * n) ^ (wordOnes (parityWordOf r n) - 1) :=
    pow_le_pow_of_le (3 * n + 1) (4 * n) (wordOnes (parityWordOf r n) - 1) h3n1_le_4n
  have h4n_pow : (4 * n) ^ (wordOnes (parityWordOf r n) - 1) =
      4 ^ (wordOnes (parityWordOf r n) - 1) * n ^ (wordOnes (parityWordOf r n) - 1) :=
    mul_pow_eq 4 n (wordOnes (parityWordOf r n) - 1)
  have hdelta_coarse_mul :
      n ^ (wordOnes (parityWordOf r n) - 1) * (wordDelta (parityWordOf r n) * n) ≤
      n ^ (wordOnes (parityWordOf r n) - 1) *
        (wordOnes (parityWordOf r n) * 4 ^ (wordOnes (parityWordOf r n) - 1)) := by
    have hrhs_le : wordOnes (parityWordOf r n) * (3 * n + 1) ^ (wordOnes (parityWordOf r n) - 1) ≤
        n ^ (wordOnes (parityWordOf r n) - 1) *
          (wordOnes (parityWordOf r n) * 4 ^ (wordOnes (parityWordOf r n) - 1)) := by
      have hm := Nat.mul_le_mul_left (wordOnes (parityWordOf r n)) hpow_le
      rw [h4n_pow, ← Nat.mul_assoc,
          Nat.mul_comm (wordOnes (parityWordOf r n) * 4 ^ _) (n ^ _)] at hm
      exact hm
    rw [← h1]
    exact Nat.le_trans hdelta_na_le_rhs hrhs_le
  have hpos_na1 : n ^ (wordOnes (parityWordOf r n) - 1) > 0 :=
    pow_pos_of_pos n (wordOnes (parityWordOf r n) - 1) (by omega)
  have hdelta_4 : wordDelta (parityWordOf r n) * n ≤
      wordOnes (parityWordOf r n) * 4 ^ (wordOnes (parityWordOf r n) - 1) :=
    Nat.le_of_mul_le_mul_left hdelta_coarse_mul hpos_na1
  exact ⟨ha1, hres_B_le, hB_le, hdelta_na_le, hdelta_na_le_rhs, hdelta_4⟩

/-! ## Section 7: Signed Projective Gap over `Int`, 2-Adic Modular Branch Lock, and Surviving Lift Sets `𝓢_r(n)`

    Because `wordDelta w = wordD w - wordA w` uses truncated natural-number subtraction,
    it vanishes at expanding depths (`wordD w ≤ wordA w`). Defining the **Signed Projective Gap**
    over `Int`:
    `signedProjectiveGap w n = ((wordD w : Int) - (wordA w : Int)) * (n : Int) - (wordB w : Int)`
    retains complete sign and magnitude information across **both** expanding and contracting regimes:
    1. **Uniform Identity & Sign Trichotomy (`signedProjectiveGap_eq_wordD_mul_sub`, `signedProjectiveGap_sign_trichotomy`)**:
       For every admissible word `w` of `n` (regardless of spectral regime!),
       `G_w(n) = D_w * (n - F_w(n))`. Thus `G_w(n) > 0 ↔ F_w(n) < n`, `G_w(n) = 0 ↔ F_w(n) = n`,
       and `G_w(n) < 0 ↔ F_w(n) > n`.
    2. **Exact Step Update Recurrences (`signedProjectiveGap_even_step`, `signedProjectiveGap_odd_step`)**:
       For every word `w` and integer `n`:
       `G_{w ++ [false]}(n) = G_w(n) + D_w * n` and
       `G_{w ++ [true]}(n) = 3 * G_w(n) - D_w * (n + 1)`.
    3. **2-Adic Modular Branch Lock & Autonomous Recurrence (`signedProjectiveGap_modular_branch_lock`, `signedProjectiveGap_even_step_descent_band`)**:
       For any admissible prefix `w` of `n`, `G_{w0}(n) = D_w * (2n - F_w(n))` and
       `G_{w1}(n) = D_w * (2n - (3 F_w(n) + 1))`. Moreover, for odd `n`, the trajectory gap
       `G_r(n) = G_{w_r(n)}(n)` satisfies an autonomous 2-adic recurrence determined solely by
       whether `2^{r+1} ∣ G_r(n)`. Whenever `-2^r * n < G_r(n) ≤ 0`, any even step forces
       immediate strict descent `G_{r+1}(n) > 0`.
    4. **Surviving Prefix-Non-Descending Lift Sets `𝓢_r(n)` (`InSurvivingLiftSet`, `survivingLiftSet_intermediate_contracting_cap`)**:
       For `𝓢_r(n) = { m ∈ ℕ : m ≡ n (mod 2^r) ∧ ∀ i ≤ r, F^i(m) ≥ m }`, every member `m ∈ 𝓢_r(n)`
       shares the exact parity prefix `w_i(n)` for all `i ≤ r`, satisfies `G_{w_i(n)}(m) ≤ 0` and
       the Reservoir-Offset Duality Identity at every intermediate depth `i ≤ r`, and is bounded above
       by the projective fixed point `B_{w_i} / (2^i - 3^{a_i})` at **every** intermediate contracting
       depth `i ≤ r` (even if the trajectory re-expands at depth `r`).
-/

/-- Signed projective gap `G_w(n) = D_w * n - A_w * n - B_w = (D_w - A_w) * n - B_w` over `Int`.
    Retains full sign and magnitude across both expanding (`D_w < A_w`) and
    contracting (`D_w > A_w`) regimes without natural-number truncation. -/
def signedProjectiveGap (w : List Bool) (n : Nat) : Int :=
  (wordD w : Int) * (n : Int) - (wordA w : Int) * (n : Int) - (wordB w : Int)

/-- Factored form `G_w(n) = (D_w - A_w) * n - B_w` over `Int`. -/
theorem signedProjectiveGap_factored (w : List Bool) (n : Nat) :
    signedProjectiveGap w n =
      ((wordD w : Int) - (wordA w : Int)) * (n : Int) - (wordB w : Int) := by
  unfold signedProjectiveGap
  rw [Int.sub_mul]

/-- Exact Trajectory Identity for the Signed Projective Gap (`signedProjectiveGap_eq_wordD_mul_sub`):
    For EVERY parity word `w` (expanding, neutral, or contracting) and EVERY admissible `n`
    (`validParityWord n w`), `G_w(n) = D_w * (n - F_w(n))`. -/
theorem signedProjectiveGap_eq_wordD_mul_sub (w : List Bool) (n : Nat)
    (hv : validParityWord n w) :
    signedProjectiveGap w n =
      (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) := by
  have haff := parityWord_affine_identity w n hv
  have haffInt : (wordD w : Int) * (applyParityWord n w : Int) =
      (wordA w : Int) * (n : Int) + (wordB w : Int) := by
    exact_mod_cast haff
  unfold signedProjectiveGap
  rw [Int.mul_sub]
  omega

/-- Uniform Sign Trichotomy for the Signed Projective Gap (`signedProjectiveGap_sign_trichotomy`):
    For EVERY admissible parity word `w` of `n` (regardless of whether `D_w > A_w` or `D_w ≤ A_w`):
    1. `G_w(n) > 0 ↔ F_w(n) < n` (strict descent),
    2. `G_w(n) = 0 ↔ F_w(n) = n` (return to starting value),
    3. `G_w(n) < 0 ↔ F_w(n) > n` (net expansion), and
    4. `G_w(n) ≤ 0 ↔ F_w(n) ≥ n` (non-descent). -/
theorem signedProjectiveGap_sign_trichotomy (w : List Bool) (n : Nat)
    (hv : validParityWord n w) :
    (signedProjectiveGap w n > 0 ↔ applyParityWord n w < n) ∧
    (signedProjectiveGap w n = 0 ↔ applyParityWord n w = n) ∧
    (signedProjectiveGap w n < 0 ↔ applyParityWord n w > n) ∧
    (signedProjectiveGap w n ≤ 0 ↔ applyParityWord n w ≥ n) := by
  have heq := signedProjectiveGap_eq_wordD_mul_sub w n hv
  have hD_pos : wordD w > 0 := wordD_pos w
  have hD_int_pos : (wordD w : Int) > 0 := by omega
  rw [heq]
  refine ⟨?_, ?_, ?_, ?_⟩
  · constructor
    · intro hpos
      by_cases hlt : applyParityWord n w < n
      · exact hlt
      · have hle : (n : Int) - (applyParityWord n w : Int) ≤ 0 := by omega
        have hmul_le : (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) ≤
            (wordD w : Int) * 0 := Int.mul_le_mul_of_nonneg_left hle (by omega)
        omega
    · intro hlt
      have hge1 : (n : Int) - (applyParityWord n w : Int) ≥ 1 := by omega
      have hmul_ge : (wordD w : Int) * 1 ≤
          (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) :=
        Int.mul_le_mul_of_nonneg_left hge1 (by omega)
      omega
  · constructor
    · intro hz
      rcases Int.mul_eq_zero.mp hz with hD0 | hsub0 <;> omega
    · intro heq_n
      have hsub0 : (n : Int) - (applyParityWord n w : Int) = 0 := by omega
      rw [hsub0, Int.mul_zero]
  · constructor
    · intro hneg
      by_cases hgt : applyParityWord n w > n
      · exact hgt
      · have hge0 : (n : Int) - (applyParityWord n w : Int) ≥ 0 := by omega
        have hmul_ge : (wordD w : Int) * 0 ≤
            (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) :=
          Int.mul_le_mul_of_nonneg_left hge0 (by omega)
        omega
    · intro hgt
      have hle_m1 : (n : Int) - (applyParityWord n w : Int) ≤ -1 := by omega
      have hmul_le : (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) ≤
          (wordD w : Int) * (-1) :=
        Int.mul_le_mul_of_nonneg_left hle_m1 (by omega)
      omega
  · constructor
    · intro hle0
      by_cases hge : applyParityWord n w ≥ n
      · exact hge
      · have hge1 : (n : Int) - (applyParityWord n w : Int) ≥ 1 := by omega
        have hmul_ge : (wordD w : Int) * 1 ≤
            (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) :=
          Int.mul_le_mul_of_nonneg_left hge1 (by omega)
        omega
    · intro hge
      have hle0 : (n : Int) - (applyParityWord n w : Int) ≤ 0 := by omega
      have hmul_le : (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) ≤
          (wordD w : Int) * 0 :=
        Int.mul_le_mul_of_nonneg_left hle0 (by omega)
      omega

/-- Exact Even-Step Affine Update for the Signed Projective Gap (`signedProjectiveGap_even_step`):
    For EVERY parity word `w` and EVERY `n : Nat` (without requiring admissibility),
    `G_{w ++ [false]}(n) = G_w(n) + D_w * n`. -/
theorem signedProjectiveGap_even_step (w : List Bool) (n : Nat) :
    signedProjectiveGap (w ++ [false]) n =
      signedProjectiveGap w n + (wordD w : Int) * (n : Int) := by
  have hD : (wordD (w ++ [false]) : Int) = 2 * (wordD w : Int) := by
    rw [wordD_append]; dsimp [wordD]; omega
  have hA : (wordA (w ++ [false]) : Int) = (wordA w : Int) := by
    rw [wordA_append]; dsimp [wordA]; omega
  have hB : (wordB (w ++ [false]) : Int) = (wordB w : Int) := by
    rw [wordB_append]; dsimp [wordB, wordA]; omega
  unfold signedProjectiveGap
  rw [hD, hA, hB, Int.mul_assoc]
  omega

/-- Exact Odd-Step Affine Update for the Signed Projective Gap (`signedProjectiveGap_odd_step`):
    For EVERY parity word `w` and EVERY `n : Nat` (without requiring admissibility),
    `G_{w ++ [true]}(n) = 3 * G_w(n) - D_w * (n + 1)`. -/
theorem signedProjectiveGap_odd_step (w : List Bool) (n : Nat) :
    signedProjectiveGap (w ++ [true]) n =
      3 * signedProjectiveGap w n - (wordD w : Int) * ((n : Int) + 1) := by
  have hD : (wordD (w ++ [true]) : Int) = 2 * (wordD w : Int) := by
    rw [wordD_append]; dsimp [wordD]; omega
  have hA : (wordA (w ++ [true]) : Int) = 3 * (wordA w : Int) := by
    rw [wordA_append]; dsimp [wordA]; omega
  have hB : (wordB (w ++ [true]) : Int) = 3 * (wordB w : Int) + (wordD w : Int) := by
    rw [wordB_append]; dsimp [wordB, wordA]; omega
  unfold signedProjectiveGap
  rw [hD, hA, hB, Int.mul_assoc 2, Int.mul_assoc 3, Int.mul_add, Int.mul_one]
  omega

/-- Exact Shift Linearity of the Signed Projective Gap (`signedProjectiveGap_shift_law`):
    For any parity word `w` and any `m₁ m₂ : Nat`:
    `G_w(m₂) - G_w(m₁) = (D_w - A_w) * (m₂ - m₁)`.
    In particular, for any residue lift `m = m₁ + q * D_w`:
    `G_w(m₁ + q * D_w) = G_w(m₁) + (D_w - A_w) * (q * D_w)`. -/
theorem signedProjectiveGap_shift_law (w : List Bool) (m₁ m₂ q : Nat) :
    signedProjectiveGap w m₂ - signedProjectiveGap w m₁ =
      ((wordD w : Int) - (wordA w : Int)) * ((m₂ : Int) - (m₁ : Int)) ∧
    signedProjectiveGap w (m₁ + q * wordD w) =
      signedProjectiveGap w m₁ +
        ((wordD w : Int) - (wordA w : Int)) * ((q * wordD w : Nat) : Int) := by
  unfold signedProjectiveGap
  have hcast : ((m₁ + q * wordD w : Nat) : Int) = (m₁ : Int) + ((q * wordD w : Nat) : Int) := by
    omega
  constructor
  · rw [Int.sub_mul, Int.mul_sub, Int.mul_sub]
    omega
  · rw [hcast, Int.sub_mul, Int.mul_add (wordD w : Int), Int.mul_add (wordA w : Int)]
    omega

/-- 2-Adic Modular Branch Lock and Autonomous Signed-Gap Recurrence
    (`signedProjectiveGap_modular_branch_lock`):
    For any admissible prefix `w` of `n` (`validParityWord n w`), let `y = applyParityWord n w`:
    1. Candidate branch formulas:
       `G_{w ++ [false]}(n) = D_w * (2n - y)` and
       `G_{w ++ [true]}(n) = D_w * (2n - (3y + 1))`,
    2. Cross-branch parity separation:
       `G_{w ++ [false]}(n) - G_{w ++ [true]}(n) + 2 * G_w(n) = D_w * (2n + 1)`,
    3. Autonomous 2-adic step recurrence for odd `n` (`n % 2 = 1`):
       - Step `w ++ [true]` is taken (`y % 2 = 1`) IF AND ONLY IF `G_w(n) % (2 * D_w) = 0`, and
       - Step `w ++ [false]` is taken (`y % 2 = 0`) IF AND ONLY IF `G_w(n) % (2 * D_w) ≠ 0`. -/
theorem signedProjectiveGap_modular_branch_lock (w : List Bool) (n : Nat)
    (hv : validParityWord n w) :
    let y := applyParityWord n w
    let D := (wordD w : Int)
    signedProjectiveGap (w ++ [false]) n = D * (2 * (n : Int) - (y : Int)) ∧
    signedProjectiveGap (w ++ [true]) n = D * (2 * (n : Int) - (3 * (y : Int) + 1)) ∧
    signedProjectiveGap (w ++ [false]) n - signedProjectiveGap (w ++ [true]) n +
      2 * signedProjectiveGap w n = D * (2 * (n : Int) + 1) ∧
    (n % 2 = 1 →
      (y % 2 = 1 ↔ signedProjectiveGap w n % (2 * D) = 0) ∧
      (y % 2 = 0 ↔ signedProjectiveGap w n % (2 * D) ≠ 0)) := by
  dsimp
  have heq := signedProjectiveGap_eq_wordD_mul_sub w n hv
  have hev := signedProjectiveGap_even_step w n
  have hodd := signedProjectiveGap_odd_step w n
  have h1 : signedProjectiveGap (w ++ [false]) n =
      (wordD w : Int) * (2 * (n : Int) - (applyParityWord n w : Int)) := by
    rw [hev, heq, Int.mul_sub, Int.mul_sub, ← Int.mul_assoc (wordD w : Int) 2,
        Int.mul_comm (wordD w : Int) 2, Int.mul_assoc 2]
    omega
  have h2 : signedProjectiveGap (w ++ [true]) n =
      (wordD w : Int) * (2 * (n : Int) - (3 * (applyParityWord n w : Int) + 1)) := by
    rw [hodd, heq, Int.mul_sub (wordD w : Int), Int.mul_add (wordD w : Int),
        Int.mul_one, Int.mul_sub (wordD w : Int), Int.mul_add (wordD w : Int),
        Int.mul_one, ← Int.mul_assoc (wordD w : Int) 2,
        Int.mul_comm (wordD w : Int) 2, Int.mul_assoc 2,
        ← Int.mul_assoc (wordD w : Int) 3,
        Int.mul_comm (wordD w : Int) 3, Int.mul_assoc 3]
    omega
  have h3 : signedProjectiveGap (w ++ [false]) n - signedProjectiveGap (w ++ [true]) n +
      2 * signedProjectiveGap w n = (wordD w : Int) * (2 * (n : Int) + 1) := by
    rw [hev, hodd, Int.mul_add (wordD w : Int), Int.mul_one,
        Int.mul_add (wordD w : Int), Int.mul_one,
        ← Int.mul_assoc (wordD w : Int) 2,
        Int.mul_comm (wordD w : Int) 2, Int.mul_assoc 2]
    omega
  refine ⟨h1, h2, h3, ?_⟩
  intro hn_odd
  have hD_pos : (wordD w : Int) > 0 := by
    have hp := wordD_pos w
    omega
  have hodd_imp : applyParityWord n w % 2 = 1 →
      signedProjectiveGap w n % (2 * (wordD w : Int)) = 0 := by
    intro hy_odd
    rw [heq]
    let k : Int := (n : Int) / 2 - (applyParityWord n w : Int) / 2
    have hsub : (n : Int) - (applyParityWord n w : Int) = 2 * k := by omega
    have hmul : (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) =
        (2 * (wordD w : Int)) * k := by
      rw [hsub, ← Int.mul_assoc, Int.mul_comm (wordD w : Int) 2, Int.mul_assoc]
    rw [hmul, Int.mul_emod_right]
  have hev_imp : applyParityWord n w % 2 = 0 →
      signedProjectiveGap w n % (2 * (wordD w : Int)) ≠ 0 := by
    intro hy_ev
    rw [heq]
    let k : Int := (n : Int) / 2 - (applyParityWord n w : Int) / 2
    have hsub : (n : Int) - (applyParityWord n w : Int) = 1 + 2 * k := by omega
    have hmul : (wordD w : Int) * ((n : Int) - (applyParityWord n w : Int)) =
        (wordD w : Int) + (2 * (wordD w : Int)) * k := by
      rw [hsub, Int.mul_add, Int.mul_one,
          ← Int.mul_assoc, Int.mul_comm (wordD w : Int) 2, Int.mul_assoc]
    rw [hmul, Int.add_mul_emod_self_left]
    have hmod_eq : (wordD w : Int) % (2 * (wordD w : Int)) = (wordD w : Int) :=
      Int.emod_eq_of_lt (by omega) (by omega)
    omega
  constructor
  · constructor
    · exact hodd_imp
    · intro hmod0
      by_cases hy1 : applyParityWord n w % 2 = 1
      · exact hy1
      · exfalso
        exact hev_imp (by omega) hmod0
  · constructor
    · exact hev_imp
    · intro hne0
      by_cases hy0 : applyParityWord n w % 2 = 0
      · exact hy0
      · exfalso
        exact hne0 (hodd_imp (by omega))

/-- Even-Step Descent Band Theorem (`signedProjectiveGap_even_step_descent_band`):
    For any depth `r` and integer `n`, let `w = parityWordOf r n`:
    1. If `F^r(n)` is even (`iterateAccelerated n r % 2 = 0`), then step `r` is an even step and
       strict descent at depth `r + 1` (`signedProjectiveGap (parityWordOf (r + 1) n) n > 0`)
       holds IF AND ONLY IF `signedProjectiveGap w n + (wordD w : Int) * (n : Int) > 0`
       (equivalently `iterateAccelerated n r < 2 * n`).
    2. Consequently, whenever `signedProjectiveGap w n + (wordD w : Int) * (n : Int) > 0`
       (`F^r(n) < 2 * n`), non-descent at depth `r + 1` FORCES step `r` to be an odd step
       (`iterateAccelerated n r % 2 = 1`). -/
theorem signedProjectiveGap_even_step_descent_band (n r : Nat) :
    let w := parityWordOf r n
    let w_succ := parityWordOf (r + 1) n
    (iterateAccelerated n r % 2 = 0 →
      (signedProjectiveGap w_succ n > 0 ↔
        signedProjectiveGap w n + (wordD w : Int) * (n : Int) > 0) ∧
      (signedProjectiveGap w_succ n > 0 ↔ iterateAccelerated n r < 2 * n)) ∧
    (signedProjectiveGap w n + (wordD w : Int) * (n : Int) > 0 →
      signedProjectiveGap w_succ n ≤ 0 →
      iterateAccelerated n r % 2 = 1) := by
  dsimp
  have hv_r := parityWordOf_valid r n
  have hD_pos : (wordD (parityWordOf r n) : Int) > 0 := by
    have hp := wordD_pos (parityWordOf r n)
    omega
  have hlock := (signedProjectiveGap_modular_branch_lock (parityWordOf r n) n hv_r).1
  rw [applyParityWord_parityWordOf] at hlock
  have hsucc_eq := parityWordOf_succ_eq_append r n
  have hstep := signedProjectiveGap_even_step (parityWordOf r n) n
  refine ⟨?_, ?_⟩
  · intro hev
    have hnot1 : ¬(iterateAccelerated n r % 2 = 1) := by omega
    have hb_false : (iterateAccelerated n r % 2 == 1) = false := by
      rw [beq_eq_false_iff_ne]; exact hnot1
    have hw_succ : parityWordOf (r + 1) n = parityWordOf r n ++ [false] := by
      rw [hsucc_eq, hb_false]
    rw [hw_succ]
    refine ⟨by rw [hstep], ?_⟩
    rw [hlock]
    constructor
    · intro hpos
      by_cases hlt : iterateAccelerated n r < 2 * n
      · exact hlt
      · have hle : 2 * (n : Int) - (iterateAccelerated n r : Int) ≤ 0 := by omega
        have hmul_le : (wordD (parityWordOf r n) : Int) *
            (2 * (n : Int) - (iterateAccelerated n r : Int)) ≤
            (wordD (parityWordOf r n) : Int) * 0 :=
          Int.mul_le_mul_of_nonneg_left hle (by omega)
        omega
    · intro hlt
      have hge1 : 2 * (n : Int) - (iterateAccelerated n r : Int) ≥ 1 := by omega
      have hmul_ge : (wordD (parityWordOf r n) : Int) * 1 ≤
          (wordD (parityWordOf r n) : Int) *
            (2 * (n : Int) - (iterateAccelerated n r : Int)) :=
        Int.mul_le_mul_of_nonneg_left hge1 (by omega)
      omega
  · intro hband hle0
    by_cases hev : iterateAccelerated n r % 2 = 0
    · have hnot1 : ¬(iterateAccelerated n r % 2 = 1) := by omega
      have hb_false : (iterateAccelerated n r % 2 == 1) = false := by
        rw [beq_eq_false_iff_ne]; exact hnot1
      have hw_succ : parityWordOf (r + 1) n = parityWordOf r n ++ [false] := by
        rw [hsucc_eq, hb_false]
      rw [hw_succ, hstep] at hle0
      omega
    · omega

/-- Exact Coupling of the Signed Projective Gap with the Cumulative Deficit Reservoir
    (`signedProjectiveGap_reservoir_conservation`):
    Along any non-descending prefix (`∀ i ≤ r, iterateAccelerated n i ≥ n`),
    letting `w = parityWordOf r n` and `a = wordOnes w`:
    1. `signedProjectiveGap w n = - (orbitSurplus n r : Int) ≤ 0`, and
    2. `(deficitReservoir n r : Int) - ((n ^ a : Nat) : Int) * signedProjectiveGap w n +
          ((2 ^ r * n ^ (a + 1) : Nat) : Int) =
          ((n * (3 * n + 1) ^ a : Nat) : Int)`. -/
theorem signedProjectiveGap_reservoir_conservation (n r : Nat)
    (hge : ∀ i : Nat, i ≤ r → iterateAccelerated n i ≥ n) :
    let w := parityWordOf r n
    let a := wordOnes w
    signedProjectiveGap w n = - (orbitSurplus n r : Int) ∧
    signedProjectiveGap w n ≤ 0 ∧
    (deficitReservoir n r : Int) - ((n ^ a : Nat) : Int) * signedProjectiveGap w n +
      ((2 ^ r * n ^ (a + 1) : Nat) : Int) =
      ((n * (3 * n + 1) ^ a : Nat) : Int) := by
  dsimp
  have hv := parityWordOf_valid r n
  have hD : wordD (parityWordOf r n) = 2 ^ r := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hgap := signedProjectiveGap_eq_wordD_mul_sub (parityWordOf r n) n hv
  rw [hD, applyParityWord_parityWordOf] at hgap
  have hn_r : iterateAccelerated n r ≥ n := hge r (by omega)
  have hsurp_nat : orbitSurplus n r + 2 ^ r * n = 2 ^ r * iterateAccelerated n r := by
    unfold orbitSurplus
    rw [← Nat.mul_add, Nat.sub_add_cancel hn_r]
  have hsurp_int : (orbitSurplus n r : Int) + (2 ^ r : Nat) * (n : Int) =
      (2 ^ r : Nat) * (iterateAccelerated n r : Int) := by
    exact_mod_cast hsurp_nat
  have hgap_neg : signedProjectiveGap (parityWordOf r n) n = - (orbitSurplus n r : Int) := by
    rw [hgap, Int.mul_sub]
    omega
  have hcons := reservoir_plus_surplus_eq_power_gap n r hge
  dsimp at hcons
  have hcons_int : (deficitReservoir n r : Int) +
      (n : Int) ^ wordOnes (parityWordOf r n) * (orbitSurplus n r : Int) +
      (2 : Int) ^ r * (n : Int) ^ (wordOnes (parityWordOf r n) + 1) =
      (n : Int) * (3 * (n : Int) + 1) ^ wordOnes (parityWordOf r n) := by
    exact_mod_cast hcons
  have hmul_neg : (n : Int) ^ wordOnes (parityWordOf r n) *
      signedProjectiveGap (parityWordOf r n) n =
      - ((n : Int) ^ wordOnes (parityWordOf r n) * (orbitSurplus n r : Int)) := by
    rw [hgap_neg, Int.mul_neg]
  refine ⟨hgap_neg, by omega, by omega⟩

/-- Helper lemma: equality of list prefixes of equal length from equality of appends. -/
theorem list_eq_of_append_eq_of_length_eq :
    ∀ (u₁ u₂ v₁ v₂ : List Bool),
      u₁.length = u₂.length → u₁ ++ v₁ = u₂ ++ v₂ → u₁ = u₂
  | [], [], _, _, _, _ => rfl
  | _ :: _, [], _, _, hlen, _ => by dsimp at hlen; omega
  | [], _ :: _, _, _, hlen, _ => by dsimp at hlen; omega
  | b₁ :: bs₁, b₂ :: bs₂, v₁, v₂, hlen, happ => by
    dsimp at hlen happ
    injection happ with hb hbs
    rw [hb, list_eq_of_append_eq_of_length_eq bs₁ bs₂ v₁ v₂ (by omega) hbs]

/-- Membership in the depth-`r` surviving prefix-non-descending residue lift set `𝓢_r(n)`:
    `m ≡ n (mod 2^r)` and `F^i(m) ≥ m` for all `0 ≤ i ≤ r`. -/
def InSurvivingLiftSet (n r m : Nat) : Prop :=
  m % (2 ^ r) = n % (2 ^ r) ∧ ∀ i : Nat, i ≤ r → iterateAccelerated m i ≥ m

/-- Any two integers `m ≡ n (mod 2^r)` share the exact same parity word prefix
    `parityWordOf i m = parityWordOf i n` and residue `m % 2^i = n % 2^i` for all `i ≤ r`. -/
theorem mod_pow_two_eq_implies_shared_parityWord_prefix (n r m : Nat)
    (hmod : m % (2 ^ r) = n % (2 ^ r)) :
    ∀ i : Nat, i ≤ r →
      parityWordOf i m = parityWordOf i n ∧
      m % (2 ^ i) = n % (2 ^ i) := by
  have hD_r : wordD (parityWordOf r n) = 2 ^ r := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hn_res : n % wordD (parityWordOf r n) = wordResidue (parityWordOf r n) :=
    (validParityWord_iff_mod_eq_wordResidue (parityWordOf r n) n).mp (parityWordOf_valid r n)
  have hm_res : m % wordD (parityWordOf r n) = wordResidue (parityWordOf r n) := by
    rw [hD_r] at hn_res ⊢
    omega
  have hv_m : validParityWord m (parityWordOf r n) :=
    (validParityWord_iff_mod_eq_wordResidue (parityWordOf r n) m).mpr hm_res
  have hw_r : parityWordOf r m = parityWordOf r n := by
    have h := (validParityWord_iff_eq_parityWordOf (parityWordOf r n) m).mp hv_m
    rw [parityWordOf_length] at h
    exact h
  intro i hi
  have hr_split : r = i + (r - i) := by omega
  have happ_m := parityWordOf_add i (r - i) m
  have happ_n := parityWordOf_add i (r - i) n
  rw [← hr_split] at happ_m happ_n
  have heq_app : parityWordOf i m ++ parityWordOf (r - i) (iterateAccelerated m i) =
      parityWordOf i n ++ parityWordOf (r - i) (iterateAccelerated n i) := by
    rw [← happ_m, ← happ_n, hw_r]
  have hlen_eq : (parityWordOf i m).length = (parityWordOf i n).length := by
    rw [parityWordOf_length, parityWordOf_length]
  have hw_i : parityWordOf i m = parityWordOf i n :=
    list_eq_of_append_eq_of_length_eq _ _ _ _ hlen_eq heq_app
  have hD_i : wordD (parityWordOf i n) = 2 ^ i := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hn_i : n % wordD (parityWordOf i n) = wordResidue (parityWordOf i n) :=
    (validParityWord_iff_mod_eq_wordResidue (parityWordOf i n) n).mp (parityWordOf_valid i n)
  have hm_i : m % wordD (parityWordOf i n) = wordResidue (parityWordOf i n) := by
    have hvm_i : validParityWord m (parityWordOf i n) := by
      rw [← hw_i]
      exact parityWordOf_valid i m
    exact (validParityWord_iff_mod_eq_wordResidue (parityWordOf i n) m).mp hvm_i
  rw [hD_i] at hn_i hm_i
  exact ⟨hw_i, by omega⟩

/-- Nested Antitone Property of `𝓢_r(n)` (`survivingLiftSet_antitone`):
    Whenever `r₁ ≤ r₂`, `𝓢_{r₂}(n) ⊆ 𝓢_{r₁}(n)`. -/
theorem survivingLiftSet_antitone (n r₁ r₂ m : Nat)
    (hle : r₁ ≤ r₂) (hm : InSurvivingLiftSet n r₂ m) :
    InSurvivingLiftSet n r₁ m := by
  rcases hm with ⟨hmod, hge⟩
  have hshared := (mod_pow_two_eq_implies_shared_parityWord_prefix n r₂ m hmod r₁ hle).2
  exact ⟨hshared, fun i hi => hge i (by omega)⟩

/-- Surviving Lift Set Structural and Projective Fixed-Point Exclusion Theorem
    (`survivingLiftSet_intermediate_contracting_cap`):
    For any `m ∈ 𝓢_r(n)` with `m > 1`, at EVERY intermediate depth `i ≤ r`
    (letting `w_i = parityWordOf i n` and `a_i = wordOnes w_i`):
    1. `parityWordOf i m = w_i` and `signedProjectiveGap w_i m ≤ 0`,
    2. `deficitReservoir m i + m^{a_i} * wordB w_i + m * (3 * m)^{a_i} = m * (3 * m + 1)^{a_i}`,
    3. At every intermediate depth `1 ≤ i ≤ r` (even if `w_r` re-expands at depth `r`!),
       `wordDelta w_i * m ≤ wordB w_i`,
       `m^{a_i - 1} * wordB w_i ≤ a_i * (3 * m + 1)^{a_i - 1}`, and
       `wordDelta w_i * m^{a_i} ≤ a_i * (3 * m + 1)^{a_i - 1}`. -/
theorem survivingLiftSet_intermediate_contracting_cap (n r m : Nat)
    (hm1 : m > 1) (hm : InSurvivingLiftSet n r m) :
    ∀ i : Nat, i ≤ r →
      let w_i := parityWordOf i n
      let a_i := wordOnes w_i
      parityWordOf i m = w_i ∧
      signedProjectiveGap w_i m ≤ 0 ∧
      deficitReservoir m i + m ^ a_i * wordB w_i + m * (3 * m) ^ a_i =
        m * (3 * m + 1) ^ a_i ∧
      (i ≥ 1 →
        wordDelta w_i * m ≤ wordB w_i ∧
        m ^ (a_i - 1) * wordB w_i ≤ a_i * (3 * m + 1) ^ (a_i - 1) ∧
        wordDelta w_i * m ^ a_i ≤ a_i * (3 * m + 1) ^ (a_i - 1)) := by
  rcases hm with ⟨hmod, hge_m⟩
  intro i hi
  dsimp
  have hshared := (mod_pow_two_eq_implies_shared_parityWord_prefix n r m hmod i hi).1
  have hv_m : validParityWord m (parityWordOf i n) := by
    rw [← hshared]
    exact parityWordOf_valid i m
  have hge_mi : applyParityWord m (parityWordOf i n) ≥ m := by
    rw [← hshared, applyParityWord_parityWordOf]
    exact hge_m i hi
  have hgap_le : signedProjectiveGap (parityWordOf i n) m ≤ 0 :=
    (signedProjectiveGap_sign_trichotomy (parityWordOf i n) m hv_m).2.2.2.mpr hge_mi
  have hdual_m := (reservoir_offset_duality_identity m i (fun j hj => hge_m j (by omega))).2
  rw [hshared] at hdual_m
  refine ⟨hshared, hgap_le, hdual_m, ?_⟩
  intro hi1
  rcases universal_nondescent_offset_and_fixedPoint_bound m i hm1 hi1
    (fun j hj => hge_m j (by omega)) with ⟨_, _, hB_le, _, hdelta_na_le, _⟩
  rw [hshared] at hB_le hdelta_na_le
  have hdelta_m_le_B : wordDelta (parityWordOf i n) * m ≤ wordB (parityWordOf i n) := by
    by_cases hDA : wordD (parityWordOf i n) ≥ wordA (parityWordOf i n)
    · have hnd := (discrete_deficit_nondescent_identity (parityWordOf i n) m hv_m hDA hge_mi).1
      omega
    · unfold wordDelta
      have h0 : wordD (parityWordOf i n) - wordA (parityWordOf i n) = 0 := by omega
      rw [h0, Nat.zero_mul]
      omega
  exact ⟨hdelta_m_le_B, hB_le, hdelta_na_le⟩

/-- Equivalence of Universal Collatz Descent with Eventual Positive Signed Projective Gap
    and Empty Infinite Self-Survival in `𝓢_r(n)` (`collatz_iff_signedProjectiveGap_eventually_pos`):
    1. `(∀ n > 1, ∃ r ≥ 1, iterateAccelerated n r < n) ↔
        (∀ n > 1, ∃ r ≥ 1, signedProjectiveGap (parityWordOf r n) n > 0)`, and
    2. `(∀ n > 1, ∃ r ≥ 1, signedProjectiveGap (parityWordOf r n) n > 0) ↔
        ¬(∃ n > 1, ∀ r ≥ 1, InSurvivingLiftSet n r n)`. -/
theorem collatz_iff_signedProjectiveGap_eventually_pos :
    ((∀ n : Nat, n > 1 → ∃ r : Nat, r ≥ 1 ∧ iterateAccelerated n r < n) ↔
      (∀ n : Nat, n > 1 → ∃ r : Nat, r ≥ 1 ∧
        signedProjectiveGap (parityWordOf r n) n > 0)) ∧
    ((∀ n : Nat, n > 1 → ∃ r : Nat, r ≥ 1 ∧
        signedProjectiveGap (parityWordOf r n) n > 0) ↔
      ¬(∃ n : Nat, n > 1 ∧ ∀ r : Nat, r ≥ 1 → InSurvivingLiftSet n r n)) := by
  refine ⟨?_, ?_⟩
  · constructor
    · intro hdesc n hn1
      rcases hdesc n hn1 with ⟨r, hr1, hlt⟩
      refine ⟨r, hr1, ?_⟩
      have hv := parityWordOf_valid r n
      rw [(signedProjectiveGap_sign_trichotomy (parityWordOf r n) n hv).1,
          applyParityWord_parityWordOf]
      exact hlt
    · intro hgap n hn1
      rcases hgap n hn1 with ⟨r, hr1, hpos⟩
      refine ⟨r, hr1, ?_⟩
      have hv := parityWordOf_valid r n
      rw [← applyParityWord_parityWordOf r n]
      exact (signedProjectiveGap_sign_trichotomy (parityWordOf r n) n hv).1.mp hpos
  · constructor
    · intro hgap ⟨n, hn1, hsurv⟩
      rcases hgap n hn1 with ⟨r, hr1, hpos⟩
      have hv := parityWordOf_valid r n
      have hlt : iterateAccelerated n r < n := by
        rw [← applyParityWord_parityWordOf r n]
        exact (signedProjectiveGap_sign_trichotomy (parityWordOf r n) n hv).1.mp hpos
      have hge := (hsurv r hr1).2 r (by omega)
      omega
    · intro hno_surv n hn1
      by_cases hex : ∃ r : Nat, r ≥ 1 ∧ signedProjectiveGap (parityWordOf r n) n > 0
      · exact hex
      · exfalso
        apply hno_surv
        refine ⟨n, hn1, ?_⟩
        intro r hr1
        refine ⟨rfl, ?_⟩
        intro i hi
        cases i with
        | zero => dsimp [iterateAccelerated]; omega
        | succ i' =>
          by_cases hge : iterateAccelerated n (i' + 1) ≥ n
          · exact hge
          · exfalso
            apply hex
            refine ⟨i' + 1, by omega, ?_⟩
            have hv := parityWordOf_valid (i' + 1) n
            rw [(signedProjectiveGap_sign_trichotomy (parityWordOf (i' + 1) n) n hv).1,
                applyParityWord_parityWordOf]
            omega

/-! ## Section 8: Mechanism A — Self-Similar Orbit Shift, Delayed-Descent Surplus Elimination, and Finite Quotient Collapse of `𝓢_r(n)`

    Having established the surviving prefix-non-descending lift sets `𝓢_r(n)`, we now prove three
    structural elimination mechanisms that govern how subsequent refinements `r > i` eliminate
    surviving candidates after an intermediate depth `i`:
    1. **Exact Self-Similar Orbit Shift Identity (`surplus_div_pow_two_orbit_shift`)**:
       Whenever the surplus `s_i = F^i(n) - n` at depth `i` is divisible by `2^k` (`F^i(n) = n + q * 2^k`),
       the next `k` steps of `F^i(n)` follow the exact same parity word `w_k(n)` as `n` itself, with
       `F^{i+k}(n) = F^k(n) + q * 3^{a_k}`. Moreover, if `q` is odd (`2^k ∥ s_i`), then `F^{i+k}(n)` and
       `F^k(n)` have opposite parity (`F^{i+k}(n) % 2 ≠ F^k(n) % 2`), forcing a branch divergence at step `k + 1`.
    2. **1-Step and 2-Step Delayed Elimination of Small Surpluses (`small_surplus_delayed_descent_elimination`)**:
       For any `n > 1` surviving in `𝓢_r(n)` (`r ≥ 2`), let `s_i = F^i(n) - n`:
       - If `i + 1 ≤ r` and `s_i < n`, then `s_i` must be even (`s_i % 2 = 0`); any odd `s_i < n` forces
         immediate strict descent `F^{i+1}(n) = (n + s_i) / 2 < n` at depth `i + 1`.
       - If `i + 2 ≤ r` and `3 * s_i + 1 < n`, then `s_i` must be divisible by `4` (`s_i % 4 = 0`);
         any `s_i ≡ 2 (mod 4)` with `3 * s_i + 1 < n` forces strict descent
         `F^{i+2}(n) = (3n + 3 s_i + 1) / 4 < n` at depth `i + 2`.
       - Consequently, for any non-returning depth `i` (`s_i > 0`) with `i + 2 ≤ r` and `3 * s_i + 1 < n`,
         survival in `𝓢_r(n)` forces `s_i ≥ 4` (and at any first crossing `w_i ∈ 𝓜` with `a_i ≤ n`,
         `3 * s_i < a_i` forces `a_i ≥ 13`).
    3. **Finite Quotient Collapse and Lift-Bit Elimination (`survivingLiftSet_quotient_collapse_and_liftBit_lock`)**:
       Once a trajectory encounters a contracting prefix at depth `i ≥ 1` (`Δ_i = 2^i - 3^{a_i} ≥ 1`),
       every `m ∈ 𝓢_r(n)` (`r ≥ i`, `m > 1`) satisfies
       `Δ_i * wordResidue (w_r(n)) + (m / 2^r) * (Δ_i * 2^r) ≤ B_{w_i(n)}`.
       For all `r ≥ i` with `Δ_i * 2^r > B_{w_i(n)}`, every proper lift (`m / 2^r ≥ 1`) is unconditionally
       eliminated (`m = wordResidue (w_r(n))`), collapsing `𝓢_r(n) ∩ {m > 1}` to at most `{n}`; and any
       subsequent step with `liftBit = 1` violates the cap `B_{w_i(n)}` and empties `𝓢_{r+1}(n) ∩ {m > 1}`.
-/

/-- Helper lemma: `3^a` is odd for all `a : Nat`. -/
theorem pow_three_mod_two_eq_one (a : Nat) : (3 ^ a) % 2 = 1 := by
  induction a with
  | zero => rfl
  | succ a ih =>
    rw [Nat.pow_succ]
    omega

/-- Self-Similar Orbit Shift Identity (`surplus_div_pow_two_orbit_shift`):
    For any `n i k q : Nat`, if `iterateAccelerated n i = n + q * 2^k`
    (i.e. the depth-`i` surplus `s_i = F^i(n) - n` is `q * 2^k`), then:
    1. `parityWordOf k (iterateAccelerated n i) = parityWordOf k n`,
    2. `iterateAccelerated n (i + k) = iterateAccelerated n k + q * 3 ^ (wordOnes (parityWordOf k n))`, and
    3. Whenever `q` is odd (`q % 2 = 1`, so `2^k ∥ s_i`), `iterateAccelerated n (i + k)` and
       `iterateAccelerated n k` have opposite parity:
       `(iterateAccelerated n (i + k)) % 2 ≠ (iterateAccelerated n k) % 2`. -/
theorem surplus_div_pow_two_orbit_shift (n i k q : Nat)
    (hsurp : iterateAccelerated n i = n + q * 2 ^ k) :
    let w_k := parityWordOf k n
    let a_k := wordOnes w_k
    parityWordOf k (iterateAccelerated n i) = w_k ∧
    iterateAccelerated n (i + k) = iterateAccelerated n k + q * 3 ^ a_k ∧
    (q % 2 = 1 →
      (iterateAccelerated n (i + k)) % 2 ≠ (iterateAccelerated n k) % 2) := by
  dsimp
  have hv_n := parityWordOf_valid k n
  have hD_k : wordD (parityWordOf k n) = 2 ^ k := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hA_k : wordA (parityWordOf k n) = 3 ^ wordOnes (parityWordOf k n) :=
    wordA_eq_pow_three_wordOnes (parityWordOf k n)
  have hsurp_D : iterateAccelerated n i = n + q * wordD (parityWordOf k n) := by
    rw [hD_k]; exact hsurp
  rcases parityWord_residue_shift (parityWordOf k n) n q hv_n with ⟨hv_shift, hy_shift⟩
  rw [← hsurp_D] at hv_shift hy_shift
  have hw_eq : parityWordOf k (iterateAccelerated n i) = parityWordOf k n := by
    have h := (validParityWord_iff_eq_parityWordOf (parityWordOf k n) (iterateAccelerated n i)).mp hv_shift
    rw [parityWordOf_length] at h
    exact h
  have hit_add := iterateAccelerated_add n i k
  have hy_lhs : applyParityWord (iterateAccelerated n i) (parityWordOf k n) =
      iterateAccelerated n (i + k) := by
    rw [← hw_eq, applyParityWord_parityWordOf, hit_add]
  rw [hy_lhs, applyParityWord_parityWordOf, hA_k] at hy_shift
  refine ⟨hw_eq, hy_shift, ?_⟩
  intro hq_odd
  have h3_odd := pow_three_mod_two_eq_one (wordOnes (parityWordOf k n))
  have hprod_odd : (q * 3 ^ wordOnes (parityWordOf k n)) % 2 = 1 := by
    rw [Nat.mul_mod, hq_odd, h3_odd]
  rw [hy_shift]
  omega

/-- 1-Step and 2-Step Delayed-Descent Elimination of Small Surpluses
    (`small_surplus_delayed_descent_elimination`):
    Let `n > 1` survive in `𝓢_r(n)` (`r ≥ 2`), and for any intermediate depth `i ≤ r`,
    let `s = iterateAccelerated n i - n`:
    1. If `i + 1 ≤ r` and `s < n`, then `s % 2 = 0` (`s` cannot be odd),
    2. If `i + 2 ≤ r` and `3 * s + 1 < n`, then `s % 4 = 0` (`s ≡ 2 (mod 4)` is also eliminated),
    3. If `i + 2 ≤ r`, `s > 0` (non-returning at depth `i`), and `3 * s + 1 < n`, then `s ≥ 4`, and
    4. If `w_i = parityWordOf i n` is a first-crossing word (`IsFirstCrossing w_i`) with `i + 2 ≤ r`,
       `s > 0`, and `wordOnes w_i ≤ n`, then `wordOnes w_i ≥ 13`. -/
theorem small_surplus_delayed_descent_elimination (n r i : Nat)
    (hn1 : n > 1) (hr2 : r ≥ 2) (hi : i ≤ r)
    (hsurv : InSurvivingLiftSet n r n) :
    let s := iterateAccelerated n i - n
    (i + 1 ≤ r → s < n → s % 2 = 0) ∧
    (i + 2 ≤ r → 3 * s + 1 < n → s % 4 = 0) ∧
    (i + 2 ≤ r → s > 0 → 3 * s + 1 < n → s ≥ 4) ∧
    (IsFirstCrossing (parityWordOf i n) →
      i + 2 ≤ r → s > 0 → wordOnes (parityWordOf i n) < n →
      wordOnes (parityWordOf i n) ≥ 13) := by
  dsimp
  rcases hsurv with ⟨_, hge⟩
  have h1 : iterateAccelerated n 1 ≥ n := hge 1 (by omega)
  have h2 : iterateAccelerated n 2 ≥ n := hge 2 (by omega)
  rcases nondescent_depth2_forces_mod4_eq_3_and_reservoir n hn1 h1 h2 with ⟨hm4, _, _⟩
  have hn_odd : n % 2 = 1 := by omega
  have hge_i : iterateAccelerated n i ≥ n := hge i hi
  have hit_i : iterateAccelerated n i = n + (iterateAccelerated n i - n) := by omega
  have hev_elim : i + 1 ≤ r → iterateAccelerated n i - n < n →
      (iterateAccelerated n i - n) % 2 = 0 := by
    intro hi1 hs_lt
    by_cases hs_ev : (iterateAccelerated n i - n) % 2 = 0
    · exact hs_ev
    · exfalso
      have hy_ev : iterateAccelerated n i % 2 = 0 := by omega
      have hsucc := iterateAccelerated_succ_right n i
      unfold acceleratedCollatz at hsucc
      rw [if_pos hy_ev] at hsucc
      have hge_i1 := hge (i + 1) hi1
      omega
  have hmod4_elim : i + 2 ≤ r → 3 * (iterateAccelerated n i - n) + 1 < n →
      (iterateAccelerated n i - n) % 4 = 0 := by
    intro hi2 hs3_lt
    have hs_ev : (iterateAccelerated n i - n) % 2 = 0 :=
      hev_elim (by omega) (by omega)
    let q := (iterateAccelerated n i - n) / 2
    have hsurp_q : iterateAccelerated n i = n + q * 2 ^ 1 := by omega
    rcases surplus_div_pow_two_orbit_shift n i 1 q hsurp_q with ⟨_, hit_i1, hpar_flip⟩
    have hb0 : (n % 2 == 1) = true := by rw [beq_iff_eq]; exact hn_odd
    have hones1 : wordOnes (parityWordOf 1 n) = 1 := by
      dsimp [parityWordOf]; rw [hb0]; dsimp [wordOnes]
    have hit1_eq : iterateAccelerated n 1 = (3 * n + 1) / 2 := by
      dsimp [iterateAccelerated]
      unfold acceleratedCollatz
      have hnot0 : ¬(n % 2 = 0) := by omega
      rw [if_neg hnot0]
    have hit1_odd : iterateAccelerated n 1 % 2 = 1 := by omega
    by_cases hmod4 : (iterateAccelerated n i - n) % 4 = 0
    · exact hmod4
    · exfalso
      have hq_odd : q % 2 = 1 := by omega
      have hne_par := hpar_flip hq_odd
      have hit_i1_ev : iterateAccelerated n (i + 1) % 2 = 0 := by omega
      have hsucc2 := iterateAccelerated_succ_right n (i + 1)
      unfold acceleratedCollatz at hsucc2
      rw [if_pos hit_i1_ev] at hsucc2
      rw [hones1, Nat.pow_one] at hit_i1
      have hge_i2 := hge (i + 2) hi2
      have h2_eq : i + 1 + 1 = i + 2 := by omega
      rw [h2_eq] at hsucc2
      omega
  refine ⟨hev_elim, hmod4_elim, ?_, ?_⟩
  · intro hi2 hs_pos hs3_lt
    have hm4_0 := hmod4_elim hi2 hs3_lt
    omega
  · intro hfc hi2 hs_pos ha_le_n
    have hv_i := parityWordOf_valid i n
    have hge_i_ap : applyParityWord n (parityWordOf i n) ≥ n := by
      rw [applyParityWord_parityWordOf]
      exact hge_i
    have hpe : IsPrefixExpanding (parityWordOf i n) :=
      isFirstCrossing_implies_isPrefixExpanding (parityWordOf i n) hfc
    have hB : 3 * wordB (parityWordOf i n) ≤
        wordOnes (parityWordOf i n) * wordA (parityWordOf i n) :=
      three_mul_wordB_le_wordOnes_mul_wordA (parityWordOf i n) hpe
    have hband := firstCrossing_spectral_band (parityWordOf i n) hfc
    have hnd := (discrete_deficit_nondescent_identity (parityWordOf i n) n hv_i (by omega) hge_i_ap).1
    rw [applyParityWord_parityWordOf,
        Nat.mul_comm (wordD (parityWordOf i n)) (iterateAccelerated n i - n)] at hnd
    have hdelta_pos : wordDelta (parityWordOf i n) * n > 0 :=
      Nat.mul_pos hband.2.2.1 (by omega)
    have hA_le_D : wordOnes (parityWordOf i n) * wordA (parityWordOf i n) ≤
        wordOnes (parityWordOf i n) * wordD (parityWordOf i n) :=
      Nat.mul_le_mul_left (wordOnes (parityWordOf i n)) (by omega)
    have h3s_D : (3 * (iterateAccelerated n i - n)) * wordD (parityWordOf i n) <
        wordOnes (parityWordOf i n) * wordD (parityWordOf i n) := by
      rw [Nat.mul_assoc 3 _ (wordD (parityWordOf i n))]
      omega
    have hjump : 3 * (iterateAccelerated n i - n) < wordOnes (parityWordOf i n) :=
      Nat.lt_of_mul_lt_mul_right h3s_D
    have hs3_lt : 3 * (iterateAccelerated n i - n) + 1 < n := by omega
    have hm4_0 := hmod4_elim hi2 hs3_lt
    omega

/-- Finite Quotient Collapse and Lift-Bit Elimination Theorem
    (`survivingLiftSet_quotient_collapse_and_liftBit_lock`):
    Suppose `1 ≤ i ≤ r`, and let `w_i = parityWordOf i n` and `w_r = parityWordOf r n`:
    1. Every `m ∈ 𝓢_r(n)` with `m > 1` satisfies the quotient bound:
       `wordDelta w_i * wordResidue w_r + (m / 2^r) * (wordDelta w_i * 2^r) ≤ wordB w_i`,
    2. Whenever `wordDelta w_i * 2^r > wordB w_i`, every `m ∈ 𝓢_r(n)` with `m > 1` has `m / 2^r = 0`
       and `m = wordResidue w_r` (collapsing `𝓢_r(n) ∩ {m > 1}` to at most one element), and
    3. At step `r ↦ r + 1`, let `b = (iterateAccelerated n r % 2 == 1)`. Whenever
       `wordDelta w_i * (wordResidue w_r + 2^r) > wordB w_i` and `liftBit w_r b = 1`,
       `𝓢_{r+1}(n)` contains no integers `m > 1` (`∀ m > 1, ¬InSurvivingLiftSet n (r + 1) m`). -/
theorem survivingLiftSet_quotient_collapse_and_liftBit_lock (n i r : Nat)
    (hi1 : i ≥ 1) (hir : i ≤ r) :
    let w_i := parityWordOf i n
    let w_r := parityWordOf r n
    (∀ m : Nat, m > 1 → InSurvivingLiftSet n r m →
      wordDelta w_i * wordResidue w_r + (m / 2 ^ r) * (wordDelta w_i * 2 ^ r) ≤ wordB w_i) ∧
    (wordDelta w_i * 2 ^ r > wordB w_i →
      ∀ m : Nat, m > 1 → InSurvivingLiftSet n r m →
        m / 2 ^ r = 0 ∧ m = wordResidue w_r) ∧
    (let b := iterateAccelerated n r % 2 == 1
     wordDelta w_i * (wordResidue w_r + 2 ^ r) > wordB w_i →
     liftBit w_r b = 1 →
     ∀ m : Nat, m > 1 → ¬InSurvivingLiftSet n (r + 1) m) := by
  dsimp
  have hD_r : wordD (parityWordOf r n) = 2 ^ r := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  have hn_res_r : n % (2 ^ r) = wordResidue (parityWordOf r n) := by
    have h := (validParityWord_iff_mod_eq_wordResidue (parityWordOf r n) n).mp (parityWordOf_valid r n)
    rw [hD_r] at h
    exact h
  have hq_bound : ∀ m : Nat, m > 1 → InSurvivingLiftSet n r m →
      wordDelta (parityWordOf i n) * wordResidue (parityWordOf r n) +
        (m / 2 ^ r) * (wordDelta (parityWordOf i n) * 2 ^ r) ≤
        wordB (parityWordOf i n) := by
    intro m hm1 hm_surv
    have hcap := (survivingLiftSet_intermediate_contracting_cap n r m hm1 hm_surv i hir).2.2.2 hi1
    have hm_mod : m % (2 ^ r) = wordResidue (parityWordOf r n) := by
      rw [hm_surv.1, hn_res_r]
    have hm_div : m = wordResidue (parityWordOf r n) + (m / 2 ^ r) * 2 ^ r := by
      have h := Nat.mod_add_div m (2 ^ r)
      have hcomm : 2 ^ r * (m / 2 ^ r) = (m / 2 ^ r) * 2 ^ r := Nat.mul_comm _ _
      omega
    have hmul_eq : wordDelta (parityWordOf i n) * m =
        wordDelta (parityWordOf i n) * wordResidue (parityWordOf r n) +
          (m / 2 ^ r) * (wordDelta (parityWordOf i n) * 2 ^ r) := by
      conv => lhs; rw [hm_div]
      rw [Nat.mul_add, ← Nat.mul_assoc,
          Nat.mul_comm (wordDelta (parityWordOf i n)) (m / 2 ^ r),
          Nat.mul_assoc]
    omega
  refine ⟨hq_bound, ?_, ?_⟩
  · intro hgt_B m hm1 hm_surv
    have hb := hq_bound m hm1 hm_surv
    have hq0 : m / 2 ^ r = 0 := by
      cases hq : m / 2 ^ r with
      | zero => rfl
      | succ q' =>
        rw [hq] at hb
        have hge1 : (q' + 1) * (wordDelta (parityWordOf i n) * 2 ^ r) ≥
            1 * (wordDelta (parityWordOf i n) * 2 ^ r) :=
          Nat.mul_le_mul_right _ (by omega)
        omega
    have hm_mod : m % (2 ^ r) = wordResidue (parityWordOf r n) := by
      rw [hm_surv.1, hn_res_r]
    have hm_div := Nat.mod_add_div m (2 ^ r)
    rw [hm_mod, hq0, Nat.mul_zero, Nat.add_zero] at hm_div
    exact ⟨hq0, hm_div.symm⟩
  · intro hgt_lift hbit1 m hm1 hm_surv_succ
    have hcap := (survivingLiftSet_intermediate_contracting_cap n (r + 1) m hm1
      hm_surv_succ i (by omega)).2.2.2 hi1
    have hsucc_w := parityWordOf_succ_eq_append r n
    have hres_succ := (wordResidue_append_eq_add_liftBit (parityWordOf r n)
      (iterateAccelerated n r % 2 == 1)).2
    rw [← hsucc_w, hbit1, Nat.one_mul, hD_r] at hres_succ
    have hD_succ : wordD (parityWordOf (r + 1) n) = 2 ^ (r + 1) := by
      rw [wordD_eq_pow_two_length, parityWordOf_length]
    have hn_res_succ : n % (2 ^ (r + 1)) = wordResidue (parityWordOf (r + 1) n) := by
      have h := (validParityWord_iff_mod_eq_wordResidue (parityWordOf (r + 1) n) n).mp
        (parityWordOf_valid (r + 1) n)
      rw [hD_succ] at h
      exact h
    have hm_ge_res : m ≥ wordResidue (parityWordOf (r + 1) n) := by
      have hm_mod : m % (2 ^ (r + 1)) = wordResidue (parityWordOf (r + 1) n) := by
        rw [hm_surv_succ.1, hn_res_succ]
      have hle := Nat.mod_le m (2 ^ (r + 1))
      omega
    have hmul_ge : wordDelta (parityWordOf i n) * wordResidue (parityWordOf (r + 1) n) ≤
        wordDelta (parityWordOf i n) * m :=
      Nat.mul_le_mul_left _ hm_ge_res
    rw [hres_succ] at hmul_ge
    omega

/-! ## Section 9: Unified Trichotomy Reduction, Two-Point Temporal Self-Similarity, and Sharpened Cycle Obstructions

    We now organize the entire contradiction architecture around a hypothetical never-descending
    integer `n > 1` (`∀ r ≥ 0, T^r(n) ≥ n`), partitioning its possible long-time behavior into
    three cases:
    - **Case A (Bounded Recurrence)**: Infinitely many iterates (or `M - n + 2` iterates) lie in a
      bounded interval `[n, M]`, or a surplus `s = T^i(n) - n` recurs (`T^i(n) - n = T^j(n) - n` for `i < j`).
    - **Case B (Escape to Infinity / Strictly Injective Non-Descent)**: No two iterates coincide
      (`∀ i < j, T^i(n) ≠ T^j(n)`), and for every `M ≥ n`, at most `M - n + 1` iterates lie in `[n, M]`.
    - **Case C (Pure Nontrivial Cycle)**: A periodic minimum `m* > 1` with `T^p(m*) = m*` (`p ≥ 1`)
      and `∀ r ≥ 0, T^r(m*) ≥ m*`.

    In this section we prove unconditionally in Lean 4:
    1. **Two-Point Temporal Self-Similarity & 2-Adic Uniqueness (`two_point_orbit_shift_and_parity_divergence`)**:
       For any two iterates `T^i(n)` and `T^j(n)` with `T^j(n) = T^i(n) + q * 2^k`, they share the
       same `k`-step parity word, satisfy `T^{j+k}(n) = T^{i+k}(n) + q * 3^{a_k}`, and diverge onto
       opposite parity branches at step `k` whenever `q` is odd. Conversely, sharing a `k`-step parity
       word with `|T^j(n) - T^i(n)| < 2^k` forces `T^j(n) = T^i(n)`.
    2. **Unconditional Reduction of Case A (Bounded Recurrence) to Case C (Pure Cycle Minimum)
       (`recurrent_surplus_forces_pure_cycle_minimum`, `nat_pigeonhole_le`, `bounded_recurrence_reduces_to_pure_cycle`)**:
       Any orbit visiting `[n, M]` at `M - n + 2` distinct depths repeats a surplus by the constructive
       Pigeonhole Principle (`nat_pigeonhole_le`), which forces a periodic tail `T^{i+k}(n) = T^{j+k}(n)`
       and extracts a pure cycle minimum `m* ≥ n > 1` satisfying `T^p(m*) = m*` and `∀ r, T^r(m*) ≥ m*`.
    3. **Sharpened Case C Cycle Interior Excursion (`s_i ≥ 4`) and Exact Cycle Reservoir Identity
       (`cycle_interior_gap_ge_four_and_reservoir_identity`)**:
       Combining `descent_of_lt_1024` (`n ≥ 1024`) with `small_surplus_delayed_descent_elimination`
       proves that along ANY nontrivial cycle of minimal period `p ≥ 1`, EVERY interior iterate
       `1 ≤ i < p` must satisfy `T^i(n) ≥ n + 4` (ruling out `s_i ∈ {1, 2, 3}` globally!), while at
       the period `p`, `G_p(n) = 0`, `B_{w_p} = (2^p - 3^{a_p}) * n`, and
       `P_p(n) + 2^p * n^{a_p + 1} = n * (3 * n + 1)^{a_p}`.
    4. **Exact Two-Target Reduction of the Collatz Conjecture (`collatz_iff_no_pure_cycle_and_no_divergent_nondescent`)**:
       Because Case A reduces unconditionally to Case C, universal Collatz convergence is equivalent
       to the conjunction of Pure Cycle Exclusion (Case C) and Divergent Non-Descent Exclusion (Case B).
-/

/-- Two-Point Temporal Self-Similarity and 2-Adic Valuation Divergence
    (`two_point_orbit_shift_and_parity_divergence`):
    For any `n i j k q : Nat`:
    1. If `iterateAccelerated n j = iterateAccelerated n i + q * 2^k`, then:
       - `parityWordOf k (iterateAccelerated n j) = parityWordOf k (iterateAccelerated n i)`,
       - `iterateAccelerated n (j + k) = iterateAccelerated n (i + k) +
           q * 3 ^ (wordOnes (parityWordOf k (iterateAccelerated n i)))`, and
       - If `q % 2 = 1`, then `(iterateAccelerated n (j + k)) % 2 ≠ (iterateAccelerated n (i + k)) % 2`.
    2. Conversely, if `parityWordOf k (iterateAccelerated n j) = parityWordOf k (iterateAccelerated n i)`,
       `iterateAccelerated n i ≤ iterateAccelerated n j`, and
       `iterateAccelerated n j - iterateAccelerated n i < 2^k`, then
       `iterateAccelerated n j = iterateAccelerated n i`. -/
theorem two_point_orbit_shift_and_parity_divergence (n i j k q : Nat) :
    (iterateAccelerated n j = iterateAccelerated n i + q * 2 ^ k →
      let w_ik := parityWordOf k (iterateAccelerated n i)
      let a_ik := wordOnes w_ik
      parityWordOf k (iterateAccelerated n j) = w_ik ∧
      iterateAccelerated n (j + k) = iterateAccelerated n (i + k) + q * 3 ^ a_ik ∧
      (q % 2 = 1 →
        (iterateAccelerated n (j + k)) % 2 ≠ (iterateAccelerated n (i + k)) % 2)) ∧
    (parityWordOf k (iterateAccelerated n j) = parityWordOf k (iterateAccelerated n i) →
      iterateAccelerated n i ≤ iterateAccelerated n j →
      iterateAccelerated n j - iterateAccelerated n i < 2 ^ k →
      iterateAccelerated n j = iterateAccelerated n i) := by
  refine ⟨?_, ?_⟩
  · intro hshift
    dsimp
    have hv_i := parityWordOf_valid k (iterateAccelerated n i)
    have hD_k : wordD (parityWordOf k (iterateAccelerated n i)) = 2 ^ k := by
      rw [wordD_eq_pow_two_length, parityWordOf_length]
    have hA_k : wordA (parityWordOf k (iterateAccelerated n i)) =
        3 ^ wordOnes (parityWordOf k (iterateAccelerated n i)) :=
      wordA_eq_pow_three_wordOnes (parityWordOf k (iterateAccelerated n i))
    have hshift_D : iterateAccelerated n j =
        iterateAccelerated n i + q * wordD (parityWordOf k (iterateAccelerated n i)) := by
      rw [hD_k]; exact hshift
    rcases parityWord_residue_shift (parityWordOf k (iterateAccelerated n i))
      (iterateAccelerated n i) q hv_i with ⟨hv_j, hy_j⟩
    rw [← hshift_D] at hv_j hy_j
    have hw_eq : parityWordOf k (iterateAccelerated n j) =
        parityWordOf k (iterateAccelerated n i) := by
      have h := (validParityWord_iff_eq_parityWordOf
        (parityWordOf k (iterateAccelerated n i)) (iterateAccelerated n j)).mp hv_j
      rw [parityWordOf_length] at h
      exact h
    have hy_lhs : applyParityWord (iterateAccelerated n j)
        (parityWordOf k (iterateAccelerated n i)) = iterateAccelerated n (j + k) := by
      rw [← hw_eq, applyParityWord_parityWordOf, ← iterateAccelerated_add n j k]
    have hy_rhs : applyParityWord (iterateAccelerated n i)
        (parityWordOf k (iterateAccelerated n i)) = iterateAccelerated n (i + k) := by
      rw [applyParityWord_parityWordOf, ← iterateAccelerated_add n i k]
    rw [hy_lhs, hy_rhs, hA_k] at hy_j
    refine ⟨hw_eq, hy_j, ?_⟩
    intro hq_odd
    have h3_odd := pow_three_mod_two_eq_one
      (wordOnes (parityWordOf k (iterateAccelerated n i)))
    have hprod_odd : (q * 3 ^ wordOnes (parityWordOf k (iterateAccelerated n i))) % 2 = 1 := by
      rw [Nat.mul_mod, hq_odd, h3_odd]
    rw [hy_j]
    omega
  · intro hw_eq hle hlt_pow
    have hv_i := parityWordOf_valid k (iterateAccelerated n i)
    have hv_j : validParityWord (iterateAccelerated n j)
        (parityWordOf k (iterateAccelerated n i)) := by
      rw [← hw_eq]
      exact parityWordOf_valid k (iterateAccelerated n j)
    have hmod0 := validParityWord_sub_mod_wordD_eq_zero
      (parityWordOf k (iterateAccelerated n i))
      (iterateAccelerated n i) (iterateAccelerated n j) hv_i hv_j hle
    have hD_k : wordD (parityWordOf k (iterateAccelerated n i)) = 2 ^ k := by
      rw [wordD_eq_pow_two_length, parityWordOf_length]
    rw [hD_k, Nat.mod_eq_of_lt hlt_pow] at hmod0
    omega

/-- Helper lemma: periodicity of `iterateAccelerated x₀` across multiples of period `p`. -/
theorem iterateAccelerated_add_mul_period (x₀ p : Nat)
    (hper : iterateAccelerated x₀ p = x₀) :
    ∀ (a q : Nat), iterateAccelerated x₀ (a + p * q) = iterateAccelerated x₀ a := by
  intro a q
  induction q with
  | zero =>
    rw [Nat.mul_zero, Nat.add_zero]
  | succ q ih =>
    have h1 : a + p * (q + 1) = p + (a + p * q) := by
      rw [Nat.mul_add, Nat.mul_one]
      omega
    rw [h1, iterateAccelerated_add x₀ p (a + p * q), hper, ih]

/-- Helper lemma: every non-empty prefix `0 ≤ t < p` (`p ≥ 1`) of `f : Nat → Nat` attains a minimum. -/
theorem exists_min_on_prefix (f : Nat → Nat) :
    ∀ p : Nat, p ≥ 1 → ∃ t_min : Nat, t_min < p ∧ ∀ t : Nat, t < p → f t_min ≤ f t
  | 0, hp => by omega
  | 1, _ => ⟨0, by omega, fun t ht => by
      have heq : t = 0 := by omega
      rw [heq]
      omega⟩
  | p' + 2, _ => by
    rcases exists_min_on_prefix f (p' + 1) (by omega) with ⟨t₀, ht₀_lt, ht₀_min⟩
    by_cases hle : f t₀ ≤ f (p' + 1)
    · refine ⟨t₀, by omega, ?_⟩
      intro t ht
      by_cases hlt : t < p' + 1
      · exact ht₀_min t hlt
      · have heq : t = p' + 1 := by omega
        rw [heq]
        exact hle
    · refine ⟨p' + 1, by omega, ?_⟩
      intro t ht
      by_cases hlt : t < p' + 1
      · have h0 := ht₀_min t hlt
        omega
      · have heq : t = p' + 1 := by omega
        rw [heq]
        omega

/-- Recurrent Surplus Forces a Pure Cycle Minimum (`recurrent_surplus_forces_pure_cycle_minimum`):
    If a never-descending orbit of `n > 1` (`∀ r, iterateAccelerated n r ≥ n`) has a recurring
    surplus `iterateAccelerated n i - n = iterateAccelerated n j - n` at two depths `i < j`,
    then letting `p = j - i ≥ 1`:
    1. `iterateAccelerated n i = iterateAccelerated n j`,
    2. For all `k ≥ 0`, `iterateAccelerated n (i + k) = iterateAccelerated n (j + k)`, and
    3. There exists a cycle minimum `m* = iterateAccelerated n (i + t*)` (`t* < p`) such that
       `m* ≥ n > 1`, `iterateAccelerated m* p = m*`, and `∀ r : Nat, iterateAccelerated m* r ≥ m*`. -/
theorem recurrent_surplus_forces_pure_cycle_minimum (n i j : Nat)
    (hn1 : n > 1) (hij : i < j)
    (hnever_desc : ∀ r : Nat, iterateAccelerated n r ≥ n)
    (hsurp_eq : iterateAccelerated n i - n = iterateAccelerated n j - n) :
    let p := j - i
    p ≥ 1 ∧
    iterateAccelerated n i = iterateAccelerated n j ∧
    (∀ k : Nat, iterateAccelerated n (i + k) = iterateAccelerated n (j + k)) ∧
    (∃ m_star : Nat,
      m_star ≥ n ∧
      m_star > 1 ∧
      iterateAccelerated m_star p = m_star ∧
      ∀ r : Nat, iterateAccelerated m_star r ≥ m_star) := by
  dsimp
  have hge_i := hnever_desc i
  have hge_j := hnever_desc j
  have heq_ij : iterateAccelerated n i = iterateAccelerated n j := by omega
  have hp_pos : j - i ≥ 1 := by omega
  have hj_eq : j = i + (j - i) := by omega
  have hper_x0 : iterateAccelerated (iterateAccelerated n i) (j - i) =
      iterateAccelerated n i := by
    rw [← iterateAccelerated_add n i (j - i), ← hj_eq, heq_ij]
  have htail : ∀ k : Nat, iterateAccelerated n (i + k) = iterateAccelerated n (j + k) := by
    intro k
    rw [iterateAccelerated_add n i k, iterateAccelerated_add n j k, heq_ij]
  rcases exists_min_on_prefix (fun t => iterateAccelerated (iterateAccelerated n i) t)
    (j - i) hp_pos with ⟨t_star, ht_lt, ht_min⟩
  let m_star := iterateAccelerated (iterateAccelerated n i) t_star
  have hm_eq : m_star = iterateAccelerated n (i + t_star) := by
    unfold m_star
    rw [← iterateAccelerated_add n i t_star]
  have hm_ge_n : m_star ≥ n := by
    rw [hm_eq]
    exact hnever_desc (i + t_star)
  have hm_per : iterateAccelerated m_star (j - i) = m_star := by
    unfold m_star
    rw [← iterateAccelerated_add (iterateAccelerated n i) t_star (j - i)]
    have hmul1 : t_star + (j - i) = t_star + (j - i) * 1 := by omega
    rw [hmul1]
    exact iterateAccelerated_add_mul_period (iterateAccelerated n i) (j - i) hper_x0 t_star 1
  have hm_min_all : ∀ r : Nat, iterateAccelerated m_star r ≥ m_star := by
    intro r
    unfold m_star
    rw [← iterateAccelerated_add (iterateAccelerated n i) t_star r]
    have hdiv := (Nat.mod_add_div (t_star + r) (j - i)).symm
    have hper_div := iterateAccelerated_add_mul_period
      (iterateAccelerated n i) (j - i) hper_x0
      ((t_star + r) % (j - i)) ((t_star + r) / (j - i))
    rw [← hdiv] at hper_div
    rw [hper_div]
    have hmod_lt : (t_star + r) % (j - i) < j - i := Nat.mod_lt _ (by omega)
    exact ht_min ((t_star + r) % (j - i)) hmod_lt
  exact ⟨hp_pos, heq_ij, htail, ⟨m_star, hm_ge_n, by omega, hm_per, hm_min_all⟩⟩

/-- Helper lemma: decidable bounded search on `0 ≤ t ≤ K` for `f t = v`. -/
theorem exists_le_eq_or_forall_ne (f : Nat → Nat) (v : Nat) :
    ∀ K : Nat, (∃ t : Nat, t ≤ K ∧ f t = v) ∨ (∀ t : Nat, t ≤ K → f t ≠ v)
  | 0 => by
    by_cases h0 : f 0 = v
    · exact Or.inl ⟨0, by omega, h0⟩
    · exact Or.inr (fun t ht => by
        have heq : t = 0 := by omega
        rw [heq]
        exact h0)
  | K + 1 => by
    rcases exists_le_eq_or_forall_ne f v K with ⟨t, ht, hft⟩ | hall
    · exact Or.inl ⟨t, by omega, hft⟩
    · by_cases hK1 : f (K + 1) = v
      · exact Or.inl ⟨K + 1, by omega, hK1⟩
      · refine Or.inr (fun t ht => ?_)
        by_cases hle : t ≤ K
        · exact hall t hle
        · have heq : t = K + 1 := by omega
          rw [heq]
          exact hK1

/-- Constructive Finite Pigeonhole Principle (`nat_pigeonhole_le`):
    For every `K : Nat` and `f : Nat → Nat`, if `∀ t ≤ K + 1, f t ≤ K`
    (`K + 2` values in `{0, 1, ..., K}`), then there exist `t₁ < t₂ ≤ K + 1` with `f t₁ = f t₂`. -/
theorem nat_pigeonhole_le :
    ∀ (K : Nat) (f : Nat → Nat),
      (∀ t : Nat, t ≤ K + 1 → f t ≤ K) →
      ∃ t₁ t₂ : Nat, t₁ < t₂ ∧ t₂ ≤ K + 1 ∧ f t₁ = f t₂
  | 0, f, hbound => by
    have h0 := hbound 0 (by omega)
    have h1 := hbound 1 (by omega)
    exact ⟨0, 1, by omega, by omega, by omega⟩
  | K + 1, f, hbound => by
    rcases exists_le_eq_or_forall_ne f (f (K + 2)) (K + 1) with ⟨t, ht, hft⟩ | hall_ne
    · exact ⟨t, K + 2, by omega, by omega, hft⟩
    · let g : Nat → Nat := fun t => if f t < f (K + 2) then f t else f t - 1
      have hg_bound : ∀ t : Nat, t ≤ K + 1 → g t ≤ K := by
        intro t ht
        have hft_le := hbound t (by omega)
        have hfK2_le := hbound (K + 2) (by omega)
        have hne := hall_ne t ht
        dsimp [g]
        by_cases hlt : f t < f (K + 2)
        · rw [if_pos hlt]; omega
        · rw [if_neg hlt]; omega
      rcases nat_pigeonhole_le K g hg_bound with ⟨t₁, t₂, hlt12, ht2_le, hg_eq⟩
      refine ⟨t₁, t₂, hlt12, by omega, ?_⟩
      have hne1 := hall_ne t₁ (by omega)
      have hne2 := hall_ne t₂ ht2_le
      dsimp [g] at hg_eq
      by_cases h1 : f t₁ < f (K + 2) <;> by_cases h2 : f t₂ < f (K + 2)
      · rw [if_pos h1, if_pos h2] at hg_eq; exact hg_eq
      · rw [if_pos h1, if_neg h2] at hg_eq; omega
      · rw [if_neg h1, if_pos h2] at hg_eq; omega
      · rw [if_neg h1, if_neg h2] at hg_eq; omega

/-- Unconditional Reduction of Case A (Bounded Recurrence) to Case C (Pure Cycle Minimum)
    (`bounded_recurrence_reduces_to_pure_cycle`):
    Suppose `n > 1` is never-descending (`∀ r, iterateAccelerated n r ≥ n`), and there exists a
    bound `M ≥ n` and a strictly increasing sequence of depths `depthSeq : Nat → Nat`
    (`∀ t₁ < t₂, depthSeq t₁ < depthSeq t₂`) such that `iterateAccelerated n (depthSeq t) ≤ M`
    for all `0 ≤ t ≤ M - n + 1`. Then:
    1. There exist `t₁ < t₂ ≤ M - n + 1` with `iterateAccelerated n (depthSeq t₁) = iterateAccelerated n (depthSeq t₂)`, and
    2. There exists a pure cycle minimum `m* ≥ n > 1` and period `p = depthSeq t₂ - depthSeq t₁ ≥ 1`
       such that `iterateAccelerated m* p = m*` and `∀ r : Nat, iterateAccelerated m* r ≥ m*`. -/
theorem bounded_recurrence_reduces_to_pure_cycle (n M : Nat) (depthSeq : Nat → Nat)
    (hn1 : n > 1)
    (hnever_desc : ∀ r : Nat, iterateAccelerated n r ≥ n)
    (hmono : ∀ t₁ t₂ : Nat, t₁ < t₂ → depthSeq t₁ < depthSeq t₂)
    (hbounded : ∀ t : Nat, t ≤ M - n + 1 → iterateAccelerated n (depthSeq t) ≤ M) :
    (∃ t₁ t₂ : Nat,
      t₁ < t₂ ∧ t₂ ≤ M - n + 1 ∧
      iterateAccelerated n (depthSeq t₁) = iterateAccelerated n (depthSeq t₂)) ∧
    (∃ m_star p : Nat,
      p ≥ 1 ∧ m_star ≥ n ∧ m_star > 1 ∧
      iterateAccelerated m_star p = m_star ∧
      ∀ r : Nat, iterateAccelerated m_star r ≥ m_star) := by
  let f : Nat → Nat := fun t => iterateAccelerated n (depthSeq t) - n
  have hf_bound : ∀ t : Nat, t ≤ M - n + 1 → f t ≤ M - n := by
    intro t ht
    have hle := hbounded t ht
    dsimp [f]
    omega
  rcases nat_pigeonhole_le (M - n) f hf_bound with ⟨t₁, t₂, hlt12, ht2_le, hf_eq⟩
  dsimp [f] at hf_eq
  have hge1 := hnever_desc (depthSeq t₁)
  have hge2 := hnever_desc (depthSeq t₂)
  have hit_eq : iterateAccelerated n (depthSeq t₁) = iterateAccelerated n (depthSeq t₂) := by
    omega
  have hr_lt : depthSeq t₁ < depthSeq t₂ := hmono t₁ t₂ hlt12
  rcases recurrent_surplus_forces_pure_cycle_minimum n (depthSeq t₁) (depthSeq t₂)
    hn1 hr_lt hnever_desc hf_eq with ⟨hp_pos, _, _, ⟨m_star, hm_ge, hm1, hm_per, hm_min⟩⟩
  exact ⟨⟨t₁, t₂, hlt12, ht2_le, hit_eq⟩,
    ⟨m_star, depthSeq t₂ - depthSeq t₁, hp_pos, hm_ge, hm1, hm_per, hm_min⟩⟩

/-- Sharpened Case C Cycle Interior Excursion (`s_i ≥ 4`) and Exact Cycle Reservoir Identity
    (`cycle_interior_gap_ge_four_and_reservoir_identity`):
    Suppose `n > 1` is the strict minimum element of a nontrivial cycle of minimal period `p ≥ 1`
    (`∀ i, 1 ≤ i → i < p → iterateAccelerated n i > n` and `iterateAccelerated n p = n`).
    Let `w_p = parityWordOf p n` and `a_p = wordOnes w_p`. Then:
    1. `n ≥ 1024` and `p ≥ 65`,
    2. For EVERY interior step `1 ≤ i < p`, the surplus `s_i = iterateAccelerated n i - n` satisfies
       `s_i ≥ 4` (i.e. `iterateAccelerated n i ≥ n + 4`), `(s_i < n → s_i % 2 = 0)`, and
       `(3 * s_i + 1 < n → s_i % 4 = 0)`,
    3. At the period `p`, `signedProjectiveGap w_p n = 0`, `wordDelta w_p * n = wordB w_p`,
       `wordB w_p % n = 0`, and
    4. Exact Cycle Reservoir Identity:
       `deficitReservoir n p + 2 ^ p * n ^ (a_p + 1) = n * (3 * n + 1) ^ a_p`. -/
theorem cycle_interior_gap_ge_four_and_reservoir_identity (n p : Nat)
    (hn1 : n > 1) (hp1 : p ≥ 1)
    (hstrict : ∀ i : Nat, 1 ≤ i → i < p → iterateAccelerated n i > n)
    (hcycle : iterateAccelerated n p = n) :
    let w_p := parityWordOf p n
    let a_p := wordOnes w_p
    n ≥ 1024 ∧
    p ≥ 65 ∧
    (∀ i : Nat, 1 ≤ i → i < p →
      let s_i := iterateAccelerated n i - n
      s_i ≥ 4 ∧
      (s_i < n → s_i % 2 = 0) ∧
      (3 * s_i + 1 < n → s_i % 4 = 0)) ∧
    signedProjectiveGap w_p n = 0 ∧
    wordDelta w_p * n = wordB w_p ∧
    wordB w_p % n = 0 ∧
    deficitReservoir n p + 2 ^ p * n ^ (a_p + 1) = n * (3 * n + 1) ^ a_p := by
  dsimp
  have hmin : ∀ r : Nat, iterateAccelerated n r ≥ n := by
    intro r
    have hdiv := (Nat.mod_add_div r p).symm
    have hper := iterateAccelerated_add_mul_period n p hcycle (r % p) (r / p)
    rw [← hdiv] at hper
    rw [hper]
    have hmod_lt : r % p < p := Nat.mod_lt r hp1
    cases hrem : r % p with
    | zero => dsimp [iterateAccelerated]; omega
    | succ i' =>
      rw [hrem] at hmod_lt
      have hgt := hstrict (i' + 1) (by omega) hmod_lt
      omega
  have hn_1024 : n ≥ 1024 := by
    by_cases hlt : n < 1024
    · rcases descent_of_lt_1024 n hn1 hlt with ⟨k, _, hk_lt⟩
      have hge_k := hmin k
      omega
    · omega
  have hp_65 : p ≥ 65 := by
    by_cases hle64 : p ≤ 64
    · exact False.elim (no_nontrivial_cycle_length_le_64 n p hn1 hp1 hle64 hmin hcycle)
    · omega
  have hint : ∀ i : Nat, 1 ≤ i → i < p →
      let s_i := iterateAccelerated n i - n
      s_i ≥ 4 ∧
      (s_i < n → s_i % 2 = 0) ∧
      (3 * s_i + 1 < n → s_i % 4 = 0) := by
    intro i hi1 hip
    dsimp
    have hsurv : InSurvivingLiftSet n (i + 2) n := ⟨rfl, fun j _ => hmin j⟩
    rcases small_surplus_delayed_descent_elimination n (i + 2) i hn1 (by omega) (by omega) hsurv with
      ⟨hev, hmod4, hs4, _⟩
    have hgt_i : iterateAccelerated n i > n := hstrict i hi1 hip
    have hs_ge4 : iterateAccelerated n i - n ≥ 4 := by
      by_cases hlt4 : iterateAccelerated n i - n < 4
      · have hs3_lt : 3 * (iterateAccelerated n i - n) + 1 < n := by omega
        exact hs4 (by omega) (by omega) hs3_lt
      · omega
    exact ⟨hs_ge4, hev (by omega), hmod4 (by omega)⟩
  have hv_p := parityWordOf_valid p n
  have hgap0 : signedProjectiveGap (parityWordOf p n) n = 0 := by
    rw [(signedProjectiveGap_sign_trichotomy (parityWordOf p n) n hv_p).2.1,
        applyParityWord_parityWordOf]
    exact hcycle
  rcases universal_cycle_minimum_element_bound n p n hn1 hp1 (by omega) (by omega)
    (fun i _ => hmin i) hcycle with ⟨_, hcont, _, _⟩
  have hDA : wordD (parityWordOf p n) ≥ wordA (parityWordOf p n) := by
    rw [wordD_eq_pow_two_length, parityWordOf_length, wordA_eq_pow_three_wordOnes]
    omega
  have hge_p_ap : applyParityWord n (parityWordOf p n) ≥ n := by
    rw [applyParityWord_parityWordOf, hcycle]
    omega
  have hnd := (discrete_deficit_nondescent_identity (parityWordOf p n) n hv_p hDA hge_p_ap).1
  rw [applyParityWord_parityWordOf, hcycle, Nat.sub_self, Nat.mul_zero, Nat.add_zero] at hnd
  have hB_mod : wordB (parityWordOf p n) % n = 0 := by
    rw [hnd, Nat.mul_mod_left]
  have hcons := reservoir_plus_surplus_eq_power_gap n p (fun i _ => hmin i)
  dsimp at hcons
  have hsurp0 : orbitSurplus n p = 0 := by
    unfold orbitSurplus
    rw [hcycle, Nat.sub_self, Nat.mul_zero]
  rw [hsurp0, Nat.mul_zero, Nat.add_zero] at hcons
  exact ⟨hn_1024, hp_65, hint, hgap0, hnd.symm, hB_mod, hcons⟩

/-- Unified Two-Target Contradiction Theorem (`collatz_iff_no_pure_cycle_and_no_divergent_nondescent`):
    Because Case A (bounded recurrence) reduces unconditionally to Case C (pure cycle minimum),
    universal Collatz convergence (`CollatzConjecture`) is equivalent to the conjunction of:
    1. **Pure Cycle Exclusion (Case C)**:
       `¬(∃ m > 1, ∃ p ≥ 1, iterateAccelerated m p = m ∧ ∀ r, iterateAccelerated m r ≥ m)`, and
    2. **Injective / Divergent Non-Descent Exclusion (Case B)**:
       `¬(∃ n > 1, (∀ r, iterateAccelerated n r ≥ n) ∧ (∀ i j, i < j → iterateAccelerated n i ≠ iterateAccelerated n j))`. -/
theorem collatz_iff_no_pure_cycle_and_no_divergent_nondescent :
    CollatzConjecture ↔
      (¬(∃ m p : Nat, m > 1 ∧ p ≥ 1 ∧
          iterateAccelerated m p = m ∧ ∀ r : Nat, iterateAccelerated m r ≥ m) ∧
       ¬(∃ n : Nat, n > 1 ∧
          (∀ r : Nat, iterateAccelerated n r ≥ n) ∧
          (∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j))) := by
  constructor
  · intro hcollatz
    have hdesc : ∀ n : Nat, n > 1 → ∃ k : Nat, k > 0 ∧ iterateAccelerated n k < n :=
      universalAcceleratedDescent_iff_collatz.mpr hcollatz
    refine ⟨?_, ?_⟩
    · rintro ⟨m, p, hm1, _, _, hm_min⟩
      rcases hdesc m hm1 with ⟨k, _, hk_lt⟩
      have hge := hm_min k
      omega
    · rintro ⟨n, hn1, hn_min, _⟩
      rcases hdesc n hn1 with ⟨k, _, hk_lt⟩
      have hge := hn_min k
      omega
  · rintro ⟨hno_cycle, hno_div⟩
    apply universalAcceleratedDescent_iff_collatz.mp
    intro n hn1
    by_cases hex : ∃ k : Nat, k > 0 ∧ iterateAccelerated n k < n
    · exact hex
    · exfalso
      have hnever_desc : ∀ r : Nat, iterateAccelerated n r ≥ n := by
        intro r
        cases r with
        | zero => dsimp [iterateAccelerated]; omega
        | succ r' =>
          by_cases hge : iterateAccelerated n (r' + 1) ≥ n
          · exact hge
          · exfalso
            exact hex ⟨r' + 1, by omega, by omega⟩
      have hinj : ∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j := by
        intro i j hij heq_ij
        have hsurp : iterateAccelerated n i - n = iterateAccelerated n j - n := by
          rw [heq_ij]
        rcases recurrent_surplus_forces_pure_cycle_minimum n i j hn1 hij hnever_desc hsurp with
          ⟨hp_pos, _, _, ⟨m_star, _, hm1, hm_per, hm_min⟩⟩
        exact hno_cycle ⟨m_star, j - i, hm1, hp_pos, hm_per, hm_min⟩
      exact hno_div ⟨n, hn1, hnever_desc, hinj⟩

/-! ## Section 10: Exact Divergence Characterization (`DivergentOrbit`), Two-Target Reduction (`NoNontrivialCycle ∧ NoDivergentOrbit`), and Valuation-Block Asymptotics

    Strengthens the Section 9 decomposition into the exact two-branch proof target:
    1. **Divergence to Infinity (`DivergentOrbit n`)**:
       `∀ M : Nat, ∃ R : Nat, ∀ r : Nat, r ≥ R → iterateAccelerated n r > M` (`lim_{r → ∞} T^r(n) = +∞`).
       We prove unconditionally (`divergentOrbit_iff_injective`) that for every `n : Nat`,
       `DivergentOrbit n ↔ (∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j)`.
       Furthermore (`divergentOrbit_attains_global_nondescent_minimum`), every divergent orbit of `n > 1`
       attains a global minimum `n* = iterateAccelerated n r* > 1` (`n* ≤ n`) that is simultaneously
       never-descending (`∀ r, iterateAccelerated n* r ≥ n*`) and divergent (`DivergentOrbit n*`).
    2. **Exact Two-Target Structural Equivalence (`collatz_iff_noNontrivialCycle_and_noDivergentOrbit`)**:
       `CollatzConjecture ↔ (NoNontrivialCycle ∧ NoDivergentOrbit)`.
    3. **Divergent-Orbit Asymptotic Power & Projective-Gap Laws (`divergentOrbit_asymptotic_power_and_gap_laws`)**:
       For any never-descending `DivergentOrbit n` (`n > 1`), for every threshold `M ≥ n` and every `m : Nat`,
       there exists `R : Nat` such that for all `r ≥ R`:
       - `iterateAccelerated n r > M`,
       - `signedProjectiveGap (parityWordOf r n) n < -(Int.ofNat (2^r * (M - n)))`,
       - `2^r * n^{a_r} * (M + 1) ≤ n * (3 * n + 1)^{a_r}`, and
       - `2^{r + m} * n^{a_r} < (3 * n + 1)^{a_r}`.
    4. **Odd-to-Odd Return-Map Valuation Block Laws (`singleOddWord_step_dichotomy`,
       `returnMap_nondescent_valuation_and_gap_laws`)**:
       Every single odd-to-odd block `singleOddWord k` on `u > 1` strictly increases `u` when `k = 0`
       (`v_2(3u + 1) = 1`) and strictly decreases `u` whenever `k ≥ 1` (`v_2(3u + 1) ≥ 2`); and across any
       `s`-step valuation sequence `ks` of cumulative length `K = totalValuation ks`, non-descent locks `n`
       to `n % 2^K = wordResidue (returnMapWord ks)` and enforces
       `deficitReservoir n K + 2^K * n^s * F^K(n) = n * (3 * n + 1)^s` with `2^K * n^s ≤ (3 * n + 1)^s`.
-/

/-- An accelerated Collatz orbit of `n` diverges to infinity (`lim_{r → ∞} T^r(n) = +∞`)
    if for every bound `M : Nat`, there exists a threshold depth `R : Nat` such that
    `iterateAccelerated n r > M` for all `r ≥ R`. -/
def DivergentOrbit (n : Nat) : Prop :=
  ∀ M : Nat, ∃ R : Nat, ∀ r : Nat, r ≥ R → iterateAccelerated n r > M

/-- Track 1 Target (`NoNontrivialCycle`):
    No integer `m > 1` is the minimum element of a periodic orbit of period `p ≥ 1`. -/
def NoNontrivialCycle : Prop :=
  ¬(∃ m p : Nat, m > 1 ∧ p ≥ 1 ∧
      iterateAccelerated m p = m ∧ ∀ r : Nat, iterateAccelerated m r ≥ m)

/-- Track 2 Target (`NoDivergentOrbit`):
    No integer `n > 1` has an accelerated Collatz trajectory tending to `+∞`. -/
def NoDivergentOrbit : Prop :=
  ¬(∃ n : Nat, n > 1 ∧ DivergentOrbit n)

/-- Every divergent orbit is strictly injective (`∀ i < j, iterateAccelerated n i ≠ iterateAccelerated n j`). -/
theorem divergentOrbit_implies_injective (n : Nat) (hdiv : DivergentOrbit n) :
    ∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j := by
  intro i j hij heq
  let p := j - i
  have hp_pos : p ≥ 1 := by omega
  have hj_eq : j = i + p := by omega
  have hper : iterateAccelerated (iterateAccelerated n i) p = iterateAccelerated n i := by
    rw [← iterateAccelerated_add n i p, ← hj_eq, heq]
  rcases hdiv (iterateAccelerated n i) with ⟨R, hR⟩
  have hpR_ge : i + p * R ≥ R := by
    have hmul : 1 * R ≤ p * R := Nat.mul_le_mul_right R hp_pos
    omega
  have hgt := hR (i + p * R) hpR_ge
  have hrep : iterateAccelerated n (i + p * R) = iterateAccelerated n i := by
    rw [iterateAccelerated_add n i (p * R)]
    have h0 : p * R = 0 + p * R := by omega
    rw [h0, iterateAccelerated_add_mul_period (iterateAccelerated n i) p hper 0 R]
    rfl
  omega

/-- Constructive finite depth-sequence extraction: if an orbit visits `[0, M]` at arbitrarily
    large depths (`∀ R, ∃ r ≥ R, iterateAccelerated n r ≤ M`), then for every `K : Nat` there is
    a strictly increasing depth sequence `depthSeq` visiting `[0, M]` on `0 ≤ t ≤ K`. -/
theorem bounded_visit_sequence_of_frequently_le (n M : Nat)
    (hfreq : ∀ R : Nat, ∃ r : Nat, r ≥ R ∧ iterateAccelerated n r ≤ M) :
    ∀ K : Nat,
      ∃ depthSeq : Nat → Nat,
        (∀ t₁ t₂ : Nat, t₁ < t₂ → depthSeq t₁ < depthSeq t₂) ∧
        (∀ t : Nat, t ≤ K → iterateAccelerated n (depthSeq t) ≤ M)
  | 0 => by
    rcases hfreq 0 with ⟨r₀, _, hr₀_le⟩
    refine ⟨fun t => r₀ + t, fun t₁ t₂ hlt => by dsimp; omega, fun t ht => ?_⟩
    dsimp
    have heq : t = 0 := by omega
    rw [heq, Nat.add_zero]
    exact hr₀_le
  | K + 1 => by
    rcases bounded_visit_sequence_of_frequently_le n M hfreq K with ⟨seqK, hmonoK, hboundK⟩
    rcases hfreq (seqK K + 1) with ⟨r_next, hr_ge, hr_le⟩
    let seqNext : Nat → Nat := fun t =>
      if t ≤ K then seqK t else r_next + (t - (K + 1))
    refine ⟨seqNext, ?_, ?_⟩
    · intro t₁ t₂ hlt
      dsimp [seqNext]
      by_cases h1 : t₁ ≤ K <;> by_cases h2 : t₂ ≤ K
      · rw [if_pos h1, if_pos h2]
        exact hmonoK t₁ t₂ hlt
      · rw [if_pos h1, if_neg h2]
        have hleK : seqK t₁ ≤ seqK K := by
          by_cases heq : t₁ = K
          · rw [heq]
            omega
          · have hltK : t₁ < K := by omega
            have hlt_seq := hmonoK t₁ K hltK
            omega
        omega
      · omega
      · rw [if_neg h1, if_neg h2]
        omega
    · intro t ht
      dsimp [seqNext]
      by_cases hle : t ≤ K
      · rw [if_pos hle]
        exact hboundK t hle
      · rw [if_neg hle]
        have heq : t = K + 1 := by omega
        rw [heq, Nat.sub_self, Nat.add_zero]
        exact hr_le

/-- Exact Equivalence Between Orbit Divergence (`lim_{r → ∞} T^r(n) = +∞`) and Orbit Injectivity
    (`divergentOrbit_iff_injective`):
    For EVERY natural number `n : Nat`, `DivergentOrbit n` holds if and only if all iterates
    `iterateAccelerated n r` (`r ≥ 0`) are pairwise distinct. -/
theorem divergentOrbit_iff_injective (n : Nat) :
    DivergentOrbit n ↔
      (∀ i j : Nat, i < j → iterateAccelerated n i ≠ iterateAccelerated n j) := by
  constructor
  · exact divergentOrbit_implies_injective n
  · intro hinj M
    by_cases hex : ∃ R : Nat, ∀ r : Nat, r ≥ R → iterateAccelerated n r > M
    · exact hex
    · exfalso
      have hfreq : ∀ R : Nat, ∃ r : Nat, r ≥ R ∧ iterateAccelerated n r ≤ M := by
        intro R
        exact Classical.byContradiction fun hnot =>
          hex ⟨R, fun r hr => by
            by_cases hle : iterateAccelerated n r ≤ M
            · exact False.elim (hnot ⟨r, hr, hle⟩)
            · omega⟩
      rcases bounded_visit_sequence_of_frequently_le n M hfreq (M + 1) with
        ⟨depthSeq, hmono, hbound⟩
      rcases nat_pigeonhole_le M (fun t => iterateAccelerated n (depthSeq t)) hbound with
        ⟨t₁, t₂, hlt12, _, heq⟩
      exact hinj (depthSeq t₁) (depthSeq t₂) (hmono t₁ t₂ hlt12) heq

/-- Every divergent orbit of `n > 1` attains a global minimum `n* = iterateAccelerated n r* > 1`
    (`n* ≤ n`) whose tail is both never-descending (`∀ r, iterateAccelerated n* r ≥ n*`) and
    divergent (`DivergentOrbit n*`). -/
theorem divergentOrbit_attains_global_nondescent_minimum (n : Nat)
    (hn1 : n > 1) (hdiv : DivergentOrbit n) :
    ∃ r_star : Nat,
      let n_star := iterateAccelerated n r_star
      n_star > 1 ∧
      n_star ≤ n ∧
      (∀ r : Nat, iterateAccelerated n_star r ≥ n_star) ∧
      DivergentOrbit n_star := by
  have hinj := (divergentOrbit_iff_injective n).mp hdiv
  rcases hdiv n with ⟨R, hR⟩
  rcases exists_min_on_prefix (fun t => iterateAccelerated n t) (R + 1) (by omega) with
    ⟨r_star, _, hr_min⟩
  refine ⟨r_star, ?_⟩
  dsimp
  let n_star := iterateAccelerated n r_star
  have hn_star_le_n : n_star ≤ n := hr_min 0 (by omega)
  have hn_star_pos : n_star > 0 := iterateAccelerated_pos n r_star (by omega)
  have hn_star_ne1 : n_star ≠ 1 := by
    intro heq1
    have hstep2 : iterateAccelerated n (r_star + 2) = iterateAccelerated n_star 2 :=
      iterateAccelerated_add n r_star 2
    have h1_2 : iterateAccelerated 1 2 = 1 := by decide
    rw [heq1, h1_2] at hstep2
    exact hinj r_star (r_star + 2) (by omega) (by omega)
  have hn_star_gt1 : n_star > 1 := by omega
  have hn_star_min : ∀ r : Nat, iterateAccelerated n_star r ≥ n_star := by
    intro r
    have hadd : iterateAccelerated n (r_star + r) = iterateAccelerated n_star r :=
      iterateAccelerated_add n r_star r
    rw [← hadd]
    by_cases hlt : r_star + r < R + 1
    · exact hr_min (r_star + r) hlt
    · have hgt := hR (r_star + r) (by omega)
      omega
  have hn_star_div : DivergentOrbit n_star := by
    rw [divergentOrbit_iff_injective]
    intro i j hij heq_ij
    have hi : iterateAccelerated n (r_star + i) = iterateAccelerated n_star i :=
      iterateAccelerated_add n r_star i
    have hj : iterateAccelerated n (r_star + j) = iterateAccelerated n_star j :=
      iterateAccelerated_add n r_star j
    exact hinj (r_star + i) (r_star + j) (by omega) (by rw [hi, hj, heq_ij])
  exact ⟨hn_star_gt1, hn_star_le_n, hn_star_min, hn_star_div⟩

/-- Exact Two-Target Structural Equivalence (`collatz_iff_noNontrivialCycle_and_noDivergentOrbit`):
    `CollatzConjecture` holds if and only if both:
    1. `NoNontrivialCycle` (no minimum `m > 1` satisfies `T^p(m) = m` for `p ≥ 1`), and
    2. `NoDivergentOrbit` (no starting integer `n > 1` satisfies `lim_{r → ∞} T^r(n) = +∞`). -/
theorem collatz_iff_noNontrivialCycle_and_noDivergentOrbit :
    CollatzConjecture ↔ (NoNontrivialCycle ∧ NoDivergentOrbit) := by
  rw [collatz_iff_no_pure_cycle_and_no_divergent_nondescent]
  unfold NoNontrivialCycle NoDivergentOrbit
  constructor
  · rintro ⟨hno_cyc, hno_inj⟩
    refine ⟨hno_cyc, ?_⟩
    rintro ⟨n, hn1, hdiv⟩
    rcases divergentOrbit_attains_global_nondescent_minimum n hn1 hdiv with
      ⟨r_star, hn_star1, _, hn_star_min, hn_star_div⟩
    exact hno_inj ⟨iterateAccelerated n r_star, hn_star1, hn_star_min,
      (divergentOrbit_iff_injective _).mp hn_star_div⟩
  · rintro ⟨hno_cyc, hno_div⟩
    refine ⟨hno_cyc, ?_⟩
    rintro ⟨n, hn1, _, hinj⟩
    exact hno_div ⟨n, hn1, (divergentOrbit_iff_injective n).mpr hinj⟩

/-- Asymptotic Power-Deficit and Signed-Gap Laws for a Never-Descending Divergent Orbit
    (`divergentOrbit_asymptotic_power_and_gap_laws`):
    If `n > 1` is never-descending (`∀ r, iterateAccelerated n r ≥ n`) and satisfies `DivergentOrbit n`,
    then for every threshold `M ≥ n` and every exponent shift `m : Nat`, there exists `R : Nat`
    such that for all `r ≥ R` (with `w_r = parityWordOf r n` and `a_r = wordOnes w_r`):
    1. `iterateAccelerated n r > M` and `iterateAccelerated n r > 2 ^ m * n`,
    2. `signedProjectiveGap w_r n < ((2 ^ r : Nat) : Int) * ((n : Int) - (M : Int))`,
    3. `2 ^ r * n ^ a_r * (M + 1) ≤ n * (3 * n + 1) ^ a_r`, and
    4. `2 ^ (r + m) * n ^ a_r < (3 * n + 1) ^ a_r`. -/
theorem divergentOrbit_asymptotic_power_and_gap_laws (n M m : Nat)
    (hn1 : n > 1) (_hM : M ≥ n)
    (hnever_desc : ∀ r : Nat, iterateAccelerated n r ≥ n)
    (hdiv : DivergentOrbit n) :
    ∃ R : Nat, ∀ r : Nat, r ≥ R →
      let w_r := parityWordOf r n
      let a_r := wordOnes w_r
      iterateAccelerated n r > M ∧
      iterateAccelerated n r > 2 ^ m * n ∧
      signedProjectiveGap w_r n < ((2 ^ r : Nat) : Int) * ((n : Int) - (M : Int)) ∧
      2 ^ r * n ^ a_r * (M + 1) ≤ n * (3 * n + 1) ^ a_r ∧
      2 ^ (r + m) * n ^ a_r < (3 * n + 1) ^ a_r := by
  rcases hdiv (max M (2 ^ m * n)) with ⟨R, hR⟩
  refine ⟨R, ?_⟩
  intro r hr
  dsimp
  let w_r := parityWordOf r n
  let a_r := wordOnes w_r
  have hgt_max := hR r hr
  have hmax1 : M ≤ max M (2 ^ m * n) := Nat.le_max_left M (2 ^ m * n)
  have hmax2 : 2 ^ m * n ≤ max M (2 ^ m * n) := Nat.le_max_right M (2 ^ m * n)
  have hit_M : iterateAccelerated n r > M := by omega
  have hit_2m : iterateAccelerated n r > 2 ^ m * n := by omega
  have hv_r := parityWordOf_valid r n
  have hgap_eq := signedProjectiveGap_eq_wordD_mul_sub w_r n hv_r
  have hD_eq : (wordD w_r : Int) = ((2 ^ r : Nat) : Int) := by
    rw [wordD_eq_pow_two_length, parityWordOf_length]
  rw [hD_eq, applyParityWord_parityWordOf] at hgap_eq
  have hpow_pos : 2 ^ r ≥ 1 := Nat.one_le_pow r 2 (by decide)
  have hgap_lt : signedProjectiveGap w_r n < ((2 ^ r : Nat) : Int) * ((n : Int) - (M : Int)) := by
    rw [hgap_eq]
    have hsub_le : (n : Int) - (iterateAccelerated n r : Int) ≤
        (n : Int) - (M : Int) - 1 := by omega
    have hmul_le : ((2 ^ r : Nat) : Int) * ((n : Int) - (iterateAccelerated n r : Int)) ≤
        ((2 ^ r : Nat) : Int) * ((n : Int) - (M : Int) - 1) :=
      Int.mul_le_mul_of_nonneg_left hsub_le (by omega)
    have hrhs : ((2 ^ r : Nat) : Int) * ((n : Int) - (M : Int) - 1) =
        ((2 ^ r : Nat) : Int) * ((n : Int) - (M : Int)) - ((2 ^ r : Nat) : Int) := by
      rw [Int.mul_sub, Int.mul_one]
    omega
  have hpb := nondescent_prefix_power_bound n r (fun i _ => hnever_desc i)
  have hM1_le : 2 ^ r * n ^ a_r * (M + 1) ≤ n * (3 * n + 1) ^ a_r := by
    have hle_it : M + 1 ≤ iterateAccelerated n r := by omega
    have hmul := Nat.mul_le_mul_left (2 ^ r * n ^ a_r) hle_it
    exact Nat.le_trans hmul hpb
  have hna_pos : n ^ a_r ≥ 1 := pow_pos_of_pos n a_r (by omega)
  have h2r_na_pos : 2 ^ r * n ^ a_r ≥ 1 := by
    have h := Nat.mul_le_mul hpow_pos hna_pos
    omega
  have hstrict_mul : (2 ^ r * n ^ a_r) * (2 ^ m * n) < (2 ^ r * n ^ a_r) * iterateAccelerated n r := by
    have hle_it : 2 ^ m * n + 1 ≤ iterateAccelerated n r := by omega
    have hmul := Nat.mul_le_mul_left (2 ^ r * n ^ a_r) hle_it
    rw [Nat.mul_add, Nat.mul_one] at hmul
    omega
  have hstrict_rhs : (2 ^ r * n ^ a_r) * (2 ^ m * n) < n * (3 * n + 1) ^ a_r :=
    Nat.lt_of_lt_of_le hstrict_mul hpb
  have hlhs_rearrange : (2 ^ r * n ^ a_r) * (2 ^ m * n) = n * (2 ^ (r + m) * n ^ a_r) := by
    rw [Nat.pow_add 2 r m]
    have h1 : 2 ^ r * n ^ a_r * (2 ^ m * n) = 2 ^ r * (n ^ a_r * (2 ^ m * n)) :=
      Nat.mul_assoc _ _ _
    have h2 : n ^ a_r * (2 ^ m * n) = 2 ^ m * (n ^ a_r * n) := by
      rw [← Nat.mul_assoc (n ^ a_r) (2 ^ m) n, Nat.mul_comm (n ^ a_r) (2 ^ m), Nat.mul_assoc]
    have h3 : 2 ^ r * (2 ^ m * (n ^ a_r * n)) = (2 ^ r * 2 ^ m) * (n * n ^ a_r) := by
      rw [← Nat.mul_assoc (2 ^ r) (2 ^ m) _, Nat.mul_comm (n ^ a_r) n]
    have h4 : (2 ^ r * 2 ^ m) * (n * n ^ a_r) = n * (2 ^ r * 2 ^ m * n ^ a_r) := by
      rw [← Nat.mul_assoc (2 ^ r * 2 ^ m) n (n ^ a_r),
          Nat.mul_comm (2 ^ r * 2 ^ m) n,
          Nat.mul_assoc n (2 ^ r * 2 ^ m) (n ^ a_r)]
    rw [h1, h2, h3, h4]
  rw [hlhs_rearrange] at hstrict_rhs
  have hshift_lt : 2 ^ (r + m) * n ^ a_r < (3 * n + 1) ^ a_r := by
    by_cases hlt : 2 ^ (r + m) * n ^ a_r < (3 * n + 1) ^ a_r
    · exact hlt
    · have hge : (3 * n + 1) ^ a_r ≤ 2 ^ (r + m) * n ^ a_r := by omega
      have hmul := Nat.mul_le_mul_left n hge
      omega
  exact ⟨hit_M, hit_2m, hgap_lt, hM1_le, hshift_lt⟩

/-- Helper lemma: `wordOnes (List.replicate k false) = 0`. -/
theorem wordOnes_replicate_false (k : Nat) :
    wordOnes (List.replicate k false) = 0 := by
  induction k with
  | zero => rfl
  | succ k ih =>
    dsimp [List.replicate, wordOnes]
    exact ih

/-- Every single odd-to-odd return block `singleOddWord k = true :: replicate k false`
    contains exactly `1` odd step (`wordOnes (singleOddWord k) = 1`). -/
theorem wordOnes_singleOddWord (k : Nat) :
    wordOnes (singleOddWord k) = 1 := by
  dsimp [singleOddWord, wordOnes]
  rw [wordOnes_replicate_false]

/-- For every valuation sequence `ks : List Nat`, the number of odd steps in `returnMapWord ks`
    equals `ks.length` (`wordOnes (returnMapWord ks) = ks.length`). -/
theorem wordOnes_returnMapWord (ks : List Nat) :
    wordOnes (returnMapWord ks) = ks.length := by
  induction ks with
  | nil => rfl
  | cons k ks ih =>
    dsimp [returnMapWord]
    rw [wordOnes_append, wordOnes_singleOddWord, ih]
    omega

/-- Single Odd-to-Odd Return-Map Block Dichotomy (`singleOddWord_step_dichotomy`):
    For any odd integer `u > 1` and extra-halving count `k : Nat` (`v_2(3u + 1) = k + 1`)
    with `validParityWord u (singleOddWord k)`:
    1. `2 ^ (k + 1) * applyParityWord u (singleOddWord k) = 3 * u + 1`,
    2. `k = 0 → applyParityWord u (singleOddWord k) > u` (strict growth when `v_2(3u + 1) = 1`), and
    3. `k ≥ 1 → applyParityWord u (singleOddWord k) < u` (strict single-block descent whenever `v_2(3u + 1) ≥ 2`). -/
theorem singleOddWord_step_dichotomy (k u : Nat)
    (hu1 : u > 1) (hv : validParityWord u (singleOddWord k)) :
    2 ^ (k + 1) * applyParityWord u (singleOddWord k) = 3 * u + 1 ∧
    (k = 0 → applyParityWord u (singleOddWord k) > u) ∧
    (k ≥ 1 → applyParityWord u (singleOddWord k) < u) := by
  have hid := parityWord_affine_identity (singleOddWord k) u hv
  have hA : wordA (singleOddWord k) = 3 := wordA_singleOddWord k
  have hB : wordB (singleOddWord k) = 1 := by
    dsimp [singleOddWord, wordB]
    rw [wordA_replicate_false, wordB_replicate_false]
  have hD : wordD (singleOddWord k) = 2 ^ (k + 1) := by
    rw [wordD_eq_pow_two_length]
    dsimp [singleOddWord]
    rw [List.length_replicate]
  rw [hA, hB, hD] at hid
  refine ⟨hid, ?_, ?_⟩
  · intro hk0
    rw [hk0] at hid ⊢
    change 2 * applyParityWord u (singleOddWord 0) = 3 * u + 1 at hid
    omega
  · intro hk1
    obtain ⟨k', rfl⟩ : ∃ k', k = k' + 1 := ⟨k - 1, by omega⟩
    have hpow_ge4 : 2 ^ (k' + 1 + 1) ≥ 4 := by
      rw [Nat.pow_succ, Nat.pow_succ]
      have hp : 2 ^ k' ≥ 1 := Nat.one_le_pow k' 2 (by decide)
      omega
    have hmul_ge : 2 ^ (k' + 1 + 1) * u ≥ 4 * u :=
      Nat.mul_le_mul_right u hpow_ge4
    have hgt_lhs : 2 ^ (k' + 1 + 1) * applyParityWord u (singleOddWord (k' + 1)) <
        2 ^ (k' + 1 + 1) * u := by omega
    by_cases hlt : applyParityWord u (singleOddWord (k' + 1)) < u
    · exact hlt
    · have hge : u ≤ applyParityWord u (singleOddWord (k' + 1)) := by omega
      have hmul_le := Nat.mul_le_mul_left (2 ^ (k' + 1 + 1)) hge
      omega

/-- Multi-Block Return-Map Valuation & Reservoir Conservation Laws
    (`returnMap_nondescent_valuation_and_gap_laws`):
    For any starting integer `n > 1` realizing a valuation sequence `ks : List Nat`
    (`validParityWord n (returnMapWord ks)`) along a non-descending prefix of length
    `K = totalValuation ks` (`∀ i ≤ K, iterateAccelerated n i ≥ n`), let `s = ks.length`:
    1. `parityWordOf K n = returnMapWord ks` and `wordOnes (parityWordOf K n) = s`,
    2. `n % (2 ^ K) = wordResidue (returnMapWord ks)` (exact 2-adic residue cylinder lock),
    3. `deficitReservoir n K + 2 ^ K * n ^ s * applyParityWord n (returnMapWord ks) = n * (3 * n + 1) ^ s`,
    4. `2 ^ K * n ^ s ≤ (3 * n + 1) ^ s`, and
    5. `n ^ s * wordB (returnMapWord ks) ≤ n * ((3 * n + 1) ^ s - (3 * n) ^ s)`. -/
theorem returnMap_nondescent_valuation_and_gap_laws (ks : List Nat) (n : Nat)
    (hn1 : n > 1)
    (hv : validParityWord n (returnMapWord ks))
    (hge : ∀ i : Nat, i ≤ totalValuation ks → iterateAccelerated n i ≥ n) :
    let K := totalValuation ks
    let s := ks.length
    parityWordOf K n = returnMapWord ks ∧
    wordOnes (parityWordOf K n) = s ∧
    n % (2 ^ K) = wordResidue (returnMapWord ks) ∧
    deficitReservoir n K + 2 ^ K * n ^ s * applyParityWord n (returnMapWord ks) =
      n * (3 * n + 1) ^ s ∧
    2 ^ K * n ^ s ≤ (3 * n + 1) ^ s ∧
    n ^ s * wordB (returnMapWord ks) ≤ n * ((3 * n + 1) ^ s - (3 * n) ^ s) := by
  dsimp
  let K := totalValuation ks
  let s := ks.length
  have hw_eq : parityWordOf K n = returnMapWord ks := by
    unfold K totalValuation
    exact (validParityWord_iff_eq_parityWordOf (returnMapWord ks) n).mp hv
  have hones_eq : wordOnes (parityWordOf K n) = s := by
    rw [hw_eq, wordOnes_returnMapWord]
  have hmod_eq : n % (2 ^ K) = wordResidue (returnMapWord ks) :=
    (returnMapWord_admissible_iff ks n).mp hv
  have hcons := reservoir_surplus_conservation_law n K (fun i hi => hge i (by omega))
  dsimp at hcons
  rw [hones_eq, ← applyParityWord_parityWordOf K n, hw_eq] at hcons
  have hratio := (nondescent_diophantine_sandwich n K (by omega) hge).2.2
  rw [hones_eq] at hratio
  have hduality := (reservoir_offset_duality_identity n K (fun i hi => hge i (by omega))).2
  rw [hones_eq, hw_eq] at hduality
  have hB_le : n ^ s * wordB (returnMapWord ks) ≤ n * ((3 * n + 1) ^ s - (3 * n) ^ s) := by
    rw [Nat.mul_sub]
    omega
  exact ⟨hw_eq, hones_eq, hmod_eq, hcons, hratio, hB_le⟩

end CollatzProofClosure
end BBB17
