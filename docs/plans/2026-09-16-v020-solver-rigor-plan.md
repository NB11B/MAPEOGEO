# v0.20 Solver-Rigor Implementation Plan

> Execute test-first. Do not restore the historical 10/10 headline by weakening a gate. Every task records RED before production changes and GREEN after.

## Task 1: Canonical evidence identities

**Files:** new `canonical.py`; `model.py`, `operators.py`, `test_canonical.py`, `test_model_goals.py`.

Add failing golden-vector and cross-process tests covering type separation, dict/set order, hash seed, `-0.0`, exact rationals, NumPy/SymPy, and rejection of nonfinite/opaque values. Implement domain-separated canonical SHA-256; replace randomized derived IDs. Add typed artifacts, named ports, structured refusals, derivation/obligation records, lineage receipts, runtime macro bindings, and verifier stage/subject fields. Commit `refactor(v0.20): add canonical typed evidence model`.

## Task 2: One contract-checked transition engine

**Files:** `operators.py`, `v2.py`, `v0_20_operators.py`, `planner.py`, `compatibility.py`; new `lineage.py`; `test_execution_contracts.py`, existing planner/typing tests.

Add failing tests for exact port multiplicity, whole-state leakage, runtime output-type mismatch, forged provenance, equal-valued distinct roots, full target contract, later valid candidates, preserved failure traces, unknown verifier classes, and exact large integers. Extend `_spec` to complete input/output contracts and mark meta operators. Implement planner-owned roots/derivations, injective bindings, full state signatures, exhaustive candidate verification, structured counters/refusals, and immutable inferred root routing. Commit `refactor(v0.20): enforce typed transitions and lineage`.

## Task 3: Independent historical-family verification

**Files:** new `goal_verifiers.py`; `operators.py`, `planner.py`, `goals.py`, `campaign.py`; `test_goal_verifier_mutations.py`.

For G1-G12, first add one forged-candidate mutation test per family plus specific tests for G2 basis validity, G3 localization, G4 exact separation, G5 equal-input identity, G7 supplied generator, G9 scale-aware error bounds, G10 order ten, and G11 homothety. Implement root-recomputed terminal verifiers and trustworthy primitive verifiers. Repair G9/G10 algorithms or fail closed on unsupported inputs. Commit `fix(v0.20): independently verify historical goal families`.

## Task 4: Foundational and complex mathematics

**Files:** `v0_20_goals.py`, `v0_20_operators.py`, `goal_verifiers.py`, `campaign.py`, `test_v0_20_math_rigor.py`.

Add failing positive/negative/domain/alternate-witness tests. Replace F1 with exact `sqrt(2)` cut bounds, F2 with exact quadratic MVT, and F3 with integer-domain Bézout evidence. Bind C1 symbols explicitly and recompute residuals; bind C2 variable/pole and recompute arbitrary residues. Make scoring certificate-based rather than implementation-output equality. Commit `fix(v0.20): implement rigorous foundational and complex contracts`.

## Task 5: Genuine cross-class X1/X2

**Files:** `v0_20_goals.py`, `v0_20_operators.py`, `goal_verifiers.py`; new `elliptic_periods.py`; `test_v0_20_cross_class_math.py`.

Add failing X1 tests for root reconstruction, rational references, perturbed numerical values, tolerance mutation, and forged zero residual. Add X2 tests for discriminant convention, singular refusal, full-period factors, AGM enclosures, q-series invariant reconstruction, perturbed periods, and positive-discriminant calibration cases. Implement exact-to-symbolic-to-numerical pipelines and independently checked terminal enclosures. Commit `fix(v0.20): certify cross-class polynomial and elliptic pipelines`.

## Task 6: Sound shortcut proof and runtime enforcement

**Files:** new `shortcut_proof.py`; `model.py`, `planner.py`, `compatibility.py`, `v0_20_goals.py`, `v0_20_campaign.py`; `test_v0_20_shortcut_soundness.py`.

Add failing tests for injected direct shortcuts, each bridge ablation, unrelated evidence, forged provenance, wrong target representation/exactness, registry mutation, and macro attempts to waive lineage. Implement finite type-hypergraph/lineage closure, replayable witnesses, digest validation, and candidate-specific runtime obligations. Replace `prove_no_same_class_shortcut`. Commit `fix(v0.20): prove and enforce candidate lineage obligations`.

## Task 7: Macro conservation authority boundary

**Files:** `macros.py`, `v0_20_macros.py`, `planner.py`, `campaign.py`, `v0_20_campaign.py`; `test_macro_conservation.py`, existing macro tests.

Adversarial review showed that the proposal schema did not bind the complete executable dependency closure, runtime request/configuration, budget, or typed replay ledger. Production macro replay is therefore disabled fail-closed: `solve()` never evaluates proposals, no proposal can rescue a primitive failure, and no macro conservation or efficiency credit is awarded. The report keeps exact macro conservation as a failing capability gate until a complete authority design is implemented.

## Task 8: Prospective disjoint corpus and non-vacuous gates

**Files:** `goals.py`, `v0_20_goals.py`, `campaign.py`, `v0_20_campaign.py`, `test_v0_20_corpus_integrity.py`, `test_v0_20_campaign.py`.

Add content-fingerprint collision tests and frozen expected counts for every split/family/control. Build genuinely disjoint variants and negative/corrupt/alternate controls. Require every expected case and control in each relevant mode; make empty/missing channels fail. Do not count correctness labels as verifier evidence. Commit `test(v0.20): freeze prospective corpus and fail-closed gates`.

## Task 9: Deterministic report and CI

**Files:** `generate_v0_20_report.py`, `requirements-v0.20-lock.txt`, evidence JSON, `.github/workflows/pct-goal-solver-v0-20-rigor.yml`, `.github/workflows/pct-e1-e25-campaign.yml`, `test_generate_v0_20_report.py`, E26-E31 fixture tests.

Add failing byte-comparison tests across hash seeds and explicit output directories. Pin runtime versions; add canonical report/newline and digest manifest. Correct workflow branch/PR triggers, run the v0.20 generator, compare committed evidence, and require the currently expected truthful `EVIDENCE_PARTIAL` result, zero wrong positives, and intact provenance. Any status drift—including `NOT_SUPPORTED`, `ENGINE_INVALID`, or `SUPPORTED`—requires explicit review rather than silently passing CI. For E26-E31, preflight both frozen SHAs and the external artifact digest; execute the claimed frozen solver or narrow the claim, and never pass with absent committed fixtures. Commit `ci(v0.20): bind deterministic evidence and frozen fixtures`.

## Task 10: Bind repaired current main without merging

After `agent/main-math-rigor-v0-20` passes review, keep it separate. Bind the feature campaign to the exact repaired-main commit, tree, frozen boundary files, and producer manifest; CI checks out that revision into a second directory and verifies it without merging either branch.

## Final verification

Run at minimum:

```bash
python -m pytest -q experiments/pct_goal_solver
python -m pytest -q experiments/pct_e1_e25 experiments/pct_e26_e31 tests
python -m experiments.pct_goal_solver.generate_v0_20_report --out-dir /tmp/v020-a
PYTHONHASHSEED=1 python -m experiments.pct_goal_solver.generate_v0_20_report --out-dir /tmp/v020-b
diff -ru /tmp/v020-a /tmp/v020-b
git status --short
```

Request independent reviews for mathematics, planner/lineage, macro conservation, and CI/evidence. Fix all P0/P1 findings, rerun the full matrix, push both named branches, and leave them unmerged.
