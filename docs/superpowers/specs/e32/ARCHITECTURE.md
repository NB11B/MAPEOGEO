# E32 architecture

## 1. Question and alternatives

Primary question: can a compiler transform a decision workflow into a shallower executable graph while preserving its declared observable behavior and realizing a measured local benefit?

A vendor-API-only comparison would entangle the architecture with a black box. A simulator-only comparison would establish no hardware speedup. The selected hybrid design separates deterministic compiler validity from model/backend performance. Neither plane substitutes for the other.

The source graph is a decision program, not arbitrary prose. Version 1 does not infer safe dependencies from a language model's explanation and does not translate unrestricted agent reasoning into an equivalent circuit.

## 2. Arms

| Arm | Definition | Purpose |
|---|---|---|
| S | Stable topological execution, one ready node at a time, lazy guarded branches | Serial reference |
| M | Human-authored legal schedule and optional speculative graph, frozen before test | Manual factorization |
| G | Automatic typed compiler with checked rewrite receipts | Proposed architecture |
| T | Ordinary ready-queue topological scheduler on the source graph, no semantic rewrites | Necessary attribution control |

S is intentionally serialized, not a claim about the best possible serial agent. T prevents attributing ordinary concurrency to MAPEOGEO. All arms share source state, query text, option order, executor, resource limits, output validation and decision policy.

G must generate schedules from the solver-visible graph and a development-calibrated cost profile. It may not use case IDs, hidden answers, reference schedules or test timings as a lookup table. Node IDs are randomly relabelled in invariance tests.

If G merely implements topological batching, the conclusion is generic scheduler equivalence, not added EO/GEO value. Calling a new scheduler MAPEOGEO does not establish a mathematical integration result.

## 3. Runtime flow

Immutable state plus typed source graph enters validation. The compiler emits a candidate graph, schedule and rewrite receipts. An independent checker validates receipts before dispatch. The executor evaluates eligible nodes with bounded resources, validates each output, applies pure deterministic composition and emits an action or a structured refusal. Terminal verification and reporting occur outside model inference.

Core units:

- IR validator: graph well-formedness, typed port bindings, effect and guard checks.
- Solver adapter: read-only translation of actual solver-visible decisions.
- Compiler: bounded search over legal rewrites, with deterministic tie breaking.
- Receipt checker: independently checks every rewrite against source contracts.
- Scheduler: resource-aware readiness, batching and deterministic result association.
- Backends: exact deterministic functions; local causal-model option scoring.
- Policy: fixed arithmetic, constraints, utility and abstention, outside the model.
- Audit/report: complete traces, rejected candidates, timing and claim gates.

The receipt checker must not call the compiler's rewrite-acceptance function. Common serialization utilities are allowed; shared semantic checking logic must be disclosed.

## 4. Dependency and probability semantics

A data edge means the downstream node needs an upstream value. A guard edge controls whether a node is selected. An effect-order edge preserves observable side-effect ordering. Scheduling edges are distinct, explicitly removable serialization constraints and cannot masquerade as data edges.

Two nodes can run together only when all needed inputs are available and effects/resources permit it. This is computational independence, not conditional statistical independence. Correlated query outputs remain correlated. Marginal probabilities must not be multiplied into a joint probability without a separately specified joint model.

A finite DAG is required. Cycles, missing producers and ambiguous ports fail validation. Loops require explicit bounded unrolling with iteration IDs; unbounded loops are unsupported. An upstream-dependent query is evaluated only after its actual inputs arrive.

## 5. Legal transformations

R1: remove artificial scheduling edges after proving no data, guard-safety, lineage or effect constraint is removed.

R2: partition a ready antichain into backend-supported batches, retaining per-item state/query identity and output association. Shared state ingestion is measured only if the backend actually implements reuse; padded batching is not shared encoding.

R3: hoist a guarded query speculatively only if it is pure, total on the hoisted input domain, reads available immutable inputs and has no external actions. Its discarded output has no decision effect. Cost, allocation, failures and power consumption are still recorded. A discarded branch's inference failure is recorded without failing a successful selected branch; if later selected, that failure must cause refusal.

R4: eliminate duplicate pure deterministic nodes only when operator, version, input digests, scope and output contract are identical. No stochastic-query deduplication in version 1. Provenance retains both use sites.

No associativity, commutativity, EO/GEO conversion or numeric reassociation is presumed. Such rewrites require separately registered executable or formal obligations and a new spec version. Changing the prompt, option order, model precision, inference method, utility or tolerance is not a scheduling rewrite.

## 6. Equivalence and cost

Deterministic observational equivalence means identical selected action, selected output values, selected failure/refusal behavior and lineage obligations. Wall time and speculative trace size may differ. Exact rational fixtures require exact equality. Numeric contracts specify tolerances before execution.

For a stochastic/model backend, a legal graph transformation does not by itself guarantee identical samples or distributions across batch shapes. Deterministic scoring is preferred; measured distribution drift is a separate acceptance gate. Per-node RNG streams must be keyed by case/node identity when stochastic backends are later added.

Let W be total executed work, including discarded speculation, and D the longest true dependency path in node count. Weighted span L uses frozen per-node cost estimates; resource-limited makespan is distinct. For P identical processors, max(W/P,L) is a lower bound under the declared work model, not a latency promise.

Compiler objective: minimize development-predicted end-to-end latency subject to semantic validity, memory/resource limits and W <= 2 times the lazy reference's predicted work. Search budget is 1,000 candidate rewrites per graph, deterministic lexical tie breaking; preserve the valid original graph if no improvement is found. Runtime breaches are failures, not silently widened budgets. Forecast errors are reported.

Report both cold one-shot latency (compilation included) and amortized reused-plan latency. A compile cache key includes graph, state schema, operator registry, backend profile and contract hashes. Cross-case output caching is disabled in the primary campaign.

## 7. Trust and safety

Models provide scores only; they cannot authorize operators or execute tools. User text is data, not executable code. Validate finite probabilities, option coverage and state bindings. No NaN repair, guessed defaults or silent renormalization of malformed external distributions.

No real-world actions occur. Decisions are recorded labels. Timeout, OOM, unsupported backend capability, stale cache, invalid receipt and malformed output have distinct status codes. Resource cleanup occurs after each trial. Retries are disabled in primary timings; a diagnostic retry is recorded separately and cannot replace a failed trial.
