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

theorem step_deterministic (c : Config) (x y : Config)
    (hx : x = step c) (hy : y = step c) : x = y := by
  rw [hx, hy]

end BBB17
