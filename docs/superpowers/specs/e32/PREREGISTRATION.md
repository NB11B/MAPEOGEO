# E32 preregistration

Status: prospective design; no results exist in this package. Specification version: 1.2. This document fixes the primary decision rules. An implementation must additionally freeze fixture bytes, factorization contracts, model files, resource budgets, backend capability level, diagnostic metrics and environment before running sealed tests.

## 1. Hypotheses and attribution

H1: registered typed factorizations and legal graph rewrites preserve deterministic observable behavior on their declared admissible domains.

H2: typed factorization exposes executable width without falsely reducing true dependency depth.

H3: human factorization M provides measurable structural and/or latency benefit beyond conventional scheduling T on factorization-eligible decisions.

H4: automatic G recovers a substantial fraction of the benefit of M, and any incremental G>M benefit is reported separately rather than assumed.

H5: on an ordinary local causal model, backend batching/shared-state mechanisms can convert exposed width into measured latency/resource benefit without meaningful quality loss; this does not establish a proprietary non-autoregressive sampler.

H6: speculative fan-out has a bounded operating region; it is not universally beneficial.

H7: when a B3 backend is explicitly implemented, direct typed readout can be evaluated separately from teacher-forced answer-string scoring for quality, latency and option-count scaling without claiming reconstruction of Jev or any unpublished sampler.

Report all hypotheses separately. H1/H2 success cannot establish model latency. T beating S supports ordinary scheduling. M beating T supports representation/factorization value. G approximating M supports automatic factorization. G beating T but not M still supports useful automation without establishing superiority to human decomposition. Any backend speedup is conditional on the tested model/hardware/capability level.

## 2. Structural signature under test

Let n denote eligible parallel width and d denote true dependency depth after semantic dependencies are fixed. E32 tests the qualitative signature that, inside the tested hardware/backend parallel region, added width is substantially cheaper than added true depth.

Report per-family surfaces for measured latency/resource cost as a function of width and depth rather than reducing the experiment to one aggregate speedup. The campaign must separately report:

- source-graph exposed width;
- factored-graph exposed width;
- source true dependency depth;
- factored true dependency depth;
- schedule stages under each arm;
- predicted weighted span;
- measured latency.

A reduction in imposed serial schedule stages must never be described as a reduction in genuine dependency depth unless DATA/GUARD/EFFECT semantics actually permit that conclusion.

## 3. Question-isolation and listwise-option model

The model under test has two different scopes of interaction.

Across sibling atomic questions over shared immutable state, undeclared cross-question conditioning is prohibited by the E32 interface. Independent question order and unrelated sibling presence are therefore tested for invariance within the registered model-drift tolerance.

Within one CHOICE or SCORE question, the complete ordered option set is a single listwise decision object. Reordering, adding or deleting options changes the query contract. E32 therefore does not preregister probability invariance across different option sets.

Mandatory characterization probes include:

1. **Sibling-isolation probe**: evaluate a target question alone; with an unrelated sibling; with a sibling containing a disambiguating fact unavailable to the target; and with that same fact moved into the target's declared shared-state projection. The first three conditions test undeclared sibling influence; the fourth is an intentional semantic-input change and is expected to be allowed to move the target distribution.
2. **Question-order probe**: permute independent sibling question order while preserving each individual query contract and key association.
3. **Option-order probe**: permute the ordered option list for a CHOICE/SCORE question, re-hash the query, realign common keys after inference and report probability/selection changes.
4. **List-expansion probe**: add one or more registered alternatives to an existing CHOICE/SCORE option set, then report changes on common keys including pairwise log-odds where defined.

Option-order and list-expansion results are characterization measurements, not semantic-validity failures. Incorrect answer-to-key association is always a validity failure.

## 4. Corpus and pattern families

Seven primary families reproduce the programming patterns under study:

1. **Parallel question battery**: independent typed judgments over one immutable state.
2. **Speculative fan-out**: guarded downstream judgments that may be evaluated early when legal.
3. **Hierarchical classification**: parallel width within each level, serial dependency across levels.
4. **Shared-state scoring**: many judgments over a common large state projection, used to measure state reprocessing versus reuse.
5. **Code composition**: atomic judgments combined through deterministic arithmetic/logic rather than model-side multi-hop prose.
6. **Shared subexpressions**: exact deterministic graph fragments with legal structural deduplication opportunities.
7. **True dependency chains**: negative-control workflows in which downstream inputs genuinely depend on upstream outputs.

CPU-bound exact operator compositions are embedded across families where applicable rather than treated as a separate claim category.

For each family generate 180 distinct cases: 60 development, 20 validation and 100 sealed test, for 1,260 total cases and 700 sealed test cases.

Deterministic seeds are 11, 22 and 33. Across the complete 180-case family, allocate exactly 60 cases per seed. Within each split, width/depth/seed cells are near-balanced with count differences at most one wherever the generator's validity constraints permit. Any indivisible remainder is assigned deterministically by canonical cell order fixed in the generator before case materialization. Impossible width/depth combinations are excluded by a frozen generator rule, never after results.

Primary widths are 1, 4, 16 and 64. Primary true dependency depths are 1, 2, 4 and 8. Family-specific valid combinations are fixed before fixture generation.

Split by source/template group before surface rendering, not by individual paraphrase. Group canonical hashes must be disjoint across splits. Fixture manifests record each source/template, seed, family, source graph, factorization eligibility, registered factorization contracts, ground truth and split. Class/action frequencies, branch-selection frequencies and eligible-width/depth distributions are published before sealed runs.

At least 140 of the 700 sealed test cases must adapt actual pinned goal-solver contracts, spread across at least three available operator families. At least 120 of those 140 source-bound cases must have an independently computable exact oracle and therefore contribute to efficacy gates. Re-express verified properties as typed decision questions and compute truth with an independent exact oracle where possible. Historical outcomes are not treated as universal ground truth. If these quotas cannot be met without renaming synthetic cases, the corpus gate fails.

Report synthetic and source-bound strata separately.

Model tasks use sealed natural-language renderings of exact fixture facts with distractors and contradictions assigned by generator rules. This is a controlled synthetic reasoning benchmark, not a general language-understanding benchmark.

Model/local hardware calibration may use development data only. M factorizations, G factorization/cost profiles, backend configuration, readout contracts and diagnostic metric contracts are frozen before validation. Validation may reject the proposed configuration. Any material adjustment after validation access increments the campaign version and regenerates untouched validation/test partitions. No test-driven tuning is allowed.

## 5. Arm construction

S executes the serial source formulation in declared order with lazy guards.

T executes the same source graph using the conventional ready-queue scheduler. T and G use the same scheduler/runtime substrate. T cannot apply R0, R1, R3 or R4 in the primary comparison. R2 batching is common runtime behavior whenever a ready antichain already exists. A separate T+R1 diagnostic may be run but cannot replace primary T.

M uses human-authored factorization under registered FactorizationContracts. M is frozen using development data only and must pass the same validation/checking/resource rules as G.

G automatically selects registered R0 factorizations and legal R1-R4 rewrites using solver-visible information and the frozen development-calibrated cost profile. G cannot inspect M's sealed candidate graph as a reference solution.

The primary attribution comparisons are:

- T/S for ordinary scheduling;
- M/T for factorization value;
- G/T for automatic factorization value;
- G/M for automatic-versus-human factorization quality;
- G ablations for rewrite-specific contributions.

## 6. Backend execution matrix

Run S, T, M and G against identical sealed cases on the deterministic plane.

Local-model plane requires one completely pinned model at minimum for any real-model claim. Users select weights already available locally; model identity is bound in the run lock before validation/test access. A run with no model is valid as architecture-only and marks all local-model hypotheses NOT_RUN.

Backend levels are reported separately:

- B0: isolated teacher-forced scoring for eligible atomic judgments.
- B1: batched teacher-forced scoring with no shared-state-reuse claim.
- B2: explicitly implemented and preflight-validated shared-state/prefix reuse.
- B3: direct typed readout under a sealed ReadoutContract; no answer-string continuation scoring.
- B4: decision-specialized post-training/calibration; outside the v1.2 primary campaign.

Primary local-model comparison requires B0 and B1 when both are supported by the pinned runtime. B2 and B3 are optional capability-gated replications. B3 may enter a confirmatory v1.2 run only if the complete ReadoutContract and any trained readout parameters are frozen before validation access. B4 requires a later campaign version.

A simulated-latency model may be reported separately as SIMULATION and never supplies a hardware speedup gate.

Primary hardware settings: concurrency/batch-item cap 8, maximum 4,096 input-plus-option tokens per item, one inference process, no cross-case output cache. Reject rather than truncate oversized sealed inputs. Secondary resource sweeps use caps 1, 2, 4 and 16 and are reported descriptively. Reserve a maximum 80% of preflight free device memory; model loading exceeding that budget blocks the run. CPU thread counts and numerical-library threads are fixed in the lock.

Per arm/case/backend-level: 3 warmups and 10 measured repeats.

Arm order is assigned over the complete case x repeat matrix using repeated balanced Latin-square blocks. Because ten repeats are not divisible by four, exact within-case equality is not required; over the complete primary matrix, each arm occupies each ordinal position with count difference at most one, using deterministic canonical remainder assignment fixed before execution.

Inference weights remain loaded; record model load time separately. Primary end-to-end cold-plan timings include factorization where applicable, compile/check, dispatch, state projection, inference/readout, composition, synchronization and terminal verification. For each measured cold-plan trial clear only plan/factorization caches, not weights. Secondary hot-plan timing reuses a checked plan and reports amortization separately.

Use GPU synchronization around timing boundaries. Python thread concurrency is not evidence of simultaneous GPU execution. Record batching, stream policy, CPU overhead, state-token reprocessing, model input tokens processed, continuation tokens scored, direct-readout evaluations, peak memory and device time where available. Any thermal throttling or background-load observation is recorded; do not selectively delete slow trials.

## 7. Predeclared validity gates

| Gate | Requirement |
|---|---|
| V0 provenance | Complete pins, clean implementation tree, source/test separation and all artifacts verified |
| V1 typing/safety | 100% required validator and adversarial tests pass |
| V2 factorization semantics | 100% deterministic selected outputs, required selected values, refusals and lineage obligations agree with the source observable contract on exact cases |
| V3 leakage/invariance | No forbidden oracle/reference access; raw node relabelling preserves selected candidate modulo isomorphism; independent sibling-question permutation/add-drop probes remain within registered drift tolerance |
| V4 resource/accounting | Complete trials or explicit failures; no silent OOM recovery, skipped cases or omitted speculative work |
| V5 source-bound corpus | >=140 source-bound sealed cases, >=120 with independent exact oracle, across >=3 operator families |
| V6 backend capability | Claimed B0/B1/B2/B3 capability demonstrated in preflight; no padded batching reported as shared-state reuse; no B3 claim without valid ReadoutContract |
| V7 option-set characterization | All required option-order and list-expansion probes execute with exact key association and complete characterization records; no false invariance assumption is applied across different option sets |

An engine-validity failure makes affected scientific hypotheses INCONCLUSIVE/INVALID_RUN, not supported.

## 8. Predeclared scientific gates

H2 structural gate, factorization-eligible width >=4 cases:

- M/T median schedule-stage ratio <= 0.5 or G/T median schedule-stage ratio <= 0.5 for the corresponding factorization claim;
- true semantic dependency depth is reported separately and must not be falsely reduced.

H3 human factorization gate:

- lower endpoint of the two-sided 95% paired-bootstrap interval for geometric-mean T/M cold-plan latency ratio > 1.05 on the registered factorization-eligible stratum, OR a registered deterministic work/span gate showing structural benefit where wall-clock timing is not meaningful;
- deterministic validity gates must pass.

H4 automatic factorization gate:

- lower endpoint of the two-sided 95% paired-bootstrap interval for geometric-mean T/G cold-plan latency ratio > 1.05 on the same registered eligible stratum;
- and G reaches at least 80% of M's log-speedup benefit on that stratum, where benefit_fraction = log(T/G) / log(T/M), evaluated only when T/M > 1 and reported with its bootstrap interval;
- quality/semantic gates must pass.

G>M is not required. If observed, report it as an additional result with the same paired interval rather than a preregistered success condition.

Local-model quality gate:

- upper endpoint of the two-sided 95% paired-bootstrap interval on G minus S error rate <= 0.01;
- upper endpoint of the two-sided 95% paired-bootstrap interval on G minus S multiclass/binary Brier score <= 0.01;
- analogous M and T comparisons are reported.

Local-model latency gate at B1:

- lower endpoint of the two-sided 95% paired-bootstrap interval for geometric-mean B0/B1 latency ratio > 1.10 on independent-ready width >=4 atomic-question groups;
- and lower endpoint for T/G cold-plan latency ratio > 1.05 on registered factorization-eligible cases when testing automatic-factorization realization.

B2 shared-state gate, only if B2 is implemented:

- state tokens reprocessed per case are strictly lower than B1 on shared-state scoring cases;
- report paired latency and memory effects without converting B2 into a vendor-sampler equivalence claim.

B3 direct-readout gate, only if B3 is implemented and sealed before validation:

- upper endpoint of the two-sided 95% paired-bootstrap interval on B3 minus the best available teacher-forced backend error rate <= 0.01;
- upper endpoint of the corresponding Brier-score increase <= 0.01;
- report paired latency ratios against B0/B1/B2 and option-count scaling separately;
- no minimum latency speedup is required for scientific validity, but any speedup claim must use the same paired interval protocol and include all readout/projection overhead.

Speculation budget:

- total predicted weighted cost C_hat_G <= 2 * C_hat_S for every primary case;
- report actual W_G/W_S, token, memory and measured-time ratios separately.

Model invariance across sibling-question scheduling:

- at least 99% selected-action agreement and maximum per-option probability drift <= 1e-4 for permutations/add-drop of unrelated sibling questions under deterministic-scoring/readout settings. Failure prohibits exact cross-question-isolation language for that backend.

There is deliberately no corresponding probability-invariance gate across different option sets. Option-order/list-expansion sensitivity is reported as characterization.

A valid run missing a numerical scientific gate yields gate FAIL and a narrative NOT_SUPPORTED statement. A missing model yields NOT_RUN, not failure of the mathematical architecture.

## 9. Width-depth and option-set analysis

For every family and backend level, report the full valid width x depth grid rather than only pooled aggregates.

Primary structural quantities include:

- median latency and interval by width/depth cell;
- marginal change with width at fixed depth;
- marginal change with depth at fixed width;
- schedule-stage count;
- true dependency depth;
- W and C_hat;
- state tokens reprocessed;
- batch count and mean batch occupancy.

The preregistered qualitative signature is supported only when increased width shows sublinear measured growth over at least two successive width increases within a fixed shallow-depth stratum while increasing true depth continues to increase serial stages. This signature is descriptive unless a later version preregisters a parametric scaling law.

For CHOICE/SCORE characterization, report by backend:

- probability deltas on common keys after option-order permutation;
- selected-key change rate;
- pairwise log-odds deltas on common key pairs where probabilities are nonzero;
- effects of adding 1, 2 and, where cardinality permits, larger distractor alternatives;
- latency and memory as option count increases at fixed state/question length;
- exact key-association correctness.

For B3, option-count scaling additionally reports direct-readout projection cost separately from base-model prefill cost.

## 10. Statistical protocol

Primary correctness uses independent exact labels. Report accuracy, all-class confusion matrix, action agreement and selective accuracy versus coverage. Multiclass Brier score is the sum of squared errors over classes; binary NOUL uses its two-class distribution. Report NLL with evaluation-only clipping at 1e-12 and ten equal-width-bin ECE descriptively. Do not infer calibration from peaked distributions or from diagnostic confidence metrics.

Aggregate each case/arm/backend-level's ten repeats by median before statistical testing. Bootstrap paired cases, stratified by family and clustered by template, with 10,000 resamples and seed 20260917. Report two-sided 95% percentile intervals. Whenever a gate says lower or upper 95% bound, it means the relevant endpoint of this two-sided 95% interval unless explicitly stated otherwise.

Use geometric means for latency ratios and paired differences for errors/Brier. Repeat-level observations are not independent samples.

Do not pool exploratory resource sweeps into the primary test. Report all family-specific effects, CPU/GPU results and backend levels separately, with raw denominators and failures. Timeouts count as incorrect decisions and latency at least their deadline. Aggregate speedup claims are blocked if any compared arm has unresolved timeouts/OOM; censored values remain in reports.

## 11. Mandatory falsification and characterization controls

- Delete a true DATA dependency: checker rejects.
- Present an R0 factorization outside its registered source pattern/domain: checker rejects.
- Replace a registered deterministic composition with an unregistered semantically different composition: checker rejects.
- Hoist an input-dependent or effectful query: checker rejects.
- Inject a cycle, stale registry or forged receipt: fail closed.
- Rename every node ID: G selects the same candidate modulo graph isomorphism and produces the same action/cost prediction.
- Permute independent sibling-question order: target query hashes remain unchanged and aligned results satisfy the sibling invariance gate.
- Add/drop an unrelated sibling question: the target question satisfies the sibling invariance gate.
- Put a disambiguating fact only in a sibling question: the target must not receive it through undeclared state or hidden question-to-question conditioning.
- Move that fact into the target's declared shared state: this is an intentional semantic-input change and may change the target distribution.
- Reorder CHOICE/SCORE options: create a new query hash, preserve key association exactly and record listwise sensitivity without imposing probability invariance.
- Expand/reduce a CHOICE/SCORE option set: create a new query hash and report common-key/log-odds changes.
- Correlate sibling questions: show marginal products are not used as a joint model.
- Width 1 and deep chains: retain serial dependencies; no guaranteed speedup.
- Expensive irrelevant branches: speculation cap prevents uncontrolled work.
- Batch cap 1: separates graph-factorization benefit from runtime concurrency.
- Random legal scheduler on the same graph: tests whether cost guidance matters.
- T+R1 diagnostic: measures how much apparent G gain is attributable solely to schedule-edge removal.
- G without R0: isolates graph rewrites from factorization.
- G without R3 and G without R4: isolates speculation and deterministic deduplication.
- B1 with deliberately disabled batching: must collapse toward B0 execution shape within measurement noise.
- Claimed B2 with reuse disabled: preflight must refuse B2 capability.
- Claimed B3 with answer-string scoring still active: preflight must refuse B3 capability.
- B3 with corrupted readout-position/projection hash: fail closed.
- Deliberately overconfident wrong scores: calibration/utility diagnostics detect them.
- Always-abstain policy: report coverage and utility; never celebrate selective accuracy alone.

Utility fixture: correct action +1, wrong action -1, abstain 0; sealed labels determine realized reward. Primary policy behavior is exactly the PolicyContract described in CONTRACTS.md. Report utility and coverage for every arm. No information-gathering claim is made: active sensing is outside version 1.2.

## 12. Claim limits

Even a complete success supports only the tested decision-contract families, registered R0 factorization contracts, rewrite rules, model, backend capability level, hardware and resource region.

It may support claims about typed atomic decision factorization, exposed executable parallelism, cross-question isolation under the tested probes, listwise option sensitivity as an observed property, conventional batching/shared-state reuse when directly measured, direct typed readout when directly implemented, and MAPEOGEO's ability to recover useful registered factorizations.

It does not establish an unpublished vendor sampler, RLCD calibration, universal TypeSafe/Jev architectural equivalence, general proof synthesis, universal EO/GEO equivalence, automatic decomposition of arbitrary language chains, or a proprietary non-autoregressive inference architecture unless such a mechanism is directly implemented and separately validated.
