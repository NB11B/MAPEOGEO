import BBB17

/-!
Two-step macro certificates. Each theorem ranges over arbitrary tape functions
and positions, not just the observed blank-tape trajectory.
The composition J→F→G is exact, but not yet an arithmetic Collatz operator.
-/
namespace BBB17

theorem JF_two_step_state (p : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).state = (6 : State) := by
  cases h : t (p + 1) <;> simp [step, action, h]

theorem JF_two_step_head (p : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).head = p := by
  cases h : t (p + 1) <;> simp [step, action, h]

theorem F_one_step_state (p : Int) (t : Int → Bool) :
    (step ⟨(5 : State), p, t⟩).state = (6 : State) := by
  cases h : t p <;> simp [step, action, h]

theorem J_one_step_state (p : Int) (t : Int → Bool) :
    (step ⟨(9 : State), p, t⟩).state = (5 : State) := by
  cases h : t p <;> simp [step, action, h]

-- Local machine semantics are deterministic for all configurations.
theorem step_deterministic (c : Config) (x y : Config)
    (hx : x = step c) (hy : y = step c) : x = y := by
  rw [hx, hy]

end BBB17
