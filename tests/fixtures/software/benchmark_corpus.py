"""Canonical N = 50 Software Requirements Benchmark Corpus.

Spans 5 domains of software systems engineering:
1. Distributed Consensus & Raft Replication (10 requirements, weight = 32.076 each)
2. Security & Cryptographic Token Verification (10 requirements, weight = 25.704 each)
3. Asynchronous Reactive Event Streaming (10 requirements, weight = 20.52 each)
4. Traffic Shaping & Token-Bucket Rate Limiting (10 requirements, weight = 14.515 each)
5. Resilience, Fault Tolerance & Circuit Breaking (10 requirements, weight = 15.876 each)

Total initial deficiency severity:
320.76 + 257.04 + 205.20 + 145.15 + 158.76 = 1086.91
"""

from __future__ import annotations

from mapeogeo.domains.software.ontology import (
    SoftwareRequirement,
    SoftwareVerificationContracts,
)


def get_software_requirements_corpus() -> list[SoftwareRequirement]:
    """Return the canonical N = 50 software requirements corpus."""
    corpus: list[SoftwareRequirement] = []

    # 1. Distributed Consensus & Replication (REQ-RAFT-001 to 010)
    for i in range(1, 11):
        corpus.append(
            SoftwareRequirement(
                requirement_id=f"REQ-RAFT-{i:03d}",
                title=f"Raft Distributed Consensus & Quorum Log Replication {i}",
                domain="Distributed Systems",
                weight=32.076,
                required_signatures=(
                    "RAFT_CONSENSUS_STATE_MACHINE",
                    "QUORUM_LOG_REPLICATION",
                ),
                contracts=SoftwareVerificationContracts(
                    unit_test_spec="test_raft_quorum_election_and_log_append",
                    type_contract=(
                        "RaftNode[State, LogEntry] -> Result[CommitIndex, ConsensusError]"
                    ),
                    static_analysis_rule="zero_unhandled_election_timeouts",
                    latency_bound_ms=50.0,
                    concurrency_invariant="linearizable_state_history",
                ),
            )
        )

    # 2. Security & Cryptographic Token Verification (REQ-SEC-001 to 010)
    for i in range(1, 11):
        corpus.append(
            SoftwareRequirement(
                requirement_id=f"REQ-SEC-{i:03d}",
                title=f"Constant-Time HMAC & Nonce Replay Prevention {i}",
                domain="Security & Cryptography",
                weight=25.704,
                required_signatures=(
                    "CONSTANT_TIME_HMAC_VERIFIER",
                    "NONCE_REPLAY_PROTECTION_FILTER",
                ),
                contracts=SoftwareVerificationContracts(
                    unit_test_spec="test_constant_time_token_verify_and_nonce_uniqueness",
                    type_contract="TokenVerifier[SecretKey, Token] -> Result[Claims, AuthError]",
                    static_analysis_rule="zero_timing_side_channel_leakage",
                    latency_bound_ms=1.0,
                    concurrency_invariant="atomic_nonce_cache_expiration",
                ),
            )
        )

    # 3. Asynchronous Reactive Event Streaming (REQ-ASYNC-001 to 010)
    for i in range(1, 11):
        corpus.append(
            SoftwareRequirement(
                requirement_id=f"REQ-ASYNC-{i:03d}",
                title=f"Non-blocking Reactive Event Bus & Backpressure Stream {i}",
                domain="Reactive Streaming",
                weight=20.520,
                required_signatures=(
                    "ASYNC_EVENT_BUS_ROUTER",
                    "STREAM_BACKPRESSURE_FLOW",
                ),
                contracts=SoftwareVerificationContracts(
                    unit_test_spec="test_event_pubsub_and_backpressure_drain",
                    type_contract="EventBus[Event, Stream] -> AsyncIterator[Event]",
                    static_analysis_rule="zero_channel_leaks_or_deadlocks",
                    latency_bound_ms=5.0,
                    concurrency_invariant="ordered_partition_delivery",
                ),
            )
        )

    # 4. Traffic Shaping & Token-Bucket Rate Limiting (REQ-LIMIT-001 to 010)
    for i in range(1, 11):
        corpus.append(
            SoftwareRequirement(
                requirement_id=f"REQ-LIMIT-{i:03d}",
                title=f"Token-Bucket Rate Limiter & Burst Smoothing {i}",
                domain="Traffic Shaping",
                weight=14.515,
                required_signatures=(
                    "TOKEN_BUCKET_RATE_LIMITER",
                    "SLIDING_WINDOW_BURST_ABSORPTION",
                ),
                contracts=SoftwareVerificationContracts(
                    unit_test_spec="test_token_replenishment_and_burst_throttling",
                    type_contract="RateLimiter[Key, Capacity] -> AcquireResult[bool, WaitDuration]",
                    static_analysis_rule="monotonic_clock_invariant",
                    latency_bound_ms=0.5,
                    concurrency_invariant="lock_free_atomic_cas_counter",
                ),
            )
        )

    # 5. Resilience, Fault Tolerance & Circuit Breaking (REQ-RESIL-001 to 010)
    for i in range(1, 11):
        corpus.append(
            SoftwareRequirement(
                requirement_id=f"REQ-RESIL-{i:03d}",
                title=f"Circuit Breaker Failover & Exponential Backoff Retry {i}",
                domain="Resilience & Fault Tolerance",
                weight=15.876,
                required_signatures=(
                    "CIRCUIT_BREAKER_STATE_MACHINE",
                    "EXPONENTIAL_BACKOFF_RETRY",
                ),
                contracts=SoftwareVerificationContracts(
                    unit_test_spec="test_circuit_trip_half_open_and_backoff",
                    type_contract="CircuitBreaker[Req, Resp] -> FallbackOrResponse[Resp]",
                    static_analysis_rule="bounded_retry_exhaustion_guarantee",
                    latency_bound_ms=2.0,
                    concurrency_invariant="thread_safe_failure_counting",
                ),
            )
        )

    return corpus
