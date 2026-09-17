# E32 preregistration

Status: prospective design; no results exist in this package. This document fixes the decision rules. An implementation must additionally freeze fixture bytes, model files, resource budgets and environment before running sealed tests.

## Hypotheses and attribution

H1: legal graph transformations preserve deterministic observable behavior.
H2: G reduces dependency depth/work tradeoffs on eligible graphs relative to S.
H3: G realizes end-to-end local-model latency improvement without meaningful quality loss.
H4: G adds measurable benefit beyond the ordinary scheduler T.
H5: speculative fan-out has a bounded operating region; it is not universally beneficial.

Report these separately. H1/H2 success cannot establish H3. Beating S but tying T supports scheduling utility, not MAPEOGEO-specific compiler value. M is a frozen reference, not an oracle guaranteed to be optimal.

## Corpus and splits

Six families: independent queries; guarded routing; true multi-hop data dependencies; shared subexpressions; correlated judgments with utility/abstention; and CPU-bound exact operator compositions.

For each family generate 180 distinct cases: 60 development, 20 validation, 100 sealed test, for 1,080 cases and 600 test cases total. Deterministic seeds: 11, 22, 33, with equal allocation across seeds. Widths 1, 4, 16, 64 and dependency depths 1, 2, 4, 8 are balanced within each family's valid combinations; impossible combinations are excluded by a frozen generator rule, never after results.

Split by source/template group before surface rendering, not by individual paraphrase. Group canonical hashes must be disjoint across splits. Fixture manifests record each source/template, seed, family, graph, ground truth and split. Class/action frequencies and branch-selection frequencies are published before test runs.

At least 120 of the 600 test cases must adapt actual pinned goal-solver contracts, spread across at least three available operator families. Re-express verified properties as typed decision questions and compute truth with an independent exact oracle where possible. Historical outcomes are not treated as universal ground truth. If insufficient valid adapters exist, the corpus gate fails; do not fill the quota with renamed synthetic cases. Report synthetic and source-bound strata separately.

Model tasks use sealed natural-language renderings of exact fixture facts with distractors and contradictions assigned by generator rules. This is a controlled synthetic reasoning benchmark, not a general language-understanding benchmark.

Model/local hardware calibration may use development data only. M schedules and G cost profiles are frozen before validation. Validation may reject the proposed configuration; any subsequent adjustment increments the campaign version and regenerates an untouched validation/test partition. No test-driven tuning is allowed.

## Execution matrix

Run S, M, G and T against identical test cases on both planes. Deterministic plane executes real exact functions, not injected sleeps. A simulated-latency model may be reported separately as SIMULATION and never supplies a hardware speedup gate.

Local-model plane requires one completely pinned model at minimum. Users select weights already available locally; model identity is bound in the run lock before testing. A run with no model is valid as architecture-only and marks H3/H4-model NOT_RUN. Additional models are separate replications, not pooled silently.

Primary hardware settings: concurrency/batch-item cap 8, maximum 4,096 input-plus-option tokens per item, one inference process, no cross-case output cache. Reject rather than truncate oversized test inputs. Secondary resource sweeps use caps 1, 2, 4 and 16, reported descriptively. Reserve a maximum 80% of preflight free device memory; model loading exceeding that budget blocks the run. CPU thread counts and numerical-library threads are fixed in the lock.

Per arm/case: 3 warmups and 10 measured repeats. Rotate the four arm orders using a balanced Latin square across case/repeat blocks. Inference weights remain loaded; record model load time separately. Primary end-to-end timings include graph compile/check, dispatch, state projection, inference, composition, synchronization and terminal verification. For each measured cold-plan trial clear only the plan cache, not weights. Secondary hot-plan timing reuses a checked plan and reports amortization separately.

Use GPU synchronization around timing boundaries. Python thread concurrency is not evidence of simultaneous GPU execution. Record batching, stream policy, CPU overhead and peak memory. Any thermal throttling or background load observation is recorded; do not selectively delete slow trials.

## Predeclared gates

| Gate | Requirement |
|---|---|
| V0 provenance | Complete pins, clean implementation tree, source/test separation and all artifacts verified |
| V1 typing/safety | 100% required validator and adversarial tests pass |
| V2 deterministic semantics | 100% selected outputs, refusals and lineage obligations agree across arms on all exact test cases |
| V3 leakage/invariance | No forbidden oracle access; node relabelling and independent-query permutation preserve results |
| V4 resource/accounting | Complete trials or explicit failures; no silent OOM recovery, skipped cases or omitted speculative work |
| H2 structural | On eligible width >= 4, depth <= 2 cases, median G/S dependency-stage ratio <= 0.5 |
| H3 quality | Upper 95% bound on G minus S error rate <= 0.01; upper bound on Brier increase <= 0.01 |
| H3 latency | Lower 95% bound on geometric-mean S/G cold-plan latency ratio > 1.10 on the same eligible stratum |
| H4 incremental value | Lower 95% bound on T/G cold-plan ratio > 1.05 on guarded/shared-subexpression eligible cases, with H3 quality met |
| Speculation budget | Executed speculative work <= 2 times S work for every case under the locked cost model |
| Model invariance | At least 99% selected-action agreement and max per-option probability drift <= 1e-4 for scheduling-only batch permutations |

H2 dependency-stage ratio refers to S's imposed serial stages versus G's valid schedule stages; additionally report unchanged true-DAG depth so removing artificial serialization is not represented as reducing genuine dependencies.

An engine-validity failure makes affected scientific hypotheses INCONCLUSIVE/INVALID_RUN, not supported. A valid run missing a numerical gate yields NOT_SUPPORTED in narrative with gate FAIL. A missing model yields NOT_RUN, not failure of the mathematical architecture. Distribution invariance failures prohibit exact-equivalence language even if aggregate accuracy passes.

## Statistical protocol

Primary correctness uses independent exact labels; report accuracy, all-class confusion matrix, action agreement and selective accuracy versus coverage. Multiclass Brier score is sum of squared errors over classes; binary NOUL uses its two-class distribution. Report NLL with evaluation-only clipping at 1e-12 and ten equal-width-bin ECE descriptively. Do not infer calibration from peaked distributions.

Aggregate each case/arm's ten repeats by median before statistical testing. Bootstrap paired cases, stratified by family and clustered by template, with 10,000 resamples and seed 20260917. Report 95% percentile intervals. Use geometric means for latency ratios and paired differences for errors/Brier. Repeat-level observations are not independent samples.

H3 requires both quality and latency gates; H4 is tested only after H3. Do not pool exploratory resource sweeps into the primary test. Report all family-specific effects, CPU/GPU results separately, raw denominators and failures. Timeouts count as incorrect decisions and latency at least their deadline; aggregate speedup claims are blocked if any arm has unresolved timeouts/OOM, with censored values retained in reports.

## Mandatory falsification controls

- Delete a true data dependency: checker rejects.
- Hoist an input-dependent or effectful query: checker rejects.
- Inject a cycle, stale registry or forged receipt: fail closed.
- Add/drop/permutate unrelated questions: compare probability and action invariance.
- Correlate queries: show marginal products are not used as a joint model.
- Width 1 and deep chains: retain serial dependencies; no guaranteed speedup.
- Expensive irrelevant branches: speculation cap prevents uncontrolled work.
- Batch cap 1: separates graph rewrite effects from concurrency.
- Random legal scheduler: tests whether G's cost guidance matters.
- G without R3 and G without R4: frozen ablations isolate speculation/deduplication.
- Deliberately overconfident wrong scores: calibration and utility diagnostics detect them.
- Always-abstain policy: report coverage and utility, never celebrate selective accuracy alone.

Utility fixture: correct action +1, wrong action -1, abstain 0; sealed labels determine realized reward. Primary policy acts when the highest option probability is strictly greater than 0.5, otherwise abstains. Report utility and coverage for every arm. No information-gathering claim is made: active sensing is outside version 1.

## Claim limits

Even a complete success supports only the tested graphs, rewrite rules, model, hardware and resource region. It does not establish an unpublished vendor sampler, calibrated reasoning in general, general proof synthesis, universal EO/GEO equivalence or automatic parallelization of arbitrary language chains.
