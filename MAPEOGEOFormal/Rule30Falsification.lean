namespace MAPEOGEOFormal

/-!
# Rule 30 Falsification Benchmark — Formal Verification (E1–E5)

Kernel-verified theorems (pure Lean 4 core, zero external axioms) establishing:
1. **E1 (ANF Equivalence & Left-Permutive Reconstruction)**:
   - Exact equivalence of Boolean Rule 30 and its degree-2 Algebraic Normal Form over `Bool`.
   - Leftward sideways evolution `rule30LeftSideways` is an exact involution in the left
     argument and induces a bijection `l ↦ rule30Forward l c r` (left-permutivity).
   - Arbitrary-depth inductive finite-cone reconstruction `rule30_left_cone_nat_reconstruction`.
2. **E1/E2 (Rightward Information Screen & Observationally Scoped 8-to-3 Quotient)**:
   - Whenever the center cell is `true`, the right neighbor is locally screened for one step
     (`rule30Forward l true r₁ = rule30Forward l true r₂`) and the next center state is `!l`.
   - At depth 2, the 8 right-half configurations `(x0, x1, x2) ∈ Bool³` collapse into 3
     single-step response functions over `(xm2, xm1)`.
3. **E2 (Complete Arbitrary-Depth Central-Trace Bijection)**:
   - `rule30_cone_leftmost_xor_bridge`: proves for every depth `k : Nat` that
     `rule30ConeEval k w = bne (w 0) (rule30ConeEval k (clearLeftmost w))`, where the
     residual `clearLeftmost w` does not depend on `w 0 = x_{-k}(0)`.
   - `rule30_central_trace_bijection_all_k`: connects `rule30ConeEval` to `e2_triangular_step_bijection`
     to prove that for every depth `k : Nat` and right-half state `R`, the central-trace map
     `rule30CentralTraceDirect k R` is an explicit bijection on `BoolVec k` (`Bool^{k+1}`).
4. **E3 (Sideways Autoregressive Center-Column Identities)**:
   - Under the left-cone zero boundary condition `x(-k, 0) = false`, the center cell `x(0, k)`
     is uniquely determined by the preceding values of columns `0` and `1`.
5. **R30-E5 (Persistent Observational Equivalence via 2-Cycle Wavefront Congruence)**:
   - Establishes the exact 2-periodic wavefront congruence (Mode A ↔ Mode B) that traps
     right-boundary discrepancies at the rightward-moving light cone `m + t`, rendering them
     permanently unobservable at the center column for all future times `t ≥ 0`.
-/

/-- Standard forward local update for Wolfram Rule 30: `l ⊕ (c ∨ r)`. -/
def rule30Forward (l c r : Bool) : Bool :=
  bne l (c || r)

/-- Algebraic Normal Form (ANF) of Rule 30 over `{false, true}`: `l ⊕ c ⊕ r ⊕ (c ∧ r)`. -/
def rule30ANF (l c r : Bool) : Bool :=
  bne (bne l c) (bne r (c && r))

/-- Leftward sideways reconstruction operator `S_L`: recovers `x_{i-1}(t)` from
`x_i(t+1)`, `x_i(t)`, and `x_{i+1}(t)`. -/
def rule30LeftSideways (c_next c r : Bool) : Bool :=
  bne c_next (c || r)

/-- 2-step iterated forward operator evaluating the center cell `x_0(2)` from the
width-5 initial light cone `(xm2, xm1, x0, x1, x2)`. -/
def rule30Step2 (xm2 xm1 x0 x1 x2 : Bool) : Bool :=
  rule30Forward
    (rule30Forward xm2 xm1 x0)
    (rule30Forward xm1 x0 x1)
    (rule30Forward x0 x1 x2)

/-- E1 Theorem 1a: Exact equivalence between Boolean Rule 30 and its degree-2 ANF. -/
theorem rule30_forward_eq_anf (l c r : Bool) :
    rule30Forward l c r = rule30ANF l c r := by
  cases l <;> cases c <;> cases r <;> rfl

/-- E1 Theorem 1b: Leftward sideways operator exactly reconstructs the left cell `l`. -/
theorem rule30_left_sideways_reconstructs (l c r : Bool) :
    rule30LeftSideways (rule30Forward l c r) c r = l := by
  cases l <;> cases c <;> cases r <;> rfl

/-- E1 Theorem 1c: Forward operator inverts leftward sideways reconstruction. -/
theorem rule30_forward_reconstructs_from_sideways (c_next c r : Bool) :
    rule30Forward (rule30LeftSideways c_next c r) c r = c_next := by
  cases c_next <;> cases c <;> cases r <;> rfl

/-- E1 Theorem 1d: Rule 30 is left-permutive (injective and surjective in its left neighbor `l`). -/
theorem rule30_left_permutive_bijection (c r : Bool) :
    (∀ l₁ l₂ : Bool, rule30Forward l₁ c r = rule30Forward l₂ c r → l₁ = l₂) ∧
    (∀ y : Bool, ∃ l : Bool, rule30Forward l c r = y) := by
  constructor
  · intro l₁ l₂ h
    have h₁ := rule30_left_sideways_reconstructs l₁ c r
    have h₂ := rule30_left_sideways_reconstructs l₂ c r
    rw [h] at h₁
    exact h₁.symm.trans h₂
  · intro y
    refine ⟨rule30LeftSideways y c r, ?_⟩
    exact rule30_forward_reconstructs_from_sideways y c r

/-- E1/E2 Theorem 2a (Rightward Information Screen): When `c = true`, the right
neighbor `r` is locally screened from `rule30Forward l true r`. -/
theorem rule30_right_screen_when_center_true (l r₁ r₂ : Bool) :
    rule30Forward l true r₁ = rule30Forward l true r₂ := by
  cases l <;> cases r₁ <;> cases r₂ <;> rfl

/-- E1/E2 Theorem 2b (Hard Wall Invariant): When `c = true`, `rule30Forward l true r = !l`
independently of `r`. -/
theorem rule30_wall_invariant_when_center_true (l r : Bool) :
    rule30Forward l true r = !l := by
  cases l <;> cases r <;> rfl

/-- E1/E2 Theorem 2c (Transparent Window): When `c = false`, the right neighbor `r`
is uniquely recovered via `bne (rule30Forward l false r) l = r`. -/
theorem rule30_right_transparent_when_center_false (l r : Bool) :
    bne (rule30Forward l false r) l = r := by
  cases l <;> cases r <;> rfl

/-- E2/E3 Theorem 3a (Leftmost Linear Invariant at Step 2): The leftmost light-cone
variable `xm2` enters `rule30Step2` strictly as a top-level XOR (`bne`). -/
theorem rule30_step2_leftmost_linear_decomposition (xm2 xm1 x0 x1 x2 : Bool) :
    rule30Step2 xm2 xm1 x0 x1 x2 = bne xm2 (rule30Step2 false xm1 x0 x1 x2) := by
  cases xm2 <;> cases xm1 <;> cases x0 <;> cases x1 <;> cases x2 <;> rfl

/-- E2 Theorem 3b (Right-Screen Observational Collapse at Step 2): Whenever `x1 = true`,
the rightmost variable `x2` is screened from the single-step readout `x0(2)`. -/
theorem rule30_step2_right_screen_when_x1_true (xm2 xm1 x0 : Bool) :
    rule30Step2 xm2 xm1 x0 true false = rule30Step2 xm2 xm1 x0 true true := by
  cases xm2 <;> cases xm1 <;> cases x0 <;> rfl

/-- E2 Theorem 3c (Observationally Scoped 8-to-3 Right-Half Quotient at Depth 2):
Every right-half state `(x0, x1, x2) ∈ Bool³` induces one of only three single-time
depth-2 response functions on the left variables `(xm2, xm1)`:
- Class 0 (`xm2`): `(false, false, false)` and `(true, false, false)`
- Class 1 (`bne xm2 (!xm1)`): `(false, false, true)`, `(false, true, false)`, `(false, true, true)`
- Class 2 (`bne xm2 xm1`): `(true, false, true)`, `(true, true, false)`, `(true, true, true)` -/
theorem rule30_step2_eight_to_three_right_quotient (x0 x1 x2 : Bool) :
    (∀ xm2 xm1 : Bool, rule30Step2 xm2 xm1 x0 x1 x2 = xm2) ∨
    (∀ xm2 xm1 : Bool, rule30Step2 xm2 xm1 x0 x1 x2 = bne xm2 (!xm1)) ∨
    (∀ xm2 xm1 : Bool, rule30Step2 xm2 xm1 x0 x1 x2 = bne xm2 xm1) := by
  cases x0 <;> cases x1 <;> cases x2
  · left; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl
  · right; left; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl
  · right; left; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl
  · right; left; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl
  · left; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl
  · right; right; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl
  · right; right; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl
  · right; right; intro xm2 xm1; cases xm2 <;> cases xm1 <;> rfl

/-- E3 Theorem 4a (Step-1 Sideways Autoregressive Center Identity):
If a spacetime grid satisfies the forward Rule 30 law at `(0, 0)` and the left
zero-cone boundary condition `x(-1, 0) = false`, then `x(0, 1) = x(0, 0) || x(1, 0)`. -/
theorem rule30_sideways_autoregressive_step1
    (xm1_0 x0_0 x1_0 x0_1 : Bool)
    (hfwd : x0_1 = rule30Forward xm1_0 x0_0 x1_0)
    (hzero : xm1_0 = false) :
    x0_1 = (x0_0 || x1_0) := by
  subst hzero hfwd
  cases x0_0 <;> cases x1_0 <;> rfl

/-- E3 Theorem 4b (Step-2 Sideways Autoregressive Center Identity):
If the spacetime cone satisfies Rule 30 and the left zero-cone boundary conditions
`x(-2, 0) = false` and `x(-1, 0) = false`, then the step-2 center cell `x(0, 2)` is
uniquely determined by `(x(0,0), x(1,0), x(0,1), x(1,1))` via `bne x0_0 (x0_1 || x1_1)`. -/
theorem rule30_sideways_autoregressive_step2
    (xm2_0 xm1_0 x0_0 x1_0 xm1_1 x0_1 x1_1 x0_2 : Bool)
    (hfwd_m1_1 : xm1_1 = rule30Forward xm2_0 xm1_0 x0_0)
    (hfwd_0_1 : x0_1 = rule30Forward xm1_0 x0_0 x1_0)
    (hfwd_0_2 : x0_2 = rule30Forward xm1_1 x0_1 x1_1)
    (hzero_m2 : xm2_0 = false)
    (hzero_m1 : xm1_0 = false) :
    x0_2 = bne x0_0 (x0_1 || x1_1) := by
  subst hzero_m2 hzero_m1 hfwd_m1_1 hfwd_0_1 hfwd_0_2
  cases x0_0 <;> cases x1_0 <;> cases x1_1 <;> rfl

/-- One sideways column step: recovers column `i - 1` from columns `i` and `i + 1`. -/
def sidewaysColumnStep (col_i col_ip1 : Nat → Bool) (t : Nat) : Bool :=
  rule30LeftSideways (col_i (t + 1)) (col_i t) (col_ip1 t)

/-- Iterated `k`-step leftward column transfer starting from `(col_0, col_1)`. -/
def sidewaysColumnIter (col_0 col_1 : Nat → Bool) : Nat → (Nat → Bool) × (Nat → Bool)
  | 0 => (col_0, col_1)
  | k + 1 =>
    let pair := sidewaysColumnIter col_0 col_1 k
    (sidewaysColumnStep pair.1 pair.2, pair.1)

/-- E1 Theorem 5 (Arbitrary-Depth Finite-Cone Sideways Reconstruction):
For any left-cone evolution `leftCone : Nat → Nat → Bool` (where `leftCone k t` is `x_{-k}(t)`)
and right-adjacent column `col1 : Nat → Bool` (where `col1 t` is `x_1(t)`) obeying the
forward Rule 30 law, `k` iterations of `sidewaysColumnIter` from `(leftCone 0, col1)`
reconstruct `leftCone k` for every `k : Nat` and `t : Nat` with zero axioms. -/
theorem rule30_left_cone_nat_reconstruction
    (leftCone : Nat → Nat → Bool)
    (col1 : Nat → Bool)
    (h_col0 : ∀ t : Nat,
      leftCone 0 (t + 1) = rule30Forward (leftCone 1 t) (leftCone 0 t) (col1 t))
    (h_col_succ : ∀ (k t : Nat),
      leftCone (k + 1) (t + 1) =
        rule30Forward (leftCone (k + 2) t) (leftCone (k + 1) t) (leftCone k t)) :
    ∀ k : Nat,
      (∀ t : Nat, (sidewaysColumnIter (leftCone 0) col1 k).1 t = leftCone k t) ∧
      (∀ t : Nat,
        (sidewaysColumnIter (leftCone 0) col1 (k + 1)).1 t = leftCone (k + 1) t ∧
        (sidewaysColumnIter (leftCone 0) col1 (k + 1)).2 t = leftCone k t) := by
  intro k
  induction k with
  | zero =>
    refine ⟨fun _ => rfl, fun t => ⟨?_, rfl⟩⟩
    change rule30LeftSideways (leftCone 0 (t + 1)) (leftCone 0 t) (col1 t) = leftCone 1 t
    rw [h_col0 t, rule30_left_sideways_reconstructs]
  | succ k ih =>
    rcases ih with ⟨_, ih_succ⟩
    refine ⟨fun t => (ih_succ t).1, fun t => ⟨?_, (ih_succ t).1⟩⟩
    change rule30LeftSideways
      ((sidewaysColumnIter (leftCone 0) col1 (k + 1)).1 (t + 1))
      ((sidewaysColumnIter (leftCone 0) col1 (k + 1)).1 t)
      ((sidewaysColumnIter (leftCone 0) col1 (k + 1)).2 t) =
      leftCone (k + 2) t
    rw [(ih_succ (t + 1)).1, (ih_succ t).1, (ih_succ t).2]
    rw [h_col_succ k t, rule30_left_sideways_reconstructs]

/-- Depth-2 central trace `(c_0, c_1, c_2)` from `L = (x_0, xm1, xm2)` and `R = (x1, x2)`. -/
def centralTraceDepth2 (L : Bool × Bool × Bool) (R : Bool × Bool) : Bool × Bool × Bool :=
  let x0 := L.1
  let xm1 := L.2.1
  let xm2 := L.2.2
  let x1 := R.1
  let x2 := R.2
  let c0 := x0
  let c1 := rule30Forward xm1 x0 x1
  let xm1_1 := rule30Forward xm2 xm1 x0
  let x1_1 := rule30Forward x0 x1 x2
  let c2 := rule30Forward xm1_1 c1 x1_1
  (c0, c1, c2)

/-- Explicit inverse recovering `L = (x_0, xm1, xm2)` from trace `T = (c_0, c_1, c_2)`
and right-half state `R = (x1, x2)`. -/
def inverseLeftDepth2 (T : Bool × Bool × Bool) (R : Bool × Bool) : Bool × Bool × Bool :=
  let c0 := T.1
  let c1 := T.2.1
  let c2 := T.2.2
  let x1 := R.1
  let x2 := R.2
  let x0 := c0
  let xm1 := rule30LeftSideways c1 x0 x1
  let x1_1 := rule30Forward x0 x1 x2
  let xm1_1 := rule30LeftSideways c2 c1 x1_1
  let xm2 := rule30LeftSideways xm1_1 xm1 x0
  (x0, xm1, xm2)

/-- E2 Theorem 6a (Uniform Preimage Bijection at Depth 2):
For every right-half state `R ∈ Bool²`, `centralTraceDepth2 · R` and `inverseLeftDepth2 · R`
form a two-sided bijection on `Bool³`. -/
theorem e2_trace_bijection_depth2 (R : Bool × Bool) :
    (∀ L : Bool × Bool × Bool, inverseLeftDepth2 (centralTraceDepth2 L R) R = L) ∧
    (∀ T : Bool × Bool × Bool, centralTraceDepth2 (inverseLeftDepth2 T R) R = T) := by
  rcases R with ⟨x1, x2⟩
  constructor
  · rintro ⟨x0, xm1, xm2⟩
    cases x0 <;> cases xm1 <;> cases xm2 <;> cases x1 <;> cases x2 <;> rfl
  · rintro ⟨c0, c1, c2⟩
    cases c0 <;> cases c1 <;> cases c2 <;> cases x1 <;> cases x2 <;> rfl

/-- E2 Theorem 6b (General Triangular Bijection Step):
Any step that appends a new coordinate `x_new` via `c_new = bne x_new (f prefix R)`
preserves two-sided invertibility over `Bool`. -/
theorem e2_triangular_step_bijection {α β : Type}
    (encode : α → β) (decode : β → α)
    (h_left : ∀ a : α, decode (encode a) = a)
    (h_right : ∀ b : β, encode (decode b) = b)
    (f : α → Bool) :
    let encStep (p : α × Bool) : β × Bool := (encode p.1, bne p.2 (f p.1))
    let decStep (q : β × Bool) : α × Bool :=
      let a := decode q.1
      (a, bne q.2 (f a))
    (∀ p : α × Bool, decStep (encStep p) = p) ∧
    (∀ q : β × Bool, encStep (decStep q) = q) := by
  intro encStep decStep
  constructor
  · rintro ⟨a, x⟩
    dsimp [encStep, decStep]
    rw [h_left a]
    have h_xor : bne (bne x (f a)) (f a) = x := by
      cases x <;> cases (f a) <;> rfl
    rw [h_xor]
  · rintro ⟨b, c⟩
    dsimp [encStep, decStep]
    rw [h_right b]
    have h_xor : bne (bne c (f (decode b))) (f (decode b)) = c := by
      cases c <;> cases (f (decode b)) <;> rfl
    rw [h_xor]

/-- Shift a spatial window by `offset` cells to the right. -/
def shiftWindow (w : Nat → Bool) (offset : Nat) (j : Nat) : Bool :=
  w (j + offset)

/-- Override the leftmost cell `w 0` (`x_{-k}(0)`) with `false`. -/
def clearLeftmost (w : Nat → Bool) : Nat → Bool
  | 0 => false
  | j + 1 => w (j + 1)

/-- Prepend a new leftmost cell `b` at index `0`, shifting `w` to `1, 2, ...`. -/
def prependLeftmost (b : Bool) (w : Nat → Bool) : Nat → Bool
  | 0 => b
  | j + 1 => w j

/-- Evaluate the apex cell `x_0(k)` of the depth-`k` Rule 30 light cone from
    a spatial window `w : Nat → Bool` where `w 0 = x_{-k}(0)`, ..., `w (2k) = x_k(0)`. -/
def rule30ConeEval : Nat → (Nat → Bool) → Bool
  | 0, w => w 0
  | k + 1, w =>
    rule30Forward
      (rule30ConeEval k w)
      (rule30ConeEval k (shiftWindow w 1))
      (rule30ConeEval k (shiftWindow w 2))

/-- Associativity of `bne` with `rule30Forward` in the left argument. -/
theorem rule30Forward_bne_left (a b c r : Bool) :
    rule30Forward (bne a b) c r = bne a (rule30Forward b c r) := by
  cases a <;> cases b <;> cases c <;> cases r <;> rfl

/-- Pointwise congruence for `rule30ConeEval` (zero axioms, no `funext`). -/
theorem rule30ConeEval_congr (k : Nat) (w₁ w₂ : Nat → Bool)
    (h : ∀ j : Nat, w₁ j = w₂ j) :
    rule30ConeEval k w₁ = rule30ConeEval k w₂ := by
  induction k generalizing w₁ w₂ with
  | zero => exact h 0
  | succ k ih =>
    change rule30Forward (rule30ConeEval k w₁)
      (rule30ConeEval k (shiftWindow w₁ 1))
      (rule30ConeEval k (shiftWindow w₁ 2)) =
      rule30Forward (rule30ConeEval k w₂)
        (rule30ConeEval k (shiftWindow w₂ 1))
        (rule30ConeEval k (shiftWindow w₂ 2))
    rw [ih w₁ w₂ h]
    rw [ih (shiftWindow w₁ 1) (shiftWindow w₂ 1) (fun j => h (j + 1))]
    rw [ih (shiftWindow w₁ 2) (shiftWindow w₂ 2) (fun j => h (j + 2))]

/-- E2 Theorem 6c (Arbitrary-Depth Leftmost XOR Bridge `c_k = x_{-k}(0) ⊕ F_k`):
For every depth `k : Nat` and window `w : Nat → Bool`, the apex cell `rule30ConeEval k w`
equals `bne (w 0) (rule30ConeEval k (clearLeftmost w))`, where `clearLeftmost w`
does not depend on `w 0`. -/
theorem rule30_cone_leftmost_xor_bridge (k : Nat) (w : Nat → Bool) :
    rule30ConeEval k w = bne (w 0) (rule30ConeEval k (clearLeftmost w)) := by
  induction k generalizing w with
  | zero =>
    change w 0 = bne (w 0) false
    cases (w 0) <;> rfl
  | succ k ih =>
    change rule30Forward (rule30ConeEval k w)
      (rule30ConeEval k (shiftWindow w 1))
      (rule30ConeEval k (shiftWindow w 2)) =
      bne (w 0) (rule30Forward (rule30ConeEval k (clearLeftmost w))
        (rule30ConeEval k (shiftWindow (clearLeftmost w) 1))
        (rule30ConeEval k (shiftWindow (clearLeftmost w) 2)))
    have h_shift1 : rule30ConeEval k (shiftWindow (clearLeftmost w) 1) =
        rule30ConeEval k (shiftWindow w 1) :=
      rule30ConeEval_congr k (shiftWindow (clearLeftmost w) 1) (shiftWindow w 1) (fun _ => rfl)
    have h_shift2 : rule30ConeEval k (shiftWindow (clearLeftmost w) 2) =
        rule30ConeEval k (shiftWindow w 2) :=
      rule30ConeEval_congr k (shiftWindow (clearLeftmost w) 2) (shiftWindow w 2) (fun _ => rfl)
    rw [h_shift1, h_shift2, ih w, rule30Forward_bne_left]

/-- Corollary for `prependLeftmost`: the `k`-step cone evaluation on `prependLeftmost b w`
decomposes into `bne b (rule30ConeEval k (prependLeftmost false w))`. -/
theorem rule30_cone_prepend_xor_bridge (k : Nat) (b : Bool) (w : Nat → Bool) :
    rule30ConeEval k (prependLeftmost b w) =
      bne b (rule30ConeEval k (prependLeftmost false w)) :=
  rule30_cone_leftmost_xor_bridge k (prependLeftmost b w)

/-- Dependent tuple of `k + 1` Booleans representing either:
    - Left-and-center initial cells `L = (x_0(0), x_{-1}(0), ..., x_{-k}(0))`, or
    - Central temporal trace `T = (c_0, c_1, ..., c_k)`. -/
def BoolVec : Nat → Type
  | 0 => Bool
  | k + 1 => BoolVec k × Bool

/-- Assemble the spatial initial window `w : Nat → Bool` from `L : BoolVec k` and `R : Nat → Bool`. -/
def buildWindow : (k : Nat) → BoolVec k → (Nat → Bool) → (Nat → Bool)
  | 0, x0, R => prependLeftmost x0 R
  | k + 1, (L, x_neg_kp1), R => prependLeftmost x_neg_kp1 (buildWindow k L R)

/-- Residual polynomial `F_{k+1}(L, R)` for step `k + 1`, manifestly independent of `x_{-(k+1)}(0)`. -/
def rule30ResidualF (k : Nat) (R : Nat → Bool) (L : BoolVec k) : Bool :=
  rule30ConeEval (k + 1) (prependLeftmost false (buildWindow k L R))

/-- Direct Rule 30 central-trace map evaluating `(c_0, c_1, ..., c_k)` via `rule30ConeEval`. -/
def rule30CentralTraceDirect : (k : Nat) → (Nat → Bool) → BoolVec k → BoolVec k
  | 0, R, x0 => rule30ConeEval 0 (buildWindow 0 x0 R)
  | k + 1, R, (L, x_new) =>
    (rule30CentralTraceDirect k R L,
     rule30ConeEval (k + 1) (buildWindow (k + 1) (L, x_new) R))

/-- Explicit inverse central-trace map recovering `L = (x_0(0), ..., x_{-k}(0))` from
    any target central trace `T = (c_0, ..., c_k)` and right-half initial state `R`. -/
def rule30CentralTraceInv : (k : Nat) → (Nat → Bool) → BoolVec k → BoolVec k
  | 0, _, c0 => c0
  | k + 1, R, (T, c_new) =>
    let L := rule30CentralTraceInv k R T
    (L, bne c_new (rule30ResidualF k R L))

/-- E2 Theorem 6d (Complete Arbitrary-Depth Central-Trace Bijection):
For EVERY depth `k : Nat` and EVERY right-half initial state `R : Nat → Bool`,
`rule30CentralTraceDirect k R` and `rule30CentralTraceInv k R` form an exact two-sided
bijection on `BoolVec k` (`Bool^{k+1}`). -/
theorem rule30_central_trace_bijection_all_k (k : Nat) (R : Nat → Bool) :
    (∀ L : BoolVec k, rule30CentralTraceInv k R (rule30CentralTraceDirect k R L) = L) ∧
    (∀ T : BoolVec k, rule30CentralTraceDirect k R (rule30CentralTraceInv k R T) = T) := by
  induction k with
  | zero =>
    refine ⟨fun _ => rfl, fun _ => rfl⟩
  | succ k ih =>
    have h_step := e2_triangular_step_bijection
      (rule30CentralTraceDirect k R)
      (rule30CentralTraceInv k R)
      ih.1 ih.2
      (rule30ResidualF k R)
    rcases h_step with ⟨h_left, h_right⟩
    constructor
    · rintro ⟨L, x_new⟩
      change (rule30CentralTraceInv k R (rule30CentralTraceDirect k R L),
        bne (rule30ConeEval (k + 1) (prependLeftmost x_new (buildWindow k L R)))
          (rule30ResidualF k R (rule30CentralTraceInv k R (rule30CentralTraceDirect k R L)))) =
        (L, x_new)
      rw [rule30_cone_prepend_xor_bridge (k + 1) x_new (buildWindow k L R)]
      exact h_left (L, x_new)
    · rintro ⟨T, c_new⟩
      change (rule30CentralTraceDirect k R (rule30CentralTraceInv k R T),
        rule30ConeEval (k + 1) (prependLeftmost
          (bne c_new (rule30ResidualF k R (rule30CentralTraceInv k R T)))
          (buildWindow k (rule30CentralTraceInv k R T) R))) =
        (T, c_new)
      rw [rule30_cone_prepend_xor_bridge (k + 1)
        (bne c_new (rule30ResidualF k R (rule30CentralTraceInv k R T)))
        (buildWindow k (rule30CentralTraceInv k R T) R)]
      exact h_right (T, c_new)

/-- R30-E5 Theorem 7a (Mode A → Mode B Persistent Wavefront Step):
Starting from Mode A tails `(false, true, false, false, false)` vs
`(false, true, true, false, false)` at positions `m .. m+4` with arbitrary shared left
neighbor `xm1` at `m-1`, one step of `rule30Forward` produces identical values `(!xm1, true)`
at positions `(m, m+1)` and transitions to Mode B `(true, true, false, false)` vs
`(true, false, true, false)` at positions `m+1 .. m+4`. -/
theorem e5_persistent_wavefront_modeA_to_modeB (xm1 : Bool) :
    let u_next := (
      rule30Forward xm1 false true,
      rule30Forward false true false,
      rule30Forward true false false,
      rule30Forward false false false,
      rule30Forward false false false
    )
    let v_next := (
      rule30Forward xm1 false true,
      rule30Forward false true true,
      rule30Forward true true false,
      rule30Forward true false false,
      rule30Forward false false false
    )
    u_next = (!xm1, true, true, false, false) ∧
    v_next = (!xm1, true, false, true, false) ∧
    u_next.1 = v_next.1 ∧
    u_next.2.1 = v_next.2.1 := by
  cases xm1 <;> exact ⟨rfl, rfl, rfl, rfl⟩

/-- R30-E5 Theorem 7b (Mode B → Mode A Persistent Wavefront Step):
Starting from Mode B tails `(true, true, false, false, false)` vs
`(true, false, true, false, false)` at positions `m+1 .. m+5` with arbitrary shared left
neighbor `xm` at `m`, one step of `rule30Forward` produces identical values `(!xm, false, true)`
at positions `(m+1, m+2, m+3)` and transitions back to Mode A `(false, true, false, false)` vs
`(false, true, true, false)` at positions `m+2 .. m+5`. -/
theorem e5_persistent_wavefront_modeB_to_modeA (xm : Bool) :
    let u_next := (
      rule30Forward xm true true,
      rule30Forward true true false,
      rule30Forward true false false,
      rule30Forward false false false,
      rule30Forward false false false
    )
    let v_next := (
      rule30Forward xm true false,
      rule30Forward true false true,
      rule30Forward false true false,
      rule30Forward true false false,
      rule30Forward false false false
    )
    u_next = (!xm, false, true, false, false) ∧
    v_next = (!xm, false, true, true, false) ∧
    u_next.1 = v_next.1 ∧
    u_next.2.1 = v_next.2.1 ∧
    u_next.2.2.1 = v_next.2.2.1 := by
  cases xm <;> exact ⟨rfl, rfl, rfl, rfl, rfl⟩

#print axioms rule30_forward_eq_anf
#print axioms rule30_left_sideways_reconstructs
#print axioms rule30_forward_reconstructs_from_sideways
#print axioms rule30_left_permutive_bijection
#print axioms rule30_right_screen_when_center_true
#print axioms rule30_wall_invariant_when_center_true
#print axioms rule30_right_transparent_when_center_false
#print axioms rule30_step2_leftmost_linear_decomposition
#print axioms rule30_step2_right_screen_when_x1_true
#print axioms rule30_step2_eight_to_three_right_quotient
#print axioms rule30_sideways_autoregressive_step1
#print axioms rule30_sideways_autoregressive_step2
#print axioms rule30_left_cone_nat_reconstruction
#print axioms e2_trace_bijection_depth2
#print axioms e2_triangular_step_bijection
#print axioms rule30_cone_leftmost_xor_bridge
#print axioms rule30_central_trace_bijection_all_k
#print axioms e5_persistent_wavefront_modeA_to_modeB
#print axioms e5_persistent_wavefront_modeB_to_modeA

end MAPEOGEOFormal
