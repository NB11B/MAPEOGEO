# Rule 30 Prize: Proof-Closure Engineering Environment (`R30-CLOSE-001`)

- **Baseline:** Frozen `G0`–`G11` commit `8cb32c288f78bd04dbfd1b9e5e4883ed960d4c51` (`experiment/rule30-prize-qualification-g11`, **103/103** headlines, **693** replayed declarations).
- **Closure Branch:** `research/rule30-proof-closure`
- **Formal Modules (`formal/`):** 5 Lean `v4.35.0` modules (`Rule30ClosureCore.lean`, `Rule30LeftReconstruction.lean`, `Rule30RightInformation.lean`, `Rule30BilateralCompatibility.lean`, `Rule30PrizeClosure.lean`), **20/20** proof-closure headlines verified by official `Check.lean` (`"verdict": "pass"`, `"claim": "partial"`, `"newAxioms": []`).

## Reproduction

```bash
# Run the complete R30-CLOSE-001 campaign and regenerate evidence/
python -m experiments.rule30_proof_closure.certificates.proof_certificate

# Run the 5-file proof-closure pytest suite (including live Lean 4.35.0 + Check.lean verification)
pytest experiments/rule30_proof_closure/tests -v
```

## Checkpoints & Proof Obligations (`M1`–`M5`)

| Checkpoint / Obligation | Status | Key Formal Declarations & Findings |
| :--- | :--- | :--- |
| **Checkpoint 01 / `M1` (Reconstruction Completeness)** | `EXACT` (Passed) | `stepLeftRow_rowAtLeft`, `runLeftWord_rowAtLeft`, `left_black_step_screened_forcing`, `left_effective_boundary_autonomous_step`, `left_light_cone_support_bound`. Forward left-half word evolution is 100% determined by `rowAtLeft t (-1)` and `col0Word t L` with zero right-half dependency. |
| **Checkpoint 02 / `M2` (Bilateral Soundness & Decoupling Falsification)** | `EXACT` (Passed) | `bilateral_center_conservation`, `obsLeftWord_rowAtLeft_eq_orColWord_rowAt`, `bilateral_observation_mismatch_excludes_periodic_word`, `decoupled_halves_consistent_but_bilaterally_incompatible`. Proves `cell t (-1) = xor (cell (t+1) 0) (orCol 0 t)` and refutes left-right decoupling at $T = 1, w = [0, 1]$ (`L_unsat = 8` vs `C_unsat = 1`). |
| **Checkpoint 03 / `M3` (Infinite-Horizon Obstructions)** | `EXACT` (Constant / $P=1$ / Linear Re-Entry) & `BOUNDED` (Cone Elimination) | `no_eventually_all_white_center`, `no_eventually_all_black_center`, `no_period_one_center_all_transients`, `periodic_center_has_black_and_white_in_every_period`, `universal_linear_reentry_horizon_bound`, `periodic_center_distinct_futureWork_classes_at_linear_horizon`. Upgrades `G11.4` to an explicit constructive linear re-entry bound $(k + 1)P \ge t_0 + (m_0 + q)P$ via `window_jen`. |
| **`M4` (Universal Lifting Theorem)** | `UNRESOLVED` | Isolated to two exact mathematical obligations: (Track A/C) $\mathbb{F}_2$ non-vanishing of the overdetermined degree-2 cone polynomial system in $2T - 2$ variables, or (Track B) a sub-linear upper bound on realizable single-seed `FutureWorkEquiv` classes to contradict the $\Omega(M)$ `window_jen` lower bound. |
| **Checkpoint 04 / `M5` (End-to-End Composition & Claim Audit)** | `CONDITIONAL` (Partial Verified; Complete Claim Automatically Rejected by `M4` Audit) | `bilateral_cone_unsat_implies_problem1`, `linear_horizon_quotient_collision_implies_problem1`. Both end-to-end reductions to `Rule30Prize.Problem1` are kernel-verified; the automated dependency auditor rejects any unconditional closure claim until an `M4` node is proved `EXACT`. |
