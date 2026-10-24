import ArithmeticOrbitBridge

/-!
Complete multi-phase orbit reduction and kernel-checked proof of
`GlobalOrbitBridge` and `MachineEquivalentToCollatz` (`Quasihalts ↔ ¬ CollatzConjecture`):
1. Exact correspondence `run t = iterateStep t initial`.
2. Equivalence between register termination `RegReachesZero u` under the accelerated
   register map `collatzRegStep` and standard Collatz termination `ReachesOne (u + 1)`.
3. Beep-free execution (`noBeepInSteps`) across all positive-register macro-phases
   (`evenPhase` and `oddPhase`), derived from the 4-step state-bound property of states `≤ 10`.
4. Multi-phase machine execution from `canonConfig j u v` to `canonConfig j 0 v'`
   whenever `RegReachesZero u` holds, and infinite beep-free execution whenever `¬ RegReachesZero u`.
5. Prefix enumeration `GoodPrefix J → ∃ t ≥ J, ∃ v, run t = canonConfig J J v`.
6. Unconditional proof of both directions of `MachineEquivalentToCollatz`:
   - `quasihalts_implies_not_collatz : Quasihalts → ¬ CollatzConjecture`
   - `not_collatz_implies_quasihalts : ¬ CollatzConjecture → Quasihalts`
   - `machineEquivalentToCollatz_holds : MachineEquivalentToCollatz`

No axioms or `sorry` placeholders are used.
-/
namespace BBB17

/-! ### 1. Relating `run` and `iterateStep` -/

theorem iterateStep_step_comm (n : Nat) (c : Config) :
    iterateStep n (step c) = step (iterateStep n c) := by
  induction n generalizing c with
  | zero => rfl
  | succ n ih =>
    rw [iterateStep_succ, ih, ← iterateStep_succ]

theorem run_eq_iterateStep (t : Nat) :
    run t = iterateStep t initial := by
  induction t with
  | zero => rfl
  | succ t ih =>
    unfold run
    rw [ih, iterateStep_succ, iterateStep_step_comm]

theorem beepsAt_iff_iterateStep (t : Nat) :
    beepsAt t ↔ exitBeep (iterateStep t initial) := by
  unfold beepsAt
  rw [run_eq_iterateStep]

/-! ### 2. Beep-Free Execution (`noBeepInSteps`) and State-Bound Lemmas -/

/-- No configuration visited during the first `k` steps from `c` is in beep state `O` (14). -/
def noBeepInSteps (k : Nat) (c : Config) : Prop :=
  ∀ r : Nat, r < k → ¬ exitBeep (iterateStep r c)

theorem noBeepInSteps_zero (c : Config) : noBeepInSteps 0 c := by
  intro r hr
  omega

theorem noBeepInSteps_add (m n : Nat) (c : Config)
    (hm : noBeepInSteps m c) (hn : noBeepInSteps n (iterateStep m c)) :
    noBeepInSteps (m + n) c := by
  intro r hr
  by_cases hrm : r < m
  · exact hm r hrm
  · have hsub : r = m + (r - m) := by omega
    rw [hsub, iterateStep_add]
    exact hn (r - m) (by omega)

/-- Finite-state transition bounds: from any state `≤ 10`, one step reaches `≤ 11`,
    two steps reach `≤ 12`, and three steps reach `≤ 13` (all strictly below beep state `14`). -/
theorem action_next_le_11 (q : State) (b : Bool) (hq : q.val ≤ 10) :
    (action q b).next.val ≤ 11 := by
  revert q b
  decide

theorem action_next_le_12 (q : State) (b : Bool) (hq : q.val ≤ 11) :
    (action q b).next.val ≤ 12 := by
  revert q b
  decide

theorem action_next_le_13 (q : State) (b : Bool) (hq : q.val ≤ 12) :
    (action q b).next.val ≤ 13 := by
  revert q b
  decide

theorem step_state_le_11 (c : Config) (hc : c.state.val ≤ 10) :
    (step c).state.val ≤ 11 :=
  action_next_le_11 c.state (c.tape c.head) hc

theorem step_state_le_12 (c : Config) (hc : c.state.val ≤ 11) :
    (step c).state.val ≤ 12 :=
  action_next_le_12 c.state (c.tape c.head) hc

theorem step_state_le_13 (c : Config) (hc : c.state.val ≤ 12) :
    (step c).state.val ≤ 13 :=
  action_next_le_13 c.state (c.tape c.head) hc

theorem not_exitBeep_of_le_13 (c : Config) (hc : c.state.val ≤ 13) :
    ¬ exitBeep c := by
  unfold exitBeep
  intro h
  have hval : c.state.val = 14 := congrArg Fin.val h
  omega

/-- Any configuration with `c.state.val ≤ 10` cannot visit beep state `O` (14)
    within `d ≤ 4` steps, regardless of tape contents or head position. -/
theorem noBeepInSteps_le_four (c : Config) (hc : c.state.val ≤ 10)
    (d : Nat) (hd : d ≤ 4) : noBeepInSteps d c := by
  intro r hr
  have h1 : (step c).state.val ≤ 11 := step_state_le_11 c hc
  have h2 : (step (step c)).state.val ≤ 12 := step_state_le_12 (step c) h1
  have h3 : (step (step (step c))).state.val ≤ 13 := step_state_le_13 (step (step c)) h2
  rcases (by omega : r = 0 ∨ r = 1 ∨ r = 2 ∨ r = 3) with rfl | rfl | rfl | rfl
  · exact not_exitBeep_of_le_13 c (by omega)
  · exact not_exitBeep_of_le_13 (step c) (by omega)
  · exact not_exitBeep_of_le_13 (step (step c)) (by omega)
  · exact not_exitBeep_of_le_13 (step (step (step c))) h3

/-- Generic beep-free theorem for any right-sweep of `k` ones followed by `d ≤ 4` turnaround steps
    starting from a state `q` with `q.val ≤ 10`. -/
theorem noBeepInSteps_right_sweep_plus (q : State) (hq : action q true = ⟨true, true, q⟩)
    (hle : q.val ≤ 10) (k d : Nat) (hd : d ≤ 4) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    noBeepInSteps (k + d) ⟨q, p, t⟩ := by
  apply noBeepInSteps_add k d
  · intro r hr
    have hsub : ∀ j : Nat, j < r → t (p + ↑j) = true := fun j hj => hones j (by omega)
    rw [right_sweep_run q hq r p t hsub]
    exact not_exitBeep_of_le_13 _ (by dsimp; omega)
  · rw [right_sweep_run q hq k p t hones]
    exact noBeepInSteps_le_four _ hle d hd

/-- Generic beep-free theorem for any left-sweep of `k` ones followed by `d ≤ 4` turnaround steps
    starting from a state `q` with `q.val ≤ 10`. -/
theorem noBeepInSteps_left_sweep_plus (q : State) (hq : action q true = ⟨true, false, q⟩)
    (hle : q.val ≤ 10) (k d : Nat) (hd : d ≤ 4) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    noBeepInSteps (k + d) ⟨q, p, t⟩ := by
  apply noBeepInSteps_add k d
  · intro r hr
    have hsub : ∀ j : Nat, j < r → t (p - ↑j) = true := fun j hj => hones j (by omega)
    rw [left_sweep_run q hq r p t hsub]
    exact not_exitBeep_of_le_13 _ (by dsimp; omega)
  · rw [left_sweep_run q hq k p t hones]
    exact noBeepInSteps_le_four _ hle d hd

/-- Exact count of visits to beep state `O` (14) during `k` steps starting from `c`. -/
def beepsInSteps : Nat → Config → Nat
  | 0, _ => 0
  | k + 1, c => (if c.state = (14 : State) then 1 else 0) + beepsInSteps k (step c)

@[simp] theorem beepsInSteps_zero (c : Config) : beepsInSteps 0 c = 0 := rfl

@[simp] theorem beepsInSteps_succ (k : Nat) (c : Config) :
    beepsInSteps (k + 1) c =
      (if c.state = (14 : State) then 1 else 0) + beepsInSteps k (step c) := rfl

theorem beepsInSteps_add (m n : Nat) (c : Config) :
    beepsInSteps (m + n) c = beepsInSteps m c + beepsInSteps n (iterateStep m c) := by
  induction m generalizing c with
  | zero => simp
  | succ m ih =>
    rw [Nat.succ_add, beepsInSteps_succ, beepsInSteps_succ, ih (step c), iterateStep_succ, Nat.add_assoc]

theorem beepsInSteps_eq_zero_of_noBeep (k : Nat) (c : Config) (h : noBeepInSteps k c) :
    beepsInSteps k c = 0 := by
  induction k generalizing c with
  | zero => rfl
  | succ k ih =>
    have h0 : c.state ≠ (14 : State) := h 0 (by omega)
    have htail : noBeepInSteps k (step c) := by
      intro r hr
      have hr1 : r + 1 < k + 1 := by omega
      simpa [iterateStep_succ] using h (r + 1) hr1
    rw [beepsInSteps_succ, if_neg h0, ih (step c) htail]

theorem noBeepInSteps_right_sweep_exact (q : State) (hq : action q true = ⟨true, true, q⟩)
    (hne14 : q ≠ (14 : State)) (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    noBeepInSteps k ⟨q, p, t⟩ := by
  intro r hr
  have hsub : ∀ j : Nat, j < r → t (p + ↑j) = true := fun j hj => hones j (by omega)
  rw [right_sweep_run q hq r p t hsub]
  exact hne14

theorem noBeepInSteps_left_sweep_exact (q : State) (hq : action q true = ⟨true, false, q⟩)
    (hne14 : q ≠ (14 : State)) (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    noBeepInSteps k ⟨q, p, t⟩ := by
  intro r hr
  have hsub : ∀ j : Nat, j < r → t (p - ↑j) = true := fun j hj => hones j (by omega)
  rw [left_sweep_run q hq r p t hsub]
  exact hne14

/-! ### 3. Beep-Free Refinement of `evenPhase` and `oddPhase` Loops -/

theorem halving_loop_base_noBeep (j s v : Nat) :
    noBeepInSteps (s + 3) ⟨(1 : State), (s : Int) + 1, halvingTape j s 0 v⟩ := by
  have hsplit : s + 3 = (0 + 2) + (s + 1) := by omega
  rw [hsplit]
  apply noBeepInSteps_add (0 + 2) (s + 1)
  · exact noBeepInSteps_le_four _ (by dsimp; decide) 2 (by omega)
  · have hones0 : ∀ r : Nat, r < 0 → halvingTape j s 0 v (((s : Int) + 1) + ↑r) = true := by
      intro r hr; omega
    have hzero : halvingTape j s 0 v (((s : Int) + 1) + ↑(0 : Nat)) = false := by
      rw [Bool_eq_false_iff, halvingTape_true_iff]; omega
    have hprev : halvingTape j s 0 v (((s : Int) + 1) + ↑(0 : Nat) - 1) = false := by
      rw [Bool_eq_false_iff, halvingTape_true_iff]; omega
    have hBCK := sweep_B_then_C0_to_K 0 ((s : Int) + 1) (halvingTape j s 0 v) hones0 hzero hprev
    have hheadK : (s : Int) + 1 + ↑(0 : Nat) - 2 = (s : Int) - 1 := by omega
    have htapeK : updateTape (halvingTape j s 0 v) ((s : Int) + 1 + ↑(0 : Nat)) true =
        canonTape j s (v + 1) := by
      funext i; rw [Bool_eq_iff]
      simp only [updateTape_true_iff, halvingTape_true_iff, canonTape_true_iff]; omega
    rw [hheadK, htapeK] at hBCK
    rw [hBCK]
    have hKones : ∀ r : Nat, r < s → canonTape j s (v + 1) (((s : Int) - 1) - ↑r) = true := by
      intro r hr; rw [canonTape_true_iff]; omega
    exact noBeepInSteps_left_sweep_plus (10 : State) action_K_on_one (by decide) s 1 (by omega)
      ((s : Int) - 1) (canonTape j s (v + 1)) hKones

theorem halving_loop_pass_noBeep (j s m v : Nat) :
    noBeepInSteps (4 * m + 7) ⟨(1 : State), (s : Int) + 1, halvingTape j s (m + 1) v⟩ := by
  have hsplit : 4 * m + 7 = ((2 * m + 2) + 2) + ((2 * m + 1) + 2) := by omega
  rw [hsplit]
  have hBones : ∀ r : Nat, r < 2 * m + 2 →
      halvingTape j s (m + 1) v (((s : Int) + 1) + ↑r) = true := by
    intro r hr; rw [halvingTape_true_iff]; omega
  have hBzero : halvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 2)) = false := by
    rw [Bool_eq_false_iff, halvingTape_true_iff]; omega
  have hBprev : halvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 2) - 1) = true := by
    rw [halvingTape_true_iff]; omega
  have hBCD := sweep_B_then_C1_to_D (2 * m + 2) ((s : Int) + 1)
    (halvingTape j s (m + 1) v) hBones hBzero hBprev
  let midTape : Int → Bool := updateTape (canonTape j (s + 2 * m + 2) (v + 1)) (s : Int) false
  have hheadD : (s : Int) + 1 + ↑(2 * m + 2) - 2 = (s : Int) + 2 * ↑m + 1 := by omega
  have htapeD : updateTape (updateTape (halvingTape j s (m + 1) v)
      (((s : Int) + 1) + ↑(2 * m + 2)) true) (((s : Int) + 1) + ↑(2 * m + 2) - 1) false = midTape := by
    funext i; rw [Bool_eq_iff]
    simp only [midTape, updateTape_false_iff, updateTape_true_iff, halvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadD, htapeD] at hBCD
  apply noBeepInSteps_add ((2 * m + 2) + 2) ((2 * m + 1) + 2)
  · exact noBeepInSteps_right_sweep_plus (1 : State) action_B_on_one (by decide)
      (2 * m + 2) 2 (by omega) ((s : Int) + 1) (halvingTape j s (m + 1) v) hBones
  · rw [hBCD]
    have hDones : ∀ r : Nat, r < 2 * m + 1 →
        midTape (((s : Int) + 2 * ↑m + 1) - ↑r) = true := by
      intro r hr; simp only [midTape, updateTape_false_iff, canonTape_true_iff]; omega
    exact noBeepInSteps_left_sweep_plus (3 : State) action_D_on_one (by decide)
      (2 * m + 1) 2 (by omega) ((s : Int) + 2 * ↑m + 1) midTape hDones

theorem halving_loop_run_noBeep (m j s v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      noBeepInSteps steps ⟨(1 : State), (s : Int) + 1, halvingTape j s m v⟩ ∧
      iterateStep steps ⟨(1 : State), (s : Int) + 1, halvingTape j s m v⟩ =
        canonConfig j (s + m) (v + m + 1) := by
  induction m generalizing s v with
  | zero =>
    refine ⟨s + 3, by omega, halving_loop_base_noBeep j s v, ?_⟩
    simpa using halving_loop_base j s v
  | succ m ih =>
    rcases ih (s + 1) (v + 1) with ⟨steps, hpos, hnobeep, hrun⟩
    refine ⟨(4 * m + 7) + steps, by omega, ?_, ?_⟩
    · apply noBeepInSteps_add (4 * m + 7) steps
      · exact halving_loop_pass_noBeep j s m v
      · rw [halving_loop_pass j s m v]
        exact hnobeep
    · rw [iterateStep_add (4 * m + 7) steps, halving_loop_pass j s m v, hrun]
      have hs : s + 1 + m = s + (m + 1) := by omega
      have hv : v + 1 + m + 1 = v + (m + 1) + 1 := by omega
      rw [hs, hv]

theorem evenPhase_sim_noBeep (j k v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      noBeepInSteps steps (canonConfig j (2 * k + 1) v) ∧
      iterateStep steps (canonConfig j (2 * k + 1) v) =
        canonConfig j k (v + k + 1) := by
  rcases halving_loop_run_noBeep k j 0 v with ⟨steps, hpos, hnobeep, hrun⟩
  refine ⟨1 + steps, by omega, ?_, ?_⟩
  · apply noBeepInSteps_add 1 steps
    · exact noBeepInSteps_le_four _ (by dsimp [canonConfig]; decide) 1 (by omega)
    · rw [iterateStep_one, evenPhase_init_step j k v]
      exact hnobeep
  · rw [iterateStep_add 1 steps, iterateStep_one, evenPhase_init_step j k v, hrun]
    simp

theorem oddHalving_loop_pass_noBeep (j s m v : Nat) :
    noBeepInSteps (4 * m + 9) ⟨(1 : State), (s : Int) + 1, oddHalvingTape j s (m + 1) v⟩ := by
  have hsplit : 4 * m + 9 = ((2 * m + 3) + 2) + ((2 * m + 2) + 2) := by omega
  rw [hsplit]
  have hBones : ∀ r : Nat, r < 2 * m + 3 →
      oddHalvingTape j s (m + 1) v (((s : Int) + 1) + ↑r) = true := by
    intro r hr; rw [oddHalvingTape_true_iff]; omega
  have hBzero : oddHalvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 3)) = false := by
    rw [Bool_eq_false_iff, oddHalvingTape_true_iff]; omega
  have hBprev : oddHalvingTape j s (m + 1) v (((s : Int) + 1) + ↑(2 * m + 3) - 1) = true := by
    rw [oddHalvingTape_true_iff]; omega
  have hBCD := sweep_B_then_C1_to_D (2 * m + 3) ((s : Int) + 1)
    (oddHalvingTape j s (m + 1) v) hBones hBzero hBprev
  let midTape : Int → Bool := updateTape (canonTape j (s + 2 * m + 3) (v + 1)) (s : Int) false
  have hheadD : (s : Int) + 1 + ↑(2 * m + 3) - 2 = (s : Int) + 2 * ↑m + 2 := by omega
  have htapeD : updateTape (updateTape (oddHalvingTape j s (m + 1) v)
      (((s : Int) + 1) + ↑(2 * m + 3)) true) (((s : Int) + 1) + ↑(2 * m + 3) - 1) false = midTape := by
    funext i; rw [Bool_eq_iff]
    simp only [midTape, updateTape_false_iff, updateTape_true_iff, oddHalvingTape_true_iff, canonTape_true_iff]
    omega
  rw [hheadD, htapeD] at hBCD
  apply noBeepInSteps_add ((2 * m + 3) + 2) ((2 * m + 2) + 2)
  · exact noBeepInSteps_right_sweep_plus (1 : State) action_B_on_one (by decide)
      (2 * m + 3) 2 (by omega) ((s : Int) + 1) (oddHalvingTape j s (m + 1) v) hBones
  · rw [hBCD]
    have hDones : ∀ r : Nat, r < 2 * m + 2 →
        midTape (((s : Int) + 2 * ↑m + 2) - ↑r) = true := by
      intro r hr; simp only [midTape, updateTape_false_iff, canonTape_true_iff]; omega
    exact noBeepInSteps_left_sweep_plus (3 : State) action_D_on_one (by decide)
      (2 * m + 2) 2 (by omega) ((s : Int) + 2 * ↑m + 2) midTape hDones

theorem oddHalving_loop_base_noBeep (j s v : Nat) :
    noBeepInSteps 6 ⟨(1 : State), (s : Int) + 1, oddHalvingTape j s 0 v⟩ := by
  have hsplit : (6 : Nat) = (1 + 2) + 3 := by omega
  rw [hsplit]
  have hBones : ∀ r : Nat, r < 1 → oddHalvingTape j s 0 v (((s : Int) + 1) + ↑r) = true := by
    intro r hr; rw [oddHalvingTape_true_iff]; omega
  have hBzero : oddHalvingTape j s 0 v (((s : Int) + 1) + ↑(1 : Nat)) = false := by
    rw [Bool_eq_false_iff, oddHalvingTape_true_iff]; omega
  have hBprev : oddHalvingTape j s 0 v (((s : Int) + 1) + ↑(1 : Nat) - 1) = true := by
    rw [oddHalvingTape_true_iff]; omega
  have hBCD := sweep_B_then_C1_to_D 1 ((s : Int) + 1) (oddHalvingTape j s 0 v) hBones hBzero hBprev
  apply noBeepInSteps_add (1 + 2) 3
  · exact noBeepInSteps_right_sweep_plus (1 : State) action_B_on_one (by decide)
      1 2 (by omega) ((s : Int) + 1) (oddHalvingTape j s 0 v) hBones
  · rw [hBCD]
    exact noBeepInSteps_le_four _ (by dsimp; decide) 3 (by omega)

theorem oddHalving_loop_run_noBeep (m j s v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      noBeepInSteps steps ⟨(1 : State), (s : Int) + 1, oddHalvingTape j s m v⟩ ∧
      iterateStep steps ⟨(1 : State), (s : Int) + 1, oddHalvingTape j s m v⟩ =
        ⟨(6 : State), ((s + m + 1 : Nat) : Int) + 3 * ↑(0 : Nat),
          triplingTape j (s + m + 1) 0 (s + 2 * m + 2 + v)⟩ := by
  induction m generalizing s v with
  | zero =>
    refine ⟨6, by omega, oddHalving_loop_base_noBeep j s v, ?_⟩
    simpa using oddHalving_loop_base j s v
  | succ m ih =>
    rcases ih (s + 1) (v + 1) with ⟨steps, hpos, hnobeep, hrun⟩
    refine ⟨(4 * m + 9) + steps, by omega, ?_, ?_⟩
    · apply noBeepInSteps_add (4 * m + 9) steps
      · exact oddHalving_loop_pass_noBeep j s m v
      · rw [oddHalving_loop_pass j s m v]
        exact hnobeep
    · rw [iterateStep_add (4 * m + 9) steps, oddHalving_loop_pass j s m v, hrun]
      have hs : s + 1 + m + 1 = s + (m + 1) + 1 := by omega
      have hR : s + 1 + 2 * m + 2 + (v + 1) = s + 2 * (m + 1) + 2 + v := by omega
      rw [hs, hR]

theorem tripling_loop_pass_noBeep (j a b R : Nat) :
    noBeepInSteps (6 * b + 6)
      ⟨(6 : State), ((a + 1 : Nat) : Int) + 3 * (b : Int), triplingTape j (a + 1) b R⟩ := by
  have hsplit : 6 * b + 6 = (3 * b + 2) + ((3 * b + 1) + 3) := by omega
  rw [hsplit]
  have hGones : ∀ r : Nat, r < 3 * b →
      triplingTape j (a + 1) b R ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑r) = true := by
    intro r hr; rw [triplingTape_true_iff]; omega
  have hGzero : triplingTape j (a + 1) b R
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b)) = false := by
    rw [Bool_eq_false_iff, triplingTape_true_iff]; omega
  have hGprev : triplingTape j (a + 1) b R
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b) - 1) = true := by
    rw [triplingTape_true_iff]; omega
  have hGHI := sweep_G_then_H1_to_I (3 * b) (((a + 1 : Nat) : Int) + 3 * (b : Int))
    (triplingTape j (a + 1) b R) hGones hGzero hGprev
  let midITape : Int → Bool :=
    updateTape (updateTape (triplingTape j (a + 1) b R) ((a : Int) + 1) true) (a : Int) false
  have hheadI : ((a + 1 : Nat) : Int) + 3 * (b : Int) - ↑(3 * b) = (a : Int) + 1 := by omega
  have htapeI : updateTape (updateTape (triplingTape j (a + 1) b R)
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b)) true)
      ((((a + 1 : Nat) : Int) + 3 * (b : Int)) - ↑(3 * b) - 1) false = midITape := by
    funext i; rw [Bool_eq_iff]
    simp only [midITape, updateTape_false_iff, updateTape_true_iff, triplingTape_true_iff]
    omega
  rw [htapeI, hheadI] at hGHI
  apply noBeepInSteps_add (3 * b + 2) ((3 * b + 1) + 3)
  · exact noBeepInSteps_left_sweep_plus (6 : State) action_G_on_one (by decide)
      (3 * b) 2 (by omega) (((a + 1 : Nat) : Int) + 3 * (b : Int)) (triplingTape j (a + 1) b R) hGones
  · rw [hGHI]
    have hIones : ∀ r : Nat, r < 3 * b + 1 → midITape (((a : Int) + 1) + ↑r) = true := by
      intro r hr
      simp only [midITape, updateTape_false_iff, updateTape_true_iff, triplingTape_true_iff]
      omega
    exact noBeepInSteps_right_sweep_plus (8 : State) action_I_on_one (by decide)
      (3 * b + 1) 3 (by omega) ((a : Int) + 1) midITape hIones

theorem tripling_loop_base_noBeep (j b R : Nat) :
    noBeepInSteps (3 * b + 2)
      ⟨(6 : State), ((0 : Nat) : Int) + 3 * (b : Int), triplingTape j 0 b R⟩ := by
  have hGones : ∀ r : Nat, r < 3 * b →
      triplingTape j 0 b R ((((0 : Nat) : Int) + 3 * (b : Int)) - ↑r) = true := by
    intro r hr; rw [triplingTape_true_iff]; omega
  exact noBeepInSteps_left_sweep_plus (6 : State) action_G_on_one (by decide)
    (3 * b) 2 (by omega) (((0 : Nat) : Int) + 3 * (b : Int)) (triplingTape j 0 b R) hGones

theorem tripling_loop_run_noBeep (a j b R : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      noBeepInSteps steps ⟨(6 : State), (a : Int) + 3 * (b : Int), triplingTape j a b R⟩ ∧
      iterateStep steps ⟨(6 : State), (a : Int) + 3 * (b : Int), triplingTape j a b R⟩ =
        ⟨(0 : State), 0, updateTape (triplingTape j 0 (a + b) R) 0 true⟩ := by
  induction a generalizing b with
  | zero =>
    refine ⟨3 * b + 2, by omega, tripling_loop_base_noBeep j b R, ?_⟩
    simpa using tripling_loop_base j b R
  | succ a ih =>
    rcases ih (b + 1) with ⟨steps, hpos, hnobeep, hrun⟩
    refine ⟨(6 * b + 6) + steps, by omega, ?_, ?_⟩
    · apply noBeepInSteps_add (6 * b + 6) steps
      · exact tripling_loop_pass_noBeep j a b R
      · rw [tripling_loop_pass j a b R]
        exact hnobeep
    · rw [iterateStep_add (6 * b + 6) steps, tripling_loop_pass j a b R, hrun]
      have hab : a + (b + 1) = a + 1 + b := by omega
      rw [hab]

theorem oddPhase_sim_noBeep (j k v : Nat) (hk : k > 0) :
    ∃ steps : Nat, steps > 0 ∧
      noBeepInSteps steps (canonConfig j (2 * k) v) ∧
      iterateStep steps (canonConfig j (2 * k) v) =
        canonConfig j (3 * k + 1) (v - (k + 1)) := by
  obtain ⟨m, rfl⟩ : ∃ m : Nat, k = m + 1 := ⟨k - 1, by omega⟩
  rcases oddHalving_loop_run_noBeep m j 0 v with ⟨s1, hs1, hnb1, hrun1⟩
  rcases tripling_loop_run_noBeep (m + 1) j 0 (2 * (m + 1) + v) with ⟨s2, hs2, hnb2, hrun2⟩
  refine ⟨1 + (s1 + s2), by omega, ?_, ?_⟩
  · apply noBeepInSteps_add 1 (s1 + s2)
    · exact noBeepInSteps_le_four _ (by dsimp [canonConfig]; decide) 1 (by omega)
    · rw [iterateStep_one, oddPhase_init_step j m v]
      apply noBeepInSteps_add s1 s2 _ hnb1
      rw [hrun1]
      have h0m : 0 + m + 1 = m + 1 := by omega
      have h0R : 0 + 2 * m + 2 + v = 2 * (m + 1) + v := by omega
      rw [h0m, h0R]
      exact hnb2
  · rw [iterateStep_add 1 (s1 + s2), iterateStep_one, oddPhase_init_step j m v]
    rw [iterateStep_add s1 s2, hrun1]
    have h0m : 0 + m + 1 = m + 1 := by omega
    have h0R : 0 + 2 * m + 2 + v = 2 * (m + 1) + v := by omega
    rw [h0m, h0R, hrun2]
    simp only [canonConfig]
    congr 1
    funext i; rw [Bool_eq_iff]
    simp only [updateTape_true_iff, triplingTape_true_iff, canonTape_true_iff]
    omega

/-! ### 4. Register Collatz Map and Equivalence with `ReachesOne (u + 1)` -/

/-- One macro-phase update on a positive active unary register `u`. -/
def collatzRegStep (u : Nat) : Nat :=
  if u % 2 = 1 then u / 2 else 3 * (u / 2) + 1

/-- `n`-fold iteration of `collatzRegStep`. -/
def iterateRegStep (u : Nat) : Nat → Nat
  | 0 => u
  | n + 1 => iterateRegStep (collatzRegStep u) n

@[simp] theorem iterateRegStep_zero (u : Nat) :
    iterateRegStep u 0 = u := rfl

@[simp] theorem iterateRegStep_succ (u n : Nat) :
    iterateRegStep u (n + 1) = iterateRegStep (collatzRegStep u) n := rfl

/-- The unary register `u` reaches `0` in finitely many macro-phases. -/
def RegReachesZero (u : Nat) : Prop :=
  ∃ n : Nat, iterateRegStep u n = 0

/-- Shift law for `iterateCollatz`: `iterateCollatz m (k + 1) = iterateCollatz (collatz m) k`. -/
theorem iterateCollatz_succ_left (m k : Nat) :
    iterateCollatz m (k + 1) = iterateCollatz (collatz m) k := by
  induction k generalizing m with
  | zero => rfl
  | succ k ih =>
    unfold iterateCollatz
    rw [ih m]

/-- For odd `u` (`m = u + 1` even), one `collatzRegStep` equals one `collatz` step on `u + 1`. -/
theorem collatzRegStep_odd (u : Nat) (hodd : u % 2 = 1) :
    collatz (u + 1) = collatzRegStep u + 1 := by
  have heven : (u + 1) % 2 = 0 := by omega
  dsimp [collatz, collatzRegStep]
  rw [if_pos heven, if_pos hodd]
  omega

/-- For even `u` (`m = u + 1` odd), one `collatzRegStep` equals two `collatz` steps on `u + 1`. -/
theorem collatzRegStep_even (u : Nat) (heven : ¬(u % 2 = 1)) :
    collatz (collatz (u + 1)) = collatzRegStep u + 1 := by
  have hodd1 : ¬((u + 1) % 2 = 0) := by omega
  have heven2 : (3 * (u + 1) + 1) % 2 = 0 := by omega
  dsimp [collatz, collatzRegStep]
  rw [if_neg hodd1, if_pos heven2, if_neg heven]
  omega

/-- Every `n` steps of `iterateRegStep u` correspond to some `k` steps of `iterateCollatz (u + 1)`. -/
theorem iterateRegStep_to_iterateCollatz (n u : Nat) :
    ∃ k : Nat, iterateCollatz (u + 1) k = iterateRegStep u n + 1 := by
  induction n generalizing u with
  | zero =>
    exact ⟨0, rfl⟩
  | succ n ih =>
    rcases ih (collatzRegStep u) with ⟨k, hk⟩
    by_cases hodd : u % 2 = 1
    · refine ⟨1 + k, ?_⟩
      rw [Nat.add_comm 1 k, iterateCollatz_succ_left, collatzRegStep_odd u hodd, hk]
      rfl
    · refine ⟨2 + k, ?_⟩
      have h2 : 2 + k = k + 1 + 1 := by omega
      rw [h2, iterateCollatz_succ_left, iterateCollatz_succ_left, collatzRegStep_even u hodd, hk]
      rfl

/-- Forward equivalence: if `u` reaches `0` under `collatzRegStep`, then `u + 1` reaches `1`
    under `collatz`. -/
theorem reachesOne_of_regReachesZero (u : Nat) (h : RegReachesZero u) :
    ReachesOne (u + 1) := by
  rcases h with ⟨n, hn⟩
  rcases iterateRegStep_to_iterateCollatz n u with ⟨k, hk⟩
  refine ⟨k, ?_⟩
  rw [hk, hn]

/-- Backward equivalence helper by bounded induction on the Collatz step bound `B`. -/
theorem regReachesZero_of_iterateCollatz_bounded (B : Nat) :
    ∀ k : Nat, k ≤ B → ∀ u : Nat, iterateCollatz (u + 1) k = 1 → RegReachesZero u := by
  induction B with
  | zero =>
    intro k hkB u hk
    have hk0 : k = 0 := by omega
    subst hk0
    unfold iterateCollatz at hk
    have hu0 : u = 0 := by omega
    subst hu0
    exact ⟨0, rfl⟩
  | succ B ih =>
    intro k hkB u hk
    by_cases hu0 : u = 0
    · subst hu0
      exact ⟨0, rfl⟩
    · cases k with
      | zero =>
        unfold iterateCollatz at hk
        omega
      | succ k1 =>
        by_cases hodd : u % 2 = 1
        · rw [iterateCollatz_succ_left, collatzRegStep_odd u hodd] at hk
          rcases ih k1 (by omega) (collatzRegStep u) hk with ⟨n, hn⟩
          exact ⟨n + 1, hn⟩
        · cases k1 with
          | zero =>
            have hodd1 : ¬((u + 1) % 2 = 0) := by omega
            change collatz (u + 1) = 1 at hk
            unfold collatz at hk
            rw [if_neg hodd1] at hk
            omega
          | succ k2 =>
            rw [iterateCollatz_succ_left, iterateCollatz_succ_left, collatzRegStep_even u hodd] at hk
            rcases ih k2 (by omega) (collatzRegStep u) hk with ⟨n, hn⟩
            exact ⟨n + 1, hn⟩

theorem regReachesZero_of_iterateCollatz (k u : Nat)
    (hk : iterateCollatz (u + 1) k = 1) : RegReachesZero u :=
  regReachesZero_of_iterateCollatz_bounded k k (Nat.le_refl k) u hk

/-- Exact equivalence between `RegReachesZero u` and `ReachesOne (u + 1)`. -/
theorem regReachesZero_iff_reachesOne (u : Nat) :
    RegReachesZero u ↔ ReachesOne (u + 1) := by
  constructor
  · exact reachesOne_of_regReachesZero u
  · intro h
    rcases h with ⟨k, hk⟩
    exact regReachesZero_of_iterateCollatz k u hk

/-! ### 5. Unified Positive-Register Step with Beep-Free Guarantee -/

/-- One macro-phase from `canonConfig j u v` with `u > 0` takes `steps > 0` steps,
    emits zero beeps (`noBeepInSteps steps`), and reaches `canonConfig j (collatzRegStep u) v'`. -/
theorem posReg_machine_phase_noBeep (j u v : Nat) (hu : u > 0) :
    ∃ steps v' : Nat, steps > 0 ∧
      noBeepInSteps steps (canonConfig j u v) ∧
      iterateStep steps (canonConfig j u v) = canonConfig j (collatzRegStep u) v' := by
  rcases canon_register_trichotomy u with rfl | ⟨k, rfl⟩ | ⟨k, hk, rfl⟩
  · omega
  · rcases evenPhase_sim_noBeep j k v with ⟨steps, hpos, hnobeep, hrun⟩
    have hmod : (2 * k + 1) % 2 = 1 := by omega
    have hdiv : (2 * k + 1) / 2 = k := by omega
    refine ⟨steps, v + k + 1, hpos, hnobeep, ?_⟩
    simpa [collatzRegStep, hmod, hdiv] using hrun
  · rcases oddPhase_sim_noBeep j k v hk with ⟨steps, hpos, hnobeep, hrun⟩
    have hmod : ¬((2 * k) % 2 = 1) := by omega
    have hdiv : (2 * k) / 2 = k := by omega
    refine ⟨steps, v - (k + 1), hpos, hnobeep, ?_⟩
    simpa [collatzRegStep, hmod, hdiv] using hrun

/-- Multi-phase induction along a terminating register orbit: if `iterateRegStep u n = 0`,
    then for any `j, v`, `canonConfig j u v` reaches `canonConfig j 0 v'` in finitely many steps. -/
theorem iterateRegStep_reaches_canonZero (n : Nat) :
    ∀ j u v : Nat, iterateRegStep u n = 0 →
      ∃ steps v' : Nat, iterateStep steps (canonConfig j u v) = canonConfig j 0 v' := by
  induction n with
  | zero =>
    intro j u v h0
    simp at h0
    subst h0
    exact ⟨0, v, rfl⟩
  | succ n ih =>
    intro j u v hsucc
    by_cases hu0 : u = 0
    · subst hu0
      exact ⟨0, v, rfl⟩
    · have hu : u > 0 := by omega
      rcases posReg_machine_phase_noBeep j u v hu with ⟨s1, v1, _, _, hrun1⟩
      rw [iterateRegStep_succ] at hsucc
      rcases ih j (collatzRegStep u) v1 hsucc with ⟨s2, v', hrun2⟩
      refine ⟨s1 + s2, v', ?_⟩
      rw [iterateStep_add s1 s2, hrun1, hrun2]

/-- Whenever `ReachesOne (j + 1)` holds, starting from `canonConfig j j v` the machine
    completes the Collatz orbit of `j + 1`, emits a beep in state `O`, and advances to
    `canonConfig (j + 1) (j + 1) v'`. -/
theorem orbit_advances_and_beeps (j v : Nat) (hreach : ReachesOne (j + 1)) :
    ∃ bStep totalSteps v' : Nat,
      bStep < totalSteps ∧
      exitBeep (iterateStep bStep (canonConfig j j v)) ∧
      iterateStep totalSteps (canonConfig j j v) = canonConfig (j + 1) (j + 1) v' := by
  have hreg : RegReachesZero j := (regReachesZero_iff_reachesOne j).mpr hreach
  rcases hreg with ⟨n, hn⟩
  rcases iterateRegStep_reaches_canonZero n j j v hn with ⟨sOrbit, v1, hOrbit⟩
  rcases resetCanonicalPhaseSimulation_holds j v1 with ⟨bSteps, hbpos, hbeep, hreset⟩
  refine ⟨sOrbit + bSteps, sOrbit + (bSteps + 1), (resetPhase j v1).2.2, by omega, ?_, ?_⟩
  · rw [iterateStep_add sOrbit bSteps, hOrbit]
    exact hbeep
  · rw [iterateStep_add sOrbit (bSteps + 1), hOrbit]
    simpa [resetPhase] using hreset

/-! ### 6. Infinite Beep-Free Execution for Non-Terminating Register Orbits -/

/-- Bounded induction on step offset `d ≤ B`: if `u` never reaches `0` under `iterateRegStep`
    (`∀ n, iterateRegStep u n > 0`), then `canonConfig j u v` NEVER visits beep state `O`
    at any future step `d`. -/
theorem nonterminating_orbit_noBeep_bounded (B : Nat) :
    ∀ d : Nat, d ≤ B → ∀ j u v : Nat,
      (∀ n : Nat, iterateRegStep u n > 0) →
      ¬ exitBeep (iterateStep d (canonConfig j u v)) := by
  induction B with
  | zero =>
    intro d hdB j u v hpos
    have hd0 : d = 0 := by omega
    subst hd0
    exact not_exitBeep_of_le_13 (canonConfig j u v) (by dsimp [canonConfig]; decide)
  | succ B ih =>
    intro d hdB j u v hpos
    have hu : u > 0 := hpos 0
    rcases posReg_machine_phase_noBeep j u v hu with ⟨steps, v', hspos, hnobeep, hrun⟩
    by_cases hlt : d < steps
    · exact hnobeep d hlt
    · have hsplit : d = steps + (d - steps) := by omega
      rw [hsplit, iterateStep_add steps (d - steps), hrun]
      have hpos' : ∀ n : Nat, iterateRegStep (collatzRegStep u) n > 0 := by
        intro n
        exact hpos (n + 1)
      exact ih (d - steps) (by omega) j (collatzRegStep u) v' hpos'

theorem nonterminating_orbit_noBeep (j u v : Nat)
    (hpos : ∀ n : Nat, iterateRegStep u n > 0) (d : Nat) :
    ¬ exitBeep (iterateStep d (canonConfig j u v)) :=
  nonterminating_orbit_noBeep_bounded d d (Nat.le_refl d) j u v hpos

/-! ### 7. Prefix Enumeration and Full Proof of `MachineEquivalentToCollatz` -/

theorem goodPrefix_zero : GoodPrefix 0 := by
  intro n hn1 hn0
  omega

/-- Least counterexample extraction: if `GoodPrefix M` fails, there is a first index `J`
    where `GoodPrefix J` holds and `¬ ReachesOne (J + 1)`. -/
theorem exists_first_bad_input (M : Nat) (hbad : ¬ GoodPrefix M) :
    ∃ J : Nat, GoodPrefix J ∧ ¬ ReachesOne (J + 1) := by
  induction M with
  | zero =>
    exact False.elim (hbad goodPrefix_zero)
  | succ M ih =>
    by_cases hM : GoodPrefix M
    · refine ⟨M, hM, ?_⟩
      intro hreach
      apply hbad
      intro n hn1 hnM1
      by_cases heq : n = M + 1
      · subst heq
        exact hreach
      · exact hM n hn1 (by omega)
    · exact ih hM

/-- If `GoodPrefix J` holds, then starting from the initial blank tape `initial`,
    the machine reaches `canonConfig J J v` at some step `t ≥ J`. -/
theorem goodPrefix_reaches_checkpoint (J : Nat) (hgood : GoodPrefix J) :
    ∃ t v : Nat, t ≥ J ∧ iterateStep t initial = canonConfig J J v := by
  induction J with
  | zero =>
    exact ⟨0, 0, by omega, initial_eq_canonConfig⟩
  | succ J ih =>
    have hgoodJ : GoodPrefix J := by
      intro m hm1 hmJ
      exact hgood m hm1 (by omega)
    rcases ih hgoodJ with ⟨t, v, ht, hrun⟩
    have hreach : ReachesOne (J + 1) := hgood (J + 1) (by omega) (by omega)
    rcases orbit_advances_and_beeps J v hreach with ⟨bStep, totalSteps, v', hlt, _, hnext⟩
    refine ⟨t + totalSteps, v', by omega, ?_⟩
    rw [iterateStep_add t totalSteps, hrun, hnext]

/-- If `CollatzConjecture` holds, then after every `cutoff : Nat` there is a later
    step `n ≥ cutoff` at which the BBB17 machine emits a beep (`beepsAt n`). -/
theorem collatz_implies_unbounded_beeps (hcollatz : CollatzConjecture) (cutoff : Nat) :
    ∃ n : Nat, n ≥ cutoff ∧ beepsAt n := by
  have hgood : GoodPrefix cutoff := goodPrefix_of_collatz hcollatz cutoff
  rcases goodPrefix_reaches_checkpoint cutoff hgood with ⟨t, v, ht, hrun⟩
  have hreach : ReachesOne (cutoff + 1) := hcollatz (cutoff + 1) (by omega)
  rcases orbit_advances_and_beeps cutoff v hreach with ⟨bStep, totalSteps, v', _, hbeep, _⟩
  refine ⟨t + bStep, by omega, ?_⟩
  rw [beepsAt_iff_iterateStep, iterateStep_add t bStep, hrun]
  exact hbeep

/-- Direction 1 (`Quasihalts → ¬ CollatzConjecture`):
    If BBB17 quasihalts, then the Collatz Conjecture is false. -/
theorem quasihalts_implies_not_collatz : Quasihalts → ¬ CollatzConjecture := by
  intro hqh hcollatz
  rcases hqh with ⟨cutoff, hcutoff⟩
  rcases collatz_implies_unbounded_beeps hcollatz cutoff with ⟨n, hn, hbeep⟩
  exact hcutoff n hn hbeep

/-- Direction 2 (`¬ CollatzConjecture → Quasihalts`):
    If the Collatz Conjecture is false, then BBB17 reaches the first counterexample
    checkpoint `canonConfig J J v` and executes positive-register phases forever without
    ever visiting beep state `O` again. -/
theorem not_collatz_implies_quasihalts : ¬ CollatzConjecture → Quasihalts := by
  intro hnot
  have hexists : ∃ M : Nat, ¬ GoodPrefix M := by
    by_cases h : ∃ M : Nat, ¬ GoodPrefix M
    · exact h
    · exfalso
      apply hnot
      intro m hm
      by_cases hgm : GoodPrefix m
      · exact hgm m hm (Nat.le_refl m)
      · exact False.elim (h ⟨m, hgm⟩)
  rcases hexists with ⟨M, hbadM⟩
  rcases exists_first_bad_input M hbadM with ⟨J, hgoodJ, hnotReach⟩
  rcases goodPrefix_reaches_checkpoint J hgoodJ with ⟨t0, v0, _, hrun0⟩
  have hpos : ∀ n : Nat, iterateRegStep J n > 0 := by
    intro n
    by_cases hz : iterateRegStep J n = 0
    · exfalso
      exact hnotReach ((regReachesZero_iff_reachesOne J).mp ⟨n, hz⟩)
    · omega
  refine ⟨t0, ?_⟩
  intro n hn
  rw [beepsAt_iff_iterateStep]
  have hsplit : n = t0 + (n - t0) := by omega
  rw [hsplit, iterateStep_add t0 (n - t0), hrun0]
  exact nonterminating_orbit_noBeep J J v0 hpos (n - t0)

/-- Complete Certified Equivalence (`MachineEquivalentToCollatz`):
    BBB17 quasihalts if and only if the Collatz Conjecture is false. -/
theorem machineEquivalentToCollatz_holds : MachineEquivalentToCollatz :=
  ⟨quasihalts_implies_not_collatz, not_collatz_implies_quasihalts⟩

/-- Certified proof of `GlobalOrbitBridge` (`Quasihalts ↔ ¬ CollatzConjecture`)
    from `ArithmeticOrbitBridge.lean`. -/
theorem globalOrbitBridge_holds : GlobalOrbitBridge :=
  machineEquivalentToCollatz_holds

/-! ### 8. Exact `(j + 1)` Beep Count Certification for the Reset Phase -/

theorem beepsInSteps_one_ne (c : Config) (h : c.state ≠ (14 : State)) :
    beepsInSteps 1 c = 0 := by
  simp [beepsInSteps, h]

theorem beepsInSteps_one_eq (c : Config) (h : c.state = (14 : State)) :
    beepsInSteps 1 c = 1 := by
  simp [beepsInSteps, h]

theorem beepsInSteps_left_sweep_turnaround (q : State) (hq : action q true = ⟨true, false, q⟩)
    (hne14 : q ≠ (14 : State)) (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p - ↑j) = true) :
    beepsInSteps (k + 1) ⟨q, p, t⟩ = 0 := by
  rw [beepsInSteps_add k 1]
  have h1 : beepsInSteps k ⟨q, p, t⟩ = 0 :=
    beepsInSteps_eq_zero_of_noBeep k _ (noBeepInSteps_left_sweep_exact q hq hne14 k p t hones)
  rw [h1, left_sweep_run q hq k p t hones, beepsInSteps_one_ne _ hne14]

theorem beepsInSteps_right_sweep_turnaround (q : State) (hq : action q true = ⟨true, true, q⟩)
    (hne14 : q ≠ (14 : State)) (k : Nat) (p : Int) (t : Int → Bool)
    (hones : ∀ j : Nat, j < k → t (p + ↑j) = true) :
    beepsInSteps (k + 1) ⟨q, p, t⟩ = 0 := by
  rw [beepsInSteps_add k 1]
  have h1 : beepsInSteps k ⟨q, p, t⟩ = 0 :=
    beepsInSteps_eq_zero_of_noBeep k _ (noBeepInSteps_right_sweep_exact q hq hne14 k p t hones)
  rw [h1, right_sweep_run q hq k p t hones, beepsInSteps_one_ne _ hne14]

theorem reset_init_beeps_zero (j v : Nat) :
    beepsInSteps 2 (canonConfig j 0 v) = 0 := by
  apply beepsInSteps_eq_zero_of_noBeep
  exact noBeepInSteps_le_four _ (by dsimp [canonConfig]; decide) 2 (by omega)

theorem reset_loop_base_beeps_one (s v : Nat) :
    beepsInSteps (s + 4) ⟨(12 : State), (s : Int), resetTape 0 s v⟩ = 1 := by
  have hsplit : s + 4 = (s + 3) + 1 := by omega
  rw [hsplit, beepsInSteps_add (s + 3) 1, reset_loop_base_to_beep s v]
  have hbeep1 : beepsInSteps 1 ⟨(14 : State), -1, updateTape (resetTape 0 s v) (-2 : Int) true⟩ = 1 :=
    beepsInSteps_one_eq _ rfl
  rw [hbeep1]
  have hsplit2 : s + 3 = ((s + 1) + 1) + (0 + 1) := by omega
  rw [hsplit2, beepsInSteps_add ((s + 1) + 1) (0 + 1)]
  have hMones : ∀ r : Nat, r < s + 1 → resetTape 0 s v ((s : Int) - ↑r) = true := by
    intro r hr; rw [resetTape_true_iff]; omega
  have hMzero : resetTape 0 s v ((s : Int) - ↑(s + 1)) = false := by
    rw [Bool_eq_false_iff, resetTape_true_iff]; omega
  have hMN := sweep_M_to_N (s + 1) (s : Int) (resetTape 0 s v) hMones hMzero
  have hheadN : (s : Int) - ↑(s + 1) - 1 = -2 := by omega
  rw [hheadN] at hMN
  have hbM : beepsInSteps ((s + 1) + 1) ⟨(12 : State), (s : Int), resetTape 0 s v⟩ = 0 :=
    beepsInSteps_left_sweep_turnaround (12 : State) action_M_on_one (by decide)
      (s + 1) (s : Int) (resetTape 0 s v) hMones
  rw [hbM, hMN]
  have hbN : beepsInSteps (0 + 1) ⟨(13 : State), -2, resetTape 0 s v⟩ = 0 :=
    beepsInSteps_one_ne _ (by dsimp; decide)
  rw [hbN]

theorem reset_loop_pass_beeps_one (a s v : Nat) :
    beepsInSteps (2 * a + 2 * s + 9) ⟨(12 : State), (s : Int), resetTape (a + 1) s v⟩ = 1 := by
  have hsplit : 2 * a + 2 * s + 9 =
      ((s + 1) + 1) + (((a + 1) + 1) + (1 + ((a + 1) + ((s + 1) + 2)))) := by omega
  rw [hsplit, beepsInSteps_add ((s + 1) + 1)]
  have hMones : ∀ r : Nat, r < s + 1 → resetTape (a + 1) s v ((s : Int) - ↑r) = true := by
    intro r hr; rw [resetTape_true_iff]; omega
  have hMzero : resetTape (a + 1) s v ((s : Int) - ↑(s + 1)) = false := by
    rw [Bool_eq_false_iff, resetTape_true_iff]; omega
  have hMN := sweep_M_to_N (s + 1) (s : Int) (resetTape (a + 1) s v) hMones hMzero
  have hheadN : (s : Int) - ↑(s + 1) - 1 = -2 := by omega
  rw [hheadN] at hMN
  have hbM : beepsInSteps ((s + 1) + 1) ⟨(12 : State), (s : Int), resetTape (a + 1) s v⟩ = 0 :=
    beepsInSteps_left_sweep_turnaround (12 : State) action_M_on_one (by decide)
      (s + 1) (s : Int) (resetTape (a + 1) s v) hMones
  rw [hbM, hMN, Nat.zero_add, beepsInSteps_add ((a + 1) + 1)]
  have hNones : ∀ r : Nat, r < a + 1 → resetTape (a + 1) s v ((-2 : Int) - ↑r) = true := by
    intro r hr; rw [resetTape_true_iff]; omega
  have hNzero : resetTape (a + 1) s v ((-2 : Int) - ↑(a + 1)) = false := by
    rw [Bool_eq_false_iff, resetTape_true_iff]; omega
  have hNO := sweep_N_to_beep_O (a + 1) (-2 : Int) (resetTape (a + 1) s v) hNones hNzero
  let tapeO : Int → Bool := updateTape (resetTape (a + 1) s v) (-3 - (a : Int)) true
  have hheadO : (-2 : Int) - ↑(a + 1) + 1 = -2 - (a : Int) := by omega
  have htapeO : updateTape (resetTape (a + 1) s v) ((-2 : Int) - ↑(a + 1)) true = tapeO := by
    have heq : (-2 : Int) - ↑(a + 1) = -3 - (a : Int) := by omega
    rw [heq]
  rw [hheadO, htapeO] at hNO
  have hbN : beepsInSteps ((a + 1) + 1) ⟨(13 : State), -2, resetTape (a + 1) s v⟩ = 0 :=
    beepsInSteps_left_sweep_turnaround (13 : State) action_N_on_one (by decide)
      (a + 1) (-2 : Int) (resetTape (a + 1) s v) hNones
  rw [hbN, hNO, Nat.zero_add, beepsInSteps_add 1, iterateStep_one]
  have hbO : beepsInSteps 1 ⟨(14 : State), -2 - (a : Int), tapeO⟩ = 1 :=
    beepsInSteps_one_eq _ rfl
  have hOone : tapeO (-2 - (a : Int)) = true := by
    simp only [tapeO, updateTape_true_iff, resetTape_true_iff]; omega
  let tapeP : Int → Bool := updateTape tapeO (-2 - (a : Int)) false
  have hOP : step ⟨(14 : State), -2 - (a : Int), tapeO⟩ =
      ⟨(15 : State), -1 - (a : Int), tapeP⟩ := by
    simp [step, hOone, action_O_on_one]
    constructor
    · omega
    · funext i
      by_cases hi : i = -2 - (a : Int) <;> simp [tapeP, updateTape, hi]
  rw [hbO, hOP, beepsInSteps_add (a + 1)]
  have hPones : ∀ r : Nat, r < a → tapeP ((-1 - (a : Int)) + ↑r) = true := by
    intro r hr
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]; omega
  have hPzero : tapeP ((-1 - (a : Int)) + ↑a) = false := by
    rw [Bool_eq_false_iff]
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]; omega
  have hPQ := sweep_P_to_Q a (-1 - (a : Int)) tapeP hPones hPzero
  have hheadQ : -1 - (a : Int) + ↑a + 1 = 0 := by omega
  rw [hheadQ] at hPQ
  have hbP : beepsInSteps (a + 1) ⟨(15 : State), -1 - (a : Int), tapeP⟩ = 0 :=
    beepsInSteps_right_sweep_turnaround (15 : State) action_P_on_one (by decide)
      a (-1 - (a : Int)) tapeP hPones
  rw [hbP, hPQ, Nat.zero_add]
  have hQsplit : (s + 1) + 2 = ((s + 1) + 1) + 1 := by omega
  rw [hQsplit, beepsInSteps_add ((s + 1) + 1) 1]
  have hQones : ∀ r : Nat, r < s + 1 → tapeP ((0 : Int) + ↑r) = true := by
    intro r hr
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]; omega
  have hQzero : tapeP ((s : Int) + 1) = false := by
    rw [Bool_eq_false_iff]
    simp only [tapeP, tapeO, updateTape_false_iff, updateTape_true_iff, resetTape_true_iff]; omega
  have hbQ : beepsInSteps ((s + 1) + 1) ⟨(16 : State), 0, tapeP⟩ = 0 :=
    beepsInSteps_right_sweep_turnaround (16 : State) action_Q_on_one (by decide)
      (s + 1) 0 tapeP hQones
  have hQstep : iterateStep ((s + 1) + 1) ⟨(16 : State), 0, tapeP⟩ =
      ⟨(11 : State), (s : Int) + 1 + 1, updateTape tapeP ((s : Int) + 1) true⟩ := by
    rw [iterateStep_add (s + 1) 1, sweep_Q_ones (s + 1) 0 tapeP hQones, iterateStep_one]
    simp [step, hQzero, action_Q_on_zero]
    funext i
    by_cases hi : i = (s : Int) + 1 <;> simp [updateTape, hi]
  rw [hbQ, hQstep, beepsInSteps_one_ne _ (by dsimp; decide)]

theorem reset_loop_run_exact_beeps (a s v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      beepsInSteps steps ⟨(12 : State), (s : Int), resetTape a s v⟩ = a + 1 ∧
      iterateStep steps ⟨(12 : State), (s : Int), resetTape a s v⟩ =
        ⟨(0 : State), 0, updateTape (resetTape 0 (a + s) v) (-2 : Int) true⟩ := by
  induction a generalizing s with
  | zero =>
    refine ⟨s + 4, by omega, reset_loop_base_beeps_one s v, ?_⟩
    have hsplit : s + 4 = (s + 3) + 1 := by omega
    rw [hsplit, iterateStep_add (s + 3) 1, reset_loop_base_to_beep s v, iterateStep_one]
    simpa using reset_loop_beep_to_A s v
  | succ a ih =>
    rcases ih (s + 1) with ⟨steps, hpos, hbeeps, hrun⟩
    refine ⟨(2 * a + 2 * s + 9) + steps, by omega, ?_, ?_⟩
    · rw [beepsInSteps_add (2 * a + 2 * s + 9) steps, reset_loop_pass_beeps_one a s v,
        reset_loop_pass a s v, hbeeps]
      omega
    · rw [iterateStep_add (2 * a + 2 * s + 9) steps, reset_loop_pass a s v, hrun]
      have has : a + (s + 1) = a + 1 + s := by omega
      rw [has]

/-- Certified Exact Beep-Count Theorem for the Reset Phase (`u = 0`):
    Starting from `canonConfig j 0 v`, the reset phase advances `(j, 0, v)` to
    `(j + 1, j + 1, v - (j + 1))` while visiting beep state `O` (14) **exactly `j + 1` times**. -/
theorem resetPhase_exact_beep_count (j v : Nat) :
    ∃ steps : Nat, steps > 0 ∧
      beepsInSteps steps (canonConfig j 0 v) = j + 1 ∧
      iterateStep steps (canonConfig j 0 v) =
        canonConfig (resetPhase j v).1 (resetPhase j v).2.1 (resetPhase j v).2.2 := by
  rcases reset_loop_run_exact_beeps j 0 v with ⟨steps, hpos, hbeeps, hrun⟩
  refine ⟨2 + steps, by omega, ?_, ?_⟩
  · rw [beepsInSteps_add 2 steps, reset_init_beeps_zero j v, resetPhase_init_two_steps j v,
      hbeeps, Nat.zero_add]
  · rw [iterateStep_add 2 steps, resetPhase_init_two_steps j v, hrun]
    have hj0 : j + 0 = j := by omega
    rw [hj0]
    simp only [canonConfig, resetPhase]
    congr 1
    funext i; rw [Bool_eq_iff]
    simp only [updateTape_true_iff, resetTape_true_iff, canonTape_true_iff]
    omega

end BBB17
