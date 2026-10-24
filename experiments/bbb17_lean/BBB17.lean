/-!
BBB17: exact transition relation for the proposed 17-state beeping machine.
Machine string:
1RL0RB_1LC1RB_0LK0LD_1RE1LD_0RF0RB_0LG0LG_1LH1LG_0RA0RI_1RJ1RI_1RF1RF_0RA1LK_0LM0LM_0LN1LM_1RO1LN_0RA0RP_0RQ1RP_1RL1RQ
A=0, ..., O=14, Q=16. First triple reads 0; second reads 1.
This file deliberately does NOT assert a Collatz simulation theorem.
-/
namespace BBB17
abbrev State := Fin 17
structure Action where
  write : Bool
  right : Bool
  next : State
  deriving DecidableEq, Repr

def action (q : State) (read : Bool) : Action :=
  match q.val, read with
  | 0, false => ⟨true, true, 11⟩
  | 0, true  => ⟨false, true, 1⟩
  | 1, false => ⟨true, false, 2⟩
  | 1, true  => ⟨true, true, 1⟩
  | 2, false => ⟨false, false, 10⟩
  | 2, true  => ⟨false, false, 3⟩
  | 3, false => ⟨true, true, 4⟩
  | 3, true  => ⟨true, false, 3⟩
  | 4, false => ⟨false, true, 5⟩
  | 4, true  => ⟨false, true, 1⟩
  | 5, false => ⟨false, false, 6⟩
  | 5, true  => ⟨false, false, 6⟩
  | 6, false => ⟨true, false, 7⟩
  | 6, true  => ⟨true, false, 6⟩
  | 7, false => ⟨false, true, 0⟩
  | 7, true  => ⟨false, true, 8⟩
  | 8, false => ⟨true, true, 9⟩
  | 8, true  => ⟨true, true, 8⟩
  | 9, false => ⟨true, true, 5⟩
  | 9, true  => ⟨true, true, 5⟩
  | 10, false => ⟨false, true, 0⟩
  | 10, true  => ⟨true, false, 10⟩
  | 11, false => ⟨false, false, 12⟩
  | 11, true  => ⟨false, false, 12⟩
  | 12, false => ⟨false, false, 13⟩
  | 12, true  => ⟨true, false, 12⟩
  | 13, false => ⟨true, true, 14⟩
  | 13, true  => ⟨true, false, 13⟩
  | 14, false => ⟨false, true, 0⟩
  | 14, true  => ⟨false, true, 15⟩
  | 15, false => ⟨false, true, 16⟩
  | 15, true  => ⟨true, true, 15⟩
  | 16, false => ⟨true, true, 11⟩
  | 16, true  => ⟨true, true, 16⟩
  | _, _ => ⟨false, true, 0⟩

-- Exhaustive finite-state property: O can only be entered from N reading 0.
theorem enters_O_iff (q : State) (b : Bool) :
    (action q b).next = (14 : State) ↔ q = (13 : State) ∧ b = false := by
  revert q b
  decide

structure Config where
  state : State
  head : Int
  tape : Int → Bool

def initial : Config := ⟨0, 0, fun _ => false⟩
def exitBeep (c : Config) : Prop := c.state = (14 : State)

def step (c : Config) : Config :=
  let a := action c.state (c.tape c.head)
  { state := a.next
    head := if a.right then c.head + 1 else c.head - 1
    tape := fun i => if i = c.head then a.write else c.tape i }

def run (n : Nat) : Config := (step^[n]) initial

def beepsAt (n : Nat) : Prop := exitBeep (run n)
def Quasihalts : Prop := ∃ cutoff : Nat, ∀ n ≥ cutoff, ¬ beepsAt n

-- The definition explicitly quantifies over all future steps.
theorem quasihalts_iff_finitely_many_beep_times :
    Quasihalts ↔ ∃ cutoff : Nat, ∀ n ≥ cutoff, ¬ beepsAt n := Iff.rfl
end BBB17
