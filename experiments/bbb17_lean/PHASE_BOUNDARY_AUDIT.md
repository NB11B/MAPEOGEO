# BBB17 phase-boundary discovery (2026-10-24)

## Reproducible observations (not mathematical proof)

From the *exact supplied 34 transitions*, using 0-indexed execution steps, the beep at index `j(j+1)/2` for each integer `1 <= j <= 26` occurs with the head at `-1`, leftmost written 1-cell at `-(j+1)`, and the total number of beeps through this event is triangular.

At the 351st beep (`j=26`): step 62273, head=-1, leftmost 1-cell=-27, rightmost 1-cell=79, number of 1-cells=105.

At 10,000,000 executed steps: state D (3), head 1628, leftmost 1-cell -27, rightmost 1-cell 2428, 2453 marked 1-cells. No additional beep recorded.

The input 27 is known to generate a long but terminating Collatz orbit; absence of beeps while its simulation is in progress is compatible with the intended enumeration, but cannot prove it.

These observations suggest unary input indexing and beep grouping. The remaining indispensable theorem is a quantified transition macro relating each machine phase to a bounded arithmetic computation, then a global enumeration invariant. **Do not infer counterexample or quasihalting from the 10-million-step beep-free suffix.**

## Falsification checks

- Verify exact tape patterns at consecutive beep clusters.
- Produce a *proved* macro transition for each arithmetic primitive.
- Prove each prefix completion event is reachable exactly when the corresponding Collatz obligations terminate.
- Prove infinitely many successful prefixes iff infinitely many beeps (including the relevant finite multiplicity condition).
- Audit both directions of the final equivalence separately.

Status: empirical invariant candidates only. No theorem claim.
