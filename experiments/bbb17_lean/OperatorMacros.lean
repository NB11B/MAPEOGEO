import BBB17

/-! Exact local transition macros. These theorems quantify over arbitrary tapes
and positions; they do not assume a Collatz interpretation. -/
namespace BBB17

theorem action_F (b : Bool) :
    action (5 : State) b = ⟨false, false, (6 : State)⟩ := by
  cases b <;> decide

theorem action_J (b : Bool) :
    action (9 : State) b = ⟨true, true, (5 : State)⟩ := by
  cases b <;> decide

theorem action_M_on_one :
    action (12 : State) true = ⟨true, false, (12 : State)⟩ := by
  decide

theorem action_P_on_one :
    action (15 : State) true = ⟨true, true, (15 : State)⟩ := by
  decide

theorem action_Q_on_one :
    action (16 : State) true = ⟨true, true, (16 : State)⟩ := by
  decide

theorem action_N_on_zero :
    action (13 : State) false = ⟨true, true, (14 : State)⟩ := by
  decide

theorem action_O_on_zero :
    action (14 : State) false = ⟨false, true, (0 : State)⟩ := by
  decide

theorem action_O_on_one :
    action (14 : State) true = ⟨false, true, (15 : State)⟩ := by
  decide

-- A single transition is never itself a Collatz theorem.
-- These exact identities are primitive blocks from which multi-step
-- arithmetic simulations must be derived and certified.
end BBB17
