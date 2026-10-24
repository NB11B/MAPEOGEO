import TwoStepMacros

/-!
Next proof layer on top of verified checkpoint 991231b:
1. Unified configuration-equality theorem `JF_two_step_config` combining the
   three pointwise tape lemmas from `TwoStepMacros.lean`.
2. Multi-step execution combinator `iterateStep` and composition laws.
3. Exact tape-preservation lemmas when rewriting an existing `true` or `false` cell.
4. Inductive right-sweep (`B`, `I`, `P`, `Q`) and left-sweep (`D`, `G`, `K`, `M`, `N`)
   macros over arbitrary `k`-cell runs of `1`s.
5. Complete boundary turnaround macros for all sweep states:
   - `I` → `J → F → G` (`sweep_I_then_JF_to_G`)
   - `Q` → `L → M` (`QL_two_step_config`, `sweep_Q_then_L_to_M`)
   - `P` → `Q` (`sweep_P_to_Q`)
   - `G` → `H` and branches `H(1) → I`, `H(0) → A` (`sweep_G_to_H`, `sweep_G_then_H1_to_I`, `sweep_G_then_H0_to_A`)
   - `B` → `C` and branches `C(1) → D`, `C(0) → K` (`sweep_B_to_C`, `sweep_B_then_C1_to_D`, `sweep_B_then_C0_to_K`)
   - `D` → `E` and branches `E(1) → B`, `E(0) → F → G` (`sweep_D_to_E`, `sweep_D_then_E1_to_B`, `sweep_D_then_E0_to_F`, `sweep_D_then_E0_F_to_G`)
   - `K` → `A` (`sweep_K_to_A`)
   - `M` → `N` (`sweep_M_to_N`)
   - `N` → `O` beep entry (`sweep_N_to_beep_O`)
-/
namespace BBB17

/-- Resulting tape after the two-step macro `J → F` (or `Q(0) → L`) starting at head `p`. -/
def jfTape (p : Int) (t : Int → Bool) : Int → Bool :=
  fun i => if i = p + 1 then false else if i = p then true else t i

/-- Extensional tape equality combining `JF_tape_at_start`, `JF_tape_at_next`,
    and `JF_tape_elsewhere`. -/
theorem JF_two_step_tape (p : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).tape = jfTape p t := by
  funext i
  by_cases hn : i = p + 1
  · subst hn
    rw [JF_tape_at_next]
    simp [jfTape]
  · by_cases hp : i = p
    · subst hp
      rw [JF_tape_at_start]
      simp [jfTape, hn]
    · rw [JF_tape_elsewhere p i t hp hn]
      simp [jfTape, hn, hp]

/-- Complete configuration equality for the two-step transition `(J, p, t) ⊢² (G, p, jfTape p t)`. -/
theorem JF_two_step_config (p : Int) (t : Int → Bool) :
    step (step ⟨(9 : State), p, t⟩) = ⟨(6 : State), p, jfTape p t⟩ := by
  cases h : step (step ⟨(9 : State), p, t⟩) with
  | mk s hd tp =>
    have hs : s = (6 : State) := by
      have := JF_two_step_state p t
      rw [h] at this
      exact this
    have hhd : hd = p := by
      have := JF_two_step_head p t
      rw [h] at this
      exact this
    have htp : tp = jfTape p t := by
      have := JF_two_step_tape p t
      rw [h] at this
      exact this
    subst hs hhd htp
    rfl

/-! ### Multi-step iteration and tape update helpers -/

/-- Pointwise tape update at cell `p`. -/
def updateTape (t : Int → Bool) (p : Int) (b : Bool) : Int → Bool :=
  fun i => if i = p then b else t i

/-- Writing `true` to a cell that already holds `true` leaves the tape function unchanged. -/
theorem tape_write_true_eq (t : Int → Bool) (p : Int) (hp : t p = true) :
    (fun i => if i = p then true else t i) = t := by
  funext i
  by_cases h : i = p
  · subst h
    simp [hp]
  · simp [h]

/-- Writing `false` to a cell that already holds `false` leaves the tape function unchanged. -/
theorem tape_write_false_eq (t : Int → Bool) (p : Int) (hp : t p = false) :
    (fun i => if i = p then false else t i) = t := by
  funext i
  by_cases h : i = p
  · subst h
    simp [hp]
  · simp [h]

/-- `k`-step machine execution from an arbitrary starting configuration `c`. -/
def iterateStep : Nat → Config → Config
  | 0, c => c
  | k + 1, c => iterateStep k (step c)

@[simp] theorem iterateStep_zero (c : Config) :
    iterateStep 0 c = c := rfl

@[simp] theorem iterateStep_succ (k : Nat) (c : Config) :
    iterateStep (k + 1) c = iterateStep k (step c) := rfl

theorem iterateStep_add (m n : Nat) (c : Config) :
    iterateStep (m + n) c = iterateStep n (iterateStep m c) := by
  induction m generalizing c with
  | zero => simp
  | succ m ih =>
    rw [Nat.succ_add, iterateStep_succ, iterateStep_succ, ih]

theorem iterateStep_one (c : Config) :
    iterateStep 1 c = step c := rfl

theorem iterateStep_two (c : Config) :
    iterateStep 2 c = step (step c) := rfl

/-! ### Generic right-sweep and left-sweep induction over runs of `1`s -/

/-- Any state `q` whose action on `true` writes `true`, moves right, and stays in `q`
    advances the head by `+1` while preserving the tape unchanged. -/
theorem right_sweep_step (q : State) (hq : action q true = ⟨true, true, q⟩)
    (p : Int) (t : Int → Bool) (hp : t p = true) :
    step ⟨q, p, t⟩ = ⟨q, p + 1, t⟩ := by
  simp [step, hp, hq]
  funext i
  by_cases h : i = p <;> simp [h, hp]

/-- Inductive right sweep over `k` consecutive `1` cells starting at `p`. -/
theorem right_sweep_run (q : State) (hq : action q true = ⟨true, true, q⟩)
    (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    iterateStep k ⟨q, p, t⟩ = ⟨q, p + ↑k, t⟩ := by
  induction k generalizing p with
  | zero =>
    simp
  | succ k ih =>
    have hp0 : t p = true := by
      have h0 := hones 0 (Nat.zero_lt_succ k)
      simpa using h0
    rw [iterateStep_succ, right_sweep_step q hq p t hp0]
    have hshift : ∀ j : Nat, j < k → t ((p + 1) + ↑j) = true := by
      intro j hj
      have hsucc := hones (j + 1) (Nat.succ_lt_succ hj)
      have heq : (p + 1) + (↑j : Int) = p + ↑(j + 1) := by omega
      rw [heq]
      exact hsucc
    rw [ih (p + 1) hshift]
    have hhead : (p + 1) + (↑k : Int) = p + ↑(k + 1) := by omega
    rw [hhead]

/-- Any state `q` whose action on `true` writes `true`, moves left, and stays in `q`
    moves the head by `-1` while preserving the tape unchanged. -/
theorem left_sweep_step (q : State) (hq : action q true = ⟨true, false, q⟩)
    (p : Int) (t : Int → Bool) (hp : t p = true) :
    step ⟨q, p, t⟩ = ⟨q, p - 1, t⟩ := by
  simp [step, hp, hq]
  funext i
  by_cases h : i = p <;> simp [h, hp]

/-- Inductive left sweep over `k` consecutive `1` cells starting at `p`. -/
theorem left_sweep_run (q : State) (hq : action q true = ⟨true, false, q⟩)
    (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    iterateStep k ⟨q, p, t⟩ = ⟨q, p - ↑k, t⟩ := by
  induction k generalizing p with
  | zero =>
    simp
  | succ k ih =>
    have hp0 : t p = true := by
      have h0 := hones 0 (Nat.zero_lt_succ k)
      simpa using h0
    rw [iterateStep_succ, left_sweep_step q hq p t hp0]
    have hshift : ∀ j : Nat, j < k → t ((p - 1) - ↑j) = true := by
      intro j hj
      have hsucc := hones (j + 1) (Nat.succ_lt_succ hj)
      have heq : (p - 1) - (↑j : Int) = p - ↑(j + 1) := by omega
      rw [heq]
      exact hsucc
    rw [ih (p - 1) hshift]
    have hhead : (p - 1) - (↑k : Int) = p - ↑(k + 1) := by omega
    rw [hhead]

/-! ### Concrete BBB17 transition lemmas for sweep & turnaround states -/

theorem action_B_on_one : action (1 : State) true = ⟨true, true, (1 : State)⟩ := by decide
theorem action_I_on_one : action (8 : State) true = ⟨true, true, (8 : State)⟩ := by decide
theorem action_D_on_one : action (3 : State) true = ⟨true, false, (3 : State)⟩ := by decide
theorem action_G_on_one : action (6 : State) true = ⟨true, false, (6 : State)⟩ := by decide
theorem action_K_on_one : action (10 : State) true = ⟨true, false, (10 : State)⟩ := by decide
theorem action_N_on_one : action (13 : State) true = ⟨true, false, (13 : State)⟩ := by decide

theorem action_B_on_zero : action (1 : State) false = ⟨true, false, (2 : State)⟩ := by decide
theorem action_C_on_zero : action (2 : State) false = ⟨false, false, (10 : State)⟩ := by decide
theorem action_C_on_one  : action (2 : State) true  = ⟨false, false, (3 : State)⟩ := by decide
theorem action_D_on_zero : action (3 : State) false = ⟨true, true, (4 : State)⟩ := by decide
theorem action_E_on_zero : action (4 : State) false = ⟨false, true, (5 : State)⟩ := by decide
theorem action_E_on_one  : action (4 : State) true  = ⟨false, true, (1 : State)⟩ := by decide
theorem action_G_on_zero : action (6 : State) false = ⟨true, false, (7 : State)⟩ := by decide
theorem action_H_on_zero : action (7 : State) false = ⟨false, true, (0 : State)⟩ := by decide
theorem action_H_on_one  : action (7 : State) true  = ⟨false, true, (8 : State)⟩ := by decide
theorem action_I_on_zero : action (8 : State) false = ⟨true, true, (9 : State)⟩ := by decide
theorem action_K_on_zero : action (10 : State) false = ⟨false, true, (0 : State)⟩ := by decide
theorem action_L (b : Bool) : action (11 : State) b = ⟨false, false, (12 : State)⟩ := by
  cases b <;> decide
theorem action_M_on_zero : action (12 : State) false = ⟨false, false, (13 : State)⟩ := by decide
theorem action_P_on_zero : action (15 : State) false = ⟨false, true, (16 : State)⟩ := by decide
theorem action_Q_on_zero : action (16 : State) false = ⟨true, true, (11 : State)⟩ := by decide

/-! ### Concrete BBB17 state-sweep specializations -/

/-- State `I` (8) sweeps right across `k` ones without altering the tape. -/
theorem sweep_I_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    iterateStep k ⟨(8 : State), p, t⟩ = ⟨(8 : State), p + ↑k, t⟩ :=
  right_sweep_run (8 : State) action_I_on_one k p t hones

/-- State `B` (1) sweeps right across `k` ones without altering the tape. -/
theorem sweep_B_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    iterateStep k ⟨(1 : State), p, t⟩ = ⟨(1 : State), p + ↑k, t⟩ :=
  right_sweep_run (1 : State) action_B_on_one k p t hones

/-- State `P` (15) sweeps right across `k` ones without altering the tape. -/
theorem sweep_P_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    iterateStep k ⟨(15 : State), p, t⟩ = ⟨(15 : State), p + ↑k, t⟩ :=
  right_sweep_run (15 : State) action_P_on_one k p t hones

/-- State `Q` (16) sweeps right across `k` ones without altering the tape. -/
theorem sweep_Q_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    iterateStep k ⟨(16 : State), p, t⟩ = ⟨(16 : State), p + ↑k, t⟩ :=
  right_sweep_run (16 : State) action_Q_on_one k p t hones

/-- State `G` (6) sweeps left across `k` ones without altering the tape. -/
theorem sweep_G_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    iterateStep k ⟨(6 : State), p, t⟩ = ⟨(6 : State), p - ↑k, t⟩ :=
  left_sweep_run (6 : State) action_G_on_one k p t hones

/-- State `D` (3) sweeps left across `k` ones without altering the tape. -/
theorem sweep_D_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    iterateStep k ⟨(3 : State), p, t⟩ = ⟨(3 : State), p - ↑k, t⟩ :=
  left_sweep_run (3 : State) action_D_on_one k p t hones

/-- State `K` (10) sweeps left across `k` ones without altering the tape. -/
theorem sweep_K_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    iterateStep k ⟨(10 : State), p, t⟩ = ⟨(10 : State), p - ↑k, t⟩ :=
  left_sweep_run (10 : State) action_K_on_one k p t hones

/-- State `M` (12) sweeps left across `k` ones without altering the tape. -/
theorem sweep_M_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    iterateStep k ⟨(12 : State), p, t⟩ = ⟨(12 : State), p - ↑k, t⟩ :=
  left_sweep_run (12 : State) action_M_on_one k p t hones

/-- State `N` (13) sweeps left across `k` ones without altering the tape. -/
theorem sweep_N_ones (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    iterateStep k ⟨(13 : State), p, t⟩ = ⟨(13 : State), p - ↑k, t⟩ :=
  left_sweep_run (13 : State) action_N_on_one k p t hones

/-! ### Complete boundary turnaround macros -/

/-- Unconditional single step from `F` (5) to `G` (6) at `p - 1` clearing cell `p`. -/
theorem F_one_step_config (p : Int) (t : Int → Bool) :
    step ⟨(5 : State), p, t⟩ = ⟨(6 : State), p - 1, updateTape t p false⟩ := by
  simp [step, action_F]
  funext i
  by_cases h : i = p <;> simp [updateTape, h]

/-- Unconditional single step from `L` (11) to `M` (12) at `p - 1` clearing cell `p`. -/
theorem L_one_step_config (p : Int) (t : Int → Bool) :
    step ⟨(11 : State), p, t⟩ = ⟨(12 : State), p - 1, updateTape t p false⟩ := by
  simp [step, action_L]
  funext i
  by_cases h : i = p <;> simp [updateTape, h]

/-- Two-step turnaround `Q(0) → L → M` at head `p`: writes `true` at `p`, clears `p + 1`,
    and returns the head to `p` in state `M` (12). -/
theorem QL_two_step_config (p : Int) (t : Int → Bool) (hzero : t p = false) :
    step (step ⟨(16 : State), p, t⟩) = ⟨(12 : State), p, jfTape p t⟩ := by
  have hQ0 : step ⟨(16 : State), p, t⟩ = ⟨(11 : State), p + 1, updateTape t p true⟩ := by
    simp [step, hzero, action_Q_on_zero]
    funext i
    by_cases h : i = p <;> simp [updateTape, h]
  rw [hQ0, L_one_step_config]
  simp
  funext i
  by_cases hn : i = p + 1
  · subst hn
    simp [updateTape, jfTape]
  · by_cases hp : i = p
    · subst hp
      simp [updateTape, jfTape, hn]
    · simp [updateTape, jfTape, hn, hp]

/-- 1. Complete `I`-sweep across `k` ones followed by reading `0` at `p + k` and executing `J → F → G`:
    in `k + 3` steps, `(I, p, t)` reaches `(G, p + k + 1, jfTape (p + k + 1) (updateTape t (p + k) true))`. -/
theorem sweep_I_then_JF_to_G (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true)
    (hzero : t (p + ↑k) = false) :
    iterateStep (k + 3) ⟨(8 : State), p, t⟩ =
      ⟨(6 : State), p + ↑k + 1, jfTape (p + ↑k + 1) (updateTape t (p + ↑k) true)⟩ := by
  have hsplit : k + 3 = k + (1 + 2) := by omega
  rw [hsplit, iterateStep_add k (1 + 2), sweep_I_ones k p t hones]
  rw [iterateStep_add 1 2, iterateStep_one]
  have hI0 : step ⟨(8 : State), p + ↑k, t⟩ =
      ⟨(9 : State), p + ↑k + 1, updateTape t (p + ↑k) true⟩ := by
    simp [step, hzero, action_I_on_zero]
    funext i
    by_cases h : i = p + ↑k <;> simp [updateTape, h]
  rw [hI0, iterateStep_two, JF_two_step_config]

/-- 2. Complete `Q`-sweep across `k` ones followed by reading `0` at `p + k` and executing `L → M`:
    in `k + 2` steps, `(Q, p, t)` reaches `(M, p + k, jfTape (p + k) t)`. -/
theorem sweep_Q_then_L_to_M (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true)
    (hzero : t (p + ↑k) = false) :
    iterateStep (k + 2) ⟨(16 : State), p, t⟩ =
      ⟨(12 : State), p + ↑k, jfTape (p + ↑k) t⟩ := by
  rw [iterateStep_add k 2, sweep_Q_ones k p t hones, iterateStep_two]
  exact QL_two_step_config (p + ↑k) t hzero

/-- 3. Complete `P`-sweep across `k` ones followed by reading `0` at `p + k`:
    in `k + 1` steps, `(P, p, t)` reaches `(Q, p + k + 1, t)` with the tape unchanged. -/
theorem sweep_P_to_Q (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true)
    (hzero : t (p + ↑k) = false) :
    iterateStep (k + 1) ⟨(15 : State), p, t⟩ =
      ⟨(16 : State), p + ↑k + 1, t⟩ := by
  rw [iterateStep_add k 1, sweep_P_ones k p t hones, iterateStep_one]
  simp [step, hzero, action_P_on_zero]
  funext i
  by_cases h : i = p + ↑k <;> simp [h, hzero]

/-- 4a. Complete `G`-sweep across `k` ones followed by reading `0` at `p - k`:
    in `k + 1` steps, `(G, p, t)` reaches `(H, p - k - 1, updateTape t (p - k) true)`. -/
theorem sweep_G_to_H (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false) :
    iterateStep (k + 1) ⟨(6 : State), p, t⟩ =
      ⟨(7 : State), p - ↑k - 1, updateTape t (p - ↑k) true⟩ := by
  rw [iterateStep_add k 1, sweep_G_ones k p t hones, iterateStep_one]
  simp [step, hzero, action_G_on_zero]
  funext i
  by_cases h : i = p - ↑k <;> simp [updateTape, h]

/-- 4b. `G`-sweep turnaround when cell `p - k - 1` is `1` (`G →* H(1) → I`):
    in `k + 2` steps, `(G, p, t)` reaches `(I, p - k, updateTape (updateTape t (p - k) true) (p - k - 1) false)`. -/
theorem sweep_G_then_H1_to_I (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false)
    (hprev : t (p - ↑k - 1) = true) :
    iterateStep (k + 2) ⟨(6 : State), p, t⟩ =
      ⟨(8 : State), p - ↑k, updateTape (updateTape t (p - ↑k) true) (p - ↑k - 1) false⟩ := by
  have hsplit : k + 2 = (k + 1) + 1 := by omega
  rw [hsplit, iterateStep_add (k + 1) 1, sweep_G_to_H k p t hones hzero, iterateStep_one]
  have hne : p - ↑k - 1 ≠ p - ↑k := by omega
  have hread : updateTape t (p - ↑k) true (p - ↑k - 1) = true := by
    simp [updateTape, hne, hprev]
  simp [step, hread, action_H_on_one]
  funext i
  by_cases h : i = p - ↑k - 1 <;> simp [updateTape, h]

/-- 4c. `G`-sweep turnaround when cell `p - k - 1` is `0` (`G →* H(0) → A`):
    in `k + 2` steps, `(G, p, t)` reaches `(A, p - k, updateTape t (p - ↑k) true)`. -/
theorem sweep_G_then_H0_to_A (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false)
    (hprev : t (p - ↑k - 1) = false) :
    iterateStep (k + 2) ⟨(6 : State), p, t⟩ =
      ⟨(0 : State), p - ↑k, updateTape t (p - ↑k) true⟩ := by
  have hsplit : k + 2 = (k + 1) + 1 := by omega
  rw [hsplit, iterateStep_add (k + 1) 1, sweep_G_to_H k p t hones hzero, iterateStep_one]
  have hne : p - ↑k - 1 ≠ p - ↑k := by omega
  have hread : updateTape t (p - ↑k) true (p - ↑k - 1) = false := by
    simp [updateTape, hne, hprev]
  simp [step, hread, action_H_on_zero]
  funext i
  by_cases h : i = p - ↑k - 1
  · subst h
    simp [updateTape, hne, hprev]
  · simp [updateTape, h]

/-- 5a. Complete `B`-sweep across `k` ones followed by reading `0` at `p + k`:
    in `k + 1` steps, `(B, p, t)` reaches `(C, p + k - 1, updateTape t (p + k) true)`. -/
theorem sweep_B_to_C (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true)
    (hzero : t (p + ↑k) = false) :
    iterateStep (k + 1) ⟨(1 : State), p, t⟩ =
      ⟨(2 : State), p + ↑k - 1, updateTape t (p + ↑k) true⟩ := by
  rw [iterateStep_add k 1, sweep_B_ones k p t hones, iterateStep_one]
  simp [step, hzero, action_B_on_zero]
  funext i
  by_cases h : i = p + ↑k <;> simp [updateTape, h]

/-- 5b. `B`-sweep turnaround when cell `p + k - 1` is `1` (`B →* C(1) → D`):
    in `k + 2` steps, `(B, p, t)` reaches `(D, p + k - 2, updateTape (updateTape t (p + k) true) (p + k - 1) false)`. -/
theorem sweep_B_then_C1_to_D (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true)
    (hzero : t (p + ↑k) = false)
    (hprev : t (p + ↑k - 1) = true) :
    iterateStep (k + 2) ⟨(1 : State), p, t⟩ =
      ⟨(3 : State), p + ↑k - 2, updateTape (updateTape t (p + ↑k) true) (p + ↑k - 1) false⟩ := by
  have hsplit : k + 2 = (k + 1) + 1 := by omega
  rw [hsplit, iterateStep_add (k + 1) 1, sweep_B_to_C k p t hones hzero, iterateStep_one]
  have hne : p + ↑k - 1 ≠ p + ↑k := by omega
  have hread : updateTape t (p + ↑k) true (p + ↑k - 1) = true := by
    simp [updateTape, hne, hprev]
  simp [step, hread, action_C_on_one]
  constructor
  · omega
  · funext i
    by_cases h : i = p + ↑k - 1 <;> simp [updateTape, h]

/-- 5c. `B`-sweep turnaround when cell `p + k - 1` is `0` (`B →* C(0) → K`):
    in `k + 2` steps, `(B, p, t)` reaches `(K, p + k - 2, updateTape t (p + ↑k) true)`. -/
theorem sweep_B_then_C0_to_K (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true)
    (hzero : t (p + ↑k) = false)
    (hprev : t (p + ↑k - 1) = false) :
    iterateStep (k + 2) ⟨(1 : State), p, t⟩ =
      ⟨(10 : State), p + ↑k - 2, updateTape t (p + ↑k) true⟩ := by
  have hsplit : k + 2 = (k + 1) + 1 := by omega
  rw [hsplit, iterateStep_add (k + 1) 1, sweep_B_to_C k p t hones hzero, iterateStep_one]
  have hne : p + ↑k - 1 ≠ p + ↑k := by omega
  have hread : updateTape t (p + ↑k) true (p + ↑k - 1) = false := by
    simp [updateTape, hne, hprev]
  simp [step, hread, action_C_on_zero]
  constructor
  · omega
  · funext i
    by_cases h : i = p + ↑k - 1
    · subst h
      simp [updateTape, hne, hprev]
    · simp [updateTape, h]

/-- 6a. Complete `D`-sweep across `k` ones followed by reading `0` at `p - k`:
    in `k + 1` steps, `(D, p, t)` reaches `(E, p - k + 1, updateTape t (p - k) true)`. -/
theorem sweep_D_to_E (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false) :
    iterateStep (k + 1) ⟨(3 : State), p, t⟩ =
      ⟨(4 : State), p - ↑k + 1, updateTape t (p - ↑k) true⟩ := by
  rw [iterateStep_add k 1, sweep_D_ones k p t hones, iterateStep_one]
  simp [step, hzero, action_D_on_zero]
  funext i
  by_cases h : i = p - ↑k <;> simp [updateTape, h]

/-- 6b. `D`-sweep turnaround when cell `p - k + 1` is `1` (`D →* E(1) → B`):
    in `k + 2` steps, `(D, p, t)` reaches `(B, p - k + 2, updateTape (updateTape t (p - k) true) (p - k + 1) false)`. -/
theorem sweep_D_then_E1_to_B (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false)
    (hnext : t (p - ↑k + 1) = true) :
    iterateStep (k + 2) ⟨(3 : State), p, t⟩ =
      ⟨(1 : State), p - ↑k + 2, updateTape (updateTape t (p - ↑k) true) (p - ↑k + 1) false⟩ := by
  have hsplit : k + 2 = (k + 1) + 1 := by omega
  rw [hsplit, iterateStep_add (k + 1) 1, sweep_D_to_E k p t hones hzero, iterateStep_one]
  have hne : p - ↑k + 1 ≠ p - ↑k := by omega
  have hread : updateTape t (p - ↑k) true (p - ↑k + 1) = true := by
    simp [updateTape, hne, hnext]
  simp [step, hread, action_E_on_one]
  constructor
  · omega
  · funext i
    by_cases h : i = p - ↑k + 1 <;> simp [updateTape, h]

/-- 6c. `D`-sweep turnaround when cell `p - k + 1` is `0` (`D →* E(0) → F`):
    in `k + 2` steps, `(D, p, t)` reaches `(F, p - k + 2, updateTape t (p - k) true)`. -/
theorem sweep_D_then_E0_to_F (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false)
    (hnext : t (p - ↑k + 1) = false) :
    iterateStep (k + 2) ⟨(3 : State), p, t⟩ =
      ⟨(5 : State), p - ↑k + 2, updateTape t (p - ↑k) true⟩ := by
  have hsplit : k + 2 = (k + 1) + 1 := by omega
  rw [hsplit, iterateStep_add (k + 1) 1, sweep_D_to_E k p t hones hzero, iterateStep_one]
  have hne : p - ↑k + 1 ≠ p - ↑k := by omega
  have hread : updateTape t (p - ↑k) true (p - ↑k + 1) = false := by
    simp [updateTape, hne, hnext]
  simp [step, hread, action_E_on_zero]
  constructor
  · omega
  · funext i
    by_cases h : i = p - ↑k + 1
    · subst h
      simp [updateTape, hne, hnext]
    · simp [updateTape, h]

/-- 6d. Complete `D →* E(0) → F → G` turnaround when cell `p - k + 1` is `0`:
    in `k + 3` steps, `(D, p, t)` reaches `(G, p - k + 1, updateTape (updateTape t (p - k) true) (p - k + 2) false)`. -/
theorem sweep_D_then_E0_F_to_G (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false)
    (hnext : t (p - ↑k + 1) = false) :
    iterateStep (k + 3) ⟨(3 : State), p, t⟩ =
      ⟨(6 : State), p - ↑k + 1, updateTape (updateTape t (p - ↑k) true) (p - ↑k + 2) false⟩ := by
  have hsplit : k + 3 = (k + 2) + 1 := by omega
  rw [hsplit, iterateStep_add (k + 2) 1, sweep_D_then_E0_to_F k p t hones hzero hnext, iterateStep_one]
  rw [F_one_step_config]
  have hhead : p - ↑k + 2 - 1 = p - ↑k + 1 := by omega
  rw [hhead]

/-- 7. Complete `K`-sweep across `k` ones followed by reading `0` at `p - k`:
    in `k + 1` steps, `(K, p, t)` reaches `(A, p - k + 1, t)` with the tape unchanged. -/
theorem sweep_K_to_A (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false) :
    iterateStep (k + 1) ⟨(10 : State), p, t⟩ =
      ⟨(0 : State), p - ↑k + 1, t⟩ := by
  rw [iterateStep_add k 1, sweep_K_ones k p t hones, iterateStep_one]
  simp [step, hzero, action_K_on_zero]
  funext i
  by_cases h : i = p - ↑k <;> simp [h, hzero]

/-- 8. Complete `M`-sweep across `k` ones followed by reading `0` at `p - k`:
    in `k + 1` steps, `(M, p, t)` reaches `(N, p - k - 1, t)` with the tape unchanged. -/
theorem sweep_M_to_N (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false) :
    iterateStep (k + 1) ⟨(12 : State), p, t⟩ =
      ⟨(13 : State), p - ↑k - 1, t⟩ := by
  rw [iterateStep_add k 1, sweep_M_ones k p t hones, iterateStep_one]
  simp [step, hzero, action_M_on_zero]
  funext i
  by_cases h : i = p - ↑k <;> simp [h, hzero]

/-- 9. Complete `N`-sweep across `k` ones followed by reading `0` at `p - k`:
    in `k + 1` steps, `(N, p, t)` enters the beep state `O` (14) at head `p - k + 1`
    having written `true` at `p - k`. -/
theorem sweep_N_to_beep_O (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true)
    (hzero : t (p - ↑k) = false) :
    iterateStep (k + 1) ⟨(13 : State), p, t⟩ =
      ⟨(14 : State), p - ↑k + 1, updateTape t (p - ↑k) true⟩ := by
  rw [iterateStep_add k 1, sweep_N_ones k p t hones, iterateStep_one]
  simp [step, hzero, action_N_on_zero]
  funext i
  by_cases h : i = p - ↑k <;> simp [updateTape, h]

end BBB17
