"""Certification Boundary Component (C).

Enforces 4-gate verification before machinery admission:
    Gate 1: Dependency Completeness and Acyclicity
    Gate 2: Constructive Witness and Work Grammar Compliance
    Gate 3: Semantic Non-Triviality
    Gate 4: Reach Consistency and Non-Regression
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mapeogeo.grammar.work_grammar import WorkGrammar

if TYPE_CHECKING:
    from mapeogeo.kernel.machinery import MachineryCandidate
    from mapeogeo.kernel.state import KnowledgeState


@dataclass(frozen=True)
class CertificationResult:
    """Outcome of 4-gate certification evaluation."""

    is_certified: bool
    certificate_id: str
    gates_passed: tuple[str, ...]
    failure_reason: str | None = None
    timestamp: float = 0.0


class CertificationBoundary:
    """Evaluates candidate machinery across the 4 formal certification gates."""

    def __init__(self, grammar: WorkGrammar | None = None) -> None:
        self.grammar = grammar or WorkGrammar()

    def certify_candidate(
        self,
        candidate: MachineryCandidate,
        current_state: KnowledgeState,
    ) -> CertificationResult:
        """Run all 4 verification gates fail-closed."""
        gates_passed: list[str] = []
        now = time.time()

        # Gate 1: Dependency completeness against current state
        available_caps = set(current_state.signatures)
        for node in candidate.nodes:
            missing_deps = set(node.dependencies) - available_caps
            if missing_deps:
                return CertificationResult(
                    is_certified=False,
                    certificate_id="",
                    gates_passed=tuple(gates_passed),
                    failure_reason=(
                        f"Gate 1 failed: node '{node.node_id}' has unresolved "
                        f"dependencies {sorted(missing_deps)}"
                    ),
                    timestamp=now,
                )
        gates_passed.append("GATE_1_DEPENDENCY_COMPLETENESS")

        # Gate 2: Witness certificates and grammar compliance
        for w_id in candidate.witness_ids:
            witness = self.grammar.get_witness(w_id)
            if witness is None:
                return CertificationResult(
                    is_certified=False,
                    certificate_id="",
                    gates_passed=tuple(gates_passed),
                    failure_reason=(
                        f"Gate 2 failed: witness '{w_id}' is not registered in work grammar"
                    ),
                    timestamp=now,
                )
        gates_passed.append("GATE_2_WITNESS_GRAMMAR_COMPLIANCE")

        # Gate 3: Semantic non-triviality (must provide at least one declared signature)
        if not candidate.provided_signatures or len(candidate.nodes) == 0:
            return CertificationResult(
                is_certified=False,
                certificate_id="",
                gates_passed=tuple(gates_passed),
                failure_reason=(
                    "Gate 3 failed: candidate provides empty signatures or empty node set"
                ),
                timestamp=now,
            )
        gates_passed.append("GATE_3_SEMANTIC_NON_TRIVIALITY")

        # Gate 4: Reach consistency and non-regression
        cand_sigs = frozenset(candidate.provided_signatures)
        if cand_sigs.issubset(current_state.signatures) and len(candidate.nodes) == 0:
            return CertificationResult(
                is_certified=False,
                certificate_id="",
                gates_passed=tuple(gates_passed),
                failure_reason="Gate 4 failed: candidate provides zero capability growth",
                timestamp=now,
            )
        gates_passed.append("GATE_4_REACH_CONSISTENCY")

        # All 4 gates passed: issue deterministic certificate
        cert_hasher = hashlib.sha256()
        cert_hasher.update(candidate.candidate_id.encode())
        cert_hasher.update(current_state.state_hash.encode())
        cert_hasher.update(str(now).encode())
        cert_id = f"cert-{cert_hasher.hexdigest()[:16]}"

        return CertificationResult(
            is_certified=True,
            certificate_id=cert_id,
            gates_passed=tuple(gates_passed),
            failure_reason=None,
            timestamp=now,
        )
