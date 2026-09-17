# E32 normative contracts

All records include schema_version = "e32.v1". Unknown fields are rejected in sealed normative records. Diagnostic metadata uses an explicitly separate map. IDs are nonempty UTF-8 strings unique within their declared namespace. Hashes are lowercase 64-character SHA-256 hex. JSON floats must be finite; exact rationals use reduced decimal-string numerator and positive denominator.

## Graph schema

Graph requires graph_id, state_schema_hash, nodes, edges, output_node_ids, operator_registry_hash and observable_contract_hash.

Node requires node_id, kind, operator_id, operator_version, input_bindings, output_type, effect, totality_domain, guard, query and scope_hash.

- kind: QUERY, COMPOSE, GUARD or DECIDE.
- input_bindings: map from named port to state field or producer node/output port; exactly one source per required input.
- effect: PURE or ORDERED. Speculation requires PURE.
- guard: null or a producer boolean port plus selected boolean value.
- query: null for non-queries; otherwise question text, state projection paths, answer contract and model-independent query hash.
- output_type: BOOL, RATIONAL, VECTOR, NOUL, CHOICE, SCORE or ACTION, with dimensions/options/range explicitly supplied where applicable.
- totality_domain: registered domain contract hash, never merely an unchecked true flag.

Edge requires source, target, kind (DATA, GUARD, EFFECT_ORDER, SCHEDULE) and reason_contract_hash. SCHEDULE removal cannot remove any other edge or transitive semantic obligation.

Validate output references, type/shape/domain compatibility, guards, acyclicity and unique IDs. Empty graphs and unreachable output nodes are invalid. Unused nodes are allowed only when marked as speculative or diagnostic and charged to work.

## Answer schema

Answer requires case_id, node_id, state_hash, query_hash, backend_hash, status and payload. Status is OK, INVALID_OUTPUT, TIMEOUT, OOM, UNSUPPORTED or BACKEND_ERROR. Non-OK payload is null and carries a bounded diagnostic outside the normative payload.

| Type | Required payload | Invariant |
|---|---|---|
| NOUL | p_yes | finite, 0 <= p_yes <= 1 |
| CHOICE | ordered keys, probabilities, selected_key | unique keys, at least two, one probability per key |
| SCORE | ordered numeric levels, probabilities, expected_value | strictly increasing levels, expected value equals sum(level*p) |
| ACTION | action_key, policy_hash | key is in declared action set |

CHOICE/SCORE probability sum tolerance is 1e-6. Selection ties use first key in sealed order. Expected-value tolerance is 1e-6 times max(1, maximum absolute level). NOUL is a probability, not intensity. Confidence, if reported, is explicitly named normalized_entropy_confidence = 1 - H(p)/log(K); it is not calibrated correctness. Version 1 does not use this statistic to authorize actions.

The backend constructs normalized probabilities from finite logits; the validator does not repair already malformed probability records.

## Backend interface

prepare(run_lock) -> BackendDescriptor.
evaluate_batch(state_records, query_records) -> ordered Answer records.
synchronize() -> completion barrier.
close() -> resource-release receipt.

BackendDescriptor declares model/tokenizer file digests, library versions, device, precision, scoring method, max_batch_items, max_tokens, max_memory_bytes, supports_shared_state_encoding and determinism policy. A capability must be true only when implemented and tested.

Local version-1 scoring uses teacher-forced continuation log likelihood for complete declared answer strings, summed across continuation tokens and softmax-normalized over the option set. Continuation token boundaries, EOS policy and exact prompt bytes are sealed. No length normalization, calibration fitting or prompt tuning on test data. Equal-length answer labels are preferred but token lengths must be recorded. These are normalized option likelihoods, not inherently calibrated probabilities.

## Compiler and checker interfaces

compile_graph(graph, registry, cost_profile, resource_budget) -> CompileResult.
check_rewrite(source_graph, candidate_graph, receipts, registry) -> CheckResult.
execute(graph, schedule, backend, state, policy) -> ExecutionTrace.

CompileResult requires source_graph_hash, candidate_graph_hash, schedule, receipts, search_count, compile_ns and status. Schedule records dispatch groups and resource reservations; runtime may split oversized groups but must log the split.

Each receipt requires rewrite_id, rule (R1..R4), before_hash, after_hash, affected_node_ids, precondition_contract_hashes, dependency_witness and provenance_mapping. Receipt chains must start at the source and end at the candidate. Self-reported checker success in a receipt is never authoritative.

CheckResult is VALID, INVALID or UNSUPPORTED with failed obligation IDs. INVALID/UNSUPPORTED candidates are never executed as G; a logged fallback to the original graph is permitted but cannot count as a successful optimization.

## Run lock and result schema

RunLock requires spec_commit, implementation_commit, base_commit, fixture_manifest_hash, split_manifest_hash, registry_hash, policy_hash, environment_lock_hash, backend_descriptor_hash, cost_profile_hash, random_seeds, resource_budgets and manifest_hash.

Spec_commit is the actual docs commit; implementation_commit must differ once code exists. A dirty tree makes the run exploratory only. The lock is frozen before test access. All referenced files are content-hashed, including weights/tokenizer for model runs. The lock hashes the canonical record excluding manifest_hash.

ExecutionTrace requires run_id, case_id, arm, plane, run_lock_hash, graph hashes, compile/check times, node events, selected outputs, terminal verdict, refusal code, counters and timing. Node events include input/output digests, dispatch group, start/end monotonic timestamps, device completion time where available, selected/discarded status and provenance.

Counters include attempted, executed, failed, speculative, discarded and verifier node counts; model tokens scored; state tokens reprocessed; batches; peak device memory; measured CPU/GPU time where available. Unsupported telemetry is null with a reason, never zero.

CaseResult requires trace hash, correctness, action agreement, distribution drift, calibration contribution and performance metrics. Correctness may be null only with a documented unavailable oracle; such cases are excluded from efficacy gates, not counted as correct.

CampaignResult requires plane_verdicts, gate_records, complete_case_counts, exclusions, confidence_intervals, artifact_hashes and claim_boundary. Verdict vocabulary: PASS, FAIL, INCONCLUSIVE, NOT_RUN, INVALID_RUN. Every gate has measured value, threshold, denominator and reason.

## Canonical serialization

Use UTF-8 JSON, sorted keys, no insignificant whitespace, no NaN/Infinity and a domain-separated SHA-256 prefix "MAPEOGEO-E32-v1:" plus record kind plus newline. Preserve array order; reject duplicate JSON keys. Record raw file hashes separately from canonical-record hashes. Never silently mix E32 hash rules with the historical solver's canonical digest domains.

## Validator test obligations

Positive examples and independently mutated negative examples are required for every field and cross-record invariant. Mutation coverage includes stale input hashes, swapped answers, missing options, infinity, duplicate keys, cycles, undeclared dependencies, false totality declarations, counterfeit registry versions, corrupted receipt chains and fabricated terminal PASS. Validator tests precede implementation of the accepting paths.
