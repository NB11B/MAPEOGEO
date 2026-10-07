"""Candidate Software Machinery Fixtures.

Concrete candidate software machinery packages providing functional signatures
and executable verification contracts across:
1. Raft Distributed Consensus Engine
2. Constant-Time HMAC Verification Library
3. Async Event Bus & Reactive Backpressure Engine
4. Lock-Free Token-Bucket Rate Limiter
5. Tri-State Circuit Breaker & Exponential Backoff Library
6. Unrelated ASCII Art Control Library
"""

from __future__ import annotations

from mapeogeo.domains.software.ontology import (
    SoftwareEvidence,
    SoftwareMachinery,
)
from mapeogeo.kernel.machinery import MachineryCandidate, MachineryNode


def get_candidate_software_machinery() -> list[SoftwareMachinery]:
    """Return the candidate software machinery packages."""
    return [
        SoftwareMachinery(
            machinery_id="LIB_RAFT_CONSENSUS",
            name="Raft Distributed Consensus & Quorum Replication Engine",
            domain="Distributed Systems",
            cost=14.0,
            provided_signatures=(
                "RAFT_CONSENSUS_STATE_MACHINE",
                "QUORUM_LOG_REPLICATION",
            ),
            witness_id="w_sw_raft_1",
            witness_symbol="WITNESS_RAFT_CONSENSUS_CORE",
            evidence=SoftwareEvidence(
                type_safety_pass=True,
                unit_tests_pass=True,
                static_analysis_pass=True,
                measured_latency_ms=32.4,  # Under 50ms bound
                fault_tolerance_pass=True,
                details={"concurrency": "linearizable_state_history"},
            ),
        ),
        SoftwareMachinery(
            machinery_id="LIB_SEC_HMAC_AUTH",
            name="Constant-Time HMAC & Nonce Replay Protection Library",
            domain="Security & Cryptography",
            cost=12.5,
            provided_signatures=(
                "CONSTANT_TIME_HMAC_VERIFIER",
                "NONCE_REPLAY_PROTECTION_FILTER",
            ),
            witness_id="w_sw_sec_1",
            witness_symbol="WITNESS_CONSTANT_TIME_HMAC",
            evidence=SoftwareEvidence(
                type_safety_pass=True,
                unit_tests_pass=True,
                static_analysis_pass=True,
                measured_latency_ms=0.42,  # Under 1.0ms bound
                fault_tolerance_pass=True,
                details={"timing": "constant_time_invariant"},
            ),
        ),
        SoftwareMachinery(
            machinery_id="LIB_ASYNC_EVENT_STREAM",
            name="Async Event Bus & Reactive Backpressure Engine",
            domain="Reactive Streaming",
            cost=11.5,
            provided_signatures=(
                "ASYNC_EVENT_BUS_ROUTER",
                "STREAM_BACKPRESSURE_FLOW",
            ),
            witness_id="w_sw_async_1",
            witness_symbol="WITNESS_REACTIVE_EVENT_BUS",
            evidence=SoftwareEvidence(
                type_safety_pass=True,
                unit_tests_pass=True,
                static_analysis_pass=True,
                measured_latency_ms=2.1,  # Under 5.0ms bound
                fault_tolerance_pass=True,
                details={"backpressure": "bounded_channel_drain"},
            ),
        ),
        SoftwareMachinery(
            machinery_id="LIB_TOKEN_RATE_LIMITER",
            name="Lock-Free Token-Bucket Rate Limiter & Burst Smoother",
            domain="Traffic Shaping",
            cost=9.5,
            provided_signatures=(
                "TOKEN_BUCKET_RATE_LIMITER",
                "SLIDING_WINDOW_BURST_ABSORPTION",
            ),
            witness_id="w_sw_limit_1",
            witness_symbol="WITNESS_TOKEN_BUCKET_CAS",
            evidence=SoftwareEvidence(
                type_safety_pass=True,
                unit_tests_pass=True,
                static_analysis_pass=True,
                measured_latency_ms=0.18,  # Under 0.5ms bound
                fault_tolerance_pass=True,
                details={"cas": "lock_free_monotonic_cas"},
            ),
        ),
        SoftwareMachinery(
            machinery_id="LIB_CIRCUIT_BREAKER",
            name="Tri-State Circuit Breaker & Exponential Backoff Library",
            domain="Resilience & Fault Tolerance",
            cost=10.5,
            provided_signatures=(
                "CIRCUIT_BREAKER_STATE_MACHINE",
                "EXPONENTIAL_BACKOFF_RETRY",
            ),
            witness_id="w_sw_resil_1",
            witness_symbol="WITNESS_CIRCUIT_BREAKER",
            evidence=SoftwareEvidence(
                type_safety_pass=True,
                unit_tests_pass=True,
                static_analysis_pass=True,
                measured_latency_ms=0.85,  # Under 2.0ms bound
                fault_tolerance_pass=True,
                details={"failover": "tri_state_isolation"},
            ),
        ),
        SoftwareMachinery(
            machinery_id="LIB_UNRELATED_ASCII_CONTROL",
            name="Unrelated Control Library (ASCII Font Art Generator)",
            domain="Text Manipulation",
            cost=10.0,
            provided_signatures=(
                "UNRELATED_ASCII_TILING",
                "UNUSED_FONT_METRICS",
            ),
            witness_id="w_sw_ascii_1",
            witness_symbol="WITNESS_ASCII_TILING",
            evidence=SoftwareEvidence(
                type_safety_pass=True,
                unit_tests_pass=True,
                static_analysis_pass=True,
                measured_latency_ms=1.2,
                fault_tolerance_pass=True,
                details={"rendering": "ascii_banners"},
            ),
        ),
    ]


def to_machinery_candidates(packages: list[SoftwareMachinery]) -> list[MachineryCandidate]:
    """Convert SoftwareMachinery packages to kernel MachineryCandidate instances."""
    candidates: list[MachineryCandidate] = []
    for pkg in packages:
        nodes = tuple(
            MachineryNode(
                node_id=f"node:{pkg.machinery_id.lower()}:{i}",
                provided_signatures=(sig,),
                dependencies=(),
                witness_id=pkg.witness_id,
            )
            for i, sig in enumerate(pkg.provided_signatures)
        )
        candidates.append(
            MachineryCandidate(
                candidate_id=pkg.machinery_id,
                provided_signatures=pkg.provided_signatures,
                cost=pkg.cost,
                nodes=nodes,
                witness_ids=(pkg.witness_id,) if pkg.witness_id else (),
                metadata={"domain": pkg.domain, "name": pkg.name},
            )
        )
    return candidates
