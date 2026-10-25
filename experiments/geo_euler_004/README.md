# GEO-EULER-004 — Partial observations and restricted grammar search

From shuffled opaque IDs, successor, zero/one anchors, and incomplete binary-operation tables, infer recurrence rules without identifying the operators by name. Candidate grammars are supplied in a **small enumerated library**: successor shifts 0/1/2; and, for a second operator, recursion through the first, successor, or identity. Rule selection uses training cells only; missing cells are reconstructed recursively, and withheld cells are scored independently.

Sandbox run 2026-10-25: 10/10 unit tests passed; 186 untouched predictions correct (142 first operator, 44 second); ten prime IDs through 30 recovered; 5 independent symbol permutations and three refusal controls qualified. An initial local import-path failure was corrected before qualification.

Run from repository root:
```bash
cd experiments/geo_euler_004
python -m unittest discover -v
python grammar.py
```

### Boundaries
This is **restricted recurrence grammar selection**, not autonomous discovery of an unrestricted operator language. The successor chain, zero and one, finite bound, candidate recurrence templates, and encoded transition samples are all supplied. Reference primality uses the separately held decoding only when reporting results. The predicted operations are defined over a truncated finite arithmetic universe; out-of-domain predictions are not asserted. No claim of formal proof or native MAPEOGEO semantic invention.
