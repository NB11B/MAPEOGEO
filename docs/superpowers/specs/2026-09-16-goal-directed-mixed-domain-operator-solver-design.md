# Goal-Directed Mixed-Domain Operator Solver Design

> **Historical V1 design — superseded for current v0.20.** Primitive-plus-macro
> execution and macro-support criteria in this document apply only to the frozen
> V1/V2 program. Current v0.20 macro proposals are inert and have no execution,
> conservation, or efficiency authority.

**Status:** APPROVED FOR EXECUTION  
**Date:** 2026-09-16  
**Branch:** `agent/pct-computational-architecture`  
**Primary user directive:** structured goals first; mixed exact/symbolic/numerical domain; test explicit and inferred typing; test primitive-only and primitive+macro synthesis; no LLM inside the scored scientific core.

## 1. Governing question

Can the accumulated MAPEOGEO/PCT E-series machinery be organized into a true goal-directed solver that searches and composes executable mathematical operators, rather than classifying hidden semantic labels from graph fingerprints?

The target architecture is:

```text
structured goal
  -> admissible operator search
  -> operator composition
  -> candidate construction
  -> falsification / contradiction search
  -> independent verification
  -> fail-closed verdict + trace
```

The first campaign deliberately includes exact, symbolic, and numerical tasks in one search space. If mixed-domain planning fails, the failure is part of the scientific result rather than a reason to split the system post hoc.

## 2. Scope and claim boundary

The scored core accepts only structured goals. Natural-language interpretation is excluded from this campaign so language-model competence cannot mask or cause mathematical planner behavior. LLMs may later interrogate goal traces or translate human requests into the frozen structured-goal schema.

A positive result supports goal-directed operator composition over the tested mixed-domain task family. It does not establish universal theorem proving, unrestricted symbolic mathematics, or correctness outside the bounded operator registry and goal grammar.

## 3. Experimental factors

Two orthogonal factors are scored.

### 3.1 Typing mode

- `EXPLICIT`: operators expose semantic input/output types, applicability predicates, exactness class, and verifier class. Search prunes incompatible compositions before execution.
- `INFERRED`: semantic type labels are hidden from the planner. The planner sees structural state descriptors and successful calibration transitions, then infers operator compatibility from observed transition signatures. Hard runtime safety guards still prevent malformed execution, but their semantic labels are not visible to search.
- `HYBRID`: hard representation/safety classes remain explicit while operator relevance and domain routing are inferred from transition history.

`EXPLICIT` is the primary capability test. `INFERRED` measures whether compatibility can be learned from operator behavior. `HYBRID` is the practical architecture if it preserves correctness while reducing search.

### 3.2 Composition mode

- `PRIMITIVE`: search may use only frozen primitive operators.
- `SYNTHESIZED`: search may additionally create macro-operators from already validated primitive subsequences. A macro has no new mathematical semantics; its contract is the composition of its constituents and it inherits their verifier chain.

This creates six scored modes:

```text
EXPLICIT/PRIMITIVE
EXPLICIT/SYNTHESIZED
INFERRED/PRIMITIVE
INFERRED/SYNTHESIZED
HYBRID/PRIMITIVE
HYBRID/SYNTHESIZED
```

## 4. Structured goal schema

Every goal is represented by a deterministic `GoalSpec` with:

```text
goal_id
family
inputs: named Artifact values
target: TargetSpec
constraints
allowed_numeric_tolerance
required_verifier_class
sealed_expected_result
sealed_reference_path
```

The solver-visible form excludes `sealed_expected_result` and `sealed_reference_path`. Those fields are loaded only by the scorer after a solver verdict has been finalized.

An `Artifact` contains:

```text
artifact_id
semantic_type
representation_class
value
exactness_class     # EXACT | SYMBOLIC | NUMERICAL
metadata
provenance
```

The planner state is a multiset of artifacts plus unresolved target obligations.

## 5. Operator contract

Every primitive operator is an `OperatorSpec` with:

```text
operator_id
input_types
output_type
representation_class
exactness_class
cost
applicability(state, bindings) -> Applicability
execute(state, bindings) -> Artifact | OperatorFailure
verify(input_artifacts, output_artifact) -> VerificationResult
structural_signature
```

Applicability verdicts are first-class:

```text
APPLICABLE
NOT_APPLICABLE
MISSING_PRECONDITION
INVALID_INPUT
NUMERICALLY_UNSAFE
```

No operator may silently coerce an inapplicable task into a numerical result.

## 6. Initial primitive registry

The first registry is derived from already established E-series mechanisms and existing MAPEOGEO proof-navigation/PCT primitives. It is intentionally broad enough to force mixed-domain search.

### Exact / finite primitives

1. `EXACT_MATRIX_RANK_Q`
2. `EXACT_NULLSPACE_Q`
3. `GF2_RANK`
4. `ZETA_TRANSFORM_BOOLEAN`
5. `MOBIUS_INVERT_BOOLEAN`
6. `CHAIN_RESIDUAL`
7. `CHAIN_MAP_CHECK`
8. `INCIDENCE_CORRUPTION_LOCALIZE`
9. `BARCODE_TO_BETTI`
10. `BETTI_TO_EULER`
11. `GRAPH_EULER_BETTI`
12. `GRAPH_DEGREE_SIGNATURE`
13. `GRAPH_LAPLACIAN_SIGNATURE`
14. `GRAPH_WL_SIGNATURE`
15. `FINITE_COUNTEREXAMPLE_SEARCH`

These correspond to mechanisms established in E5, E10-E18, E23, and E24.

### Symbolic primitives

16. `SYMBOLIC_SIMPLIFY`
17. `SYMBOLIC_IDENTITY_CHECK`
18. `NILPOTENCY_CHECK`
19. `POLYNOMIAL_INVARIANT_CHECK`
20. `LINEAR_INVARIANT_DISCOVERY`
21. `GAUSSIAN_EXPONENT_REWRITE`

These exercise E21-E22 and the source-bound symbolic equivalence work already present in MAPEOGEO.

### Numerical / geometric primitives

22. `NUMERIC_MATRIX_RANK`
23. `CONDITIONING_RISK_CHECK`
24. `SUPPORT_FUNCTION_SAMPLE`
25. `SUPPORT_SPECTRUM`
26. `CONVEXITY_CHECK`
27. `STEINER_OFFSET_PREDICT`
28. `MIXED_AREA_DEFECT`
29. `NUMERIC_RELATION_FIT`
30. `NUMERIC_RESIDUAL_VERIFY`

These exercise E4, E9, E17, E19, E20, and E22.

### Meta-operators

31. `SEPARATION_ESCALATE` — choose progressively richer invariants until candidates separate or the bank is exhausted.
32. `FALSIFY_CANDIDATE` — invoke an applicable bounded counterexample generator before promotion.
33. `VERIFY_CANDIDATE` — route to exact, symbolic, or numerical verifier according to the produced artifact.

## 7. Search architecture

Search is deterministic best-first search over planner states.

A state score is lexicographic rather than probabilistic:

1. number of unresolved target obligations;
2. accumulated operator cost;
3. number of unverified derived artifacts;
4. path length;
5. canonical operator-id sequence tie-break.

In `EXPLICIT` mode, only type-compatible and applicability-compatible operators are expanded.

In `INFERRED` mode, the planner builds transition compatibility from a calibration split. For each operator, it records structural input descriptors for successful applications and the resulting output descriptor. At solve time it ranks candidate operators by exact structural-signature agreement, then bounded Hamming/set distance. Runtime guards still reject invalid applications. No sealed goal result contributes to compatibility inference.

In `HYBRID` mode, broad representation classes (`EXACT`, `SYMBOLIC`, `NUMERICAL`, `GRAPH`, `CHAIN`, `GEOMETRY`) remain hard constraints, while operator ordering is inferred.

Search budgets are frozen per goal family. Exceeding a budget produces `NOT_ESTABLISHED`, not a guessed answer.

## 8. Macro synthesis

Macro synthesis is enabled only in `SYNTHESIZED` modes.

After calibration goals are solved, every successful primitive path of length 2-4 is considered. A sequence becomes a macro only if:

- it occurs in at least two distinct calibration goals;
- all constituent verifier steps passed;
- its endpoint input/output contract is stable across occurrences;
- replaying the macro reproduces primitive-path output exactly for exact/symbolic cases or within the frozen tolerance for numerical cases.

Macro score is based only on search-node reduction and path reuse. Macros may not inspect sealed answers and may not introduce a new executor. Execution expands back into constituent primitives for provenance.

## 9. Goal families

The campaign uses parameterized goal generators so success cannot come from hard-coded answers.

### G1 — Exact transform inversion

Given cumulative Boolean-lattice data, recover the atomic signal. Expected solution requires Möbius inversion and forward verification.

### G2 — Null-space / identifiability

Given an observation matrix and target uniqueness requirement, determine whether reconstruction is unique; if not, return the exact nullity and `NOT_ESTABLISHED` for unique recovery.

### G3 — Chain-map diagnosis

Given source/target boundary operators and a proposed map, determine whether it is a chain map; for corrupted incidence cases, localize the fault where possible.

### G4 — Persistence information-loss reasoning

Given barcodes and an equality/distinguishability target, search barcode -> Betti -> Euler paths and determine which representation still separates the objects.

### G5 — Adaptive graph discrimination

Given two finite graphs and a target `DISTINGUISH` or `NOT_ESTABLISHED`, start from Euler/Betti and escalate through degree, Laplacian, and WL signatures until separated or the frozen bank is exhausted.

### G6 — Exact-vs-numerical rank safety

Given an ill-conditioned rational matrix and rank target, use conditioning evidence to decide whether a floating result is sufficient or exact rank is required.

### G7 — Symbolic conserved invariant verification

Given a nilpotent generator, state vector, and candidate polynomial invariant, compose flow generation and symbolic invariant checking.

### G8 — Blind invariant recovery

Given multiple trajectories but not the invariant coefficients, use numerical relation fitting to produce a candidate and symbolic/numerical verification to accept or reject it.

### G9 — Convex parallel-body prediction

Given a polygon/body and offset distance, verify applicability and predict offset area using the Steiner relation. Nonconvex controls must return `NOT_APPLICABLE`.

### G10 — Harmonic support-spectrum inference

Given a sampled convex polygon support function, infer the rotational harmonic structure and verify the expected selection rule within numerical tolerance.

### G11 — Mixed-area equivalence discrimination

Given normalized convex bodies, determine whether a pair behaves as homothetic under the mixed-area defect test and verify the residual.

### G12 — Cross-representation identity

Given two symbolic forms of the Gaussian exponent or an EO/GEO correspondence, find a rewrite/verification path and return exact equivalence only if the identity checker closes.

## 10. Split design and anti-leakage

Each goal family has deterministic seeds partitioned into:

- `CALIBRATION`: used for inferred typing and macro synthesis;
- `VALIDATION`: used to select no parameters, only to ensure the implementation executes;
- `SEALED`: scored only after all operator contracts, search budgets, compatibility rules, and macro policy are frozen.

A sealed goal varies parameters and, for selected families, composition shape. The planner never receives the expected result or reference path.

To test composition rather than memorization, at least one sealed goal in each applicable family uses a primitive sequence not seen as an exact sequence in calibration.

## 11. Scoring

For every mode and goal family report:

- total goals;
- solved and correctly verified goals;
- wrong positive goals;
- `NOT_ESTABLISHED`;
- `NOT_APPLICABLE`;
- invalid/error;
- exact result accuracy;
- selective accuracy among positive answers;
- median expanded states;
- median primitive executions;
- median verified path length;
- counterexamples found before promotion;
- verifier failures;
- macro reuse and search reduction when enabled.

Primary scientific gates:

1. `EXPLICIT/PRIMITIVE` must solve correctly at least one sealed goal in every one of the 12 families.
2. `EXPLICIT/PRIMITIVE` must have zero wrong positives on adversarial/inapplicable controls.
3. At least six families must require a path length >= 2 on at least one sealed goal; direct one-operator lookup alone is insufficient.
4. At least three families must require operators from different exactness/representation classes within one successful path.
5. `INFERRED/PRIMITIVE` must achieve nonzero correct transfer in all three broad exactness classes (exact, symbolic, numerical) without increased wrong-positive rate over its explicit counterpart on controls.
6. `HYBRID/PRIMITIVE` must preserve zero control wrong positives and solve no fewer families than `INFERRED/PRIMITIVE`.
7. Macro synthesis is supported only if `SYNTHESIZED` reduces median expanded states or primitive executions without changing any verified answer or refusal.
8. Every positive answer must terminate in an independent verifier result; planner confidence alone is never sufficient.

Campaign-level status is not a single averaged score. Report four conclusions separately:

```text
GOAL_DIRECTED_SOLVING
INFERRED_COMPATIBILITY
MIXED_DOMAIN_COMPOSITION
MACRO_SYNTHESIS
```

Each is `SUPPORTED`, `NOT_SUPPORTED`, or `INCONCLUSIVE`.

## 12. Fail-closed semantics

Allowed final verdicts:

```text
PASS
NOT_ESTABLISHED
NOT_APPLICABLE
INVALID
ERROR
```

A numerical candidate may become `PASS` only if its verifier is within the frozen tolerance and no conditioning guard requires escalation to exact/symbolic evaluation.

A candidate defeated by bounded counterexample search is discarded and search continues. If no candidate survives before the search budget expires, return `NOT_ESTABLISHED`.

## 13. Evidence and provenance

The campaign records semantic evidence, not repository-byte trivia.

Every solve trace records:

```text
goal_id
mode
operator_path
expanded_state_count
primitive_execution_count
macro_ids
candidate_artifact
verifier_chain
falsification_events
final_verdict
```

Commit SHAs and code hashes may be recorded as provenance metadata, but byte-for-byte artifact equality is not a scientific pass/fail gate. Candidate reports are uploaded as CI artifacts for inspection.

## 14. Implementation boundary

Implementation lives in a new package:

```text
experiments/pct_goal_solver/
```

Existing E1-E31 modules remain unchanged except the CI workflow may add the new test/campaign commands. `main` remains read-only and is not merged or modified.

The new package must be independently testable and may import established branch utilities where they are generic. If an E-series experiment only exists as a monolithic test routine, the new package may re-express its already established mathematical operation as a focused operator implementation, with parity tests against the historical result where practical.

## 15. Expected interpretation

The decisive question is no longer whether the graph predicts semantic labels. It is whether a target can cause the system to choose and compose mathematical operations, reject invalid paths, synthesize intermediate reusable sequences, and independently verify the result.

If the explicit mixed-domain planner succeeds while inferred typing fails, the result is still important: MAPEOGEO has a functioning general operator-search architecture whose remaining bottleneck is routing/typing inference. If explicit planning itself fails, the failure localizes the problem to operator composability or search architecture rather than language understanding.
