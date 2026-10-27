# ETH / bounded-width SAT independent audit (2026-10-26)

Source: https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf

Formal endpoint: https://github.com/openai/math/blob/main/lean/OAI/Algorithms/SubexponentialSAT/SqrtLogSpace/Final.lean

## Scope and evidence boundary

The real formal endpoint is `SqrtLogSpace.exact_count_and_sat` (and `exact_count_eth`), **not** the unfinished comparator challenge. Its statement concerns a fixed primitive machine, exact model counts, decision state, asymptotic running time, and all-prefix polynomial visited-tape space. A repository file with `sorry` is not independently certified, but its existence elsewhere does not invalidate this implementation.

This repository's `sat_audit.py` provides two independent bounded exact-count implementations (truth-table enumeration and DPLL with free-variable accounting), including empty CNFs, empty clauses, tautologies, and randomized width <= 3 instances. It is **not** an implementation, independent kernel audit, asymptotic validation, or computational reproduction of OpenAI's subexponential algorithm.

## Verification gates

- G1: Pin upstream commit and capture PDF hash, Lean toolchain and dependency locks.
- G2: Rebuild full Lean import closure of `SqrtLogSpace/Final.lean`; collect `#print axioms` and check for `sorryAx`, extra axioms, and imported assumptions.
- G3: Compare the exact compiled machine statement, complexity constants and space measure with the preprint; distinguish the manuscript's sharper cases.
- G4: Extract or implement the actual algorithm and demonstrate small-instance equality against the bounded oracles, with fixed seeds and adversarial instances.
- G5: Compare wall time, visited work, memory, and input encoding against matched DPLL/CDCL, with timeouts and confidence intervals. Finite tests cannot prove asymptotic complexity.
- G6: Only after G1-G5, study safe MAPEOGEO/NGC state-quotient interpretations; do not assume SAT reductions are geometric.

## Bounded regression

Run `python experiments/eth_sat_audit/sat_audit.py`.

Locally prior to publication: 456/456 oracle comparisons passed using CPython in the sandbox. These tests verify only the oracle code's internal agreement. No Lean compilation or upstream algorithm execution was performed here.
