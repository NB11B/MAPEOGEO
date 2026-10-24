# BBB17–Collatz Lean 4 formalization (research gate)

The two Lean files separate (a) the **34 supplied machine transitions and beep semantics** from (b) the Collatz conjecture and finite-prefix mathematics.

## Claims and limits
- `enters_O_iff` exhaustively checks the only entry into beep state O is state N reading 0.
- `bad_input_blocks_larger_prefixes` proves that a counterexample rules out all prefixes that include it.
- `MachineEquivalentToCollatz` is a **definition of the desired theorem statement**, NOT a theorem.
- No axiom, `sorry`, or admitted Collatz equivalence is supplied.
- A blank tape and state A are the initial configuration. Beeps are counted **on exit from O** (state before executing the transition).
- The transition action's first triple corresponds to reading 0, second to reading 1.

## Reproduction
From this directory with Lean 4 installed:
```sh
lean BBB17.lean
LEAN_PATH=. lean CollatzBridge.lean
```
Repository CI compiles both modules. Verify the specific version in the workflow.

## Blocking proof gate
Construct an arithmetic abstraction `decode : Config → ...` and an exact simulation lemma relating `step` (or well-founded grouped machine steps) to a Collatz enumeration process, including completeness of emitted beeps. Then prove both directions of `MachineEquivalentToCollatz` without assuming Collatz itself.

Do NOT infer quasihalting from a finite beep-free suffix.
