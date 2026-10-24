import OperatorMacros

/-!
Exact two-step J→F→G state and head macros on arbitrary tapes.
Proofs use the already certified action lemmas instead of unfolding
the full 34-transition table.
Full tape equality remains a separate unverified obligation.
-/
namespace BBB17

theorem JF_two_step_state (p : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).state = (6 : State) := by
  simp [step, action_J, action_F]

theorem JF_two_step_head (p : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).head = p := by
  simp [step, action_J, action_F]

theorem F_one_step_state (p : Int) (t : Int → Bool) :
    (step ⟨(5 : State), p, t⟩).state = (6 : State) := by
  simp [step, action_F]

theorem J_one_step_state (p : Int) (t : Int → Bool) :
    (step ⟨(9 : State), p, t⟩).state = (5 : State) := by
  simp [step, action_J]


-- Exact tape effects of J followed by F at arbitrary tape/head.
theorem JF_tape_at_start (p : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).tape p = true := by
  simp [step, action_J, action_F]

theorem JF_tape_at_next (p : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).tape (p + 1) = false := by
  simp [step, action_J, action_F]

theorem JF_tape_elsewhere (p i : Int) (t : Int → Bool)
    (hp : i ≠ p) (hn : i ≠ p + 1) :
    (step (step ⟨(9 : State), p, t⟩)).tape i = t i := by
  simp [step, action_J, action_F, hp, hn]

theorem step_deterministic (c : Config) (x y : Config)
    (hx : x = step c) (hy : y = step c) : x = y := by
  rw [hx, hy]

end BBB17
