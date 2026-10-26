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

/-! ## Section 11: Ordered Valuation-Block Operator Dynamics `Y_s = (u_s, K_s, B_s, ρ_s, P_s, G_s)`, Exact Affine-Parity Equivalence, and Target Falsification Analysis

    Advances the two-track proof attack on `NoNontrivialCycle` and `NoDivergentOrbit` by establishing:
    1. **Exact Affine-Parity Equivalence (`affine_identity_iff_validParityWord_and_output`)**:
       For EVERY parity word `w` and EVERY `n, y : Nat`,
       `wordD w * y = wordA w * n + wordB w ↔ (validParityWord n w ∧ applyParityWord n w = y)`.
       Because `wordA bs = 3^{a(bs)}` is odd for every suffix `bs`, the single natural-number equation
       `2^|w| * y = 3^{a(w)} * n + B_w` automatically forces 2-adic parity admissibility at every step!
    2. **Pure Diophantine Non-Divisibility Equivalence for `NoNontrivialCycle`
       (`noNontrivialCycle_iff_offset_nondivisibility`, `noNontrivialCycle_implies_returnMap_offset_nondivisibility`)**:
       Eliminates the starting-integer quantifier and 2-adic residue constraint from `NoNontrivialCycle`:
       `NoNontrivialCycle ↔ ∀ w : List Bool, wordD w > wordA w → wordB w > 2 * wordDelta w → wordB w % wordDelta w ≠ 0`.
       And for any ordered valuation sequence `ks : List Nat` with `w = returnMapWord ks`:
       `NoNontrivialCycle → wordD w > wordA w → wordB w > wordDelta w → wordB w % wordDelta w ≠ 0`.
    3. **Genuine Consecutive Odd-to-Odd Return Sequences (`validOddReturnSeq`,
       `validOddReturnSeq_iff_affine_and_odd_output`)**:
       Addresses the qualification requirement that each block `singleOddWord k` must end at an odd integer
       so that `v_2(3 u_j + 1) = k_j + 1` holds exactly:
       `validOddReturnSeq n ks ↔ ∃ u_s : Nat, 2^(totalValuation ks) * u_s = 3^(ks.length) * n + wordB (returnMapWord ks) ∧ u_s % 2 = 1`.
    4. **Ordered Valuation-Block Operator State `Y_s = (u_s, K_s, B_s, ρ_s, P_s, G_s)` and Block Recurrences
       (`wordB_returnMapWord_snoc`, `signedProjectiveGap_returnMapWord_snoc`,
        `deficitReservoir_returnMap_block_step`, `returnMap_two_block_swap_offset_law`,
        `returnMap_offset_extremal_sandwich`)**:
       - Exact offset update: `B_{s+1} = 3 * B_s + 2^{K_s}` (with `K_{s+1} = K_s + k_s + 1`),
       - Exact ordering sensitivity: swapping adjacent blocks `[k₁, k₂] → [k₂, k₁]` preserves `s` and `K`
         while shifting `B` by `2^{K_s + 1} * (2^{k₂} - 2^{k₁})`,
       - Universal two-sided ordering sandwich: `3^s - 2^s ≤ B_s ≤ 2^{K_s - s} * (3^s - 2^s)`,
       - Exact reservoir block recurrence: `P_{K_{s+1}}(n) = (3n + 1) * P_{K_s}(n) + n^s * Ω_{K_s}(n)`.
    5. **Formal Falsifications of Naive Strengthening Hypotheses
       (`trivial_cycle_repeat_divides_offset_witness`, `contracting_odd_block_survives_above_initial_at_27`)**:
       - Certifies that omitting the threshold `wordB w > wordDelta w` in `returnMapWord` non-divisibility is
         falsified by `ks = [1, 1]` (`s = 2, K = 4, Δ = 7, B = 7, n = 1`), and omitting `wordB w > 2 * wordDelta w`
         for general parity words is falsified by `w = [false, true]` (`r = 2, a = 1, Δ = 1, B = 2, n = 2`).
       - Certifies that a contracting odd-to-odd return block (`k_j ≥ 1`, so `u_{j+1} < u_j`) does NOT force
         immediate descent below `n`: at `n = 27`, `ks = [0, 1]` is a genuine odd-to-odd return sequence with
         `u_1 = 41 > 27`, `k_1 = 1 ≥ 1`, and `u_2 = 31 < 41`, yet `u_2 = 31 > 27`.
-/

/-- Exact Affine-Parity Equivalence Theorem (`affine_identity_iff_validParityWord_and_output`):
    For EVERY parity word `w : List Bool` and EVERY `n, y : Nat`, the natural-number affine
    equation `wordD w * y = wordA w * n + wordB w` holds if and only if `n` is 2-adically
    admissible for `w` (`validParityWord n w`) and `applyParityWord n w = y`. -/
theorem affine_identity_iff_validParityWord_and_output (w : List Bool) :
    ∀ (n y : Nat),
      wordD w * y = wordA w * n + wordB w ↔
        (validParityWord n w ∧ applyParityWord n w = y) := by
  induction w with
  | nil =>
    intro n y
    dsimp [wordD, wordA, wordB, validParityWord, applyParityWord]
    constructor
    · intro heq
      exact ⟨trivial, by omega⟩
    · rintro ⟨_, hy⟩
      omega
  | cons b bs ih =>
    intro n y
    constructor
    · intro heq
      have hA_odd : wordA bs % 2 = 1 := wordA_odd bs
      cases b with
      | false =>
        dsimp [wordD, wordA, wordB] at heq
        have hn_even : n % 2 = 0 := by
          have hmod : (2 * wordD bs * y) % 2 = (wordA bs * n + 2 * wordB bs) % 2 := by
            rw [heq]
          rw [Nat.mul_assoc 2 (wordD bs) y, Nat.mul_mod_right,
              Nat.add_mod, Nat.mul_mod_right, Nat.add_zero, Nat.mod_mod,
              Nat.mul_mod, hA_odd, Nat.one_mul, Nat.mod_mod] at hmod
          omega
        have hstep_n : acceleratedCollatz n = n / 2 := by
          unfold acceleratedCollatz
          rw [if_pos hn_even]
        let n' := acceleratedCollatz n
        have hn_eq : n = 2 * n' := by
          change n = 2 * acceleratedCollatz n
          omega
        have heq_bs : wordD bs * y = wordA bs * n' + wordB bs := by
          have h1 : wordA bs * n = 2 * (wordA bs * n') := by
            rw [hn_eq, ← Nat.mul_assoc, Nat.mul_comm (wordA bs) 2, Nat.mul_assoc]
          have h2 : 2 * (wordD bs * y) = 2 * (wordA bs * n' + wordB bs) := by
            rw [← Nat.mul_assoc 2 (wordD bs) y, heq, h1, Nat.mul_add]
          exact Nat.eq_of_mul_eq_mul_left (by decide : 2 > 0) h2
        rcases (ih n' y).mp heq_bs with ⟨hv_bs, hy_bs⟩
        exact ⟨⟨hn_even, hv_bs⟩, hy_bs⟩
      | true =>
        dsimp [wordD, wordA, wordB] at heq
        have hcomb : 3 * wordA bs * n + (wordA bs + 2 * wordB bs) =
            wordA bs * (3 * n + 1) + 2 * wordB bs := by
          rw [Nat.mul_add, Nat.mul_one, ← Nat.mul_assoc (wordA bs) 3 n,
              Nat.mul_comm (wordA bs) 3, ← Nat.add_assoc]
        have hn_odd : n % 2 = 1 := by
          have hmod : (2 * wordD bs * y) % 2 =
              (3 * wordA bs * n + (wordA bs + 2 * wordB bs)) % 2 := by
            rw [heq]
          rw [hcomb, Nat.mul_assoc 2 (wordD bs) y, Nat.mul_mod_right,
              Nat.add_mod, Nat.mul_mod_right, Nat.add_zero, Nat.mod_mod,
              Nat.mul_mod, hA_odd, Nat.one_mul, Nat.mod_mod] at hmod
          omega
        have hnot_ev : ¬(n % 2 = 0) := by omega
        have hstep_n : acceleratedCollatz n = (3 * n + 1) / 2 := by
          unfold acceleratedCollatz
          rw [if_neg hnot_ev]
        let n' := acceleratedCollatz n
        have hn_eq : 3 * n + 1 = 2 * n' := by
          change 3 * n + 1 = 2 * acceleratedCollatz n
          omega
        have heq_bs : wordD bs * y = wordA bs * n' + wordB bs := by
          have h1 : wordA bs * (3 * n + 1) = 2 * (wordA bs * n') := by
            rw [hn_eq, ← Nat.mul_assoc, Nat.mul_comm (wordA bs) 2, Nat.mul_assoc]
          have h2 : 2 * (wordD bs * y) = 2 * (wordA bs * n' + wordB bs) := by
            rw [← Nat.mul_assoc 2 (wordD bs) y, heq, hcomb, h1, Nat.mul_add]
          exact Nat.eq_of_mul_eq_mul_left (by decide : 2 > 0) h2
        rcases (ih n' y).mp heq_bs with ⟨hv_bs, hy_bs⟩
        exact ⟨⟨hn_odd, hv_bs⟩, hy_bs⟩
    · rintro ⟨hv, rfl⟩
      exact parityWord_affine_identity (b :: bs) n hv

/-- Helper lemma: the accelerated orbit of `1` stays within `{1, 2}` (`iterateAccelerated 1 r ≤ 2`). -/
theorem iterateAccelerated_one_eq_one_or_two (r : Nat) :
    iterateAccelerated 1 r = 1 ∨ iterateAccelerated 1 r = 2 := by
  induction r with
  | zero => exact Or.inl rfl
  | succ r ih =>
    rw [iterateAccelerated_succ_right]
    rcases ih with h1 | h2
    · rw [h1]; exact Or.inr rfl
    · rw [h2]; exact Or.inl rfl

/-- Pure Diophantine Non-Divisibility Equivalence for `NoNontrivialCycle`
    (`noNontrivialCycle_iff_offset_nondivisibility`):
    `NoNontrivialCycle` holds if and only if for every contracting parity word `w`
    (`wordD w > wordA w`) with `wordB w > 2 * wordDelta w`, `wordDelta w` does not divide `wordB w`. -/
theorem noNontrivialCycle_iff_offset_nondivisibility :
    NoNontrivialCycle ↔
      (∀ w : List Bool,
        wordD w > wordA w →
        wordB w > 2 * wordDelta w →
        wordB w % wordDelta w ≠ 0) := by
  unfold NoNontrivialCycle
  constructor
  · intro hno_cyc w hcont hB_gt2 hdiv_mod
    have hdelta_pos : wordDelta w > 0 := by
      unfold wordDelta; omega
    let n := wordB w / wordDelta w
    have hmul_eq : wordDelta w * n = wordB w :=
      Nat.mul_div_cancel' (Nat.dvd_of_mod_eq_zero hdiv_mod)
    have hn_gt2 : n > 2 := by
      by_cases hle2 : n ≤ 2
      · have hle_mul := Nat.mul_le_mul_left (wordDelta w) hle2
        omega
      · omega
    have haff : wordD w * n = wordA w * n + wordB w := by
      unfold wordDelta at hmul_eq
      have hsub : (wordD w - wordA w) * n + wordA w * n = wordD w * n := by
        rw [← Nat.add_mul, Nat.sub_add_cancel (by omega)]
      omega
    rcases (affine_identity_iff_validParityWord_and_output w n n).mp haff with ⟨hv_n, hout_n⟩
    have hp_pos : w.length ≥ 1 := by
      cases w with
      | nil => dsimp [wordD, wordA] at hcont; omega
      | cons _ _ => simp
    have hlen_eq : parityWordOf w.length n = w :=
      (validParityWord_iff_eq_parityWordOf w n).mp hv_n
    have hit_n : iterateAccelerated n w.length = n := by
      rw [← applyParityWord_parityWordOf, hlen_eq, hout_n]
    rcases exists_min_on_prefix (fun t => iterateAccelerated n t) w.length hp_pos with
      ⟨t_star, _, ht_min⟩
    let m_star := iterateAccelerated n t_star
    have hm_pos : m_star > 0 := iterateAccelerated_pos n t_star (by omega)
    have hm_ne1 : m_star ≠ 1 := by
      intro hm1
      have hadd := iterateAccelerated_add n t_star (w.length - t_star)
      have hlen_sub : t_star + (w.length - t_star) = w.length := by omega
      rw [hlen_sub, hit_n] at hadd
      change n = iterateAccelerated m_star (w.length - t_star) at hadd
      rw [hm1] at hadd
      rcases iterateAccelerated_one_eq_one_or_two (w.length - t_star) with h1 | h2 <;> omega
    have hm_per : iterateAccelerated m_star w.length = m_star := by
      unfold m_star
      rw [← iterateAccelerated_add n t_star w.length]
      have h1 : t_star + w.length = t_star + w.length * 1 := by omega
      rw [h1]
      exact iterateAccelerated_add_mul_period n w.length hit_n t_star 1
    have hm_min_all : ∀ r : Nat, iterateAccelerated m_star r ≥ m_star := by
      intro r
      unfold m_star
      rw [← iterateAccelerated_add n t_star r]
      have hdiv := (Nat.mod_add_div (t_star + r) w.length).symm
      have hper := iterateAccelerated_add_mul_period n w.length hit_n
        ((t_star + r) % w.length) ((t_star + r) / w.length)
      rw [← hdiv] at hper
      rw [hper]
      exact ht_min ((t_star + r) % w.length) (Nat.mod_lt _ hp_pos)
    exact hno_cyc ⟨m_star, w.length, by omega, hp_pos, hm_per, hm_min_all⟩
  · rintro hall ⟨m, p, hm1, hp1, hper, hmin⟩
    have hm_ge1024 : m ≥ 1024 := by
      by_cases hlt : m < 1024
      · rcases descent_of_lt_1024 m hm1 hlt with ⟨k, _, _, hk_lt⟩
        have hge := hmin k
        omega
      · omega
    let w := parityWordOf p m
    rcases universal_cycle_minimum_element_bound m p m hm1 hp1 (by omega) (by omega)
      (fun i _ => hmin i) hper with ⟨_, hcont_pow, _, _⟩
    have hcont : wordD w > wordA w := by
      rw [wordD_eq_pow_two_length, parityWordOf_length, wordA_eq_pow_three_wordOnes]
      exact hcont_pow
    have hv := parityWordOf_valid p m
    have hge_ap : applyParityWord m w ≥ m := by
      rw [applyParityWord_parityWordOf, hper]
      omega
    have hnd := (discrete_deficit_nondescent_identity w m hv (by omega) hge_ap).1
    rw [applyParityWord_parityWordOf, hper, Nat.sub_self, Nat.mul_zero, Nat.add_zero] at hnd
    have hdelta_pos : wordDelta w > 0 := by
      unfold wordDelta; omega
    have hB_gt2 : wordB w > 2 * wordDelta w := by
      have hmul3 : wordDelta w * 3 ≤ wordDelta w * m :=
        Nat.mul_le_mul_left (wordDelta w) (by omega)
      omega
    have hB_mod : wordB w % wordDelta w = 0 := by
      rw [hnd, Nat.mul_mod_right]
    exact hall w hcont hB_gt2 hB_mod

/-- Genuine Consecutive Odd-to-Odd Return Valuation Sequence (`validOddReturnSeq`):
    An integer `n` realizes `ks : List Nat` as a genuine sequence of consecutive odd-to-odd
    returns (`v_2(3 u_j + 1) = k_j + 1` with odd endpoint `u_s`) iff `n` is odd, `returnMapWord ks`
    is admissible for `n`, and the terminal output `applyParityWord n (returnMapWord ks)` is odd. -/
def validOddReturnSeq (n : Nat) (ks : List Nat) : Prop :=
  n % 2 = 1 ∧
  validParityWord n (returnMapWord ks) ∧
  applyParityWord n (returnMapWord ks) % 2 = 1

/-- Exact Affine-Endpoint Characterization of `validOddReturnSeq`
    (`validOddReturnSeq_iff_affine_and_odd_output`):
    `validOddReturnSeq n ks` holds if and only if `n` is odd and there exists an odd integer `u_s`
    such that `2 ^ totalValuation ks * u_s = 3 ^ ks.length * n + wordB (returnMapWord ks)`. -/
theorem validOddReturnSeq_iff_affine_and_odd_output (n : Nat) (ks : List Nat) :
    validOddReturnSeq n ks ↔
      (n % 2 = 1 ∧
       ∃ u_s : Nat,
         2 ^ totalValuation ks * u_s =
           3 ^ ks.length * n + wordB (returnMapWord ks) ∧
         u_s % 2 = 1) := by
  unfold validOddReturnSeq
  constructor
  · rintro ⟨hn_odd, hv, hout_odd⟩
    refine ⟨hn_odd, applyParityWord n (returnMapWord ks), ?_, hout_odd⟩
    exact returnMap_exact_affine ks n hv
  · rintro ⟨hn_odd, u_s, haff, hu_odd⟩
    rw [← wordD_returnMapWord ks, ← wordA_returnMapWord ks] at haff
    rcases (affine_identity_iff_validParityWord_and_output (returnMapWord ks) n u_s).mp haff with
      ⟨hv, rfl⟩
    exact ⟨hn_odd, hv, hu_odd⟩

/-- Concatenation law for `returnMapWord`:
    `returnMapWord (ks₁ ++ ks₂) = returnMapWord ks₁ ++ returnMapWord ks₂`. -/
theorem returnMapWord_append (ks₁ ks₂ : List Nat) :
    returnMapWord (ks₁ ++ ks₂) = returnMapWord ks₁ ++ returnMapWord ks₂ := by
  induction ks₁ with
  | nil => rfl
  | cons k ks₁ ih =>
    dsimp [returnMapWord]
    rw [ih, List.append_assoc]

/-- Right-append law for `returnMapWord`:
    `returnMapWord (ks ++ [k]) = returnMapWord ks ++ singleOddWord k`. -/
theorem returnMapWord_snoc (ks : List Nat) (k : Nat) :
    returnMapWord (ks ++ [k]) = returnMapWord ks ++ singleOddWord k := by
  rw [returnMapWord_append]
  dsimp [returnMapWord]
  rw [List.append_nil]

/-- Cumulative valuation step recurrence (`totalValuation_snoc`):
    `totalValuation (ks ++ [k]) = totalValuation ks + k + 1`. -/
theorem totalValuation_snoc (ks : List Nat) (k : Nat) :
    totalValuation (ks ++ [k]) = totalValuation ks + k + 1 := by
  unfold totalValuation
  rw [returnMapWord_snoc, List.length_append]
  dsimp [singleOddWord]
  rw [List.length_replicate]
  omega

/-- Exact Ordered Valuation-Block Offset Recurrence (`wordB_returnMapWord_snoc`):
    Appending block `k` updates the affine offset according to
    `B_{s+1} = 3 * B_s + 2^{K_s}`. -/
theorem wordB_returnMapWord_snoc (ks : List Nat) (k : Nat) :
    wordB (returnMapWord (ks ++ [k])) =
      3 * wordB (returnMapWord ks) + 2 ^ totalValuation ks := by
  rw [returnMapWord_snoc, wordB_append, wordA_singleOddWord, wordD_returnMapWord]
  have hB1 : wordB (singleOddWord k) = 1 := by
    dsimp [singleOddWord, wordB]
    rw [wordA_replicate_false, wordB_replicate_false]
  rw [hB1, Nat.mul_one]

/-- Exact Signed Projective Gap Block Recurrence (`signedProjectiveGap_returnMapWord_snoc`):
    Across appending block `k` to `ks` (`K_s = totalValuation ks`),
    `G_{s+1}(n) = 3 * G_s(n) + 2^{K_s} * ((2^{k+1} - 3) * n - 1)`. -/
theorem signedProjectiveGap_returnMapWord_snoc (ks : List Nat) (k n : Nat) :
    signedProjectiveGap (returnMapWord (ks ++ [k])) n =
      3 * signedProjectiveGap (returnMapWord ks) n +
        ((2 ^ totalValuation ks : Nat) : Int) *
          ((((2 ^ (k + 1) : Nat) : Int) - 3) * (n : Int) - 1) := by
  have hD_snoc : wordD (returnMapWord (ks ++ [k])) =
      2 ^ totalValuation ks * 2 ^ (k + 1) := by
    rw [returnMapWord_snoc, wordD_append, wordD_returnMapWord, wordD_eq_pow_two_length]
    dsimp [singleOddWord]
    rw [List.length_replicate]
  have hA_snoc : wordA (returnMapWord (ks ++ [k])) =
      3 * wordA (returnMapWord ks) := by
    rw [returnMapWord_snoc, wordA_append, wordA_singleOddWord, Nat.mul_comm]
  have hB_snoc := wordB_returnMapWord_snoc ks k
  have hD_ks := wordD_returnMapWord ks
  unfold signedProjectiveGap
  rw [hD_snoc, hA_snoc, hB_snoc, hD_ks]
  have hcast : ((2 ^ totalValuation ks * 2 ^ (k + 1) : Nat) : Int) =
      ((2 ^ totalValuation ks : Nat) : Int) * ((2 ^ (k + 1) : Nat) : Int) := by
    push_cast; rfl
  have hcastA : ((3 * wordA (returnMapWord ks) : Nat) : Int) =
      3 * (wordA (returnMapWord ks) : Int) := by
    push_cast; rfl
  have hcastB : ((3 * wordB (returnMapWord ks) + 2 ^ totalValuation ks : Nat) : Int) =
      3 * (wordB (returnMapWord ks) : Int) + ((2 ^ totalValuation ks : Nat) : Int) := by
    push_cast; rfl
  rw [hcast, hcastA, hcastB]
  let D_s := ((2 ^ totalValuation ks : Nat) : Int)
  let D_k := ((2 ^ (k + 1) : Nat) : Int)
  let A_s := (wordA (returnMapWord ks) : Int)
  let B_s := (wordB (returnMapWord ks) : Int)
  change D_s * D_k * (n : Int) - 3 * A_s * (n : Int) - (3 * B_s + D_s) =
    3 * (D_s * (n : Int) - A_s * (n : Int) - B_s) + D_s * ((D_k - 3) * (n : Int) - 1)
  have hrhs1 : 3 * (D_s * (n : Int) - A_s * (n : Int) - B_s) =
      3 * (D_s * (n : Int)) - 3 * (A_s * (n : Int)) - 3 * B_s := by
    rw [Int.mul_sub, Int.mul_sub]
  have hrhs2 : D_s * ((D_k - 3) * (n : Int) - 1) =
      D_s * D_k * (n : Int) - 3 * (D_s * (n : Int)) - D_s := by
    rw [Int.sub_mul, Int.mul_sub, Int.mul_sub, Int.mul_one,
        ← Int.mul_assoc D_s D_k (n : Int),
        ← Int.mul_assoc D_s 3 (n : Int),
        Int.mul_comm D_s 3,
        Int.mul_assoc 3 D_s (n : Int)]
  have hassocA : 3 * A_s * (n : Int) = 3 * (A_s * (n : Int)) :=
    Int.mul_assoc 3 A_s (n : Int)
  omega

/-- Reservoir invariance across `k` consecutive even steps (`deficitReservoir_even_run`):
    If steps `r, r + 1, ..., r + k - 1` are even, `deficitReservoir n (r + k) = deficitReservoir n r`. -/
theorem deficitReservoir_even_run (n r : Nat) :
    ∀ k : Nat,
      (∀ j : Nat, j < k → iterateAccelerated n (r + j) % 2 = 0) →
      deficitReservoir n (r + k) = deficitReservoir n r
  | 0, _ => by rw [Nat.add_zero]
  | k + 1, hev => by
    have ih := deficitReservoir_even_run n r k (fun j hj => hev j (by omega))
    have hev_k : iterateAccelerated n (r + k) % 2 = 0 := hev k (by omega)
    have hnot1 : ¬(iterateAccelerated n (r + k) % 2 = 1) := by omega
    have hstep : deficitReservoir n (r + k + 1) = deficitReservoir n (r + k) := by
      change (if iterateAccelerated n (r + k) % 2 = 1 then
        (3 * n + 1) * deficitReservoir n (r + k) +
          n ^ wordOnes (parityWordOf (r + k) n) * orbitSurplus n (r + k)
      else deficitReservoir n (r + k)) = deficitReservoir n (r + k)
      rw [if_neg hnot1]
    have hassoc : r + (k + 1) = r + k + 1 := by omega
    rw [hassoc, hstep, ih]

/-- Ordering Sensitivity of Valuation Blocks (`returnMap_two_block_swap_offset_law`):
    Swapping two adjacent valuation blocks `[k₁, k₂] ↔ [k₂, k₁]` after any prefix `ks`
    preserves `s` and `totalValuation`, while shifting `wordB` by
    `wordB(ks ++ [k₂, k₁]) + 2^{K + k₁ + 1} = wordB(ks ++ [k₁, k₂]) + 2^{K + k₂ + 1}`. -/
theorem returnMap_two_block_swap_offset_law (ks : List Nat) (k₁ k₂ : Nat) :
    let K := totalValuation ks
    wordB (returnMapWord (ks ++ [k₂, k₁])) + 2 ^ (K + k₁ + 1) =
      wordB (returnMapWord (ks ++ [k₁, k₂])) + 2 ^ (K + k₂ + 1) := by
  dsimp
  have h12 : ks ++ [k₁, k₂] = (ks ++ [k₁]) ++ [k₂] := by simp
  have h21 : ks ++ [k₂, k₁] = (ks ++ [k₂]) ++ [k₁] := by simp
  rw [h12, h21,
      wordB_returnMapWord_snoc (ks ++ [k₁]) k₂,
      wordB_returnMapWord_snoc (ks ++ [k₂]) k₁,
      wordB_returnMapWord_snoc ks k₁,
      wordB_returnMapWord_snoc ks k₂,
      totalValuation_snoc ks k₁,
      totalValuation_snoc ks k₂]
  omega

/-- Left-cons offset recurrence for `returnMapWord` (`wordB_returnMapWord_cons`):
    Prepending block `k` to `ks` satisfies
    `wordB (returnMapWord (k :: ks)) = 3 ^ ks.length + 2 ^ (k + 1) * wordB (returnMapWord ks)`. -/
theorem wordB_returnMapWord_cons (k : Nat) (ks : List Nat) :
    wordB (returnMapWord (k :: ks)) =
      3 ^ ks.length + 2 ^ (k + 1) * wordB (returnMapWord ks) := by
  dsimp [returnMapWord]
  rw [wordB_append, wordA_returnMapWord]
  have hB1 : wordB (singleOddWord k) = 1 := by
    dsimp [singleOddWord, wordB]
    rw [wordA_replicate_false, wordB_replicate_false]
  have hD1 : wordD (singleOddWord k) = 2 ^ (k + 1) := by
    rw [wordD_eq_pow_two_length]
    dsimp [singleOddWord]
    rw [List.length_replicate]
  rw [hB1, hD1, Nat.mul_one]

/-- Left-cons cumulative valuation recurrence (`totalValuation_cons`):
    `totalValuation (k :: ks) = k + 1 + totalValuation ks`. -/
theorem totalValuation_cons (k : Nat) (ks : List Nat) :
    totalValuation (k :: ks) = k + 1 + totalValuation ks := by
  unfold totalValuation
  dsimp [returnMapWord]
  rw [List.length_append]
  dsimp [singleOddWord]
  rw [List.length_replicate]

/-- Helper lemma: `a ≤ b → 2 ^ a ≤ 2 ^ b`. -/
theorem two_pow_le_two_pow (a b : Nat) (h : a ≤ b) : 2 ^ a ≤ 2 ^ b := by
  obtain ⟨d, rfl⟩ : ∃ d, b = a + d := ⟨b - a, by omega⟩
  rw [Nat.pow_add]
  have hd : 2 ^ d ≥ 1 := Nat.one_le_pow d 2 (by decide)
  have hmul := Nat.mul_le_mul_left (2 ^ a) hd
  omega

/-- Universal Two-Sided Ordering Sandwich for Return-Map Offsets (`returnMap_offset_extremal_sandwich`):
    For EVERY valuation sequence `ks : List Nat` (with `s = ks.length` and `K = totalValuation ks`):
    1. `K ≥ s`,
    2. `wordB (returnMapWord ks) + 2 ^ s ≥ 3 ^ s` (`B_s ≥ 3^s - 2^s`), and
    3. `2 ^ s * wordB (returnMapWord ks) + 2 ^ K * 2 ^ s ≤ 2 ^ K * 3 ^ s` (`B_s ≤ 2^{K - s} * (3^s - 2^s)`). -/
theorem returnMap_offset_extremal_sandwich (ks : List Nat) :
    let s := ks.length
    let K := totalValuation ks
    K ≥ s ∧
    wordB (returnMapWord ks) + 2 ^ s ≥ 3 ^ s ∧
    2 ^ s * wordB (returnMapWord ks) + 2 ^ K * 2 ^ s ≤ 2 ^ K * 3 ^ s := by
  let P := fun (l : List Nat) =>
    totalValuation l ≥ l.length ∧
    wordB (returnMapWord l) + 2 ^ l.length ≥ 3 ^ l.length ∧
    2 ^ l.length * wordB (returnMapWord l) + 2 ^ totalValuation l * 2 ^ l.length ≤
      2 ^ totalValuation l * 3 ^ l.length
  have hnil : P [] := by
    dsimp [P, totalValuation, returnMapWord, wordB]
    omega
  have hsnoc : ∀ (l : List Nat) (k : Nat), P l → P (l ++ [k]) := by
    intro l k ih
    dsimp [P] at ih ⊢
    rcases ih with ⟨hK_ge_s, hlow, hhigh⟩
    have hlen : (l ++ [k]).length = l.length + 1 := by
      rw [List.length_append]; rfl
    have hK_snoc : totalValuation (l ++ [k]) = totalValuation l + k + 1 :=
      totalValuation_snoc l k
    have hB_snoc : wordB (returnMapWord (l ++ [k])) =
        3 * wordB (returnMapWord l) + 2 ^ totalValuation l :=
      wordB_returnMapWord_snoc l k
    rw [hlen, hK_snoc, hB_snoc]
    have hpow_s_le_K : 2 ^ l.length ≤ 2 ^ totalValuation l :=
      two_pow_le_two_pow l.length (totalValuation l) hK_ge_s
    have hlow_step : 3 * wordB (returnMapWord l) + 2 ^ totalValuation l +
        2 ^ (l.length + 1) ≥ 3 ^ (l.length + 1) := by
      rw [Nat.pow_succ 2 l.length, Nat.pow_succ 3 l.length]
      omega
    have hhigh_step : 2 ^ (l.length + 1) *
        (3 * wordB (returnMapWord l) + 2 ^ totalValuation l) +
        2 ^ (totalValuation l + k + 1) * 2 ^ (l.length + 1) ≤
        2 ^ (totalValuation l + k + 1) * 3 ^ (l.length + 1) := by
      have hmul6 := Nat.mul_le_mul_left 6 hhigh
      have hSB : (2 ^ l.length * 2) * (3 * wordB (returnMapWord l)) =
          6 * (2 ^ l.length * wordB (returnMapWord l)) := by
        rw [Nat.mul_assoc (2 ^ l.length) 2 (3 * wordB (returnMapWord l)),
            ← Nat.mul_assoc 2 3 (wordB (returnMapWord l)),
            ← Nat.mul_assoc (2 ^ l.length) (2 * 3) (wordB (returnMapWord l)),
            Nat.mul_comm (2 ^ l.length) (2 * 3),
            Nat.mul_assoc (2 * 3) (2 ^ l.length) (wordB (returnMapWord l))]
      have hTS1 : (2 ^ l.length * 2) * 2 ^ totalValuation l =
          2 * (2 ^ totalValuation l * 2 ^ l.length) := by
        rw [Nat.mul_comm (2 ^ l.length) 2,
            Nat.mul_assoc 2 (2 ^ l.length) (2 ^ totalValuation l),
            Nat.mul_comm (2 ^ l.length) (2 ^ totalValuation l)]
      have hTS2 : (2 ^ totalValuation l * 2) * (2 ^ l.length * 2) =
          4 * (2 ^ totalValuation l * 2 ^ l.length) := by
        rw [Nat.mul_comm (2 ^ totalValuation l) 2,
            Nat.mul_assoc 2 (2 ^ totalValuation l) (2 ^ l.length * 2),
            ← Nat.mul_assoc (2 ^ totalValuation l) (2 ^ l.length) 2,
            Nat.mul_comm (2 ^ totalValuation l * 2 ^ l.length) 2,
            ← Nat.mul_assoc 2 2 (2 ^ totalValuation l * 2 ^ l.length)]
      have hlhs6 : 6 * (2 ^ l.length * wordB (returnMapWord l) +
          2 ^ totalValuation l * 2 ^ l.length) =
          2 ^ (l.length + 1) * (3 * wordB (returnMapWord l) + 2 ^ totalValuation l) +
            2 ^ (totalValuation l + 1) * 2 ^ (l.length + 1) := by
        rw [Nat.pow_succ 2 l.length, Nat.pow_succ 2 (totalValuation l),
            Nat.mul_add 6, Nat.mul_add (2 ^ l.length * 2),
            hSB, hTS1, hTS2]
        omega
      have hrhs6 : 6 * (2 ^ totalValuation l * 3 ^ l.length) =
          2 ^ (totalValuation l + 1) * 3 ^ (l.length + 1) := by
        rw [Nat.pow_succ 2 (totalValuation l), Nat.pow_succ 3 l.length,
            Nat.mul_comm (2 ^ totalValuation l) 2,
            Nat.mul_assoc 2 (2 ^ totalValuation l) (3 ^ l.length * 3),
            ← Nat.mul_assoc (2 ^ totalValuation l) (3 ^ l.length) 3,
            Nat.mul_comm (2 ^ totalValuation l * 3 ^ l.length) 3,
            ← Nat.mul_assoc 2 3 (2 ^ totalValuation l * 3 ^ l.length)]
      rw [hlhs6, hrhs6] at hmul6
      have h2_le_3 : 2 ^ (l.length + 1) ≤ 3 ^ (l.length + 1) :=
        pow_le_pow_of_le 2 3 (l.length + 1) (by decide)
      have hpow_K1_le : 2 ^ (totalValuation l + 1) ≤ 2 ^ (totalValuation l + k + 1) :=
        two_pow_le_two_pow (totalValuation l + 1) (totalValuation l + k + 1) (by omega)
      have hdiff_le := Nat.mul_le_mul_right (3 ^ (l.length + 1) - 2 ^ (l.length + 1)) hpow_K1_le
      rw [Nat.mul_sub, Nat.mul_sub] at hdiff_le
      have hsub1 : 2 ^ (totalValuation l + 1) * 2 ^ (l.length + 1) ≤
          2 ^ (totalValuation l + 1) * 3 ^ (l.length + 1) :=
        Nat.mul_le_mul_left _ h2_le_3
      have hsub2 : 2 ^ (totalValuation l + k + 1) * 2 ^ (l.length + 1) ≤
          2 ^ (totalValuation l + k + 1) * 3 ^ (l.length + 1) :=
        Nat.mul_le_mul_left _ h2_le_3
      omega
    exact ⟨by omega, hlow_step, hhigh_step⟩
  have hacc : ∀ (rem pfx : List Nat), P pfx → P (pfx ++ rem) := by
    intro rem
    induction rem with
    | nil =>
      intro pfx hp
      rw [List.append_nil]
      exact hp
    | cons k tl ih =>
      intro pfx hp
      have hcons : pfx ++ (k :: tl) = (pfx ++ [k]) ++ tl := by simp
      rw [hcons]
      exact ih (pfx ++ [k]) (hsnoc pfx k hp)
  exact hacc ks [] hnil

/-- Goodstein 2-Adic Tail Rank Decay Law Across Expanding Runs (`allTrueWord_goodstein_plus_one_law`):
    Along an expanding run `allTrueWord a` of `a` consecutive odd steps (where the visible integer
    `n` strictly increases), the shifted value `n + 1` satisfies
    `2 ^ a * (applyParityWord n (allTrueWord a) + 1) = 3 ^ a * (n + 1)` and `n + 1 ≥ 2 ^ a`,
    consuming `a` factors of `2` from `n + 1` and forcing an exit to an even step within `≤ n` steps. -/
theorem allTrueWord_goodstein_plus_one_law (a n : Nat)
    (hv : validParityWord n (allTrueWord a)) :
    2 ^ a * (applyParityWord n (allTrueWord a) + 1) = 3 ^ a * (n + 1) ∧
    n + 1 ≥ 2 ^ a := by
  have hid := parityWord_affine_identity (allTrueWord a) n hv
  have hD := wordD_allTrueWord_eq a
  have hA := wordA_allTrueWord_eq a
  have hB := wordB_allTrueWord_add_wordD a
  rw [hD, hA] at hid hB
  have hge := validParityWord_allTrueWord_ge a n hv
  rw [hD] at hge
  refine ⟨?_, hge⟩
  rw [Nat.mul_add, Nat.mul_one, Nat.mul_add, Nat.mul_one]
  omega

/-- Four-Color Reducible 1-Circuit Configuration Theorem (`oneCircuitWord_reducible_descent`):
    Every contracting 1-circuit configuration `oneCircuitWord a k = allTrueWord a ++ replicate k false`
    (`a ≥ 1`, `2^{a+k} > 3^a`) satisfying `a = 1 ∨ (2^{a+k} - 3^a) * (2^a - 1) > 3^a - 2^a`
    is unconditionally reducible: EVERY integer `n > 1` realizing `oneCircuitWord a k` strictly
    descends below `n` (`applyParityWord n (oneCircuitWord a k) < n`). -/
theorem oneCircuitWord_reducible_descent (a k n : Nat)
    (ha : a ≥ 1) (hn1 : n > 1)
    (hv : validParityWord n (oneCircuitWord a k))
    (hcont : 2 ^ (a + k) > 3 ^ a)
    (hred : a = 1 ∨ (2 ^ (a + k) - 3 ^ a) * (2 ^ a - 1) > 3 ^ a - 2 ^ a) :
    applyParityWord n (oneCircuitWord a k) < n := by
  rcases oneCircuitWord_coefficients a k with ⟨hA, hD, hB⟩
  have hcont_w : wordD (oneCircuitWord a k) > wordA (oneCircuitWord a k) := by
    rw [hD, hA]; exact hcont
  rw [contracting_word_descent_iff (oneCircuitWord a k) n hv hcont_w, hD, hA]
  have hB_eq : wordB (oneCircuitWord a k) = 3 ^ a - 2 ^ a := by omega
  rw [hB_eq]
  rcases hred with rfl | hgt_red
  · have hdelta_pos : 2 ^ (1 + k) - 3 ^ 1 ≥ 1 := by omega
    have hmul : (2 ^ (1 + k) - 3 ^ 1) * 2 ≤ (2 ^ (1 + k) - 3 ^ 1) * n :=
      Nat.mul_le_mul_left (2 ^ (1 + k) - 3 ^ 1) (by omega)
    omega
  · have hv_allTrue : validParityWord n (allTrueWord a) :=
      ((validParityWord_append (allTrueWord a) (List.replicate k false) n).mp hv).1
    have hn_ge : n + 1 ≥ 2 ^ a :=
      (allTrueWord_goodstein_plus_one_law a n hv_allTrue).2
    have hn_ge' : n ≥ 2 ^ a - 1 := by omega
    have hmul : (2 ^ (a + k) - 3 ^ a) * (2 ^ a - 1) ≤ (2 ^ (a + k) - 3 ^ a) * n :=
      Nat.mul_le_mul_left (2 ^ (a + k) - 3 ^ a) hn_ge'
    omega

/-- Formal Falsification Witness CE-C10-05 (`trivial_cycle_repeat_divides_offset_witness`):
    Proves that the threshold `wordB w > wordDelta w` (for `returnMapWord ks`, where `n = 1`
    realizes `ks = [1, 1]` with `Δ = 7, B = 7`) and `wordB w > 2 * wordDelta w` (for general parity
    words, where `n = 2` realizes `w = [false, true]` with `Δ = 1, B = 2`) cannot be omitted
    from `noNontrivialCycle_iff_offset_nondivisibility`. -/
theorem trivial_cycle_repeat_divides_offset_witness :
    let w1 := returnMapWord [1, 1]
    let w2 := [false, true]
    (wordD w1 > wordA w1 ∧
     wordB w1 = wordDelta w1 ∧
     wordB w1 % wordDelta w1 = 0) ∧
    (wordD w2 > wordA w2 ∧
     wordB w2 = 2 * wordDelta w2 ∧
     wordB w2 % wordDelta w2 = 0) := by
  decide

/-- Formal Falsification Witness CE-C10-06 (`contracting_odd_block_survives_above_initial_at_27`):
    Proves that encountering a contracting odd-to-odd return block (`k_j ≥ 1`, where `u_{j+1} < u_j`)
    does NOT by itself force immediate descent below the starting integer `n`:
    for `n = 27`, `ks = [0, 1]` is a genuine odd-to-odd return sequence with `u_1 = 41 > 27`,
    `k_1 = 1 ≥ 1`, and `u_2 = 31 < 41`, yet `u_2 = 31 > 27`. -/
theorem contracting_odd_block_survives_above_initial_at_27 :
    validOddReturnSeq 27 [0] ∧
    applyParityWord 27 (returnMapWord [0]) = 41 ∧
    validOddReturnSeq 27 [0, 1] ∧
    applyParityWord 27 (returnMapWord [0, 1]) = 31 ∧
    31 < 41 ∧ 31 > 27 := by
  dsimp [validOddReturnSeq, returnMapWord, singleOddWord, validParityWord,
         stepParityMatches, acceleratedCollatz, applyParityWord]
  decide

/-! ## Section 12: Cyclic Rotation Algebra, Unavoidable Reducibility Thresholds,
    Goodstein Run-Exit Dichotomy, and Targeted Falsifications (CE-C10-07..09) -/

/-- Cyclic invariance of `wordD` (`wordD_append_comm`):
    `wordD (w1 ++ w2) = wordD (w2 ++ w1)`. -/
theorem wordD_append_comm (w1 w2 : List Bool) :
    wordD (w1 ++ w2) = wordD (w2 ++ w1) := by
  rw [wordD_append, wordD_append, Nat.mul_comm]

/-- Cyclic invariance of `wordA` (`wordA_append_comm`):
    `wordA (w1 ++ w2) = wordA (w2 ++ w1)`. -/
theorem wordA_append_comm (w1 w2 : List Bool) :
    wordA (w1 ++ w2) = wordA (w2 ++ w1) := by
  rw [wordA_append, wordA_append, Nat.mul_comm]

/-- Cyclic invariance of the cycle denominator `wordDelta` (`wordDelta_append_comm`):
    `wordDelta (w1 ++ w2) = wordDelta (w2 ++ w1)`. -/
theorem wordDelta_append_comm (w1 w2 : List Bool) :
    wordDelta (w1 ++ w2) = wordDelta (w2 ++ w1) := by
  unfold wordDelta
  rw [wordD_append_comm, wordA_append_comm]

/-- Universal Cyclic Shift Identity for Parity-Word Offsets (`wordB_cyclic_shift_identity`):
    Rotating a split parity word `w1 ++ w2` to `w2 ++ w1` (when `wordD (w1 ++ w2) ≥ wordA (w1 ++ w2)`)
    transforms the affine offset by the exact linear law:
    `wordD w1 * wordB (w2 ++ w1) = wordA w1 * wordB (w1 ++ w2) + wordDelta (w1 ++ w2) * wordB w1`. -/
theorem wordB_cyclic_shift_identity (w1 w2 : List Bool)
    (hcont : wordD (w1 ++ w2) ≥ wordA (w1 ++ w2)) :
    wordD w1 * wordB (w2 ++ w1) =
      wordA w1 * wordB (w1 ++ w2) + wordDelta (w1 ++ w2) * wordB w1 := by
  unfold wordDelta
  rw [wordB_append w2 w1, wordB_append w1 w2,
      wordD_append w1 w2, wordA_append w1 w2,
      Nat.mul_add (wordD w1), Nat.mul_add (wordA w1),
      Nat.sub_mul]
  rw [wordD_append w1 w2, wordA_append w1 w2] at hcont
  have hle : (wordA w1 * wordA w2) * wordB w1 ≤ (wordD w1 * wordD w2) * wordB w1 :=
    Nat.mul_le_mul_right (wordB w1) hcont
  have h1 : wordD w1 * (wordA w1 * wordB w2) = wordA w1 * (wordD w1 * wordB w2) := by
    rw [← Nat.mul_assoc (wordD w1) (wordA w1) (wordB w2),
        Nat.mul_comm (wordD w1) (wordA w1),
        Nat.mul_assoc (wordA w1) (wordD w1) (wordB w2)]
  have h2 : wordD w1 * (wordD w2 * wordB w1) = (wordD w1 * wordD w2) * wordB w1 := by
    rw [Nat.mul_assoc]
  have h3 : wordA w1 * (wordA w2 * wordB w1) = (wordA w1 * wordA w2) * wordB w1 := by
    rw [Nat.mul_assoc]
  omega

/-- Single-Block Cyclic Rotation Law for Return-Map Offsets (`returnMap_cyclic_rotate_one_offset_law`):
    Rotating the head block `k` of `k :: tl` to the tail `tl ++ [k]` preserves length `s = tl.length + 1`
    and total valuation `K = totalValuation (k :: tl)`, and when `2^K ≥ 3^s`, satisfies:
    `2 ^ (k + 1) * wordB (returnMapWord (tl ++ [k])) = 3 * wordB (returnMapWord (k :: tl)) + (2 ^ K - 3 ^ s)`. -/
theorem returnMap_cyclic_rotate_one_offset_law (k : Nat) (tl : List Nat)
    (hcont : 2 ^ totalValuation (k :: tl) ≥ 3 ^ (k :: tl).length) :
    2 ^ (k + 1) * wordB (returnMapWord (tl ++ [k])) =
      3 * wordB (returnMapWord (k :: tl)) +
        (2 ^ totalValuation (k :: tl) - 3 ^ (k :: tl).length) := by
  have hcons_eq : returnMapWord (k :: tl) = singleOddWord k ++ returnMapWord tl := rfl
  have hsnoc_eq : returnMapWord (tl ++ [k]) = returnMapWord tl ++ singleOddWord k :=
    returnMapWord_snoc tl k
  have hD_cons : wordD (singleOddWord k ++ returnMapWord tl) = 2 ^ totalValuation (k :: tl) :=
    wordD_returnMapWord (k :: tl)
  have hA_cons : wordA (singleOddWord k ++ returnMapWord tl) = 3 ^ (k :: tl).length :=
    wordA_returnMapWord (k :: tl)
  have hcont_w : wordD (singleOddWord k ++ returnMapWord tl) ≥
      wordA (singleOddWord k ++ returnMapWord tl) := by
    rw [hD_cons, hA_cons]; exact hcont
  have hshift := wordB_cyclic_shift_identity (singleOddWord k) (returnMapWord tl) hcont_w
  have hD1 : wordD (singleOddWord k) = 2 ^ (k + 1) := by
    rw [wordD_eq_pow_two_length]; dsimp [singleOddWord]; rw [List.length_replicate]
  have hA1 : wordA (singleOddWord k) = 3 := wordA_singleOddWord k
  have hB1 : wordB (singleOddWord k) = 1 := by
    dsimp [singleOddWord, wordB]; rw [wordA_replicate_false, wordB_replicate_false]
  unfold wordDelta at hshift
  rw [hD1, hA1, hB1, hD_cons, hA_cons, ← hcons_eq, ← hsnoc_eq, Nat.mul_one] at hshift
  exact hshift

/-- Cycle Rotation Quotient Shift & Automatic Rotated Divisibility
    (`cycle_rotation_quotient_shift_and_divisibility`):
    If `n0` is an integer cycle fixed point of `w1 ++ w2` (`wordDelta (w1 ++ w2) * n0 = wordB (w1 ++ w2)`
    with `wordD (w1 ++ w2) > wordA (w1 ++ w2)`), then the intermediate orbit state
    `n1 = applyParityWord n0 w1` is an exact integer cycle fixed point of the rotated word `w2 ++ w1`:
    1. `wordDelta (w2 ++ w1) * n1 = wordB (w2 ++ w1)`,
    2. `wordB (w2 ++ w1) % wordDelta (w2 ++ w1) = 0`, and
    3. `n0 ≤ n1 ↔ wordB (w1 ++ w2) ≤ wordB (w2 ++ w1)`. -/
theorem cycle_rotation_quotient_shift_and_divisibility (w1 w2 : List Bool) (n0 : Nat)
    (hcont : wordD (w1 ++ w2) > wordA (w1 ++ w2))
    (hcyc : wordDelta (w1 ++ w2) * n0 = wordB (w1 ++ w2)) :
    let n1 := applyParityWord n0 w1
    wordDelta (w2 ++ w1) * n1 = wordB (w2 ++ w1) ∧
    wordB (w2 ++ w1) % wordDelta (w2 ++ w1) = 0 ∧
    (n0 ≤ n1 ↔ wordB (w1 ++ w2) ≤ wordB (w2 ++ w1)) := by
  dsimp
  have haff : wordD (w1 ++ w2) * n0 = wordA (w1 ++ w2) * n0 + wordB (w1 ++ w2) := by
    unfold wordDelta at hcyc
    have hsub := Nat.sub_mul (wordD (w1 ++ w2)) (wordA (w1 ++ w2)) n0
    have hle : wordA (w1 ++ w2) * n0 ≤ wordD (w1 ++ w2) * n0 :=
      Nat.mul_le_mul_right n0 (by omega)
    omega
  have hv12 : validParityWord n0 (w1 ++ w2) :=
    ((affine_identity_iff_validParityWord_and_output (w1 ++ w2) n0 n0).mp haff).1
  have hv1 : validParityWord n0 w1 := ((validParityWord_append w1 w2 n0).mp hv12).1
  have hid1 := parityWord_affine_identity w1 n0 hv1
  have hshift := wordB_cyclic_shift_identity w1 w2 (by omega)
  have hmul : wordD w1 * (wordDelta (w1 ++ w2) * applyParityWord n0 w1) =
      wordD w1 * wordB (w2 ++ w1) := by
    have hstep1 : wordD w1 * (wordDelta (w1 ++ w2) * applyParityWord n0 w1) =
        wordDelta (w1 ++ w2) * (wordD w1 * applyParityWord n0 w1) := by
      rw [← Nat.mul_assoc (wordD w1) (wordDelta (w1 ++ w2)) (applyParityWord n0 w1),
          Nat.mul_comm (wordD w1) (wordDelta (w1 ++ w2)),
          Nat.mul_assoc (wordDelta (w1 ++ w2)) (wordD w1) (applyParityWord n0 w1)]
    have hstep2 : wordDelta (w1 ++ w2) * (wordA w1 * n0) =
        wordA w1 * (wordDelta (w1 ++ w2) * n0) := by
      rw [← Nat.mul_assoc (wordDelta (w1 ++ w2)) (wordA w1) n0,
          Nat.mul_comm (wordDelta (w1 ++ w2)) (wordA w1),
          Nat.mul_assoc (wordA w1) (wordDelta (w1 ++ w2)) n0]
    rw [hstep1, hid1, Nat.mul_add, hstep2, hcyc, ← hshift]
  have hD1_pos : wordD w1 > 0 := wordD_pos w1
  have hrot_eq1 : wordDelta (w1 ++ w2) * applyParityWord n0 w1 = wordB (w2 ++ w1) :=
    Nat.eq_of_mul_eq_mul_left hD1_pos hmul
  have hrot_eq : wordDelta (w2 ++ w1) * applyParityWord n0 w1 = wordB (w2 ++ w1) := by
    rw [← wordDelta_append_comm w1 w2]
    exact hrot_eq1
  have hdiv : wordB (w2 ++ w1) % wordDelta (w2 ++ w1) = 0 := by
    rw [← hrot_eq, Nat.mul_comm, Nat.mul_mod_left]
  have hdelta_pos : wordDelta (w1 ++ w2) > 0 := by
    unfold wordDelta; omega
  have hord : n0 ≤ applyParityWord n0 w1 ↔ wordB (w1 ++ w2) ≤ wordB (w2 ++ w1) := by
    rw [← hcyc, ← hrot_eq1]
    constructor
    · intro hle
      exact Nat.mul_le_mul_left (wordDelta (w1 ++ w2)) hle
    · intro hle
      exact Nat.le_of_mul_le_mul_left hle hdelta_pos
  exact ⟨hrot_eq, hdiv, hord⟩

/-- Cycle Minimum vs. Maximum Rotation Valuation Dichotomy
    (`cycle_extremal_rotation_first_valuation_dichotomy`):
    For any odd integer `n0 > 1` realizing `singleOddWord k` with output
    `n1 = applyParityWord n0 (singleOddWord k)`:
    1. If `n0 ≤ n1` (e.g., at the minimum odd element of a nontrivial cycle), then `k = 0`
       (`2 ^ (k + 1) * n1 = 3 * n0 + 1` forces an expanding block `k = 0`).
    2. If `n1 ≤ n0` (e.g., at the maximum odd element of a cycle), then `k ≥ 1`. -/
theorem cycle_extremal_rotation_first_valuation_dichotomy (k n0 : Nat)
    (hn0 : n0 > 1)
    (hv : validParityWord n0 (singleOddWord k)) :
    let n1 := applyParityWord n0 (singleOddWord k)
    (n0 ≤ n1 → k = 0) ∧ (n1 ≤ n0 → k ≥ 1) := by
  dsimp
  rcases singleOddWord_step_dichotomy k n0 hn0 hv with ⟨_, h0, h1⟩
  constructor
  · intro hle
    cases k with
    | zero => rfl
    | succ k' =>
      have hlt := h1 (by omega)
      omega
  · intro hle
    cases k with
    | zero =>
      have hgt := h0 rfl
      omega
    | succ k' => omega

/-- Universal Multi-Circuit Sandwich Reducibility (`returnMap_universal_sandwich_reducible_descent`):
    For ANY valuation sequence `ks : List Nat` (arbitrary number of circuits and arbitrary block
    ordering) with `s = ks.length`, `K = totalValuation ks`, and `2 ^ K > 3 ^ s`:
    every integer `n` realizing `returnMapWord ks` that satisfies
    `(2 ^ K - 3 ^ s) * (2 ^ s * n) > 2 ^ K * (3 ^ s - 2 ^ s)`
    strictly descends below `n` (`applyParityWord n (returnMapWord ks) < n`). -/
theorem returnMap_universal_sandwich_reducible_descent (ks : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord ks))
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length)
    (hred : (2 ^ totalValuation ks - 3 ^ ks.length) * (2 ^ ks.length * n) >
      2 ^ totalValuation ks * (3 ^ ks.length - 2 ^ ks.length)) :
    applyParityWord n (returnMapWord ks) < n := by
  have hD := wordD_returnMapWord ks
  have hA := wordA_returnMapWord ks
  have hcont_w : wordD (returnMapWord ks) > wordA (returnMapWord ks) := by
    rw [hD, hA]; exact hcont
  rw [contracting_word_descent_iff (returnMapWord ks) n hv hcont_w, hD, hA]
  rcases returnMap_offset_extremal_sandwich ks with ⟨_, _, hhigh⟩
  have h2_le_3 : 2 ^ ks.length ≤ 3 ^ ks.length :=
    pow_le_pow_of_le 2 3 ks.length (by decide)
  have hsub : 2 ^ totalValuation ks * (3 ^ ks.length - 2 ^ ks.length) =
      2 ^ totalValuation ks * 3 ^ ks.length - 2 ^ totalValuation ks * 2 ^ ks.length :=
    Nat.mul_sub (2 ^ totalValuation ks) (3 ^ ks.length) (2 ^ ks.length)
  have hle_B : 2 ^ ks.length * wordB (returnMapWord ks) ≤
      2 ^ totalValuation ks * (3 ^ ks.length - 2 ^ ks.length) := by
    omega
  have hlt_mul : 2 ^ ks.length * wordB (returnMapWord ks) <
      2 ^ ks.length * ((2 ^ totalValuation ks - 3 ^ ks.length) * n) := by
    have hcomm : (2 ^ totalValuation ks - 3 ^ ks.length) * (2 ^ ks.length * n) =
        2 ^ ks.length * ((2 ^ totalValuation ks - 3 ^ ks.length) * n) := by
      rw [← Nat.mul_assoc (2 ^ totalValuation ks - 3 ^ ks.length) (2 ^ ks.length) n,
          Nat.mul_comm (2 ^ totalValuation ks - 3 ^ ks.length) (2 ^ ks.length),
          Nat.mul_assoc (2 ^ ks.length) (2 ^ totalValuation ks - 3 ^ ks.length) n]
    omega
  exact Nat.lt_of_mul_lt_mul_left hlt_mul

/-- Reservoir-Threshold Unconditional Reducibility on Non-Descending Prefixes
    (`nondescent_prefix_reservoir_threshold_reducible_descent`):
    If a trajectory starting at `n ≥ 1` remains non-descending up to step `r`
    (`∀ j < r, iterateAccelerated n j ≥ n`), and its cumulative parameters `(r, a_r)`
    cross the reservoir threshold `2 ^ r * n ^ a_r > (3 * n + 1) ^ a_r`, then
    strict descent `iterateAccelerated n r < n` is unconditionally forced at step `r`
    with ZERO pincer exceptions. -/
theorem nondescent_prefix_reservoir_threshold_reducible_descent (n r : Nat)
    (hn : n ≥ 1)
    (hnd : ∀ j : Nat, j < r → iterateAccelerated n j ≥ n)
    (hthr : 2 ^ r * n ^ wordOnes (parityWordOf r n) >
      (3 * n + 1) ^ wordOnes (parityWordOf r n)) :
    iterateAccelerated n r < n := by
  let a := wordOnes (parityWordOf r n)
  have hcons : deficitReservoir n r + 2 ^ r * n ^ a * iterateAccelerated n r =
      n * (3 * n + 1) ^ a :=
    reservoir_surplus_conservation_law n r hnd
  have hmul_lt : n * (3 * n + 1) ^ a < n * (2 ^ r * n ^ a) :=
    Nat.mul_lt_mul_of_pos_left hthr (by omega)
  have hlt : (2 ^ r * n ^ a) * iterateAccelerated n r < (2 ^ r * n ^ a) * n := by
    have hcomm : n * (2 ^ r * n ^ a) = (2 ^ r * n ^ a) * n := Nat.mul_comm _ _
    omega
  exact Nat.lt_of_mul_lt_mul_left hlt

/-- Exact Goodstein Branch & Run-Exit Dichotomy Modulo 4 (`odd_step_goodstein_branch_dichotomy`):
    For every odd integer `u` (`u % 2 = 1`):
    1. `u % 4 = 3 ↔ acceleratedCollatz u % 2 = 1` (so `k = 0`, the Goodstein odd run continues,
       and `2 * (acceleratedCollatz u + 1) = 3 * (u + 1)`),
    2. `u % 4 = 1 ↔ acceleratedCollatz u % 2 = 0` (so `k ≥ 1`, the Goodstein odd run terminates
       and forces at least one even division). -/
theorem odd_step_goodstein_branch_dichotomy (u : Nat) (hodd : u % 2 = 1) :
    2 * (acceleratedCollatz u + 1) = 3 * (u + 1) ∧
    (u % 4 = 3 ↔ acceleratedCollatz u % 2 = 1) ∧
    (u % 4 = 1 ↔ acceleratedCollatz u % 2 = 0) := by
  unfold acceleratedCollatz
  rw [if_neg (by omega : ¬(u % 2 = 0))]
  omega

/-- Shifted `u + 1` Identity Across a General Return Block (`singleOddWord_shifted_plus_one_identity`):
    Across `singleOddWord k` realized by `u`, the shifted state `u + 1` satisfies
    `2 ^ (k + 1) * (applyParityWord u (singleOddWord k) + 1) = 3 * (u + 1) + 2 ^ (k + 1) - 2`. -/
theorem singleOddWord_shifted_plus_one_identity (k u : Nat)
    (hv : validParityWord u (singleOddWord k)) :
    2 ^ (k + 1) * (applyParityWord u (singleOddWord k) + 1) =
      3 * (u + 1) + 2 ^ (k + 1) - 2 := by
  have hid := parityWord_affine_identity (singleOddWord k) u hv
  have hD : wordD (singleOddWord k) = 2 ^ (k + 1) := by
    rw [wordD_eq_pow_two_length]; dsimp [singleOddWord]; rw [List.length_replicate]
  have hA : wordA (singleOddWord k) = 3 := wordA_singleOddWord k
  have hB : wordB (singleOddWord k) = 1 := by
    dsimp [singleOddWord, wordB]; rw [wordA_replicate_false, wordB_replicate_false]
  rw [hD, hA, hB] at hid
  have hpow : 2 ^ (k + 1) ≥ 2 := by
    have h1 := two_pow_le_two_pow 1 (k + 1) (by omega)
    omega
  rw [Nat.mul_add, Nat.mul_one, Nat.mul_add, Nat.mul_one]
  omega

/-- Formal Falsification Witness CE-C10-07
    (`cyclic_rotation_preserves_divisibility_and_shifts_offset_witness`):
    Demonstrates on `ks = [0, 1, 2]` and its cyclic rotations `[1, 2, 0]` and `[2, 0, 1]`
    (`s = 3, K = 6, Δ = 64 - 27 = 37`) that:
    1. Every cyclic rotation satisfies `2 ^ (k + 1) * B(rot_1(ks)) = 3 * B(ks) + Δ`,
    2. Because `gcd(2 ^ (k + 1), Δ) = 1`, modular divisibility `d | B(ks)` is invariant across all
       rotations (so cyclic rotation does not create new modular divisors on `1`-cycle repeats like
       `ks = [1, 1, 1]` where `Δ = 37, B = 37`),
    3. Instead, cyclic rotation breaks symmetry through the strict integer ordering of the offsets:
       `B([0, 1, 2]) = 23 < B([2, 0, 1]) = 49 < B([1, 2, 0]) = 53`. -/
theorem cyclic_rotation_preserves_divisibility_and_shifts_offset_witness :
    let ks0 := [0, 1, 2]
    let ks1 := [1, 2, 0]
    let ks2 := [2, 0, 1]
    wordDelta (returnMapWord ks0) = 37 ∧
    wordB (returnMapWord ks0) = 23 ∧
    wordB (returnMapWord ks1) = 53 ∧
    wordB (returnMapWord ks2) = 49 ∧
    2 ^ 1 * wordB (returnMapWord ks1) = 3 * wordB (returnMapWord ks0) + 37 ∧
    2 ^ 2 * wordB (returnMapWord ks2) = 3 * wordB (returnMapWord ks1) + 37 ∧
    2 ^ 3 * wordB (returnMapWord ks0) = 3 * wordB (returnMapWord ks2) + 37 ∧
    wordB (returnMapWord ks0) < wordB (returnMapWord ks2) ∧
    wordB (returnMapWord ks2) < wordB (returnMapWord ks1) := by
  decide

/-- Formal Falsification Witness CE-C10-08
    (`contracting_odd_return_word_survives_at_165_witness`):
    Falsifies the naive strengthening that EVERY globally contracting complete odd-to-odd
    return sequence (`validOddReturnSeq n ks` with `2 ^ K_s > 3 ^ s` and `n > 1`) forces `u_s < n`:
    at `n = 165`, `ks = [3, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 2]` has `s = 17`,
    `K_17 = 27`, and `2 ^ 27 = 134217728 > 129140163 = 3 ^ 17`, yet `u_17 = 167 > 165`
    (because the first block `k_0 = 3` drops `165 → 31 < 165`, violating prefix non-descent). -/
theorem contracting_odd_return_word_survives_at_165_witness :
    let ks := [3, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 2]
    ks.length = 17 ∧
    totalValuation ks = 27 ∧
    2 ^ 27 > 3 ^ 17 ∧
    validOddReturnSeq 165 ks ∧
    applyParityWord 165 (returnMapWord [3]) = 31 ∧
    31 < 165 ∧
    applyParityWord 165 (returnMapWord ks) = 167 ∧
    167 > 165 := by
  dsimp [validOddReturnSeq, totalValuation, returnMapWord, singleOddWord, validParityWord,
         stepParityMatches, acceleratedCollatz, applyParityWord]
  decide

/-- Formal Falsification Witness CE-C10-09
    (`goodstein_tail_rank_resets_above_initial_at_27_witness`):
    Falsifies any purely local lexicographic rank built solely from `(u_s, v_2(u_s + 1))`
    across completed odd-to-odd circuits: at `n = 27` (`u_0 = 27`, where `27 + 1 = 28 = 4 * 7`
    has `v_2(u_0 + 1) = 2`), after the 2-block circuit `ks = [0, 1]` (`27 → 41 → 31`),
    `u_2 = 31 > 27` AND `u_2 + 1 = 32 = 2 ^ 5` resets the 2-adic tail valuation to
    `v_2(u_2 + 1) = 5 > 2 = v_2(u_0 + 1)`. -/
theorem goodstein_tail_rank_resets_above_initial_at_27_witness :
    let u0 := 27
    let u1 := applyParityWord 27 (returnMapWord [0])
    let u2 := applyParityWord 27 (returnMapWord [0, 1])
    u1 = 41 ∧ u2 = 31 ∧
    (u0 + 1) % 4 = 0 ∧ (u0 + 1) % 8 ≠ 0 ∧
    (u1 + 1) % 2 = 0 ∧ (u1 + 1) % 4 ≠ 0 ∧
    (u2 + 1) = 2 ^ 5 ∧
    u2 > u0 := by
  decide

/-! ## Section 13: Two-Branch First-Crossing vs. Indefinite-Expansion Architecture,
    Universal First-Crossing Offset Cap, and Finite Survivor Trap -/

/-- Recursive predicate `preCrossingFrom j K ks` checking that every proper prefix of `ks`
    (starting at block index `j` and cumulative valuation `K`) satisfies `2 ^ K_m ≤ 3 ^ m`. -/
def preCrossingFrom (j K : Nat) : List Nat → Prop
  | [] => True
  | k :: tl => (2 ^ K ≤ 3 ^ j) ∧ preCrossingFrom (j + 1) (K + k + 1) tl

/-- `PreCrossingReturnSeq ks` holds when every proper prefix `0 ≤ j < ks.length` of `ks`
    remains spectrally non-contracting (`2 ^ K_j ≤ 3 ^ j`). -/
def PreCrossingReturnSeq (ks : List Nat) : Prop :=
  preCrossingFrom 0 0 ks

/-- Right-append (`snoc`) decomposition for `preCrossingFrom` (`preCrossingFrom_snoc`). -/
theorem preCrossingFrom_snoc (ks : List Nat) (k : Nat) :
    ∀ j K : Nat,
      preCrossingFrom j K (ks ++ [k]) ↔
        (preCrossingFrom j K ks ∧ 2 ^ (K + totalValuation ks) ≤ 3 ^ (j + ks.length)) := by
  induction ks with
  | nil =>
    intro j K
    dsimp [preCrossingFrom, totalValuation, returnMapWord, singleOddWord]
    constructor
    · intro h; exact ⟨trivial, h.1⟩
    · intro h; exact ⟨h.2, trivial⟩
  | cons x tl ih =>
    intro j K
    dsimp [preCrossingFrom]
    rw [ih (j + 1) (K + x + 1), totalValuation_cons x tl]
    have hK : K + x + 1 + totalValuation tl = K + (x + 1 + totalValuation tl) := by omega
    have hj : j + 1 + tl.length = j + (tl.length + 1) := by omega
    rw [hK, hj]
    constructor
    · intro h; exact ⟨⟨h.1, h.2.1⟩, h.2.2⟩
    · intro h; exact ⟨h.1.1, ⟨h.1.2, h.2⟩⟩

/-- Right-append (`snoc`) characterization of `PreCrossingReturnSeq` (`preCrossingReturnSeq_snoc`):
    `PreCrossingReturnSeq (ks ++ [k]) ↔ PreCrossingReturnSeq ks ∧ 2 ^ totalValuation ks ≤ 3 ^ ks.length`. -/
theorem preCrossingReturnSeq_snoc (ks : List Nat) (k : Nat) :
    PreCrossingReturnSeq (ks ++ [k]) ↔
      (PreCrossingReturnSeq ks ∧ 2 ^ totalValuation ks ≤ 3 ^ ks.length) := by
  unfold PreCrossingReturnSeq
  rw [preCrossingFrom_snoc ks k 0 0, Nat.zero_add, Nat.zero_add]

/-- Universal Pre-Crossing Return-Map Offset Cap (`preCrossing_returnMap_offset_upper_bound`):
    Whereas a general return word of length `s` and valuation `K` can have offset as large as
    `2 ^ (K - s) * (3 ^ s - 2 ^ s)`, ANY return word `ks` whose proper prefixes have not yet
    crossed (`PreCrossingReturnSeq ks`, i.e., `∀ j < s, 2 ^ K_j ≤ 3 ^ j`) satisfies the
    valuation-independent linear-exponential cap:
    `3 * wordB (returnMapWord ks) ≤ ks.length * 3 ^ ks.length`
    and `wordB (returnMapWord ks) ≤ ks.length * 3 ^ (ks.length - 1)`. -/
theorem preCrossing_returnMap_offset_upper_bound (ks : List Nat)
    (hpre : PreCrossingReturnSeq ks) :
    3 * wordB (returnMapWord ks) ≤ ks.length * 3 ^ ks.length ∧
    wordB (returnMapWord ks) ≤ ks.length * 3 ^ (ks.length - 1) := by
  let P := fun (l : List Nat) =>
    PreCrossingReturnSeq l →
      3 * wordB (returnMapWord l) ≤ l.length * 3 ^ l.length
  have hnil : P [] := by
    intro _
    dsimp [returnMapWord, wordB]
    omega
  have hsnoc : ∀ (l : List Nat) (k : Nat), P l → P (l ++ [k]) := by
    intro l k ih hpre_lk
    rcases (preCrossingReturnSeq_snoc l k).mp hpre_lk with ⟨hpre_l, hK_le⟩
    have hB_l := ih hpre_l
    have hlen : (l ++ [k]).length = l.length + 1 := by
      rw [List.length_append]; rfl
    have hB_snoc := wordB_returnMapWord_snoc l k
    rw [hlen, hB_snoc, Nat.pow_succ 3 l.length]
    have hstep1 : wordB (returnMapWord (l ++ [k])) ≤ (l.length + 1) * 3 ^ l.length := by
      rw [hB_snoc, Nat.add_mul, Nat.one_mul]
      omega
    have hmul : (l.length + 1) * (3 ^ l.length * 3) =
        3 * ((l.length + 1) * 3 ^ l.length) := by
      rw [← Nat.mul_assoc (l.length + 1) (3 ^ l.length) 3,
          Nat.mul_comm ((l.length + 1) * 3 ^ l.length) 3]
    omega
  have hacc : ∀ (rem pfx : List Nat), P pfx → P (pfx ++ rem) := by
    intro rem
    induction rem with
    | nil =>
      intro pfx hp
      rw [List.append_nil]
      exact hp
    | cons k tl ih =>
      intro pfx hp
      have hcons : pfx ++ (k :: tl) = (pfx ++ [k]) ++ tl := by simp
      rw [hcons]
      exact ih (pfx ++ [k]) (hsnoc pfx k hp)
  have hmain : 3 * wordB (returnMapWord ks) ≤ ks.length * 3 ^ ks.length :=
    hacc ks [] hnil hpre
  refine ⟨hmain, ?_⟩
  cases hlen_cases : ks.length with
  | zero =>
    have hnil_ks : ks = [] := List.eq_nil_of_length_eq_zero hlen_cases
    subst hnil_ks
    dsimp [returnMapWord, wordB]
    omega
  | succ m =>
    rw [hlen_cases] at hmain
    rw [Nat.add_sub_cancel, Nat.pow_succ 3 m] at *
    have hcomm : (m + 1) * (3 ^ m * 3) = 3 * ((m + 1) * 3 ^ m) := by
      rw [← Nat.mul_assoc (m + 1) (3 ^ m) 3, Nat.mul_comm ((m + 1) * 3 ^ m) 3]
    omega

/-- First-Crossing Linear Offset Exclusion & Finite Survivor Trap
    (`first_crossing_linear_offset_exclusion`):
    For EVERY first-crossing return word `ks` (`PreCrossingReturnSeq ks` and `2 ^ K_s > 3 ^ s`),
    1. Every integer `n` realizing `returnMapWord ks` with `3 * ((2 ^ K_s - 3 ^ s) * n) > s * 3 ^ s`
       strictly descends below `n` (`applyParityWord n (returnMapWord ks) < n`), EVEN WITHOUT
       requiring intermediate non-descent `u_j ≥ n`.
    2. Conversely, any hypothetical survivor (`applyParityWord n (returnMapWord ks) ≥ n`) is trapped
       in the finite interval `3 * ((2 ^ K_s - 3 ^ s) * n) ≤ s * 3 ^ s` (`n ≤ s * 3^{s-1} / (2^{K_s} - 3^s)`). -/
theorem first_crossing_linear_offset_exclusion (ks : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord ks))
    (hpre : PreCrossingReturnSeq ks)
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length) :
    (3 * ((2 ^ totalValuation ks - 3 ^ ks.length) * n) > ks.length * 3 ^ ks.length →
      applyParityWord n (returnMapWord ks) < n) ∧
    (applyParityWord n (returnMapWord ks) ≥ n →
      3 * ((2 ^ totalValuation ks - 3 ^ ks.length) * n) ≤ ks.length * 3 ^ ks.length) := by
  have hD := wordD_returnMapWord ks
  have hA := wordA_returnMapWord ks
  have hcont_w : wordD (returnMapWord ks) > wordA (returnMapWord ks) := by
    rw [hD, hA]; exact hcont
  have hiff := contracting_word_descent_iff (returnMapWord ks) n hv hcont_w
  rw [hD, hA] at hiff
  have hcap := (preCrossing_returnMap_offset_upper_bound ks hpre).1
  constructor
  · intro hgt
    rw [hiff]
    omega
  · intro hge
    have hnot : ¬(applyParityWord n (returnMapWord ks) < n) := by omega
    rw [hiff] at hnot
    omega

/-- Branch 2 (No-First-Crossing / Indefinite Expansion) Shifted Growth & Non-Descent Law
    (`no_first_crossing_shifted_growth_and_nondescent`):
    For EVERY return word `ks` realized by `n`:
    1. `2 ^ K_s * (applyParityWord n (returnMapWord ks) + 1) ≥ 3 ^ s * (n + 1)`, and
    2. Whenever `s = ks.length ≥ 1` and `2 ^ K_s ≤ 3 ^ s` (in particular, at every step along the
       no-first-crossing branch `∀ s ≥ 1, 2 ^ K_s < 3 ^ s`), the odd return strictly exceeds `n`
       (`applyParityWord n (returnMapWord ks) > n`). -/
theorem no_first_crossing_shifted_growth_and_nondescent (ks : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord ks)) :
    2 ^ totalValuation ks * (applyParityWord n (returnMapWord ks) + 1) ≥
      3 ^ ks.length * (n + 1) ∧
    (ks.length ≥ 1 → 2 ^ totalValuation ks ≤ 3 ^ ks.length →
      applyParityWord n (returnMapWord ks) > n) := by
  have hid := parityWord_affine_identity (returnMapWord ks) n hv
  rw [wordD_returnMapWord, wordA_returnMapWord] at hid
  rcases returnMap_offset_extremal_sandwich ks with ⟨hK_ge_s, hlow, _⟩
  have hpow_le : 2 ^ ks.length ≤ 2 ^ totalValuation ks :=
    two_pow_le_two_pow ks.length (totalValuation ks) hK_ge_s
  have hshifted : 2 ^ totalValuation ks * (applyParityWord n (returnMapWord ks) + 1) ≥
      3 ^ ks.length * (n + 1) := by
    rw [Nat.mul_add, Nat.mul_one, Nat.mul_add, Nat.mul_one]
    omega
  refine ⟨hshifted, ?_⟩
  intro hs1 hle_exp
  have hB_pos : wordB (returnMapWord ks) ≥ 1 := by
    cases ks with
    | nil => dsimp at hs1; omega
    | cons k0 tl =>
      rw [wordB_returnMapWord_cons k0 tl]
      have h3_pos : 3 ^ tl.length ≥ 1 := Nat.one_le_pow tl.length 3 (by decide)
      omega
  have hmul_le : 2 ^ totalValuation ks * n ≤ 3 ^ ks.length * n :=
    Nat.mul_le_mul_right n hle_exp
  have hlt_mul : 2 ^ totalValuation ks * n <
      2 ^ totalValuation ks * applyParityWord n (returnMapWord ks) := by
    omega
  exact Nat.lt_of_mul_lt_mul_left hlt_mul

/-- Finite-Horizon First-Crossing vs. No-Crossing Dichotomy
    (`finite_valuation_first_crossing_or_no_crossing`):
    For any cumulative valuation sequence `K : Nat → Nat` and any horizon `S : Nat`, either:
    1. `(∀ s : Nat, 1 ≤ s → s ≤ S → 2 ^ K s ≤ 3 ^ s)` (No spectral crossing up to `S`), or
    2. `(∃ s : Nat, 1 ≤ s ∧ s ≤ S ∧ 2 ^ K s > 3 ^ s ∧ ∀ j : Nat, 1 ≤ j → j < s → 2 ^ K j ≤ 3 ^ j)`
       (A unique first spectral crossing occurs at some `1 ≤ s ≤ S`). -/
theorem finite_valuation_first_crossing_or_no_crossing (K : Nat → Nat) :
    ∀ S : Nat,
      (∀ s : Nat, 1 ≤ s → s ≤ S → 2 ^ K s ≤ 3 ^ s) ∨
      (∃ s : Nat, 1 ≤ s ∧ s ≤ S ∧ 2 ^ K s > 3 ^ s ∧
        ∀ j : Nat, 1 ≤ j → j < s → 2 ^ K j ≤ 3 ^ j)
  | 0 => Or.inl (fun s hs1 hs0 => by omega)
  | S + 1 => by
    rcases finite_valuation_first_crossing_or_no_crossing K S with hno | ⟨s, hs1, hsS, hgt, hpre⟩
    · by_cases hcur : 2 ^ K (S + 1) ≤ 3 ^ (S + 1)
      · left
        intro s hs1 hs_le
        by_cases h_eq : s = S + 1
        · subst h_eq; exact hcur
        · exact hno s hs1 (by omega)
      · right
        refine ⟨S + 1, by omega, by omega, by omega, ?_⟩
        intro j hj1 hj_lt
        exact hno j hj1 (by omega)
    · right
      exact ⟨s, hs1, by omega, hgt, hpre⟩

/-- Infinite-Horizon Two-Branch Dichotomy for Valuation Sequences
    (`infinite_valuation_first_crossing_or_indefinite_expansion`):
    Every infinite valuation trajectory `K : Nat → Nat` falls into one of two disjoint branches:
    1. **Branch 1 (First Spectral Crossing Occurs)**:
       `∃ s ≥ 1, 2 ^ K s > 3 ^ s ∧ ∀ j, 1 ≤ j → j < s → 2 ^ K j ≤ 3 ^ j`, or
    2. **Branch 2 (Indefinite Spectral Expansion / No First Crossing)**:
       `∀ s ≥ 1, 2 ^ K s ≤ 3 ^ s`. -/
theorem infinite_valuation_first_crossing_or_indefinite_expansion (K : Nat → Nat) :
    (∃ s : Nat, s ≥ 1 ∧ 2 ^ K s > 3 ^ s ∧
      ∀ j : Nat, 1 ≤ j → j < s → 2 ^ K j ≤ 3 ^ j) ∨
    (∀ s : Nat, s ≥ 1 → 2 ^ K s ≤ 3 ^ s) := by
  by_cases hall : ∀ s : Nat, s ≥ 1 → 2 ^ K s ≤ 3 ^ s
  · exact Or.inr hall
  · left
    have hex : ∃ S : Nat, ¬(∀ s : Nat, 1 ≤ s → s ≤ S → 2 ^ K s ≤ 3 ^ s) := by
      exact Classical.byContradiction (fun hno =>
        hall (fun s hs1 =>
          Classical.byContradiction (fun hnot_le =>
            hno ⟨s, fun h => hnot_le (h s hs1 (by omega))⟩)))
    rcases hex with ⟨S, hnot_all⟩
    rcases finite_valuation_first_crossing_or_no_crossing K S with hno | ⟨s, hs1, _, hgt, hpre⟩
    · exact False.elim (hnot_all hno)
    · exact ⟨s, hs1, hgt, hpre⟩

/-- Formal Benchmark & Cap Separation Witness (`first_crossing_benchmarks_and_cap_witness`):
    1. At `n = 165`, the true first odd-endpoint spectral crossing is `ks = [3]` (`s = 1, K = 4`),
       which satisfies `PreCrossingReturnSeq [3]`, `2 ^ 4 > 3 ^ 1`, and descends to `31 < 165`.
    2. At `s = 5, K = 8` (`Δ = 256 - 243 = 13`), the first-crossing words `[0, 0, 0, 0, 3]`
       (`B = 211`) and `[0, 1, 0, 1, 1]` (`B = 319`) satisfy `PreCrossingReturnSeq` and obey the
       linear cap `B ≤ 5 * 3^4 = 405`, whereas the non-first-crossing permutation `[3, 0, 0, 0, 0]`
       violates `PreCrossingReturnSeq` and has `B = 1121 > 405`. -/
theorem first_crossing_benchmarks_and_cap_witness :
    (PreCrossingReturnSeq [3] ∧
     validOddReturnSeq 165 [3] ∧
     applyParityWord 165 (returnMapWord [3]) = 31 ∧
     31 < 165) ∧
    (PreCrossingReturnSeq [0, 0, 0, 0, 3] ∧
     wordB (returnMapWord [0, 0, 0, 0, 3]) = 211 ∧
     211 ≤ 5 * 3 ^ 4) ∧
    (PreCrossingReturnSeq [0, 1, 0, 1, 1] ∧
     wordB (returnMapWord [0, 1, 0, 1, 1]) = 319 ∧
     319 ≤ 5 * 3 ^ 4) ∧
    (¬PreCrossingReturnSeq [3, 0, 0, 0, 0] ∧
     wordB (returnMapWord [3, 0, 0, 0, 0]) = 1121 ∧
     1121 > 5 * 3 ^ 4) := by
  dsimp [PreCrossingReturnSeq, preCrossingFrom, validOddReturnSeq, returnMapWord,
         singleOddWord, validParityWord, stepParityMatches, acceleratedCollatz, applyParityWord]
  decide

/-! ## Section 14: Sharpened First-Crossing Offset Cap, Surplus Decomposition,
    Kernel-Certified `s ≤ 40` Exclusion, and No-Crossing Excess Valuation Laws -/

/-- Helper lemma: `3 ^ j` is always odd (`3 ^ j % 2 = 1`). -/
theorem three_pow_mod_two : ∀ j : Nat, 3 ^ j % 2 = 1
  | 0 => rfl
  | j + 1 => by
    rw [Nat.pow_succ 3 j]
    have ih := three_pow_mod_two j
    omega

/-- Helper lemma: for any `K ≥ 1`, `2 ^ K ≤ 3 ^ j` implies the strict inequality
    `2 ^ K + 1 ≤ 3 ^ j` (since `2 ^ K` is even while `3 ^ j` is odd). -/
theorem two_pow_lt_three_pow_of_le (K j : Nat)
    (hK : K ≥ 1) (hle : 2 ^ K ≤ 3 ^ j) :
    2 ^ K + 1 ≤ 3 ^ j := by
  obtain ⟨m, rfl⟩ : ∃ m, K = m + 1 := ⟨K - 1, by omega⟩
  have hev : 2 ^ (m + 1) % 2 = 0 := by
    rw [Nat.pow_succ 2 m]
    omega
  have hodd : 3 ^ j % 2 = 1 := three_pow_mod_two j
  omega

/-- Sharpened Pre-Crossing Return-Map Offset Cap (`preCrossing_returnMap_offset_sharpened_bound`):
    Because `2 ^ K_j` is even and `3 ^ j` is odd for every `1 ≤ j < s`, `PreCrossingReturnSeq ks`
    implies the strict prefix bound `2 ^ K_j ≤ 3 ^ j - 1` for all `1 ≤ j < s`, sharpening
    `wordB (returnMapWord ks) ≤ s * 3^{s-1}` to:
    `2 * wordB (returnMapWord ks) + 3 ^ (ks.length - 1) ≤ 2 * ks.length * 3 ^ (ks.length - 1) + 1`
    (i.e., `B_s ≤ s * 3^{s-1} - (3^{s-1} - 1) / 2`) for every non-empty `ks` (`ks.length ≥ 1`). -/
theorem preCrossing_returnMap_offset_sharpened_bound (ks : List Nat)
    (hpre : PreCrossingReturnSeq ks)
    (hs1 : ks.length ≥ 1) :
    2 * wordB (returnMapWord ks) + 3 ^ (ks.length - 1) ≤
      2 * ks.length * 3 ^ (ks.length - 1) + 1 := by
  let P := fun (l : List Nat) =>
    PreCrossingReturnSeq l →
      l.length ≥ 1 →
      2 * wordB (returnMapWord l) + 3 ^ (l.length - 1) ≤
        2 * l.length * 3 ^ (l.length - 1) + 1
  have hnil : P [] := by
    intro _ hlen
    dsimp at hlen
    omega
  have hsnoc : ∀ (l : List Nat) (k : Nat), P l → P (l ++ [k]) := by
    intro l k ih hpre_lk _
    have hlen_lk : (l ++ [k]).length = l.length + 1 := by
      rw [List.length_append]; rfl
    have hB_lk := wordB_returnMapWord_snoc l k
    cases hlen_cases : l.length with
    | zero =>
      have hl_nil : l = [] := List.eq_nil_of_length_eq_zero hlen_cases
      subst hl_nil
      rw [hB_lk]
      dsimp [totalValuation, returnMapWord, wordB]
      omega
    | succ m =>
      rcases (preCrossingReturnSeq_snoc l k).mp hpre_lk with ⟨hpre_l, hK_le⟩
      have hl_ge1 : l.length ≥ 1 := by omega
      have ih_l := ih hpre_l hl_ge1
      rcases returnMap_offset_extremal_sandwich l with ⟨hK_ge_len, _, _⟩
      have hK_ge1 : totalValuation l ≥ 1 := by omega
      have hK_strict : 2 ^ totalValuation l + 1 ≤ 3 ^ l.length :=
        two_pow_lt_three_pow_of_le (totalValuation l) l.length hK_ge1 hK_le
      rw [hlen_lk, Nat.add_sub_cancel, hB_lk]
      rw [hlen_cases, Nat.add_sub_cancel] at ih_l
      rw [hlen_cases, Nat.pow_succ 3 m] at hK_strict ⊢
      have hmul : 2 * (m + 1 + 1) * (3 ^ m * 3) =
          3 * (2 * (m + 1) * 3 ^ m) + 2 * (3 ^ m * 3) := by
        rw [Nat.mul_add 2 (m + 1) 1, Nat.mul_one, Nat.add_mul,
            ← Nat.mul_assoc (2 * (m + 1)) (3 ^ m) 3,
            Nat.mul_comm (2 * (m + 1) * 3 ^ m) 3]
      omega
  have hacc : ∀ (rem pfx : List Nat), P pfx → P (pfx ++ rem) := by
    intro rem
    induction rem with
    | nil =>
      intro pfx hp
      rw [List.append_nil]
      exact hp
    | cons k tl ih =>
      intro pfx hp
      have hcons : pfx ++ (k :: tl) = (pfx ++ [k]) ++ tl := by simp
      rw [hcons]
      exact ih (pfx ++ [k]) (hsnoc pfx k hp)
  exact hacc ks [] hnil hpre hs1

/-- Exact First-Crossing Surplus Decomposition & `s ≤ 6` Strict-Growth Exclusion
    (`first_crossing_surplus_decomposition_and_s_le_6_exclusion`):
    For any return word `ks` realized by `n` with `2 ^ K_s > 3 ^ s` and
    `u_s = applyParityWord n (returnMapWord ks) ≥ n`:
    1. `(2 ^ K_s - 3 ^ s) * n + 2 ^ K_s * (u_s - n) = wordB (returnMapWord ks)`,
    2. If `PreCrossingReturnSeq ks` holds, then `3 * (2 ^ K_s * (u_s - n)) < ks.length * 2 ^ K_s`,
       forcing `3 * (u_s - n) < ks.length` (so for `1 ≤ ks.length ≤ 3`, `u_s = n`), and
    3. If `PreCrossingReturnSeq ks` and `validOddReturnSeq n ks` hold, then for `1 ≤ ks.length ≤ 6`,
       strict growth `u_s > n` is unconditionally impossible (`u_s = n`). -/
theorem first_crossing_surplus_decomposition_and_s_le_6_exclusion (ks : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord ks))
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length)
    (hge : applyParityWord n (returnMapWord ks) ≥ n) :
    let s := ks.length
    let K := totalValuation ks
    let u_s := applyParityWord n (returnMapWord ks)
    (2 ^ K - 3 ^ s) * n + 2 ^ K * (u_s - n) = wordB (returnMapWord ks) ∧
    (PreCrossingReturnSeq ks → 3 * (u_s - n) < s) ∧
    (PreCrossingReturnSeq ks → validOddReturnSeq n ks → s ≤ 6 → u_s = n) := by
  dsimp
  have hid := parityWord_affine_identity (returnMapWord ks) n hv
  rw [wordD_returnMapWord, wordA_returnMapWord] at hid
  have hsub1 : (2 ^ totalValuation ks - 3 ^ ks.length) * n =
      2 ^ totalValuation ks * n - 3 ^ ks.length * n :=
    Nat.sub_mul (2 ^ totalValuation ks) (3 ^ ks.length) n
  have hsub2 : 2 ^ totalValuation ks * (applyParityWord n (returnMapWord ks) - n) =
      2 ^ totalValuation ks * applyParityWord n (returnMapWord ks) -
        2 ^ totalValuation ks * n :=
    Nat.mul_sub (2 ^ totalValuation ks) (applyParityWord n (returnMapWord ks)) n
  have hle_n : 3 ^ ks.length * n ≤ 2 ^ totalValuation ks * n :=
    Nat.mul_le_mul_right n (by omega)
  have hle_u : 2 ^ totalValuation ks * n ≤
      2 ^ totalValuation ks * applyParityWord n (returnMapWord ks) :=
    Nat.mul_le_mul_left (2 ^ totalValuation ks) hge
  have hdecomp : (2 ^ totalValuation ks - 3 ^ ks.length) * n +
      2 ^ totalValuation ks * (applyParityWord n (returnMapWord ks) - n) =
      wordB (returnMapWord ks) := by
    omega
  refine ⟨hdecomp, ?_, ?_⟩
  · intro hpre
    have hcap := (preCrossing_returnMap_offset_upper_bound ks hpre).1
    have hlt_s : ks.length * 3 ^ ks.length < ks.length * 2 ^ totalValuation ks := by
      cases hlen : ks.length with
      | zero =>
        have hnil_ks : ks = [] := List.eq_nil_of_length_eq_zero hlen
        subst hnil_ks
        dsimp [totalValuation, returnMapWord] at hcont
        omega
      | succ m =>
        rw [← hlen]
        exact Nat.mul_lt_mul_of_pos_left hcont (by omega)
    have hmul_lt : 2 ^ totalValuation ks * (3 * (applyParityWord n (returnMapWord ks) - n)) <
        2 ^ totalValuation ks * ks.length := by
      have hc1 : 2 ^ totalValuation ks * (3 * (applyParityWord n (returnMapWord ks) - n)) =
          3 * (2 ^ totalValuation ks * (applyParityWord n (returnMapWord ks) - n)) := by
        rw [← Nat.mul_assoc (2 ^ totalValuation ks) 3 _,
            Nat.mul_comm (2 ^ totalValuation ks) 3,
            Nat.mul_assoc 3 (2 ^ totalValuation ks) _]
      have hc2 : 2 ^ totalValuation ks * ks.length = ks.length * 2 ^ totalValuation ks :=
        Nat.mul_comm _ _
      omega
    exact Nat.lt_of_mul_lt_mul_left hmul_lt
  · intro hpre hv_odd hs6
    rcases hv_odd with ⟨hn_odd, _, hu_odd⟩
    have hcap := (preCrossing_returnMap_offset_upper_bound ks hpre).1
    by_cases hgt : applyParityWord n (returnMapWord ks) > n
    · have hdiff_ge2 : applyParityWord n (returnMapWord ks) - n ≥ 2 := by omega
      have hmul_ge : 2 ^ totalValuation ks * 2 ≤
          2 ^ totalValuation ks * (applyParityWord n (returnMapWord ks) - n) :=
        Nat.mul_le_mul_left (2 ^ totalValuation ks) hdiff_ge2
      have hs_le : ks.length * 3 ^ ks.length ≤ 6 * 3 ^ ks.length :=
        Nat.mul_le_mul_right (3 ^ ks.length) hs6
      omega
    · omega

/-- Mathematically Exhaustive Final-Valuation Cutoff for First-Crossing Words
    (`first_crossing_large_valuation_forced_descent`):
    For fixed `s = ks.length`, if the final crossing valuation makes `K = totalValuation ks`
    satisfy `6 * (2 ^ K - 3 ^ s) > s * 3 ^ s` (or for odd `n ≥ 3`, `9 * (2 ^ K - 3 ^ s) > s * 3 ^ s`),
    then EVERY `n > 1` (resp. `n ≥ 3`) realizing `returnMapWord ks` with `PreCrossingReturnSeq ks`
    strictly descends below `n`. Thus only finitely many final valuations `K` can ever permit
    a survivor at block count `s`. -/
theorem first_crossing_large_valuation_forced_descent (ks : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord ks))
    (hpre : PreCrossingReturnSeq ks)
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length) :
    (n > 1 → 6 * (2 ^ totalValuation ks - 3 ^ ks.length) > ks.length * 3 ^ ks.length →
      applyParityWord n (returnMapWord ks) < n) ∧
    (n ≥ 3 → 9 * (2 ^ totalValuation ks - 3 ^ ks.length) > ks.length * 3 ^ ks.length →
      applyParityWord n (returnMapWord ks) < n) := by
  have hexcl := (first_crossing_linear_offset_exclusion ks n hv hpre hcont).1
  constructor
  · intro hn1 h6
    apply hexcl
    have hmul : (2 ^ totalValuation ks - 3 ^ ks.length) * 2 ≤
        (2 ^ totalValuation ks - 3 ^ ks.length) * n :=
      Nat.mul_le_mul_left (2 ^ totalValuation ks - 3 ^ ks.length) (by omega)
    omega
  · intro hn3 h9
    apply hexcl
    have hmul : (2 ^ totalValuation ks - 3 ^ ks.length) * 3 ≤
        (2 ^ totalValuation ks - 3 ^ ks.length) * n :=
      Nat.mul_le_mul_left (2 ^ totalValuation ks - 3 ^ ks.length) (by omega)
    omega

/-- Computable boolean certificate verifying that for every block count `1 ≤ s ≤ 40`
    and every `1 ≤ K ≤ 64`, `2 ^ 64 > 3 ^ s` and whenever `2 ^ K > 3 ^ s`,
    `3 * ((2 ^ K - 3 ^ s) * 1024) > s * 3 ^ s` (`n_cap(s, K) < 1024`). -/
def checkFirstCrossingCap1024_40 : Bool :=
  (List.range 41).all fun s =>
    (List.range 65).all fun K =>
      !(decide (1 ≤ s ∧
        ((K = 64 ∧ 2 ^ K ≤ 3 ^ s) ∨
         (2 ^ K > 3 ^ s ∧ 3 * ((2 ^ K - 3 ^ s) * 1024) ≤ s * 3 ^ s))))

/-- Kernel-certified verification that `checkFirstCrossingCap1024_40 = true`. -/
theorem checkFirstCrossingCap1024_40_true :
    checkFirstCrossingCap1024_40 = true := by
  decide

/-- First-Crossing Descent Certificate for `n ≥ 1024` and `1 ≤ s ≤ 40`
    (`first_crossing_descent_for_ge_1024_and_s_le_40`):
    For EVERY integer `n ≥ 1024` and EVERY first-crossing return word `ks` of length
    `1 ≤ s ≤ 40` (`PreCrossingReturnSeq ks` and `2 ^ K_s > 3 ^ s`, for ANY final valuation `K_s`)
    realized by `n`, strict descent `applyParityWord n (returnMapWord ks) < n` holds. -/
theorem first_crossing_descent_for_ge_1024_and_s_le_40 (ks : List Nat) (n : Nat)
    (hn1024 : n ≥ 1024)
    (hs1 : ks.length ≥ 1)
    (hs40 : ks.length ≤ 40)
    (hv : validParityWord n (returnMapWord ks))
    (hpre : PreCrossingReturnSeq ks)
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length) :
    applyParityWord n (returnMapWord ks) < n := by
  apply (first_crossing_linear_offset_exclusion ks n hv hpre hcont).1
  let s := ks.length
  let K := totalValuation ks
  have hs_mem : s ∈ List.range 41 := List.mem_range.mpr (by omega)
  have hall_s := (List.all_eq_true.mp checkFirstCrossingCap1024_40_true) s hs_mem
  have h1024_gt : 3 * ((2 ^ K - 3 ^ s) * 1024) > s * 3 ^ s := by
    by_cases hK64 : K ≤ 64
    · have hK_mem : K ∈ List.range 65 := List.mem_range.mpr (by omega)
      have hall_K := (List.all_eq_true.mp hall_s) K hK_mem
      by_cases hle : 3 * ((2 ^ K - 3 ^ s) * 1024) ≤ s * 3 ^ s
      · have hdec : decide (1 ≤ s ∧
            ((K = 64 ∧ 2 ^ K ≤ 3 ^ s) ∨
             (2 ^ K > 3 ^ s ∧ 3 * ((2 ^ K - 3 ^ s) * 1024) ≤ s * 3 ^ s))) = true :=
          decide_eq_true ⟨hs1, Or.inr ⟨hcont, hle⟩⟩
        rw [hdec] at hall_K
        contradiction
      · exact Nat.gt_of_not_le hle
    · have h64_mem : 64 ∈ List.range 65 := List.mem_range.mpr (by decide)
      have hall_64 := (List.all_eq_true.mp hall_s) 64 h64_mem
      have h2_64_gt : 2 ^ 64 > 3 ^ s := by
        by_cases hle64 : 2 ^ 64 ≤ 3 ^ s
        · have hdec : decide (1 ≤ s ∧
              ((64 = 64 ∧ 2 ^ 64 ≤ 3 ^ s) ∨
               (2 ^ 64 > 3 ^ s ∧ 3 * ((2 ^ 64 - 3 ^ s) * 1024) ≤ s * 3 ^ s))) = true :=
            decide_eq_true ⟨hs1, Or.inl ⟨rfl, hle64⟩⟩
          rw [hdec] at hall_64
          contradiction
        · exact Nat.gt_of_not_le hle64
      have hcap64 : 3 * ((2 ^ 64 - 3 ^ s) * 1024) > s * 3 ^ s := by
        by_cases hle64 : 3 * ((2 ^ 64 - 3 ^ s) * 1024) ≤ s * 3 ^ s
        · have hdec : decide (1 ≤ s ∧
              ((64 = 64 ∧ 2 ^ 64 ≤ 3 ^ s) ∨
               (2 ^ 64 > 3 ^ s ∧ 3 * ((2 ^ 64 - 3 ^ s) * 1024) ≤ s * 3 ^ s))) = true :=
            decide_eq_true ⟨hs1, Or.inr ⟨h2_64_gt, hle64⟩⟩
          rw [hdec] at hall_64
          contradiction
        · exact Nat.gt_of_not_le hle64
      have hpow_ge : 2 ^ 64 ≤ 2 ^ K := two_pow_le_two_pow 64 K (by omega)
      have hsub_ge : 2 ^ 64 - 3 ^ s ≤ 2 ^ K - 3 ^ s := Nat.sub_le_sub_right hpow_ge (3 ^ s)
      have hmul1 : (2 ^ 64 - 3 ^ s) * 1024 ≤ (2 ^ K - 3 ^ s) * 1024 :=
        Nat.mul_le_mul_right 1024 hsub_ge
      have hmul2 : 3 * ((2 ^ 64 - 3 ^ s) * 1024) ≤ 3 * ((2 ^ K - 3 ^ s) * 1024) :=
        Nat.mul_le_mul_left 3 hmul1
      exact Nat.lt_of_lt_of_le hcap64 hmul2
  have hmul_n : (2 ^ K - 3 ^ s) * 1024 ≤ (2 ^ K - 3 ^ s) * n :=
    Nat.mul_le_mul_left (2 ^ K - 3 ^ s) hn1024
  have hmul3 : 3 * ((2 ^ K - 3 ^ s) * 1024) ≤ 3 * ((2 ^ K - 3 ^ s) * n) :=
    Nat.mul_le_mul_left 3 hmul_n
  exact Nat.lt_of_lt_of_le h1024_gt hmul3

/-- Kernel-Certified Exclusion of First Spectral Crossings at `1 ≤ s ≤ 40` for Never-Descending
    Orbits (`nondescent_orbit_no_first_crossing_le_40`):
    Combining `descent_of_lt_1024` (`n ≥ 1024`) with `first_crossing_descent_for_ge_1024_and_s_le_40`
    proves unconditionally—without simulating Collatz trajectories above `1023`—that NO
    never-descending orbit starting at `n > 1` (`∀ r, iterateAccelerated n r ≥ n`) can have
    its first completed odd-return spectral crossing at block count `1 ≤ s ≤ 40`. -/
theorem nondescent_orbit_no_first_crossing_le_40 (n : Nat) (ks : List Nat)
    (hn1 : n > 1)
    (hnever : ∀ r : Nat, iterateAccelerated n r ≥ n)
    (hs1 : ks.length ≥ 1)
    (hs40 : ks.length ≤ 40)
    (hv : validParityWord n (returnMapWord ks))
    (hpre : PreCrossingReturnSeq ks) :
    ¬(2 ^ totalValuation ks > 3 ^ ks.length) := by
  intro hcont
  have hn1024 : n ≥ 1024 := by
    by_cases hlt : n < 1024
    · rcases descent_of_lt_1024 n hn1 hlt with ⟨k, _, _, hk_lt⟩
      have hge := hnever k
      omega
    · omega
  have hdesc := first_crossing_descent_for_ge_1024_and_s_le_40 ks n hn1024 hs1 hs40 hv hpre hcont
  have hw_eq : returnMapWord ks = parityWordOf (returnMapWord ks).length n :=
    ((validParityWord_iff_eq_parityWordOf (returnMapWord ks) n).mp hv).symm
  have h_it : applyParityWord n (returnMapWord ks) =
      iterateAccelerated n (returnMapWord ks).length := by
    rw [hw_eq, applyParityWord_parityWordOf (returnMapWord ks).length n, ← hw_eq]
  have hge := hnever (returnMapWord ks).length
  omega

/-- Excess Valuation Sum `excessValuation ks := totalValuation ks - ks.length` (`∑ k_j`). -/
def excessValuation (ks : List Nat) : Nat :=
  totalValuation ks - ks.length

/-- No-First-Crossing Excess Valuation Bound (`excessValuation_no_crossing_bound`):
    For any valuation sequence `ks` of length `s = ks.length`:
    1. `totalValuation ks = s + excessValuation ks` and `2 ^ K_s = 2 ^ s * 2 ^ (excessValuation ks)`,
    2. Whenever `s ≥ 1` and `2 ^ K_s ≤ 3 ^ s` (the No-First-Crossing branch),
       `2 ^ s * 2 ^ (excessValuation ks) ≤ 3 ^ s` and `excessValuation ks < s` (`K_s < 2 * s`). -/
theorem excessValuation_no_crossing_bound (ks : List Nat) :
    let s := ks.length
    let K := totalValuation ks
    let E := excessValuation ks
    K = s + E ∧
    2 ^ K = 2 ^ s * 2 ^ E ∧
    (s ≥ 1 → 2 ^ K ≤ 3 ^ s → E < s) := by
  dsimp [excessValuation]
  rcases returnMap_offset_extremal_sandwich ks with ⟨hK_ge_s, _, _⟩
  have hsum : totalValuation ks = ks.length + (totalValuation ks - ks.length) := by omega
  have hpow : 2 ^ totalValuation ks =
      2 ^ ks.length * 2 ^ (totalValuation ks - ks.length) := by
    rw [← Nat.pow_add, ← hsum]
  refine ⟨hsum, hpow, ?_⟩
  intro hs1 hle
  by_cases hge_s : totalValuation ks - ks.length ≥ ks.length
  · have h2E : 2 ^ ks.length ≤ 2 ^ (totalValuation ks - ks.length) :=
      two_pow_le_two_pow ks.length (totalValuation ks - ks.length) hge_s
    have h4s : 2 ^ ks.length * 2 ^ ks.length ≤ 2 ^ totalValuation ks := by
      rw [hpow]
      exact Nat.mul_le_mul_left (2 ^ ks.length) h2E
    have hpow_mul : ∀ m : Nat, 2 ^ m * 2 ^ m = 4 ^ m := by
      intro m
      induction m with
      | zero => rfl
      | succ m ih =>
        rw [Nat.pow_succ 2 m, Nat.pow_succ 4 m, ← ih]
        have hc : 2 ^ m * 2 * (2 ^ m * 2) = 2 ^ m * 2 ^ m * 4 := by
          rw [Nat.mul_assoc (2 ^ m) 2 (2 ^ m * 2),
              ← Nat.mul_assoc 2 (2 ^ m) 2,
              Nat.mul_comm 2 (2 ^ m),
              Nat.mul_assoc (2 ^ m) 2 2,
              ← Nat.mul_assoc (2 ^ m) (2 ^ m) 4]
        exact hc
    rw [hpow_mul ks.length] at h4s
    have h3_lt_4 : ∀ m : Nat, m ≥ 1 → 3 ^ m < 4 ^ m := by
      intro m
      induction m with
      | zero =>
        intro hm
        omega
      | succ m ih =>
        intro _
        cases m with
        | zero => decide
        | succ m' =>
          have ihm := ih (by omega)
          rw [Nat.pow_succ 3 (m' + 1), Nat.pow_succ 4 (m' + 1)]
          omega
    have hlt := h3_lt_4 ks.length hs1
    omega
  · omega

/-- Formal Falsification Witness CE-C10-10
    (`no_crossing_branch_not_stepwise_monotone_at_27_witness`):
    Proves that inside the No-First-Crossing branch (`2 ^ K_s ≤ 3 ^ s`), while every odd return
    exceeds the initial integer `n` (`u_s > n`), consecutive odd returns are NOT stepwise
    monotone (`u_1 < u_2` can fail): at `n = 27`, `ks = [0, 1]` has `s = 2, K_2 = 3`,
    `2 ^ 3 = 8 ≤ 9 = 3 ^ 2`, `u_1 = 41 > 27`, and `u_2 = 31 > 27`, yet `u_2 = 31 < 41 = u_1`. -/
theorem no_crossing_branch_not_stepwise_monotone_at_27_witness :
    PreCrossingReturnSeq [0, 1] ∧
    2 ^ totalValuation [0, 1] ≤ 3 ^ ([0, 1] : List Nat).length ∧
    applyParityWord 27 (returnMapWord [0]) = 41 ∧
    applyParityWord 27 (returnMapWord [0, 1]) = 31 ∧
    41 > 27 ∧ 31 > 27 ∧ 31 < 41 := by
  dsimp [PreCrossingReturnSeq, preCrossingFrom]
  decide

/-! ## Section 15: First-Crossing Surplus Diophantine Equivalence, Temporal Self-Similarity
    Coupling (`v_2(t) = 1` Forced Two-Step Descent), and Falsifications (CE-C10-11..12) -/

/-- General append decomposition for `preCrossingFrom` (`preCrossingFrom_append`). -/
theorem preCrossingFrom_append (ks₁ ks₂ : List Nat) :
    ∀ j K : Nat,
      preCrossingFrom j K (ks₁ ++ ks₂) ↔
        (preCrossingFrom j K ks₁ ∧
         preCrossingFrom (j + ks₁.length) (K + totalValuation ks₁) ks₂) := by
  induction ks₁ with
  | nil =>
    intro j K
    dsimp [preCrossingFrom, totalValuation, returnMapWord]
    constructor
    · intro h; exact ⟨trivial, h⟩
    · intro h; exact h.2
  | cons x tl ih =>
    intro j K
    dsimp [preCrossingFrom]
    rw [ih (j + 1) (K + x + 1), totalValuation_cons x tl]
    have hK : K + x + 1 + totalValuation tl = K + (x + 1 + totalValuation tl) := by omega
    have hj : j + 1 + tl.length = j + (tl.length + 1) := by omega
    rw [hK, hj]
    constructor
    · intro h; exact ⟨⟨h.1, h.2.1⟩, h.2.2⟩
    · intro h; exact ⟨h.1.1, ⟨h.1.2, h.2⟩⟩

/-- Every proper prefix `ks₁` of a `PreCrossingReturnSeq (ks₁ ++ ks₂)` with `ks₂.length ≥ 1`
    satisfies both `PreCrossingReturnSeq ks₁` and `2 ^ totalValuation ks₁ ≤ 3 ^ ks₁.length`
    (`preCrossingReturnSeq_prefix_noncrossing`). -/
theorem preCrossingReturnSeq_prefix_noncrossing (ks₁ ks₂ : List Nat)
    (hpre : PreCrossingReturnSeq (ks₁ ++ ks₂))
    (hne : ks₂.length ≥ 1) :
    PreCrossingReturnSeq ks₁ ∧ 2 ^ totalValuation ks₁ ≤ 3 ^ ks₁.length := by
  unfold PreCrossingReturnSeq at hpre ⊢
  rcases (preCrossingFrom_append ks₁ ks₂ 0 0).mp hpre with ⟨hpre1, hpre2⟩
  rw [Nat.zero_add, Nat.zero_add] at hpre2
  cases ks₂ with
  | nil =>
    dsimp at hne
    omega
  | cons k tl₂ =>
    dsimp [preCrossingFrom] at hpre2
    exact ⟨hpre1, hpre2.1⟩

/-- Exact Equivalence of the Surplus Diophantine Equation and Admissible First-Crossing Survivors
    (`first_crossing_surplus_diophantine_iff_admissible_survivor`):
    For ANY pre-crossing valuation sequence `ks` (`PreCrossingReturnSeq ks`, `s = ks.length ≥ 1`,
    `Δ_s = 2 ^ K_s - 3 ^ s > 0`) and any `n ≥ 1`, `t : Nat`:
    1. The single Diophantine equation `(2 ^ K_s - 3 ^ s) * n + 2 ^ K_s * t = B(returnMapWord ks)`
       holds if and only if `validParityWord n (returnMapWord ks)` AND
       `applyParityWord n (returnMapWord ks) = n + t` (so integrality of `n = (B_s - 2^{K_s} t)/Δ_s`
       ALREADY forces the exact 2-adic word-admissibility congruence!).
    2. Moreover, any solution `(n, t)` automatically satisfies:
       - `n % 2 = 1` (`n` is odd),
       - `applyParityWord n (returnMapWord ks) % 2 = 1 ↔ t % 2 = 0` (`u_s = n + t` is odd iff `t` is even),
       - `3 * t < s` (`0 ≤ t < s / 3`),
       - `2 * ((2 ^ K_s - 3 ^ s) * n) + 3 ^ (s - 1) ≤ 2 * s * 3 ^ (s - 1) + 1`, and
       - Automatic intermediate odd-return expansion: for every proper split `ks = ks₁ ++ ks₂`
         with `ks₁.length ≥ 1` and `ks₂.length ≥ 1`,
         `validParityWord n (returnMapWord ks₁) ∧ applyParityWord n (returnMapWord ks₁) > n`. -/
theorem first_crossing_surplus_diophantine_iff_admissible_survivor
    (ks : List Nat) (n t : Nat)
    (_hn1 : n ≥ 1)
    (hs1 : ks.length ≥ 1)
    (hpre : PreCrossingReturnSeq ks)
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length) :
    let s := ks.length
    let K := totalValuation ks
    let delta := 2 ^ K - 3 ^ s
    let B := wordB (returnMapWord ks)
    (delta * n + 2 ^ K * t = B ↔
      (validParityWord n (returnMapWord ks) ∧
       applyParityWord n (returnMapWord ks) = n + t)) ∧
    (delta * n + 2 ^ K * t = B →
      n % 2 = 1 ∧
      (applyParityWord n (returnMapWord ks) % 2 = 1 ↔ t % 2 = 0) ∧
      3 * t < s ∧
      2 * (delta * n) + 3 ^ (s - 1) ≤ 2 * s * 3 ^ (s - 1) + 1 ∧
      (∀ ks₁ ks₂ : List Nat,
        ks = ks₁ ++ ks₂ → ks₁.length ≥ 1 → ks₂.length ≥ 1 →
          validParityWord n (returnMapWord ks₁) ∧
          applyParityWord n (returnMapWord ks₁) > n)) := by
  dsimp
  have hD := wordD_returnMapWord ks
  have hA := wordA_returnMapWord ks
  have hle_pow : 3 ^ ks.length * n ≤ 2 ^ totalValuation ks * n :=
    Nat.mul_le_mul_right n (by omega)
  have hsub_mul : (2 ^ totalValuation ks - 3 ^ ks.length) * n =
      2 ^ totalValuation ks * n - 3 ^ ks.length * n :=
    Nat.sub_mul (2 ^ totalValuation ks) (3 ^ ks.length) n
  have hmul_add : 2 ^ totalValuation ks * (n + t) =
      2 ^ totalValuation ks * n + 2 ^ totalValuation ks * t :=
    Nat.mul_add (2 ^ totalValuation ks) n t
  have heq_iff : (2 ^ totalValuation ks - 3 ^ ks.length) * n + 2 ^ totalValuation ks * t =
      wordB (returnMapWord ks) ↔
      wordD (returnMapWord ks) * (n + t) =
        wordA (returnMapWord ks) * n + wordB (returnMapWord ks) := by
    rw [hD, hA]
    omega
  have hmain_iff : (2 ^ totalValuation ks - 3 ^ ks.length) * n + 2 ^ totalValuation ks * t =
      wordB (returnMapWord ks) ↔
      (validParityWord n (returnMapWord ks) ∧
       applyParityWord n (returnMapWord ks) = n + t) := by
    rw [heq_iff]
    exact affine_identity_iff_validParityWord_and_output (returnMapWord ks) n (n + t)
  refine ⟨hmain_iff, ?_⟩
  intro hdioph
  rcases hmain_iff.mp hdioph with ⟨hv, hout⟩
  have hn_odd : n % 2 = 1 := by
    cases ks with
    | nil => dsimp at hs1; omega
    | cons k tl =>
      dsimp [returnMapWord, singleOddWord, validParityWord, stepParityMatches] at hv
      exact hv.1
  have hout_parity : applyParityWord n (returnMapWord ks) % 2 = 1 ↔ t % 2 = 0 := by
    rw [hout]
    omega
  have hge_n : applyParityWord n (returnMapWord ks) ≥ n := by omega
  rcases first_crossing_surplus_decomposition_and_s_le_6_exclusion ks n hv hcont hge_n with
    ⟨_, hsurp_fn, _⟩
  have hsurp_lt := hsurp_fn hpre
  have ht_eq : applyParityWord n (returnMapWord ks) - n = t := by omega
  rw [ht_eq] at hsurp_lt
  have hsharp := preCrossing_returnMap_offset_sharpened_bound ks hpre hs1
  have hdn_le : (2 ^ totalValuation ks - 3 ^ ks.length) * n ≤ wordB (returnMapWord ks) := by omega
  have hsharp_n : 2 * ((2 ^ totalValuation ks - 3 ^ ks.length) * n) + 3 ^ (ks.length - 1) ≤
      2 * ks.length * 3 ^ (ks.length - 1) + 1 := by omega
  refine ⟨hn_odd, hout_parity, hsurp_lt, hsharp_n, ?_⟩
  intro ks₁ ks₂ hsplit hlen1 hlen2
  have hv_split : validParityWord n (returnMapWord ks₁ ++ returnMapWord ks₂) := by
    rw [← returnMapWord_append, ← hsplit]
    exact hv
  have hv₁ : validParityWord n (returnMapWord ks₁) :=
    ((validParityWord_append (returnMapWord ks₁) (returnMapWord ks₂) n).mp hv_split).1
  have hpre_split : PreCrossingReturnSeq (ks₁ ++ ks₂) := by
    rw [← hsplit]; exact hpre
  rcases preCrossingReturnSeq_prefix_noncrossing ks₁ ks₂ hpre_split hlen2 with ⟨_, hnoncross₁⟩
  have hgt₁ : applyParityWord n (returnMapWord ks₁) > n :=
    (no_first_crossing_shifted_growth_and_nondescent ks₁ n hv₁).2 hlen1 hnoncross₁
  exact ⟨hv₁, hgt₁⟩

/-- Forced First Block Valuation `k_0 = 0` and `n ≡ 3 (mod 4)` for All Pre-Crossing Words with `s ≥ 2`
    (`preCrossing_first_valuation_eq_zero_and_first_step_odd`):
    For EVERY pre-crossing sequence `k₀ :: k₁ :: tl` (`s ≥ 2`, `PreCrossingReturnSeq (k₀ :: k₁ :: tl)`):
    1. The first block valuation is forced to be `k₀ = 0` (`K_1 = 1`, since `2^{k₀ + 1} ≤ 3^1 = 3`),
    2. For every integer `n` realizing `returnMapWord (k₀ :: k₁ :: tl)`, both `n` and
       `acceleratedCollatz n` are odd (`n % 2 = 1` and `(acceleratedCollatz n) % 2 = 1`, i.e. `n ≡ 3 (mod 4)`),
       with `2 * acceleratedCollatz n = 3 * n + 1`. -/
theorem preCrossing_first_valuation_eq_zero_and_first_step_odd
    (k₀ k₁ : Nat) (tl : List Nat) (n : Nat)
    (hpre : PreCrossingReturnSeq (k₀ :: k₁ :: tl)) :
    k₀ = 0 ∧
    (validParityWord n (returnMapWord (k₀ :: k₁ :: tl)) →
      n % 2 = 1 ∧
      (acceleratedCollatz n) % 2 = 1 ∧
      2 * acceleratedCollatz n = 3 * n + 1) := by
  unfold PreCrossingReturnSeq at hpre
  dsimp [preCrossingFrom] at hpre
  rcases hpre with ⟨_, hK1_le, _⟩
  have hk0 : k₀ = 0 := by
    cases k₀ with
    | zero => rfl
    | succ m =>
      have hge4 : 2 ^ 2 ≤ 2 ^ (0 + (m + 1) + 1) :=
        two_pow_le_two_pow 2 (0 + (m + 1) + 1) (by omega)
      have h4 : 2 ^ 2 = 4 := rfl
      have h3 : 3 ^ 1 = 3 := rfl
      omega
  refine ⟨hk0, ?_⟩
  intro hv
  rw [hk0] at hv
  dsimp [returnMapWord, singleOddWord, List.replicate, validParityWord, stepParityMatches] at hv
  rcases hv with ⟨hn_odd, hT1_odd, _⟩
  have hm_n : stepParityMatches n true := by
    dsimp [stepParityMatches]; exact hn_odd
  have hstep1 : 2 * acceleratedCollatz n = 3 * n + 1 := by
    have hs := acceleratedCollatz_step_eq n true hm_n
    simpa using hs
  exact ⟨hn_odd, hT1_odd, hstep1⟩

/-- Universal Two-Step Self-Similarity Descent for `v_2(t) = 1` Surpluses (`t = 2 * q`, `q` odd)
    at Arbitrary Block Count `s ≥ 2` (`first_crossing_surplus_v2_eq_one_forced_two_step_descent`):
    For ANY pre-crossing sequence `ks = k₀ :: k₁ :: tl` (`s = ks.length ≥ 2`, `PreCrossingReturnSeq ks`)
    realized by `n` (`validParityWord n (returnMapWord ks)`), if the endpoint `u_s = applyParityWord n (returnMapWord ks)`
    has surplus `t = 2 * q` with `q` odd (`u_s = n + 2 * q`, `q % 2 = 1`, so `v_2(t) = 1`):
    1. `u_s % 2 = 1` (`u_s` is odd),
    2. `acceleratedCollatz u_s = acceleratedCollatz n + 3 * q` (exact 1-step self-similarity shift),
    3. `(acceleratedCollatz u_s) % 2 = 0` (forced parity divergence at `v = 1`: `T^1(n)` is odd, so `T^1(u_s)` is even!),
    4. `4 * iterateAccelerated u_s 2 = 3 * n + 6 * q + 1`, and
    5. Whenever `n > 6 * q + 1` (and in particular whenever `2 ^ K_s > 3 ^ s` and `n > s`),
       `iterateAccelerated u_s 2 < n` (strict descent below `n` two steps after the crossing!). -/
theorem first_crossing_surplus_v2_eq_one_forced_two_step_descent
    (k₀ k₁ : Nat) (tl : List Nat) (n q : Nat)
    (hpre : PreCrossingReturnSeq (k₀ :: k₁ :: tl))
    (hv : validParityWord n (returnMapWord (k₀ :: k₁ :: tl)))
    (hq_odd : q % 2 = 1)
    (hus : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) = n + 2 * q) :
    let ks := k₀ :: k₁ :: tl
    let u_s := applyParityWord n (returnMapWord ks)
    u_s % 2 = 1 ∧
    acceleratedCollatz u_s = acceleratedCollatz n + 3 * q ∧
    (acceleratedCollatz u_s) % 2 = 0 ∧
    4 * iterateAccelerated u_s 2 = 3 * n + 6 * q + 1 ∧
    (n > 6 * q + 1 → iterateAccelerated u_s 2 < n) ∧
    (2 ^ totalValuation ks > 3 ^ ks.length → n > ks.length → iterateAccelerated u_s 2 < n) := by
  dsimp
  rcases (preCrossing_first_valuation_eq_zero_and_first_step_odd k₀ k₁ tl n hpre).2 hv with
    ⟨hn_odd, hT1_odd, hT1_eq⟩
  have hu_odd : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) % 2 = 1 := by
    rw [hus]
    omega
  have hm_u : stepParityMatches (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) true := by
    dsimp [stepParityMatches]; exact hu_odd
  have hTu1_step : 2 * acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) =
      3 * (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) + 1 := by
    have hs := acceleratedCollatz_step_eq (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) true hm_u
    simpa using hs
  have hTu1_shift : acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) =
      acceleratedCollatz n + 3 * q := by omega
  have hTu1_even : (acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)))) % 2 = 0 := by omega
  have hm_Tu1 : stepParityMatches (acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)))) false := by
    dsimp [stepParityMatches]; exact hTu1_even
  have hTu2_step : 2 * iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2 =
      acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) := by
    have hs := acceleratedCollatz_step_eq
      (acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)))) false hm_Tu1
    exact hs
  have hit2_eq : 4 * iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2 =
      3 * n + 6 * q + 1 := by omega
  have hdesc_of_gt : n > 6 * q + 1 →
      iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2 < n := by
    intro hn_gt
    omega
  refine ⟨hu_odd, hTu1_shift, hTu1_even, hit2_eq, hdesc_of_gt, ?_⟩
  · intro hcont hn_gt_s
    have hge_n : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) ≥ n := by omega
    rcases first_crossing_surplus_decomposition_and_s_le_6_exclusion
      (k₀ :: k₁ :: tl) n hv hcont hge_n with ⟨_, hsurp_fn, _⟩
    have hsurp_lt := hsurp_fn hpre
    have hsub_eq : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) - n = 2 * q := by omega
    have hlen_eq : (k₀ :: k₁ :: tl).length = tl.length + 2 := rfl
    rw [hsub_eq, hlen_eq] at hsurp_lt
    exact hdesc_of_gt (by omega)

/-- Complete Exclusion of Positive Even First-Crossing Surpluses for `1 ≤ s ≤ 12` and `n ≥ 8`
    (`first_crossing_s_le_12_positive_even_surplus_forced_descent`):
    For any first-crossing sequence `ks` (`PreCrossingReturnSeq ks` and `2 ^ K_s > 3 ^ s`) with
    `1 ≤ s ≤ 12` and any `n ≥ 8` realizing `returnMapWord ks`:
    if `u_s = applyParityWord n (returnMapWord ks) = n + t` with `t > 0` and `t % 2 = 0`, then:
    1. `7 ≤ ks.length` and `t = 2` (since `3 * t < s ≤ 12` with `t > 0` even forces `t = 2`), and
    2. `iterateAccelerated u_s 2 < n` (strict descent below `n` two steps after the crossing). -/
theorem first_crossing_s_le_12_positive_even_surplus_forced_descent
    (ks : List Nat) (n t : Nat)
    (hn8 : n ≥ 8)
    (_hs1 : ks.length ≥ 1)
    (hs12 : ks.length ≤ 12)
    (hv : validParityWord n (returnMapWord ks))
    (hpre : PreCrossingReturnSeq ks)
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length)
    (ht_pos : t > 0)
    (ht_even : t % 2 = 0)
    (hus : applyParityWord n (returnMapWord ks) = n + t) :
    ks.length ≥ 7 ∧
    t = 2 ∧
    iterateAccelerated (applyParityWord n (returnMapWord ks)) 2 < n := by
  have hge_n : applyParityWord n (returnMapWord ks) ≥ n := by omega
  rcases first_crossing_surplus_decomposition_and_s_le_6_exclusion ks n hv hcont hge_n with
    ⟨_, hsurp_fn, _⟩
  have hsurp_lt := hsurp_fn hpre
  have hsub : applyParityWord n (returnMapWord ks) - n = t := by omega
  rw [hsub] at hsurp_lt
  have hs7 : ks.length ≥ 7 := by omega
  have ht2 : t = 2 := by omega
  cases ks with
  | nil => dsimp at hs7; omega
  | cons k₀ tl₀ =>
    cases tl₀ with
    | nil => dsimp at hs7; omega
    | cons k₁ tl =>
      have hus_q1 : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) = n + 2 * 1 := by omega
      have hdesc := (first_crossing_surplus_v2_eq_one_forced_two_step_descent
        k₀ k₁ tl n 1 hpre hv rfl hus_q1).2.2.2.2.1 (by omega)
      exact ⟨hs7, ht2, hdesc⟩

/-- Formal Falsification Witness CE-C10-11
    (`surplus_v2_ge_two_no_three_step_descent_witness`):
    Proves why `v_2(t) ≥ 2` (`t = 4 * q` with `q` odd, first allowed at `s = 13` where `3 * 4 < 13`)
    does NOT automatically descend at step `v + 1 = 3`:
    when `k_0 = 0` (`n` odd and `T^1(n)` odd), the first `v = 2` steps of both `n` and `n + 4 * q`
    are odd (`a_2 = 2`), giving `4 * T^2(n) = 9 * n + 5` and `T^2(n + 4 * q) = T^2(n) + 9 * q`.
    Even when `T^2(n)` is odd (`k_1 = 0`) so that `T^2(n + 4 * q)` is even and step 3 halves,
    `8 * T^3(n + 4 * q) = 9 * n + 36 * q + 5 > 8 * n` (because `3 ^ 2 = 9 > 8 = 2 ^ 3`).
    Certified both generally and on `(n = 7, t = 4, u_s = 11)`, where `T^2(7) = 17`, `T^2(11) = 26`,
    and `T^3(11) = 13 > 7`. -/
theorem surplus_v2_ge_two_no_three_step_descent_witness :
    (∀ n q : Nat,
      n % 2 = 1 →
      (acceleratedCollatz n) % 2 = 1 →
      (iterateAccelerated n 2) % 2 = 1 →
      q % 2 = 1 →
      4 * iterateAccelerated n 2 = 9 * n + 5 ∧
      iterateAccelerated (n + 4 * q) 2 = iterateAccelerated n 2 + 9 * q ∧
      (iterateAccelerated (n + 4 * q) 2) % 2 = 0 ∧
      8 * iterateAccelerated (n + 4 * q) 3 = 9 * n + 36 * q + 5 ∧
      iterateAccelerated (n + 4 * q) 3 > n) ∧
    (iterateAccelerated 7 2 = 17 ∧
     iterateAccelerated 11 2 = 26 ∧
     iterateAccelerated 11 3 = 13 ∧
     13 > 7) := by
  refine ⟨?_, by decide⟩
  intro n q hn_odd hT1_odd hT2_odd hq_odd
  have hm0 : stepParityMatches n true := by dsimp [stepParityMatches]; exact hn_odd
  have hs1 : 2 * acceleratedCollatz n = 3 * n + 1 := by
    have hs := acceleratedCollatz_step_eq n true hm0; simpa using hs
  have hm1 : stepParityMatches (acceleratedCollatz n) true := by
    dsimp [stepParityMatches]; exact hT1_odd
  have hs2 : 2 * iterateAccelerated n 2 = 3 * acceleratedCollatz n + 1 := by
    have hs := acceleratedCollatz_step_eq (acceleratedCollatz n) true hm1
    exact hs
  have hT2_eq : 4 * iterateAccelerated n 2 = 9 * n + 5 := by omega
  have hu_odd : (n + 4 * q) % 2 = 1 := by omega
  have hmu0 : stepParityMatches (n + 4 * q) true := by dsimp [stepParityMatches]; exact hu_odd
  have hsu1 : 2 * acceleratedCollatz (n + 4 * q) = 3 * (n + 4 * q) + 1 := by
    have hs := acceleratedCollatz_step_eq (n + 4 * q) true hmu0; simpa using hs
  have hTu1_odd : (acceleratedCollatz (n + 4 * q)) % 2 = 1 := by omega
  have hmu1 : stepParityMatches (acceleratedCollatz (n + 4 * q)) true := by
    dsimp [stepParityMatches]; exact hTu1_odd
  have hsu2 : 2 * iterateAccelerated (n + 4 * q) 2 =
      3 * acceleratedCollatz (n + 4 * q) + 1 := by
    have hs := acceleratedCollatz_step_eq (acceleratedCollatz (n + 4 * q)) true hmu1
    exact hs
  have hTu2_shift : iterateAccelerated (n + 4 * q) 2 = iterateAccelerated n 2 + 9 * q := by omega
  have hTu2_even : (iterateAccelerated (n + 4 * q) 2) % 2 = 0 := by omega
  have hmu2 : stepParityMatches (iterateAccelerated (n + 4 * q) 2) false := by
    dsimp [stepParityMatches]; exact hTu2_even
  have hsu3 : 2 * iterateAccelerated (n + 4 * q) 3 = iterateAccelerated (n + 4 * q) 2 := by
    have hs := acceleratedCollatz_step_eq (iterateAccelerated (n + 4 * q) 2) false hmu2
    exact hs
  refine ⟨hT2_eq, hTu2_shift, hTu2_even, by omega, by omega⟩

/-- Formal Falsification Witness CE-C10-12
    (`non_preCrossing_diophantine_solution_at_s5_witness`):
    Proves that if `PreCrossingReturnSeq ks` is omitted, formal integer solutions to
    `B_s = Δ_s * n + 2^{K_s} * t` with `n > 1` and `0 ≤ t < s / 3` DO exist already at
    `s = 5, K_5 = 8, Δ_5 = 13`: for `ks = [0, 0, 1, 2, 0]`, `B_5 = 347 = 13 * 7 + 256 * 1`
    (`n = 7 > 1, t = 1`), `validParityWord 7 (returnMapWord ks)` holds and
    `applyParityWord 7 (returnMapWord ks) = 8 = 7 + 1`, but `ks` is eliminated by the prefix
    crossing at `j = 4` (`K_4 = 7, 2^7 = 128 > 81 = 3^4`), where `u_4 = 5 < 7` already descended. -/
theorem non_preCrossing_diophantine_solution_at_s5_witness :
    let ks := [0, 0, 1, 2, 0]
    ks.length = 5 ∧
    totalValuation ks = 8 ∧
    2 ^ totalValuation ks - 3 ^ ks.length = 13 ∧
    wordB (returnMapWord ks) = 347 ∧
    13 * 7 + 2 ^ 8 * 1 = 347 ∧
    3 * 1 < 5 ∧
    validParityWord 7 (returnMapWord ks) ∧
    applyParityWord 7 (returnMapWord ks) = 8 ∧
    ¬PreCrossingReturnSeq ks ∧
    applyParityWord 7 (returnMapWord [0, 0, 1, 2]) = 5 ∧
    5 < 7 := by
  dsimp [PreCrossingReturnSeq, preCrossingFrom, totalValuation, returnMapWord,
         singleOddWord, wordB, validParityWord, stepParityMatches,
         acceleratedCollatz, applyParityWord]
  decide

/-! ## Section 16: Final-Block Surplus Decomposition, Multi-Step Post-Crossing Self-Similarity
    Operator (`v_2(t) ≥ 2` Extended Even-Run Descent), and 3-Adic Endpoint Obstructions -/

/-- Exact Endpoint Decomposition (`Δ_s * (n + t) + 3^s * t = B_s`) and Surplus-Reduced Survivor Cap
    (`first_crossing_endpoint_decomposition_and_surplus_reduced_cap`):
    For ANY pre-crossing sequence `ks` (`PreCrossingReturnSeq ks`, `s = ks.length ≥ 1`,
    `Δ_s = 2 ^ K_s - 3 ^ s > 0`) and any `n, t : Nat` satisfying `Δ_s * n + 2 ^ K_s * t = B_s`:
    1. `Δ_s * (n + t) + 3 ^ s * t = B_s` (i.e., `Δ_s * u_s + 3^s * t = B_s`),
    2. `3 * (Δ_s * (n + t)) + 3 * t * 3 ^ s ≤ s * 3 ^ s` (reducing the coarse block budget from `s` to `s - 3 * t`),
    3. `2 * (Δ_s * (n + t)) + 6 * t * 3 ^ (s - 1) + 3 ^ (s - 1) ≤ 2 * s * 3 ^ (s - 1) + 1`
       (sharpened surplus-reduced cap on `u_s = n + t` and `n`). -/
theorem first_crossing_endpoint_decomposition_and_surplus_reduced_cap
    (ks : List Nat) (n t : Nat)
    (hs1 : ks.length ≥ 1)
    (hpre : PreCrossingReturnSeq ks)
    (hcont : 2 ^ totalValuation ks > 3 ^ ks.length)
    (hdioph : (2 ^ totalValuation ks - 3 ^ ks.length) * n +
      2 ^ totalValuation ks * t = wordB (returnMapWord ks)) :
    let s := ks.length
    let K := totalValuation ks
    let delta := 2 ^ K - 3 ^ s
    let B := wordB (returnMapWord ks)
    delta * (n + t) + 3 ^ s * t = B ∧
    3 * (delta * (n + t)) + 3 * t * 3 ^ s ≤ s * 3 ^ s ∧
    2 * (delta * (n + t)) + 6 * t * 3 ^ (s - 1) + 3 ^ (s - 1) ≤
      2 * s * 3 ^ (s - 1) + 1 := by
  dsimp
  have hmul_add : (2 ^ totalValuation ks - 3 ^ ks.length) * (n + t) =
      (2 ^ totalValuation ks - 3 ^ ks.length) * n +
        (2 ^ totalValuation ks - 3 ^ ks.length) * t :=
    Nat.mul_add (2 ^ totalValuation ks - 3 ^ ks.length) n t
  have hsub_mul_t : (2 ^ totalValuation ks - 3 ^ ks.length) * t =
      2 ^ totalValuation ks * t - 3 ^ ks.length * t :=
    Nat.sub_mul (2 ^ totalValuation ks) (3 ^ ks.length) t
  have hle_t : 3 ^ ks.length * t ≤ 2 ^ totalValuation ks * t :=
    Nat.mul_le_mul_right t (by omega)
  have hend : (2 ^ totalValuation ks - 3 ^ ks.length) * (n + t) + 3 ^ ks.length * t =
      wordB (returnMapWord ks) := by omega
  have hcoarse := (preCrossing_returnMap_offset_upper_bound ks hpre).1
  have hsharp := preCrossing_returnMap_offset_sharpened_bound ks hpre hs1
  have h3s_eq : 3 ^ ks.length = 3 ^ (ks.length - 1) * 3 := by
    cases hlen : ks.length with
    | zero => omega
    | succ m =>
      rw [Nat.add_sub_cancel, Nat.pow_succ 3 m]
  have hcoarse_red : 3 * ((2 ^ totalValuation ks - 3 ^ ks.length) * (n + t)) +
      3 * t * 3 ^ ks.length ≤ ks.length * 3 ^ ks.length := by
    have h1 : 3 * (3 ^ ks.length * t) = 3 * t * 3 ^ ks.length := by
      rw [Nat.mul_comm (3 ^ ks.length) t, ← Nat.mul_assoc 3 t (3 ^ ks.length)]
    omega
  have hsharp_red : 2 * ((2 ^ totalValuation ks - 3 ^ ks.length) * (n + t)) +
      6 * t * 3 ^ (ks.length - 1) + 3 ^ (ks.length - 1) ≤
      2 * ks.length * 3 ^ (ks.length - 1) + 1 := by
    have h2 : 2 * (3 ^ ks.length * t) = 6 * t * 3 ^ (ks.length - 1) := by
      rw [h3s_eq, Nat.mul_comm (3 ^ (ks.length - 1)) 3,
          Nat.mul_assoc 3 (3 ^ (ks.length - 1)) t,
          Nat.mul_comm (3 ^ (ks.length - 1)) t,
          ← Nat.mul_assoc 3 t (3 ^ (ks.length - 1)),
          ← Nat.mul_assoc 2 (3 * t) (3 ^ (ks.length - 1)),
          ← Nat.mul_assoc 2 3 t]
    omega
  exact ⟨hend, hcoarse_red, hsharp_red⟩

/-- Final-Block Valuation Lower Bound (`k ≥ 1`), Offset Reduction Identity, and 3-Adic Endpoint Lock
    (`first_crossing_final_block_valuation_and_mod3_lock`):
    For ANY pre-crossing sequence `ks ++ [k]` (`PreCrossingReturnSeq (ks ++ [k])`) that crosses at the
    final block (`2 ^ totalValuation (ks ++ [k]) > 3 ^ (ks ++ [k]).length`):
    1. `k ≥ 1` (the final crossing block cannot have `k = 0`),
    2. `2 ^ (k + 1) * B_s = 3 * (2 ^ (k + 1) * B_{s-1} + 3 ^ ks.length) + Δ_s`,
    3. `(2 ^ (k + 1) * B_s - Δ_s) % 3 = 0`, and
    4. For any `n ≥ 1, t : Nat` solving `Δ_s * n + 2 ^ K_s * t = B_s`, there exists an intermediate
       penultimate odd return `u_{s-1} = applyParityWord n (returnMapWord ks)` such that
       `2 ^ (k + 1) * (n + t) = 3 * u_{s-1} + 1`, `(2 ^ (k + 1) * (n + t)) % 3 = 1`, and `(n + t) % 3 ≠ 0`.
       In particular, for `t = 0` (`Δ_s * n = B_s`), `n % 3 ≠ 0` and `(2 ^ (k + 1) * n) % 3 = 1`. -/
theorem first_crossing_final_block_valuation_and_mod3_lock
    (ks : List Nat) (k : Nat)
    (hpre : PreCrossingReturnSeq (ks ++ [k]))
    (hcont : 2 ^ totalValuation (ks ++ [k]) > 3 ^ (ks ++ [k]).length) :
    let s := (ks ++ [k]).length
    let K_s := totalValuation (ks ++ [k])
    let delta := 2 ^ K_s - 3 ^ s
    let B_s := wordB (returnMapWord (ks ++ [k]))
    let B_prev := wordB (returnMapWord ks)
    k ≥ 1 ∧
    2 ^ (k + 1) * B_s = 3 * (2 ^ (k + 1) * B_prev + 3 ^ ks.length) + delta ∧
    (2 ^ (k + 1) * B_s - delta) % 3 = 0 ∧
    (∀ n t : Nat,
      n ≥ 1 →
      delta * n + 2 ^ K_s * t = B_s →
        let u_prev := applyParityWord n (returnMapWord ks)
        2 ^ (k + 1) * (n + t) = 3 * u_prev + 1 ∧
        (2 ^ (k + 1) * (n + t)) % 3 = 1 ∧
        (n + t) % 3 ≠ 0) := by
  dsimp
  rcases (preCrossingReturnSeq_snoc ks k).mp hpre with ⟨_, hK_prev_le⟩
  have hlen_snoc : (ks ++ [k]).length = ks.length + 1 := by
    rw [List.length_append]; rfl
  have hK_snoc : totalValuation (ks ++ [k]) = totalValuation ks + k + 1 :=
    totalValuation_snoc ks k
  have hk_ge1 : k ≥ 1 := by
    cases k with
    | zero =>
      rw [hlen_snoc, hK_snoc, Nat.pow_add 2 (totalValuation ks) 1,
          Nat.pow_succ 3 ks.length] at hcont
      have h21 : 2 ^ 1 = 2 := rfl
      rw [h21] at hcont
      omega
    | succ m => omega
  have hB_snoc : wordB (returnMapWord (ks ++ [k])) =
      3 * wordB (returnMapWord ks) + 2 ^ totalValuation ks :=
    wordB_returnMapWord_snoc ks k
  have hpow_split : 2 ^ (k + 1) * 2 ^ totalValuation ks =
      2 ^ totalValuation (ks ++ [k]) := by
    rw [hK_snoc, Nat.add_assoc (totalValuation ks) k 1,
        Nat.pow_add 2 (totalValuation ks) (k + 1), Nat.mul_comm]
  have h3_split : 3 * 3 ^ ks.length = 3 ^ (ks ++ [k]).length := by
    rw [hlen_snoc, Nat.pow_succ 3 ks.length, Nat.mul_comm]
  have hB_red : 2 ^ (k + 1) * wordB (returnMapWord (ks ++ [k])) =
      3 * (2 ^ (k + 1) * wordB (returnMapWord ks) + 3 ^ ks.length) +
        (2 ^ totalValuation (ks ++ [k]) - 3 ^ (ks ++ [k]).length) := by
    rw [hB_snoc, Nat.mul_add (2 ^ (k + 1)), hpow_split,
        Nat.mul_left_comm (2 ^ (k + 1)) 3 (wordB (returnMapWord ks)),
        Nat.mul_add 3, h3_split]
    omega
  have hmod3_zero : (2 ^ (k + 1) * wordB (returnMapWord (ks ++ [k])) -
      (2 ^ totalValuation (ks ++ [k]) - 3 ^ (ks ++ [k]).length)) % 3 = 0 := by
    omega
  refine ⟨hk_ge1, hB_red, hmod3_zero, ?_⟩
  intro n t hn1 hdioph
  have hs_pos : (ks ++ [k]).length ≥ 1 := by rw [hlen_snoc]; omega
  rcases (first_crossing_surplus_diophantine_iff_admissible_survivor
    (ks ++ [k]) n t hn1 hs_pos hpre hcont).1.mp hdioph with ⟨hv_all, hout_all⟩
  rw [returnMapWord_snoc ks k] at hv_all hout_all
  rcases (validParityWord_append (returnMapWord ks) (singleOddWord k) n).mp hv_all with
    ⟨_, hv_last⟩
  rw [applyParityWord_append (returnMapWord ks) (singleOddWord k) n] at hout_all
  have hid_last := parityWord_affine_identity (singleOddWord k)
    (applyParityWord n (returnMapWord ks)) hv_last
  have hA1 : wordA (singleOddWord k) = 3 := wordA_singleOddWord k
  have hB1 : wordB (singleOddWord k) = 1 := by
    dsimp [singleOddWord, wordB]; rw [wordA_replicate_false, wordB_replicate_false]
  have hD1 : wordD (singleOddWord k) = 2 ^ (k + 1) := by
    rw [wordD_eq_pow_two_length]; dsimp [singleOddWord]; rw [List.length_replicate]
  rw [hA1, hB1, hD1, hout_all] at hid_last
  have hmod1 : (2 ^ (k + 1) * (n + t)) % 3 = 1 := by omega
  have hne0 : (n + t) % 3 ≠ 0 := by
    intro h0
    have hmul0 : (2 ^ (k + 1) * (n + t)) % 3 = 0 := by
      rw [Nat.mul_mod, h0, Nat.mul_zero]
    omega
  exact ⟨hid_last, hmod1, hne0⟩

/-- Appending `d` even steps (`List.replicate d false`) to any parity word `w` preserves
    `wordA` and `wordB` while scaling `wordD` by `2 ^ d` (`wordABD_append_replicate_false`). -/
theorem wordABD_append_replicate_false (w : List Bool) (d : Nat) :
    wordA (w ++ List.replicate d false) = wordA w ∧
    wordB (w ++ List.replicate d false) = wordB w ∧
    wordD (w ++ List.replicate d false) = wordD w * 2 ^ d := by
  have hA : wordA (w ++ List.replicate d false) = wordA w := by
    rw [wordA_append, wordA_replicate_false, Nat.mul_one]
  have hB : wordB (w ++ List.replicate d false) = wordB w := by
    rw [wordB_append, wordA_replicate_false, wordB_replicate_false,
        Nat.one_mul, Nat.mul_zero, Nat.add_zero]
  have hD : wordD (w ++ List.replicate d false) = wordD w * 2 ^ d := by
    rw [wordD_append, wordD_eq_pow_two_length (List.replicate d false), List.length_replicate]
  exact ⟨hA, hB, hD⟩

/-- General Multi-Step Post-Crossing Self-Similarity Operator for Arbitrary Valuation `v = w.length`
    (`post_crossing_self_similarity_even_run_operator`):
    For ANY prefix parity word `w` realized by `n` (`validParityWord n w`), any `q : Nat`, and
    any post-divergence even run length `d : Nat`, let `u = n + q * wordD w`:
    1. `validParityWord u w` and `applyParityWord u w = applyParityWord n w + q * wordA w`,
    2. If `q % 2 = 1`, then `(applyParityWord u w) % 2 ≠ (applyParityWord n w) % 2` (forced parity flip),
    3. If `applyParityWord u w` undergoes `d` even halving steps (`validParityWord (applyParityWord u w) (List.replicate d false)`),
       then `u` realizes `w ++ List.replicate d false`, with exact offset-invariant affine identity:
       `(wordD w * 2 ^ d) * applyParityWord u (w ++ List.replicate d false) = wordA w * u + wordB w`, and
    4. Whenever `wordD w * 2 ^ d > wordA w` and
       `(wordD w * 2 ^ d - wordA w) * n > wordA w * (q * wordD w) + wordB w`,
       strict descent `applyParityWord u (w ++ List.replicate d false) < n` holds! -/
theorem post_crossing_self_similarity_even_run_operator
    (w : List Bool) (n q d : Nat)
    (hv : validParityWord n w) :
    let u := n + q * wordD w
    let w_ext := w ++ List.replicate d false
    validParityWord u w ∧
    applyParityWord u w = applyParityWord n w + q * wordA w ∧
    (q % 2 = 1 → (applyParityWord u w) % 2 ≠ (applyParityWord n w) % 2) ∧
    (validParityWord (applyParityWord u w) (List.replicate d false) →
      validParityWord u w_ext ∧
      (wordD w * 2 ^ d) * applyParityWord u w_ext = wordA w * u + wordB w ∧
      (wordD w * 2 ^ d > wordA w →
        (wordD w * 2 ^ d - wordA w) * n > wordA w * (q * wordD w) + wordB w →
          applyParityWord u w_ext < n)) := by
  dsimp
  rcases parityWord_residue_shift w n q hv with ⟨hv_u, hout_u⟩
  have hflip : q % 2 = 1 →
      (applyParityWord (n + q * wordD w) w) % 2 ≠ (applyParityWord n w) % 2 := by
    intro hq_odd
    have hA_odd : wordA w % 2 = 1 := wordA_odd w
    have hprod_odd : (q * wordA w) % 2 = 1 := by
      rw [Nat.mul_mod, hq_odd, hA_odd]
    rw [hout_u]
    omega
  refine ⟨hv_u, hout_u, hflip, ?_⟩
  intro hv_rep
  have hv_ext : validParityWord (n + q * wordD w) (w ++ List.replicate d false) :=
    (validParityWord_append w (List.replicate d false) (n + q * wordD w)).mpr ⟨hv_u, hv_rep⟩
  have hid_ext := parityWord_affine_identity (w ++ List.replicate d false)
    (n + q * wordD w) hv_ext
  rcases wordABD_append_replicate_false w d with ⟨hA_ext, hB_ext, hD_ext⟩
  rw [hA_ext, hB_ext, hD_ext] at hid_ext
  refine ⟨hv_ext, hid_ext, ?_⟩
  intro hcont_ext hgt_ext
  have hcont_w : wordD (w ++ List.replicate d false) > wordA (w ++ List.replicate d false) := by
    rw [hD_ext, hA_ext]; exact hcont_ext
  have hiff := (contracting_word_descent_iff (w ++ List.replicate d false)
    (n + q * wordD w) hv_ext hcont_w).mpr
  have hmul_u : wordA w * (n + q * wordD w) =
      wordA w * n + wordA w * (q * wordD w) :=
    Nat.mul_add (wordA w) n (q * wordD w)
  have hsub_n : (wordD w * 2 ^ d - wordA w) * n =
      (wordD w * 2 ^ d) * n - wordA w * n :=
    Nat.sub_mul (wordD w * 2 ^ d) (wordA w) n
  have hle_An : wordA w * n ≤ (wordD w * 2 ^ d) * n :=
    Nat.mul_le_mul_right n (by omega)
  have hlt_mul : (wordD w * 2 ^ d) *
      applyParityWord (n + q * wordD w) (w ++ List.replicate d false) <
      (wordD w * 2 ^ d) * n := by omega
  by_cases hlt : applyParityWord (n + q * wordD w) (w ++ List.replicate d false) < n
  · exact hlt
  · have hge : n ≤ applyParityWord (n + q * wordD w) (w ++ List.replicate d false) := by omega
    have hmul_ge := Nat.mul_le_mul_left (wordD w * 2 ^ d) hge
    omega

/-- Explicit 4-Step Self-Similarity Descent for `v_2(t) = 2` Surpluses (`t = 4 * q`, `q` odd)
    (`first_crossing_surplus_v2_eq_two_four_step_descent`):
    When `n` realizes a pre-crossing sequence `k₀ :: k₁ :: tl` (`s ≥ 2`, so `k₀ = 0`, `n` odd, `T^1(n)` odd)
    and finishes at `u_s = n + 4 * q` (`q` odd, `v_2(t) = 2`):
    if `T^2(u_s)` undergoes `d = 2` even halving steps (`(iterateAccelerated u_s 2) % 2 = 0` and
    `(iterateAccelerated u_s 3) % 2 = 0`), then:
    1. `16 * iterateAccelerated u_s 4 = 9 * n + 36 * q + 5`,
    2. Whenever `7 * n > 36 * q + 5` (and in particular at any first crossing whenever `7 * n ≥ 3 * ks.length + 3`),
       `iterateAccelerated u_s 4 < n` (strict descent below `n` in 4 post-crossing steps!).
    3. Concrete witness at `n = 15, q = 1, t = 4, u_s = 19`: `T^3(19) = 22 > 15` (3 steps does not descend),
       whereas `T^4(19) = 11 < 15` (`16 * 11 = 9 * 15 + 36 + 5 = 176`). -/
theorem first_crossing_surplus_v2_eq_two_four_step_descent
    (k₀ k₁ : Nat) (tl : List Nat) (n q : Nat)
    (hpre : PreCrossingReturnSeq (k₀ :: k₁ :: tl))
    (hv : validParityWord n (returnMapWord (k₀ :: k₁ :: tl)))
    (hq_odd : q % 2 = 1)
    (hus : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) = n + 4 * q)
    (hev2 : (iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2) % 2 = 0)
    (hev3 : (iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 3) % 2 = 0) :
    let ks := k₀ :: k₁ :: tl
    let u_s := applyParityWord n (returnMapWord ks)
    16 * iterateAccelerated u_s 4 = 9 * n + 36 * q + 5 ∧
    (7 * n > 36 * q + 5 → iterateAccelerated u_s 4 < n) ∧
    (2 ^ totalValuation ks > 3 ^ ks.length →
      7 * n ≥ 3 * ks.length + 3 →
        iterateAccelerated u_s 4 < n) ∧
    (iterateAccelerated 19 3 = 22 ∧ 22 > 15 ∧
     iterateAccelerated 19 4 = 11 ∧ 11 < 15) := by
  dsimp
  rcases (preCrossing_first_valuation_eq_zero_and_first_step_odd k₀ k₁ tl n hpre).2 hv with
    ⟨hn_odd, _, _⟩
  have hu_odd : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) % 2 = 1 := by
    rw [hus]; omega
  have hmu0 : stepParityMatches (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) true := by
    dsimp [stepParityMatches]; exact hu_odd
  have hsu1 : 2 * acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) =
      3 * (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) + 1 := by
    have hs := acceleratedCollatz_step_eq
      (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) true hmu0
    simpa using hs
  have hTu1_odd : (acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)))) % 2 = 1 := by
    omega
  have hmu1 : stepParityMatches
      (acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)))) true := by
    dsimp [stepParityMatches]; exact hTu1_odd
  have hsu2 : 2 * iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2 =
      3 * acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) + 1 := by
    have hs := acceleratedCollatz_step_eq
      (acceleratedCollatz (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)))) true hmu1
    exact hs
  have hmu2 : stepParityMatches
      (iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2) false := by
    dsimp [stepParityMatches]; exact hev2
  have hsu3 : 2 * iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 3 =
      iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2 := by
    have hs := acceleratedCollatz_step_eq
      (iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2) false hmu2
    exact hs
  have hmu3 : stepParityMatches
      (iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 3) false := by
    dsimp [stepParityMatches]; exact hev3
  have hsu4 : 2 * iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 4 =
      iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 3 := by
    have hs := acceleratedCollatz_step_eq
      (iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 3) false hmu3
    exact hs
  have hit4_eq : 16 * iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 4 =
      9 * n + 36 * q + 5 := by omega
  have hdesc_of_gt : 7 * n > 36 * q + 5 →
      iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 4 < n := by
    intro hgt
    omega
  refine ⟨hit4_eq, hdesc_of_gt, ?_, by decide⟩
  intro hcont h7n
  have hge_n : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) ≥ n := by omega
  rcases first_crossing_surplus_decomposition_and_s_le_6_exclusion
    (k₀ :: k₁ :: tl) n hv hcont hge_n with ⟨_, hsurp_fn, _⟩
  have hsurp_lt := hsurp_fn hpre
  have hsub_eq : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) - n = 4 * q := by omega
  have hlen_eq : (k₀ :: k₁ :: tl).length = tl.length + 2 := rfl
  rw [hsub_eq, hlen_eq] at hsurp_lt
  exact hdesc_of_gt (by omega)

/-- Unconditional Exclusion of `v_2(t) = 1` First-Crossing Surpluses Across `2 ≤ s ≤ 1023`
    on Never-Descending Orbits Without Assuming `n > s`
    (`nondescent_orbit_no_v2_eq_one_surplus_le_1023`):
    Combining `descent_of_lt_1024` (`n ≥ 1024`) with `first_crossing_surplus_v2_eq_one_forced_two_step_descent`
    removes the hypothesis `n > s` for all `2 ≤ s ≤ 1023` on any never-descending orbit starting at `n > 1`:
    for every `q` with `q % 2 = 1`, `applyParityWord n (returnMapWord ks) ≠ n + 2 * q`. -/
theorem nondescent_orbit_no_v2_eq_one_surplus_le_1023
    (n : Nat) (k₀ k₁ : Nat) (tl : List Nat) (q : Nat)
    (hn1 : n > 1)
    (hnever : ∀ r : Nat, iterateAccelerated n r ≥ n)
    (hs1023 : (k₀ :: k₁ :: tl).length ≤ 1023)
    (hv : validParityWord n (returnMapWord (k₀ :: k₁ :: tl)))
    (hpre : PreCrossingReturnSeq (k₀ :: k₁ :: tl))
    (hcont : 2 ^ totalValuation (k₀ :: k₁ :: tl) > 3 ^ (k₀ :: k₁ :: tl).length)
    (hq_odd : q % 2 = 1) :
    applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) ≠ n + 2 * q := by
  intro hus
  have hn1024 : n ≥ 1024 := by
    by_cases hlt : n < 1024
    · rcases descent_of_lt_1024 n hn1 hlt with ⟨k, _, _, hk_lt⟩
      have hge := hnever k
      omega
    · omega
  have hn_gt_s : n > (k₀ :: k₁ :: tl).length := by omega
  have hdesc := (first_crossing_surplus_v2_eq_one_forced_two_step_descent
    k₀ k₁ tl n q hpre hv hq_odd hus).2.2.2.2.2 hcont hn_gt_s
  have hw_eq : returnMapWord (k₀ :: k₁ :: tl) =
      parityWordOf (returnMapWord (k₀ :: k₁ :: tl)).length n :=
    ((validParityWord_iff_eq_parityWordOf (returnMapWord (k₀ :: k₁ :: tl)) n).mp hv).symm
  have h_us_it : applyParityWord n (returnMapWord (k₀ :: k₁ :: tl)) =
      iterateAccelerated n (returnMapWord (k₀ :: k₁ :: tl)).length := by
    rw [hw_eq, applyParityWord_parityWordOf (returnMapWord (k₀ :: k₁ :: tl)).length n, ← hw_eq]
  have h_it2 : iterateAccelerated (applyParityWord n (returnMapWord (k₀ :: k₁ :: tl))) 2 =
      iterateAccelerated n ((returnMapWord (k₀ :: k₁ :: tl)).length + 2) := by
    rw [h_us_it, ← iterateAccelerated_add n (returnMapWord (k₀ :: k₁ :: tl)).length 2]
  have hge := hnever ((returnMapWord (k₀ :: k₁ :: tl)).length + 2)
  omega

/-! ## Section 17: 3-Block Pre-Crossing Prefix Trichotomy, Unconditional Multi-Branch Exhaustion on the `k_1 = 0` Subtree, and Falsification of Fixed-Horizon Post-Crossing Descent on `(0, 1, 0)` (`CE-C10-13..14`)

    Section 16 observed that 4-step post-crossing descent for `v_2(t) = 2` (`t = 4q`, `q` odd) required
    an external assumption (`d = 2` post-divergence halving steps), and asked whether multi-step
    self-similarity across admissible prefix configurations can eliminate that assumption.

    In Section 17 we execute a complete prefix classification for all pre-crossing sequences of length
    `s ≥ 4` (`k₀ :: k₁ :: k₂ :: k₃ :: tl`) and discover a sharp structural dichotomy for `t = 4`:
    1. **Exact 3-Block Pre-Crossing Prefix Trichotomy (`preCrossing_three_block_prefix_trichotomy`)**:
       Every pre-crossing sequence `k₀ :: k₁ :: k₂ :: k₃ :: tl` (`s ≥ 4`) satisfies `2^{K_1} ≤ 3`,
       `2^{K_2} ≤ 9`, and `2^{K_3} ≤ 27`, restricting `(k₀, k₁, k₂)` to **exactly three triples**:
       `(0, 0, 0)`, `(0, 0, 1)`, or `(0, 1, 0)`.
    2. **Step-3 Linear Coupling & Parity Flip on `k_1 = 0` (`surplus_four_k1_zero_step3_coupling`)**:
       Whenever `k₀ = 0` and `k₁ = 0`, `8 * T^3(n) = 27 * n + 19` and `8 * T^3(n + 4) = 9 * n + 41`,
       which obey the exact step-3 coupling identity
       `3 * T^3(n + 4) = T^3(n) + 13`.
       Because `3` and `13` are odd, `T^3(n + 4)` and `T^3(n)` are locked to **opposite parities**!
    3. **Unconditional Multi-Branch Exhaustion on the Entire `k_1 = 0` Subtree (`first_crossing_surplus_four_k1_zero_unconditional_descent`)**:
       - On branch `(0, 0, 0)` (`k₂ = 0`), `T^3(n)` is odd, which **forces** `T^3(u_s)` to be even (`d = 2`),
         giving `16 * T^4(u_s) = 9 * n + 41` and unconditional 4-step descent `T^4(u_s) < n` for all `n ≥ 6`.
       - On branch `(0, 0, 1)` (`k₂ = 1`), `T^3(n)` is even and `T^4(n) = T^3(n) / 2` is odd, which **forces**
         `T^3(u_s)` to be odd and `T^4(u_s) = T^4(n) + 7` to be **even**, giving `32 * T^5(u_s) = 27 * n + 131`
         and unconditional 5-step descent `T^5(u_s) < n` for all `n ≥ 27`.
       Thus on the entire `k_1 = 0` subtree (`s ≥ 4`), `t = 4` descends in **at most 5 steps** (`T^4(u_s) < n ∨ T^5(u_s) < n`)
       for every `n ≥ 27` with **zero** post-crossing even-run hypotheses!
    4. **Adversarial Escape & Forced 5-Odd-Step Expansion on `(0, 1, 0)` (`surplus_four_prefix_010_five_odd_steps_expansion` & `CE-C10-13..14`)**:
       On the third admissible prefix `(0, 1, 0)`, `T^2(n)` is even while `T^3(n)` and `T^4(n)` are odd.
       Consequently, `T^2(n + 4) = T^2(n) + 9` (odd), `T^3(n + 4) = 3 * T^3(n) + 14` (odd), and
       `T^4(n + 4) = 3 * T^4(n) + 20` (odd), forcing **5 consecutive odd steps** on `u_s = n + 4`:
       `32 * T^5(n + 4) = 243 * n + 1183 > 32 * n`.
       Formal falsification witnesses `CE-C10-13` (`n = 27, u_s = 31`, 56-step delay) and `CE-C10-14`
       (`n = 1051, u_s = 1055`, 80-step delay) prove that fixed-horizon local self-similarity cannot
       close `(0, 1, 0)` without global Diophantine offset constraints.
-/

/-- Complete 3-Block Pre-Crossing Prefix Trichotomy (`preCrossing_three_block_prefix_trichotomy`):
    For any pre-crossing sequence `k₀ :: k₁ :: k₂ :: k₃ :: tl` of length `s ≥ 4`
    (`PreCrossingReturnSeq (k₀ :: k₁ :: k₂ :: k₃ :: tl)`), the prefix conditions
    `2^{K_1} ≤ 3`, `2^{K_2} ≤ 9`, and `2^{K_3} ≤ 27` force `(k₀, k₁, k₂)` into
    exactly one of three admissible triples:
    `(0, 0, 0)`, `(0, 0, 1)`, or `(0, 1, 0)`. -/
theorem preCrossing_three_block_prefix_trichotomy
    (k₀ k₁ k₂ k₃ : Nat) (tl : List Nat)
    (hpre : PreCrossingReturnSeq (k₀ :: k₁ :: k₂ :: k₃ :: tl)) :
    k₀ = 0 ∧
    ((k₁ = 0 ∧ (k₂ = 0 ∨ k₂ = 1)) ∨ (k₁ = 1 ∧ k₂ = 0)) ∧
    ((k₀ = 0 ∧ k₁ = 0 ∧ k₂ = 0) ∨
     (k₀ = 0 ∧ k₁ = 0 ∧ k₂ = 1) ∨
     (k₀ = 0 ∧ k₁ = 1 ∧ k₂ = 0)) := by
  unfold PreCrossingReturnSeq at hpre
  dsimp [preCrossingFrom] at hpre
  rcases hpre with ⟨_, hK1_le, hK2_le, hK3_le, _⟩
  have hk0 : k₀ = 0 := by
    cases k₀ with
    | zero => rfl
    | succ m =>
      have hge4 : 2 ^ 2 ≤ 2 ^ (0 + (m + 1) + 1) :=
        two_pow_le_two_pow 2 (0 + (m + 1) + 1) (by omega)
      have h4 : 2 ^ 2 = 4 := rfl
      have h3 : 3 ^ 1 = 3 := rfl
      omega
  rw [hk0] at hK2_le hK3_le
  have hk1 : k₁ = 0 ∨ k₁ = 1 := by
    cases k₁ with
    | zero => exact Or.inl rfl
    | succ m₁ =>
      cases m₁ with
      | zero => exact Or.inr rfl
      | succ m₂ =>
        exfalso
        have hge16 : 2 ^ 4 ≤ 2 ^ (0 + 0 + 1 + (m₂ + 1 + 1) + 1) :=
          two_pow_le_two_pow 4 (0 + 0 + 1 + (m₂ + 1 + 1) + 1) (by omega)
        have h16 : 2 ^ 4 = 16 := rfl
        have h9 : 3 ^ 2 = 9 := rfl
        omega
  rcases hk1 with hk1_0 | hk1_1
  · rw [hk1_0] at hK3_le
    have hk2 : k₂ = 0 ∨ k₂ = 1 := by
      cases k₂ with
      | zero => exact Or.inl rfl
      | succ n₁ =>
        cases n₁ with
        | zero => exact Or.inr rfl
        | succ n₂ =>
          exfalso
          have hge32 : 2 ^ 5 ≤ 2 ^ (0 + 0 + 1 + 0 + 1 + (n₂ + 1 + 1) + 1) :=
            two_pow_le_two_pow 5 (0 + 0 + 1 + 0 + 1 + (n₂ + 1 + 1) + 1) (by omega)
          have h32 : 2 ^ 5 = 32 := rfl
          have h27 : 3 ^ 3 = 27 := rfl
          omega
    rcases hk2 with hk2_0 | hk2_1
    · exact ⟨hk0, Or.inl ⟨hk1_0, Or.inl hk2_0⟩, Or.inl ⟨hk0, hk1_0, hk2_0⟩⟩
    · exact ⟨hk0, Or.inl ⟨hk1_0, Or.inr hk2_1⟩, Or.inr (Or.inl ⟨hk0, hk1_0, hk2_1⟩)⟩
  · rw [hk1_1] at hK3_le
    have hk2_0 : k₂ = 0 := by
      cases k₂ with
      | zero => rfl
      | succ n₁ =>
        exfalso
        have hge32 : 2 ^ 5 ≤ 2 ^ (0 + 0 + 1 + 1 + 1 + (n₁ + 1) + 1) :=
          two_pow_le_two_pow 5 (0 + 0 + 1 + 1 + 1 + (n₁ + 1) + 1) (by omega)
        have h32 : 2 ^ 5 = 32 := rfl
        have h27 : 3 ^ 3 = 27 := rfl
        omega
    exact ⟨hk0, Or.inr ⟨hk1_1, hk2_0⟩, Or.inr (Or.inr ⟨hk0, hk1_1, hk2_0⟩)⟩

/-- Helper lemma: peel one step off `validParityWord (iterateAccelerated n r) (b :: bs)`
    without creating nested `acceleratedCollatz` terms. -/
theorem validParityWord_cons_iterateAccelerated (n r : Nat) (b : Bool) (bs : List Bool)
    (hv : validParityWord (iterateAccelerated n r) (b :: bs)) :
    stepParityMatches (iterateAccelerated n r) b ∧
    validParityWord (iterateAccelerated n (r + 1)) bs := by
  rcases hv with ⟨hm, hv'⟩
  rw [← iterateAccelerated_succ_right n r] at hv'
  exact ⟨hm, hv'⟩

/-- Helper lemma: single-step linear equation for `iterateAccelerated n (r + 1)` from
    `stepParityMatches (iterateAccelerated n r) b` without unfolding `iterateAccelerated`. -/
theorem iterateAccelerated_step_of_matches (n r : Nat) (b : Bool)
    (hm : stepParityMatches (iterateAccelerated n r) b) :
    2 * iterateAccelerated n (r + 1) =
      (if b then 3 * iterateAccelerated n r + 1 else iterateAccelerated n r) := by
  have hs := acceleratedCollatz_step_eq (iterateAccelerated n r) b hm
  rw [← iterateAccelerated_succ_right n r] at hs
  exact hs

/-- Helper lemma: pure linear arithmetic for `surplus_four_k1_zero_step3_coupling`. -/
theorem k1_zero_step3_algebra (n t1n t2n t3n t3u : Nat)
    (hs1 : 2 * t1n = 3 * n + 1)
    (hs2 : 2 * t2n = 3 * t1n + 1)
    (hs3 : 2 * t3n = 3 * t2n + 1)
    (hT3u : 8 * t3u = 9 * n + 36 * 1 + 5) :
    8 * t3n = 27 * n + 19 ∧
    8 * t3u = 9 * n + 41 ∧
    3 * t3u = t3n + 13 ∧
    t3u % 2 ≠ t3n % 2 := by
  omega

/-- Helper lemma: pure linear arithmetic for branch `k₂ = 0` (`(0, 0, 0)`). -/
theorem k1_zero_branch0_algebra (n t3n t3u t4u : Nat)
    (hT3u : 8 * t3u = 9 * n + 41)
    (_hcoupl : 3 * t3u = t3n + 13)
    (hm3n : t3n % 2 = 1) :
    t3u % 2 = 0 ∧
    (2 * t4u = t3u →
      16 * t4u = 9 * n + 41 ∧ (n ≥ 6 → t4u < n)) := by
  omega

/-- Helper lemma: pure linear arithmetic for branch `k₂ = 1` (`(0, 0, 1)`). -/
theorem k1_zero_branch1_algebra (n t3n t4n t3u t4u t5u : Nat)
    (hT3n : 8 * t3n = 27 * n + 19)
    (hT3u : 8 * t3u = 9 * n + 41)
    (_hcoupl : 3 * t3u = t3n + 13)
    (hm3n : t3n % 2 = 0)
    (hm4n : t4n % 2 = 1)
    (hs4n : 2 * t4n = t3n) :
    t3u % 2 = 1 ∧
    (2 * t4u = 3 * t3u + 1 →
      t4u = t4n + 7 ∧
      t4u % 2 = 0 ∧
      (2 * t5u = t4u →
        32 * t5u = 27 * n + 131 ∧ (n ≥ 27 → t5u < n))) := by
  have h1 : t3u % 2 = 1 := by clear hm4n hs4n; omega
  refine ⟨h1, ?_⟩
  intro hsu4
  clear hm3n h1
  have h2 : t4u = t4n + 7 := by clear hm4n; omega
  have h3 : t4u % 2 = 0 := by clear hT3n hT3u hs4n hsu4; omega
  refine ⟨h2, h3, ?_⟩
  intro hsu5
  clear hm4n h3
  exact ⟨by omega, fun _ => by omega⟩

/-- Helper lemma: pure linear arithmetic for steps 1–3 of the `(0, 1, 0)` expansion. -/
theorem prefix_010_steps123_algebra
    (n t1n t2n t3n t1u t2u t3u : Nat)
    (hm1 : t1n % 2 = 1)
    (hm2 : t2n % 2 = 0)
    (hm3 : t3n % 2 = 1)
    (hs1 : 2 * t1n = 3 * n + 1)
    (hs2 : 2 * t2n = 3 * t1n + 1)
    (hs3 : 2 * t3n = t2n)
    (hsu1 : 2 * t1u = 3 * (n + 4) + 1) :
    8 * t3n = 9 * n + 5 ∧
    t1u % 2 = 1 ∧
    (2 * t2u = 3 * t1u + 1 →
      t2u = t2n + 9 ∧
      t2u % 2 = 1 ∧
      (2 * t3u = 3 * t2u + 1 →
        t3u = 3 * t3n + 14 ∧
        t3u % 2 = 1)) := by
  have h8 : 8 * t3n = 9 * n + 5 := by clear hm1 hm2 hm3 hsu1; omega
  have hu1 : t1u % 2 = 1 := by clear hm2 hm3 hs2 hs3 h8; omega
  refine ⟨h8, hu1, ?_⟩
  intro hsu2
  clear hm1 hu1
  have hu2 : t2u = t2n + 9 := by clear hm2 hm3 hs3 h8; omega
  have hu2_odd : t2u % 2 = 1 := by clear hm3 hs1 hs2 hs3 hsu1 h8 hsu2; omega
  refine ⟨hu2, hu2_odd, ?_⟩
  intro hsu3
  clear hm2 hu2_odd
  have hu3 : t3u = 3 * t3n + 14 := by clear hm3 hs1 hs2 hsu1 h8 hsu2; omega
  have hu3_odd : t3u % 2 = 1 := by clear hs1 hs2 hs3 hsu1 h8 hsu2 hu2 hsu3; omega
  exact ⟨hu3, hu3_odd⟩

/-- Helper lemma: pure linear arithmetic for steps 4–5 of the `(0, 1, 0)` expansion. -/
theorem prefix_010_steps45_algebra
    (n t3n t4n t3u t4u t5u : Nat)
    (h8 : 8 * t3n = 9 * n + 5)
    (hm4 : t4n % 2 = 1)
    (hs4 : 2 * t4n = 3 * t3n + 1)
    (hu3 : t3u = 3 * t3n + 14)
    (hsu4 : 2 * t4u = 3 * t3u + 1) :
    t4u = 3 * t4n + 20 ∧
    t4u % 2 = 1 ∧
    (2 * t5u = 3 * t4u + 1 →
      32 * t5u = 243 * n + 1183 ∧ t5u > n) := by
  have hu4 : t4u = 3 * t4n + 20 := by clear h8 hm4; omega
  have hu4_odd : t4u % 2 = 1 := by clear h8 hs4 hu3 hsu4; omega
  refine ⟨hu4, hu4_odd, ?_⟩
  intro hsu5
  clear hm4 hu3 hsu4 hu4_odd
  exact ⟨by omega, by omega⟩

/-- Exact Step-3 Coupling and Parity Opposition on the `k_1 = 0` Subtree (`surplus_four_k1_zero_step3_coupling`):
    Whenever `n` realizes `returnMapWord (0 :: 0 :: k₂ :: tl)`, the first three steps of `n` are odd
    (`n % 2 = 1`, `T^1(n) % 2 = 1`, `T^2(n) % 2 = 1`), yielding:
    1. `8 * iterateAccelerated n 3 = 27 * n + 19`,
    2. `8 * iterateAccelerated (n + 4) 3 = 9 * n + 41`,
    3. `3 * iterateAccelerated (n + 4) 3 = iterateAccelerated n 3 + 13`, and
    4. `(iterateAccelerated (n + 4) 3) % 2 ≠ (iterateAccelerated n 3) % 2`
       (the parity of `T^3(n + 4)` is unconditionally opposite to the parity of `T^3(n)`!). -/
theorem surplus_four_k1_zero_step3_coupling
    (k₂ : Nat) (tl : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord (0 :: 0 :: k₂ :: tl))) :
    n % 2 = 1 ∧
    (acceleratedCollatz n) % 2 = 1 ∧
    (iterateAccelerated n 2) % 2 = 1 ∧
    8 * iterateAccelerated n 3 = 27 * n + 19 ∧
    8 * iterateAccelerated (n + 4) 3 = 9 * n + 41 ∧
    3 * iterateAccelerated (n + 4) 3 = iterateAccelerated n 3 + 13 ∧
    (iterateAccelerated (n + 4) 3) % 2 ≠ (iterateAccelerated n 3) % 2 := by
  have hv0 : validParityWord (iterateAccelerated n 0)
      (true :: true :: true :: (List.replicate k₂ false ++ returnMapWord tl)) := hv
  rcases validParityWord_cons_iterateAccelerated n 0 true _ hv0 with ⟨hm0, hv1⟩
  rcases validParityWord_cons_iterateAccelerated n 1 true _ hv1 with ⟨hm1, hv2⟩
  rcases validParityWord_cons_iterateAccelerated n 2 true _ hv2 with ⟨hm2, _⟩
  have hs1 := iterateAccelerated_step_of_matches n 0 true hm0
  have hs2 := iterateAccelerated_step_of_matches n 1 true hm1
  have hs3 := iterateAccelerated_step_of_matches n 2 true hm2
  dsimp [stepParityMatches] at hm0 hm1 hm2
  dsimp at hs1 hs2 hs3
  have hn_odd : n % 2 = 1 := hm0
  have hT1_odd : (acceleratedCollatz n) % 2 = 1 := hm1
  have hT2_odd : (iterateAccelerated n 2) % 2 = 1 := hm2
  have h1_odd : (1 : Nat) % 2 = 1 := rfl
  rcases (surplus_v2_ge_two_no_three_step_descent_witness).1 n 1 hn_odd hT1_odd hT2_odd h1_odd with
    ⟨_, _, _, hT3u, _⟩
  have hn4 : n + 4 * 1 = n + 4 := by omega
  rw [hn4] at hT3u
  rcases k1_zero_step3_algebra n
    (iterateAccelerated n 1) (iterateAccelerated n 2)
    (iterateAccelerated n 3) (iterateAccelerated (n + 4) 3)
    hs1 hs2 hs3 hT3u with ⟨h1, h2, h3, h4⟩
  exact ⟨hn_odd, hT1_odd, hT2_odd, h1, h2, h3, h4⟩

/-- Unconditional Multi-Branch Exhaustion for `t = 4` on the Entire `k_1 = 0` Subtree (`s ≥ 4`)
    Without Post-Crossing Even-Run Hypotheses (`first_crossing_surplus_four_k1_zero_unconditional_descent`):
    For ANY pre-crossing sequence `ks = k₀ :: 0 :: k₂ :: k₃ :: tl` (`s ≥ 4`, `k₁ = 0`) realized by `n`
    with endpoint `u_s = applyParityWord n (returnMapWord ks) = n + 4`:
    1. Prefix trichotomy forces `k₀ = 0` and `k₂ = 0 ∨ k₂ = 1`.
    2. On branch `(0, 0, 0)` (`k₂ = 0`), `T^3(n)` is odd, which forces `T^3(u_s)` to be even (`d = 2`),
       yielding `16 * T^4(u_s) = 9 * n + 41` and strict 4-step descent `T^4(u_s) < n` for all `n ≥ 6`.
    3. On branch `(0, 0, 1)` (`k₂ = 1`), `T^3(n)` is even and `T^4(n)` is odd, which forces `T^3(u_s)` to be odd
       and `T^4(u_s) = T^4(n) + 7` to be even, yielding `32 * T^5(u_s) = 27 * n + 131` and strict 5-step
       descent `T^5(u_s) < n` for all `n ≥ 27`.
    4. Consequently, for EVERY `n ≥ 27` on the `k_1 = 0` subtree, `u_s = n + 4` unconditionally satisfies
       `iterateAccelerated u_s 4 < n ∨ iterateAccelerated u_s 5 < n`. -/
theorem first_crossing_surplus_four_k1_zero_unconditional_descent
    (k₀ k₂ k₃ : Nat) (tl : List Nat) (n : Nat)
    (hpre : PreCrossingReturnSeq (k₀ :: 0 :: k₂ :: k₃ :: tl))
    (hv : validParityWord n (returnMapWord (k₀ :: 0 :: k₂ :: k₃ :: tl)))
    (hus : applyParityWord n (returnMapWord (k₀ :: 0 :: k₂ :: k₃ :: tl)) = n + 4) :
    let ks := k₀ :: 0 :: k₂ :: k₃ :: tl
    let u_s := applyParityWord n (returnMapWord ks)
    k₀ = 0 ∧
    (k₂ = 0 ∨ k₂ = 1) ∧
    (k₂ = 0 →
      (iterateAccelerated u_s 3) % 2 = 0 ∧
      16 * iterateAccelerated u_s 4 = 9 * n + 41 ∧
      (n ≥ 6 → iterateAccelerated u_s 4 < n)) ∧
    (k₂ = 1 →
      (iterateAccelerated u_s 3) % 2 = 1 ∧
      iterateAccelerated u_s 4 = iterateAccelerated n 4 + 7 ∧
      (iterateAccelerated u_s 4) % 2 = 0 ∧
      32 * iterateAccelerated u_s 5 = 27 * n + 131 ∧
      (n ≥ 27 → iterateAccelerated u_s 5 < n)) ∧
    (n ≥ 27 → iterateAccelerated u_s 4 < n ∨ iterateAccelerated u_s 5 < n) := by
  dsimp
  rcases preCrossing_three_block_prefix_trichotomy k₀ 0 k₂ k₃ tl hpre with
    ⟨hk0, hbranch, _⟩
  have hk2_or : k₂ = 0 ∨ k₂ = 1 := by
    rcases hbranch with ⟨_, hk2⟩ | ⟨h01, _⟩
    · exact hk2
    · omega
  have hv0 : validParityWord n (returnMapWord (0 :: 0 :: k₂ :: k₃ :: tl)) := by
    have h := hv
    rw [hk0] at h
    exact h
  rcases surplus_four_k1_zero_step3_coupling k₂ (k₃ :: tl) n hv0 with
    ⟨_, _, _, hT3n, hT3u, hcoupl, _⟩
  rw [hus]
  have hbranch0 : k₂ = 0 →
      (iterateAccelerated (n + 4) 3) % 2 = 0 ∧
      16 * iterateAccelerated (n + 4) 4 = 9 * n + 41 ∧
      (n ≥ 6 → iterateAccelerated (n + 4) 4 < n) := by
    intro hk2_0
    have hv000 : validParityWord n (returnMapWord (0 :: 0 :: 0 :: k₃ :: tl)) := by
      have h := hv0
      rw [hk2_0] at h
      exact h
    have hv000' : validParityWord (iterateAccelerated n 0)
        (true :: true :: true :: true :: (List.replicate k₃ false ++ returnMapWord tl)) := hv000
    rcases validParityWord_cons_iterateAccelerated n 0 true _ hv000' with ⟨_, hv1⟩
    rcases validParityWord_cons_iterateAccelerated n 1 true _ hv1 with ⟨_, hv2⟩
    rcases validParityWord_cons_iterateAccelerated n 2 true _ hv2 with ⟨_, hv3⟩
    rcases validParityWord_cons_iterateAccelerated n 3 true _ hv3 with ⟨hm3n, _⟩
    dsimp [stepParityMatches] at hm3n
    rcases k1_zero_branch0_algebra n
      (iterateAccelerated n 3) (iterateAccelerated (n + 4) 3) (iterateAccelerated (n + 4) 4)
      hT3u hcoupl hm3n with ⟨hT3u_even, hstep4⟩
    have hmu3 : stepParityMatches (iterateAccelerated (n + 4) 3) false := by
      dsimp [stepParityMatches]; exact hT3u_even
    have hsu4 := iterateAccelerated_step_of_matches (n + 4) 3 false hmu3
    dsimp at hsu4
    rcases hstep4 hsu4 with ⟨h16, hlt4⟩
    exact ⟨hT3u_even, h16, hlt4⟩
  have hbranch1 : k₂ = 1 →
      (iterateAccelerated (n + 4) 3) % 2 = 1 ∧
      iterateAccelerated (n + 4) 4 = iterateAccelerated n 4 + 7 ∧
      (iterateAccelerated (n + 4) 4) % 2 = 0 ∧
      32 * iterateAccelerated (n + 4) 5 = 27 * n + 131 ∧
      (n ≥ 27 → iterateAccelerated (n + 4) 5 < n) := by
    intro hk2_1
    have hv001 : validParityWord n (returnMapWord (0 :: 0 :: 1 :: k₃ :: tl)) := by
      have h := hv0
      rw [hk2_1] at h
      exact h
    have hv001' : validParityWord (iterateAccelerated n 0)
        (true :: true :: true :: false :: true :: (List.replicate k₃ false ++ returnMapWord tl)) := hv001
    rcases validParityWord_cons_iterateAccelerated n 0 true _ hv001' with ⟨_, hv1⟩
    rcases validParityWord_cons_iterateAccelerated n 1 true _ hv1 with ⟨_, hv2⟩
    rcases validParityWord_cons_iterateAccelerated n 2 true _ hv2 with ⟨_, hv3⟩
    rcases validParityWord_cons_iterateAccelerated n 3 false _ hv3 with ⟨hm3n, hv4⟩
    rcases validParityWord_cons_iterateAccelerated n 4 true _ hv4 with ⟨hm4n, _⟩
    have hs4n := iterateAccelerated_step_of_matches n 3 false hm3n
    dsimp [stepParityMatches] at hm3n hm4n
    dsimp at hs4n
    rcases k1_zero_branch1_algebra n
      (iterateAccelerated n 3) (iterateAccelerated n 4)
      (iterateAccelerated (n + 4) 3) (iterateAccelerated (n + 4) 4) (iterateAccelerated (n + 4) 5)
      hT3n hT3u hcoupl hm3n hm4n hs4n with ⟨hT3u_odd, hstep4⟩
    have hmu3 : stepParityMatches (iterateAccelerated (n + 4) 3) true := by
      dsimp [stepParityMatches]; exact hT3u_odd
    have hsu4 := iterateAccelerated_step_of_matches (n + 4) 3 true hmu3
    dsimp at hsu4
    rcases hstep4 hsu4 with ⟨hT4u_shift, hT4u_even, hstep5⟩
    have hmu4 : stepParityMatches (iterateAccelerated (n + 4) 4) false := by
      dsimp [stepParityMatches]; exact hT4u_even
    have hsu5 := iterateAccelerated_step_of_matches (n + 4) 4 false hmu4
    dsimp at hsu5
    rcases hstep5 hsu5 with ⟨h32, hlt5⟩
    exact ⟨hT3u_odd, hT4u_shift, hT4u_even, h32, hlt5⟩
  refine ⟨hk0, hk2_or, hbranch0, hbranch1, ?_⟩
  intro hn27
  rcases hk2_or with hk2_0 | hk2_1
  · exact Or.inl ((hbranch0 hk2_0).2.2 (by omega))
  · exact Or.inr ((hbranch1 hk2_1).2.2.2.2 hn27)

/-- Forced 5-Odd-Step Expansion on the `(0, 1, 0)` Pre-Crossing Branch for `t = 4`
    (`surplus_four_prefix_010_five_odd_steps_expansion`):
    For ANY integer `n` realizing `returnMapWord (0 :: 1 :: 0 :: k₃ :: tl)`:
    1. `n % 2 = 1`, `T^1(n) % 2 = 1`, `T^2(n) % 2 = 0`, `T^3(n) % 2 = 1`, and `T^4(n) % 2 = 1`,
    2. For `u_s = n + 4`, `T^2(u_s) = T^2(n) + 9` is odd, `T^3(u_s) = 3 * T^3(n) + 14` is odd,
       and `T^4(u_s) = 3 * T^4(n) + 20` is odd,
    3. Thus `u_s = n + 4` is forced to take **5 consecutive odd steps**, satisfying
       `32 * iterateAccelerated (n + 4) 5 = 243 * n + 1183` and `iterateAccelerated (n + 4) 5 > n`. -/
theorem surplus_four_prefix_010_five_odd_steps_expansion
    (k₃ : Nat) (tl : List Nat) (n : Nat)
    (hv : validParityWord n (returnMapWord (0 :: 1 :: 0 :: k₃ :: tl))) :
    let u_s := n + 4
    n % 2 = 1 ∧
    (acceleratedCollatz n) % 2 = 1 ∧
    (iterateAccelerated n 2) % 2 = 0 ∧
    (iterateAccelerated n 3) % 2 = 1 ∧
    (iterateAccelerated n 4) % 2 = 1 ∧
    iterateAccelerated u_s 2 = iterateAccelerated n 2 + 9 ∧
    (iterateAccelerated u_s 2) % 2 = 1 ∧
    iterateAccelerated u_s 3 = 3 * iterateAccelerated n 3 + 14 ∧
    (iterateAccelerated u_s 3) % 2 = 1 ∧
    iterateAccelerated u_s 4 = 3 * iterateAccelerated n 4 + 20 ∧
    (iterateAccelerated u_s 4) % 2 = 1 ∧
    32 * iterateAccelerated u_s 5 = 243 * n + 1183 ∧
    iterateAccelerated u_s 5 > n := by
  dsimp
  have hv0 : validParityWord (iterateAccelerated n 0)
      (true :: true :: false :: true :: true :: (List.replicate k₃ false ++ returnMapWord tl)) := hv
  rcases validParityWord_cons_iterateAccelerated n 0 true _ hv0 with ⟨hm0, hv1⟩
  rcases validParityWord_cons_iterateAccelerated n 1 true _ hv1 with ⟨hm1, hv2⟩
  rcases validParityWord_cons_iterateAccelerated n 2 false _ hv2 with ⟨hm2, hv3⟩
  rcases validParityWord_cons_iterateAccelerated n 3 true _ hv3 with ⟨hm3, hv4⟩
  rcases validParityWord_cons_iterateAccelerated n 4 true _ hv4 with ⟨hm4, _⟩
  have hs1 := iterateAccelerated_step_of_matches n 0 true hm0
  have hs2 := iterateAccelerated_step_of_matches n 1 true hm1
  have hs3 := iterateAccelerated_step_of_matches n 2 false hm2
  have hs4 := iterateAccelerated_step_of_matches n 3 true hm3
  dsimp [stepParityMatches] at hm0 hm1 hm2 hm3 hm4
  dsimp at hs1 hs2 hs3 hs4
  have hn_odd : n % 2 = 1 := hm0
  have hT1_odd : (acceleratedCollatz n) % 2 = 1 := hm1
  have hu0_odd : (iterateAccelerated (n + 4) 0) % 2 = 1 := by
    change (n + 4) % 2 = 1
    rw [Nat.add_mod, hn_odd]
  have hmu0 : stepParityMatches (iterateAccelerated (n + 4) 0) true := by
    dsimp [stepParityMatches]; exact hu0_odd
  have hsu1 := iterateAccelerated_step_of_matches (n + 4) 0 true hmu0
  dsimp at hsu1
  rcases prefix_010_steps123_algebra n
    (iterateAccelerated n 1) (iterateAccelerated n 2) (iterateAccelerated n 3)
    (iterateAccelerated (n + 4) 1) (iterateAccelerated (n + 4) 2) (iterateAccelerated (n + 4) 3)
    hm1 hm2 hm3 hs1 hs2 hs3 hsu1 with ⟨h8, hu1_odd, hstep2⟩
  have hmu1 : stepParityMatches (iterateAccelerated (n + 4) 1) true := by
    dsimp [stepParityMatches]; exact hu1_odd
  have hsu2 := iterateAccelerated_step_of_matches (n + 4) 1 true hmu1
  dsimp at hsu2
  rcases hstep2 hsu2 with ⟨hu2_shift, hu2_odd, hstep3⟩
  have hmu2 : stepParityMatches (iterateAccelerated (n + 4) 2) true := by
    dsimp [stepParityMatches]; exact hu2_odd
  have hsu3 := iterateAccelerated_step_of_matches (n + 4) 2 true hmu2
  dsimp at hsu3
  rcases hstep3 hsu3 with ⟨hu3_shift, hu3_odd⟩
  have hmu3 : stepParityMatches (iterateAccelerated (n + 4) 3) true := by
    dsimp [stepParityMatches]; exact hu3_odd
  have hsu4 := iterateAccelerated_step_of_matches (n + 4) 3 true hmu3
  dsimp at hsu4
  rcases prefix_010_steps45_algebra n
    (iterateAccelerated n 3) (iterateAccelerated n 4)
    (iterateAccelerated (n + 4) 3) (iterateAccelerated (n + 4) 4) (iterateAccelerated (n + 4) 5)
    h8 hm4 hs4 hu3_shift hsu4 with ⟨hu4_shift, hu4_odd, hstep5⟩
  have hmu4 : stepParityMatches (iterateAccelerated (n + 4) 4) true := by
    dsimp [stepParityMatches]; exact hu4_odd
  have hsu5 := iterateAccelerated_step_of_matches (n + 4) 4 true hmu4
  dsimp at hsu5
  rcases hstep5 hsu5 with ⟨h32_eq, hgt_n⟩
  exact ⟨hn_odd, hT1_odd, hm2, hm3, hm4,
         hu2_shift, hu2_odd, hu3_shift, hu3_odd, hu4_shift, hu4_odd,
         h32_eq, hgt_n⟩

set_option maxRecDepth 20000

/-- Formal Falsification Witnesses CE-C10-13 and CE-C10-14
    (`prefix_010_long_post_crossing_delay_witnesses`):
    Certifies that on the `(0, 1, 0)` pre-crossing branch (`n ≡ 27 (mod 32)`), a hypothetical
    `t = 4` endpoint `u_s = n + 4 ≡ 31 (mod 32)` escapes bounded-depth local descent:
    1. (`CE-C10-13`) At `n = 27` (`u_s = 31`, realizing `returnMapWord [0, 1, 0, 0]`),
       `32 * T^5(31) = 243 * 27 + 1183`, `T^5(31) = 242 > 27`, `T^{55}(31) = 46 ≥ 27`, and
       `T^{56}(31) = 23 < 27` (a 56-step post-crossing delay before descending below `n = 27`).
    2. (`CE-C10-14`) At `n = 1051` (`u_s = 1055`, realizing `returnMapWord [0, 1, 0, 0]`),
       `32 * T^5(1055) = 243 * 1051 + 1183`, `T^5(1055) = 8018 > 1051`, `T^{79}(1055) = 1256 ≥ 1051`,
       and `T^{80}(1055) = 628 < 1051` (an 80-step post-crossing delay). -/
theorem prefix_010_long_post_crossing_delay_witnesses :
    (validParityWordBool 27 (returnMapWord [0, 1, 0, 0]) = true ∧
     32 * iterateAccelerated 31 5 = 243 * 27 + 1183 ∧
     iterateAccelerated 31 5 = 242 ∧
     iterateAccelerated 31 55 = 46 ∧
     iterateAccelerated 31 56 = 23 ∧
     23 < 27) ∧
    (validParityWordBool 1051 (returnMapWord [0, 1, 0, 0]) = true ∧
     32 * iterateAccelerated 1055 5 = 243 * 1051 + 1183 ∧
     iterateAccelerated 1055 5 = 8018 ∧
     iterateAccelerated 1055 79 = 1256 ∧
     iterateAccelerated 1055 80 = 628 ∧
     628 < 1051) := by
  decide

end CollatzProofClosure
end BBB17
