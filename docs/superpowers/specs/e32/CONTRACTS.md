# E32 normative contracts

All records include schema_version = "e32.v1_2". Unknown fields are rejected in sealed normative records. Diagnostic metadata uses an explicitly separate map. IDs are nonempty UTF-8 strings unique within their declared namespace. Hashes are lowercase 64-character SHA-256 hex. JSON floats must be finite; exact rationals use reduced decimal-string numerator and positive denominator.

## 1. Graph and decision-contract schema

Graph requires graph_id, decision_contract_hash, state_schema_hash, nodes, edges, output_node_ids, factorization_registry_hash, operator_registry_hash and observable_contract_hash.

Node requires node_id, kind, operator_id, operator_version, input_bindings, output_type, effect, totality_domain, guard, query, scope_hash and role.

Allowed node kinds and roles:

| kind | allowed role | output class |
|---|---|---|
| QUERY | ATOMIC_JUDGMENT | NOUL, CHOICE or SCORE |
| COMPOSE | DETERMINISTIC_COMPOSE | BOOL, RATIONAL, VECTOR, NOUL, CHOICE, SCORE or intermediate registered type |
| GUARD | CONTROL_GUARD | BOOL |
| DECIDE | POLICY_DECISION | ACTION |

The local-model backend may evaluate QUERY nodes only. It must never directly produce ACTION. ACTION is produced by a registered deterministic policy/DECIDE node.

input_bindings is a map from named port to exactly one source: a state field/projection or producer node/output port. Bindings preserve canonical order only through serialization; semantic lookup is by port name.

output_type is a closed tagged record:

- BOOL: {kind}
- RATIONAL: {kind, numerator_contract, denominator_contract}
- VECTOR: {kind, length, element_type, range_contract_hash}
- NOUL: {kind}
- CHOICE: {kind, ordered_keys}
- SCORE: {kind, ordered_levels}
- ACTION: {kind, ordered_action_keys}

No undeclared output type is accepted in a sealed v1.2 campaign.

effect is PURE or ORDERED. Speculation requires PURE.

totality_domain is a registered domain-contract hash, never an unchecked boolean assertion.

guard is null or exactly {producer_node_id, producer_port, selected_boolean}. The producer port must be BOOL.

query is null for non-QUERY nodes; otherwise exactly {question_text, state_projection_paths, answer_contract_hash, option_set_hash, option_semantics, query_hash}.

- state_projection_paths is an ordered list of declared immutable state paths.
- option_semantics is exactly LISTWISE_ORDERED for CHOICE and SCORE and SINGLE_BINARY for NOUL.
- option_set_hash binds the complete ordered keys/levels and is null only for NOUL.
- query_hash is model-independent and binds exact question bytes, state-projection declaration, answer contract, option semantics and ordered option set. It does not bind backend/model identity.

Changing a CHOICE/SCORE option order, adding/removing an option or changing an option label creates a new option_set_hash and query_hash. Question-order permutations across independent sibling QUERY nodes do not change any individual query_hash.

role is one of the role values in the table above and must match kind.

Edge requires source, target, kind and reason_contract_hash. kind is DATA, GUARD, EFFECT_ORDER or SCHEDULE. Removing a SCHEDULE edge cannot remove any other edge or transitive semantic obligation.

Validate output references, type/shape/domain compatibility, guards, acyclicity, unique IDs, reachable outputs and role/kind consistency. Empty graphs and unreachable output nodes are invalid. Unused nodes are allowed only when explicitly marked in diagnostic metadata as speculative or diagnostic and charged to work.

## 2. DecisionContract, ObservableContract and PolicyContract

DecisionContract is the source-level object against which S/T execute and M/G factorizations are checked. It requires decision_contract_id, input_state_schema_hash, source_graph_hash, observable_contract_hash, policy_contract_hash, allowed_factorization_contract_ids and lineage_obligation_hash.

ObservableContract requires observable_contract_id, selected_action_required, selected_output_specs, refusal_semantics_hash, lineage_obligation_hash and numeric_tolerance_contracts. selected_output_specs is an ordered list of {node_or_role, output_type, comparison_mode, tolerance_contract_hash_or_null}.

PolicyContract requires policy_contract_id, policy_version, input_bindings, action_keys, abstain_key, decision_rule and utility_contract_hash.

Version-1.2 primary policy semantics are explicit:

- CHOICE: select argmax using sealed key order for ties; act only if max probability > 0.5, otherwise abstain.
- NOUL: represent the distribution (p_yes, 1-p_yes); choose YES when p_yes > 0.5, NO when p_yes < 0.5, and abstain exactly at 0.5 unless the registered decision rule maps YES/NO to another action set.
- SCORE: a SCORE node alone never authorizes an action. A registered deterministic composition or threshold mapping must convert the expected score/distribution into CHOICE/NOUL or an explicit policy input before DECIDE.

Any policy differing from these primary semantics requires a distinct PolicyContract hash and a new sealed campaign configuration; test-data-driven policy changes are prohibited.

## 3. FactorizationContract

FactorizationContract requires factorization_contract_id, source_pattern_hash, source_observable_contract_hash, admissible_input_domain_hash, atomic_node_templates, composition_template, lineage_mapping_contract_hash, checker_obligation_ids and version.

atomic_node_templates is an ordered list of exact node-template contracts including kind, role, output type, state projection/input binding pattern and semantic contract hash.

composition_template identifies a pure deterministic composition graph and its registry/operator versions.

A FactorizationContract is admissible only when the independent checker can decide every listed obligation from solver-visible inputs, registry contracts and candidate/source graphs without sealed answers. Human-authored M and automatically generated G factorizations use the same FactorizationContract registry.

Factorization contracts do not assert universal semantic equivalence. They authorize only the registered source pattern and admissible domain under the declared checker obligations.

## 4. Answer schema and listwise semantics

Answer requires case_id, node_id, state_hash, query_hash, backend_hash, status and payload. status is OK, INVALID_OUTPUT, TIMEOUT, OOM, UNSUPPORTED or BACKEND_ERROR. Non-OK payload is null and carries a bounded diagnostic outside the normative payload.

| Type | Required payload | Invariant |
|---|---|---|
| NOUL | {p_yes} | finite, 0 <= p_yes <= 1 |
| CHOICE | {ordered_keys, probabilities, selected_key} | unique keys, at least two, one probability per key |
| SCORE | {ordered_levels, probabilities, expected_value} | strictly increasing levels, one probability per level, expected value equals sum(level*p) |

The backend never returns ACTION in v1.2.

CHOICE/SCORE probability sum tolerance is 1e-6. Selection ties use first key in sealed order. Expected-value tolerance is 1e-6 times max(1, maximum absolute level). NOUL is a probability, not intensity.

CHOICE and SCORE are listwise outputs. The returned distribution is defined relative to the complete ordered option set bound by query_hash. A probability assigned to key k under option set O is not normatively required to equal the probability assigned to k under a different order or expanded/reduced option set O'. Cross-option-set comparisons are characterization measurements, not answer-equivalence checks.

The backend constructs normalized probabilities from finite logits/readout scores according to its sealed scoring_method. The validator does not repair already malformed probability records.

## 5. Deterministic confidence diagnostics

Confidence is optional diagnostic post-processing and is never a second model prediction.

NOUL has no separate normative confidence value in v1.2.

CHOICE may report choice_uniform_baseline_confidence, computed only from the returned distribution as:

c = (p_max - 1/K) / (1 - 1/K)

where K >= 2 is the number of declared keys and p_max is the maximum returned probability. The value must be finite. A validator may either require 0 <= c <= 1 within numerical tolerance or reject a distribution that makes the registered metric invalid; it may not clip silently.

SCORE has no universal confidence formula in v1.2. A SCORE diagnostic may be reported only under a registered DiagnosticMetricContract that names the metric, exact deterministic formula, applicable answer type and version. Entropy, variance, concentration or another metric must not be relabelled generically as "confidence" without such a contract.

DiagnosticMetricContract requires metric_id, metric_version, answer_type, exact_formula_id, parameter_record and output_range_contract_hash. Its hash is sealed in RunLock through diagnostic_metrics_hash.

No diagnostic confidence metric authorizes actions in the primary PolicyContract.

## 6. Backend interface and capability levels

probe_backend(preflight_config) -> BackendDescriptor.
prepare(run_lock, expected_descriptor_hash) -> PreparedBackend.
evaluate_batch(state_records, query_records) -> ordered Answer records.
synchronize() -> completion barrier.
close() -> resource-release receipt.

BackendDescriptor requires backend_id, capability_level, model_tokenizer_digests, library_versions, device, precision, scoring_method, max_batch_items, max_tokens, max_memory_bytes, supports_shared_state_encoding, supports_prefix_reuse, supports_direct_readout, readout_contract_hash_or_null and determinism_policy.

capability_level is B0, B1, B2, B3 or B4 as defined in ARCHITECTURE.md. A capability flag may be true only when implemented and tested in preflight. prepare must fail if the live backend descriptor differs from the hash sealed in RunLock.

B0/B1/B2 teacher-forced scoring uses continuation log likelihood for complete declared answer strings, summed across continuation tokens and softmax-normalized over the option set. Continuation token boundaries, EOS policy and exact prompt bytes are sealed. No length normalization, calibration fitting or prompt tuning on test data. Equal-length answer labels are preferred but token lengths must be recorded. These are normalized option likelihoods, not inherently calibrated probabilities.

B0 evaluates eligible questions independently. B1 may tensor-batch independent question/option scoring but must not claim shared-state reuse. B2 may claim shared-state/prefix reuse only when preflight tests demonstrate actual reuse and its accounting fields report reduced state reprocessing.

B3 direct typed readout uses a sealed ReadoutContract and does not score generated answer strings. ReadoutContract requires readout_contract_id, base_model_hash, tokenizer_hash, extraction_location, extraction_rule, source_tensor_contract, projection_contract_hash, option_encoding_contract_hash, normalization_rule, answer_type_set, trainable_parameter_hashes, training_provenance_hash_or_null and version.

- extraction_location/rule identify the exact hidden-state/logit position(s) consumed after the declared input has been processed.
- projection_contract_hash identifies the deterministic or trained mapping from source tensor(s) to finite option scores.
- option_encoding_contract_hash binds how ordered keys/levels are represented to the readout.
- normalization_rule defines the exact conversion from finite readout scores to the returned distribution.
- training_provenance_hash_or_null is null only when the readout introduces no trained parameters beyond already sealed model parameters.

A B3 backend may use an ordinary causal-model prefill. B3 means non-generative typed decision readout only; it does not establish a proprietary single-pass sampler, noncausal attention architecture or Jev equivalence.

B4 requires a future campaign version that seals the decision-specialized post-training/calibration corpus, objective, optimizer/training procedure, held-out calibration protocol and resulting parameter hashes. B4 is not part of the v1.2 primary campaign.

## 7. CostProfile and ResourceBudget

CostProfile requires profile_id, backend_descriptor_hash, estimator_version, node_cost_table, batch_cost_model, state_reprocessing_model, calibration_split_hash and frozen_at_commit.

Each node_cost_table entry is keyed by a relabel-invariant structural signature and provides a finite nonnegative predicted cost unit. Test case IDs, sealed labels and test timings are forbidden inputs to the estimator.

ResourceBudget requires budget_id, concurrency_cap, batch_item_cap, max_tokens_per_item, max_memory_bytes, cpu_thread_count, numerical_library_thread_count, timeout_ns and optional_gpu_stream_policy.

## 8. Compiler, factorizer and checker interfaces

factorize_graph(decision_contract, source_graph, factorization_registry, registry, cost_profile, resource_budget) -> FactorizationResult.
compile_graph(graph, registry, cost_profile, resource_budget) -> CompileResult.
check_factorization(decision_contract, source_graph, candidate_graph, receipts, factorization_registry, registry) -> CheckResult.
check_rewrite(source_graph, candidate_graph, receipts, registry) -> CheckResult.
execute(graph, schedule, backend, state, policy) -> ExecutionTrace.

FactorizationResult requires source_graph_hash, candidate_graph_hash, factorization_receipts, search_count, factorization_ns and status.

CompileResult requires source_graph_hash, candidate_graph_hash, schedule, rewrite_receipts, search_count, compile_ns and status. Schedule requires schedule_id, graph_hash, dispatch_groups, resource_reservations, scheduling_policy_hash and structural_tie_break_key_version. Runtime may split oversized groups but must log the split.

Each factorization/rewrite receipt requires receipt_id, rule, before_hash, after_hash, affected_node_ids, precondition_contract_hashes, obligation_ids, dependency_witness and provenance_mapping.

For R0, dependency_witness additionally binds factorization_contract_id and source-pattern match. For R1-R4 it binds the rule-specific semantic preconditions. provenance_mapping is an ordered mapping from every affected source use site to candidate use site(s); dropped speculative/diagnostic sites require an explicit reason.

Receipt chains must start at the source and end at the candidate. Self-reported checker success in a receipt is never authoritative.

CheckResult is VALID, INVALID or UNSUPPORTED with failed obligation IDs. INVALID/UNSUPPORTED candidates are never executed as G. A logged fallback to the original graph is permitted but cannot count as a successful optimization/factorization.

## 9. Relabel-invariant structural key

Compiler search and tie breaking must not depend on raw node IDs. The structural key is computed from a canonical topological refinement over node kind/role, operator/version, typed input-source signatures, guard/effect metadata, output contract and recursively derived predecessor signatures. If automorphisms remain, equivalent candidates are ordered by canonical serialized multiset representation rather than original IDs.

Node-relabel invariance tests must demonstrate identical selected candidate structure modulo isomorphism, identical action and identical cost prediction.

## 10. Run lock and result schema

RunLock requires spec_commit, implementation_commit, base_commit, fixture_manifest_hash, split_manifest_hash, factorization_registry_hash, registry_hash, policy_hash, diagnostic_metrics_hash, environment_lock_hash, backend_descriptor_hash, cost_profile_hash, resource_budget_hash, random_seeds and manifest_hash.

Spec_commit is the actual docs commit. implementation_commit must differ once code exists. A dirty tree makes the run exploratory only. The lock is frozen after successful preflight and before validation/test access. All referenced files are content-hashed, including weights/tokenizer/readout parameters for model runs. The lock hashes the canonical record excluding manifest_hash.

ExecutionTrace requires run_id, case_id, arm, plane, backend_level, run_lock_hash, graph hashes, factorization/compile/check times, node events, selected outputs, terminal verdict, refusal code, counters and timing.

Node events include input/output digests, dispatch group, start/end monotonic timestamps, device completion time where available, selected/discarded status and provenance.

Counters include attempted, executed, failed, speculative, discarded and verifier node counts; model input tokens processed; option continuation tokens scored; direct-readout evaluations; state tokens reprocessed; batches; peak device memory; measured CPU/GPU time when available; and predicted_cost_units. Unsupported telemetry is null with a reason, never zero.

CaseResult requires trace_hash, correctness, action_agreement, distribution_drift, calibration_contribution, structural_metrics, option_set_characterization and performance_metrics.

option_set_characterization may be null only when the case has no CHOICE/SCORE probe. When present it records source_option_set_hash, perturbed_option_set_hash, perturbation_type, aligned_common_keys, per_common_key_probability_delta, pairwise_log_odds_delta where defined, selected_key_change and diagnostic notes.

Correctness may be null only with a documented unavailable oracle; such cases are excluded from efficacy gates, not counted as correct.

CampaignResult requires plane_verdicts, backend_level_verdicts, gate_records, complete_case_counts, exclusions, confidence_intervals, artifact_hashes and claim_boundary. Verdict vocabulary is PASS, FAIL, INCONCLUSIVE, NOT_RUN or INVALID_RUN. Narrative may use NOT_SUPPORTED only as prose explaining a failed scientific gate. Every gate records measured value, threshold, denominator and reason.

## 11. Canonical serialization

Use UTF-8 JSON, sorted keys, no insignificant whitespace, no NaN/Infinity and a domain-separated SHA-256 prefix "MAPEOGEO-E32-v1.2:" plus record kind plus newline. Preserve array order; reject duplicate JSON keys. Record raw file hashes separately from canonical-record hashes. Never silently mix E32 hash rules with the historical solver's canonical digest domains.

## 12. Validator test obligations

Positive examples and independently mutated negative examples are required for every field and cross-record invariant. Mutation coverage includes stale input hashes, swapped answers, missing options, infinity, duplicate keys, cycles, undeclared dependencies, false totality declarations, counterfeit registry versions, malformed role/kind pairs, backend ACTION output, corrupted receipt chains, invalid R0 source-pattern matches, state-dependent compile-cache reuse, raw-node-ID tie breaking, stale option_set_hash, query hash that fails to bind option order, invalid confidence metric formula/hash, malformed B3 ReadoutContract and fabricated terminal PASS.

Validator tests precede implementation of accepting paths.
