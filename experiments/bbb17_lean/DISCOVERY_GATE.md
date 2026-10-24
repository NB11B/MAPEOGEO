# BBB17 discovery → Lean certification gate
Run `python -m unittest -v test_discover.py` and `python discover.py --steps 1000000` from this directory. Pure Python, no dependencies. The exact independent interpreter is in the previous BBB17 qualification package.

**Observed**: 351 beeps in 1,000,000 steps; final observed beep at step 62,273. At each observed triangular beep rank 1..26, head = -1, leftmost 1-cell = -(rank+1). Neither pattern has been proved for arbitrary rank.

**Falsified candidate**: The number of marked tape cells is NOT rank*(rank+1)/2: at first triangular checkpoint it is 2 instead of 1; later checkpoints likewise differ. Failure classified as a wrong conjecture, not a Lean/compiler error.

**Integration rule**: Exact transition → checkpoint discovery → independently compare against reference → formulate theorem → Lean check → only then permit composition. Do not use finite executions to infer quasihalting. The full machine ↔ Collatz equivalence remains UNPROVED.

**Formal gate**: The Lean machine file and CollatzBridge formalization reside in the sibling files. A structural phase macro and an all-input arithmetic decoding relation are still required. GitHub Actions CI must report success before any claim of compiled theorems.
