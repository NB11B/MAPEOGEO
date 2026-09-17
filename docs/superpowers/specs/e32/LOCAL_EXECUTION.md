# Local execution and implementation handoff

## Available now: retrieve specifications

In an existing NB11B/MAPEOGEO checkout, preserve any local changes and use:

```bash
git fetch origin agent/e32-typed-parallel-decision-graph-spec
git worktree add ../MAPEOGEO-e32-spec origin/agent/e32-typed-parallel-decision-graph-spec
```

Choose an unused worktree directory. These commands retrieve documentation; they do not run E32. Do not reset or overwrite an existing checkout.

## Required implementation surface

Future modules under experiments/typed_parallel_decision_graph/:

contracts.py, graph.py, factorization.py, rewrites.py, receipt_checker.py, scheduler.py, solver_adapter.py, deterministic_backend.py, local_model_backend.py, direct_readout_backend.py, readout_contracts.py, fixtures.py, metrics.py, campaign.py, cli.py and test_*.py.

The CPU deterministic profile must work offline without model libraries. Use Python 3.11 as the initial compatibility target; produce tested exact dependency locks per supported platform. Local-model dependencies belong to a separate optional lock. Do not claim a dependency combination is validated until installation and preflight pass on that environment.

Target environments: Windows PowerShell and Linux shell; CPU required, CUDA optional. Record actual GPU/VRAM rather than assuming capacity from its model name. The user's RTX 5070 Laptop GPU is a target for local validation, not hardware available or tested in this specification session.

No model download is implicit. The user supplies a local weights directory and records its licensing/source. Preflight computes weight/tokenizer/readout hashes and checks exact dependency versions, tokenization boundaries, option-score normalization, deterministic repeatability, isolated-vs-batched drift, claimed backend capability level, option-key association and available memory. Incompatible CUDA/library combinations stop with actionable diagnostics.

## Implementation phases

E32 implementation is one system but should be built in this dependency order:

1. normative contracts, validators and canonical serialization;
2. source decision graph execution for S/T;
3. independent checker and FactorizationContract registry;
4. human M factorization fixtures;
5. automatic G R0 factorization search;
6. R1-R4 rewrite layer;
7. deterministic campaign/metrics;
8. local-model B0 backend;
9. B1 batching backend;
10. optional B2 shared-state/prefix-reuse backend only if actually implemented and preflight-verifiable;
11. optional B3 direct-readout backend under a fully sealed ReadoutContract;
12. option-order, list-expansion and sibling-isolation characterization harness.

B4 decision-specialized post-training/calibration is not part of the v1.2 primary implementation.

## Future command contract: NOT IMPLEMENTED in this branch

Every command must have --help, return structured JSON diagnostics and avoid network access by default.

CPU deterministic sequence:

```bash
python -m experiments.typed_parallel_decision_graph.cli preflight --profile cpu --output runs/e32/preflight.json
python -m experiments.typed_parallel_decision_graph.cli seal --profile cpu --preflight runs/e32/preflight.json --output runs/e32/run-lock.json
python -m experiments.typed_parallel_decision_graph.cli run --lock runs/e32/run-lock.json --plane deterministic --arms S T M G --output runs/e32/deterministic
python -m experiments.typed_parallel_decision_graph.cli verify --run runs/e32/deterministic
```

Local-model sequence, with the model path supplied interactively by preflight so no path placeholder is executable:

```bash
python -m experiments.typed_parallel_decision_graph.cli preflight --profile local-model --choose-model-directory --backend-levels B0 B1 --output runs/e32/model-preflight.json
python -m experiments.typed_parallel_decision_graph.cli seal --profile local-model --preflight runs/e32/model-preflight.json --output runs/e32/model-lock.json
python -m experiments.typed_parallel_decision_graph.cli run --lock runs/e32/model-lock.json --plane local-model --arms S T M G --backend-levels B0 B1 --output runs/e32/model
python -m experiments.typed_parallel_decision_graph.cli verify --run runs/e32/model
python -m experiments.typed_parallel_decision_graph.cli characterize --run runs/e32/model --question-isolation --option-order --list-expansion
python -m experiments.typed_parallel_decision_graph.cli report --runs runs/e32/deterministic runs/e32/model --output runs/e32/report
```

If B2 is genuinely implemented and preflight validates shared-state/prefix reuse, add B2 explicitly. If B3 is implemented, preflight must also receive and validate a complete ReadoutContract before B3 can be requested. The CLI must reject a backend level not supported by the sealed BackendDescriptor.

Each run command executes the complete frozen matrix, controls and ablations without repeated user intervention. Resumption requires matching lock hashes and appends immutable trial records; it never replaces failed trials. Existing output directories fail unless --resume is explicitly selected. No automatic uploads.

Exit codes: 0 complete and valid (scientific support may still be absent), 2 invalid configuration/provenance, 3 incomplete execution, 4 engine-validity failure. Reports must distinguish completion from supported hypotheses. A separate --require-support flag may make failed scientific gates nonzero but is not the default.

## Preflight and sealing order

The sealing sequence is normative and resolves backend/run-lock circularity:

1. preflight probes the live backend/environment and writes BackendDescriptor plus environment/resource observations;
2. if B3 is requested, preflight also validates ReadoutContract, readout parameters, extraction positions and the absence of answer-string scoring in the B3 path;
3. the user/runtime selects supported backend levels and resource budget;
4. seal hashes BackendDescriptor, CostProfile, ResourceBudget, fixtures, factorization registry, policy, diagnostic metric contracts, readout contract where applicable and environment into RunLock;
5. prepare(run_lock, expected_descriptor_hash) reprobes/validates the live backend before execution and refuses drift.

Seal generation must refuse absent pins, missing fixtures, missing FactorizationContracts, missing local model files for model runs, unsupported requested capabilities, dirty implementation trees for confirmatory runs and unresolved environment drift. It must never insert fake model/readout hashes or reuse this documentation's base commit as the implementation commit.

## Artifact layout

- run-lock.json: immutable inputs/environment/limits.
- backend-descriptor.json: probed backend identity and capability level.
- readout-contract.json: B3 extraction/projection/option-encoding contract when B3 is present.
- diagnostic-metrics.json: sealed deterministic diagnostic metric definitions.
- cost-profile.json: frozen development-calibrated predicted cost model.
- resource-budget.json: concurrency, batch, token, memory and timeout limits.
- factorization-registry.json: exact R0 contracts and checker obligations.
- fixtures-manifest.json and split-manifest.json: exact case identities and isolation.
- factorization.jsonl: every M/G source-pattern match, candidate, receipt and rejection.
- compilation.jsonl: all R1-R4 candidates, rejected rewrites and checked receipts.
- trials.jsonl: complete per-trial records, including errors.
- answers.jsonl: option scores/probabilities and decision outputs.
- question-isolation.jsonl: sibling-order/add-drop/shared-state characterization.
- option-set-characterization.jsonl: option-order/list-expansion aligned-key results.
- structure.json: width/depth/stage/span metrics for source and factored graphs.
- metrics.json: per-case and aggregate efficacy/performance metrics with intervals.
- controls.json: every falsification control and ablation outcome.
- hashes.json: raw SHA-256 inventory of all other artifacts.
- REPORT.md: separate deterministic/model/backend-level findings and claim limits.

Timing fields are excluded from semantic reproducibility hashes but included in raw artifact hashes. Never expect wall-clock measurements to reproduce bit-for-bit. Exact fixtures, source/factored graph hashes, selected deterministic outputs, registry bindings, factorization receipts, rewrite checks, readout contract hashes and option-set query hashes must reproduce exactly.

## Required scheduler parity

T and G must instantiate the same scheduler implementation, ready-queue semantics, resource allocator, batch-packing policy and executor. Arm-specific behavior is expressed by the graph supplied to that scheduler, not by separate scheduling code paths.

A scheduler parity test must feed T and G an identical graph and assert identical dispatch groups, resource reservations and outputs under the same backend/resource profile. Any divergence invalidates primary T/G attribution until explained and fixed in a new campaign version.

## Required R0 tests

Before any accepting R0 implementation:

- reject an unregistered source-pattern substitution;
- reject an admissible pattern outside its domain contract;
- reject a candidate that changes selected observable outputs;
- reject missing/incorrect lineage mapping;
- reject a composition operator/version mismatch;
- reject a factorization requiring sealed oracle fields;
- accept independently constructed positive fixtures for each registered FactorizationContract;
- verify M and G candidates are checked through the same obligation engine.

R0 search tests must also demonstrate that raw node-ID relabeling cannot change candidate selection except for graph-isomorphic serialization differences.

## Required question and option semantics tests

Cross-question isolation:

- evaluate a target QUERY alone and with independent siblings in multiple sibling orders;
- add/drop an unrelated sibling and enforce the preregistered drift gate;
- put a disambiguating fact only inside a sibling question and verify it is not injected into the target's declared state/query bytes;
- move the same fact into the target's declared shared-state projection and verify the query/state hash changes appropriately;
- preserve exact case/node/query association under every batch permutation.

Listwise option handling:

- option_set_hash and query_hash must change when CHOICE/SCORE options are reordered, added, removed or relabelled;
- key-probability association must remain exact after every permutation;
- option-order/list-expansion probes must realign results by canonical key before computing deltas;
- tests must not assert probability invariance across different option sets;
- pairwise log-odds are omitted/null when mathematically undefined rather than repaired.

Confidence diagnostics:

- CHOICE uniform-baseline confidence matches the exact registered formula;
- NOUL emits no separate normative confidence;
- SCORE confidence is rejected unless a matching DiagnosticMetricContract is sealed;
- no diagnostic confidence field may alter the primary policy action.

## Required backend tests

B0:

- deterministic repeatability under the sealed scoring policy;
- exact ordered-option association correctness;
- no ACTION emission from the backend.

B1:

- same per-question query/state identity as B0;
- sibling-question batch permutations satisfy the preregistered drift gate;
- capability does not claim shared-state reuse;
- batch cap 1 collapses to the B0 execution shape apart from measured framework overhead.

B2, if implemented:

- demonstrate actual reduced state/prefix reprocessing relative to B1 on controlled fixtures;
- detect and refuse stale or incompatible prefix/state caches;
- prove cache keys bind model/tokenizer/prompt/state/query contracts and case scope;
- never infer B2 support solely from using a batch dimension or KV cache somewhere in the stack.

B3, if implemented:

- ReadoutContract hashes the exact base model/tokenizer, extraction position/rule, source tensor contract, projection, option encoding, normalization and all trainable readout parameters;
- B3 path performs no teacher-forced answer-string continuation scoring;
- prefill/readout/projection timing is measured separately where instrumentation permits;
- identical inputs under deterministic settings reproduce the same readout distribution;
- ordered option/key association is exact;
- malformed or stale readout hashes fail closed;
- B3 quality is compared against the best available teacher-forced backend under the preregistered noninferiority gates;
- option-count scaling reports projection cost separately from base-model prefill cost.

## Implementation acceptance order

1. Write and run rejection tests for all normative contracts, hidden oracle access and invalid DAGs.
2. Implement exact S/T execution and independent terminal verification.
3. Implement scheduler parity tests proving identical T/G scheduling behavior on identical graphs.
4. Implement FactorizationContract checking and positive/negative R0 fixtures.
5. Implement frozen M factorizations and G R0 search without sealed-test access.
6. Implement R1-R4 with mutation tests and the T+R1 diagnostic.
7. Verify all deterministic controls and width/depth accounting before allowing model efficacy reporting.
8. Add B0 teacher-forced local scoring and instrumentation.
9. Add B1 batching and validate sibling-question isolated-vs-batched invariance.
10. Add option-order/list-expansion characterization and typed diagnostic confidence metrics.
11. Add B2 only if shared-state reuse is real and measurable.
12. Add B3 only under a complete ReadoutContract with no answer-string scoring path.
13. Freeze the complete implementation, data, factorization/readout/diagnostic contracts, costs and environment; run the full matrix once.
14. Publish raw failures and bounded conclusions before deciding whether a new campaign version is justified.

These are construction dependencies, not separate moving-goalpost scientific campaigns. There is one frozen confirmatory evaluation campaign per spec/implementation/fixture seal. A material fix after validation/test exposure requires a new version and untouched holdout.

Existing solver and historical tests must also run in implementation validation. Their exact invocation and fixture hydration must follow the pinned repository instructions; do not claim the prior integration suite has been rerun merely by writing or updating this specification.
