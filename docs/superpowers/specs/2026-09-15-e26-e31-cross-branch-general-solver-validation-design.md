# E26–E31 Cross-Branch General Solver Validation Design

**Status:** APPROVED / FROZEN DESIGN  
**Date:** 2026-09-15  
**Experimental branch:** `agent/pct-computational-architecture`  
**Solver baseline SHA:** `6c9333ed3ec48a298ad943a74e72a01fa1ffcd78`  
**Knowledge baseline SHA:** `fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f`  
**Knowledge baseline stage:** MAPEOGEO v0.15.1 confirmatory replay

## 1. Governing question

The purpose of E26–E31 is not to test whether the latest E25 trust machinery can merely traverse a larger graph. The purpose is to test whether the accumulated E-series mechanism behaves like a general relational solver when exposed to a substantially larger, independently expanded mathematical corpus, and to use the E-series in the reverse direction to audit the independently developed implementation on `main`.

The solver mechanism under test is the sequence established across E1–E25:

```text
observe
  -> separate
  -> reconstruct
  -> infer
  -> falsify
  -> verify
  -> record closure
```

The campaign is strictly cross-branch and read-only with respect to `main`. No merge, cherry-pick, semantic graph promotion, or mutation of the knowledge baseline is permitted.

## 2. Frozen baselines and independence

Two exact historical states are inputs to the campaign:

```text
B_solver    = agent/pct-computational-architecture@6c9333ed3ec48a298ad943a74e72a01fa1ffcd78
B_knowledge = main@fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f
```

The experimental branch may advance only by adding E26–E31 harness code, tests, reports, and frozen evidence. The existing E1–E25J implementation modules and their frozen evidence are immutable test inputs for this campaign. If a defect is found that requires changing those prior modules, the campaign must stop and record baseline invalidation before a new solver baseline is preregistered.

The `main` checkout is never imported into the experimental branch tree. CI or the local runner must obtain it as a separate checkout pinned to `B_knowledge`. Main-side PCT code is invoked only through a subprocess boundary with an explicit JSON input/output protocol so identically named packages cannot be accidentally mixed in-process.

Any future movement of either named branch does not alter this experiment. A new commit requires a new campaign baseline rather than silently changing the answer corpus.

## 3. Knowledge corpus under test

The frozen v0.15.1 confirmatory corpus reports:

- 416 source declarations
- 109 canonical mathematical objects
- 53 two-source supported canonical objects
- 33 three-source supported canonical objects
- 9 four-source supported canonical objects
- 444 typed cross-source semantic bridges
- 1,616 graph edges
- 257 EO candidates
- 27 GEO candidates
- 159 DUAL candidates
- 7 inherited `FORMAL_LINKED` objects
- four mathematical domains:
  - Linear Algebra
  - Applied Linear Algebra
  - Convex Analysis & Optimization
  - Differential Calculus & Real Analysis

The formal-link distinction is binding: `FORMAL_LINKED` is not treated as `KERNEL_VERIFIED` unless independent kernel evidence is explicitly present.

The typed semantic vocabulary must remain distinct throughout the campaign:

```text
SAME_SEMANTICS
SCOPED_OVERLAP
RELATED_TO
```

No experiment may collapse these labels into one generic equivalence class.

## 4. Scientific hypotheses

### H0 — no general solver transfer

The E-series mechanisms do not materially generalize beyond their original bounded experiments. On the expanded corpus, richer relational machinery does not improve held-out recovery over simpler graph baselines, cannot expose minimal sufficient evidence, or produces unjustified positive answers under ambiguity.

### H1 — relational solver transfer

A preregistered composition of the frozen E-series mechanisms can recover or correctly refuse held-out mathematical relationships across the expanded graph, can identify bounded minimal evidence sets and null spaces, can generate and attack candidate structural rules, and can preserve fail-closed provenance and closure.

H1 requires both positive capability and calibrated refusal. A system that answers more cases by fabricating certainty does not satisfy H1.

### H2 — independent main-side implementation survives E-series adversaries

The independently developed PCT implementation present in `B_knowledge` reproduces the relevant invariants and failure detection behavior established by the frozen E-series tests when those tests are replayed through an adapter boundary.

A missing capability is recorded as a coverage gap or `NOT_APPLICABLE`; it is not converted into a scientific failure unless the main implementation explicitly claims that capability.

## 5. Claim boundary

A positive campaign result would establish solver-like capability on the frozen MAPEOGEO corpus and cross-validation between two independently developed branches. It would not establish:

- a universal mathematics solver
- autonomous theorem proving
- universal injectivity of any transform
- universal minimal probe counts
- correctness outside the frozen corpus
- that every absent graph edge is mathematically false
- that a mined structural rule is a theorem
- that `FORMAL_LINKED` implies kernel verification
- permission to merge the branches

## 6. Answer-key isolation

The frozen `main` graph and alignment artifacts are used in two roles that must remain separated:

1. **Solver-visible sanitized corpus** — direct target answers are removed before inference.
2. **Verifier-only sealed answer key** — the complete frozen data is retained for scoring after solver output is committed in memory and hashed.

The solver process receives only the sanitized graph, the preregistered solver recipe, and explicitly allowed metadata. It must not read alignment manifests, acceptance manifests, full graph copies, or answer-key files containing the held-out relation.

For every case the harness records:

```text
target_case_id
sanitized_input_sha256
solver_recipe_sha256
solver_output_sha256
sealed_answer_sha256
knowledge_baseline_sha
solver_baseline_sha
```

The inference result is generated before the answer is loaded for scoring.

Absent edges are never automatically treated as negative mathematical facts. Negative controls must be either explicitly grounded or synthetic corruptions whose falsity follows from a known frozen binding.

## 7. Frozen solver recipe

E26–E31 evaluates an orchestration of already established E-series ideas. The campaign may add adapters and orchestration, but may not tune solver rules after inspecting sealed answers.

The solver recipe is:

1. Construct a finite candidate universe for the target task.
2. Compute discrete relational probes from the sanitized graph, including typed local paths, endpoint/node types, representation profiles, source identities, dependency orientation, multipath signatures, and available cross-view evidence.
3. Build the exact ambiguity set: candidates still consistent with the observed probe vector and all preregistered fail-closed rules.
4. Use bounded exact probe-selection search to find a smallest separating subset within the frozen candidate probe bank when a unique solution exists.
5. Search for contradictory evidence and counterexamples before emitting a positive relation.
6. Emit a positive class only when one candidate remains consistent. Otherwise return `NOT_ESTABLISHED`, `NOT_APPLICABLE`, `INVALID`, or `ERROR` as appropriate.
7. Bind every scored result to E25-style provenance and closure receipts.

No probabilistic confidence score can override ambiguity. Candidate-set cardinality and exact evidence support are the uncertainty representation.

## 8. Baselines

Held-out solver performance is compared on exactly the same cases against increasingly informative controls:

- **B0 — prior-only:** relation frequency within the visible training corpus.
- **B1 — endpoint metadata:** endpoint/source/type metadata without relational paths.
- **B2 — one-hop signature:** local degree and one-hop typed-neighbor signatures.
- **B3 — path heuristic:** shortest typed-path and shared-neighbor evidence without exact probe minimization, null-space accounting, or falsification.
- **B4 — full E-series solver:** the frozen solver recipe above.

B0–B3 are comparison baselines only. A positive solver claim requires evidence that the full relational pipeline contributes beyond the strongest applicable simpler baseline.

## 9. E26 — Cross-Branch Corpus Binding

### Objective

Establish the exact, auditable test substrate without exercising solver claims.

### Required outputs

E26 must:

- verify both frozen commit SHAs
- verify that the two states remain separate histories rather than a test-time merge
- locate the frozen v0.15.1 graph and relevant manifests
- compute fresh SHA-256 digests of every graph/alignment artifact used
- enumerate node and edge type vocabularies
- reproduce graph headline counts directly from the graph rather than trusting reports
- enumerate canonical objects, source declarations, domains, representation profiles, typed semantic bridges, dependencies, source bindings, and formal-link records
- identify which records have enough evidence for each later test family
- bind all later cases to stable IDs

If report/manifest counts disagree with direct graph counts, E26 records the discrepancy and uses direct graph reconstruction as the execution substrate. It does not silently repair either branch.

### Verdict

E26 is `PASS` only if the pinned corpus is deterministic and internally loadable. Semantic discrepancies may coexist with an E26 `PASS` if they are explicitly recorded for later audit rather than hidden.

## 10. E27 — Sealed Held-Out Relational Recovery

E27 is the primary general-solver test.

### R1 — exhaustive leave-one-edge-out recovery

For every eligible typed cross-source semantic bridge in the frozen corpus, remove that direct target edge while preserving the rest of the graph. Predict the exact relation class:

```text
SAME_SEMANTICS
SCOPED_OVERLAP
RELATED_TO
NOT_ESTABLISHED
```

The full corpus reports 444 cross-source bridges; E26 determines the exact eligible count from the graph.

### R2 — canonical-cluster holdout

Group bridge records by their sealed canonical object. Remove all semantic bridge labels belonging to one canonical cluster at a time while preserving non-answer structural evidence that would legitimately exist for a new object.

This prevents trivial recovery from redundant sibling edges and tests transfer of relational rules to a previously unlabeled canonical cluster.

### R3 — leave-one-domain-out transfer

Hold out semantic labels for one mathematical domain and derive the relation rules only from the other domains. Repeat for each eligible domain.

The newest `Differential Calculus & Real Analysis` domain is a particularly important confirmatory transfer test because it was added independently on `main` after the original E-series campaign.

### R4 — refusal and corruption controls

Construct deterministic synthetic controls by corrupting one endpoint, source binding, scope, or relation type of known answer-key records. Also create deliberately underdetermined cases by removing separating evidence.

The expected response is refusal or ambiguity, not a guessed positive relation.

### Metrics

For every tier E27 reports:

- total cases
- answered cases
- `NOT_ESTABLISHED` cases
- exact relation-type accuracy
- selective accuracy among answered cases
- false-certainty count
- per-class confusion matrix
- ambiguity-set size distribution
- paired case-by-case comparison against B0–B3
- results by domain, relation type, source multiplicity, and representation richness

### Solver-signal criterion

A positive E27 solver signal requires all of the following:

1. zero false certainty on the preregistered R4 corruption/underdetermination controls
2. B4 strictly exceeds the strongest simpler baseline on exact recovery in at least the canonical-cluster holdout (R2) and domain-transfer holdout (R3)
3. any increased answer coverage does not come from a higher wrong-positive count
4. every positive result has a reproducible evidence trace

If these conditions are not met, H1 is not supported regardless of R1 performance.

## 11. E28 — Minimal Evidence, Redundancy, and Null-Space Audit

E28 applies the E2/E3/E10/E11/E15 principles to real graph problems successfully addressed in E27.

For each eligible correctly recovered R2/R3 target:

1. Freeze the finite evidence/probe bank used by the solver.
2. Find a smallest subset that still uniquely identifies the same target relation within that bank.
3. Certify minimality by exact bounded search or exact integer optimization.
4. Measure erasure tolerance: how many evidence elements may be removed before uniqueness is lost.
5. Remove each critical item in turn and recompute the ambiguity set.
6. Report the resulting null space / unresolved candidate set rather than forcing an answer.

The claim is explicitly bounded to the frozen probe bank. E28 does not claim globally minimal mathematical evidence over all possible representations.

A successful E28 case must reproduce the original answer from its certified subset and become ambiguous or change classification when all separating information is removed.

## 12. E29 — Structural Rule Discovery and Falsification

E29 tests the E21–E23 transition from analysis to search.

### Discovery

Using solver-visible training structure only, enumerate low-complexity candidate relational rules composed of at most three typed probes/path predicates. A candidate rule must have multiple independent supporting instances; singleton rules are not eligible.

Example rule shape:

```text
probe_A AND probe_B -> candidate_relation_type
```

The implementation may discover different rule content; rule syntax and search depth are frozen before sealed evaluation.

### Falsification

For every candidate rule:

- search the visible corpus exhaustively for counterexamples within its declared scope
- test source, domain, and representation-scope perturbations
- retain surviving rules only as `CANDIDATE_SURVIVED_VISIBLE_SEARCH`
- evaluate survivors against sealed E27 holdouts after the candidate set is frozen

Any discovered counterexample defeats the corresponding universal form immediately. A rule that survives bounded search remains a candidate; it is never promoted to theorem status by E29 alone.

### Outputs

E29 reports:

- candidate rules generated
- supporting-instance counts
- counterexamples found
- scope restrictions required to rescue overbroad candidates
- held-out transfer outcomes
- surviving-but-unproven candidates

## 13. E30 — Independent Main-PCT Adversarial Replay

E30 tests the independently developed `mapeogeo/pct` implementation from `B_knowledge` using adversarial cases established on the solver branch.

Main-side code is executed in a subprocess whose `PYTHONPATH` contains only the frozen main checkout plus its dependencies. Results return through JSON. No branch implementation module is imported into that process.

The replay matrix covers, where semantically applicable:

- **E5:** direct chain-map corruption and chain-map-valid semantic adversaries
- **E9:** applicability refusal for theorem hypotheses
- **E11:** explicit probe null spaces
- **E14:** barcode -> Betti -> Euler information-loss controls
- **E16:** internally valid but cross-view incorrect EO/GEO correspondences
- **E17:** exact algebra versus floating rank heuristics
- **E18:** incidence corruption detection and localization
- **E23:** bounded counterexample controls
- **E24:** graph-atlas relational discrimination and subdivision-map controls

Each test is classified before execution as:

```text
DIRECT_REPLAY
ADAPTER_REQUIRED
NOT_APPLICABLE
CAPABILITY_NOT_EXPOSED
```

Only `DIRECT_REPLAY` and semantics-preserving `ADAPTER_REQUIRED` cases are scored as pass/fail. `CAPABILITY_NOT_EXPOSED` is a coverage finding, not automatically a failure.

No adapter may implement the capability being tested on behalf of `main`; adapters may only translate data representations and call an existing main-side operation.

## 14. E31 — Bidirectional Solver/Verifier Closure

E31 binds the two directions into one auditable evidence system without merging code.

### Direction A

```text
branch E-series solver output
    -> frozen main answer key / source / executable / formal evidence
```

### Direction B

```text
main PCT behavior
    -> frozen branch E-series adversarial oracle
```

Every scored case receives immutable evidence receipts for:

- C0 identity and frozen baseline binding
- C1 source/certificate/answer-key binding
- C2 executable solver or replay result
- C3/C4 only where chain/homology contracts are actually applicable
- C5a exact result/morphism agreement when meaningful
- C5b provenance-bound correspondence
- strict C5 eligibility policy

`NOT_APPLICABLE` C3/C4 layers remain explicit and are never rewritten as `PASS`.

The E25I/J lifecycle semantics remain binding. If either frozen branch SHA or a required artifact digest changes, affected E31 receipts become stale. They do not silently update or reactivate.

## 15. Fail-closed verdict vocabulary

All E26–E31 components use the existing vocabulary:

```text
PASS
FAIL
NOT_APPLICABLE
NOT_ESTABLISHED
INVALID
ERROR
INCONCLUSIVE
```

`NOT_ESTABLISHED` is a valid scientific result and is preferred over unsupported positive inference.

## 16. Validity gates

The campaign is invalid unless all applicable gates pass:

- **V26.0 — Frozen refs:** both exact baseline SHAs resolve.
- **V26.1 — Artifact identity:** all used graph/alignment artifacts have frozen digests.
- **V26.2 — No merge contamination:** no test reads a merged working tree.
- **V26.3 — Corpus reconstruction:** direct graph counts and vocabularies are reproducible.
- **V27.0 — Answer isolation:** solver-visible inputs contain no direct target answer.
- **V27.1 — Determinism:** identical sanitized inputs produce identical outputs and evidence traces.
- **V27.2 — Typed semantics:** semantic relation classes remain distinct.
- **V27.3 — Refusal integrity:** ambiguity cannot be converted to positive output by fallback heuristics.
- **V28.0 — Bounded-minimum honesty:** all minimality claims identify their frozen candidate bank.
- **V29.0 — Discovery separation:** candidate generation occurs before sealed-answer evaluation.
- **V29.1 — Counterexample precedence:** one valid counterexample defeats an overbroad rule.
- **V30.0 — Runtime isolation:** main PCT executes in its own pinned subprocess environment.
- **V30.1 — Adapter honesty:** adapters translate only; they do not supply missing mathematical functionality.
- **V31.0 — Receipt completeness:** every scored result has identity, input, output, answer, and baseline bindings.
- **V31.1 — No semantic mutation:** the campaign cannot modify `main` or auto-promote graph relations.
- **V31.2 — Lifecycle replay:** derived closure is reproducible from immutable receipts.

## 17. Frozen evidence products

Implementation should produce deterministic, regenerable evidence at paths equivalent to:

```text
evidence/pct_e26_cross_branch_manifest.json
evidence/pct_e27_heldout_relational_recovery.json
evidence/pct_e28_minimal_evidence_nullspace.json
evidence/pct_e29_rule_discovery_falsification.json
evidence/pct_e30_main_pct_adversarial_replay.json
evidence/pct_e31_bidirectional_closure.json
```

and a final report:

```text
docs/PCT_E26_E31_CROSS_BRANCH_SOLVER_VALIDATION_REPORT.md
```

Generated candidate evidence must be produced outside committed `evidence/` first. Frozen evidence is committed only after fresh generation has been inspected and byte-equivalence regression checks are in place.

## 18. CI and mutation policy

The E26–E31 workflow runs from `agent/pct-computational-architecture` only.

CI must:

1. check out the experimental branch normally
2. obtain `B_solver` and `B_knowledge` as separate read-only checkouts/directories
3. verify their exact SHAs
4. regenerate the cross-branch corpus manifest
5. run E27–E31 deterministically
6. upload generated evidence separately
7. compare generated evidence with frozen branch evidence
8. run the complete prior PCT regression suite

The workflow receives read-only repository permissions in normal operation. It must never push to `main`, never merge refs, and never create semantic graph mutations.

## 19. Interpretation rules

The campaign reports three independent conclusions rather than one aggregate score:

1. **Solver transfer:** whether E-series relational solving generalizes on sealed larger-corpus tasks.
2. **Main implementation replay:** which E-series adversarial properties the independently developed main PCT implementation reproduces.
3. **Bidirectional trust:** whether both directions can be bound into deterministic, revocable E25-style evidence closure.

A failure in one conclusion does not get averaged away by success in another.

The governing rule is:

```text
A general solver must know both when structure determines an answer
and when the available structure leaves a genuine ambiguity.
```
