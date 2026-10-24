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


-- Complete tape effect, not just final state and head. J writes at p,
-- then F erases at p+1, independently of both pre-existing symbols.
theorem JF_two_step_tape (p i : Int) (t : Int → Bool) :
    (step (step ⟨(9 : State), p, t⟩)).tape i =
      (if i = p + 1 then false else if i = p then true else t i) := by
  cases h : t p <;> cases h2 : t (p + 1) <;>
    simp [step, action, h, h2]

-- Local machine semantics are deterministic for all configurations.
theorem step_deterministic (c : Config) (x y : Config)
    (hx : x = step c) (hy : y = step c) : x = y := by
  rw [hx, hy]

end BBB17
