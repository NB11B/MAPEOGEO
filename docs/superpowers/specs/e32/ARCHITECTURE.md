# E32 architecture

## 1. Question and layers

Primary question: can a decision expressed as a sequential formulation be transformed into a typed operator graph that exposes substantially more executable parallelism while preserving its declared observable contract, and can MAPEOGEO discover that factorization rather than merely schedule an already-parallel graph?

E32 separates four layers that must be measured independently:

1. **Decision factorization**: replace a composite judgment with typed atomic judgments over shared immutable state plus deterministic composition.
2. **Graph scheduling**: execute independent ready nodes concurrently without changing graph semantics.
3. **Graph optimization**: apply checked rewrites such as speculative fan-out and deterministic deduplication.
4. **Backend execution**: realize the graph through separate inference, batching, shared-state/prefix reuse or another explicitly implemented backend capability.

A vendor-API-only comparison would entangle these layers with a black box. A simulator-only comparison would establish no hardware speedup. The selected hybrid design separates deterministic compiler validity from model/backend performance. Neither plane substitutes for the other.

The source program is a declared decision contract, not arbitrary prose. Version 1 does not infer safe dependencies from a language model's explanation, translate unrestricted agent reasoning into an equivalent circuit, or claim to reproduce unpublished TypeSafe/Jev sampler internals.

## 2. Execution arms

| Arm | Definition | Purpose |
|---|---|---|
| S | Serial decision formulation executed in declared order with lazy guarded branches | Serial formulation reference |
| T | Conventional ready-queue scheduler on the exact supplied source graph after common validation/normalization only | Scheduling control |
| M | Human-authored typed factorization plus legal schedule, frozen before test and independently checked | Manual factorization reference |
| G | Automatic MAPEOGEO factorization and checked graph rewrites plus the same scheduler/runtime substrate as T | Proposed architecture |

S and T operate on the same source decision formulation. T may exploit only parallelism already exposed in that graph. M and G may operate on factored candidate graphs that must satisfy the same declared observable contract.

T and G share the same ready-set implementation, resource allocator, batch packing policy, executor, backend, resource limits, output validation, terminal verification and deterministic tie-breaking substrate. Common normalization may remove representation-neutral bookkeeping but may not expose new semantic independence. Any transformation that changes the dependency structure belongs to M/G and requires a checked receipt.

M is not assumed optimal. M must pass the same graph validator, independent receipt/contract checker where applicable, resource accounting and terminal verification as G. Human authors may use development data only and cannot inspect sealed test outcomes.

G must generate factorization/rewrite candidates from the solver-visible decision contract and a development-calibrated cost profile. It may not use case IDs, hidden answers, reference schedules, human M graphs, sealed labels or test timings as a lookup table. Node IDs are randomly relabelled in invariance tests. Compiler tie-breaking uses a relabel-invariant structural key, never raw node IDs.

Interpretation matrix:

- S ≈ T: the source representation itself is serial.
- M > T: factorization exposes useful parallelism.
- G ≈ M: the automatic system recovers roughly the useful human factorization.
- G > M on a registered family: G found an admissible factorization/optimization with additional measured benefit.
- G ≈ T while M > T: the factorization idea works but automatic discovery failed.

If G merely implements topological batching on an already-parallel graph, the conclusion is generic scheduler utility, not added EO/GEO or MAPEOGEO value.

## 3. Typed decision representation

A factored decision program maps shared immutable state S and a set of typed atomic questions to typed answer distributions or exact operator outputs, followed by deterministic composition:

F(S, {q_1, ..., q_n}) -> {a_1, ..., a_n} -> policy/composition -> action or refusal.

Atomic questions must declare exactly which state projection they read. Two questions are parallel-eligible only when neither consumes the other's output and all data, guard, lineage, effect and resource constraints permit concurrent execution.

Computational independence is not conditional statistical independence. Correlated query outputs remain correlated. Marginal probabilities must not be multiplied into a joint probability without a separately specified joint model.

Version 1 treats width and true dependency depth as distinct structural quantities. The central behavioral signature is that added width should become relatively cheap inside the hardware/backend parallel region while genuine dependency depth remains serial.

## 4. Runtime flow

Immutable state plus a typed source decision contract enters validation. S/T execute the source graph; M supplies a frozen checked factorization; G emits a candidate factored graph, schedule and rewrite receipts. An independent checker validates factorization/rewrite obligations before dispatch. The executor evaluates eligible nodes with bounded resources, validates each output, applies pure deterministic composition and emits an action or structured refusal. Terminal verification and reporting occur outside model inference.

Core units:

- IR validator: graph well-formedness, typed port bindings, effect and guard checks.
- Solver adapter: read-only translation of actual solver-visible decisions.
- Factorizer/compiler: bounded search over registered decompositions and legal rewrites with deterministic tie breaking.
- Receipt checker: independently checks every factorization/rewrite obligation against source contracts.
- Scheduler: shared T/G resource-aware readiness, batching and deterministic result association.
- Backends: exact deterministic functions; local causal-model option scoring; optional explicitly tested shared-state/prefix reuse.
- Policy/composition: fixed arithmetic, constraints, utility and abstention outside the model.
- Audit/report: complete traces, rejected candidates, timing, structure and claim gates.

The receipt checker must not call the compiler's factorization or rewrite-acceptance function. Common serialization utilities are allowed; shared semantic checking logic must be disclosed.

## 5. Dependency and control semantics

A DATA edge means the downstream node needs an upstream value. A GUARD edge controls whether a node is selected. An EFFECT_ORDER edge preserves observable side-effect ordering. A SCHEDULE edge is a representation-level serialization constraint and may be removed only through a registered checked transformation; it cannot masquerade as a DATA edge.

A finite DAG is required. Cycles, missing producers and ambiguous ports fail validation. Loops require explicit bounded unrolling with iteration IDs; unbounded loops are unsupported. An upstream-dependent query is evaluated only after its actual inputs arrive unless a registered speculative rule proves that it can be evaluated from already available inputs without changing the selected observable contract.

## 6. Legal transformations

### R0: typed factorization

Replace a registered composite decision node/subgraph with a set of typed atomic judgments and pure deterministic composition only when a declared FactorizationContract identifies:

- the source observable contract;
- the atomic question/operator contracts and state projections;
- the deterministic composition/policy function;
- the admissible input domain;
- the required lineage mapping;
- the equivalence or acceptance obligation used by the independent checker.

R0 is not a license to decompose arbitrary prose or to claim semantic equivalence from intuition. Human-authored M factorizations and automatic G factorizations are checked against the same registered obligations. A new decomposition family requires a new registered contract before sealed evaluation.

### R1: remove artificial scheduling edges

Remove a declared SCHEDULE edge only after proving that no DATA, GUARD, guard-safety, lineage, effect or source-observable obligation is removed. Because R1 changes exposed dependency structure, it is not available to T in the primary attribution comparison; a separate T+R1 diagnostic may be reported.

### R2: partition a ready antichain into backend-supported batches

Retain per-item state/query identity and output association. Shared state ingestion is measured only if the backend actually implements reuse; padded batching is not shared encoding.

R2 is scheduler/runtime behavior common to T, M and G whenever the same ready antichain exists. It is not by itself evidence of MAPEOGEO-specific value.

### R3: speculative fan-out

Hoist a guarded query speculatively only if it is pure, total on the hoisted input domain, reads available immutable inputs and has no external actions. Its discarded output has no decision effect. Cost, allocation, failures and power/energy telemetry when available are still recorded. A discarded branch's inference failure is recorded without failing a successful selected branch; if later selected, that failure must cause refusal.

### R4: deterministic structural deduplication

Eliminate duplicate pure deterministic nodes only when operator ID/version, canonical input bindings/provenance, scope, output contract and all semantic preconditions are identical. R4 is structural at compile time; it does not depend on runtime value digests. Provenance retains all original use sites.

Runtime value memoization, if later added, is a separate explicitly named mechanism keyed by actual input digests and disabled across cases in the primary campaign. No stochastic-query deduplication exists in version 1.

No associativity, commutativity, EO/GEO conversion or numeric reassociation is presumed. Such rewrites require separately registered executable or formal obligations and a new spec version. Changing prompt bytes, option order, model precision, inference method, utility, policy or tolerance is not a scheduling rewrite.

## 7. Backend levels

E32 reports backend capability levels separately:

- B0: separate ordinary inference/scoring for each eligible question.
- B1: batched independent scoring with no claim of shared-state reuse.
- B2: explicitly implemented and tested shared-state/prefix reuse.
- B3: a custom parallel option/sampler architecture, only if directly implemented and validated in a later version.

Version 1 requires B0 and B1 for local-model testing when practical; B2 is optional and must be capability-gated. B3 is outside the initial claim. A speedup from B1/B2 on a causal LM does not establish equivalence to an unpublished vendor sampler.

## 8. Equivalence and cost

Deterministic observational equivalence means identical selected action, selected output values required by the observable contract, selected failure/refusal behavior and lineage obligations. Wall time and discarded speculative trace size may differ. Exact rational fixtures require exact equality. Numeric contracts specify tolerances before execution.

For a stochastic/model backend, a legal graph transformation does not by itself guarantee identical samples or distributions across batch shapes. Deterministic scoring is preferred; measured distribution drift is a separate acceptance gate. Per-node RNG streams must be keyed by case/node identity if stochastic backends are later added.

Define separately:

- W: executed node/work-unit count, including discarded speculation;
- C_hat: locked predicted weighted cost, the sum of frozen development-estimated node/backend costs;
- L_hat: locked predicted weighted span on the true dependency graph;
- T_measured: measured end-to-end wall/device timing and resource counters.

For P identical processors, max(C_hat/P, L_hat) is a lower bound under the declared predicted-work model, not a latency promise.

Compiler objective: minimize development-predicted end-to-end latency subject to semantic validity, memory/resource limits and C_hat_G <= 2 * C_hat_S for every primary case. Search budget is 1,000 candidate factorization/rewrite steps per graph, with relabel-invariant deterministic tie breaking. Preserve the valid original graph if no admissible improvement is found. Runtime breaches are failures, not silently widened budgets. Forecast errors are reported by comparing predicted and measured costs.

Report both cold one-shot latency, including factorization/compilation/checking, and hot/reused-plan latency. A compile cache key includes graph/decision-contract hash, state schema, factorization-contract registry, operator registry, backend profile and policy/observable-contract hashes. It may not depend on case-specific output values unless the plan is explicitly state-specialized and then cannot be reused across states. Cross-case output caching is disabled in the primary campaign.

## 9. Trust and safety

Models provide typed scores/distributions only; they cannot authorize operators, directly emit an executable ACTION in the local-model backend, or execute tools. User text is data, not executable code. Validate finite probabilities, option coverage and state bindings. No NaN repair, guessed defaults or silent renormalization of malformed external distributions.

No real-world actions occur. DECIDE/policy nodes produce recorded action labels only. Timeout, OOM, unsupported backend capability, stale cache, invalid receipt and malformed output have distinct status codes. Resource cleanup occurs after each trial. Retries are disabled in primary timings; a diagnostic retry is recorded separately and cannot replace a failed trial.
